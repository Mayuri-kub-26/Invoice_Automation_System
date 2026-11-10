# Data Dictionary

Schema reference for the invoice intake, 3-way matching, exception routing and payment
readiness pipeline. It covers the entity relationships, field types, allowed values and the
validation rules the pipeline relies on.

---

### Entity relationships

```
+---------------+           1:N           +---------------------+
|    Vendor     |------------------------<|    PurchaseOrder    |
+---------------+                         +---------------------+
        | 1                                          | 1
        |                                            |
        | 1:N                                        | 1:N
        v                                            v
+---------------+           1:N           +---------------------+
|    Invoice    |------------------------<|  PurchaseOrderLine  |
+---------------+                         +---------------------+
        | 1                                          | 1
        |                                            |
        | 1:N                                        | 1:N
        v                                            v
+---------------+           N:1           +---------------------+
|  InvoiceLine  |>------------------------|  GoodsReceiptLine   |
+---------------+                         +---------------------+
        | 1                                          ^
        |                                            | 1:N
        | 1:1/1:N                                    | 1
        v                                 +---------------------+
+---------------+                         |    GoodsReceipt     |
|   Approval    |                         +---------------------+
+---------------+
        | 1
        | 1:1
        v
+---------------+
|    Payment    |
+---------------+
```

---

### Tables

#### 1. Entity: `Vendor`
- **Description**: Master repository of approved suppliers, tax compliance attributes, and payment terms.
- **Primary Key**: `vendor_id`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `vendor_id` | VARCHAR(16) | Yes | Regex `^VND-[0-9]{5}$` | None | Primary Key | Zero-padded 5 digits. Example: `VND-00001` |
| `vendor_name` | VARCHAR(100) | Yes | Non-empty string | None | Unique | Standard corporate trade name |
| `tax_id` | VARCHAR(20) | Yes | Regex `^[0-9]{2}-[0-9]{7}$` | None | Unique | Federal/Regional Tax Identification Number |
| `status` | VARCHAR(20) | Yes | `ACTIVE`, `INACTIVE`, `SUSPENDED`, `CLOSED` | None | No | Only `ACTIVE` vendors can issue POs/invoices |
| `payment_terms` | VARCHAR(20) | Yes | `NET15`, `NET30`, `NET45`, `NET60`, `DUE_ON_RECEIPT` | None | No | Determines payment due date calculation |
| `currency` | VARCHAR(3) | Yes | `USD`, `EUR`, `GBP`, `CAD` | ISO-4217 | No | Master currency for transactions |
| `contact_email` | VARCHAR(100) | Yes | Valid email format | None | No | Automated remittance and exception notifications |
| `address_country` | VARCHAR(2) | Yes | `US`, `GB`, `DE`, `CA`, `IN` | ISO-3166-1 | No | Standard two-letter country code |
| `created_at` | TIMESTAMP | Yes | ISO-8601 | UTC | No | Must precede transaction dates |
| `updated_at` | TIMESTAMP | Yes | ISO-8601 | UTC | No | Must be `>= created_at` |

---

#### 2. Entity: `PurchaseOrder`
- **Description**: Commercial commitment issued by buyer specifying items, quantities, and agreed prices.
- **Primary Key**: `po_id`
- **Foreign Keys**: `vendor_id` -> `Vendor(vendor_id)`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `po_id` | VARCHAR(20) | Yes | Regex `^PO-2026-[0-9]{6}$` | None | Primary Key | Format `PO-2026-000001` |
| `vendor_id` | VARCHAR(16) | Yes | Valid `Vendor.vendor_id` | None | No | Must reference an existing `ACTIVE` vendor |
| `buyer_id` | VARCHAR(20) | Yes | Regex `^EMP-[0-9]{4}$` | None | No | Internal employee ID of business requester |
| `department` | VARCHAR(50) | Yes | `Engineering`, `Operations`, `IT`, `Marketing`, `Facilities` | None | No | Cost center attribution |
| `status` | VARCHAR(25) | Yes | `ISSUED`, `PARTIALLY_FULFILLED`, `FULFILLED`, `CANCELLED`, `CLOSED` | None | No | Lifecycle state tracker |
| `currency` | VARCHAR(3) | Yes | `USD`, `EUR`, `GBP`, `CAD` | ISO-4217 | No | Must match referenced Vendor currency |
| `subtotal_amount` | DECIMAL(12,2)| Yes | Float `>= 0.00` | Currency | No | Derived exact sum of `PurchaseOrderLine.line_subtotal` |
| `tax_amount` | DECIMAL(12,2)| Yes | Float `>= 0.00` | Currency | No | Derived exact sum of `PurchaseOrderLine.line_tax` |
| `total_amount` | DECIMAL(12,2)| Yes | Float `>= 0.00` | Currency | No | Must equal `subtotal_amount + tax_amount` |
| `order_date` | DATE | Yes | YYYY-MM-DD | None | No | Date PO was legally committed |
| `expected_delivery_date`| DATE | Yes | YYYY-MM-DD | None | No | Must be `>= order_date` |
| `created_at` | TIMESTAMP | Yes | ISO-8601 | UTC | No | Audit record timestamp |

