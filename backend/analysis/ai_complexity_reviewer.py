"""Bounded AI corroboration for uncertain deterministic complexity analysis.

AI is never allowed to become the scoring authority here. It receives only
the submitted code and language, then its independent result is compared with
the AST estimate outside of the provider prompt.
"""
from __future__ import annotations

import asyncio
import json
from collections import OrderedDict, deque
from dataclasses import dataclass
from hashlib import sha256
from time import monotonic
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field


class AIComplexityReview(BaseModel):
    time_complexity: str | None = None
    space_complexity: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""
    evidence: list[str] = Field(default_factory=list)
    status: str = "NEEDS_REVIEW"


@dataclass(frozen=True)
class ComplexityReview:
    time_complexity: str | None
    space_complexity: str | None
    confidence: float
    status: str
    evidence: list[str]
    # Provider proposal is retained for audit/CLI output. When status is
    # ``AI_FALLBACK``, the primary time/space fields contain that validated
    # code-only AI estimate.
    ai_time_complexity: str | None = None
    ai_space_complexity: str | None = None
    ai_confidence: float | None = None


class AIReviewRateLimiter:
    """Non-blocking per-process guard for optional complexity reviews.

    A full queue would make a student submission wait behind provider traffic.
    Instead, saturated requests retain their deterministic review-required
    outcome and can be retried later.  This keeps grading available during a
    provider outage or 429 burst.
    """

    def __init__(self, requests_per_minute: int, max_concurrency: int) -> None:
        self.requests_per_minute = max(1, requests_per_minute)
        self._requests: deque[float] = deque()
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.BoundedSemaphore(max(1, max_concurrency))

    async def try_acquire(self) -> bool:
        async with self._lock:
            now = monotonic()
            while self._requests and now - self._requests[0] >= 60:
                self._requests.popleft()
            if len(self._requests) >= self.requests_per_minute or self._semaphore.locked():
                return False
            self._requests.append(now)
            await self._semaphore.acquire()
            return True

    def release(self) -> None:
        self._semaphore.release()


class ComplexityReviewCache:
    """Small TTL cache keyed by normalized submitted source and language."""

    def __init__(self, ttl_seconds: int, max_entries: int = 512) -> None:
        self.ttl_seconds = max(1, ttl_seconds)
        self.max_entries = max_entries
        self._items: OrderedDict[str, tuple[float, ComplexityReview]] = OrderedDict()

    @staticmethod
    def key(
        source_code: str,
        language: str,
        ast_result: dict[str, Any] | None,
        runtime_measurements: list[dict[str, Any]] | None = None,
    ) -> str:
        normalized_code = "\n".join(line.strip() for line in source_code.splitlines() if line.strip())
        payload = "\x1f".join((
            language.lower().strip(), normalized_code,
            json.dumps(runtime_measurements or [], sort_keys=True),
        ))
        return sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> ComplexityReview | None:
        item = self._items.get(key)
        if item is None:
            return None
        expires_at, review = item
        if monotonic() >= expires_at:
            del self._items[key]
            return None
        self._items.move_to_end(key)
        return review

    def put(self, key: str, review: ComplexityReview) -> None:
        self._items[key] = (monotonic() + self.ttl_seconds, review)
        self._items.move_to_end(key)
        while len(self._items) > self.max_entries:
            self._items.popitem(last=False)


