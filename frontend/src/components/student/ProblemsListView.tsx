import React, { useState } from 'react';
import {
  Code2,
  Search,
  ArrowRight,
  GraduationCap,
  Calendar
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';

export const ProblemsListView: React.FC = () => {
  const { problems, openProblemWorkspace, goBackToDashboard } = useApp();
  // Strictly only 2 independent modes: 'assigned' (Instructor) or 'self' (Practice). NO 'all' tab.
  const [activeMode, setActiveMode] = useState<'assigned' | 'self'>('assigned');
  const [search, setSearch] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');

  const assignedProblems = problems.filter(p => p.origin === 'instructor_assigned');
  const selfPracticeProblems = problems.filter(p => p.origin !== 'instructor_assigned');

  const currentDataset = activeMode === 'assigned' ? assignedProblems : selfPracticeProblems;
  const allTags = Array.from(new Set(currentDataset.flatMap((p) => p.tags)));

  const filtered = currentDataset.filter((p) => {
    const matchSearch = p.title.toLowerCase().includes(search.toLowerCase()) || p.tags.some(t => t.toLowerCase().includes(search.toLowerCase()));
    const matchDiff = difficultyFilter === 'all' || p.difficulty.toLowerCase() === difficultyFilter.toLowerCase();
    const matchTag = selectedTag === 'all' || p.tags.includes(selectedTag);
    return matchSearch && matchDiff && matchTag;
  });

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Breadcrumb Navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={goBackToDashboard}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-indigo-600 transition-colors p-2 hover:bg-slate-100 rounded-xl cursor-pointer"
        >
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>Back to Dashboard</span>
        </button>
      </div>

      {/* Header & Independent Mode Selector */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {activeMode === 'assigned' ? 'Instructor Coursework Questions' : 'Self-Paced Practice Catalog'}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {activeMode === 'assigned'
              ? 'Mandatory questions assigned by Prof. Sarah Miller for CSE-301 Section A.'
              : 'Independent algorithmic challenges in the sandbox without instructor deadlines.'}
          </p>
        </div>

        {/* 2 Purely Independent Mode Switcher Tabs (NO "All" tab) */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-100 rounded-2xl border border-slate-200/80 self-start md:self-auto">
          <button
            onClick={() => {
              setActiveMode('assigned');
              setSelectedTag('all');
            }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeMode === 'assigned'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GraduationCap className="w-4 h-4" />
            <span>Instructor Coursework ({assignedProblems.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveMode('self');
              setSelectedTag('all');
            }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeMode === 'self'
                ? 'bg-purple-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Code2 className="w-4 h-4" />
            <span>Self-Paced Practice ({selfPracticeProblems.length})</span>
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
            placeholder={`Search ${activeMode === 'assigned' ? 'coursework' : 'practice'} problems...`}
            className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-slate-200/80 rounded-xl focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500">Difficulty:</span>
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-indigo-500"
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
              className="text-xs bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-indigo-500"
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
          const isDone = prob.studentStatus === 'Submitted';

          return (
            <div
              key={prob.id}
              className={`bg-white rounded-3xl border p-5 transition-all flex flex-col justify-between group ${
                isAssigned
                  ? 'border-indigo-200/80 hover:border-indigo-500 hover:shadow-md'
                  : 'border-slate-200/80 hover:border-purple-400 hover:shadow-md'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <DifficultyBadge difficulty={prob.difficulty} />
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      isAssigned
                        ? isDone
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                        : 'bg-purple-50 text-purple-700 border border-purple-200'
                    }`}>
                      {isAssigned ? (isDone ? '✓ Submitted' : 'Coursework') : 'Self-Practice'}
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
                      className="text-[10px] bg-slate-50 text-slate-600 px-2 py-0.5 rounded-md font-medium border border-slate-100"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {isAssigned && prob.dueDate && (
                  <div className="mt-3 flex items-center gap-1.5 text-[11px] font-mono text-indigo-700 bg-indigo-50/60 px-2.5 py-1 rounded-lg border border-indigo-100">
                    <Calendar className="w-3 h-3 text-indigo-600" />
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
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                    isAssigned
                      ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs'
                      : 'bg-purple-600 hover:bg-purple-700 text-white shadow-xs'
                  }`}
                >
                  <span>{isDone ? 'Review in IDE' : 'Solve in IDE'}</span>
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
