import re


# ─── Rank Table ────────────────────────────────────────────────────────────────
# Rank 1 = best/cheapest, Rank 10 = worst/most expensive.
# Multi-variable and graph complexities share ranks with equivalent algorithmic tiers.

COMPLEXITY_RANKS = {
    "O(1)":             1,
    "O(log n)":         2,
    "O(log N)":         2,
    "O(log m)":         2,
    "O(log V)":         2,
    "O(H)":             2,
    "O(log m log n)":   2,
    "O(sqrt(n))":       3,
    "O(n)":             4,
    "O(N)":             4,
    "O(m)":             4,
    "O(k)":             4,
    "O(K)":             4,
    "O(W)":             4,
    "O(V)":             4,
    "O(E)":             4,
    "O(m+n)":           4,
    "O(V+E)":           4,
    "O(H + K)":         4,
    "O(H+K)":           4,
    "O(n log n)":       5,
    "O(N log N)":       5,
    "O(n log m)":       5,
    "O(m log n)":       5,
    "O(n log k)":       5,
    "O(n log K)":       5,
    "O(E log V)":       5,
    "O((V+E) log V)":   5,
    "O(V log V)":       5,
    "O(mn)":            6,
    "O(m*n)":           6,
    "O(n*m)":           6,
    "O(nk)":            6,
    "O(n*k)":           6,
    "O(nW)":            6,
    "O(n^2)":           6,
    "O(N^2)":           6,
    "O(VE)":            6,
    "O(V^2)":           6,
    "O(n^2 log n)":     7,
    "O(n^3)":           7,
    "O(N^3)":           7,
    "O(V^3)":           7,
    "O(n^4)":           7,
    "O(N^4)":           7,
    "O(n^5)":           7,
    "O(n^6)":           7,
    "O(n^4+)":          7,
    "O(n^2m)":          7,
    "O(nm^2)":          7,
    "O(2^n)":           9,
    "O(2^N)":           9,
    "O(2^V)":           9,
    "O(3^n)":           9,
    "O(n!)":            10,
    "O(N!)":            10,
    "O(V!)":            10,
}


