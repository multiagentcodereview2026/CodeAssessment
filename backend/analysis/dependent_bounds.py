"""Conservative detection of dependent loop bounds.

This module only records structural evidence.  It deliberately abstains when
the relationship cannot be identified, leaving the existing algebra and
confidence policy in control of the final result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DependentBoundEvidence:
    detected: bool = False
    relation: str = ""
    sum_class: str = ""


def detect_dependent_bounds(source: str, language: str = "") -> DependentBoundEvidence:
    text = source or ""
    lower = text.lower()

    # Python range forms: for i in range(n): for j in range(i/n-i).
    python_outer = re.search(r"\bfor\s+(?P<outer>[a-z_]\w*)\s+in\s+range\s*\(", lower)
    if python_outer:
        outer = python_outer.group("outer")
        inner = re.search(
            rf"\bfor\s+(?P<inner>[a-z_]\w*)\s+in\s+range\s*\(\s*(?:[^)]*\b)?",
            lower[python_outer.end():],
        )
        if inner:
            inner_expr = lower[python_outer.end() + inner.start():python_outer.end() + inner.end()]
            if re.search(rf"\b{re.escape(outer)}\b", inner_expr):
                relation = "inner-bound-uses-outer"
                if re.search(rf"\brange\s*\(\s*(?:\w+\s*-\s*)?{re.escape(outer)}\b", inner_expr):
                    relation = "inner-bound-uses-outer-complement"
                return DependentBoundEvidence(True, relation, "triangular")

    # C-family forms: for (i=0; i<n; ++i) for (j=0; j<i; ++j), including
    # n-i and i/2 style derived bounds.  Limit the search to loop headers so
    # arbitrary arithmetic in the body cannot create a false positive.
    headers = re.findall(r"\b(?:for|while)\s*\(([^)]*)\)", lower)
    if len(headers) >= 2:
        outer_counter = None
        outer_index = -1
        for index, header in enumerate(headers):
            match = re.search(r"(?:int|long|size_t|auto)?\s*([a-z_]\w*)\s*=", header)
            if match:
                outer_counter = match.group(1)
                outer_index = index
                break
        if outer_counter:
            for header in headers[outer_index + 1:]:
                condition = header.split(";", 2)[1] if header.count(";") >= 1 else header
                # Require an actual relational bound.  Merely mentioning the
                # outer index in a collision probe (for example `used[h]` in
                # a hash table inside `for (i=...)`) is not dependence.
                if re.search(
                    rf"(?:\b{re.escape(outer_counter)}\b\s*(?:<|<=|>|>=)|"
                    rf"(?:<|<=|>|>=)\s*\b{re.escape(outer_counter)}\b)",
                    condition,
                ):
                    return DependentBoundEvidence(True, "inner-condition-uses-outer", "triangular")

    return DependentBoundEvidence()

