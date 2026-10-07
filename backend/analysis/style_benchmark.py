"""Read-only benchmark for labeled Style Agent samples.

Input JSONL records must contain: id, language, source, expected_label.
Labels are high, medium, or low.  The runner writes per-record evidence and
aggregate classification metrics; it never changes the database.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .style_ast_analyzer import analyze_style


def _predicted_label(score: float) -> str:
    if score >= 85:
        return "high"
    if score >= 70:
        return "medium"
    return "low"


def run(path: str) -> dict[str, Any]:
    # PowerShell commonly emits UTF-8 with a BOM; accept both BOM and plain
    # UTF-8 so benchmark files are portable across Windows and containers.
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8-sig")
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    records: list[dict[str, Any]] = []
    labels = {"high", "medium", "low"}
    for row in rows:
        expected = str(row["expected_label"]).lower()
        if expected not in labels:
            raise ValueError(f"Unsupported expected_label: {expected}")
        result = analyze_style(row.get("source", ""), row.get("language", "cpp"))
        predicted = _predicted_label(result["style_score"])
        label_consistency_warning = None
        source = str(row.get("source", ""))
        if "REPLACE_WITH_INDEPENDENTLY_LABELED_SOURCE" in source:
            label_consistency_warning = "Source is a benchmark placeholder and cannot be scored."
        elif expected == "high" and result["style_score"] < 85:
            label_consistency_warning = "Expected high but source score is below the high threshold."
        elif expected == "medium" and not 70 <= result["style_score"] < 85:
            label_consistency_warning = "Expected medium but source score is outside the medium threshold."
        elif expected == "low" and result["style_score"] >= 70:
            label_consistency_warning = "Expected low but source score is at least the medium threshold."
        records.append({
            "id": row.get("id"),
            "expected_label": expected,
            "predicted_label": predicted,
            "style_score": result["style_score"],
            "naming_score": result["naming_score"],
            "readability_score": result["readability_score"],
            "modularity_score": result["modularity_score"],
            "maintainability_score": result["maintainability_score"],
            "label_consistency_warning": label_consistency_warning,
            "findings": result["naming_issues"] + result["readability_issues"] + result["modularity_issues"] + result["maintainability_issues"],
        })
    eligible_records = [r for r in records if r["label_consistency_warning"] is None]
    correct = sum(r["expected_label"] == r["predicted_label"] for r in eligible_records)
    by_label: dict[str, dict[str, int]] = {}
    for label in sorted(labels):
        tp = sum(r["expected_label"] == label and r["predicted_label"] == label for r in eligible_records)
        fp = sum(r["expected_label"] != label and r["predicted_label"] == label for r in eligible_records)
        fn = sum(r["expected_label"] == label and r["predicted_label"] != label for r in eligible_records)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        by_label[label] = {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}
    warnings = sum(record["label_consistency_warning"] is not None for record in records)
    return {"records": records, "summary": {"total": len(records), "eligible": len(eligible_records), "correct": correct, "accuracy": round(correct / len(eligible_records), 4) if eligible_records else None, "benchmark_valid": warnings == 0 and bool(eligible_records), "label_consistency_warnings": warnings, "by_label": by_label}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run(args.dataset)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    for record in report["records"]:
        print(json.dumps({
            "id": record["id"],
            "expected": record["expected_label"],
            "predicted": record["predicted_label"],
            "style_score": record["style_score"],
            "label_warning": record["label_consistency_warning"],
        }))
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
