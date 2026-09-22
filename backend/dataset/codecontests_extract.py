"""Streaming, restartable CodeContests extractor for a private judge corpus."""
import argparse, hashlib, json, os, re
from collections import Counter
from pathlib import Path
from datasets import load_dataset

def clean(v): return re.sub(r"\s+", " ", str(v or "")).strip()
def key(v): return hashlib.sha256(str(v).encode()).hexdigest()
def tests(raw):
    """Accept both HF Sequence layouts: list[dict] and {input:[], output:[]}."""
    if isinstance(raw, dict):
        ins, outs = raw.get("input", raw.get("inputs", [])), raw.get("output", raw.get("outputs", []))
        if isinstance(ins, str): ins, outs = [ins], [outs]
        return [{"input": i, "output": o} for i, o in zip(ins or [], outs or [])]
    if isinstance(raw, list):
        return [{"input": x.get("input"), "output": x.get("output")} for x in raw if isinstance(x, dict)]
    return []
def solutions(raw):
    if isinstance(raw, dict):
        langs, code = raw.get("language", []), raw.get("solution", [])
        return [{"language": str(a), "solution": str(b)} for a, b in zip(langs, code) if b]
    if isinstance(raw, list): return [{"language": str(x.get("language", "")), "solution": str(x.get("solution", ""))} for x in raw if x.get("solution")]
    return []
def source_name(row, field):
    value = row.get(field, "UNKNOWN")
    return str(value)
def normalized_cases(items, seen, malformed):
    out = []
    for item in items:
        i, o = item.get("input"), item.get("output")
        if not isinstance(i, str) or not isinstance(o, str) or not i.strip() or not o.strip():
            malformed[0] += 1; continue
        digest = key(i)
        if digest in seen: continue
        seen.add(digest); out.append({"input": i, "output": o})
    return out
def write_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--target", type=int, default=1000)
    ap.add_argument("--dataset", default="deepmind/code_contests")
    ap.add_argument("--min-hidden", type=int, default=60)
    ap.add_argument("--max-hidden", type=int, default=200)
    args = ap.parse_args()
    if args.min_hidden < 60 or args.max_hidden > 200 or args.min_hidden > args.max_hidden: raise ValueError("Use hidden limits within 60..200")
    root, problems = Path(args.output), Path(args.output) / "problems"
    problems.mkdir(parents=True, exist_ok=True)
    jsonl, progress = root / "dataset.jsonl", root / "progress.json"
    accepted = set()
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip(): accepted.add(json.loads(line)["source_key"])
    stats = {"scanned": 0, "insufficient_tests": 0, "malformed_tests": 0, "missing_reference_solution": 0, "duplicates": 0}
    if progress.exists(): stats.update(json.loads(progress.read_text(encoding="utf-8")).get("stats", {}))
    for split in ("train", "valid", "test"):
        if len(accepted) >= args.target: break
        stream = load_dataset(args.dataset, split=split, streaming=True, trust_remote_code=True)
        for row_index, row in enumerate(stream):
            if len(accepted) >= args.target: break
            stats["scanned"] += 1
            source_key = f"{split}:{row.get('name', '')}:{row_index}"
            if source_key in accepted: continue
            correct = solutions(row.get("solutions"))
            if not correct: stats["missing_reference_solution"] += 1; continue
            malformed = [0]; seen = set()
            public = normalized_cases(tests(row.get("public_tests")), seen, malformed)[:10]
            hidden = normalized_cases(tests(row.get("private_tests")), seen, malformed)
            hidden += normalized_cases(tests(row.get("generated_tests")), seen, malformed)
            stats["malformed_tests"] += malformed[0]
            if len(hidden) < args.min_hidden:
                stats["insufficient_tests"] += 1; continue
            hidden = hidden[:args.max_hidden]
            # Preserve only source-provided public tests; never relabel them hidden.
            record = {
                "problem_id": f"codecontests-{len(accepted)+1:06d}", "source_key": source_key,
                "title": row.get("name") or f"CodeContests {split} {row_index}", "description": row.get("description", ""),
                "difficulty": source_name(row, "difficulty"), "source": source_name(row, "source"),
                "source_url": None, "starter_code": None, "public_tests": public, "hidden_tests": hidden,
                "reference_solutions": correct, "incorrect_solutions": solutions(row.get("incorrect_solutions")),
                "time_limit": row.get("time_limit"), "memory_limit": row.get("memory_limit_bytes"), "tags": row.get("cf_tags", []),
            }
            number = len(accepted) + 1
            write_json(problems / f"problem_{number:06d}.json", record)
            with jsonl.open("a", encoding="utf-8") as fp: fp.write(json.dumps(record, ensure_ascii=False) + "\n")
            accepted.add(source_key)
            if number % 50 == 0: write_json(progress, {"accepted": number, "stats": stats})
    records = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = [len(record["hidden_tests"]) for record in records]
    metadata = {"total_problems": len(counts), "minimum_hidden_tests": args.min_hidden, "maximum_hidden_tests": args.max_hidden,
                "average_hidden_tests": sum(counts)/len(counts) if counts else 0, "total_hidden_tests": sum(counts),
                "source_distribution": dict(Counter(str(record["source"]) for record in records)),
                "difficulty_distribution": dict(Counter(str(record["difficulty"]) for record in records)), "stats": stats}
    write_json(root / "metadata.json", metadata); write_json(progress, {"accepted": len(counts), "stats": stats})
    print(json.dumps(metadata, indent=2))
    assert len(counts) >= args.target, "Not enough qualifying problems; inspect metadata.json"
    assert min(counts) >= args.min_hidden and max(counts) <= args.max_hidden
if __name__ == "__main__": main()
