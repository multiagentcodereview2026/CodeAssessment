"""Stage 10 deterministic final-gate report.

This module only aggregates frozen measurement artifacts; it never changes
the analyzer or private labels.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _read(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _test_rate(report: dict[str, Any]) -> float | None:
    test = report.get("splits", {}).get("test", {})
    rate = test.get("exact_rate")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)):
        return None
    rate = float(rate)
    return rate if math.isfinite(rate) and 0.0 <= rate <= 1.0 else None


def _report_ready(report: dict[str, Any]) -> bool:
    """Require nonempty, complete, labeled data and a valid test metric."""
    dataset_rows = report.get("dataset_rows")
    analyzed_rows = report.get("analyzed_rows")
    if (
        isinstance(dataset_rows, bool)
        or not isinstance(dataset_rows, int)
        or dataset_rows <= 0
        or isinstance(analyzed_rows, bool)
        or not isinstance(analyzed_rows, int)
        or analyzed_rows != dataset_rows
    ):
        return False
    if report.get("missing_reference_source") != 0 or report.get("missing_labels") != 0:
        return False
    test = report.get("splits", {}).get("test", {})
    test_rows = test.get("rows")
    return (
        isinstance(test_rows, int)
        and not isinstance(test_rows, bool)
        and test_rows > 0
        and _test_rate(report) is not None
    )


def evaluate(baseline: str, unseen: str, adversarial: str) -> dict[str, Any]:
    reports = {
        "baseline": _read(baseline),
        "unseen": _read(unseen),
        "adversarial": _read(adversarial),
    }
    readiness = {name: _report_ready(report) for name, report in reports.items()}
    holdouts_valid = readiness["unseen"] and readiness["adversarial"]
    baseline_ready = readiness["baseline"]
    return {
        "stage": "10",
        "baseline": {
            "rows": reports["baseline"].get("dataset_rows", 0),
            "test_exact_rate": _test_rate(reports["baseline"]),
            "freeze_fingerprint": reports["baseline"].get("freeze_fingerprint"),
            "ready": baseline_ready,
        },
        "unseen": {
            "rows": reports["unseen"].get("dataset_rows", 0),
            "test_exact_rate": _test_rate(reports["unseen"]),
            "ready": readiness["unseen"],
        },
        "adversarial": {
            "rows": reports["adversarial"].get("dataset_rows", 0),
            "test_exact_rate": _test_rate(reports["adversarial"]),
            "ready": readiness["adversarial"],
        },
        "holdouts_valid": holdouts_valid,
        "status": "READY_FOR_FINAL_REVIEW" if baseline_ready and holdouts_valid else "HOLD",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--unseen", required=True)
    parser.add_argument("--adversarial", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = evaluate(args.baseline, args.unseen, args.adversarial)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
