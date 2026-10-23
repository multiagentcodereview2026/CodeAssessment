"""Deterministic, private complexity scoring policy.

The LLM identifies the apparent complexity of the submitted code. This module
compares that observation with a curated target stored only in the backend
problem record. Target complexity is never part of an LLM payload or an API
response.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional


TIME_COMPLEXITY_LEVELS = (
    "O(1)",
    "O(log n)",
    "O(sqrt n)",
    "O(n)",
    "O(n log n)",
    "O(n^2)",
    "O(n^3)",
    "O(n^4+)",
    "O(2^n)",
    "O(n!)",
)

# Kept as an alias for callers that used the previous name.
COMPLEXITY_LEVELS = list(TIME_COMPLEXITY_LEVELS)


def normalize_complexity(complexity: Optional[str]) -> Optional[str]:
    """Normalize common single-variable Big-O spellings.

    Any *one* symbolic input-size variable is canonicalized to ``n``. For
    example, ``O(L)``, ``O(m^2)``, and ``O(log P)`` use the same single-input
    growth buckets as ``O(n)``, ``O(n^2)``, and ``O(log n)``. Expressions
    containing two independent dimensions, such as ``O(V + E)`` and
    ``O(m*n)``, deliberately remain unsupported because they need a
    problem-family-specific comparator.
    """
    if not complexity or not isinstance(complexity, str):
        return None

    raw = complexity.strip().lower()
    compact = raw
    compact = compact.replace("²", "^2").replace("³", "^3")
    compact = compact.replace("ⁿ", "^n").replace("√", "sqrt")
    compact = compact.replace("·", "*").replace("×", "*")
    compact = compact.replace("**", "^")
    compact = re.sub(r"\s+", "", compact)
    # Normalize common log spellings and harmless constant factors.
    compact = compact.replace("log₂", "log").replace("log10", "log")
    compact = compact.replace("log_2", "log").replace("log_10", "log")
    compact = compact.replace("ln", "log")
    compact = re.sub(r"^o\(\d+\*", "o(", compact)

    replacements = {
        "o(1)": "O(1)",
        "o(logn)": "O(log n)",
        "o(log2n)": "O(log n)",
        "o(log(n))": "O(log n)",
        "o(sqrtn)": "O(sqrt n)",
        "o(sqrt(n))": "O(sqrt n)",
        "o(n)": "O(n)",
        "o(nlogn)": "O(n log n)",
        "o(nlog(n))": "O(n log n)",
        "o(n^2)": "O(n^2)",
        "o(n2)": "O(n^2)",
        "o(n^3)": "O(n^3)",
        "o(n3)": "O(n^3)",
        # Keep multi-factor bounded-parameter expressions exact in the report.
        # They are projected to the score ladder separately, using only the
        # private constraints of the current problem.
        "o(n*k)": "O(n*k)",
        "o(k*n)": "O(n*k)",
        "o(n^2*k)": "O(n^2*k)",
        "o(k*n^2)": "O(n^2*k)",
        "o(n*k^2)": "O(n*k^2)",
        "o(k^2*n)": "O(n*k^2)",
        "o(2^n)": "O(2^n)",
        "o(n!)": "O(n!)",
    }
    normalized = replacements.get(compact)
    if normalized:
        return normalized

    # The character alphabet in this platform's string problems is a fixed,
    # finite domain. A solution bounded by |Sigma| therefore uses constant
    # auxiliary space under the same asymptotic model as O(1).
    if compact in {"o(|\\sigma|)", "o(|sigma|)", "o(σ)", "o(alphabet)"}:
        return "O(1)"

    # Equivalent logarithmic bounds that use multiple input-size variables.
    # They remain logarithmic for the problem's input scale and can safely
    # enter the fixed ladder; other multi-variable expressions stay review-only.
    if re.fullmatch(r"o\(log\((min|max)\([a-z],?[a-z]\)\)\)", compact):
        return "O(log n)"
    if compact in {"o(log(m+n))", "o(log(m+n))"}:
        return "O(log n)"
    # For this platform, m+n represents the total input size and is mapped
    # to the single-size linear buckets used by the fixed scoring ladder.
    if compact in {"o(m+n)", "o(n+m)", "o(rows+cols)", "o(cols+rows)"}:
        return "O(n)"
    if compact in {
        "o((m+n)log(m+n))",
        "o((n+m)log(n+m))",
        "o(m+nlog(m+n))",
    }:
        return "O(n log n)"

    # The ladder intentionally buckets every polynomial above cubic into one
    # rank. This keeps O(n^4), O(n^5), and O(n^k) comparable without adding
    # unbounded ranks while preserving exponential and factorial levels.
    polynomial_match = re.fullmatch(r"o\(n\^(\d+)\)", compact)
    if polynomial_match and int(polynomial_match.group(1)) >= 4:
        return "O(n^4+)"
    polynomial_match = re.fullmatch(r"o\(n(\d+)\)", compact)
    if polynomial_match and int(polynomial_match.group(1)) >= 4:
        return "O(n^4+)"

    # Fixed ten-bucket projection of the wider asymptotic hierarchy. These
    # rules cover common logarithmic powers and fractional polynomial terms.
    if re.fullmatch(r"o\((log|loglog|logloglog|log\*)n?\)", compact):
        return "O(log n)"
    if re.fullmatch(r"o\(log\^\d+n\)", compact):
        return "O(log n)"
    if re.fullmatch(r"o\(\(?logn\)?\^\d+\)", compact):
        return "O(log n)"
    if compact in {"o(sqrtlogn)", "o(n^(1/4))", "o(n^(1/3))", "o(sqrtn)"}:
        return "O(sqrt n)"
    if compact in {"o(n/logn)", "o(n/log^2n)", "o(n^(1/2))"}:
        return "O(sqrt n)"
    if compact in {"o(nloglogn)", "o(nlog^2n)", "o(nlog^3n)", "o(n^(3/2))"}:
        return "O(n log n)"
    if compact in {"o(n^2/logn)", "o(n^2/log^2n)"}:
        return "O(n^2)"
    if compact in {"o(n^2loglogn)", "o(n^2logn)", "o(n^2log^2n)", "o(n^(5/2))"}:
        return "O(n^3)"
    if compact in {"o(n^3logn)", "o(n^3log^2n)"}:
        return "O(n^4+)"
    if re.fullmatch(r"o\(n\^\(logn\)\)", compact):
        return "O(n^4+)"
    if compact in {"o(2^sqrt(n))", "o(2^sqrt n)"}:
        return "O(n^4+)"
    if re.fullmatch(r"o\((2|3|4)\^n\*?n?(\^2)?\)", compact):
        return "O(2^n)"
    if re.fullmatch(r"o\(c\^n\)", compact):
        return "O(2^n)"
    return complexity.strip()


def bounded_parameters_from_constraints(constraints: object) -> set[str]:
    """Find scalar parameters with a fixed numeric upper bound.

    This is deliberately a constraint parser rather than a problem-name rule.
    ``1 <= k <= 100`` establishes that ``k`` is bounded for rank scoring,
    while ``n`` remains the platform's primary input-size variable.
    """
    if isinstance(constraints, str):
        constraints = [constraints]
    if not isinstance(constraints, (list, tuple)):
        return set()

    bounded: set[str] = set()
    for constraint in constraints:
        text = str(constraint).lower().replace("≤", "<=")
        for name, upper in re.findall(r"\b([a-z][a-z0-9_]*)\s*<=\s*(\d+)\b", text):
            if name != "n" and int(upper) >= 0:
                bounded.add(name)
    return bounded


def _score_projection(
    complexity: Optional[str],
    bounded_parameters: Iterable[str] = (),
) -> Optional[str]:
    """Project a simple monomial onto the fixed single-size rank ladder.

    The original expression is never replaced in the student report.  This
    private projection is only used for score comparison.  It supports terms
    such as ``O(k*n^2)`` when ``k`` has a fixed upper bound in the problem's
    published constraints.  General multi-variable expressions remain review
    only rather than being guessed.
    """
    # Preserve a bounded scalar's constant-size behaviour before generic
    # display normalization maps a single symbol (for example ``k``) to n.
    # ``O(k)`` with ``k <= 100`` scores as O(1), whereas unbounded ``O(k)``
    # scores as the ordinary single-input O(n) bucket.
    raw_compact = str(complexity or "").strip().lower()
    raw_compact = raw_compact.replace("²", "^2").replace("³", "^3")
    raw_compact = re.sub(r"\s+", "", raw_compact)
    bounded_monomial = re.fullmatch(
        r"o\(([a-z][a-z0-9_]*)(?:\^\d+)?\)", raw_compact
    )
    if bounded_monomial and bounded_monomial.group(1) in {
        str(name).lower() for name in bounded_parameters
    }:
        return "O(1)"

    symbolic_rank = _symbolic_single_input_rank(raw_compact)
    if symbolic_rank:
        return symbolic_rank

    normalized = normalize_complexity(complexity)
    if normalized in TIME_COMPLEXITY_LEVELS:
        return normalized
    if not normalized:
        return None

    compact = normalized.lower().replace("·", "*").replace("×", "*")
    compact = re.sub(r"\s+", "", compact)
    match = re.fullmatch(r"o\(([^()]+)\)", compact)
    if not match:
        return None

    expression = match.group(1)
    if any(token in expression for token in "+/-") or "log" in expression:
        return None
    factors = expression.split("*")
    powers: dict[str, int] = {}
    for factor in factors:
        factor_match = re.fullmatch(r"([a-z][a-z0-9_]*)(?:\^(\d+))?", factor)
        if not factor_match:
            return None
        name, exponent = factor_match.groups()
        powers[name] = powers.get(name, 0) + int(exponent or 1)

    for name in bounded_parameters:
        powers.pop(str(name).lower(), None)

    if not powers:
        return "O(1)"
    if set(powers) != {"n"}:
        return None

    degree = powers["n"]
    if degree == 1:
        return "O(n)"
    if degree == 2:
        return "O(n^2)"
    if degree == 3:
        return "O(n^3)"
    if degree >= 4:
        return "O(n^4+)"
    return None


def _benchmark_rank_projection(
    complexity: Optional[str],
    bounded_parameters: Iterable[str] = (),
) -> Optional[str]:
    """Project a curated benchmark formula onto the fixed score ladder.

    Problem-bank targets may legitimately describe several dimensions, for
    example ``O(V + E)``, ``O(m*n)``, or ``O(n*k)``.  The public assessment
    ladder nevertheless has one input-scale axis.  This function gives the
    *private benchmark* a conservative structural bucket without changing the
    formula shown anywhere in the student experience.

    This is intentionally not used for student estimates.  A student result
    with genuinely independent dimensions still requires review rather than
    being guessed.  Here the formula was already curated as the benchmark, so
    its highest polynomial growth order is a safe comparison ceiling.
    """
    strict = _score_projection(complexity, bounded_parameters)
    if strict:
        return strict

    raw = str(complexity or "").strip()
    compact = raw.lower()
    compact = compact.replace("²", "^2").replace("³", "^3")
    compact = compact.replace("·", "*").replace("×", "*").replace("**", "^")
    compact = re.sub(r"\s+", "", compact)
    match = re.fullmatch(r"o\((.*)\)", compact)
    if not match:
        return None
    expression = match.group(1)

    # Exponential and factorial growth remain above every polynomial bucket.
    if "!" in expression:
        return "O(n!)"
    if re.search(r"(?:^|\*)[2-9]\^[a-z][a-z0-9_]*(?:$|\*)", expression):
        return "O(2^n)"

    # A logarithm of any aggregate input quantity remains logarithmic in the
    # total input scale: log(m*n), log(V+E), and log(sum) all share this rank.
    if expression.startswith("log(") and expression.endswith(")"):
        return "O(log n)"

    # Split a top-level sum.  Addition is dominated by its highest-order term.
    terms = re.split(r"(?<!\^)\+", expression)
    if len(terms) > 1:
        buckets = [
            _benchmark_rank_projection(f"O({term})", bounded_parameters)
            for term in terms
        ]
        buckets = [bucket for bucket in buckets if bucket]
        if len(buckets) == len(terms):
            return max(buckets, key=complexity_rank)
        return None

    # Parentheses only group a term; min/max of input dimensions have linear
    # magnitude in the total input scale.
    expression = expression.strip("()")
    if re.fullmatch(r"(?:min|max)\([a-z][a-z0-9_]*,[a-z][a-z0-9_]*\)", expression):
        return "O(n)"

    # Standard catalogue notation often writes a product as ``mn`` rather
    # than ``m*n``.  Restrict this interpretation to two one-letter symbols so
    # ordinary names such as ``amount`` are never split heuristically.
    if re.fullmatch(r"[a-z]{2}", expression) and expression not in {"nn", "ll"}:
        return "O(n^2)"

    factors = expression.split("*")
    degree = 0
    logarithmic_factor = False
    bounded = {str(name).lower() for name in bounded_parameters}
    for factor in factors:
        factor = factor.strip("()")
        if not factor or factor.isdigit():
            continue
        if factor.startswith("log"):
            logarithmic_factor = True
            continue
        named = re.fullmatch(r"([a-z][a-z0-9_]*)(?:\^(\d+))?", factor)
        if named:
            name, exponent = named.groups()
            if name not in bounded:
                degree += int(exponent or 1)
            continue
        # A grouped logarithmic term, e.g. ``(logn)^2``, does not change the
        # polynomial degree of the fixed ladder.
        if re.fullmatch(r"log[a-z][a-z0-9_]*(?:\^\d+)?", factor):
            logarithmic_factor = True
            continue
        return None

    if degree == 0:
        return "O(1)"
    if degree == 1:
        return "O(n log n)" if logarithmic_factor else "O(n)"
    if degree == 2:
        return "O(n^3)" if logarithmic_factor else "O(n^2)"
    if degree == 3:
        return "O(n^4+)" if logarithmic_factor else "O(n^3)"
    return "O(n^4+)"


def _symbolic_single_input_rank(compact: str) -> Optional[str]:
    """Map an exact one-input display expression onto the private rank ladder.

    The report deliberately keeps names such as ``L`` and aggregate input
    notation such as ``N + Σ|word|``. This helper is used only for score
    comparison, where they are equivalent to the platform's canonical n when
    they describe one input scale. Independent dimensions remain unresolved.
    """
    compact = str(compact or "")
    compact = compact.replace("∑", "sum").replace("Σ", "sum").replace("σ", "sum")
    compact = compact.replace("·", "*").replace("×", "*").replace("**", "^")

    # Count plus a sum of the same collection's element sizes is one total
    # input scale for the fixed rank ladder: O(N + Σ|word|) -> O(n).
    aggregate = r"[a-z][a-z0-9_]*"
    if re.fullmatch(
        rf"o\((?:{aggregate}\+sum\|{aggregate}\||sum\|{aggregate}\|\+{aggregate})\)",
        compact,
    ):
        return "O(n)"

    if re.fullmatch(r"o\(log\(?[a-z][a-z0-9_]*\)?\)", compact):
        return "O(log n)"
    if re.fullmatch(r"o\(sqrt\(?[a-z][a-z0-9_]*\)?\)", compact):
        return "O(sqrt n)"
    if re.fullmatch(r"o\(([a-z][a-z0-9_]*)log\1\)", compact):
        return "O(n log n)"
    if re.fullmatch(r"o\([a-z][a-z0-9_]*!\)", compact):
        return "O(n!)"
    if re.fullmatch(r"o\([2-9]\^[a-z][a-z0-9_]*\)", compact):
        return "O(2^n)"

    # Constant multiples of one symbolic variable are still linear. The
    # lower-cased representation makes N and n one display dimension here.
    additive_terms = compact.removeprefix("o(").removesuffix(")").split("+")
    if len(additive_terms) > 1:
        dimensions = []
        for term in additive_terms:
            match = re.fullmatch(r"(?:\d+\*?)?([a-z][a-z0-9_]*)", term)
            if not match:
                dimensions = []
                break
            dimensions.append(match.group(1))
        if dimensions and len(set(dimensions)) == 1:
            return "O(n)"

    monomial = re.fullmatch(r"o\(([a-z][a-z0-9_]*)(?:\^(\d+))?\)", compact)
    if not monomial:
        return None
    _name, exponent = monomial.groups()
    degree = int(exponent or 1)
    if degree == 1:
        return "O(n)"
    if degree == 2:
        return "O(n^2)"
    if degree == 3:
        return "O(n^3)"
    if degree >= 4:
        return "O(n^4+)"
    return None


def complexity_rank(complexity: str) -> int:
    normalized = normalize_complexity(complexity)
    if normalized not in TIME_COMPLEXITY_LEVELS:
        raise ValueError(f"Unsupported single-variable complexity: {complexity}")
    # The approved assessment policy uses ranks 1 through 10, not zero-based
    # array indexes. This makes the stored rank and its explanation unambiguous.
    return TIME_COMPLEXITY_LEVELS.index(normalized) + 1


def private_time_complexity_breakdown(
    optimal_time: Optional[str],
    student_time: Optional[str],
    *,
    bounded_parameters: Iterable[str] = (),
) -> dict[str, Any]:
    """Calculate the complete rank-distance assessment inside the backend.

    The result includes private benchmark data and must never be returned from
    an API endpoint or added to an AI prompt. ``time_complexity_assessment``
    below creates the student-safe representation.
    """
    normalized_student = normalize_complexity(student_time)
    normalized_target = normalize_complexity(optimal_time)

    if not optimal_time:
        return {
            "status": "TARGET_NOT_CONFIGURED",
            "classification": "REVIEW_REQUIRED",
            "time_score": None,
            "score_percent": None,
            "student_time_complexity": normalized_student,
            "reason": "A verified complexity benchmark has not been configured for this problem.",
        }

    if not student_time:
        return {
            "status": "ANALYSIS_UNAVAILABLE",
            "classification": "REVIEW_REQUIRED",
            "time_score": None,
            "score_percent": None,
            "student_time_complexity": None,
            "reason": "The submitted algorithm could not be classified automatically.",
        }

    # Project the original expressions so a bounded scalar (for example
    # ``k <= 100``) is still recognised before display normalization maps a
    # single variable to the generic n bucket.
    projected_target = (
        _score_projection(optimal_time, bounded_parameters)
        or _benchmark_rank_projection(optimal_time, bounded_parameters)
    )
    projected_student = _score_projection(student_time, bounded_parameters)
    if not projected_target or not projected_student:
        return {
            "status": "REVIEW_REQUIRED",
            "classification": "REVIEW_REQUIRED",
            "time_score": None,
            "score_percent": None,
            "student_time_complexity": normalized_student,
            "reason": "This problem uses variables that require a problem-specific complexity comparison.",
        }

    optimal_rank = complexity_rank(projected_target)
    student_rank = complexity_rank(projected_student)
    difference = student_rank - optimal_rank
    # Score the student relative to the benchmark's remaining worse ranks,
    # rather than against the whole ten-level ladder.  A one-rank regression
    # from an O(n) target should therefore matter more than a one-rank
    # regression from an O(1) target: the former has fewer acceptable slower
    # buckets before reaching the worst category.  This is deterministic and
    # applies equally to time and auxiliary-space assessments.
    worse_ranks_available = len(TIME_COMPLEXITY_LEVELS) - optimal_rank
    penalty = (
        0.0
        if difference <= 0
        else min(25.0, difference * (25.0 / max(1, worse_ranks_available)))
    )
    marks = round(max(0.0, min(25.0, 25.0 - penalty)), 3)

    if difference <= 0:
        classification = "OPTIMAL"
    elif difference == 1:
        classification = "NEAR_OPTIMAL"
    elif difference <= 3:
        classification = "MODERATE"
    elif difference <= 5:
        classification = "INEFFICIENT"
    else:
        classification = "VERY_INEFFICIENT"

    return {
        "status": "SCORED",
        "classification": classification,
        "time_score": marks,
        "score_percent": round(marks * 4, 3),
        "student_time_complexity": normalized_student,
        # Private evaluation-only values. The wrapper removes them.
        "optimal_time_complexity": normalized_target,
        "student_rank": student_rank,
        "optimal_rank": optimal_rank,
        "difference": difference,
        "penalty": round(penalty, 3),
        "benchmark_review_required": difference < 0,
        "reason": "The detected time complexity was compared with the private benchmark for this problem.",
    }


def private_space_complexity_breakdown(
    optimal_space: Optional[str],
    student_space: Optional[str],
    *,
    bounded_parameters: Iterable[str] = (),
) -> dict[str, Any]:
    """Apply the same private 1–10 rank-distance policy to auxiliary space."""
    result = private_time_complexity_breakdown(
        optimal_space,
        student_space,
        bounded_parameters=bounded_parameters,
    )
    result["student_space_complexity"] = result.get("student_time_complexity")
    if result.get("status") == "SCORED":
        result["reason"] = "The detected auxiliary-space complexity was compared with the private benchmark for this problem."
    return result


def time_complexity_assessment(
    optimal_time: Optional[str],
    student_time: Optional[str],
    *,
    bounded_parameters: Iterable[str] = (),
) -> dict[str, Any]:
    """Return the 25-mark time-complexity result without exposing targets.

    The returned value intentionally omits the target, its rank and the rank
    difference. Those values are private assessment data.
    """
    private = private_time_complexity_breakdown(
        optimal_time,
        student_time,
        bounded_parameters=bounded_parameters,
    )
    return {
        "status": private["status"],
        "classification": private["classification"],
        "time_score": private["time_score"],
        "score_percent": private["score_percent"],
        "student_time_complexity": private["student_time_complexity"],
        "reason": private["reason"],
    }


def space_complexity_assessment(
    optimal_space: Optional[str],
    student_space: Optional[str],
    *,
    bounded_parameters: Iterable[str] = (),
) -> dict[str, Any]:
    """Create a student-safe 25-mark auxiliary-space assessment."""
    private = private_space_complexity_breakdown(
        optimal_space,
        student_space,
        bounded_parameters=bounded_parameters,
    )
    return {
        "status": private["status"],
        "classification": private["classification"],
        "space_score": private["time_score"],
        "score_percent": private["score_percent"],
        "student_space_complexity": private["student_space_complexity"],
        "reason": private["reason"],
    }


def calculate_complexity_component_score(expected: str, student: str) -> float:
    """Legacy 0-100 wrapper for the new time-score policy."""
    result = time_complexity_assessment(expected, student)
    if result["score_percent"] is None:
        raise ValueError("Complexity requires problem-specific review")
    return float(result["score_percent"])


def calculate_complexity_score(
    expected_time: str,
    student_time: str,
    expected_space: str,
    student_space: str,
) -> float:
    """Compatibility wrapper; the active policy scores time only (/25)."""
    del expected_space, student_space
    return calculate_complexity_component_score(expected_time, student_time)
