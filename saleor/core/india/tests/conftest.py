"""Pytest fixtures for India module tests."""

from decimal import Decimal

import pytest


@pytest.fixture
def valid_gstin():
    """Valid GSTIN for Maharashtra."""
    return "27AAPFU0939F1ZV"


@pytest.fixture
def valid_gstin_delhi():
    """Valid GSTIN for Delhi."""
    return "07AABCU9603R1ZM"


@pytest.fixture
def sample_indian_address():
    """Sample valid Indian address."""
    return {
        "street_address_1": "123 MG Road",
        "street_address_2": "Opposite Central Mall",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "IN",
    }


@pytest.fixture
def sample_delhi_address():
    """Sample valid Delhi address."""
    return {
        "street_address_1": "456 Connaught Place",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "IN",
    }


@pytest.fixture
def inr_amounts():
    """Sample INR amounts for testing."""
    return {
        "small": Decimal("10.50"),
        "medium": Decimal("1000.00"),
        "large": Decimal("100000.00"),
        "very_large": Decimal("10000000.00"),  # 1 crore
    }


@pytest.fixture
def gst_rates():
    """Standard GST rates."""
    return {
        "zero": Decimal("0.00"),
        "five": Decimal("5.00"),
        "twelve": Decimal("12.00"),
        "eighteen": Decimal("18.00"),
        "twenty_eight": Decimal("28.00"),
    }


@pytest.fixture
def discount_tiers():
    """Sample discount tiers for bulk pricing."""
    return [
        {"min_qty": 5, "discount_pct": 5},
        {"min_qty": 10, "discount_pct": 10},
        {"min_qty": 25, "discount_pct": 15},
        {"min_qty": 50, "discount_pct": 20},
    ]
