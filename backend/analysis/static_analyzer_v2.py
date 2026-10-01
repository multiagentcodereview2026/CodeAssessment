"""
Enhanced static analyzer with AST support for advanced C++ complexity detection.
Falls back to regex for edge cases where AST parsing fails.
"""
from typing import Optional
from .complexity_normalizer import normalize_complexity
from .models import ComplexityAnalysis
from .ast_engine import infer_complexity_from_ir

# Import AST parser if available
try:
    from .ast_parser import parse_cpp_ast, AST_AVAILABLE
except ImportError:
    AST_AVAILABLE = False
    parse_cpp_ast = None


def analyze_cpp(source: str) -> ComplexityAnalysis:
    """
    Analyze C++ code complexity using AST when available, falling back to regex.
    """
    # Try AST-based analysis first for better accuracy
    if AST_AVAILABLE and parse_cpp_ast:
        try:
            analyzer = parse_cpp_ast(source)
            if analyzer:
                ir = analyzer.analyze()
                if ir:
                    return infer_complexity_from_ir(ir)
        except Exception:
            # Fall back to regex on any AST failure
            pass

    # Fallback to existing regex-based analysis
    return _regex_analyze_cpp(source)


# === REGEX FALLBACK (existing implementation) ===

def _regex_analyze_cpp(source: str) -> ComplexityAnalysis:
    """
    Original regex-based complexity analyzer (preserved as fallback).
    """
    from . import static_analyzer as legacy

    time_complexity = legacy._infer_time_complexity(source)
    space_complexity = legacy._infer_space_complexity(source)

    return ComplexityAnalysis(
        time_complexity=normalize_complexity(time_complexity) or "O(1)",
        space_complexity=normalize_complexity(space_complexity) or "O(1)"
    )