---

#### 3. Entity: `PurchaseOrderLine`
- **Description**: Itemized SKU rows within an authorized Purchase Order.
- **Primary Key**: `po_line_id`
- **Foreign Keys**: `po_id` -> `PurchaseOrder(po_id)`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `po_line_id` | VARCHAR(30) | Yes | Regex `^POL-PO-2026-[0-9]{6}-[0-9]{2}$` | None | Primary Key | Format `POL-PO-2026-000001-01` |
| `po_id` | VARCHAR(20) | Yes | Valid `PurchaseOrder.po_id` | None | No | Parent PO relationship |
| `line_number` | INTEGER | Yes | 1 to 8 | None | No | Sequential row sequence per PO |
| `sku` | VARCHAR(50) | Yes | Alphanumeric SKU identifier | None | No | Catalog stock keeping unit code |
| `item_description` | VARCHAR(255)| Yes | Free text | None | No | Plain English item or service description |
| `ordered_quantity`| DECIMAL(10,2)| Yes | `> 0.00` | UOM units | No | Authorized purchase volume |
| `unit_of_measure` | VARCHAR(10) | Yes | `EA`, `BOX`, `HRS`, `KG`, `LTR` | None | No | Standard packaging or service unit |
| `unit_price` | DECIMAL(10,2)| Yes | `> 0.00` | Currency/UOM| No | Contractual unit price |
| `tax_code` | VARCHAR(10) | Yes | `TAX_0`, `TAX_5`, `TAX_10`, `TAX_18`, `TAX_EXEMPT` | None | No | Tax jurisdiction classification |
| `tax_rate` | DECIMAL(5,4) | Yes | `0.0000`, `0.0500`, `0.1000`, `0.1800` | Percentage | No | Tax fraction corresponding to tax_code |
| `line_subtotal` | DECIMAL(12,2)| Yes | Float `> 0.00` | Currency | No | Must equal `ROUND(ordered_quantity * unit_price, 2)` |
| `line_tax` | DECIMAL(12,2)| Yes | Float `>= 0.00` | Currency | No | Must equal `ROUND(line_subtotal * tax_rate, 2)` |
| `line_total` | DECIMAL(12,2)| Yes | Float `> 0.00` | Currency | No | Must equal `line_subtotal + line_tax` |

---

#### 4. Entity: `GoodsReceipt`
- **Description**: Proof of physical receipt and warehouse acceptance of delivered goods.
- **Primary Key**: `grn_id`
- **Foreign Keys**: `po_id` -> `PurchaseOrder(po_id)`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `grn_id` | VARCHAR(20) | Yes | Regex `^GRN-2026-[0-9]{6}$` | None | Primary Key | Format `GRN-2026-000001` |
| `po_id` | VARCHAR(20) | Yes | Valid `PurchaseOrder.po_id` | None | No | Must reference an existing PO |
| `received_by` | VARCHAR(20) | Yes | Regex `^EMP-[0-9]{4}$` | None | No | Employee receiving the shipment |
| `receipt_date` | DATE | Yes | YYYY-MM-DD | None | No | Must be `>= PurchaseOrder.order_date` |
| `delivery_note_ref`| VARCHAR(50)| Yes | External string | None | No | Waybill / Bill of Lading reference |
| `status` | VARCHAR(20) | Yes | `RECEIVED`, `PARTIALLY_RECEIVED`, `REJECTED` | None | No | Warehouse inspection status |
| `created_at` | TIMESTAMP | Yes | ISO-8601 | UTC | No | Warehouse ingest time |

