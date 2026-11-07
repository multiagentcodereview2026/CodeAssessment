import React, { useEffect, useState } from 'react';
import { CheckCircle2, ChevronRight, Circle, LockKeyhole, Play, Trophy } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';
import { Difficulty } from '../../types';

type Problem = { id: string; title: string; difficulty: Difficulty; available: boolean; completed: boolean; best_score: number | null };
type Step = {
  id: string; title: string; level: string;
  status: 'LOCKED' | 'AVAILABLE' | 'CURRENT' | 'CORE_COMPLETE' | 'MASTERED';
  catalogue_problems: number; completed_problems: number; average_score: number | null;
  core_required_problems: number; core_required_average: number; mastery_required_average: number;
  completed_by_difficulty: Record<Difficulty, number>; core_difficulty_requirements: Record<Difficulty, number>;
  prerequisite_titles: string[]; foundation_prerequisites: string[]; difficulty_mismatches: string[]; problems: Problem[];
};
type Data = {
  enrolled: boolean; steps: Step[]; total_completed_problems: number; total_curated_problems: number; total_curated_topics: number;
  next_problem: { id: string; title: string; difficulty: Difficulty; topic: string; reason: string } | null;
  next_requirement?: { topic: string; problem_id: string } | null;
  core_path_complete: boolean; mastery_complete: boolean;
  foundations: { id: string; title: string; description: string }[];
  level_summaries: { level: string; topics: number; required_problems: number; completed_problems: number; complete: boolean }[];
  overall_milestones: { name: string; target: number; completed: boolean }[];
};
const number = (id: string) => id.match(/(\d+)$/)?.[1] || id;
const card = 'rounded-xl border border-slate-200 bg-white p-5';
const primary = 'inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60';

