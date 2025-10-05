from decimal import Decimal

import pytest
from prices import Money

from saleor.india.types import AddressIN, OrderInput, OrderItem
from saleor.india.services.order import create_order
from saleor.india.errors import ValidationError


def _addr(gstin: str | None = None) -> AddressIN:
    return AddressIN(
        first_name="A",
        last_name="B",
        street_address_1="Line 1",
        street_address_2=None,
        city="Mumbai",
        state_code="MH",
        postal_code="400001",
        gstin=gstin,
    )


def test_create_order_success():
    order = OrderInput(
        order_id="ORD1",
        items=[
            OrderItem(name="x", quantity=2, unit_price=Money(Decimal("10.00"), "INR")),
            OrderItem(name="y", quantity=1, unit_price=Money(Decimal("5.00"), "INR")),
        ],
        shipping_address=_addr("27ABCDE1234F1Z5"),
        billing_address=_addr(),
    )

    out, total = create_order(order)
    assert out.order_id == "ORD1"
    assert total == Money(Decimal("25.00"), "INR")


@pytest.mark.parametrize("pincode", ["000000", "12", "4A0001"])  # invalid
def test_create_order_invalid_pincode(pincode):
    addr = _addr()
    addr.postal_code = pincode
    order = OrderInput(
        order_id="ORD1",
        items=[OrderItem(name="x", quantity=1, unit_price=Money(Decimal("1.00"), "INR"))],
        shipping_address=addr,
        billing_address=_addr(),
    )
    with pytest.raises(ValidationError):
        create_order(order)


def test_create_order_invalid_currency():
    order = OrderInput(
        order_id="ORD1",
        items=[OrderItem(name="x", quantity=1, unit_price=Money(Decimal("1.00"), "USD"))],
        shipping_address=_addr(),
        billing_address=_addr(),
    )
    with pytest.raises(ValueError):
        create_order(order)


