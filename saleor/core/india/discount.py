"""India-specific discount utilities with GST considerations."""

import logging
from decimal import Decimal

from .currency import format_inr, validate_inr_amount
from .gst import calculate_gst

logger = logging.getLogger(__name__)


class IndianDiscountError(Exception):
    """Exception raised for Indian discount-related errors."""


def apply_discount_with_gst(
    original_amount: Decimal,
    discount_value: Decimal,
    discount_type: str,  # "fixed" or "percentage"
    gst_rate: Decimal,
    billing_state_code: str,
    shipping_state_code: str | None = None,
) -> dict:
    """Step 1: Apply discount to amount with proper GST recalculation.

    In India, discounts can be applied:
    1. Before GST (discount on base amount)
    2. After GST (discount on final amount)

    This function applies discount before GST calculation, which is
    the standard practice for most e-commerce transactions.

    Args:
        original_amount: Original amount (including GST)
        discount_value: Discount amount or percentage
        discount_type: "fixed" for fixed amount, "percentage" for percentage
        gst_rate: GST rate as percentage
        billing_state_code: Billing address state code
        shipping_state_code: Shipping address state code

    Returns:
        Dictionary with detailed discount and GST breakdown

    """
    # Step 1.1: Validate inputs
    is_valid, error = validate_inr_amount(original_amount)
    if not is_valid:
        error_msg = f"Invalid original amount: {error}"
        logger.error(error_msg)
        raise IndianDiscountError(error_msg)

    is_valid, error = validate_inr_amount(discount_value, min_amount=Decimal("0.00"))
    if not is_valid and discount_type == "fixed":
        error_msg = f"Invalid discount value: {error}"
        logger.error(error_msg)
        raise IndianDiscountError(error_msg)

    # Step 1.2: Validate discount type
    if discount_type not in ["fixed", "percentage"]:
        error_msg = f"Invalid discount type: {discount_type}"
        logger.error(error_msg)
        raise IndianDiscountError(error_msg)

    # Step 1.3: Calculate original GST breakdown
    original_gst = calculate_gst(
        amount=original_amount,
        gst_rate=gst_rate,
        billing_state_code=billing_state_code,
        shipping_state_code=shipping_state_code,
        include_gst=True,
    )

    # Step 1.4: Calculate discount amount on base price
    if discount_type == "percentage":
        if discount_value < 0 or discount_value > 100:
            error_msg = (
                f"Discount percentage must be between 0 and 100: {discount_value}"
            )
            logger.error(error_msg)
            raise IndianDiscountError(error_msg)
        discount_on_base = (original_gst.base_amount * discount_value / 100).quantize(
            Decimal("0.01")
        )
    else:  # fixed
        # For fixed discount, we need to extract base amount from discount
        # assuming discount includes proportional GST
        discount_on_base = (discount_value * 100 / (100 + gst_rate)).quantize(
            Decimal("0.01")
        )

    # Step 1.5: Calculate new base amount after discount
    new_base_amount = original_gst.base_amount - discount_on_base
    if new_base_amount < 0:
        new_base_amount = Decimal("0.00")

    # Step 1.6: Calculate GST on discounted amount
    new_gst = calculate_gst(
        amount=new_base_amount,
        gst_rate=gst_rate,
        billing_state_code=billing_state_code,
        shipping_state_code=shipping_state_code,
        include_gst=False,
    )

    # Step 1.7: Calculate total discount amount (including GST)
    total_discount = original_amount - new_gst.total_amount

    # Step 1.8: Log the discount application
    logger.info(
        f"Applied {discount_type} discount: "
        f"Original: {format_inr(original_amount)}, "
        f"Discount: {format_inr(total_discount)}, "
        f"Final: {format_inr(new_gst.total_amount)}"
    )

    # Step 1.9: Return comprehensive breakdown
    return {
        "original": {
            "base_amount": original_gst.base_amount,
            "gst_amount": original_gst.total_gst,
            "total_amount": original_gst.total_amount,
        },
        "discount": {
            "type": discount_type,
            "value": discount_value,
            "discount_on_base": discount_on_base,
            "discount_on_gst": original_gst.total_gst - new_gst.total_gst,
            "total_discount": total_discount,
        },
        "final": {
            "base_amount": new_gst.base_amount,
            "cgst": new_gst.cgst,
            "sgst": new_gst.sgst,
            "igst": new_gst.igst,
            "total_gst": new_gst.total_gst,
            "total_amount": new_gst.total_amount,
        },
        "savings": {
            "amount": total_discount,
            "percentage": (
                (total_discount / original_amount * 100).quantize(Decimal("0.01"))
                if original_amount > 0
                else Decimal("0.00")
            ),
        },
    }


