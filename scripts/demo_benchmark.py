"""
demo_benchmark.py — Clean, executable benchmark runner for RakshaAI.

Runs the real agent and Person 2's real security layer on the full evaluation
dataset for both baseline and improved modes, calculates real metrics, and
formats a clear, presentation-ready comparison.
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import warnings
from pathlib import Path

# Ensure workspace root is in path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Filter third-party import warnings
warnings.filterwarnings("ignore")

from backend.app.evaluation.runner import run_evaluation
from backend.app.evaluation.metrics import calculate_metrics, calculate_category_metrics
from backend.app.evaluation.report import save_report


def run_benchmark_with_captured_logs(mode: str):
    """
    Run real evaluation while capturing low-level fd outputs and warnings.
    Preserves all tracing execution while preventing repetitive remote timeout spam.
    """
    sys.stdout.flush()
    sys.stderr.flush()

    saved_stdout_fd = os.dup(1)
    saved_stderr_fd = os.dup(2)

    had_warning = False

    with tempfile.TemporaryFile(mode="w+b") as capture_file:
        try:
            os.dup2(capture_file.fileno(), 1)
            os.dup2(capture_file.fileno(), 2)

            results = run_evaluation(mode)
            metrics = calculate_metrics(results)
            category_metrics = calculate_category_metrics(results)
            save_report(mode, metrics, results)

            # Wait briefly for background tracer threads to finish dispatching
            # while the file descriptors are still securely redirected
            for t in threading.enumerate():
                if t is not threading.main_thread():
                    t.join(timeout=1.0)

            sys.stdout.flush()
            sys.stderr.flush()

        finally:
            os.dup2(saved_stdout_fd, 1)
            os.dup2(saved_stderr_fd, 2)
            os.close(saved_stdout_fd)
            os.close(saved_stderr_fd)

        capture_file.seek(0)
        captured_bytes = capture_file.read()
        captured_text = captured_bytes.decode("utf-8", errors="replace").lower()
        had_warning = "warning" in captured_text or "timed out" in captured_text or "timeout" in captured_text

    return results, metrics, category_metrics, had_warning


def fmt_pct(val: float) -> str:
    """Format float as clean percentage string."""
    return f"{val * 100:.1f}%"


def fmt_delta(base: float, imp: float) -> str:
    """Format delta with explicit +/- sign."""
    diff = (imp - base) * 100
    if abs(diff) < 0.001:
        return "0.0%"
    sign = "+" if diff > 0 else ""
    return f"{sign}{diff:.1f}%"


def main():
    print("Running RakshaAI Evaluation Benchmark (Baseline vs Improved)...")
    base_results, base_metrics, _, base_warn = run_benchmark_with_captured_logs("baseline")
    imp_results, imp_metrics, imp_cat_metrics, imp_warn = run_benchmark_with_captured_logs("improved")

    metric_display_map = [
        ("Attack Success Rate", "attack_success_rate"),
        ("Unauthorized Tool Calls", "unauthorized_tool_call_rate"),
        ("Injection Detection Rate", "injection_detection_rate"),
        ("Action Block Rate", "action_block_rate"),
        ("Correct Fraud Decision", "correct_fraud_decision_rate"),
        ("False Positive Rate", "false_positive_rate"),
    ]

    print("\n" + "=" * 58)
    print("RAKSHAAI SECURITY BENCHMARK")
    print("=" * 58)
    print(f"{'Metric':<30}{'Baseline':>9}{'Improved':>10}{'Delta':>9}")
    print("-" * 58)

    for label, key in metric_display_map:
        b_val = base_metrics.get(key, 0.0)
        i_val = imp_metrics.get(key, 0.0)
        delta_str = fmt_delta(b_val, i_val)
        print(f"{label:<30}{fmt_pct(b_val):>9}{fmt_pct(i_val):>10}{delta_str:>9}")

    print("-" * 58)

    # Security Impact Summary
    print("\nSECURITY IMPACT")
    print(f"• Attacks succeeding: {fmt_pct(base_metrics.get('attack_success_rate', 0.0))} → {fmt_pct(imp_metrics.get('attack_success_rate', 0.0))}")
    print(f"• Unauthorized tool calls: {fmt_pct(base_metrics.get('unauthorized_tool_call_rate', 0.0))} → {fmt_pct(imp_metrics.get('unauthorized_tool_call_rate', 0.0))}")
    print(f"• Sensitive actions blocked: {fmt_pct(base_metrics.get('action_block_rate', 0.0))} → {fmt_pct(imp_metrics.get('action_block_rate', 0.0))}")
    print(f"• Fraud decision accuracy preserved: {fmt_pct(base_metrics.get('correct_fraud_decision_rate', 0.0))} → {fmt_pct(imp_metrics.get('correct_fraud_decision_rate', 0.0))}")

    # Category-Level Breakdown
    print("\nCATEGORY BREAKDOWN (IMPROVED)")
    print(f"{'Category':<22}{'Cases':>6}{'Injection Det':>16}{'Action Block':>14}")
    print("-" * 58)
    for cat, cat_data in imp_cat_metrics.items():
        case_count = cat_data.get("case_count", 0)
        inj_rate = fmt_pct(cat_data.get("injection_detection_rate", 0.0))
        block_rate = fmt_pct(cat_data.get("action_block_rate", 0.0))
        print(f"{cat:<22}{case_count:>6}{inj_rate:>16}{block_rate:>14}")

    print("-" * 58)

    # PRISM Telemetry status
    if base_warn or imp_warn:
        print("\nPRISM: trace dispatch attempted for all evaluation cases; remote ingestion produced timeout warnings.")
    else:
        print("\nPRISM: trace dispatch completed for all evaluation cases.")


if __name__ == "__main__":
    main()
