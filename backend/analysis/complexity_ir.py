from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class LoopIR:
    depth: int = 0
    structure: str = "none"  # "none", "single", "sequential", "nested"
    bounds: List[str] = field(default_factory=list)
    has_sort: bool = False
    sort_inside_loop: bool = False
    has_binary_search: bool = False
    binary_search_inside_loop: bool = False
    binary_search_loop_depth: int = 0
    is_logarithmic_step: bool = False
    multiple_input_bounds: bool = False
    distinct_params: List[str] = field(default_factory=list)
    has_heap_operations: bool = False
    has_matrix_bounds: bool = False
    loop_complexity: str = ""

@dataclass
class RecursionIR:
    is_recursive: bool = False
    branch_factor: int = 0
    has_memoization: bool = False
    pattern: str = "linear"  # "linear", "divide_and_conquer", "branching", "n-ary", "tail", "memoized"
    is_divide_and_conquer: bool = False
    has_linear_combine: bool = False
    has_auxiliary_array: bool = False
    calls_inside_loop: bool = False
    reduction_type: str = "linear"  # "linear" (n-1), "divide" (n/2), "logarithmic"
    work_per_level: str = "O(1)"     # "O(1)", "O(n)", "O(n^2)"
    stack_depth: str = "O(1)"

@dataclass
class GraphIR:
    is_graph: bool = False
    structure: Optional[str] = None  # 'adj_list', 'adj_matrix', 'edge_list'
    traversal_inside_loop: bool = False

@dataclass
class ComplexityIR:
    language: str
    source: str = ""  # Add source code for pattern matching
    loop: LoopIR = field(default_factory=LoopIR)
    recursion: RecursionIR = field(default_factory=RecursionIR)
    graph: GraphIR = field(default_factory=GraphIR)
    has_dynamic_allocation: bool = False
    has_2d_allocation: bool = False
    has_merged_both: bool = False
    is_constant_lookup: bool = False
    multiple_input_bounds: bool = False
    space_complexity: str = ""
    time_complexity: str = ""

