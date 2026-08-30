import React, { useState } from 'react';
import {
  Code2,
  Search,
  Filter,
  ArrowRight,
  Sparkles,
  CheckCircle,
  Clock,
  Layers
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { MOCK_PROBLEMS } from '../../mock/data';
import { DifficultyBadge } from '../common/Badge';

export const ProblemsListView: React.FC = () => {
  const { openProblemWorkspace } = useApp();
  const [search, setSearch] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');

  const allTags = Array.from(new Set(MOCK_PROBLEMS.flatMap((p) => p.tags)));

  const filtered = MOCK_PROBLEMS.filter((p) => {
    const matchSearch = p.title.toLowerCase().includes(search.toLowerCase()) || p.tags.some(t => t.toLowerCase().includes(search.toLowerCase()));
    const matchDiff = difficultyFilter === 'all' || p.difficulty.toLowerCase() === difficultyFilter.toLowerCase();
    const matchTag = selectedTag === 'all' || p.tags.includes(selectedTag);
    return matchSearch && matchDiff && matchTag;
  });

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Coding Problem Bank
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Solve algorithmic problems with real-time sandbox execution and multi-agent AI assessment.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
            Available Challenges: <strong className="text-slate-900 font-mono">{MOCK_PROBLEMS.length}</strong>
          </span>
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
            placeholder="Search problems, topics, algorithms..."
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
        {filtered.map((prob) => (
          <div
            key={prob.id}
            className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 hover:border-indigo-300 hover:shadow-md transition-all flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <DifficultyBadge difficulty={prob.difficulty} />
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
            </div>

            <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] font-mono text-slate-400">
                Opt: {prob.optimalComplexity.time}
              </span>
              <button
                onClick={() => openProblemWorkspace(prob.id)}
                className="px-3.5 py-1.5 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 group-hover:shadow-sm"
              >
                <span>Code Challenge</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
