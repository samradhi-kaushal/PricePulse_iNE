from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from tracker.models import Product, TrackedProduct, PriceHistory, ScrapeLog
from tracker.scraper.parse import parse_price, parse_stock
from tracker.scraper.browser import ScraperError
from tracker.services.scrape_runner import execute_scrape_for_tracked_product, run_scrape_due_batch


class ScraperValidationAndServicesTest(TestCase):
    def setUp(self):
        self.p1 = Product.objects.create(
            external_id="1",
            name="Product A",
            product_url="https://demo.inelabteamdev.com/product/1"
        )
        self.p2 = Product.objects.create(
            external_id="2",
            name="Product B",
            product_url="https://demo.inelabteamdev.com/product/2"
        )
        self.tp1 = TrackedProduct.objects.create(product=self.p1, is_active=True)
        self.tp2 = TrackedProduct.objects.create(product=self.p2, is_active=True)

    def test_price_validation(self):
        self.assertEqual(parse_price("₹ 1,299.00"), Decimal("1299.00"))
        self.assertEqual(parse_price("1.299,00 €"), Decimal("1299.00"))
        self.assertIsNone(parse_price("0.00"))
        self.assertIsNone(parse_price("-50.00"))
        self.assertIsNone(parse_price("Call for price"))

    def test_stock_validation(self):
        self.assertEqual(parse_stock("Out of stock"), 0)
        self.assertEqual(parse_stock("Only 94 left in stock"), 94)
        self.assertIsNone(parse_stock("In Stock"))
        self.assertIsNone(parse_stock(""))

    @patch("tracker.services.scrape_runner._single_attempt_scrape")
    def test_successful_scrape_creates_price_history_and_log(self, mock_scrape):
        mock_scrape.return_value = {
            "product_name": "Product A",
            "price": Decimal("1500.00"),
            "currency": "INR",
            "stock": 10
        }

        res = execute_scrape_for_tracked_product(self.tp1)

        self.assertTrue(res["success"])
        self.assertEqual(PriceHistory.objects.filter(tracked_product=self.tp1).count(), 1)
        self.assertEqual(ScrapeLog.objects.filter(tracked_product=self.tp1).count(), 1)
        self.assertEqual(ScrapeLog.objects.first().status, "SUCCESS")

    @patch("tracker.services.scrape_runner._single_attempt_scrape")
    def test_failed_scrape_does_not_create_price_history(self, mock_scrape):
        mock_scrape.side_effect = ScraperError("STORE_TIMEOUT", "Timeout occurred", retryable=False)

        res = execute_scrape_for_tracked_product(self.tp1)

        self.assertFalse(res["success"])
        self.assertEqual(PriceHistory.objects.filter(tracked_product=self.tp1).count(), 0)
        self.assertEqual(ScrapeLog.objects.filter(tracked_product=self.tp1).count(), 1)
        self.assertEqual(ScrapeLog.objects.first().status, "FAILED")

    @patch("tracker.services.scrape_runner._single_attempt_scrape")
    def test_retry_behavior_creates_multiple_logs_and_single_price_history(self, mock_scrape):
        attempts_call = 0
        def side_effect(url, **kwargs):
            nonlocal attempts_call
            attempts_call += 1
            if attempts_call == 1:
                raise ScraperError("STORE_TEMPORARY_ERROR", "Temporary 500 error", retryable=True)
            return {"product_name": "Product A", "price": Decimal("1500.00"), "currency": "INR", "stock": 10}

        mock_scrape.side_effect = side_effect

        res = execute_scrape_for_tracked_product(self.tp1)

        self.assertTrue(res["success"])
        self.assertEqual(res["attempts"], 2)
        logs = ScrapeLog.objects.filter(tracked_product=self.tp1).order_by("attempt_number")
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs[0].status, "RETRIED")
        self.assertEqual(logs[1].status, "SUCCESS")
        self.assertEqual(PriceHistory.objects.filter(tracked_product=self.tp1).count(), 1)

    @patch("tracker.services.scrape_runner._single_attempt_scrape")
    def test_scrape_due_batch_continues_on_failure(self, mock_scrape):
        def side_effect(url, **kwargs):
            if "product/1" in url:
                raise ScraperError("STORE_TIMEOUT", "Failed p1", retryable=False)
            return {"product_name": "Product B", "price": Decimal("2000.00"), "currency": "INR", "stock": 5}

        mock_scrape.side_effect = side_effect

        batch_res = run_scrape_due_batch(limit=10)

        self.assertEqual(batch_res["due_count"], 2)
        self.assertEqual(batch_res["successful_count"], 1)
        self.assertEqual(batch_res["failed_count"], 1)
        self.assertEqual(ScrapeLog.objects.filter(tracked_product=self.tp1, status="FAILED").count(), 1)
        self.assertEqual(ScrapeLog.objects.filter(tracked_product=self.tp2, status="SUCCESS").count(), 1)
