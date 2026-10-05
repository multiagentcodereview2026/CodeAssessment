"""Split TIME_ONLY benchmark mismatches into safe review queues.

The result is a triage artifact, not an automatic decision about whether the
AST or the stored target is correct.  It makes the direction of disagreement
visible so fixes can be reviewed in coherent batches.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .complexity_normalizer import complexity_rank


def classify(item: dict[str, Any]) -> tuple[str, str]:
    target_rank = complexity_rank(item.get("target_time"))
    detected_rank = complexity_rank(item.get("detected_time"))
    signals = set(item.get("signals") or [])

    if target_rank is None or detected_rank is None:
        return "NOTATION_OR_MULTI_VARIABLE", "Normalize/inspect variables before changing AST behavior."
    if detected_rank > target_rank:
        if "loop-depth:2" in signals:
            return "POSSIBLE_AST_OVERCOUNT", "Check amortized/constant-bounded loops, then verify reference optimality."
        if "library-sort" in signals:
            return "SORT_CONTEXT_REVIEW", "Determine whether sorting is global or repeated per input item."
        return "REFERENCE_OR_AST_OVERCOUNT", "Verify source complexity with a fixture before changing generic rules."
    if detected_rank < target_rank:
        return "POSSIBLE_AST_UNDERCOUNT", "Check hidden library work, recursion, heap/BIT, or missing loop evidence."
    return "SAME_RANK_NOTATION_OR_VARIABLES", "Compare multi-variable expression semantics; do not force an ordinal match."


def build(ledger_path: Path, output_path: Path, summary_path: Path) -> dict[str, Any]:
    groups: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("cluster") != "TIME_ONLY":
            continue
        queue, action = classify(item)
        item["time_review_queue"] = queue
        item["time_review_action"] = action
        rows.append(item)
        groups[queue] += 1
    with output_path.open("w", encoding="utf-8") as stream:
        for item in rows:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
    summary = {"time_only_records": len(rows), "queues": dict(groups.most_common()), "output": str(output_path)}
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.ledger, args.output, args.summary), indent=2))


if __name__ == "__main__":
    main()
