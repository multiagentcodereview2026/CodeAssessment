"""Generate independent AI complexity predictions for offline evaluation.

This tool intentionally excludes all ground-truth/optimal fields from the AI
payload. It writes successful predictions separately from failures so the
comparison benchmark cannot mistake unavailable AI calls for wrong answers.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from .ai_complexity_reviewer import AIComplexityReview, build_review_payload
from .analyzer_service import analyze_submission_complexity, final_complexity_result


def _rows(path: str) -> list[dict[str, Any]]:
    file = Path(path)
    if not file.is_file():
        raise IsADirectoryError(f"Dataset must be a JSONL file: {file}")
    return [json.loads(line) for line in file.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _id(row: dict[str, Any], index: int) -> str:
    return str(row.get("solution_id") or row.get("problem_id") or index)


async def generate(dataset: str, output: str, errors_output: str) -> dict[str, Any]:
    # Import lazily so offline AST tests do not require Groq credentials.
    from agents.base import SystemMessage, HumanMessage, extract_clean_json, llm

    rows = _rows(dataset)
    predictions: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        solution_id = _id(row, index)
        source = str(row.get("source") or row.get("reference_source") or "")
        language = str(row.get("language") or "").lower().strip()
        try:
            if llm is None:
                raise RuntimeError("Groq model is unavailable; set GROQ_API_KEY")
            evidence = await analyze_submission_complexity(source, language)
            ast = final_complexity_result(evidence)
            ast_payload = {
                "time_complexity": ast.time_complexity,
                "space_complexity": ast.space_complexity,
                "confidence": ast.confidence,
                "signals": ast.signals,
                "explanation": ast.explanation,
            }
            payload = build_review_payload(source, language, ast_payload)
            response = await llm.ainvoke([
                SystemMessage(content=payload["instruction"]),
                HumanMessage(content=json.dumps({
                    "language": payload["language"],
                    "source_code": payload["source_code"],
                })),
            ])
            review = AIComplexityReview.model_validate_json(extract_clean_json(response.content))
            predictions.append({
                "solution_id": solution_id,
                "language": language,
                **review.model_dump(),
            })
        except Exception as exc:
            errors.append({
                "solution_id": solution_id,
                "language": language,
                "status": "AI_ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            })

    Path(output).write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions),
        encoding="utf-8",
    )
    Path(errors_output).write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in errors),
        encoding="utf-8",
    )
    return {
        "dataset_rows": len(rows),
        "predictions": len(predictions),
        "errors": len(errors),
        "predictions_output": output,
        "errors_output": errors_output,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--errors-output", required=True)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(generate(args.dataset, args.output, args.errors_output)), indent=2))


if __name__ == "__main__":
    main()