export const DsaRoadmapView: React.FC<{ embedded?: boolean }> = ({ embedded = false }) => {
  const { authFetch } = useAuth();
  const { openProblemWorkspace } = useApp();
  const navigate = useNavigate();
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const response = await authFetch('/api/student/roadmap', { cache: 'no-store' });
        if (!response.ok) throw new Error('The DSA roadmap could not be loaded.');
        const payload = await response.json();
        if (!cancelled) { setData(payload); setError(''); }
      } catch (cause) {
        if (!cancelled) setError(cause instanceof Error ? cause.message : 'The roadmap could not be loaded.');
      } finally { if (!cancelled) setLoading(false); }
    };
    void load();
    return () => { cancelled = true; };
  }, [authFetch]);
  const start = async () => {
    setStarting(true); setError('');
    try {
      const response = await authFetch('/api/student/roadmap/start', { method: 'POST' });
      if (!response.ok) throw new Error('The roadmap could not be started.');
      setData(await response.json());
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'The roadmap could not be started.'); }
    finally { setStarting(false); }
  };
  const open = (id: string) => { openProblemWorkspace(id); navigate('/problems/' + id); };
  if (loading) return <main className="grid min-h-64 place-items-center text-sm text-slate-500">Loading your DSA roadmap…</main>;
  return <div className={(embedded ? '' : 'mx-auto max-w-5xl pb-12 ') + 'space-y-6'}>
    <header className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-200 pb-6">
      <div><p className="mb-2 text-xs font-semibold uppercase tracking-widest text-indigo-700">Optional learning path</p><h2 className="text-2xl font-bold text-slate-900">DSA Roadmap</h2><p className="mt-2 text-sm text-slate-600">Beginner → Intermediate → Advanced · {data?.total_curated_topics ?? 32} topics · {data?.total_curated_problems ?? 446} curated problems</p></div>
      {!data?.enrolled && <button onClick={start} disabled={starting} className={primary}><Play className="h-4 w-4" />{starting ? 'Starting…' : 'Start roadmap'}</button>}
    </header>
    {error && <p role="alert" className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}
    {!data?.enrolled && <p className="rounded-xl bg-indigo-50 p-5 text-sm text-indigo-800">Follow this path when you want structured guidance. You can still practise any public problem independently.</p>}
    <section className={card}><h3 className="font-bold text-slate-900">Stage 0 · Foundations</h3><p className="mt-2 text-sm text-slate-600">Optional preparation. These learning topics do not add problem completions or scores.</p><div className="mt-4 grid gap-3 sm:grid-cols-3">{data?.foundations?.map(item => <div key={item.id} className="rounded-lg bg-slate-50 p-3"><h4 className="text-sm font-semibold text-slate-900">{item.title}</h4><p className="mt-1 text-xs leading-5 text-slate-600">{item.description}</p></div>)}</div></section>
    <section className="grid gap-3 sm:grid-cols-3" aria-label="Roadmap stages">{data?.level_summaries?.map(stage => <div key={stage.level} className={card}><h3 className="font-semibold text-slate-900">{stage.complete ? '✓ ' : ''}{stage.level}</h3><p className="mt-1 text-xs text-slate-500">{stage.topics} topics · {stage.required_problems} curated problems</p><p className="mt-2 text-sm font-semibold text-indigo-700">{stage.completed_problems}/{stage.required_problems} assessed</p></div>)}</section>
    {data?.enrolled && <section className={card}><p className="font-semibold text-slate-900">{data.total_completed_problems}/{data.total_curated_problems} distinct roadmap problems assessed</p><p className="mt-1 text-xs text-slate-500">Core completion requires all listed problems and a 90% best-score average per topic. Mastery requires 97%.</p><div className="mt-3 flex flex-wrap gap-2">{data.overall_milestones.map(m => <span key={m.name} className={'rounded-full px-3 py-1 text-xs ' + (m.completed ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600')}>{m.completed ? '✓ ' : ''}{m.name} · {m.target}</span>)}</div></section>}
    {data?.enrolled && data.core_path_complete && <p className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">{data.mastery_complete ? 'Roadmap mastered. Every curated topic meets the mastery threshold.' : 'Core roadmap complete. Revisit lower scores toward 97% mastery, or continue in Practice & topics.'}</p>}
    {data?.enrolled && data.next_problem && <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 sm:flex sm:items-center sm:justify-between sm:gap-5"><div><p className="text-xs font-bold uppercase text-emerald-700">Next roadmap problem</p><p className="mt-1 font-mono text-xs text-slate-500">Problem #{number(data.next_problem.id)} · {data.next_problem.id}</p><h3 className="mt-1 text-lg font-bold text-slate-900">{data.next_problem.title}</h3><p className="mt-1 text-sm text-slate-600">{data.next_problem.reason}</p><div className="mt-3 flex items-center gap-2"><span className="text-xs text-slate-600">{data.next_problem.topic}</span><DifficultyBadge difficulty={data.next_problem.difficulty} /></div></div><button onClick={() => open(data.next_problem!.id)} className={primary + ' mt-4 shrink-0 sm:mt-0'}>Start problem<ChevronRight className="h-4 w-4" /></button></section>}
    {data?.enrolled && data.next_requirement && <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-800">The exact curated problem {data.next_requirement.problem_id} is missing from the public catalogue. Its place in {data.next_requirement.topic} is retained.</p>}
    <section className={card}>
      <h3 className="font-bold text-slate-900">Learning path</h3><p className="mb-5 mt-1 text-sm text-slate-500">Open a topic to see its exact problem IDs, ordered Easy → Medium → Hard.</p>
      {data?.steps.map((step, index) => {
        const active = selected === step.id;
        const done = step.status === 'CORE_COMPLETE' || step.status === 'MASTERED';
        const Icon = done ? CheckCircle2 : step.status === 'LOCKED' ? LockKeyhole : Circle;
        const current = step.status === 'CURRENT';
        return <React.Fragment key={step.id}>
          {(index === 0 || data.steps[index - 1].level !== step.level) && <h4 className="mb-3 pt-3 text-xs font-bold uppercase tracking-widest text-slate-500">{step.level}</h4>}
          <div className="relative pb-5 pl-10">
            {index < data.steps.length - 1 && <div className={'absolute left-3 top-6 h-full w-px ' + (done ? 'bg-emerald-500' : 'border-l border-dashed border-slate-300')} />}
            <Icon className={'absolute left-0 top-4 h-6 w-6 rounded-full bg-white ' + (done || current ? 'text-emerald-600' : 'text-slate-400')} />
            <div className={'rounded-lg border ' + (current ? 'border-emerald-200 bg-emerald-50' : 'border-slate-200 bg-white')}>
              <button onClick={() => setSelected(active ? null : step.id)} aria-expanded={active} aria-controls={'topic-' + step.id} className="w-full p-4 text-left">
                <div className="flex flex-wrap justify-between gap-2"><h4 className="font-semibold text-slate-900">{step.title}</h4><span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">{step.status.replaceAll('_', ' ')}</span></div>
                <p className="mt-1 text-xs text-slate-500">{step.catalogue_problems}/{step.core_required_problems} listed problems available</p>
                <div role="progressbar" aria-label={step.title + ' problem coverage'} aria-valuemin={0} aria-valuemax={step.core_required_problems} aria-valuenow={step.completed_problems} className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500" style={{ width: Math.min(100, step.completed_problems / step.core_required_problems * 100) + '%' }} /></div>
                <p className="mt-2 text-xs text-slate-600">{step.completed_problems}/{step.core_required_problems} assessed · {step.average_score == null ? 'No score yet' : step.average_score + '% best-score average'}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">{(['Easy', 'Medium', 'Hard'] as Difficulty[]).map(d => <span key={d} className="rounded border border-slate-200 bg-white px-2 py-1 text-slate-600">{d} {step.completed_by_difficulty[d]}/{step.core_difficulty_requirements[d]}</span>)}</div>
              </button>
              {active && <div id={'topic-' + step.id} className="border-t border-slate-200 px-4 pb-4 pt-3">
                <p className="text-xs leading-5 text-slate-600">Core: all {step.core_required_problems} listed problems with {step.core_required_average}% average. Mastery: the same set with {step.mastery_required_average}% average.</p>
                {step.prerequisite_titles.length > 0 && <p className="mt-1 text-xs text-slate-500">Prerequisites: {step.prerequisite_titles.join(', ')}.</p>}
                {step.foundation_prerequisites.length > 0 && <p className="mt-1 text-xs text-slate-500">Stage 0 preparation: {step.foundation_prerequisites.join(', ')}.</p>}
                {step.difficulty_mismatches.length > 0 && <p className="mt-2 text-xs text-amber-700">Some catalogue difficulty labels differ from the curriculum and need review.</p>}
                <ol className="mt-3 divide-y divide-slate-100">{step.problems.map(p => <li key={p.id}><button disabled={!p.available} onClick={() => open(p.id)} className="flex w-full items-center gap-3 py-3 text-left hover:text-indigo-700 disabled:opacity-50">
                  {p.completed ? <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" /> : <Circle className="h-4 w-4 shrink-0 text-slate-300" />}
                  <span className="min-w-0 flex-1"><span className="block text-xs text-slate-500">Problem #{number(p.id)} · {p.id}</span><span className="block text-sm font-medium text-slate-900">{p.title}</span>{!p.available && <span className="text-xs text-amber-700">Missing from the public bank</span>}</span>
                  {p.best_score != null && <span className="text-xs font-semibold text-emerald-700">{p.best_score}%</span>}<DifficultyBadge difficulty={p.difficulty} />
                </button></li>)}</ol>
              </div>}
            </div>
          </div>
        </React.Fragment>;
      })}
    </section>
    <p className="flex items-start gap-2 text-xs leading-5 text-slate-600"><Trophy className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />Progress uses your highest official independent-practice score for each listed problem. Instructor/course questions are excluded. Practice &amp; topics remains available for additional problems.</p>
  </div>;
};
