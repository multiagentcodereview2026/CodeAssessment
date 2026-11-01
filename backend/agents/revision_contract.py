"""Deterministic validation and release rules for private revision jobs."""
import ast
import hashlib
import math
import re
import sys
from pathlib import Path

from analysis.ast_parser import ASTComplexityAnalyzer
from scoring.complexity import rank_complexity_for_scoring, complexity_rank

CONTRACT_VERSION = 12
RELEASE_POLICY_VERSION = 2


def analyzer_fingerprint():
    root = Path(__file__).resolve().parents[1]
    names = ("analysis/static_analyzer.py", "analysis/ast_parser.py", "analysis/ast_engine.py",
             "analysis/style_ast_analyzer.py", "scoring/complexity.py", "scoring/rubric.py")
    return hashlib.sha256(b"".join((root / name).read_text(encoding="utf-8").replace("\r\n", "\n").encode() for name in names)).hexdigest()


def _tree(source, language):
    parser = ASTComplexityAnalyzer(source, language)
    return parser.tree


def _nodes(node):
    yield node
    for child in node.named_children:
        yield from _nodes(child)


def validate_candidate(source, candidate, language, steps):
    """Return safe rejection codes, never source or judge diagnostics."""
    if not candidate.strip() or "```" in candidate:
        return ["candidate_not_raw_source"]
    if not steps or len(steps) > 3:
        return ["invalid_step_count"]
    from agents.revision import RevisionStep
    from pydantic import ValidationError
    try:
        steps = [RevisionStep.model_validate(step).model_dump() for step in steps]
    except ValidationError:
        return ["step_schema_invalid"]
    original_tree, candidate_tree = _tree(source, language), _tree(candidate, language)
    if not original_tree or not candidate_tree:
        return ["parser_unavailable"]
    if candidate_tree.root_node.has_error:
        return ["candidate_syntax_error"]
    identifiers = {node.text.decode() for node in _nodes(original_tree.root_node)
                   if node.type in {"identifier", "field_identifier", "property_identifier"}}
    errors = []
    ids = set()
    for step in steps:
        if step.get("id") in ids:
            errors.append("duplicate_step_id")
        ids.add(step.get("id"))
        if (step.get("target") or {}).get("symbol") not in identifiers:
            errors.append("target_not_in_original_ast")
        if len(str(step.get("change") or "").split()) < 5:
            errors.append("vague_change")
        if any(phrase in str(step.get("change") or "").lower() for phrase in (
            "use a better structure", "optimize the code", "improve efficiency",
            "make it faster", "keep needed state", "review the analysis",
        )):
            errors.append("vague_change")
        if re.search(r"```|#\s*include|\bint\s+main\s*\(", step.get("change") or ""):
            errors.append("source_code_in_guidance")
    language = language.lower()
    if language in {"python", "py"}:
        try:
            old, new = ast.parse(source), ast.parse(candidate)
        except SyntaxError:
            return ["candidate_syntax_error"]
        functions = lambda tree: {n.name: ast.dump(n.args) for n in tree.body
                                  if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for name, signature in functions(old).items():
            if name in functions(new) and functions(new)[name] != signature:
                errors.append("signature_changed")
        banned = {"os", "subprocess", "socket", "ctypes", "multiprocessing", "importlib"}
        for node in ast.walk(new):
            modules = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            if any(module.split('.')[0] in banned or module.split('.')[0] not in sys.stdlib_module_names for module in modules):
                errors.append("unsupported_import")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "open", "__import__", "compile"}:
                errors.append("banned_call")
    else:
        # Preserve public entry points. Helpers may be introduced only when
        # explicitly explained and independently approved by alignment review.
        entry = re.search(r"\bmain\s*(\([^{};]*\))", source)
        if entry:
            replacement = re.search(r"\bmain\s*(\([^{};]*\))", candidate)
            if not replacement or re.sub(r"\s+", "", entry[1]) != re.sub(r"\s+", "", replacement[1]):
                errors.append("entry_signature_changed")
        calls = {n.child_by_field_name("function").text.decode() for n in _nodes(candidate_tree.root_node)
                 if n.type == "call_expression" and n.child_by_field_name("function") is not None}
        if {call.split("::")[-1] for call in calls} & {"system", "popen", "fopen", "socket", "exec", "eval", "require"}:
            errors.append("banned_call")
        if re.search(r'#\s*include\s*"|\bimport\s+(?!java\.|javax\.)[\w.*]+\s*;', candidate):
            errors.append("external_dependency")
        if re.search(r'#\s*include\s*<\s*(?:boost|curl|openssl|windows|unistd|sys/)', candidate):
            errors.append("external_dependency")
    return sorted(set(errors))


