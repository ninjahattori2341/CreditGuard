import json
from pathlib import Path

from backend.app.prism.evaluators import evaluate_result


def save_report(mode: str, metrics: dict, results: list):
    output_dir = Path("evaluation_mock")
    output_dir.mkdir(exist_ok=True)

    detailed_results = []

    for result in results:
        detailed_results.append(
            evaluate_result(result)
        )

    output = {
        "mode": mode,
        "metrics": metrics,
        "results": detailed_results,
    }

    path = output_dir / f"{mode}_report.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return path