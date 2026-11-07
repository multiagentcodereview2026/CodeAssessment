import pytest
from analysis.analyzer_service import analyze_static_complexity


@pytest.mark.parametrize("start", [0, 2, 3, 4, 8, 10, 26])
def test_literal_start_does_not_make_variable_end_constant(start):
    source = f"""int compute(int n){{int total=0;
        for(int prefix={start};prefix<=n;++prefix)
            for(int a=0;a<prefix;++a)
                for(int b=a+1;b<prefix;++b) total+=a+b;
        return total;}}"""
    result = analyze_static_complexity(source, "cpp")
    assert result.time_complexity == "O(n^3)"


def test_fixed_alphabet_loop_is_not_subtracted_twice():
    result = analyze_static_complexity(
        "int f(int n){int x=0;for(int i=0;i<n;i++)for(int j=0;j<n;j++)for(int c=0;c<26;c++)x++;return x;}",
        "cpp",
    )
    assert result.time_complexity == "O(n^2)"
