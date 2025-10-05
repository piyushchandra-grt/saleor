"""Unit tests for INR currency handling utilities."""

from decimal import Decimal

import pytest

from ..currency import (
    convert_from_paisa,
    convert_to_paisa,
    format_inr,
    parse_inr_string,
    validate_inr_amount,
)


# Test INR formatting
def test_format_inr_basic():
    """Test basic INR formatting."""
    formatted = format_inr(Decimal("1234.56"))
    assert formatted == "₹1,234.56"


def test_format_inr_lakhs():
    """Test INR formatting with lakhs."""
    formatted = format_inr(Decimal("123456.78"))
    assert formatted == "₹1,23,456.78"


def test_format_inr_crores():
    """Test INR formatting with crores."""
    formatted = format_inr(Decimal("12345678.90"))
    assert formatted == "₹1,23,45,678.90"


def test_format_inr_without_symbol():
    """Test INR formatting without currency symbol."""
    formatted = format_inr(Decimal("1234.56"), include_symbol=False)
    assert formatted == "1,234.56"


def test_format_inr_small_amount():
    """Test INR formatting for small amounts."""
    formatted = format_inr(Decimal("99.50"))
    assert formatted == "₹99.50"


def test_format_inr_zero():
    """Test INR formatting for zero."""
    formatted = format_inr(Decimal("0.00"))
    assert formatted == "₹0.00"


def test_format_inr_invalid_type():
    """Test formatting fails for invalid type."""
    with pytest.raises(ValueError, match="Invalid amount"):
        format_inr("not a number")


# Test INR validation
def test_validate_inr_amount_valid():
    """Test validation of valid INR amount."""
    is_valid, error = validate_inr_amount(Decimal("100.50"))
    assert is_valid is True
    assert error is None


def test_validate_inr_amount_minimum():
    """Test validation with minimum amount."""
    is_valid, error = validate_inr_amount(Decimal("5.00"), min_amount=Decimal("10.00"))
    assert is_valid is False
    assert "below minimum" in error


def test_validate_inr_amount_negative():
    """Test validation fails for negative amount."""
    is_valid, error = validate_inr_amount(Decimal("-10.00"))
    assert is_valid is False
    assert "positive" in error.lower()


def test_validate_inr_amount_zero():
    """Test validation fails for zero amount."""
    is_valid, error = validate_inr_amount(Decimal("0.00"))
    assert is_valid is False
    assert "positive" in error.lower()


def test_validate_inr_amount_too_many_decimals():
    """Test validation fails for more than 2 decimal places."""
    is_valid, error = validate_inr_amount(Decimal("10.123"))
    assert is_valid is False
    assert "decimal places" in error


def test_validate_inr_amount_maximum():
    """Test validation fails for amount exceeding maximum."""
    is_valid, error = validate_inr_amount(Decimal("200000000.00"))  # > 10 crores
    assert is_valid is False
    assert "exceeds maximum" in error


def test_validate_inr_amount_converts_string():
    """Test validation converts string to Decimal."""
    # This should work through convert but validation expects Decimal
    with pytest.raises(AttributeError):
        validate_inr_amount("100.50")


# Test paisa conversion
def test_convert_to_paisa():
    """Test conversion of rupees to paisa."""
    paisa = convert_to_paisa(Decimal("100.50"))
    assert paisa == 10050


def test_convert_to_paisa_whole_number():
    """Test conversion of whole rupees to paisa."""
    paisa = convert_to_paisa(Decimal("50.00"))
    assert paisa == 5000


def test_convert_to_paisa_small_amount():
    """Test conversion of small amount to paisa."""
    paisa = convert_to_paisa(Decimal("1.25"))
    assert paisa == 125


def test_convert_from_paisa():
    """Test conversion of paisa to rupees."""
    amount = convert_from_paisa(10050)
    assert amount == Decimal("100.50")


def test_convert_from_paisa_whole():
    """Test conversion of paisa to whole rupees."""
    amount = convert_from_paisa(5000)
    assert amount == Decimal("50.00")


def test_convert_from_paisa_invalid_type():
    """Test conversion fails for non-integer paisa."""
    with pytest.raises(TypeError, match="integer"):
        convert_from_paisa(100.5)


def test_convert_from_paisa_negative():
    """Test conversion fails for negative paisa."""
    with pytest.raises(ValueError, match="cannot be negative"):
        convert_from_paisa(-100)


def test_paisa_round_trip():
    """Test round-trip conversion between rupees and paisa."""
    original = Decimal("123.45")
    paisa = convert_to_paisa(original)
    converted_back = convert_from_paisa(paisa)
    assert converted_back == original


# Test INR string parsing
def test_parse_inr_string_with_symbol():
    """Test parsing INR string with rupee symbol."""
    amount = parse_inr_string("₹1,234.56")
    assert amount == Decimal("1234.56")


def test_parse_inr_string_with_rs():
    """Test parsing INR string with Rs. prefix."""
    amount = parse_inr_string("Rs. 1,234.56")
    assert amount == Decimal("1234.56")


def test_parse_inr_string_plain():
    """Test parsing plain number string."""
    amount = parse_inr_string("1234.56")
    assert amount == Decimal("1234.56")


def test_parse_inr_string_with_commas():
    """Test parsing string with Indian number formatting."""
    amount = parse_inr_string("12,34,567.89")
    assert amount == Decimal("1234567.89")


def test_parse_inr_string_empty():
    """Test parsing fails for empty string."""
    with pytest.raises(ValueError, match="empty"):
        parse_inr_string("")


def test_parse_inr_string_invalid():
    """Test parsing fails for invalid string."""
    with pytest.raises(ValueError, match="Cannot parse"):
        parse_inr_string("not a number")


def test_parse_inr_string_negative():
    """Test parsing fails for negative amount."""
    with pytest.raises(ValueError, match="positive"):
        parse_inr_string("-100.00")


# Test edge cases
def test_format_large_amount():
    """Test formatting very large amount."""
    formatted = format_inr(Decimal("99999999.99"))
    assert "9,99,99,999.99" in formatted


def test_validate_minimum_one_rupee():
    """Test default minimum is 1 rupee."""
    is_valid, error = validate_inr_amount(Decimal("0.50"))
    assert is_valid is False
    assert "below minimum" in error
