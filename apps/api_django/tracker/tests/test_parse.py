from decimal import Decimal
from tracker.scraper.parse import parse_price, parse_currency, parse_stock, clean_text


def test_clean_text():
    raw = "  ₹\u00A01,299.00\u200B  "
    assert clean_text(raw) == "₹ 1,299.00"


def test_parse_currency():
    assert parse_currency("₹ 1,299.00") == "INR"
    assert parse_currency("$ 49.99") == "USD"
    assert parse_currency("1.299,00 €") == "EUR"
    assert parse_currency("£ 10.00") == "GBP"
    assert parse_currency("1299") is None


def test_parse_price_standard_indian():
    assert parse_price("₹ 1,299.00") == Decimal("1299.00")
    assert parse_price("₹1,29,900.50") == Decimal("129900.50")
    assert parse_price("1299") == Decimal("1299.00")


def test_parse_price_european():
    assert parse_price("1.299,00 €") == Decimal("1299.00")


def test_parse_price_invalid():
    assert parse_price("Price on request") is None
    assert parse_price("0.00") is None
    assert parse_price("-50.00") is None
    assert parse_price("") is None


def test_parse_stock():
    assert parse_stock("In Stock (5 left)") == 5
    assert parse_stock("Currently Out of Stock") == 0
    assert parse_stock("In Stock") is None
    assert parse_stock("Unknown status") is None
