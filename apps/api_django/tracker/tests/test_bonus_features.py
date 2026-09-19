from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone as dj_timezone
from rest_framework.test import APIClient
from rest_framework import status

from tracker.models import Product, TrackedProduct, PriceHistory, ScrapeLog, ProductChange, Alert
from tracker.services.scrape_runner import execute_scrape_for_tracked_product, run_scrape_due_batch


class BonusFeaturesTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.product1 = Product.objects.create(
            external_id="101",
            name="Field Monitor X",
            brand="Amperage",
            category="Video",
            sku="AMP-FMX-101",
            product_url="https://demo.inelabteamdev.com/product/101"
        )
        self.product2 = Product.objects.create(
            external_id="102",
            name="Field Monitor Y",
            brand="Amperage",
            category="Video",
            sku="AMP-FMY-102",
            product_url="https://demo.inelabteamdev.com/product/102"
        )
        self.tracked1 = TrackedProduct.objects.create(product=self.product1, is_active=True, scrape_interval_hours=2)
        self.tracked2 = TrackedProduct.objects.create(product=self.product2, is_active=True, scrape_interval_hours=6)

    @patch("tracker.services.scrape_runner._single_attempt_scrape")
    def test_change_detection_and_alerts_on_price_drop(self, mock_scrape):
        mock_scrape.return_value = {
            "product_name": "Field Monitor X",
            "price": Decimal("28000.00"),
            "currency": "INR",
            "stock": 100
        }
        res1 = execute_scrape_for_tracked_product(self.tracked1)
        self.assertTrue(res1["success"])
        self.assertEqual(ProductChange.objects.count(), 0)
        self.assertEqual(Alert.objects.count(), 0)

        mock_scrape.return_value = {
            "product_name": "Field Monitor X",
            "price": Decimal("25000.00"),
            "currency": "INR",
            "stock": 100
        }
        res2 = execute_scrape_for_tracked_product(self.tracked1)
        self.assertTrue(res2["success"])
        self.assertEqual(ProductChange.objects.count(), 1)
        chg = ProductChange.objects.first()
        self.assertEqual(chg.change_type, "PRICE_DECREASE")
        self.assertEqual(chg.previous_value, "28000.00")
        self.assertEqual(chg.current_value, "25000.00")

        self.assertEqual(Alert.objects.count(), 1)
        alt = Alert.objects.first()
        self.assertEqual(alt.alert_type, "PRICE_DECREASE")
        self.assertFalse(alt.is_read)

    @patch("tracker.services.scrape_runner._single_attempt_scrape")
    def test_stock_change_detection_and_alerts(self, mock_scrape):
        mock_scrape.return_value = {
            "product_name": "Field Monitor Y",
            "price": Decimal("10000.00"),
            "currency": "INR",
            "stock": 50
        }
        execute_scrape_for_tracked_product(self.tracked2)

        mock_scrape.return_value = {
            "product_name": "Field Monitor Y",
            "price": Decimal("10000.00"),
            "currency": "INR",
            "stock": 20
        }
        execute_scrape_for_tracked_product(self.tracked2)

        self.assertEqual(ProductChange.objects.count(), 1)
        self.assertEqual(ProductChange.objects.first().change_type, "STOCK_DECREASE")
        self.assertEqual(Alert.objects.count(), 1)
        self.assertEqual(Alert.objects.first().alert_type, "STOCK_DECREASE")

    @patch("tracker.services.scrape_runner._single_attempt_scrape")
    def test_failed_scrape_generates_no_changes_or_alerts(self, mock_scrape):
        from tracker.scraper.browser import ScraperError
        mock_scrape.side_effect = ScraperError("TIMEOUT", "Store offline", retryable=False)

        res = execute_scrape_for_tracked_product(self.tracked1)
        self.assertFalse(res["success"])
        self.assertEqual(PriceHistory.objects.count(), 0)
        self.assertEqual(ProductChange.objects.count(), 0)
        self.assertEqual(Alert.objects.count(), 0)

    def test_alert_api_endpoints(self):
        chg = ProductChange.objects.create(
            tracked_product=self.tracked1,
            change_type="PRICE_DECREASE",
            previous_value="2000",
            current_value="1500"
        )
        alert1 = Alert.objects.create(
            tracked_product=self.tracked1,
            change_event=chg,
            alert_type="PRICE_DECREASE",
            title="Price dropped",
            message="2000 -> 1500"
        )

        res_cnt = self.client.get(reverse("alert-unread-count"))
        self.assertEqual(res_cnt.status_code, status.HTTP_200_OK)
        self.assertEqual(res_cnt.json()["unread_count"], 1)

        res_read = self.client.post(reverse("alert-mark-read", kwargs={"pk": alert1.pk}))
        self.assertEqual(res_read.status_code, status.HTTP_200_OK)
        alert1.refresh_from_db()
        self.assertTrue(alert1.is_read)

        res_all = self.client.post(reverse("alert-mark-all-read"))
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)

    def test_configurable_scrape_frequency(self):
        res = self.client.patch(
            reverse("tracked-product-detail", kwargs={"pk": self.tracked1.pk}),
            data={"scrape_interval_hours": 12},
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.tracked1.refresh_from_db()
        self.assertEqual(self.tracked1.scrape_interval_hours, 12)

        res_bad = self.client.patch(
            reverse("tracked-product-detail", kwargs={"pk": self.tracked1.pk}),
            data={"scrape_interval_hours": 99},
            format="json"
        )
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_multi_product_response(self):
        res = self.client.get(reverse("dashboard"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["tracked_product_count"], 2)
        self.assertIn("unread_alert_count", data)
        self.assertIn("recent_changes", data)
        self.assertIn("recent_alerts", data)
