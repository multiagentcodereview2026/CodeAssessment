import React, { useState } from 'react';
import {
  BarChart3,
  AlertTriangle,
  Target,
  Send
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreDistributionBarChart } from '../common/ChartComponents';
import { COHORT_WEAKNESS_STATS, BACKEND_FIELD_GUIDE } from '../../data/learningInsights';

export const ClassAnalyticsView: React.FC = () => {
  const { instructorStats, studentRoster } = useApp();
  const [selectedRange, setSelectedRange] = useState('This Month');

  const topicWeaknessStats = COHORT_WEAKNESS_STATS;
  const atRiskStudents = studentRoster.filter((student) => student.status !== 'On Track');
  const highestRiskTopic = topicWeaknessStats[0];

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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-rose-200/80 p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-extrabold uppercase text-rose-700">Remediation Queue</span>
            <h2 className="mt-1 text-lg font-extrabold text-slate-900">{highestRiskTopic.topic}</h2>
            <p className="mt-1 text-xs text-slate-500 leading-relaxed">
              {highestRiskTopic.studentsCount} students impacted. {highestRiskTopic.reason}
            </p>
          </div>
          <button className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold flex items-center justify-center gap-2 cursor-pointer">
            <Send className="w-3.5 h-3.5" />
            <span>{highestRiskTopic.action}</span>
          </button>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
          <span className="text-xs font-extrabold uppercase text-slate-500">At-Risk Watchlist</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-700 font-mono">{atRiskStudents.length}</span>
            <span className="text-xs text-slate-500">students need attention</span>
          </div>
          <p className="mt-2 text-[11px] text-slate-500 leading-relaxed">
            Filter the roster by status to inspect individual weak topics and contact students.
          </p>
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
                      {item.action}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-slate-900">Backend Integration Map</h3>
          </div>
          <span className="text-xs text-slate-400 font-medium">Frontend contract</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {BACKEND_FIELD_GUIDE.map((item) => (
            <div key={item.feature} className="rounded-2xl bg-slate-50 border border-slate-200/80 p-4">
              <span className="text-xs font-extrabold text-slate-900">{item.feature}</span>
              <p className="mt-1 text-[11px] font-mono text-indigo-700">{item.endpoint}</p>
              <p className="mt-1 text-[11px] text-slate-500 leading-relaxed">{item.payload}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
