from decimal import Decimal
from unittest.mock import Mock

import pytest
from prices import Money, TaxedMoney

from saleor.checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from saleor.plugins.manager import get_plugins_manager

from ..gst_plugin import GstPlugin


@pytest.fixture
def gst_plugin_configuration(db, channel_USD):
    def factory(is_active=True, gst_rate="18.0"):
        plugin = GstPlugin.construct(
            configuration=[
                {"name": "is_active", "value": is_active},
                {"name": "gst_rate", "value": gst_rate},
            ],
            channel=channel_USD,
        )
        return plugin
    return factory


def test_calculate_checkout_line_total_valid_indian_address(
    checkout_with_item, address, gst_plugin_configuration
):
    # given
    address.country = "IN"
    address.gst_number = "123456789012345"  # Valid format
    address.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    manager = get_plugins_manager(allow_replica=False)
    plugin = gst_plugin_configuration()
    manager.plugins = [plugin]

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    line_info = lines[0]
    
    # when
    taxed_line_total = plugin.calculate_checkout_line_total(
        checkout_info, lines, line_info, address, line_info.line.total_price
    )

    # then
    expected_net = line_info.line.total_price.net
    expected_tax = expected_net.amount * Decimal("0.18")
    expected_gross = expected_net + Money(expected_tax, "USD")
    
    assert taxed_line_total == TaxedMoney(net=expected_net, gross=expected_gross)


def test_calculate_checkout_line_total_plugin_inactive(
    checkout_with_item, address, gst_plugin_configuration
):
    # given
    address.country = "IN"
    address.gst_number = "123456789012345"
    address.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    manager = get_plugins_manager(allow_replica=False)
    plugin = gst_plugin_configuration(is_active=False)
    manager.plugins = [plugin]

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    line_info = lines[0]
    
    # when
    taxed_line_total = plugin.calculate_checkout_line_total(
        checkout_info, lines, line_info, address, line_info.line.total_price
    )

    # then
    assert taxed_line_total == line_info.line.total_price


def test_calculate_checkout_line_total_not_indian_address(
    checkout_with_item, address, gst_plugin_configuration
):
    # given
    address.country = "US"
    address.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    manager = get_plugins_manager(allow_replica=False)
    plugin = gst_plugin_configuration()
    manager.plugins = [plugin]

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    line_info = lines[0]
    
    # when
    taxed_line_total = plugin.calculate_checkout_line_total(
        checkout_info, lines, line_info, address, line_info.line.total_price
    )

    # then
    assert taxed_line_total == line_info.line.total_price


def test_calculate_checkout_line_total_missing_gst_number(
    checkout_with_item, address, gst_plugin_configuration
):
    # given
    address.country = "IN"
    address.gst_number = ""
    address.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    manager = get_plugins_manager(allow_replica=False)
    plugin = gst_plugin_configuration()
    manager.plugins = [plugin]

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    line_info = lines[0]
    
    # when
    taxed_line_total = plugin.calculate_checkout_line_total(
        checkout_info, lines, line_info, address, line_info.line.total_price
    )

    # then
    assert taxed_line_total == line_info.line.total_price


def test_calculate_checkout_line_total_invalid_gst_number(
    checkout_with_item, address, gst_plugin_configuration
):
    # given
    address.country = "IN"
    address.gst_number = "INVALID"
    address.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    manager = get_plugins_manager(allow_replica=False)
    plugin = gst_plugin_configuration()
    manager.plugins = [plugin]

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    line_info = lines[0]
    
    # when
    taxed_line_total = plugin.calculate_checkout_line_total(
        checkout_info, lines, line_info, address, line_info.line.total_price
    )

    # then
    assert taxed_line_total == line_info.line.total_price