---

#### 5. Entity: `GoodsReceiptLine`
- **Description**: Detailed line items received against a specific Purchase Order Line.
- **Primary Key**: `grn_line_id`
- **Foreign Keys**: `grn_id` -> `GoodsReceipt(grn_id)`, `po_line_id` -> `PurchaseOrderLine(po_line_id)`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `grn_line_id` | VARCHAR(30) | Yes | Regex `^GRNL-GRN-2026-[0-9]{6}-[0-9]{2}$` | None | Primary Key | Format `GRNL-GRN-2026-000001-01` |
| `grn_id` | VARCHAR(20) | Yes | Valid `GoodsReceipt.grn_id` | None | No | Parent Goods Receipt |
| `po_line_id` | VARCHAR(30) | Yes | Valid `PurchaseOrderLine.po_line_id` | None | No | Target PO Line being fulfilled |
| `line_number` | INTEGER | Yes | 1 to 8 | None | No | Sequence index |
| `received_quantity`| DECIMAL(10,2)| Yes | `>= 0.00` | UOM units | No | Physical quantity counted at dock |
| `accepted_quantity`| DECIMAL(10,2)| Yes | `>= 0.00` | UOM units | No | Must be `<= received_quantity` |
| `rejected_quantity`| DECIMAL(10,2)| Yes | `>= 0.00` | UOM units | No | Must equal `received_quantity - accepted_quantity` |
| `inspection_notes`| VARCHAR(255)| No | Free text | None | No | Reason if items rejected or damaged |

---

