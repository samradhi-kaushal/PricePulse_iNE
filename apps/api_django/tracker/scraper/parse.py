import re
from decimal import Decimal, InvalidOperation
from typing import Optional

FULLWIDTH_MAP = str.maketrans("０１２３４５６７８９", "0123456789")

CURRENCY_SYMBOLS = {
    "₹": "INR",
    "INR": "INR",
    "$": "USD",
    "USD": "USD",
    "€": "EUR",
    "EUR": "EUR",
    "£": "GBP",
    "GBP": "GBP",
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.translate(FULLWIDTH_MAP)
    text = re.sub(r'[\u00A0\u200B\u200C\u200D\uFEFF]', ' ', text)
    return text.strip()


def parse_currency(text: str) -> Optional[str]:
    cleaned = clean_text(text)
    for sym, code in CURRENCY_SYMBOLS.items():
        if sym in cleaned:
            return code
    return None


def parse_price(text: str) -> Optional[Decimal]:
    """
    Parses and validates current selling price.
    Must be > 0. Rejects missing, NaN, or non-positive values.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return None

    numeric_part = re.sub(r'[^\d.,-]', '', cleaned)
    if not numeric_part:
        return None

    if ',' in numeric_part and '.' in numeric_part:
        if numeric_part.rfind(',') > numeric_part.rfind('.'):
            numeric_part = numeric_part.replace('.', '').replace(',', '.')
        else:
            numeric_part = numeric_part.replace(',', '')
    elif ',' in numeric_part:
        if re.search(r',\d{2}$', numeric_part):
            numeric_part = numeric_part.replace(',', '.')
        else:
            numeric_part = numeric_part.replace(',', '')

    try:
        val = Decimal(numeric_part)
        if val <= 0:
            return None
        return val.quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None


def parse_stock(text: str) -> Optional[int]:
    """
    Parses stock count from isolated stock text:
    - Explicit out-of-stock ("out of stock", "sold out", "currently unavailable") -> 0
    - Explicit numeric stock ("49 left", "hurry, just 49 left", "49 units in stock", "stock: 49") -> 49
    - Unknown / unquantified stock ("in stock") -> None (does NOT convert to 1 or arbitrary number)
    """
    cleaned = clean_text(text).lower()
    if not cleaned:
        return None

    if any(phrase in cleaned for phrase in ["out of stock", "sold out", "currently unavailable"]):
        return 0

    match = re.search(r'(\d+)\s*(?:left|in stock|available|units)', cleaned)
    if match:
        return int(match.group(1))

    match_prefix = re.search(r'(?:stock|left|available)[:\s]*(\d+)', cleaned)
    if match_prefix:
        return int(match_prefix.group(1))

    if cleaned.isdigit():
        return int(cleaned)

    return None
