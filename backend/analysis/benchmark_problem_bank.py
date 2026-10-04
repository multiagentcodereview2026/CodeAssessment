"""Run a read-only AST benchmark over a representative problem-bank sample.

This benchmark never changes PostgreSQL or the dataset.  It samples problems
by tag/category, analyzes available starter/reference snippets, and records
coverage, confidence, and target agreement for manual review.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .static_analyzer import analyze_source


def _category(row: dict[str, Any]) -> str:
    if row.get("category"):
        return str(row["category"])
    tags = row.get("tags") or []
    return str(tags[0] if tags else "Uncategorized")


def _sample(rows: list[dict[str, Any]], per_category: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_category(row)].append(row)
    selected: list[dict[str, Any]] = []
    for category in sorted(grouped):
        selected.extend(sorted(grouped[category], key=lambda r: str(r.get("problem_id")))[:per_category])
    return selected


def _is_placeholder(source: str, language: str) -> bool:
    """Starter templates are not valid algorithm benchmarks."""
    text = source.strip().lower()
    if language in {"cpp", "c++", "c", "java"}:
        return "return 0;" in text and len(text.splitlines()) <= 12 and not any(
            token in text for token in ("for", "while", "sort", "push", "recursive")
        )
    if language in {"python", "py"}:
        return text in {"def main():\n    pass\n\nif __name__ == \"__main__\":\n    main()", "pass"}
    if language in {"javascript", "js", "typescript", "ts"}:
        return text in {"'use strict';", '"use strict";'}
    return not text


def _equivalent_complexity(left: str | None, right: str | None, category: str) -> bool:
    """Compare harmless notation differences without collapsing variables."""
    if not left or not right:
        return left == right
    def canonical_simple_product(value: str) -> str:
        raw = value.replace(" ", "").lower()
        match = re.fullmatch(r"o\(([^()]*)\)", raw)
        if not match:
            return raw
        inner = match.group(1).replace("*", "").replace("·", "")
        if inner in {"mn", "nm"}:
            return "o(mn)"
        if inner in {"ve", "ev"}:
            return "o(ve)"
        return raw
    if canonical_simple_product(left) == canonical_simple_product(right):
        return True
    a = left.replace(" ", "").replace("*", "").lower()
    b = right.replace(" ", "").replace("*", "").lower()
    if a == b:
        return True
    # Graph benchmarks commonly use n/e in code and V/E in problem metadata.
    if any(token in category.lower() for token in ("graph", "breadth", "depth", "tree")):
        aliases = {"v": "n", "e": "e"}
        for old, new in aliases.items():
            a = re.sub(rf"\b{old}\b", new, a)
            b = re.sub(rf"\b{old}\b", new, b)
    return a == b


def run(dataset: Path, per_category: int) -> dict[str, Any]:
    rows = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    sample = _sample(rows, per_category)
    report: dict[str, Any] = {
        "dataset": str(dataset),
        "dataset_rows": len(rows),
        "sample_rows": len(sample),
        "per_category": per_category,
        "categories": Counter(_category(row) for row in rows),
        "languages": Counter(),
        "analyzed": 0,
        "unavailable": 0,
        "target_agreement": 0,
        "target_disagreement": 0,
        "time_agreement": 0,
        "space_agreement": 0,
        "low_confidence": 0,
        "skipped_placeholders": 0,
        "missing_reference_source": 0,
        "records": [],
    }

    for row in sample:
        # Starter code is intentionally excluded.  Only an explicit complete
        # reference implementation is valid evidence for Phase J.
        starters = row.get("reference_solution_sources") or row.get("reference_solutions") or {}
        if not starters and isinstance(row.get("reference_solution_source"), str):
            language = str(row.get("reference_solution_language") or "cpp")
            starters = {language: row["reference_solution_source"]}
        if not starters:
            report["missing_reference_source"] += 1
            continue
        for language, source in starters.items():
            if not isinstance(source, str) or not source.strip():
                continue
            language = str(language).lower()
            if _is_placeholder(source, language):
                report["skipped_placeholders"] += 1
                continue
            result = analyze_source(source, language)
            report["languages"][language] += 1
            record = {
                "problem_id": row.get("problem_id"),
                "title": row.get("title"),
                "category": _category(row),
                "language": language,
                "target_time": row.get("target_time_complexity"),
                "target_space": row.get("target_space_complexity"),
                "detected_time": result.time_complexity,
                "detected_space": result.space_complexity,
                "status": result.status,
                "confidence": result.confidence,
                "method": result.method,
                "signals": list(result.signals),
            }
            report["records"].append(record)
            if result.status == "ANALYZED":
                report["analyzed"] += 1
            else:
                report["unavailable"] += 1
            if result.confidence < 0.8:
                report["low_confidence"] += 1
            equivalent = (
                _equivalent_complexity(result.time_complexity, row.get("target_time_complexity"), _category(row))
                and _equivalent_complexity(result.space_complexity, row.get("target_space_complexity"), _category(row))
            )
            time_equivalent = _equivalent_complexity(
                result.time_complexity, row.get("target_time_complexity"), _category(row)
            )
            space_equivalent = _equivalent_complexity(
                result.space_complexity, row.get("target_space_complexity"), _category(row)
            )
            if time_equivalent:
                report["time_agreement"] += 1
            if space_equivalent:
                report["space_agreement"] += 1
            record["equivalent_to_target"] = equivalent
            if equivalent:
                report["target_agreement"] += 1
            else:
                report["target_disagreement"] += 1

    report["categories"] = dict(report["categories"])
    report["languages"] = dict(report["languages"])
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--per-category", type=int, default=5)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.dataset, max(1, args.per_category))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "dataset_rows", "sample_rows", "analyzed", "unavailable",
        "time_agreement", "space_agreement", "target_agreement",
        "target_disagreement", "low_confidence", "missing_reference_source",
    )}, indent=2))


if __name__ == "__main__":
    main()
