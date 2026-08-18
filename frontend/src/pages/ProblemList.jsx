import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Code, ArrowRight, CheckCircle, Search, Filter } from 'lucide-react';

const ProblemList = () => {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch('/api/problems')
      .then(res => res.json())
      .then(data => {
        setProblems(data);
        setLoading(false);
      })
      .catch(() => {
        setProblems([
          { id: "two-sum", title: "Two Sum", difficulty: "Easy", category: "Arrays & Hashing" },
          { id: "binary-search", title: "Binary Search", difficulty: "Easy", category: "Searching" },
          { id: "valid-parentheses", title: "Valid Parentheses", difficulty: "Easy", category: "Stack" }
        ]);
        setLoading(false);
      });
  }, []);

  const filtered = problems.filter(p => 
    p.title.toLowerCase().includes(search.toLowerCase()) || 
    p.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Practice Problems</h1>
          <p className="text-slate-500 text-sm mt-1">Select a challenge and receive instant multi-dimensional AI evaluation.</p>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search problems or tags..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-500 shadow-sm"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((problem) => (
          <div key={problem.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-3">
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                  problem.difficulty === 'Easy' ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' :
                  problem.difficulty === 'Medium' ? 'bg-amber-50 text-amber-600 border border-amber-100' :
                  'bg-red-50 text-red-600 border border-red-100'
                }`}>
                  {problem.difficulty}
                </span>
                <span className="text-xs text-slate-400 font-medium">{problem.category}</span>
              </div>
              <h2 className="text-lg font-bold text-slate-800 mb-2">{problem.title}</h2>
              <p className="text-slate-500 text-xs line-clamp-2 mb-6">
                Master optimal space and time complexity tradeoffs with automated LangGraph agent review.
              </p>
            </div>

            <Link 
              to={`/problems/${problem.id}`}
              className="w-full py-2.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 font-semibold text-xs rounded-xl flex items-center justify-center transition-colors"
            >
              Solve Problem <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProblemList;
