"""India-specific utilities for Saleor e-commerce platform.

This module provides utilities for:
- GST validation and calculation
- INR currency handling
- Indian address validation
- State code mapping
"""

from .address import INDIAN_STATES, validate_indian_address
from .currency import format_inr, validate_inr_amount
from .gst import GSTCalculation, GSTRate, calculate_gst, validate_gstin

__all__ = [
    "calculate_gst",
    "validate_gstin",
    "GSTRate",
    "GSTCalculation",
    "validate_indian_address",
    "INDIAN_STATES",
    "format_inr",
    "validate_inr_amount",
]
