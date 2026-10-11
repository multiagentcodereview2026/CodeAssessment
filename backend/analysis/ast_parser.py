import re
from typing import Dict, List, Optional, Set, Tuple, Any
from .complexity_ir import ComplexityIR, LoopIR, RecursionIR, GraphIR, ControlFlowIR
from .pattern_library import classify_pattern, detect_semantic_patterns
from .dependent_bounds import detect_dependent_bounds
from .library_costs import detect_library_costs

# Tree-sitter imports - handle gracefully if not available
AST_AVAILABLE = False
try:
    from tree_sitter import Language, Node, Parser, Tree
    AST_AVAILABLE = True
except Exception:
    # Tree-sitter not available - use regex fallback
    Node = type('Node', (), {})
    Parser = type('Parser', (), {})
    Tree = type('Tree', (), {})
    Language = type('Language', (), {})




def parse_cpp_ast(source: str):
    """Factory function for backward compatibility with static_analyzer_v2.py"""
    try:
        return ASTComplexityAnalyzer(source, 'cpp')
    except Exception:
        return None


class ASTComplexityAnalyzer:
    """
    AST-based complexity analyzer for multi-language code.
    Falls back to regex analysis when tree-sitter is unavailable.
    """

    def __init__(self, source_code: str, language: str = 'cpp'):
        self.source = source_code
        self.language = language.lower()
        self.parser = None
        self.tree = None
        self.use_ast = AST_AVAILABLE

        if AST_AVAILABLE:
            self._initialize_parser()

    def _initialize_parser(self) -> None:
        """Initialize tree-sitter parser for the given language."""
        if not AST_AVAILABLE:
            return

        lang_map = {
            'cpp': ('tree_sitter_cpp', 'language'),
            'c++': ('tree_sitter_cpp', 'language'),
            'c': ('tree_sitter_c', 'language'),
            'python': ('tree_sitter_python', 'language'),
            'py': ('tree_sitter_python', 'language'),
            'java': ('tree_sitter_java', 'language'),
            'javascript': ('tree_sitter_javascript', 'language'),
            'js': ('tree_sitter_javascript', 'language'),
        }

        lang_key = self.language.lower().strip()

        try:
            if lang_key in lang_map:
                mod_name, fn_name = lang_map[lang_key]
                mod = __import__(mod_name)
                lang_fn = getattr(mod, fn_name)
                ts_lang = Language(lang_fn())
                try:
                    self.parser = Parser(ts_lang)
                except Exception:
                    self.parser = Parser()
                    self.parser.set_language(ts_lang)

                self.tree = self.parser.parse(bytes(self.source, 'utf-8'))
                self.use_ast = True
                return
        except Exception:
            pass

        try:
            from tree_sitter_languages import get_parser
            mapped_lang = 'cpp' if lang_key in {'cpp', 'c++'} else lang_key
            self.parser = get_parser(mapped_lang)
            if self.parser:
                self.tree = self.parser.parse(bytes(self.source, 'utf-8'))
                self.use_ast = True
        except Exception:
            self.use_ast = False
            self.parser = None
            self.tree = None


    def analyze(self) -> ComplexityIR:
        """
        Main analysis entry point.
        Returns ComplexityIR with extracted features.
        """
        if self.use_ast and self.tree and self.tree.root_node:
            return self._ast_analysis()
        else:
            return self._regex_analysis()

    def _ast_analysis(self) -> ComplexityIR:
        """AST-based analysis (when tree-sitter is available)."""
        ir = ComplexityIR(
            language=self.language,
            source=self.source,
            parser_backend="tree-sitter",
        )

        try:
            # Extract features from AST
            ir.loop = self._extract_loop_features(self.tree.root_node)
            ir.recursion = self._extract_recursion_features(self.tree.root_node)
            ir.graph = self._extract_graph_features(self.tree.root_node)
            ir.control_flow = self._extract_control_flow_features()

            # Extract additional algorithm patterns
            ir.has_heap_operations = self._detect_heap_operations()
            ir.has_matrix_bounds = self._detect_matrix_bounds()
            ir.has_dynamic_allocation = self._detect_dynamic_allocation()
            ir.input_storage_only = self._detect_input_storage_only()
            ir.has_2d_allocation = self._detect_2d_allocation()
            ir.is_constant_lookup = self._detect_constant_lookup()
            ir.multiple_input_bounds = ir.loop.multiple_input_bounds
            ir.has_merged_both = self._detect_merged_both_inputs()
            costs = detect_library_costs(self.source, self.language)
            ir.library_costs = {
                "sort": costs.sort,
                "hash_average_constant": costs.hash_average_constant,
                "heap_logarithmic": costs.heap_logarithmic,
                "dynamic_append_amortized": costs.dynamic_append_amortized,
            }
            dependent = detect_dependent_bounds(self.source, self.language)
            ir.loop.dependent_bounds = dependent.detected
            ir.loop.dependent_relation = dependent.relation
            ir.loop.dependent_sum_class = dependent.sum_class
            ir.algorithm_pattern = classify_pattern(ir).name
            ir.semantic_patterns = detect_semantic_patterns(ir)

        except Exception:
            # If AST extraction fails, fall back to regex
            return self._regex_analysis()

        self._populate_normalized_facts(ir)
        return ir

    def _regex_analysis(self) -> ComplexityIR:
        """
        Fallback regex-based analysis when AST parsing fails or is unavailable.
        Enhanced version with comprehensive pattern detection.
        """
        ir = ComplexityIR(
            language=self.language,
            source=self.source,
            parser_backend="regex-fallback",
        )
        src = self.source.lower()

        # === LOOP DETECTION ===

        for_loops = len(re.findall(r'\bfor\s*\(', src)) + len(re.findall(r'\bfor\s+\w+\s+in\s+', src))
        while_loops = len(re.findall(r'\bwhile\s*\(', src)) + len(re.findall(r'\bwhile\s+\w+', src))
        do_loops = len(re.findall(r'\bdo\s*\{', src))
        builtin_loops = len(re.findall(r'\b(?:sum|max|min|any|all|map|filter|Counter|sorted)\s*\(', src)) + len(re.findall(r'\.(?:split|join|replace|count)\s*\(', src))

        total_loops = for_loops + while_loops + do_loops + builtin_loops

        if total_loops > 0:
            # Detect TRUE nesting vs sequential patterns
            # for(...) { for(...) } = truly nested O(n^2)
            # for(...) { for(...) { for(...) } } = triple nested O(n^3)
            # for(...) {} for(...) {} = sequential O(n)

            # Count nested depth by checking for patterns like for{...for{...}}
            # We need to distinguish between for{...} for{...} (sequential) vs for{...for{...}} (nested)

            # Check for triple nested: for{...for{...for{...}}}
            triple_nested = bool(re.search(r'for\s*\([^}]*for\s*\([^}]*for\s*\(', src, re.DOTALL))

            # Check for double nested: for{...for{...}}
            double_nested = bool(re.search(r'for\s*\([^}]*for\s*\(', src, re.DOTALL)) and not triple_nested

            # Check for sequential: for{...} for{...} (loops separated, not nested)
            # Pattern: for(...){...} some_code for(...){...}
            sequential_pattern = re.search(r'for\s*\([^}]*\}\s*[^}]*for\s*\(', src, re.DOTALL)
            is_sequential = bool(sequential_pattern) and not double_nested and not triple_nested

            # Check for logarithmic inner loop: while(x>1) { x/=2; } inside
            # a linear loop.  The update is in the while body, after the
            # closing condition parenthesis.
            has_log_inner = bool(re.search(
                r'for\s*\([^)]*\)\s*\{[^{}]*while\s*\([^)]*\)\s*\{[^{}]*(?:/=\s*2|>>=\s*1|/=\s*10)',
                src,
                re.DOTALL,
            ))
            has_nested_linear = bool(re.search(
                r'for\s*\([^)]*\)\s*\{[^{}]*while\s*\([^)]*\)\s*\{',
                src,
                re.DOTALL,
            ))

            # Check for amortized patterns: sliding window, two-pointer, monotonic stack, heap ops
            is_sliding_window = bool(re.search(r'\bwhile\s*\([^)]*sum|l\+\+|left\+\+', src))
            is_monotonic_stack = bool(re.search(r'st\.pop\(\)|stack.*pop|st\.push|stack.*push', src))
            is_heap_while = bool(re.search(r'\bwhile\s*\([^)]*pq\.|heap|priority_queue', src))

            if triple_nested:
                ir.loop.depth = 3
                ir.loop.structure = "triple_nested"
            elif double_nested:
                ir.loop.depth = 2
                ir.loop.structure = "nested"
            elif is_sequential:
                ir.loop.depth = 1  # Sequential loops = O(n) not O(n²)
                ir.loop.structure = "sequential"
            elif has_log_inner:
                # for(i<n){while(x>1)x/=2;} = O(n log n)
                ir.loop.depth = 1
                ir.loop.structure = "logarithmic_nested"
            elif has_nested_linear:
                # Insertion-sort style for + while is genuinely quadratic.
                ir.loop.depth = 2
                ir.loop.structure = "nested"
            elif total_loops > 1:
                ir.loop.depth = 1
                ir.loop.structure = "sequential"
            else:
                ir.loop.depth = 1
                ir.loop.structure = "single"

        # === ALGORITHM PATTERN DETECTION ===

        # Binary search patterns
        binary_search_patterns = [
            r'lower_bound\s*\(',
            r'upper_bound\s*\(',
            r'binary_search\s*\(',
            r'while\s*\(\s*\w+\s*<=\s*\w+\s*\)',  # while(left <= right)
            r'mid\s*=\s*\([^)]*\+[^)]*\)\s*/\s*2',  # mid = (left + right) / 2
        ]
        ir.loop.has_binary_search = any(re.search(p, src) for p in binary_search_patterns)

        # Sort operations
        sort_patterns = [r'sort\s*\(', r'std::sort\s*\(', r'\.sort\s*\(', r'qsort\s*\(']
        ir.loop.has_sort = any(re.search(p, src) for p in sort_patterns)

        # Logarithmic step patterns
        log_patterns = [r'\*=\s*2', r'/=\s*2', r'\*=\s*10', r'/=\s*10', r'<<=', r'>>=']
        ir.loop.is_logarithmic_step = any(re.search(p, src) for p in log_patterns)
        log_headers = re.findall(r'\bfor\s*\([^)]*(?:\*=\s*2|/=\s*2|>>=\s*1)', src)
        if len(log_headers) >= 2:
            ir.loop.depth = 2
            ir.loop.structure = "log_squared"
            ir.loop.is_logarithmic_step = True

        # Heap operations - only priority_queue specific patterns, not generic push/pop
        ir.has_heap_operations = self._detect_heap_operations()
        ir.loop.has_heap_operations = ir.has_heap_operations

        # Matrix bounds detection
        ir.has_matrix_bounds = self._detect_matrix_bounds()
        ir.loop.has_matrix_bounds = ir.has_matrix_bounds

        # Multiple input bounds (e.g., m and n)
        bounds_vars = set()
        for match in re.finditer(r'\b([a-zA-Z_]\w*)\s*\.\s*size\s*\(\)', src):
            bounds_vars.add(match.group(1))
        for match in re.finditer(r'\bfor\s*\([^)]*<\s*(\w+)[^)]*\)', src):
            bounds_vars.add(match.group(1))

        # Also look for m,n variables used in bounds
        for match in re.finditer(r'\b(m|n|rows|cols)\b', src):
            if match.group(1) not in ['main', 'min', 'max']:  # exclude keywords
                bounds_vars.add(match.group(1))

        ir.loop.multiple_input_bounds = len(bounds_vars) >= 2
        ir.multiple_input_bounds = ir.loop.multiple_input_bounds
        if hasattr(ir.loop, 'distinct_params'):
            ir.loop.distinct_params = list(bounds_vars)

        # === RECURSION DETECTION ===

        # Find function names and check for recursive calls
        # Exclude C++ keywords that have parentheses like for, while, if, switch
        cpp_keywords = {'for', 'while', 'if', 'switch', 'catch', 'try'}
        func_matches = list(re.finditer(r'\b(\w+)\s*\([^)]*\)\s*\{', src))
        # JavaScript function expressions/arrow functions and C++ lambdas
        # are named by an assignment rather than a declaration keyword.
        func_matches += list(re.finditer(
            r'\b(\w+)\s*=\s*(?:function\s*\([^)]*\)|\([^)]*\)\s*=>|\[[^\]]*\]\s*\([^)]*\))\s*(?:->\s*[^\{]+)?\{',
            src,
        ))
        for func_match in func_matches:
            func_name = func_match.group(1)

            # Skip C++ keywords (for loops, while loops, if statements, etc.)
            if func_name in cpp_keywords:
                continue

            body_start = func_match.end()
            remaining_code = src[body_start:]

            # Look for actual function calls (func_name followed by '(')
            # Use word boundary and ensure it's not part of another word (like 'for' containing 'f')
            call_pattern = rf'(?<!\w){func_name}(?!\w)\s*\('
            recursive_calls = list(re.finditer(call_pattern, remaining_code))
            call_count = len(recursive_calls)

            if call_count > 0:
                ir.recursion.is_recursive = True
                ir.recursion.branch_factor = min(call_count, 4)

                # Check for memoization
                if any(pattern in src for pattern in ['dp[', 'memo[', 'cache[', '@cache', '@lru_cache']) or re.search(
                    r'\b(?:f|dp|memo|cache)\s*\[[^\]]+\]\s*\[[^\]]+\]', src
                ):
                    ir.recursion.has_memoization = True
                    ir.recursion.pattern = "memoized"
                    ir.recursion.memo_dimensions = 2 if (
                        re.search(r'\b(?:f|dp|memo|cache)\s*\[[^\]]+\]\s*\[[^\]]+\]', src)
                        or re.search(r'@(?:cache|lru_cache)', src)
                    ) else 1
                elif call_count >= 2:
                    ir.recursion.pattern = "branching"
                else:
                    ir.recursion.pattern = "linear"

                # Check for divide and conquer (detect m= or mid= with l+r pattern OR pivot-based partitioning)
                has_mid_var = any(re.search(pattern, src) for pattern in [
                    r'\bm\s*=\s*\(\s*l\s*\+\s*r\s*\)',  # m = (l + r)
                    r'\bmid\s*=\s*\(\s*l\s*\+\s*r\s*\)',
                    r'\bm\s*=\s*\(\s*l\s*\+\s*r\s*\)\s*/\s*\d+',  # m = (l + r) / 2
                    r'\bmid\s*=\s*\(\s*l\s*\+\s*r\s*\)\s*/\s*\d+',
                    r'\bm\s*=\s*l\s*\+\s*\(\s*r\s*-\s*l\s*\)\s*/\s*\d+',  # m = l + (r - l) / 2
                ])

                # Quick Sort detection: partition with pivot, recursive calls f(a,l,i-1) and f(a,i+1,r)
                is_quicksort = (
                    (re.search(rf'(?<!\w){func_name}\s*\(\s*a\s*,\s*l\s*,\s*i\s*-\s*1\s*\)', src) and
                     re.search(rf'(?<!\w){func_name}\s*\(\s*a\s*,\s*i\s*\+\s*1\s*,\s*r\s*\)', src)) or
                    (re.search(r'p\s*=\s*a\[', src) and call_count == 2 and
                     re.search(r'for\s*\([^)]*j[^)]*\)', src))
                )

                if has_mid_var or 'mid' in src or 'middle' in src or is_quicksort:
                    ir.recursion.is_divide_and_conquer = True
                    ir.recursion.pattern = "divide_and_conquer"

                    # Check if it's a simple D&C (no merge work) or standard D&C
                    # Simple D&C: just returns max/min of two halves, no O(n) merge
                    has_merge_work = any(re.search(pattern, src) for pattern in [
                        r'\.push_back\s*\(', r'\.emplace_back\s*\(',
                        r'\bmerge\b', r'while\s*\(\s*i\b', r'while\s*\(\s*j\b',
                        r'vector\s*<.*>\s+\w+\s*;',  # auxiliary array declaration
                        r'\bfor\s*\(',              # FOR loop inside = O(n) work
                        r'\bwhile\s*\(',            # WHILE loop inside = O(n) work
                    ])
                    if not has_merge_work and call_count == 2:
                        ir.recursion.pattern = "simple_divide_and_conquer"

                # Check for path compression (Union Find pattern)
                # Must be exact pattern p[x] = find(p, p[x]) where LHS is exactly p[x] or parent[x]
                path_compression_pattern1 = rf'\bp\[\w+\]\s*=\s*{func_name}\s*\(\s*[^)]*p\[\w+\]\s*\)'
                path_compression_pattern2 = rf'\bparent\[\w+\]\s*=\s*{func_name}\s*\(\s*[^)]*parent\[\w+\]\s*\)'

                if re.search(path_compression_pattern1, src) or re.search(path_compression_pattern2, src):
                    ir.recursion.pattern = "path_compression"
                    ir.recursion.branch_factor = 1

                # Check for auxiliary array allocation in recursive functions
                if any(kw in remaining_code for kw in ['push_back', 'emplace_back', 'vector<']):
                    ir.recursion.has_auxiliary_array = True

                break

        # === GRAPH DETECTION ===
        # Only detect as graph if it has graph-specific patterns, not just vector<vector>

        # Graph-specific indicators
        # A helper named ``dfs``/``bfs`` is not sufficient evidence of a
        # graph: dynamic programming and backtracking solutions commonly use
        # those names for ordinary recursion.  Require an adjacency/visited
        # representation (or an explicit graph container) as well.
        graph_indicators = [
            r'\bvis\b.*\bvis\b',  # visited array used multiple times
            r'adjacency',
            r'\bNode\b',
            r'\badj\b',
            r'\bvisited\b',
            r'\bgraph\s*\[',
            r'\bneighbors\b',
        ]

        # vector<vector> is only a graph if combined with graph indicators
        has_vector_vector = bool(re.search(r'vector\s*<\s*vector\s*<', src))
        has_graph_indicator = any(re.search(p, src) for p in graph_indicators)

        # Python helper functions named ``dfs``/``bfs`` are frequent in DP and
        # backtracking.  Without an explicit adjacency representation, do not
        # classify them as graph traversal; the Python-specific extractor below
        # handles genuine ``graph[node]``/visited traversals.
        if self.language in {'python', 'py'} and not re.search(
            r'\b(?:graph|adj|adjacency|neighbor|visited|seen)\b', src,
        ):
            has_graph_indicator = False

        # Parameter name hints for graph (g, graph, adj)
        has_graph_param = bool(re.search(r'\b(g|graph|adj)\b', src))

        if has_vector_vector and (has_graph_indicator or has_graph_param):
            ir.graph.is_graph = True
            ir.graph.structure = "adj_list"
        elif has_graph_indicator:
            ir.graph.is_graph = True
        elif re.search(r'\[\s*\]\s*\[\s*\]', src):
            ir.graph.structure = "adj_matrix"

        # DFS with recursive call on adjacency list is a graph algorithm
        if ir.recursion.is_recursive and has_graph_param and has_vector_vector:
            ir.graph.is_graph = True
            ir.graph.structure = "adj_list"

        # The regex fallback can inherit a graph flag from generic recursion
        # text.  For Python, retain it only when the source names an explicit
        # adjacency/visited representation; genuine Python graph traversal is
        # detected more precisely by ``_extract_graph_features``.
        if self.language in {'python', 'py'} and not re.search(
            r'\b(?:graph|adj|adjacency|neighbor|visited)\b', src,
        ):
            ir.graph.is_graph = False
            ir.graph.structure = ""

        # === SPACE COMPLEXITY PATTERNS ===

        ir.has_dynamic_allocation = self._detect_dynamic_allocation()
        ir.input_storage_only = self._detect_input_storage_only()
        ir.has_2d_allocation = self._detect_2d_allocation()
        ir.is_constant_lookup = self._detect_constant_lookup()
        ir.has_merged_both = self._detect_merged_both_inputs()
        costs = detect_library_costs(self.source, self.language)
        ir.library_costs = {
            "sort": costs.sort,
            "hash_average_constant": costs.hash_average_constant,
            "heap_logarithmic": costs.heap_logarithmic,
            "dynamic_append_amortized": costs.dynamic_append_amortized,
        }
        dependent = detect_dependent_bounds(self.source, self.language)
        ir.loop.dependent_bounds = dependent.detected
        ir.loop.dependent_relation = dependent.relation
        ir.loop.dependent_sum_class = dependent.sum_class
        ir.algorithm_pattern = classify_pattern(ir).name
        ir.semantic_patterns = detect_semantic_patterns(ir)
        ir.control_flow = self._extract_control_flow_features()

        self._populate_normalized_facts(ir)
        return ir

    def _extract_control_flow_features(self) -> ControlFlowIR:
        """Extract conservative CFG/data-flow facts shared by all languages."""
        src = self.source.lower()
        branch_count = len(re.findall(r'\b(?:if|elif|else|switch|case|catch)\b', src))
        early_exit_count = len(re.findall(r'\b(?:break|continue|return)\b', src))
        updates = len(re.findall(
            r'\b(?:[a-z_]\w*)\s*(?:\+\+|--|\+=\s*1|-=\s*1|=\s*[^;\n]+\+\s*1)',
            src,
        ))
        push = bool(re.search(r'\.(?:push|push_back|append|add|offer)\s*\(', src))
        pop = bool(re.search(r'\.(?:pop|pop_back|popleft|remove|poll)\s*\(', src))
        pointer = bool(re.search(
            r'\b(?:left|right|start|end|slow|fast|l|r|i|j)\s*(?:\+\+|--|\+=|-=)',
            src,
        ))
        return ControlFlowIR(
            branch_count=branch_count,
            early_exit_count=early_exit_count,
            loop_carried_updates=updates,
            amortized_push_pop=push and pop,
            monotonic_pointer_updates=pointer,
            branch_join_count=max(0, branch_count - 1),
        )

    @staticmethod
    def _populate_normalized_facts(ir: ComplexityIR) -> None:
        """Publish a stable Stage 1 structural-facts view.

        The inference engine intentionally keeps using the richer typed IR;
        this snapshot is a language-neutral contract for later algebra/CFG
        stages and for benchmark diagnostics.
        """
        loop = ir.loop
        recursion = ir.recursion
        graph = ir.graph
        flow = ir.control_flow
        bounds = list(loop.bounds or [])
        params = list(loop.distinct_params or [])
        ir.normalized_facts = {
            "parser_backend": ir.parser_backend,
            "language": ir.language,
            "loop": {
                "depth": int(loop.depth or 0),
                "structure": loop.structure or "none",
                "bounds": bounds,
                "bound_count": len(bounds),
                "distinct_params": params,
                "multiple_input_bounds": bool(loop.multiple_input_bounds or ir.multiple_input_bounds),
                "constant_inner_loop": bool(loop.has_constant_inner_loop),
                "sort": bool(loop.has_sort),
                "sort_inside_loop": bool(loop.sort_inside_loop),
                "binary_search": bool(loop.has_binary_search),
                "binary_search_inside_loop": bool(loop.binary_search_inside_loop),
                "logarithmic_step": bool(loop.is_logarithmic_step),
                "sliding_window": bool(loop.is_sliding_window),
                "monotonic_stack": bool(loop.is_monotonic_stack),
                "amortized_membership": bool(loop.is_amortized_membership),
                "amortized_index_placement": bool(loop.is_amortized_index_placement),
                "dependent_bounds": bool(loop.dependent_bounds),
                "dependent_relation": loop.dependent_relation or "",
                "dependent_sum_class": loop.dependent_sum_class or "",
            },
            "recursion": {
                "detected": bool(recursion.is_recursive),
                "pattern": recursion.pattern or "linear",
                "branch_factor": int(recursion.branch_factor or 0),
                "memoized": bool(recursion.has_memoization),
                "divide_and_conquer": bool(recursion.is_divide_and_conquer),
                "calls_inside_loop": bool(recursion.calls_inside_loop),
                "reduction": recursion.reduction_type or "linear",
                "work_per_level": recursion.work_per_level or "O(1)",
                "mutual": bool(recursion.has_mutual_recursion),
                "call_graph_nodes": int(recursion.call_graph_nodes or 0),
                "call_graph_edges": int(recursion.call_graph_edges or 0),
                "recursive_cycle_size": int(recursion.recursive_cycle_size or 0),
            },
            "graph": {
                "detected": bool(graph.is_graph),
                "structure": graph.structure or "none",
                "traversal_inside_loop": bool(graph.traversal_inside_loop),
            },
            "control_flow": {
                "branch_count": int(flow.branch_count or 0),
                "branch_join_count": int(flow.branch_join_count or 0),
                "early_exit_count": int(flow.early_exit_count or 0),
                "loop_carried_updates": int(flow.loop_carried_updates or 0),
                "amortized_push_pop": bool(flow.amortized_push_pop),
                "monotonic_pointer_updates": bool(flow.monotonic_pointer_updates),
            },
            "storage": {
                "dynamic": bool(ir.has_dynamic_allocation),
                "input_only": bool(ir.input_storage_only),
                "two_dimensional": bool(ir.has_2d_allocation),
                "constant_lookup": bool(ir.is_constant_lookup),
                "classification": ASTComplexityAnalyzer._classify_space_facts(ir),
            },
            "operations": {
                "heap": bool(ir.has_heap_operations or loop.has_heap_operations),
                "bit": bool(loop.has_bit_operations),
                "matrix_bounds": bool(ir.has_matrix_bounds or loop.has_matrix_bounds),
                "merged_inputs": bool(ir.has_merged_both),
            },
            "library_costs": dict(ir.library_costs or {}),
            "algorithm_pattern": ir.algorithm_pattern or "unknown",
            "semantic_patterns": list(ir.semantic_patterns or []),
        }

    @staticmethod
    def _classify_space_facts(ir: ComplexityIR) -> str:
        """Return a conservative Stage 6 auxiliary-space class."""
        if ir.has_2d_allocation:
            return "quadratic-or-product"
        if ir.graph.is_graph and not ir.input_storage_only:
            return "graph-state"
        if ir.has_dynamic_allocation and not ir.input_storage_only:
            return "linear"
        if ir.recursion.is_recursive:
            return "recursion-stack"
        return "constant"

    def _detect_heap_operations(self) -> bool:
        """Detect priority queue / heap operations that add O(log n) factor."""
        src = self.source.lower()

        heap_patterns = [
            r"priority_queue\s*<[^>]*>\s*\w+",
            r"\bpriorityqueue\b",
            r"\b(?:minheap|maxheap|heap)\s*=\s*new\s+",
            r"make_heap\s*\(",
            r"push_heap\s*\(",
            r"pop_heap\s*\(",
            r"heappush\s*\(",
            r"heappop\s*\(",
            r"heapify\s*\(",
        ]

        # Also detect priority_queue usage via pq.push/pq.pop/pq.top
        has_pq_decl = bool(re.search(r'priority_queue', src))
        has_pq_ops = has_pq_decl and any(
            re.search(p, src) for p in [r'\.push\s*\(', r'\.pop\s*\(', r'\.top\s*\(']
        )

        js_heap_ops = bool(re.search(r"\b(?:heap|minheap|maxheap)\b", src)) and bool(
            re.search(r"\.(?:push|pop|peek|extract(?:min|max))\s*\(", src)
        )
        return has_pq_ops or js_heap_ops or any(re.search(p, src) for p in heap_patterns)

    def _detect_matrix_bounds(self) -> bool:
        """Detect matrix operations with distinct m*n bounds."""
        src = self.source.lower()

        # Look for nested loops with different bounds like a.size() and a[i].size()
        # A vector<vector<T>> declaration alone is an allocation shape, not
        # evidence of independent matrix input dimensions.
        has_matrix_access = (
            bool(re.search(r"a\[\s*i\s*\]\.\s*size\s*\(\)", src)) or
            bool(re.search(r"matrix\[\s*i\s*\]\.\s*size\s*\(\)", src)) or
            bool(re.search(r"grid\[\s*i\s*\]\.\s*size\s*\(\)", src)) or
            bool(re.search(r"a\[0\]\.size\(\)", src)) or
            ("vector<vector" in src and len(re.findall(r"\bfor\s*\(", src)) >= 2)
        )

        # Look for explicit m*n parameters or bounds
        has_mn_params = bool(re.search(r"\bm\b.*\bn\b", src)) or \
                       bool(re.search(r"rows.*cols", src))

        return has_matrix_access or has_mn_params

    def _detect_dynamic_allocation(self) -> bool:
        """Detect dynamic memory allocation inside function body."""
        src = self.source.lower()

        # Find the function body (after first '{')
        # Python uses braces for dictionary/set literals, not function
        # delimiters. Keep the complete source so ``counts = {}`` and similar
        # containers are not truncated at the first literal.
        if self.language in {'python', 'py'}:
            function_body = src
        else:
            brace_pos = src.find('{')
            if brace_pos < 0:
                return False
            function_body = src[brace_pos:]

        # Check for dynamic allocation operations IN the function body
        body_allocation_patterns = [
            r'\.push_back\s*\(',
            r'\.emplace_back\s*\(',
            r'\.resize\s*\(',
            r'\.reserve\s*\(',
            r'\.insert\s*\(',
            r'\bnew\s+\w+',
            r'\bmalloc\s*\(',
            r'\b(?:calloc|realloc)\s*\(',
            # Python containers and mutating operations.
            # Counter/dict/list/set/deque/defaultdict/counter creation and mutating ops.
            r'\b(?:list|dict|set|deque|defaultdict|counter)\s*\(',
            r'\.(?:append|extend|add|update|setdefault|popleft|appendleft)\s*\(',
            r'\bheapq\.(?:heappush|heappop|heapify)\s*\(',
            # New container literal assignment (not comparison): var = [...] or var = {}
            # The old pattern r'\w+(?:\[[^\]]+\])+\s*=' was matching arr[i] == 0 (comparison)
            # because == contains = and the pattern had no negative lookahead.
            r'\w+\s*=\s*\[',  # var = [...] new list creation
            r'\w+\s*=\s*\{',  # var = {...} new dict/set creation
            # Require the list literal to begin at a token boundary.  Without
            # this guard ``row[0] * column`` is falsely treated as allocation.
            r'(?<![\w\]])\[[^\]]+\]\s*\*\s*(?:\w+|\([^)]+\))', # [0] * n
            r'\[[^\]]+for\s+\w+\s+in', # Python list comprehension
            r'\bsorted\s*\(',  # sorted() always creates a new list copy
            r'\.slice\s*\(',  # JavaScript slice() creates a new array copy
            r'\.filter\s*\(',  # JavaScript Array.filter() creates a new array copy
        ]


        has_body_ops = any(re.search(p, function_body) for p in body_allocation_patterns)
        if has_body_ops:
            return True

        # Check for local variable declarations of containers (not parameters)
        # More flexible patterns that match vector<T> name( or name;
        local_container_patterns = [
            r'vector\s*<[^>]+>\s+\w+\s*[\(;]',          # vector<T> name ( or ;
            r'unordered_map\s*<[^>]+>\s+\w+\s*[\(;]',
            r'unordered_set\s*<[^>]+>\s+\w+\s*[\(;]',
            r'map\s*<[^>]+>\s+\w+\s*[\(;]',
            r'set\s*<[^>]+>\s+\w+\s*[\(;]',
            r'stack\s*<[^>]+>\s+\w+\s*[\(;]',
            r'queue\s*<[^>]+>\s+\w+\s*[\(;]',
            r'priority_queue\s*<[^>]+>\s+\w+\s*[\(;]',
            r'list\s*<[^>]+>\s+\w+\s*[\(;]',
        ]

        # Also check for array-style declarations inside function
        array_allocation_patterns = [
            r'int\s+\w+\s*\[\s*\w+\s*\]',      # int arr[n]
            r'float\s+\w+\s*\[\s*\w+\s*\]',
            r'double\s+\w+\s*\[\s*\w+\s*\]',
            r'char\s+\w+\s*\[\s*\w+\s*\]',
        ]

        # SIMPLIFIED: Just check if any container declaration exists in function body
        container_keywords = [
            'vector<', 'unordered_map<', 'unordered_set<', 'map<', 'set<',
            'stack<', 'queue<', 'priority_queue<', 'list<'
        ]

        for keyword in container_keywords:
            # Check if keyword exists in function body
            if keyword in function_body:
                # Make sure it's not just a parameter (should have variable after >)
                # Allow 0 or more spaces between > and variable name, and allow ( or ; or {}
                pattern = rf'{keyword}[^>]+>\s*\w+\s*[\(;{{]'
                if re.search(pattern, function_body):
                    return True

        # Check for DP/memoization pattern (vector<int>& dp parameter)
        # Even though it's a reference parameter, recursion uses O(n) space for the DP table
        dp_patterns = [
            r'vector\s*<[^>]+>&\s+dp',
            r'unordered_map\s*<[^>]+>&\s+dp',
            r'map\s*<[^>]+>&\s+dp',
            r'\bmemo\b',
            r'\bcache\b',
        ]

        if any(re.search(p, src) for p in dp_patterns):
            return True

        # Check for Quick Sort pattern: divide-and-conquer with partition and 2 recursive calls
        # Quick Sort worst-case space is O(n) for recursion stack
        has_quick_sort_pattern = False
        if re.search(r'p\s*=\s*a\[', src) or re.search(r'pivot\s*=', src):
            # Has pivot partitioning
            if re.search(r'for\s*\([^)]*j[^)]*\)', src):
                # Has inner loop (partitioning loop)
                has_quick_sort_pattern = True

        if has_quick_sort_pattern:
            return True

        # Check array declarations
        for pattern in array_allocation_patterns:
            if re.search(pattern, function_body):
                return True

        return False

    def _detect_input_storage_only(self) -> bool:
        """Identify a standalone input container, excluded from auxiliary SC."""
        if self.language not in {'cpp', 'c++', 'c'}:
            return False
        src = self.source.lower()
        has_input_size = bool(re.search(r'cin\s*>>\s*\w+', src))
        has_sized_vector = bool(re.search(r'vector\s*<[^>]+>\s+\w+\s*\(\s*\w+\s*\)', src))
        has_input_loop = bool(re.search(
            r'for\s*\([^)]*cin\s*>>|cin\s*>>\s*\w+\s*\[|for\s+\w+\s*:\s*\w+',
            src,
        ))
        has_extra_buffer = bool(re.search(r'\b(?:merged|result|answer|output|dp|seen|visited)\b\s*(?:=|\.|\[)', src))
        return has_input_size and has_sized_vector and has_input_loop and not has_extra_buffer

    def _detect_2d_allocation(self) -> bool:
        """Detect 2D dynamic allocation."""
        src = self.source.lower()

        brace_pos = src.find('{')
        if brace_pos < 0:
            function_body = src if self.language in {'python', 'py'} else ''
            if not function_body:
                return False
        else:
            function_body = src[brace_pos:]

        # Look for local 2D vector declarations: vector<vector<T>> name(...) or name = ...
        vec_decl = bool(re.search(r'vector\s*<\s*vector\s*<[^>]+\s*>\s*>\s*\w+', function_body))

        # Look for 2D dynamic arrays: new T[n][m] or type arr[n][m] declaration
        arr_decl = bool(re.search(r'\bnew\s+\w+\s*\[[^\]]+\]\s*\[[^\]]+\]', function_body)) or \
                   bool(re.search(r'\b(?:int|float|double|char|bool)\s+\w+\s*\[[^\]]+\]\s*\[[^\]]+\]', function_body))

        # Python nested-list comprehensions, e.g. [[0] * m for _ in range(n)].
        python_2d = bool(re.search(
            r'\[\s*\[[^\]]*\]\s*(?:for|\*)', function_body
        ))

        return vec_decl or arr_decl or python_2d

    def _detect_constant_lookup(self) -> bool:
        """Detect constant-time lookup operations."""
        src = self.source.lower()

        lookup_patterns = [
            r"unordered_map",
            r"unordered_set",
            r"hash_map",
            r"hash_set",
            r"dict\s*\[",
        ]

        return any(re.search(p, src) for p in lookup_patterns)

    def _detect_merged_both_inputs(self) -> bool:
        """Detect if algorithm merges two inputs (e.g., median of two sorted arrays)."""
        src = self.source.lower()

        patterns = [
            r"merge\s+two",
            r"median\s+of\s+two",
            r"intersection\s+of\s+two",
            r"union\s+of\s+two",
            r"two\s+pointers",
            r"merge\s*sorted",
            r"nums1.*nums2",
            r"arr1.*arr2",
        ]

        return any(re.search(p, src) for p in patterns)

    # === AST-SPECIFIC METHODS (only used when tree-sitter is available) ===

    # === AST-SPECIFIC METHODS ===

    def _extract_loop_features(self, root) -> LoopIR:
        """Extract loop features by traversing tree-sitter AST nodes."""
        loop = LoopIR()
        loop_types = {
            'for_statement', 'while_statement', 'do_statement',
            'for_range_loop', 'enhanced_for_statement',
            # JavaScript uses for_in_statement for both for...in and
            # for...of loops in tree-sitter-javascript.
            'for_in_statement',
            # Python comprehensions execute an input-sized iteration even
            # though they do not appear as a standalone for_statement.
            'list_comprehension', 'set_comprehension',
            'dictionary_comprehension', 'generator_expression',
        }

        loop_nodes = []

        def find_loops(node):
            if node.type in loop_types:
                loop_nodes.append(node)
            for child in node.children:
                find_loops(child)

        find_loops(root)

        def is_constant_bounded(node):
            """Return True for loops whose iteration count is input-independent."""
            text = node.text.decode('utf-8', errors='ignore') if isinstance(node.text, bytes) else str(node.text)
            body = node.child_by_field_name('body')
            if body is not None:
                body_text = body.text.decode('utf-8', errors='ignore') if isinstance(body.text, bytes) else str(body.text)
                header = text[:text.find(body_text)] if body_text in text else text
            else:
                header = text
            lower = header.lower()
            # Python range literals (range(4), range(0, 26), ...).
            if re.search(r'\brange\s*\(\s*(?:0\s*,\s*)?(?:[1-9]|[1-9]\d|100)\s*\)', lower):
                return True
            # C/C++ loop conditions bounded by a numeric literal.
            if re.search(r';[^;]*[<>]=?\s*(?:[1-9]|[1-9]\d|100)\b', lower):
                return True
            # Small fixed direction/array-alphabet loops are also constant.
            # Python ``range(n - 2)`` is input-sized; do not mistake its
            # offset literal for a constant bound. Literal Python ranges were
            # handled by the stricter rule above, so this fallback is only for
            # C/C++/Java-style headers.
            if re.search(r'\b(?:2|3|4|8|10|26|27|36|52)\b', lower) and 'for' in lower and 'range' not in lower:
                return True
            return False

        # Tree-sitter may materialize distinct Python wrapper objects for the
        # same underlying node while walking parent links.  ``id(node)`` is
        # therefore not a stable identity here; source offsets are.
        constant_loop_ids = {node.start_byte for node in loop_nodes if is_constant_bounded(node)}

        # 1. Determine nesting depth and parent-child hierarchy
        max_depth = 0
        loop_ancestor_counts = []
        for node in loop_nodes:
            ancestors = 0
            curr = node.parent
            while curr:
                if curr.type in loop_types and curr.start_byte not in constant_loop_ids:
                    ancestors += 1
                curr = curr.parent
            loop_ancestor_counts.append(ancestors)
            if node.start_byte not in constant_loop_ids:
                max_depth = max(max_depth, ancestors + 1)

        loop.depth = max_depth

        # Some tree-sitter Python versions expose parent wrappers whose type
        # metadata is incomplete during upward traversal.  Recover nesting
        # from stable source ranges as a language-neutral fallback.  This is
        # important for ``for`` + two-pointer ``while`` algorithms such as
        # 3Sum: the inner pointer scan is repeated for every outer item.
        active_loops = [
            node for node in loop_nodes if node.start_byte not in constant_loop_ids
        ]
        for outer in active_loops:
            for inner in active_loops:
                if outer is inner:
                    continue
                if (
                    outer.start_byte < inner.start_byte
                    and inner.end_byte <= outer.end_byte
                ):
                    loop.depth = max(loop.depth, 2)
                    break

        # Check if loops are sequential vs nested
        top_level_loops = [loop_nodes[i] for i, anc in enumerate(loop_ancestor_counts)
                           if anc == 0 and loop_nodes[i].start_byte not in constant_loop_ids]
        if max_depth == 1 and len(top_level_loops) > 1:
            loop.structure = "sequential"
        elif max_depth == 2:
            loop.structure = "nested"
        elif max_depth >= 3:
            loop.structure = "triple_nested"
        else:
            loop.structure = "single"

        # 2. Check logarithmic step patterns across loops (% b, &=, /= 2, *= 2, >>= 1)
        log_loop_count = 0
        for node in loop_nodes:
            if node.start_byte in constant_loop_ids:
                continue
            # Always define full_text first so while/do branches never hit NameError
            full_text = node.text.decode('utf-8', errors='ignore').lower() if isinstance(node.text, bytes) else str(node.text).lower()
            body = node.child_by_field_name('body')
            if body:
                body_text = body.text.decode('utf-8', errors='ignore').lower() if isinstance(body.text, bytes) else str(body.text).lower()
                header_text = full_text[:full_text.find(body_text)] if body_text in full_text else full_text
            else:
                header_text = full_text
                body_text = full_text

            if node.type in ['while_statement', 'do_statement']:
                check_text = full_text
            else:
                check_text = header_text

            if any(op in check_text for op in ['*=', '/=', '>>=', '<<=', '/ 2', '/10', '* 2', '* 10', '%', '&=']):
                log_loop_count += 1

        if log_loop_count >= 2:
            loop.is_logarithmic_step = True
            loop.structure = "log_squared"
        elif log_loop_count == 1:
            loop.is_logarithmic_step = True
            if max_depth >= 2:
                loop.structure = "logarithmic_nested"

        # 3. Check algorithm operations (sort, binary search, heap) inside/outside loops
        src_lower = self.source.lower()
        # Python library operations can hide an input-sized traversal without
        # an explicit AST loop node (for example ``sum(values)``,
        # ``Counter(values)``, and ``sorted(values)``).  Preserve explicit
        # loop depth when present; otherwise record one linear pass.
        python_linear_builtin = self.language in {'python', 'py'} and bool(re.search(
            r'\b(?:sum|min|max|any|all|counter)\s*\(', src_lower,
        ))
        if python_linear_builtin and loop.depth == 0:
            loop.depth = 1
            loop.structure = "single"
        # Ignore small fixed 2-3 element pair sorting (e.g. sorted([a, b]), sorted(domino))
        has_pair_sort = bool(re.search(r'sorted\s*\(\s*(?:\[[^\]]*\]|\([^)]*\)|\w+)\s*\)', src_lower)) and any(
            t in src_lower for t in ('domino', 'pair', '[a, b]', '[u, v]', '[x, y]', '(a, b)', 'sorted([', 'sorted((')
        )
        # Sorting a fixed-size temporary (for example
        # ``vector<int> triplet = {a, b, c}; sort(triplet.begin(),
        # triplet.end());``) is constant work.  It must not turn a triple
        # nested brute-force search into O(n^2 log n).
        fixed_initializer_sort = False
        for match in re.finditer(
            r'(?:vector\s*<[^;{}]+>\s+)?(\w+)\s*=\s*\{([^{}]*)\}',
            src_lower,
        ):
            variable, initializer = match.groups()
            element_count = 0 if not initializer.strip() else initializer.count(',') + 1
            if element_count <= 4 and re.search(
                rf'\bsort\s*\(\s*{re.escape(variable)}\s*\.\s*begin\s*\(\s*\)\s*,\s*'
                rf'{re.escape(variable)}\s*\.\s*end\s*\(\s*\)\s*\)',
                src_lower,
            ):
                fixed_initializer_sort = True
                break
        loop.has_sort = any(s in src_lower for s in [
            'sort(', 'std::sort', '.sort(', 'sorted(',
        ]) and not has_pair_sort and not fixed_initializer_sort
        # A sort performed for every input item composes multiplicatively with
        # its surrounding loop.  Keep this separate from one preprocessing
        # sort followed by a scan.
        loop.sort_inside_loop = loop.has_sort and any(
            any(marker in (
                (node.child_by_field_name('body').text.decode('utf-8', errors='ignore')
                 if isinstance(node.child_by_field_name('body').text, bytes)
                 else str(node.child_by_field_name('body').text))
                if node.child_by_field_name('body') is not None else ''
            ).lower() for marker in ('sort(', 'std::sort', '.sort(', 'sorted('))
            for node in loop_nodes
        )
        explicit_binary_call = bool(re.search(
            r'\b(?:lower_bound|upper_bound|binary_search|bisect_left|bisect_right)\s*\(',
            src_lower,
        ))
        halving_loop = bool(
            re.search(r'\b(?:while|for)\s*\([^)]*(?:<=|>=)[^)]*\)', src_lower)
            and re.search(r'\b(?:mid|middle|m)\s*=\s*[^\n;]*(?:/\s*2|>>\s*1)', src_lower)
            and re.search(r'\b(?:left|right|l|r)\s*=\s*[^\n;]*\b(?:mid|middle|m)\b', src_lower)
        )
        python_halving_loop = bool(
            re.search(r'\bwhile\s+\w+\s*(?:<|<=|>|>=)\s*\w+\s*:', src_lower)
            and re.search(r'\b(?:mid|middle|m)\s*=\s*[^\n#]*(?:/\s*2|//\s*2|>>\s*1)', src_lower)
            and re.search(r'\b(?:low|high|left|right|l|r)\s*=\s*[^\n#]*\b(?:mid|middle|m)\b', src_lower)
        )
        halving_loop = halving_loop or python_halving_loop
        loop.has_binary_search = explicit_binary_call or halving_loop
        # A binary-search call nested in another loop is multiplicative.  Keep
        # this separate from a loop whose own update halves the search range.
        binary_call_patterns = [
            r'\b(?:binary_search|lower_bound|upper_bound|bisect_left|bisect_right)\s*\(',
        ]
        loop.binary_search_inside_loop = any(
            any(re.search(pattern, (node.text.decode('utf-8', errors='ignore')
                                     if isinstance(node.text, bytes) else str(node.text)).lower())
                for pattern in binary_call_patterns)
            for node in loop_nodes
        )
        # A binary-search iteration that invokes a user-defined helper must
        # include the helper's per-iteration scan.  This covers patterns such
        # as Koko/Shipping Capacity without assuming the helper's cost is
        # constant merely because the call is nested in a loop.
        helper_names = set(re.findall(r'\bdef\s+(\w+)\s*\(', src_lower))
        helper_names.update(re.findall(
            r'\b(?:int|long|bool|void|double|float|string)\s+(\w+)\s*\([^)]*\)\s*\{',
            src_lower,
        ))
        helper_call_inside_loop = any(
            any(re.search(rf'\b{re.escape(name)}\s*\(',
                         (node.text.decode('utf-8', errors='ignore')
                          if isinstance(node.text, bytes) else str(node.text)).lower())
                for name in helper_names)
            for node in loop_nodes
        )
        if loop.has_binary_search and helper_call_inside_loop and max_depth >= 1:
            loop.binary_search_inside_loop = True
        loop.binary_search_loop_depth = max_depth if loop.binary_search_inside_loop else 0
        loop.has_heap_operations = self._detect_heap_operations()
        # Amortized patterns are recognized structurally, rather than by a
        # generic pop/increment token.  This prevents unrelated nested loops
        # from being incorrectly collapsed to O(n).
        has_window_pointer = bool(re.search(
            r'\b(?:left|right|start|end|l|r|i|j|slow|fast|p1|p2)\s*(?:\+\+|\+=\s*1|=\s*\w+\s*\+\s*1)',
            src_lower,
        ))
        # Python writes ``while condition:``, C-family languages write
        # ``while (condition)``. The pointer movement requirement above keeps
        # this broad loop marker from classifying arbitrary nested loops as a
        # sliding window.
        has_window_loop = bool(re.search(r'\bwhile\b', src_lower))
        loop.is_sliding_window = max_depth >= 2 and has_window_pointer and has_window_loop

        has_stack_container = bool(re.search(
            r'\b(?:stack|deque|vector)\s*<[^>]+>\s*(?:stack|st|s|dq)\b'
            r'|\b(?:stack|st|s|dq)\s*=\s*\['
            r'|\b(?:stack|st|s|dq)\s*=\s*(?:deque|list)\s*\(',
            src_lower,
        ))
        has_stack_push = bool(re.search(r'\.(?:push|push_back|append|appendleft)\s*\(', src_lower))
        has_stack_pop = bool(re.search(r'\.(?:pop|pop_back|popleft)\s*\(', src_lower))
        loop.is_monotonic_stack = max_depth >= 2 and has_stack_container and has_stack_push and has_stack_pop
        # Detect Fenwick/BIT work only from unambiguous identifiers or the
        # canonical lowbit update. A bare ``bit`` token is too broad because
        # it also appears in ordinary bit-manipulation solutions.
        loop.has_bit_operations = bool(re.search(
            r'\b(?:fenwick(?:tree)?|bitree|binary_indexed(?:_tree)?)\b'
            r'|\b(?:bit|tree)\s*\.\s*(?:add|sum|query|update)\s*\('
            r'|\b(\w+)\s*[+\-]=\s*\1\s*&\s*-\s*\1\b',
            src_lower,
        ))
        loop.has_matrix_bounds = self._detect_matrix_bounds()

        # Fixed alphabets/ranges add constant work per input item.
        loop.has_constant_inner_loop = bool(re.search(
            r'(?:for\s*\([^)]*[<]=?\s*(?:10|16|26|52|64|100)\b|'
            r'for\s+\w+\s+in\s+range\(\s*(?:10|16|26|52|64|100)\s*\))',
            src_lower,
        )) and max_depth >= 2
        if loop.has_constant_inner_loop:
            loop.depth = max(1, loop.depth - 1)
            loop.structure = "sequential"

        # Nested scans over disjoint groups are linear in the total number of
        # elements, e.g. ``for group in buckets.values(): for item in group``.
        loop.is_grouped_partition = bool(re.search(
            r'for\s+\w+\s+in\s+[^\n:]+\.(?:values|items)\s*\(\s*\)',
            src_lower,
        )) and max_depth >= 2

        # Collision-name allocation advances a stored counter monotonically;
        # each generated key is consumed once, so the inner membership loop
        # is amortized rather than a full independent n-loop.
        loop.is_amortized_membership = (
            self.language in {'python', 'py'}
            and max_depth >= 2
            and bool(re.search(r'while\s+[^\n:]+\s+in\s+\w+', src_lower))
            and bool(re.search(r'\b(?:k|count|index)\s*\+=\s*1', src_lower))
            and bool(re.search(r'\b(?:dict|map|set|count|used|name_count)', src_lower))
        )

        # Open-addressed hash tables in C-family implementations often use a
        # collision probe such as ``while (used[h]) h = (h + 1) & mask``.
        # The probe is amortized constant per input insertion; it must not be
        # multiplied by a separate capacity-doubling setup loop.
        loop.is_amortized_membership = loop.is_amortized_membership or (
            bool(re.search(r'\bfor\s*\(', src_lower))
            and bool(re.search(
                r'\bwhile\s*\(\s*(?:used|occupied|filled|table)\s*\[',
                src_lower,
            ))
            and bool(re.search(
                r'\b(?:h|slot|pos|idx)\s*(?:\+\+|\+=\s*1|=\s*\([^\n;]*\+\s*1\)',
                src_lower,
            ))
        )

        # In-place cyclic placement (e.g. First Missing Positive) may have a
        # nested ``while`` inside a scan, but every swap puts an item into its
        # final slot.  The total number of swaps is amortized O(n), not O(n²).
        loop.is_amortized_index_placement = (
            self.language in {'python', 'py'}
            and max_depth >= 2
            and bool(re.search(r'while\s+[^\n:]*\w+\s*\[\s*\w+\s*\]\s*[-+]?\s*1\s*\]', src_lower))
            and bool(re.search(r'\b(?:swap|correct_index|nums\s*\[)', src_lower))
        )

        # Check for multiple input bounds (e.g. m and n or w/W or size calls)
        loop_counter_vars = set(re.findall(r'\bfor\s*\(\s*(?:[a-zA-Z_]\w*\s+)?([a-zA-Z_]\w*)\s*=', src_lower))
        loop_counter_vars.update(re.findall(r'\bfor\s+([a-zA-Z_]\w*)\s+in\s+', src_lower))
        loop_counter_vars.update({'i', 'j', 'k', 'x', 'y', 'z', 'idx', 'index', 'row', 'col', 'r', 'c', 'it'})

        bounds_vars = list(dict.fromkeys(re.findall(r'\b([a-zA-Z_]\w*)\s*\.\s*size\s*\(\)', src_lower)))
        for match in re.finditer(r'\bfor\s*\([^)]*<\s*=?\s*(\w+)[^)]*\)', src_lower):
            v = match.group(1)
            if v not in ['0', '1', '2'] and v not in bounds_vars and v not in loop_counter_vars:
                bounds_vars.append(v)
        # Container identifiers from ``a.size()`` are not independent
        # asymptotic dimensions when the loop is otherwise bounded by the
        # derived scalar ``n`` (a common two-pass array pattern).
        if len(bounds_vars) >= 2 and 'n' in bounds_vars:
            arbitrary_containers = [b for b in bounds_vars if b not in {'n', 'm', 'v', 'e', 'rows', 'cols', 'w', 'k'}]
            if arbitrary_containers and len(arbitrary_containers) == len(bounds_vars) - 1:
                bounds_vars = ['n']

        # Enhanced/range loops expose independent dimensions directly in the
        # iterable names (``for row in left`` followed by ``for col in
        # right``). Preserve that evidence as O(m*n) instead of collapsing
        # every nested pair to O(n^2).
        if max_depth >= 2:
            iterables = re.findall(
                r'\bfor\s+(?:\([^)]*\)|[a-zA-Z_]\w*)\s+(?:in|of)\s+([a-zA-Z_]\w*)',
                src_lower,
            )
            iterables += re.findall(
                r'\bfor\s*\([^:;]+:\s*([a-zA-Z_]\w*)\)', src_lower,
            )
            iterables += re.findall(
                r'\bfor\s*\([^)]*\b(?:in|of)\s+([a-zA-Z_]\w*)\)', src_lower,
            )
            if len(dict.fromkeys(iterables)) >= 2:
                bounds_vars = ['m', 'n']

        loop.distinct_params = bounds_vars
        loop.multiple_input_bounds = len(bounds_vars) >= 2

        # A genuine amortized window/stack nested in a scan can be collapsed
        # to linear time.  Do not collapse a sorted outer scan with an inner
        # pointer loop: that is the standard O(n^2) 3Sum shape.
        if (loop.is_sliding_window or loop.is_monotonic_stack) and max_depth == 2 and not loop.has_sort:
            loop.depth = 1
            loop.structure = "sequential"

        # Preserve the established amortized fallback for compact reference
        # solutions that do not expose descriptive pointer/container names
        # (for example, BFS queues and contest-style ``s.pop()`` stacks).
        # The structured rules above provide stronger evidence when present.
        legacy_amortized = any(token in src_lower for token in (
            '.pop()', 'pop_back()', 'popleft(', 'pop(0)',
            'left++', 'l++', 'start++', 'left += 1', 'left+=1',
            'l += 1', 'l+=1', 'start += 1', 'start+=1',
        ))
        if legacy_amortized and max_depth == 2 and not loop.has_sort:
            loop.depth = 1
            loop.structure = "sequential"

        # Counting-sort frequency scans use a fixed alphabet/range table. The
        # inner decrement loop consumes each input item once overall, so it is
        # linear rather than quadratic.
        is_fixed_frequency_scan = bool(re.search(
            r'\b(?:cnt|count|freq|c)\s*\[\s*\d+\s*\]'
            r'|\b(?:cnt|count|freq|c)\s*\[\s*\d+\s*\]\s*=',
            src_lower,
        )) and bool(re.search(r'\b(?:cnt|count|freq|c)\s*\[\s*\w+\s*\]\s*--', src_lower))
        if is_fixed_frequency_scan and max_depth >= 2:
            loop.depth = 1
            loop.structure = "sequential"

        # Source-level fallbacks cover compact C/C++ loop headers that
        # tree-sitter represents without a loop parent relationship.  Keep
        # these narrowly tied to canonical complexity idioms.
        nested_log_pattern = bool(re.search(
            r'\bfor\s*\([^)]*;[^)]*;[^)]*\+\+[^)]*\)\s*\{[^{}]*'
            r'\bwhile\s*\([^)]*\)\s*\{[^{}]*(?:/=|>>=|\*=)\s*(?:2|10)',
            src_lower, re.DOTALL,
        ))
        log_squared_pattern = bool(re.search(
            r'\bfor\s*\([^)]*(?:\*=|/=|>>=)\s*2[^)]*\)\s*'
            r'(?:\{\s*)?for\s*\([^)]*(?:\*=|/=|>>=)\s*2',
            src_lower, re.DOTALL,
        ))
        if log_squared_pattern:
            loop.depth = max(loop.depth, 2)
            loop.structure = "log_squared"
            loop.is_logarithmic_step = True
            loop.is_sliding_window = False
        elif nested_log_pattern:
            loop.depth = max(loop.depth, 2)
            loop.structure = "logarithmic_nested"
            loop.is_logarithmic_step = True
            loop.is_sliding_window = False
        else:
            # Insertion sort's inner scan moves backwards through the prefix;
            # unlike a sliding window it is a genuinely nested worst-case
            # linear scan.
            insertion_pattern = bool(re.search(
                r'\bfor\s*\([^)]*\)\s*\{[^{}]*\bwhile\s*\([^)]*'
                r'(?:>=\s*0|>\s*[-\w]|\b[a-z_]\w*\s*>)',
                src_lower, re.DOTALL,
            )) and bool(re.search(r'(?:j\s*--|a\s*\[\s*j\s*\]|\bkey\b)', src_lower))
            if insertion_pattern:
                loop.depth = max(loop.depth, 2)
                loop.structure = "nested"
                loop.is_sliding_window = False

        # Compact insertion-sort implementations often omit whitespace and
        # use a single-letter key.  The canonical backward scan is still
        # unambiguous: an outer forward scan, inner j>=0 guard, and j-- move.
        if (re.search(r'\bfor\s*\([^)]*\)\s*\{', src_lower) and
                re.search(r'\bwhile\s*\(\s*j\s*>=\s*0\s*&&', src_lower) and
                re.search(r'\bj\s*--', src_lower)):
            loop.depth = max(loop.depth, 2)
            loop.structure = "nested"
            loop.is_sliding_window = False

        return loop

    def _extract_recursion_features(self, root) -> RecursionIR:
        """Extract recursion features from AST."""
        rec = RecursionIR()
        loop_types = {'for_statement', 'while_statement', 'do_statement', 'for_range_loop', 'enhanced_for_statement'}

        func_nodes = []
        def find_funcs(node):
            if node.type in ['function_definition', 'method_declaration', 'function_declaration']:
                func_nodes.append(node)
            for child in node.children:
                find_funcs(child)
        find_funcs(root)

        if not func_nodes:
            return self._regex_analysis().recursion

        # Build a small, language-neutral call graph before inspecting the
        # individual functions.  The old extractor only looked for a function
        # calling itself, so patterns such as even() -> odd() -> even() and
        # backtracking split between solve()/choose() were reported as linear.
        # Tree-sitter exposes calls as ``call_expression`` for C-like
        # languages and ``call`` for Python; both are handled here.
        def function_name(fn_node):
            name = ""
            declarator = fn_node.child_by_field_name('declarator')
            if declarator:
                # Prefer the declarator's named identifier.  Taking the first
                # identifier child can select a parameter name (for example
                # ``values``) and makes a normal helper call look recursive.
                candidate = declarator
                while candidate is not None:
                    if candidate.type in ['identifier', 'field_identifier']:
                        name = candidate.text.decode('utf-8', errors='ignore') if isinstance(candidate.text, bytes) else str(candidate.text)
                        break
                    candidate = (
                        candidate.child_by_field_name('declarator')
                        or candidate.child_by_field_name('name')
                    )
            if not name:
                name_node = fn_node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf-8', errors='ignore') if isinstance(name_node.text, bytes) else str(name_node.text)
            return name

        graph_records = []
        known_names = set()
        for node in func_nodes:
            name = function_name(node)
            if name and name not in {'main', 'if', 'for', 'while'}:
                text = node.text.decode('utf-8', errors='ignore') if isinstance(node.text, bytes) else str(node.text)
                graph_records.append((name, node, text))
                known_names.add(name)

        adjacency = {name: set() for name in known_names}
        graph_calls = {name: [] for name in known_names}
        for name, fn_node, _ in graph_records:
            def collect_graph_calls(node):
                if node.type in {'call_expression', 'call', 'method_invocation'}:
                    func_expr = node.child_by_field_name('function') or (node.children[0] if node.children else None)
                    if func_expr:
                        raw = func_expr.text.decode('utf-8', errors='ignore') if isinstance(func_expr.text, bytes) else str(func_expr.text)
                        call_name = raw.split('::')[-1].split('.')[-1].split('->')[-1]
                        if call_name in known_names:
                            in_loop = False
                            parent = node.parent
                            while parent:
                                if parent.type in loop_types:
                                    in_loop = True
                                    break
                                parent = parent.parent
                            adjacency[name].add(call_name)
                            graph_calls[name].append((call_name, in_loop))
                for child in node.children:
                    collect_graph_calls(child)
            collect_graph_calls(fn_node)

        # Find a directed cycle containing more than one function.  A bounded
        # DFS is sufficient here and avoids imposing a graph dependency on the
        # parser; function counts in a submission are small.
        mutual_cycle = []
        for start in known_names:
            stack = [(start, [start])]
            while stack and not mutual_cycle:
                current, path = stack.pop()
                for nxt in adjacency.get(current, ()):
                    if nxt == start and len(path) > 1:
                        mutual_cycle = path[:]
                        break
                    if nxt not in path and len(path) <= len(known_names):
                        stack.append((nxt, path + [nxt]))
        if mutual_cycle:
            cycle_set = set(mutual_cycle)
            cycle_edges = []
            for name in cycle_set:
                cycle_edges.extend((target, inside) for target, inside in graph_calls.get(name, []) if target in cycle_set)
            rec.is_recursive = True
            rec.has_mutual_recursion = True
            rec.call_graph_nodes = len(known_names)
            rec.call_graph_edges = sum(len(v) for v in adjacency.values())
            rec.recursive_cycle_size = len(cycle_set)
            rec.branch_factor = max(1, max((sum(1 for target, _ in graph_calls.get(name, []) if target in cycle_set) for name in cycle_set), default=1))
            rec.calls_inside_loop = any(inside for _, inside in cycle_edges)
            cycle_text = ' '.join(text for name, _, text in graph_records if name in cycle_set).lower()
            permutation_like = bool(re.search(r'\bswap\s*\(|\bpermute\b|\bpermutation\b|\bqueen|\bcolumn', cycle_text))
            rec.pattern = 'factorial' if permutation_like and rec.branch_factor >= 2 else 'mutual_recursive'
            rec.reduction_type = 'linear'
            rec.stack_depth = 'O(n)'
            return rec

        for fn_node in func_nodes:
            fn_name = function_name(fn_node)

            if not fn_name or fn_name in {'main', 'if', 'for', 'while'}:
                continue

            fn_text = fn_node.text.decode('utf-8', errors='ignore') if isinstance(fn_node.text, bytes) else str(fn_node.text)

            # Normalize the declaration name from the function header.  Some
            # C-like grammars expose a parameter identifier as the first child
            # of a declarator; using it would turn a normal helper call into a
            # false self-recursion signal.
            header = fn_text.split('{', 1)[0].split(':', 1)[0].strip()
            declared = re.search(r'(?:def\s+)?([A-Za-z_]\w*)\s*\([^()]*\)\s*$', header)
            if declared:
                fn_name = declared.group(1)

            self_calls = []
            calls_inside_loop = False

            def find_calls(node):
                nonlocal calls_inside_loop
                # Tree-sitter names calls ``call_expression`` in C/C++/Java
                # and simply ``call`` in Python.  Treat both uniformly so
                # nested Python backtracking helpers are recognized.
                if node.type in {'call_expression', 'call', 'method_invocation'}:
                    func_expr = node.child_by_field_name('function') or (node.children[0] if node.children else None)
                    if func_expr:
                        call_name = func_expr.text.decode('utf-8', errors='ignore') if isinstance(func_expr.text, bytes) else str(func_expr.text)
                        if call_name == fn_name:
                            self_calls.append(node)
                            curr = node.parent
                            while curr:
                                if curr.type in loop_types:
                                    calls_inside_loop = True
                                    break
                                curr = curr.parent
                for child in node.children:
                    find_calls(child)

            find_calls(fn_node)

            # Guard against grammar-specific name resolution selecting a
            # parameter/helper identifier.  Only a call to the declared
            # function name inside its body is genuine self-recursion.
            body_text = fn_text.split('{', 1)[1] if '{' in fn_text else fn_text
            if not re.search(rf'\b{re.escape(fn_name)}\s*\(', body_text):
                self_calls = []

            if self_calls:
                rec.is_recursive = True

                # Measure work performed by one recursive activation.  This
                # is intentionally local to the function containing the
                # self-call; a caller's loops are handled by the call-graph
                # composition layer instead.  T(n)=T(n-1)+O(n^d) therefore
                # carries an O(n^(d+1)) total-time recurrence.
                local_loops = []
                def collect_local_loops(node):
                    if node.type in loop_types:
                        local_loops.append(node)
                    for child in node.children:
                        collect_local_loops(child)
                collect_local_loops(fn_node)
                local_depth = 0
                for candidate in local_loops:
                    depth = 1
                    parent = candidate.parent
                    while parent is not None and parent is not fn_node:
                        if parent.type in loop_types:
                            depth += 1
                        parent = parent.parent
                    local_depth = max(local_depth, depth)
                if local_depth >= 2:
                    rec.work_per_level = "O(n^2)"
                elif local_depth == 1:
                    rec.work_per_level = "O(n)"

                # Determine mutual exclusivity vs simultaneous branching
                is_exclusive = False
                if len(self_calls) >= 2:
                    call1, call2 = self_calls[0], self_calls[1]

                    def get_if_ancestor(node):
                        curr = node.parent
                        prev = node
                        while curr:
                            if curr.type == 'if_statement':
                                return curr, prev
                            prev = curr
                            curr = curr.parent
                        return None, None

                    if1, child1 = get_if_ancestor(call1)
                    if2, child2 = get_if_ancestor(call2)

                    if if1 and if2 and if1.start_byte == if2.start_byte:
                        if child1.type != child2.type or (hasattr(child1, 'start_byte') and hasattr(child2, 'start_byte') and child1.start_byte != child2.start_byte):
                            is_exclusive = True
                    elif if1 and not if2:
                        if 'return' in (if1.text.decode('utf-8', errors='ignore') if isinstance(if1.text, bytes) else str(if1.text)):
                            is_exclusive = True
                    elif if2 and not if1:
                        if 'return' in (if2.text.decode('utf-8', errors='ignore') if isinstance(if2.text, bytes) else str(if2.text)):
                            is_exclusive = True

                rec.branch_factor = 1 if is_exclusive else len(self_calls)

                # Check graph context (Graph DFS with recursive call inside loop over edges/adj)
                # Only suppress calls_inside_loop for true graph DFS — NOT for permutation/backtracking
                # Permutation patterns use swap + recursion inside a loop => must keep calls_inside_loop
                has_swap = 'swap(' in fn_text or 'swap (' in fn_text
                is_graph_func = (
                    any(g in fn_text for g in ['vector<vector', 'adj', 'graph', 'vis', 'visited'])
                    and not has_swap
                )
                if is_graph_func:
                    calls_inside_loop = False

                rec.calls_inside_loop = calls_inside_loop

                div_count = 0
                sub_count = 0
                for call_node in self_calls:
                    args_text = call_node.text.decode('utf-8', errors='ignore') if isinstance(call_node.text, bytes) else str(call_node.text)
                    if '/ 2' in args_text or '/2' in args_text or '>> 1' in args_text:
                        div_count += 1
                    if '- 1' in args_text or '-1' in args_text or '- 2' in args_text:
                        sub_count += 1

                has_pivot_split = rec.branch_factor == 2 and ('-1' in fn_text or '- 1' in fn_text) and ('+1' in fn_text or '+ 1' in fn_text)
                has_dc_split = any(pattern in fn_text for pattern in ['(l + r) / 2', '(l+r)/2', 'mid =', 'm = (l', 'm=(l', 'pivot', 'partition']) or has_pivot_split
                if has_dc_split or div_count > 0:
                    rec.reduction_type = "divide"
                    rec.is_divide_and_conquer = True
                    rec.stack_depth = "O(log n)"
                else:
                    rec.reduction_type = "linear"
                    rec.stack_depth = "O(n)"

                is_path_compression = bool(re.search(rf'\bparent\[\w+\]\s*=\s*{fn_name}', fn_text)) or \
                                       bool(re.search(rf'\bpar\[\w+\]\s*=\s*{fn_name}', fn_text)) or \
                                       bool(re.search(rf'\bp\[\w+\]\s*=\s*{fn_name}', fn_text))

                if is_path_compression:
                    rec.pattern = "path_compression"
                elif any(m in fn_text.lower() for m in [
                    'memo[', 'dp[', 'cache[', 'containskey(',
                    'memo.get(', 'cache.get(', 'memo.set(', 'cache.set(',
                    '.has(', '@cache', '@lru_cache', 'lru_cache(',
                ]):
                    rec.has_memoization = True
                    rec.pattern = "memoized"
                    memo_text = fn_text.lower()
                    # Detect the state dimensionality instead of reducing all
                    # memoized recurrences to generic O(n).  C/C++/Java DP
                    # tables use f[i][j], while Python decorators and maps
                    # commonly encode a one- or two-argument state.
                    if re.search(r"\b(?:memo|dp|cache|f)\s*\[[^\]]+\]\s*\[[^\]]+\]", memo_text) \
                            or re.search(r"(?:cache|memo)\s*\(\s*[^,]+\s*,\s*[^)]+\)", memo_text) \
                            or re.search(r"@(?:cache|lru_cache)", memo_text) and len(re.findall(r"\b(?:i|j|x|y|left|right|index|pos)\b", memo_text)) >= 2:
                        rec.memo_dimensions = 2
                    else:
                        rec.memo_dimensions = 1
                elif calls_inside_loop:
                    rec.pattern = "factorial"
                elif rec.branch_factor >= 2:
                    rec.pattern = "branching"
                elif rec.reduction_type == "divide":
                    rec.pattern = "divide_and_conquer"
                else:
                    rec.pattern = "linear"

                return rec

        # With a parsed function set, absence of a verified self-call is
        # meaningful. Falling back to broad regex recursion heuristics here
        # misclassifies ordinary helper calls (for example solve() calling
        # count_matches()) as recursive.
        return rec

    def _extract_graph_features(self, root) -> GraphIR:
        """Extract graph features from AST."""
        graph = self._regex_analysis().graph
        src_lower = self.source.lower()
        python_neighbor_loop = bool(re.search(
            r'for\s+\w+\s+in\s+(?:self\.)?(?:graph|adj|adjacency)\s*\[',
            src_lower,
        ))
        python_visited = bool(re.search(
            r'\b(?:visited|seen)\b\s*(?:\.|\[)|\.(?:add|discard)\s*\(',
            src_lower,
        ))
        if python_neighbor_loop and python_visited:
            graph.is_graph = True
            graph.structure = "adj_list"
        # C++ contest BFS commonly uses a color array named c rather than a
        # descriptive visited/color identifier.  The combination of an
        # adjacency-list parameter, queue, and color assignment is sufficient
        # graph evidence without broadening generic vector detection.
        if (self.language not in {'python', 'py'} and
                re.search(r'vector\s*<\s*vector\s*<', src_lower) and
                re.search(r'\bqueue\s*<', src_lower) and
                re.search(r'\b(?:c|color|colour)\s*\[', src_lower)):
            graph.is_graph = True
            graph.structure = "adj_list"
        # Java BFS commonly uses List<List<Integer>>, ArrayDeque and a
        # boolean/color array. This is graph traversal evidence even without
        # identifiers named graph, adj, or visited.
        if (self.language in {'java', 'javascript', 'js'} and
                re.search(r'(?:list\s*<\s*list|arraylist\s*<)', src_lower) and
                re.search(r'(?:arraydeque|deque|queue)', src_lower) and
                re.search(r'(?:boolean\s*\[\]|boolean\s+\w+\s*=|color|seen)', src_lower) and
                re.search(r'\.(?:get|poll|remove|add)\s*\(', src_lower)):
            graph.is_graph = True
            graph.structure = "adj_list"
        if ('p[' in src_lower or 'parent[' in src_lower) and ('p[a]' in src_lower or 'p[b]' in src_lower or 'sz[' in src_lower or 'size[' in src_lower):
            graph.is_graph = True
            graph.structure = "edge_list"
        return graph
