from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class LoopIR:
    depth: int = 0
    structure: str = "none" # "none", "single", "sequential", "nested"
    bounds: List[str] = field(default_factory=list)
    has_sort: bool = False
    has_binary_search: bool = False

@dataclass
class RecursionIR:
    is_recursive: bool = False
    branch_factor: int = 0
    has_memoization: bool = False
    pattern: str = "linear" # "linear", "binary", "n-ary"

@dataclass
class GraphIR:
    is_graph: bool = False
    structure: Optional[str] = None # 'adj_list', 'adj_matrix', 'edge_list'

@dataclass
class ComplexityIR:
    language: str
    loop: LoopIR = field(default_factory=LoopIR)
    recursion: RecursionIR = field(default_factory=RecursionIR)
    graph: GraphIR = field(default_factory=GraphIR)
    has_dynamic_allocation: bool = False
