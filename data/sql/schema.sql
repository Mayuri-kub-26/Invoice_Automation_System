-- =====================================================================
-- Invoice automation database schema
-- Standard: ANSI SQL / SQLite / PostgreSQL compatible
-- =====================================================================

PRAGMA foreign_keys = ON;

-- 1. Master Vendor Table
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id VARCHAR(16) PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL UNIQUE,
    tax_id VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL CHECK(status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'CLOSED')),
    payment_terms VARCHAR(20) NOT NULL CHECK(payment_terms IN ('NET15', 'NET30', 'NET45', 'NET60', 'DUE_ON_RECEIPT')),
    currency VARCHAR(3) NOT NULL CHECK(currency IN ('USD', 'EUR', 'GBP', 'CAD')),
    contact_email VARCHAR(100) NOT NULL,
    address_country VARCHAR(2) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- 2. Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id VARCHAR(20) PRIMARY KEY,
    vendor_id VARCHAR(16) NOT NULL,
    buyer_id VARCHAR(20) NOT NULL,
    department VARCHAR(50) NOT NULL,
    status VARCHAR(25) NOT NULL CHECK(status IN ('ISSUED', 'PARTIALLY_FULFILLED', 'FULFILLED', 'CANCELLED', 'CLOSED')),
    currency VARCHAR(3) NOT NULL,
    subtotal_amount DECIMAL(12,2) NOT NULL CHECK(subtotal_amount >= 0.00),
    tax_amount DECIMAL(12,2) NOT NULL CHECK(tax_amount >= 0.00),
    total_amount DECIMAL(12,2) NOT NULL CHECK(total_amount >= 0.00),
    order_date DATE NOT NULL,
    expected_delivery_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

-- 3. Purchase Order Lines
CREATE TABLE IF NOT EXISTS purchase_order_lines (
    po_line_id VARCHAR(30) PRIMARY KEY,
    po_id VARCHAR(20) NOT NULL,
    line_number INTEGER NOT NULL CHECK(line_number BETWEEN 1 AND 8),
    sku VARCHAR(50) NOT NULL,
    item_description VARCHAR(255) NOT NULL,
    ordered_quantity DECIMAL(10,2) NOT NULL CHECK(ordered_quantity > 0.00),
    unit_of_measure VARCHAR(10) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL CHECK(unit_price > 0.00),
    tax_code VARCHAR(10) NOT NULL,
    tax_rate DECIMAL(5,4) NOT NULL CHECK(tax_rate >= 0.0000),
    line_subtotal DECIMAL(12,2) NOT NULL,
    line_tax DECIMAL(12,2) NOT NULL,
    line_total DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)
);

-- 4. Goods Receipts
CREATE TABLE IF NOT EXISTS goods_receipts (
    grn_id VARCHAR(20) PRIMARY KEY,
    po_id VARCHAR(20) NOT NULL,
    received_by VARCHAR(20) NOT NULL,
    receipt_date DATE NOT NULL,
    delivery_note_ref VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK(status IN ('RECEIVED', 'PARTIALLY_RECEIVED', 'REJECTED')),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)
);

-- 5. Goods Receipt Lines
CREATE TABLE IF NOT EXISTS goods_receipt_lines (
    grn_line_id VARCHAR(30) PRIMARY KEY,
    grn_id VARCHAR(20) NOT NULL,
    po_line_id VARCHAR(30) NOT NULL,
    line_number INTEGER NOT NULL CHECK(line_number BETWEEN 1 AND 8),
    received_quantity DECIMAL(10,2) NOT NULL CHECK(received_quantity >= 0.00),
    accepted_quantity DECIMAL(10,2) NOT NULL CHECK(accepted_quantity >= 0.00),
    rejected_quantity DECIMAL(10,2) NOT NULL CHECK(rejected_quantity >= 0.00),
    inspection_notes VARCHAR(255),
    FOREIGN KEY (grn_id) REFERENCES goods_receipts(grn_id),
    FOREIGN KEY (po_line_id) REFERENCES purchase_order_lines(po_line_id)
);

