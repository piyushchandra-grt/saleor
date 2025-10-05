"""Unit tests for India-specific discount utilities."""

from decimal import Decimal

import pytest

from ..discount import (
    IndianDiscountError,
    apply_discount_with_gst,
    calculate_bulk_discount_with_gst,
    validate_discount_eligibility,
)


# Test discount application with GST
def test_apply_percentage_discount_with_gst():
    """Test applying percentage discount with GST recalculation."""
    result = apply_discount_with_gst(
        original_amount=Decimal("1180.00"),  # Including 18% GST
        discount_value=Decimal("10.00"),  # 10% discount
        discount_type="percentage",
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
        shipping_state_code="27",
    )

    assert "original" in result
    assert "discount" in result
    assert "final" in result
    assert "savings" in result

    # Original should be 1000 base + 180 GST
    assert result["original"]["base_amount"] == Decimal("1000.00")
    assert result["original"]["gst_amount"] == Decimal("180.00")

    # After 10% discount on base (100), new base is 900
    # GST on 900 @ 18% = 162
    # Total = 1062
    assert result["final"]["base_amount"] == Decimal("900.00")
    assert result["final"]["total_gst"] == Decimal("162.00")
    assert result["final"]["total_amount"] == Decimal("1062.00")


def test_apply_fixed_discount_with_gst():
    """Test applying fixed discount with GST recalculation."""
    result = apply_discount_with_gst(
        original_amount=Decimal("1180.00"),  # Including 18% GST
        discount_value=Decimal("118.00"),  # Fixed 118 discount
        discount_type="fixed",
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
        shipping_state_code="27",
    )

    assert result["discount"]["type"] == "fixed"
    # Fixed discount of 118 on amount with GST means 100 base discount
    assert result["discount"]["discount_on_base"] == Decimal("100.00")


def test_apply_discount_inter_state():
    """Test discount application for inter-state transaction."""
    result = apply_discount_with_gst(
        original_amount=Decimal("1180.00"),
        discount_value=Decimal("10.00"),
        discount_type="percentage",
        gst_rate=Decimal("18.00"),
        billing_state_code="27",  # Maharashtra
        shipping_state_code="07",  # Delhi (inter-state)
    )

    # For inter-state, IGST should be used
    assert result["final"]["igst"] > 0
    assert result["final"]["cgst"] == Decimal("0.00")
    assert result["final"]["sgst"] == Decimal("0.00")


def test_apply_discount_invalid_amount():
    """Test discount fails for invalid amount."""
    with pytest.raises(IndianDiscountError, match="Invalid original amount"):
        apply_discount_with_gst(
            original_amount=Decimal("-100.00"),  # Negative
            discount_value=Decimal("10.00"),
            discount_type="percentage",
            gst_rate=Decimal("18.00"),
            billing_state_code="27",
        )


def test_apply_discount_invalid_type():
    """Test discount fails for invalid type."""
    with pytest.raises(IndianDiscountError, match="Invalid discount type"):
        apply_discount_with_gst(
            original_amount=Decimal("1180.00"),
            discount_value=Decimal("10.00"),
            discount_type="invalid",  # Invalid type
            gst_rate=Decimal("18.00"),
            billing_state_code="27",
        )


def test_apply_discount_invalid_percentage():
    """Test discount fails for invalid percentage."""
    with pytest.raises(IndianDiscountError, match="between 0 and 100"):
        apply_discount_with_gst(
            original_amount=Decimal("1180.00"),
            discount_value=Decimal("150.00"),  # > 100%
            discount_type="percentage",
            gst_rate=Decimal("18.00"),
            billing_state_code="27",
        )


def test_apply_discount_savings_percentage():
    """Test discount savings percentage calculation."""
    result = apply_discount_with_gst(
        original_amount=Decimal("1180.00"),
        discount_value=Decimal("10.00"),
        discount_type="percentage",
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )

    # Total discount = 1180 - 1062 = 118
    # Savings percentage = (118 / 1180) * 100 = 10%
    assert result["savings"]["amount"] == Decimal("118.00")
    assert result["savings"]["percentage"] == Decimal("10.00")


# Test discount eligibility validation
def test_validate_discount_eligibility_valid():
    """Test discount eligibility for valid order."""
    is_eligible, error = validate_discount_eligibility(
        order_amount=Decimal("1000.00"),
        discount_code="SAVE10",
        min_order_value=Decimal("500.00"),
    )

    assert is_eligible is True
    assert error is None


def test_validate_discount_eligibility_below_minimum():
    """Test discount fails for order below minimum."""
    is_eligible, error = validate_discount_eligibility(
        order_amount=Decimal("400.00"),
        discount_code="SAVE10",
        min_order_value=Decimal("500.00"),
    )

    assert is_eligible is False
    assert "below minimum" in error


