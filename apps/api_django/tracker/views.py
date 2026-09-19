import os
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from django.utils import timezone as dj_timezone
from .models import Product, TrackedProduct, PriceHistory, ScrapeLog, ProductChange, Alert
from .serializers import (
    ProductSerializer,
    TrackedProductSerializer,
    PriceHistorySerializer,
    ScrapeLogSerializer,
    ProductChangeSerializer,
    AlertSerializer,
)
from .scraper.store_api import populate_catalogue, fetch_single_store_product
from .services.scrape_runner import execute_scrape_for_tracked_product, run_scrape_due_batch


class HealthView(APIView):
    def get(self, request):
        return Response({"ok": True})


class ProductListView(APIView):
    """GET /api/products/ - Search & list catalogue products."""
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        
        if not Product.objects.exists():
            populate_catalogue()

        products = Product.objects.all()
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query) |
                Q(sku__icontains=query) |
                Q(category__icontains=query)
            )

        serializer = ProductSerializer(products[:60], many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    """GET /api/products/<uuid:pk>/ - Single catalogue product."""
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)


class TrackedProductListView(APIView):
    """
    GET /api/tracked-products/ - List active tracked products
    POST /api/tracked-products/ - Track a product by product_id or external_id
    """
    def get(self, request):
        tracked = TrackedProduct.objects.filter(is_active=True)
        serializer = TrackedProductSerializer(tracked, many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        product_id = request.data.get("product_id") or request.data.get("sourceProductId") or request.data.get("productId")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        product = Product.objects.filter(Q(id=product_id) | Q(external_id=str(product_id))).first()
        if not product:
            meta = fetch_single_store_product(str(product_id))
            if not meta:
                return Response({"error": f"Product '{product_id}' not found"}, status=status.HTTP_404_NOT_FOUND)
            product = Product.objects.create(
                external_id=meta["external_id"],
                name=meta["name"],
                brand=meta["brand"],
                category=meta["category"],
                sku=meta["sku"],
                product_url=meta["product_url"]
            )

        tracked, created = TrackedProduct.objects.update_or_create(
            product=product,
            defaults={"is_active": True}
        )

        serializer = TrackedProductSerializer(tracked)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class TrackedProductDetailView(APIView):
    """
    GET /api/tracked-products/<uuid:pk>/
    PATCH /api/tracked-products/<uuid:pk>/ - Update scrape interval
    DELETE /api/tracked-products/<uuid:pk>/ - Untrack product
    """
    def get(self, request, pk):
        try:
            tracked = TrackedProduct.objects.get(pk=pk)
            serializer = TrackedProductSerializer(tracked)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TrackedProduct.DoesNotExist:
            return Response({"error": "Tracked product not found"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        try:
            tracked = TrackedProduct.objects.get(pk=pk)
            interval = request.data.get("scrape_interval_hours")
            if interval is not None:
                try:
                    interval = int(interval)
                except (ValueError, TypeError):
                    return Response({"error": "scrape_interval_hours must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

                if interval not in TrackedProduct.ALLOWED_INTERVALS:
                    return Response(
                        {"error": f"Allowed intervals are {TrackedProduct.ALLOWED_INTERVALS} hours"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                tracked.scrape_interval_hours = interval
                tracked.next_scrape_at = dj_timezone.now() + dj_timezone.timedelta(hours=interval)
                tracked.save()

            serializer = TrackedProductSerializer(tracked)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TrackedProduct.DoesNotExist:
            return Response({"error": "Tracked product not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            tracked = TrackedProduct.objects.get(pk=pk)
            tracked.is_active = False
            tracked.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TrackedProduct.DoesNotExist:
            return Response({"error": "Tracked product not found"}, status=status.HTTP_404_NOT_FOUND)


class TrackedProductHistoryView(APIView):
    """GET /api/tracked-products/<uuid:pk>/history/ - Price history for tracked product."""
    def get(self, request, pk):
        try:
            tracked = TrackedProduct.objects.get(pk=pk)
            history = PriceHistory.objects.filter(tracked_product=tracked)
            serializer = PriceHistorySerializer(history, many=True)
            return Response({"items": serializer.data}, status=status.HTTP_200_OK)
        except TrackedProduct.DoesNotExist:
            return Response({"error": "Tracked product not found"}, status=status.HTTP_404_NOT_FOUND)


class TrackedProductScrapesView(APIView):
    """GET /api/tracked-products/<uuid:pk>/scrapes/ - Scrape logs for tracked product."""
    def get(self, request, pk):
        try:
            tracked = TrackedProduct.objects.get(pk=pk)
            logs = ScrapeLog.objects.filter(tracked_product=tracked)
            serializer = ScrapeLogSerializer(logs, many=True)
            return Response({"items": serializer.data}, status=status.HTTP_200_OK)
        except TrackedProduct.DoesNotExist:
            return Response({"error": "Tracked product not found"}, status=status.HTTP_404_NOT_FOUND)


class TrackedProductManualScrapeView(APIView):
    """POST /api/tracked-products/<uuid:pk>/scrape/ - Manual scrape trigger."""
    def post(self, request, pk):
        try:
            tracked = TrackedProduct.objects.get(pk=pk)
            res = execute_scrape_for_tracked_product(tracked, headless=True)
            tracked.refresh_from_db()
            serializer = TrackedProductSerializer(tracked)
            return Response({
                "scrape_result": res,
                "tracked_product": serializer.data
            }, status=status.HTTP_200_OK if res["success"] else status.HTTP_500_INTERNAL_SERVER_ERROR)
        except TrackedProduct.DoesNotExist:
            return Response({"error": "Tracked product not found"}, status=status.HTTP_404_NOT_FOUND)


class AllScrapeLogsView(APIView):
    """GET /api/scrapes/ - Global scrape logs for dedicated Scrape Activity page."""
    def get(self, request):
        logs = ScrapeLog.objects.select_related("tracked_product__product").all()[:100]
        serializer = ScrapeLogSerializer(logs, many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)


class AlertListView(APIView):
    """
    GET /api/alerts/ - List alerts
    """
    def get(self, request):
        unread_only = request.query_params.get("unread", "").lower() in ("true", "1")
        alerts = Alert.objects.select_related("tracked_product__product")
        if unread_only:
            alerts = alerts.filter(is_read=False)
        serializer = AlertSerializer(alerts[:50], many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)


class AlertUnreadCountView(APIView):
    """GET /api/alerts/unread-count/ - Unread alert counter."""
    def get(self, request):
        unread_count = Alert.objects.filter(is_read=False).count()
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


class AlertMarkReadView(APIView):
    """POST /api/alerts/<uuid:pk>/read/ - Mark a single alert as read."""
    def post(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
            alert.is_read = True
            alert.save()
            return Response(AlertSerializer(alert).data, status=status.HTTP_200_OK)
        except Alert.DoesNotExist:
            return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)


class AlertMarkAllReadView(APIView):
    """POST /api/alerts/read-all/ - Mark all alerts as read."""
    def post(self, request):
        updated_count = Alert.objects.filter(is_read=False).update(is_read=True)
        return Response({"marked_read": updated_count}, status=status.HTTP_200_OK)


class ProductChangeListView(APIView):
    """GET /api/changes/ - Global change detection log."""
    def get(self, request):
        changes = ProductChange.objects.select_related("tracked_product__product").all()[:100]
        serializer = ProductChangeSerializer(changes, many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)


class TrackedProductChangesView(APIView):
    """GET /api/tracked-products/<uuid:pk>/changes/ - Product-specific change history."""
    def get(self, request, pk):
        try:
            tracked = TrackedProduct.objects.get(pk=pk)
            changes = ProductChange.objects.filter(tracked_product=tracked)
            serializer = ProductChangeSerializer(changes, many=True)
            return Response({"items": serializer.data}, status=status.HTTP_200_OK)
        except TrackedProduct.DoesNotExist:
            return Response({"error": "Tracked product not found"}, status=status.HTTP_404_NOT_FOUND)


class DashboardView(APIView):
    """GET /api/dashboard/ - Real aggregated statistics, multi-product overview, and recent activity."""
    def get(self, request):
        tracked_products = TrackedProduct.objects.filter(is_active=True).select_related("product")
        tracked_count = tracked_products.count()
        success_count = ScrapeLog.objects.filter(status="SUCCESS").count()
        retried_count = ScrapeLog.objects.filter(status="RETRIED").count()
        failed_count = ScrapeLog.objects.filter(status="FAILED").count()
        unread_alert_count = Alert.objects.filter(is_read=False).count()

        recent_tracked = tracked_products.order_by("-created_at")[:10]
        recent_scrapes = ScrapeLog.objects.select_related("tracked_product__product").all()[:10]
        recent_changes = ProductChange.objects.select_related("tracked_product__product").all()[:5]
        recent_alerts = Alert.objects.select_related("tracked_product__product").all()[:5]

        return Response({
            "tracked_product_count": tracked_count,
            "successful_scrape_count": success_count,
            "retry_count": retried_count,
            "failed_scrape_count": failed_count,
            "unread_alert_count": unread_alert_count,
            "recent_tracked_products": TrackedProductSerializer(recent_tracked, many=True).data,
            "recent_scrape_activity": ScrapeLogSerializer(recent_scrapes, many=True).data,
            "recent_changes": ProductChangeSerializer(recent_changes, many=True).data,
            "recent_alerts": AlertSerializer(recent_alerts, many=True).data,
        }, status=status.HTTP_200_OK)


class ScrapeDueView(APIView):
    """POST /api/jobs/scrape-due - Cron trigger calling run_scrape_due_batch()."""
    def post(self, request):
        auth_header = request.headers.get("Authorization", "")
        secret = auth_header.replace("Bearer ", "").strip()
        expected_secret = os.environ.get("CRON_SECRET", "replace-with-a-long-random-value")

        if not secret or secret != expected_secret:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        batch_result = run_scrape_due_batch(limit=10)
        return Response(batch_result, status=status.HTTP_200_OK)


