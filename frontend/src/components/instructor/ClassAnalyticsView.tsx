import React, { useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Award,
  AlertTriangle,
  Calendar,
  Layers,
  ChevronDown
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreDistributionBarChart, ScoreTrendLineChart } from '../common/ChartComponents';

export const ClassAnalyticsView: React.FC = () => {
  const { instructorStats, studentRoster } = useApp();
  const [selectedRange, setSelectedRange] = useState('This Month');

  const topicWeaknessStats = [
    { topic: 'Dynamic Programming', failRate: '42.5%', studentsCount: 19, severity: 'High' },
    { topic: 'Graphs (BFS/DFS)', failRate: '36.8%', studentsCount: 16, severity: 'High' },
    { topic: 'Trees & Recursion', failRate: '28.1%', studentsCount: 12, severity: 'Medium' },
    { topic: 'Linked Lists', failRate: '18.4%', studentsCount: 8, severity: 'Low' },
    { topic: 'Arrays & Two Pointers', failRate: '8.2%', studentsCount: 4, severity: 'Low' }
  ];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Class Performance Analytics
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Cohort grade metrics, multi-agent score trends, and concept weakness heatmaps.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedRange}
            onChange={(e) => setSelectedRange(e.target.value)}
            className="bg-white border border-slate-200 text-xs font-semibold text-slate-700 rounded-xl px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="This Month">This Month (May)</option>
            <option value="Last Month">April 2026</option>
            <option value="Full Semester">Full Semester</option>
          </select>
        </div>
      </div>

      {/* Top 3 Metric Cards (Matches Step 3 in diagram) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Average Score
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 font-mono">
              {instructorStats.averageScore}%
            </span>
            <span className="text-xs text-emerald-600 font-bold">+2.4% vs midterm</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">
            Highest Score
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-emerald-700 font-mono">
              {instructorStats.highestScore}%
            </span>
            <span className="text-xs text-slate-500">(Ananya S.)</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-rose-600">
            Lowest Score
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-700 font-mono">
              {instructorStats.lowestScore}%
            </span>
            <span className="text-xs text-rose-600 font-semibold">Requires Intervention</span>
          </div>
        </div>
      </div>

      {/* Score Distribution Bar Chart */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">Cohort Score Distribution (0 - 100)</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">48 Enrolled Submissions</span>
        </div>

        <div className="pt-4">
          <ScoreDistributionBarChart distribution={instructorStats.scoreDistribution} />
        </div>
      </div>

      {/* Weak Topics & Common Mistakes Section */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h3 className="text-base font-bold text-slate-900">Cohort Algorithmic Weaknesses & Common Pitfalls</h3>
          </div>
          <span className="text-xs text-indigo-600 font-semibold">AI Diagnosed</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 font-semibold text-[11px] uppercase">
                <th className="pb-3">Topic / Concept Area</th>
                <th className="pb-3">Failure / Deduction Rate</th>
                <th className="pb-3">Impacted Students</th>
                <th className="pb-3">Severity</th>
                <th className="pb-3 text-right">Recommended Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {topicWeaknessStats.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3.5 font-bold text-slate-800">{item.topic}</td>
                  <td className="py-3.5 font-mono text-slate-700">{item.failRate}</td>
                  <td className="py-3.5 font-mono text-slate-700">{item.studentsCount} students</td>
                  <td className="py-3.5">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      item.severity === 'High' ? 'bg-rose-100 text-rose-800' :
                      item.severity === 'Medium' ? 'bg-amber-100 text-amber-800' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {item.severity}
                    </span>
                  </td>
                  <td className="py-3.5 text-right">
                    <button className="px-2.5 py-1 text-xs font-bold text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
                      Assign Remedial Problem Set
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
