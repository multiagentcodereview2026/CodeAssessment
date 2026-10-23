import React, { useEffect, useState, useRef } from 'react';
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
  Check,
  ChevronDown,
  RotateCcw,
  Filter
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
  const [isInstructorSkillsOpen, setIsInstructorSkillsOpen] = useState(false);
  const [skillSearch, setSkillSearch] = useState('');
  const skillsDropdownRef = useRef<HTMLDivElement>(null);
  const instructorSkillsDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (skillsDropdownRef.current && !skillsDropdownRef.current.contains(e.target as Node)) {
        setIsSkillsOpen(false);
      }
      if (instructorSkillsDropdownRef.current && !instructorSkillsDropdownRef.current.contains(e.target as Node)) {
        setIsInstructorSkillsOpen(false);
      }
    };
    if (isSkillsOpen || isInstructorSkillsOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isSkillsOpen, isInstructorSkillsOpen]);
  const [practiceProblems, setPracticeProblems] = useState<Problem[]>(readCachedPracticeCatalogue);
  const [isPracticeLoading, setIsPracticeLoading] = useState(() => readCachedPracticeCatalogue().length === 0);
  const [practiceLoadError, setPracticeLoadError] = useState('');
  const [practiceReloadKey, setPracticeReloadKey] = useState(0);
  const [instructorProblems, setInstructorProblems] = useState<Problem[]>([]);
  const [isInstructorLoading, setIsInstructorLoading] = useState(true);
  const [instructorLoadError, setInstructorLoadError] = useState('');
  const [practicePage, setPracticePage] = useState(1);
  const practicePageSize = 50;

  useEffect(() => {
    setPracticePage(1);
  }, [search, difficultyFilter, selectedTag, languageFilter]);

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
  const studentInstructorTopics = Array.from(new Set(studentInstructorProblems.flatMap((problem) => problem.tags))).sort();
  const currentTopics = activeTab === 'instructor' && studentInstructorTopics.length ? studentInstructorTopics : studentPracticeTopics;
  const studentPracticeLanguages = Array.from(new Set(orderedPracticeProblems.flatMap((problem) => Object.keys(problem.starterCode || {}).map((language) => language.toLowerCase())))).sort();
  const visibleStudentPractice = orderedPracticeProblems.filter((problem, index) => {
    const matchesNumber = /^\d+$/.test(normalizedStudentSearch) && questionOrder(problem.id) === Number(normalizedStudentSearch);
    const matchesText = !normalizedStudentSearch || `${problem.id} ${problem.title} ${problem.tags.join(' ')}`.toLowerCase().includes(normalizedStudentSearch);
    return (matchesNumber || matchesText) &&
      (difficultyFilter === 'all' || problem.difficulty.toLowerCase() === difficultyFilter) &&
      (selectedTag === 'all' || problem.tags.includes(selectedTag)) &&
      (languageFilter === 'all' || Object.keys(problem.starterCode || {}).some((language) => language.toLowerCase() === languageFilter));
  });

  const totalPracticePages = Math.ceil(visibleStudentPractice.length / practicePageSize) || 1;
  const paginatedStudentPractice = visibleStudentPractice.slice(
    (practicePage - 1) * practicePageSize,
    practicePage * practicePageSize
  );
  const visibleStudentInstructor = studentInstructorProblems.filter((problem) => {
    const content = `${problem.title} ${problem.courseCode || ''} ${problem.tags.join(' ')}`.toLowerCase();
    const matchSearch = !normalizedStudentSearch || content.includes(normalizedStudentSearch);
    const matchDiff = difficultyFilter === 'all' || problem.difficulty.toLowerCase() === difficultyFilter.toLowerCase();
    const matchTag = selectedTag === 'all' || problem.tags.includes(selectedTag);
    return matchSearch && matchDiff && matchTag;
  });

  if (!isInstructor) {
    return (
      <div className="space-y-6 pb-12 animate-fadeIn">
        {/* Unified Page Header Aligned with App Design System */}
        <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-indigo-700">Independent practice</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Find a problem to solve
            </h1>
            <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-600">
              Choose a topic and difficulty, then open a problem to write code, run examples, and submit for assessment.
            </p>
          </div>

          {/* Compact Tab Switcher Aligned to Header */}
          <div className="flex shrink-0 items-center">
            <div className="inline-flex items-center gap-0.5 rounded-lg border border-slate-200/90 bg-slate-100 p-0.5 shadow-2xs">
              <button
                type="button"
                onClick={() => { setActiveTab('practice'); navigate('/problems'); }}
                className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-all cursor-pointer ${
                  activeTab === 'practice'
                    ? 'bg-white text-slate-900 font-semibold shadow-xs border border-slate-200/70'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-white/50'
                }`}
              >
                <Code2 className={`h-3.5 w-3.5 ${activeTab === 'practice' ? 'text-indigo-600' : 'text-slate-400'}`} />
                <span>DSA Practice</span>
                <span className={`ml-0.5 inline-flex items-center justify-center px-1.5 py-0.5 rounded-full text-[10px] font-mono leading-none transition-colors ${
                  activeTab === 'practice'
                    ? 'bg-indigo-50 text-indigo-700 font-medium border border-indigo-100'
                    : 'bg-slate-200/70 text-slate-500'
                }`}>
                  {orderedPracticeProblems.length || practiceProblems.length}
                </span>
              </button>

              <button
                type="button"
                onClick={() => { setActiveTab('instructor'); navigate('/problems?view=instructor'); }}
                className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-all cursor-pointer ${
                  activeTab === 'instructor'
                    ? 'bg-white text-slate-900 font-semibold shadow-xs border border-slate-200/70'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-white/50'
                }`}
              >
                <GraduationCap className={`h-3.5 w-3.5 ${activeTab === 'instructor' ? 'text-indigo-600' : 'text-slate-400'}`} />
                <span>Instructor Problems</span>
                <span className={`ml-0.5 inline-flex items-center justify-center px-1.5 py-0.5 rounded-full text-[10px] font-mono leading-none transition-colors ${
                  activeTab === 'instructor'
                    ? 'bg-indigo-50 text-indigo-700 font-medium border border-indigo-100'
                    : 'bg-slate-200/70 text-slate-500'
                }`}>
                  {studentInstructorProblems.length}
                </span>
              </button>
            </div>
          </div>
        </header>

        <section className="space-y-4">
          <div className="relative">
            <main className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
              {/* Filter and Search Bar */}
              <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder={activeTab === 'practice' ? "Search by number, question name, or DSA topic..." : "Search by question name, topic, or course..."}
                    className="h-9 w-full rounded-xl border border-slate-200 bg-slate-50/70 py-1.5 pl-9 pr-3 text-xs text-slate-900 outline-none transition-all placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:ring-1 focus:ring-indigo-100"
                  />
                  {search && (
                    <button
                      type="button"
                      onClick={() => setSearch('')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Skills Popover Filter */}
                <div className="relative" ref={skillsDropdownRef}>
                  <button
                    type="button"
                    onClick={() => setIsSkillsOpen((open) => !open)}
                    aria-expanded={isSkillsOpen}
                    className={`inline-flex h-9 w-full items-center justify-between gap-2 rounded-xl border px-3 text-xs font-medium transition-all cursor-pointer sm:w-auto ${
                      selectedTag !== 'all'
                        ? 'border-indigo-300 bg-indigo-50 text-indigo-700 shadow-2xs font-semibold'
                        : isSkillsOpen
                        ? 'border-indigo-300 bg-indigo-50/50 text-indigo-700 shadow-xs'
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-1.5">
                      <Layers className={`h-3.5 w-3.5 ${selectedTag !== 'all' ? 'text-indigo-600' : 'text-slate-400'}`} />
                      <span>{selectedTag === 'all' ? 'Skills' : selectedTag}</span>
                    </div>
                    {selectedTag !== 'all' ? (
                      <span
                        role="button"
                        tabIndex={0}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTag('all');
                        }}
                        className="rounded-full p-0.5 text-indigo-500 hover:bg-indigo-200/70 hover:text-indigo-800 transition-colors"
                        title="Clear skill filter"
                      >
                        <X className="h-3 w-3" />
                      </span>
                    ) : (
                      <ChevronDown className={`h-3 w-3 text-slate-400 transition-transform duration-150 ${isSkillsOpen ? 'rotate-180 text-indigo-600' : ''}`} />
                    )}
                  </button>

                  {isSkillsOpen && (
                    <div className="absolute right-0 top-full z-40 mt-1.5 w-[min(340px,calc(100vw-2rem))] rounded-2xl border border-slate-200/90 bg-white p-3 text-slate-800 shadow-xl shadow-indigo-950/10 animate-fadeIn">
                      {/* Popover Header */}
                      <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
                        <div className="flex items-center gap-1.5">
                          <Layers className="h-3.5 w-3.5 text-indigo-600" />
                          <h3 className="text-xs font-bold text-slate-900">Filter by Topic</h3>
                          <span className="rounded-full bg-slate-100 px-1.5 py-0.2 text-[10px] font-semibold text-slate-600">
                            {currentTopics.length}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {selectedTag !== 'all' && (
                            <button
                              type="button"
                              onClick={() => { setSelectedTag('all'); setIsSkillsOpen(false); }}
                              className="flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 cursor-pointer"
                            >
                              <RotateCcw className="h-2.5 w-2.5" />
                              Reset
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => setIsSkillsOpen(false)}
                            aria-label="Close skills"
                            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors cursor-pointer"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* Search Input for Topics */}
                      <div className="relative mt-2.5">
                        <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-400" />
                        <input
                          type="text"
                          value={skillSearch}
                          onChange={(e) => setSkillSearch(e.target.value)}
                          placeholder="Search topics (e.g., Array, Graph, DP)..."
                          className="w-full rounded-lg border border-slate-200 bg-slate-50/80 py-1.5 pl-8 pr-7 text-xs text-slate-800 placeholder-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-200"
                        />
                        {skillSearch && (
                          <button
                            type="button"
                            onClick={() => setSkillSearch('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        )}
                      </div>

                      {/* All Topics option */}
                      <div className="mt-2.5">
                        <button
                          type="button"
                          onClick={() => { setSelectedTag('all'); setIsSkillsOpen(false); }}
                          className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
                            selectedTag === 'all'
                              ? 'bg-indigo-600 text-white shadow-xs font-semibold'
                              : 'bg-slate-50 text-slate-700 hover:bg-indigo-50 hover:text-indigo-700'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className={`w-1.5 h-1.5 rounded-full ${selectedTag === 'all' ? 'bg-white' : 'bg-slate-400'}`} />
                            <span>All Topics</span>
                          </div>
                          <span className={`rounded px-1.5 py-0.2 text-[10px] font-mono ${selectedTag === 'all' ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-200/80 text-slate-600'}`}>
                            {activeTab === 'instructor' ? studentInstructorProblems.length : orderedPracticeProblems.length}
                          </span>
                        </button>
                      </div>

                      {/* Topics Pill Cloud */}
                      <div className="mt-2 max-h-52 overflow-y-auto pr-1">
                        <div className="flex flex-wrap gap-1">
                          {currentTopics
                            .filter((topic) => !skillSearch || topic.toLowerCase().includes(skillSearch.toLowerCase()))
                            .map((topic) => {
                              const count = (activeTab === 'instructor' ? studentInstructorProblems : orderedPracticeProblems).filter((p) => p.tags.includes(topic)).length;
                              const isSelected = selectedTag === topic;
                              return (
                                <button
                                  type="button"
                                  key={topic}
                                  onClick={() => { setSelectedTag(topic); setIsSkillsOpen(false); }}
                                  className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium transition-all cursor-pointer ${
                                    isSelected
                                      ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                                      : 'border border-slate-200 bg-white text-slate-700 hover:border-indigo-300 hover:bg-indigo-50/60 hover:text-indigo-700'
                                  }`}
                                >
                                  <span>{topic}</span>
                                  <span className={`rounded px-1 py-0.2 text-[9px] font-mono ${
                                    isSelected ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-100 text-slate-500'
                                  }`}>
                                    {count}
                                  </span>
                                </button>
                              );
                            })}
                        </div>
                        {currentTopics.filter((topic) => !skillSearch || topic.toLowerCase().includes(skillSearch.toLowerCase())).length === 0 && (
                          <p className="py-5 text-center text-xs text-slate-400">No topics match &quot;{skillSearch}&quot;</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <select
                  aria-label="Filter by difficulty"
                  value={difficultyFilter}
                  onChange={(event) => setDifficultyFilter(event.target.value)}
                  className="h-9 rounded-xl border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-700 outline-none transition-all hover:border-slate-300 focus:border-indigo-500 cursor-pointer"
                >
                  <option value="all">All difficulties</option>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>

                {activeTab === 'practice' && studentPracticeLanguages.length > 0 && (
                  <select
                    aria-label="Filter by supported language"
                    value={languageFilter}
                    onChange={(event) => setLanguageFilter(event.target.value)}
                    className="h-9 rounded-xl border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-700 outline-none transition-all hover:border-slate-300 focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="all">All languages</option>
                    {studentPracticeLanguages.map((language) => (
                      <option key={language} value={language}>
                        {({ cpp: 'C++', c: 'C', java: 'Java', python: 'Python', javascript: 'JavaScript' } as Record<string, string>)[language] || language.toUpperCase()}
                      </option>
                    ))}
                  </select>
                )}

                {hasActiveFilters && (
                  <button
                    type="button"
                    onClick={handleClearFilters}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 hover:underline px-2 py-1 cursor-pointer"
                  >
                    Reset Filters
                  </button>
                )}
              </div>

              {/* Active Tab: Instructor Problems */}
              {activeTab === 'instructor' ? (
                isInstructorLoading ? (
                  <div className="flex min-h-56 items-center justify-center text-sm font-semibold text-slate-500">
                    Loading instructor assignments…
                  </div>
                ) : studentInstructorProblems.length === 0 ? (
                  <div className="space-y-3 p-12 text-center">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                      <GraduationCap className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-bold text-slate-800">No instructor assignments yet</h3>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto">
                      Your instructor has not published any coursework assignments yet. Explore DSA Practice to sharpen your coding skills.
                    </p>
                    <button
                      type="button"
                      onClick={() => { setActiveTab('practice'); navigate('/problems'); }}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition-colors cursor-pointer"
                    >
                      <Code2 className="w-3.5 h-3.5" />
                      <span>Switch to DSA Practice</span>
                    </button>
                  </div>
                ) : visibleStudentInstructor.length === 0 ? (
                  <div className="space-y-3 p-12 text-center">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                      <Search className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-bold text-slate-800">No matching instructor problems</h3>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto">
                      Try adjusting your search keyword or clearing the filters.
                    </p>
                    {hasActiveFilters && (
                      <button
                        type="button"
                        onClick={handleClearFilters}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition-colors cursor-pointer"
                      >
                        Clear Filters
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-200/80 dark:border-slate-800 bg-slate-50/75 dark:bg-slate-800/60 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                          <th className="py-3 px-4 w-16 text-center">#</th>
                          <th className="py-3 px-4">Title</th>
                          <th className="py-3 px-4 hidden md:table-cell">Course &amp; Due Date</th>
                          <th className="py-3 px-4 w-32">Difficulty</th>
                          <th className="py-3 px-4 w-32 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                        {visibleStudentInstructor.map((problem, idx) => {
                          const solved = solvedSlugs.has(problem.slug) || solvedSlugs.has(problem.id);
                          return (
                            <tr
                              key={problem.id}
                              onClick={() => handleSolve(problem.id)}
                              className="group hover:bg-indigo-50/40 dark:hover:bg-indigo-950/40 transition-colors cursor-pointer"
                            >
                              <td className="py-3.5 px-4 text-center">
                                {solved ? (
                                  <span className="inline-flex items-center justify-center text-emerald-600" title="Solved">
                                    <CheckCircle2 className="w-4 h-4" />
                                  </span>
                                ) : (
                                  <span className="font-mono text-xs font-semibold text-slate-400 group-hover:text-indigo-600 transition-colors">
                                    {idx + 1}
                                  </span>
                                )}
                              </td>
                              <td className="py-3.5 px-4">
                                <div className="flex flex-col">
                                  <span className="text-sm font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                                    {problem.title}
                                  </span>
                                  <div className="flex flex-wrap items-center gap-1 mt-1">
                                    {problem.tags.slice(0, 3).map((tag, tIdx) => (
                                      <span key={tIdx} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
                                        {tag}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              </td>
                              <td className="py-3.5 px-4 hidden md:table-cell text-xs text-slate-500">
                                <div className="flex flex-col gap-0.5">
                                  {problem.courseCode && (
                                    <span className="inline-flex items-center gap-1 font-bold text-slate-700">
                                      <GraduationCap className="w-3.5 h-3.5 text-indigo-600" />
                                      {problem.courseCode}
                                    </span>
                                  )}
                                  {problem.dueDate ? (
                                    <span className="inline-flex items-center gap-1 text-[11px] text-amber-700">
                                      <Calendar className="w-3 h-3 text-amber-600" />
                                      {new Date(problem.dueDate).toLocaleDateString()}
                                    </span>
                                  ) : (
                                    <span className="text-[11px] text-slate-400">No due date</span>
                                  )}
                                </div>
                              </td>
                              <td className="py-3.5 px-4">
                                <DifficultyBadge difficulty={problem.difficulty} />
                              </td>
                              <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                                <button
                                  type="button"
                                  onClick={() => handleSolve(problem.id)}
                                  className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-bold transition-all shadow-2xs ${
                                    solved
                                      ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-600 hover:text-white'
                                      : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-600 hover:text-white'
                                  }`}
                                >
                                  <span>{solved ? 'Review' : 'Solve'}</span>
                                  <ArrowRight className="h-3 w-3" />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )
              ) : (
                /* Active Tab: DSA Practice */
                isPracticeLoading && orderedPracticeProblems.length === 0 ? (
                  <div className="flex min-h-56 items-center justify-center text-sm font-semibold text-slate-500">Loading DSA problems…</div>
                ) : practiceLoadError && orderedPracticeProblems.length === 0 ? (
                  <div className="flex min-h-56 flex-col items-center justify-center gap-2 p-6 text-center" role="alert"><p className="text-sm font-semibold text-slate-800">Problem bank unavailable</p><p className="max-w-md text-sm text-slate-500">{practiceLoadError}</p><button type="button" onClick={() => { setIsPracticeLoading(true); setPracticeReloadKey((key) => key + 1); }} className="mt-2 rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-800">Try again</button></div>
                ) : (
                  <div>
                    {practiceLoadError && orderedPracticeProblems.length > 0 && <div role="status" className="border-b border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-900">Showing the last saved problem list. The latest refresh failed. <button type="button" onClick={() => { setIsPracticeLoading(true); setPracticeReloadKey((key) => key + 1); }} className="ml-1 font-semibold underline">Retry</button></div>}
                    {/* Row-wise Problems Table */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="border-b border-slate-200/80 dark:border-slate-800 bg-slate-50/75 dark:bg-slate-800/60 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                            <th className="py-3 px-4 w-16 text-center">#</th>
                            <th className="py-3 px-4">Title</th>
                            <th className="py-3 px-4 hidden md:table-cell">Tags</th>
                            <th className="py-3 px-4 w-32">Difficulty</th>
                            <th className="py-3 px-4 w-32 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                          {paginatedStudentPractice.map((problem) => {
                            const number = orderedPracticeProblems.findIndex((item) => item.id === problem.id) + 1;
                            const solved = solvedSlugs.has(problem.slug) || solvedSlugs.has(problem.id);

                            return (
                              <tr
                                key={problem.id}
                                onClick={() => handleSolve(problem.id)}
                                className="group hover:bg-indigo-50/40 dark:hover:bg-indigo-950/40 transition-colors cursor-pointer"
                              >
                                {/* Problem Number / Status */}
                                <td className="py-3.5 px-4 text-center">
                                  {solved ? (
                                    <span className="inline-flex items-center justify-center text-emerald-600" title="Solved">
                                      <CheckCircle2 className="w-4 h-4" />
                                    </span>
                                  ) : (
                                    <span className="font-mono text-xs font-semibold text-slate-400 group-hover:text-indigo-600 transition-colors">
                                      {number}
                                    </span>
                                  )}
                                </td>

                                {/* Problem Title & Mobile Tags */}
                                <td className="py-3.5 px-4">
                                  <div className="flex flex-col">
                                    <span className="text-sm font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                                      {problem.title}
                                    </span>
                                    <div className="flex flex-wrap items-center gap-1.5 mt-1 md:hidden">
                                      {problem.tags.slice(0, 2).map((tag, tIdx) => (
                                        <span
                                          key={tIdx}
                                          className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600"
                                        >
                                          {tag}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                </td>

                                {/* Desktop Tags */}
                                <td className="py-3.5 px-4 hidden md:table-cell">
                                  <div className="flex flex-wrap items-center gap-1.5">
                                    {problem.tags.slice(0, 3).map((tag, tIdx) => (
                                      <span
                                        key={tIdx}
                                        className="rounded-lg bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 border border-slate-200/50"
                                      >
                                        {tag}
                                      </span>
                                    ))}
                                    {problem.optimalComplexity?.time && problem.optimalComplexity.time !== '—' && (
                                      <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-400 ml-1">
                                        <Clock className="w-3 h-3" />
                                        {problem.optimalComplexity.time}
                                      </span>
                                    )}
                                  </div>
                                </td>

                                {/* Difficulty */}
                                <td className="py-3.5 px-4">
                                  <DifficultyBadge difficulty={problem.difficulty} />
                                </td>

                                {/* Action */}
                                <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                                  <button
                                    type="button"
                                    onClick={() => handleSolve(problem.id)}
                                    className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-bold transition-all shadow-2xs ${
                                      solved
                                        ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-600 hover:text-white'
                                        : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-600 hover:text-white'
                                    }`}
                                  >
                                    <span>{solved ? 'Review' : 'Solve'}</span>
                                    <ArrowRight className="h-3 w-3" />
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Pagination Controls */}
                    {visibleStudentPractice.length > practicePageSize && (
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-200/80 px-6 py-3.5 bg-slate-50/60">
                        <span className="text-xs text-slate-500 font-medium">
                          Showing <strong className="text-slate-800 font-mono">{(practicePage - 1) * practicePageSize + 1}</strong>–<strong className="text-slate-800 font-mono">{Math.min(practicePage * practicePageSize, visibleStudentPractice.length)}</strong> of <strong className="text-slate-800 font-mono">{visibleStudentPractice.length.toLocaleString()}</strong> problems
                        </span>

                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            disabled={practicePage === 1}
                            onClick={() => setPracticePage((p) => Math.max(1, p - 1))}
                            className="px-3 py-1.5 text-xs font-semibold rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer shadow-2xs"
                          >
                            Previous
                          </button>

                          <span className="px-3 py-1 text-xs font-mono font-bold text-slate-700 bg-white rounded-xl border border-slate-200">
                            Page {practicePage} of {totalPracticePages}
                          </span>

                          <button
                            type="button"
                            disabled={practicePage === totalPracticePages}
                            onClick={() => setPracticePage((p) => Math.min(totalPracticePages, p + 1))}
                            className="px-3 py-1.5 text-xs font-semibold rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer shadow-2xs"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    )}
                    {!visibleStudentPractice.length && <div className="p-10 text-center"><p className="text-sm font-semibold text-slate-800">{orderedPracticeProblems.length === 0 ? 'No practice problems are available yet' : 'No matching problems'}</p><p className="mt-1 text-sm text-slate-500">{orderedPracticeProblems.length === 0 ? 'The practice catalogue is empty. Try again later or open an instructor assignment.' : 'Try a different search or clear the selected filters.'}</p>{hasActiveFilters && <button type="button" onClick={handleClearFilters} className="mt-3 text-sm font-semibold text-indigo-700 hover:text-indigo-900">Clear filters</button>}</div>}
                  </div>
                )
              )}
            </main>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full min-w-0 max-w-7xl space-y-6 pb-12 animate-fadeIn">
      {/* Header Aligned to Design System */}
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-emerald-600">Course Administration</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Problem Bank &amp; Assessments
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-600">
            Create, customize test cases, configure due dates, and inspect multi-agent question diagnostics.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {isInstructor && (
            <button
              type="button"
              onClick={handleOpenCreateModal}
              className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-emerald-600 px-3.5 text-xs font-semibold text-white shadow-2xs transition hover:bg-emerald-700 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>+ Add Question</span>
            </button>
          )}

          <span className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 shadow-2xs">
            {isInstructor ? 'Course Questions' : 'Total Problems'}: <strong className="text-emerald-600 font-mono text-xs ml-0.5">{isInstructor ? instructorProblems.length : problems.length}</strong>
          </span>
        </div>
      </header>

      {/* Queue Intelligence */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Course Questions</span>
            <Layers className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900 font-mono">{instructorProblems.length}</span>
            <span className="text-xs text-slate-500">questions published</span>
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
            Assigned across your active courses with customized tests and due dates.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Active Courses</span>
            <GraduationCap className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900 font-mono">{courses.length}</span>
            <span className="text-xs text-slate-500">linked courses</span>
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
            Students enrolled in these courses can view and submit these questions.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Assessment Workflow</span>
            <ShieldAlert className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="mt-2 text-sm font-semibold text-slate-800">Automated Evaluation</p>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-500">
            Inspect execution accuracy, analyze failures, and monitor student submissions.
          </p>
        </div>
      </div>

      <main className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {/* Filter and Search Bar */}
        <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search questions, topics, course..."
              className="h-9 w-full rounded-xl border border-slate-200 bg-slate-50/70 py-1.5 pl-9 pr-3 text-xs text-slate-900 outline-none transition-all placeholder:text-slate-400 focus:border-emerald-500 focus:bg-white focus:ring-1 focus:ring-emerald-100"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Topics Popover Filter */}
          <div className="relative" ref={instructorSkillsDropdownRef}>
            <button
              type="button"
              onClick={() => setIsInstructorSkillsOpen((open) => !open)}
              aria-expanded={isInstructorSkillsOpen}
              className={`inline-flex h-9 w-full items-center justify-between gap-2 rounded-xl border px-3 text-xs font-medium transition-all cursor-pointer sm:w-auto ${
                selectedTag !== 'all'
                  ? 'border-emerald-300 bg-emerald-50 text-emerald-700 shadow-2xs font-semibold'
                  : isInstructorSkillsOpen
                  ? 'border-emerald-300 bg-emerald-50/50 text-emerald-700 shadow-xs'
                  : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <Layers className={`h-3.5 w-3.5 ${selectedTag !== 'all' ? 'text-emerald-600' : 'text-slate-400'}`} />
                <span>{selectedTag === 'all' ? 'Skills' : selectedTag}</span>
              </div>
              {selectedTag !== 'all' ? (
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedTag('all');
                  }}
                  className="rounded-full p-0.5 text-emerald-500 hover:bg-emerald-200/70 hover:text-emerald-800 transition-colors"
                  title="Clear skill filter"
                >
                  <X className="h-3 w-3" />
                </span>
              ) : (
                <ChevronDown className={`h-3 w-3 text-slate-400 transition-transform duration-150 ${isInstructorSkillsOpen ? 'rotate-180 text-emerald-600' : ''}`} />
              )}
            </button>

            {isInstructorSkillsOpen && (
              <div className="absolute right-0 top-full z-40 mt-1.5 w-[min(340px,calc(100vw-2rem))] rounded-2xl border border-slate-200/90 bg-white p-3 text-slate-800 shadow-xl shadow-emerald-950/10 animate-fadeIn">
                {/* Popover Header */}
                <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
                  <div className="flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5 text-emerald-600" />
                    <h3 className="text-xs font-bold text-slate-900">Filter by Topic</h3>
                    <span className="rounded-full bg-slate-100 px-1.5 py-0.2 text-[10px] font-semibold text-slate-600">
                      {allTags.length}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedTag !== 'all' && (
                      <button
                        type="button"
                        onClick={() => { setSelectedTag('all'); setIsInstructorSkillsOpen(false); }}
                        className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600 hover:text-emerald-800 cursor-pointer"
                      >
                        <RotateCcw className="h-2.5 w-2.5" />
                        Reset
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setIsInstructorSkillsOpen(false)}
                      aria-label="Close skills"
                      className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors cursor-pointer"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Search Input for Topics */}
                <div className="relative mt-2.5">
                  <Search className="absolute left-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={skillSearch}
                    onChange={(e) => setSkillSearch(e.target.value)}
                    placeholder="Search topics..."
                    className="w-full rounded-lg border border-slate-200 bg-slate-50/80 py-1.5 pl-8 pr-7 text-xs text-slate-800 placeholder-slate-400 focus:border-emerald-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-emerald-200"
                  />
                  {skillSearch && (
                    <button
                      type="button"
                      onClick={() => setSkillSearch('')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>

                {/* All Topics option */}
                <div className="mt-2.5">
                  <button
                    type="button"
                    onClick={() => { setSelectedTag('all'); setIsInstructorSkillsOpen(false); }}
                    className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
                      selectedTag === 'all'
                        ? 'bg-emerald-600 text-white shadow-xs font-semibold'
                        : 'bg-slate-50 text-slate-700 hover:bg-emerald-50 hover:text-emerald-700'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${selectedTag === 'all' ? 'bg-white' : 'bg-slate-400'}`} />
                      <span>All Topics</span>
                    </div>
                    <span className={`rounded px-1.5 py-0.2 text-[10px] font-mono ${selectedTag === 'all' ? 'bg-emerald-700 text-emerald-100' : 'bg-slate-200/80 text-slate-600'}`}>
                      {instructorProblems.length}
                    </span>
                  </button>
                </div>

                {/* Topics Pill Cloud */}
                <div className="mt-2 max-h-52 overflow-y-auto pr-1">
                  <div className="flex flex-wrap gap-1">
                    {allTags
                      .filter((topic) => !skillSearch || topic.toLowerCase().includes(skillSearch.toLowerCase()))
                      .map((topic) => {
                        const count = instructorProblems.filter((p) => p.tags.includes(topic)).length;
                        const isSelected = selectedTag === topic;
                        return (
                          <button
                            type="button"
                            key={topic}
                            onClick={() => { setSelectedTag(topic); setIsInstructorSkillsOpen(false); }}
                            className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium transition-all cursor-pointer ${
                              isSelected
                                ? 'bg-emerald-600 text-white font-semibold shadow-xs'
                                : 'border border-slate-200 bg-white text-slate-700 hover:border-emerald-300 hover:bg-emerald-50/60 hover:text-emerald-700'
                            }`}
                          >
                            <span>{topic}</span>
                            <span className={`rounded px-1 py-0.2 text-[9px] font-mono ${
                              isSelected ? 'bg-emerald-700 text-emerald-100' : 'bg-slate-100 text-slate-500'
                            }`}>
                              {count}
                            </span>
                          </button>
                        );
                      })}
                  </div>
                  {allTags.filter((topic) => !skillSearch || topic.toLowerCase().includes(skillSearch.toLowerCase())).length === 0 && (
                    <p className="py-5 text-center text-xs text-slate-400">No topics match &quot;{skillSearch}&quot;</p>
                  )}
                </div>
              </div>
            )}
          </div>

          <select
            aria-label="Filter by difficulty"
            value={difficultyFilter}
            onChange={(event) => setDifficultyFilter(event.target.value)}
            className="h-9 rounded-xl border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-700 outline-none transition-all hover:border-slate-300 focus:border-emerald-500 cursor-pointer"
          >
            <option value="all">All difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>

          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleClearFilters}
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 hover:underline px-2 py-1 cursor-pointer"
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Row-wise Problems Table or Empty State */}
        {filtered.length === 0 ? (
          <div className="space-y-3 p-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-800">
              {isInstructorLoading ? 'Loading course questions…' : instructorProblems.length === 0 ? 'No course questions yet' : 'No matching questions found'}
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {isInstructorLoading
                ? 'Loading saved course questions…'
                : instructorLoadError
                  ? instructorLoadError
                  : courses.length === 0
                    ? 'Create a course in Courses before publishing questions.'
                    : instructorProblems.length === 0
                      ? 'No questions have been published to your courses yet. Use + Add Question to create one.'
                      : 'Try adjusting your search keyword or topic filter.'}
            </p>
            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-semibold hover:bg-emerald-700 transition-colors cursor-pointer"
              >
                Clear All Filters
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200/80 dark:border-slate-800 bg-slate-50/75 dark:bg-slate-800/60 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <th className="py-3 px-4 w-12 text-center">#</th>
                  <th className="py-3 px-4">Title &amp; Course</th>
                  <th className="py-3 px-4 hidden md:table-cell">Due Date</th>
                  <th className="py-3 px-4 hidden lg:table-cell">Test Cases</th>
                  <th className="py-3 px-4 w-28">Difficulty</th>
                  <th className="py-3 px-4 w-44 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {filtered.map((prob, idx) => (
                  <tr
                    key={prob.id}
                    className="group hover:bg-emerald-50/40 dark:hover:bg-emerald-950/40 transition-colors cursor-pointer"
                    onClick={() => setSelectedProblemForAnalytics(prob)}
                  >
                    {/* Index */}
                    <td className="py-3.5 px-4 text-center">
                      <span className="font-mono text-xs font-semibold text-slate-400 group-hover:text-emerald-600 transition-colors">
                        {idx + 1}
                      </span>
                    </td>

                    {/* Title & Course */}
                    <td className="py-3.5 px-4">
                      <div className="flex flex-col">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-slate-900 group-hover:text-emerald-700 transition-colors">
                            {prob.title}
                          </span>
                          {prob.courseCode && (
                            <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200 uppercase tracking-wide">
                              <GraduationCap className="w-3 h-3 text-emerald-600" />
                              {prob.courseCode}
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-1.5 mt-1">
                          {prob.tags.map((tag, tIdx) => (
                            <span
                              key={tIdx}
                              className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-medium border border-slate-200/60"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </td>

                    {/* Due Date */}
                    <td className="py-3.5 px-4 hidden md:table-cell text-xs text-slate-500">
                      {prob.dueDate ? (
                        <span className="inline-flex items-center gap-1.5 text-slate-700 font-medium">
                          <Calendar className="w-3.5 h-3.5 text-amber-600" />
                          {new Date(prob.dueDate).toLocaleString()}
                        </span>
                      ) : (
                        <span className="text-slate-400">No due date</span>
                      )}
                    </td>

                    {/* Test Cases */}
                    <td className="py-3.5 px-4 hidden lg:table-cell text-xs">
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 bg-slate-100/80 dark:bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-200/60 dark:border-slate-700/60">
                        <FileCheck2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                        <span>{prob.testCases.length} test cases</span>
                      </span>
                    </td>

                    {/* Difficulty */}
                    <td className="py-3.5 px-4">
                      <DifficultyBadge difficulty={prob.difficulty} />
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="inline-flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={() => setSelectedProblemForAnalytics(prob)}
                          title="View Diagnostics & Analytics"
                          className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition-colors cursor-pointer"
                        >
                          <BarChart3 className="w-3.5 h-3.5 text-emerald-600" />
                          <span className="hidden sm:inline">Analytics</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleOpenEditModal(prob)}
                          title="Edit question & test cases"
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-emerald-50 hover:text-emerald-600 transition-colors cursor-pointer"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>

                        <button
                          type="button"
                          onClick={() => handleDeleteProblem(prob)}
                          title="Delete question"
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

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

