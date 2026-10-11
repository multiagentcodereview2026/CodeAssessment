"""Offline benchmark for the experimental AI + Complexity AST reviewer.

The dataset must contain snippet-specific ground truth.  This runner never
uses a problem's optimal label and never changes the production workflow.
AI predictions are supplied as a separate JSONL recording so results are
reproducible and API limits cannot silently change the benchmark.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .ai_complexity_reviewer import AIComplexityReview, resolve_review
from .analyzer_service import analyze_submission_complexity, final_complexity_result


def _rows(path: str) -> list[dict[str, Any]]:
    file = Path(path)
    if not file.is_file():
        raise IsADirectoryError(f"Dataset must be a JSONL file: {file}")
    return [json.loads(line) for line in file.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if row.get(key) is not None:
            return row[key]
    return None


def _canonical(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).lower().replace(" ", "").replace("×", "*").replace("\\log", "log")


def _exact(actual_time: Any, actual_space: Any, row: dict[str, Any]) -> bool:
    return (
        _canonical(actual_time) == _canonical(_value(row, "true_time_complexity", "snippet_time_complexity", "expected_time"))
        and _canonical(actual_space) == _canonical(_value(row, "true_space_complexity", "snippet_space_complexity", "expected_space"))
    )


def _metrics(records: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    eligible = [record for record in records if record[f"{prefix}_status"] != "UNAVAILABLE"]
    exact = sum(record[f"{prefix}_exact"] for record in eligible)
    return {
        "total": len(records),
        "eligible": len(eligible),
        "exact": exact,
        "accuracy": round(exact / len(eligible), 4) if eligible else None,
    }


def evaluate_rows(rows: list[dict[str, Any]], ai_rows: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    ai_rows = ai_rows or {}
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        source = str(_value(row, "source", "reference_source") or "")
        language = str(row.get("language", "")).lower().strip()
        solution_id = str(_value(row, "solution_id", "problem_id") or index)
        evidence = asyncio.run(analyze_submission_complexity(source, language))
        ast = final_complexity_result(evidence)
        ast_dict = {
            "time_complexity": ast.time_complexity,
            "space_complexity": ast.space_complexity,
            "confidence": ast.confidence,
            "signals": ast.signals,
            "explanation": ast.explanation,
        }
        ai = ai_rows.get(solution_id)
        hybrid = resolve_review(ast_dict, AIComplexityReview.model_validate(ai)) if ai else None
        record = {
            "solution_id": solution_id,
            "problem_id": row.get("problem_id"),
            "language": language,
            "ast_time": ast.time_complexity,
            "ast_space": ast.space_complexity,
            "ast_confidence": ast.confidence,
            "ast_status": ast.status,
            "ast_exact": _exact(ast.time_complexity, ast.space_complexity, row),
            "ai_time": ai.get("time_complexity") if ai else None,
            "ai_space": ai.get("space_complexity") if ai else None,
            "ai_confidence": ai.get("confidence") if ai else None,
            "ai_status": "AVAILABLE" if ai else "UNAVAILABLE",
            "ai_exact": _exact(ai.get("time_complexity"), ai.get("space_complexity"), row) if ai else False,
            "hybrid_time": hybrid.time_complexity if hybrid else None,
            "hybrid_space": hybrid.space_complexity if hybrid else None,
            "hybrid_confidence": hybrid.confidence if hybrid else None,
            "hybrid_status": hybrid.status if hybrid else "UNAVAILABLE",
            "hybrid_exact": _exact(hybrid.time_complexity, hybrid.space_complexity, row) if hybrid else False,
        }
        records.append(record)

    by_language: dict[str, Any] = {}
    for language in sorted({record["language"] for record in records}):
        subset = [record for record in records if record["language"] == language]
        by_language[language] = {
            "ast": _metrics(subset, "ast"),
            "ai": _metrics(subset, "ai"),
            "hybrid": _metrics(subset, "hybrid"),
        }
    return {
        "benchmark": "ai_ast_complexity_comparison",
        "total": len(records),
        "ast": _metrics(records, "ast"),
        "ai": _metrics(records, "ai"),
        "hybrid": _metrics(records, "hybrid"),
        "hybrid_status_counts": dict(Counter(record["hybrid_status"] for record in records)),
        "by_language": by_language,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--ai-predictions", help="Optional JSONL recording keyed by solution_id")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    ai_rows = {}
    if args.ai_predictions:
        ai_rows = {
            str(_value(row, "solution_id", "problem_id")): row
            for row in _rows(args.ai_predictions)
        }
    report = evaluate_rows(_rows(args.dataset), ai_rows)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
