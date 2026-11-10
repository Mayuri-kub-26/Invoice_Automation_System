"""
Reproducibility Verification Suite (Step 10)
Demonstrates deterministic reproducibility by regenerating the complete dataset twice
using the same fixed seed (20261022) and asserting bitwise SHA-256 hash and row count equivalence.
"""

import os
import shutil
import hashlib
import json
from pathlib import Path
from typing import Dict, Any

from src.config import DEFAULT_SEED, BASE_DIR, REPORTS_DIR
from src.generator import SyntheticDataGenerator

class ReproducibilityAuditor:
    """
    Auditor that verifies byte-for-byte reproducibility of synthetic generation.
    """

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed
        self.reports_dir = REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)
        self.temp_run_a = BASE_DIR / "data" / "reproducibility_run_a"
        self.temp_run_b = BASE_DIR / "data" / "reproducibility_run_b"

    def _compute_sha256(self, filepath: Path) -> str:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _count_rows(self, filepath: Path) -> int:
        with open(filepath, "r", encoding="utf-8") as f:
            # subtract 1 for CSV header
            return max(0, sum(1 for _ in f) - 1)

    def run_reproducibility_test(self) -> Dict[str, Any]:
        """Executes Run A and Run B and compares checksums."""
        # Cleanup any previous runs
        if self.temp_run_a.exists():
            shutil.rmtree(self.temp_run_a)
        if self.temp_run_b.exists():
            shutil.rmtree(self.temp_run_b)

        print(f"[Reproducibility] Executing Run A with seed {self.seed}...")
        gen_a = SyntheticDataGenerator(seed=self.seed, scale=1.0)
        gen_a.generate_all()
        gen_a.export_data(
            output_raw_dir=self.temp_run_a / "raw",
            output_gt_dir=self.temp_run_a / "ground_truth",
        )

        print(f"[Reproducibility] Executing Run B with seed {self.seed}...")
        gen_b = SyntheticDataGenerator(seed=self.seed, scale=1.0)
        gen_b.generate_all()
        gen_b.export_data(
            output_raw_dir=self.temp_run_b / "raw",
            output_gt_dir=self.temp_run_b / "ground_truth",
        )

        target_files = [
            ("raw/vendors.csv", "vendors.csv"),
            ("raw/purchase_orders.csv", "purchase_orders.csv"),
            ("raw/po_lines.csv", "po_lines.csv"),
            ("raw/goods_receipts.csv", "goods_receipts.csv"),
            ("raw/goods_receipt_lines.csv", "goods_receipt_lines.csv"),
            ("raw/invoices.csv", "invoices.csv"),
            ("raw/invoice_lines.csv", "invoice_lines.csv"),
            ("ground_truth/ground_truth.csv", "ground_truth.csv"),
        ]

        file_comparisons = {}
        all_matched = True

        for rel_path, display_name in target_files:
            file_a = self.temp_run_a / rel_path
            file_b = self.temp_run_b / rel_path

            hash_a = self._compute_sha256(file_a)
            hash_b = self._compute_sha256(file_b)
            rows_a = self._count_rows(file_a)
            rows_b = self._count_rows(file_b)

            hashes_match = (hash_a == hash_b)
            rows_match = (rows_a == rows_b)
            status = hashes_match and rows_match
            if not status:
                all_matched = False

            file_comparisons[display_name] = {
                "rows_run_a": rows_a,
                "rows_run_b": rows_b,
                "rows_identical": rows_match,
                "sha256_run_a": hash_a,
                "sha256_run_b": hash_b,
                "checksums_identical": hashes_match,
                "status": "PASS" if status else "FAIL",
            }

        # Clean temporary run folders
        shutil.rmtree(self.temp_run_a, ignore_errors=True)
        shutil.rmtree(self.temp_run_b, ignore_errors=True)

        results = {
            "fixed_seed": self.seed,
            "overall_reproducibility": "PASSED - 100% BITWISE EQUIVALENCE" if all_matched else "FAILED",
            "file_comparisons": file_comparisons,
        }

        # Export Report JSON
        report_json_path = self.reports_dir / "reproducibility_report.json"
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Export Report Markdown
        report_md_path = self.reports_dir / "reproducibility_report.md"
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write("# Reproducibility Report\n\n")
            f.write(f"### Status: **{results['overall_reproducibility']}**\n\n")
            f.write(f"- **Fixed Generator Seed**: `{self.seed}`\n")
            f.write("- **Methodology**: Two clean isolated runs from scratch, comparing file row counts and SHA-256 hashes.\n\n")
            f.write("### File-by-File Integrity & Parity Audit\n\n")
            f.write("| Table / File | Rows (A / B) | SHA-256 Checksum (Run A & Run B) | Parity Status |\n")
            f.write("| :--- | :---: | :---: | :---: |\n")
            for fname, d in file_comparisons.items():
                hash_snippet = f"`{d['sha256_run_a'][:16]}...`"
                f.write(f"| `{fname}` | {d['rows_run_a']:,} / {d['rows_run_b']:,} | {hash_snippet} | {d['status']} |\n")

        print(f"[Reproducibility] Audit complete: {results['overall_reproducibility']}")
        return results
