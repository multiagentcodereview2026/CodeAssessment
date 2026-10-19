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


def _review_exclusions(path: str | None) -> dict[str, str]:
    """Load reviewed benchmark exclusions without changing the source corpus.

    Each entry must name a ``solution_id`` and state why its independently
    reviewed truth cannot be compared under this benchmark's conventions.
    Missing reasons are rejected so a failed AST prediction can never be
    silently removed from the denominator.
    """
    if path is None:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = payload.get("exclusions", payload) if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise ValueError("Review exclusions must be a JSON list or an object with an 'exclusions' list.")
    exclusions: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each review exclusion must be an object.")
        solution_id = str(entry.get("solution_id") or "").strip()
        reason = str(entry.get("reason") or "").strip()
        if not solution_id or not reason:
            raise ValueError("Each review exclusion requires solution_id and reason.")
        exclusions[solution_id] = reason
    return exclusions


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
    # For a single linked list, reviewed sources use both L (list length) and
    # n (generic input length).  Treat only the exact unary forms as aliases;
    # do not rewrite L inside multi-parameter expressions where it may denote
    # a genuinely different quantity.
    if text == "o(l)":
        text = "o(n)"
    return text


def _equal(left: Any, right: Any) -> bool:
    return _canonical(left) == _canonical(right) and left is not None and right is not None


def _expected(row: dict[str, Any], dimension: str) -> Any:
    return row.get(f"snippet_{dimension}_complexity") or row.get(
        f"true_{dimension}_complexity"
    )


def classify_row(row: dict[str, Any], mode: str = "legacy") -> dict[str, Any]:
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

    result = analyze_source(source, language, mode=mode)
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


def run(path: str, mode: str = "legacy", review_exclusions_path: str | None = None) -> dict[str, Any]:
    exclusions = _review_exclusions(review_exclusions_path)
    records = [classify_row(row, mode=mode) for row in _rows(path)]
    for record in records:
        reason = exclusions.get(str(record.get("solution_id") or ""))
        if reason:
            record["review_exclusion_reason"] = reason
    counts = Counter(record["status"] for record in records)
    raw_eligible = [record for record in records if record["status"] in {"AST_CORRECT", "AST_PARTIAL", "AST_WRONG"}]
    eligible = [record for record in raw_eligible if "review_exclusion_reason" not in record]
    correct = sum(record["status"] == "AST_CORRECT" for record in eligible)
    time_correct = sum(
        _equal(record.get("predicted_time"), record.get("expected_time"))
        for record in eligible
    )
    space_correct = sum(
        _equal(record.get("predicted_space"), record.get("expected_space"))
        for record in eligible
    )
    partial_breakdown = Counter()
    for record in eligible:
        time_ok = _equal(record.get("predicted_time"), record.get("expected_time"))
        space_ok = _equal(record.get("predicted_space"), record.get("expected_space"))
        if time_ok and not space_ok:
            partial_breakdown["TIME_CORRECT_SPACE_MISMATCH"] += 1
        elif space_ok and not time_ok:
            partial_breakdown["SPACE_CORRECT_TIME_MISMATCH"] += 1
        elif not time_ok and not space_ok:
            partial_breakdown["BOTH_MISMATCH"] += 1
    by_approach: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    by_language: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    for record in records:
        by_approach[str(record.get("approach") or "unknown")][record["status"]] += 1
        by_language[str(record.get("language") or "unknown")][record["status"]] += 1
    return {
        "benchmark": "snippet_complexity_truth",
        "mode": mode,
        "total": len(records),
        "raw_eligible": len(raw_eligible),
        "eligible": len(eligible),
        "reviewed_excluded": len(raw_eligible) - len(eligible),
        "correct": correct,
        "accuracy": round(correct / len(eligible), 4) if eligible else None,
        "time_correct": time_correct,
        "time_accuracy": round(time_correct / len(eligible), 4) if eligible else None,
        "space_correct": space_correct,
        "space_accuracy": round(space_correct / len(eligible), 4) if eligible else None,
        "partial_breakdown": dict(partial_breakdown),
        "status_counts": dict(counts),
        "by_approach": {key: dict(value) for key, value in by_approach.items()},
        "by_language": {key: dict(value) for key, value in by_language.items()},
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode",
        choices=("legacy", "structural"),
        default="legacy",
        help="legacy includes existing semantic shortcuts; structural uses generic AST evidence only",
    )
    parser.add_argument(
        "--review-exclusions",
        help="Optional JSON review manifest; excluded records remain in the raw corpus and report.",
    )
    args = parser.parse_args()
    report = run(args.dataset, mode=args.mode, review_exclusions_path=args.review_exclusions)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "benchmark", "mode", "total", "raw_eligible", "eligible", "reviewed_excluded", "correct", "accuracy",
        "time_correct", "time_accuracy", "space_correct", "space_accuracy",
        "partial_breakdown", "status_counts",
    )}, indent=2))


if __name__ == "__main__":
    main()
