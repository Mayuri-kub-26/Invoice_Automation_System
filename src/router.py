"""
Exception Routing Module
Routes invoice discrepancies to designated organizational actors based on
governance rules, exception severity, and dollar value thresholds.
"""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from src.models import Invoice, AuditEvent

@dataclass
class InvoiceExceptionRecord:
    exception_id: str
    invoice_id: str
    vendor_id: str
    exception_type: str
    assigned_role: str
    assigned_actor_id: str
    priority: str
    action_required: str
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ExceptionRouter:
    """
    Intelligent routing engine that directs invoice exceptions to the right actors:
    - Business Requester: Quantity issues, receipt follow-up
    - Approver / Process Owner: Price variances, budget overrides
    - Operations Analyst: Arithmetic, temporal, tax discrepancies
    - System Administrator: Duplicate suppression, closed vendor blocks
    """

    def __init__(self):
        self.exception_counter = 1

    def route_exception(
        self,
        invoice: Invoice,
        match_status: str,
        event_counter: int,
        variance_details: Optional[Dict[str, Any]] = None
    ) -> Tuple[InvoiceExceptionRecord, AuditEvent]:
        """
        Determines the designated actor, priority, and required resolution action.
        """
        exc_id = f"EXC-2026-{self.exception_counter:06d}"
        self.exception_counter += 1

        if match_status == "EXCEPTION_PRICE_VARIANCE":
            # High dollar variance goes to Process Owner; standard goes to Approver
            var_amt = variance_details.get("total_price_variance_amount", 0.0) if variance_details else 0.0
            if var_amt > 500.00:
                role = "PROCESS_OWNER"
                actor_id = "EMP-1001"
                priority = "HIGH"
                action = f"Review high price variance (${var_amt:.2f}) and authorize contract amendment or price override."
            else:
                role = "APPROVER"
                actor_id = "EMP-1010"
                priority = "MEDIUM"
                action = f"Review line unit price variance against PO rate and approve cost variance or request credit memo."

        elif match_status == "EXCEPTION_QUANTITY_MISMATCH":
            role = "BUSINESS_REQUESTER"
            actor_id = "EMP-1025"
            priority = "HIGH"
            action = "Confirm physical receipt status with warehouse dock or request amended billing for partial delivery."

        elif match_status == "EXCEPTION_MISSING_RECEIPT":
            role = "OPERATIONS_ANALYST"
            actor_id = "EMP-2005"
            priority = "HIGH"
            action = "Expedite Goods Receipt creation with receiving dock or verify logistics tracking details."

        elif match_status == "EXCEPTION_ARITHMETIC_ERROR":
            role = "OPERATIONS_ANALYST"
            actor_id = "EMP-2010"
            priority = "MEDIUM"
            action = "Reject invoice payload back to vendor due to line arithmetic / grand total reconciliation failure."

        elif match_status == "EXCEPTION_TAX_MISMATCH":
            role = "OPERATIONS_ANALYST"
            actor_id = "EMP-2012"
            priority = "MEDIUM"
            action = "Verify tax code compliance with finance tax matrix; request corrected tax invoice."

        elif match_status == "EXCEPTION_CLOSED_VENDOR":
            role = "SYSTEM_ADMIN"
            actor_id = "EMP-3001"
            priority = "CRITICAL"
            action = "Vendor status is INACTIVE or CLOSED. Block settlement and notify vendor management procurement."

        elif match_status == "EXCEPTION_DUPLICATE":
            role = "SYSTEM_ADMIN"
            actor_id = "EMP-3001"
            priority = "CRITICAL"
            action = "Potential duplicate submission detected. Void invoice intake to prevent double payment disbursement."

        elif match_status == "EXCEPTION_TEMPORAL_VIOLATION":
            role = "OPERATIONS_ANALYST"
            actor_id = "EMP-2015"
            priority = "LOW"
            action = "Invoice date precedes purchase order issue date. Verify retro-billing authorization."

        else:
            role = "OPERATIONS_ANALYST"
            actor_id = "EMP-2001"
            priority = "MEDIUM"
            action = "Investigate unclassified processing discrepancy."

        record = InvoiceExceptionRecord(
            exception_id=exc_id,
            invoice_id=invoice.invoice_id,
            vendor_id=invoice.vendor_id,
            exception_type=match_status,
            assigned_role=role,
            assigned_actor_id=actor_id,
            priority=priority,
            action_required=action,
            status="OPEN",
            created_at=invoice.created_at,
        )

        audit_evt = AuditEvent(
            event_id=f"EVT-2026-{event_counter:06d}",
            entity_name="Invoice",
            entity_id=invoice.invoice_id,
            action="EXCEPTION_ROUTED",
            actor_role=role,
            actor_id=actor_id,
            previous_state=invoice.status,
            new_state="IN_REVIEW",
            details=f"Discrepancy routed to {role} [{actor_id}] - Priority: {priority}. Action: {action}",
            timestamp=invoice.created_at,
        )

        return record, audit_evt
