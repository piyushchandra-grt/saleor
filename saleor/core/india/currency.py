"""INR (Indian Rupee) currency handling utilities."""

import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def format_inr(amount: Decimal, include_symbol: bool = True) -> str:
    """Step 1: Format amount as Indian Rupees with proper formatting.

    Indian number system uses lakhs and crores:
    - 1,00,000 (1 lakh = 100,000)
    - 1,00,00,000 (1 crore = 10,000,000)

    Args:
        amount: Amount to format
        include_symbol: Whether to include ₹ symbol

    Returns:
        Formatted string representation

    """
    # Step 1.1: Input validation
    if not isinstance(amount, Decimal):
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError) as e:
            error_msg = f"Invalid amount for INR formatting: {amount}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    # Step 1.2: Round to 2 decimal places
    amount = amount.quantize(Decimal("0.01"))

    # Step 1.3: Split into integer and decimal parts
    amount_str = str(amount)
    if "." in amount_str:
        integer_part, decimal_part = amount_str.split(".")
    else:
        integer_part, decimal_part = amount_str, "00"

    # Step 1.4: Apply Indian number formatting
    if len(integer_part) <= 3:
        formatted = integer_part
    else:
        # Last 3 digits
        last_three = integer_part[-3:]
        # Remaining digits
        remaining = integer_part[:-3]

        # Add commas every 2 digits for the remaining part (from right to left)
        formatted_remaining = ""
        while remaining:
            if formatted_remaining:
                formatted_remaining = "," + formatted_remaining
            formatted_remaining = remaining[-2:] + formatted_remaining
            remaining = remaining[:-2]

        formatted = formatted_remaining + "," + last_three

    # Step 1.5: Add decimal part
    formatted = f"{formatted}.{decimal_part}"

    # Step 1.6: Add currency symbol if requested
    if include_symbol:
        formatted = f"₹{formatted}"

    logger.debug(f"Formatted INR amount: {amount} -> {formatted}")
    return formatted


def validate_inr_amount(
    amount: Decimal, min_amount: Decimal | None = None
) -> tuple[bool, str | None]:
    """Step 2: Validate INR amount for payment processing.

    Args:
        amount: Amount to validate
        min_amount: Minimum allowed amount (default: ₹1.00)

    Returns:
        Tuple of (is_valid, error_message)

    """
    # Step 2.1: Set default minimum amount
    if min_amount is None:
        min_amount = Decimal("1.00")

    # Step 2.2: Type validation
    if not isinstance(amount, Decimal):
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError):
            error_msg = f"Invalid amount type: {type(amount)}"
            logger.warning(f"INR validation failed: {error_msg}")
            return False, error_msg

    # Step 2.3: Check if amount is positive
    if amount <= 0:
        error_msg = f"Amount must be positive: {amount}"
        logger.warning(f"INR validation failed: {error_msg}")
        return False, error_msg

    # Step 2.4: Check minimum amount
    if amount < min_amount:
        error_msg = (
            f"Amount {format_inr(amount)} is below minimum {format_inr(min_amount)}"
        )
        logger.warning(f"INR validation failed: {error_msg}")
        return False, error_msg

    # Step 2.5: Check decimal places (max 2)
    if amount.as_tuple().exponent < -2:
        error_msg = "Amount cannot have more than 2 decimal places"
        logger.warning(f"INR validation failed: {error_msg}")
        return False, error_msg

    # Step 2.6: Check maximum amount (for security - 10 crores)
    max_amount = Decimal("100000000.00")  # 10 crore rupees
    if amount > max_amount:
        error_msg = (
            f"Amount {format_inr(amount)} exceeds maximum {format_inr(max_amount)}"
        )
        logger.warning(f"INR validation failed: {error_msg}")
        return False, error_msg

    logger.info(f"INR validation successful: {format_inr(amount)}")
    return True, None


def convert_to_paisa(amount: Decimal) -> int:
    """Step 3: Convert INR amount to paisa (smallest unit).

    Used for payment gateway integration (e.g., Razorpay).

    Args:
        amount: Amount in rupees

    Returns:
        Amount in paisa (1 rupee = 100 paisa)

    """
    # Step 3.1: Validate amount
    is_valid, error = validate_inr_amount(amount)
    if not is_valid:
        logger.error(f"Cannot convert invalid amount to paisa: {error}")
        raise ValueError(error)

    # Step 3.2: Convert to paisa (multiply by 100)
    paisa = int(amount * 100)

    logger.debug(f"Converted to paisa: {format_inr(amount)} -> {paisa} paisa")
    return paisa


def convert_from_paisa(paisa: int) -> Decimal:
    """Step 4: Convert paisa to INR amount.

    Args:
        paisa: Amount in paisa

    Returns:
        Amount in rupees as Decimal

    """
    # Step 4.1: Validate paisa value
    if not isinstance(paisa, int):
        error_msg = f"Paisa must be an integer: {type(paisa)}"
        logger.error(error_msg)
        raise TypeError(error_msg)

    if paisa < 0:
        error_msg = f"Paisa cannot be negative: {paisa}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Step 4.2: Convert to rupees (divide by 100)
    amount = Decimal(paisa) / 100

    # Step 4.3: Round to 2 decimal places
    amount = amount.quantize(Decimal("0.01"))

    logger.debug(f"Converted from paisa: {paisa} paisa -> {format_inr(amount)}")
    return amount


def parse_inr_string(amount_str: str) -> Decimal:
    """Step 5: Parse INR string to Decimal amount.

    Handles various formats:
    - ₹1,23,456.78
    - Rs. 1,23,456.78
    - 1,23,456.78
    - 123456.78

    Args:
        amount_str: String representation of amount

    Returns:
        Decimal amount

    Raises:
        ValueError: If string cannot be parsed

    """
    # Step 5.1: Input validation
    if not amount_str:
        error_msg = "Amount string is empty"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Step 5.2: Remove currency symbols and spaces
    cleaned = amount_str.strip()
    cleaned = cleaned.replace("₹", "").replace("Rs.", "").replace("Rs", "")
    cleaned = cleaned.replace("INR", "").strip()

    # Step 5.3: Remove commas
    cleaned = cleaned.replace(",", "")

    # Step 5.4: Parse to Decimal
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError) as e:
        error_msg = f"Cannot parse amount string: {amount_str}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    # Step 5.5: Validate the parsed amount
    is_valid, error = validate_inr_amount(amount)
    if not is_valid:
        logger.error(f"Parsed amount is invalid: {error}")
        raise ValueError(error)

    logger.info(f"Parsed INR string: '{amount_str}' -> {format_inr(amount)}")
    return amount
