"""
AST-based complexity analyzer using tree-sitter.
Supports C, C++, Java, and Python.
"""
import re
from typing import Optional, Set, Dict, List, Tuple
from dataclasses import dataclass
from .complexity_ir import ComplexityIR, LoopIR, RecursionIR, GraphIR

try:
    import tree_sitter
    import tree_sitter_c
    import tree_sitter_cpp
    import tree_sitter_java
    import tree_sitter_python
    from tree_sitter import Language, Parser, Node

    LANGUAGES = {
        "c": Language(tree_sitter_c.language()),
        "cpp": Language(tree_sitter_cpp.language()),
        "java": Language(tree_sitter_java.language()),
        "python": Language(tree_sitter_python.language()),
    }
    PARSERS = {lang: Parser(LANG) for lang, LANG in LANGUAGES.items()}
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False
    Node = None
    LANGUAGES = {}
    PARSERS = {}


@dataclass
class VariableInfo:
    """Tracks variable scope and bounds information."""
    name: str
    scope_depth: int
    is_loop_bound: bool = False
    bound_value: Optional[str] = None  # e.g., "n", "m", "V", "E"


@dataclass
class FunctionInfo:
    """Tracks function definitions and recursive call patterns."""
    name: str
    node: 'Node'
    recursive_calls: int = 0
    has_memoization: bool = False
    call_sites: List['Node'] = None
    calls_inside_loop: bool = False

    def __post_init__(self):
        if self.call_sites is None:
            self.call_sites = []


