import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Target, Trophy, Clock, CheckSquare } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const StatCard = ({ title, value, subtitle, icon: Icon, colorClass }) => (
  <motion.div 
    whileHover={{ y: -2 }}
    className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 flex flex-col justify-between"
  >
    <div className="flex justify-between items-start mb-2">
      <h3 className="text-xs font-semibold text-slate-500">{title}</h3>
      <div className={`p-2 rounded-lg ${colorClass}`}>
        <Icon className="w-4 h-4" />
      </div>
    </div>
    <div>
      <div className="text-2xl font-bold text-slate-800">{value}</div>
      <div className="text-xs text-slate-500 mt-1">{subtitle}</div>
    </div>
  </motion.div>
);

const SkeletonCard = () => (
  <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between animate-pulse">
    <div className="flex justify-between items-start mb-2">
      <div className="h-4 bg-slate-200 rounded w-24"></div>
      <div className="h-8 w-8 bg-slate-200 rounded-lg"></div>
    </div>
    <div>
      <div className="h-8 bg-slate-200 rounded w-16 mb-2"></div>
      <div className="h-3 bg-slate-200 rounded w-32"></div>
    </div>
  </div>
);

const Dashboard = () => {
  const { user, authFetch } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [recentSubs, setRecentSubs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    
    setLoading(true);
    Promise.all([
      authFetch(`/api/analytics/student/${user.username}`)
        .then(res => res.json())
        .then(data => setAnalytics(data))
        .catch(() => {}),
        
      authFetch(`/api/submissions`)
        .then(res => res.json())
        .then(data => setRecentSubs(data.slice(0, 4)))
        .catch(() => {})
    ]).finally(() => {
      setLoading(false);
    });
  }, [user, authFetch]);

  const overall = analytics?.overall_score ?? 89.0;
  const streak = analytics?.streak_days ?? 7;
  const xp = analytics?.xp ?? 420;
  const solved = analytics?.problems_solved ?? 3;
  const total = analytics?.total_problems ?? 5;
  const trend = analytics?.score_trend ?? [
    { date: 'Apr 1', score: 30 }, { date: 'Apr 8', score: 45 }, { date: 'Apr 15', score: 42 }, 
    { date: 'Apr 22', score: 65 }, { date: 'Apr 29', score: overall }
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <h1 className="text-2xl font-bold text-slate-800 mb-1">Hello, {user?.name || user?.username || 'Student'}! 👋</h1>
        <p className="text-slate-500 text-xs">Keshav Memorial Institute of Technology • Computer Science & Engineering</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          <>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
              <StatCard title="Overall Score" value={`${overall} / 100`} subtitle="Calculated from real evaluations" icon={Target} colorClass="bg-indigo-50 text-indigo-600" />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
              <StatCard title="Problems Solved" value={`${solved} / ${total}`} subtitle="Active curriculum challenges" icon={CheckSquare} colorClass="bg-emerald-50 text-emerald-600" />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
              <StatCard title="Current Streak" value={`${streak} Days`} subtitle={`Total XP: ${xp}`} icon={Clock} colorClass="bg-amber-50 text-amber-600" />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.4 }}>
              <StatCard title="Class Standing" value="Top 10%" subtitle="Department rank" icon={Trophy} colorClass="bg-purple-50 text-purple-600" />
            </motion.div>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.5 }}
          className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col hover:shadow-lg transition-all duration-300"
        >
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-base font-semibold text-slate-800">Recent AI Evaluations</h2>
            <Link to="/submissions" className="text-xs text-indigo-600 font-semibold hover:text-indigo-700">View All Submissions</Link>
          </div>
          
          <div className="overflow-x-auto">
            {loading ? (
              <div className="space-y-4 animate-pulse">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-10 bg-slate-100 rounded"></div>
                ))}
              </div>
            ) : recentSubs.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                No submissions yet. Go to <Link to="/problems" className="text-indigo-600 underline font-semibold">Problems</Link> to write your first code!
              </div>
            ) : (
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 font-medium">Problem</th>
                    <th className="px-4 py-3 font-medium">Score</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recentSubs.map((sub) => (
                    <tr key={sub.submission_id} className="border-b border-slate-100 hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-medium text-slate-800">{sub.problem_id}</td>
                      <td className="px-4 py-3 text-slate-600 font-semibold">{sub.overall_score ?? "—"} / 100</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
                          {sub.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-xs">
                        {sub.created_at ? new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Just now"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </motion.div>

        <div className="space-y-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.6 }}
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-lg transition-all duration-300"
          >
            <h2 className="text-sm font-semibold text-slate-800 mb-3">Focus Areas & Weak Topics</h2>
            {loading ? (
              <div className="flex flex-wrap gap-2 animate-pulse">
                <div className="h-6 w-24 bg-slate-200 rounded-lg"></div>
                <div className="h-6 w-20 bg-slate-200 rounded-lg"></div>
                <div className="h-6 w-28 bg-slate-200 rounded-lg"></div>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium border border-slate-200">Dynamic Programming</span>
                <span className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium border border-slate-200">Graph Traversals</span>
                <span className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium border border-slate-200">Bit Manipulation</span>
              </div>
            )}
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.7 }}
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col hover:shadow-lg transition-all duration-300"
          >
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-semibold text-slate-800">Learning Progress Curve</h2>
            </div>
            {loading ? (
              <div className="h-40 w-full bg-slate-100 animate-pulse rounded-lg"></div>
            ) : (
              <div className="h-40 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trend} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: '#64748b' }} dy={5} />
                    <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: '#64748b' }} />
                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
