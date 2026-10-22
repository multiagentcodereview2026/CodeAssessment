import React, { useEffect, useState } from 'react';
import { CheckCircle2, ChevronRight, Circle, LockKeyhole, Map, Play, Trophy } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';
import { Difficulty } from '../../types';

type RoadmapStep = {
  id: string;
  title: string;
  level: 'Fundamental' | 'Intermediate' | 'Advanced';
  status: 'LOCKED' | 'AVAILABLE' | 'CURRENT' | 'CORE_COMPLETE' | 'MASTERED';
  unlocked: boolean;
  catalogue_problems: number;
  completed_problems: number;
  average_score: number | null;
  core_required_problems: number;
  core_required_average: number;
  completed_by_difficulty: Record<'Easy' | 'Medium' | 'Hard', number>;
  core_difficulty_requirements: Record<'Easy' | 'Medium' | 'Hard', number>;
  mastery_min_problems: number;
  mastery_max_problems: number;
  mastery_required_average: number;
  mastery_difficulty_requirements: Record<'Easy' | 'Medium' | 'Hard', number>;
  prerequisites: string[];
};

type NextProblem = { id: string; title: string; difficulty: string; topic: string; reason: string };
type RoadmapData = { enrolled: boolean; steps: RoadmapStep[]; current_step_id: string | null; next_problem: NextProblem | null; next_requirement?: { topic: string; difficulty: string } | null; total_completed_problems: number; overall_milestones: { name: string; target: number; completed: boolean }[] };

const statusCopy: Record<RoadmapStep['status'], string> = {
  LOCKED: 'Complete prerequisites to unlock',
  AVAILABLE: 'Available to explore',
  CURRENT: 'Current roadmap topic',
  CORE_COMPLETE: 'Core milestone complete',
  MASTERED: 'Mastered',
};