#### 6. Entity: `Invoice`
- **Description**: Commercial claim received from vendor requesting payment for delivered goods/services.
- **Primary Key**: `invoice_id`
- **Foreign Keys**: `vendor_id` -> `Vendor(vendor_id)`, `po_id` -> `PurchaseOrder(po_id)` (nullable for non-PO)

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invoice_id` | VARCHAR(35) | Yes | Regex `^INV-VND-[0-9]{5}-2026-[0-9]{6}$` | None | Primary Key | Format `INV-VND-00001-2026-000001` |
| `invoice_number` | VARCHAR(50) | Yes | Vendor external string | None | Compound | Vendor Invoice Number; flagged if duplicated per vendor |
| `vendor_id` | VARCHAR(16) | Yes | Valid `Vendor.vendor_id` | None | No | Master vendor identifier |
| `po_id` | VARCHAR(20) | No | Valid `PurchaseOrder.po_id` | None | No | Referenced PO; missing PO creates an exception |
| `invoice_date` | DATE | Yes | YYYY-MM-DD | None | No | Stated billing date; must be `>= PO.order_date` |
| `due_date` | DATE | Yes | YYYY-MM-DD | None | No | Must equal `invoice_date + Vendor.payment_terms` |
| `currency` | VARCHAR(3) | Yes | `USD`, `EUR`, `GBP`, `CAD` | ISO-4217 | No | Must match PO currency |
| `subtotal_amount` | DECIMAL(12,2)| Yes | Float `>= 0.00` | Currency | No | Invoiced subtotal; validated against line items |
| `tax_amount` | DECIMAL(12,2)| Yes | Float `>= 0.00` | Currency | No | Invoiced tax; validated against line taxes |
| `total_amount` | DECIMAL(12,2)| Yes | Float `>= 0.00` | Currency | No | Must equal `subtotal_amount + tax_amount` |
| `intake_channel` | VARCHAR(20) | Yes | `EMAIL_OCR`, `PORTAL_UPLOAD`, `EDI`, `PAPER_SCAN` | None | No | Ingestion source route |
| `match_status` | VARCHAR(30) | Yes | `PENDING_MATCH`, `MATCHED`, `PRICE_VARIANCE`, `QUANTITY_MISMATCH`, `MISSING_RECEIPT`, `ARITHMETIC_ERROR`, `TEMPORAL_VIOLATION`, `CLOSED_VENDOR`, `DUPLICATE` | None | No | Derived 3-way match classification |
| `status` | VARCHAR(25) | Yes | `RECEIVED`, `EXTRACTED`, `IN_REVIEW`, `APPROVED`, `REJECTED`, `PAYMENT_READY`, `PAID` | None | No | Workflow execution state |
| `created_at` | TIMESTAMP | Yes | ISO-8601 | UTC | No | Intake ingestion timestamp |

---

#### 7. Entity: `InvoiceLine`
- **Description**: Itemized billing rows extracted from the vendor invoice payload.
- **Primary Key**: `invoice_line_id`
- **Foreign Keys**: `invoice_id` -> `Invoice(invoice_id)`, `po_line_id` -> `PurchaseOrderLine(po_line_id)`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invoice_line_id`| VARCHAR(45) | Yes | Regex `^INVL-INV-VND-[0-9]{5}-2026-[0-9]{6}-[0-9]{2}$` | None | Primary Key | Format `INVL-INV-VND-00001-2026-000001-01` |
| `invoice_id` | VARCHAR(35) | Yes | Valid `Invoice.invoice_id` | None | No | Parent Invoice reference |
| `po_line_id` | VARCHAR(30) | No | Valid `PurchaseOrderLine.po_line_id` | None | No | Matched PO Line reference |
| `line_number` | INTEGER | Yes | 1 to 8 | None | No | Sequential row sequence per invoice |
| `sku` | VARCHAR(50) | Yes | Alphanumeric SKU identifier | None | No | Catalog stock keeping unit code |
| `item_description`| VARCHAR(255)| Yes | Free text | None | No | Invoiced item description |
| `invoiced_quantity`| DECIMAL(10,2)| Yes| `> 0.00` | UOM units | No | Quantity billed by supplier |
| `unit_of_measure` | VARCHAR(10) | Yes | `EA`, `BOX`, `HRS`, `KG`, `LTR` | None | No | Invoiced packaging unit |
| `unit_price` | DECIMAL(10,2)| Yes | `> 0.00` | Currency/UOM| No | Unit price charged by vendor |
| `tax_code` | VARCHAR(10) | Yes | `TAX_0`, `TAX_5`, `TAX_10`, `TAX_18`, `TAX_EXEMPT` | None | No | Tax code applied |
| `tax_rate` | DECIMAL(5,4) | Yes | Float `>= 0.0000` | Percentage | No | Tax percentage applied |
| `line_subtotal` | DECIMAL(12,2)| Yes | Float `> 0.00` | Currency | No | Must equal `ROUND(invoiced_quantity * unit_price, 2)` |
| `line_tax` | DECIMAL(12,2)| Yes | Float `>= 0.00` | Currency | No | Must equal `ROUND(line_subtotal * tax_rate, 2)` |
| `line_total` | DECIMAL(12,2)| Yes | Float `> 0.00` | Currency | No | Must equal `line_subtotal + line_tax` |
| `match_status` | VARCHAR(30) | Yes | `MATCHED`, `PRICE_VARIANCE`, `QUANTITY_MISMATCH`, `UNMATCHED` | None | No | Granular line-level match verdict |

---

#### 8. Entity: `Approval`
- **Description**: Authorization record documenting human or system sign-off before payment disbursement.
- **Primary Key**: `approval_id`
- **Foreign Keys**: `invoice_id` -> `Invoice(invoice_id)`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `approval_id` | VARCHAR(25) | Yes | Regex `^APP-2026-[0-9]{6}$` | None | Primary Key | Format `APP-2026-000001` |
| `invoice_id` | VARCHAR(35) | Yes | Valid `Invoice.invoice_id` | None | No | Must reference an existing invoice |
| `approver_id` | VARCHAR(20) | Yes | Regex `^(EMP-[0-9]{4}\|SYS-AUTO)$` | None | No | Designated actor ID |
| `approver_role` | VARCHAR(30) | Yes | `BUSINESS_REQUESTER`, `PROCESS_OWNER`, `APPROVER`, `OPERATIONS_ANALYST`, `SYSTEM_ADMIN` | None | No | Role of actor granting approval |
| `approval_type` | VARCHAR(30) | Yes | `AUTO_APPROVAL`, `PRICE_VARIANCE_APPROVAL`, `MANUAL_OVERRIDE`, `EXCEPTION_CLEARANCE` | None | No | Policy pathway |
| `decision` | VARCHAR(15) | Yes | `APPROVED`, `REJECTED`, `ESCALATED` | None | No | Conclusive decision |
| `comments` | TEXT | No | Free text audit comments | None | No | Mandatory if rejected or overridden |
| `decision_date` | TIMESTAMP | Yes | ISO-8601 | UTC | No | Must be `>= Invoice.created_at` |

