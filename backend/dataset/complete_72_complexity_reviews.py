"""Complete the approved 72 fixed-ladder complexity reviews.

This utility is deliberately narrow: it refuses to modify a bank unless it
contains exactly 72 records marked ``complexity_needs_review``.  Every other
JSONL line is copied byte-for-byte, so the already-approved 1,814 records are
not rewritten.  It emits a machine-readable audit report for the 72 changes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


# id: (fixed-ladder time target, fixed-ladder auxiliary-space target, rationale)
# The platform compares only its ten ordered buckets.  These are reviewed
# projections of the problem's optimal asymptotic method, not student-code
# measurements.
REVIEWS: dict[str, tuple[str, str, str]] = {
    "leetcode-1016": ("O(n)", "O(1)", "Linear scan over the binary input; no input-sized auxiliary structure is required."),
    "leetcode-1065": ("O(n)", "O(n)", "Trie/search work is linear in the total input characters; the trie stores input dictionary characters."),
    "leetcode-1088": ("O(2^n)", "O(n)", "Digit DFS branches over valid rotated digits and uses a recursion stack."),
    "leetcode-1140": ("O(n^2)", "O(n^2)", "Memoized Stone Game II dynamic programming has quadratic states/transitions after suffix optimization."),
    "leetcode-1183": ("O(n^2)", "O(n^2)", "The repeated pattern grid is evaluated over two dimensions."),
    "leetcode-1187": ("O(n^3)", "O(n)", "Dynamic programming over positions and replacement candidates is projected to cubic time in the fixed ladder."),
    "leetcode-1240": ("O(2^n)", "O(n)", "Backtracking rectangle tiling is exponential; state storage is bounded by recursion/profile depth."),
    "leetcode-1316": ("O(n^2)", "O(n^2)", "Echo substrings require quadratic candidate comparison/storage in the chosen method."),
    "leetcode-1317": ("O(n)", "O(1)", "The candidate search is linear in the numeric search range and uses constant auxiliary memory."),
    "leetcode-1335": ("O(n^2)", "O(n)", "Job/day dynamic programming is quadratic when days scale with jobs; rolling state is linear."),
    "leetcode-1389": ("O(n^2)", "O(n)", "Indexed insertion into an array can shift existing elements, giving quadratic total time."),
    "leetcode-139": ("O(n^2)", "O(n)", "Word-break DP checks prefixes/word lengths; worst-case word length scales with input."),
    "leetcode-1408": ("O(n^2)", "O(n)", "Each word may be checked against other input words; output/index storage is linear."),
    "leetcode-1467": ("O(n^3)", "O(n)", "The combinatorial DP is projected to the cubic fixed-ladder bucket with linear recursion/state depth."),
    "leetcode-1534": ("O(n^3)", "O(1)", "The direct optimal-for-constraints triplet enumeration is cubic and in-place."),
    "leetcode-1548": ("O(n^3)", "O(n^2)", "Path-position by graph-edge DP has cubic worst-case projection and a two-dimensional DP table."),
    "leetcode-1563": ("O(n^2)", "O(n^2)", "Optimized interval dynamic programming is quadratic in time and memoized interval storage."),
    "leetcode-1621": ("O(n^2)", "O(n^2)", "DP over length and selected segments is quadratic when k scales with n."),
    "leetcode-1659": ("O(2^n)", "O(2^n)", "Row-profile dynamic programming is exponential in the bounded grid width."),
    "leetcode-1668": ("O(n^2)", "O(1)", "Repeated substring matching can compare a linear-size word at linear candidate positions."),
    "leetcode-1682": ("O(n^2)", "O(n^2)", "Two-index palindromic subsequence DP uses a quadratic table."),
    "leetcode-1698": ("O(n)", "O(n)", "Suffix automaton construction is linear in string length and stores linear states."),
    "leetcode-1723": ("O(2^n)", "O(2^n)", "Subset/backtracking assignment is exponential with exponential memo/subset state."),
    "leetcode-1815": ("O(2^n)", "O(2^n)", "Remainder-state memoization is exponential in the variable remainder profile."),
    "leetcode-1900": ("O(n^4+)", "O(n^2)", "Round-pair memoized state exploration has quartic worst-case projection."),
    "leetcode-1931": ("O(n)", "O(1)", "The row-profile count is bounded by the fixed width constraint, leaving linear growth in rows."),
    "leetcode-1956": ("O(n^3)", "O(n^2)", "All-pairs shortest path computation uses cubic time and a distance matrix."),
    "leetcode-1967": ("O(n^2)", "O(1)", "Checking each candidate string within the word has quadratic worst-case input growth."),
    "leetcode-1981": ("O(n^3)", "O(n)", "Matrix/value-sum DP is projected to cubic time and linear rolling state."),
    "leetcode-2183": ("O(n^2)", "O(n)", "Divisor pairing is projected to the quadratic bucket when k scales with input magnitude."),
    "leetcode-2189": ("O(n^2)", "O(n)", "Card-house dynamic programming has quadratic work and linear rolling state."),
    "leetcode-2221": ("O(n^2)", "O(1)", "Repeated adjacent reductions perform quadratic total work in-place."),
    "leetcode-2249": ("O(n^3)", "O(n^2)", "Enumerating circle coverage is projected to cubic time with quadratic point storage."),
    "leetcode-2301": ("O(n^2)", "O(1)", "Each pattern alignment can compare a linear-length substring without auxiliary collections."),
    "leetcode-2305": ("O(2^n)", "O(2^n)", "Cookie assignment backtracking/memoization is exponential."),
    "leetcode-2470": ("O(n^2)", "O(1)", "All start/end LCM extensions yield quadratic worst-case work and constant auxiliary state."),
    "leetcode-2601": ("O(n log n)", "O(n)", "Prime preprocessing plus per-item search is projected to linearithmic time and linear sieve storage."),
    "leetcode-2735": ("O(n^2)", "O(n)", "Evaluating every rotation across all chocolate types is quadratic with linear working storage."),
    "leetcode-2781": ("O(n)", "O(n)", "Forbidden-string length is bounded; sliding-window/trie checks are linear in input with linear dictionary storage."),
    "leetcode-2827": ("O(n^2)", "O(n)", "Digit DP is projected to quadratic fixed-ladder time with linear memo/state depth."),
    "leetcode-2902": ("O(n^2)", "O(n)", "Bounded-sum DP is projected to quadratic time and linear state."),
    "leetcode-2911": ("O(n^3)", "O(n^2)", "Partition DP plus palindrome cost preprocessing is cubic in the fixed-ladder model."),
    "leetcode-2941": ("O(n log n)", "O(n)", "GCD aggregation over logarithmic value changes is bucketed as linearithmic."),
    "leetcode-2947": ("O(n^2)", "O(n)", "The square-root divisibility factor is projected to the quadratic ladder bucket."),
    "leetcode-2949": ("O(n^2)", "O(n)", "The square-root divisibility factor is projected to the quadratic ladder bucket."),
    "leetcode-30": ("O(n^2)", "O(n^2)", "Candidate-window word matching is quadratic in the fixed-ladder projection and stores word/window data."),
    "leetcode-3018": ("O(n^2)", "O(n^2)", "Interval dynamic programming requires quadratic time and state."),
    "leetcode-3076": ("O(n^3)", "O(n^2)", "Substring comparison across words is projected to cubic time with quadratic substring/index storage."),
    "leetcode-3098": ("O(n^4+)", "O(n)", "Subsequence-power DP/enumeration has quartic-or-higher fixed-ladder projection."),
    "leetcode-3102": ("O(n)", "O(1)", "Maintain extreme Manhattan transforms in one pass using constant auxiliary state."),
    "leetcode-3139": ("O(n)", "O(1)", "A linear scan of extrema/sum determines the optimal equalization cost with constant auxiliary state."),
    "leetcode-3197": ("O(n^2)", "O(1)", "A constant number of grid partition scans is quadratic for a two-dimensional grid."),
    "leetcode-321": ("O(n^3)", "O(n)", "Selecting and merging across all split points has cubic fixed-ladder projection."),
    "leetcode-3213": ("O(n^2)", "O(n)", "String-cost DP is projected to quadratic time with linear DP storage."),
    "leetcode-3269": ("O(n^2)", "O(n^2)", "Two-sequence construction dynamic programming uses a quadratic state space."),
    "leetcode-3276": ("O(2^n)", "O(2^n)", "Row-selection bitmask DP is exponential in the number of selectable rows."),
    "leetcode-3376": ("O(2^n)", "O(2^n)", "Subset dynamic programming is exponential in lock count."),
    "leetcode-3395": ("O(n)", "O(n)", "Frequency/prefix accounting processes the sequence once using linear maps."),
    "leetcode-3426": ("O(n)", "O(1)", "Combinatorial contribution calculation is linear in selected positions and constant-space."),
    "leetcode-3428": ("O(n^2)", "O(n^2)", "Sorting plus k-dependent combinatorics is projected to quadratic time and state."),
    "leetcode-3444": ("O(2^n)", "O(2^n)", "Target-subset DP is exponential in the distinct target set."),
    "leetcode-3447": ("O(n log n)", "O(n)", "Preprocess divisors/groups then answer assignments in linearithmic time with linear storage."),
    "leetcode-3458": ("O(n)", "O(n)", "Interval selection over discovered special substrings is linear with linear interval storage."),
    "leetcode-3485": ("O(n)", "O(n)", "Trie/prefix aggregation and removal answers are linear in total input characters."),
    "leetcode-3489": ("O(n^2)", "O(n)", "The transformation search is quadratic with linear auxiliary tracking."),
    "leetcode-3491": ("O(n log n)", "O(n)", "Sorting or trie-prefix processing is linearithmic and uses linear storage."),
    "leetcode-466": ("O(n^2)", "O(n)", "Repeated-string state transitions are projected to quadratic time with linear state."),
    "leetcode-750": ("O(n^3)", "O(1)", "Row/column pair counting is cubic in the square-grid fixed-ladder projection."),
    "leetcode-792": ("O(n)", "O(n)", "Indexed-next-character matching is linear in aggregate input with linear index storage."),
    "leetcode-805": ("O(2^n)", "O(2^n)", "Meet-in-the-middle subset enumeration is exponential in the fixed ladder."),
    "leetcode-956": ("O(n^2)", "O(n)", "Difference-sum DP is pseudo-polynomial and is projected to quadratic time with linear state."),
    "leetcode-996": ("O(2^n)", "O(2^n)", "Bitmask permutation DP is exponential in input size."),
}


def update(source: Path, destination: Path, report_path: Path) -> None:
    changed: list[dict[str, object]] = []
    review_ids: set[str] = set()
    output_lines: list[str] = []

    for line_number, raw in enumerate(source.read_text(encoding="utf-8").splitlines(keepends=True), 1):
        if not raw.strip():
            output_lines.append(raw)
            continue
        row = json.loads(raw)
        problem_id = str(row.get("problem_id") or "")
        if row.get("complexity_needs_review"):
            review_ids.add(problem_id)
        review = REVIEWS.get(problem_id)
        if review is None:
            output_lines.append(raw)
            continue

        if not row.get("complexity_needs_review"):
            raise ValueError(f"{problem_id} is not marked for review; refusing to alter an approved record")

        time_target, space_target, rationale = review
        old = {
            "problem_id": problem_id,
            "title": row.get("title"),
            "old_time": row.get("target_time_complexity"),
            "old_space": row.get("target_space_complexity"),
        }
        row["target_time_complexity"] = time_target
        row["target_space_complexity"] = space_target
        row["complexity_source"] = "reviewed-fixed-ladder-20261004"
        row["complexity_confidence"] = 1.0
        row["complexity_reasoning"] = rationale
        row["complexity_needs_review"] = False
        changed.append({**old, "new_time": time_target, "new_space": space_target, "rationale": rationale})
        output_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + ("\n" if raw.endswith("\n") else ""))

    if len(review_ids) != 72:
        raise ValueError(f"Expected exactly 72 review records, found {len(review_ids)}")
    if set(REVIEWS) != review_ids:
        missing = sorted(review_ids - set(REVIEWS))
        extra = sorted(set(REVIEWS) - review_ids)
        raise ValueError(f"Review map mismatch; missing={missing}, extra={extra}")
    if len(changed) != 72:
        raise ValueError(f"Expected 72 changes, wrote {len(changed)}")

    destination.write_text("".join(output_lines), encoding="utf-8")
    report_path.write_text(json.dumps({"updated_records": changed, "count": len(changed)}, indent=2), encoding="utf-8")
    print(json.dumps({"updated": len(changed), "unchanged": 1814, "output": str(destination), "report": str(report_path)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    update(args.source, args.output, args.report)
