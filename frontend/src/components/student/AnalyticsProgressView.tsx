import React from 'react';
import { useApp } from '../../context/AppContext';
import { ScoreTrendLineChart } from '../common/ChartComponents';

export const AnalyticsProgressView: React.FC = () => {
  const { studentProgress } = useApp();
  const totalAssessed = studentProgress.scoreTrend.length;

  return (
    <main className="mx-auto max-w-6xl space-y-6 pb-12">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-xs font-bold uppercase text-indigo-700">Your account</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Analytics & Progress</h1>
        <p className="mt-1 text-sm text-slate-600">Metrics use your saved assessed submissions. Independent practice and course assignments are both included in your personal history.</p>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        <article className="border-b border-slate-200 p-4 sm:border-b-0 sm:border-r">
          <p className="text-sm text-slate-500">Average score</p>
          <p className="mt-2 font-mono text-3xl font-bold text-slate-900">{studentProgress.overallScore == null ? 'N/A' : `${studentProgress.overallScore}%`}</p>
          <p className="mt-1 text-xs text-slate-500">Latest assessed attempt per problem</p>
        </article>
        <article className="border-b border-slate-200 p-4 sm:border-b-0 sm:border-r">
          <p className="text-sm text-slate-500">Problems solved</p>
          <p className="mt-2 font-mono text-3xl font-bold text-slate-900">{studentProgress.problemsSolved} / {studentProgress.totalProblems}</p>
          <p className="mt-1 text-xs text-slate-500">At least one assessed attempt scoring 70 or higher</p>
        </article>
        <article className="p-4">
          <p className="text-sm text-slate-500">Current streak</p>
          <p className="mt-2 font-mono text-3xl font-bold text-slate-900">{studentProgress.currentStreak} days</p>
          <p className="mt-1 text-xs text-slate-500">Saved student profile value</p>
        </article>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <article className="min-w-0 border-y border-slate-200 py-5">
          <h2 className="font-semibold text-slate-900">Assessed score trend</h2>
          <p className="mt-1 text-xs text-slate-500">{totalAssessed} latest-per-problem data points</p>
          {totalAssessed ? <div className="mt-4"><ScoreTrendLineChart data={studentProgress.scoreTrend} height={220} /></div> : <p className="py-12 text-center text-sm text-slate-500">No graded submissions yet.</p>}
        </article>

        <article className="border-y border-slate-200 py-5">
          <h2 className="font-semibold text-slate-900">Assessment dimensions</h2>
          <p className="mt-1 text-xs text-slate-500">Scores returned by completed assessments</p>
          {studentProgress.categoryWiseScores.length === 0 ? <p className="py-12 text-center text-sm text-slate-500">No dimension scores available yet.</p> : (
            <div className="mt-4 space-y-4">
              {studentProgress.categoryWiseScores.map((category) => (
                <div key={category.name}>
                  <div className="mb-1 flex items-center justify-between text-sm"><span className="text-slate-700">{category.name}</span><strong className="font-mono text-slate-900">{category.scoreDisplay}</strong></div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full" style={{ width: `${Math.max(0, Math.min(100, category.percentage))}%`, backgroundColor: category.color }} /></div>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>

      <section className="border-y border-slate-200 py-5">
        <h2 className="font-semibold text-slate-900">Topics to review</h2>
        <p className="mt-1 text-xs text-slate-500">Only topics with at least three assessed problems and an average below 70 are listed.</p>
        {studentProgress.weakTopics.length === 0 ? <p className="py-6 text-sm text-slate-500">No topics meet the review threshold yet.</p> : <ul className="mt-3 flex flex-wrap gap-2">{studentProgress.weakTopics.map((topic) => <li key={topic} className="border-b border-amber-300 px-2 py-2 text-sm text-slate-800">{topic}</li>)}</ul>}
      </section>
    </main>
  );
};
