import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  Sparkles,
  Calendar,
  FileCode,
  X,
  RotateCcw
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/Badge';
import { FilterDropdown, FilterDropdownOption } from '../ui/filter-dropdown';

export const SubmissionsList: React.FC = () => {
  const navigate = useNavigate();
  const { submissions, openAssessmentResult, openProblemWorkspace } = useApp();
  const [search, setSearch] = useState('');
  const [filterStatuses, setFilterStatuses] = useState<string[]>([]);
  const [filterSources, setFilterSources] = useState<string[]>([]);

  const statusOptions: FilterDropdownOption[] = useMemo(
    () => [
      {
        value: 'all',
        label: 'All Statuses',
        count: submissions.length,
      },
      {
        value: 'passed',
        label: 'Passed',
        count: submissions.filter((s) => s.status?.toLowerCase() === 'passed').length,
      },
      {
        value: 'partial',
        label: 'Partial',
        count: submissions.filter((s) => s.status?.toLowerCase() === 'partial').length,
      },
      {
        value: 'failed',
        label: 'Failed',
        count: submissions.filter((s) => s.status?.toLowerCase() === 'failed').length,
      },
    ],
    [submissions]
  );

  const sourceOptions: FilterDropdownOption[] = useMemo(
    () => [
      {
        value: 'all',
        label: 'All Sources',
        count: submissions.length,
      },
      {
        value: 'Independent Practice',
        label: 'Independent Practice',
        count: submissions.filter((s) => s.source === 'Independent Practice').length,
      },
      {
        value: 'Instructor Assigned',
        label: 'Instructor Assigned',
        count: submissions.filter((s) => s.source === 'Instructor Assigned').length,
      },
    ],
    [submissions]
  );

  const isFiltered = search.trim() !== '' || filterStatuses.length > 0 || filterSources.length > 0;

  const handleClearAll = () => {
    setSearch('');
    setFilterStatuses([]);
    setFilterSources([]);
  };

  const filtered = submissions.filter((sub) => {
    const matchesSearch =
      sub.problemTitle?.toLowerCase().includes(search.toLowerCase()) ||
      sub.language?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus =
      filterStatuses.length === 0 || filterStatuses.includes(sub.status?.toLowerCase());
    const matchesSource =
      filterSources.length === 0 || filterSources.includes(sub.source);
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
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Submission History
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Track all submitted code, sandbox test passes, and multi-agent AI reports.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 px-3.5 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs">
            Total Submissions: <strong className="text-indigo-600 dark:text-indigo-400 font-mono text-sm ml-1">{submissions.length}</strong>
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 sm:p-4 shadow-xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <div className="flex flex-1 flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by problem or language..."
              className="w-full pl-10 pr-9 py-2 text-xs bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-xl focus:outline-none focus:border-indigo-500 focus:bg-white dark:focus:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-colors font-mono placeholder:font-sans"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
                aria-label="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Designated Dropdown Box for Status */}
          <FilterDropdown
            label="Status"
            placeholder="All Statuses"
            options={statusOptions}
            value={filterStatuses}
            onChange={(val) => setFilterStatuses(val)}
            variant="indigo"
          />

          {/* Designated Dropdown Box for Source */}
          <FilterDropdown
            label="Source"
            placeholder="All Sources"
            options={sourceOptions}
            value={filterSources}
            onChange={(val) => setFilterSources(val)}
            variant="indigo"
          />
        </div>

        <div className="text-xs text-slate-500 dark:text-slate-400 font-medium shrink-0 self-end md:self-auto">
          Showing <strong className="text-slate-800 dark:text-slate-200">{filtered.length}</strong> of{' '}
          <strong className="text-slate-800 dark:text-slate-200">{submissions.length}</strong>
        </div>
      </div>

      {/* Submissions Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
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
                          <button type="button" onClick={() => handleOpenReport(sub.id)} className="block text-left font-semibold text-slate-900 dark:text-slate-100 transition-colors hover:text-indigo-600 dark:hover:text-indigo-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 cursor-pointer">
                            {sub.problemTitle}
                          </button>
                          <span className="text-[11px] text-slate-400 dark:text-slate-500 font-mono">
                            ID: {sub.id}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      <div className="flex items-baseline gap-1 font-mono">
                        <span className={`font-extrabold text-sm ${
                          sub.score == null ? 'text-slate-500' : sub.score >= 80 ? 'text-emerald-600 dark:text-emerald-400' : sub.score >= 60 ? 'text-indigo-600 dark:text-indigo-400' : 'text-rose-600 dark:text-rose-400'
                        }`}>
                          {sub.score ?? 'Pending'}
                        </span>
                        <span className="text-slate-400 dark:text-slate-500 text-[10px]">/100</span>
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      <StatusBadge status={sub.status} />
                    </td>
                    <td className="py-4 px-6"><span className={`rounded-lg px-2 py-1 text-[10px] font-bold ${sub.source === 'Instructor Assigned' ? 'bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'}`}>{sub.source}</span></td>

                    <td className="py-4 px-6 font-mono font-medium text-slate-700 dark:text-slate-300">
                      {sub.language}
                    </td>

                    <td className="py-4 px-6 font-mono text-slate-600 dark:text-slate-400">
                      {sub.passedTestCases} / {sub.totalTestCases} Passed
                    </td>

                    <td className="py-4 px-6 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{sub.date}</span>
                      </div>
                    </td>

                    <td className="py-4 px-6 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenCode(sub.problemId)}
                          className="px-3 py-1.5 text-xs font-bold text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-slate-800 rounded-xl border border-slate-200/80 dark:border-slate-700 transition-colors cursor-pointer"
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
                  <td colSpan={8} className="text-center py-12 text-slate-400 dark:text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Filter className="w-8 h-8 text-slate-300 dark:text-slate-600" />
                      <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
                        No submissions found matching criteria.
                      </p>
                      {isFiltered && (
                        <button
                          type="button"
                          onClick={handleClearAll}
                          className="mt-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-semibold underline underline-offset-4 cursor-pointer"
                        >
                          Reset all filters
                        </button>
                      )}
                    </div>
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