def test_validate_discount_eligibility_invalid_amount():
    """Test discount fails for invalid amount."""
    is_eligible, error = validate_discount_eligibility(
        order_amount=Decimal("-100.00"),
        discount_code="SAVE10",
    )

    assert is_eligible is False
    assert error is not None


def test_validate_discount_eligibility_empty_code():
    """Test discount fails for empty code."""
    is_eligible, error = validate_discount_eligibility(
        order_amount=Decimal("1000.00"),
        discount_code="",
    )

    assert is_eligible is False
    assert "required" in error.lower()


# Test bulk discount calculation
def test_calculate_bulk_discount_no_tiers():
    """Test bulk discount with no applicable tiers."""
    result = calculate_bulk_discount_with_gst(
        item_price=Decimal("100.00"),
        quantity=3,
        discount_tiers=[],
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )

    assert result["quantity"] == 3
    assert result["applied_tier"] is None
    assert result["discount_percentage"] == Decimal("0.00")
    assert result["final_total"] == Decimal("300.00")


def test_calculate_bulk_discount_single_tier():
    """Test bulk discount with single tier."""
    discount_tiers = [{"min_qty": 5, "discount_pct": 10}]

    result = calculate_bulk_discount_with_gst(
        item_price=Decimal("118.00"),  # Including GST
        quantity=5,
        discount_tiers=discount_tiers,
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )

    assert result["applied_tier"] == {"min_qty": 5, "discount_pct": 10}
    assert result["discount_percentage"] == Decimal("10.00")
    # With discount, total should be less than 118 * 5 = 590
    assert result["final_total"] < Decimal("590.00")


def test_calculate_bulk_discount_multiple_tiers():
    """Test bulk discount with multiple tiers."""
    discount_tiers = [
        {"min_qty": 5, "discount_pct": 10},
        {"min_qty": 10, "discount_pct": 20},
        {"min_qty": 20, "discount_pct": 30},
    ]

    # Test quantity 15 (should get 20% discount)
    result = calculate_bulk_discount_with_gst(
        item_price=Decimal("118.00"),
        quantity=15,
        discount_tiers=discount_tiers,
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )

    assert result["applied_tier"]["discount_pct"] == 20
    assert result["discount_percentage"] == Decimal("20.00")


def test_calculate_bulk_discount_highest_tier():
    """Test bulk discount selects highest applicable tier."""
    discount_tiers = [
        {"min_qty": 5, "discount_pct": 10},
        {"min_qty": 10, "discount_pct": 20},
    ]

    # Quantity 25 should get the highest tier (20%)
    result = calculate_bulk_discount_with_gst(
        item_price=Decimal("118.00"),
        quantity=25,
        discount_tiers=discount_tiers,
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )

    assert result["applied_tier"]["discount_pct"] == 20


def test_calculate_bulk_discount_below_tier():
    """Test bulk discount when quantity is below all tiers."""
    discount_tiers = [{"min_qty": 10, "discount_pct": 20}]

    result = calculate_bulk_discount_with_gst(
        item_price=Decimal("118.00"),
        quantity=5,  # Below minimum
        discount_tiers=discount_tiers,
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )

    assert result["applied_tier"] is None
    assert result["discount_percentage"] == Decimal("0.00")


def test_calculate_bulk_discount_invalid_price():
    """Test bulk discount fails for invalid price."""
    with pytest.raises(IndianDiscountError, match="Invalid item price"):
        calculate_bulk_discount_with_gst(
            item_price=Decimal("-100.00"),
            quantity=5,
            discount_tiers=[],
            gst_rate=Decimal("18.00"),
            billing_state_code="27",
        )


def test_calculate_bulk_discount_invalid_quantity():
    """Test bulk discount fails for invalid quantity."""
    with pytest.raises(IndianDiscountError, match="must be positive"):
        calculate_bulk_discount_with_gst(
            item_price=Decimal("118.00"),
            quantity=0,  # Invalid
            discount_tiers=[],
            gst_rate=Decimal("18.00"),
            billing_state_code="27",
        )


# Test edge cases
def test_apply_discount_full_discount():
    """Test applying 100% discount."""
    result = apply_discount_with_gst(
        original_amount=Decimal("1180.00"),
        discount_value=Decimal("100.00"),
        discount_type="percentage",
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )

    assert result["final"]["base_amount"] == Decimal("0.00")
    assert result["final"]["total_gst"] == Decimal("0.00")
    assert result["final"]["total_amount"] == Decimal("0.00")


def test_calculate_bulk_discount_per_item_price():
    """Test bulk discount calculates correct per-item price."""
    discount_tiers = [{"min_qty": 10, "discount_pct": 20}]

    result = calculate_bulk_discount_with_gst(
        item_price=Decimal("118.00"),
        quantity=10,
        discount_tiers=discount_tiers,
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )

    # Final per item price should be less than original
    assert result["final_per_item_price"] < result["item_price"]
    # And final total should equal per_item_price * quantity
    assert result["final_total"] == result["final_per_item_price"] * 10
