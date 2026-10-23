import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  ArrowRight,
  Sparkles,
  Calendar,
  FileCode,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/Badge';

export const SubmissionsList: React.FC = () => {
  const navigate = useNavigate();
  const { submissions, openAssessmentResult, openProblemWorkspace } = useApp();
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterSource, setFilterSource] = useState<string>('all');

  const filtered = submissions.filter((sub) => {
    const matchesSearch = sub.problemTitle.toLowerCase().includes(search.toLowerCase()) || sub.language.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = filterStatus === 'all' || sub.status.toLowerCase() === filterStatus.toLowerCase();
    const matchesSource = filterSource === 'all' || sub.source === filterSource;
    return matchesSearch && matchesStatus && matchesSource;
  });

  const handleOpenReport = (subId: string) => {
    openAssessmentResult(subId);
    navigate(`/submissions/${subId}`);
  };

  const handleOpenCode = (problemId: string) => {
    openProblemWorkspace(problemId);
    navigate(`/problems/${problemId}`);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Submission History
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Track all submitted code, sandbox test passes, and multi-agent AI reports.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600 bg-white px-3.5 py-2.5 rounded-2xl border border-slate-200 shadow-xs">
            Total Submissions: <strong className="text-indigo-600 font-mono text-sm ml-1">{submissions.length}</strong>
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by problem or language..."
            className="w-full pl-10 pr-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors font-mono placeholder:font-sans"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-600">Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium text-slate-700 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="passed">Passed</option>
            <option value="partial">Partial</option>
            <option value="failed">Failed</option>
          </select>
          <span className="ml-2 text-xs font-semibold text-slate-600">Source:</span>
          <select value={filterSource} onChange={(e) => setFilterSource(e.target.value)} className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium text-slate-700 focus:outline-none focus:border-indigo-500 cursor-pointer">
            <option value="all">All Sources</option>
            <option value="Independent Practice">Independent Practice</option>
            <option value="Instructor Assigned">Instructor Assigned</option>
          </select>
        </div>
      </div>

      {/* Submissions Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50/70 dark:bg-slate-800/60 border-b border-slate-200/80 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-4 px-6">Problem</th>
                <th className="py-4 px-6">Score</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6">Source</th>
                <th className="py-4 px-6">Language</th>
                <th className="py-4 px-6">Test Cases</th>
                <th className="py-4 px-6">Date</th>
                <th className="py-4 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
              {filtered.length > 0 ? (
                filtered.map((sub) => (
                  <tr key={sub.id} className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/40 group">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2.5">
                        <FileCode className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                        <div>
                          <button type="button" onClick={() => handleOpenReport(sub.id)} className="block text-left font-semibold text-slate-900 transition-colors hover:text-indigo-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500">
                            {sub.problemTitle}
                          </button>
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
                    <td className="py-4 px-6"><span className={`rounded-lg px-2 py-1 text-[10px] font-bold ${sub.source === 'Instructor Assigned' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-100 text-slate-600'}`}>{sub.source}</span></td>

                    <td className="py-4 px-6 font-mono font-medium text-slate-700">
                      {sub.language}
                    </td>

                    <td className="py-4 px-6 font-mono text-slate-600">
                      {sub.passedTestCases} / {sub.totalTestCases} Passed
                    </td>

                    <td className="py-4 px-6 text-slate-500 font-mono text-[11px]">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{sub.date}</span>
                      </div>
                    </td>

                    <td className="py-4 px-6 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenCode(sub.problemId)}
                          className="px-3 py-1.5 text-xs font-bold text-slate-700 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl border border-slate-200/80 transition-colors cursor-pointer"
                        >
                          Code
                        </button>
                        <button
                          onClick={() => handleOpenReport(sub.id)}
                          className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold flex items-center gap-1.5 transition-all shadow-md shadow-indigo-600/20 text-xs hover:scale-105 active:scale-95 cursor-pointer"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>AI Report</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-slate-400">
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
