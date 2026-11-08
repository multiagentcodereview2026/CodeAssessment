import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Target,
  Code2
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/useAuth';
import { DifficultyBadge } from '../common/Badge';
import { Difficulty } from '../../types';
import { DsaRoadmapView } from './DsaRoadmapView';

type PracticeProblem = { id: string; title: string; difficulty: string; category: string; topic_tags?: string[]; topic?: string; reason?: string };
type TopicProgress = { name: string; averageScore: number | null; attempts: number; color: string; nextAction: string };
type RecommendationTopic = { topic: string; average_score: number | null; assessed_problems: number; reason: string };
type RecommendationProblem = PracticeProblem & { reason: string };
const TOPIC_COLORS = ['#10b981', '#3b82f6', '#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444'];

export const FeedbackRecommendationsView: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { submissions, openProblemWorkspace } = useApp();
  const { authFetch } = useAuth();

  const [practiceCatalogue, setPracticeCatalogue] = useState<PracticeProblem[]>([]);
  const [catalogueLoading, setCatalogueLoading] = useState(true);
  const [catalogueError, setCatalogueError] = useState('');
  const [catalogueRetry, setCatalogueRetry] = useState(0);
  const [selectedTopic, setSelectedTopic] = useState('');
  const roadmapTab = new URLSearchParams(location.search).get('tab') === 'roadmap';
  const setWorkspaceTab = (tab: 'practice' | 'roadmap') => {
    const params = new URLSearchParams(location.search);
    if (tab === 'roadmap') params.set('tab', 'roadmap'); else params.delete('tab');
    navigate({ pathname: '/feedback', search: params.toString() ? `?${params}` : '' });
  };
  const evaluatedSubmissions = useMemo(() => submissions.filter(submission => submission.evaluationStatus === 'EVALUATED'), [submissions]);
  const [recommendationData, setRecommendationData] = useState<{ topics: RecommendationTopic[]; priorityTopics: string[]; problems: RecommendationProblem[] }>({ topics: [], priorityTopics: [], problems: [] });
  const [recommendationError, setRecommendationError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const loadRecommendations = async () => {
      setRecommendationError('');
      try {
        const query = selectedTopic ? `?topic=${encodeURIComponent(selectedTopic)}` : '';
        const response = await authFetch(`/api/student/recommendations${query}`, { cache: 'no-store' });
        if (!response.ok) throw new Error('Personalized recommendations are temporarily unavailable.');
        const data = await response.json();
        if (cancelled) return;
        setRecommendationData({
          topics: Array.isArray(data.topics) ? data.topics : [],
          priorityTopics: Array.isArray(data.priority_topics) ? data.priority_topics : [],
          problems: Array.isArray(data.problems) ? data.problems : []
        });
      } catch (error) {
        if (!cancelled) setRecommendationError(error instanceof Error ? error.message : 'Personalized recommendations are temporarily unavailable.');
      }
    };
    void loadRecommendations();
    return () => { cancelled = true; };
  }, [authFetch, evaluatedSubmissions.length, selectedTopic]);

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
          category: String(problem.category || 'Algorithms'),
          topic_tags: Array.isArray(problem.topic_tags) && problem.topic_tags.length
            ? problem.topic_tags.map(String)
            : [String(problem.category || 'Algorithms')]
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

  const topicProgress = useMemo<TopicProgress[]>(() => recommendationData.topics.map((topic, index) => ({
    name: topic.topic,
    averageScore: topic.average_score == null ? null : Math.round(topic.average_score),
    attempts: topic.assessed_problems,
    color: TOPIC_COLORS[index % TOPIC_COLORS.length],
    nextAction: topic.reason,
  })), [recommendationData.topics]);

  const recommendedTopics = recommendationData.priorityTopics
    .map(name => topicProgress.find(topic => topic.name === name))
    .filter((topic): topic is TopicProgress => Boolean(topic));
  const practiceProblems = useMemo(() => {
    const matching = selectedTopic
      ? recommendationData.problems.filter(problem => problem.topic === selectedTopic)
      : recommendationData.problems.filter(problem => recommendationData.priorityTopics.includes(problem.topic || ''));
    return matching.slice(0, 6);
  }, [selectedTopic, recommendationData]);

  const handleStartPractice = (probId: string) => {
    openProblemWorkspace(probId);
    navigate(`/problems/${probId}`);
  };

  return (
    <div className="mx-auto max-w-7xl space-y-7 pb-12 animate-fadeIn">
      {/* Unified Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 dark:border-white/10 pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-[0.14em] text-indigo-500 dark:text-indigo-400">Learning workspace</span>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white mt-1">
            Feedback &amp; learning
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Choose targeted practice or follow the optional self-learning DSA roadmap.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 self-start rounded-xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] px-3.5 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 shadow-2xs sm:self-auto">
          <span>Assessments</span>
          <strong className="font-extrabold font-mono text-indigo-600 dark:text-indigo-400 ml-1">{evaluatedSubmissions.length}</strong>
        </div>
      </div>

      <div className="flex gap-6 border-b border-slate-200 dark:border-white/10">
        <button
          onClick={() => setWorkspaceTab('practice')}
          className={`border-b-2 px-1 pb-3 text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
            !roadmapTab
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Practice &amp; topics
        </button>
        <button
          onClick={() => setWorkspaceTab('roadmap')}
          className={`border-b-2 px-1 pb-3 text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
            roadmapTab
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          DSA Roadmap
        </button>
      </div>

      {roadmapTab ? <DsaRoadmapView embedded /> : <div className="space-y-6">
          {recommendationError && <p className="rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 px-4 py-3 text-xs text-amber-800 dark:text-amber-300 font-semibold">{recommendationError} Your saved assessment history is still available below.</p>}
          {/* Recommended Topic Clusters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recommendedTopics.map((topic) => (
              <button key={topic.name} onClick={() => setSelectedTopic(topic.name)} className={`rounded-2xl border p-5 text-left transition-all cursor-pointer card-hover ${selectedTopic === topic.name ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/40' : 'border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] hover:border-indigo-300 dark:hover:border-white/20'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-800 dark:text-white">{topic.name}</span>
                  <span className={`text-xs font-mono font-bold ${topic.averageScore == null ? 'text-slate-500' : topic.averageScore < 70 ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>{topic.averageScore == null ? 'Not tried' : `${topic.averageScore}% avg.`}</span>
                </div>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10">
                  {topic.averageScore != null && <div className="h-full rounded-full" style={{ width: `${topic.averageScore}%`, backgroundColor: topic.color }} />}
                </div>
                <p className="mt-3 text-xs leading-relaxed text-slate-600 dark:text-slate-400">{topic.attempts ? `${topic.attempts} problem${topic.attempts === 1 ? '' : 's'} attempted. ` : ''}{topic.nextAction}</p>
              </button>
            ))}
          </div>

          {/* All topics */}
          <div className="space-y-4 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 sm:p-6 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-white/10">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">All topics</h3>
              </div>
              <button onClick={() => setSelectedTopic('')} className="text-xs text-indigo-600 dark:text-indigo-400 font-bold hover:underline cursor-pointer">Show all topics</button>
            </div>

            <div className="flex flex-wrap gap-2">
              {topicProgress.map((topic) => (
                <button key={topic.name} onClick={() => setSelectedTopic(topic.name)} className={`rounded-xl border px-3 py-2 text-xs font-semibold transition-all cursor-pointer ${selectedTopic === topic.name ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300' : 'border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-white/20'}`}>
                  {topic.name}<span className="ml-2 font-mono text-[11px] text-slate-400">{topic.averageScore == null ? 'New' : `Avg ${topic.averageScore}%`}</span>
                </button>
              ))}
              {!catalogueLoading && topicProgress.length === 0 && <p className="text-xs text-slate-500 dark:text-slate-400">No topics are available yet.</p>}
            </div>
          </div>

          {/* Targeted Practice Problems */}
          <div className="space-y-4 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 sm:p-6 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-white/10">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Suggested problems</h3>
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">{selectedTopic || 'All topics'}</span>
            </div>

            {catalogueLoading ? <p className="py-6 text-center text-xs text-slate-500 dark:text-slate-400">Loading practice problems…</p>
              : catalogueError ? <div className="rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50 dark:bg-rose-950/20 p-4 text-xs text-rose-700 dark:text-rose-400 font-semibold">{catalogueError}<button onClick={() => setCatalogueRetry(value => value + 1)} className="ml-2 font-bold underline cursor-pointer">Retry</button></div>
              : practiceProblems.length === 0 ? <div className="rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-[#16161d] p-6 text-center">
                <p className="text-xs font-bold text-slate-700 dark:text-slate-300">No practice problems found for this topic.</p>
                <button onClick={() => setSelectedTopic('')} className="mt-2 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer">Show recommended problems</button>
              </div>
              : <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{practiceProblems.map((prob) => (
                <div
                  key={prob.id}
                  className="group flex flex-col justify-between space-y-4 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#16161d] p-5 shadow-xs card-hover"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono text-slate-500 dark:text-slate-400">#{prob.id.match(/(\d+)$/)?.[1] || prob.id}</span>
                      <DifficultyBadge difficulty={(['Easy', 'Medium', 'Hard'].includes(prob.difficulty) ? prob.difficulty : 'Medium') as Difficulty} />
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      {prob.title}
                    </h4>
                    <div className="flex flex-wrap gap-1.5 mt-2.5">
                      <span className="rounded-md bg-slate-100 dark:bg-white/10 px-2 py-0.5 text-[11px] font-medium text-slate-600 dark:text-slate-300">{prob.topic || prob.category}</span>
                      <span className="rounded-md bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 text-[11px] font-semibold text-indigo-700 dark:text-indigo-300">Problem bank</span>
                    </div>
                    {prob.reason && <p className="mt-2.5 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{prob.reason}</p>}
                  </div>

                  <button
                    onClick={() => handleStartPractice(prob.id)}
                    className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 py-2.5 text-xs font-bold text-white shadow-md shadow-indigo-600/20 transition-all active:scale-95 ring-1 ring-white/20"
                  >
                    <Code2 className="w-3.5 h-3.5" />
                    <span>Start Practice</span>
                  </button>
                </div>
              ))}</div>}
          </div>
      </div>}
    </div>
  );
};
