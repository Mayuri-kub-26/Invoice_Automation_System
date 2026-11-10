"""
Unified CLI Entry Point for the Invoice Automation System
Usage:
    python main.py generate [--seed 20261022] [--scale 1.0]
    python main.py pipeline
    python main.py validate
    python main.py evaluate
    python main.py reproducibility
    python main.py all
    python main.py dashboard
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.config import DEFAULT_SEED
from src.generator import SyntheticDataGenerator
from src.pipeline import InvoiceProcessingPipeline
from src.validator import DataIntegrityValidator
from src.evaluator import ModelEvaluator
from src.reproducibility_check import ReproducibilityAuditor

def cmd_generate(args):
    print("=" * 70)
    print("STEP 1-7: EXECUTING SYNTHETIC DATA GENERATION")
    print(f"Seed: {args.seed} | Scale: {args.scale}")
    print("=" * 70)
    gen = SyntheticDataGenerator(seed=args.seed, scale=args.scale)
    gen.generate_all()
    gen.export_data()
    print("\nGeneration complete. Master tables, transactions and SQL seed created.\n")

def cmd_pipeline(args):
    print("=" * 70)
    print("STEP 3: RUNNING END-TO-END INVOICE PROCESSING PIPELINE")
    print("=" * 70)
    pipe = InvoiceProcessingPipeline()
    pipe.run_pipeline()
    print("\nPipeline complete. Invoices matched, exceptions routed, payments scheduled.\n")

def cmd_validate(args):
    print("=" * 70)
    print("STEP 8: RUNNING DATA INTEGRITY & CONSTRAINT VALIDATION SUITE")
    print("=" * 70)
    validator = DataIntegrityValidator()
    results = validator.validate_all()
    print(f"\nValidation Summary: {results['summary']['status']}")
    print(f"Checks Passed: {results['summary']['passed_checks']} / {results['summary']['total_checks']}\n")

def cmd_evaluate(args):
    print("=" * 70)
    print("STEP 7-8: RUNNING ACCURACY & FINANCIAL SAFETY EVALUATION")
    print("=" * 70)
    evaluator = ModelEvaluator()
    res = evaluator.evaluate()
    m = res["evaluation_metrics"]
    print(f"\nAccuracy: {m['accuracy']*100:.2f}% | Precision: {m['precision']*100:.2f}% | Recall: {m['recall']*100:.2f}% | F1: {m['f1_score']*100:.2f}%")
    print(f"Safety Status: {res['financial_safety_audit']['safety_control_status']}\n")

def cmd_reproducibility(args):
    print("=" * 70)
    print("STEP 10: RUNNING FIXED-SEED DOUBLE REPRODUCIBILITY AUDIT")
    print("=" * 70)
    auditor = ReproducibilityAuditor(seed=args.seed)
    res = auditor.run_reproducibility_test()
    print(f"\nReproducibility Result: {res['overall_reproducibility']}\n")

def cmd_all(args):
    print("\n" + "#" * 70)
    print("STARTING FULL END-TO-END INVOICE AUTOMATION SUITE")
    print("#" * 70 + "\n")
    cmd_generate(args)
    cmd_pipeline(args)
    cmd_validate(args)
    cmd_evaluate(args)
    cmd_reproducibility(args)
    print("#" * 70)
    print("ALL WORKFLOW STEPS SUCCESSFULLY COMPLETED!")
    print("#" * 70 + "\n")

def cmd_dashboard(args):
    app_path = BASE_DIR / "app.py"
    print(f"Launching Streamlit Web Dashboard: {app_path} ...")
    subprocess.run(["streamlit", "run", str(app_path)])

def main():
    parser = argparse.ArgumentParser(
        description="Invoice Automation System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Workflow command to execute")

    # Generate
    p_gen = subparsers.add_parser("generate", help="Generate synthetic master & transaction data")
    p_gen.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Pseudorandom generator seed")
    p_gen.add_argument("--scale", type=float, default=1.0, help="Volume scale multiplier (default: 1.0)")

    # Pipeline
    subparsers.add_parser("pipeline", help="Run intake, extraction, 3-way match, and payment engine")

    # Validate
    subparsers.add_parser("validate", help="Run Step 8 integrity checks (PK/FK/enums/dates/arithmetic)")

    # Evaluate
    subparsers.add_parser("evaluate", help="Audit model decisions against ground truth")

    # Reproducibility
    p_rep = subparsers.add_parser("reproducibility", help="Run Step 10 double-run reproducibility verification")
    p_rep.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Pseudorandom generator seed")

    # All
    p_all = subparsers.add_parser("all", help="Execute complete pipeline: generate, process, validate, evaluate, verify")
    p_all.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Pseudorandom generator seed")
    p_all.add_argument("--scale", type=float, default=1.0, help="Volume scale multiplier")

    # Dashboard
    subparsers.add_parser("dashboard", help="Launch interactive Streamlit web dashboard")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "generate": cmd_generate,
        "pipeline": cmd_pipeline,
        "validate": cmd_validate,
        "evaluate": cmd_evaluate,
        "reproducibility": cmd_reproducibility,
        "all": cmd_all,
        "dashboard": cmd_dashboard,
    }

    dispatch[args.command](args)

if __name__ == "__main__":
    main()
