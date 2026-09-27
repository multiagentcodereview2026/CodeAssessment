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
    quadratic_ratio = n_ratio ** 2
    log_ratio = max(1.0, math.log2(last["input_size"])) / max(
        1.0,
        math.log2(first["input_size"]),
    )

    if time_ratio <= log_ratio * 1.8:
        return "O(log n)"

    if time_ratio <= linear_ratio * 1.8:
        return "O(n)"

    if time_ratio <= quadratic_ratio * 1.8:
        return "O(n^2)"

    return "O(n^3)"


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

    estimated_time = _estimate_growth(measurements)

    if estimated_time is None:
        return ComplexityAnalysis(
            status="REVIEW_REQUIRED",
            method="dynamic",
            confidence=0.0,
            dynamic_measurements=measurements,
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
        explanation=(
            "Complexity was estimated from runtime and memory growth "
            "across controlled benchmark inputs."
        ),
    )