"""
Evaluation & Accuracy Metrics Module
Compares workflow engine decisions against independent ground truth labels.
Computes Precision, Recall, F1-Score, Confusion Matrix, and Financial Safety Metrics.
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.config import GROUND_TRUTH_DIR, PROCESSED_DATA_DIR, REPORTS_DIR

class ModelEvaluator:
    """
    Evaluator that rigorously audits the performance, classification accuracy,
    and financial control safety of the 3-Way Matching and Routing Engine.
    """

    def __init__(
        self,
        gt_dir: Optional[Path] = None,
        processed_dir: Optional[Path] = None,
        reports_dir: Optional[Path] = None,
    ):
        self.gt_dir = gt_dir or GROUND_TRUTH_DIR
        self.processed_dir = processed_dir or PROCESSED_DATA_DIR
        self.reports_dir = reports_dir or REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)

    def evaluate(self) -> Dict[str, Any]:
        """Runs comparative evaluation against ground truth."""
        gt_path = self.gt_dir / "ground_truth.json"
        processed_inv_path = self.processed_dir / "invoices_processed.json"
        payments_path = self.processed_dir / "payments.json"

        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = {r["invoice_id"]: r for r in json.load(f)}

        with open(processed_inv_path, "r", encoding="utf-8") as f:
            processed_invoices = {r["invoice_id"]: r for r in json.load(f)}

        with open(payments_path, "r", encoding="utf-8") as f:
            paid_invoice_ids = {r["invoice_id"] for r in json.load(f)}

        # Counters
        tp = 0  # Actual anomaly, detected as exception
        fp = 0  # Clean invoice, detected as exception
        tn = 0  # Clean invoice, accurately approved
        fn = 0  # Actual anomaly, erroneously approved (CRITICAL LEAKAGE)

        anomaly_breakdown: Dict[str, Dict[str, int]] = {}

        for inv_id, gt in gt_data.items():
            is_true_anomaly = gt["is_anomaly"]
            true_type = gt["anomaly_type"]

            inv = processed_invoices.get(inv_id)
            if not inv:
                continue

            engine_status = inv["match_status"]
            is_detected_exception = engine_status != "MATCHED"

            if true_type not in anomaly_breakdown:
                anomaly_breakdown[true_type] = {"total": 0, "detected": 0, "missed": 0}
            anomaly_breakdown[true_type]["total"] += 1

            if is_true_anomaly:
                if is_detected_exception:
                    tp += 1
                    anomaly_breakdown[true_type]["detected"] += 1
                else:
                    fn += 1
                    anomaly_breakdown[true_type]["missed"] += 1
            else:
                if is_detected_exception:
                    fp += 1
                else:
                    tn += 1

        total_samples = tp + fp + tn + fn
        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        accuracy = ((tp + tn) / total_samples) if total_samples > 0 else 0.0
        leakage_rate = (fn / (tp + fn)) if (tp + fn) > 0 else 0.0

        results = {
            "evaluation_metrics": {
                "total_invoices_evaluated": total_samples,
                "true_positives": tp,
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1_score, 4),
                "leakage_rate_false_negatives": round(leakage_rate, 4),
            },
            "financial_safety_audit": {
                "blocked_invoice_payment_leakage": fn,
                "safety_control_status": "PASSED - ZERO DEFECTIVE PAYMENTS" if fn == 0 else "FAILED - PAYMENTS LEAKED",
            },
            "category_level_breakdown": anomaly_breakdown,
        }

        # Export Report JSON
        report_json_path = self.reports_dir / "evaluation_report.json"
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Export Report Markdown
        report_md_path = self.reports_dir / "evaluation_report.md"
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write("# Evaluation Report\n\n")
            f.write("### Summary\n")
            f.write(f"- **Total Invoices Evaluated**: {total_samples:,}\n")
            f.write(f"- **Overall Accuracy**: {accuracy * 100:.2f}%\n")
            f.write(f"- **Precision**: {precision * 100:.2f}%\n")
            f.write(f"- **Recall**: {recall * 100:.2f}%\n")
            f.write(f"- **F1-Score**: {f1_score * 100:.2f}%\n")
            f.write(f"- **Payment Safety Compliance**: **{results['financial_safety_audit']['safety_control_status']}**\n\n")

            f.write("### Confusion Matrix\n\n")
            f.write("| Metric | Predicted Exception | Predicted Matched / Ready |\n")
            f.write("| :--- | :---: | :---: |\n")
            f.write(f"| **Actual Anomaly** | **TP: {tp:,}** | **FN: {fn:,}** |\n")
            f.write(f"| **Actual Clean** | **FP: {fp:,}** | **TN: {tn:,}** |\n\n")

            f.write("### Anomaly Category Detection Breakdown\n\n")
            f.write("| Anomaly Category | Total Cases | Accurately Detected | Detection Recall | Missed |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: |\n")
            for cat, data in anomaly_breakdown.items():
                cat_recall = (data["detected"] / data["total"] * 100) if data["total"] > 0 else 100.0
                f.write(f"| `{cat}` | {data['total']} | {data['detected']} | {cat_recall:.1f}% | {data['missed']} |\n")

        print(f"[Evaluator] Evaluation completed. Report generated at {report_md_path}")
        print(f"  - Precision: {precision * 100:.2f}% | Recall: {recall * 100:.2f}% | F1: {f1_score * 100:.2f}%")
        print(f"  - Financial Safety: {results['financial_safety_audit']['safety_control_status']}")
        return results