---

#### 9. Entity: `Payment`
- **Description**: Disbursement order generated strictly for fully approved and reconciled invoices.
- **Primary Key**: `payment_id`
- **Foreign Keys**: `invoice_id` -> `Invoice(invoice_id)`, `vendor_id` -> `Vendor(vendor_id)`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `payment_id` | VARCHAR(25) | Yes | Regex `^PAY-2026-[0-9]{6}$` | None | Primary Key | Format `PAY-2026-000001` |
| `invoice_id` | VARCHAR(35) | Yes | Valid `Invoice.invoice_id` | None | Unique | Strict 1:1 relationship with paid invoice |
| `vendor_id` | VARCHAR(16) | Yes | Valid `Vendor.vendor_id` | None | No | Payee identity |
| `amount` | DECIMAL(12,2)| Yes | Float `> 0.00` | Currency | No | Must strictly match `Invoice.total_amount` |
| `currency` | VARCHAR(3) | Yes | `USD`, `EUR`, `GBP`, `CAD` | ISO-4217 | No | Must strictly match `Invoice.currency` |
| `payment_method` | VARCHAR(20) | Yes | `ACH`, `WIRE`, `CHECK`, `VIRTUAL_CARD` | None | No | Banking disbursement channel |
| `payment_reference`| VARCHAR(50)| Yes | Bank transaction string | None | Unique | Unique payment voucher / trace ID |
| `scheduled_date` | DATE | Yes | YYYY-MM-DD | None | No | Execution scheduling target |
| `execution_date` | DATE | No | YYYY-MM-DD | None | No | Populated upon settlement |
| `status` | VARCHAR(20) | Yes | `SCHEDULED`, `PROCESSING`, `EXECUTED`, `FAILED` | None | No | Lifecycle payment state |
| `created_at` | TIMESTAMP | Yes | ISO-8601 | UTC | No | Payment record creation time |

---

#### 10. Supporting Entity: `AuditEvent`
- **Description**: Immutable append-only audit trail recording every state change, actor, and payload difference.
- **Primary Key**: `event_id`

| Field Name | Type | Req | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `event_id` | VARCHAR(30) | Yes | Regex `^EVT-2026-[0-9]{6}$` | None | Primary Key | Format `EVT-2026-000001` |
| `entity_name` | VARCHAR(30) | Yes | `Invoice`, `PurchaseOrder`, `Approval`, `Payment` | None | No | Target entity table |
| `entity_id` | VARCHAR(50) | Yes | Target Entity PK | None | No | Referenced entity primary key |
| `action` | VARCHAR(40) | Yes | `INTAKE_INGESTED`, `MATCH_EVALUATED`, `EXCEPTION_ROUTED`, `APPROVED`, `REJECTED`, `PAYMENT_AUTHORIZED` | None | No | Business event type |
| `actor_role` | VARCHAR(30) | Yes | `SYSTEM`, `BUSINESS_REQUESTER`, `PROCESS_OWNER`, `APPROVER`, `OPERATIONS_ANALYST`, `SYSTEM_ADMIN` | None | No | Role executing the transition |
| `actor_id` | VARCHAR(30) | Yes | `SYS-AUTO` or `EMP-[0-9]{4}` | None | No | Individual actor identity |
| `previous_state` | VARCHAR(30) | No | Any lifecycle status | None | No | Prior state |
| `new_state` | VARCHAR(30) | Yes | Any lifecycle status | None | No | Resulting state |
| `details` | JSON / TEXT | Yes | Valid JSON string | None | No | Granular reason codes, variance amounts, notes |
| `timestamp` | TIMESTAMP | Yes | ISO-8601 | UTC | No | Monotonically non-decreasing event timestamp |
