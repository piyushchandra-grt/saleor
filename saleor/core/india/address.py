"""Indian address validation utilities."""

import logging
import re

logger = logging.getLogger(__name__)

# Step 1: Define Indian states with their codes
INDIAN_STATES = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman and Diu",
    "26": "Dadra and Nagar Haveli",
    "27": "Maharashtra",
    "28": "Andhra Pradesh",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
}

# Step 2: Define reverse mapping (state name to code)
STATE_NAME_TO_CODE = {v.upper(): k for k, v in INDIAN_STATES.items()}

# Step 3: Define Indian PIN code pattern (6 digits)
PINCODE_PATTERN = re.compile(r"^[1-9][0-9]{5}$")


class IndianAddressValidationError(Exception):
    """Custom exception for Indian address validation errors."""


def validate_indian_pincode(pincode: str) -> tuple[bool, str | None]:
    """Step 4: Validate Indian PIN code.

    Args:
        pincode: PIN code to validate

    Returns:
        Tuple of (is_valid, error_message)

    """
    # Step 4.1: Input validation
    if not pincode:
        error_msg = "PIN code is required"
        logger.warning(f"PIN code validation failed: {error_msg}")
        return False, error_msg

    # Step 4.2: Remove spaces and hyphens
    pincode = pincode.strip().replace(" ", "").replace("-", "")

    # Step 4.3: Validate format (6 digits, cannot start with 0)
    if not PINCODE_PATTERN.match(pincode):
        error_msg = "PIN code must be 6 digits and cannot start with 0"
        logger.warning(f"PIN code validation failed: {error_msg} for PIN: {pincode}")
        return False, error_msg

    # Step 4.4: Validate first digit (represents region)
    first_digit = int(pincode[0])
    if not (1 <= first_digit <= 9):
        error_msg = f"Invalid PIN code region: {first_digit}"
        logger.warning(f"PIN code validation failed: {error_msg}")
        return False, error_msg

    logger.info(f"PIN code validation successful: {pincode}")
    return True, None


def validate_indian_state(state: str) -> tuple[bool, str | None, str | None]:
    """Step 5: Validate Indian state name or code.

    Args:
        state: State name or code

    Returns:
        Tuple of (is_valid, state_code, error_message)

    """
    # Step 5.1: Input validation
    if not state:
        error_msg = "State is required"
        logger.warning(f"State validation failed: {error_msg}")
        return False, None, error_msg

    state = state.strip()

    # Step 5.2: Check if it's a state code (2 digits)
    if len(state) == 2 and state.isdigit():
        if state in INDIAN_STATES:
            logger.info(f"State code validation successful: {state}")
            return True, state, None
        error_msg = f"Invalid state code: {state}"
        logger.warning(f"State validation failed: {error_msg}")
        return False, None, error_msg

    # Step 5.3: Check if it's a state name
    state_upper = state.upper()
    if state_upper in STATE_NAME_TO_CODE:
        state_code = STATE_NAME_TO_CODE[state_upper]
        logger.info(f"State name validation successful: {state} -> {state_code}")
        return True, state_code, None

    # Step 5.4: Try partial matching (case-insensitive)
    for state_name, code in STATE_NAME_TO_CODE.items():
        if state_upper in state_name or state_name in state_upper:
            logger.info(f"State partial match found: {state} -> {code}")
            return True, code, None

    error_msg = f"Invalid state name or code: {state}"
    logger.warning(f"State validation failed: {error_msg}")
    return False, None, error_msg


def validate_indian_address(
    street_address_1: str,
    city: str,
    state: str,
    postal_code: str,
    country: str = "IN",
    street_address_2: str | None = None,
) -> dict:
    """Step 6: Validate complete Indian address.

    Args:
        street_address_1: Primary street address
        city: City name
        state: State name or code
        postal_code: PIN code
        country: Country code (must be 'IN')
        street_address_2: Secondary street address (optional)

    Returns:
        Dictionary with validation results and normalized data

    Raises:
        IndianAddressValidationError: If validation fails

    """
    errors = []

    # Step 6.1: Validate country code
    if country.upper() != "IN":
        error_msg = f"Invalid country code for Indian address: {country}"
        logger.error(error_msg)
        raise IndianAddressValidationError(error_msg)

    # Step 6.2: Validate required fields
    if not street_address_1 or not street_address_1.strip():
        errors.append("Street address is required")

    if not city or not city.strip():
        errors.append("City is required")

    # Step 6.3: Validate PIN code
    pincode_valid, pincode_error = validate_indian_pincode(postal_code)
    if not pincode_valid:
        errors.append(pincode_error)

    # Step 6.4: Validate state
    state_valid, state_code, state_error = validate_indian_state(state)
    if not state_valid:
        errors.append(state_error)

    # Step 6.5: If there are validation errors, raise exception
    if errors:
        error_msg = "; ".join(errors)
        logger.error(f"Indian address validation failed: {error_msg}")
        raise IndianAddressValidationError(error_msg)

    # Step 6.6: Return normalized address data
    normalized_address = {
        "street_address_1": street_address_1.strip(),
        "street_address_2": street_address_2.strip() if street_address_2 else "",
        "city": city.strip(),
        "state": INDIAN_STATES[state_code],
        "state_code": state_code,
        "postal_code": postal_code.strip().replace(" ", "").replace("-", ""),
        "country": "IN",
        "is_valid": True,
    }

    logger.info(f"Indian address validation successful: {city}, {state_code}")
    return normalized_address


def get_state_code(state: str) -> str | None:
    """Get state code from state name or return the code if already a code.

    Args:
        state: State name or code

    Returns:
        Two-digit state code or None if invalid

    """
    is_valid, state_code, _ = validate_indian_state(state)
    return state_code if is_valid else None


def get_state_name(state_code: str) -> str | None:
    """Get state name from state code.

    Args:
        state_code: Two-digit state code

    Returns:
        State name or None if invalid

    """
    return INDIAN_STATES.get(state_code)
