"""
Synthetic data generator for the invoice automation system.
Implements Granular Steps 1 through 7 with deterministic IDs, realistic distributions,
strictly derived values, and separate ground truth labels.
"""

import os
import json
import random
import csv
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from src.config import (
    DEFAULT_SEED,
    DEFAULT_VOLUMES,
    RAW_DATA_DIR,
    GROUND_TRUTH_DIR,
    SQL_DIR,
    ALLOWED_CURRENCIES,
    ALLOWED_PAYMENT_TERMS,
    ALLOWED_INTAKE_CHANNELS,
)
from src.models import (
    Vendor,
    PurchaseOrder,
    PurchaseOrderLine,
    GoodsReceipt,
    GoodsReceiptLine,
    Invoice,
    InvoiceLine,
    GroundTruthRecord,
)

VENDOR_PREFIXES = [
    "Apex", "Summit", "Nexus", "Vanguard", "Pinnacle", "Titan", "Quantum", "Cascade",
    "Horizon", "Atlas", "Omega", "Meridian", "Cobalt", "Crestview", "Northstar",
    "Silverline", "Trillium", "Dynamic", "Starlight", "Beacon", "Solstice", "Zenith",
    "Ironclad", "Aegis", "Velocity", "Synergy", "Pacific", "Atlantic", "Keystone", "Vertex"
]

VENDOR_SUFFIXES = [
    "Logistics LLC", "Technologies Inc", "Industrial Supplies Corp", "Global Solutions Ltd",
    "Components GmbH", "Systems Co", "Manufacturing Corp", "Enterprises LLC",
    "Distribution SA", "Chemicals Ltd", "Hardware & Tools Inc", "Electronics Ltd",
    "Packaging Group", "Materials Corp", "Engineering Partners", "Supply Chain Services"
]

SKU_CATALOG = [
    ("SKU-IND-1001", "Heavy Duty Industrial Flange 4-inch", 125.00, "EA", "TAX_10", 0.1000),
    ("SKU-ELC-2042", "Copper Core Busbar Assembly 100A", 84.50, "EA", "TAX_18", 0.1800),
    ("SKU-PNE-3309", "Pneumatic Solenoid Valve 24V DC", 45.00, "EA", "TAX_18", 0.1800),
    ("SKU-HYD-4011", "High-Pressure Hydraulic Hose 2m", 68.20, "EA", "TAX_18", 0.1800),
    ("SKU-SFT-5110", "ANSI Certified Safety Helmets (Pack of 10)", 150.00, "BOX", "TAX_5", 0.0500),
    ("SKU-PKG-6003", "Corrugated Shipping Cartons (Bundle of 50)", 95.00, "BOX", "TAX_5", 0.0500),
    ("SKU-LUB-7020", "Synthetic Industrial Lubricant ISO VG 46 (20L)", 210.00, "LTR", "TAX_18", 0.1800),
    ("SKU-RAW-8055", "Cold-Rolled Steel Plate 10mm x 1m x 2m", 340.00, "EA", "TAX_10", 0.1000),
    ("SKU-IT-9102", "Cat6A Shielded Patch Cable 10m (Pack of 5)", 55.00, "BOX", "TAX_18", 0.1800),
    ("SKU-FST-1200", "Grade 8 Zinc Hex Cap Screws M12 (Pack of 100)", 32.50, "BOX", "TAX_10", 0.1000),
    ("SKU-SVC-1300", "Certified Calibration & Diagnostic Service", 450.00, "HRS", "TAX_18", 0.1800),
    ("SKU-CLN-1400", "Biodegradable Degreaser Concentrate (25L)", 115.00, "LTR", "TAX_10", 0.1000),
    ("SKU-TMP-1500", "Digital Thermocouple Sensor Probe Type-K", 78.00, "EA", "TAX_10", 0.1000),
    ("SKU-MTR-1600", "Three-Phase Induction Motor 1.5kW 400V", 620.00, "EA", "TAX_18", 0.1800),
    ("SKU-EXP-1700", "Customs Clearance & Documentation Fee", 180.00, "EA", "TAX_0", 0.0000),
]

DEPARTMENTS = ["Engineering", "Operations", "IT & Infrastructure", "Supply Chain", "Facilities", "Quality Assurance"]