-- 6. Invoices
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id VARCHAR(35) PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL,
    vendor_id VARCHAR(16) NOT NULL,
    po_id VARCHAR(20),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    currency VARCHAR(3) NOT NULL,
    subtotal_amount DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    intake_channel VARCHAR(20) NOT NULL CHECK(intake_channel IN ('EMAIL_OCR', 'PORTAL_UPLOAD', 'EDI', 'PAPER_SCAN')),
    match_status VARCHAR(30) NOT NULL,
    status VARCHAR(25) NOT NULL CHECK(status IN ('RECEIVED', 'EXTRACTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'PAYMENT_READY', 'PAID')),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)
);

-- 7. Invoice Lines
CREATE TABLE IF NOT EXISTS invoice_lines (
    invoice_line_id VARCHAR(45) PRIMARY KEY,
    invoice_id VARCHAR(35) NOT NULL,
    po_line_id VARCHAR(30),
    line_number INTEGER NOT NULL CHECK(line_number BETWEEN 1 AND 8),
    sku VARCHAR(50) NOT NULL,
    item_description VARCHAR(255) NOT NULL,
    invoiced_quantity DECIMAL(10,2) NOT NULL CHECK(invoiced_quantity > 0.00),
    unit_of_measure VARCHAR(10) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL CHECK(unit_price > 0.00),
    tax_code VARCHAR(10) NOT NULL,
    tax_rate DECIMAL(5,4) NOT NULL CHECK(tax_rate >= 0.0000),
    line_subtotal DECIMAL(12,2) NOT NULL,
    line_tax DECIMAL(12,2) NOT NULL,
    line_total DECIMAL(12,2) NOT NULL,
    match_status VARCHAR(30) NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (po_line_id) REFERENCES purchase_order_lines(po_line_id)
);

-- 8. Approvals
CREATE TABLE IF NOT EXISTS approvals (
    approval_id VARCHAR(25) PRIMARY KEY,
    invoice_id VARCHAR(35) NOT NULL,
    approver_id VARCHAR(20) NOT NULL,
    approver_role VARCHAR(30) NOT NULL CHECK(approver_role IN ('BUSINESS_REQUESTER', 'PROCESS_OWNER', 'APPROVER', 'OPERATIONS_ANALYST', 'SYSTEM_ADMIN')),
    approval_type VARCHAR(30) NOT NULL CHECK(approval_type IN ('AUTO_APPROVAL', 'PRICE_VARIANCE_APPROVAL', 'MANUAL_OVERRIDE', 'EXCEPTION_CLEARANCE')),
    decision VARCHAR(15) NOT NULL CHECK(decision IN ('APPROVED', 'REJECTED', 'ESCALATED')),
    comments TEXT,
    decision_date TIMESTAMP NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
);

-- 9. Payments
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(25) PRIMARY KEY,
    invoice_id VARCHAR(35) NOT NULL UNIQUE,
    vendor_id VARCHAR(16) NOT NULL,
    amount DECIMAL(12,2) NOT NULL CHECK(amount > 0.00),
    currency VARCHAR(3) NOT NULL,
    payment_method VARCHAR(20) NOT NULL CHECK(payment_method IN ('ACH', 'WIRE', 'CHECK', 'VIRTUAL_CARD')),
    payment_reference VARCHAR(50) NOT NULL UNIQUE,
    scheduled_date DATE NOT NULL,
    execution_date DATE,
    status VARCHAR(20) NOT NULL CHECK(status IN ('SCHEDULED', 'PROCESSING', 'EXECUTED', 'FAILED')),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

-- 10. Audit Events (Traceability and Event Sourcing)
CREATE TABLE IF NOT EXISTS audit_events (
    event_id VARCHAR(30) PRIMARY KEY,
    entity_name VARCHAR(30) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    action VARCHAR(40) NOT NULL,
    actor_role VARCHAR(30) NOT NULL,
    actor_id VARCHAR(30) NOT NULL,
    previous_state VARCHAR(30),
    new_state VARCHAR(30) NOT NULL,
    details TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

-- Indexes for Query Performance & Lookups
CREATE INDEX IF NOT EXISTS idx_po_vendor ON purchase_orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_pol_po ON purchase_order_lines(po_id);
CREATE INDEX IF NOT EXISTS idx_grn_po ON goods_receipts(po_id);
CREATE INDEX IF NOT EXISTS idx_grnl_grn ON goods_receipt_lines(grn_id);
CREATE INDEX IF NOT EXISTS idx_grnl_pol ON goods_receipt_lines(po_line_id);
CREATE INDEX IF NOT EXISTS idx_inv_vendor ON invoices(vendor_id);
CREATE INDEX IF NOT EXISTS idx_inv_po ON invoices(po_id);
CREATE INDEX IF NOT EXISTS idx_inv_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_inv_match_status ON invoices(match_status);
CREATE INDEX IF NOT EXISTS idx_invl_invoice ON invoice_lines(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invl_pol ON invoice_lines(po_line_id);
CREATE INDEX IF NOT EXISTS idx_app_invoice ON approvals(invoice_id);
CREATE INDEX IF NOT EXISTS idx_pay_invoice ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_evt_entity ON audit_events(entity_name, entity_id);
