"""Release synthetic fixtures and normalized AI proposals, never raw reviews.

Only allowlisted fields are exported. Model rationales, returned source copies,
instructor fields, and private path names are deliberately excluded.
"""
import argparse
import hashlib
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.strip().startswith("```")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--review-a", required=True, type=Path)
    parser.add_argument("--review-b", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original = rows(args.original)
    indexed = {row["solution_id"]: row for row in original}
    if len(indexed) != 20 or len(original) != 20:
        raise ValueError("This release expects the canonical twenty-snippet pilot")
    exports = {}
    for alias, path in (("a", args.review_a), ("b", args.review_b)):
        proposals = rows(path)
        if len(proposals) != 20 or {row["solution_id"] for row in proposals} != set(indexed):
            raise ValueError("Proposal identifiers must match the canonical pilot")
        released = []
        for row in proposals:
            if row.get("reviewer_type") != "ai_assisted" or row.get("ground_truth_source") != "ai_assisted_unverified":
                raise ValueError("AI provenance must be retained")
            base = indexed[row["solution_id"]]
            time = row.get("time_complexity") or row.get("proposed_time_complexity")
            space = row.get("auxiliary_space") or row.get("proposed_auxiliary_space")
            if not isinstance(time, str) or not isinstance(space, str):
                raise ValueError("Missing proposed label")
            released.append({"solution_id": base["solution_id"], "problem_id": base["problem_id"],
                             "language": base["language"], "source_sha256": base["source_sha256"],
                             "time_complexity": time, "auxiliary_space": space,
                             "reviewer_id": "proposal-" + alias.upper(), "reviewer_type": "ai_assisted",
                             "ground_truth_source": "ai_assisted_unverified"})
        exports["proposals-" + alias + ".jsonl"] = released
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "pilot.jsonl").write_bytes(args.original.read_bytes())
    for name, released in exports.items():
        (args.output / name).write_text("".join(json.dumps(row) + "\n" for row in released), encoding="utf-8", newline="\n")
    metadata = {"release": "paper-artifacts-20261030", "snippets": 20, "problem_groups": 2,
                "languages": sorted({row["language"] for row in original}),
                "human_validated": False, "ground_truth_source": "ai_assisted_unverified",
                "application_commit": "d4cdb86aa95d99f544d5e3253bf116eeeac87b24",
                "experiment_commit": "7ddc4aa08e4ff3a7a0d4c2701c44fe41121042f0",
                "input_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in
                                 (("canonical_original", args.original), ("original_proposal_a", args.review_a), ("original_proposal_b", args.review_b))},
                "preprocessing": "Canonical source and problem groups retained. Only label proposals are released, associated by canonical solution ID. Proposal aliases are not authenticated identities. Raw review prose, duplicated returned source, unsupported hash assertions and instructor fields are not published.",
                "limits": "Synthetic pilot with two problem groups; labels are AI proposals, not independent expert ground truth. No application accuracy, instructor-grade validation, or learning-benefit claim."}
    (args.output / "provenance.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
