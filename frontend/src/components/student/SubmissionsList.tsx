import React, { useState } from 'react';
import {
  Search,
  Filter,
  ArrowRight,
  Sparkles,
  Calendar,
  FileCode,
  GraduationCap,
  Code2
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/Badge';

export const SubmissionsList: React.FC = () => {
  const { submissions, openAssessmentResult, openProblemWorkspace } = useApp();
  // Strictly 2 independent modes: 'assigned' (Instructor) vs 'self' (Practice). NO 'all' tab.
  const [activeMode, setActiveMode] = useState<'assigned' | 'self'>('assigned');
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const assignedSubmissions = submissions.filter(s => s.origin === 'instructor_assigned');
  const practiceSubmissions = submissions.filter(s => s.origin !== 'instructor_assigned');

  const currentDataset = activeMode === 'assigned' ? assignedSubmissions : practiceSubmissions;

  const filtered = currentDataset.filter((sub) => {
    const matchesSearch = sub.problemTitle.toLowerCase().includes(search.toLowerCase()) || sub.language.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = filterStatus === 'all' || sub.status.toLowerCase() === filterStatus.toLowerCase();
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Header & Independent Mode Switcher */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {activeMode === 'assigned' ? 'Coursework Submissions History' : 'Practice Sandbox Submissions'}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {activeMode === 'assigned'
              ? 'Evaluated submissions for mandatory assignments in CSE-301 Section A.'
              : 'Evaluated submissions for independent self-paced algorithmic practice.'}
          </p>
        </div>

        {/* 2 Independent Tabs (NO "All" tab) */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-100 rounded-2xl border border-slate-200/80 self-start md:self-auto">
          <button
            onClick={() => setActiveMode('assigned')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeMode === 'assigned'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GraduationCap className="w-4 h-4" />
            <span>Coursework Records ({assignedSubmissions.length})</span>
          </button>

          <button
            onClick={() => setActiveMode('self')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeMode === 'self'
                ? 'bg-purple-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Code2 className="w-4 h-4" />
            <span>Practice Records ({practiceSubmissions.length})</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search ${activeMode === 'assigned' ? 'coursework' : 'practice'} submissions...`}
            className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors font-mono placeholder:font-sans"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-600">Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium text-slate-700 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="passed">Passed</option>
            <option value="partial">Partial</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Submissions Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3.5 px-6">Problem</th>
                <th className="py-3.5 px-6">Score</th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6">Language</th>
                <th className="py-3.5 px-6">Test Cases</th>
                <th className="py-3.5 px-6">Date</th>
                <th className="py-3.5 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans">
              {filtered.length > 0 ? (
                filtered.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-50/80 transition-colors group">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <FileCode className={`w-4 h-4 flex-shrink-0 ${activeMode === 'assigned' ? 'text-indigo-500' : 'text-purple-500'}`} />
                        <div>
                          <span className="font-bold text-slate-900 block group-hover:text-indigo-600 transition-colors">
                            {sub.problemTitle}
                          </span>
                          <span className="text-[11px] text-slate-400 font-mono">
                            ID: {sub.id}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      <div className="flex items-baseline gap-1 font-mono">
                        <span className={`font-extrabold text-sm ${
                          sub.score >= 80 ? 'text-emerald-600' : sub.score >= 60 ? 'text-indigo-600' : 'text-rose-600'
                        }`}>
                          {sub.score}
                        </span>
                        <span className="text-slate-400 text-[10px]">/100</span>
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      <StatusBadge status={sub.status} />
                    </td>

                    <td className="py-4 px-6 font-mono font-medium text-slate-700">
                      {sub.language}
                    </td>

                    <td className="py-4 px-6 font-mono text-slate-600">
                      {sub.passedTestCases} / {sub.totalTestCases} Passed
                    </td>

                    <td className="py-4 px-6 text-slate-500 font-mono text-[11px] flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      {sub.date}
                    </td>

                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openProblemWorkspace(sub.problemId)}
                          className="px-2.5 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                        >
                          Code
                        </button>
                        <button
                          onClick={() => openAssessmentResult(sub.id)}
                          className={`px-3 py-1.5 rounded-lg font-bold flex items-center gap-1 transition-colors cursor-pointer ${
                            activeMode === 'assigned'
                              ? 'bg-indigo-50 hover:bg-indigo-100 text-indigo-700'
                              : 'bg-purple-50 hover:bg-purple-100 text-purple-700'
                          }`}
                        >
                          <Sparkles className="w-3 h-3" />
                          <span>AI Report</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    No submissions found matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
