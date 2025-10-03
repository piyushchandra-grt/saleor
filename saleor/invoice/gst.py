from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import json
from typing import Optional

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.timezone import now

from ..account.models import Address
from ..core import JobStatus
from ..invoice.models import Invoice
from ..order.models import Order
from ..site.models import SiteSettings


@dataclass
class GstBreakdown:
    kind: str  # "intra-state" or "inter-state"
    taxable_value: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    currency: str
    customer_gstin: str
    seller_state: Optional[str]
    customer_state: Optional[str]


def _get_state_code(address: Optional[Address]) -> Optional[str]:
    if not address:
        return None
    try:
        if getattr(address.country, "code", None) != "IN":
            return None
    except Exception:
        # address.country may be stored as raw code already in some contexts
        if str(address.country) != "IN":
            return None
    state = (address.country_area or "").strip()
    return state.upper() or None


def _calc_total_tax(order: Order) -> Decimal:
    # Use already computed values on Order: Tax = gross - net (includes shipping)
    total_tax = Decimal(order.total_gross_amount) - Decimal(order.total_net_amount)
    return total_tax


def _calc_taxable_value(order: Order) -> Decimal:
    return Decimal(order.total_net_amount)


def _generate_breakdown(order: Order, customer_gstin: str) -> GstBreakdown:
    # Seller state from SiteSettings.company_address
    site_settings = SiteSettings.objects.get(site_id=settings.SITE_ID)
    seller_state = _get_state_code(site_settings.company_address)

    # Customer state prefers shipping, then billing
    customer_addr = order.shipping_address or order.billing_address
    customer_state = _get_state_code(customer_addr)

    total_tax = _calc_total_tax(order)
    taxable_value = _calc_taxable_value(order)

    intra_state = bool(seller_state and customer_state and seller_state == customer_state)

    if intra_state:
        half = (total_tax / Decimal("2")).quantize(Decimal("0.01"))
        cgst = half
        sgst = total_tax.quantize(Decimal("0.01")) - half
        igst = Decimal("0.00")
        kind = "intra-state"
    else:
        cgst = Decimal("0.00")
        sgst = Decimal("0.00")
        igst = total_tax.quantize(Decimal("0.01"))
        kind = "inter-state"

    return GstBreakdown(
        kind=kind,
        taxable_value=taxable_value.quantize(Decimal("0.01")),
        cgst_amount=cgst,
        sgst_amount=sgst,
        igst_amount=igst,
        currency=order.currency,
        customer_gstin=customer_gstin,
        seller_state=seller_state,
        customer_state=customer_state,
    )


def generate_gst_invoice(order_id: int, customer_gstin: str) -> Invoice:
    """
    Generate a GST invoice for the given order number and customer GSTIN.

    - Determines CGST/SGST vs IGST based on seller vs customer states (India).
    - Uses existing order totals for tax amounts; does not recalculate prices.
    - Creates an Invoice with a JSON invoice file and stores GST details in metadata.

    Args:
        order_id: Order.number (sequential integer), NOT the UUID primary key.
        customer_gstin: Customer GSTIN string to include on the invoice.

    Returns:
        The created Invoice instance.
    """
    order = Order.objects.get(number=order_id)

    breakdown = _generate_breakdown(order, customer_gstin)

    # Create invoice record
    invoice = Invoice.objects.create(
        order=order,
        number=f"INV-{order.number}",
        created=now(),
        status=JobStatus.SUCCESS,
    )

    # Store GST data in invoice metadata
    invoice.store_value_in_metadata(
        {
            "gst.kind": breakdown.kind,
            "gst.taxable_value": str(breakdown.taxable_value),
            "gst.cgst_amount": str(breakdown.cgst_amount),
            "gst.sgst_amount": str(breakdown.sgst_amount),
            "gst.igst_amount": str(breakdown.igst_amount),
            "gst.currency": breakdown.currency,
            "gst.customer_gstin": breakdown.customer_gstin,
            "gst.seller_state": breakdown.seller_state,
            "gst.customer_state": breakdown.customer_state,
        }
    )
    invoice.save(update_fields=["metadata", "updated_at"])

    # Generate a simple JSON invoice file content
    file_payload = {
        "invoice_number": invoice.number,
        "order_number": order.number,
        "currency": breakdown.currency,
        "gst": asdict(breakdown) | {
            # ensure decimals serialized as strings
            "taxable_value": str(breakdown.taxable_value),
            "cgst_amount": str(breakdown.cgst_amount),
            "sgst_amount": str(breakdown.sgst_amount),
            "igst_amount": str(breakdown.igst_amount),
        },
        "created_at": now().isoformat(),
    }
    content = json.dumps(file_payload, ensure_ascii=False, separators=(",", ":"))
    content_file = ContentFile(content.encode("utf-8"))
    invoice.invoice_file.save(f"gst_invoice_{order.number}.json", content_file)
    invoice.save(update_fields=["invoice_file", "updated_at"])

    return invoice
