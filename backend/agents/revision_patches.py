"""Apply bounded, exact source edits; the model never replaces the full file."""
import hashlib
import re

from pydantic import BaseModel, ConfigDict, Field

from analysis.ast_parser import ASTComplexityAnalyzer

PATCH_FORMAT = "exact_patch_v1"


class SourcePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_id: str = Field(min_length=1, max_length=40)
    old: str = Field(min_length=1, max_length=20000)
    new: str = Field(max_length=20000)


def source_context(source, language):
    """Supply real AST identifiers and line locations, not invented targets."""
    tree = ASTComplexityAnalyzer(source, language).tree
    symbols = {}
    def walk(node):
        if node.type in {"identifier", "field_identifier", "property_identifier"}:
            name = node.text.decode("utf-8")
            symbols.setdefault(name, set()).add(node.start_point[0] + 1)
        for child in node.named_children:
            walk(child)
    if tree:
        walk(tree.root_node)
    return {"source_hash": hashlib.sha256(source.encode()).hexdigest(),
        "symbols": [{"name": name, "lines": sorted(lines)} for name, lines in sorted(symbols.items())]}


def apply_source_patches(source, patches, steps, expected_hash):
    """Resolve all edits against the original, then apply them back to front."""
    if hashlib.sha256(source.encode()).hexdigest() != expected_hash:
        return "", ["stale_patch_source"]
    if not patches or len(patches) > 6:
        return "", ["invalid_patch_count"]
    targets = {step["id"]: (step.get("target") or {}).get("symbol") for step in steps}
    spans, covered = [], set()
    for raw in patches:
        try:
            patch = SourcePatch.model_validate(raw)
        except (ValueError, TypeError):
            return "", ["patch_schema_invalid"]
        if patch.step_id not in targets:
            return "", ["patch_step_not_in_guide"]
        anchor, replacement = patch.old, patch.new
        if anchor not in source and "\r\n" in source and "\r\n" not in anchor:
            # JSON responses commonly use LF even for CRLF submissions.
            # Normalize only this edit; untouched bytes remain unchanged.
            anchor = anchor.replace("\n", "\r\n")
            replacement = replacement.replace("\r\n", "\n").replace("\n", "\r\n")
        start = source.find(anchor)
        if start < 0 or source.find(anchor, start + 1) != -1:
            return "", ["patch_anchor_not_unique"]
        if patch.old == patch.new:
            return "", ["patch_has_no_change"]
        if patch.old.strip() == source.strip() or (len(patch.old) > len(source) * .8 and re.search(r"\bmain\s*\(|\bdef\s+", patch.old)):
            return "", ["whole_program_patch_rejected"]
        if "```" in patch.new:
            return "", ["fenced_patch_rejected"]
        # A required include may accompany an algorithm edit. Wholesale header
        # replacement is not necessary and must not slip into a time/space step.
        old_lines, new_lines = patch.old.strip().splitlines(), patch.new.strip().splitlines()
        include = lambda lines: bool(lines) and all(re.fullmatch(r"\s*#\s*include\s*<[^>]+>\s*", line) for line in lines)
        header_edit = include(old_lines) and include(new_lines)
        imports = lambda lines: bool(lines) and all(re.fullmatch(r"\s*(?:import\s+[\w.* ,]+;?|from\s+[\w.]+\s+import\s+[\w* ,]+)\s*", line) for line in lines)
        import_edit = imports(old_lines) and imports(new_lines)
        if header_edit:
            old_headers = set(re.findall(r"<([^>]+)>", patch.old))
            new_headers = set(re.findall(r"<([^>]+)>", patch.new))
            if not old_headers <= new_headers or ("bits/stdc++.h" in new_headers - old_headers):
                return "", ["unrequested_header_replacement"]
        elif import_edit:
            if not {line.strip() for line in old_lines} <= {line.strip() for line in new_lines}:
                return "", ["unrequested_import_replacement"]
        elif not targets[patch.step_id] or not re.search(r"\b" + re.escape(targets[patch.step_id]) + r"\b", patch.old):
            return "", ["patch_does_not_touch_target"]
        spans.append((start, start + len(anchor), replacement))
        covered.add(patch.step_id)
    if covered != set(targets):
        return "", ["guide_step_without_patch"]
    spans.sort()
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        return "", ["overlapping_source_patches"]
    result = source
    for start, end, replacement in reversed(spans):
        result = result[:start] + replacement + result[end:]
    return result, []
