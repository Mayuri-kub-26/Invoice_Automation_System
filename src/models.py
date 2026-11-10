"""
Data models for the invoice automation system.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

@dataclass
class Vendor:
    vendor_id: str
    vendor_name: str
    tax_id: str
    status: str
    payment_terms: str
    currency: str
    contact_email: str
    address_country: str
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PurchaseOrder:
    po_id: str
    vendor_id: str
    buyer_id: str
    department: str
    status: str
    currency: str
    subtotal_amount: float
    tax_amount: float
    total_amount: float
    order_date: str
    expected_delivery_date: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PurchaseOrderLine:
    po_line_id: str
    po_id: str
    line_number: int
    sku: str
    item_description: str
    ordered_quantity: float
    unit_of_measure: str
    unit_price: float
    tax_code: str
    tax_rate: float
    line_subtotal: float
    line_tax: float
    line_total: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GoodsReceipt:
    grn_id: str
    po_id: str
    received_by: str
    receipt_date: str
    delivery_note_ref: str
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GoodsReceiptLine:
    grn_line_id: str
    grn_id: str
    po_line_id: str
    line_number: int
    received_quantity: float
    accepted_quantity: float
    rejected_quantity: float
    inspection_notes: Optional[str] = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Invoice:
    invoice_id: str
    invoice_number: str
    vendor_id: str
    po_id: Optional[str]
    invoice_date: str
    due_date: str
    currency: str
    subtotal_amount: float
    tax_amount: float
    total_amount: float
    intake_channel: str
    match_status: str
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InvoiceLine:
    invoice_line_id: str
    invoice_id: str
    po_line_id: Optional[str]
    line_number: int
    sku: str
    item_description: str
    invoiced_quantity: float
    unit_of_measure: str
    unit_price: float
    tax_code: str
    tax_rate: float
    line_subtotal: float
    line_tax: float
    line_total: float
    match_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Approval:
    approval_id: str
    invoice_id: str
    approver_id: str
    approver_role: str
    approval_type: str
    decision: str
    comments: str
    decision_date: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Payment:
    payment_id: str
    invoice_id: str
    vendor_id: str
    amount: float
    currency: str
    payment_method: str
    payment_reference: str
    scheduled_date: str
    execution_date: Optional[str]
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AuditEvent:
    event_id: str
    entity_name: str
    entity_id: str
    action: str
    actor_role: str
    actor_id: str
    previous_state: Optional[str]
    new_state: str
    details: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GroundTruthRecord:
    invoice_id: str
    invoice_number: str
    vendor_id: str
    po_id: Optional[str]
    is_anomaly: bool
    anomaly_type: str
    expected_match_status: str
    expected_routing_role: str
    expected_payment_ready: bool
    root_cause_field: str
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
