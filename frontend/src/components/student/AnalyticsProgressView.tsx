import React, { useEffect, useState } from 'react';
import { AlertCircle, ArrowRight, Award, CheckCircle2, Flame, LineChart, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';
import { ScoreTrendLineChart } from '../common/ChartComponents';

type TrendPoint = { date: string; score: number };
type Dimension = { name: string; percentage: number; scoreDisplay: string; color?: string };
type AnalyticsData = {
  overallScore: number | null;
  problemsSolved: number;
  totalProblems: number;
  currentStreak: number;
  weakTopics: string[];
  scoreTrend: TrendPoint[];
  categoryWiseScores: Dimension[];
};

export const AnalyticsProgressView: React.FC = () => {
  const { user, authFetch } = useAuth();
  const navigate = useNavigate();
  const [studentProgress, setStudentProgress] = useState<AnalyticsData | null>(null);
  const [error, setError] = useState('');
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    setError('');
    setStudentProgress(null);
    authFetch(`/api/analytics/student/${encodeURIComponent(user.id)}/practice`, { cache: 'no-store' })
      .then(async (response) => {
        if (!response.ok) throw new Error('Independent-practice analytics could not be loaded. Try again in a moment.');
        return response.json();
      })
      .then((data) => {
        if (cancelled) return;
        setStudentProgress({
          overallScore: data.overall_score == null ? null : Number(data.overall_score),
          problemsSolved: Number(data.problems_solved || 0),
          totalProblems: Number(data.total_problems || 0),
          currentStreak: Number(data.streak_days || 0),
          weakTopics: Array.isArray(data.weak_topics) ? data.weak_topics : [],
          scoreTrend: Array.isArray(data.score_trend) ? data.score_trend.filter((point: any) => Number.isFinite(Number(point.score))).map((point: any) => ({ date: String(point.date), score: Number(point.score) })) : [],
          categoryWiseScores: Array.isArray(data.category_breakdown) ? data.category_breakdown.filter((item: any) => item.value != null && Number.isFinite(Number(item.value))).map((item: any) => ({ ...item, percentage: Math.max(0, Math.min(100, Number(item.value))), scoreDisplay: `${Number(item.value).toFixed(1)}%` })) : [],
        });
      })
      .catch((loadError) => { if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'Analytics could not be loaded.'); });
    return () => { cancelled = true; };
  }, [authFetch, user, retryKey]);

  if (error) return (
    <main className="mx-auto w-full max-w-7xl py-8">
      <section role="alert" className="flex flex-col items-start gap-4 rounded-xl border border-rose-200 bg-white dark:bg-[#1a0808] dark:border-rose-500/40 dark:text-rose-200 p-6 sm:flex-row sm:items-center">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-50 dark:bg-rose-950/40"><AlertCircle className="h-5 w-5 text-rose-700 dark:text-rose-400" /></span>
        <div className="flex-1"><h1 className="font-semibold text-slate-900 dark:text-zinc-100">Analytics unavailable</h1><p className="mt-1 text-sm text-slate-600 dark:text-zinc-400">{error}</p></div>
        <button onClick={() => setRetryKey((value) => value + 1)} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-300 dark:border-white/12 px-3 text-sm font-semibold text-slate-700 dark:text-zinc-200 hover:bg-slate-50 dark:hover:bg-[#16161d] cursor-pointer"><RefreshCw className="h-4 w-4" /> Try again</button>
      </section>
    </main>
  );
  if (!studentProgress) return <main className="mx-auto w-full max-w-7xl py-8" aria-busy="true"><div className="h-8 w-56 animate-pulse rounded bg-slate-200 dark:bg-white/10"/><div className="mt-6 grid gap-4 sm:grid-cols-3"><div className="h-28 animate-pulse rounded-xl bg-white dark:bg-[#121217]"/><div className="h-28 animate-pulse rounded-xl bg-white dark:bg-[#121217]"/><div className="h-28 animate-pulse rounded-xl bg-white dark:bg-[#121217]"/></div><p className="mt-5 text-sm text-slate-500 dark:text-zinc-400">Loading your practice analytics…</p></main>;

  const totalAssessed = studentProgress.scoreTrend.length;
  const solvedPercent = studentProgress.totalProblems > 0 ? Math.min(100, Math.round(studentProgress.problemsSolved / studentProgress.totalProblems * 100)) : 0;

  return (
    <main className="mx-auto w-full min-w-0 max-w-7xl space-y-6 pb-12 animate-fadeIn">
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 dark:border-white/10 pb-5 sm:flex-row sm:items-end">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-[0.14em] text-indigo-500 dark:text-indigo-400">Independent practice</span>
          <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">Analytics &amp; progress</h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-2xl">A view of your personal practice results. Instructor-assigned coursework is available in My Courses.</p>
        </div>
        <button onClick={() => navigate('/courses')} className="inline-flex min-h-10 items-center gap-2 self-start rounded-xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] px-4 py-2.5 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-neutral-800 shadow-xs transition-all hover:scale-105 active:scale-95 cursor-pointer sm:self-auto">View coursework <ArrowRight className="h-4 w-4" /></button>
      </header>

      <section className="grid min-w-0 gap-4 sm:grid-cols-3" aria-label="Practice summary">
        <article className="rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 sm:p-6 shadow-xs card-hover"><div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-[0.14em] text-indigo-600 dark:text-indigo-400"><Award className="h-4 w-4 text-indigo-600 dark:text-indigo-400"/>Average score</div><p className="mt-4 font-mono text-3xl font-extrabold text-slate-900 dark:text-white">{studentProgress.overallScore == null ? '—' : `${studentProgress.overallScore.toFixed(1)}%`}</p><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Latest assessed attempt per problem</p></article>
        <article className="rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 sm:p-6 shadow-xs card-hover"><div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-[0.14em] text-emerald-600 dark:text-emerald-400"><CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400"/>Problems solved</div><p className="mt-4 font-mono text-3xl font-extrabold text-slate-900 dark:text-white">{studentProgress.problemsSolved}<span className="ml-2 text-base font-medium text-slate-400">/ {studentProgress.totalProblems}</span></p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${solvedPercent}%` }}/></div></article>
        <article className="rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 sm:p-6 shadow-xs card-hover"><div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-[0.14em] text-amber-600 dark:text-amber-400"><Flame className="h-4 w-4 text-amber-600 dark:text-amber-400"/>Current streak</div><p className="mt-4 font-mono text-3xl font-extrabold text-slate-900 dark:text-white">{studentProgress.currentStreak}<span className="ml-2 text-base font-medium text-slate-400">days</span></p><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Consecutive days with assessed practice</p></article>
      </section>

      <section className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(300px,1fr)]">
        <article className="min-w-0 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 sm:p-6 shadow-xs">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 dark:border-white/10 pb-4"><div><div className="flex items-center gap-2"><LineChart className="h-4 w-4 text-indigo-600 dark:text-indigo-400"/><h2 className="font-bold text-slate-900 dark:text-white text-base">Score trend</h2></div><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Latest assessment for each problem</p></div><span className="text-xs font-mono text-slate-400">{totalAssessed} {totalAssessed === 1 ? 'problem' : 'problems'} assessed</span></div>
          {totalAssessed >= 2 ? <div className="mt-4 min-w-0"><ScoreTrendLineChart data={studentProgress.scoreTrend} height={260}/></div> : <div className="grid min-h-64 place-items-center px-4 text-center"><div><span className="mx-auto flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 dark:bg-white/10"><LineChart className="h-5 w-5 text-slate-500 dark:text-slate-400"/></span><p className="mt-3 text-sm font-bold text-slate-800 dark:text-slate-200">More results will reveal your trend</p><p className="mt-1 max-w-sm text-xs leading-5 text-slate-500 dark:text-slate-400">{totalAssessed === 0 ? 'Complete an assessment to begin your score history.' : 'Complete one more assessment to compare results over time.'}</p><button onClick={() => navigate('/problems')} className="mt-3 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer">Browse problems <ArrowRight className="inline h-3.5 w-3.5"/></button></div></div>}
        </article>

        <article className="min-w-0 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 sm:p-6 shadow-xs">
          <div className="border-b border-slate-100 dark:border-white/10 pb-4"><h2 className="font-bold text-slate-900 dark:text-white text-base">Assessment dimensions</h2><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Averages from available completed assessments</p></div>
          {studentProgress.categoryWiseScores.length === 0 ? <div className="grid min-h-64 place-items-center px-4 text-center"><div><p className="text-sm font-bold text-slate-800 dark:text-slate-200">No dimension scores yet</p><p className="mt-1 max-w-xs text-xs leading-5 text-slate-500 dark:text-slate-400">Dimension breakdowns appear after an assessment returns those results.</p></div></div> : <div className="mt-5 space-y-5">{studentProgress.categoryWiseScores.map((category) => <div key={category.name}><div className="mb-2 flex items-center justify-between gap-3 text-xs font-medium"><span className="text-slate-700 dark:text-slate-300 font-bold">{category.name}</span><strong className="font-mono text-slate-900 dark:text-white">{category.scoreDisplay}</strong></div><div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10"><div className="h-full rounded-full" style={{ width: `${category.percentage}%`, backgroundColor: category.color || '#4f46e5' }}/></div></div>)}</div>}
        </article>
      </section>

      <section className="rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 sm:p-6 shadow-xs">
        <div className="border-b border-slate-100 dark:border-white/10 pb-4"><h2 className="font-bold text-slate-900 dark:text-white text-base">Topics to review</h2><p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">Topics with enough assessed problems to identify a consistent practice gap.</p></div>
        {studentProgress.weakTopics.length === 0 ? <div className="flex items-start gap-3 py-6"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-950/50"><CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400"/></span><div><p className="text-xs font-bold text-slate-800 dark:text-slate-200">No review topics identified</p><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Keep practicing. We’ll show a topic here when your assessment history supports a recommendation.</p></div></div> : <ul className="mt-4 flex flex-wrap gap-2">{studentProgress.weakTopics.map((topic) => <li key={topic} className="rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/30 px-3.5 py-1.5 text-xs font-bold text-amber-900 dark:text-amber-300 font-sans">{topic}</li>)}</ul>}
      </section>
    </main>
  );
};
