import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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
  X,
  Plus,
  BarChart3,
  Edit3,
  Trash2,
  AlertTriangle,
  Award,
  ShieldAlert,
  FileCheck2,
  Check,
  Eye,
  EyeOff
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { MOCK_PROBLEMS } from '../../mock/data';
import { DifficultyBadge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { Problem, Difficulty } from '../../types';

interface TestCaseItem {
  id: string;
  input: string;
  output: string;
  isHidden: boolean;
}

export const ProblemsListView: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isInstructor = location.pathname.startsWith('/instructor');
  const { openProblemWorkspace, submissions, courses } = useApp();

  const [activeTab, setActiveTab] = useState<'instructor' | 'practice'>('instructor');
  const [search, setSearch] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [problems, setProblems] = useState<Problem[]>(MOCK_PROBLEMS);

  // Question Creator / Customizer Modal State
  const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false);
  const [editingProblemId, setEditingProblemId] = useState<string | null>(null);
  const [formTitle, setFormTitle] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formCourseCode, setFormCourseCode] = useState('CS201');
  const [formDueDate, setFormDueDate] = useState('15 May, 2026');
  const [formDifficulty, setFormDifficulty] = useState<Difficulty>('Medium');
  const [formTags, setFormTags] = useState('Arrays, Two Pointers');
  const [formTimeComp, setFormTimeComp] = useState('O(N)');
  const [formSpaceComp, setFormSpaceComp] = useState('O(1)');
  const [formTestCases, setFormTestCases] = useState<TestCaseItem[]>([
    { id: 'tc-1', input: 'nums = [2,7,11,15], target = 9', output: '[0,1]', isHidden: false },
    { id: 'tc-2', input: 'nums = [3,2,4], target = 6', output: '[1,2]', isHidden: false },
    { id: 'tc-3', input: 'nums = [3,3], target = 6', output: '[0,1]', isHidden: true }
  ]);

  // Question Specific Analytics Modal State
  const [selectedProblemForAnalytics, setSelectedProblemForAnalytics] = useState<Problem | null>(null);

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

  // Open Create Question Modal
  const handleOpenCreateModal = () => {
    setEditingProblemId(null);
    setFormTitle('');
    setFormDescription('');
    setFormCourseCode('CS201');
    setFormDueDate('25 May, 2026');
    setFormDifficulty('Medium');
    setFormTags('Arrays, Hash Map');
    setFormTimeComp('O(N)');
    setFormSpaceComp('O(1)');
    setFormTestCases([
      { id: `tc-${Date.now()}-1`, input: 'arr = [1,2,3,4,5], k = 3', output: '[3,4,5,1,2]', isHidden: false },
      { id: `tc-${Date.now()}-2`, input: 'arr = [-1,-100,3,99], k = 2', output: '[3,99,-1,-100]', isHidden: false },
      { id: `tc-${Date.now()}-3`, input: 'arr = [1], k = 0', output: '[1]', isHidden: true }
    ]);
    setIsQuestionModalOpen(true);
  };

  // Open Edit Question Modal
  const handleOpenEditModal = (prob: Problem) => {
    setEditingProblemId(prob.id);
    setFormTitle(prob.title);
    setFormDescription(prob.description);
    setFormCourseCode(prob.courseCode || 'CS201');
    setFormDueDate('15 May, 2026');
    setFormDifficulty(prob.difficulty);
    setFormTags(prob.tags.join(', '));
    setFormTimeComp(prob.optimalComplexity.time);
    setFormSpaceComp(prob.optimalComplexity.space);
    setFormTestCases(
      prob.testCases.map((tc, idx) => ({
        id: `tc-${idx + 1}`,
        input: tc.input,
        output: tc.expectedOutput,
        isHidden: idx >= 2
      }))
    );
    setIsQuestionModalOpen(true);
  };

  // Handle Add Test Case Row
  const handleAddTestCaseRow = () => {
    setFormTestCases([
      ...formTestCases,
      {
        id: `tc-${Date.now()}`,
        input: '',
        output: '',
        isHidden: false
      }
    ]);
  };

  // Handle Remove Test Case Row
  const handleRemoveTestCaseRow = (tcId: string) => {
    if (formTestCases.length <= 1) return;
    setFormTestCases(formTestCases.filter(tc => tc.id !== tcId));
  };

  // Handle Save Question
  const handleSaveQuestion = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim()) return;

    const parsedTags = formTags
      .split(',')
      .map(t => t.trim())
      .filter(Boolean);

    const formattedTestCases = formTestCases.map(tc => ({
      input: tc.input || 'nums = [1, 2, 3]',
      expectedOutput: tc.output || '[0, 1]'
    }));

    if (editingProblemId) {
      // Update existing problem
      setProblems(prev =>
        prev.map(p => {
          if (p.id === editingProblemId) {
            return {
              ...p,
              title: formTitle.trim(),
              description: formDescription.trim(),
              difficulty: formDifficulty,
              courseCode: formCourseCode,
              tags: parsedTags.length > 0 ? parsedTags : ['Algorithms'],
              optimalComplexity: {
                time: formTimeComp.trim() || 'O(N)',
                space: formSpaceComp.trim() || 'O(1)'
              },
              testCases: formattedTestCases
            };
          }
          return p;
        })
      );
    } else {
      // Create new problem
      const newProblem: Problem = {
        id: `prob-${Date.now()}`,
        title: formTitle.trim(),
        slug: formTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
        difficulty: formDifficulty,
        acceptanceRate: '0.0%',
        description: formDescription.trim() || 'Solve this algorithmic challenge with optimal time and space complexity.',
        tags: parsedTags.length > 0 ? parsedTags : ['Algorithms'],
        isInstructorAssigned: true,
        courseCode: formCourseCode,
        optimalComplexity: {
          time: formTimeComp.trim() || 'O(N)',
          space: formSpaceComp.trim() || 'O(1)'
        },
        starterCode: {
          cpp: '// Starter code template\n#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    void solve() {\n        // Your code here\n    }\n};',
          python: '# Starter code template\nclass Solution:\n    def solve(self):\n        pass',
          java: '// Starter code template\nclass Solution {\n    public void solve() {\n        // Your code here\n    }\n}'
        },
        testCases: formattedTestCases
      };

      setProblems([newProblem, ...problems]);
    }

    setIsQuestionModalOpen(false);
  };

  // Delete Problem
  const handleDeleteProblem = (probId: string) => {
    if (window.confirm('Are you sure you want to remove this problem from the problem bank?')) {
      setProblems(problems.filter(p => p.id !== probId));
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {isInstructor ? 'Problem Bank & Assessments' : 'Coding Problem Bank'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {isInstructor
              ? 'Create, customize test cases, configure due dates, and inspect multi-agent question diagnostics.'
              : 'Solve algorithmic problems with real-time sandbox execution and multi-agent AI assessment.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isInstructor && (
            <button
              onClick={handleOpenCreateModal}
              className="px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>+ Add Question</span>
            </button>
          )}

          <span className="text-xs font-semibold text-slate-600 bg-white px-3.5 py-2.5 rounded-2xl border border-slate-200 shadow-xs">
            Total Problems: <strong className="text-indigo-600 font-mono text-sm ml-1">{problems.length}</strong>
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
                        {prob.courseCode || 'CS201'}
                      </span>
                    )}
                  </div>

                  {/* Status & Accuracy Sub-row */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div>
                      {isInstructor ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-xl border border-slate-200/80">
                          <FileCheck2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>45/48 Submissions</span>
                        </span>
                      ) : isSolved ? (
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
                    onClick={() => {
                      if (isInstructor) {
                        setSelectedProblemForAnalytics(prob);
                      } else {
                        handleSolve(prob.id);
                      }
                    }}
                    className="text-base font-bold text-slate-900 group-hover:text-emerald-700 transition-colors cursor-pointer"
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

                {/* Footer Controls */}
                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <span>Opt: {prob.optimalComplexity.time}</span>
                  </div>

                  {isInstructor ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleOpenEditModal(prob)}
                        title="Customize specifics of this question"
                        className="p-2 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-xl transition-colors cursor-pointer"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteProblem(prob.id)}
                        title="Delete Question"
                        className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setSelectedProblemForAnalytics(prob)}
                        className="px-4 py-2 bg-slate-900 hover:bg-emerald-600 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-md hover:scale-105 active:scale-95 cursor-pointer"
                      >
                        <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Analytics</span>
                      </button>
                    </div>
                  ) : (
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
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* QUESTION CREATOR & CUSTOMIZER MODAL */}
      <Modal
        isOpen={isQuestionModalOpen}
        onClose={() => setIsQuestionModalOpen(false)}
        title={editingProblemId ? 'Customize Question & Test Cases' : 'Add New Question to Problem Bank'}
        subtitle="Configure problem statement, sandbox test cases, optimal complexity, and due date"
        maxWidth="2xl"
      >
        <form onSubmit={handleSaveQuestion} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <label className="block font-bold text-slate-700 mb-1">Question Title</label>
              <input
                type="text"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                placeholder="e.g. Longest Palindromic Substring"
                required
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Course Cohort</label>
              <select
                value={formCourseCode}
                onChange={(e) => setFormCourseCode(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium cursor-pointer"
              >
                {courses.map(c => (
                  <option key={c.id} value={c.code}>
                    {c.code}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Due Date</label>
              <input
                type="text"
                value={formDueDate}
                onChange={(e) => setFormDueDate(e.target.value)}
                placeholder="e.g. 20 May, 2026"
                required
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Difficulty</label>
              <select
                value={formDifficulty}
                onChange={(e) => setFormDifficulty(e.target.value as Difficulty)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium cursor-pointer"
              >
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Tags (comma separated)</label>
              <input
                type="text"
                value={formTags}
                onChange={(e) => setFormTags(e.target.value)}
                placeholder="e.g. DP, String, Two Pointers"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
              />
            </div>
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Problem Statement & Complexity Constraints</label>
            <textarea
              value={formDescription}
              onChange={(e) => setFormDescription(e.target.value)}
              rows={3}
              placeholder="Describe the algorithmic problem, input formats, constraints, and edge conditions..."
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-sans leading-relaxed"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Optimal Time Complexity</label>
              <input
                type="text"
                value={formTimeComp}
                onChange={(e) => setFormTimeComp(e.target.value)}
                placeholder="e.g. O(N log N)"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>
            <div>
              <label className="block font-bold text-slate-700 mb-1">Optimal Space Complexity</label>
              <input
                type="text"
                value={formSpaceComp}
                onChange={(e) => setFormSpaceComp(e.target.value)}
                placeholder="e.g. O(N)"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>
          </div>

          {/* Dynamic Test Cases Builder */}
          <div className="space-y-2 pt-2 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <span className="font-extrabold text-slate-900 block">
                Sandbox Test Cases ({formTestCases.length})
              </span>
              <button
                type="button"
                onClick={handleAddTestCaseRow}
                className="px-3 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg font-bold border border-emerald-200 flex items-center gap-1 transition-colors cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Test Case</span>
              </button>
            </div>

            <div className="space-y-2.5 max-h-52 overflow-y-auto custom-scrollbar p-1">
              {formTestCases.map((tc, index) => (
                <div
                  key={tc.id}
                  className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-slate-600">
                      Test Case #{index + 1}
                    </span>
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-1.5 text-[11px] text-slate-600 font-medium cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={tc.isHidden}
                          onChange={(e) => {
                            const updated = [...formTestCases];
                            updated[index].isHidden = e.target.checked;
                            setFormTestCases(updated);
                          }}
                          className="rounded text-emerald-600 focus:ring-emerald-500"
                        />
                        <span>Hidden Test Case</span>
                      </label>
                      {formTestCases.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveTestCaseRow(tc.id)}
                          className="text-slate-400 hover:text-rose-600 p-0.5 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block mb-0.5">Input:</span>
                      <input
                        type="text"
                        value={tc.input}
                        onChange={(e) => {
                          const updated = [...formTestCases];
                          updated[index].input = e.target.value;
                          setFormTestCases(updated);
                        }}
                        placeholder="e.g. nums = [2,7,11,15], target = 9"
                        required
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg font-mono text-xs focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block mb-0.5">Expected Output:</span>
                      <input
                        type="text"
                        value={tc.output}
                        onChange={(e) => {
                          const updated = [...formTestCases];
                          updated[index].output = e.target.value;
                          setFormTestCases(updated);
                        }}
                        placeholder="e.g. [0,1]"
                        required
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg font-mono text-xs focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsQuestionModalOpen(false)}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-95 cursor-pointer"
            >
              {editingProblemId ? 'Save Changes' : 'Publish Question'}
            </button>
          </div>
        </form>
      </Modal>

      {/* QUESTION SPECIFIC ANALYTICS MODAL */}
      {selectedProblemForAnalytics && (
        <Modal
          isOpen={Boolean(selectedProblemForAnalytics)}
          onClose={() => setSelectedProblemForAnalytics(null)}
          title={`Analytics: ${selectedProblemForAnalytics.title}`}
          subtitle={`Detailed algorithmic cohort diagnostics for ${selectedProblemForAnalytics.courseCode || 'CS201'}`}
          maxWidth="2xl"
        >
          <div className="space-y-6 text-xs">
            {/* Top Stat Summary Grid */}
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Submissions</span>
                <span className="text-xl font-extrabold text-slate-900 font-mono mt-0.5 block">
                  45 / 48
                </span>
                <span className="text-[10px] text-emerald-600 font-semibold block">93.8% Turnout</span>
              </div>

              <div className="p-3.5 bg-emerald-50 border border-emerald-200/80 rounded-2xl">
                <span className="text-[10px] uppercase font-bold text-emerald-700 block">Avg Cohort Score</span>
                <span className="text-xl font-extrabold text-emerald-700 font-mono mt-0.5 block">
                  76.4%
                </span>
                <span className="text-[10px] text-emerald-600 font-semibold block">Proficient</span>
              </div>

              <div className="p-3.5 bg-purple-50 border border-purple-200/80 rounded-2xl">
                <span className="text-[10px] uppercase font-bold text-purple-700 block">Test Pass Rate</span>
                <span className="text-xl font-extrabold text-purple-700 font-mono mt-0.5 block">
                  88.9%
                </span>
                <span className="text-[10px] text-purple-600 font-semibold block">Automated</span>
              </div>
            </div>

            {/* 5D Rubric Diagnostic Breakdown */}
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-3">
              <h4 className="font-bold text-slate-900">5-Dimensional AI Rubric Breakdown</h4>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-slate-600 mb-1 font-medium">
                    <span>1. Correctness & Test Cases</span>
                    <span className="font-mono font-bold text-slate-900">21.4 / 25 (85.6%)</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full rounded-full" style={{ width: '85.6%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-600 mb-1 font-medium">
                    <span>2. Time Complexity Optimal Bounds</span>
                    <span className="font-mono font-bold text-slate-900">17.2 / 25 (68.8%)</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div className="bg-amber-500 h-full rounded-full" style={{ width: '68.8%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-600 mb-1 font-medium">
                    <span>3. Space Complexity & Allocation</span>
                    <span className="font-mono font-bold text-slate-900">21.0 / 25 (84.0%)</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div className="bg-blue-500 h-full rounded-full" style={{ width: '84%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-600 mb-1 font-medium">
                    <span>4. Code Quality & Modularity</span>
                    <span className="font-mono font-bold text-slate-900">19.8 / 25 (79.2%)</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div className="bg-purple-500 h-full rounded-full" style={{ width: '79.2%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-600 mb-1 font-medium">
                    <span>5. Similarity & AST Originality</span>
                    <span className="font-mono font-bold text-slate-900">22.5 / 25 (90.0%)</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div className="bg-teal-500 h-full rounded-full" style={{ width: '90%' }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Common Student Mistakes Identified by AI */}
            <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200 space-y-2">
              <div className="flex items-center gap-2 text-amber-900 font-bold">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Common Mistakes & Complexity Bottlenecks Identified</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-amber-800 text-[11px] leading-relaxed">
                <li>32% of students implemented an O(N²) nested loop instead of optimal O(N) single-pass lookup.</li>
                <li>18% failed on hidden large integer edge test cases due to missing boundary checks.</li>
                <li>8% encountered variable naming and code readability deductions.</li>
              </ul>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-slate-100">
              <button
                onClick={() => setSelectedProblemForAnalytics(null)}
                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors cursor-pointer"
              >
                Close
              </button>

              <button
                onClick={() => {
                  setSelectedProblemForAnalytics(null);
                  navigate('/instructor/analytics');
                }}
                className="px-5 py-2.5 bg-slate-900 hover:bg-emerald-600 text-white rounded-xl font-bold transition-all flex items-center gap-2 cursor-pointer shadow-md"
              >
                <span>View Full Class Analytics</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
