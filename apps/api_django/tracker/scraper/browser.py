import time
from decimal import Decimal
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Response
from .parse import parse_price, parse_currency, parse_stock

class ScraperError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def _single_attempt_scrape(product_url: str, headless: bool = True) -> Dict[str, Any]:
    """
    Runs a single scrape attempt in a brand-new Playwright context.
    Shared identically by both normal (headless=True) and demo (headless=False) modes.
    """
    captured_layout: Dict[str, Any] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_response(response: Response):
            nonlocal captured_layout
            if "/api/layout" in response.url and response.status == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        captured_layout = data
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            response = page.goto(product_url, wait_until="domcontentloaded", timeout=15000)
            if not response or response.status >= 500 or response.status == 429:
                raise ScraperError("STORE_TEMPORARY_ERROR", f"Store returned HTTP status {response.status if response else 'None'}", retryable=True)
            if response.status == 404:
                raise ScraperError("PRODUCT_NOT_FOUND", "Product URL returned 404", retryable=False)

            h1_elem = page.wait_for_selector("h1", timeout=8000)
            product_name = h1_elem.inner_text().strip() if h1_elem else ""

            price_block = page.query_selector(".price-block") or page.query_selector("#price-container")
            if price_block:
                box = price_block.bounding_box()
                if box:
                    start_x = box["x"] + 10
                    start_y = box["y"] + 10
                    for i in range(12):
                        page.mouse.move(start_x + i * 5, start_y + (i % 3) * 5)
                        time.sleep(0.06)

            try:
                reveal_btn = page.wait_for_selector("button.reveal-price, button:has-text('Reveal price'), .price-block button", timeout=5000)
                if reveal_btn:
                    reveal_btn.click(timeout=5000)
            except Exception:
                pass

            try:
                page.wait_for_function(
                    "() => { const el = document.querySelector('.price-block, .price-display'); return el && !el.innerText.includes('Loading') && !el.innerText.includes('Price hidden'); }",
                    timeout=8000
                )
            except Exception:
                time.sleep(1.5)

            classes = captured_layout.get("classes", {}) if isinstance(captured_layout, dict) else {}
            price_class = (
                classes.get("priceValue")
                or classes.get("priceValueClass")
                or captured_layout.get("priceValueClass")
                or captured_layout.get("priceValue")
            )
            stock_class = (
                classes.get("stock")
                or classes.get("stockClass")
                or captured_layout.get("stockClass")
                or captured_layout.get("stock")
            )

            price_elem = page.query_selector(f".{price_class}") if price_class else None
            if not price_elem:
                price_elem = page.query_selector(".price-display") or page.query_selector(".price-value") or page.query_selector(".price-block")

            stock_elem = page.query_selector(f".{stock_class}") if stock_class else None
            if not stock_elem:
                stock_elem = page.query_selector(".stock-status") or page.query_selector(".stock") or page.query_selector(".price-block")

            raw_price_text = price_elem.inner_text() if price_elem else ""
            raw_stock_text = stock_elem.inner_text() if stock_elem else ""

            price_val = parse_price(raw_price_text)
            currency_val = parse_currency(raw_price_text) or "INR"
            stock_val = parse_stock(raw_stock_text)

            if stock_val is None and price_elem:
                stock_val = parse_stock(price_elem.inner_text())

            if price_val is None:
                raise ScraperError("PRICE_INVALID", f"Could not extract valid selling price from '{raw_price_text}'", retryable=True)
            if stock_val is None:
                if "out of stock" in raw_stock_text.lower() or "sold out" in raw_stock_text.lower():
                    stock_val = 0
                else:
                    raise ScraperError("STOCK_INVALID", f"Could not determine valid stock count from '{raw_stock_text}'", retryable=True)

            return {
                "product_name": product_name,
                "price": float(price_val),
                "currency": currency_val,
                "stock": stock_val,
            }

        except ScraperError:
            raise
        except Exception as err:
            err_str = str(err)
            if "Timeout" in err_str:
                raise ScraperError("STORE_TIMEOUT", err_str, retryable=True)
            raise ScraperError("STORE_NETWORK_ERROR", err_str, retryable=True)
        finally:
            browser.close()


def scrape_product(product_url: str, headless: bool = True) -> Dict[str, Any]:
    """
    Scrapes any valid product URL with up to 3 fresh Playwright page/browser attempts.
    Returns structured result dict.
    - headless=True: Production headless execution.
    - headless=False: Production headed execution (demo / inspection).
    """
    max_attempts = 3
    backoff_seconds = [2, 5]
    last_error_msg = ""
    product_name = ""

    for attempt in range(1, max_attempts + 1):
        try:
            data = _single_attempt_scrape(product_url, headless=headless)
            return {
                "success": True,
                "product_url": product_url,
                "product_name": data["product_name"],
                "price": data["price"],
                "currency": data["currency"],
                "stock": data["stock"],
                "attempts": attempt,
                "error": None,
            }
        except ScraperError as err:
            last_error_msg = f"[{err.code}] {err.message}"
            if not err.retryable or attempt == max_attempts:
                return {
                    "success": False,
                    "product_url": product_url,
                    "product_name": product_name,
                    "price": None,
                    "currency": None,
                    "stock": None,
                    "attempts": attempt,
                    "error": last_error_msg,
                }
            time.sleep(backoff_seconds[attempt - 1] if attempt - 1 < len(backoff_seconds) else 2)
        except Exception as err:
            last_error_msg = str(err)
            if attempt == max_attempts:
                return {
                    "success": False,
                    "product_url": product_url,
                    "product_name": product_name,
                    "price": None,
                    "currency": None,
                    "stock": None,
                    "attempts": attempt,
                    "error": last_error_msg,
                }
            time.sleep(2)

    return {
        "success": False,
        "product_url": product_url,
        "product_name": product_name,
        "price": None,
        "currency": None,
        "stock": None,
        "attempts": max_attempts,
        "error": last_error_msg,
    }
