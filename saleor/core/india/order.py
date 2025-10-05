"""India-specific order creation and management utilities."""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from .currency import format_inr, validate_inr_amount
from .gst import GSTCalculation, calculate_gst, validate_gstin

if TYPE_CHECKING:
    from ...account.models import Address
    from ...order.models import Order, OrderLine

logger = logging.getLogger(__name__)


@dataclass
class IndianOrderData:
    """Container for India-specific order data."""

    order_id: str
    base_amount: Decimal
    gst_calculation: GSTCalculation
    customer_gstin: str | None
    invoice_number: str | None
    is_b2b: bool  # Business-to-Business transaction
    place_of_supply: str  # State code


class IndianOrderError(Exception):
    """Exception raised for Indian order-related errors."""


def validate_indian_order_data(
    order_amount: Decimal,
    billing_address: Optional["Address"] = None,
    shipping_address: Optional["Address"] = None,
    customer_gstin: str | None = None,
) -> tuple[bool, str | None]:
    """Step 1: Validate order data for Indian compliance.

    Args:
        order_amount: Total order amount in INR
        billing_address: Billing address (must be in India)
        shipping_address: Shipping address (must be in India)
        customer_gstin: Customer's GSTIN (optional, required for B2B)

    Returns:
        Tuple of (is_valid, error_message)

    """
    # Step 1.1: Validate order amount
    is_valid, error = validate_inr_amount(order_amount)
    if not is_valid:
        logger.error(f"Order amount validation failed: {error}")
        return False, error

    # Step 1.2: Validate billing address exists and is in India
    if billing_address:
        if billing_address.country.code != "IN":
            error_msg = (
                f"Billing address must be in India, got: {billing_address.country.code}"
            )
            logger.error(error_msg)
            return False, error_msg

    # Step 1.3: Validate shipping address if provided
    if shipping_address:
        if shipping_address.country.code != "IN":
            error_msg = f"Shipping address must be in India, got: {shipping_address.country.code}"
            logger.error(error_msg)
            return False, error_msg

    # Step 1.4: Validate customer GSTIN if provided
    if customer_gstin:
        is_valid_gstin, gstin_error = validate_gstin(customer_gstin)
        if not is_valid_gstin:
            logger.error(f"Customer GSTIN validation failed: {gstin_error}")
            return False, f"Invalid customer GSTIN: {gstin_error}"

    logger.info("Indian order data validation successful")
    return True, None


def create_indian_order(
    order: "Order",
    gst_rate: Decimal,
    customer_gstin: str | None = None,
    include_gst_in_price: bool = True,
) -> IndianOrderData:
    """Step 2: Create India-specific order with GST calculations.

    Args:
        order: Saleor Order object
        gst_rate: GST rate to apply (as percentage)
        customer_gstin: Customer's GSTIN for B2B transactions
        include_gst_in_price: Whether prices already include GST

    Returns:
        IndianOrderData object with GST breakdown

    Raises:
        IndianOrderError: If order creation fails

    """
    # Step 2.1: Validate order currency is INR
    if order.currency != "INR":
        error_msg = f"Order currency must be INR, got: {order.currency}"
        logger.error(error_msg)
        raise IndianOrderError(error_msg)

    # Step 2.2: Get billing and shipping state codes
    if not order.billing_address:
        error_msg = "Billing address is required for Indian orders"
        logger.error(error_msg)
        raise IndianOrderError(error_msg)

    billing_state_code = _get_state_code_from_address(order.billing_address)

    shipping_state_code = None
    if order.shipping_address:
        shipping_state_code = _get_state_code_from_address(order.shipping_address)
    else:
        shipping_state_code = billing_state_code

    # Step 2.3: Validate customer GSTIN if provided
    is_b2b = False
    if customer_gstin:
        is_valid, error = validate_gstin(customer_gstin)
        if not is_valid:
            error_msg = f"Invalid customer GSTIN: {error}"
            logger.error(error_msg)
            raise IndianOrderError(error_msg)
        is_b2b = True

    # Step 2.4: Calculate GST
    order_amount = order.total.gross.amount
    gst_calculation = calculate_gst(
        amount=order_amount,
        gst_rate=gst_rate,
        billing_state_code=billing_state_code,
        shipping_state_code=shipping_state_code,
        include_gst=include_gst_in_price,
    )

    # Step 2.5: Generate invoice number (simplified)
    invoice_number = f"INV-{order.number}"

    # Step 2.6: Create Indian order data
    indian_order = IndianOrderData(
        order_id=str(order.id),
        base_amount=gst_calculation.base_amount,
        gst_calculation=gst_calculation,
        customer_gstin=customer_gstin,
        invoice_number=invoice_number,
        is_b2b=is_b2b,
        place_of_supply=shipping_state_code or billing_state_code,
    )

    logger.info(
        f"Created Indian order: {invoice_number}, "
        f"Amount: {format_inr(gst_calculation.total_amount)}, "
        f"GST: {format_inr(gst_calculation.total_gst)}"
    )

    return indian_order


