from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from tracker.models import Product, TrackedProduct, PriceHistory, ScrapeLog



class ViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(
            external_id="1",
            name="Nordkraft Headphones Pro",
            brand="Nordkraft",
            category="Audio",
            sku="NK-HP-01",
            product_url="https://demo.inelabteamdev.com/product/1"
        )
        self.tracked = TrackedProduct.objects.create(product=self.product, is_active=True)

    def test_health_check(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"ok": True})

    def test_product_list_and_search(self):
        response = self.client.get(reverse("product-list"), {"q": "Nordkraft"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.json().get("items", [])
        self.assertGreaterEqual(len(items), 1)

    def test_tracked_product_list_and_post(self):
        response = self.client.get(reverse("tracked-product-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.json().get("items", [])
        self.assertEqual(len(items), 1)

    def test_tracked_product_detail_and_delete(self):
        response = self.client.get(reverse("tracked-product-detail", kwargs={"pk": self.tracked.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        del_resp = self.client.delete(reverse("tracked-product-detail", kwargs={"pk": self.tracked.pk}))
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.tracked.refresh_from_db()
        self.assertFalse(self.tracked.is_active)

    def test_dashboard_endpoint(self):
        PriceHistory.objects.create(tracked_product=self.tracked, price=5000, currency="INR", stock=10)
        ScrapeLog.objects.create(tracked_product=self.tracked, attempt_number=1, status="SUCCESS", duration_ms=200)

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["tracked_product_count"], 1)
        self.assertEqual(data["successful_scrape_count"], 1)

    @patch("tracker.views.run_scrape_due_batch")
    def test_scrape_due_authentication(self, mock_batch):
        mock_batch.return_value = {
            "ok": True,
            "due_count": 0,
            "processed": 0,
            "successful_count": 0,
            "succeeded": 0,
            "retried_count": 0,
            "failed_count": 0,
            "failed": 0,
            "results": []
        }

        res_missing = self.client.post(reverse("scrape-due"))
        self.assertEqual(res_missing.status_code, status.HTTP_401_UNAUTHORIZED)

        res_wrong = self.client.post(
            reverse("scrape-due"),
            headers={"Authorization": "Bearer wrong-secret"}
        )
        self.assertEqual(res_wrong.status_code, status.HTTP_401_UNAUTHORIZED)

        valid_secret = "replace-with-a-long-random-value"
        res_valid = self.client.post(
            reverse("scrape-due"),
            headers={"Authorization": f"Bearer {valid_secret}"}
        )
        self.assertEqual(res_valid.status_code, status.HTTP_200_OK)
        data = res_valid.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("processed", data)
        self.assertIn("succeeded", data)
        self.assertIn("failed", data)


