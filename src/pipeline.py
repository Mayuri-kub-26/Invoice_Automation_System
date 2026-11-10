"""
End-to-End Invoice Processing Pipeline Orchestrator
Coordinates Intake Validation, 3-Way Matching, Exception Routing,
Approval Generation, Payment Readiness, and Immutable Audit Logging.
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from src.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
)
from src.models import (
    Vendor,
    PurchaseOrder,
    PurchaseOrderLine,
    GoodsReceipt,
    GoodsReceiptLine,
    Invoice,
    InvoiceLine,
    Approval,
    Payment,
    AuditEvent,
)
from src.extractor import ExtractionValidator
from src.matcher import ThreeWayMatcher
from src.router import ExceptionRouter, InvoiceExceptionRecord
from src.payment_engine import PaymentReadinessEngine

class InvoiceProcessingPipeline:
    """
    Workflow engine that runs the full invoice lifecycle.
    """

    def __init__(self, raw_data_dir: Optional[Path] = None, processed_data_dir: Optional[Path] = None):
        self.raw_dir = raw_data_dir or RAW_DATA_DIR
        self.processed_dir = processed_data_dir or PROCESSED_DATA_DIR
        os.makedirs(self.processed_dir, exist_ok=True)

        self.event_counter = 1

        # Output containers
        self.processed_invoices: List[Invoice] = []
        self.processed_lines: List[InvoiceLine] = []
        self.approvals: List[Approval] = []
        self.payments: List[Payment] = []
        self.exceptions: List[InvoiceExceptionRecord] = []
        self.audit_events: List[AuditEvent] = []
        self.match_results: List[Dict[str, Any]] = []

    def load_raw_data(self) -> Tuple[
        List[Vendor],
        List[PurchaseOrder],
        List[PurchaseOrderLine],
        List[GoodsReceipt],
        List[GoodsReceiptLine],
        List[Invoice],
        List[InvoiceLine],
    ]:
        """Loads generated raw CSV datasets into typed model instances."""
        def load_csv(filename: str):
            filepath = self.raw_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Raw data file not found: {filepath}. Run generator first.")
            with open(filepath, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))

        vendors = [
            Vendor(
                vendor_id=r["vendor_id"],
                vendor_name=r["vendor_name"],
                tax_id=r["tax_id"],
                status=r["status"],
                payment_terms=r["payment_terms"],
                currency=r["currency"],
                contact_email=r["contact_email"],
                address_country=r["address_country"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in load_csv("vendors.csv")
        ]

        purchase_orders = [
            PurchaseOrder(
                po_id=r["po_id"],
                vendor_id=r["vendor_id"],
                buyer_id=r["buyer_id"],
                department=r["department"],
                status=r["status"],
                currency=r["currency"],
                subtotal_amount=float(r["subtotal_amount"]),
                tax_amount=float(r["tax_amount"]),
                total_amount=float(r["total_amount"]),
                order_date=r["order_date"],
                expected_delivery_date=r["expected_delivery_date"],
                created_at=r["created_at"],
            )
            for r in load_csv("purchase_orders.csv")
        ]

        po_lines = [
            PurchaseOrderLine(
                po_line_id=r["po_line_id"],
                po_id=r["po_id"],
                line_number=int(r["line_number"]),
                sku=r["sku"],
                item_description=r["item_description"],
                ordered_quantity=float(r["ordered_quantity"]),
                unit_of_measure=r["unit_of_measure"],
                unit_price=float(r["unit_price"]),
                tax_code=r["tax_code"],
                tax_rate=float(r["tax_rate"]),
                line_subtotal=float(r["line_subtotal"]),
                line_tax=float(r["line_tax"]),
                line_total=float(r["line_total"]),
            )
            for r in load_csv("po_lines.csv")
        ]

        goods_receipts = [
            GoodsReceipt(
                grn_id=r["grn_id"],
                po_id=r["po_id"],
                received_by=r["received_by"],
                receipt_date=r["receipt_date"],
                delivery_note_ref=r["delivery_note_ref"],
                status=r["status"],
                created_at=r["created_at"],
            )
            for r in load_csv("goods_receipts.csv")
        ]

        goods_receipt_lines = [
            GoodsReceiptLine(
                grn_line_id=r["grn_line_id"],
                grn_id=r["grn_id"],
                po_line_id=r["po_line_id"],
                line_number=int(r["line_number"]),
                received_quantity=float(r["received_quantity"]),
                accepted_quantity=float(r["accepted_quantity"]),
                rejected_quantity=float(r["rejected_quantity"]),
                inspection_notes=r.get("inspection_notes", ""),
            )
            for r in load_csv("goods_receipt_lines.csv")
        ]

        invoices = [
            Invoice(
                invoice_id=r["invoice_id"],
                invoice_number=r["invoice_number"],
                vendor_id=r["vendor_id"],
                po_id=r["po_id"] if r["po_id"] else None,
                invoice_date=r["invoice_date"],
                due_date=r["due_date"],
                currency=r["currency"],
                subtotal_amount=float(r["subtotal_amount"]),
                tax_amount=float(r["tax_amount"]),
                total_amount=float(r["total_amount"]),
                intake_channel=r["intake_channel"],
                match_status=r["match_status"],
                status=r["status"],
                created_at=r["created_at"],
            )
            for r in load_csv("invoices.csv")
        ]

        invoice_lines = [
            InvoiceLine(
                invoice_line_id=r["invoice_line_id"],
                invoice_id=r["invoice_id"],
                po_line_id=r["po_line_id"] if r["po_line_id"] else None,
                line_number=int(r["line_number"]),
                sku=r["sku"],
                item_description=r["item_description"],
                invoiced_quantity=float(r["invoiced_quantity"]),
                unit_of_measure=r["unit_of_measure"],
                unit_price=float(r["unit_price"]),
                tax_code=r["tax_code"],
                tax_rate=float(r["tax_rate"]),
                line_subtotal=float(r["line_subtotal"]),
                line_tax=float(r["line_tax"]),
                line_total=float(r["line_total"]),
                match_status=r["match_status"],
            )
            for r in load_csv("invoice_lines.csv")
        ]

        return (
            vendors,
            purchase_orders,
            po_lines,
            goods_receipts,
            goods_receipt_lines,
            invoices,
            invoice_lines,
        )

    def run_pipeline(self):
        """Executes the complete invoice intake, 3-way match, and payment readiness flow."""
        (
            vendors,
            purchase_orders,
            po_lines,
            goods_receipts,
            goods_receipt_lines,
            invoices,
            invoice_lines,
        ) = self.load_raw_data()

        # Group invoice lines by invoice_id
        lines_by_invoice: Dict[str, List[InvoiceLine]] = {}
        for line in invoice_lines:
            lines_by_invoice.setdefault(line.invoice_id, []).append(line)

        # Initialize workflow engines
        extractor = ExtractionValidator(vendors, purchase_orders)
        matcher = ThreeWayMatcher(purchase_orders, po_lines, goods_receipts, goods_receipt_lines)
        router = ExceptionRouter()
        payment_engine = PaymentReadinessEngine()

        for inv in invoices:
            lines = lines_by_invoice.get(inv.invoice_id, [])

            # Phase 1: Intake & Extraction Validation
            intake_exc, root_field, intake_events = extractor.validate_intake(
                inv, lines, self.event_counter
            )
            self.event_counter += len(intake_events)
            self.audit_events.extend(intake_events)

            if intake_exc is not None:
                # Intake validation failed: update status and route exception
                inv.match_status = intake_exc
                inv.status = "REJECTED" if intake_exc in ("EXCEPTION_CLOSED_VENDOR", "EXCEPTION_DUPLICATE") else "IN_REVIEW"

                exc_rec, exc_evt = router.route_exception(inv, intake_exc, self.event_counter)
                self.event_counter += 1
                self.exceptions.append(exc_rec)
                self.audit_events.append(exc_evt)

                # Record match result
                self.match_results.append({
                    "invoice_id": inv.invoice_id,
                    "po_id": inv.po_id,
                    "match_status": intake_exc,
                    "is_exception": True,
                    "exception_stage": "INTAKE_VALIDATION",
                    "root_cause_field": root_field,
                })

            else:
                # Phase 2: 3-Way Reconciliations
                match_status, evaluated_lines, match_evts, match_summary = matcher.evaluate_invoice(
                    inv, lines, self.event_counter
                )
                self.event_counter += len(match_evts)
                self.audit_events.extend(match_evts)
                inv.match_status = match_status

                # Phase 3: Route Exception or Authorize Payment
                if match_status != "MATCHED":
                    exc_rec, exc_evt = router.route_exception(
                        inv, match_status, self.event_counter, match_summary
                    )
                    self.event_counter += 1
                    self.exceptions.append(exc_rec)
                    self.audit_events.append(exc_evt)

                    # Update status
                    inv.status = "IN_REVIEW"

                    self.match_results.append({
                        "invoice_id": inv.invoice_id,
                        "po_id": inv.po_id,
                        "match_status": match_status,
                        "is_exception": True,
                        "exception_stage": "THREE_WAY_MATCH",
                        "root_cause_field": "line_variance",
                    })

                else:
                    # Clean match: Authorize Payment Readiness
                    approval, payment, pay_evts = payment_engine.process_payment_readiness(
                        inv, match_status, self.event_counter
                    )
                    self.event_counter += len(pay_evts)
                    self.audit_events.extend(pay_evts)

                    if approval:
                        self.approvals.append(approval)
                    if payment:
                        self.payments.append(payment)

                    self.match_results.append({
                        "invoice_id": inv.invoice_id,
                        "po_id": inv.po_id,
                        "match_status": "MATCHED",
                        "is_exception": False,
                        "exception_stage": "NONE",
                        "root_cause_field": "NONE",
                    })

            self.processed_invoices.append(inv)
            self.processed_lines.extend(lines)

        self.export_processed_data()

    def export_processed_data(self):
        """Exports all processed workflow outcomes to CSV and JSON."""
        exports = {
            "invoices_processed": [inv.to_dict() for inv in self.processed_invoices],
            "invoice_lines_processed": [l.to_dict() for l in self.processed_lines],
            "match_results": self.match_results,
            "exceptions": [exc.to_dict() for exc in self.exceptions],
            "approvals": [app.to_dict() for app in self.approvals],
            "payments": [pay.to_dict() for pay in self.payments],
            "audit_events": [evt.to_dict() for evt in self.audit_events],
        }

        for name, records in exports.items():
            csv_path = self.processed_dir / f"{name}.csv"
            json_path = self.processed_dir / f"{name}.json"

            if records:
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
                    writer.writeheader()
                    writer.writerows(records)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)

        print(f"[Pipeline] Processing completed. Results exported to {self.processed_dir}")
        print(f"  - Invoices Evaluated: {len(self.processed_invoices)}")
        print(f"  - Approvals Issued: {len(self.approvals)}")
        print(f"  - Payments Scheduled: {len(self.payments)}")
        print(f"  - Exceptions Routed: {len(self.exceptions)}")
        print(f"  - Audit Trail Events: {len(self.audit_events)}")
