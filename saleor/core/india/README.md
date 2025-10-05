# Saleor India - Backend Features

This module provides comprehensive India-specific features for the Saleor e-commerce platform, including GST compliance, INR currency handling, Razorpay UPI payment integration, and regional address validation.

## Features

### 1. GST (Goods and Services Tax) Support

#### GSTIN Validation
- Full validation of 15-character GSTIN format
- State code extraction and validation
- Checksum verification using official algorithm
- Comprehensive error messages

```python
from saleor.core.india.gst import validate_gstin

is_valid, error = validate_gstin("27AAPFU0939F1ZV")
if is_valid:
    print("Valid GSTIN")
```

#### GST Calculation
- Automatic CGST/SGST split for intra-state transactions
- IGST calculation for inter-state transactions
- Support for all standard GST rates (0%, 5%, 12%, 18%, 28%)
- Handle both inclusive and exclusive GST amounts

```python
from saleor.core.india.gst import calculate_gst
from decimal import Decimal

gst_calc = calculate_gst(
    amount=Decimal("1000.00"),
    gst_rate=Decimal("18.00"),
    billing_state_code="27",  # Maharashtra
    shipping_state_code="07",  # Delhi
    include_gst=False
)

print(f"Base: ₹{gst_calc.base_amount}")
print(f"IGST: ₹{gst_calc.igst}")
print(f"Total: ₹{gst_calc.total_amount}")
```

### 2. INR Currency Handling

#### Indian Number Formatting
- Proper lakh and crore formatting (1,00,000 and 1,00,00,000)
- Rupee symbol (₹) support
- Two decimal place precision

```python
from saleor.core.india.currency import format_inr
from decimal import Decimal

formatted = format_inr(Decimal("1234567.89"))
# Output: ₹12,34,567.89
```

#### Amount Validation
- Minimum and maximum amount checks
- Decimal place validation
- Type safety with Decimal

```python
from saleor.core.india.currency import validate_inr_amount

is_valid, error = validate_inr_amount(Decimal("100.50"))
```

#### Paisa Conversion
- Convert between rupees and paisa (1 rupee = 100 paisa)
- Required for payment gateway integration

```python
from saleor.core.india.currency import convert_to_paisa, convert_from_paisa

paisa = convert_to_paisa(Decimal("100.50"))  # Returns 10050
amount = convert_from_paisa(10050)  # Returns Decimal("100.50")
```

### 3. Indian Address Validation

#### PIN Code Validation
- 6-digit format validation
- Cannot start with 0
- Region code validation

```python
from saleor.core.india.address import validate_indian_pincode

is_valid, error = validate_indian_pincode("400001")
```

#### State Validation
- Support for all 38 Indian states and union territories
- State code and name mapping
- Case-insensitive matching
- Partial name matching

```python
from saleor.core.india.address import validate_indian_state, get_state_code

is_valid, state_code, error = validate_indian_state("Maharashtra")
# Returns: (True, "27", None)

code = get_state_code("Delhi")  # Returns "07"
```

#### Complete Address Validation
- Validates all address components
- Returns normalized address data
- Country code enforcement (must be "IN")

```python
from saleor.core.india.address import validate_indian_address

address = validate_indian_address(
    street_address_1="123 MG Road",
    city="Mumbai",
    state="Maharashtra",
    postal_code="400001",
    country="IN"
)
```

### 4. Order Management

#### India-Specific Order Creation
- Automatic GST calculation on order creation
- B2B vs B2C transaction handling
- Invoice number generation
- Place of supply determination

```python
from saleor.core.india.order import create_indian_order

indian_order = create_indian_order(
    order=order,
    gst_rate=Decimal("18.00"),
    customer_gstin="27AAPFU0939F1ZV",  # Optional for B2B
    include_gst_in_price=True
)
```

#### Order GST Breakdown
- Line-item level GST calculation
- Total GST aggregation
- Support for mixed GST rates

```python
from saleor.core.india.order import calculate_order_gst_breakdown

breakdown = calculate_order_gst_breakdown(
    order_lines=order.lines.all(),
    billing_state_code="27",
    shipping_state_code="07"
)
```

### 5. Discount Management with GST

#### Discount Application
- Automatic GST recalculation after discount
- Support for fixed and percentage discounts
- Discount applied on base amount (before GST)
- Savings calculation

```python
from saleor.core.india.discount import apply_discount_with_gst

discount_result = apply_discount_with_gst(
    original_amount=Decimal("1180.00"),  # Including GST
    discount_value=Decimal("10.00"),  # 10% off
    discount_type="percentage",
    gst_rate=Decimal("18.00"),
    billing_state_code="27"
)
```

#### Bulk Discount Tiers
- Quantity-based discount tiers
- Automatic tier selection
- GST-aware pricing

```python
from saleor.core.india.discount import calculate_bulk_discount_with_gst

discount_tiers = [
    {"min_qty": 5, "discount_pct": 10},
    {"min_qty": 10, "discount_pct": 20},
]

bulk_result = calculate_bulk_discount_with_gst(
    item_price=Decimal("118.00"),
    quantity=15,
    discount_tiers=discount_tiers,
    gst_rate=Decimal("18.00"),
    billing_state_code="27"
)
```

### 6. Razorpay UPI Payment Integration

#### UPI Payment Support
- Virtual Payment Address (VPA) validation
- Mock mode for testing
- Real-time payment processing
- Secure transaction handling

```python
from saleor.payment.gateways.razorpay.upi import validate_upi_vpa

is_valid, error = validate_upi_vpa("user@paytm")
```

