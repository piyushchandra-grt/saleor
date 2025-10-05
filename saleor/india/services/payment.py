from __future__ import annotations

import logging
from dataclasses import asdict

from prices import Money

from ..clients import RazorpayClientMock
from ..errors import PaymentGatewayError, ValidationError
from ..types import PaymentInput, PaymentResult
from ..validators import sanitize_for_logging, validate_currency_inr, validate_money_is_inr, validate_upi_vpa


logger = logging.getLogger(__name__)


def process_payment_gateway(payment: PaymentInput, *, client: RazorpayClientMock | None = None) -> PaymentResult:
    """Process Razorpay UPI payment in INR with validation and safe logging.

    This uses an injectable client to allow mocking in tests.
    """
    validate_currency_inr(payment.currency)
    validate_money_is_inr(payment.amount)
    validate_upi_vpa(payment.upi_vpa)

    if payment.amount.amount <= 0:
        raise ValidationError("Payment amount must be positive")
    if payment.method != "UPI":
        raise ValidationError("Only UPI method is supported in India module")

    client = client or RazorpayClientMock()
    try:
        order = client.create_order(amount=payment.amount, receipt=payment.order_id)
        pmt = client.capture_upi_payment(order_id=order.id, amount=payment.amount, vpa=payment.upi_vpa)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("payment.gateway.exception", extra={"data": sanitize_for_logging(asdict(payment))})
        raise PaymentGatewayError("Unexpected payment gateway exception") from exc

    if pmt.status != "captured":
        logger.error(
            "payment.captured.failed",
            extra={"data": sanitize_for_logging(pmt.__dict__)},
        )
        return PaymentResult(
            success=False,
            status=pmt.status,
            payment_id=pmt.id,
            error_code=pmt.error_code,
            error_message=pmt.error_description,
            gateway_response={
                "id": pmt.id,
                "status": pmt.status,
                "order_id": pmt.order_id,
                "vpa": pmt.vpa,
                "error_code": pmt.error_code or "",
                "error_description": pmt.error_description or "",
                "raw": pmt.raw or {},
            },
        )

    logger.info("payment.captured.success", extra={"data": sanitize_for_logging(pmt.__dict__)})
    return PaymentResult(
        success=True,
        status=pmt.status,
        payment_id=pmt.id,
        error_code=None,
        error_message=None,
        gateway_response={
            "id": pmt.id,
            "status": pmt.status,
            "order_id": pmt.order_id,
            "vpa": pmt.vpa,
            "raw": pmt.raw or {},
        },
    )


