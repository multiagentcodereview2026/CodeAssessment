import { useState, useEffect } from 'react';
import { Search, Filter, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const StudentSubmissions = () => {
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    fetch(`/api/submissions?student_id=${user.id}`)
      .then(res => res.json())
      .then(data => {
        setSubmissions(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [user]);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Submission History</h1>
          <p className="text-slate-500 text-sm mt-1">Live record of student code submissions and multi-agent AI reviews.</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {submissions.length === 0 && !loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            No submissions recorded yet. Go to <Link to="/problems" className="text-indigo-600 font-semibold underline">Problems</Link> to submit your first code!
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-medium">Submission ID</th>
                <th className="px-6 py-4 font-medium">Problem</th>
                <th className="px-6 py-4 font-medium">Language</th>
                <th className="px-6 py-4 font-medium">Score</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Date</th>
                <th className="px-6 py-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((sub) => (
                <tr key={sub.submission_id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-6 py-4 font-mono text-slate-500 text-xs">{sub.submission_id}</td>
                  <td className="px-6 py-4 font-medium text-slate-800">{sub.problem_id}</td>
                  <td className="px-6 py-4 text-slate-600">{sub.language}</td>
                  <td className="px-6 py-4 font-bold text-slate-700">{sub.overall_score ?? "—"} / 100</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-md text-xs font-semibold">
                      {sub.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-500 text-xs">
                    {sub.created_at ? new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Just now"}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link to={`/submissions/${sub.submission_id}`} className="text-indigo-600 hover:text-indigo-800 font-medium text-xs inline-flex items-center">
                      <Eye className="w-3.5 h-3.5 mr-1" /> View AI Feedback
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default StudentSubmissions;