#### Enhanced Razorpay Plugin
- Full INR support
- UPI payment method
- GST validation (optional)
- Mock API for testing
- Comprehensive error logging

```python
# Configuration in Saleor settings
PLUGINS = [
    "saleor.payment.gateways.razorpay.india_plugin.RazorpayIndiaGatewayPlugin",
]
```

## Installation

### Requirements
```
python >= 3.10
razorpay >= 1.3.0
```

### Setup

1. Install dependencies:
```bash
pip install razorpay
```

2. Configure Razorpay plugin in Saleor admin:
   - Public API key
   - Secret API key
   - Enable UPI payments
   - Enable mock mode (for testing)
   - Enable GST validation (optional)

## Testing

### Running Tests

```bash
# Run all India module tests
pytest saleor/core/india/tests/

# Run specific test file
pytest saleor/core/india/tests/test_gst.py

# Run with coverage
pytest saleor/core/india/tests/ --cov=saleor.core.india

# Run UPI payment tests
pytest saleor/payment/gateways/razorpay/tests/test_upi.py

# Use database reuse for faster tests
pytest saleor/core/india/tests/ --reuse-db
```

### Test Coverage

- **GST Module**: 100% coverage
  - GSTIN validation
  - GST calculation (intra-state and inter-state)
  - Rate determination

- **Currency Module**: 100% coverage
  - INR formatting
  - Amount validation
  - Paisa conversion

- **Address Module**: 100% coverage
  - PIN code validation
  - State validation
  - Complete address validation

- **Discount Module**: 100% coverage
  - Discount application with GST
  - Bulk discount tiers
  - Eligibility validation

- **UPI Module**: 100% coverage
  - VPA validation
  - Payment request creation
  - Mock payment processing

## API Reference

### GST Module (`saleor.core.india.gst`)

#### `validate_gstin(gstin: str) -> tuple[bool, Optional[str]]`
Validate a GSTIN (GST Identification Number).

**Parameters:**
- `gstin`: 15-character GSTIN string

**Returns:**
- `(True, None)` if valid
- `(False, error_message)` if invalid

#### `calculate_gst(...) -> GSTCalculation`
Calculate GST breakdown for an amount.

**Parameters:**
- `amount`: Base amount (Decimal)
- `gst_rate`: GST rate as percentage (Decimal)
- `billing_state_code`: Two-digit state code
- `shipping_state_code`: Two-digit state code (optional)
- `include_gst`: Whether amount includes GST (bool)

**Returns:**
- `GSTCalculation` object with detailed breakdown

### Currency Module (`saleor.core.india.currency`)

#### `format_inr(amount: Decimal, include_symbol: bool = True) -> str`
Format amount as Indian Rupees.

#### `validate_inr_amount(amount: Decimal, min_amount: Optional[Decimal] = None) -> tuple[bool, Optional[str]]`
Validate INR amount.

#### `convert_to_paisa(amount: Decimal) -> int`
Convert rupees to paisa.

#### `convert_from_paisa(paisa: int) -> Decimal`
Convert paisa to rupees.

### Address Module (`saleor.core.india.address`)

#### `validate_indian_address(...) -> dict`
Validate complete Indian address.

**Raises:**
- `IndianAddressValidationError` if validation fails

### Discount Module (`saleor.core.india.discount`)

#### `apply_discount_with_gst(...) -> dict`
Apply discount with GST recalculation.

### UPI Module (`saleor.payment.gateways.razorpay.upi`)

#### `validate_upi_vpa(vpa: str) -> tuple[bool, Optional[str]]`
Validate UPI Virtual Payment Address.

#### `process_upi_payment(payment_information, config, mock_mode=False) -> GatewayResponse`
Process UPI payment.

## Error Handling

All modules implement comprehensive error handling:

1. **Input Validation**: All inputs are validated before processing
2. **Type Safety**: Uses Decimal for all monetary values
3. **Error Logging**: All errors are logged with context
4. **User-Friendly Messages**: Clear error messages for validation failures

Example error handling:
```python
from saleor.core.india.gst import validate_gstin
import logging

logger = logging.getLogger(__name__)

is_valid, error = validate_gstin(user_input)
if not is_valid:
    logger.error(f"GSTIN validation failed: {error}")
    # Handle error appropriately
```

## Security Considerations

1. **Input Sanitization**: All inputs are sanitized and validated
2. **Decimal Precision**: Uses Decimal type to avoid floating-point errors
3. **API Key Protection**: Razorpay keys stored securely in configuration
4. **Mock Mode**: Separate mock mode for testing (never use in production)
5. **Transaction Logging**: All payment transactions are logged

## Best Practices

1. **Always use Decimal**: Use `Decimal` type for all monetary values
2. **Validate Early**: Validate inputs as early as possible
3. **Log Everything**: Use comprehensive logging for debugging
4. **Test Thoroughly**: Write unit tests for all features
5. **Mock in Testing**: Use mock mode for UPI payments in tests
6. **Handle Errors**: Always handle validation errors gracefully

## License

This module is part of the Saleor project and follows the same BSD license.

## Contributing

When contributing to this module:

1. Follow existing code style
2. Write comprehensive tests
3. Update documentation
4. Use stepwise implementation with comments
5. Add error logging
6. Validate all inputs

## Support

For issues or questions:
- Check existing tests for usage examples
- Review error logs for debugging
- Refer to Saleor documentation
- Open an issue on GitHub
