import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Code2,
  Search,
  ArrowRight,
  GraduationCap,
  Sparkles,
  BookOpen,
  CheckCircle2,
  Clock,
  Layers,
  Calendar,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { MOCK_PROBLEMS } from '../../mock/data';
import { DifficultyBadge } from '../common/Badge';
import { Problem } from '../../types';

export const ProblemsListView: React.FC = () => {
  const navigate = useNavigate();
  const { openProblemWorkspace, submissions } = useApp();
  const [activeTab, setActiveTab] = useState<'instructor' | 'practice'>('instructor');
  const [search, setSearch] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [problems, setProblems] = useState<Problem[]>(MOCK_PROBLEMS);

  // Sync problems from API if available, falling back to mock problems
  useEffect(() => {
    fetch('/api/problems')
      .then(res => {
        if (res.ok) return res.json();
        return null;
      })
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          const merged = MOCK_PROBLEMS.map(mockP => {
            const apiMatch = data.find((d: any) => d.problem_id === mockP.slug || d.problem_id === mockP.id);
            if (apiMatch) {
              return {
                ...mockP,
                title: apiMatch.title || mockP.title,
                difficulty: apiMatch.difficulty || mockP.difficulty,
                description: apiMatch.description || mockP.description,
                isInstructorAssigned: true,
                courseCode: 'CS201'
              };
            }
            return mockP;
          });
          setProblems(merged);
        }
      })
      .catch(() => {});
  }, []);

  const allTags = Array.from(new Set(problems.flatMap((p) => p.tags)));
  const solvedSlugs = new Set(submissions.map(s => s.problemSlug || s.problemId));

  const instructorCount = problems.filter(p => p.isInstructorAssigned).length;
  const practiceCount = problems.filter(p => !p.isInstructorAssigned).length;

  const filtered = problems.filter((p) => {
    if (activeTab === 'instructor' && !p.isInstructorAssigned) return false;
    if (activeTab === 'practice' && p.isInstructorAssigned) return false;

    const matchSearch = p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.tags.some(t => t.toLowerCase().includes(search.toLowerCase())) ||
      (p.courseCode && p.courseCode.toLowerCase().includes(search.toLowerCase()));

    const matchDiff = difficultyFilter === 'all' || p.difficulty.toLowerCase() === difficultyFilter.toLowerCase();
    const matchTag = selectedTag === 'all' || p.tags.includes(selectedTag);

    return matchSearch && matchDiff && matchTag;
  });

  const hasActiveFilters = search !== '' || difficultyFilter !== 'all' || selectedTag !== 'all';

  const handleClearFilters = () => {
    setSearch('');
    setDifficultyFilter('all');
    setSelectedTag('all');
  };

  const handleSolve = (probId: string) => {
    openProblemWorkspace(probId);
    navigate(`/problems/${probId}`);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Coding Problem Bank
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Solve algorithmic problems with real-time sandbox execution and multi-agent AI assessment.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600 bg-white px-3.5 py-2.5 rounded-2xl border border-slate-200 shadow-xs">
            Available Problems: <strong className="text-indigo-600 font-mono text-sm ml-1">{problems.length}</strong>
          </span>
        </div>
      </div>

      {/* Binary Tabs (Strictly Instructor Assigned or Standard Practice) */}
      <div className="flex bg-slate-200/60 p-1.5 rounded-2xl border border-slate-200/80 max-w-md w-full sm:w-auto">
        <button
          onClick={() => setActiveTab('instructor')}
          className={`flex-1 sm:flex-initial py-2.5 px-5 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
            activeTab === 'instructor'
              ? 'bg-white text-emerald-600 shadow-sm shadow-emerald-100'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <GraduationCap className="w-4 h-4" />
          <span>Instructor Assigned</span>
          <span className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono font-bold ${activeTab === 'instructor' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}>
            {instructorCount}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('practice')}
          className={`flex-1 sm:flex-initial py-2.5 px-5 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
            activeTab === 'practice'
              ? 'bg-white text-indigo-600 shadow-sm shadow-indigo-100'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Standard Practice</span>
          <span className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono font-bold ${activeTab === 'practice' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'}`}>
            {practiceCount}
          </span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-3xl border border-slate-200/80 shadow-xs flex flex-col lg:flex-row items-center justify-between gap-4">
        <div className="relative w-full lg:w-96">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search problems, topics, algorithms..."
            className="w-full pl-10 pr-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
          {activeTab !== 'instructor' && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500">Difficulty:</span>
              <select
                value={difficultyFilter}
                onChange={(e) => setDifficultyFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium text-slate-700 focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value="all">All Difficulties</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          )}

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Topic:</span>
            <select
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium text-slate-700 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="all">All Topics</option>
              {allTags.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </div>

          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 hover:underline px-2 py-1 cursor-pointer"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Problems Grid */}
      {filtered.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
            <Search className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800">No matching problems found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Try adjusting your search keyword or topic filter.
          </p>
          <button
            onClick={handleClearFilters}
            className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition-colors cursor-pointer"
          >
            Clear All Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((prob) => {
            const isSolved = solvedSlugs.has(prob.slug) || solvedSlugs.has(prob.id);

            return (
              <div
                key={prob.id}
                className={`bg-white rounded-3xl border transition-all duration-200 p-6 flex flex-col justify-between group hover:shadow-lg card-hover relative overflow-hidden ${
                  prob.isInstructorAssigned
                    ? 'border-indigo-200/90 shadow-xs ring-1 ring-indigo-500/10'
                    : 'border-slate-200/80 shadow-xs'
                }`}
              >
                {/* Visual indicator for Instructor Assigned questions */}
                <div>
                  {/* Top Badge Row */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    {prob.isInstructorAssigned ? (
                      <span className="inline-flex items-center gap-1.5 text-xs font-extrabold text-amber-900 bg-amber-50 border border-amber-300 px-3 py-1 rounded-xl shadow-xs">
                        <Calendar className="w-3.5 h-3.5 text-amber-600" />
                        <span>Due: 15 May, 2026</span>
                      </span>
                    ) : (
                      <DifficultyBadge difficulty={prob.difficulty} />
                    )}

                    {prob.isInstructorAssigned && (
                      <span className="inline-flex items-center gap-1 bg-emerald-600 text-white text-[10px] font-extrabold px-2.5 py-1 rounded-xl shadow-xs tracking-wider uppercase">
                        <GraduationCap className="w-3 h-3" />
                        {prob.courseCode || 'Assignment'}
                      </span>
                    )}
                  </div>

                  {/* Status & Accuracy Sub-row */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div>
                      {isSolved ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-extrabold text-emerald-800 bg-emerald-100/90 border border-emerald-300 px-2.5 py-1 rounded-xl shadow-xs">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Solved</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200">
                          Unsolved
                        </span>
                      )}
                    </div>

                    <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-xl border border-slate-200/80 shadow-xs">
                      Acc: <strong className="text-indigo-600">{prob.acceptanceRate}</strong>
                    </span>
                  </div>

                  {/* Title */}
                  <h3
                    onClick={() => handleSolve(prob.id)}
                    className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors cursor-pointer"
                  >
                    {prob.title}
                  </h3>

                  {/* Description snippet */}
                  <p className="text-xs text-slate-500 line-clamp-2 mt-2 leading-relaxed">
                    {prob.description.replace(/[`*]/g, '')}
                  </p>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5 mt-3.5">
                    {prob.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] bg-slate-100 text-slate-600 px-2.5 py-1 rounded-lg font-medium border border-slate-200/50"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Footer */}
                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <span>Opt: {prob.optimalComplexity.time}</span>
                  </div>
                  
                  <button
                    onClick={() => handleSolve(prob.id)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer active:scale-95 ${
                      prob.isInstructorAssigned
                        ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-600/20'
                        : 'bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white'
                    }`}
                  >
                    <span>{isSolved ? 'Review / Solve' : 'Code Challenge'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
