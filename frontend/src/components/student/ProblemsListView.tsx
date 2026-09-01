import React, { useState } from 'react';
import {
  Code2,
  Search,
  Filter,
  ArrowRight,
  Sparkles,
  GraduationCap,
  Calendar,
  Layers
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';

export const ProblemsListView: React.FC = () => {
  const { problems, openProblemWorkspace } = useApp();
  const [search, setSearch] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [modeFilter, setModeFilter] = useState<'all' | 'assigned' | 'self'>('all');

  const allTags = Array.from(new Set(problems.flatMap((p) => p.tags)));

  const filtered = problems.filter((p) => {
    const matchSearch = p.title.toLowerCase().includes(search.toLowerCase()) || p.tags.some(t => t.toLowerCase().includes(search.toLowerCase()));
    const matchDiff = difficultyFilter === 'all' || p.difficulty.toLowerCase() === difficultyFilter.toLowerCase();
    const matchTag = selectedTag === 'all' || p.tags.includes(selectedTag);
    const matchMode =
      modeFilter === 'all'
        ? true
        : modeFilter === 'assigned'
        ? p.origin === 'instructor_assigned'
        : p.origin !== 'instructor_assigned';
    return matchSearch && matchDiff && matchTag && matchMode;
  });

  const assignedCount = problems.filter(p => p.origin === 'instructor_assigned').length;
  const selfCount = problems.filter(p => p.origin !== 'instructor_assigned').length;

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Coding Problem Bank
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Solve instructor-assigned coursework or practice self-paced challenges in the sandbox.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
            Total Problems: <strong className="text-slate-900 font-mono">{problems.length}</strong>
          </span>
        </div>
      </div>

      {/* Mode Switcher Tabs (Assigned vs Self-Practice) */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 bg-slate-100/80 rounded-2xl border border-slate-200/80 w-fit">
        <button
          onClick={() => setModeFilter('all')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            modeFilter === 'all'
              ? 'bg-white text-indigo-600 shadow-sm border border-slate-200'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          All Challenges ({problems.length})
        </button>

        <button
          onClick={() => setModeFilter('assigned')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
            modeFilter === 'assigned'
              ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <GraduationCap className="w-3.5 h-3.5" />
          <span>Instructor Assigned ({assignedCount})</span>
        </button>

        <button
          onClick={() => setModeFilter('self')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
            modeFilter === 'self'
              ? 'bg-purple-600 text-white shadow-sm shadow-purple-600/30'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Self-Paced Practice ({selfCount})</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search problems, algorithms, topics..."
            className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500">Difficulty:</span>
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Difficulties</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500">Topic:</span>
            <select
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Topics</option>
              {allTags.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Problems Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((prob) => {
          const isAssigned = prob.origin === 'instructor_assigned';

          return (
            <div
              key={prob.id}
              className={`bg-white rounded-3xl border shadow-xs p-5 hover:shadow-md transition-all flex flex-col justify-between group ${
                isAssigned ? 'border-indigo-200 hover:border-indigo-500' : 'border-slate-200/80 hover:border-purple-400'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <DifficultyBadge difficulty={prob.difficulty} />
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      isAssigned ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {isAssigned ? 'Instructor Assigned' : 'Self-Paced'}
                    </span>
                  </div>

                  <span className="text-[11px] font-mono text-slate-400">
                    Acc: {prob.acceptanceRate}
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  {prob.title}
                </h3>

                <p className="text-xs text-slate-500 line-clamp-2 mt-1.5 leading-relaxed">
                  {prob.description.replace(/[`*]/g, '')}
                </p>

                <div className="flex flex-wrap gap-1.5 mt-3">
                  {prob.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-medium"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {isAssigned && prob.dueDate && (
                  <div className="mt-3 flex items-center gap-1.5 text-[11px] font-mono text-amber-700 bg-amber-50 px-2 py-1 rounded-lg border border-amber-200/60">
                    <Calendar className="w-3 h-3 text-amber-600" />
                    <span>Due: {prob.dueDate}</span>
                  </div>
                )}
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">
                  Opt: {prob.optimalComplexity.time}
                </span>
                <button
                  onClick={() => openProblemWorkspace(prob.id)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                    isAssigned
                      ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs'
                      : 'bg-slate-900 hover:bg-purple-600 text-white shadow-xs'
                  }`}
                >
                  <span>{isAssigned ? 'Solve Assigned' : 'Practice Sandbox'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
