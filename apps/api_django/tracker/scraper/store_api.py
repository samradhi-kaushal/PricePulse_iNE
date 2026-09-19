import time
import requests
from typing import List, Dict, Any, Optional
from django.utils.text import slugify

STORE_BASE_URL = "https://demo.inelabteamdev.com"

_catalog_cache: Optional[List[Dict[str, Any]]] = None
_catalog_cache_expiry: float = 0.0


def fetch_store_catalog() -> List[Dict[str, Any]]:
    global _catalog_cache, _catalog_cache_expiry
    now = time.time()
    if _catalog_cache is not None and now < _catalog_cache_expiry:
        return _catalog_cache

    response = requests.get(f"{STORE_BASE_URL}/api/catalog?page=1&pageSize=60", timeout=10)
    response.raise_for_status()
    data = response.json()
    items = data.get("items", [])
    
    _catalog_cache = items
    _catalog_cache_expiry = now + 120.0
    return items


def populate_catalogue() -> List[Any]:
    """
    Populates Product table from store catalog.
    Creates or updates Product records without triggering price scraping.
    """
    from tracker.models import Product

    items = fetch_store_catalog()
    products = []

    for item in items:
        ext_id = str(item.get("id"))
        name = item.get("name") or f"Product {ext_id}"
        brand = item.get("brand") or ""
        category = item.get("category") or ""
        sku = item.get("sku") or ""
        product_url = f"{STORE_BASE_URL}/product/{ext_id}"

        product, _ = Product.objects.update_or_create(
            external_id=ext_id,
            defaults={
                "name": name,
                "slug": slugify(name),
                "brand": brand,
                "category": category,
                "sku": sku,
                "product_url": product_url,
            }
        )
        products.append(product)

    return products


def fetch_single_store_product(external_id: str) -> Optional[Dict[str, Any]]:
    try:
        url = f"{STORE_BASE_URL}/api/product/{external_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return {
            "external_id": str(data.get("id")),
            "name": data.get("name"),
            "brand": data.get("brand") or "",
            "category": data.get("category") or "",
            "sku": data.get("sku") or "",
            "product_url": f"{STORE_BASE_URL}/product/{data.get('id')}",
        }
    except Exception:
        return None
