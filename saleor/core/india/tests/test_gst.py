"""Unit tests for GST validation and calculation utilities."""

from decimal import Decimal

import pytest

from ..gst import (
    GSTCalculation,
    GSTRate,
    calculate_gst,
    determine_gst_rate_by_category,
    get_state_code_from_gstin,
    validate_gstin,
)


# Test GSTIN validation
def test_validate_gstin_valid():
    """Test validation of valid GSTIN."""
    # Valid GSTIN for Maharashtra
    is_valid, error = validate_gstin("27AAPFU0939F1ZV")
    assert is_valid is True
    assert error is None


def test_validate_gstin_empty():
    """Test validation fails for empty GSTIN."""
    is_valid, error = validate_gstin("")
    assert is_valid is False
    assert "required" in error.lower()


def test_validate_gstin_invalid_length():
    """Test validation fails for incorrect length."""
    is_valid, error = validate_gstin("27AAPFU0939F1Z")  # 14 chars instead of 15
    assert is_valid is False
    assert "15 characters" in error


def test_validate_gstin_invalid_format():
    """Test validation fails for invalid format."""
    is_valid, error = validate_gstin("ABCDEFGHIJKLMNO")  # Invalid format
    assert is_valid is False
    assert "format" in error.lower()


def test_validate_gstin_invalid_state_code():
    """Test validation fails for invalid state code."""
    is_valid, error = validate_gstin("99AAPFU0939F1ZV")  # State code 99 invalid
    assert is_valid is False
    assert "state code" in error.lower()


def test_validate_gstin_case_insensitive():
    """Test GSTIN validation is case-insensitive."""
    is_valid, error = validate_gstin("27aapfu0939f1zv")  # Lowercase
    assert is_valid is True
    assert error is None


# Test GST calculation
def test_calculate_gst_intra_state():
    """Test GST calculation for intra-state transaction (CGST + SGST)."""
    result = calculate_gst(
        amount=Decimal("1000.00"),
        gst_rate=Decimal("18.00"),
        billing_state_code="27",  # Maharashtra
        shipping_state_code="27",  # Maharashtra
        include_gst=False,
    )

    assert isinstance(result, GSTCalculation)
    assert result.base_amount == Decimal("1000.00")
    assert result.gst_rate == Decimal("18.00")
    assert result.total_gst == Decimal("180.00")
    assert result.cgst == Decimal("90.00")  # Half of 180
    assert result.sgst == Decimal("90.00")  # Half of 180
    assert result.igst == Decimal("0.00")
    assert result.total_amount == Decimal("1180.00")
    assert result.is_inter_state is False


def test_calculate_gst_inter_state():
    """Test GST calculation for inter-state transaction (IGST)."""
    result = calculate_gst(
        amount=Decimal("1000.00"),
        gst_rate=Decimal("18.00"),
        billing_state_code="27",  # Maharashtra
        shipping_state_code="07",  # Delhi
        include_gst=False,
    )

    assert result.base_amount == Decimal("1000.00")
    assert result.total_gst == Decimal("180.00")
    assert result.cgst == Decimal("0.00")
    assert result.sgst == Decimal("0.00")
    assert result.igst == Decimal("180.00")  # Full GST as IGST
    assert result.is_inter_state is True


def test_calculate_gst_with_included_gst():
    """Test GST calculation when GST is included in amount."""
    result = calculate_gst(
        amount=Decimal("1180.00"),  # Amount including 18% GST
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
        shipping_state_code="27",
        include_gst=True,
    )

    assert result.base_amount == Decimal("1000.00")
    assert result.total_gst == Decimal("180.00")
    assert result.total_amount == Decimal("1180.00")


def test_calculate_gst_different_rates():
    """Test GST calculation with different tax rates."""
    # Test 5% GST
    result_5 = calculate_gst(
        amount=Decimal("1000.00"),
        gst_rate=Decimal("5.00"),
        billing_state_code="27",
        include_gst=False,
    )
    assert result_5.total_gst == Decimal("50.00")
    assert result_5.total_amount == Decimal("1050.00")

    # Test 28% GST
    result_28 = calculate_gst(
        amount=Decimal("1000.00"),
        gst_rate=Decimal("28.00"),
        billing_state_code="27",
        include_gst=False,
    )
    assert result_28.total_gst == Decimal("280.00")
    assert result_28.total_amount == Decimal("1280.00")


