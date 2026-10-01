import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Award, BookOpen, CheckCircle2, Clock3, Code2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser, studentProgress, submissions } = useApp();
  const solvedPercent = studentProgress.totalProblems > 0
    ? Math.min(100, Math.round(studentProgress.problemsSolved / studentProgress.totalProblems * 100))
    : 0;

  return (
    <main className="mx-auto max-w-7xl space-y-6 pb-12">
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase text-indigo-700">Student workspace</p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">Welcome, {currentUser.name}</h1>
          <p className="mt-1 text-sm text-slate-600">Your saved assessment progress and recent submissions.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => navigate('/courses')} className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-indigo-300">
            <BookOpen className="h-4 w-4" /> My Courses
          </button>
          <button onClick={() => navigate('/problems')} className="inline-flex items-center gap-2 rounded-lg bg-indigo-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-600">
            <Code2 className="h-4 w-4" /> Problem Bank
          </button>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3" aria-label="Assessment summary">
        <article className="border-b border-slate-200 p-4 sm:border-b-0 sm:border-r">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-500"><Award className="h-4 w-4 text-indigo-700" /> Average assessed score</div>
          <p className="mt-3 font-mono text-3xl font-bold text-slate-900">{studentProgress.overallScore == null ? 'N/A' : `${studentProgress.overallScore}%`}</p>
          <p className="mt-1 text-xs text-slate-500">{studentProgress.overallScore == null ? 'No graded submissions yet' : 'Latest assessed attempt per problem'}</p>
        </article>
        <article className="border-b border-slate-200 p-4 sm:border-b-0 sm:border-r">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-500"><CheckCircle2 className="h-4 w-4 text-emerald-700" /> Problems solved</div>
          <p className="mt-3 font-mono text-3xl font-bold text-slate-900">{studentProgress.problemsSolved}<span className="text-base font-medium text-slate-400"> / {studentProgress.totalProblems}</span></p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full bg-emerald-600" style={{ width: `${solvedPercent}%` }} /></div>
        </article>
        <article className="p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-500"><Clock3 className="h-4 w-4 text-amber-700" /> Current streak</div>
          <p className="mt-3 font-mono text-3xl font-bold text-slate-900">{studentProgress.currentStreak}<span className="ml-2 text-base font-medium text-slate-500">days</span></p>
          <p className="mt-1 text-xs text-slate-500">From your saved student profile</p>
        </article>
      </section>

      <section className="border-y border-slate-200">
        <div className="flex items-center justify-between py-4">
          <div>
            <h2 className="font-semibold text-slate-900">Recent submissions</h2>
            <p className="mt-1 text-xs text-slate-500">Persisted assessment history</p>
          </div>
          <button onClick={() => navigate('/submissions')} className="inline-flex items-center gap-1 text-sm font-semibold text-indigo-700 hover:text-indigo-600">View history <ArrowRight className="h-4 w-4" /></button>
        </div>
        {submissions.length === 0 ? (
          <div className="border-t border-slate-100 py-8 text-center text-sm text-slate-500">No submissions yet. Choose a problem to begin.</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {submissions.slice(0, 5).map((submission) => (
              <button key={submission.id} onClick={() => navigate(`/submissions/${encodeURIComponent(submission.id)}`)} className="grid w-full grid-cols-[1fr_auto_auto] items-center gap-4 py-3 text-left hover:bg-slate-50">
                <span className="min-w-0"><span className="block truncate text-sm font-semibold text-slate-900">{submission.problemTitle}</span><span className="mt-0.5 block text-xs text-slate-500">{submission.language} · {submission.date}</span></span>
                <span className="font-mono text-sm font-bold text-slate-800">{submission.score}/100</span>
                <span className="text-xs font-semibold text-slate-600">{submission.status}</span>
              </button>
            ))}
          </div>
        )}
      </section>
    </main>
  );
};
