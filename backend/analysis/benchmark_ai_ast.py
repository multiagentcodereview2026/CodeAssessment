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
from collections import Counter
from pathlib import Path
from typing import Any
from unittest.mock import patch

from .ai_complexity_reviewer import AIComplexityReview, AIReviewRateLimiter, ComplexityReviewCache
from .analyzer_service import analyze_static_complexity
from . import analyzer_service
from config.settings import settings


def _offline_combined(source, language, ast, prediction):
    """Replay the production orchestration against frozen provider evidence.

    Never call a real provider or substitute the lower-level review resolver
    for the production decision about retaining an AST formula.
    """
    async def frozen_provider(_payload):
        return AIComplexityReview.model_validate(prediction or {}).model_dump()
    with patch.object(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True), patch.multiple(
        analyzer_service, _invoke_complexity_reviewer=frozen_provider,
        _review_cache=ComplexityReviewCache(60), _review_limiter=AIReviewRateLimiter(1000, 1),
    ):
        return asyncio.run(analyzer_service.analyze_submission_complexity(source, language, static_result=ast)).final


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
    # REVIEW_REQUIRED and failed guesses are abstentions, not confident answers.
    eligible = [record for record in records if record[f"{prefix}_status"] in {"ANALYZED", "AVAILABLE", "AGREEMENT", "AI_FALLBACK", "AST_CONFIRMED"}
                and record.get(f"{prefix}_time") and record.get(f"{prefix}_space")]
    exact = sum(record[f"{prefix}_exact"] for record in eligible)
    return {
        "total": len(records),
        "eligible": len(eligible),
        "exact": exact,
        "accuracy": round(exact / len(eligible), 4) if eligible else None,
        "coverage": round(len(eligible) / len(records), 4) if records else None,
        "accuracy_all_rows": round(exact / len(records), 4) if records else None,
        "time_accuracy": round(sum(record[f"{prefix}_time_exact"] for record in eligible) / len(eligible), 4) if eligible else None,
        "space_accuracy": round(sum(record[f"{prefix}_space_exact"] for record in eligible) / len(eligible), 4) if eligible else None,
    }


def evaluate_rows(rows: list[dict[str, Any]], ai_rows: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    ai_rows = ai_rows or {}
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        source = str(_value(row, "source", "reference_source") or "")
        language = str(row.get("language", "")).lower().strip()
        solution_id = str(_value(row, "solution_id", "problem_id") or index)
        if not source.strip() or not language or not _value(row, "true_time_complexity", "snippet_time_complexity", "expected_time") or not _value(row, "true_space_complexity", "snippet_space_complexity", "expected_space"):
            raise ValueError("Each benchmark row needs source, language and code-specific time/space labels")
        # The AST comparator must be static-only. The production combined
        # workflow can invoke the model and must not be mislabeled an AST run.
        ast = analyze_static_complexity(source, language)
        ai = ai_rows.get(solution_id)
        hybrid = _offline_combined(source, language, ast, ai)
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
            "ai_status": str(ai.get("status") or "AVAILABLE").upper() if ai else "UNAVAILABLE",
            "ai_exact": _exact(ai.get("time_complexity"), ai.get("space_complexity"), row) if ai else False,
            "hybrid_time": hybrid.time_complexity if hybrid else None,
            "hybrid_space": hybrid.space_complexity if hybrid else None,
            "hybrid_confidence": hybrid.confidence if hybrid else None,
            "hybrid_status": hybrid.status if hybrid else "UNAVAILABLE",
            "hybrid_exact": _exact(hybrid.time_complexity, hybrid.space_complexity, row) if hybrid else False,
        }
        for prefix in ("ast", "ai", "hybrid"):
            record[f"{prefix}_time_exact"] = _canonical(record[f"{prefix}_time"]) == _canonical(_value(row, "true_time_complexity", "snippet_time_complexity", "expected_time"))
            record[f"{prefix}_space_exact"] = _canonical(record[f"{prefix}_space"]) == _canonical(_value(row, "true_space_complexity", "snippet_space_complexity", "expected_space"))
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
        "hybrid_scope": "production orchestration replay with frozen optional provider predictions; no live provider calls",
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
