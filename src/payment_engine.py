"""
Payment Readiness & Approval Engine Module
Enforces strict policy-based payment authorization:
Only verified, 3-way matched, non-anomalous invoices are authorized for payment.
"""

from typing import Dict, List, Tuple, Any, Optional
from src.models import Invoice, Approval, Payment, AuditEvent

class PaymentReadinessEngine:
    """
    Evaluates payment readiness, generates approval events, and creates
    scheduled payment disbursement records for clean invoices.
    """

    def __init__(self):
        self.approval_counter = 1
        self.payment_counter = 1

    def process_payment_readiness(
        self,
        invoice: Invoice,
        match_status: str,
        event_counter: int
    ) -> Tuple[Optional[Approval], Optional[Payment], List[AuditEvent]]:
        """
        Processes invoice readiness.
        If matched, issues Auto-Approval and schedules Payment.
        If exception, quarantines invoice and suppresses payment.
        """
        events: List[AuditEvent] = []

        if match_status == "MATCHED":
            # 1. Generate Approval Record
            app_id = f"APP-2026-{self.approval_counter:06d}"
            self.approval_counter += 1

            approval = Approval(
                approval_id=app_id,
                invoice_id=invoice.invoice_id,
                approver_id="SYS-AUTO",
                approver_role="PROCESS_OWNER",
                approval_type="AUTO_APPROVAL",
                decision="APPROVED",
                comments="Three-way match confirmed within contract tolerances. Automated approval granted.",
                decision_date=invoice.created_at,
            )

            # Audit Event: Approval Granted
            evt_app = AuditEvent(
                event_id=f"EVT-2026-{event_counter:06d}",
                entity_name="Approval",
                entity_id=app_id,
                action="APPROVED",
                actor_role="PROCESS_OWNER",
                actor_id="SYS-AUTO",
                previous_state="RECEIVED",
                new_state="APPROVED",
                details=f"Invoice {invoice.invoice_id} auto-approved for payment readiness.",
                timestamp=invoice.created_at,
            )
            events.append(evt_app)

            # 2. Generate Scheduled Payment Record
            pay_id = f"PAY-2026-{self.payment_counter:06d}"
            self.payment_counter += 1

            payment = Payment(
                payment_id=pay_id,
                invoice_id=invoice.invoice_id,
                vendor_id=invoice.vendor_id,
                amount=invoice.total_amount,
                currency=invoice.currency,
                payment_method="ACH",
                payment_reference=f"EFT-2026-{self.payment_counter:06d}",
                scheduled_date=invoice.due_date,
                execution_date=None,
                status="SCHEDULED",
                created_at=invoice.created_at,
            )

            # Audit Event: Payment Scheduled
            evt_pay = AuditEvent(
                event_id=f"EVT-2026-{(event_counter + 1):06d}",
                entity_name="Payment",
                entity_id=pay_id,
                action="PAYMENT_AUTHORIZED",
                actor_role="SYSTEM",
                actor_id="SYS-AUTO",
                previous_state=None,
                new_state="SCHEDULED",
                details=f"Disbursement of {invoice.total_amount:.2f} {invoice.currency} scheduled for {invoice.due_date} via ACH.",
                timestamp=invoice.created_at,
            )
            events.append(evt_pay)

            # Update Invoice Lifecycle
            invoice.status = "PAYMENT_READY"

            return approval, payment, events

        else:
            # Invoice has an exception: Strictly blocked from payment readiness
            if match_status in ("EXCEPTION_CLOSED_VENDOR", "EXCEPTION_DUPLICATE"):
                invoice.status = "REJECTED"
            else:
                invoice.status = "IN_REVIEW"

            return None, None, events
