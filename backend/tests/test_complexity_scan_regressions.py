from analysis.static_analyzer import analyze_source, _nested_for_bound_product
from scoring.complexity import time_complexity_assessment


STONE = '''
#include <vector>
int main() {
 int n; cin >> n; vector<int> stones(n);
 for (int i=0;i<n;++i) cin >> stones[i];
 while(stones.size()>1) {
  int count=static_cast<int>(stones.size());
  for(int i=0;i<count-1;++i) {
   for(int j=0;j<count-1-i;++j) {
    if(stones[j]>stones[j+1]) swap(stones[j],stones[j+1]);
   }
  }
  int a=stones.back(); stones.pop_back();
  int b=stones.back(); stones.pop_back();
  if(a!=b) stones.push_back(a-b);
 }
}
'''


def test_repeated_bubble_sort_counts_all_three_loop_levels():
    result = analyze_source(STONE, 'cpp')
    assert result.time_complexity == 'O(n^3)'
    assert result.space_complexity == 'O(n)'
    score = time_complexity_assessment('O(n log n)', result.time_complexity)
    assert score['classification'] != 'OPTIMAL'


def test_casts_and_induction_counters_are_not_input_dimensions():
    assert _nested_for_bound_product('''
for(int i=0;i<static_cast<int>(first.size());++i) {
 for(int j=0;j<i;++j) {}
}''') is None


def test_true_independent_scalar_bounds_are_preserved():
    assert _nested_for_bound_product('for(int i=0;i<m;++i) { for(int j=0;j<n;++j) {} }') == 'O(m*n)'


def test_triple_brute_scan_is_not_capped_at_quadratic():
    result = analyze_source('''int main() { int n; cin>>n;
 for(int i=0;i<n;++i) { for(int j=0;j<n;++j) {
  for(int k=0;k<n;++k) { cout<<i+j+k; }
 } } }''', 'cpp')
    assert result.time_complexity == 'O(n^3)'


def test_content_dependent_repetition_is_not_confidently_scored_as_sliding_window():
    result = analyze_source('''int main() {
 int n; cin>>n; vector<string> words(n);
 for(int a=0;a<n;++a) cin>>words[a];
 for(int idx=0;idx<words[0].size();++idx) {
  while(true) { bool seen=false;
   for(int i=0;i<n;++i) {
    for(int j=0;j<words[i].size();++j) { if(words[i][j]=='x') seen=true; }
   }
   if(!seen) break;
  }
 }
}''', 'cpp')
    assert result.status == 'REVIEW_REQUIRED'
    assert result.confidence < 0.85
    assert result.space_complexity != 'O(1)'


def test_sequential_passes_remain_linear():
    result = analyze_source('''int main() { int n;cin>>n;vector<int>a(n);
 for(int i=0;i<n;++i)cin>>a[i];
 for(int i=0;i<n;++i)cout<<a[i]; }''', 'cpp')
    assert result.time_complexity == 'O(n)'


def test_faster_target_receives_less_than_full_marks_for_cubic_work():
    score = time_complexity_assessment('O(n log n)', 'O(n^3)')
    assert score['time_score'] == 15


def test_programming_cast_cannot_receive_complexity_marks():
    score = time_complexity_assessment('O(n*k)', 'O(static_cast*i)')
    assert score['time_score'] is None
    assert score['classification'] == 'REVIEW_REQUIRED'
