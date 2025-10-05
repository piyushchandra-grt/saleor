from django.apps import AppConfig


class SaleorIndiaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "saleor.india"

    def ready(self):
        from . import i18n_override
        i18n_override.i18n_rules_override()
