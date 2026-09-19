import time
from typing import Dict, Any, List
from django.db import transaction
from django.utils import timezone as dj_timezone
from tracker.models import TrackedProduct, PriceHistory, ScrapeLog, ProductChange, Alert
from tracker.scraper.browser import _single_attempt_scrape, ScraperError


def execute_scrape_for_tracked_product(tracked_product: TrackedProduct, headless: bool = True) -> Dict[str, Any]:
    """
    Executes up to 3 bounded scrape attempts for a TrackedProduct.
    - Records EVERY attempt in ScrapeLog.
    - Creates PriceHistory ONLY upon successful validated scrape.
    - Detects price & stock changes and generates persistent Alerts.
    - Updates next_scrape_at schedule using tracked_product.scrape_interval_hours.
    """
    max_attempts = 3
    backoff_seconds = [2, 5]
    product_url = tracked_product.product.product_url

    retried_occurred = False
    final_success = False

    for attempt_num in range(1, max_attempts + 1):
        start_time = time.time()
        attempted_at = dj_timezone.now()

        try:
            res = _single_attempt_scrape(product_url, headless=headless)
            duration_ms = int((time.time() - start_time) * 1000)

            ScrapeLog.objects.create(
                tracked_product=tracked_product,
                attempted_at=attempted_at,
                attempt_number=attempt_num,
                status="SUCCESS",
                duration_ms=duration_ms
            )

            with transaction.atomic():
                prior_history = PriceHistory.objects.filter(
                    tracked_product=tracked_product
                ).order_by("-recorded_at").first()

                new_history = PriceHistory.objects.create(
                    tracked_product=tracked_product,
                    price=res["price"],
                    currency=res["currency"],
                    stock=res["stock"],
                    recorded_at=attempted_at
                )

                interval_hours = getattr(tracked_product, "scrape_interval_hours", 2)
                if interval_hours not in TrackedProduct.ALLOWED_INTERVALS:
                    interval_hours = 2
                tracked_product.next_scrape_at = attempted_at + dj_timezone.timedelta(hours=interval_hours)
                tracked_product.save()

                if prior_history:
                    if res["price"] < prior_history.price:
                        change = ProductChange.objects.create(
                            tracked_product=tracked_product,
                            change_type="PRICE_DECREASE",
                            previous_value=str(prior_history.price),
                            current_value=str(res["price"]),
                            detected_at=attempted_at
                        )
                        Alert.objects.create(
                            tracked_product=tracked_product,
                            change_event=change,
                            alert_type="PRICE_DECREASE",
                            title=f"Price dropped for {tracked_product.product.name}",
                            message=f"₹{prior_history.price:,.2f} → ₹{res['price']:,.2f}"
                        )
                    elif res["price"] > prior_history.price:
                        change = ProductChange.objects.create(
                            tracked_product=tracked_product,
                            change_type="PRICE_INCREASE",
                            previous_value=str(prior_history.price),
                            current_value=str(res["price"]),
                            detected_at=attempted_at
                        )
                        Alert.objects.create(
                            tracked_product=tracked_product,
                            change_event=change,
                            alert_type="PRICE_INCREASE",
                            title=f"Price increased for {tracked_product.product.name}",
                            message=f"₹{prior_history.price:,.2f} → ₹{res['price']:,.2f}"
                        )

                    prior_stock = prior_history.stock
                    curr_stock = res["stock"]
                    if prior_stock is not None and curr_stock is not None:
                        if curr_stock < prior_stock:
                            change = ProductChange.objects.create(
                                tracked_product=tracked_product,
                                change_type="STOCK_DECREASE",
                                previous_value=str(prior_stock),
                                current_value=str(curr_stock),
                                detected_at=attempted_at
                            )
                            Alert.objects.create(
                                tracked_product=tracked_product,
                                change_event=change,
                                alert_type="STOCK_DECREASE",
                                title=f"Stock decreased for {tracked_product.product.name}",
                                message=f"{prior_stock} → {curr_stock} left"
                            )
                        elif curr_stock > prior_stock:
                            change = ProductChange.objects.create(
                                tracked_product=tracked_product,
                                change_type="STOCK_INCREASE",
                                previous_value=str(prior_stock),
                                current_value=str(curr_stock),
                                detected_at=attempted_at
                            )
                            Alert.objects.create(
                                tracked_product=tracked_product,
                                change_event=change,
                                alert_type="STOCK_INCREASE",
                                title=f"Stock increased for {tracked_product.product.name}",
                                message=f"{prior_stock} → {curr_stock} left"
                            )

            final_success = True
            return {
                "success": True,
                "product_id": str(tracked_product.id),
                "product_name": res["product_name"],
                "price": res["price"],
                "stock": res["stock"],
                "attempts": attempt_num,
                "retried": retried_occurred,
                "error": None
            }

        except ScraperError as err:
            duration_ms = int((time.time() - start_time) * 1000)
            will_retry = err.retryable and (attempt_num < max_attempts)
            status = "RETRIED" if will_retry else "FAILED"

            if will_retry:
                retried_occurred = True

            ScrapeLog.objects.create(
                tracked_product=tracked_product,
                attempted_at=attempted_at,
                attempt_number=attempt_num,
                status=status,
                error_code=err.code,
                error_message=err.message,
                duration_ms=duration_ms
            )

            if will_retry:
                time.sleep(backoff_seconds[attempt_num - 1] if attempt_num - 1 < len(backoff_seconds) else 2)
            else:
                tracked_product.next_scrape_at = dj_timezone.now() + dj_timezone.timedelta(minutes=10)
                tracked_product.save()
                return {
                    "success": False,
                    "product_id": str(tracked_product.id),
                    "product_name": tracked_product.product.name,
                    "price": None,
                    "stock": None,
                    "attempts": attempt_num,
                    "retried": retried_occurred,
                    "error": f"[{err.code}] {err.message}"
                }

        except Exception as err:
            duration_ms = int((time.time() - start_time) * 1000)
            ScrapeLog.objects.create(
                tracked_product=tracked_product,
                attempted_at=attempted_at,
                attempt_number=attempt_num,
                status="FAILED",
                error_code="UNKNOWN_ERROR",
                error_message=str(err),
                duration_ms=duration_ms
            )

            tracked_product.next_scrape_at = dj_timezone.now() + dj_timezone.timedelta(minutes=10)
            tracked_product.save()
            return {
                "success": False,
                "product_id": str(tracked_product.id),
                "product_name": tracked_product.product.name,
                "price": None,
                "stock": None,
                "attempts": attempt_num,
                "retried": retried_occurred,
                "error": str(err)
            }

    return {
        "success": False,
        "product_id": str(tracked_product.id),
        "product_name": tracked_product.product.name,
        "price": None,
        "stock": None,
        "attempts": max_attempts,
        "retried": retried_occurred,
        "error": "Max retries exceeded"
    }


def run_scrape_due_batch(limit: int = 10) -> Dict[str, Any]:
    """
    Finds active TrackedProducts due for scraping, executes scrapes sequentially,
    records logs, and continues if any single product fails.
    """
    due_products = TrackedProduct.objects.filter(
        is_active=True,
        next_scrape_at__lte=dj_timezone.now()
    )[:limit]

    results = []
    success_cnt = 0
    retried_cnt = 0
    failed_cnt = 0

    for tp in due_products:
        res = execute_scrape_for_tracked_product(tp, headless=True)
        results.append(res)
        if res["success"]:
            success_cnt += 1
            if res.get("retried"):
                retried_cnt += 1
        else:
            failed_cnt += 1

    return {
        "ok": True,
        "due_count": len(due_products),
        "processed": len(due_products),
        "successful_count": success_cnt,
        "succeeded": success_cnt,
        "retried_count": retried_cnt,
        "failed_count": failed_cnt,
        "failed": failed_cnt,
        "results": results
    }

