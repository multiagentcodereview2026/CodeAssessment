import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { BookOpen, Users, FileText, ArrowUp, ArrowDown } from 'lucide-react';

const scoreDistribution = [
  { range: '0-20', count: 0 },
  { range: '21-40', count: 1 },
  { range: '41-60', count: 2 },
  { range: '61-80', count: 8 },
  { range: '81-100', count: 15 },
];

const InstructorDashboard = () => {
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    fetch('/api/instructor/overview')
      .then(res => res.json())
      .then(data => setOverview(data))
      .catch(() => {});
  }, []);

  const totalStudents = overview?.total_students ?? 5;
  const activeAssignments = overview?.active_assignments ?? 6;
  const totalSubmissions = overview?.total_submissions ?? 12;
  const classAvg = overview?.class_avg_score ?? "89.0%";
  const students = overview?.students ?? [
    { name: 'Vignesh (24BD1A058Z)', subs: 3, avg: '89.0%', trend: 'up' },
    { name: 'Mani Greeva (24BD1A0586)', subs: 2, avg: '88.4%', trend: 'up' },
    { name: 'Nayaneesh (24BD1A058K)', subs: 2, avg: '84.2%', trend: 'up' },
    { name: 'Pavan (24BD1A058V)', subs: 1, avg: '78.1%', trend: 'down' },
    { name: 'Karthikeya (24BD1A059V)', subs: 1, avg: '82.7%', trend: 'up' },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 mb-1">Total Enrolled Students</div>
          <div className="text-2xl font-bold text-slate-800 flex items-center"><Users className="w-5 h-5 mr-2 text-indigo-500" /> {totalStudents}</div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 mb-1">Active Curriculums</div>
          <div className="text-2xl font-bold text-slate-800 flex items-center"><FileText className="w-5 h-5 mr-2 text-emerald-500" /> {activeAssignments}</div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 mb-1">Submissions Evaluated</div>
          <div className="text-2xl font-bold text-slate-800 flex items-center"><BookOpen className="w-5 h-5 mr-2 text-blue-500" /> {totalSubmissions}</div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 mb-1">Class Aggregate Score</div>
          <div className="text-2xl font-bold text-emerald-600">{classAvg}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h2 className="font-semibold text-slate-800 text-sm mb-4">Class Performance Distribution</h2>
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreDistribution} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="range" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} dy={10} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col">
          <h2 className="font-semibold text-slate-800 mb-4 text-sm">Student Roster Performance</h2>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-xs text-left">
              <thead className="text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2.5 font-medium">Student</th>
                  <th className="px-3 py-2.5 font-medium">Submissions</th>
                  <th className="px-3 py-2.5 font-medium">Avg Score</th>
                  <th className="px-3 py-2.5 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s, idx) => (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-2.5 font-medium text-slate-800">{s.name}</td>
                    <td className="px-3 py-2.5 text-slate-600">{s.subs}</td>
                    <td className="px-3 py-2.5 font-bold text-slate-700">{s.avg}</td>
                    <td className="px-3 py-2.5">
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
                        {s.status || "Active"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InstructorDashboard;
