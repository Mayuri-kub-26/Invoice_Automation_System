"""
3-Way Matching Engine Module
Performs deterministic 3-way matching between Invoices, Purchase Orders, and Goods Receipts
against configurable enterprise price and quantity tolerances.
"""

from typing import Dict, List, Tuple, Any, Optional
from src.models import (
    Invoice,
    InvoiceLine,
    PurchaseOrder,
    PurchaseOrderLine,
    GoodsReceipt,
    GoodsReceiptLine,
    AuditEvent,
)
from src.config import MATCH_TOLERANCES

class ThreeWayMatcher:
    """
    Core matching engine that reconciles Invoice Lines against PO Lines and GRN Lines.
    Exposes granular line-level verdicts and transparent variance metrics.
    """

    def __init__(
        self,
        purchase_orders: List[PurchaseOrder],
        po_lines: List[PurchaseOrderLine],
        goods_receipts: List[GoodsReceipt],
        goods_receipt_lines: List[GoodsReceiptLine],
    ):
        self.po_map: Dict[str, PurchaseOrder] = {po.po_id: po for po in purchase_orders}
        self.po_lines_map: Dict[str, PurchaseOrderLine] = {pol.po_line_id: pol for pol in po_lines}
        
        # Index GRN Lines by PO Line ID
        self.grn_lines_by_pol: Dict[str, List[GoodsReceiptLine]] = {}
        for grnl in goods_receipt_lines:
            self.grn_lines_by_pol.setdefault(grnl.po_line_id, []).append(grnl)

    def evaluate_invoice(
        self,
        invoice: Invoice,
        lines: List[InvoiceLine],
        event_counter: int
    ) -> Tuple[str, List[InvoiceLine], List[AuditEvent], Dict[str, Any]]:
        """
        Executes 3-way matching for the invoice.
        Returns:
            (overall_match_status, evaluated_lines, audit_events, match_summary)
        """
        events: List[AuditEvent] = []
        match_summary: Dict[str, Any] = {
            "invoice_id": invoice.invoice_id,
            "po_id": invoice.po_id,
            "total_lines": len(lines),
            "matched_lines": 0,
            "price_variance_lines": 0,
            "quantity_mismatch_lines": 0,
            "missing_receipt_lines": 0,
            "total_price_variance_amount": 0.0,
            "total_quantity_variance": 0.0,
        }

        # Header Check: PO existence
        if not invoice.po_id or invoice.po_id not in self.po_map:
            status = "EXCEPTION_MISSING_RECEIPT"
            evt = AuditEvent(
                event_id=f"EVT-2026-{event_counter:06d}",
                entity_name="Invoice",
                entity_id=invoice.invoice_id,
                action="MATCH_EVALUATED",
                actor_role="SYSTEM",
                actor_id="SYS-AUTO",
                previous_state="RECEIVED",
                new_state=status,
                details="Referenced Purchase Order not found in ERP repository",
                timestamp=invoice.created_at,
            )
            return status, lines, [evt], match_summary

        po = self.po_map[invoice.po_id]

        # Line-Level Reconciliations
        line_exceptions: List[str] = []

        for line in lines:
            po_line = self.po_lines_map.get(line.po_line_id) if line.po_line_id else None
            if not po_line:
                line.match_status = "EXCEPTION_QUANTITY_MISMATCH"
                line_exceptions.append(line.match_status)
                continue

            # 1. Price Matching
            unit_price_diff = round(line.unit_price - po_line.unit_price, 2)
            pct_price_diff = (unit_price_diff / po_line.unit_price) if po_line.unit_price > 0 else 0.0

            is_price_variance = (
                (unit_price_diff > 0.05 and pct_price_diff > MATCH_TOLERANCES["price_percentage_tolerance"])
                or unit_price_diff > MATCH_TOLERANCES["price_absolute_tolerance"]
            )

            # 2. Goods Receipt Matching (3-Way)
            grn_lines = self.grn_lines_by_pol.get(line.po_line_id, [])
            total_accepted_qty = sum(grnl.accepted_quantity for grnl in grn_lines)

            is_missing_receipt = len(grn_lines) == 0 or total_accepted_qty <= 0.0
            is_quantity_mismatch = (
                line.invoiced_quantity > (total_accepted_qty + MATCH_TOLERANCES["quantity_tolerance"])
                or line.invoiced_quantity > (po_line.ordered_quantity + MATCH_TOLERANCES["quantity_tolerance"])
            )

            # Assign line verdict
            if is_missing_receipt:
                line.match_status = "EXCEPTION_MISSING_RECEIPT"
                match_summary["missing_receipt_lines"] += 1
                line_exceptions.append(line.match_status)
            elif is_quantity_mismatch:
                line.match_status = "EXCEPTION_QUANTITY_MISMATCH"
                match_summary["quantity_mismatch_lines"] += 1
                match_summary["total_quantity_variance"] += round(line.invoiced_quantity - total_accepted_qty, 2)
                line_exceptions.append(line.match_status)
            elif is_price_variance:
                line.match_status = "EXCEPTION_PRICE_VARIANCE"
                match_summary["price_variance_lines"] += 1
                match_summary["total_price_variance_amount"] += round(unit_price_diff * line.invoiced_quantity, 2)
                line_exceptions.append(line.match_status)
            else:
                line.match_status = "MATCHED"
                match_summary["matched_lines"] += 1

        # Roll up to Invoice Match Status
        if not line_exceptions:
            overall_status = "MATCHED"
            details = "All invoice lines strictly reconciled against PO and Goods Receipt within policy tolerances."
        elif "EXCEPTION_MISSING_RECEIPT" in line_exceptions:
            overall_status = "EXCEPTION_MISSING_RECEIPT"
            details = f"Goods receipt missing or pending physical inspection for {match_summary['missing_receipt_lines']} line(s)."
        elif "EXCEPTION_QUANTITY_MISMATCH" in line_exceptions:
            overall_status = "EXCEPTION_QUANTITY_MISMATCH"
            details = f"Invoiced quantity exceeds dock received/accepted quantity. Discrepancy: {match_summary['total_quantity_variance']} units."
        elif "EXCEPTION_PRICE_VARIANCE" in line_exceptions:
            overall_status = "EXCEPTION_PRICE_VARIANCE"
            details = f"Line unit price exceeds contractual PO price by {match_summary['total_price_variance_amount']} {invoice.currency}."
        else:
            overall_status = "EXCEPTION_PRICE_VARIANCE"
            details = "Match discrepancy identified."

        evt = AuditEvent(
            event_id=f"EVT-2026-{event_counter:06d}",
            entity_name="Invoice",
            entity_id=invoice.invoice_id,
            action="MATCH_EVALUATED",
            actor_role="SYSTEM",
            actor_id="SYS-AUTO",
            previous_state=invoice.status,
            new_state=overall_status,
            details=details,
            timestamp=invoice.created_at,
        )
        events.append(evt)

        return overall_status, lines, events, match_summary
