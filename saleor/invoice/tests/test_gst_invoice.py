import pytest
from decimal import Decimal

from saleor.invoice.gst import generate_gst_invoice
from saleor.account.models import Address
from saleor.site.models import SiteSettings


@pytest.fixture
def india_seller_address(db):
    return Address.objects.create(
        first_name="Seller",
        last_name="HQ",
        street_address_1="1 MG Road",
        city="Bengaluru",
        postal_code="560001",
        country="IN",
        country_area="KA",  # Karnataka
    )


@pytest.fixture
def set_site_seller_address(site_settings, india_seller_address):
    site_settings.company_address = india_seller_address
    site_settings.save(update_fields=["company_address"])
    return site_settings


@pytest.fixture
def order_in_india(order_with_lines, set_site_seller_address):
    # Ensure customer shipping/billing is India as well
    addr = order_with_lines.shipping_address
    addr.country = "IN"
    addr.country_area = "KA"  # Karnataka
    addr.save(update_fields=["country", "country_area"])

    bill = order_with_lines.billing_address
    bill.country = "IN"
    bill.country_area = "KA"
    bill.save(update_fields=["country", "country_area"])

    order_with_lines.refresh_from_db()
    return order_with_lines


@pytest.mark.django_db
def test_gst_invoice_intra_state(order_in_india, media_root):
    order = order_in_india
    invoice = generate_gst_invoice(order.number, customer_gstin="29ABCDE1234F1Z5")

    # Validate invoice metadata
    md = invoice.metadata
    assert md["gst.kind"] == "intra-state"

    total_tax = Decimal(order.total_gross_amount) - Decimal(order.total_net_amount)
    cgst = Decimal(md["gst.cgst_amount"]) if isinstance(md["gst.cgst_amount"], str) else Decimal(str(md["gst.cgst_amount"]))
    sgst = Decimal(md["gst.sgst_amount"]) if isinstance(md["gst.sgst_amount"], str) else Decimal(str(md["gst.sgst_amount"]))
    igst = Decimal(md["gst.igst_amount"]) if isinstance(md["gst.igst_amount"], str) else Decimal(str(md["gst.igst_amount"]))

    assert cgst + sgst == total_tax.quantize(Decimal("0.01"))
    assert igst == Decimal("0.00")
    assert invoice.invoice_file and invoice.invoice_file.name.endswith(
        f"gst_invoice_{order.number}.json"
    )


@pytest.mark.django_db
def test_gst_invoice_inter_state(order_in_india, media_root):
    order = order_in_india

    # Set customer to a different state to trigger IGST
    addr = order.shipping_address
    addr.country_area = "MH"  # Maharashtra
    addr.save(update_fields=["country_area"])

    order.refresh_from_db()

    invoice = generate_gst_invoice(order.number, customer_gstin="27ABCDE1234F1Z7")

    md = invoice.metadata
    assert md["gst.kind"] == "inter-state"

    total_tax = Decimal(order.total_gross_amount) - Decimal(order.total_net_amount)
    cgst = Decimal(md["gst.cgst_amount"]) if isinstance(md["gst.cgst_amount"], str) else Decimal(str(md["gst.cgst_amount"]))
    sgst = Decimal(md["gst.sgst_amount"]) if isinstance(md["gst.sgst_amount"], str) else Decimal(str(md["gst.sgst_amount"]))
    igst = Decimal(md["gst.igst_amount"]) if isinstance(md["gst.igst_amount"], str) else Decimal(str(md["gst.igst_amount"]))

    assert cgst == Decimal("0.00") and sgst == Decimal("0.00")
    assert igst == total_tax.quantize(Decimal("0.01"))
    assert invoice.invoice_file and invoice.invoice_file.name.endswith(
        f"gst_invoice_{order.number}.json"
    )