def build_review_payload(
    source_code: str,
    language: str,
    ast_result: dict[str, Any] | None,
    runtime_measurements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create an independent, target-free, code-only AI prompt payload.

    ``ast_result`` remains in the signature for cache/caller compatibility but
    is deliberately excluded from the provider payload.  The reviewer must
    derive its estimate from source alone, without being anchored to AST's
    estimate, signals, a benchmark, or ground truth.
    """
    payload = {
        "instruction": (
            "Analyze only the submitted code. Do not infer the problem's optimal "
            "solution. Return valid JSON with time_complexity, space_complexity, "
            "confidence, reasoning, evidence, and status. Explain source-code "
            "structures that support the estimate. Use NEEDS_REVIEW when the code "
            "does not provide enough evidence."
        ),
        "language": language,
        "source_code": source_code,
    }
    if runtime_measurements:
        # These are raw observations, not an AST conclusion. They help only
        # when profiling was possible and do not anchor the model to a label.
        payload["runtime_measurements"] = runtime_measurements
    return payload


def _canonical(value: str | None) -> str | None:
    if not value:
        return None
    text = value.lower().replace(" ", "").replace("×", "*")
    return text.replace("\\log", "log")


def resolve_review(
    ast_result: dict[str, Any] | None,
    ai_result: AIComplexityReview | dict[str, Any] | None,
    *,
    minimum_confidence: float = 0.70,
) -> ComplexityReview:
    """Resolve a low-confidence AST review using independent AI evidence.

    An AI answer is allowed to replace an AST guess only in this fallback
    path: it must provide both estimates, source-derived evidence, meet the
    configured confidence minimum, and be more confident than the AST guess.
    This function never changes a high-confidence direct AST result because
    those do not enter AI review in the first place.
    """
    ast = ast_result or {}
    ai = AIComplexityReview.model_validate(ai_result or {})
    ast_time = ast.get("time_complexity")
    ast_space = ast.get("space_complexity")
    time_agrees = ast_time and ai.time_complexity and _canonical(ast_time) == _canonical(ai.time_complexity)
    space_agrees = ast_space and ai.space_complexity and _canonical(ast_space) == _canonical(ai.space_complexity)
    ast_confidence = float(ast.get("confidence") or 0.0)
    ai_confidence = float(ai.confidence)
    evidence = list(ai.evidence)
    if ai.reasoning:
        evidence.append(ai.reasoning)
    # AI receives only code, so its evidence must be independently generated.
    # Agreement still requires both canonical estimates to match; a blank AI
    # explanation is not enough to corroborate a deterministic result.
    evidence_supported = bool(ai.evidence)

    if time_agrees and space_agrees and ai_confidence >= minimum_confidence and evidence_supported:
        return ComplexityReview(
            ast_time,
            ast_space,
            round(min(1.0, max(ast_confidence, ai_confidence) + 0.10), 3),
            "AGREEMENT",
            evidence + ["AST and AI complexity results agree."],
            ai.time_complexity,
            ai.space_complexity,
            ai_confidence,
        )

    # There are only two independent estimates, so a numerical "majority" is
    # not meaningful. For an already low-confidence AST result, use the AI
    # proposal only when it carries stronger, source-derived evidence.
    if (
        ai.time_complexity
        and ai.space_complexity
        and ai_confidence >= minimum_confidence
        and ai_confidence > ast_confidence
        and evidence_supported
    ):
        return ComplexityReview(
            ai.time_complexity,
            ai.space_complexity,
            round(ai_confidence, 3),
            "AI_FALLBACK",
            evidence + ["AI code-only estimate replaced a lower-confidence AST estimate."],
            ai.time_complexity,
            ai.space_complexity,
            ai_confidence,
        )

    return ComplexityReview(
        ast_time,
        ast_space,
        round(min(ast_confidence, ai_confidence), 3),
        "NEEDS_REVIEW",
        evidence + ["AI evidence did not corroborate the AST result."],
        ai.time_complexity,
        ai.space_complexity,
        ai_confidence,
    )


async def review_complexity(
    source_code: str,
    language: str,
    ast_result: dict[str, Any] | None,
    invoke: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
    runtime_measurements: list[dict[str, Any]] | None = None,
) -> ComplexityReview:
    """Run an injected AI reviewer; no network call occurs without ``invoke``."""
    if invoke is None:
        return ComplexityReview(
            ast_result.get("time_complexity") if ast_result else None,
            ast_result.get("space_complexity") if ast_result else None,
            float((ast_result or {}).get("confidence") or 0.0),
            "AI_UNAVAILABLE",
            ["No AI reviewer was configured; AST result was preserved."],
        )
    try:
        ai_result = await invoke(build_review_payload(
            source_code, language, ast_result, runtime_measurements,
        ))
        return resolve_review(ast_result, ai_result)
    except Exception as exc:  # AI is optional and must not break AST scoring.
        return ComplexityReview(
            ast_result.get("time_complexity") if ast_result else None,
            ast_result.get("space_complexity") if ast_result else None,
            float((ast_result or {}).get("confidence") or 0.0),
            "AI_ERROR",
            [f"AI reviewer unavailable: {type(exc).__name__}"],
        )


async def review_with_limits(
    source_code: str,
    language: str,
    ast_result: dict[str, Any] | None,
    *,
    invoke: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    limiter: AIReviewRateLimiter,
    cache: ComplexityReviewCache,
    minimum_confidence: float = 0.70,
    runtime_measurements: list[dict[str, Any]] | None = None,
) -> ComplexityReview:
    """Use cache and a non-blocking rate limit around an optional AI call."""
    key = cache.key(source_code, language, ast_result, runtime_measurements)
    cached = cache.get(key)
    if cached is not None:
        return cached
    if not await limiter.try_acquire():
        return ComplexityReview(
            (ast_result or {}).get("time_complexity"),
            (ast_result or {}).get("space_complexity"),
            float((ast_result or {}).get("confidence") or 0.0),
            "AI_RATE_LIMITED",
            ["AI review was deferred because the optional review budget is exhausted."],
        )
    try:
        review = await review_complexity(
            source_code, language, ast_result, invoke, runtime_measurements,
        )
        if review.status == "AGREEMENT":
            cache.put(key, review)
        return review
    finally:
        limiter.release()
