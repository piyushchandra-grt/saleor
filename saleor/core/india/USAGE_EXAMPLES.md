# Saleor India - Usage Examples

This guide provides practical examples for integrating India-specific features into your Saleor implementation.

## Table of Contents

1. [Creating an Order with GST](#creating-an-order-with-gst)
2. [Applying Discounts with GST](#applying-discounts-with-gst)
3. [Processing UPI Payments](#processing-upi-payments)
4. [Validating Indian Addresses](#validating-indian-addresses)
5. [Complete E-commerce Flow](#complete-e-commerce-flow)

## Creating an Order with GST

### Example 1: Simple Intra-State Order

```python
from decimal import Decimal
from saleor.core.india.gst import calculate_gst
from saleor.core.india.currency import format_inr

# Product price (excluding GST)
product_price = Decimal("1000.00")
gst_rate = Decimal("18.00")

# Calculate GST for intra-state transaction
gst_calc = calculate_gst(
    amount=product_price,
    gst_rate=gst_rate,
    billing_state_code="27",  # Maharashtra
    shipping_state_code="27",  # Same state
    include_gst=False
)

print(f"Product Price: {format_inr(gst_calc.base_amount)}")
print(f"CGST (9%): {format_inr(gst_calc.cgst)}")
print(f"SGST (9%): {format_inr(gst_calc.sgst)}")
print(f"Total Amount: {format_inr(gst_calc.total_amount)}")

# Output:
# Product Price: ₹1,000.00
# CGST (9%): ₹90.00
# SGST (9%): ₹90.00
# Total Amount: ₹1,180.00
```

### Example 2: Inter-State Order

```python
from decimal import Decimal
from saleor.core.india.gst import calculate_gst
from saleor.core.india.currency import format_inr

# Inter-state transaction (Maharashtra to Delhi)
gst_calc = calculate_gst(
    amount=Decimal("1000.00"),
    gst_rate=Decimal("18.00"),
    billing_state_code="27",  # Maharashtra
    shipping_state_code="07",  # Delhi
    include_gst=False
)

print(f"Product Price: {format_inr(gst_calc.base_amount)}")
print(f"IGST (18%): {format_inr(gst_calc.igst)}")
print(f"Total Amount: {format_inr(gst_calc.total_amount)}")
print(f"Inter-State: {gst_calc.is_inter_state}")

# Output:
# Product Price: ₹1,000.00
# IGST (18%): ₹180.00
# Total Amount: ₹1,180.00
# Inter-State: True
```

### Example 3: B2B Order with GSTIN

```python
from saleor.core.india.gst import validate_gstin
from saleor.core.india.order import create_indian_order

# Validate customer GSTIN
customer_gstin = "27AAPFU0939F1ZV"
is_valid, error = validate_gstin(customer_gstin)

if not is_valid:
    print(f"Invalid GSTIN: {error}")
else:
    # Create order with GST calculation
    indian_order = create_indian_order(
        order=order,  # Saleor Order object
        gst_rate=Decimal("18.00"),
        customer_gstin=customer_gstin,
        include_gst_in_price=True
    )

    print(f"Invoice: {indian_order.invoice_number}")
    print(f"B2B Transaction: {indian_order.is_b2b}")
    print(f"Place of Supply: {indian_order.place_of_supply}")
```

## Applying Discounts with GST

### Example 1: Percentage Discount

```python
from decimal import Decimal
from saleor.core.india.discount import apply_discount_with_gst
from saleor.core.india.currency import format_inr

# Original price: ₹1,180 (including 18% GST on ₹1,000 base)
# Apply 10% discount
result = apply_discount_with_gst(
    original_amount=Decimal("1180.00"),
    discount_value=Decimal("10.00"),  # 10% off
    discount_type="percentage",
    gst_rate=Decimal("18.00"),
    billing_state_code="27"
)

print("Original:")
print(f"  Base: {format_inr(result['original']['base_amount'])}")
print(f"  GST: {format_inr(result['original']['gst_amount'])}")
print(f"  Total: {format_inr(result['original']['total_amount'])}")

print("\nDiscount Applied:")
print(f"  Discount: {format_inr(result['discount']['total_discount'])}")

print("\nFinal Price:")
print(f"  Base: {format_inr(result['final']['base_amount'])}")
print(f"  CGST: {format_inr(result['final']['cgst'])}")
print(f"  SGST: {format_inr(result['final']['sgst'])}")
print(f"  Total: {format_inr(result['final']['total_amount'])}")

print(f"\nYou Save: {format_inr(result['savings']['amount'])} ({result['savings']['percentage']}%)")

# Output:
# Original:
#   Base: ₹1,000.00
#   GST: ₹180.00
#   Total: ₹1,180.00
#
# Discount Applied:
#   Discount: ₹118.00
#
# Final Price:
#   Base: ₹900.00
#   CGST: ₹81.00
#   SGST: ₹81.00
#   Total: ₹1,062.00
#
# You Save: ₹118.00 (10.00%)
```

### Example 2: Bulk Discount Tiers

```python
from decimal import Decimal
from saleor.core.india.discount import calculate_bulk_discount_with_gst
from saleor.core.india.currency import format_inr

# Define discount tiers
discount_tiers = [
    {"min_qty": 5, "discount_pct": 5},
    {"min_qty": 10, "discount_pct": 10},
    {"min_qty": 25, "discount_pct": 15},
    {"min_qty": 50, "discount_pct": 20},
]

# Calculate for 15 items at ₹118 each (including GST)
result = calculate_bulk_discount_with_gst(
    item_price=Decimal("118.00"),
    quantity=15,
    discount_tiers=discount_tiers,
    gst_rate=Decimal("18.00"),
    billing_state_code="27"
)

print(f"Item Price: {format_inr(result['item_price'])}")
print(f"Quantity: {result['quantity']}")
print(f"Original Total: {format_inr(result['original_total'])}")
print(f"\nApplied Tier: Buy {result['applied_tier']['min_qty']}+ items")
print(f"Discount: {result['discount_percentage']}%")
print(f"\nFinal Total: {format_inr(result['final_total'])}")
print(f"Final Per Item: {format_inr(result['final_per_item_price'])}")

savings = result['original_total'] - result['final_total']
print(f"\nTotal Savings: {format_inr(savings)}")
```

### Example 3: Coupon Code Validation

```python
from decimal import Decimal
from saleor.core.india.discount import validate_discount_eligibility

# Check if order qualifies for discount
is_eligible, error = validate_discount_eligibility(
    order_amount=Decimal("1500.00"),
    discount_code="SAVE500",
    min_order_value=Decimal("1000.00")
)

if is_eligible:
    print("Discount code can be applied!")
else:
    print(f"Cannot apply discount: {error}")
```

## Processing UPI Payments

### Example 1: Mock UPI Payment (Testing)

```python
from decimal import Decimal
from saleor.payment.gateways.razorpay.upi import (
    validate_upi_vpa,
    process_upi_payment
)
from saleor.payment.interface import PaymentData, GatewayConfig

# Validate UPI VPA
vpa = "user@paytm"
is_valid, error = validate_upi_vpa(vpa)

if not is_valid:
    print(f"Invalid VPA: {error}")
else:
    # Create payment data
    payment_data = PaymentData(
        gateway="razorpay",
        amount=Decimal("1180.00"),
        currency="INR",
        billing=None,
        shipping=None,
        payment_id=1,
        graphql_payment_id="UGF5bWVudDox",
        order_id="order_123",
        customer_ip_address="127.0.0.1",
        customer_email="customer@example.com",
        data={
            "upi_vpa": vpa,
            "payment_method": "upi"
        }
    )

    # Gateway config
    config = GatewayConfig(
        gateway_name="razorpay",
        auto_capture=True,
        supported_currencies="INR",
        connection_params={
            "public_key": "test_key",
            "private_key": "test_secret",
        }
    )

    # Process payment in mock mode
    response = process_upi_payment(
        payment_data,
        config,
        mock_mode=True  # Set to False in production
    )

    if response.is_success:
        print(f"Payment successful!")
        print(f"Transaction ID: {response.transaction_id}")
        print(f"Amount: ₹{response.amount}")
    else:
        print(f"Payment failed: {response.error}")
```

### Example 2: Configure Razorpay India Plugin

```python
# In Saleor settings.py or admin configuration

RAZORPAY_INDIA_CONFIG = {
    "Public API key": "rzp_test_your_public_key",
    "Secret API key": "rzp_test_your_secret_key",
    "Enable UPI payments": True,
    "Mock mode": False,  # Set to True for testing
    "Validate GST": True,
    "Automatic payment capture": True,
    "Supported currencies": "INR",
}
```

## Validating Indian Addresses

### Example 1: Complete Address Validation

```python
from saleor.core.india.address import validate_indian_address

try:
    address = validate_indian_address(
        street_address_1="123 MG Road",
        street_address_2="Opposite Central Mall",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400001",
        country="IN"
    )

    print("Address validated successfully!")
    print(f"Street: {address['street_address_1']}")
    print(f"City: {address['city']}")
    print(f"State: {address['state']} (Code: {address['state_code']})")
    print(f"PIN: {address['postal_code']}")

except IndianAddressValidationError as e:
    print(f"Address validation failed: {str(e)}")
```

### Example 2: PIN Code Validation

```python
from saleor.core.india.address import validate_indian_pincode

# Validate various PIN code formats
pin_codes = ["400001", "110 001", "560001", "12345"]

for pin in pin_codes:
    is_valid, error = validate_indian_pincode(pin)
    if is_valid:
        print(f"✓ {pin} is valid")
    else:
        print(f"✗ {pin} is invalid: {error}")

# Output:
# ✓ 400001 is valid
# ✓ 110 001 is valid (spaces removed)
# ✓ 560001 is valid
# ✗ 12345 is invalid: PIN code must be 6 digits
```

### Example 3: State Code Lookup

```python
from saleor.core.india.address import get_state_code, get_state_name

# Get state code from name
code = get_state_code("Maharashtra")
print(f"Maharashtra code: {code}")  # Output: 27

# Get state name from code
name = get_state_name("27")
print(f"Code 27 is: {name}")  # Output: Maharashtra
```

## Complete E-commerce Flow

### Example: Full Order Processing

```python
from decimal import Decimal
from saleor.core.india.gst import calculate_gst, validate_gstin
from saleor.core.india.address import validate_indian_address
from saleor.core.india.discount import apply_discount_with_gst
from saleor.core.india.currency import format_inr
from saleor.payment.gateways.razorpay.upi import process_upi_payment

def process_indian_order(
    product_price: Decimal,
    quantity: int,
    billing_address: dict,
    shipping_address: dict,
    customer_gstin: str = None,
    discount_code: str = None,
    payment_vpa: str = None
):
    """Complete order processing flow for Indian customers."""

    # Step 1: Validate addresses
    print("Step 1: Validating addresses...")
    try:
        billing = validate_indian_address(**billing_address)
        shipping = validate_indian_address(**shipping_address)
        print("✓ Addresses validated")
    except Exception as e:
        print(f"✗ Address validation failed: {e}")
        return None

    # Step 2: Calculate base order amount
    print("\nStep 2: Calculating order amount...")
    base_amount = product_price * quantity
    print(f"Base amount: {format_inr(base_amount)}")

    # Step 3: Calculate GST
    print("\nStep 3: Calculating GST...")
    gst_calc = calculate_gst(
        amount=base_amount,
        gst_rate=Decimal("18.00"),
        billing_state_code=billing["state_code"],
        shipping_state_code=shipping["state_code"],
        include_gst=False
    )

    if gst_calc.is_inter_state:
        print(f"Inter-state transaction (IGST): {format_inr(gst_calc.igst)}")
    else:
        print(f"Intra-state transaction")
        print(f"  CGST: {format_inr(gst_calc.cgst)}")
        print(f"  SGST: {format_inr(gst_calc.sgst)}")

    order_amount = gst_calc.total_amount

    # Step 4: Apply discount if provided
    if discount_code:
        print(f"\nStep 4: Applying discount code '{discount_code}'...")
        discount_result = apply_discount_with_gst(
            original_amount=order_amount,
            discount_value=Decimal("10.00"),  # 10% off
            discount_type="percentage",
            gst_rate=Decimal("18.00"),
            billing_state_code=billing["state_code"],
            shipping_state_code=shipping["state_code"]
        )
        order_amount = discount_result["final"]["total_amount"]
        print(f"Discount applied: {format_inr(discount_result['savings']['amount'])}")

    print(f"\nFinal Order Amount: {format_inr(order_amount)}")

    # Step 5: Validate GSTIN for B2B orders
    if customer_gstin:
        print(f"\nStep 5: Validating GSTIN for B2B order...")
        is_valid, error = validate_gstin(customer_gstin)
        if not is_valid:
            print(f"✗ Invalid GSTIN: {error}")
            return None
        print(f"✓ Valid GSTIN: {customer_gstin}")

    # Step 6: Process payment
    if payment_vpa:
        print(f"\nStep 6: Processing UPI payment...")
        # Payment processing logic here
        print(f"✓ Payment initiated to {payment_vpa}")

    print("\n" + "="*50)
    print("ORDER SUMMARY")
    print("="*50)
    print(f"Items: {quantity} × {format_inr(product_price)}")
    print(f"Subtotal: {format_inr(base_amount)}")
    print(f"GST: {format_inr(gst_calc.total_gst)}")
    if discount_code:
        print(f"Discount: -{format_inr(discount_result['savings']['amount'])}")
    print(f"Total: {format_inr(order_amount)}")
    print("="*50)

    return {
        "order_amount": order_amount,
        "gst_breakdown": gst_calc,
        "billing_address": billing,
        "shipping_address": shipping,
    }

# Example usage
order_result = process_indian_order(
    product_price=Decimal("100.00"),
    quantity=10,
    billing_address={
        "street_address_1": "123 MG Road",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001"
    },
    shipping_address={
        "street_address_1": "456 Connaught Place",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001"
    },
    customer_gstin="27AAPFU0939F1ZV",
    discount_code="SAVE10",
    payment_vpa="customer@paytm"
)
```

## Error Handling Best Practices

### Example: Comprehensive Error Handling

```python
from decimal import Decimal
from saleor.core.india.gst import validate_gstin
from saleor.core.india.address import (
    validate_indian_address,
    IndianAddressValidationError
)
from saleor.core.india.currency import validate_inr_amount
import logging

logger = logging.getLogger(__name__)

def safe_order_processing(order_data: dict) -> dict:
    """Process order with comprehensive error handling."""

    errors = []

    # Validate amount
    try:
        amount = Decimal(order_data["amount"])
        is_valid, error = validate_inr_amount(amount)
        if not is_valid:
            errors.append(f"Amount validation failed: {error}")
    except (ValueError, KeyError) as e:
        errors.append(f"Invalid amount: {str(e)}")

    # Validate GSTIN if provided
    if order_data.get("gstin"):
        is_valid, error = validate_gstin(order_data["gstin"])
        if not is_valid:
            errors.append(f"GSTIN validation failed: {error}")

    # Validate address
    try:
        address = validate_indian_address(**order_data["address"])
    except IndianAddressValidationError as e:
        errors.append(f"Address validation failed: {str(e)}")
    except KeyError as e:
        errors.append(f"Missing address field: {str(e)}")

    # Return results
    if errors:
        logger.error(f"Order validation failed: {'; '.join(errors)}")
        return {
            "success": False,
            "errors": errors
        }

    logger.info("Order validation successful")
    return {
        "success": True,
        "validated_data": {
            "amount": amount,
            "address": address,
        }
    }
```

## Testing Examples

### Example: Unit Test for Order Processing

```python
import pytest
from decimal import Decimal
from saleor.core.india.gst import calculate_gst

def test_order_gst_calculation():
    """Test GST calculation for an order."""
    # Given
    amount = Decimal("1000.00")
    gst_rate = Decimal("18.00")

    # When
    result = calculate_gst(
        amount=amount,
        gst_rate=gst_rate,
        billing_state_code="27",
        include_gst=False
    )

    # Then
    assert result.base_amount == Decimal("1000.00")
    assert result.total_gst == Decimal("180.00")
    assert result.total_amount == Decimal("1180.00")
    assert result.cgst == Decimal("90.00")
    assert result.sgst == Decimal("90.00")

def test_upi_payment_mock():
    """Test UPI payment in mock mode."""
    # Given
    payment_data = create_test_payment_data()
    config = create_test_gateway_config()

    # When
    response = process_upi_payment(
        payment_data,
        config,
        mock_mode=True
    )

    # Then
    assert response.is_success is True
    assert response.error is None
    assert "upi_mock_" in response.transaction_id
```

---

For more examples and detailed API documentation, see the [README.md](README.md).
