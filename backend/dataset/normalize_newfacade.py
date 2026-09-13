"""Convert Newfacade LeetCodeDataset records into portable stdin/stdout cases.

Newfacade stores Python method calls such as ``n = 5, queries = [[...]]``.
This tool keeps the problem statement, title, tags and oracle outputs, but
normalizes every supported problem to an ordinary command-line contract so a
student can submit a complete ``main`` program in any supported language.

Only records with a concrete, portable type signature are emitted.  This is
intentional: a record is never imported unless the same input contract can be
expressed for C, C++, Python, Java and JavaScript.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


SCALAR_TYPES = {"int", "float", "str", "bool"}


def type_from_annotation(node: ast.AST | None) -> dict[str, Any] | None:
    """Return a small language-neutral type tree, or None when unsupported."""
    if isinstance(node, ast.Name) and node.id in SCALAR_TYPES:
        return {"kind": node.id}
    if isinstance(node, ast.Subscript):
        base = node.value.id if isinstance(node.value, ast.Name) else ""
        if base in {"List", "list"}:
            child = type_from_annotation(node.slice)
            return {"kind": "list", "item": child} if child else None
        if base in {"Optional"}:
            child = type_from_annotation(node.slice)
            return {"kind": "optional", "item": child} if child else None
    return None


def read_signature(starter_code: str) -> tuple[str, list[tuple[str, dict[str, Any]]], dict[str, Any]] | None:
    # Dataset starters intentionally end at an empty method body.  Add a
    # harmless body only for parsing the signature; it is never imported.
    source_variants = [starter_code, starter_code.rstrip() + "\n        pass\n"]
    tree = None
    for source in source_variants:
        try:
            tree = ast.parse(source)
            break
        except SyntaxError:
            continue
    if tree is None:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name == "__init__":
            continue
        pairs: list[tuple[str, dict[str, Any]]] = []
        for argument in node.args.args:
            if argument.arg == "self":
                continue
            parsed = type_from_annotation(argument.annotation)
            if not parsed:
                return None
            pairs.append((argument.arg, parsed))
        result = type_from_annotation(node.returns)
        if pairs and result:
            return node.name, pairs, result
    return None


def literal_value(node: ast.AST) -> Any:
    """Parse the safe Python-like literals used by Newfacade input_output."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal_value(item) for item in node.elts]
    if isinstance(node, ast.Dict):
        return {literal_value(key): literal_value(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -literal_value(node.operand)
    if isinstance(node, ast.Name) and node.id in {"None", "null"}:
        return None
    if isinstance(node, ast.Name) and node.id in {"True", "true"}:
        return True
    if isinstance(node, ast.Name) and node.id in {"False", "false"}:
        return False
    raise ValueError(f"unsupported literal: {ast.dump(node, include_attributes=False)}")


def parse_arguments(source: str) -> dict[str, Any]:
    call = ast.parse(f"f({source})", mode="eval").body
    if not isinstance(call, ast.Call) or call.args:
        raise ValueError("expected keyword arguments")
    return {keyword.arg: literal_value(keyword.value) for keyword in call.keywords if keyword.arg}


def accepts(value: Any, schema: dict[str, Any]) -> bool:
    kind = schema["kind"]
    if kind == "optional":
        return value is None or accepts(value, schema["item"])
    if kind == "list":
        return isinstance(value, list) and all(accepts(item, schema["item"]) for item in value)
    if kind == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "str":
        return isinstance(value, str)
    if kind == "bool":
        return isinstance(value, bool)
    return False


def input_lines(value: Any, schema: dict[str, Any]) -> list[str]:
    """Serialise one value for an ordinary stdin/stdout program.

    Lists retain their lengths because that is structural information required
    to decode a list.  Strings intentionally do *not* receive a synthetic
    length: students should be able to use getline/input/nextLine directly
    and receive spaces exactly as stored in the testcase.
    """
    kind = schema["kind"]
    if kind == "optional":
        return ["0"] if value is None else ["1", *input_lines(value, schema["item"])]
    if kind == "list":
        lines = [str(len(value))]
        item_schema = schema["item"]

        # Keep the list length on its own line, then put scalar list members
        # on the next line.  This is the conventional stdin shape used by
        # complete programs in every supported language:
        #
        #     n = int(input())
        #     values = list(map(int, input().split()))
        #
        # The prior one-value-per-line layout worked with C++ ``cin >>`` but
        # made the equivalent Python program read only the first list member
        # and could lead to an IndexError during normal execution.  Nested
        # and non-scalar members retain their line-delimited recursive form,
        # because their boundaries are structural information.
        if item_schema["kind"] in {"int", "float", "bool"}:
            # Keep an empty payload line for an empty numeric list.  Then the
            # same conventional Python reader works for both cases:
            # ``nums = list(map(int, input().split()))`` becomes ``[]``
            # instead of raising EOFError when n is zero.
            scalar_tokens = [input_lines(item, item_schema)[0] for item in value]
            lines.append(" ".join(scalar_tokens))
            return lines

        for item in value:
            lines.extend(input_lines(item, item_schema))
        return lines
    if kind == "bool":
        return ["1" if value else "0"]
    if kind == "str":
        # Preserve embedded newlines exactly. Problems that genuinely model a
        # multiline text input receive those lines through stdin unchanged.
        return [value]
    return [str(value)]


def output_text(value: Any, schema: dict[str, Any]) -> str:
    """Use whitespace-normalized scalar tokens for portable result comparison."""
    kind = schema["kind"]
    if kind == "optional":
        return "null" if value is None else output_text(value, schema["item"])
    if kind == "list":
        return " ".join(output_text(item, schema["item"]) for item in value).strip()
    if kind == "bool":
        return "true" if value else "false"
    return str(value)


def language_starters(problem_title: str, method: str, parameters: list[tuple[str, dict[str, Any]]]) -> dict[str, str]:
    """Return editable full-program skeletons, never method-only templates."""
    return {
        "cpp": "#include <iostream>\nusing namespace std;\n\nint main() {\n\n    return 0;\n}\n",
        "java": "import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n\n    }\n}\n",
        "c": "#include <stdio.h>\n\nint main() {\n\n    return 0;\n}\n",
        "python": "def main():\n    pass\n\nif __name__ == \"__main__\":\n    main()\n",
        "javascript": "'use strict';\n\n",
    }


def normalize_row(row: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    signature = read_signature(str(row.get("starter_code") or ""))
    if not signature:
        return None, "unsupported_signature"
    method, parameters, result_schema = signature
    cases: list[dict[str, str]] = []
    for source_case in row.get("input_output") or []:
        try:
            values = parse_arguments(str(source_case.get("input") or ""))
            if set(values) != {name for name, _ in parameters}:
                return None, "parameter_mismatch"
            ordered = [values[name] for name, _ in parameters]
            if not all(accepts(value, schema) for value, (_, schema) in zip(ordered, parameters)):
                return None, "input_type_mismatch"
            expected = literal_value(ast.parse(str(source_case.get("output") or ""), mode="eval").body)
            if not accepts(expected, result_schema):
                return None, "output_type_mismatch"
            input_data = "\n".join(line for value, (_, schema) in zip(ordered, parameters) for line in input_lines(value, schema)) + "\n"
            cases.append({"input": input_data, "output": output_text(expected, result_schema)})
        except (SyntaxError, ValueError, TypeError):
            return None, "unparseable_case"
    if len(cases) < 4:
        return None, "too_few_cases"

    task_id = str(row["task_id"])
    title = task_id.replace("-", " ").title()
    description = str(row.get("problem_description") or "").strip()
    if not description:
        return None, "missing_description"
    signature_text = ", ".join(f"{name}: {json.dumps(schema)}" for name, schema in parameters)
    description += (
        "\n\nPlatform Input/Output Format\n"
        "Write a complete program that reads standard input and writes standard output. "
        "Arguments appear in this order: " + signature_text + ". "
        "Every list begins with its length; scalar numeric list values follow on the next whitespace-separated line, "
        "and nested lists use a length at every level. "
        "Strings are passed as raw input lines, including spaces; no string length is prepended. "
        "Print scalar results directly and list results as whitespace-separated values. "
        "Do not print explanatory text."
    )
    public_cases = cases[:3]
    hidden_cases = cases[3:]
    return {
        "problem_id": f"leetcode-{row.get('question_id') or task_id}",
        "title": title,
        "difficulty": str(row.get("difficulty") or "Medium").title(),
        "tags": [str(tag) for tag in row.get("tags") or [] if str(tag).strip()],
        "description": description,
        "examples": [{"input": item["input"], "output": item["output"], "explanation": ""} for item in public_cases],
        "constraints": [],
        "starter_codes": language_starters(title, method, parameters),
        "public_tests": public_cases,
        "hidden_tests": hidden_cases,
        "source_url": f"https://leetcode.com/problems/{task_id}/",
        "source_license": "Newfacade LeetCodeDataset (Apache-2.0)",
        "method": method,
        "parameter_schema": {name: schema for name, schema in parameters},
        "return_schema": result_schema,
        "content_hash": hashlib.sha256((task_id + "\n" + description).encode("utf-8")).hexdigest(),
    }, "ok"


def run(source_paths: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    seen, reasons = set(), Counter()
    imported = total = hidden = 0
    with output.open("w", encoding="utf-8") as destination:
        for path in source_paths:
            with path.open("r", encoding="utf-8") as source:
                for line in source:
                    if not line.strip():
                        continue
                    total += 1
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        reasons["invalid_json"] += 1
                        continue
                    normalized, reason = normalize_row(record)
                    if normalized is None:
                        reasons[reason] += 1
                        continue
                    if normalized["problem_id"] in seen:
                        reasons["duplicate_question_id"] += 1
                        continue
                    seen.add(normalized["problem_id"])
                    destination.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                    imported += 1
                    hidden += len(normalized["hidden_tests"])
    report = {"source_rows": total, "validated_problems": imported, "hidden_cases": hidden, "skipped": dict(reasons)}
    output.with_suffix(".report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, nargs="+", help="Official Newfacade JSONL train/test files")
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    run([Path(path) for path in arguments.source], Path(arguments.output))
