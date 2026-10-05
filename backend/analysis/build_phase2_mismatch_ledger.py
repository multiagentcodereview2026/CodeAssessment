"""Create a transparent audit ledger for every exact benchmark mismatch.

This tool is deliberately read-only: it does not alter the bank, dump, or
PostgreSQL.  Its classifications are triage labels based on structural
evidence, not claims that a target is wrong.  A human can therefore review
the complete failure set in deterministic clusters before adding new rules.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


MULTI_VARIABLE = re.compile(r"\b(?:m|n|v|e|w|k)\b", re.IGNORECASE)


def _has_multiple_dimensions(value: str) -> bool:
    """True only when an expression actually contains two+ dimensions."""
    # ``O(n)`` is not multi-variable merely because n is a valid dimension.
    variables = set(MULTI_VARIABLE.findall(value.lower()))
    return len(variables) >= 2


def _kind(record: dict[str, Any]) -> tuple[str, str, str]:
    """Return (cluster, triage_status, recommended_action)."""
    time_mismatch = not record.get("time_equivalent", record.get("target_time") == record.get("detected_time"))
    space_mismatch = not record.get("space_equivalent", record.get("target_space") == record.get("detected_space"))
    target = " ".join(str(record.get(key) or "") for key in ("target_time", "target_space"))
    detected = " ".join(str(record.get(key) or "") for key in ("detected_time", "detected_space"))
    signals = set(record.get("signals") or [])
    category = str(record.get("category") or "").lower()

    if "graph:" in " ".join(signals) or any(word in category for word in ("graph", "breadth", "depth", "tree", "union")):
        return "GRAPH_OR_DSU", "AST_RULE_CANDIDATE", "Review graph/DSU structural evidence and add a generic fixture if missing."
    if any("pattern:sliding-window" == signal or "pattern:monotonic-stack" == signal for signal in signals):
        return "AMORTIZED_LOOP", "AST_RULE_CANDIDATE", "Review amortized pointer/stack evidence; do not use raw loop depth."
    if any("library-sort" == signal or "pattern:comparison-sort" == signal for signal in signals):
        return "SORT_CONTEXT", "AST_RULE_CANDIDATE", "Determine whether sort is global, per-item, or over a bounded bucket."
    if _has_multiple_dimensions(target) or _has_multiple_dimensions(detected):
        return "MULTI_VARIABLE_OR_CONTEXT", "CONTEXT_OR_REFERENCE_REVIEW", "Check public constraints and whether the reference implementation matches the optimal target."
    if space_mismatch and not time_mismatch:
        return "SPACE_ONLY", "AST_SPACE_RULE_CANDIDATE", "Review allocation size: fixed-domain versus input-sized storage."
    if time_mismatch and not space_mismatch:
        return "TIME_ONLY", "AST_TIME_RULE_CANDIDATE", "Review loop composition, recursion, and library-operation context."
    if time_mismatch and space_mismatch:
        return "BOTH_TIME_AND_SPACE", "SOURCE_OR_TARGET_REVIEW", "Verify the reference source and target before changing a general rule."
    return "UNCLASSIFIED", "MANUAL_REVIEW", "Inspect source and add a fixture before changing behavior."


def build(report_path: Path, corpus_path: Path, output_path: Path, summary_path: Path) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    sources: dict[tuple[str, str], str] = {}
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for language, source in (row.get("reference_solution_sources") or {}).items():
            sources[(str(row.get("problem_id")), str(language).lower())] = source

    clusters: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    rows = []
    for record in report.get("records", []):
        if record.get("equivalent_to_target"):
            continue
        cluster, status, action = _kind(record)
        item = {
            "problem_id": record.get("problem_id"),
            "title": record.get("title"),
            "category": record.get("category"),
            "language": record.get("language"),
            "target_time": record.get("target_time"),
            "detected_time": record.get("detected_time"),
            "target_space": record.get("target_space"),
            "detected_space": record.get("detected_space"),
            "signals": record.get("signals") or [],
            "confidence": record.get("confidence"),
            "cluster": cluster,
            "triage_status": status,
            "recommended_action": action,
            "reference_source": sources.get((str(record.get("problem_id")), str(record.get("language")).lower()), ""),
        }
        rows.append(item)
        clusters[cluster] += 1
        statuses[status] += 1

    with output_path.open("w", encoding="utf-8") as stream:
        for item in rows:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")

    summary = {
        "report": str(report_path),
        "corpus": str(corpus_path),
        "total_records": len(report.get("records", [])),
        "exact_failures": len(rows),
        "clusters": dict(clusters.most_common()),
        "triage_statuses": dict(statuses.most_common()),
        "ledger": str(output_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.report, args.corpus, args.output, args.summary), indent=2))


if __name__ == "__main__":
    main()
