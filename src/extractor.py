"""
Invoice Intake & Extraction Module
Performs header and line extraction validation, arithmetic audit, tax consistency,
vendor status verification, temporal validation, and duplicate detection.
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import date
from src.models import Invoice, InvoiceLine, Vendor, PurchaseOrder, AuditEvent
from src.config import MATCH_TOLERANCES

class ExtractionValidator:
    """
    Validates ingested invoice payloads before 3-way matching.
    Enforces arithmetic integrity, temporal ordering, and duplicate detection.
    """

    def __init__(self, vendors: List[Vendor], purchase_orders: List[PurchaseOrder]):
        self.vendors_map: Dict[str, Vendor] = {v.vendor_id: v for v in vendors}
        self.po_map: Dict[str, PurchaseOrder] = {po.po_id: po for po in purchase_orders}
        self.seen_signatures: Dict[str, str] = {}  # signature -> invoice_id
        self.seen_vendor_invoices: Dict[Tuple[str, str], str] = {}  # (vendor_id, invoice_number) -> invoice_id

    def _generate_payload_signature(self, invoice: Invoice, lines: List[InvoiceLine]) -> str:
        """Create deterministic fingerprint of invoice payload for duplicate detection."""
        line_fingerprint = "|".join(
            f"{l.sku}:{l.invoiced_quantity:.2f}:{l.unit_price:.2f}" for l in sorted(lines, key=lambda x: x.line_number)
        )
        po_key = invoice.po_id or "NO_PO"
        return f"{invoice.vendor_id}|{invoice.invoice_number}|{po_key}|{invoice.currency}|{invoice.total_amount:.2f}|{line_fingerprint}"

    def validate_intake(
        self,
        invoice: Invoice,
        lines: List[InvoiceLine],
        event_counter: int
    ) -> Tuple[Optional[str], Optional[str], List[AuditEvent]]:
        """
        Validates invoice intake and extraction integrity.
        Returns:
            (exception_status, root_cause_field, audit_events)
        """
        events: List[AuditEvent] = []
        vendor = self.vendors_map.get(invoice.vendor_id)
        po = self.po_map.get(invoice.po_id) if invoice.po_id else None

        # Event: Intake Ingestion
        evt_id = f"EVT-2026-{event_counter:06d}"
        events.append(AuditEvent(
            event_id=evt_id,
            entity_name="Invoice",
            entity_id=invoice.invoice_id,
            action="INTAKE_INGESTED",
            actor_role="SYSTEM",
            actor_id="SYS-AUTO",
            previous_state=None,
            new_state="RECEIVED",
            details=f"Invoice received via {invoice.intake_channel} from Vendor {invoice.vendor_id}",
            timestamp=invoice.created_at,
        ))

        # Check 1: Vendor Existence & Status
        if not vendor:
            return "EXCEPTION_CLOSED_VENDOR", "vendor_id", events

        if vendor.status in ("CLOSED", "INACTIVE", "SUSPENDED"):
            return "EXCEPTION_CLOSED_VENDOR", "vendor_status", events

        # Check 2: Duplicate Invoice Detection (Compound Vendor + External Invoice Number)
        vendor_inv_key = (invoice.vendor_id, invoice.invoice_number)
        if vendor_inv_key in self.seen_vendor_invoices:
            prev_id = self.seen_vendor_invoices[vendor_inv_key]
            return "EXCEPTION_DUPLICATE", "invoice_number", events

        # Check 3: Duplicate Payload Signature (Exact Re-submission)
        sig = self._generate_payload_signature(invoice, lines)
        if sig in self.seen_signatures:
            return "EXCEPTION_DUPLICATE", "payload_signature", events

        # Record clean signatures after passing duplicate check
        self.seen_vendor_invoices[vendor_inv_key] = invoice.invoice_id
        self.seen_signatures[sig] = invoice.invoice_id

        # Check 4: Temporal Consistency (Invoice date >= PO date)
        if po:
            inv_dt = date.fromisoformat(invoice.invoice_date)
            po_dt = date.fromisoformat(po.order_date)
            if inv_dt < po_dt:
                return "EXCEPTION_TEMPORAL_VIOLATION", "invoice_date", events

        # Check 5: Header vs Lines Arithmetic Reconciliation
        calculated_subtotal = round(sum(l.line_subtotal for l in lines), 2)
        calculated_tax = round(sum(l.line_tax for l in lines), 2)
        calculated_total = round(calculated_subtotal + calculated_tax, 2)

        if abs(calculated_total - invoice.total_amount) > 0.01:
            return "EXCEPTION_ARITHMETIC_ERROR", "total_amount", events

        if abs(calculated_subtotal - invoice.subtotal_amount) > 0.01:
            return "EXCEPTION_ARITHMETIC_ERROR", "subtotal_amount", events

        # Check 6: Tax Reconciliation & Rate Legitimacy
        if abs(calculated_tax - invoice.tax_amount) > MATCH_TOLERANCES["tax_amount_tolerance"]:
            return "EXCEPTION_TAX_MISMATCH", "tax_amount", events

        for l in lines:
            if l.tax_code == "TAX_CUSTOM_28" or l.tax_rate > 0.20:
                return "EXCEPTION_TAX_MISMATCH", "tax_rate", events

        return None, None, events
