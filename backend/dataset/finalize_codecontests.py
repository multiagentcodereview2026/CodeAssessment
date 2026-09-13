import argparse, json
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
args = parser.parse_args()
root = Path(args.output)
counts, sources, difficulties, total = [], Counter(), Counter(), 0
with (root / "dataset.jsonl").open(encoding="utf-8") as stream:
    for line in stream:
        if not line.strip(): continue
        record = json.loads(line)
        count = len(record.get("hidden_tests", []))
        counts.append(count); total += 1
        sources[str(record.get("source", "UNKNOWN"))] += 1
        difficulties[str(record.get("difficulty", "UNKNOWN"))] += 1
metadata = {
    "total_problems": total, "minimum_hidden_tests": min(counts) if counts else 0,
    "maximum_hidden_tests": max(counts) if counts else 0,
    "average_hidden_tests": sum(counts) / total if total else 0,
    "total_hidden_tests": sum(counts), "source_distribution": dict(sources),
    "difficulty_distribution": dict(difficulties),
}
assert total >= 1000
assert metadata["minimum_hidden_tests"] >= 60
assert metadata["maximum_hidden_tests"] <= 200
(root / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(json.dumps(metadata, indent=2))
