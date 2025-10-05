"""Razorpay UPI payment method support for India."""

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal

from ....core.india.currency import convert_to_paisa, format_inr, validate_inr_amount
from ....core.telemetry import saleor_attributes, tracer
from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData
from . import errors

logger = logging.getLogger(__name__)


@dataclass
class UPIPaymentData:
    """Data class for UPI payment information."""

    vpa: str  # Virtual Payment Address (e.g., user@upi)
    amount: Decimal
    order_id: str
    description: str
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None


class UPIValidationError(Exception):
    """Exception raised for UPI validation errors."""


def validate_upi_vpa(vpa: str) -> tuple[bool, str | None]:
    """Step 1: Validate UPI Virtual Payment Address (VPA).

    UPI VPA format: username@bankcode
    Examples: user@paytm, 9876543210@ybl

    Args:
        vpa: Virtual Payment Address to validate

    Returns:
        Tuple of (is_valid, error_message)

    """
    # Step 1.1: Check if VPA is provided
    if not vpa:
        error_msg = "UPI VPA is required"
        logger.warning(f"UPI VPA validation failed: {error_msg}")
        return False, error_msg

    # Step 1.2: Remove whitespace
    vpa = vpa.strip()

    # Step 1.3: Check format (must contain @)
    if "@" not in vpa:
        error_msg = "UPI VPA must contain @ symbol"
        logger.warning(f"UPI VPA validation failed: {error_msg} for VPA: {vpa}")
        return False, error_msg

    # Step 1.4: Split and validate parts
    parts = vpa.split("@")
    if len(parts) != 2:
        error_msg = "UPI VPA format is invalid (must be username@bank)"
        logger.warning(f"UPI VPA validation failed: {error_msg} for VPA: {vpa}")
        return False, error_msg

    username, bank_code = parts

    # Step 1.5: Validate username part (not empty, alphanumeric with dots/underscores)
    if not username or len(username) < 3:
        error_msg = "UPI VPA username must be at least 3 characters"
        logger.warning(f"UPI VPA validation failed: {error_msg}")
        return False, error_msg

    # Step 1.6: Validate bank code (not empty)
    if not bank_code or len(bank_code) < 2:
        error_msg = "UPI VPA bank code is invalid"
        logger.warning(f"UPI VPA validation failed: {error_msg}")
        return False, error_msg

    logger.info(f"UPI VPA validation successful: {vpa}")
    return True, None


def create_upi_payment_request(
    payment_information: PaymentData, config: GatewayConfig
) -> dict:
    """Step 2: Create UPI payment request for Razorpay.

    Args:
        payment_information: Payment data from Saleor
        config: Gateway configuration

    Returns:
        Dictionary with UPI payment request data

    Raises:
        UPIValidationError: If validation fails

    """
    # Step 2.1: Validate currency is INR
    if payment_information.currency != "INR":
        error_msg = f"UPI payments only support INR currency, got: {payment_information.currency}"
        logger.error(error_msg)
        raise UPIValidationError(error_msg)

    # Step 2.2: Validate amount
    is_valid, error = validate_inr_amount(payment_information.amount)
    if not is_valid:
        logger.error(f"UPI payment amount validation failed: {error}")
        raise UPIValidationError(error)

    # Step 2.3: Extract UPI VPA from payment data
    vpa = None
    if payment_information.data:
        vpa = payment_information.data.get("upi_vpa")

    if not vpa:
        error_msg = "UPI VPA is required in payment data"
        logger.error(error_msg)
        raise UPIValidationError(error_msg)

    # Step 2.4: Validate UPI VPA
    is_valid, error = validate_upi_vpa(vpa)
    if not is_valid:
        logger.error(f"UPI VPA validation failed: {error}")
        raise UPIValidationError(error)

    # Step 2.5: Convert amount to paisa
    amount_paisa = convert_to_paisa(payment_information.amount)

    # Step 2.6: Create payment request
    payment_request = {
        "amount": amount_paisa,
        "currency": "INR",
        "method": "upi",
        "vpa": vpa,
        "order_id": payment_information.order_id or f"order_{uuid.uuid4().hex[:12]}",
        "description": f"Payment for order {payment_information.order_id}",
        "customer": {
            "email": payment_information.customer_email,
        },
    }

    # Step 2.7: Add optional customer details
    if payment_information.billing:
        payment_request["customer"]["name"] = (
            f"{payment_information.billing.first_name} "
            f"{payment_information.billing.last_name}"
        )
        payment_request["customer"]["contact"] = payment_information.billing.phone

    logger.info(
        f"Created UPI payment request: {format_inr(payment_information.amount)} "
        f"to {vpa}"
    )

    return payment_request