export const DsaRoadmapView: React.FC<{ embedded?: boolean }> = ({ embedded = false }) => {
  const { authFetch } = useAuth();
  const { openProblemWorkspace } = useApp();
  const navigate = useNavigate();
  const [data, setData] = useState<RoadmapData | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [selectedStep, setSelectedStep] = useState<string | null>(null);

  const loadRoadmap = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await authFetch('/api/student/roadmap', { cache: 'no-store' });
      if (!response.ok) throw new Error('The DSA roadmap could not be loaded.');
      setData(await response.json());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The DSA roadmap could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadRoadmap(); }, [authFetch]);

  const startRoadmap = async () => {
    setStarting(true);
    setError('');
    try {
      const response = await authFetch('/api/student/roadmap/start', { method: 'POST' });
      if (!response.ok) throw new Error('The roadmap could not be started.');
      setData(await response.json());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The roadmap could not be started.');
    } finally {
      setStarting(false);
    }
  };

  const startProblem = (problem: NextProblem) => {
    openProblemWorkspace(problem.id);
    navigate(`/problems/${problem.id}`);
  };

  if (loading) return <main className="grid min-h-64 place-items-center text-sm text-slate-500">Loading your DSA roadmap…</main>;

  return <div className={`${embedded ? '' : 'mx-auto max-w-5xl pb-12'} space-y-7`}>
    {!embedded && <header className="flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-indigo-700">Optional learning path</p>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">DSA Roadmap</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">A guided sequence for self-learners. You can still practise any problem or topic whenever you want.</p>
      </div>
      {!data?.enrolled && <button onClick={startRoadmap} disabled={starting} className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"><Play className="h-4 w-4" />{starting ? 'Starting…' : 'Start roadmap'}</button>}
    </header>}

    {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}

    {!data?.enrolled && <section className="rounded-2xl border border-indigo-200 bg-indigo-50/60 p-6">
      <div className="flex gap-3"><Map className="mt-0.5 h-5 w-5 shrink-0 text-indigo-700" /><div><h2 className="font-bold text-slate-900">Start only if you want structured DSA guidance.</h2><p className="mt-1 text-sm leading-6 text-slate-600">The roadmap suggests one next problem, unlocks topics after core milestones, and records mastery. It never locks the regular problem bank.</p></div></div>
    </section>}

    {embedded && <div className="flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between"><div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-indigo-700">Optional learning path</p><h2 className="text-2xl font-bold tracking-tight text-slate-900">DSA Roadmap</h2><p className="mt-2 text-sm text-slate-600">A structured, optional route through the public problem bank.</p></div>{!data?.enrolled && <button onClick={startRoadmap} disabled={starting} className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"><Play className="h-4 w-4" />{starting ? 'Starting…' : 'Start roadmap'}</button>}</div>}

    {data?.enrolled && <section className="rounded-xl border border-slate-200 bg-white p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-sm font-bold text-slate-900">{data.total_completed_problems} distinct problem-bank problems completed</p><p className="mt-1 text-xs text-slate-500">Overall learner milestones are based on distinct official best-score results.</p></div><div className="flex flex-wrap gap-2">{data.overall_milestones.map(milestone => <span key={milestone.name} className={`rounded-full px-2.5 py-1 text-xs font-semibold ${milestone.completed ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{milestone.completed ? '✓ ' : ''}{milestone.name} {milestone.target}+</span>)}</div></div></section>}

    {data?.enrolled && data.next_problem && <section className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-5 sm:flex sm:items-center sm:justify-between sm:gap-5">
      <div><p className="text-xs font-bold uppercase tracking-wide text-emerald-700">Next roadmap problem</p><p className="mt-1 font-mono text-xs text-slate-500">Problem #{data.next_problem.id.match(/(\d+)$/)?.[1] || data.next_problem.id} · ID: {data.next_problem.id}</p><h2 className="mt-1 text-lg font-bold text-slate-900">{data.next_problem.title}</h2><p className="mt-1 text-sm text-slate-600">{data.next_problem.reason}</p><div className="mt-3 flex items-center gap-2"><span className="rounded bg-white px-2 py-1 text-xs text-slate-600">{data.next_problem.topic}</span><DifficultyBadge difficulty={(['Easy', 'Medium', 'Hard'].includes(data.next_problem.difficulty) ? data.next_problem.difficulty : 'Medium') as Difficulty} /></div></div>
      <button onClick={() => startProblem(data.next_problem!)} className="mt-4 inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 sm:mt-0">Start problem <ChevronRight className="h-4 w-4" /></button>
    </section>}
    {data?.enrolled && !data.next_problem && data.next_requirement && <section className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">The roadmap needs a <b>{data.next_requirement.difficulty}</b> problem tagged <b>{data.next_requirement.topic}</b>. No different topic or difficulty was substituted; add a matching public problem-bank item to continue.</section>}

    <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
      <div className="mb-5"><h2 className="text-base font-bold text-slate-900">Learning path</h2><p className="mt-1 text-sm text-slate-500">Core completion needs the exact level-specific Easy/Medium/Hard mix below and a 90% best-score average. Mastery needs 97%.</p></div>
      <div className="space-y-0">
        {data?.steps.map((step, index) => {
          const active = selectedStep === step.id;
          const done = step.status === 'CORE_COMPLETE' || step.status === 'MASTERED';
          const Icon = done ? CheckCircle2 : step.status === 'LOCKED' ? LockKeyhole : Circle;
          const progress = Math.min(100, Math.round((step.completed_problems / step.core_required_problems) * 100));
          const current = step.status === 'CURRENT';
          const showLevel = index === 0 || data.steps[index - 1].level !== step.level;
          return <React.Fragment key={step.id}>{showLevel && <div className="mb-3 pt-2 text-xs font-bold uppercase tracking-[0.12em] text-slate-500">{step.level}</div>}<div className="relative pl-10 pb-5 last:pb-0">
            {index < (data.steps.length - 1) && <div className={`absolute left-[11px] top-6 h-[calc(100%-8px)] w-px ${done ? 'bg-emerald-500' : 'border-l border-dashed border-slate-300'}`} />}
            <button onClick={() => setSelectedStep(active ? null : step.id)} className={`absolute left-0 top-0 grid h-6 w-6 place-items-center rounded-full ${done ? 'bg-emerald-600 text-white' : current ? 'border-4 border-emerald-200 bg-emerald-500 text-white' : 'border-2 border-slate-300 bg-white text-slate-400'}`} aria-label={`Open ${step.title}`}><Icon className="h-3.5 w-3.5" /></button>
            <button onClick={() => setSelectedStep(active ? null : step.id)} className={`w-full rounded-lg border p-4 text-left transition-colors ${current ? 'border-emerald-100 bg-emerald-50' : active ? 'border-slate-300 bg-slate-50' : 'border-transparent bg-white hover:border-slate-200 hover:bg-slate-50'}`}>
              <div className="flex flex-wrap items-center justify-between gap-2"><div><h3 className="font-semibold text-slate-900">{step.title}</h3><p className="mt-1 text-xs text-slate-500">{statusCopy[step.status]} · {step.catalogue_problems} problem-bank problems available</p></div><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${done ? 'bg-emerald-100 text-emerald-700' : step.status === 'CURRENT' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-600'}`}>{step.status.replace('_', ' ')}</span></div>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/80"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${progress}%` }} /></div>
              <p className="mt-2 text-xs text-slate-600">{step.completed_problems} / {step.core_required_problems} core problems · {step.average_score == null ? 'No score yet' : `${step.average_score}% best-score average`}</p>
              <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]"><span className="rounded bg-emerald-50 px-2 py-1 text-emerald-700">Easy {step.completed_by_difficulty.Easy}/{step.core_difficulty_requirements.Easy}</span><span className="rounded bg-amber-50 px-2 py-1 text-amber-700">Medium {step.completed_by_difficulty.Medium}/{step.core_difficulty_requirements.Medium}</span><span className="rounded bg-rose-50 px-2 py-1 text-rose-700">Hard {step.completed_by_difficulty.Hard}/{step.core_difficulty_requirements.Hard}</span></div>
              {active && <div className="mt-3 border-t border-slate-200 pt-3 text-xs leading-5 text-slate-600"><p>Core: {step.core_required_problems} distinct problems, 90% average, and at least {step.core_difficulty_requirements.Easy} Easy / {step.core_difficulty_requirements.Medium} Medium / {step.core_difficulty_requirements.Hard} Hard.</p><p>Mastery target: {step.mastery_min_problems}–{step.mastery_max_problems} distinct problems, {step.mastery_required_average}% average, and balanced difficulty coverage.</p>{step.prerequisites.length > 0 && <p>Prerequisite roadmap steps: {step.prerequisites.join(', ')}.</p>}<p>This topic remains optional; you may open any problem in the regular bank.</p></div>}
            </button>
          </div></React.Fragment>;
        })}
      </div>
    </section>
    <div className="flex items-start gap-2 rounded-xl border border-slate-200 bg-white p-4 text-xs leading-5 text-slate-600"><Trophy className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />Roadmap scores use your highest official evaluated score for each distinct problem. Course/instructor questions are not included.</div>
  </div>;
};
