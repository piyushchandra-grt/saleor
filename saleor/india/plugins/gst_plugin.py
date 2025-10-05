from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from saleor.core.taxes import zero_taxed_money

if TYPE_CHECKING:
    from saleor.account.models import Address
    from saleor.checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from prices import TaxedMoney


class GstPlugin(BasePlugin):
    PLUGIN_ID = "saleor.india.gst"
    PLUGIN_NAME = "GST India"
    DEFAULT_CONFIGURATION = [
        {"name": "is_active", "value": False},
        {"name": "gst_rate", "value": "18.0"},
    ]
    CONFIG_STRUCTURE = {
        "is_active": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Enable this plugin to calculate GST for Indian addresses.",
            "label": "Is Active",
        },
        "gst_rate": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "GST rate in percent (e.g., 18.0).",
            "label": "GST Rate (%)",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.is_active = configuration["is_active"]
        try:
            self.gst_rate = Decimal(configuration["gst_rate"]) / 100
        except (ValueError, TypeError):
            self.gst_rate = Decimal("0.18")

    def _skip_plugin(self, address: Optional["Address"]) -> bool:
        if not self.is_active:
            return True
        if not address or address.country.code != "IN":
            return True
        
        # Basic GST number format validation (15 characters, alphanumeric)
        gst_number = getattr(address, 'gst_number', '')
        if not gst_number or len(gst_number) != 15 or not gst_number.isalnum():
            return True

        return False

    def calculate_checkout_line_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: list["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        previous_value: "TaxedMoney",
    ) -> "TaxedMoney":
        if self._skip_plugin(address):
            return previous_value

        line_total = checkout_line_info.line.total_price
        tax_amount = line_total.net.amount * self.gst_rate
        
        return TaxedMoney(
            net=line_total.net,
            gross=line_total.gross + tax_amount
        )
