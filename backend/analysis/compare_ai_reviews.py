"""Compare AI-assisted reviews against the canonical pilot without creating human labels."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path


def read_rows(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    return [json.loads(line) for line in text.splitlines() if line.strip() and not line.strip().startswith("```")]


def canonical(value):
    return str(value or "").lower().replace(" ", "").replace("²", "^2").replace("³", "^3")


def labels(row):
    time = row.get("time_complexity") or row.get("proposed_time_complexity")
    space = row.get("auxiliary_space") or row.get("proposed_auxiliary_space")
    if not isinstance(time, str) or not time.strip() or not isinstance(space, str) or not space.strip():
        raise ValueError(f"Missing proposed complexity labels: {row.get('solution_id')}")
    return time, space


def index_rows(rows, description):
    indexed = {}
    for row in rows:
        sid = row.get("solution_id")
        if not isinstance(sid, str) or not sid or sid in indexed:
            raise ValueError(f"Missing or duplicate solution ID in {description}: {sid}")
        indexed[sid] = row
    if not indexed:
        raise ValueError(f"Empty dataset: {description}")
    return indexed


def compare(original, review_a, review_b, analyze=False):
    originals = index_rows(original, "original pack")
    reviews = [index_rows(review_a, "review A"), index_rows(review_b, "review B")]
    metadata = []
    for index, review in enumerate(reviews):
        if set(review) != set(originals):
            raise ValueError(f"Review {index + 1} has missing or unknown solution IDs")
        audit = {"review": index + 1, "reviewer_ids_self_reported": sorted({str(r.get("reviewer_id") or "model_identity_unavailable") for r in review.values()}),
                 "source_validation": Counter(), "changed_problem_group_ids": [], "hash_claim_warnings": []}
        for sid, row in review.items():
            base = originals[sid]
            if row.get("reviewer_type") != "ai_assisted" or row.get("ground_truth_source") != "ai_assisted_unverified":
                raise ValueError("These AI outputs must retain their AI-assisted, unverified provenance")
            if row.get("language", "").lower() != base["language"]:
                raise ValueError(f"Language differs from original: {sid}")
            labels(row)
            source = row.get("source")
            if source is None:
                audit["source_validation"]["id_link_only_source_not_returned"] += 1
            elif source == base["source"]:
                audit["source_validation"]["byte_identical"] += 1
            elif source.rstrip("\r\n") == base["source"].rstrip("\r\n"):
                audit["source_validation"]["ending_newlines_only"] += 1
            else:
                raise ValueError(f"Returned source differs from original beyond ending newlines: {sid}")
            declared = row.get("source_sha256_declared")
            if source is not None and declared and declared != hashlib.sha256(source.encode()).hexdigest():
                audit["hash_claim_warnings"].append({"solution_id": sid, "declared_matches_canonical_original": declared == hashlib.sha256(base["source"].encode()).hexdigest()})
            if row.get("problem_id") is not None and row["problem_id"] != base["problem_id"]:
                audit["changed_problem_group_ids"].append(sid)
        audit["source_validation"] = dict(audit["source_validation"])
        metadata.append(audit)
    cases, consensus = [], []
    for sid, base in originals.items():
        a, b = reviews[0][sid], reviews[1][sid]
        ta, sa = labels(a)
        tb, sb = labels(b)
        time_agrees, space_agrees = canonical(ta) == canonical(tb), canonical(sa) == canonical(sb)
        item = {"solution_id": sid, "problem_id": base["problem_id"], "language": base["language"],
                "source_sha256": hashlib.sha256(base["source"].encode()).hexdigest(),
                "review_a_time": ta, "review_b_time": tb, "review_a_space": sa, "review_b_space": sb,
                "time_agrees": time_agrees, "space_agrees": space_agrees, "joint_agrees": time_agrees and space_agrees}
        if item["joint_agrees"]:
            consensus.append({**base, "snippet_time_complexity": ta, "snippet_space_complexity": sa,
                              "reviewer_type": "ai_assisted", "ground_truth_source": "ai_assisted_unverified",
                              "reviewer_ids_self_reported": [a.get("reviewer_id"), b.get("reviewer_id")]})
        if analyze:
            from analysis.analyzer_service import analyze_static_complexity
            estimate = analyze_static_complexity(base["source"], base["language"])
            eligible = item["joint_agrees"] and estimate.status == "ANALYZED" and bool(estimate.time_complexity and estimate.space_complexity)
            item["platform"] = {"time": estimate.time_complexity, "space": estimate.space_complexity,
                "status": estimate.status, "heuristic_confidence": estimate.confidence, "eligible": eligible,
                "time_matches_consensus": eligible and canonical(estimate.time_complexity) == canonical(ta),
                "space_matches_consensus": eligible and canonical(estimate.space_complexity) == canonical(sa)}
            item["platform"]["joint_matches_consensus"] = item["platform"]["time_matches_consensus"] and item["platform"]["space_matches_consensus"]
        cases.append(item)
    count = len(cases)
    report = {"kind": "ai_assisted_pilot_agreement", "human_validated": False, "rows": count,
              "original_problem_groups": len({r["problem_id"] for r in original}), "review_metadata": metadata,
              "model_agreement": {dimension: sum(r[dimension] for r in cases) for dimension in ("time_agrees", "space_agrees", "joint_agrees")},
              "cases": cases, "limitations": ["Model identifiers are self-reported; identities, prompts and independence were not verified.",
                  f"Agreement is not expert-ground-truth accuracy. This synthetic pilot has {len({r['problem_id'] for r in original})} original problem groups.",
                  "No instructor-grade, feedback-quality or educational-benefit result is supplied by these files."]}
    if analyze:
        def metrics(rows):
            eligible = [r for r in rows if r["platform"]["eligible"]]
            return {"rows": len(rows), "answered": len(eligible), "joint_matches": sum(r["platform"]["joint_matches_consensus"] for r in eligible),
                    "time_matches": sum(r["platform"]["time_matches_consensus"] for r in eligible), "space_matches": sum(r["platform"]["space_matches_consensus"] for r in eligible)}
        report["static_platform_comparison"] = {"scope": "Static analyzer only; optional provider not invoked", **metrics(cases),
            "by_language": {language: metrics([r for r in cases if r["language"] == language]) for language in sorted({r["language"] for r in cases})}}
    return report, consensus


def write_report(output, report):
    total = report["rows"]
    lines = ["# AI-assisted pilot comparison", "", f"Both review files contain {total} matched snippets.",
             f"Time-label agreement: {report['model_agreement']['time_agrees']}/{total}. Space-label agreement: {report['model_agreement']['space_agrees']}/{total}. Joint agreement: {report['model_agreement']['joint_agrees']}/{total}.",
             "", "These are model-agreement results, not human-expert accuracy.", ""]
    if "static_platform_comparison" in report:
        result = report["static_platform_comparison"]
        lines += [f"The static platform answered {result['answered']}/{total} cases confidently. Of those answers, {result['joint_matches']} matched both AI-consensus labels.", "",
                  "| Language | Cases | Answered | Both labels match |", "| --- | ---: | ---: | ---: |"]
        lines += [f"| {language} | {m['rows']} | {m['answered']} | {m['joint_matches']} |" for language, m in result["by_language"].items()]
        lines += ["", "## Cases needing investigation", ""]
        for case in report["cases"]:
            if not case["platform"]["joint_matches_consensus"]:
                p = case["platform"]
                lines.append(f"- {case['solution_id']}: platform {p['time']} time / {p['space']} space ({p['status']}); AI proposals {case['review_a_time']} / {case['review_a_space']}.")
    lines += ["", "## Provenance and limits", ""] + [f"- {item}" for item in report["limitations"]]
    lines += ["- Canonical source bytes and problem groups come from the original pack. See comparison.json for source/hash/group discrepancies in returned review metadata.", "- Original inputs are preserved in raw/. Consensus proposals retain ai_assisted_unverified and must not pass a human-reviewed corpus gate."]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--review-a", required=True, type=Path)
    parser.add_argument("--review-b", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--analyze", action="store_true")
    args = parser.parse_args()
    report, consensus = compare(read_rows(args.original), read_rows(args.review_a), read_rows(args.review_b), args.analyze)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    raw = args.output_dir / "raw"
    raw.mkdir()
    for name, path in (("original.jsonl", args.original), ("review-A.txt", args.review_a), ("review-B.jsonl", args.review_b)):
        shutil.copyfile(path, raw / name)
    report["input_file_sha256"] = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in (("original", args.original), ("review_a", args.review_a), ("review_b", args.review_b))}
    (args.output_dir / "comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (args.output_dir / "ai-consensus-proposals.jsonl").write_text("".join(json.dumps(row) + "\n" for row in consensus), encoding="utf-8")
    write_report(args.output_dir, report)
    print(json.dumps({key: value for key, value in report.items() if key not in {"cases", "review_metadata"}}, indent=2))
