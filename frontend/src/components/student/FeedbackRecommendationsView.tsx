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
    <div className="mx-auto max-w-7xl space-y-7 pb-12">
      {/* Unified Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-indigo-700">Learning workspace</p>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Feedback &amp; learning
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Choose targeted practice or follow the optional self-learning DSA roadmap.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 self-start rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 sm:self-auto">
          <span>Assessments</span>
          <strong className="font-semibold tabular-nums text-slate-900">{evaluatedSubmissions.length}</strong>
        </div>
      </div>

      <div className="flex gap-2 border-b border-slate-200"><button onClick={() => setWorkspaceTab('practice')} className={`border-b-2 px-4 py-3 text-sm font-semibold ${!roadmapTab ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-500 hover:text-slate-800'}`}>Practice &amp; topics</button><button onClick={() => setWorkspaceTab('roadmap')} className={`border-b-2 px-4 py-3 text-sm font-semibold ${roadmapTab ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-500 hover:text-slate-800'}`}>DSA Roadmap</button></div>

      {roadmapTab ? <DsaRoadmapView embedded /> : <div className="space-y-6">
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
                      <span className="text-xs font-medium text-slate-500">Problem #{prob.id.match(/(\d+)$/)?.[1] || prob.id}</span>
                      <DifficultyBadge difficulty={(['Easy', 'Medium', 'Hard'].includes(prob.difficulty) ? prob.difficulty : 'Medium') as Difficulty} />
                    </div>
                    <h4 className="text-sm font-semibold text-slate-900 group-hover:text-indigo-700">
                      {prob.title}
                    </h4>
                    <div className="flex flex-wrap gap-1 mt-2">
                      <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">{prob.topic || prob.category}</span>
                      <span className="rounded bg-indigo-50 px-2 py-1 text-xs text-indigo-700">Problem bank</span>
                      <span className="font-mono text-[11px] text-slate-400">ID: {prob.id}</span>
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
      </div>}
    </div>
  );
};
