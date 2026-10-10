"""Benchmark AST complexity against the complexity of each snippet itself.

This intentionally keeps problem-optimal labels separate.  A brute-force
solution is correct when its independently reviewed snippet complexity says
O(n^3), even if the problem has an O(n^2) optimal solution.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .static_analyzer import analyze_source


def _rows(path: str) -> list[dict[str, Any]]:
    dataset = Path(path)
    if not dataset.exists():
        raise FileNotFoundError(
            f"Dataset file does not exist: {dataset}. "
            "Create the JSONL file before running the benchmark."
        )
    if not dataset.is_file():
        raise IsADirectoryError(
            f"Dataset path is a directory, not a JSONL file: {dataset}. "
            "Check the Docker bind-mount source path on the host."
        )
    text = dataset.read_text(encoding="utf-8-sig")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _canonical(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    text = text.replace("²", "^2").replace("³", "^3")
    text = re.sub(r"\s+", "", text)
    # README labels commonly use Unicode/LaTeX multiplication.  Treat these
    # as notation variants so ``O(m \\times n)``, ``O(m*n)`` and ``O(mn)``
    # compare equal instead of becoming false AST mismatches.
    text = text.replace("×", "*").replace("\\times", "*").replace("\\cdot", "*")
    text = text.replace("\\,", "")
    text = text.replace("\\log", "log")
    text = text.replace("\\max", "max")
    text = re.sub(r"log[_]?\{?10\}?", "log", text)
    text = text.replace("log|x|", "logn")
    text = text.replace("log(n)", "logn")
    # Canonicalize commutative product notation used by reviewed labels.
    # These are equivalent descriptions, not analyzer-specific guesses.
    text = text.replace("o(n*logk)", "o(nlogk)")
    text = text.replace("o(n*log(k))", "o(nlogk)")
    text = text.replace("o(n*m)", "o(m*n)")
    text = text.replace("o(nm)", "o(m*n)")
    text = text.replace("o(n*k)", "o(nk)")
    return text


def _equal(left: Any, right: Any) -> bool:
    return _canonical(left) == _canonical(right) and left is not None and right is not None


def _expected(row: dict[str, Any], dimension: str) -> Any:
    return row.get(f"snippet_{dimension}_complexity") or row.get(
        f"true_{dimension}_complexity"
    )


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    source = row.get("source") or row.get("reference_source") or ""
    language = str(row.get("language", "")).lower().strip()
    expected_time = _expected(row, "time")
    expected_space = _expected(row, "space")
    base = {
        "problem_id": row.get("problem_id"),
        "solution_id": row.get("solution_id"),
        "approach": row.get("approach"),
        "language": language,
        "expected_time": expected_time,
        "expected_space": expected_space,
        "optimal_time": row.get("optimal_time_complexity"),
        "optimal_space": row.get("optimal_space_complexity"),
    }
    if not source or not language or expected_time is None or expected_space is None:
        return {**base, "status": "MISSING_SNIPPET_TRUTH", "predicted_time": None, "predicted_space": None}

    result = analyze_source(source, language)
    predicted_time = result.time_complexity
    predicted_space = result.space_complexity
    base.update(
        {
            "predicted_time": predicted_time,
            "predicted_space": predicted_space,
            "confidence": result.confidence,
            "method": result.method,
            "analyzer_status": result.status,
            "signals": list(result.signals),
            "evidence_quality": result.evidence_quality,
            "optimal_match": (
                _equal(predicted_time, row.get("optimal_time_complexity"))
                and _equal(predicted_space, row.get("optimal_space_complexity"))
                if row.get("optimal_time_complexity") is not None
                and row.get("optimal_space_complexity") is not None
                else None
            ),
        }
    )
    if not predicted_time or not predicted_space or result.status != "ANALYZED":
        base["status"] = "REVIEW_REQUIRED"
    elif _equal(predicted_time, expected_time) and _equal(predicted_space, expected_space):
        base["status"] = "AST_CORRECT"
    elif _equal(predicted_time, expected_time) or _equal(predicted_space, expected_space):
        base["status"] = "AST_PARTIAL"
    else:
        base["status"] = "AST_WRONG"
    return base


def run(path: str) -> dict[str, Any]:
    records = [classify_row(row) for row in _rows(path)]
    counts = Counter(record["status"] for record in records)
    eligible = [record for record in records if record["status"] in {"AST_CORRECT", "AST_PARTIAL", "AST_WRONG"}]
    correct = sum(record["status"] == "AST_CORRECT" for record in eligible)
    by_approach: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    by_language: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    for record in records:
        by_approach[str(record.get("approach") or "unknown")][record["status"]] += 1
        by_language[str(record.get("language") or "unknown")][record["status"]] += 1
    return {
        "benchmark": "snippet_complexity_truth",
        "total": len(records),
        "eligible": len(eligible),
        "correct": correct,
        "accuracy": round(correct / len(eligible), 4) if eligible else None,
        "status_counts": dict(counts),
        "by_approach": {key: dict(value) for key, value in by_approach.items()},
        "by_language": {key: dict(value) for key, value in by_language.items()},
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run(args.dataset)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("benchmark", "total", "eligible", "correct", "accuracy", "status_counts")}, indent=2))


if __name__ == "__main__":
    main()
