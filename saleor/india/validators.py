from __future__ import annotations

import re
from copy import deepcopy
from decimal import Decimal
from typing import Any, Dict, Iterable

from prices import Money

from saleor.core.prices import MAXIMUM_PRICE, quantize_price


_GSTIN_RE = re.compile(r"^(?P<state>\d{2})(?P<pan>[A-Z]{5}\d{4}[A-Z])(?P<entity>[A-Z0-9])Z(?P<check>[A-Z0-9])$")
_PINCODE_RE = re.compile(r"^[1-9][0-9]{5}$")
_UPI_VPA_RE = re.compile(r"^[a-zA-Z0-9._\-]{2,256}@[a-zA-Z]{3,64}$")


def validate_currency_inr(currency: str) -> None:
    if currency != "INR":
        raise ValueError("Only INR currency is supported in Saleor India module")


def validate_money_is_inr(amount: Money) -> None:
    validate_currency_inr(amount.currency)


def validate_decimal_non_negative(value: Decimal, *, field_name: str) -> None:
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be non-negative")


def validate_decimal_positive(value: Decimal, *, field_name: str) -> None:
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")


def validate_pincode(pincode: str) -> None:
    if not _PINCODE_RE.match(pincode or ""):
        raise ValueError("Invalid Indian PIN code format")


def validate_gstin(gstin: str) -> None:
    """Validate GSTIN format. Pattern validation only (checksum not enforced)."""
    if not gstin:
        return
    if not _GSTIN_RE.match(gstin):
        raise ValueError("Invalid GSTIN format")


def validate_upi_vpa(vpa: str) -> None:
    if not _UPI_VPA_RE.match(vpa or ""):
        raise ValueError("Invalid UPI VPA format")


def sanitize_for_logging(data: Dict[str, Any], *, redact_keys: Iterable[str] | None = None) -> Dict[str, Any]:
    """Return a deep-copied dict with sensitive keys redacted.

    This prevents leaking sensitive financial data in logs.
    """
    if data is None:
        return {}
    redacted: Dict[str, Any] = deepcopy(data)
    keys_to_redact = set(k.lower() for k in (redact_keys or [])) | {"upi_vpa", "vpa", "card", "token"}

    def _redact(obj: Any) -> Any:
        if isinstance(obj, dict):
            new_obj: Dict[str, Any] = {}
            for key, value in obj.items():
                if key.lower() in keys_to_redact:
                    new_obj[key] = "***"
                else:
                    new_obj[key] = _redact(value)
            return new_obj
        elif isinstance(obj, list):
            return [_redact(v) for v in obj]
        return obj

    return _redact(redacted)


def clamp_discount_amount(amount: Money, *, max_value: Money) -> Money:
    if amount.currency != max_value.currency:
        raise ValueError("Currency mismatch when clamping discount")
    if amount.amount > Decimal(MAXIMUM_PRICE):
        amount = Money(Decimal(MAXIMUM_PRICE), amount.currency)
    if amount > max_value:
        return quantize_price(max_value, max_value.currency)
    return quantize_price(amount, amount.currency)


