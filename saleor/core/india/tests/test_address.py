"""Unit tests for Indian address validation utilities."""

import pytest

from ..address import (
    INDIAN_STATES,
    IndianAddressValidationError,
    get_state_code,
    get_state_name,
    validate_indian_address,
    validate_indian_pincode,
    validate_indian_state,
)


# Test PIN code validation
def test_validate_pincode_valid():
    """Test validation of valid PIN code."""
    is_valid, error = validate_indian_pincode("400001")
    assert is_valid is True
    assert error is None


def test_validate_pincode_with_spaces():
    """Test validation handles spaces in PIN code."""
    is_valid, error = validate_indian_pincode("400 001")
    assert is_valid is True
    assert error is None


def test_validate_pincode_empty():
    """Test validation fails for empty PIN code."""
    is_valid, error = validate_indian_pincode("")
    assert is_valid is False
    assert "required" in error.lower()


def test_validate_pincode_invalid_length():
    """Test validation fails for wrong length."""
    is_valid, error = validate_indian_pincode("12345")
    assert is_valid is False
    assert "6 digits" in error


def test_validate_pincode_starts_with_zero():
    """Test validation fails for PIN code starting with 0."""
    is_valid, error = validate_indian_pincode("012345")
    assert is_valid is False
    assert "6 digits" in error or "cannot start with 0" in error


def test_validate_pincode_non_numeric():
    """Test validation fails for non-numeric PIN code."""
    is_valid, error = validate_indian_pincode("ABCDEF")
    assert is_valid is False
    assert "6 digits" in error


# Test state validation
def test_validate_state_by_code():
    """Test validation of state by code."""
    is_valid, state_code, error = validate_indian_state("27")
    assert is_valid is True
    assert state_code == "27"
    assert error is None


def test_validate_state_by_name():
    """Test validation of state by name."""
    is_valid, state_code, error = validate_indian_state("Maharashtra")
    assert is_valid is True
    assert state_code == "27"
    assert error is None


def test_validate_state_case_insensitive():
    """Test state validation is case-insensitive."""
    is_valid, state_code, error = validate_indian_state("maharashtra")
    assert is_valid is True
    assert state_code == "27"


def test_validate_state_partial_match():
    """Test state validation with partial name match."""
    is_valid, state_code, error = validate_indian_state("Delhi")
    assert is_valid is True
    assert state_code == "07"


def test_validate_state_empty():
    """Test validation fails for empty state."""
    is_valid, state_code, error = validate_indian_state("")
    assert is_valid is False
    assert "required" in error.lower()


def test_validate_state_invalid_code():
    """Test validation fails for invalid state code."""
    is_valid, state_code, error = validate_indian_state("99")
    assert is_valid is False
    assert "Invalid state" in error


def test_validate_state_invalid_name():
    """Test validation fails for invalid state name."""
    is_valid, state_code, error = validate_indian_state("NotAState")
    assert is_valid is False
    assert "Invalid state" in error


# Test complete address validation
def test_validate_complete_address_valid():
    """Test validation of complete valid address."""
    address = validate_indian_address(
        street_address_1="123 MG Road",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400001",
        country="IN",
    )

    assert address["is_valid"] is True
    assert address["street_address_1"] == "123 MG Road"
    assert address["city"] == "Mumbai"
    assert address["state"] == "Maharashtra"
    assert address["state_code"] == "27"
    assert address["postal_code"] == "400001"
    assert address["country"] == "IN"


def test_validate_address_with_optional_fields():
    """Test validation with optional street address 2."""
    address = validate_indian_address(
        street_address_1="Building A",
        street_address_2="Floor 5",
        city="Delhi",
        state="07",
        postal_code="110001",
    )

    assert address["street_address_2"] == "Floor 5"


def test_validate_address_missing_street():
    """Test validation fails for missing street address."""
    with pytest.raises(IndianAddressValidationError, match="Street address"):
        validate_indian_address(
            street_address_1="",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400001",
        )


def test_validate_address_missing_city():
    """Test validation fails for missing city."""
    with pytest.raises(IndianAddressValidationError, match="City"):
        validate_indian_address(
            street_address_1="123 MG Road",
            city="",
            state="Maharashtra",
            postal_code="400001",
        )


def test_validate_address_invalid_pincode():
    """Test validation fails for invalid PIN code."""
    with pytest.raises(IndianAddressValidationError, match="6 digits"):
        validate_indian_address(
            street_address_1="123 MG Road",
            city="Mumbai",
            state="Maharashtra",
            postal_code="12345",
        )


def test_validate_address_invalid_state():
    """Test validation fails for invalid state."""
    with pytest.raises(IndianAddressValidationError, match="Invalid state"):
        validate_indian_address(
            street_address_1="123 MG Road",
            city="Mumbai",
            state="InvalidState",
            postal_code="400001",
        )


def test_validate_address_wrong_country():
    """Test validation fails for non-Indian address."""
    with pytest.raises(IndianAddressValidationError, match="country code"):
        validate_indian_address(
            street_address_1="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="US",
        )


# Test helper functions
def test_get_state_code_by_name():
    """Test getting state code from state name."""
    state_code = get_state_code("Maharashtra")
    assert state_code == "27"


def test_get_state_code_by_code():
    """Test getting state code when already a code."""
    state_code = get_state_code("27")
    assert state_code == "27"


def test_get_state_code_invalid():
    """Test getting state code returns None for invalid state."""
    state_code = get_state_code("InvalidState")
    assert state_code is None


def test_get_state_name():
    """Test getting state name from code."""
    state_name = get_state_name("27")
    assert state_name == "Maharashtra"


def test_get_state_name_invalid():
    """Test getting state name returns None for invalid code."""
    state_name = get_state_name("99")
    assert state_name is None


# Test all Indian states
def test_all_indian_states_defined():
    """Test that all Indian states are defined."""
    assert len(INDIAN_STATES) > 0
    # Check some key states
    assert "27" in INDIAN_STATES  # Maharashtra
    assert "07" in INDIAN_STATES  # Delhi
    assert "29" in INDIAN_STATES  # Karnataka
    assert "33" in INDIAN_STATES  # Tamil Nadu


# Test edge cases
def test_validate_address_whitespace_handling():
    """Test address validation handles extra whitespace."""
    address = validate_indian_address(
        street_address_1="  123 MG Road  ",
        city="  Mumbai  ",
        state="  Maharashtra  ",
        postal_code=" 400 001 ",
    )

    assert address["street_address_1"] == "123 MG Road"
    assert address["city"] == "Mumbai"
    assert address["postal_code"] == "400001"
