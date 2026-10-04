"""Build a review queue for Phase J reference implementations.

The normalized problem bank contains optimal TC/SC targets, while the raw
reference snippets are not guaranteed to be optimal.  This utility never
changes PostgreSQL or the main dataset; it joins the benchmark report with
the source corpus and emits only records requiring reference review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build(corpus: Path, report: Path, output: Path) -> dict[str, int]:
    rows = {
        row["problem_id"]: row
        for line in corpus.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for row in [json.loads(line)]
    }
    data = json.loads(report.read_text(encoding="utf-8"))
    count = 0
    by_reason: dict[str, int] = {}
    with output.open("w", encoding="utf-8") as stream:
        for record in data.get("records", []):
            if record.get("equivalent_to_target"):
                continue
            source_row = rows.get(record.get("problem_id"), {})
            source_map = source_row.get("reference_solution_sources") or {}
            language = record.get("language") or next(iter(source_map), "")
            item = {
                "problem_id": record.get("problem_id"),
                "title": record.get("title"),
                "category": record.get("category"),
                "language": language,
                "target_time_complexity": record.get("target_time"),
                "target_space_complexity": record.get("target_space"),
                "detected_time_complexity": record.get("detected_time"),
                "detected_space_complexity": record.get("detected_space"),
                "reference_source": source_map.get(language, ""),
                "review_status": "REPLACE_OR_VERIFY_REFERENCE",
            }
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1
            reason = "both" if (
                record.get("target_time") != record.get("detected_time")
                and record.get("target_space") != record.get("detected_space")
            ) else "time" if record.get("target_time") != record.get("detected_time") else "space"
            by_reason[reason] = by_reason.get(reason, 0) + 1
    return {"review_records": count, **{f"{k}_mismatch": v for k, v in by_reason.items()}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.corpus, args.report, args.output), indent=2))


if __name__ == "__main__":
    main()
