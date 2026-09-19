from django.test import TestCase
from tracker.models import Product, TrackedProduct, PriceHistory, ScrapeLog


class ModelTest(TestCase):
    def test_product_creation_and_slug(self):
        prod = Product.objects.create(
            external_id="101",
            name="Test Headphones",
            brand="AudioBrand",
            category="Audio",
            sku="AUDIO-101",
            product_url="https://demo.inelabteamdev.com/product/101"
        )
        self.assertEqual(str(prod), "Test Headphones (101)")
        self.assertEqual(prod.slug, "test-headphones")

    def test_tracked_product_relationship(self):
        prod = Product.objects.create(
            external_id="102",
            name="Test Monitor",
            product_url="https://demo.inelabteamdev.com/product/102"
        )
        tracked = TrackedProduct.objects.create(product=prod, is_active=True)
        self.assertTrue(tracked.is_active)
        self.assertEqual(prod.tracking, tracked)

    def test_price_history_and_scrape_log(self):
        prod = Product.objects.create(
            external_id="103",
            name="Test Keyboard",
            product_url="https://demo.inelabteamdev.com/product/103"
        )
        tracked = TrackedProduct.objects.create(product=prod)

        history = PriceHistory.objects.create(
            tracked_product=tracked,
            price=1499.00,
            currency="INR",
            stock=12
        )
        self.assertEqual(history.tracked_product, tracked)

        log = ScrapeLog.objects.create(
            tracked_product=tracked,
            attempt_number=1,
            status="SUCCESS",
            duration_ms=450
        )
        self.assertEqual(log.status, "SUCCESS")