def validate_discount_eligibility(
    order_amount: Decimal,
    discount_code: str,
    min_order_value: Decimal | None = None,
    max_discount_value: Decimal | None = None,
) -> tuple[bool, str | None]:
    """Step 2: Validate if discount can be applied to an order.

    Args:
        order_amount: Order amount in INR
        discount_code: Discount code being applied
        min_order_value: Minimum order value required for discount
        max_discount_value: Maximum discount amount allowed

    Returns:
        Tuple of (is_eligible, error_message)

    """
    # Step 2.1: Validate order amount
    is_valid, error = validate_inr_amount(order_amount)
    if not is_valid:
        logger.warning(f"Invalid order amount for discount: {error}")
        return False, error

    # Step 2.2: Check minimum order value
    if min_order_value is not None:
        if order_amount < min_order_value:
            error_msg = (
                f"Order amount {format_inr(order_amount)} is below "
                f"minimum {format_inr(min_order_value)} for discount '{discount_code}'"
            )
            logger.info(error_msg)
            return False, error_msg

    # Step 2.3: Validate discount code format (basic validation)
    if not discount_code or not discount_code.strip():
        error_msg = "Discount code is required"
        logger.warning(error_msg)
        return False, error_msg

    logger.info(
        f"Discount '{discount_code}' is eligible for order amount {format_inr(order_amount)}"
    )
    return True, None


def calculate_bulk_discount_with_gst(
    item_price: Decimal,
    quantity: int,
    discount_tiers: list[dict],
    gst_rate: Decimal,
    billing_state_code: str,
    shipping_state_code: str | None = None,
) -> dict:
    """Step 3: Calculate bulk/quantity-based discount with GST.

    Args:
        item_price: Price per item (including GST)
        quantity: Number of items
        discount_tiers: List of discount tiers
                       e.g., [{"min_qty": 5, "discount_pct": 10},
                              {"min_qty": 10, "discount_pct": 20}]
        gst_rate: GST rate as percentage
        billing_state_code: Billing address state code
        shipping_state_code: Shipping address state code

    Returns:
        Dictionary with pricing breakdown including bulk discount

    """
    # Step 3.1: Validate inputs
    is_valid, error = validate_inr_amount(item_price)
    if not is_valid:
        error_msg = f"Invalid item price: {error}"
        logger.error(error_msg)
        raise IndianDiscountError(error_msg)

    if quantity <= 0:
        error_msg = f"Quantity must be positive: {quantity}"
        logger.error(error_msg)
        raise IndianDiscountError(error_msg)

    # Step 3.2: Calculate original total
    original_total = item_price * quantity

    # Step 3.3: Determine applicable discount tier
    applicable_discount = Decimal("0.00")
    applied_tier = None

    if discount_tiers:
        # Sort tiers by minimum quantity (descending)
        sorted_tiers = sorted(discount_tiers, key=lambda x: x["min_qty"], reverse=True)

        for tier in sorted_tiers:
            if quantity >= tier["min_qty"]:
                applicable_discount = Decimal(str(tier["discount_pct"]))
                applied_tier = tier
                break

    # Step 3.4: Apply discount with GST recalculation
    if applicable_discount > 0:
        discount_result = apply_discount_with_gst(
            original_amount=original_total,
            discount_value=applicable_discount,
            discount_type="percentage",
            gst_rate=gst_rate,
            billing_state_code=billing_state_code,
            shipping_state_code=shipping_state_code,
        )

        final_total = discount_result["final"]["total_amount"]
        per_item_price = (final_total / quantity).quantize(Decimal("0.01"))
    else:
        discount_result = None
        final_total = original_total
        per_item_price = item_price

    # Step 3.5: Log bulk discount application
    if applied_tier:
        logger.info(
            f"Applied bulk discount: Quantity {quantity} -> "
            f"{applicable_discount}% off, "
            f"Saved: {format_inr(original_total - final_total)}"
        )

    # Step 3.6: Return comprehensive breakdown
    return {
        "item_price": item_price,
        "quantity": quantity,
        "original_total": original_total,
        "applied_tier": applied_tier,
        "discount_percentage": applicable_discount,
        "discount_details": discount_result,
        "final_total": final_total,
        "final_per_item_price": per_item_price,
    }
