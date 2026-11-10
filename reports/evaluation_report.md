# Evaluation Report

The matching engine was run over the default dataset (seed `20261022`) and compared with the
ground truth labels. There are 2,000 invoices: 1,400 clean and 600 with an injected anomaly.

### Summary

- Invoices evaluated: 2,000
- Accuracy: 100.00%
- Precision: 100.00%
- Recall: 100.00%
- F1: 100.00%
- Payment safety: PASSED – no anomalous invoice reached payment

### Confusion matrix

| | Predicted exception | Predicted matched |
| :--- | :---: | :---: |
| Actual anomaly | TP: 600 | FN: 0 |
| Actual clean | FP: 0 | TN: 1,400 |

### Detection by category

| Category | Cases | Detected | Recall | Missed |
| :--- | ---: | ---: | ---: | ---: |
| `NONE` | 1400 | 0 | 0.0% | 0 |
| `PRICE_VARIANCE` | 200 | 200 | 100.0% | 0 |
| `PARTIAL_DELIVERY` | 80 | 80 | 100.0% | 0 |
| `INVOICE_EXCEEDS_PO_QUANTITY` | 80 | 80 | 100.0% | 0 |
| `MISSING_RECEIPT` | 80 | 80 | 100.0% | 0 |
| `DUPLICATE_INVOICE_NUMBER` | 50 | 50 | 100.0% | 0 |
| `SAME_INVOICE_SUBMITTED_TWICE` | 50 | 50 | 100.0% | 0 |
| `CLOSED_VENDOR` | 15 | 15 | 100.0% | 0 |
| `TAX_MISMATCH` | 15 | 15 | 100.0% | 0 |
| `INVOICE_TOTAL_DIFFERS_FROM_LINE_SUM` | 15 | 15 | 100.0% | 0 |
| `INVOICE_DATE_BEFORE_PO_DATE` | 15 | 15 | 100.0% | 0 |
