"""Enrich a normalized Newfacade corpus with validated complexity metadata.

This is an offline dataset-preparation tool, not a request-serving component.
It asks a configured Groq model to select a target *worst-case* time complexity
and target *auxiliary* space complexity from a closed set. Each answer is
stored with provenance and confidence, and uncertain responses are marked for
human review rather than guessed.

It never sends testcase data to the model. In particular, hidden inputs and
expected outputs stay in the local corpus and PostgreSQL database.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
except ImportError:  # The backend image installs python-dotenv; keep metadata helpers importable without it.
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        return False


COMPLEXITY_LEVELS = (
    "O(1)",
    "O(log n)",
    "O(n)",
    "O(n log n)",
    "O(n^2)",
    "O(n^3)",
    "O(2^n)",
    "O(n!)",
)


class ComplexityAssessment(BaseModel):
    target_time_complexity: str | None = None
    target_space_complexity: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    reasoning: str = Field(default="Model returned no reasoning.", min_length=1, max_length=700)
    needs_review: bool = False


SYSTEM_PROMPT = """You are curating complexity metadata for programming problems.
Return one JSON object only. Choose the best generally expected worst-case time
complexity and auxiliary-space complexity for a high-quality accepted solution.
Auxiliary space excludes the input and required output. Choose values only from:
O(1), O(log n), O(n), O(n log n), O(n^2), O(n^3), O(2^n), O(n!).
If the prompt is ambiguous or supports materially different valid targets, set
both complexity fields to null and needs_review to true. Do not use testcase
data; you receive only public problem metadata. Do not assume an unstated
constraint. Keep reasoning concise and describe the intended algorithm.
Use exactly these JSON keys and no others:
{"target_time_complexity":"O(n)","target_space_complexity":"O(1)",
"confidence":0.90,"reasoning":"One scan with constant state.",
"needs_review":false}
"""


def clean_text(value: Any, maximum: int) -> str:
    text = str(value or "").replace("\x00", " ").strip()
    return text[:maximum]


def prompt_sections(row: dict[str, Any]) -> tuple[str, list[str]]:
    """Remove examples and platform boilerplate to conserve model tokens."""
    description = clean_text(row.get("description"), 20_000)
    lower = description.lower()
    platform_at = lower.find("platform input/output format")
    if platform_at >= 0:
        description = description[:platform_at].rstrip()
        lower = description.lower()

    constraints = [clean_text(item, 500) for item in row.get("constraints") or [] if clean_text(item, 500)]
    constraints_at = lower.rfind("constraints:")
    if not constraints and constraints_at >= 0:
        constraints = [
            line.strip(" \t-*•")
            for line in description[constraints_at + len("constraints:"):].splitlines()
            if line.strip(" \t-*•")
        ][:30]

    # Examples rarely affect asymptotic complexity and dominate prompt size.
    statement = description[:constraints_at].rstrip() if constraints_at >= 0 else description
    example_markers = ("\nexample 1:", "\nexample:")
    statement_lower = statement.lower()
    positions = [statement_lower.find(marker) for marker in example_markers]
    positions = [position for position in positions if position >= 0]
    if positions:
        statement = statement[:min(positions)].rstrip()
    return clean_text(statement, 4_000), constraints


def model_payload(row: dict[str, Any]) -> dict[str, Any]:
    """Send metadata only; do not expose public or hidden testcase payloads."""
    statement, constraints = prompt_sections(row)
    return {
        "problem_id": clean_text(row.get("problem_id"), 140),
        "title": clean_text(row.get("title"), 300),
        "difficulty": clean_text(row.get("difficulty"), 30),
        "tags": [clean_text(tag, 80) for tag in row.get("tags") or []][:20],
        "description": statement,
        "constraints": constraints,
        "parameter_schema": row.get("parameter_schema") or {},
        "return_schema": row.get("return_schema") or {},
    }


def build_model(api_key: str, model_name: str):
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_groq import ChatGroq
    except ImportError as exc:
        raise RuntimeError("Install backend requirements before running this tool.") from exc

    model = ChatGroq(
        model_name=model_name,
        temperature=0,
        max_tokens=250,
        groq_api_key=api_key,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    def assess(row: dict[str, Any]) -> ComplexityAssessment:
        response = model.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(model_payload(row), ensure_ascii=False)),
        ])
        return parse_assessment(response.content)

    return assess


def parse_assessment(content: Any) -> ComplexityAssessment:
    """Accept valid JSON plus common provider aliases/content-block shapes."""
    if isinstance(content, dict):
        data = content
    else:
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    text_parts.append(block["text"])
                elif isinstance(block, str):
                    text_parts.append(block)
            text = "\n".join(text_parts)
        else:
            text = str(content or "")
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("Model response did not contain a JSON object.")
        data = json.loads(text[start:end + 1])

    if isinstance(data.get("assessment"), dict):
        data = data["assessment"]

    def first(*keys: str) -> Any:
        return next((data[key] for key in keys if key in data), None)

    confidence = first("confidence", "complexity_confidence")
    if isinstance(confidence, str):
        confidence = confidence.strip()
        confidence = float(confidence[:-1]) / 100 if confidence.endswith("%") else float(confidence)
    if confidence is None:
        confidence = 0.5

    needs_review = first("needs_review", "complexity_needs_review")
    if isinstance(needs_review, str):
        needs_review = needs_review.strip().lower() in {"true", "1", "yes"}

    return ComplexityAssessment.model_validate({
        "target_time_complexity": first(
            "target_time_complexity", "optimal_time_complexity", "time_complexity", "tc"
        ),
        "target_space_complexity": first(
            "target_space_complexity", "optimal_space_complexity", "space_complexity", "sc"
        ),
        "confidence": confidence,
        "reasoning": first("reasoning", "reason", "explanation") or "Model returned no reasoning.",
        "needs_review": bool(needs_review),
    })


def normalise_result(result: ComplexityAssessment) -> dict[str, Any]:
    aliases = {value.lower().replace(" ", ""): value for value in COMPLEXITY_LEVELS}
    time_raw = str(result.target_time_complexity or "").strip()
    space_raw = str(result.target_space_complexity or "").strip()
    time_value = aliases.get(time_raw.lower().replace(" ", ""))
    space_value = aliases.get(space_raw.lower().replace(" ", ""))
    valid = (
        not result.needs_review
        and time_value in COMPLEXITY_LEVELS
        and space_value in COMPLEXITY_LEVELS
    )
    return {
        "target_time_complexity": time_value if valid else None,
        "target_space_complexity": space_value if valid else None,
        "complexity_source": "groq-llm-validated" if valid else "groq-llm-needs-review",
        "complexity_confidence": result.confidence if valid else None,
        "complexity_reasoning": result.reasoning,
        "complexity_needs_review": not valid,
    }


def read_existing(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    existing: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                existing[str(row["problem_id"])] = row
    return existing


def enrich(
    source_path: Path,
    output_path: Path,
    api_key: str,
    model_name: str,
    delay_seconds: float,
    limit: int | None,
) -> None:
    if not source_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {source_path}")
    if source_path.resolve() == output_path.resolve():
        raise ValueError("Use a different output path; never overwrite the source corpus.")

    assess = build_model(api_key, model_name)
    existing = read_existing(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    processed = 0
    halted_reason: str | None = None
    with source_path.open("r", encoding="utf-8") as source:
        total_records = sum(1 for line in source if line.strip())
    print(json.dumps({
        "status": "starting",
        "problems": total_records,
        "resumable_records_found": len(existing),
        "model": model_name,
    }), flush=True)

    with source_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as destination:
        current = 0
        for line in source:
            if not line.strip():
                continue
            current += 1
            row = json.loads(line)
            problem_id = str(row["problem_id"])
            prior = existing.get(problem_id)

            if prior and prior.get("complexity_source") in {
                "groq-llm-validated",
                "groq-llm-needs-review",
            }:
                enriched = prior
                counts["resumed"] += 1
            elif halted_reason:
                enriched = dict(row)
                enriched.update({
                    "target_time_complexity": None,
                    "target_space_complexity": None,
                    "complexity_source": "not-processed",
                    "complexity_confidence": None,
                    "complexity_reasoning": f"Run paused: {halted_reason}",
                    "complexity_needs_review": True,
                })
                counts["not_processed"] += 1
            elif limit is not None and processed >= limit:
                enriched = dict(row)
                enriched.update({
                    "target_time_complexity": None,
                    "target_space_complexity": None,
                    "complexity_source": "not-processed",
                    "complexity_confidence": None,
                    "complexity_reasoning": None,
                    "complexity_needs_review": True,
                })
                counts["not_processed"] += 1
            else:
                try:
                    enriched = dict(row)
                    enriched.update(normalise_result(assess(row)))
                    counts["validated" if not enriched["complexity_needs_review"] else "needs_review"] += 1
                except Exception as exc:
                    error_name = type(exc).__name__
                    if error_name == "RateLimitError":
                        halted_reason = "Groq rate limit reached; rerun later to resume."
                    enriched = dict(row)
                    enriched.update({
                        "target_time_complexity": None,
                        "target_space_complexity": None,
                        "complexity_source": "generation-error",
                        "complexity_confidence": None,
                        "complexity_reasoning": f"Generation error: {error_name}: {clean_text(exc, 400)}",
                        "complexity_needs_review": True,
                    })
                    counts["generation_error"] += 1
                processed += 1
                if delay_seconds:
                    time.sleep(delay_seconds)

            destination.write(json.dumps(enriched, ensure_ascii=False) + "\n")
            if current % 10 == 0 or current == total_records:
                destination.flush()
                print(json.dumps({
                    "status": "running",
                    "completed": current,
                    "total": total_records,
                    "validated": counts["validated"],
                    "needs_review": counts["needs_review"],
                    "generation_error": counts["generation_error"],
                    "resumed": counts["resumed"],
                }), flush=True)

    report = {
        "source": str(source_path),
        "output": str(output_path),
        "model": model_name,
        "records_processed_this_run": processed,
        "counts": dict(counts),
        "allowed_complexities": list(COMPLEXITY_LEVELS),
        "halted_reason": halted_reason,
    }
    output_path.with_suffix(".complexity.report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add Groq-generated target TC/SC metadata to a normalized corpus.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    parser.add_argument("--limit", type=int)
    arguments = parser.parse_args()
    # Allows the normal backend/.env location while keeping secrets out of Git.
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("GROQ_API_KEY is required. Put it in backend/.env or set it in the shell; never commit it.")
    enrich(
        source_path=Path(arguments.source),
        output_path=Path(arguments.output),
        api_key=api_key,
        model_name=arguments.model,
        delay_seconds=max(0.0, arguments.delay_seconds),
        limit=arguments.limit,
    )
