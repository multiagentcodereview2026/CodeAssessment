import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Award,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  Code2,
  Flame,
  LineChart,
  Sparkles,
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser, studentProgress, submissions, submissionsLoadState, submissionsOwnerId } = useApp();
  const solvedPercent = studentProgress.totalProblems > 0
    ? Math.min(100, Math.round(studentProgress.problemsSolved / studentProgress.totalProblems * 100))
    : 0;
  const recentSubmissions = submissions.slice(0, 5);
  const historyLoadState = submissionsOwnerId === currentUser.id ? submissionsLoadState : 'loading';
  const hasSubmissionHistory = historyLoadState === 'ready' && submissions.length > 0;
  const isFirstVisit = historyLoadState === 'ready' && submissions.length === 0;
  const greetingName = currentUser.name?.trim().split(/\s+/)[0] || 'there';

  return (
    <main className="mx-auto w-full min-w-0 max-w-7xl space-y-7 pb-12">
      <header className="flex min-w-0 flex-col justify-between gap-5 border-b border-slate-200/80 pb-6 sm:flex-row sm:items-end">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-indigo-700">Your learning space</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-[2rem]">{isFirstVisit ? `Welcome, ${greetingName}` : `Welcome back, ${greetingName}`}</h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">{isFirstVisit ? 'Practice coding problems, run your solution, then get clear feedback to help you improve.' : 'A clear view of your progress, recent work, and what to practice next.'}</p>
        </div>
        <div className="flex flex-wrap gap-2.5">
          <button onClick={() => navigate('/analytics')} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
            <LineChart className="h-4 w-4 text-slate-500" /> View my progress
          </button>
          <button onClick={() => navigate('/problems')} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-indigo-700 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
            <Code2 className="h-4 w-4" /> {isFirstVisit ? 'Start practicing' : 'Practice problems'} <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </header>

      {historyLoadState === 'error' && <section role="alert" className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">Your saved activity could not be loaded, so progress is hidden for now. Open Submissions to try loading your history again.</section>}

      {hasSubmissionHistory && <section className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3" aria-label="Assessment summary">
        <article className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 text-sm font-semibold text-slate-600"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50"><Award className="h-[18px] w-[18px] text-indigo-700" /></span>Average score</div>
            <span className="text-[11px] font-medium text-slate-400">Latest per problem</span>
          </div>
          <div className="mt-5 flex items-end justify-between gap-3">
            <p className="font-mono text-4xl font-bold tracking-tight text-slate-900">{studentProgress.overallScore == null ? '—' : `${studentProgress.overallScore}%`}</p>
            <span className="pb-1 text-xs text-slate-500">{studentProgress.overallScore == null ? 'No graded work yet' : 'Keep building'}</span>
          </div>
        </article>

        <article className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 text-sm font-semibold text-slate-600"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50"><CheckCircle2 className="h-[18px] w-[18px] text-emerald-700" /></span>Problems solved</div>
            <span className="text-[11px] font-medium text-slate-400">{solvedPercent}% of bank</span>
          </div>
          <div className="mt-5 flex items-baseline gap-2">
            <p className="font-mono text-4xl font-bold tracking-tight text-slate-900">{studentProgress.problemsSolved}</p>
            <span className="font-mono text-sm text-slate-400">/ {studentProgress.totalProblems}</span>
          </div>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-label="Problems solved" aria-valuenow={solvedPercent} aria-valuemin={0} aria-valuemax={100}>
            <div className="h-full rounded-full bg-emerald-600 transition-[width] duration-500" style={{ width: `${solvedPercent}%` }} />
          </div>
        </article>

        <article className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40 sm:col-span-2 xl:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 text-sm font-semibold text-slate-600"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50"><Flame className="h-[18px] w-[18px] text-amber-700" /></span>Current streak</div>
            <span className="text-[11px] font-medium text-slate-400">Daily practice</span>
          </div>
          <div className="mt-5 flex items-end justify-between gap-3">
            <p className="font-mono text-4xl font-bold tracking-tight text-slate-900">{studentProgress.currentStreak}<span className="ml-2 text-base font-medium text-slate-500">days</span></p>
            <p className="pb-1 text-xs text-slate-500">One step at a time</p>
          </div>
        </article>
      </section>}

      {isFirstVisit ? (
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-200/40">
          <div className="grid gap-7 p-5 sm:p-7 lg:grid-cols-[minmax(0,1fr)_minmax(240px,0.72fr)] lg:items-center">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-800"><Sparkles className="h-3.5 w-3.5" />Your first practice session</span>
              <h2 className="mt-4 text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">Learn by solving, one step at a time</h2>
              <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">Choose a problem and work through it at your own pace. You can run the visible examples before submitting for a full assessment.</p>
              <button onClick={() => navigate('/problems')} className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl bg-indigo-700 px-4 text-sm font-semibold text-white transition hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">Choose your first problem <ArrowRight className="h-4 w-4" /></button>
            </div>
            <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1" aria-label="How practice works">
              {[
                'Choose a problem that interests you',
                'Write code and run the examples',
                'Submit your solution for assessment',
                'Review your score and recommendations'
              ].map((step, index) => <li key={step} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3.5"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-xs font-bold text-indigo-700 ring-1 ring-slate-200">{index + 1}</span><span className="pt-1 text-sm font-medium leading-5 text-slate-700">{step}</span></li>)}
            </ol>
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-slate-100 bg-slate-50 px-5 py-3 text-xs text-slate-600 sm:px-7"><span className="font-semibold text-slate-700">Your first session</span><span>Problem</span><ChevronRight className="h-3.5 w-3.5 text-slate-400" /><span>Code</span><ChevronRight className="h-3.5 w-3.5 text-slate-400" /><span>Run</span><ChevronRight className="h-3.5 w-3.5 text-slate-400" /><span>Submit</span><ChevronRight className="h-3.5 w-3.5 text-slate-400" /><span>Learn</span></div>
        </section>
      ) : historyLoadState === 'loading' ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-6" aria-busy="true"><div className="h-5 w-48 animate-pulse rounded bg-slate-200" /><div className="mt-5 space-y-3"><div className="h-12 animate-pulse rounded-lg bg-slate-100" /><div className="h-12 animate-pulse rounded-lg bg-slate-100" /></div><p className="mt-4 text-sm text-slate-500">Loading your saved activity…</p></section>
      ) : hasSubmissionHistory ? <section className="grid min-w-0 grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(250px,310px)]">
        <div className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-200/40">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4 sm:px-6">
            <div>
              <h2 className="text-base font-bold text-slate-900">Recent submissions</h2>
              <p className="mt-1 text-xs text-slate-500">Your latest assessment activity</p>
            </div>
            <button onClick={() => navigate('/submissions')} className="inline-flex items-center gap-1 text-sm font-semibold text-indigo-700 transition hover:text-indigo-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
              All submissions <ArrowRight className="h-4 w-4" />
            </button>
          </div>
          {recentSubmissions.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100"><Code2 className="h-5 w-5 text-slate-500" /></span>
              <h3 className="mt-4 text-sm font-semibold text-slate-900">Your first solution starts here</h3>
              <p className="mt-1 text-sm text-slate-500">Choose a problem and submit your code to see your progress.</p>
              <button onClick={() => navigate('/problems')} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-800"><Code2 className="h-4 w-4" /> Browse problems</button>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {recentSubmissions.map((submission) => {
                const accepted = /accepted|passed|success/i.test(submission.status);
                return (
                  <button key={submission.id} onClick={() => navigate(`/submissions/${encodeURIComponent(submission.id)}`)} className="group grid w-full min-w-0 grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-2 px-5 py-4 text-left transition hover:bg-slate-50 focus:outline-none focus-visible:bg-indigo-50/60 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:px-6">
                    <span className="flex min-w-0 items-center gap-3">
                      <span className="hidden h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600 sm:flex"><Code2 className="h-4 w-4" /></span>
                      <span className="min-w-0"><span className="block truncate text-sm font-semibold text-slate-900 group-hover:text-indigo-800">{submission.problemTitle}</span><span className="mt-1 block truncate text-xs text-slate-500">{submission.language} <span aria-hidden="true">·</span> {submission.date}</span></span>
                    </span>
                    <span className="justify-self-end text-right"><span className="block font-mono text-sm font-bold text-slate-900">{submission.score}<span className="text-slate-400">/100</span></span><span className={`mt-1 inline-flex items-center gap-1 text-[11px] font-semibold sm:hidden ${accepted ? 'text-emerald-700' : 'text-slate-500'}`}>{accepted && <Check className="h-3 w-3" />}{submission.status}</span></span>
                    <span className={`hidden items-center gap-1.5 justify-self-end rounded-full px-2.5 py-1 text-xs font-semibold sm:inline-flex ${accepted ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>{accepted && <Check className="h-3.5 w-3.5" />}{submission.status}</span>
                    <ChevronRight className="hidden h-4 w-4 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-indigo-600 lg:block" />
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <aside className="grid min-w-0 gap-4 sm:grid-cols-2 lg:grid-cols-1">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50"><LineChart className="h-4 w-4 text-indigo-700" /></span>Your progress</div>
            <div className="mt-5 flex items-end justify-between gap-2"><span className="text-sm text-slate-600">Problem bank completed</span><span className="font-mono text-sm font-bold text-slate-900">{solvedPercent}%</span></div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100" aria-hidden="true"><div className="h-full rounded-full bg-indigo-600" style={{ width: `${solvedPercent}%` }} /></div>
            <p className="mt-3 text-xs leading-5 text-slate-500">{studentProgress.problemsSolved} of {studentProgress.totalProblems} problems solved. Every submission moves you forward.</p>
          </section>

          <section className="relative overflow-hidden rounded-2xl bg-slate-900 p-5 text-white shadow-sm">
            <div className="absolute -right-8 -top-8 h-28 w-28 rounded-full border border-white/10" aria-hidden="true" />
            <div className="relative">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10"><Sparkles className="h-[18px] w-[18px] text-indigo-200" /></span>
              <h2 className="mt-4 text-base font-bold">A little practice goes a long way</h2>
              <p className="mt-2 text-sm leading-6 text-slate-300">Pick a challenge that matches your pace and keep building your skills.</p>
              <button onClick={() => navigate('/problems')} className="mt-5 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold text-slate-900 transition hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-slate-900">Explore problems <ArrowRight className="h-4 w-4" /></button>
            </div>
          </section>
        </aside>
      </section> : null}
    </main>
  );
};
