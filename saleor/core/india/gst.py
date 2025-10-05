"""GST (Goods and Services Tax) validation and calculation utilities for India."""

import logging
import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

logger = logging.getLogger(__name__)


class GSTRate(Enum):
    """Standard GST rates in India."""

    ZERO = Decimal("0.00")
    FIVE = Decimal("5.00")
    TWELVE = Decimal("12.00")
    EIGHTEEN = Decimal("18.00")
    TWENTY_EIGHT = Decimal("28.00")


@dataclass
class GSTCalculation:
    """Result of GST calculation."""

    base_amount: Decimal
    gst_rate: Decimal
    cgst: Decimal  # Central GST
    sgst: Decimal  # State GST
    igst: Decimal  # Integrated GST (for inter-state)
    total_gst: Decimal
    total_amount: Decimal
    is_inter_state: bool


# Step 1: Define GSTIN validation regex pattern
# GSTIN Format: 2 digits (state code) + 10 chars (PAN) + 1 char (entity number)
#               + 1 char (default Z) + 1 alphanumeric (checksum)
GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


def validate_gstin(gstin: str) -> tuple[bool, str | None]:
    """Step 2: Validate a GSTIN (GST Identification Number).

    Args:
        gstin: The GSTIN string to validate

    Returns:
        Tuple of (is_valid, error_message)

    """
    # Step 2.1: Input validation - check if GSTIN is provided
    if not gstin:
        error_msg = "GSTIN is required"
        logger.warning(f"GSTIN validation failed: {error_msg}")
        return False, error_msg

    # Step 2.2: Remove whitespace and convert to uppercase
    gstin = gstin.strip().upper()

    # Step 2.3: Check length (must be 15 characters)
    if len(gstin) != 15:
        error_msg = f"GSTIN must be 15 characters long, got {len(gstin)}"
        logger.warning(f"GSTIN validation failed: {error_msg} for GSTIN: {gstin}")
        return False, error_msg

    # Step 2.4: Validate format using regex pattern
    if not GSTIN_PATTERN.match(gstin):
        error_msg = "GSTIN format is invalid"
        logger.warning(f"GSTIN validation failed: {error_msg} for GSTIN: {gstin}")
        return False, error_msg

    # Step 2.5: Extract and validate state code
    state_code = gstin[:2]
    try:
        state_code_int = int(state_code)
        if not (1 <= state_code_int <= 38):  # Valid Indian state codes
            error_msg = f"Invalid state code: {state_code}"
            logger.warning(f"GSTIN validation failed: {error_msg} for GSTIN: {gstin}")
            return False, error_msg
    except ValueError:
        error_msg = f"State code must be numeric: {state_code}"
        logger.warning(f"GSTIN validation failed: {error_msg}")
        return False, error_msg

    # Step 2.6: Validate checksum digit (15th character)
    if not _validate_gstin_checksum(gstin):
        error_msg = "GSTIN checksum validation failed"
        logger.warning(f"GSTIN validation failed: {error_msg} for GSTIN: {gstin}")
        return False, error_msg

    # Step 2.7: Validation successful
    logger.info(f"GSTIN validation successful: {gstin}")
    return True, None


def _validate_gstin_checksum(gstin: str) -> bool:
    """Validate GSTIN checksum using the official algorithm.

    Args:
        gstin: The 15-character GSTIN

    Returns:
        True if checksum is valid, False otherwise

    """
    # Step 1: Define character-to-value mapping for checksum calculation
    char_map = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Step 2: Extract first 14 characters for checksum calculation
    gstin_chars = gstin[:14]
    checksum_char = gstin[14]

    # Step 3: Calculate checksum value
    checksum_value = 0
    for i, char in enumerate(gstin_chars):
        value = char_map.index(char)
        # Multiply by 2 for even positions (0-indexed)
        if i % 2 == 0:
            value *= 2
        # Add quotient and remainder when dividing by char_map length
        checksum_value += value // len(char_map) + value % len(char_map)

    # Step 4: Calculate expected checksum character
    remainder = checksum_value % len(char_map)
    expected_checksum = char_map[(len(char_map) - remainder) % len(char_map)]

    # Step 5: Compare with actual checksum character
    return checksum_char == expected_checksum


