"""CLI proof harness for the AST-plus-AI complexity decision policy.

The command never contacts an AI provider.  Supply ``--ai-json`` to simulate
the provider's structured response, and optionally ``--ast-json`` to exercise
an uncertain or intentionally incorrect AST outcome.  This lets the policy be
verified before any submitted source is sent outside the application.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    from .ai_complexity_reviewer import AIComplexityReview, resolve_review
    from .confidence_policy import apply_confidence_policy
    from .models import ComplexityAnalysis
    from .static_analyzer import analyze_source
except ImportError:  # Supports direct execution from PowerShell as well.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from analysis.ai_complexity_reviewer import AIComplexityReview, resolve_review
    from analysis.confidence_policy import apply_confidence_policy
    from analysis.models import ComplexityAnalysis
    from analysis.static_analyzer import analyze_source


async def verify_with_groq(source_code: str, language: str) -> dict[str, Any]:
    """Run the same optional hybrid path used by a website submission."""
    from config.settings import settings
    from analysis.analyzer_service import analyze_submission_complexity

    previous_enabled = settings.COMPLEXITY_AI_REVIEW_ENABLED
    settings.COMPLEXITY_AI_REVIEW_ENABLED = True
    try:
        evidence = await analyze_submission_complexity(source_code, language)
    finally:
        settings.COMPLEXITY_AI_REVIEW_ENABLED = previous_enabled

    final = evidence.final or ComplexityAnalysis(status="REVIEW_REQUIRED")
    route = (
        "AI_CORROBORATED" if final.method == "ast+ai-corroborated"
        else "AI_FALLBACK" if final.method == "ai-fallback"
        else "AST_DIRECT" if final.status == "ANALYZED"
        else "REVIEW_REQUIRED"
    )
    return {
        "route": route,
        "ast": asdict(evidence.static) if evidence.static else None,
        "ai": evidence.ai_review,
        "final": asdict(final),
        "external_ai_called": evidence.ai_review is not None,
    }


def _read_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return payload


def _analysis_from_payload(payload: dict[str, Any]) -> ComplexityAnalysis:
    return ComplexityAnalysis(
        time_complexity=payload.get("time_complexity"),
        space_complexity=payload.get("space_complexity"),
        confidence=float(payload.get("confidence", 0.0)),
        method=str(payload.get("method", "fixture")),
        status=str(payload.get("status", "ANALYZED")),
        signals=list(payload.get("signals") or []),
        explanation=str(payload.get("explanation", "")),
    )


def verify(
    source_code: str,
    language: str,
    *,
    ast_fixture: dict[str, Any] | None = None,
    ai_fixture: dict[str, Any] | None = None,
    direct_confidence: float = 0.90,
    ai_minimum_confidence: float = 0.70,
) -> dict[str, Any]:
    ast = (
        _analysis_from_payload(ast_fixture)
        if ast_fixture is not None
        else analyze_source(source_code, language)
    )
    ast = apply_confidence_policy(ast) or ComplexityAnalysis()
    ast_payload = asdict(ast)

    if ast.confidence >= direct_confidence and ast.status == "ANALYZED":
        return {
            "route": "AST_DIRECT",
            "ast": ast_payload,
            "ai": None,
            "final": ast_payload,
            "external_ai_called": False,
        }

    if ai_fixture is None:
        return {
            "route": "AI_REVIEW_REQUIRED",
            "ast": ast_payload,
            "ai": None,
            "final": {
                **ast_payload,
                "status": "REVIEW_REQUIRED",
                "method": "ast+ai-review",
            },
            "external_ai_called": False,
        }

    ai = AIComplexityReview.model_validate(ai_fixture)
    review = resolve_review(
        ast_payload,
        ai,
        minimum_confidence=ai_minimum_confidence,
    )
    final_status = "ANALYZED" if review.status in {"AGREEMENT", "AI_FALLBACK"} else "REVIEW_REQUIRED"
    final = {
        **ast_payload,
        "time_complexity": review.time_complexity,
        "space_complexity": review.space_complexity,
        "confidence": review.confidence,
        "status": final_status,
        "method": (
            "ast+ai-corroborated" if review.status == "AGREEMENT"
            else "ai-fallback" if review.status == "AI_FALLBACK"
            else "ast+ai-review"
        ),
        "signals": [*ast.signals, f"ai-review:{review.status.lower()}"],
        "explanation": (
            "AST and AI corroborated each other." if review.status == "AGREEMENT"
            else "AI supplied a higher-confidence, code-only fallback estimate." if review.status == "AI_FALLBACK"
            else "AI did not corroborate AST; review is required."
        ),
    }
    return {
        "route": (
            "AI_CORROBORATED" if review.status == "AGREEMENT"
            else "AI_FALLBACK" if review.status == "AI_FALLBACK"
            else "REVIEW_REQUIRED"
        ),
        "ast": ast_payload,
        "ai": ai.model_dump(),
        "review": asdict(review),
        "final": final,
        "external_ai_called": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify hybrid AST/AI complexity decisions locally.")
    parser.add_argument("--file", required=True, help="Path to the submitted source file.")
    parser.add_argument("--language", required=True, help="Source language, such as cpp or python.")
    parser.add_argument("--ast-json", help="Optional JSON fixture that replaces the live AST result.")
    parser.add_argument("--ai-json", help="Optional JSON fixture that simulates AI structured output.")
    parser.add_argument("--direct-confidence", type=float, default=0.90)
    parser.add_argument("--ai-minimum-confidence", type=float, default=0.70)
    parser.add_argument(
        "--use-groq",
        action="store_true",
        help="Send this one source file to the configured Groq reviewer when AST confidence is below the direct threshold.",
    )
    args = parser.parse_args()

    source_code = Path(args.file).read_text(encoding="utf-8")
    if args.use_groq:
        if args.ast_json or args.ai_json:
            parser.error("--use-groq cannot be combined with fixture JSON files")
        result = asyncio.run(verify_with_groq(source_code, args.language))
    else:
        result = verify(
            source_code,
            args.language,
            ast_fixture=_read_json(args.ast_json) if args.ast_json else None,
            ai_fixture=_read_json(args.ai_json) if args.ai_json else None,
            direct_confidence=args.direct_confidence,
            ai_minimum_confidence=args.ai_minimum_confidence,
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
