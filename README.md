# Invoice Automation System

A small Python project for accounts payable automation. It generates a synthetic ERP-style
dataset (vendors, purchase orders, goods receipts and invoices), validates and matches invoices
against the purchase orders and goods receipts, routes discrepancies to the right people, and
producing payment-ready records with an audit trail.

The generator is seeded, so the same seed always produces the same dataset. That makes the
results reproducible and easy to test.

## What it does

- **Invoice intake** – checks vendor status, duplicate invoice numbers, duplicate payloads,
  arithmetic, tax rates and invoice dates before anything else happens.
- **3-way matching** – compares each invoice line with the matching purchase order line and
  goods receipt line. Price tolerance is 1% with a $5 cap; quantity tolerance is zero.
- **Exception routing** – assigns each discrepancy to a role (business requester, process owner,
  approver, operations analyst or system administrator) with a priority and a next action.
- **Payment readiness** – only fully matched invoices get an auto-approval and a scheduled
  payment. Everything else is held.
- **Audit trail** – every state change is written as an append-only event with the actor,
  timestamp and reason.

## Pipeline

```
Raw invoice (from a generated ERP extract)
        |
        v
+-----------------------------+
| Intake validation           |  vendor status, duplicates, arithmetic,
|                             |  tax rates, date ordering
+-----------------------------+
        |
   pass | fail -> exception routed to operations analyst / system admin
        v
+-----------------------------+
| 3-way match                 |  invoice line vs PO line vs goods receipt line
| price +/-1% ($5 max), qty 0%|
+-----------------------------+
        |
   clean| variance -> exception routed to approver, process owner
        v               or business requester
+-----------------------------+
| Payment readiness           |  auto-approval + scheduled ACH payment
+-----------------------------+
        |
        v
+-----------------------------+
| Audit log                   |  append-only event history
+-----------------------------+
```

## Roles

| Role | Responsibility | Exceptions handled |
| :--- | :--- | :--- |
| Business Requester | Raised the purchase order and confirms what was delivered. | Quantity mismatch, partial delivery |
| Process Owner | Owns budget policy and high-value overrides (over $500). | High-value price variance, policy escalations |
| Approver | Cost-centre manager for standard price variances. | Standard price variance |
| Operations Analyst | AP specialist who triages documents and follows up on receipts. | Missing receipt, arithmetic error, tax mismatch, date violation |
| System Administrator | Maintains vendor master data and duplicate suppression. | Closed vendor, duplicate invoice |

## Dataset

The data is generated from seed `20261022` in a fixed order: vendors, purchase orders, PO lines,
goods receipts, invoices and invoice lines. The default run produces:

| Table | Rows |
| :--- | ---: |
| vendors | 300 |
| purchase_orders | 1,500 |
| po_lines | 2,200 |
| goods_receipts | 1,800 |
| goods_receipt_lines | 2,800 |
| invoices | 2,000 |
| invoice_lines | 2,785 |

The 2,000 invoices are split across a set of scenarios so the matcher has something to work with:

| Scenario | Share | Invoices | What happens |
| :--- | ---: | ---: | :--- |
| Clean 3-way match | 70% | 1,400 | Full quantity received, contractual price honoured. Auto-approved and paid. |
| Price variance | 10% | 200 | Unit price inflated by 15% + $6.00, outside tolerance. Held. |
| Quantity mismatch | 8% | 160 | 80 partial deliveries and 80 invoices above PO quantity. Held. |
| Duplicate invoice | 5% | 100 | 50 duplicate invoice numbers and 50 identical resubmissions. Voided. |
| Missing receipt | 4% | 80 | Invoice arrives before the goods receipt exists. Held. |
| Tax / vendor / arithmetic / date | 3% | 60 | 15 closed vendors, 15 tax mismatches, 15 line-sum errors, 15 pre-dated invoices. |

Ground truth labels live in `data/ground_truth/` and are never used as input to the matcher.

## Results

The validation suite runs 24 checks covering primary keys, foreign keys, enum values, date
ordering, PO arithmetic and payment safety. With the default dataset all 24 pass.

The evaluator compares engine decisions with the ground truth:

```
Invoices evaluated : 2,000
Anomalies found    : 600
Clean invoices     : 1,400
False positives    : 0
False negatives    : 0

Accuracy / precision / recall / F1 : 100%
Payment leakage (anomalies paid)   : 0
```

Two independent generation runs with the same seed produce identical row counts and identical
SHA-256 hashes for all eight tables.

## Project structure

```
Invoice_Automation_System/
├── data/
│   ├── raw/                 # generated master and transaction tables (CSV + JSON)
│   ├── ground_truth/        # labelled outcomes, kept separate from the input data
│   ├── processed/           # pipeline outputs, exceptions, approvals, payments, audit log
│   └── sql/                 # schema DDL and a seed script for the generated data
├── reports/                 # validation, evaluation and reproducibility reports
├── src/
│   ├── __init__.py
│   ├── config.py            # paths, seed, tolerances, volumes
│   ├── models.py            # dataclasses for the entities
│   ├── generator.py         # synthetic data generator
│   ├── extractor.py         # intake and extraction checks
│   ├── matcher.py           # 3-way matching
│   ├── router.py            # exception routing
│   ├── payment_engine.py    # approvals and payment readiness
│   ├── pipeline.py          # orchestrates the full flow
│   ├── validator.py         # data integrity checks
│   ├── evaluator.py         # accuracy and safety metrics
│   └── reproducibility_check.py
├── app.py                   # Streamlit dashboard
├── main.py                  # CLI entry point
├── DATA_DICTIONARY.md       # schema reference
├── VALIDATION_REPORT.md     # validation summary
├── MANIFEST.json            # run manifest
├── requirements.txt
└── README.md
```

## Getting started

```bash
pip install -r requirements.txt
```

Run the whole suite (generate, process, validate, evaluate, check reproducibility):

```bash
python main.py all --seed 20261022 --scale 1.0
```

Individual steps:

```bash
python main.py generate --seed 20261022 --scale 1.0
python main.py pipeline
python main.py validate
python main.py evaluate
python main.py reproducibility --seed 20261022
```

Start the dashboard:

```bash
streamlit run app.py
```

## Notes on the data

All data in this repository is synthetic and generated from a fixed seed. There are no real
people, vendors, bank details or confidential records in it. No external data was scraped or
copied.

## License

MIT
