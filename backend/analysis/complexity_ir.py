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
    has_bit_operations: bool = False
    has_matrix_bounds: bool = False
    is_sliding_window: bool = False
    is_monotonic_stack: bool = False
    loop_complexity: str = ""
    has_constant_inner_loop: bool = False
    is_grouped_partition: bool = False
    is_amortized_membership: bool = False
    is_amortized_index_placement: bool = False
    # Stage 1 complexity algebra: the inner iteration count depends on an
    # outer loop variable (for example range(i) or j < i).  This is distinct
    # from two independent input dimensions such as range(m) x range(n).
    dependent_bounds: bool = False
    dependent_relation: str = ""
    dependent_sum_class: str = ""  # triangular, logarithmic, unknown

@dataclass
class RecursionIR:
    is_recursive: bool = False
    branch_factor: int = 0
    has_memoization: bool = False
    # Number of independent input dimensions represented by the memo key.
    # A two-dimensional state (for example f[i][j]) is O(m*n), while a
    # one-dimensional state is O(n).
    memo_dimensions: int = 1
    pattern: str = "linear"  # "linear", "divide_and_conquer", "branching", "n-ary", "tail", "memoized"
    is_divide_and_conquer: bool = False
    has_linear_combine: bool = False
    has_auxiliary_array: bool = False
    calls_inside_loop: bool = False
    reduction_type: str = "linear"  # "linear" (n-1), "divide" (n/2), "logarithmic"
    work_per_level: str = "O(1)"     # "O(1)", "O(n)", "O(n^2)"
    stack_depth: str = "O(1)"
    # Phase-L call-graph evidence.  These fields distinguish recursion that is
    # spread across helper functions (mutual/cross-function recursion) from a
    # self-call found in one function body.
    has_mutual_recursion: bool = False
    call_graph_nodes: int = 0
    call_graph_edges: int = 0
    recursive_cycle_size: int = 0

@dataclass
class GraphIR:
    is_graph: bool = False
    structure: Optional[str] = None  # 'adj_list', 'adj_matrix', 'edge_list'
    traversal_inside_loop: bool = False

@dataclass
class ControlFlowIR:
    """Stage 3 control/data-flow facts used by later algebra passes."""
    branch_count: int = 0
    early_exit_count: int = 0
    loop_carried_updates: int = 0
    amortized_push_pop: bool = False
    monotonic_pointer_updates: bool = False
    branch_join_count: int = 0

@dataclass
class ComplexityIR:
    language: str
    source: str = ""  # Add source code for pattern matching
    # Stage 1a coverage metadata. This records how structural facts were
    # obtained without changing the existing complexity output schema.
    parser_backend: str = "regex"
    loop: LoopIR = field(default_factory=LoopIR)
    recursion: RecursionIR = field(default_factory=RecursionIR)
    graph: GraphIR = field(default_factory=GraphIR)
    control_flow: ControlFlowIR = field(default_factory=ControlFlowIR)
    has_dynamic_allocation: bool = False
    input_storage_only: bool = False
    has_2d_allocation: bool = False
    has_merged_both: bool = False
    is_constant_lookup: bool = False
    multiple_input_bounds: bool = False
    space_complexity: str = ""
    time_complexity: str = ""
    # Canonical Phase-M pattern label populated by the shared pattern library.
    # It is intentionally descriptive; the engine remains the single place
    # that applies precedence and computes the final complexity.
    algorithm_pattern: str = "unknown"
    semantic_patterns: List[str] = field(default_factory=list)
    # Stage 1 normalized structural facts.  This is deliberately additive:
    # existing inference continues to consume the typed fields above, while
    # downstream stages can rely on one stable, language-neutral snapshot.
    normalized_facts: Dict[str, object] = field(default_factory=dict)
    library_costs: Dict[str, bool] = field(default_factory=dict)

