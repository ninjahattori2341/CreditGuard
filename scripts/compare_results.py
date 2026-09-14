import json
from pathlib import Path


def load_report(mode: str) -> dict:
    path = Path("evaluation_mock") / f"{mode}_report.json"

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def main():
    baseline = load_report("baseline")
    improved = load_report("improved")

    baseline_metrics = baseline["metrics"]
    improved_metrics = improved["metrics"]

    print("\n" + "=" * 72)
    print("RAKSHAAI — BASELINE vs IMPROVED")
    print("=" * 72)

    print(
        f"{'Metric':<35}"
        f"{'Baseline':>12}"
        f"{'Improved':>12}"
        f"{'Change':>12}"
    )

    print("-" * 72)

    for metric in baseline_metrics:
        b = baseline_metrics[metric]
        i = improved_metrics[metric]

        change = i - b

        print(
            f"{metric:<35}"
            f"{percentage(b):>12}"
            f"{percentage(i):>12}"
            f"{percentage(change):>12}"
        )

    print("=" * 72)


if __name__ == "__main__":
    main()