class SyntheticDataGenerator:
    """
    Generator class that encapsulates the end-to-end synthetic data generation pipeline
    with guaranteed reproducibility using a seeded pseudorandom number generator.
    """

    def __init__(self, seed: int = DEFAULT_SEED, scale: float = 1.0):
        self.seed = seed
        self.scale = max(0.01, min(scale, 10.0))
        self.rng = random.Random(seed)

        self.num_vendors = max(10, int(DEFAULT_VOLUMES["num_vendors"] * self.scale))
        self.num_pos = max(20, int(DEFAULT_VOLUMES["num_pos"] * self.scale))
        self.num_po_lines = max(30, int(DEFAULT_VOLUMES["num_po_lines"] * self.scale))
        self.num_receipts = max(20, int(DEFAULT_VOLUMES["num_receipts"] * self.scale))
        self.num_invoices = max(20, int(DEFAULT_VOLUMES["num_invoices"] * self.scale))

        self.base_date = date(2026, 1, 10)

        self.vendors: List[Vendor] = []
        self.purchase_orders: List[PurchaseOrder] = []
        self.po_lines: List[PurchaseOrderLine] = []
        self.goods_receipts: List[GoodsReceipt] = []
        self.goods_receipt_lines: List[GoodsReceiptLine] = []
        self.invoices: List[Invoice] = []
        self.invoice_lines: List[InvoiceLine] = []
        self.ground_truth_records: List[GroundTruthRecord] = []

    def _format_vendor_id(self, seq: int) -> str:
        return f"VND-{seq:05d}"

    def _format_po_id(self, seq: int) -> str:
        return f"PO-2026-{seq:06d}"

    def _format_grn_id(self, seq: int) -> str:
        return f"GRN-2026-{seq:06d}"

    def _format_invoice_id(self, vendor_id: str, seq: int) -> str:
        return f"INV-{vendor_id}-2026-{seq:06d}"

    def generate_vendors(self) -> List[Vendor]:
        """Step 2a: Generate Master Vendors first (Vendors 1 to 285 ACTIVE; 286 to 300 CLOSED)."""
        self.vendors = []
        num_closed = max(2, int(self.num_vendors * 0.05))
        num_active = self.num_vendors - num_closed

        for i in range(1, self.num_vendors + 1):
            vendor_id = self._format_vendor_id(i)
            pfx = self.rng.choice(VENDOR_PREFIXES)
            sfx = self.rng.choice(VENDOR_SUFFIXES)
            vendor_name = f"{pfx} {sfx} #{i}"
            tax_id = f"{self.rng.randint(10, 99)}-{self.rng.randint(1000000, 9999999)}"

            if i <= num_active:
                status = "ACTIVE"
            else:
                status = "CLOSED"

            payment_terms = self.rng.choice(ALLOWED_PAYMENT_TERMS)
            currency = self.rng.choice(ALLOWED_CURRENCIES)
            clean_name = pfx.lower().replace(" ", "")
            contact_email = f"ar@{clean_name}-vendor{i}.com"
            address_country = self.rng.choice(["US", "DE", "GB", "CA", "IN"])
            created_at = (self.base_date - timedelta(days=self.rng.randint(60, 365))).isoformat() + "T08:00:00Z"
            updated_at = created_at

            vendor = Vendor(
                vendor_id=vendor_id,
                vendor_name=vendor_name,
                tax_id=tax_id,
                status=status,
                payment_terms=payment_terms,
                currency=currency,
                contact_email=contact_email,
                address_country=address_country,
                created_at=created_at,
                updated_at=updated_at,
            )
            self.vendors.append(vendor)
        return self.vendors

    def generate_purchase_orders_and_lines(self) -> Tuple[List[PurchaseOrder], List[PurchaseOrderLine]]:
        """Step 2b: Generate POs and PO Lines referencing vendors."""
        self.purchase_orders = []
        self.po_lines = []

        active_vendors = [v for v in self.vendors if v.status == "ACTIVE"]
        closed_vendors = [v for v in self.vendors if v.status == "CLOSED"]

        lines_per_po = [1] * self.num_pos
        remaining_lines = self.num_po_lines - self.num_pos
        idx = 0
        while remaining_lines > 0:
            po_idx = idx % self.num_pos
            if lines_per_po[po_idx] < 8:
                lines_per_po[po_idx] += 1
                remaining_lines -= 1
            idx += 1

        for i in range(1, self.num_pos + 1):
            po_id = self._format_po_id(i)

            # Assign POs 1486 to 1500 to closed vendors for closed vendor edge case
            if i > (self.num_pos - 15) and closed_vendors:
                vendor = closed_vendors[(i - 1) % len(closed_vendors)]
            else:
                vendor = active_vendors[(i - 1) % len(active_vendors)]

            buyer_id = f"EMP-{self.rng.randint(1001, 1080):04d}"
            dept = self.rng.choice(DEPARTMENTS)
            order_date = self.base_date + timedelta(days=self.rng.randint(0, 120))
            expected_delivery_date = order_date + timedelta(days=self.rng.randint(5, 30))
            created_at = order_date.isoformat() + "T09:30:00Z"

            num_lines = lines_per_po[i - 1]
            subtotal = 0.0
            tax_total = 0.0

            used_skus = set()
            for line_no in range(1, num_lines + 1):
                po_line_id = f"POL-{po_id}-{line_no:02d}"
                sku_item = self.rng.choice(SKU_CATALOG)
                while sku_item[0] in used_skus:
                    sku_item = self.rng.choice(SKU_CATALOG)
                used_skus.add(sku_item[0])

                sku, desc, unit_price, uom, tax_code, tax_rate = sku_item
                ordered_qty = float(self.rng.choice([10, 20, 25, 50, 100, 150, 200]))
                line_subtotal = round(ordered_qty * unit_price, 2)
                line_tax = round(line_subtotal * tax_rate, 2)
                line_total = round(line_subtotal + line_tax, 2)

                subtotal += line_subtotal
                tax_total += line_tax

                po_line = PurchaseOrderLine(
                    po_line_id=po_line_id,
                    po_id=po_id,
                    line_number=line_no,
                    sku=sku,
                    item_description=desc,
                    ordered_quantity=ordered_qty,
                    unit_of_measure=uom,
                    unit_price=unit_price,
                    tax_code=tax_code,
                    tax_rate=tax_rate,
                    line_subtotal=line_subtotal,
                    line_tax=line_tax,
                    line_total=line_total,
                )
                self.po_lines.append(po_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            po_total = round(subtotal + tax_total, 2)

            po = PurchaseOrder(
                po_id=po_id,
                vendor_id=vendor.vendor_id,
                buyer_id=buyer_id,
                department=dept,
                status="ISSUED",
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=po_total,
                order_date=order_date.isoformat(),
                expected_delivery_date=expected_delivery_date.isoformat(),
                created_at=created_at,
            )
            self.purchase_orders.append(po)

        return self.purchase_orders, self.po_lines

    def generate_goods_receipts(self) -> Tuple[List[GoodsReceipt], List[GoodsReceiptLine]]:
        """
        Step 2c: Generate Receipts referencing POs and PO Lines.
        - POs 361 to 440 (80 POs) -> Missing Receipts (0 GRNs)
        - POs 201 to 280 (80 POs) -> Partial Delivery (Strictly 1 GRN with 50% qty)
        - Remaining POs -> 1 (or 2) GRNs with 100% full receipt
        Calibrated to exactly 1,800 receipts.
        """
        self.goods_receipts = []
        self.goods_receipt_lines = []

        po_lines_by_po: Dict[str, List[PurchaseOrderLine]] = {}
        for pol in self.po_lines:
            po_lines_by_po.setdefault(pol.po_id, []).append(pol)

        grn_seq = 1

        # 1. Partial Delivery POs: Exactly 1 GRN with 50% accepted qty
        partial_pos = [self.purchase_orders[i - 1] for i in range(201, 281)]
        for po in partial_pos:
            grn_id = self._format_grn_id(grn_seq)
            grn_seq += 1
            order_date = date.fromisoformat(po.order_date)
            receipt_date = order_date + timedelta(days=self.rng.randint(2, 10))

            grn = GoodsReceipt(
                grn_id=grn_id,
                po_id=po.po_id,
                received_by=f"EMP-{self.rng.randint(2001, 2040):04d}",
                receipt_date=receipt_date.isoformat(),
                delivery_note_ref=f"DN-PART-{self.rng.randint(100000, 999999)}",
                status="PARTIALLY_RECEIVED",
                created_at=receipt_date.isoformat() + "T14:15:00Z",
            )
            self.goods_receipts.append(grn)

            for line_idx, pol in enumerate(po_lines_by_po.get(po.po_id, []), 1):
                part_qty = round(pol.ordered_quantity * 0.50, 2)
                grnl = GoodsReceiptLine(
                    grn_line_id=f"GRNL-{grn_id}-{line_idx:02d}",
                    grn_id=grn_id,
                    po_line_id=pol.po_line_id,
                    line_number=line_idx,
                    received_quantity=part_qty,
                    accepted_quantity=part_qty,
                    rejected_quantity=0.0,
                    inspection_notes="Partial delivery received dockside",
                )
                self.goods_receipt_lines.append(grnl)

        # 2. Fully Received Eligible POs (all POs except 201-280 and 361-440)
        fully_received_pos = [
            po for idx, po in enumerate(self.purchase_orders, 1)
            if not (201 <= idx <= 280) and not (361 <= idx <= 440)
        ]

        # Allocate receipts across fully_received_pos so total receipts == self.num_receipts
        # Current receipts: len(partial_pos) = 80
        remaining_receipts = self.num_receipts - len(partial_pos)  # 1800 - 80 = 1720
        receipts_per_po = {po.po_id: 1 for po in fully_received_pos}
        extra_receipts = remaining_receipts - len(fully_received_pos)  # 1720 - 1340 = 380

        for i in range(extra_receipts):
            po = fully_received_pos[i % len(fully_received_pos)]
            receipts_per_po[po.po_id] += 1

        for po in fully_received_pos:
            num_grns = receipts_per_po[po.po_id]
            lines = po_lines_by_po.get(po.po_id, [])
            order_date = date.fromisoformat(po.order_date)

            for g_num in range(1, num_grns + 1):
                grn_id = self._format_grn_id(grn_seq)
                grn_seq += 1
                receipt_date = order_date + timedelta(days=self.rng.randint(2, 20) + g_num)

                grn = GoodsReceipt(
                    grn_id=grn_id,
                    po_id=po.po_id,
                    received_by=f"EMP-{self.rng.randint(2001, 2040):04d}",
                    receipt_date=receipt_date.isoformat(),
                    delivery_note_ref=f"DN-FULL-{self.rng.randint(100000, 999999)}",
                    status="RECEIVED",
                    created_at=receipt_date.isoformat() + "T14:15:00Z",
                )
                self.goods_receipts.append(grn)

                for line_idx, pol in enumerate(lines, 1):
                    # Distribute line quantity evenly across receipts
                    # Last receipt takes rounding delta
                    if g_num < num_grns:
                        alloc_qty = round(pol.ordered_quantity / num_grns, 2)
                    else:
                        alloc_qty = round(pol.ordered_quantity - round(pol.ordered_quantity / num_grns, 2) * (num_grns - 1), 2)

                    grnl = GoodsReceiptLine(
                        grn_line_id=f"GRNL-{grn_id}-{line_idx:02d}",
                        grn_id=grn_id,
                        po_line_id=pol.po_line_id,
                        line_number=line_idx,
                        received_quantity=alloc_qty,
                        accepted_quantity=alloc_qty,
                        rejected_quantity=0.0,
                        inspection_notes="Passed warehouse QC inspection",
                    )
                    self.goods_receipt_lines.append(grnl)

        return self.goods_receipts, self.goods_receipt_lines

    def generate_invoices_and_scenarios(self) -> Tuple[List[Invoice], List[InvoiceLine], List[GroundTruthRecord]]:
        """
        Step 4 & Step 5: Generate baseline valid invoices and inject labelled edge cases.
        1,400 clean invoices + 600 anomalies = 2,000 invoices.
        """
        self.invoices = []
        self.invoice_lines = []
        self.ground_truth_records = []

        po_map = {po.po_id: po for po in self.purchase_orders}
        vendor_map = {v.vendor_id: v for v in self.vendors}
        po_lines_by_po: Dict[str, List[PurchaseOrderLine]] = {}
        for pol in self.po_lines:
            po_lines_by_po.setdefault(pol.po_id, []).append(pol)

        clean_pos = [po for idx, po in enumerate(self.purchase_orders, 1) if 601 <= idx <= 1485]

        inv_seq = 1
        clean_invoices_cache: List[Tuple[Invoice, List[InvoiceLine]]] = []

        # 1. Generate 1,400 Clean Invoices First
        for i in range(1, 1401):
            po = clean_pos[(i - 1) % len(clean_pos)]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            invoice_date = po_order_date + timedelta(days=self.rng.randint(3, 25))
            payment_terms_days = {
                "NET15": 15, "NET30": 30, "NET45": 45, "NET60": 60, "DUE_ON_RECEIPT": 0
            }.get(vendor.payment_terms, 30)
            due_date = invoice_date + timedelta(days=payment_terms_days)

            intake_channel = self.rng.choice(ALLOWED_INTAKE_CHANNELS)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines: List[InvoiceLine] = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                l_qty = pol.ordered_quantity
                l_price = pol.unit_price
                l_sub = pol.line_subtotal
                l_tax = pol.line_tax
                l_tot = pol.line_total

                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=l_qty,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=l_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="MATCHED",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=intake_channel,
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )

            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)
            clean_invoices_cache.append((inv, cur_lines))

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=False,
                anomaly_type="NONE",
                expected_match_status="MATCHED",
                expected_routing_role="SYSTEM",
                expected_payment_ready=True,
                root_cause_field="NONE",
                notes="Standard clean 3-way match within tolerance",
            )
            self.ground_truth_records.append(gt)

        # 2. Generate 600 Anomaly Invoices
        # 200 Price Variance (POs 1 to 200)
        for i in range(1, 201):
            po = self.purchase_orders[i - 1]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            invoice_date = po_order_date + timedelta(days=self.rng.randint(3, 20))
            due_date = invoice_date + timedelta(days=30)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                inflated_price = round(pol.unit_price * 1.15 + 6.00, 2)
                l_sub = round(pol.ordered_quantity * inflated_price, 2)
                l_tax = round(l_sub * pol.tax_rate, 2)
                l_tot = round(l_sub + l_tax, 2)

                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=pol.ordered_quantity,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=inflated_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_PRICE_VARIANCE",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="PRICE_VARIANCE",
                expected_match_status="EXCEPTION_PRICE_VARIANCE",
                expected_routing_role="APPROVER",
                expected_payment_ready=False,
                root_cause_field="unit_price",
                notes="Line unit price exceeds PO contractual price by > 1% / $5 tolerance",
            )
            self.ground_truth_records.append(gt)

        # 80 Partial Delivery (POs 201 to 280)
        for i in range(201, 281):
            po = self.purchase_orders[i - 1]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            invoice_date = po_order_date + timedelta(days=self.rng.randint(3, 20))
            due_date = invoice_date + timedelta(days=30)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                l_sub = pol.line_subtotal
                l_tax = pol.line_tax
                l_tot = pol.line_total
                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=pol.ordered_quantity,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=pol.unit_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_QUANTITY_MISMATCH",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="PARTIAL_DELIVERY",
                expected_match_status="EXCEPTION_QUANTITY_MISMATCH",
                expected_routing_role="BUSINESS_REQUESTER",
                expected_payment_ready=False,
                root_cause_field="invoiced_quantity",
                notes="Invoice billed full PO quantity but physical Goods Receipt was only partial",
            )
            self.ground_truth_records.append(gt)

        # 80 Invoice Exceeds PO Quantity (POs 281 to 360)
        for i in range(281, 361):
            po = self.purchase_orders[i - 1]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            invoice_date = po_order_date + timedelta(days=self.rng.randint(3, 20))
            due_date = invoice_date + timedelta(days=30)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                over_qty = round(pol.ordered_quantity * 1.30, 2)
                l_sub = round(over_qty * pol.unit_price, 2)
                l_tax = round(l_sub * pol.tax_rate, 2)
                l_tot = round(l_sub + l_tax, 2)
                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=over_qty,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=pol.unit_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_QUANTITY_MISMATCH",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="INVOICE_EXCEEDS_PO_QUANTITY",
                expected_match_status="EXCEPTION_QUANTITY_MISMATCH",
                expected_routing_role="BUSINESS_REQUESTER",
                expected_payment_ready=False,
                root_cause_field="invoiced_quantity",
                notes="Invoiced quantity exceeds authorized PO quantity by 30%",
            )
            self.ground_truth_records.append(gt)

        # 80 Missing Receipt (POs 361 to 440)
        for i in range(361, 441):
            po = self.purchase_orders[i - 1]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            invoice_date = po_order_date + timedelta(days=self.rng.randint(3, 20))
            due_date = invoice_date + timedelta(days=30)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                l_sub = pol.line_subtotal
                l_tax = pol.line_tax
                l_tot = pol.line_total
                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=pol.ordered_quantity,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=pol.unit_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_MISSING_RECEIPT",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="MISSING_RECEIPT",
                expected_match_status="EXCEPTION_MISSING_RECEIPT",
                expected_routing_role="OPERATIONS_ANALYST",
                expected_payment_ready=False,
                root_cause_field="grn_id",
                notes="Invoice received before Goods Receipt Note exists in ERP",
            )
            self.ground_truth_records.append(gt)

        # 50 Duplicate Invoice Numbers (reusing clean invoice's vendor + invoice number on another PO)
        for i in range(1, 51):
            ref_inv, _ = clean_invoices_cache[i - 1]
            po = self.purchase_orders[440 + i]
            vendor = vendor_map[ref_inv.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = ref_inv.invoice_number  # Duplicate invoice number!
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                l_sub = pol.line_subtotal
                l_tax = pol.line_tax
                l_tot = pol.line_total
                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=pol.ordered_quantity,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=pol.unit_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_DUPLICATE",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=ref_inv.invoice_date,
                due_date=ref_inv.due_date,
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=ref_inv.created_at,
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="DUPLICATE_INVOICE_NUMBER",
                expected_match_status="EXCEPTION_DUPLICATE",
                expected_routing_role="SYSTEM_ADMIN",
                expected_payment_ready=False,
                root_cause_field="invoice_number",
                notes="Duplicate external invoice number resubmitted for same vendor",
            )
            self.ground_truth_records.append(gt)

        # 50 Same Invoice Submitted Twice (Exact identical payload re-submission)
        for i in range(51, 101):
            ref_inv, ref_lines = clean_invoices_cache[i - 1]
            vendor = vendor_map[ref_inv.vendor_id]
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = ref_inv.invoice_number  # Exact duplicate!
            inv_seq += 1

            cur_lines = []
            for idx, l in enumerate(ref_lines, 1):
                inv_line = InvoiceLine(
                    invoice_line_id=f"INVL-{invoice_id}-{idx:02d}",
                    invoice_id=invoice_id,
                    po_line_id=l.po_line_id,
                    line_number=idx,
                    sku=l.sku,
                    item_description=l.item_description,
                    invoiced_quantity=l.invoiced_quantity,
                    unit_of_measure=l.unit_of_measure,
                    unit_price=l.unit_price,
                    tax_code=l.tax_code,
                    tax_rate=l.tax_rate,
                    line_subtotal=l.line_subtotal,
                    line_tax=l.line_tax,
                    line_total=l.line_total,
                    match_status="EXCEPTION_DUPLICATE",
                )
                cur_lines.append(inv_line)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=ref_inv.po_id,
                invoice_date=ref_inv.invoice_date,
                due_date=ref_inv.due_date,
                currency=ref_inv.currency,
                subtotal_amount=ref_inv.subtotal_amount,
                tax_amount=ref_inv.tax_amount,
                total_amount=ref_inv.total_amount,
                intake_channel=ref_inv.intake_channel,
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=ref_inv.created_at,
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=ref_inv.po_id,
                is_anomaly=True,
                anomaly_type="SAME_INVOICE_SUBMITTED_TWICE",
                expected_match_status="EXCEPTION_DUPLICATE",
                expected_routing_role="SYSTEM_ADMIN",
                expected_payment_ready=False,
                root_cause_field="invoice_number",
                notes="Identical duplicate invoice payload submitted second time",
            )
            self.ground_truth_records.append(gt)

        # 15 Closed Vendor (POs 1486 to 1500)
        for i in range(1486, 1501):
            po = self.purchase_orders[i - 1]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            invoice_date = po_order_date + timedelta(days=self.rng.randint(3, 20))
            due_date = invoice_date + timedelta(days=30)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                l_sub = pol.line_subtotal
                l_tax = pol.line_tax
                l_tot = pol.line_total
                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=pol.ordered_quantity,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=pol.unit_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_CLOSED_VENDOR",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="CLOSED_VENDOR",
                expected_match_status="EXCEPTION_CLOSED_VENDOR",
                expected_routing_role="SYSTEM_ADMIN",
                expected_payment_ready=False,
                root_cause_field="vendor_status",
                notes="Invoice submitted by an inactive, suspended, or closed vendor",
            )
            self.ground_truth_records.append(gt)

        # 15 Tax Mismatch (POs 556 to 570)
        for i in range(556, 571):
            po = self.purchase_orders[i - 1]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            invoice_date = po_order_date + timedelta(days=self.rng.randint(3, 20))
            due_date = invoice_date + timedelta(days=30)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                l_sub = pol.line_subtotal
                wrong_tax_rate = 0.2800  # Statutory mismatch
                l_tax = round(l_sub * wrong_tax_rate, 2)
                l_tot = round(l_sub + l_tax, 2)
                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=pol.ordered_quantity,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=pol.unit_price,
                    tax_code="TAX_CUSTOM_28",
                    tax_rate=wrong_tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_TAX_MISMATCH",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="TAX_MISMATCH",
                expected_match_status="EXCEPTION_TAX_MISMATCH",
                expected_routing_role="OPERATIONS_ANALYST",
                expected_payment_ready=False,
                root_cause_field="tax_rate",
                notes="Invoice applied unauthorized tax code or arbitrary tax rate",
            )
            self.ground_truth_records.append(gt)

        # 15 Line Sum Arithmetic Mismatch (POs 571 to 585)
        for i in range(571, 586):
            po = self.purchase_orders[i - 1]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            invoice_date = po_order_date + timedelta(days=self.rng.randint(3, 20))
            due_date = invoice_date + timedelta(days=30)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                l_sub = pol.line_subtotal
                l_tax = pol.line_tax
                l_tot = pol.line_total
                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=pol.ordered_quantity,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=pol.unit_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_ARITHMETIC_ERROR",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            # Inject arithmetic discrepancy
            grand_total = round(subtotal + tax_total + 150.00, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="INVOICE_TOTAL_DIFFERS_FROM_LINE_SUM",
                expected_match_status="EXCEPTION_ARITHMETIC_ERROR",
                expected_routing_role="OPERATIONS_ANALYST",
                expected_payment_ready=False,
                root_cause_field="total_amount",
                notes="Stated header grand total does not equal arithmetic sum of line totals",
            )
            self.ground_truth_records.append(gt)

        # 15 Invoice Date Before PO Date (POs 586 to 600)
        for i in range(586, 601):
            po = self.purchase_orders[i - 1]
            vendor = vendor_map[po.vendor_id]
            po_lines = po_lines_by_po.get(po.po_id, [])

            po_order_date = date.fromisoformat(po.order_date)
            # Inject temporal anomaly
            invoice_date = po_order_date - timedelta(days=self.rng.randint(5, 25))
            due_date = invoice_date + timedelta(days=30)
            invoice_id = self._format_invoice_id(vendor.vendor_id, inv_seq)
            invoice_num = f"INV-EXT-{inv_seq:06d}"
            inv_seq += 1

            subtotal = 0.0
            tax_total = 0.0
            cur_lines = []

            for idx, pol in enumerate(po_lines, 1):
                inv_line_id = f"INVL-{invoice_id}-{idx:02d}"
                l_sub = pol.line_subtotal
                l_tax = pol.line_tax
                l_tot = pol.line_total
                subtotal += l_sub
                tax_total += l_tax

                inv_line = InvoiceLine(
                    invoice_line_id=inv_line_id,
                    invoice_id=invoice_id,
                    po_line_id=pol.po_line_id,
                    line_number=idx,
                    sku=pol.sku,
                    item_description=pol.item_description,
                    invoiced_quantity=pol.ordered_quantity,
                    unit_of_measure=pol.unit_of_measure,
                    unit_price=pol.unit_price,
                    tax_code=pol.tax_code,
                    tax_rate=pol.tax_rate,
                    line_subtotal=l_sub,
                    line_tax=l_tax,
                    line_total=l_tot,
                    match_status="EXCEPTION_TEMPORAL_VIOLATION",
                )
                cur_lines.append(inv_line)

            subtotal = round(subtotal, 2)
            tax_total = round(tax_total, 2)
            grand_total = round(subtotal + tax_total, 2)

            inv = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                currency=vendor.currency,
                subtotal_amount=subtotal,
                tax_amount=tax_total,
                total_amount=grand_total,
                intake_channel=self.rng.choice(ALLOWED_INTAKE_CHANNELS),
                match_status="PENDING_MATCH",
                status="RECEIVED",
                created_at=invoice_date.isoformat() + "T10:00:00Z",
            )
            self.invoices.append(inv)
            self.invoice_lines.extend(cur_lines)

            gt = GroundTruthRecord(
                invoice_id=invoice_id,
                invoice_number=invoice_num,
                vendor_id=vendor.vendor_id,
                po_id=po.po_id,
                is_anomaly=True,
                anomaly_type="INVOICE_DATE_BEFORE_PO_DATE",
                expected_match_status="EXCEPTION_TEMPORAL_VIOLATION",
                expected_routing_role="OPERATIONS_ANALYST",
                expected_payment_ready=False,
                root_cause_field="invoice_date",
                notes="Invoice date strictly precedes the creation of the Purchase Order",
            )
            self.ground_truth_records.append(gt)

        return self.invoices, self.invoice_lines, self.ground_truth_records

    def generate_all(self):
        """Execute complete generation workflow in strict dependency order."""
        self.generate_vendors()
        self.generate_purchase_orders_and_lines()
        self.generate_goods_receipts()
        self.generate_invoices_and_scenarios()

    def export_data(self, output_raw_dir: Optional[Path] = None, output_gt_dir: Optional[Path] = None):
        """Export raw master/transaction datasets and ground truth to CSV and JSON."""
        raw_dir = output_raw_dir or RAW_DATA_DIR
        gt_dir = output_gt_dir or GROUND_TRUTH_DIR

        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(gt_dir, exist_ok=True)

        datasets = {
            "vendors": [v.to_dict() for v in self.vendors],
            "purchase_orders": [po.to_dict() for po in self.purchase_orders],
            "po_lines": [pol.to_dict() for pol in self.po_lines],
            "goods_receipts": [grn.to_dict() for grn in self.goods_receipts],
            "goods_receipt_lines": [grnl.to_dict() for grnl in self.goods_receipt_lines],
            "invoices": [inv.to_dict() for inv in self.invoices],
            "invoice_lines": [invl.to_dict() for invl in self.invoice_lines],
        }

        for name, records in datasets.items():
            csv_path = raw_dir / f"{name}.csv"
            json_path = raw_dir / f"{name}.json"

            if records:
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
                    writer.writeheader()
                    writer.writerows(records)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)

        gt_dicts = [gt.to_dict() for gt in self.ground_truth_records]
        gt_csv_path = gt_dir / "ground_truth.csv"
        gt_json_path = gt_dir / "ground_truth.json"

        if gt_dicts:
            with open(gt_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(gt_dicts[0].keys()))
                writer.writeheader()
                writer.writerows(gt_dicts)

        with open(gt_json_path, "w", encoding="utf-8") as f:
            json.dump(gt_dicts, f, indent=2)

        self.export_sql_seed()

        print(f"[Generator] Data exported successfully to {raw_dir} and {gt_dir}")
        print(f"  - Vendors: {len(self.vendors)}")
        print(f"  - Purchase Orders: {len(self.purchase_orders)}")
        print(f"  - PO Lines: {len(self.po_lines)}")
        print(f"  - Goods Receipts: {len(self.goods_receipts)}")
        print(f"  - GRN Lines: {len(self.goods_receipt_lines)}")
        print(f"  - Invoices: {len(self.invoices)}")
        print(f"  - Invoice Lines: {len(self.invoice_lines)}")
        print(f"  - Ground Truth Records: {len(self.ground_truth_records)}")

    def export_sql_seed(self, output_sql_path: Optional[Path] = None):
        """Export SQL INSERT statements for all generated tables."""
        sql_path = output_sql_path or (SQL_DIR / "seed_data.sql")
        os.makedirs(sql_path.parent, exist_ok=True)

        with open(sql_path, "w", encoding="utf-8") as f:
            f.write("-- Invoice automation seed data\n")
            f.write("-- Generated deterministically with seed 20261022\n\n")
            f.write("BEGIN TRANSACTION;\n\n")

            for v in self.vendors:
                esc_name = v.vendor_name.replace("'", "''")
                f.write(f"INSERT INTO vendors (vendor_id, vendor_name, tax_id, status, payment_terms, currency, contact_email, address_country, created_at, updated_at) "
                        f"VALUES ('{v.vendor_id}', '{esc_name}', '{v.tax_id}', '{v.status}', '{v.payment_terms}', '{v.currency}', '{v.contact_email}', '{v.address_country}', '{v.created_at}', '{v.updated_at}');\n")

            for po in self.purchase_orders:
                f.write(f"INSERT INTO purchase_orders (po_id, vendor_id, buyer_id, department, status, currency, subtotal_amount, tax_amount, total_amount, order_date, expected_delivery_date, created_at) "
                        f"VALUES ('{po.po_id}', '{po.vendor_id}', '{po.buyer_id}', '{po.department}', '{po.status}', '{po.currency}', {po.subtotal_amount}, {po.tax_amount}, {po.total_amount}, '{po.order_date}', '{po.expected_delivery_date}', '{po.created_at}');\n")

            for pol in self.po_lines:
                esc_desc = pol.item_description.replace("'", "''")
                f.write(f"INSERT INTO purchase_order_lines (po_line_id, po_id, line_number, sku, item_description, ordered_quantity, unit_of_measure, unit_price, tax_code, tax_rate, line_subtotal, line_tax, line_total) "
                        f"VALUES ('{pol.po_line_id}', '{pol.po_id}', {pol.line_number}, '{pol.sku}', '{esc_desc}', {pol.ordered_quantity}, '{pol.unit_of_measure}', {pol.unit_price}, '{pol.tax_code}', {pol.tax_rate}, {pol.line_subtotal}, {pol.line_tax}, {pol.line_total});\n")

            for grn in self.goods_receipts:
                f.write(f"INSERT INTO goods_receipts (grn_id, po_id, received_by, receipt_date, delivery_note_ref, status, created_at) "
                        f"VALUES ('{grn.grn_id}', '{grn.po_id}', '{grn.received_by}', '{grn.receipt_date}', '{grn.delivery_note_ref}', '{grn.status}', '{grn.created_at}');\n")

            for grnl in self.goods_receipt_lines:
                esc_notes = (grnl.inspection_notes or "").replace("'", "''")
                f.write(f"INSERT INTO goods_receipt_lines (grn_line_id, grn_id, po_line_id, line_number, received_quantity, accepted_quantity, rejected_quantity, inspection_notes) "
                        f"VALUES ('{grnl.grn_line_id}', '{grnl.grn_id}', '{grnl.po_line_id}', {grnl.line_number}, {grnl.received_quantity}, {grnl.accepted_quantity}, {grnl.rejected_quantity}, '{esc_notes}');\n")

            for inv in self.invoices:
                po_val = f"'{inv.po_id}'" if inv.po_id else "NULL"
                f.write(f"INSERT INTO invoices (invoice_id, invoice_number, vendor_id, po_id, invoice_date, due_date, currency, subtotal_amount, tax_amount, total_amount, intake_channel, match_status, status, created_at) "
                        f"VALUES ('{inv.invoice_id}', '{inv.invoice_number}', '{inv.vendor_id}', {po_val}, '{inv.invoice_date}', '{inv.due_date}', '{inv.currency}', {inv.subtotal_amount}, {inv.tax_amount}, {inv.total_amount}, '{inv.intake_channel}', '{inv.match_status}', '{inv.status}', '{inv.created_at}');\n")

            for invl in self.invoice_lines:
                po_line_val = f"'{invl.po_line_id}'" if invl.po_line_id else "NULL"
                esc_desc = invl.item_description.replace("'", "''")
                f.write(f"INSERT INTO invoice_lines (invoice_line_id, invoice_id, po_line_id, line_number, sku, item_description, invoiced_quantity, unit_of_measure, unit_price, tax_code, tax_rate, line_subtotal, line_tax, line_total, match_status) "
                        f"VALUES ('{invl.invoice_line_id}', '{invl.invoice_id}', {po_line_val}, {invl.line_number}, '{invl.sku}', '{esc_desc}', {invl.invoiced_quantity}, '{invl.unit_of_measure}', {invl.unit_price}, '{invl.tax_code}', {invl.tax_rate}, {invl.line_subtotal}, {invl.line_tax}, {invl.line_total}, '{invl.match_status}');\n")

            f.write("\nCOMMIT;\n")
