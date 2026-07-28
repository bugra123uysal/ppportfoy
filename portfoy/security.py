"""Input validation and output escaping.

Every value that comes from the user (form inputs) or from the network
(news feeds) passes through this module before it is stored or rendered.
"""

from __future__ import annotations

import html
import re
import unicodedata
from urllib.parse import urlparse

# Yahoo Finance style symbols: AAPL, BRK-B, XU100.IS, GC=F, ^GSPC, TRY=X
_SYMBOL_RE = re.compile(r"^[\^]?[A-Z0-9][A-Z0-9.\-=]{0,14}$")

MAX_QUANTITY = 1e9
MAX_PRICE = 1e9
MAX_CASH = 1e12
MAX_NOTE_LEN = 300
CURRENCIES = ("TRY", "USD")

_TR_MAP = str.maketrans("ıiğüşöç", "IIGUSOC")


class ValidationError(ValueError):
    """Raised when a user-supplied value fails validation."""


def normalize_symbol(raw: str) -> str:
    """Uppercase, trim and validate a ticker symbol. Raises ValidationError."""
    if not isinstance(raw, str):
        raise ValidationError("Sembol metin olmalı / symbol must be text")
    cleaned = raw.strip().translate(_TR_MAP).upper()
    if not cleaned:
        raise ValidationError("Sembol boş olamaz / symbol is empty")
    if not _SYMBOL_RE.match(cleaned):
        raise ValidationError(f"Geçersiz sembol / invalid symbol: {raw!r}")
    return cleaned


def validate_quantity(value: float) -> float:
    qty = _to_finite_float(value, "adet/quantity")
    if not 0 < qty <= MAX_QUANTITY:
        raise ValidationError("Adet 0 ile 1e9 arasında olmalı")
    return qty


def validate_price(value: float) -> float:
    price = _to_finite_float(value, "fiyat/price")
    if not 0 < price <= MAX_PRICE:
        raise ValidationError("Fiyat 0 ile 1e9 arasında olmalı")
    return price


def validate_cash(value: float) -> float:
    """Cash may be zero (an emptied balance) but never negative."""
    amount = _to_finite_float(value, "nakit/cash")
    if not 0 <= amount <= MAX_CASH:
        raise ValidationError("Nakit 0 ile 1e12 arasında olmalı")
    return amount


def validate_currency(raw: str) -> str:
    if not isinstance(raw, str):
        raise ValidationError("Para birimi metin olmalı / currency must be text")
    cleaned = raw.strip().translate(_TR_MAP).upper()
    if cleaned not in CURRENCIES:
        raise ValidationError(f"Desteklenmeyen para birimi / unsupported currency: {raw!r}")
    return cleaned


def sanitize_note(raw: str) -> str:
    """Strip control characters and cap the length of a free-text note."""
    if not isinstance(raw, str):
        return ""
    cleaned = "".join(
        ch for ch in raw if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t")
    )
    return cleaned.strip()[:MAX_NOTE_LEN]


def escape_html(raw: str) -> str:
    """Escape text before it is embedded in our HTML card markup."""
    return html.escape(str(raw), quote=True)


def is_safe_url(raw: str) -> bool:
    """Only allow absolute http(s) links (news articles)."""
    if not isinstance(raw, str) or len(raw) > 2048:
        return False
    try:
        parsed = urlparse(raw)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _to_finite_float(value: object, label: str) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Sayısal değer bekleniyor: {label}") from exc
    if result != result or result in (float("inf"), float("-inf")):
        raise ValidationError(f"Geçersiz sayı: {label}")
    return result