def test_calculate_gst_negative_amount():
    """Test GST calculation fails for negative amount."""
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_gst(
            amount=Decimal("-100.00"),
            gst_rate=Decimal("18.00"),
            billing_state_code="27",
        )


def test_calculate_gst_invalid_rate():
    """Test GST calculation fails for invalid rate."""
    with pytest.raises(ValueError, match="between 0 and 100"):
        calculate_gst(
            amount=Decimal("1000.00"),
            gst_rate=Decimal("150.00"),  # Invalid rate
            billing_state_code="27",
        )


def test_calculate_gst_invalid_state_code():
    """Test GST calculation fails for invalid state code."""
    with pytest.raises(ValueError, match="Invalid billing state code"):
        calculate_gst(
            amount=Decimal("1000.00"),
            gst_rate=Decimal("18.00"),
            billing_state_code="99",  # Invalid
        )


# Test helper functions
def test_get_state_code_from_gstin():
    """Test extraction of state code from GSTIN."""
    state_code = get_state_code_from_gstin("27AAPFU0939F1ZV")
    assert state_code == "27"


def test_get_state_code_from_gstin_invalid():
    """Test state code extraction fails for invalid GSTIN."""
    with pytest.raises(ValueError, match="Invalid GSTIN"):
        get_state_code_from_gstin("AB")


def test_determine_gst_rate_by_category():
    """Test GST rate determination by product category."""
    # Test 5% category
    assert determine_gst_rate_by_category("Food Items") == GSTRate.FIVE
    assert determine_gst_rate_by_category("Essential Medicines") == GSTRate.FIVE

    # Test 12% category
    assert determine_gst_rate_by_category("Clothing") == GSTRate.TWELVE
    assert determine_gst_rate_by_category("Books") == GSTRate.TWELVE

    # Test 28% category
    assert determine_gst_rate_by_category("Luxury Items") == GSTRate.TWENTY_EIGHT

    # Test default 18% category
    assert determine_gst_rate_by_category("General Merchandise") == GSTRate.EIGHTEEN


# Test GSTRate enum
def test_gst_rate_enum_values():
    """Test GST rate enum has correct values."""
    assert GSTRate.ZERO.value == Decimal("0.00")
    assert GSTRate.FIVE.value == Decimal("5.00")
    assert GSTRate.TWELVE.value == Decimal("12.00")
    assert GSTRate.EIGHTEEN.value == Decimal("18.00")
    assert GSTRate.TWENTY_EIGHT.value == Decimal("28.00")


# Test edge cases
def test_calculate_gst_zero_amount():
    """Test GST calculation for zero amount."""
    result = calculate_gst(
        amount=Decimal("0.00"),
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
    )
    assert result.base_amount == Decimal("0.00")
    assert result.total_gst == Decimal("0.00")
    assert result.total_amount == Decimal("0.00")


def test_calculate_gst_zero_rate():
    """Test GST calculation for zero tax rate."""
    result = calculate_gst(
        amount=Decimal("1000.00"),
        gst_rate=Decimal("0.00"),
        billing_state_code="27",
    )
    assert result.base_amount == Decimal("1000.00")
    assert result.total_gst == Decimal("0.00")
    assert result.total_amount == Decimal("1000.00")


def test_calculate_gst_rounding():
    """Test GST calculation handles rounding correctly."""
    result = calculate_gst(
        amount=Decimal("333.33"),
        gst_rate=Decimal("18.00"),
        billing_state_code="27",
        include_gst=False,
    )
    # 333.33 * 0.18 = 60.00 (rounded)
    assert result.total_gst == Decimal("60.00")
    assert result.cgst == Decimal("30.00")
    assert result.sgst == Decimal("30.00")
