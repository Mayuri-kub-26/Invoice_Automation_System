# Data Validation Report

**Status:** PASSED

- Checks run: 24
- Passed: 24
- Failed: 0

Generated from the default dataset (seed `20261022`).

### Primary key uniqueness

| Check | Status | Details |
| :--- | :---: | :--- |
| `vendors_pk_unique` | PASS | 300 rows, 300 unique keys |
| `purchase_orders_pk_unique` | PASS | 1500 rows, 1500 unique keys |
| `po_lines_pk_unique` | PASS | 2200 rows, 2200 unique keys |
| `goods_receipts_pk_unique` | PASS | 1800 rows, 1800 unique keys |
| `goods_receipt_lines_pk_unique` | PASS | 2800 rows, 2800 unique keys |
| `invoices_pk_unique` | PASS | 2000 rows, 2000 unique keys |
| `invoice_lines_pk_unique` | PASS | 2785 rows, 2785 unique keys |
| `approvals_pk_unique` | PASS | 1400 rows, 1400 unique keys |
| `payments_pk_unique` | PASS | 1400 rows, 1400 unique keys |
| `audit_events_pk_unique` | PASS | 7240 rows, 7240 unique keys |

### Foreign key integrity

| Check | Status | Details |
| :--- | :---: | :--- |
| `purchase_orders_to_vendors_fk` | PASS | Orphan POs: 0 |
| `po_lines_to_pos_fk` | PASS | Orphan PO lines: 0 |
| `goods_receipts_to_pos_fk` | PASS | Orphan goods receipts: 0 |
| `goods_receipt_lines_fks` | PASS | Orphan goods receipt lines: 0 |
| `invoices_to_vendors_pos_fk` | PASS | Orphan invoices: 0 |
| `payments_to_invoices_vendors_fk` | PASS | Orphan payments: 0 |

### Enum constraints

| Check | Status | Details |
| :--- | :---: | :--- |
| `vendor_status_valid` | PASS | Violations: 0 |
| `vendor_currency_valid` | PASS | Violations: 0 |
| `po_status_valid` | PASS | Violations: 0 |
| `invoice_status_valid` | PASS | Violations: 0 |
| `invoice_channel_valid` | PASS | Violations: 0 |

### Date ordering

| Check | Status | Details |
| :--- | :---: | :--- |
| `grn_date_ge_po_date` | PASS | Goods receipts dated before their PO: 0 |

### Arithmetic reconciliation

| Check | Status | Details |
| :--- | :---: | :--- |
| `po_line_sums_match_po_header` | PASS | Mismatches: 0 |

### Payment safety

| Check | Status | Details |
| :--- | :---: | :--- |
| `zero_payments_for_unmatched_invoices` | PASS | Payments for unmatched invoices: 0 |
