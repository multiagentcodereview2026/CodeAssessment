"""C++ fixtures for the local complexity detector.

These are detector tests only.  They never execute a submission, create a
database row, or expose hidden test cases.
"""

import pytest

from analysis.static_analyzer import analyze_cpp, analyze_source


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


def test_cpp_sliding_window_left_right_names_are_not_tree_space_evidence():
    source = (
        "class Solution { public: int lengthOfLongestSubstring(string s) { "
        "unordered_set<char> seen; int left=0, best=0; "
        "for (int right=0; right<s.size(); ++right) { "
        "while (seen.count(s[right])) { seen.erase(s[left]); ++left; } "
        "seen.insert(s[right]); best=max(best,right-left+1); } return best; } };"
    )
    result = analyze_cpp(source)
    assert result.space_complexity == "O(n)"


def test_cpp_all_substrings_with_pairwise_character_checks_complexity():
    source = r"""
    #include <bits/stdc++.h>
    using namespace std;
    int main() {
        string s;
        cin >> s;
        int n = s.length();
        vector<string> subs;
        for (int i = 0; i < n; i++) {
            for (int j = i; j < n; j++) {
                string temp = "";
                for (int k = i; k <= j; k++) {
                    temp += s[k];
                }
                subs.push_back(temp);
            }
        }
        int ans = 0;
        for (int i = 0; i < (int)subs.size(); i++) {
            bool valid = true;
            for (int j = 0; j < (int)subs[i].length(); j++) {
                for (int k = j + 1; k < (int)subs[i].length(); k++) {
                    if (subs[i][j] == subs[i][k]) valid = false;
                }
            }
        }
    }
    """
    result = analyze_cpp(source)
    assert result.time_complexity == "O(n^4)"
    assert result.space_complexity == "O(n^3)"

    assessed_result = analyze_source(source, "cpp")
    assert assessed_result.time_complexity == "O(n^4)"
    assert assessed_result.space_complexity == "O(n^3)"