def calculate_order_gst_breakdown(
    order_lines: list["OrderLine"],
    billing_state_code: str,
    shipping_state_code: str | None = None,
) -> dict:
    """Step 3: Calculate GST breakdown for all order lines.

    Args:
        order_lines: List of order lines
        billing_state_code: Billing address state code
        shipping_state_code: Shipping address state code (optional)

    Returns:
        Dictionary with GST breakdown per line and total

    """
    # Step 3.1: Initialize totals
    total_base_amount = Decimal("0.00")
    total_gst = Decimal("0.00")
    total_cgst = Decimal("0.00")
    total_sgst = Decimal("0.00")
    total_igst = Decimal("0.00")

    line_breakdowns = []

    # Step 3.2: Calculate GST for each line
    for line in order_lines:
        line_amount = line.total_price_gross_amount

        # Determine GST rate based on product (simplified - should use tax class)
        gst_rate = Decimal("18.00")  # Default 18%

        # Calculate GST for this line
        line_gst = calculate_gst(
            amount=line_amount,
            gst_rate=gst_rate,
            billing_state_code=billing_state_code,
            shipping_state_code=shipping_state_code,
            include_gst=True,
        )

        # Add to totals
        total_base_amount += line_gst.base_amount
        total_gst += line_gst.total_gst
        total_cgst += line_gst.cgst
        total_sgst += line_gst.sgst
        total_igst += line_gst.igst

        # Store line breakdown
        line_breakdowns.append(
            {
                "line_id": line.id,
                "product_name": line.product_name,
                "quantity": line.quantity,
                "base_amount": line_gst.base_amount,
                "gst_rate": gst_rate,
                "gst_amount": line_gst.total_gst,
                "total_amount": line_gst.total_amount,
            }
        )

    # Step 3.3: Return comprehensive breakdown
    return {
        "lines": line_breakdowns,
        "totals": {
            "base_amount": total_base_amount,
            "cgst": total_cgst,
            "sgst": total_sgst,
            "igst": total_igst,
            "total_gst": total_gst,
            "total_amount": total_base_amount + total_gst,
        },
        "is_inter_state": total_igst > 0,
    }


def _get_state_code_from_address(address: "Address") -> str:
    """Extract state code from address.

    Args:
        address: Address object

    Returns:
        Two-digit state code

    Raises:
        IndianOrderError: If state code cannot be determined

    """
    # Try to get from metadata first
    if hasattr(address, "metadata") and address.metadata:
        state_code = address.metadata.get("state_code")
        if state_code:
            return state_code

    # Try to derive from country_area (state name/code)
    if address.country_area:
        # Import here to avoid circular import
        from .address import get_state_code

        state_code = get_state_code(address.country_area)
        if state_code:
            return state_code

    # If we can't determine state code, raise error
    error_msg = f"Cannot determine state code from address: {address.id}"
    logger.error(error_msg)
    raise IndianOrderError(error_msg)
