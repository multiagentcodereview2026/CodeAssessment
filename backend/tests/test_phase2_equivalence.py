from analysis.benchmark_problem_bank import _equivalent_complexity


def test_layer5_commutative_sum_equivalence():
    assert _equivalent_complexity("O(n+m)", "O(m+n)", "Array")


def test_layer5_log_variable_alias_equivalence():
    assert _equivalent_complexity("O(nlogr)", "O(n log n)", "Array")


def test_layer5_case_normalization_equivalence():
    assert _equivalent_complexity("O(N)", "O(n)", "Array")
