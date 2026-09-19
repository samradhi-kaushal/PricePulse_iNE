import uuid
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    brand = models.CharField(max_length=100, blank=True, default="")
    category = models.CharField(max_length=100, blank=True, default="")
    sku = models.CharField(max_length=100, blank=True, default="")
    product_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.external_id})"


class TrackedProduct(models.Model):
    ALLOWED_INTERVALS = [2, 4, 6, 12, 24]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="tracking",
    )
    is_active = models.BooleanField(default=True)
    scrape_interval_hours = models.IntegerField(default=2)
    next_scrape_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Tracking {self.product.name} [Active={self.is_active}, Every {self.scrape_interval_hours}h]"


class PriceHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tracked_product = models.ForeignKey(
        TrackedProduct,
        on_delete=models.CASCADE,
        related_name="price_history",
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    stock = models.IntegerField(null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.currency} {self.price} (Stock: {self.stock}) @ {self.recorded_at}"


class ProductChange(models.Model):
    CHANGE_TYPES = [
        ("PRICE_INCREASE", "PRICE_INCREASE"),
        ("PRICE_DECREASE", "PRICE_DECREASE"),
        ("STOCK_INCREASE", "STOCK_INCREASE"),
        ("STOCK_DECREASE", "STOCK_DECREASE"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tracked_product = models.ForeignKey(
        TrackedProduct,
        on_delete=models.CASCADE,
        related_name="changes",
    )
    change_type = models.CharField(max_length=30, choices=CHANGE_TYPES)
    previous_value = models.CharField(max_length=100, null=True, blank=True)
    current_value = models.CharField(max_length=100, null=True, blank=True)
    detected_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.change_type} for {self.tracked_product.product.name}: {self.previous_value} -> {self.current_value}"


class Alert(models.Model):
    ALERT_TYPES = [
        ("PRICE_DECREASE", "PRICE_DECREASE"),
        ("PRICE_INCREASE", "PRICE_INCREASE"),
        ("STOCK_DECREASE", "STOCK_DECREASE"),
        ("STOCK_INCREASE", "STOCK_INCREASE"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tracked_product = models.ForeignKey(
        TrackedProduct,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    change_event = models.ForeignKey(
        ProductChange,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="alerts",
    )
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{'READ' if self.is_read else 'UNREAD'}] {self.title}"


class ScrapeLog(models.Model):
    STATUS_CHOICES = [
        ("SUCCESS", "SUCCESS"),
        ("RETRIED", "RETRIED"),
        ("FAILED", "FAILED"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tracked_product = models.ForeignKey(
        TrackedProduct,
        on_delete=models.CASCADE,
        related_name="scrape_logs",
    )
    attempted_at = models.DateTimeField(default=timezone.now)
    attempt_number = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_code = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self):
        return f"Attempt {self.attempt_number} for {self.tracked_product.product.name} [{self.status}]"

