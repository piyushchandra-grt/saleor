from decimal import Decimal

import pytest
from prices import Money

from saleor.india.services.discount import apply_discount
from saleor.india.types import DiscountInput
from saleor.india.errors import ValidationError


def test_apply_percentage_discount_with_cap():
    base = Money(Decimal("100.00"), "INR")
    discount = DiscountInput(type="PERCENTAGE", value=Decimal("20"), currency="INR", max_amount=Money(Decimal("15.00"), "INR"))

    result = apply_discount(base, discount)
    assert result.base_total == base
    # 20% of 100 is 20, but cap is 15
    assert result.discount_applied == Money(Decimal("15.00"), "INR")
    assert result.final_total == Money(Decimal("85.00"), "INR")


def test_apply_amount_discount_no_cap():
    base = Money(Decimal("50.00"), "INR")
    discount = DiscountInput(type="AMOUNT", value=Decimal("5.50"), currency="INR")
    result = apply_discount(base, discount)
    assert result.discount_applied == Money(Decimal("5.50"), "INR")
    assert result.final_total == Money(Decimal("44.50"), "INR")


def test_apply_amount_discount_exceeds_base():
    base = Money(Decimal("10.00"), "INR")
    discount = DiscountInput(type="AMOUNT", value=Decimal("25.00"), currency="INR")
    result = apply_discount(base, discount)
    assert result.discount_applied == Money(Decimal("10.00"), "INR")
    assert result.final_total == Money(Decimal("0.00"), "INR")


def test_currency_mismatch():
    base = Money(Decimal("10.00"), "INR")
    discount = DiscountInput(type="AMOUNT", value=Decimal("5.00"), currency="USD")
    with pytest.raises(ValueError):
        apply_discount(base, discount)


