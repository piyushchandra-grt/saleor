import i18naddress
import json
import os

from saleor.india.i18n_override import COUNTRIES_RULES_OVERRIDE


def test_india_address_validation_rules_are_overridden():
    # given
    # The ready() method of SaleorIndiaConfig should have patched the rules

    # when
    rules = i18naddress.load_validation_data('IN')

    # then
    expected_rules = COUNTRIES_RULES_OVERRIDE.get("IN")
    assert rules["IN"]["fmt"] == expected_rules["fmt"]
    assert rules["IN"]["require"] == expected_rules["require"]
    assert rules["IN"]["upper"] == expected_rules["upper"]
    assert rules["IN"]["zip"] == expected_rules["zip"]
    assert rules["IN"]["zipex"] == expected_rules["zipex"]
    assert rules["IN"]["state_name_type"] == expected_rules["state_name_type"]
