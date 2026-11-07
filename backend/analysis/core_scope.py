"""Analysis-only AST slicing; never changes the executable submission.

Only proven I/O is removed. Ambiguous entry points and mixed I/O require
hybrid review. No problem titles or algorithm-specific names are used.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from .ast_parser import ASTComplexityAnalyzer


@dataclass
class CoreScope:
    source: str
    space_source: str
    inputs: set[str] = field(default_factory=set)
    outputs: set[str] = field(default_factory=set)
    issues: list[str] = field(default_factory=list)
    auxiliary_copy: bool = False


def _walk(node):
    yield node
    for child in node.named_children:
        yield from _walk(child)


def _text(node):
    return node.text.decode("utf-8") if node is not None else ""


def _replace(source, edits):
    data = source.encode("utf-8")
    for start, end, value in sorted(edits, reverse=True):
        data = data[:start] + value.encode("utf-8") + data[end:]
    return data.decode("utf-8")


def _function_name(node):
    name = node.child_by_field_name("name")
    if name is not None:
        return _text(name)
    decl = node.child_by_field_name("declarator")
    while decl is not None:
        if decl.type in {"identifier", "field_identifier"}:
            return _text(decl)
        decl = decl.child_by_field_name("declarator")
    return ""


def _calls(node):
    result = set()
    for item in _walk(node):
        if item.type not in {"call_expression", "method_invocation"}:
            continue
        target = item.child_by_field_name("function") or item.child_by_field_name("name")
        names = re.findall(r"[A-Za-z_]\w*", _text(target))
        if names:
            result.add(names[-1])
    return result


def _declarators(node):
    result = []
    for child in node.named_children:
        if child.type not in {"init_declarator", "variable_declarator", "identifier", "array_declarator", "function_declarator"}:
            continue
        name = child.child_by_field_name("declarator") or child.child_by_field_name("name") or child
        while name.type in {"pointer_declarator", "reference_declarator", "array_declarator", "function_declarator"}:
            name = name.child_by_field_name("declarator") or name.named_children[-1]
        if name.type == "identifier":
            result.append(_text(name))
    return result


def extract_core_scope(source: str, language: str) -> CoreScope:
    if language.lower() in {"python", "py"}:
        return _python_scope(source)
    analyzer = ASTComplexityAnalyzer(source, language, strict_structural=True)
    if analyzer.tree is None or analyzer.tree.root_node.has_error:
        return CoreScope(source, source, issues=["core-scope:parse-unavailable"])
    root = analyzer.tree.root_node
    functions = [n for n in _walk(root) if n.type in {
        "function_definition", "method_declaration", "function_declaration", "method_definition",
    }]
    names = [_function_name(n) for n in functions]
    if not functions:
        return CoreScope(source, source, issues=["core-scope:no-explicit-entry"])
    if len(set(names)) != len(names):
        return CoreScope(source, source, issues=["core-scope:overloaded-entry"])
    by_name = dict(zip(names, functions))
    if "main" in by_name:
        entry = "main"
    else:
        called = set().union(*(_calls(n) - {name} for name, n in by_name.items()))
        roots = set(names) - called
        if len(roots) != 1:
            return CoreScope(source, source, issues=["core-scope:ambiguous-entry"])
        entry = roots.pop()
    reachable, pending = set(), [entry]
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        pending.extend((_calls(by_name[name]) & by_name.keys()) - reachable)

    inputs, outputs, issues = set(), set(), []
    auxiliary_copy = False
    entry_node = by_name[entry]
    for node in _walk(entry_node):
        text = _text(node)
        if node.type == "expression_statement" and re.match(r"\s*(?:std::)?cin\s*>>", text):
            inputs.update(re.findall(r">>\s*([A-Za-z_]\w*)", text))
        if node.type == "if_statement" and re.search(r"\bcin\s*>>", text):
            inputs.update(re.findall(r">>\s*([A-Za-z_]\w*)", text))
        if node.type in {"declaration", "local_variable_declaration", "lexical_declaration", "variable_declaration"}:
            if re.search(r"\.(?:nextInt|nextLong|nextDouble|nextLine|next)\s*\(\s*\)", text):
                inputs.update(_declarators(node))
        if node.type == "expression_statement" and re.match(r"\s*(?:std::)?scanf\s*\(", text):
            inputs.update(re.findall(r"&\s*([A-Za-z_]\w*)", text))
        if node.type == "expression_statement":
            line_input = re.match(r"\s*(?:std::)?getline\s*\(\s*(?:std::)?cin\s*,\s*(\w+)\s*\)", text)
            if line_input:
                inputs.add(line_input.group(1))
            scanner_input = re.fullmatch(r"\s*(\w+)(?:\[[^\]]+\])?\s*=\s*\w+\.(?:nextInt|nextLong|nextDouble|nextLine|next)\s*\(\s*\)\s*;", text)
            if scanner_input:
                inputs.add(scanner_input.group(1))
        if node.type == "return_statement":
            match = re.fullmatch(r"return\s+([A-Za-z_]\w*)\s*;", text.strip())
            if match:
                outputs.add(match.group(1))
        if node.type == "expression_statement" and re.match(r"\s*(?:std::)?cout\s*<<", text):
            outputs.update(re.findall(r"<<\s*([A-Za-z_]\w*)\s*\[", text))

    declaration_types = {"declaration", "local_variable_declaration", "lexical_declaration", "variable_declaration"}
    statement_containers = {"compound_statement", "block", "program", "statement_block"}
    # A by-value copy of a one-dimensional input container is real scratch
    # storage. Library sort's stack bound cannot erase that allocation.
    for node in _walk(entry_node):
        if node.type in declaration_types:
            text = _text(node)
            if re.search(r"\b(?:vector|string)\s*(?:<[^<>]+>)?\s+\w+\s*=\s*(\w+)\s*;", text):
                match = re.search(r"=\s*(\w+)\s*;", text)
                if match.group(1) in inputs and not set(_declarators(node)) <= outputs:
                    auxiliary_copy = True

    def rewrite(node, *, space=False):
        text = _text(node)
        if node.type in {"comment", "preproc_include", "import_declaration"}:
            return text
        if node.type in declaration_types:
            declared = _declarators(node)
            if re.search(r"\b(?:Scanner|BufferedReader|InputStreamReader)\b", text) and re.search(r"\bSystem\.in\b", text):
                return ""
            if declared and all(name in inputs for name in declared) and entry == "main" and active_name == entry:
                if _calls(node) - {"vector", "nextInt", "nextLong", "nextDouble", "nextLine", "next"}:
                    issues.append("core-scope:mixed-input-initializer")
                    return text
                return ""
            if space and active_name == entry and declared and all(name in outputs for name in declared):
                if _calls(node) & reachable:
                    return text
                return ""
        if node.type == "expression_statement":
            if re.match(r"\s*(?:std::)?(?:cin\s*>>|scanf\s*\()", text):
                return ""
            if re.fullmatch(r"\s*(?:std::)?getline\s*\(\s*(?:std::)?cin\s*,\s*\w+\s*\)\s*;", text):
                return ""
            if re.fullmatch(r"\s*\w+(?:\[[^\]]+\])?\s*=\s*\w+\.(?:nextInt|nextLong|nextDouble|nextLine|next)\s*\(\s*\)\s*;", text):
                return ""
            if re.search(r"(?:sync_with_stdio\s*\(|\bcin\s*\.\s*tie\s*\()", text):
                return ""
            output = re.match(r"\s*(?:(?:std::)?cout\s*<<|(?:std::)?printf\s*\(|System\.out\.print(?:ln)?\s*\(|console\.log\s*\()", text)
            if output:
                # Retain the outermost algorithm calls used to compute output.
                def retained_calls(item):
                    if item.type in {"call_expression", "method_invocation"}:
                        target = item.child_by_field_name("function") or item.child_by_field_name("name")
                        if re.findall(r"\w+", _text(target))[-1:] and re.findall(r"\w+", _text(target))[-1] in reachable:
                            return [_text(item) + ";"]
                    return [value for child in item.named_children for value in retained_calls(child)]
                calls = retained_calls(node)
                if calls:
                    return " ".join(calls)
                # Arithmetic or unknown calls in output are not proven I/O-only.
                clean = re.sub(r"'[^']*'|\"[^\"]*\"", "", text)
                if re.search(r"[+*/%]|(?<![<>=!])-", clean) or (_calls(node) - {"printf", "println", "print", "log"}):
                    issues.append("core-scope:computed-output")
                    return text
                return ""
            if space:
                receiver = re.match(r"\s*([A-Za-z_]\w*)\s*\.\s*(?:push_back|append|add|insert|reserve|resize)\s*\(", text)
                if receiver and active_name == entry and receiver.group(1) in outputs and not (_calls(node) & reachable):
                    return ""
        if node.type == "if_statement" and re.search(r"\bcin\s*>>", text):
            if re.fullmatch(r"if\s*\(.*?cin\s*>>[^;{}]+\)\s*(?:\{\s*)?return\s+\d+\s*;\s*\}?", text, re.S):
                return ""
            issues.append("core-scope:mixed-input-control")
        body = node.child_by_field_name("body")
        if node.type in {"for_statement", "enhanced_for_statement", "while_statement", "do_statement"} and body is not None:
            changed = rewrite(body, space=space)
            if not changed.strip().strip("{} \n\t"):
                return ""
            return _replace(text, [(body.start_byte-node.start_byte, body.end_byte-node.start_byte, changed)])
        if node.type in statement_containers or node.type == "if_statement":
            if node.type == "if_statement":
                consequence = node.child_by_field_name("consequence")
                alternative = node.child_by_field_name("alternative")
                if consequence is not None and not rewrite(consequence, space=space).strip().strip("{} \n\t"):
                    if alternative is None or not rewrite(alternative, space=space).strip().strip("{} \n\t"):
                        # The condition could itself do algorithm work.
                        condition = node.child_by_field_name("condition")
                        return (_text(condition) + ";") if condition is not None and _calls(condition) else ""
            changes = []
            for child in node.named_children:
                value = rewrite(child, space=space)
                if value != _text(child):
                    changes.append((child.start_byte-node.start_byte, child.end_byte-node.start_byte, value))
            return _replace(text, changes)
        return text

    edits, space_edits = [], []
    for name, node in by_name.items():
        active_name = name
        if name not in reachable:
            edits.append((node.start_byte, node.end_byte, ""))
            space_edits.append((node.start_byte, node.end_byte, ""))
            continue
        body = node.child_by_field_name("body")
        if body is None:
            issues.append("core-scope:missing-body")
            continue
        edits.append((body.start_byte, body.end_byte, rewrite(body)))
        space_edits.append((body.start_byte, body.end_byte, rewrite(body, space=True)))
        if name == "main":
            # Prevent whole-program/input-allocation shortcuts from firing.
            decl = node.child_by_field_name("declarator")
            if decl is not None:
                replacement = re.sub(r"\bmain\b", "core_entry", _text(decl), count=1)
                edits.append((decl.start_byte, decl.end_byte, replacement))
                space_edits.append((decl.start_byte, decl.end_byte, replacement))
            else:
                name_node = node.child_by_field_name("name")
                if name_node is not None:
                    edits.append((name_node.start_byte, name_node.end_byte, "core_entry"))
                    space_edits.append((name_node.start_byte, name_node.end_byte, "core_entry"))
    if re.search(r"\b(?:readFileSync|readAllBytes|fread)\s*\(", source):
        issues.append("core-scope:bulk-input-wrapper")
    core, storage = _replace(source, edits), _replace(source, space_edits)
    for sliced in (core, storage):
        parsed = ASTComplexityAnalyzer(sliced, language, strict_structural=True)
        if parsed.tree is None or parsed.tree.root_node.has_error:
            issues.append("core-scope:incomplete-slice")
    return CoreScope(core, storage, inputs, outputs, list(dict.fromkeys(issues)), auxiliary_copy)


def _python_scope(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return CoreScope(source, source, issues=["core-scope:parse-unavailable"])
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    def calls(node):
        return {c.func.id if isinstance(c.func, ast.Name) else c.func.attr
                for c in ast.walk(node) if isinstance(c, ast.Call) and isinstance(c.func, (ast.Name, ast.Attribute))}
    called = set().union(*(calls(n) - {name} for name, n in funcs.items())) if funcs else set()
    roots = {"main"} if "main" in funcs else set(funcs) - called
    if len(roots) > 1:
        return CoreScope(source, source, issues=["core-scope:ambiguous-entry"])
    reachable, pending = set(), list(roots)
    while pending:
        name = pending.pop()
        if name not in reachable:
            reachable.add(name)
            pending.extend((calls(funcs[name]) & funcs.keys()) - reachable)
    inputs, outputs, issues = set(), set(), []
    entry = funcs[next(iter(roots))] if roots else tree
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "input" for n in ast.walk(node.value)):
            if calls(node.value) <= {"input", "int", "float", "str", "list", "tuple", "map", "split", "strip", "rstrip"}:
                inputs.update(n.id for target in node.targets for n in ast.walk(target) if isinstance(n, ast.Name))
            else:
                issues.append("core-scope:mixed-input-initializer")
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Name):
            outputs.add(node.value.id)

    class Slice(ast.NodeTransformer):
        def __init__(self, space=False):
            self.space = space
        def visit_FunctionDef(self, node):
            if node.name not in reachable:
                return None
            node = self.generic_visit(node)
            node.body = node.body or [ast.Pass()]
            if node.name == "main":
                node.name = "core_entry"
            return node
        def visit_Assign(self, node):
            names = {n.id for target in node.targets for n in ast.walk(target) if isinstance(n, ast.Name)}
            is_input_read = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "input" for n in ast.walk(node.value))
            if names and names <= inputs and is_input_read:
                return None
            if self.space and names and names <= outputs and not calls(node):
                return None
            return self.generic_visit(node)
        def visit_Expr(self, node):
            value = node.value
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "print":
                keep = [ast.Expr(value=arg) for arg in value.args if isinstance(arg, ast.Call)]
                if any(isinstance(arg, (ast.BinOp, ast.ListComp, ast.GeneratorExp)) for arg in value.args):
                    issues.append("core-scope:computed-output")
                    return node
                return keep or None
            if self.space and isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) and isinstance(value.func.value, ast.Name) and value.func.value.id in outputs:
                return None
            return node
        def visit_For(self, node):
            node = self.generic_visit(node)
            return node if node.body else None
        visit_While = visit_For
        def visit_If(self, node):
            if isinstance(node.test, ast.Compare) and any(isinstance(n, ast.Name) and n.id == "__name__" for n in ast.walk(node.test)):
                return None
            node = self.generic_visit(node)
            if not node.body and not node.orelse:
                return None
            node.body = node.body or [ast.Pass()]
            return node
    def render(space):
        result = Slice(space).visit(ast.parse(source))
        ast.fix_missing_locations(result)
        return ast.unparse(result)
    core, storage = render(False), render(True)
    try:
        ast.parse(core)
        ast.parse(storage)
    except SyntaxError:
        issues.append("core-scope:incomplete-slice")
    if re.search(r"\bsys\.stdin\b", source):
        issues.append("core-scope:bulk-input-wrapper")
    return CoreScope(core, storage, inputs, outputs, list(dict.fromkeys(issues)))
