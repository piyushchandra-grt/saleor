from __future__ import annotations

from decimal import Decimal

from prices import Money

from ..errors import ValidationError
from ..types import DiscountInput, DiscountResult
from ..validators import (
    clamp_discount_amount,
    validate_currency_inr,
    validate_decimal_non_negative,
    validate_decimal_positive,
)


def apply_discount(base_total: Money, discount: DiscountInput) -> DiscountResult:
    """Apply INR discounts with optional cap.

    - Supports percentage or absolute amount
    - Validates INR currency
    - Clamps discount not to exceed provided max_amount
    - Always returns quantized Money amounts
    """
    validate_currency_inr(base_total.currency)
    validate_currency_inr(discount.currency)
    if base_total.amount < Decimal("0"):
        raise ValidationError("Base total cannot be negative")

    if discount.type == "PERCENTAGE":
        validate_decimal_non_negative(discount.value, field_name="discount.value")
        if discount.value > Decimal("100"):
            raise ValidationError("Percentage discount cannot exceed 100")
        amount = (base_total.amount * discount.value) / Decimal("100")
        discount_amount = Money(amount, base_total.currency)
    elif discount.type == "AMOUNT":
        validate_decimal_positive(discount.value, field_name="discount.value")
        discount_amount = Money(discount.value, base_total.currency)
    else:
        raise ValidationError("Unsupported discount type")

    if discount.max_amount is not None:
        if discount.max_amount.currency != base_total.currency:
            raise ValidationError("max_amount currency mismatch")
        discount_amount = clamp_discount_amount(discount_amount, max_value=discount.max_amount)

    if discount_amount.amount > base_total.amount:
        discount_amount = Money(base_total.amount, base_total.currency)

    final = Money(base_total.amount - discount_amount.amount, base_total.currency)
    return DiscountResult(base_total=base_total, discount_applied=discount_amount, final_total=final)


