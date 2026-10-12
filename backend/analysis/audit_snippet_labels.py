"""Audit snippet-level complexity labels without changing the dataset.

The problem-optimal label is not necessarily the complexity of every submitted
implementation.  This report finds same-problem records whose source shapes
disagree while their recorded snippet labels are identical.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def _rows(path: str) -> list[dict[str, Any]]:
    file = Path(path)
    if not file.is_file():
        raise IsADirectoryError(f"Dataset must be a JSONL file: {file}")
    return [json.loads(line) for line in file.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _shape(source: str) -> dict[str, Any]:
    text = source or ""
    lower = text.lower()
    loops = re.findall(r"\b(?:for|while|do)\b", lower)
    return {
        "loop_count": len(loops),
        "nested_loop_hint": bool(re.search(r"\bfor\b[\s\S]{0,800}\b(?:for|while)\b", lower)),
        "recursion": bool(re.search(r"\b(?:def|function|class|int|long|bool|void|auto)\s+(\w+)\s*\([^)]*\)[^{:]*[{:][\s\S]{0,1200}\b\1\s*\(", text, re.I)),
        "sort": bool(re.search(r"\b(?:sort|sorted)\s*\(|\.sort\s*\(", lower)),
        "hash": bool(re.search(r"\b(?:unordered_map|unordered_set|hashmap|hashset|dict|set|map)\b", lower)),
        "allocation": bool(re.search(r"\b(?:malloc|calloc|realloc|new|vector|array|hashmap|dict|set)\b", lower)),
        "two_dimensional": bool(re.search(r"vector\s*<\s*vector|\[\s*[^]]+\]\s*\[", lower)),
    }


def audit(path: str) -> dict[str, Any]:
    rows = _rows(path)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        labels = (
            row.get("snippet_time_complexity") or row.get("true_time_complexity"),
            row.get("snippet_space_complexity") or row.get("true_space_complexity"),
        )
        groups[str(row.get("problem_id") or row.get("title") or "unknown")].append({
            "solution_id": row.get("solution_id"),
            "language": row.get("language"),
            "approach": row.get("approach"),
            "labels": labels,
            "shape": _shape(row.get("source") or row.get("reference_source") or ""),
        })

    suspicious = []
    for problem_id, records in groups.items():
        by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_label[json.dumps(record["labels"], sort_keys=True)].append(record)
        for label_key, same_label in by_label.items():
            signatures = {json.dumps(record["shape"], sort_keys=True) for record in same_label}
            if len(signatures) > 1:
                suspicious.append({
                    "problem_id": problem_id,
                    "labels": json.loads(label_key),
                    "records": same_label,
                    "reason": "same labels but structurally different snippets",
                })

    return {
        "benchmark": "snippet_label_audit",
        "dataset": path,
        "rows": len(rows),
        "problem_groups": len(groups),
        "suspicious_groups": len(suspicious),
        "suspicious": suspicious,
        "status": "REVIEW_REQUIRED" if suspicious else "NO_CONTRADICTIONS_DETECTED",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = audit(args.dataset)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("benchmark", "rows", "problem_groups", "suspicious_groups", "status")}, indent=2))


if __name__ == "__main__":
    main()

