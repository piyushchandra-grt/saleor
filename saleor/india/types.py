from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional, TypedDict

from prices import Money


@dataclass(slots=True)
class AddressIN:
    first_name: str
    last_name: str
    street_address_1: str
    street_address_2: str | None
    city: str
    state_code: str  # e.g., "MH", "KA"; ISO 3166-2:IN state code
    postal_code: str  # 6-digit PIN
    country_code: str = "IN"
    phone: str | None = None
    gstin: str | None = None


@dataclass(slots=True)
class OrderItem:
    name: str
    quantity: int
    unit_price: Money


@dataclass(slots=True)
class OrderInput:
    order_id: str
    items: List[OrderItem]
    shipping_address: AddressIN
    billing_address: AddressIN


DiscountType = Literal["PERCENTAGE", "AMOUNT"]


@dataclass(slots=True)
class DiscountInput:
    type: DiscountType
    value: Decimal
    currency: str = "INR"
    max_amount: Optional[Money] = None


@dataclass(slots=True)
class DiscountResult:
    base_total: Money
    discount_applied: Money
    final_total: Money


class GatewayResponse(TypedDict, total=False):
    id: str
    status: str
    order_id: str
    vpa: str
    error_code: str
    error_description: str
    raw: Dict[str, Any]


@dataclass(slots=True)
class PaymentInput:
    order_id: str
    amount: Money
    currency: str
    method: Literal["UPI"]
    upi_vpa: str
    customer_email: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PaymentResult:
    success: bool
    status: str
    payment_id: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    gateway_response: GatewayResponse


__all__ = [
    "AddressIN",
    "OrderItem",
    "OrderInput",
    "DiscountInput",
    "DiscountResult",
    "PaymentInput",
    "PaymentResult",
    "GatewayResponse",
]


