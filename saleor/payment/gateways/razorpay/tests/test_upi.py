"""Unit tests for Razorpay UPI payment functionality."""

from decimal import Decimal

import pytest

from .... import TransactionKind
from ....interface import GatewayConfig, PaymentData
from ..upi import (
    UPIValidationError,
    create_upi_payment_request,
    process_upi_payment,
    validate_upi_vpa,
)


# Fixtures
@pytest.fixture
def gateway_config():
    """Create gateway configuration for testing."""
    return GatewayConfig(
        gateway_name="razorpay",
        auto_capture=True,
        supported_currencies="INR",
        connection_params={
            "public_key": "test_public_key",
            "private_key": "test_private_key",
        },
    )


@pytest.fixture
def upi_payment_data():
    """Create UPI payment data for testing."""
    return PaymentData(
        gateway="razorpay",
        amount=Decimal("100.00"),
        currency="INR",
        billing=None,
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="order_123",
        customer_ip_address="127.0.0.1",
        customer_email="test@example.com",
        data={"upi_vpa": "test@paytm", "payment_method": "upi"},
    )


# Test UPI VPA validation
def test_validate_upi_vpa_valid():
    """Test validation of valid UPI VPA."""
    is_valid, error = validate_upi_vpa("user@paytm")
    assert is_valid is True
    assert error is None


def test_validate_upi_vpa_valid_numeric():
    """Test validation of valid numeric UPI VPA."""
    is_valid, error = validate_upi_vpa("9876543210@ybl")
    assert is_valid is True
    assert error is None


def test_validate_upi_vpa_empty():
    """Test validation fails for empty VPA."""
    is_valid, error = validate_upi_vpa("")
    assert is_valid is False
    assert "required" in error.lower()


def test_validate_upi_vpa_no_at_symbol():
    """Test validation fails for VPA without @ symbol."""
    is_valid, error = validate_upi_vpa("userpaytm")
    assert is_valid is False
    assert "@" in error


def test_validate_upi_vpa_multiple_at_symbols():
    """Test validation fails for VPA with multiple @ symbols."""
    is_valid, error = validate_upi_vpa("user@bank@extra")
    assert is_valid is False
    assert "format" in error.lower()


def test_validate_upi_vpa_short_username():
    """Test validation fails for too short username."""
    is_valid, error = validate_upi_vpa("ab@paytm")
    assert is_valid is False
    assert "3 characters" in error


def test_validate_upi_vpa_short_bank_code():
    """Test validation fails for too short bank code."""
    is_valid, error = validate_upi_vpa("user@p")
    assert is_valid is False
    assert "bank code" in error.lower()


# Test UPI payment request creation
def test_create_upi_payment_request(upi_payment_data, gateway_config):
    """Test creation of UPI payment request."""
    request = create_upi_payment_request(upi_payment_data, gateway_config)

    assert request["amount"] == 10000  # 100.00 INR in paisa
    assert request["currency"] == "INR"
    assert request["method"] == "upi"
    assert request["vpa"] == "test@paytm"
    assert request["order_id"] == "order_123"


def test_create_upi_payment_request_invalid_currency(gateway_config):
    """Test payment request fails for non-INR currency."""
    payment_data = PaymentData(
        gateway="razorpay",
        amount=Decimal("100.00"),
        currency="USD",  # Invalid for UPI
        billing=None,
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="order_123",
        customer_ip_address="127.0.0.1",
        customer_email="test@example.com",
        data={"upi_vpa": "test@paytm"},
    )

    with pytest.raises(UPIValidationError, match="INR currency"):
        create_upi_payment_request(payment_data, gateway_config)


def test_create_upi_payment_request_missing_vpa(gateway_config):
    """Test payment request fails for missing VPA."""
    payment_data = PaymentData(
        gateway="razorpay",
        amount=Decimal("100.00"),
        currency="INR",
        billing=None,
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="order_123",
        customer_ip_address="127.0.0.1",
        customer_email="test@example.com",
        data={},  # No VPA
    )

    with pytest.raises(UPIValidationError, match="VPA is required"):
        create_upi_payment_request(payment_data, gateway_config)


def test_create_upi_payment_request_invalid_vpa(gateway_config):
    """Test payment request fails for invalid VPA."""
    payment_data = PaymentData(
        gateway="razorpay",
        amount=Decimal("100.00"),
        currency="INR",
        billing=None,
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="order_123",
        customer_ip_address="127.0.0.1",
        customer_email="test@example.com",
        data={"upi_vpa": "invalid_vpa"},  # Invalid format
    )

    with pytest.raises(UPIValidationError, match="VPA"):
        create_upi_payment_request(payment_data, gateway_config)


# Test UPI payment processing
def test_process_upi_payment_mock_mode(upi_payment_data, gateway_config):
    """Test UPI payment processing in mock mode."""
    response = process_upi_payment(upi_payment_data, gateway_config, mock_mode=True)

    assert response.is_success is True
    assert response.error is None
    assert response.amount == Decimal("100.00")
    assert response.currency == "INR"
    assert response.kind == TransactionKind.CAPTURE
    assert "upi_mock_" in response.transaction_id


def test_process_upi_payment_invalid_data(gateway_config):
    """Test UPI payment fails with invalid data."""
    payment_data = PaymentData(
        gateway="razorpay",
        amount=Decimal("-100.00"),  # Negative amount
        currency="INR",
        billing=None,
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="order_123",
        customer_ip_address="127.0.0.1",
        customer_email="test@example.com",
        data={"upi_vpa": "test@paytm"},
    )

    response = process_upi_payment(payment_data, gateway_config, mock_mode=True)

    assert response.is_success is False
    assert response.error is not None


# Test mock payment response
def test_mock_upi_payment_response_structure(upi_payment_data, gateway_config):
    """Test mock UPI payment response has correct structure."""
    response = process_upi_payment(upi_payment_data, gateway_config, mock_mode=True)

    assert hasattr(response, "transaction_id")
    assert hasattr(response, "is_success")
    assert hasattr(response, "amount")
    assert hasattr(response, "currency")
    assert hasattr(response, "kind")
    assert hasattr(response, "raw_response")

    raw_response = response.raw_response
    assert "id" in raw_response
    assert "amount" in raw_response
    assert "currency" in raw_response
    assert "status" in raw_response
    assert "method" in raw_response
    assert raw_response["method"] == "upi"


# Test edge cases
def test_process_upi_payment_large_amount(gateway_config):
    """Test UPI payment with large amount."""
    payment_data = PaymentData(
        gateway="razorpay",
        amount=Decimal("50000.00"),  # Large amount
        currency="INR",
        billing=None,
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="order_123",
        customer_ip_address="127.0.0.1",
        customer_email="test@example.com",
        data={"upi_vpa": "test@paytm"},
    )

    response = process_upi_payment(payment_data, gateway_config, mock_mode=True)

    assert response.is_success is True
    assert response.amount == Decimal("50000.00")


def test_process_upi_payment_minimum_amount(gateway_config):
    """Test UPI payment with minimum amount."""
    payment_data = PaymentData(
        gateway="razorpay",
        amount=Decimal("1.00"),  # Minimum amount
        currency="INR",
        billing=None,
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="order_123",
        customer_ip_address="127.0.0.1",
        customer_email="test@example.com",
        data={"upi_vpa": "test@paytm"},
    )

    response = process_upi_payment(payment_data, gateway_config, mock_mode=True)

    assert response.is_success is True
    assert response.amount == Decimal("1.00")
