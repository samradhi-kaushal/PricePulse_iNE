from rest_framework import serializers
from .models import Product, TrackedProduct, PriceHistory, ScrapeLog, ProductChange, Alert


class ProductSerializer(serializers.ModelSerializer):
    is_tracked = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "external_id",
            "name",
            "slug",
            "brand",
            "category",
            "sku",
            "product_url",
            "created_at",
            "updated_at",
            "is_tracked",
        ]

    def get_is_tracked(self, obj):
        return hasattr(obj, "tracking") and obj.tracking.is_active


class PriceHistorySerializer(serializers.ModelSerializer):
    tracked_product_id = serializers.UUIDField(source="tracked_product.id", read_only=True)
    price = serializers.FloatField()

    class Meta:
        model = PriceHistory
        fields = ["id", "tracked_product_id", "price", "currency", "stock", "recorded_at"]


class ScrapeLogSerializer(serializers.ModelSerializer):
    tracked_product_id = serializers.UUIDField(source="tracked_product.id", read_only=True)
    product_name = serializers.CharField(source="tracked_product.product.name", read_only=True)
    product_external_id = serializers.CharField(source="tracked_product.product.external_id", read_only=True)

    class Meta:
        model = ScrapeLog
        fields = [
            "id",
            "tracked_product_id",
            "product_name",
            "product_external_id",
            "attempted_at",
            "attempt_number",
            "status",
            "error_code",
            "error_message",
            "duration_ms",
        ]


class ProductChangeSerializer(serializers.ModelSerializer):
    tracked_product_id = serializers.UUIDField(source="tracked_product.id", read_only=True)
    product_name = serializers.CharField(source="tracked_product.product.name", read_only=True)

    class Meta:
        model = ProductChange
        fields = [
            "id",
            "tracked_product_id",
            "product_name",
            "change_type",
            "previous_value",
            "current_value",
            "detected_at",
        ]


class AlertSerializer(serializers.ModelSerializer):
    tracked_product_id = serializers.UUIDField(source="tracked_product.id", read_only=True)
    product_name = serializers.CharField(source="tracked_product.product.name", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id",
            "tracked_product_id",
            "product_name",
            "alert_type",
            "title",
            "message",
            "is_read",
            "created_at",
        ]


class TrackedProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    latest_price = serializers.SerializerMethodField()
    latest_scrape = serializers.SerializerMethodField()
    scrape_interval_hours = serializers.IntegerField(required=False)

    class Meta:
        model = TrackedProduct
        fields = [
            "id",
            "product",
            "is_active",
            "scrape_interval_hours",
            "next_scrape_at",
            "created_at",
            "updated_at",
            "latest_price",
            "latest_scrape",
        ]

    def validate_scrape_interval_hours(self, value):
        if value not in TrackedProduct.ALLOWED_INTERVALS:
            raise serializers.ValidationError(
                f"Interval must be one of {TrackedProduct.ALLOWED_INTERVALS} hours."
            )
        return value

    def get_latest_price(self, obj):
        latest = PriceHistory.objects.filter(tracked_product=obj).order_by("-recorded_at").first()
        return PriceHistorySerializer(latest).data if latest else None

    def get_latest_scrape(self, obj):
        latest = ScrapeLog.objects.filter(tracked_product=obj).order_by("-attempted_at").first()
        return ScrapeLogSerializer(latest).data if latest else None

