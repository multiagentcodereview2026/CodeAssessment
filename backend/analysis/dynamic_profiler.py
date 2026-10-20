import math
from typing import Any, Awaitable, Callable

from .models import ComplexityAnalysis


Executor = Callable[
    [str, str, list[dict[str, Any]]],
    Awaitable[dict[str, Any]],
]


def _estimate_growth(
    measurements: list[dict[str, Any]],
) -> str | None:
    valid = [
        row for row in measurements
        if row.get("input_size", 0) > 0
        and row.get("runtime_ms", 0) > 0
    ]

    if len(valid) < 2:
        return None

    first = valid[0]
    last = valid[-1]

    n_ratio = last["input_size"] / first["input_size"]
    time_ratio = last["runtime_ms"] / first["runtime_ms"]

    if n_ratio <= 1:
        return None

    linear_ratio = n_ratio
    log_ratio = max(1.0, math.log2(last["input_size"])) / max(
        1.0,
        math.log2(first["input_size"]),
    )
    n_log_n_ratio = linear_ratio * log_ratio
    quadratic_ratio = n_ratio ** 2

    if time_ratio <= log_ratio * 1.8:
        return "O(log n)"

    if time_ratio <= linear_ratio * 1.8:
        return "O(n)"

    if time_ratio <= n_log_n_ratio * 1.8:
        return "O(n log n)"

    if time_ratio <= quadratic_ratio * 1.8:
        return "O(n^2)"

    return "O(n^3)"


def _input_size(value: Any) -> int:
    """Return a conservative size proxy without parsing problem semantics.

    Most stdin assignments begin with ``n``.  When they do not, token count is
    a safer generic proxy than inventing an input generator.  The result is
    used only as low-confidence runtime evidence.
    """
    tokens = str(value or "").split()
    if not tokens:
        return 0
    try:
        leading = int(tokens[0])
    except (TypeError, ValueError):
        leading = 0
    return leading if leading > 0 else len(tokens)


def profile_execution_results(
    test_cases: list[dict[str, Any]],
    execution_result: dict[str, Any],
) -> ComplexityAnalysis:
    """Create safe, observational runtime evidence from the judge run.

    This intentionally does not manufacture larger problem inputs. It uses
    only server-side cases already executed for the submission. Those runs can
    include container startup, host scheduling, and heterogeneous case shapes,
    so their observed growth is *limited* corroborating evidence, never a
    strong enough measurement to overturn a confident structural analysis.
    Runtime evidence estimates time only; memory readings from short isolated
    runs are too noisy to classify Big-O space.
    """
    results = execution_result.get("results") or []
    measurements: list[dict[str, Any]] = []
    for case, result in zip(test_cases, results):
        measurements.append({
            "input_size": _input_size(case.get("input")),
            "runtime_ms": result.get("runtime_ms", 0),
            "memory_kb": result.get("memory_kb", 0),
            "status": result.get("status", "unknown"),
        })

    measurements.sort(key=lambda row: row.get("input_size", 0))
    valid = [
        row for row in measurements
        if row["input_size"] > 0
        and row["runtime_ms"] > 0
        and str(row["status"]).lower() == "accepted"
    ]
    distinct_sizes = {row["input_size"] for row in valid}
    estimated_time = _estimate_growth(valid) if len(distinct_sizes) >= 3 else None

    if estimated_time is None:
        return ComplexityAnalysis(
            method="runtime-profile",
            status="REVIEW_REQUIRED",
            confidence=0.0,
            dynamic_measurements=measurements,
            evidence_quality="insufficient",
            explanation="The completed judge run did not contain enough stable input-size measurements for runtime profiling.",
        )

    return ComplexityAnalysis(
        time_complexity=estimated_time,
        space_complexity=None,
        confidence=0.65,
        method="runtime-profile",
        status="ANALYZED",
        dynamic_measurements=measurements,
        evidence_quality="limited",
        explanation=(
            "A tentative runtime-growth estimate was observed across completed "
            "judge cases. It is not a controlled benchmark measurement."
        ),
    )


async def profile_submission(
    source_code: str,
    language: str,
    benchmark_cases: list[dict[str, Any]],
    executor: Executor,
) -> ComplexityAnalysis:
    measurements: list[dict[str, Any]] = []

    for benchmark in benchmark_cases:
        result = await executor(
            source_code,
            language,
            benchmark["test_cases"],
        )

        measurements.append(
            {
                "input_size": benchmark["input_size"],
                "runtime_ms": result.get("runtime_ms", 0),
                "memory_kb": result.get("memory_kb", 0),
                "status": result.get("execution_status", "unknown"),
            }
        )

    # Benchmark execution order is not a contract; sort before comparing
    # growth so dynamic evidence is deterministic.
    measurements.sort(key=lambda row: row.get("input_size", 0))
    valid_count = sum(
        1 for row in measurements
        if row.get("input_size", 0) > 0 and row.get("runtime_ms", 0) > 0
    )
    estimated_time = _estimate_growth(measurements)

    if estimated_time is None:
        return ComplexityAnalysis(
            status="REVIEW_REQUIRED",
            method="dynamic",
            confidence=0.0,
            dynamic_measurements=measurements,
            evidence_quality="insufficient",
            explanation=(
                "Not enough valid benchmark measurements were available."
            ),
        )

    memory_values = [
        row["memory_kb"]
        for row in measurements
        if row["memory_kb"] > 0
    ]

    estimated_space = "O(n)" if len(set(memory_values)) > 1 else "O(1)"

    return ComplexityAnalysis(
        time_complexity=estimated_time,
        space_complexity=estimated_space,
        confidence=0.65,
        method="dynamic",
        status="ANALYZED",
        dynamic_measurements=measurements,
        evidence_quality="strong" if valid_count >= 3 else "limited",
        explanation=(
            "Complexity was estimated from runtime and memory growth "
            "across controlled benchmark inputs."
        ),
    )
