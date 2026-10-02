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
    is_logarithmic_step: bool = False
    multiple_input_bounds: bool = False
    distinct_params: List[str] = field(default_factory=list)

@dataclass
class RecursionIR:
    is_recursive: bool = False
    branch_factor: int = 0
    has_memoization: bool = False
    pattern: str = "linear"  # "linear", "divide_and_conquer", "branching", "n-ary", "tail", "memoized"
    is_divide_and_conquer: bool = False
    has_linear_combine: bool = False
    has_auxiliary_array: bool = False

@dataclass
class GraphIR:
    is_graph: bool = False
    structure: Optional[str] = None  # 'adj_list', 'adj_matrix', 'edge_list'

@dataclass
class ComplexityIR:
    language: str
    loop: LoopIR = field(default_factory=LoopIR)
    recursion: RecursionIR = field(default_factory=RecursionIR)
    graph: GraphIR = field(default_factory=GraphIR)
    has_dynamic_allocation: bool = False
    is_constant_lookup: bool = False
    multiple_input_bounds: bool = False
