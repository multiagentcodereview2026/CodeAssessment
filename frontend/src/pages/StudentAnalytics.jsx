import { motion } from 'framer-motion';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../context/AuthContext';

const progressData = [
  { date: 'Apr 1', score: 30 }, { date: 'Apr 8', score: 45 }, { date: 'Apr 15', score: 42 }, 
  { date: 'Apr 22', score: 65 }, { date: 'Apr 29', score: 72 }
];

const categoryScores = [
  { name: 'Correctness', value: 35.0, color: '#10b981' },
  { name: 'Time Complexity', value: 20.0, color: '#3b82f6' },
  { name: 'Space Complexity', value: 15.0, color: '#f59e0b' },
  { name: 'Code Quality', value: 20.0, color: '#8b5cf6' },
  { name: 'Originality', value: 10.0, color: '#ec4899' }
];

const StudentAnalytics = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <motion.div 
        initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-bold text-slate-800">Detailed Analytics</h1>
        <p className="text-slate-500 text-sm mt-1">Deep dive into your performance metrics and AI evaluation breakdown.</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div 
          initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-lg transition-all duration-300"
        >
          <h2 className="text-base font-semibold text-slate-800 mb-6">Overall Score Trend</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={progressData} margin={{ top: 5, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.4 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-lg transition-all duration-300"
        >
          <h2 className="text-base font-semibold text-slate-800 mb-6">Multi-Agent Category Averages</h2>
          <div className="flex items-center h-64">
            <div className="w-1/2 h-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={categoryScores} cx="50%" cy="50%" innerRadius={55} outerRadius={75} paddingAngle={4} dataKey="value">
                    {categoryScores.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="w-1/2 pl-4 space-y-2.5">
              {categoryScores.map((entry, idx) => (
                <motion.div 
                  key={idx} 
                  initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 + idx * 0.1 }}
                  className="flex items-center text-xs hover:bg-slate-50 p-1.5 rounded transition-colors"
                >
                  <div className="w-2.5 h-2.5 rounded-full mr-2" style={{ backgroundColor: entry.color }}></div>
                  <span className="text-slate-600 flex-1">{entry.name}</span>
                  <span className="font-semibold text-slate-800">{entry.value}%</span>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default StudentAnalytics;
