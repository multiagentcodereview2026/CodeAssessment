import React, { useEffect, useState } from 'react';
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
  ShieldAlert,
  FileCheck2,
  Check
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { DoubleConfirmDialog } from '../common/DoubleConfirmDialog';
import { Problem, Difficulty } from '../../types';
import { useAuth } from '../../context/useAuth';

interface TestCaseItem {
  id: string;
  input: string;
  output: string;
  isHidden: boolean;
}

const PRACTICE_CATALOGUE_CACHE_KEY = 'codevedha_practice_catalogue_v2';

const readCachedPracticeCatalogue = (): Problem[] => {
  try {
    const raw = localStorage.getItem(PRACTICE_CATALOGUE_CACHE_KEY);
    const cached = raw ? JSON.parse(raw) : [];
    return Array.isArray(cached) ? cached : [];
  } catch {
    return [];
  }
};

export const ProblemsListView: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isInstructor = location.pathname.startsWith('/instructor');
  const { openProblemWorkspace, submissions, courses, problems } = useApp();
  const { authFetch } = useAuth();

  const [activeTab, setActiveTab] = useState<'instructor' | 'practice'>(() =>
    location.pathname.startsWith('/instructor') || new URLSearchParams(location.search).get('view') === 'instructor' ? 'instructor' : 'practice'
  );
  const [search, setSearch] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [languageFilter, setLanguageFilter] = useState<string>('all');
  const [isSkillsOpen, setIsSkillsOpen] = useState(false);
  const [practiceProblems, setPracticeProblems] = useState<Problem[]>(readCachedPracticeCatalogue);
  const [isPracticeLoading, setIsPracticeLoading] = useState(() => readCachedPracticeCatalogue().length === 0);
  const [practiceLoadError, setPracticeLoadError] = useState('');
  const [practiceReloadKey, setPracticeReloadKey] = useState(0);
  const [instructorProblems, setInstructorProblems] = useState<Problem[]>([]);
  const [isInstructorLoading, setIsInstructorLoading] = useState(true);
  const [instructorLoadError, setInstructorLoadError] = useState('');

  useEffect(() => {
    if (!isInstructor) {
      setActiveTab(new URLSearchParams(location.search).get('view') === 'instructor' ? 'instructor' : 'practice');
    } else {
      setActiveTab('instructor');
    }
  }, [isInstructor, location.search]);

  useEffect(() => {
    if (isInstructor) return;
    let cancelled = false;
    setPracticeLoadError('');

    const loadPracticeProblems = async () => {
      try {
        const response = await fetch('/api/problems', { cache: 'no-store' });
        if (!response.ok) throw new Error(`Problem API returned ${response.status}`);
        const records = await response.json();
        if (cancelled || !Array.isArray(records)) return;
        setInstructorLoadError('');

        const mappedProblems = records.map((problem: any): Problem => ({
          id: problem.id,
          slug: problem.id,
          title: problem.title,
          difficulty: ['Easy', 'Medium', 'Hard'].includes(problem.difficulty) ? problem.difficulty : 'Medium',
          tags: Array.isArray(problem.topic_tags) && problem.topic_tags.length ? problem.topic_tags : [problem.category || 'Algorithms'],
          acceptanceRate: '—',
          description: problem.description || '',
          examples: [],
          constraints: [],
          testCases: [],
          starterCode: problem.starter_codes || {},
          solutionCode: {},
          optimalComplexity: { time: '—', space: '—' }
        }));
        setPracticeProblems(mappedProblems);
        try {
          localStorage.setItem(PRACTICE_CATALOGUE_CACHE_KEY, JSON.stringify(mappedProblems));
        } catch {
          // A full or disabled browser store should not stop the catalogue.
        }
      } catch (error) {
        console.error('Unable to load the DSA practice catalogue:', error);
        if (!cancelled) setPracticeLoadError('The problem bank could not be loaded. Check your connection and try again.');
      } finally {
        if (!cancelled) setIsPracticeLoading(false);
      }
    };

    void loadPracticeProblems();
    return () => { cancelled = true; };
  }, [isInstructor, practiceReloadKey]);

  useEffect(() => {
    let cancelled = false;

    const loadInstructorProblems = async () => {
      try {
        const response = await authFetch('/api/instructor-problems', { cache: 'no-store' });
        if (!response.ok) throw new Error(`Instructor problem API returned ${response.status}`);
        const records = await response.json();
        if (cancelled || !Array.isArray(records)) return;
        setInstructorProblems(records.map((problem: any): Problem => ({
          id: problem.id,
          slug: problem.id,
          title: problem.title,
          difficulty: ['Easy', 'Medium', 'Hard'].includes(problem.difficulty) ? problem.difficulty : 'Medium',
          tags: Array.isArray(problem.topic_tags) && problem.topic_tags.length ? problem.topic_tags : [problem.category || 'Algorithms'],
          acceptanceRate: '—',
          description: problem.description || '',
          examples: problem.examples || [],
          constraints: problem.constraints || [],
          testCases: (problem.test_cases || []).map((testCase: any, index: number) => ({
            id: String(testCase.id || `${problem.id}-public-${index + 1}`),
            input: String(testCase.input || ''),
            expectedOutput: String(testCase.expected_output || ''),
            isHidden: Boolean(testCase.is_hidden)
          })),
          starterCode: problem.starter_codes || {},
          solutionCode: {},
          optimalComplexity: { time: problem.target_time_complexity || '—', space: problem.target_space_complexity || '—' },
          isInstructorAssigned: true,
          assignmentId: Number(problem.assignment_id),
          courseCode: problem.course_code || '',
          dueDate: problem.due_date || ''
        })));
      } catch (error) {
        console.error('Unable to load instructor assignments:', error);
        if (!cancelled) setInstructorLoadError(error instanceof Error ? error.message : 'Unable to load course questions.');
      } finally {
        if (!cancelled) setIsInstructorLoading(false);
      }
    };

    void loadInstructorProblems();
    return () => { cancelled = true; };
  }, [isInstructor, authFetch]);

  // Question Creator / Customizer Modal State
  const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false);
  const [deleteProblemTarget, setDeleteProblemTarget] = useState<Problem | null>(null);
  const [removeCaseTarget, setRemoveCaseTarget] = useState<TestCaseItem | null>(null);
  const [isDeletingProblem, setIsDeletingProblem] = useState(false);
  const [editingProblemId, setEditingProblemId] = useState<string | null>(null);
  const [formTitle, setFormTitle] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formCourseId, setFormCourseId] = useState('');
  const [formDueDate, setFormDueDate] = useState('');
  const [formDifficulty, setFormDifficulty] = useState<Difficulty>('Medium');
  const [formTags, setFormTags] = useState('');
  const [formTimeComp, setFormTimeComp] = useState('');
  const [formSpaceComp, setFormSpaceComp] = useState('');
  const [formTestCases, setFormTestCases] = useState<TestCaseItem[]>([]);
  const [isSavingQuestion, setIsSavingQuestion] = useState(false);
  const [questionError, setQuestionError] = useState('');

  // Question Specific Analytics Modal State
  const [selectedProblemForAnalytics, setSelectedProblemForAnalytics] = useState<Problem | null>(null);

  const allTags = Array.from(new Set((isInstructor ? instructorProblems : problems).flatMap((p) => p.tags)));
  const solvedSlugs = new Set(submissions.filter((submission) => submission.status.toLowerCase() === 'passed').map((submission) => submission.problemSlug || submission.problemId));

  const instructorCount = isInstructor ? instructorProblems.length : problems.filter(p => p.isInstructorAssigned).length;
  const practiceCount = problems.filter(p => !p.isInstructorAssigned).length;

  const filtered = (isInstructor ? instructorProblems : problems).filter((p) => {
    if (activeTab === 'instructor' && !p.isInstructorAssigned) return false;
    if (activeTab === 'practice' && p.isInstructorAssigned) return false;

    const matchSearch = p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.tags.some(t => t.toLowerCase().includes(search.toLowerCase())) ||
      (p.courseCode && p.courseCode.toLowerCase().includes(search.toLowerCase()));

    const matchDiff = difficultyFilter === 'all' || p.difficulty.toLowerCase() === difficultyFilter.toLowerCase();
    const matchTag = selectedTag === 'all' || p.tags.includes(selectedTag);

    return matchSearch && matchDiff && matchTag;
  });

  const hasActiveFilters = search !== '' || difficultyFilter !== 'all' || selectedTag !== 'all' || languageFilter !== 'all';
  const selectedTabCount = activeTab === 'instructor' ? instructorCount : practiceCount;
  const completionCount = filtered.filter(p => solvedSlugs.has(p.slug) || solvedSlugs.has(p.id)).length;
  const focusLabel = activeTab === 'instructor'
    ? 'Questions saved here are linked to the selected course and its students.'
    : 'Use standard practice to reinforce topics the evaluator marks as weak.';

  const handleClearFilters = () => {
    setSearch('');
    setDifficultyFilter('all');
    setSelectedTag('all');
    setLanguageFilter('all');
  };

  const handleSolve = (probId: string) => {
    openProblemWorkspace(probId);
    const problem = instructorProblems.find((item) => item.id === probId);
    const params = new URLSearchParams();
    if (activeTab === 'instructor' && !isInstructor) params.set('view', 'instructor');
    if (problem?.assignmentId) params.set('assignmentId', String(problem.assignmentId));
    navigate(`/problems/${probId}${params.size ? `?${params.toString()}` : ''}`);
  };

  // Open Create Question Modal
  const handleOpenCreateModal = () => {
    setEditingProblemId(null);
    setFormTitle('');
    setFormDescription('');
    setFormCourseId(courses[0]?.id || '');
    setFormDueDate('');
    setFormDifficulty('Medium');
    setFormTags('');
    setFormTimeComp('');
    setFormSpaceComp('');
    setFormTestCases([{ id: `tc-${Date.now()}`, input: '', output: '', isHidden: false }]);
    setQuestionError('');
    setIsQuestionModalOpen(true);
  };

  // Open Edit Question Modal
  const handleOpenEditModal = (prob: Problem) => {
    setEditingProblemId(prob.id);
    setFormTitle(prob.title);
    setFormDescription(prob.description);
    setFormCourseId(courses.find((course) => course.code === prob.courseCode)?.id || courses[0]?.id || '');
    setFormDueDate(prob.dueDate ? new Date(prob.dueDate).toISOString().slice(0, 16) : '');
    setFormDifficulty(prob.difficulty);
    setFormTags(prob.tags.join(', '));
    setFormTimeComp(prob.optimalComplexity.time);
    setFormSpaceComp(prob.optimalComplexity.space);
    setFormTestCases(prob.testCases.map((tc, idx) => ({
      id: `tc-${idx + 1}`, input: tc.input, output: tc.expectedOutput, isHidden: Boolean(tc.isHidden)
    })));
    if (!prob.testCases.length) setFormTestCases([{ id: `tc-${Date.now()}`, input: '', output: '', isHidden: false }]);
    setQuestionError('');
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
    setRemoveCaseTarget(formTestCases.find((testCase) => testCase.id === tcId) || null);
  };

  const confirmRemoveTestCase = () => {
    if (!removeCaseTarget || formTestCases.length <= 1) return;
    setFormTestCases((current) => current.filter((testCase) => testCase.id !== removeCaseTarget.id));
    setRemoveCaseTarget(null);
  };

  // Handle Save Question
  const handleSaveQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    setQuestionError('');
    if (!formTitle.trim() || !formDescription.trim() || !formCourseId || !formTimeComp.trim() || !formSpaceComp.trim()) {
      setQuestionError('Complete the title, statement, course, and complexity targets.');
      return;
    }
    if (!formTestCases.length || formTestCases.some((tc) => !tc.input.trim() || !tc.output.trim()) || !formTestCases.some((tc) => !tc.isHidden)) {
      setQuestionError('Add complete test cases and at least one example for sample runs.');
      return;
    }

    const parsedTags = formTags
      .split(',')
      .map(t => t.trim())
      .filter(Boolean);

    setIsSavingQuestion(true);
    try {
      const body = {
        title: formTitle.trim(), description: formDescription.trim(), difficulty: formDifficulty,
        category: parsedTags[0] || 'Algorithms', topic_tags: parsedTags, target_time_complexity: formTimeComp.trim(),
        target_space_complexity: formSpaceComp.trim(),
        starter_codes: editingProblemId ? instructorProblems.find((problem) => problem.id === editingProblemId)?.starterCode || {} : {},
        test_cases: formTestCases.map((tc) => ({ input: tc.input.trim(), expected_output: tc.output.trim(), is_hidden: tc.isHidden })),
        course_id: Number(formCourseId), due_date: formDueDate ? new Date(formDueDate).toISOString() : null
      };
      const response = await authFetch(editingProblemId
        ? `/api/instructor/problems/${encodeURIComponent(editingProblemId)}`
        : '/api/instructor/problems', {
        method: editingProblemId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Unable to save question.');
      setIsQuestionModalOpen(false);
      window.location.reload();
    } catch (error) {
      setQuestionError(error instanceof Error ? error.message : 'Unable to save question.');
    } finally {
      setIsSavingQuestion(false);
    }
  };

  // Delete Problem
  const handleDeleteProblem = (problem: Problem) => {
    setQuestionError('');
    setDeleteProblemTarget(problem);
  };

  const confirmDeleteProblem = async () => {
    if (!deleteProblemTarget) return;
    setIsDeletingProblem(true);
    try {
      const response = await authFetch(`/api/instructor/problems/${encodeURIComponent(deleteProblemTarget.id)}`, { method: 'DELETE' });
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        throw new Error(typeof result.detail === 'string' ? result.detail : 'Unable to delete this question.');
      }
      window.location.reload();
    } catch (error) {
      setQuestionError(error instanceof Error ? error.message : 'Unable to delete this question.');
      setDeleteProblemTarget(null);
    } finally {
      setIsDeletingProblem(false);
    }
  };

  // Students use a deliberately simple two-section bank.  The instructor's
  // authoring/dashboard page below stays independent from this presentation.
  const studentInstructorProblems = instructorProblems;
  const studentPracticeProblems = practiceProblems;
  const questionOrder = (id: string) => {
    const match = id.match(/(\d+)$/);
    return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER;
  };
  const orderedPracticeProblems = [...studentPracticeProblems]
    .sort((left, right) => questionOrder(left.id) - questionOrder(right.id) || left.title.localeCompare(right.title));
  const normalizedStudentSearch = search.trim().toLowerCase();
  const studentPracticeTopics = Array.from(new Set(orderedPracticeProblems.flatMap((problem) => problem.tags))).sort();
  const studentPracticeLanguages = Array.from(new Set(orderedPracticeProblems.flatMap((problem) => Object.keys(problem.starterCode || {}).map((language) => language.toLowerCase())))).sort();
  const visibleStudentPractice = orderedPracticeProblems.filter((problem, index) => {
    const matchesNumber = /^\d+$/.test(normalizedStudentSearch) && questionOrder(problem.id) === Number(normalizedStudentSearch);
    const matchesText = !normalizedStudentSearch || `${problem.id} ${problem.title} ${problem.tags.join(' ')}`.toLowerCase().includes(normalizedStudentSearch);
    return (matchesNumber || matchesText) &&
      (difficultyFilter === 'all' || problem.difficulty.toLowerCase() === difficultyFilter) &&
      (selectedTag === 'all' || problem.tags.includes(selectedTag)) &&
      (languageFilter === 'all' || Object.keys(problem.starterCode || {}).some((language) => language.toLowerCase() === languageFilter));
  });
  const visibleStudentInstructor = studentInstructorProblems.filter((problem) => {
    const content = `${problem.title} ${problem.courseCode || ''} ${problem.tags.join(' ')}`.toLowerCase();
    return !normalizedStudentSearch || content.includes(normalizedStudentSearch);
  });

  if (!isInstructor) {
    return (
      <div className="space-y-5 pb-12 animate-fadeIn">
        <div className="inline-flex rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
          <button
            onClick={() => { setActiveTab('practice'); navigate('/problems'); }}
            className={`rounded-lg px-4 py-2.5 text-sm font-bold transition-colors ${activeTab === 'practice' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            DSA Practice
          </button>
          <button
            onClick={() => { setActiveTab('instructor'); navigate('/problems?view=instructor'); }}
            className={`rounded-lg px-4 py-2.5 text-sm font-bold transition-colors ${activeTab === 'instructor' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            Instructor Problems
            <span className="ml-2 rounded bg-emerald-100 px-1.5 py-0.5 text-xs text-emerald-700">{studentInstructorProblems.length}</span>
          </button>
        </div>

        {activeTab === 'instructor' ? (
          <section className="space-y-5">
            <header>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-600">Course work</p>
              <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900">Instructor Problems</h1>
              <p className="mt-1 text-sm text-slate-500">Problems assigned by your instructor, kept separate from DSA practice.</p>
            </header>

            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
              {isInstructorLoading ? (
                <div className="p-10 text-center text-sm font-semibold text-slate-500">Loading instructor problems…</div>
              ) : visibleStudentInstructor.length === 0 ? (
                <div className="p-10 text-center text-sm text-slate-500">No instructor problems match this search.</div>
              ) : visibleStudentInstructor.map((problem) => {
                const attempted = solvedSlugs.has(problem.slug) || solvedSlugs.has(problem.id);
                return (
                  <button
                    key={problem.id}
                    onClick={() => handleSolve(problem.id)}
                    className="grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 border-b border-slate-100 px-6 py-5 text-left transition-colors last:border-b-0 hover:bg-emerald-50/60"
                  >
                    <span className={`text-base font-bold ${attempted ? 'text-emerald-600' : 'text-slate-300'}`}>{attempted ? '✓' : '○'}</span>
                    <span className="min-w-0">
                      <span className="block truncate text-base font-bold text-slate-900">{problem.title}</span>
                      <span className="mt-1 block text-sm text-slate-500">{problem.courseCode || 'Course assignment'}{problem.dueDate ? ` · Due ${problem.dueDate}` : ''}</span>
                    </span>
                    <DifficultyBadge difficulty={problem.difficulty} />
                  </button>
                );
              })}
            </div>
          </section>
        ) : (
          <section className="space-y-5">
            <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div><p className="text-xs font-bold uppercase tracking-[0.14em] text-indigo-700">Independent practice</p><h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Find a problem to solve</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Choose a topic and difficulty, then open a problem to write code, run examples, and submit for assessment.</p></div>
              <span className="text-sm text-slate-500">{orderedPracticeProblems.length} {orderedPracticeProblems.length === 1 ? 'problem' : 'problems'} available</span>
            </header>
            <div className="relative">
              <main className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by number, question name, or DSA topic" className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 text-sm outline-none focus:border-indigo-500" />
                  </div>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setIsSkillsOpen((open) => !open)}
                      aria-expanded={isSkillsOpen}
                      className={`inline-flex h-full w-full items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-semibold transition-colors sm:w-auto ${
                        isSkillsOpen || selectedTag !== 'all'
                          ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                          : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-indigo-200 hover:bg-indigo-50'
                      }`}
                    >
                      <Layers className="h-4 w-4" />
                      <span>Skills</span>
                      {selectedTag !== 'all' && <span className="max-w-20 truncate text-xs">{selectedTag}</span>}
                    </button>

                    {isSkillsOpen && (
                      <aside className="absolute right-0 top-full z-30 mt-2 max-h-[520px] w-[min(320px,calc(100vw-3rem))] overflow-y-auto rounded-2xl border border-slate-700 bg-slate-950 p-5 text-slate-100 shadow-xl shadow-slate-950/20">
                        <div className="flex items-center justify-between gap-3">
                          <h2 className="text-sm font-extrabold">Skills</h2>
                          <button
                            type="button"
                            onClick={() => setIsSkillsOpen(false)}
                            aria-label="Close skills"
                            className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                        <button
                          type="button"
                          onClick={() => { setSelectedTag('all'); setIsSkillsOpen(false); }}
                          className={`mt-4 text-left text-xs font-bold ${selectedTag === 'all' ? 'text-white' : 'text-slate-400 hover:text-white'}`}
                        >
                          • All DSA topics <span className="ml-1 text-slate-400">×{orderedPracticeProblems.length}</span>
                        </button>
                        <div className="mt-4 flex flex-wrap gap-1.5">
                          {studentPracticeTopics.map((topic) => (
                            <button
                              type="button"
                              key={topic}
                              onClick={() => { setSelectedTag(topic); setIsSkillsOpen(false); }}
                              className={`rounded-lg px-2 py-1 text-[11px] transition-colors ${selectedTag === topic ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-200 hover:bg-slate-700'}`}
                            >
                              {topic} <span className="text-slate-400">×{orderedPracticeProblems.filter((problem) => problem.tags.includes(topic)).length}</span>
                            </button>
                          ))}
                        </div>
                      </aside>
                    )}
                  </div>
                  <select aria-label="Filter by difficulty" value={difficultyFilter} onChange={(event) => setDifficultyFilter(event.target.value)} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-indigo-500">
                    <option value="all">All difficulties</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                  {studentPracticeLanguages.length > 0 && <select aria-label="Filter by supported language" value={languageFilter} onChange={(event) => setLanguageFilter(event.target.value)} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-indigo-500"><option value="all">All languages</option>{studentPracticeLanguages.map((language) => <option key={language} value={language}>{({ cpp: 'C++', c: 'C', java: 'Java', python: 'Python', javascript: 'JavaScript' } as Record<string, string>)[language] || language.toUpperCase()}</option>)}</select>}
                </div>

                {isPracticeLoading && orderedPracticeProblems.length === 0 ? (
                  <div className="flex min-h-56 items-center justify-center text-sm font-semibold text-slate-500">Loading DSA problems…</div>
                ) : practiceLoadError && orderedPracticeProblems.length === 0 ? (
                  <div className="flex min-h-56 flex-col items-center justify-center gap-2 p-6 text-center" role="alert"><p className="text-sm font-semibold text-slate-800">Problem bank unavailable</p><p className="max-w-md text-sm text-slate-500">{practiceLoadError}</p><button type="button" onClick={() => { setIsPracticeLoading(true); setPracticeReloadKey((key) => key + 1); }} className="mt-2 rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-800">Try again</button></div>
                ) : (
                  <div>
                    {practiceLoadError && orderedPracticeProblems.length > 0 && <div role="status" className="border-b border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-900">Showing the last saved problem list. The latest refresh failed. <button type="button" onClick={() => { setIsPracticeLoading(true); setPracticeReloadKey((key) => key + 1); }} className="ml-1 font-semibold underline">Retry</button></div>}
                    <div className="grid gap-3 p-3 sm:grid-cols-2 sm:p-4">
                    {visibleStudentPractice.map((problem) => {
                      const number = orderedPracticeProblems.findIndex((item) => item.id === problem.id) + 1;
                      const solved = solvedSlugs.has(problem.slug) || solvedSlugs.has(problem.id);
                      return (
                        <article key={problem.id} className="flex min-w-0 flex-col rounded-xl border border-slate-200 bg-white p-4 transition-colors hover:border-indigo-200 hover:bg-indigo-50/20">
                          <div className="flex items-start justify-between gap-3"><span className="min-w-0"><span className="block text-[11px] font-semibold uppercase tracking-wide text-slate-400">Problem {number}</span><span className="mt-1 block truncate text-sm font-bold text-slate-900">{problem.title}</span></span><DifficultyBadge difficulty={problem.difficulty} /></div>
                          <p className="mt-2 line-clamp-2 min-h-10 text-xs leading-5 text-slate-600">{problem.description.trim() || 'Open this problem to read the full statement and examples.'}</p>
                          <div className="mt-3 flex flex-wrap items-center gap-2"><span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">{problem.tags[0] || 'Algorithms'}</span>{solved && <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5" />Solved</span>}</div>
                          <button type="button" onClick={() => handleSolve(problem.id)} className="mt-4 inline-flex min-h-10 items-center justify-center gap-2 self-start rounded-lg bg-indigo-700 px-3.5 text-sm font-semibold text-white transition hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">{solved ? 'Review solution' : 'Solve problem'}<ArrowRight className="h-4 w-4" /></button>
                        </article>
                      );
                    })}
                    </div>
                    {!visibleStudentPractice.length && <div className="p-10 text-center"><p className="text-sm font-semibold text-slate-800">{orderedPracticeProblems.length === 0 ? 'No practice problems are available yet' : 'No matching problems'}</p><p className="mt-1 text-sm text-slate-500">{orderedPracticeProblems.length === 0 ? 'The practice catalogue is empty. Try again later or open an instructor assignment.' : 'Try a different search or clear the selected filters.'}</p>{hasActiveFilters && <button type="button" onClick={handleClearFilters} className="mt-3 text-sm font-semibold text-indigo-700 hover:text-indigo-900">Clear filters</button>}</div>}
                  </div>
                )}
              </main>
            </div>
          </section>
        )}
      </div>
    );
  }

  return (
    <div className="mx-auto w-full min-w-0 max-w-7xl space-y-6 pb-12">
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
              className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-indigo-700 px-4 text-sm font-semibold text-white transition hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              <Plus className="w-4 h-4" />
              <span>+ Add Question</span>
            </button>
          )}

            <span className="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-xs font-semibold text-slate-600">
            {isInstructor ? 'Course Questions' : 'Total Problems'}: <strong className="text-indigo-600 font-mono text-sm ml-1">{isInstructor ? instructorProblems.length : problems.length}</strong>
          </span>
        </div>
      </div>

      {/* Binary Tabs (Strictly Instructor Assigned or Standard Practice) */}
      {!isInstructor && <div className="flex bg-slate-200/60 p-1.5 rounded-2xl border border-slate-200/80 max-w-md w-full sm:w-auto">
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
      </div>}

      {/* Queue Intelligence */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Current Queue</span>
            <Layers className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900 font-mono">{selectedTabCount}</span>
            <span className="text-xs text-slate-500">{activeTab === 'instructor' ? 'assigned questions' : 'practice drills'}</span>
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">{focusLabel}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">{isInstructor ? 'Your Courses' : 'Visible Progress'}</span>
            <Check className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900 font-mono">{isInstructor ? courses.length : completionCount}</span>
            <span className="text-xs text-slate-500">{isInstructor ? 'saved courses' : 'matched as solved'}</span>
          </div>
          <div className="mt-3 h-2 rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-emerald-500"
              style={{ width: `${isInstructor ? 0 : filtered.length ? Math.round((completionCount / filtered.length) * 100) : 0}%` }}
            />
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Assessment workflow</span>
            <ShieldAlert className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="mt-3 text-sm font-semibold text-slate-800">Run first, then submit</p>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-500">
            Run checks the sample cases. Submit requests the complete assessment.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 lg:flex-row">
        <div className="relative w-full lg:w-96">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search problems by title or topic"
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
        <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-12 text-center">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
            <Search className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800">
            {isInstructor && isInstructorLoading ? 'Loading course questions' : isInstructor && instructorProblems.length === 0 ? 'No course questions yet' : 'No matching problems found'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {isInstructor && isInstructorLoading
              ? 'Loading saved course questions…'
              : isInstructor && instructorLoadError
                ? instructorLoadError
                : isInstructor && courses.length === 0
                  ? 'Create a course in Courses before publishing questions.'
                  : isInstructor && instructorProblems.length === 0
                    ? 'No questions have been published to your courses yet. Use Add Question to create one.'
                    : 'Try adjusting your search keyword or topic filter.'}
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
                className={`flex flex-col justify-between overflow-hidden rounded-xl border bg-white p-5 transition-colors group ${
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
                        <span>{prob.dueDate ? `Due: ${new Date(prob.dueDate).toLocaleString()}` : 'No due date'}</span>
                      </span>
                    ) : (
                      <DifficultyBadge difficulty={prob.difficulty} />
                    )}

                    {prob.isInstructorAssigned && (
                      <span className="inline-flex items-center gap-1 bg-emerald-600 text-white text-[10px] font-extrabold px-2.5 py-1 rounded-xl shadow-xs tracking-wider uppercase">
                        <GraduationCap className="w-3 h-3" />
                        {prob.courseCode || 'Course'}
                      </span>
                    )}
                  </div>

                  {/* Status & Accuracy Sub-row */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div>
                      {isInstructor ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-xl border border-slate-200/80">
                          <FileCheck2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>{prob.testCases.length} test cases configured</span>
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
                      {isInstructor ? 'Course question' : <>Acc: <strong className="text-indigo-600">{prob.acceptanceRate}</strong></>}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                      <span className="block text-[10px] font-bold uppercase text-slate-500">Test cases</span>
                      <span className="text-[11px] font-medium text-slate-600">Run sample cases in workspace</span>
                    </div>
                    <div className="rounded-xl bg-slate-50 border border-slate-200/70 px-3 py-2">
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Target</span>
                      <span className="text-[11px] font-mono font-bold text-slate-700">
                        {prob.optimalComplexity.time}, {prob.optimalComplexity.space}
                      </span>
                    </div>
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
                    <span>{prob.isInstructorAssigned ? (prob.dueDate ? `Due ${new Date(prob.dueDate).toLocaleString()}` : 'No due date') : `Opt: ${prob.optimalComplexity.time}`}</span>
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
                        onClick={() => handleDeleteProblem(prob)}
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
        subtitle="Create a question and publish it to an assignment in one of your courses"
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
              <label className="block font-bold text-slate-700 mb-1">Course</label>
              <select
                value={formCourseId}
                onChange={(e) => setFormCourseId(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium cursor-pointer"
              >
                <option value="">Select a course</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} · {c.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Due Date</label>
              <input
                type="datetime-local"
                value={formDueDate}
                onChange={(e) => setFormDueDate(e.target.value)}
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
              <label className="block font-bold text-slate-700 mb-1">Topic</label>
              <input
                type="text"
                value={formTags}
                onChange={(e) => setFormTags(e.target.value)}
                placeholder="e.g. Arrays"
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
                          disabled={formTestCases.length <= 1}
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

          {questionError && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm font-semibold text-rose-700">{questionError}</p>}
          {!courses.length && <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">Create a course first in Courses before publishing a question.</p>}
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
              disabled={isSavingQuestion || courses.length === 0}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-95 cursor-pointer"
            >
              {isSavingQuestion ? 'Saving…' : editingProblemId ? 'Save Changes' : 'Publish Question'}
            </button>
          </div>
        </form>
      </Modal>
      <DoubleConfirmDialog
        isOpen={Boolean(deleteProblemTarget)}
        title="Delete this question?"
        description={`This permanently deletes ${deleteProblemTarget?.title} and its test cases. If it belongs to an assignment or has submissions, deletion may be blocked to protect course history.`}
        actionLabel="delete question"
        busy={isDeletingProblem}
        onClose={() => setDeleteProblemTarget(null)}
        onConfirm={confirmDeleteProblem}
      />
      <DoubleConfirmDialog
        isOpen={Boolean(removeCaseTarget)}
        title="Remove this test case?"
        description="This test case will be removed from the question draft. The change takes effect only when you save the question."
        actionLabel="remove test case"
        onClose={() => setRemoveCaseTarget(null)}
        onConfirm={confirmRemoveTestCase}
      />

      {selectedProblemForAnalytics && (
        <Modal
          isOpen={Boolean(selectedProblemForAnalytics)}
          onClose={() => setSelectedProblemForAnalytics(null)}
          title={selectedProblemForAnalytics.title}
          subtitle={`${selectedProblemForAnalytics.courseCode || 'Course'}${selectedProblemForAnalytics.dueDate ? ` · Due ${new Date(selectedProblemForAnalytics.dueDate).toLocaleString()}` : ''}`}
          maxWidth="2xl"
        >
          <div className="space-y-5 text-sm">
            <p className="whitespace-pre-wrap text-slate-700">{selectedProblemForAnalytics.description || 'No problem statement saved.'}</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><span className="block text-xs font-bold uppercase text-slate-500">Difficulty</span><span className="mt-1 block font-semibold">{selectedProblemForAnalytics.difficulty}</span></div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><span className="block text-xs font-bold uppercase text-slate-500">Topic</span><span className="mt-1 block font-semibold">{selectedProblemForAnalytics.tags.join(', ') || '—'}</span></div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><span className="block text-xs font-bold uppercase text-slate-500">Time target</span><span className="mt-1 block font-mono font-semibold">{selectedProblemForAnalytics.optimalComplexity.time}</span></div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><span className="block text-xs font-bold uppercase text-slate-500">Space target</span><span className="mt-1 block font-mono font-semibold">{selectedProblemForAnalytics.optimalComplexity.space}</span></div>
            </div>
            <div className="rounded-xl border border-slate-200 p-4"><h3 className="font-bold">Test cases</h3><p className="mt-1 text-slate-600">Run sample cases in the workspace. Submit your solution for the complete assessment.</p></div>
            <div className="flex justify-end border-t border-slate-100 pt-3"><button onClick={() => setSelectedProblemForAnalytics(null)} className="rounded-xl px-4 py-2 font-bold text-slate-600 hover:bg-slate-100">Close</button></div>
          </div>
        </Modal>
      )}    </div>
  );
};

