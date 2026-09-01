import React, { useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Award,
  AlertTriangle,
  Calendar,
  Layers,
  ShieldAlert,
  Code2,
  Sparkles,
  CheckCircle,
  FileSpreadsheet,
  Users
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreDistributionBarChart } from '../common/ChartComponents';

export const ClassAnalyticsView: React.FC = () => {
  const { instructorStats, similarityAlerts } = useApp();
  const [activeTab, setActiveTab] = useState<'analytics' | 'similarity'>('analytics');
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  const activeAlert = similarityAlerts[0];

  const topicWeaknessStats = [
    { topic: 'Dynamic Programming', failRate: '42.5%', studentsCount: 19, severity: 'High' },
    { topic: 'Graphs (BFS/DFS)', failRate: '36.8%', studentsCount: 16, severity: 'High' },
    { topic: 'Trees & Recursion', failRate: '28.1%', studentsCount: 12, severity: 'Medium' },
    { topic: 'Linked Lists', failRate: '18.4%', studentsCount: 8, severity: 'Low' },
    { topic: 'Arrays & Two Pointers', failRate: '8.2%', studentsCount: 4, severity: 'Low' }
  ];

  const handleAction = (action: string) => {
    setActionStatus(action);
    setTimeout(() => setActionStatus(null), 3000);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Class Analytics & Integrity Shield
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Cohort grade metrics, score distributions, and AI plagiarism alerts for CSE-301 Section A.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-100 rounded-2xl border border-slate-200/80 self-start md:self-auto">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'analytics'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Class Performance</span>
          </button>

          <button
            onClick={() => setActiveTab('similarity')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'similarity'
                ? 'bg-rose-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Similarity Alerts ({similarityAlerts.length})</span>
          </button>
        </div>
      </div>

      {/* TAB 1: CLASS PERFORMANCE ANALYTICS */}
      {activeTab === 'analytics' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top 3 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Class Average Score
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900 font-mono">
                  {instructorStats.averageScore}%
                </span>
                <span className="text-xs text-emerald-600 font-bold">+2.4% vs last week</span>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">
                Top Score
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-emerald-700 font-mono">
                  {instructorStats.highestScore}%
                </span>
                <span className="text-xs text-slate-500">(Ananya Sharma)</span>
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
                <span className="text-xs text-rose-600 font-semibold">Needs Support</span>
              </div>
            </div>
          </div>

          {/* Score Distribution Bar Chart */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">Score Distribution Histogram (0 - 100)</h3>
              </div>
              <span className="text-xs font-mono text-slate-400">48 Enrolled Students</span>
            </div>

            <div className="pt-4">
              <ScoreDistributionBarChart distribution={instructorStats.scoreDistribution} />
            </div>
          </div>

          {/* Weak Topics Table */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <h3 className="text-base font-bold text-slate-900">Class-Wide Algorithmic Concept Gaps</h3>
              </div>
              <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-1 rounded-lg">AI Diagnosed</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 font-semibold text-[11px] uppercase">
                    <th className="pb-3">Concept Area</th>
                    <th className="pb-3">Failure Rate</th>
                    <th className="pb-3">Impacted Students</th>
                    <th className="pb-3">Severity</th>
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
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PLAGIARISM & SIMILARITY SHIELD */}
      {activeTab === 'similarity' && activeAlert && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top Banner */}
          <div className="bg-rose-50 border border-rose-200 rounded-3xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-rose-600 text-white rounded-2xl">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-extrabold text-rose-900">
                    High Similarity Alert ({activeAlert.similarityPercentage}%)
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-rose-200 text-rose-900 rounded">
                    Risk: {activeAlert.riskLevel}
                  </span>
                </div>
                <p className="text-xs text-rose-800">
                  Question: <strong>{activeAlert.problemTitle}</strong> • Flagged on {activeAlert.timestamp}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleAction('Flag Dismissed as false positive')}
                className="px-3.5 py-2 bg-white hover:bg-slate-100 text-slate-700 rounded-xl text-xs font-bold border border-slate-200 transition-colors cursor-pointer"
              >
                Dismiss Flag
              </button>
              <button
                onClick={() => handleAction('Review Scheduled with students')}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold shadow-xs transition-all cursor-pointer"
              >
                Request Review
              </button>
            </div>
          </div>

          {actionStatus && (
            <div className="p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-semibold animate-fadeIn">
              ✅ {actionStatus}
            </div>
          )}

          {/* Pairwise AST Code Viewer */}
          <div className="bg-slate-900 rounded-3xl border border-slate-800 overflow-hidden shadow-xl">
            <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-xs">
                <Code2 className="w-4 h-4 text-indigo-400" />
                <span>Pairwise AST Token Comparison</span>
              </div>
              <span className="text-xs font-mono text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded border border-rose-500/20">
                {activeAlert.matchedLinesCount} Token-Matched Blocks
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-800 font-mono text-xs">
              <div className="p-5 bg-slate-900/60">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                  <span className="text-sm font-bold text-white block">{activeAlert.studentA.name} ({activeAlert.studentA.rollNumber})</span>
                  <span className="text-xs px-2 py-0.5 bg-indigo-500/10 text-indigo-300 rounded">Student A</span>
                </div>
                <pre className="text-slate-300 leading-relaxed overflow-x-auto whitespace-pre">
                  {activeAlert.studentACodeSnippet}
                </pre>
              </div>

              <div className="p-5 bg-slate-950/60">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                  <span className="text-sm font-bold text-white block">{activeAlert.studentB.name} ({activeAlert.studentB.rollNumber})</span>
                  <span className="text-xs px-2 py-0.5 bg-rose-500/10 text-rose-300 rounded">Student B</span>
                </div>
                <pre className="text-slate-300 leading-relaxed overflow-x-auto whitespace-pre">
                  {activeAlert.studentBCodeSnippet}
                </pre>
              </div>
            </div>

            <div className="p-4 bg-slate-950 border-t border-slate-800 text-xs text-slate-300 space-y-1">
              <span className="text-purple-400 font-bold flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" /> AI Plagiarism Audit Notes:
              </span>
              <p className="text-slate-400 font-sans leading-relaxed">
                {activeAlert.aiAuditNotes}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
