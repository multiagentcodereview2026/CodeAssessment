"""C++ fixtures for the local complexity detector.

These are detector tests only.  They never execute a submission, create a
database row, or expose hidden test cases.
"""

import pytest

from analysis.static_analyzer import analyze_cpp


@pytest.mark.parametrize(
    ("source", "expected_time", "expected_space"),
    [
        (
            "int f(vector<int>& nums) { int total=0; for (int x: nums) total += x; return total; }",
            "O(n)",
            "O(1)",
        ),
        (
            "int f(vector<int>& a, int target) { int low=0, right=a.size()-1; while(low<=right) { int mid=(low+right)/2; if(a[mid]<target) low=mid+1; else right=mid-1; } return -1; }",
            "O(log n)",
            "O(1)",
        ),
        (
            "int f(vector<int>& a) { sort(a.begin(), a.end()); return a[0]; }",
            "O(n log n)",
            "O(1)",
        ),
        (
            "int f(vector<int>& a) { int ans=0; for(int i=0;i<a.size();++i) { for(int j=0;j<a.size();++j) ans += a[i]*a[j]; } return ans; }",
            "O(n^2)",
            "O(1)",
        ),
        (
            "void f(vector<vector<int>>& groups) { for(auto& g: groups) { sort(g.begin(), g.end()); } }",
            "O(n^2 log n)",
            "O(1)",
        ),
        (
            "int f(vector<int>& a) { unordered_map<int,int> freq; for(int x: a) ++freq[x]; return freq.size(); }",
            "O(n)",
            "O(n)",
        ),
        (
            "int f(vector<int>& a) { vector<int> dp(a.size()); for(int i=0;i<a.size();++i) dp[i]=a[i]; return dp.back(); }",
            "O(n)",
            "O(n)",
        ),
    ],
)
def test_cpp_static_detector_fixtures(source, expected_time, expected_space):
    result = analyze_cpp(source)
    assert result.time_complexity == expected_time
    assert result.space_complexity == expected_space
