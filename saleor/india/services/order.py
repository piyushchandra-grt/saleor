from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Tuple

from prices import Money

from ..errors import ValidationError
from ..types import OrderInput
from ..validators import (
    validate_gstin,
    validate_money_is_inr,
    validate_pincode,
)


def _validate_address(address) -> None:
    if not address.first_name or not address.last_name:
        raise ValidationError("Name is required")
    if not address.street_address_1:
        raise ValidationError("Street address is required")
    if not address.city or not address.state_code:
        raise ValidationError("City and state code are required")
    try:
        validate_pincode(address.postal_code)
        if address.gstin:
            validate_gstin(address.gstin)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def _calculate_items_total(order: OrderInput) -> Money:
    total_amount = Decimal("0.00")
    currency = "INR"
    for item in order.items:
        validate_money_is_inr(item.unit_price)
        currency = item.unit_price.currency
        if item.quantity <= 0:
            raise ValidationError("Item quantity must be positive")
        total_amount += item.unit_price.amount * item.quantity
    return Money(total_amount, currency)


def create_order(order: OrderInput) -> Tuple[OrderInput, Money]:
    """Validate addresses and totals for an India order and return normalized input.

    No DB writes here; this is a pure function suitable for unit testing and reuse.
    Returns the original order input and computed items total (Money in INR).
    """
    _validate_address(order.shipping_address)
    _validate_address(order.billing_address)

    total = _calculate_items_total(order)
    return order, total


