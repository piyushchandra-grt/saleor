import i18naddress
import json
import os

original_load_validation_data = i18naddress.load_validation_data


def get_rules_from_file():
    rules_path = os.path.join(os.path.dirname(__file__), "i18n_address_rules.json")
    with open(rules_path, "r") as f:
        return json.load(f)


COUNTRIES_RULES_OVERRIDE = get_rules_from_file()


def patched_load_validation_data(country_code="all"):
    validation_data = original_load_validation_data(country_code)
    upper_country_code = country_code.upper()
    if rules_override := COUNTRIES_RULES_OVERRIDE.get(upper_country_code):
        for key, value in rules_override.items():
            validation_data[upper_country_code][key] = value
    return validation_data


def i18n_rules_override():
    i18naddress.load_validation_data = patched_load_validation_data
