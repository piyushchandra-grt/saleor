from decimal import Decimal

import pytest
from prices import Money

from saleor.india.clients import RazorpayClientMock
from saleor.india.services.payment import process_payment_gateway
from saleor.india.types import PaymentInput
from saleor.india.errors import ValidationError


def test_process_payment_success():
    client = RazorpayClientMock()
    payment_in = PaymentInput(
        order_id="ORD123",
        amount=Money(Decimal("199.00"), "INR"),
        currency="INR",
        method="UPI",
        upi_vpa="user@upi",
    )
    result = process_payment_gateway(payment_in, client=client)
    assert result.success is True
    assert result.status == "captured"
    assert result.payment_id is not None


def test_process_payment_invalid_vpa():
    client = RazorpayClientMock()
    payment_in = PaymentInput(
        order_id="ORD123",
        amount=Money(Decimal("199.00"), "INR"),
        currency="INR",
        method="UPI",
        upi_vpa="bad vpa",
    )
    with pytest.raises(ValueError):
        process_payment_gateway(payment_in, client=client)


def test_process_payment_low_amount_failure():
    client = RazorpayClientMock()
    payment_in = PaymentInput(
        order_id="ORD123",
        amount=Money(Decimal("0.50"), "INR"),
        currency="INR",
        method="UPI",
        upi_vpa="user@upi",
    )
    result = process_payment_gateway(payment_in, client=client)
    assert result.success is False
    assert result.status == "failed"
    assert result.error_code == "AMOUNT_TOO_LOW"


