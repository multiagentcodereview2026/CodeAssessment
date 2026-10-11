import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import {
  MessageSquareText,
  Sparkles,
  Calendar,
  Search,
  BookOpen,
  Target,
  Code2,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';
import { Difficulty } from '../../types';
import { useAuth } from '../../context/useAuth';

type PracticeProblem = { id: string; title: string; difficulty: string; category: string };
type TopicProgress = { name: string; averageScore: number | null; attempts: number; color: string; nextAction: string };
const TOPIC_COLORS = ['#10b981', '#3b82f6', '#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444'];

export const FeedbackRecommendationsView: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { submissions, openAssessmentResult, openProblemWorkspace } = useApp();
  const { authFetch } = useAuth();

  // Tab State: 'feedback' | 'recommendations' (Strict binary toggle)
  const initialTab = searchParams.get('tab') === 'practice' ? 'recommendations' : 'feedback';
  const [activeTab, setActiveTab] = useState<'feedback' | 'recommendations'>(initialTab);
  const [search, setSearch] = useState('');
  const [practiceCatalogue, setPracticeCatalogue] = useState<PracticeProblem[]>([]);
  const [catalogueLoading, setCatalogueLoading] = useState(true);
  const [catalogueError, setCatalogueError] = useState('');
  const [catalogueRetry, setCatalogueRetry] = useState(0);
  const [selectedTopic, setSelectedTopic] = useState('');
  const evaluatedSubmissions = useMemo(() => submissions.filter(submission => submission.evaluationStatus === 'EVALUATED'), [submissions]);

  useEffect(() => {
    setActiveTab(new URLSearchParams(location.search).get('tab') === 'practice' ? 'recommendations' : 'feedback');
  }, [location.search]);

  useEffect(() => {
    let cancelled = false;
    const loadCatalogue = async () => {
      setCatalogueLoading(true);
      setCatalogueError('');
      try {
        const response = await authFetch('/api/problems', { cache: 'no-store' });
        if (!response.ok) throw new Error('Practice problems could not be loaded.');
        const records = await response.json();
        if (!Array.isArray(records)) throw new Error('The practice catalogue returned an invalid response.');
        if (!cancelled) setPracticeCatalogue(records.map((problem: any) => ({
          id: String(problem.id),
          title: String(problem.title || problem.id),
          difficulty: String(problem.difficulty || 'Medium'),
          category: String(problem.category || 'Algorithms')
        })));
      } catch (error) {
        if (!cancelled) setCatalogueError(error instanceof Error ? error.message : 'Practice problems could not be loaded.');
      } finally {
        if (!cancelled) setCatalogueLoading(false);
      }
    };
    void loadCatalogue();
    return () => { cancelled = true; };
  }, [authFetch, catalogueRetry]);

  const topicProgress = useMemo<TopicProgress[]>(() => {
    const attemptsByCategory = new Map<string, Map<string, number>>();
    const categoryByProblem = new Map(practiceCatalogue.map(problem => [problem.id, problem.category]));
    // Keep only each problem's latest score so repeated submissions do not
    // give one problem disproportionate weight in the category average.
    const latestProblemScores = new Map<string, number>();
    for (const submission of evaluatedSubmissions) {
      if (!latestProblemScores.has(submission.problemId)) latestProblemScores.set(submission.problemId, submission.score);
    }
    for (const [problemId, score] of latestProblemScores) {
      const category = categoryByProblem.get(problemId);
      if (!category) continue;
      if (!attemptsByCategory.has(category)) attemptsByCategory.set(category, new Map());
      attemptsByCategory.get(category)!.set(problemId, score);
    }
    const categoryProblemCounts = new Map<string, number>();
    for (const problem of practiceCatalogue) categoryProblemCounts.set(problem.category, (categoryProblemCounts.get(problem.category) || 0) + 1);
    const categories = [...categoryProblemCounts.keys()];
    return categories.map((name, index) => {
      const attempts = attemptsByCategory.get(name);
      const mastery = attempts?.size
        ? Math.round([...attempts.values()].reduce((total, score) => total + score, 0) / attempts.size)
        : null;
      return {
        name,
        averageScore: mastery,
        attempts: attempts?.size || 0,
        color: TOPIC_COLORS[index % TOPIC_COLORS.length],
        nextAction: mastery == null
          ? 'Start a problem in this topic to establish your progress.'
          : mastery < 70
            ? 'Your recent average is below 70. Practice another problem in this topic.'
            : 'Your recent average is 70 or higher. Try a harder problem in this topic.'
      };
    }).sort((a, b) => {
      if (a.averageScore == null && b.averageScore != null) return 1;
      if (b.averageScore == null && a.averageScore != null) return -1;
      if (a.averageScore != null && b.averageScore != null && a.averageScore !== b.averageScore) return a.averageScore - b.averageScore;
      return (categoryProblemCounts.get(b.name) || 0) - (categoryProblemCounts.get(a.name) || 0) || a.name.localeCompare(b.name);
    });
  }, [practiceCatalogue, evaluatedSubmissions]);

  const recommendedTopics = topicProgress.slice(0, 3);
  const attemptedProblemIds = new Set(evaluatedSubmissions.map(submission => submission.problemId));
  const practiceProblems = useMemo(() => {
    const matching = practiceCatalogue.filter(problem => !selectedTopic || problem.category === selectedTopic);
    const unattempted = matching.filter(problem => !attemptedProblemIds.has(problem.id));
    return (unattempted.length ? unattempted : matching).slice(0, 6);
  }, [practiceCatalogue, selectedTopic, evaluatedSubmissions]);

  const handleSelectTab = (tab: 'feedback' | 'recommendations') => {
    setActiveTab(tab);
    const params = new URLSearchParams(location.search);
    if (tab === 'recommendations') params.set('tab', 'practice');
    else params.delete('tab');
    navigate({ pathname: location.pathname, search: params.toString() ? `?${params.toString()}` : '' }, { replace: true });
  };

  const latestSubmission = evaluatedSubmissions[0];

  const filteredSubmissions = evaluatedSubmissions.filter((s) =>
    s.problemTitle.toLowerCase().includes(search.toLowerCase()) ||
    (s.feedbackSummary && s.feedbackSummary.toLowerCase().includes(search.toLowerCase())) ||
    s.language.toLowerCase().includes(search.toLowerCase())
  );

  const handleOpenReport = (subId: string) => {
    openAssessmentResult(subId);
    navigate(`/submissions/${encodeURIComponent(subId)}`);
  };

  const handleStartPractice = (probId: string) => {
    openProblemWorkspace(probId);
    navigate(`/problems/${probId}`);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Unified Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            AI Feedback & Recommendations
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Personalized algorithmic coaching, explainable evaluation history, and adaptive practice path.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600 bg-white px-3.5 py-2.5 rounded-2xl border border-slate-200 shadow-xs">
            Evaluated Submissions: <strong className="text-indigo-600 font-mono text-sm ml-1">{evaluatedSubmissions.length}</strong>
          </span>
        </div>
      </div>

      {/* Segmented View Controls (Either 'AI Feedback' or 'Practice & Topics') */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Binary 2-Tab Switcher */}
        <div className="flex bg-slate-200/60 p-1.5 rounded-2xl border border-slate-200/80 max-w-md w-full md:w-auto">
          <button
            onClick={() => handleSelectTab('feedback')}
            className={`flex-1 md:flex-initial py-2.5 px-5 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
              activeTab === 'feedback'
                ? 'bg-white text-indigo-600 shadow-sm shadow-indigo-100'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <MessageSquareText className="w-3.5 h-3.5" />
            <span>AI Feedback</span>
            <span className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono font-bold ${activeTab === 'feedback' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'}`}>
              {evaluatedSubmissions.length}
            </span>
          </button>

          <button
            onClick={() => handleSelectTab('recommendations')}
            className={`flex-1 md:flex-initial py-2.5 px-5 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
              activeTab === 'recommendations'
                ? 'bg-white text-indigo-600 shadow-sm shadow-indigo-100'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            <span>Practice & Topics</span>
            <span className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono font-bold ${activeTab === 'recommendations' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'}`}>
              {practiceProblems.length}
            </span>
          </button>
        </div>

        {/* Search Bar (Only shown on Feedback tab) */}
        {activeTab === 'feedback' && (
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search feedback notes or code..."
              className="w-full pl-10 pr-4 py-2.5 text-xs bg-white border border-slate-200 rounded-2xl focus:outline-none focus:border-indigo-500 shadow-xs"
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
        )}
      </div>

      {/* TAB 1: AI FEEDBACK */}
      {activeTab === 'feedback' && (
        <div className="space-y-4">
          <div className="bg-white rounded-3xl border border-indigo-200/80 p-5 sm:p-6 shadow-xs">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div>
                <span className="text-xs font-extrabold uppercase text-indigo-700">Continue learning</span>
                {latestSubmission ? <>
                  <h3 className="mt-1 text-base font-bold text-slate-900">Continue with {latestSubmission.problemTitle}</h3>
                  <p className="mt-1 text-xs text-slate-500 leading-relaxed">Your latest saved assessment scored {latestSubmission.score}/100. Open its report for the feedback and next steps from that evaluation.</p>
                </> : <>
                  <h3 className="mt-1 text-base font-bold text-slate-900">Start your first practice problem</h3>
                  <p className="mt-1 text-xs text-slate-500 leading-relaxed">Your saved evaluations and topic progress will appear here after you submit a solution.</p>
                </>}
              </div>
              {latestSubmission ? <div className="flex gap-2">
                <button onClick={() => handleOpenReport(latestSubmission.id)} className="px-4 py-2.5 rounded-xl border border-indigo-200 text-indigo-700 hover:bg-indigo-50 text-xs font-bold flex items-center justify-center gap-2 cursor-pointer">
                  <Sparkles className="w-3.5 h-3.5" /><span>View latest report</span>
                </button>
                <button onClick={() => handleStartPractice(latestSubmission.problemId)} className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold flex items-center justify-center gap-2 cursor-pointer">
                  <Code2 className="w-3.5 h-3.5" /><span>Practice again</span>
                </button>
              </div> : <button onClick={() => navigate('/problems')} className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold flex items-center justify-center gap-2 cursor-pointer">
                <Code2 className="w-3.5 h-3.5" /><span>Browse problems</span>
              </button>}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquareText className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Recent AI Coaching & Evaluations</h3>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              {filteredSubmissions.length} Submissions Logged
            </span>
          </div>

          <div className="space-y-3">
            {filteredSubmissions.length === 0 ? (
              <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
                No feedback notes found matching your search.
              </div>
            ) : (
              filteredSubmissions.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleOpenReport(item.id)}
                  className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs hover:border-indigo-300 card-hover transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group cursor-pointer"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3.5 bg-indigo-50 text-indigo-600 rounded-2xl flex-shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                      <MessageSquareText className="w-5 h-5" />
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                          {item.problemTitle}
                        </h3>
                        <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          {item.date}
                        </span>
                        <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                          {item.language}
                        </span>
                      </div>

                      <p className="text-xs text-slate-600 leading-relaxed font-sans">
                        {item.feedbackSummary || (item.status === 'Passed'
                          ? 'All test cases passed. Open the report for the full evaluation.'
                          : 'Open the report to review the test results and evaluation feedback.')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end sm:self-center flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                    <div className={`px-3 py-1.5 rounded-xl font-mono font-bold text-xs flex items-center gap-1 ${
                      item.score >= 85 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                      item.score >= 70 ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
                      item.score >= 60 ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                      'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      <span>{item.score} / 100</span>
                    </div>

                    <button
                      onClick={() => handleOpenReport(item.id)}
                      className="px-4 py-2 bg-slate-900 hover:bg-indigo-600 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer active:scale-95"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Full Report</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 2: PRACTICE & TOPICS */}
      {activeTab === 'recommendations' && (
        <div className="space-y-6">
          {/* Recommended Topic Clusters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recommendedTopics.map((topic) => (
              <button key={topic.name} onClick={() => setSelectedTopic(topic.name)} className={`text-left bg-white rounded-2xl border p-5 shadow-xs transition-colors ${selectedTopic === topic.name ? 'border-indigo-400 ring-2 ring-indigo-100' : 'border-slate-200/80 hover:border-indigo-300'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold text-slate-700">{topic.name}</span>
                  <span className={`text-xs font-mono font-bold ${topic.averageScore == null ? 'text-slate-500' : topic.averageScore < 70 ? 'text-amber-700' : 'text-emerald-700'}`}>{topic.averageScore == null ? 'Not tried' : `Avg ${topic.averageScore}%`}</span>
                </div>
                <div className="mt-3 h-2 rounded-full bg-slate-100 overflow-hidden">
                  {topic.averageScore != null && <div className="h-full rounded-full" style={{ width: `${topic.averageScore}%`, backgroundColor: topic.color }} />}
                </div>
                <p className="mt-3 text-[11px] text-slate-500 leading-relaxed">{topic.attempts ? `${topic.attempts} problem${topic.attempts === 1 ? '' : 's'} attempted. ` : ''}{topic.nextAction}</p>
              </button>
            ))}
          </div>

          {/* Recommended Topic Clusters */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Recommended Topic Clusters</h3>
              </div>
              <button onClick={() => setSelectedTopic('')} className="text-xs text-indigo-600 font-medium hover:underline">Show all topics</button>
            </div>

            <div className="flex flex-wrap gap-2">
              {topicProgress.map((topic) => (
                <button key={topic.name} onClick={() => setSelectedTopic(topic.name)} className={`rounded-xl border px-3 py-2 text-xs font-semibold transition-colors ${selectedTopic === topic.name ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-indigo-300'}`}>
                  {topic.name}<span className="ml-2 text-slate-400">{topic.averageScore == null ? 'New' : `Avg ${topic.averageScore}%`}</span>
                </button>
              ))}
              {!catalogueLoading && topicProgress.length === 0 && <p className="text-sm text-slate-500">No topics are available yet.</p>}
            </div>
          </div>

          {/* Targeted Practice Problems */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Targeted Practice Problems</h3>
              </div>
              <span className="text-xs text-slate-500">{selectedTopic || 'Showing all topics'}</span>
            </div>

            {catalogueLoading ? <p className="py-6 text-center text-sm text-slate-500">Loading practice problems…</p>
              : catalogueError ? <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{catalogueError}<button onClick={() => setCatalogueRetry(value => value + 1)} className="ml-2 font-bold underline">Retry</button></div>
              : practiceProblems.length === 0 ? <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-center">
                <p className="text-sm font-semibold text-slate-700">No practice problems found for this topic.</p>
                <button onClick={() => setSelectedTopic('')} className="mt-2 text-xs font-bold text-indigo-600 hover:underline">Show recommended problems</button>
              </div>
              : <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{practiceProblems.map((prob, idx) => (
                <div
                  key={prob.id}
                  className="p-5 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-4 hover:border-indigo-400 hover:bg-white transition-all group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold font-mono text-slate-400">#{idx + 1}</span>
                      <DifficultyBadge difficulty={(['Easy', 'Medium', 'Hard'].includes(prob.difficulty) ? prob.difficulty : 'Medium') as Difficulty} />
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                      {prob.title}
                    </h4>
                    <div className="flex flex-wrap gap-1 mt-2">
                      <span className="text-[10px] bg-slate-200/60 text-slate-700 px-1.5 py-0.5 rounded">{prob.category}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleStartPractice(prob.id)}
                    className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-xs flex items-center justify-center gap-1.5 transition-all hover:scale-105 active:scale-95 cursor-pointer"
                  >
                    <Code2 className="w-3.5 h-3.5" />
                    <span>Start Practice</span>
                  </button>
                </div>
              ))}</div>}
          </div>
        </div>
      )}
    </div>
  );
};
