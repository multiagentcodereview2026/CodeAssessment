"""Stage 10 deterministic final-gate report.

This module only aggregates frozen measurement artifacts; it never changes
the analyzer or private labels.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _test_rate(report: dict[str, Any]) -> float | None:
    test = report.get("splits", {}).get("test", {})
    return test.get("exact_rate")


def evaluate(baseline: str, unseen: str, adversarial: str) -> dict[str, Any]:
    reports = {
        "baseline": _read(baseline),
        "unseen": _read(unseen),
        "adversarial": _read(adversarial),
    }
    holdouts_valid = all(
        reports[name].get("analyzed_rows", 0) == reports[name].get("dataset_rows", 0)
        and reports[name].get("missing_reference_source", 0) == 0
        and reports[name].get("missing_labels", 0) == 0
        for name in ("unseen", "adversarial")
    )
    baseline_ready = (
        reports["baseline"].get("analyzed_rows", 0) > 0
        and reports["baseline"].get("missing_reference_source", 0) == 0
        and reports["baseline"].get("missing_labels", 0) == 0
    )
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
            "ready": holdouts_valid,
        },
        "adversarial": {
            "rows": reports["adversarial"].get("dataset_rows", 0),
            "test_exact_rate": _test_rate(reports["adversarial"]),
            "ready": holdouts_valid,
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
