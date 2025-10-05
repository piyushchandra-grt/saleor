from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

from prices import Money

from ..validators import sanitize_for_logging, validate_money_is_inr, validate_upi_vpa


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RazorpayOrder:
    id: str
    amount: Money
    currency: str
    receipt: str
    status: str  # created|paid|failed


@dataclass(slots=True)
class RazorpayPayment:
    id: str
    order_id: str
    amount: Money
    currency: str
    vpa: str
    status: str  # created|authorized|captured|failed
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    raw: Dict[str, Any] | None = None


class RazorpayClientMock:
    """A minimal in-memory mock of Razorpay UPI endpoints.

    This mimics creating an order and capturing a UPI payment. Intended for tests.
    """

    def __init__(self) -> None:
        self.orders: dict[str, RazorpayOrder] = {}
        self.payments: dict[str, RazorpayPayment] = {}

    def create_order(self, *, amount: Money, receipt: str) -> RazorpayOrder:
        validate_money_is_inr(amount)
        order_id = f"order_{uuid.uuid4().hex[:14]}"
        order = RazorpayOrder(
            id=order_id,
            amount=amount,
            currency=amount.currency,
            receipt=receipt,
            status="created",
        )
        self.orders[order_id] = order
        logger.info(
            "razorpay.order.created",
            extra={
                "data": sanitize_for_logging(
                    {"order_id": order_id, "amount": str(amount.amount), "receipt": receipt}
                )
            },
        )
        return order

    def capture_upi_payment(
        self, *, order_id: str, amount: Money, vpa: str
    ) -> RazorpayPayment:
        validate_money_is_inr(amount)
        validate_upi_vpa(vpa)

        if order_id not in self.orders:
            payment_id = f"pay_{uuid.uuid4().hex[:14]}"
            payment = RazorpayPayment(
                id=payment_id,
                order_id=order_id,
                amount=amount,
                currency=amount.currency,
                vpa=vpa,
                status="failed",
                error_code="ORDER_NOT_FOUND",
                error_description="Order not found",
                raw={"reason": "order_missing"},
            )
            self.payments[payment_id] = payment
            logger.error(
                "razorpay.payment.failed",
                extra={"data": sanitize_for_logging(payment.__dict__)},
            )
            return payment

        # Simple heuristic: amounts below 1 INR fail for mock
        if amount.amount < Decimal("1"):
            payment_id = f"pay_{uuid.uuid4().hex[:14]}"
            payment = RazorpayPayment(
                id=payment_id,
                order_id=order_id,
                amount=amount,
                currency=amount.currency,
                vpa=vpa,
                status="failed",
                error_code="AMOUNT_TOO_LOW",
                error_description="Amount below minimum threshold",
                raw={"reason": "min_threshold"},
            )
            self.payments[payment_id] = payment
            logger.warning(
                "razorpay.payment.failed",
                extra={"data": sanitize_for_logging(payment.__dict__)},
            )
            return payment

        payment_id = f"pay_{uuid.uuid4().hex[:14]}"
        payment = RazorpayPayment(
            id=payment_id,
            order_id=order_id,
            amount=amount,
            currency=amount.currency,
            vpa=vpa,
            status="captured",
            raw={"mode": "UPI"},
        )
        self.payments[payment_id] = payment
        # Mark order paid in mock
        order = self.orders[order_id]
        self.orders[order_id] = RazorpayOrder(
            id=order.id,
            amount=order.amount,
            currency=order.currency,
            receipt=order.receipt,
            status="paid",
        )
        logger.info(
            "razorpay.payment.captured",
            extra={"data": sanitize_for_logging(payment.__dict__)},
        )
        return payment


