import re
from typing import Dict, List, Optional, Set, Tuple, Any
from .complexity_ir import ComplexityIR, LoopIR, RecursionIR, GraphIR

# Tree-sitter imports - handle gracefully if not available
AST_AVAILABLE = False
try:
    from tree_sitter import Node, Parser, Tree
    from tree_sitter_languages import get_parser
    AST_AVAILABLE = True
except ImportError:
    # Tree-sitter not available - use regex fallback
    Node = type('Node', (), {})
    Parser = type('Parser', (), {})
    Tree = type('Tree', (), {})


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

        try:
            language_map = {
                'cpp': 'cpp',
                'c++': 'cpp',
                'c': 'c',
                'java': 'java',
                'python': 'python',
                'py': 'python',
            }

            mapped_lang = language_map.get(self.language, self.language)

            # Try to get parser
            self.parser = get_parser(mapped_lang)
            if self.parser:
                self.tree = self.parser.parse(bytes(self.source, 'utf-8'))

        except Exception:
            # Fall back to regex analysis
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
        ir = ComplexityIR(language=self.language, source=self.source)

        try:
            # Extract features from AST
            ir.loop = self._extract_loop_features(self.tree.root_node)
            ir.recursion = self._extract_recursion_features(self.tree.root_node)
            ir.graph = self._extract_graph_features(self.tree.root_node)

            # Extract additional algorithm patterns
            ir.has_heap_operations = self._detect_heap_operations()
            ir.has_matrix_bounds = self._detect_matrix_bounds()
            ir.has_dynamic_allocation = self._detect_dynamic_allocation()
            ir.has_2d_allocation = self._detect_2d_allocation()
            ir.is_constant_lookup = self._detect_constant_lookup()
            ir.multiple_input_bounds = ir.loop.multiple_input_bounds
            ir.has_merged_both = self._detect_merged_both_inputs()

        except Exception:
            # If AST extraction fails, fall back to regex
            return self._regex_analysis()

        return ir

    def _regex_analysis(self) -> ComplexityIR:
        """
        Fallback regex-based analysis when AST parsing fails or is unavailable.
        Enhanced version with comprehensive pattern detection.
        """
        ir = ComplexityIR(language=self.language, source=self.source)
        src = self.source.lower()

        # === LOOP DETECTION ===

        for_loops = len(re.findall(r'\bfor\s*\(', src))
        while_loops = len(re.findall(r'\bwhile\s*\(', src))
        do_loops = len(re.findall(r'\bdo\s*\{', src))

        total_loops = for_loops + while_loops + do_loops

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

            # Check for logarithmic inner loop: while(x>1) x/=2 inside for loop
            has_log_inner = bool(re.search(r'for\s*\([^}]*while\s*\([^)]*x\s*/=\s*2', src, re.DOTALL))

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
                if any(pattern in src for pattern in ['dp[', 'memo[', 'cache[']):
                    ir.recursion.has_memoization = True
                    ir.recursion.pattern = "memoized"
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
        graph_indicators = [
            r'\bqueue\s*<.*>\s*\w+',  # BFS queue
            r'\bdfs\s*\(',
            r'\bbfs\s*\(',
            r'\bvis\b.*\bvis\b',  # visited array used multiple times
            r'adjacency',
            r'\bNode\b',
            r'\badj\b',
        ]

        # vector<vector> is only a graph if combined with graph indicators
        has_vector_vector = bool(re.search(r'vector\s*<\s*vector\s*<', src))
        has_graph_indicator = any(re.search(p, src) for p in graph_indicators)

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

        # === SPACE COMPLEXITY PATTERNS ===

        ir.has_dynamic_allocation = self._detect_dynamic_allocation()
        ir.has_2d_allocation = self._detect_2d_allocation()
        ir.is_constant_lookup = self._detect_constant_lookup()
        ir.has_merged_both = self._detect_merged_both_inputs()

        return ir

    def _detect_heap_operations(self) -> bool:
        """Detect priority queue / heap operations that add O(log n) factor."""
        src = self.source.lower()

        heap_patterns = [
            r"priority_queue\s*<[^>]*>\s*\w+",
            r"make_heap\s*\(",
            r"push_heap\s*\(",
            r"pop_heap\s*\(",
            r"heappush\s*\(",
            r"heappop\s*\(",
        ]

        # Also detect priority_queue usage via pq.push/pq.pop/pq.top
        has_pq_decl = bool(re.search(r'priority_queue', src))
        has_pq_ops = has_pq_decl and any(
            re.search(p, src) for p in [r'\.push\s*\(', r'\.pop\s*\(', r'\.top\s*\(']
        )

        return has_pq_ops or any(re.search(p, src) for p in heap_patterns)

    def _detect_matrix_bounds(self) -> bool:
        """Detect matrix operations with distinct m*n bounds."""
        src = self.source.lower()

        # Look for nested loops with different bounds like a.size() and a[i].size()
        has_matrix_access = bool(re.search(r"a\[\s*i\s*\]\.\s*size\s*\(\)", src)) or \
                           bool(re.search(r"matrix\[\s*i\s*\]\.\s*size\s*\(\)", src)) or \
                           bool(re.search(r"grid\[\s*i\s*\]\.\s*size\s*\(\)", src)) or \
                           bool(re.search(r"a\[0\]\.size\(\)", src))  # matrix[0].size()

        # Look for explicit m*n parameters or bounds
        has_mn_params = bool(re.search(r"\bm\b.*\bn\b", src)) or \
                       bool(re.search(r"rows.*cols", src))

        return has_matrix_access or has_mn_params

    def _detect_dynamic_allocation(self) -> bool:
        """Detect dynamic memory allocation inside function body."""
        src = self.source.lower()

        # Find the function body (after first '{')
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

    def _detect_2d_allocation(self) -> bool:
        """Detect 2D dynamic allocation."""
        src = self.source.lower()

        # Only detect 2D allocation for actual 2D data structures created in the function body
        brace_pos = src.find('{')
        if brace_pos < 0:
            return False

        function_body = src[brace_pos:]
        patterns = [
            r"vector\s*<\s*vector\s*<",
            r"new\s+.*\[\s*\]\[\s*\]",
            r"malloc\s*\(\s*.*\*\s*sizeof\s*\(\s*.*\s*\*\s*\)",
        ]

        # Only count if vector<vector> is declared locally, not as a parameter
        for p in patterns:
            if re.search(p, function_body):
                # Check it's not just a parameter reference
                # If vector<vector> appears before the first '{', it's a parameter
                if p == r"vector\s*<\s*vector\s*<":
                    # Check if it's a local declaration (has a variable name after >)
                    local_decl = re.search(r"vector\s*<\s*vector\s*<[^>]+>\s*>\s+\w+\s*[\(;]", function_body)
                    if local_decl:
                        return True
                else:
                    return True

        return False

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

    def _extract_loop_features(self, root) -> LoopIR:
        """Extract loop features from AST (placeholder - uses regex fallback)."""
        return self._regex_analysis().loop

    def _extract_recursion_features(self, root) -> RecursionIR:
        """Extract recursion features from AST (placeholder - uses regex fallback)."""
        return self._regex_analysis().recursion

    def _extract_graph_features(self, root) -> GraphIR:
        """Extract graph features from AST (placeholder - uses regex fallback)."""
        return self._regex_analysis().graph
