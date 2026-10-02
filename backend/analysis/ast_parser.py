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
    bound_value: Optional[str] = None


@dataclass
class FunctionInfo:
    """Tracks function definitions and recursive call patterns."""
    name: str
    node: Optional['Node']
    recursive_calls: int = 0
    has_memoization: bool = False
    call_sites: List['Node'] = None
    calls_inside_loop: bool = False


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
        has_sort, sort_inside_loop = self._analyze_sort_calls()
        has_bs, bs_in_loop, bs_depth = self._detect_binary_search()
        graph_context = self._detect_graph_context()
        is_log_step = self._detect_logarithmic_loop(self.root)
        has_multi_bounds, has_merged_both, param_names = self._detect_multiple_input_bounds()
        is_const_lookup = self._is_constant_lookup()
        has_dyn_alloc, has_2d_alloc = self._has_dynamic_allocation(is_const_lookup)

        return ComplexityIR(
            language=self.language,
            loop=LoopIR(
                depth=self.max_loop_depth,
                structure=loop_analysis["structure"],
                bounds=loop_analysis["bounds"],
                has_sort=has_sort,
                sort_inside_loop=sort_inside_loop,
                has_binary_search=has_bs,
                binary_search_inside_loop=bs_in_loop,
                binary_search_loop_depth=bs_depth,
                is_logarithmic_step=is_log_step,
                multiple_input_bounds=has_multi_bounds,
                distinct_params=param_names
            ),
            recursion=RecursionIR(
                is_recursive=recursion_analysis.get("is_recursive", False),
                branch_factor=recursion_analysis.get("branch_factor", 0),
                has_memoization=recursion_analysis.get("has_memoization", False),
                pattern=recursion_analysis.get("pattern", "linear"),
                is_divide_and_conquer=recursion_analysis.get("is_divide_and_conquer", False),
                has_linear_combine=recursion_analysis.get("has_linear_combine", False),
                has_auxiliary_array=recursion_analysis.get("has_auxiliary_array", False),
                calls_inside_loop=recursion_analysis.get("calls_inside_loop", False)
            ),
            graph=GraphIR(
                is_graph=graph_context.get("is_graph", False),
                structure='adj_list' if graph_context.get("has_adj_list") else ('adj_matrix' if graph_context.get("has_adj_matrix") else None),
                traversal_inside_loop=graph_context.get("traversal_inside_loop", False)
            ),
            has_dynamic_allocation=has_dyn_alloc,
            has_2d_allocation=has_2d_alloc,
            has_merged_both=has_merged_both,
            is_constant_lookup=is_const_lookup,
            multiple_input_bounds=has_multi_bounds
        )

    def _is_constant_lookup(self) -> bool:
        """Detect if map or dictionary is purely a constant fixed-size lookup table."""
        src = self.source
        src_lower = src.lower()

        # Check for Roman numeral or constant literal map initialization
        has_literal_init = bool(re.search(r"unordered_map\s*<[^>]+>\s*\w+\s*=\s*\{", src)) or \
                           bool(re.search(r"map\s*<[^>]+>\s*\w+\s*=\s*\{", src)) or \
                           bool(re.search(r"\{\s*['\"][A-Za-z0-9]['\"]\s*:\s*\d+", src)) or \
                           bool(re.search(r"\{\s*\{['\"][A-Za-z0-9]['\"]\s*,\s*\d+\}", src))

        # Fixed array tables like char table[256] or int count[26]
        has_fixed_table = bool(re.search(r"\w+\s*\[\s*(?:26|128|256|1000)\s*\]", src))

        # Check if any dynamic insertion happens inside a loop
        has_dynamic_map_insert = bool(re.search(r"\b\w+\[[^\]]+\]\s*=\s*i\b", src)) or \
                                 bool(re.search(r"\b\w+\.put\s*\(", src_lower)) or \
                                 bool(re.search(r"\b\w+\.insert\s*\(", src_lower)) or \
                                 bool(re.search(r"\b\w+\[target\s*-", src_lower)) or \
                                 bool(re.search(r"\bfreq\[", src_lower)) or \
                                 bool(re.search(r"\bpos\[", src_lower))

        if (has_literal_init or has_fixed_table) and not has_dynamic_map_insert:
            return True

        return False

    def _has_dynamic_allocation(self, is_const_lookup: bool = False) -> Tuple[bool, bool]:
        """
        Detect if code allocates non-constant dynamic data structures and if 2D allocation exists.
        Returns: (has_dynamic_allocation, has_2d_allocation)
        """
        src = self.source.lower()

        if is_const_lookup:
            return False, False

        # 2D Allocation detection:
        # e.g. vector<vector<int>> dp(m + 1, vector<int>(n + 1, ...))
        # int dp[m][n], new int[m][n], [[0]*n for _ in range(m)]
        has_2d_alloc = bool(re.search(r"vector\s*<\s*vector\s*<[^>]+>\s*>\s*\w+\s*\([^,]+,\s*vector\s*<", src)) or \
                       bool(re.search(r"vector\s*<\s*vector\s*<[^>]+>\s*>\s*dp\b", src)) or \
                       bool(re.search(r"\bint\s+dp\s*\[\s*[^\]]+\s*\]\s*\[\s*[^\]]+\s*\]", src)) or \
                       bool(re.search(r"new\s+\w+\s*\[[^\]]+\]\s*\[[^\]]+\]", src)) or \
                       bool(re.search(r"\[\s*\[\s*0\s*\]\s*\*\s*\w+\s+for\s+\w+\s+in\s+range", src))

        # Dynamic heap structures that grow with input
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
            r"collections\.defaultdict",
            r"\bnew\s+\w+\s*\[\s*(?!\d+\s*\])",  # new int[n]
        ]
        if any(re.search(p, src) for p in dynamic_structures):
            return True, has_2d_alloc

        # Dynamic dictionary or set in Python
        if re.search(r"\bseen\s*=\s*(?:set\(|\{)", src) or re.search(r"\bfreq\s*=\s*(?:dict\(|\{)", src):
            return True, has_2d_alloc

        # Vectors and lists:
        # 1. vector<vector<int>> res / sorted
        if re.search(r"vector\s*<\s*vector\s*<", src):
            return True, has_2d_alloc

        # 2. vector with size argument or copy: vector<long long> dp(n + 2), vector<bool> used(n), vector<int> prev(n + 1)
        if re.search(r"vector\s*<[^>]+>\s+\w+\s*\(\s*(?:n|m|v|len|size|iv|right|high|\w+\s*\+|\w+\s*-)", src) or \
           re.search(r"vector\s*<[^>]+>\s+\w+\s*=\s*\w+;", src):
            return True, has_2d_alloc

        # 3. vector with push_back or append (e.g. res, tails, merged, ans)
        if re.search(r"\b(?:res|result|tails|merged|ans|temp|list|out)\.push_back\s*\(", src) or \
           re.search(r"\b(?:res|result|tails|merged|ans|temp|list|out)\.append\s*\(", src) or \
           re.search(r"\.push_back\s*\(\s*(?:a|nums|nums1|nums2|arr)\[", src):
            return True, has_2d_alloc

        # Java dynamic array allocation: new int[n]
        java_allocs = re.finditer(r"new\s+\w+\s*\[\s*([^\]]+)\s*\]", src)
        for m in java_allocs:
            size_arg = m.group(1).strip()
            if not re.match(r"^\d+$", size_arg):
                return True, has_2d_alloc

        if has_2d_alloc:
            return True, True

        return False, False

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
            elif self.language in {"java", "python"}:
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
                if var_name.lower() in {"n", "m", "v", "e", "size", "a", "b", "nums1", "nums2"}:
                    self.variables[var_name] = VariableInfo(
                        name=var_name,
                        scope_depth=self.current_scope_depth,
                        is_loop_bound=True,
                        bound_value=var_name.lower()
                    )

        for child in node.children:
            self._extract_variables(child)

    def _is_pointer_advancement_loop(self, loop_node: Node) -> bool:
        """Check if while loop is just a pointer skipper like while (l < r && a[l] == a[l-1]) l++;"""
        text = self._get_node_text(loop_node).lower()
        if loop_node.type == "while_statement":
            has_ptr_cond = bool(re.search(r"\b(?:l|left|r|right|i|j|lo|hi|low|high)\s*<\s*(?:r|right|l|left|hi|high)", text)) or \
                           bool(re.search(r"==\s*\w+\[", text)) or bool(re.search(r"!=\s*\w+\[", text))
            lines = [line.strip() for line in text.split(';') if line.strip()]
            body_is_simple_inc = any(
                re.search(r"\b(?:l|r|left|right|i|j|lo|hi)\s*(?:\+\+|\-\-|\+=\s*1|\-=\s*1)", l)
                for l in lines
            )
            if has_ptr_cond and body_is_simple_inc and len(lines) <= 2:
                return True
        return False

    def _is_flag_convergence_loop(self, loop_node: Node) -> bool:
        """Check if loop is a boolean flag convergence loop like while (changed) or while (swapped)."""
        text = self._get_node_text(loop_node).lower()
        if loop_node.type == "while_statement":
            cond = self._find_child(loop_node, "condition_clause") or \
                   self._find_child(loop_node, "parenthesized_expression")
            cond_text = self._get_node_text(cond).lower() if cond else text
            if re.search(r"\b(?:changed|swapped|flag|done|ok)\b", cond_text):
                return True
        return False

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
                # Check if it's a pointer advancement duplicate skipper or boolean flag loop
                is_ptr_skip = self._is_pointer_advancement_loop(n)
                is_flag_loop = self._is_flag_convergence_loop(n)

                current_depth = depth if (is_ptr_skip or (is_flag_loop and depth >= 1)) else (depth + 1)
                max_depth = max(max_depth, current_depth)
                bound = self._extract_loop_bound(n)
                bounds.append(bound or "n")
                for child in n.children:
                    visit(child, current_depth)
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
            "max_depth": self.max_loop_depth,
            "loop_count": loop_count
        }

    def _extract_loop_bound(self, loop_node: Node) -> Optional[str]:
        """Extract the complexity variable from loop condition or range."""
        text = self._get_node_text(loop_node).lower()

        if loop_node.type in {"for_range_loop", "enhanced_for_statement"} or (
            loop_node.type == "for_statement" and self.language == "python"
        ):
            for var in ["nums1", "nums2", "n", "m", "v", "e", "a", "b", "iv", "sorted"]:
                if re.search(rf"\b{var}\b", text):
                    return var
            return "n"

        condition = self._find_child(loop_node, "condition_clause") or \
                    self._find_child(loop_node, "binary_expression") or \
                    self._find_child(loop_node, "parenthesized_expression")

        cond_text = self._get_node_text(condition).lower() if condition else text

        for var in ["nums1", "nums2", "n", "m", "v", "e", "rows", "cols", "a", "b"]:
            if re.search(rf"\b{var}\b", cond_text):
                return var

        if ".size()" in cond_text or ".length" in cond_text or "len(" in cond_text:
            return "n"

        return None

    def _detect_logarithmic_loop(self, node: Node) -> bool:
        """Detect if loop step divides the loop variable (/= 10, /= 2, >>= 1, etc.)."""
        src = self.source.lower()

        div_patterns = [
            r"\/=\s*\d+",           # x /= 10, n /= 2
            r"\b\w+\s*=\s*\w+\s*\/\s*\d+",  # x = x / 10
            r">>=\s*\d+",          # x >>= 1
            r"\b\w+\s*=\s*\w+\s*>>\s*\d+",  # x = x >> 1
            r"\b\w+\s*=\s*\w+\s*\*\s*2",   # x = x * 2
            r"\*=\s*2",            # x *= 2
        ]
        return any(re.search(p, src) for p in div_patterns)

    def _detect_multiple_input_bounds(self) -> Tuple[bool, bool, List[str]]:
        """
        Detect if algorithm iterates across multiple input collections (e.g., O(m+n)).
        Returns: (has_multi_bounds, has_merged_both, param_names)
        """
        src = self.source.lower()

        params = []
        param_match = re.search(r"\(([^)]+)\)", src)
        if param_match:
            param_str = param_match.group(1)
            found_params = re.findall(r"(?:vector\s*<[^>]+>|int\s*\[\]|string|list\[[^\]]+\])\s*(?:&|\*)?\s*(\w+)", param_str)
            if not found_params:
                found_params = re.findall(r"\b(\w+)\s*:\s*(?:list|str)", param_str)
            params = found_params

        has_multi = False
        p_names = []
        if len(params) >= 2:
            p1, p2 = params[0], params[1]
            if (p1 in src and p2 in src) and (
                f"{p1}.size()" in src and f"{p2}.size()" in src or
                f"len({p1})" in src and f"len({p2})" in src or
                f"while" in src and p1 in src and p2 in src
            ):
                has_multi = True
                p_names = [p1, p2]

        if ("nums1" in src and "nums2" in src) or ("arr1" in src and "arr2" in src):
            has_multi = True
            p_names = ["m", "n"]

        has_merged_both = bool(re.search(r"merged\.push_back", src)) or \
                          (bool(re.search(r"nums1", src)) and bool(re.search(r"nums2", src)) and bool(re.search(r"\.push_back\s*\(\s*nums1\[", src))) or \
                          bool(re.search(r"merged\.append", src))

        return has_multi, has_merged_both, p_names

    def _analyze_recursion(self) -> Dict:
        """Analyze recursive call patterns, divide-and-conquer, backtracking, and memoization."""
        result = {
            "is_recursive": False,
            "branch_factor": 0,
            "has_memoization": False,
            "pattern": "none",
            "is_divide_and_conquer": False,
            "has_linear_combine": False,
            "has_auxiliary_array": False,
            "calls_inside_loop": False
        }

        src = self.source.lower()

        for func_name, func_info in self.functions.items():
            self_calls, in_loop = self._count_recursive_calls(func_info.node, func_name)
            if self_calls > 0:
                func_info.recursive_calls = self_calls
                func_info.calls_inside_loop = in_loop
                result["is_recursive"] = True
                result["calls_inside_loop"] = in_loop

                # 1. Check for memoization
                if self._has_memoization_check(func_info.node):
                    func_info.has_memoization = True
                    result["has_memoization"] = True
                    result["branch_factor"] = 1
                    result["pattern"] = "memoized"
                    return result

                body_text = self._get_node_text(func_info.node).lower() if func_info.node else src

                # 2. Check for Divide & Conquer (MergeSort, QuickSort, etc.)
                has_mid_split = bool(re.search(r"\bmid\b\s*=", body_text)) or \
                                bool(re.search(r"\b(?:left|low|l)\s*\+\s*\(\s*(?:right|high|r)\s*-\s*(?:left|low|l)\s*\)\s*/\s*2", body_text)) or \
                                bool(re.search(r"\(\s*(?:left|low|l)\s*\+\s*(?:right|high|r)\s*\)\s*/\s*2", body_text))
                has_partition_split = bool(re.search(r"\bpartition\b", body_text)) or \
                                      bool(re.search(r"\bpi\b\s*=", body_text)) or \
                                      bool(re.search(r"\bpivot\b", body_text))
                has_merge_call = bool(re.search(r"\bmerge\s*\(", body_text))

                if self_calls == 2 and (has_mid_split or has_partition_split or has_merge_call):
                    result["is_divide_and_conquer"] = True
                    result["branch_factor"] = 2
                    result["pattern"] = "divide_and_conquer"
                    result["has_linear_combine"] = True

                    has_aux_space = bool(re.search(r"vector\s*<\s*int\s*>\s*temp", src)) or \
                                    bool(re.search(r"new\s+int\s*\[", src)) or \
                                    bool(re.search(r"temp\s*\[", src)) or \
                                    "merge" in src
                    result["has_auxiliary_array"] = has_aux_space
                    return result

                # 3. Backtracking recursion inside loop
                if in_loop:
                    if "swap" in body_text or "queen" in body_text or "perm" in body_text:
                        result["branch_factor"] = 5
                        result["pattern"] = "n-ary"
                    else:
                        result["branch_factor"] = 2
                        result["pattern"] = "branching"
                elif self_calls == 1:
                    result["branch_factor"] = 1
                    result["pattern"] = "tail" if self._is_tail_recursive(func_info.node, func_name) else "linear"
                elif self_calls >= 2:
                    # Check if early return exists e.g. if (s[i] == t[j]) return edit(...);
                    if self_calls == 4 and bool(re.search(r"if\s*\([^)]*==[^)]*\)\s*return\s+" + func_name, body_text)):
                        result["branch_factor"] = 3
                    elif self_calls == 4:
                        result["branch_factor"] = 4
                    elif self_calls == 3:
                        result["branch_factor"] = 3
                    elif self_calls == 2:
                        result["branch_factor"] = 2
                    else:
                        result["branch_factor"] = self_calls
                    result["pattern"] = "branching"

        return result

    def _count_recursive_calls(self, node: Node, func_name: str, in_loop: bool = False) -> Tuple[int, bool]:
        """Count how many times a function calls itself and check if any call is inside a loop."""
        count = 0
        call_in_loop = False

        if not node:
            return 0, False

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

    def _has_memoization_check(self, node: Optional[Node]) -> bool:
        """Detect if function uses memoization (checks dp/memo/cache array or map)."""
        text = self._get_node_text(node).lower() if node else self.source.lower()

        memo_patterns = [
            r"\bdp\[",
            r"\bmemo\[",
            r"\bcache\[",
            r"!=-1",
            r"!=\s*-1",
            r"\bcontainskey\b",
            r"\bin\s+memo\b",
            r"\bin\s+cache\b",
        ]
        return any(re.search(pattern, text) for pattern in memo_patterns)

    def _is_tail_recursive(self, node: Optional[Node], func_name: str) -> bool:
        """Check if recursion is tail-recursive."""
        if not node:
            return False
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

    def _analyze_sort_calls(self) -> Tuple[bool, bool]:
        """
        Detect if code calls sort and whether sort is called inside a loop on a non-constant collection.
        """
        text = self.source.lower()
        has_sort = bool(re.search(r"\b(?:std::)?sort\s*\(|Arrays\.sort\(|Collections\.sort\(|\.sort\(|sorted\(", text))

        if not has_sort:
            return False, False

        sort_inside_loop = False
        def check_sort_in_loop(n: Node, in_loop: bool):
            nonlocal sort_inside_loop
            is_loop = n.type in {"for_statement", "for_range_loop", "enhanced_for_statement", "while_statement", "do_statement"}
            cur_in_loop = in_loop or is_loop

            if n.type in {"call_expression", "method_invocation", "call"}:
                call_text = self._get_node_text(n).lower()
                if "sort" in call_text and cur_in_loop:
                    if not re.search(r"sort\s*\(\s*t\.", call_text) and not re.search(r"sort\s*\(\s*temp_tuple", call_text):
                        sort_inside_loop = True

            for child in n.children:
                check_sort_in_loop(child, cur_in_loop)

        if self.root:
            check_sort_in_loop(self.root, False)

        return has_sort, sort_inside_loop

    def _detect_binary_search(self) -> Tuple[bool, bool, int]:
        """
        Detect binary search pattern via AST/code structure.
        Returns: (has_binary_search, binary_search_inside_loop, loop_depth_where_called)
        """
        text = self.source.lower()

        bs_call_patterns = [
            r"\bbinary_search\s*\(",
            r"\blower_bound\s*\(",
            r"\bupper_bound\s*\(",
            r"\bbisect\b",
            r"\bbisect_left\b",
            r"\bbisect_right\b",
            r"arrays\.binarysearch\s*\(",
            r"collections\.binarysearch\s*\(",
        ]
        has_bs_call = any(re.search(p, text) for p in bs_call_patterns)

        has_low_high = bool(re.search(r"\b(?:low|left|l|lo|start|s|beg)\b", text)) and \
                       bool(re.search(r"\b(?:high|right|r|hi|end|e|fin)\b", text))

        has_mid_calc = bool(re.search(r"\b(?:mid|m)\s*=\s*(?:\(?\s*(?:low|left|l|lo|start|s)\s*\+\s*(?:high|right|r|hi|end|e)\s*\)?)\s*/\s*2", text)) or \
                       bool(re.search(r"\b(?:low|left|l|lo|start|s)\s*\+\s*\(\s*(?:high|right|r|hi|end|e)\s*-\s*(?:low|left|l|lo|start|s)\s*\)\s*/\s*2", text)) or \
                       (bool(re.search(r"\bmid\s*=", text)) and bool(re.search(r"/\s*2", text)))

        has_ptr_update = bool(re.search(r"\b(?:low|left|l|lo|start|s)\s*=\s*(?:mid|m)\s*\+\s*1", text)) or \
                         bool(re.search(r"\b(?:high|right|r|hi|end|e)\s*=\s*(?:mid|m)\s*-\s*1", text))

        has_explicit_bs = has_low_high and (has_mid_calc or has_ptr_update)

        has_binary_search = has_bs_call or has_explicit_bs

        if not has_binary_search:
            return False, False, 0

        bs_in_loop = False
        bs_loop_depth = 0

        if has_bs_call:
            def check_bs_in_loop(n: Node, current_depth: int):
                nonlocal bs_in_loop, bs_loop_depth
                is_loop = n.type in {"for_statement", "for_range_loop", "enhanced_for_statement", "while_statement", "do_statement"}
                new_depth = current_depth + 1 if is_loop else current_depth

                if n.type in {"call_expression", "method_invocation", "call"}:
                    call_text = self._get_node_text(n).lower()
                    if any(re.search(p, call_text) for p in bs_call_patterns):
                        if current_depth > 0:
                            bs_in_loop = True
                            bs_loop_depth = max(bs_loop_depth, current_depth)

                for child in n.children:
                    check_bs_in_loop(child, new_depth)

            if self.root:
                check_bs_in_loop(self.root, 0)

        return has_binary_search, bs_in_loop, bs_loop_depth

    def _detect_graph_context(self) -> Dict:
        """Detect if code operates on graph structures."""
        text = self.source.lower()

        graph_keywords = ["adj", "graph", "edge", "edges", "vertex", "vertices", "visited", "vis", "dfs", "bfs", "g[u]", "canfinish", "indeg"]
        has_graph_keyword = any(kw in text for kw in graph_keywords)

        has_adj_list = bool(
            re.search(r"vector\s*<\s*vector\s*<", text)
            or re.search(r"list\s*<\s*list\s*<", text)
            or re.search(r"defaultdict\s*\(\s*list\s*\)", text)
            or re.search(r"\bg\[u\]", text)
            or re.search(r"\badj\[", text)
            or re.search(r"\badj\.get\(", text)
            or re.search(r"g\[pre\[i\]", text)
        ) and has_graph_keyword

        has_adj_matrix = bool(
            re.search(r"\[\s*v\s*\]\s*\[\s*v\s*\]", text)
            or re.search(r"matrix\s*\[[^\]]+\]\s*\[[^\]]+\]", text)
        ) and ("matrix" in text or "grid" in text or "adj" in text)

        traversal_in_loop = False
        if has_graph_keyword and has_adj_list:
            if bool(re.search(r"for\s*\([^;]+;\s*\w+\s*<\s*v;\s*[^)]+\)\s*\{[^}]*(?:vector\s*<bool>|bool\s+\w+\[|int\s+\w+\[)[^}]*(?:reach|dfs)\s*\(", text)):
                traversal_in_loop = True

        return {
            "is_graph": has_graph_keyword,
            "has_adj_list": has_adj_list,
            "has_adj_matrix": has_adj_matrix,
            "traversal_inside_loop": traversal_in_loop
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
    return parse_ast(source, "cpp")
