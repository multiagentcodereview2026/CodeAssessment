import { useState, useEffect } from 'react';
import { Search, Filter, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const SkeletonRow = () => (
  <tr className="border-b border-slate-100 animate-pulse">
    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-24"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-32"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-16"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-12"></div></td>
    <td className="px-6 py-4"><div className="h-6 bg-slate-200 rounded-md w-20"></div></td>
    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded w-20"></div></td>
    <td className="px-6 py-4 text-right"><div className="h-4 bg-slate-200 rounded w-24 ml-auto"></div></td>
  </tr>
);

const StudentSubmissions = () => {
  const { user, authFetch } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    authFetch(`/api/submissions`)
      .then(res => res.json())
      .then(data => {
        setSubmissions(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [user, authFetch]);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <motion.div 
        initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
        className="flex justify-between items-center mb-6"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Submission History</h1>
          <p className="text-slate-500 text-sm mt-1">Live record of student code submissions and multi-agent AI reviews.</p>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
        className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow duration-300"
      >
        {submissions.length === 0 && !loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            No submissions recorded yet. Go to <Link to="/problems" className="text-indigo-600 font-semibold underline hover:text-indigo-800">Problems</Link> to submit your first code!
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
              {loading ? (
                <>
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                </>
              ) : (
                submissions.map((sub, index) => (
                  <motion.tr 
                    key={sub.submission_id} 
                    initial={{ opacity: 0, x: -10 }} 
                    animate={{ opacity: 1, x: 0 }} 
                    transition={{ delay: index * 0.05 }}
                    className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                  >
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
                      {sub.created_at ? new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', year: 'numeric', month: 'short', day: 'numeric' }) : "Just now"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link to={`/submissions/${sub.submission_id}`} className="text-indigo-600 hover:text-indigo-800 font-medium text-xs inline-flex items-center transition-colors bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-lg">
                        <Eye className="w-3.5 h-3.5 mr-1.5" /> View AI Feedback
                      </Link>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </motion.div>
    </div>
  );
};

export default StudentSubmissions;
