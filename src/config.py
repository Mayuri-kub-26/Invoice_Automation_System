"""
Configuration and constants for the invoice automation system.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SQL_DIR = DATA_DIR / "sql"
REPORTS_DIR = BASE_DIR / "reports"

# Seed & Reproducibility
DEFAULT_SEED = 20261022

# Baseline Target Volumes
DEFAULT_VOLUMES = {
    "num_vendors": 300,
    "num_pos": 1500,
    "num_po_lines": 2200,
    "num_receipts": 1800,
    "num_invoices": 2000,
}

# Invoice Anomaly / Scenario Distribution (Total = 2,000 invoices)
# ~70% clean matches, 10% price variance, 8% quantity mismatch,
# 5% duplicate invoices, 4% missing receipt, 3% tax/vendor errors.
DISTRIBUTION_COUNTS = {
    "CLEAN_MATCH": 1400,            # 70%
    "PRICE_VARIANCE": 200,          # 10%
    "QUANTITY_MISMATCH": 160,       # 8%
    "DUPLICATE_INVOICE": 100,       # 5% (50 duplicate numbers, 50 resubmissions)
    "MISSING_RECEIPT": 80,          # 4%
    "TAX_VENDOR_ARITH_ERROR": 60,   # 3% (15 tax, 15 line sum, 15 date, 15 closed vendor)
}

# 3-way matching tolerances
MATCH_TOLERANCES = {
    "price_percentage_tolerance": 0.01,  # 1.0% price variance allowed
    "price_absolute_tolerance": 5.00,    # Max $5.00 absolute price variance
    "quantity_tolerance": 0.00,          # 0% quantity tolerance (strict physical receipt)
    "tax_amount_tolerance": 0.05,        # 5 cents rounding tolerance
}

# Actor Role Definitions
ACTOR_ROLES = {
    "BUSINESS_REQUESTER": "Business Requester (Initiates PO, confirms receipt/quantity)",
    "PROCESS_OWNER": "Process Owner (Supervises policy compliance & high-value variances)",
    "APPROVER": "Approver / Finance Manager (Cost center authority for price exceptions)",
    "OPERATIONS_ANALYST": "Operations Analyst (AP Specialist for intake, triage, arithmetic)",
    "SYSTEM_ADMIN": "System Administrator (Master data, closed vendor, duplicate suppression)",
}

# Allowed Enums
ALLOWED_CURRENCIES = ["USD", "EUR", "GBP", "CAD"]
ALLOWED_VENDOR_STATUSES = ["ACTIVE", "INACTIVE", "SUSPENDED", "CLOSED"]
ALLOWED_PAYMENT_TERMS = ["NET15", "NET30", "NET45", "NET60", "DUE_ON_RECEIPT"]
ALLOWED_INTAKE_CHANNELS = ["EMAIL_OCR", "PORTAL_UPLOAD", "EDI", "PAPER_SCAN"]
ALLOWED_PO_STATUSES = ["ISSUED", "PARTIALLY_FULFILLED", "FULFILLED", "CANCELLED", "CLOSED"]
ALLOWED_GRN_STATUSES = ["RECEIVED", "PARTIALLY_RECEIVED", "REJECTED"]
ALLOWED_INVOICE_STATUSES = ["RECEIVED", "EXTRACTED", "IN_REVIEW", "APPROVED", "REJECTED", "PAYMENT_READY", "PAID"]
ALLOWED_MATCH_STATUSES = [
    "PENDING_MATCH",
    "MATCHED",
    "EXCEPTION_PRICE_VARIANCE",
    "EXCEPTION_QUANTITY_MISMATCH",
    "EXCEPTION_MISSING_RECEIPT",
    "EXCEPTION_ARITHMETIC_ERROR",
    "EXCEPTION_TEMPORAL_VIOLATION",
    "EXCEPTION_CLOSED_VENDOR",
    "EXCEPTION_TAX_MISMATCH",
    "EXCEPTION_DUPLICATE",
]
ALLOWED_APPROVAL_DECISIONS = ["APPROVED", "REJECTED", "ESCALATED"]
ALLOWED_PAYMENT_METHODS = ["ACH", "WIRE", "CHECK", "VIRTUAL_CARD"]
ALLOWED_PAYMENT_STATUSES = ["SCHEDULED", "PROCESSING", "EXECUTED", "FAILED"]
