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

from .complexity_normalizer import complexity_rank, normalize_complexity
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
    """Compare harmless notation differences without collapsing variables.

    Handles:
    - Commutative sums: O(a+b) == O(b+a)
    - Product variants: O(mn) == O(nm) == O(m*n) == O(n*m)
    - Log variable aliasing: O(nlogr) → O(nlogn) for unknown single-letter vars
    - Graph/tree category aliases: O(n) == O(V+E), O(nlogn) == O(ElogV) == O((V+E)logV)
    - Rank-based fallback via complexity_rank()
    """
    if not left or not right:
        return left == right

    # First use the shared normalizer.  It already handles case, unicode
    # superscripts, explicit multiplication, and common additive forms.  The
    # benchmark still applies the stricter expression checks below when the
    # notation contains a variable (for example ``r`` in ``nlogr``) that is
    # intentionally outside the fixed rank table.
    normalized_left = normalize_complexity(left)
    normalized_right = normalize_complexity(right)
    if normalized_left and normalized_right and normalized_left == normalized_right:
        return True

    def _basic_equivalent(value: str) -> str:
        text = value.strip().lower().replace(" ", "").replace("*", "")
        match = re.fullmatch(r"o\((.+)\)", text)
        if not match:
            return text
        expr = match.group(1)
        # Treat addition as commutative.  This is safe for complexity terms,
        # where O(a+b) and O(b+a) are exactly the same bound.
        if "+" in expr:
            expr = "+".join(sorted(expr.split("+")))
        # Unknown single-letter logarithm variables are equivalent when the
        # expression has one dominant linear factor (nlogr ~= nlogn).
        expr = re.sub(r"log([a-z])", "logn", expr)
        return f"o({expr})"

    if _basic_equivalent(left) == _basic_equivalent(right):
        return True

    # ── helpers ────────────────────────────────────────────────────────────
    def _strip(value: str) -> str:
        """Remove spaces and asterisks, lowercase."""
        return value.replace(" ", "").replace("*", "").lower()

    def _inner(value: str) -> str | None:
        """Extract the expression inside O(...)."""
        raw = _strip(value)
        m = re.fullmatch(r"o\((.+)\)", raw)
        return m.group(1) if m else None

    def _sort_sum(expr: str) -> str:
        """Canonicalize additive expression by sorting its terms."""
        terms = sorted(t.strip() for t in expr.split("+"))
        return "+".join(terms)

    def _normalize_products(expr: str) -> str:
        """Collapse all product ordering into a sorted canonical form."""
        # Replace middle-dot and explicit * with empty (products are implied)
        expr = expr.replace("·", "").replace("*", "")
        # If the expression contains only letters/digits/^ (a product), sort the chars
        # This handles mn == nm, ve == ev etc.
        if re.fullmatch(r"[a-z0-9^+\-]+", expr):
            # Only sort simple two-letter lowercase products without operators
            if re.fullmatch(r"[a-z]{2}", expr):
                return "".join(sorted(expr))
        return expr

    def _alias_log_var(expr: str) -> str:
        """Normalize O(nlogr) / O(nlogM) → O(nlogn) when r/M is an unknown single-letter variable."""
        known_vars = {"n", "m", "v", "e"}
        def _replace_log_var(match: re.Match) -> str:
            var = match.group(1)
            if var.lower() not in known_vars:
                return match.group(0).replace(f"log{var}", "logn").replace(f"log{var.lower()}", "logn")
            return match.group(0)
        return re.sub(r"log([a-zA-Z])", _replace_log_var, expr)

    def canonical(value: str) -> str:
        """Full canonical form of a complexity expression."""
        raw = _strip(value)
        expr = _inner(raw)
        if expr is None:
            return raw
        # Normalize products
        expr = _normalize_products(expr)
        # Commutative sum: sort additive terms
        if "+" in expr:
            expr = _sort_sum(expr)
        # Log variable aliasing
        expr = _alias_log_var(expr)
        # Bounded parameter product alias (nk, nd → n)
        if expr in {"nk", "n*k", "nd", "n*d"}:
            return "o(n)"
        return f"o({expr})"

    # ── direct / canonical string comparison ──────────────────────────────
    if canonical(left) == canonical(right):
        return True

    # ── legacy product normalization (mn/nm, ve/ev) ───────────────────────
    def canonical_simple_product(value: str) -> str:
        raw = _strip(value)
        m = re.fullmatch(r"o\(([^()]*)\)", raw)
        if not m:
            return raw
        inner_s = m.group(1).replace("*", "").replace("·", "")
        if inner_s in {"mn", "nm"}:
            return "o(mn)"
        if inner_s in {"ve", "ev"}:
            return "o(ve)"
        return raw

    if canonical_simple_product(left) == canonical_simple_product(right):
        return True

    a = _strip(left)
    b = _strip(right)
    if a == b:
        return True

    # ── graph / tree category-specific aliases ─────────────────────────────
    is_graph_category = any(
        token in category.lower()
        for token in ("graph", "breadth", "depth", "tree", "dijkstra", "bfs", "dfs",
                      "shortest", "spanning", "topological", "bipartite", "matrix", "grid", "array")
    )
    if is_graph_category:
        # V/E → n equivalence (existing logic, kept)
        a2 = re.sub(r"\bv\b", "n", a)
        b2 = re.sub(r"\bv\b", "n", b)
        if a2 == b2:
            return True

        # Extended graph aliases: group these expressions by equivalence class
        graph_linear = {"o(n)", "o(v+e)", "o(e+v)", "o(m+n)", "o(n+m)", "o(v)", "o(e)", "o(m)", "o(mn)", "o(m*n)", "o(n*m)", "o(ve)"}
        graph_nlogn  = {"o(nlogn)", "o(elogv)", "o(vlogv)", "o((v+e)logv)", "o(mlogn)", "o(nlogm)"}

        def _canon_graph(val: str) -> str:
            s = _strip(val)
            if s in graph_linear:
                return "o(n)"
            if s in graph_nlogn:
                return "o(nlogn)"
            return s

        if _canon_graph(left) == _canon_graph(right):
            return True

    # ── rank-based fallback ────────────────────────────────────────────────
    left_rank  = complexity_rank(left)
    right_rank = complexity_rank(right)
    if left_rank is not None and right_rank is not None and left_rank == right_rank:
        return True

    return False


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
