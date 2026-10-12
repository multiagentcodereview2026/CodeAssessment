"""Small, conservative library/data-structure cost registry."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LibraryCostEvidence:
    sort: bool = False
    hash_average_constant: bool = False
    heap_logarithmic: bool = False
    dynamic_append_amortized: bool = False


def detect_library_costs(source: str, language: str = "") -> LibraryCostEvidence:
    text = (source or "").lower()
    sort = bool(re.search(r"\b(?:std::)?sort\s*\(|\bsorted\s*\(|\.sort\s*\(", text))
    hash_ops = bool(re.search(
        r"\b(?:unordered_map|unordered_set|hash_map|hash_set|dict|set|map)\b"
        r"|\.(?:find|contains|count|add|insert|emplace|get)\s*\(", text,
    ))
    heap = bool(re.search(
        r"\b(?:heapq|priority_queue|binary_heap|heap)\b"
        r"|\.(?:heappush|heappop|push_heap|pop_heap)\s*\(", text,
    ))
    append = bool(re.search(r"\.(?:append|push_back|emplace_back|push)\s*\(", text))
    return LibraryCostEvidence(
        sort=sort,
        hash_average_constant=hash_ops,
        heap_logarithmic=heap,
        dynamic_append_amortized=append,
    )

