from analysis.static_analyzer import analyze_source


def program(helper, call):
    return helper + '''
int main() {
    int n; cin >> n; vector<int> a(n);
    for (int i=0; i<n; ++i) {
        for (int j=0; j<n; ++j) { ''' + call + '''; }
    }
}
'''


def test_helper_scan_inside_two_loops_is_cubic():
    source = program('''int sum(const vector<int>& a, int len) {
        int s=0; for(int k=0;k<len;++k) { s+=a[k]; } return s;
    }''', 'cout << sum(a,n)')
    assert analyze_source(source, 'cpp').time_complexity == 'O(n^3)'


def test_constant_query_helper_preserves_quadratic_cost():
    source = program('int sum(const vector<int>& a, int len) { return a[len]-a[0]; }',
                     'cout << sum(a,n)')
    assert analyze_source(source, 'cpp').time_complexity == 'O(n^2)'


def test_sequential_helper_scan_does_not_multiply_previous_loops():
    source = program('''int sum(const vector<int>& a, int len) {
        int s=0; for(int k=0;k<len;++k) { s+=a[k]; } return s;
    }''', 'cout << a[j]').replace('\n}\n', '\ncout << sum(a,n);\n}\n')
    assert analyze_source(source, 'cpp').time_complexity == 'O(n^2)'