def validate_guidance_text(guide):
    """Do not let a model hide a replacement program in an outline or title."""
    values = [guide.get(key) for key in ("title", "next_goal", "change_summary", "improvement_explanation")]
    for key in ("algorithm_outline", "guided_steps", "future_plan"):
        values.extend(guide.get(key) or [])
    for value in values:
        if not isinstance(value, str):
            continue
        if len(value) > 1800 or re.search(r"```|#\s*include|\bint\s+main\s*\(|\bpublic\s+static\s+void\s+main|if\s+__name__\s*==", value):
            return ["source_code_in_guidance"]
    return []


def validate_revision_guidance(source, language, guide, stage):
    # Validate targets and the guide schema against the original source;
    # candidate syntax, tests and score are a separate decision.
    errors = validate_candidate(source, source, language, guide.get("steps") or [])
    errors.extend(validate_guidance_text(guide))
    expected = {"FOUNDATION": "correctness", "ALGORITHM": "correctness", "STRUCTURE": "correctness",
        "OPTIMIZE_MANUAL_WORK": "time", "OPTIMIZE_LOCAL": "time", "OPTIMIZE_DATA_STRUCTURE": "time",
        "OPTIMIZE_SPACE": "space"}.get(stage)
    areas = {step.get("area") for step in guide.get("steps") or []}
    if len(areas) != 1 or (expected and areas != {expected}):
        errors.append("stage_area_mismatch")
    return sorted(set(errors))


def release_decision(current_score, baseline, projection, steps, minimum_gain=1.0, style_tolerance=1.0):
    """Keep grading unchanged; tolerate only tiny incidental style variance."""
    def finite(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    candidate = projection.get("projected_score")
    if not finite(style_tolerance) or not 0 <= style_tolerance <= 1:
        return "assessment_incomplete"
    if not projection.get("verified") or not projection.get("available") or not finite(candidate) or not finite(current_score):
        return "assessment_incomplete"
    if round(candidate - current_score, 1) < minimum_gain:
        return "no_improvement"
    breakdown = projection.get("score_breakdown") or {}
    for key in ("correctness", "time", "space", "style"):
        before, after = (baseline.get(key) or {}).get("score"), (breakdown.get(key) or {}).get("score")
        if not finite(before) or not finite(after):
            return "assessment_incomplete"
        tolerance = style_tolerance if key == "style" and not any(step.get("area") == "style" for step in steps) else 0
        if after + tolerance + 1e-6 < before:
            return "component_regression"
    if breakdown["correctness"]["score"] != 100:
        return "correctness_not_complete"
    measured = projection.get("measured_complexity") or {}
    for step in steps:
        expected = step.get("expected_complexity") or {}
        for dimension in ("time", "space"):
            claim = expected.get(dimension + "_after")
            if claim:
                actual = rank_complexity_for_scoring(measured.get(dimension))
                target = rank_complexity_for_scoring(claim)
                if not actual or not target or complexity_rank(actual) > complexity_rank(target):
                    return "complexity_claim_unconfirmed"
    return "passed"