class ASTComplexityAnalyzer:
    """AST-based complexity analyzer supporting C, C++, Java, and Python."""

    def __init__(self, source: str, language: str = "cpp"):
        self.source = source
        self.source_bytes = source.encode('utf-8')
        self.language = self._normalize_language(language)

        self.parser = PARSERS.get(self.language) if AST_AVAILABLE else None
        self.tree = self.parser.parse(self.source_bytes) if self.parser else None
        self.root = self.tree.root_node if self.tree else None

        # Analysis state
        self.variables: Dict[str, VariableInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}
        self.loop_depth = 0
        self.max_loop_depth = 0
        self.current_scope_depth = 0

    def _normalize_language(self, language: str) -> str:
        lang = language.lower().strip()
        if lang in {"c"}:
            return "c"
        if lang in {"cpp", "c++", "cc", "cxx"}:
            return "cpp"
        if lang in {"java"}:
            return "java"
        if lang in {"python", "py"}:
            return "python"
        return "cpp"

    def analyze(self) -> Optional[ComplexityIR]:
        """Run full AST analysis and return ComplexityIR."""
        if not AST_AVAILABLE or not self.root:
            return None

        # Phase 1: Extract functions and variables
        self._extract_functions(self.root)
        self._extract_variables(self.root)

        # Phase 2: Analyze control flow
        loop_analysis = self._analyze_loops(self.root)
        recursion_analysis = self._analyze_recursion()

        # Phase 3: Detect patterns
        has_sort = self._has_sort_call()
        has_binary_search = self._detect_binary_search()
        graph_context = self._detect_graph_context()

        return ComplexityIR(
            language=self.language,
            loop=LoopIR(
                depth=self.max_loop_depth,
                structure=loop_analysis["structure"],
                bounds=loop_analysis["bounds"],
                has_sort=has_sort,
                has_binary_search=has_binary_search
            ),
            recursion=RecursionIR(
                is_recursive=recursion_analysis.get("is_recursive", False),
                branch_factor=recursion_analysis.get("branch_factor", 0),
                has_memoization=recursion_analysis.get("has_memoization", False),
                pattern=recursion_analysis.get("pattern", "linear")
            ),
            graph=GraphIR(
                is_graph=graph_context.get("is_graph", False),
                structure='adj_list' if graph_context.get("has_adj_list") else ('adj_matrix' if graph_context.get("has_adj_matrix") else None)
            ),
            has_dynamic_allocation=self._has_dynamic_allocation()
        )

    def _has_dynamic_allocation(self) -> bool:
        """Detect if code allocates non-constant dynamic data structures."""
        src = self.source.lower()

        # Dynamic heap structures
        dynamic_structures = [
            r"unordered_map\s*<",
            r"unordered_set\s*<",
            r"\bmap\s*<",
            r"\bset\s*<",
            r"\bqueue\s*<",
            r"\bstack\s*<",
            r"\bpriority_queue\s*<",
            r"hashmap\b",
            r"hashset\b",
            r"treemap\b",
            r"treeset\b",
            r"\bdict\s*\(",
            r"\{\s*:\s*\}",
            r"collections\.defaultdict",
            r"\bnew\s+\w+\s*\[\s*(?!\d+\s*\])",  # new int[n]
        ]
        if any(re.search(p, src) for p in dynamic_structures):
            return True

        # Check vectors with variable size (e.g. vector<int> dp(n) or vector<int> c(n, 1))
        # Ignore function return types like vector<int> f(string& s) and fixed-size vectors like vector<int> last(26)
        vector_matches = re.finditer(r"vector\s*<[^>]+>\s+\w+\s*\(\s*([^,\)]+)", src)
        for m in vector_matches:
            size_arg = m.group(1).strip()
            # Ignore function signatures
            if any(t in size_arg for t in ['int', 'string', 'char', 'auto', 'const', 'bool', 'float', 'double', '&', '*']):
                continue
            # If size_arg is purely a small constant number, it's O(1)
            if re.match(r"^\d+$", size_arg):
                val = int(size_arg)
                if val > 1000:
                    return True
            else:
                # Variable size like n, a.size(), g.size(), etc.
                return True

        # Java dynamic array allocation: new int[n]
        java_allocs = re.finditer(r"new\s+\w+\s*\[\s*([^\]]+)\s*\]", src)
        for m in java_allocs:
            size_arg = m.group(1).strip()
            if not re.match(r"^\d+$", size_arg):
                return True

        return False

    def _extract_functions(self, node: Node):
        """Extract function definitions across C, C++, Java, and Python."""
        func_name = None

        if node.type in {"function_definition", "method_declaration"}:
            if self.language in {"c", "cpp"}:
                declarator = self._find_child(node, "function_declarator")
                if declarator:
                    name_node = self._find_child(declarator, "identifier") or self._find_child(declarator, "field_identifier")
                    if name_node:
                        func_name = self._get_node_text(name_node)
            elif self.language == "java":
                name_node = self._find_child(node, "identifier")
                if name_node:
                    func_name = self._get_node_text(name_node)
            elif self.language == "python":
                name_node = self._find_child(node, "identifier")
                if name_node:
                    func_name = self._get_node_text(name_node)

            if func_name and func_name not in {"main"}:
                self.functions[func_name] = FunctionInfo(name=func_name, node=node)

        for child in node.children:
            self._extract_functions(child)

    def _extract_variables(self, node: Node):
        """Extract variable declarations and track loop bounds."""
        if node.type == "declaration":
            declarator = self._find_child(node, "init_declarator")
            if declarator:
                identifier = self._find_child(declarator, "identifier")
                if identifier:
                    var_name = self._get_node_text(identifier)
                    self.variables[var_name] = VariableInfo(
                        name=var_name,
                        scope_depth=self.current_scope_depth
                    )

        if node.type in {"parameter_declaration", "formal_parameter"}:
            identifier = self._find_child(node, "identifier")
            if identifier:
                var_name = self._get_node_text(identifier)
                if var_name.lower() in {"n", "m", "v", "e", "size"}:
                    self.variables[var_name] = VariableInfo(
                        name=var_name,
                        scope_depth=self.current_scope_depth,
                        is_loop_bound=True,
                        bound_value=var_name.lower()
                    )

        for child in node.children:
            self._extract_variables(child)

    def _analyze_loops(self, node: Node) -> Dict:
        """Analyze loop structure, sequential passes, and bounds."""
        bounds = []
        max_depth = 0
        loop_count = 0

        def visit(n: Node, depth: int):
            nonlocal max_depth, loop_count
            is_loop = n.type in {
                "for_statement", "for_range_loop", "enhanced_for_statement",
                "while_statement", "do_statement"
            }
            if is_loop:
                loop_count += 1
                max_depth = max(max_depth, depth + 1)
                bound = self._extract_loop_bound(n)
                bounds.append(bound or "n")
                for child in n.children:
                    visit(child, depth + 1)
            else:
                for child in n.children:
                    visit(child, depth)

        visit(node, 0)
        self.max_loop_depth = max_depth

        if max_depth == 0:
            structure = "none"
        elif max_depth >= 2:
            structure = "nested"
        elif loop_count > 1:
            structure = "sequential"
        else:
            structure = "single"

        return {
            "bounds": bounds,
            "structure": structure,
            "max_depth": self.max_loop_depth
        }

    def _extract_loop_bound(self, loop_node: Node) -> Optional[str]:
        """Extract the complexity variable from loop condition or range."""
        text = self._get_node_text(loop_node).lower()

        # Range-based loops (C++ / Java / Python)
        if loop_node.type in {"for_range_loop", "enhanced_for_statement"} or (
            loop_node.type == "for_statement" and self.language == "python"
        ):
            for var in ["n", "m", "v", "e"]:
                if re.search(rf"\b{var}\b", text):
                    return var
            return "n"

        condition = self._find_child(loop_node, "condition_clause") or \
                    self._find_child(loop_node, "binary_expression") or \
                    self._find_child(loop_node, "parenthesized_expression")

        cond_text = self._get_node_text(condition).lower() if condition else text

        for var in ["n", "m", "v", "e", "rows", "cols"]:
            if re.search(rf"\b{var}\b", cond_text):
                return var

        if ".size()" in cond_text or ".length" in cond_text or "len(" in cond_text:
            return "n"

        return None

    def _analyze_recursion(self) -> Dict:
        """Analyze recursive call patterns, backtracking, and memoization."""
        result = {
            "is_recursive": False,
            "branch_factor": 0,
            "has_memoization": False,
            "pattern": "none"
        }

        for func_name, func_info in self.functions.items():
            self_calls, in_loop = self._count_recursive_calls(func_info.node, func_name)
            if self_calls > 0:
                func_info.recursive_calls = self_calls
                func_info.calls_inside_loop = in_loop
                result["is_recursive"] = True

                # Check for memoization
                if self._has_memoization_check(func_info.node):
                    func_info.has_memoization = True
                    result["has_memoization"] = True
                    result["branch_factor"] = 1
                    result["pattern"] = "memoized"
                elif in_loop:
                    # Backtracking recursion inside loop
                    body_text = self._get_node_text(func_info.node).lower()
                    if "swap" in body_text or "queen" in body_text or "perm" in body_text or re.search(r"\[[^\]]+\]\s*\[[^\]]+\]", body_text):
                        # Permutations / N-Queens
                        result["branch_factor"] = 5
                        result["pattern"] = "n-ary"
                    elif "target" in body_text or "sum" in body_text or "subset" in body_text or "-" in body_text:
                        # Combination sum / subset recursion
                        result["branch_factor"] = 2
                        result["pattern"] = "branching"
                    else:
                        result["branch_factor"] = 5
                        result["pattern"] = "n-ary"
                elif self_calls == 1:
                    result["branch_factor"] = max(result["branch_factor"], 1)
                    result["pattern"] = "tail" if self._is_tail_recursive(func_info.node, func_name) else "linear"
                elif self_calls >= 2:
                    result["branch_factor"] = max(result["branch_factor"], self_calls)
                    result["pattern"] = "branching"

        return result

    def _count_recursive_calls(self, node: Node, func_name: str, in_loop: bool = False) -> Tuple[int, bool]:
        """Count how many times a function calls itself and check if any call is inside a loop."""
        count = 0
        call_in_loop = False

        is_loop = node.type in {
            "for_statement", "for_range_loop", "enhanced_for_statement",
            "while_statement", "do_statement"
        }
        current_in_loop = in_loop or is_loop

        if node.type in {"call_expression", "method_invocation", "call"}:
            fn_identifier = self._find_child(node, "identifier")
            if fn_identifier and self._get_node_text(fn_identifier) == func_name:
                count += 1
                if current_in_loop:
                    call_in_loop = True

        for child in node.children:
            sub_count, sub_in_loop = self._count_recursive_calls(child, func_name, current_in_loop)
            count += sub_count
            if sub_in_loop:
                call_in_loop = True

        return count, call_in_loop

    def _has_memoization_check(self, node: Node) -> bool:
        """Detect if function uses memoization (checks dp/memo/cache array or map)."""
        text = self._get_node_text(node).lower()

        memo_patterns = [
            r"\bdp\[",
            r"\bmemo\[",
            r"\bcache\[",
            r"\bmemo\b",
            r"\bdp\b",
            r"!=-1",
            r"!=\s*-1",
            r"\bcontainskey\b",
            r"\bin\s+memo\b",
            r"\bin\s+cache\b",
        ]
        return any(re.search(pattern, text) for pattern in memo_patterns)

    def _is_tail_recursive(self, node: Node, func_name: str) -> bool:
        """Check if recursion is tail-recursive."""
        returns = []
        self._find_all_returns(node, returns)

        for ret in returns:
            ret_text = self._get_node_text(ret)
            if re.search(rf"\breturn\s+{func_name}\s*\(", ret_text):
                return True
        return False

    def _find_all_returns(self, node: Node, results: List[Node]):
        """Find all return statement nodes."""
        if node.type in {"return_statement", "return"}:
            results.append(node)
        for child in node.children:
            self._find_all_returns(child, results)

    def _has_sort_call(self) -> bool:
        """Detect if code calls sort or sorted."""
        text = self.source.lower()
        return bool(re.search(r"\b(?:std::)?sort\s*\(|Arrays\.sort\(|Collections\.sort\(|\.sort\(|sorted\(", text))

    def _detect_binary_search(self) -> bool:
        """Detect binary search pattern via AST/code structure."""
        text = self.source.lower()

        has_low_high = ("low" in text or "left" in text or "l" in text) and \
                       ("high" in text or "right" in text or "r" in text)
        has_mid = "mid" in text or "m" in text
        has_mid_calc = bool(re.search(r"(?:mid|m)\s*=\s*(?:\(?\s*(?:low|left|l)\s*\+\s*(?:high|right|r)\s*\)?)\s*/\s*2", text)) or \
                       bool(re.search(r"(?:low|left|l)\s*\+\s*\(\s*(?:high|right|r)\s*-\s*(?:low|left|l)\s*\)\s*/\s*2", text))
        has_pointer_update = bool(re.search(r"(?:low|left|l)\s*=\s*(?:mid|m)\s*[+\-]", text)) or \
                             bool(re.search(r"(?:high|right|r)\s*=\s*(?:mid|m)\s*[+\-]", text))

        return has_low_high and (has_mid_calc or (has_mid and has_pointer_update))

    def _detect_graph_context(self) -> Dict:
        """Detect if code operates on graph structures."""
        text = self.source.lower()

        graph_keywords = ["adj", "graph", "edge", "edges", "vertex", "vertices", "visited", "vis", "dfs", "bfs", "g[u]"]
        has_graph_keyword = any(kw in text for kw in graph_keywords)

        # Adjacency list: vector<vector<...>>, List<List<...>>, defaultdict(list), or g[u] indexing
        has_adj_list = bool(
            re.search(r"vector\s*<\s*vector\s*<", text)
            or re.search(r"list\s*<\s*list\s*<", text)
            or re.search(r"defaultdict\s*\(\s*list\s*\)", text)
            or re.search(r"\bg\[u\]", text)
            or re.search(r"\badj\[", text)
            or re.search(r"\badj\.get\(", text)
        ) and has_graph_keyword

        # Adjacency matrix: 2D array [V][V] or matrix(V, vector<int>(V))
        has_adj_matrix = bool(
            re.search(r"\[\s*v\s*\]\s*\[\s*v\s*\]", text)
            or re.search(r"matrix\s*\[[^\]]+\]\s*\[[^\]]+\]", text)
        ) and ("matrix" in text or "grid" in text or "adj" in text)

        return {
            "is_graph": has_graph_keyword,
            "has_adj_list": has_adj_list,
            "has_adj_matrix": has_adj_matrix,
        }

    def _find_child(self, node: Node, child_type: str) -> Optional[Node]:
        """Find first child of given type."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _get_node_text(self, node: Node) -> str:
        """Get source text for a node."""
        return self.source_bytes[node.start_byte:node.end_byte].decode('utf-8')


def parse_ast(source: str, language: str = "cpp") -> Optional[ASTComplexityAnalyzer]:
    """Parse source in C, C++, Java, or Python and return AST analyzer."""
    if not AST_AVAILABLE:
        return None
    try:
        return ASTComplexityAnalyzer(source, language)
    except Exception:
        return None


def parse_cpp_ast(source: str) -> Optional[ASTComplexityAnalyzer]:
    """Legacy helper for C++ AST analysis."""
    return parse_ast(source, "cpp")
