# Reproducibility Report

**Status:** PASSED – 100% bitwise equivalence

- Generator seed: `20261022`
- Method: two clean runs from scratch, comparing row counts and SHA-256 hashes

| File | Rows (A / B) | SHA-256 (Run A) | Status |
| :--- | :---: | :---: | :---: |
| `vendors.csv` | 300 / 300 | `952c5a24112a7a9b...` | PASS |
| `purchase_orders.csv` | 1,500 / 1,500 | `81f693fe6237e7f1...` | PASS |
| `po_lines.csv` | 2,200 / 2,200 | `486a6744635a2a5a...` | PASS |
| `goods_receipts.csv` | 1,800 / 1,800 | `b3055f1d33a7d05e...` | PASS |
| `goods_receipt_lines.csv` | 2,800 / 2,800 | `0151c20612a0c546...` | PASS |
| `invoices.csv` | 2,000 / 2,000 | `043e468bc203a275...` | PASS |
| `invoice_lines.csv` | 2,785 / 2,785 | `8dd91958fe162da7...` | PASS |
| `ground_truth.csv` | 2,000 / 2,000 | `f54bff451fe93f31...` | PASS |
