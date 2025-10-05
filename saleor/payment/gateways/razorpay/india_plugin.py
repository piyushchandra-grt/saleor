"""Enhanced Razorpay Gateway Plugin with India-specific features and UPI support."""

import logging
from typing import TYPE_CHECKING

from ....core.india.currency import validate_inr_amount
from ....core.india.gst import validate_gstin
from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField
from ..utils import get_supported_currencies
from . import GatewayConfig, capture, process_payment, refund
from .upi import process_upi_payment

GATEWAY_NAME = "Razorpay India"

if TYPE_CHECKING:
    from . import GatewayResponse, PaymentData

logger = logging.getLogger(__name__)


class RazorpayIndiaGatewayPlugin(BasePlugin):
    """Enhanced Razorpay Gateway Plugin for India with UPI support.

    Features:
    - UPI payment method support
    - GST validation
    - INR-specific currency handling
    - Mock API mode for testing
    - Secure payment processing
    - Comprehensive error logging
    """

    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "mirumee.payments.razorpay.india"
    DEFAULT_CONFIGURATION = [
        {"name": "Public API key", "value": None},
        {"name": "Secret API key", "value": None},
        {"name": "Store customers card", "value": False},
        {"name": "Automatic payment capture", "value": True},
        {"name": "Supported currencies", "value": "INR"},
        {"name": "Enable UPI payments", "value": True},
        {"name": "Mock mode", "value": False},
        {"name": "Validate GST", "value": True},
    ]

    CONFIG_STRUCTURE = {
        "Public API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Razorpay public API key",
            "label": "Public API key",
        },
        "Secret API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Razorpay secret API key",
            "label": "Secret API key",
        },
        "Store customers card": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should store cards in Razorpay customer",
            "label": "Store customers card",
        },
        "Automatic payment capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automatically capture payments",
            "label": "Automatic payment capture",
        },
        "Supported currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway (comma-separated)",
            "label": "Supported currencies",
        },
        "Enable UPI payments": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Enable UPI payment method for Indian customers",
            "label": "Enable UPI payments",
        },
        "Mock mode": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Use mock API for testing (does not process real payments)",
            "label": "Mock mode",
        },
        "Validate GST": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Validate customer GSTIN for B2B transactions",
            "label": "Validate GST",
        },
    }

    def __init__(self, *args, **kwargs):
        """Step 1: Initialize the Razorpay India Gateway Plugin."""
        super().__init__(*args, **kwargs)

        # Step 1.1: Parse configuration
        configuration = {item["name"]: item["value"] for item in self.configuration}

        # Step 1.2: Create gateway config
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration["Automatic payment capture"],
            supported_currencies=configuration["Supported currencies"],
            connection_params={
                "public_key": configuration["Public API key"],
                "private_key": configuration["Secret API key"],
                "prefill": True,
                "store_name": None,
                "store_image": None,
            },
            store_customer=configuration["Store customers card"],
        )

        # Step 1.3: Store India-specific settings
        self.enable_upi = configuration.get("Enable UPI payments", True)
        self.mock_mode = configuration.get("Mock mode", False)
        self.validate_gst = configuration.get("Validate GST", True)

        if self.mock_mode:
            logger.warning(f"{GATEWAY_NAME} plugin initialized in MOCK MODE")

    def _get_gateway_config(self):
        """Get gateway configuration."""
        return self.config

    def _validate_payment_data(
        self, payment_information: "PaymentData"
    ) -> tuple[bool, str | None]:
        """Step 2: Validate payment data with India-specific checks.

        Args:
            payment_information: Payment data to validate

        Returns:
            Tuple of (is_valid, error_message)

        """
        # Step 2.1: Validate currency is INR
        if payment_information.currency != "INR":
            error_msg = (
                f"Currency not supported: {payment_information.currency}. "
                f"Only INR is supported."
            )
            logger.error(error_msg)
            return False, error_msg

        # Step 2.2: Validate amount
        is_valid, error = validate_inr_amount(payment_information.amount)
        if not is_valid:
            logger.error(f"Payment amount validation failed: {error}")
            return False, error

        # Step 2.3: Validate GSTIN if provided and validation is enabled
        if self.validate_gst and payment_information.data:
            customer_gstin = payment_information.data.get("gstin")
            if customer_gstin:
                is_valid, error = validate_gstin(customer_gstin)
                if not is_valid:
                    error_msg = f"Invalid GSTIN: {error}"
                    logger.error(error_msg)
                    return False, error_msg

        logger.info("Payment data validation successful")
        return True, None

    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        """Step 3: Capture a payment.

        Args:
            payment_information: Payment data
            previous_value: Previous plugin's return value

        Returns:
            GatewayResponse with transaction details

        """
        if not self.active:
            return previous_value

        # Step 3.1: Validate payment data
        is_valid, error = self._validate_payment_data(payment_information)
        if not is_valid:
            from ... import TransactionKind
            from ...interface import GatewayResponse

            return GatewayResponse(
                transaction_id=payment_information.payment_id,
                action_required=False,
                kind=TransactionKind.CAPTURE,
                amount=payment_information.amount,
                currency=payment_information.currency,
                error=error,
                is_success=False,
                raw_response={"error": error},
            )

        # Step 3.2: Process capture
        logger.info(
            f"Capturing payment: ID={payment_information.payment_id}, "
            f"Amount={payment_information.amount} {payment_information.currency}"
        )

        return capture(payment_information, self._get_gateway_config())

    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        """Step 4: Refund a payment.

        Args:
            payment_information: Payment data
            previous_value: Previous plugin's return value

        Returns:
            GatewayResponse with transaction details

        """
        if not self.active:
            return previous_value

        # Step 4.1: Validate payment data
        is_valid, error = self._validate_payment_data(payment_information)
        if not is_valid:
            from ... import TransactionKind
            from ...interface import GatewayResponse

            return GatewayResponse(
                transaction_id=payment_information.payment_id,
                action_required=False,
                kind=TransactionKind.REFUND,
                amount=payment_information.amount,
                currency=payment_information.currency,
                error=error,
                is_success=False,
                raw_response={"error": error},
            )

        # Step 4.2: Process refund
        logger.info(
            f"Refunding payment: ID={payment_information.payment_id}, "
            f"Amount={payment_information.amount} {payment_information.currency}"
        )

        return refund(payment_information, self._get_gateway_config())

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        """Step 5: Process a payment (capture or UPI).

        Args:
            payment_information: Payment data
            previous_value: Previous plugin's return value

        Returns:
            GatewayResponse with transaction details

        """
        if not self.active:
            return previous_value

        # Step 5.1: Validate payment data
        is_valid, error = self._validate_payment_data(payment_information)
        if not is_valid:
            from ... import TransactionKind
            from ...interface import GatewayResponse

            return GatewayResponse(
                transaction_id=payment_information.payment_id,
                action_required=False,
                kind=TransactionKind.CAPTURE,
                amount=payment_information.amount,
                currency=payment_information.currency,
                error=error,
                is_success=False,
                raw_response={"error": error},
            )

        # Step 5.2: Check if UPI payment is requested
        payment_method = None
        if payment_information.data:
            payment_method = payment_information.data.get("payment_method")

        # Step 5.3: Process UPI payment if enabled and requested
        if self.enable_upi and payment_method == "upi":
            logger.info(
                f"Processing UPI payment: ID={payment_information.payment_id}, "
                f"Amount={payment_information.amount} INR"
            )
            return process_upi_payment(
                payment_information,
                self._get_gateway_config(),
                mock_mode=self.mock_mode,
            )

        # Step 5.4: Process standard payment
        logger.info(
            f"Processing payment: ID={payment_information.payment_id}, "
            f"Amount={payment_information.amount} {payment_information.currency}"
        )

        return process_payment(payment_information, self._get_gateway_config())

    def get_supported_currencies(self, previous_value):
        """Get supported currencies."""
        if not self.active:
            return previous_value
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    def get_payment_config(self, previous_value):
        """Get payment configuration for frontend."""
        if not self.active:
            return previous_value
        config = self._get_gateway_config()
        payment_config = [
            {"field": "api_key", "value": config.connection_params["public_key"]},
            {"field": "enable_upi", "value": self.enable_upi},
            {"field": "mock_mode", "value": self.mock_mode},
        ]
        return payment_config
