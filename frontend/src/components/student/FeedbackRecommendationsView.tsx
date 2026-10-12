import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import {
  MessageSquareText,
  Calendar,
  Search,
  BookOpen,
  Target,
  Code2,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/useAuth';
import { DifficultyBadge } from '../common/Badge';
import { Difficulty } from '../../types';

type PracticeProblem = { id: string; title: string; difficulty: string; category: string; reason?: string };
type TopicProgress = { name: string; averageScore: number | null; attempts: number; color: string; nextAction: string };
type RecommendationTopic = { topic: string; average_score: number; assessed_problems: number; reason: string };
type RecommendationProblem = PracticeProblem & { reason: string };
const TOPIC_COLORS = ['#10b981', '#3b82f6', '#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444'];

export const FeedbackRecommendationsView: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { submissions, openAssessmentResult, openProblemWorkspace, activeAssessment } = useApp();
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
  const [recommendationData, setRecommendationData] = useState<{ topics: RecommendationTopic[]; problems: RecommendationProblem[] }>({ topics: [], problems: [] });
  const [recommendationError, setRecommendationError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const loadRecommendations = async () => {
      setRecommendationError('');
      try {
        const response = await authFetch('/api/student/recommendations', { cache: 'no-store' });
        if (!response.ok) throw new Error('Personalized recommendations are temporarily unavailable.');
        const data = await response.json();
        if (cancelled) return;
        setRecommendationData({
          topics: Array.isArray(data.topics) ? data.topics : [],
          problems: Array.isArray(data.problems) ? data.problems : []
        });
      } catch (error) {
        if (!cancelled) setRecommendationError(error instanceof Error ? error.message : 'Personalized recommendations are temporarily unavailable.');
      }
    };
    void loadRecommendations();
    return () => { cancelled = true; };
  }, [authFetch, evaluatedSubmissions.length]);

  const revisionPlan = activeAssessment.scoreProjection.focusAreas.map((area, index) => ({
    title: area,
    detail: activeAssessment.suggestedImprovements[index] || 'Apply the recommendation and resubmit to update your assessment.',
    status: index === 0 ? 'Priority' : index === 1 ? 'Next' : 'Refinement'
  }));

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

  const recommendedTopics = recommendationData.topics.length > 0
    ? recommendationData.topics.map((topic, index) => ({
      name: topic.topic,
      averageScore: Math.round(topic.average_score),
      attempts: topic.assessed_problems,
      color: TOPIC_COLORS[index % TOPIC_COLORS.length],
      nextAction: topic.reason
    }))
    : topicProgress.slice(0, 3);
  const attemptedProblemIds = new Set(evaluatedSubmissions.map(submission => submission.problemId));
  const practiceProblems = useMemo(() => {
    const matching = practiceCatalogue.filter(problem => !selectedTopic || problem.category === selectedTopic);
    const unattempted = matching.filter(problem => !attemptedProblemIds.has(problem.id));
    const candidates = unattempted.length ? unattempted : matching;
    const recommendationById = new Map(recommendationData.problems.map((problem, index) => [problem.id, { ...problem, index }]));
    const ranked = candidates.map(problem => {
      const recommendation = recommendationById.get(problem.id);
      return { ...problem, reason: recommendation?.reason, recommendationIndex: recommendation?.index ?? Number.MAX_SAFE_INTEGER };
    }).sort((a, b) => a.recommendationIndex - b.recommendationIndex);
    if (ranked.length > 0) return ranked.slice(0, 6);
    return selectedTopic ? [] : recommendationData.problems.slice(0, 6);
  }, [practiceCatalogue, selectedTopic, evaluatedSubmissions, recommendationData.problems]);

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
    <div className="mx-auto max-w-7xl space-y-7 pb-12">
      {/* Unified Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-indigo-700">Learning workspace</p>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Feedback &amp; practice
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Review your recent assessments and choose what to work on next.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 self-start rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 sm:self-auto">
          <span>Assessments</span>
          <strong className="font-semibold tabular-nums text-slate-900">{evaluatedSubmissions.length}</strong>
        </div>
      </div>

      {/* Segmented View Controls (Either 'AI Feedback' or 'Practice & Topics') */}
      <div className="flex flex-col gap-4 border-b border-slate-200 md:flex-row md:items-end md:justify-between">
        {/* Binary 2-Tab Switcher */}
        <div className="flex w-full gap-6 md:w-auto">
          <button
            onClick={() => handleSelectTab('feedback')}
            className={`flex items-center gap-2 border-b-2 px-1 pb-3 text-sm font-semibold transition-colors cursor-pointer ${
              activeTab === 'feedback'
                ? 'border-indigo-600 text-indigo-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <MessageSquareText className="h-4 w-4" />
            <span>Assessment feedback</span>
            <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-xs font-medium tabular-nums text-slate-600">
              {evaluatedSubmissions.length}
            </span>
          </button>

          <button
            onClick={() => handleSelectTab('recommendations')}
            className={`flex items-center gap-2 border-b-2 px-1 pb-3 text-sm font-semibold transition-colors cursor-pointer ${
              activeTab === 'recommendations'
                ? 'border-indigo-600 text-indigo-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Target className="h-4 w-4" />
            <span>Practice &amp; topics</span>
            <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-xs font-medium tabular-nums text-slate-600">
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
              className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
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
          <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Continue learning</span>
                {latestSubmission ? <>
                  <h3 className="mt-1 text-base font-bold text-slate-900">Continue with {latestSubmission.problemTitle}</h3>
                  <p className="mt-1 text-xs text-slate-500 leading-relaxed">Your latest saved assessment scored {latestSubmission.score}/100. Open its report for the feedback and next steps from that evaluation.</p>
                </> : <>
                  <h3 className="mt-1 text-base font-bold text-slate-900">Start your first practice problem</h3>
                  <p className="mt-1 text-xs text-slate-500 leading-relaxed">Your saved evaluations and topic progress will appear here after you submit a solution.</p>
                </>}
              </div>
              {latestSubmission ? <div className="flex gap-2">
                <button onClick={() => handleOpenReport(latestSubmission.id)} className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50">
                  <BookOpen className="h-4 w-4" /><span>View latest report</span>
                </button>
                <button onClick={() => handleStartPractice(latestSubmission.problemId)} className="flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700">
                  <Code2 className="h-4 w-4" /><span>Practice again</span>
                </button>
              </div> : <button onClick={() => navigate('/problems')} className="flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700">
                <Code2 className="h-4 w-4" /><span>Browse problems</span>
              </button>}
            </div>
          </div>

          {revisionPlan.length > 0 && <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Suggested next steps</span>
                <h3 className="mt-1 text-base font-bold text-slate-900">
                  Raise {activeAssessment.problemTitle} from {activeAssessment.scoreProjection.currentScore} to {activeAssessment.scoreProjection.projectedScore}
                </h3>
                <p className="mt-1 text-xs text-slate-500 leading-relaxed">Focus areas are based on your latest assessment.</p>
              </div>
              <button onClick={() => handleStartPractice(activeAssessment.problemId)} className="flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700">
                <Code2 className="h-4 w-4" /><span>Revise solution</span>
              </button>
            </div>
            <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-3">
              {revisionPlan.map(item => <div key={item.title} className="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
                <span className="text-[11px] font-semibold uppercase tracking-wide text-indigo-700">{item.status}</span>
                <h4 className="mt-1 text-sm font-semibold text-slate-900">{item.title}</h4>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{item.detail}</p>
              </div>)}
            </div>
          </div>}

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquareText className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-semibold text-slate-900">Recent assessments</h3>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              {filteredSubmissions.length} Submissions Logged
            </span>
          </div>

          <div className="space-y-3">
            {filteredSubmissions.length === 0 ? (
              <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">
                No assessments match your search.
              </div>
            ) : (
              filteredSubmissions.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleOpenReport(item.id)}
                  className="group flex cursor-pointer flex-col items-start justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 transition-colors hover:border-indigo-300 hover:bg-slate-50/50 sm:flex-row sm:items-center sm:p-5"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 rounded-lg bg-indigo-50 p-3 text-indigo-700">
                      <MessageSquareText className="h-4 w-4" />
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-sm font-semibold text-slate-900 group-hover:text-indigo-700 sm:text-base">
                          {item.problemTitle}
                        </h3>
                        <span className="flex items-center gap-1 text-xs text-slate-500">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          {item.date}
                        </span>
                        <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                          {item.language}
                        </span>
                      </div>

                      <p className="text-sm leading-relaxed text-slate-600">
                        {item.feedbackSummary || (item.status === 'Passed'
                          ? 'All test cases passed. Open the report for the full evaluation.'
                          : 'Open the report to review the test results and evaluation feedback.')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end sm:self-center flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                    <div className={`flex items-center gap-1 rounded-lg px-2.5 py-1.5 font-mono text-xs font-semibold ${
                      item.score >= 85 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                      item.score >= 70 ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
                      item.score >= 60 ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                      'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      <span>{item.score} / 100</span>
                    </div>

                    <button
                      onClick={() => handleOpenReport(item.id)}
                      className="flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 transition-colors hover:border-indigo-300 hover:bg-white hover:text-indigo-700"
                    >
                      <BookOpen className="h-3.5 w-3.5" />
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
          {recommendationError && <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{recommendationError} Your saved assessment history is still available below.</p>}
          {/* Recommended Topic Clusters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recommendedTopics.map((topic) => (
              <button key={topic.name} onClick={() => setSelectedTopic(topic.name)} className={`rounded-xl border bg-white p-4 text-left transition-colors ${selectedTopic === topic.name ? 'border-indigo-400 bg-indigo-50/40' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-800">{topic.name}</span>
                  <span className={`text-xs font-semibold tabular-nums ${topic.averageScore == null ? 'text-slate-500' : topic.averageScore < 70 ? 'text-amber-700' : 'text-emerald-700'}`}>{topic.averageScore == null ? 'Not tried' : `${topic.averageScore}% avg.`}</span>
                </div>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100">
                  {topic.averageScore != null && <div className="h-full rounded-full" style={{ width: `${topic.averageScore}%`, backgroundColor: topic.color }} />}
                </div>
                <p className="mt-3 text-xs leading-relaxed text-slate-600">{topic.attempts ? `${topic.attempts} problem${topic.attempts === 1 ? '' : 's'} attempted. ` : ''}{topic.nextAction}</p>
              </button>
            ))}
          </div>

          {/* Recommended Topic Clusters */}
          <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-600" />
                <h3 className="text-base font-semibold text-slate-900">All topics</h3>
              </div>
              <button onClick={() => setSelectedTopic('')} className="text-xs text-indigo-600 font-medium hover:underline">Show all topics</button>
            </div>

            <div className="flex flex-wrap gap-2">
              {topicProgress.map((topic) => (
                <button key={topic.name} onClick={() => setSelectedTopic(topic.name)} className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${selectedTopic === topic.name ? 'border-indigo-400 bg-indigo-50 text-indigo-700' : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'}`}>
                  {topic.name}<span className="ml-2 text-slate-400">{topic.averageScore == null ? 'New' : `Avg ${topic.averageScore}%`}</span>
                </button>
              ))}
              {!catalogueLoading && topicProgress.length === 0 && <p className="text-sm text-slate-500">No topics are available yet.</p>}
            </div>
          </div>

          {/* Targeted Practice Problems */}
          <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-indigo-600" />
                <h3 className="text-base font-semibold text-slate-900">Suggested problems</h3>
              </div>
                <span className="text-xs text-slate-500">{selectedTopic || 'All topics'}</span>
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
                  className="group flex flex-col justify-between space-y-4 rounded-lg border border-slate-200 bg-white p-4 transition-colors hover:border-indigo-300 hover:bg-slate-50/50"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-slate-500">Problem {idx + 1}</span>
                      <DifficultyBadge difficulty={(['Easy', 'Medium', 'Hard'].includes(prob.difficulty) ? prob.difficulty : 'Medium') as Difficulty} />
                    </div>
                    <h4 className="text-sm font-semibold text-slate-900 group-hover:text-indigo-700">
                      {prob.title}
                    </h4>
                    <div className="flex flex-wrap gap-1 mt-2">
                      <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">{prob.category}</span>
                    </div>
                    {prob.reason && <p className="mt-2 text-[11px] text-slate-500">{prob.reason}</p>}
                  </div>

                  <button
                    onClick={() => handleStartPractice(prob.id)}
                    className="flex w-full cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
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