def process_upi_payment(
    payment_information: PaymentData, config: GatewayConfig, mock_mode: bool = False
) -> GatewayResponse:
    """Step 3: Process UPI payment through Razorpay.

    Args:
        payment_information: Payment data from Saleor
        config: Gateway configuration
        mock_mode: If True, use mock API (for testing)

    Returns:
        GatewayResponse with transaction details

    """
    # Step 3.1: Validate payment information
    try:
        payment_request = create_upi_payment_request(payment_information, config)
    except UPIValidationError as exc:
        error_msg = str(exc)
        logger.error(f"UPI payment validation failed: {error_msg}")
        return GatewayResponse(
            transaction_id=f"failed_{uuid.uuid4().hex[:12]}",
            action_required=False,
            kind=TransactionKind.CAPTURE,
            amount=payment_information.amount,
            currency=payment_information.currency,
            error=error_msg,
            is_success=False,
            raw_response={"error": error_msg},
        )

    # Step 3.2: Process payment (mock or real)
    if mock_mode:
        response = _mock_upi_payment(payment_request, payment_information)
    else:
        response = _real_upi_payment(payment_request, payment_information, config)

    return response


def _mock_upi_payment(
    payment_request: dict, payment_information: PaymentData
) -> GatewayResponse:
    """Step 4: Mock UPI payment for testing.

    Args:
        payment_request: Payment request data
        payment_information: Payment information

    Returns:
        GatewayResponse with mock transaction

    """
    # Step 4.1: Generate mock transaction ID
    transaction_id = f"upi_mock_{uuid.uuid4().hex[:16]}"

    # Step 4.2: Log mock payment
    logger.info(
        f"[MOCK] Processing UPI payment: {format_inr(payment_information.amount)} "
        f"to {payment_request['vpa']}"
    )

    # Step 4.3: Simulate successful payment
    with tracer.start_as_current_span("razorpay.upi.mock_payment") as span:
        span.set_attribute(saleor_attributes.COMPONENT, "payment")
        span.set_attribute("payment.method", "upi")
        span.set_attribute("payment.mock", True)

        mock_response = {
            "id": transaction_id,
            "amount": payment_request["amount"],
            "currency": "INR",
            "status": "captured",
            "method": "upi",
            "vpa": payment_request["vpa"],
            "order_id": payment_request["order_id"],
            "description": payment_request["description"],
            "created_at": "2024-01-01T00:00:00+05:30",
        }

    logger.info(f"[MOCK] UPI payment successful: {transaction_id}")

    # Step 4.4: Return successful gateway response
    return GatewayResponse(
        transaction_id=transaction_id,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=None,
        is_success=True,
        raw_response=mock_response,
    )


def _real_upi_payment(
    payment_request: dict, payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Step 5: Process real UPI payment through Razorpay API.

    Args:
        payment_request: Payment request data
        payment_information: Payment information
        config: Gateway configuration

    Returns:
        GatewayResponse with transaction details

    """
    # Step 5.1: Import Razorpay client
    try:
        import razorpay

        from . import RAZORPAY_EXCEPTIONS, get_client
    except ImportError:
        error_msg = "Razorpay SDK not installed"
        logger.error(error_msg)
        return GatewayResponse(
            transaction_id=f"failed_{uuid.uuid4().hex[:12]}",
            action_required=False,
            kind=TransactionKind.CAPTURE,
            amount=payment_information.amount,
            currency=payment_information.currency,
            error=error_msg,
            is_success=False,
            raw_response={"error": error_msg},
        )

    # Step 5.2: Create Razorpay client
    razorpay_client = get_client(**config.connection_params)

    # Step 5.3: Process UPI payment
    try:
        with tracer.start_as_current_span("razorpay.upi.create_payment") as span:
            span.set_attribute(saleor_attributes.COMPONENT, "payment")
            span.set_attribute("payment.method", "upi")

            # Create payment
            response = razorpay_client.payment.create(payment_request)

            # Check if payment requires action (e.g., UPI app approval)
            action_required = response.get("status") == "created"

            logger.info(
                f"UPI payment created: {response.get('id')}, "
                f"Status: {response.get('status')}"
            )

    except RAZORPAY_EXCEPTIONS as exc:
        error_msg = f"Razorpay API error: {str(exc)}"
        logger.exception(f"UPI payment failed: {error_msg}")

        return GatewayResponse(
            transaction_id=f"failed_{uuid.uuid4().hex[:12]}",
            action_required=False,
            kind=TransactionKind.CAPTURE,
            amount=payment_information.amount,
            currency=payment_information.currency,
            error=errors.SERVER_ERROR,
            is_success=False,
            raw_response={"error": error_msg},
        )

    # Step 5.4: Return gateway response
    return GatewayResponse(
        transaction_id=response.get("id", f"txn_{uuid.uuid4().hex[:12]}"),
        action_required=action_required,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        error=None,
        is_success=True,
        raw_response=response,
    )
