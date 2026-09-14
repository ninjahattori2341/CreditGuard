import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.evaluation.runner import run_evaluation
from backend.app.evaluation.metrics import calculate_metrics
from backend.app.evaluation.report import save_report


def main():
    for mode in ["baseline", "improved"]:
        results = run_evaluation(mode)
        metrics = calculate_metrics(results)
        report_path = save_report(mode, metrics, results)

        print(f"\n=== {mode.upper()} ===")

        for name, value in metrics.items():
            print(f"{name}: {value:.2%}")

        print(f"Report: {report_path}")


if __name__ == "__main__":
    main()