def calculate_gst(
    amount: Decimal,
    gst_rate: Decimal,
    billing_state_code: str,
    shipping_state_code: str | None = None,
    include_gst: bool = False,
) -> GSTCalculation:
    """Step 3: Calculate GST breakdown for a given amount.

    Args:
        amount: Base amount (excluding GST if include_gst=False)
        gst_rate: GST rate as percentage (e.g., 18 for 18%)
        billing_state_code: Two-digit state code for billing address
        shipping_state_code: Two-digit state code for shipping address
        include_gst: If True, amount includes GST; extract base amount first

    Returns:
        GSTCalculation object with detailed breakdown

    """
    # Step 3.1: Input validation
    if amount < 0:
        error_msg = f"Amount cannot be negative: {amount}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if gst_rate < 0 or gst_rate > 100:
        error_msg = f"GST rate must be between 0 and 100: {gst_rate}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Step 3.2: Validate state codes
    try:
        billing_code = int(billing_state_code)
        if not (1 <= billing_code <= 38):
            raise ValueError(f"Invalid billing state code: {billing_state_code}")
    except (ValueError, TypeError) as e:
        error_msg = f"Invalid billing state code format: {billing_state_code}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    # Step 3.3: Determine if transaction is inter-state
    is_inter_state = False
    if shipping_state_code:
        try:
            shipping_code = int(shipping_state_code)
            if not (1 <= shipping_code <= 38):
                raise ValueError(f"Invalid shipping state code: {shipping_state_code}")
            is_inter_state = billing_code != shipping_code
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid shipping state code format: {shipping_state_code}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    else:
        shipping_state_code = billing_state_code

    # Step 3.4: Calculate base amount (if GST is included in the amount)
    if include_gst:
        base_amount = (amount * 100) / (100 + gst_rate)
    else:
        base_amount = amount

    # Step 3.5: Round base amount to 2 decimal places
    base_amount = base_amount.quantize(Decimal("0.01"))

    # Step 3.6: Calculate total GST amount
    total_gst = (base_amount * gst_rate / 100).quantize(Decimal("0.01"))

    # Step 3.7: Calculate CGST, SGST, or IGST based on transaction type
    if is_inter_state:
        # Inter-state: Use IGST (Integrated GST)
        igst = total_gst
        cgst = Decimal("0.00")
        sgst = Decimal("0.00")
        logger.info(
            f"Inter-state GST calculation: base={base_amount}, "
            f"IGST={igst}, rate={gst_rate}%"
        )
    else:
        # Intra-state: Split equally between CGST and SGST
        cgst = (total_gst / 2).quantize(Decimal("0.01"))
        sgst = (total_gst / 2).quantize(Decimal("0.01"))
        igst = Decimal("0.00")
        logger.info(
            f"Intra-state GST calculation: base={base_amount}, "
            f"CGST={cgst}, SGST={sgst}, rate={gst_rate}%"
        )

    # Step 3.8: Calculate total amount (base + GST)
    total_amount = (base_amount + total_gst).quantize(Decimal("0.01"))

    # Step 3.9: Return GST calculation object
    return GSTCalculation(
        base_amount=base_amount,
        gst_rate=gst_rate,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_gst=total_gst,
        total_amount=total_amount,
        is_inter_state=is_inter_state,
    )


def get_state_code_from_gstin(gstin: str) -> str:
    """Extract state code from a valid GSTIN.

    Args:
        gstin: Valid GSTIN

    Returns:
        Two-digit state code

    """
    if not gstin or len(gstin) < 2:
        error_msg = "Invalid GSTIN for state code extraction"
        logger.error(error_msg)
        raise ValueError(error_msg)

    return gstin[:2]


def determine_gst_rate_by_category(category: str) -> GSTRate:
    """Determine GST rate based on product category.

    This is a simplified mapping. In production, this should be
    maintained as a database table with proper category taxonomy.

    Args:
        category: Product category name

    Returns:
        Applicable GST rate

    """
    # Map common categories to GST rates
    category_lower = category.lower()

    # 5% GST items
    if any(
        keyword in category_lower
        for keyword in ["food", "grocery", "essential", "medicine", "health"]
    ):
        return GSTRate.FIVE

    # 12% GST items
    if any(
        keyword in category_lower
        for keyword in ["clothing", "fabric", "footwear", "books"]
    ):
        return GSTRate.TWELVE

    # 28% GST items
    if any(
        keyword in category_lower
        for keyword in ["luxury", "automobile", "electronics", "appliance"]
    ):
        return GSTRate.TWENTY_EIGHT

    # Default: 18% GST for most goods and services
    return GSTRate.EIGHTEEN