def normalize_complexity(value: str | None) -> str | None:
    """
    Normalises a raw complexity string to one of the canonical keys in
    COMPLEXITY_RANKS. Returns the canonical string or None.
    """
    if not value:
        return None

    # ── Tidy up the raw string ─────────────────────────────────────────────
    text = value.strip().lower()
    text = text.replace(" ", "")
    text = text.replace("²", "^2")
    text = text.replace("³", "^3")
    text = text.replace("⁴", "^4")
    text = text.replace("⁵", "^5")
    text = text.replace("⁶", "^6")
    text = text.replace("∞", "inf")
    # log base variants → log  (log₂n, log₁₀n, log2n, log10n, lgn)
    text = re.sub(r"log[_₂₁₀]+", "log", text)
    text = re.sub(r"log(?:2|10)", "log", text)
    text = text.replace("lg(", "log(")

    # ── O(1) ───────────────────────────────────────────────────────────────
    if text in {"o(1)", "1", "constant", "o(c)"}:
        return "O(1)"

    # ── O(H) (Tree height logarithmic bound) ────────────────────────────────
    if text in {"o(h)", "o(height)"}:
        return "O(H)"

    # ── O(H + K) (Kth element in BST) ──────────────────────────────────────
    if text in {"o(h+k)", "o(k+h)", "o(h+k)"}:
        return "O(H + K)"

    # ── O(log n), O(log m), O(log V) ───────────────────────────────────────
    if text in {
        "o(logn)", "o(log(n))", "o(log2n)", "o(log2(n))",
        "o(log10n)", "o(log10(n))", "o(lgn)", "o(lg(n))"
    }:
        return "O(log n)"

    if text in {"o(logm)", "o(log(m))"}:
        return "O(log m)"

    if text in {"o(logv)", "o(log(v))", "o(lgv)", "o(lg(v))"}:
        return "O(log V)"

    # ── O(log m log n) ─────────────────────────────────────────────────────
    if text in {
        "o(logmlogn)", "o(log(m)log(n))", "o(logm*logn)",
        "o(logn*logm)", "o(lognlogm)"
    }:
        return "O(log m log n)"

    # ── O(sqrt(n)) ─────────────────────────────────────────────────────────
    if text in {"o(sqrt(n))", "o(sqrtn)", "o(√n)", "o(n^0.5)"}:
        return "O(sqrt(n))"

    # ── Linear Complexity O(n), O(m), O(V), O(E), O(V+E) ──────────────────
    if text in {"o(v+e)", "o(e+v)", "o((v+e))", "o(v)+o(e)"}:
        return "O(V+E)"

    if text in {"o(v)"}:
        return "O(V)"

    if text in {"o(e)"}:
        return "O(E)"

    if text in {"o(n)"}:
        return "O(n)"

    if text in {"o(m)"}:
        return "O(m)"

    if text in {"o(m+n)", "o(n+m)", "o(m)+o(n)"}:
        return "O(m+n)"

    # ── Linear x Logarithmic Complexities ─────────────────────────────────
    if text in {
        "o((v+e)logv)", "o((v+e)*logv)", "o((v+e)log(v))",
        "o((v+e)*log(v))", "o(vlogv+elogv)"
    }:
        return "O((V+E) log V)"

    if text in {
        "o(elogv)", "o(e*logv)", "o(elog(v))", "o(e*log(v))",
        "o(eloge)", "o(e*loge)"
    }:
        return "O(E log V)"

    if text in {"o(vlogv)", "o(v*logv)", "o(vlog(v))", "o(v*log(v))"}:
        return "O(V log V)"

    if text in {
        "o(nlogn)", "o(nlog(n))", "o(n*logn)", "o(n*log(n))",
        "o(nlog2n)", "o(nlog10n)"
    }:
        return "O(n log n)"

    if text in {
        "o(nlogm)", "o(nlog(m))", "o(n*logm)", "o(n*log(m))",
        "o(nlog2m)", "o(nlog10m)"
    }:
        return "O(n log m)"

    if text in {
        "o(mlogn)", "o(mlog(n))", "o(m*logn)", "o(m*log(n))",
        "o(mlog2n)", "o(mlog10n)"
    }:
        return "O(m log n)"

    # ── Quadratic / Product Complexities O(VE), O(V^2), O(mn), O(n^2) ──────
    if text in {"o(ve)", "o(v*e)", "o(ev)", "o(e*v)", "o(v*e+v)"}:
        return "O(VE)"

    if text in {"o(v^2)", "o(v*v)", "o(v²)", "o(v2)"}:
        return "O(V^2)"

    if text in {"o(mn)", "o(m*n)"}:
        return "O(m*n)"
    if text in {"o(nm)", "o(n*m)"}:
        return "O(n*m)"

    if text in {"o(n^2)", "o(n*n)", "o(n²)", "o(n2)"}:
        return "O(n^2)"

    # ── O(n^2 log n) ───────────────────────────────────────────────────────
    if text in {
        "o(n^2logn)", "o(n^2log(n))", "o(n^2*logn)",
        "o(n²logn)", "o(n2logn)"
    }:
        return "O(n^2 log n)"

    # ── Cubic & Higher Polynomials O(V^3), O(n^3), O(n^4), O(n^5)... ──────
    if text in {"o(v^3)", "o(v*v*v)", "o(v³)", "o(v3)"}:
        return "O(V^3)"

    if text in {"o(n^3)", "o(n*n*n)", "o(n³)", "o(n3)"}:
        return "O(n^3)"

    if text in {"o(n^4)", "o(n⁴)", "o(n4)"}:
        return "O(n^4)"
    if text in {"o(n^5)", "o(n⁵)", "o(n5)"}:
        return "O(n^5)"
    if text in {"o(n^6)", "o(n⁶)", "o(n6)"}:
        return "O(n^6)"

    # ── O(n^2m) / O(nm^2) ──────────────────────────────────────────────────
    if text in {"o(n^2m)", "o(n^2*m)", "o(n2m)", "o(mn^2)", "o(m*n^2)"}:
        return "O(n^2m)"

    if text in {"o(nm^2)", "o(n*m^2)", "o(nm2)", "o(m^2n)", "o(m^2*n)"}:
        return "O(nm^2)"

    # ── O(n^4+) — any polynomial degree >= 4 ──────────────────────────────
    match = re.search(r"n\^(\d+)", text)
    if match and int(match.group(1)) >= 4:
        deg = int(match.group(1))
        canonical = f"O(n^{deg})"
        return canonical if canonical in COMPLEXITY_RANKS else "O(n^4+)"

    # ── Exponentials & Factorials ───────────────────────────────────────────
    if text in {"o(2^v)", "o(2v)", "o(2**v)"}:
        return "O(2^V)"

    if text in {"o(2^n)", "o(2n)", "o(2**n)"}:
        return "O(2^n)"

    if text in {"o(3^n)", "o(3n)", "o(3**n)"}:
        return "O(3^n)"

    if text in {"o(v!)"}:
        return "O(V!)"

    if text in {"o(n!)"}:
        return "O(n!)"

    # ── Pass-through for any recognised O(...) form not matched above ──────
    if text.startswith("o(") and text.endswith(")"):
        return value.strip()

    return None


def complexity_rank(value: str | None) -> int | None:
    normalized = normalize_complexity(value)
    if not normalized:
        return None
    if normalized in COMPLEXITY_RANKS:
        return COMPLEXITY_RANKS[normalized]
    # Any polynomial degree >= 3 is mapped to rank 7
    match = re.search(r"O\([nV]\^(\d+)\)", normalized)
    if match:
        deg = int(match.group(1))
        if deg >= 3:
            return 7
        elif deg == 2:
            return 6
        elif deg == 1:
            return 4
    return None


def rank_distance(student: str | None, optimal: str | None) -> int | None:
    student_rank = complexity_rank(student)
    optimal_rank = complexity_rank(optimal)

    if student_rank is None or optimal_rank is None:
        return None

    return max(0, student_rank - optimal_rank)


def score_complexity(
    student: str | None,
    optimal: str | None,
    maximum_score: float = 25.0,
) -> float | None:
    difference = rank_distance(student, optimal)

    if difference is None:
        return None

    penalty_per_level = maximum_score / 9
    score = maximum_score - (difference * penalty_per_level)

    return round(max(0.0, min(maximum_score, score)), 3)