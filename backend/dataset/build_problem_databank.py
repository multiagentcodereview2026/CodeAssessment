"""Build a review-ready CodeAssessment problem bank without external APIs.

The Newfacade source provides a problem statement, test cases, and a Python
reference implementation.  It does *not* provide an authoritative statement
of the mathematical optimum for every problem.  This builder therefore keeps
those two concepts separate:

* ``reference_solution_complexity`` is a conservative, local AST observation
  of the supplied reference implementation.
* ``target_time_complexity`` / ``target_space_complexity`` remain null until a
  curator has accepted a target.  They must never be populated just because a
  syntactic estimate exists.

That distinction prevents an unreviewed heuristic from being used to score a
student as inefficient.  The generated JSONL preserves all public and hidden
test cases from the normalized source unchanged and is suitable as the single
review queue for filling the final target fields.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


COMPLEXITY_ORDER = {
    "O(1)": 0,
    "O(log n)": 1,
    "O(n)": 2,
    "O(n log n)": 3,
    "O(n^2)": 4,
    "O(n^3)": 5,
    "O(2^n)": 6,
    "O(n!)": 7,
}


def question_key(problem_id: str) -> str:
    """Return the Newfacade question id from a ``leetcode-<id>`` key."""
    prefix = "leetcode-"
    return problem_id[len(prefix):] if problem_id.startswith(prefix) else problem_id


def load_reference_solutions(paths: Iterable[Path]) -> dict[str, dict[str, str]]:
    """Read local reference code and explanation indexed by ``question_id``.

    Later input files only fill a missing value.  This lets train and test
    source files be supplied together without replacing a non-empty solution.
    """
    solutions: dict[str, dict[str, str]] = {}
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Reference dataset not found: {path}")
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                key = str(row.get("question_id") or "").strip()
                completion = str(row.get("completion") or "").strip()
                response = str(row.get("response") or "").strip()
                if not key:
                    continue
                entry = solutions.setdefault(key, {"completion": "", "response": ""})
                if completion and not entry["completion"]:
                    entry["completion"] = completion
                if response and not entry["response"]:
                    entry["response"] = response
    return solutions


def normalize_complexity(value: str) -> str | None:
    """Normalise only a closed, single-variable Big-O vocabulary."""
    compact = value.lower().replace("\\", "").replace(" ", "")
    compact = compact.replace("{", "").replace("}", "")
    aliases = {
        "1": "O(1)",
        "n": "O(n)",
        "logn": "O(log n)",
        "log(n)": "O(log n)",
        "nlogn": "O(n log n)",
        "nlog(n)": "O(n log n)",
        "n^2": "O(n^2)",
        "n²": "O(n^2)",
        "n**2": "O(n^2)",
        "n^3": "O(n^3)",
        "n³": "O(n^3)",
        "n**3": "O(n^3)",
        "2^n": "O(2^n)",
        "2**n": "O(2^n)",
        "n!": "O(n!)",
    }
    return aliases.get(compact)


def stated_complexity(response: str, label: str) -> str | None:
    """Read a single allowed Big-O value stated near a local explanation.

    This is evidence from the dataset's local reference response, not a final
    optimality proof.  Variable-dependent expressions such as ``O(N log k)``
    are intentionally left unresolved because the bank's target vocabulary
    has only one input-size variable.
    """
    if not response:
        return None
    pattern = rf"(?i){label}\s+complexity|{label}\s+runtime"
    values: list[str] = []
    for match in re.finditer(pattern, response):
        nearby = response[max(0, match.start() - 120): match.end() + 360]
        for expression in re.findall(r"O\s*\(\s*([^)]{1,30})\s*\)", nearby, flags=re.IGNORECASE):
            value = normalize_complexity(expression)
            if value and value not in values:
                values.append(value)
    return values[0] if len(values) == 1 else None


class ReferenceComplexityVisitor(ast.NodeVisitor):
    """Conservative syntactic complexity evidence for a Python solution.

    The visitor deliberately returns ``needs_review`` for recursion, unknown
    while-loop termination, generator-heavy code, and non-standard calls.  A
    loop count alone cannot prove an algorithm is optimal.
    """

    def __init__(self) -> None:
        self.loop_depth = 0
        self.max_loop_depth = 0
        self.has_sort = False
        self.sort_inside_loop = False
        self.has_log_search = False
        self.has_factorial_generator = False
        self.has_recursion = False
        self.has_unknown_while = False
        self.has_comprehension = False
        self.has_linear_storage = False
        self.has_quadratic_storage = False
        self.current_function: str | None = None
        self.function_names: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        previous = self.current_function
        self.current_function = node.name
        self.function_names.add(node.name)
        self.generic_visit(node)
        self.current_function = previous

    visit_AsyncFunctionDef = visit_FunctionDef

    def _visit_loop(self, node: ast.AST) -> None:
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_For(self, node: ast.For) -> Any:
        self._visit_loop(node)

    visit_AsyncFor = visit_For

    def visit_While(self, node: ast.While) -> Any:
        # A loop based on a simple interval may be logarithmic, but determining
        # its update safely needs semantic analysis.  Keep it review-required.
        self.has_unknown_while = True
        self._visit_loop(node)

    def visit_ListComp(self, node: ast.ListComp) -> Any:
        self.has_comprehension = True
        self.max_loop_depth = max(self.max_loop_depth, len(node.generators))
        self.generic_visit(node)

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_List(self, node: ast.List) -> Any:
        if node.elts:
            self.has_linear_storage = True
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> Any:
        if node.keys:
            self.has_linear_storage = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr

        if name in {"sort", "sorted"}:
            self.has_sort = True
            self.sort_inside_loop = self.sort_inside_loop or self.loop_depth > 0
        if name in {"bisect", "bisect_left", "bisect_right"}:
            self.has_log_search = True
        if name in {"permutations"}:
            self.has_factorial_generator = True
        if name in {"product", "combinations", "combinations_with_replacement"}:
            self.has_factorial_generator = True
        if name in {"set", "dict", "defaultdict", "Counter", "deque", "heapify"}:
            self.has_linear_storage = True
        if name in {"sum", "min", "max", "any", "all", "reversed", "enumerate", "zip"}:
            # These calls may consume an input-sized iterable even when no
            # explicit Python ``for`` node appears in the reference code.
            self.max_loop_depth = max(self.max_loop_depth, self.loop_depth or 1)
        if isinstance(node.func, ast.Name) and node.func.id == self.current_function:
            self.has_recursion = True
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        # ``[[... for ...] for ...]`` is clear quadratic auxiliary storage.
        if isinstance(node.value, ast.ListComp) and any(
            isinstance(item, ast.ListComp) for item in ast.walk(node.value.elt)
        ):
            self.has_quadratic_storage = True
        self.generic_visit(node)


def observed_complexity(source: str) -> dict[str, Any]:
    """Return transparent evidence, never an assertion of optimality."""
    if not source:
        return {
            "time": None,
            "space": None,
            "confidence": "none",
            "needs_review": True,
            "notes": ["No local reference implementation was found."],
        }
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {
            "time": None,
            "space": None,
            "confidence": "none",
            "needs_review": True,
            "notes": ["Reference implementation could not be parsed."],
        }

    visitor = ReferenceComplexityVisitor()
    visitor.visit(tree)
    notes: list[str] = []
    # A source-level loop shape cannot distinguish a sliding-window's
    # amortized O(n) loop from O(n^2), nor prove the branching factor of a
    # recursive/combinatorial algorithm.  Keep those cases indeterminate.
    if visitor.has_recursion or visitor.has_unknown_while or visitor.has_factorial_generator or visitor.sort_inside_loop:
        time_value = None
        notes.append("Control flow requires semantic review; no syntactic time target is suggested.")
    elif visitor.max_loop_depth >= 3:
        time_value = "O(n^3)"
        notes.append("Reference code has three nested iteration levels.")
    elif visitor.max_loop_depth == 2:
        time_value = "O(n^2)"
        notes.append("Reference code has two nested iteration levels.")
    elif visitor.has_sort and visitor.max_loop_depth <= 1:
        time_value = "O(n log n)"
        notes.append("Reference code sorts an input-sized collection.")
    elif visitor.max_loop_depth == 1 or visitor.has_comprehension:
        time_value = "O(n)"
        notes.append("Reference code has one input-sized iteration level.")
    elif visitor.has_log_search:
        time_value = "O(log n)"
        notes.append("Reference code uses binary-search primitives.")
    else:
        time_value = "O(1)"
        notes.append("No input-sized iteration was found syntactically.")

    if visitor.has_quadratic_storage:
        space_value = "O(n^2)"
        notes.append("Reference code builds nested dynamic storage.")
    elif visitor.has_linear_storage or visitor.has_comprehension:
        space_value = "O(n)"
        notes.append("Reference code allocates dynamic auxiliary storage.")
    else:
        space_value = "O(1)"
        notes.append("No dynamic auxiliary collection was found syntactically.")

    uncertain = (
        visitor.has_recursion
        or visitor.has_unknown_while
        or visitor.has_factorial_generator
        or visitor.sort_inside_loop
    )
    if visitor.has_recursion:
        notes.append("Recursion requires semantic review before accepting a target.")
    if visitor.has_unknown_while:
        notes.append("While-loop termination requires semantic review before accepting a target.")
    if visitor.has_factorial_generator:
        notes.append("Combinatorial generator usage requires semantic review before accepting a target.")
    if visitor.sort_inside_loop:
        notes.append("A sort inside iteration requires semantic review before accepting a target.")

    confidence = "low" if uncertain else "medium"
    return {
        "time": time_value,
        "space": space_value,
        "confidence": confidence,
        "needs_review": True,
        "notes": notes,
    }


def build(source_path: Path, reference_paths: list[Path], output_path: Path) -> dict[str, Any]:
    if not source_path.is_file():
        raise FileNotFoundError(f"Normalized dataset not found: {source_path}")
    if source_path.resolve() == output_path.resolve():
        raise ValueError("Use a new output path; never overwrite the source corpus.")

    references = load_reference_solutions(reference_paths)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report: Counter[str] = Counter()

    with source_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as destination:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            report["problems"] += 1
            reference = references.get(question_key(str(row.get("problem_id") or "")), {})
            completion = reference.get("completion", "")
            observation = observed_complexity(completion)
            stated_time = stated_complexity(reference.get("response", ""), "time")
            stated_space = stated_complexity(reference.get("response", ""), "space")
            if observation["time"] is None and stated_time:
                observation["time"] = stated_time
                observation["notes"].append("Time estimate was stated in the local reference explanation.")
            if observation["space"] is None and stated_space:
                observation["space"] = stated_space
                observation["notes"].append("Space estimate was stated in the local reference explanation.")
            if completion:
                report["reference_solutions_found"] += 1
            else:
                report["reference_solutions_missing"] += 1

            # Keep target fields empty.  A human accepts them only after
            # checking the complete statement/constraints and algorithm.
            row["target_time_complexity"] = None
            row["target_space_complexity"] = None
            row["complexity_source"] = "local-reference-solution-review-pending"
            row["complexity_confidence"] = None
            row["complexity_reasoning"] = None
            row["complexity_needs_review"] = True
            row["reference_solution_complexity"] = {
                "observed_time_complexity": observation["time"],
                "observed_space_complexity": observation["space"],
                "confidence": observation["confidence"],
                "notes": observation["notes"],
                "reference_solution_available": bool(reference),
            }
            report[f"observed_time_{observation['time'] or 'unknown'}"] += 1
            report[f"observed_space_{observation['space'] or 'unknown'}"] += 1
            destination.write(json.dumps(row, ensure_ascii=False) + "\n")

    report["output_path"] = str(output_path)
    report["targets_accepted"] = 0
    report["targets_pending_review"] = report["problems"]
    return dict(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a local, review-ready CodeAssessment problem bank.")
    parser.add_argument("--source", required=True, help="Tagged normalized Newfacade JSONL.")
    parser.add_argument("--reference-source", required=True, action="append", help="Raw Newfacade JSONL containing completion code.")
    parser.add_argument("--output", required=True, help="New review-ready JSONL output path.")
    args = parser.parse_args()
    print(json.dumps(
        build(Path(args.source), [Path(path) for path in args.reference_source], Path(args.output)),
        indent=2,
        ensure_ascii=False,
    ))
