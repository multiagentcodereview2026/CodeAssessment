import React from 'react';
import {
  LineChart as LineChartIcon,
  PieChart as PieChartIcon,
  TrendingUp,
  Award,
  Zap,
  Target
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreTrendLineChart, CategoryDonutChart } from '../common/ChartComponents';

export const ScoresAnalytics: React.FC = () => {
  const { studentProgress } = useApp();

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Performance & Score Analytics
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          In-depth evaluation analytics across rubric agents and historical performance progression.
        </p>
      </div>

      {/* Top 3 Metric Callouts */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Cumulative Average
            </span>
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {studentProgress.overallScore} <span className="text-xs text-slate-400 font-normal">/ 100</span>
            </span>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Score Growth
            </span>
            <span className="text-2xl font-extrabold text-emerald-600 font-mono">
              +20.0% <span className="text-xs text-slate-400 font-normal">since Apr 1</span>
            </span>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Cohort Percentile
            </span>
            <span className="text-2xl font-extrabold text-purple-700 font-sans">
              Top 12% <span className="text-xs text-slate-400 font-normal">Rank #6/48</span>
            </span>
          </div>
        </div>
      </div>

      {/* Grid: Score Trend & Category-Wise Scores Donut (Matches diagram) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Overall Score Trend (Col span 7) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <LineChartIcon className="w-4 h-4 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Overall Score Trend</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">Apr 1 – Apr 29, 2026</span>
          </div>

          <div className="pt-2">
            <ScoreTrendLineChart data={studentProgress.scoreTrend} height={200} />
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Starting baseline: <strong className="font-mono text-slate-700">65/100</strong></span>
            <span>Current peak: <strong className="font-mono text-emerald-600">85/100</strong></span>
          </div>
        </div>

        {/* Right: Category Wise Scores Donut Chart (Col span 5) */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2">
                <PieChartIcon className="w-4 h-4 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Category Wise Scores</h3>
              </div>
              <span className="text-xs text-indigo-600 font-semibold">5D Weighting</span>
            </div>

            <CategoryDonutChart categories={studentProgress.categoryWiseScores} />
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 flex items-center gap-2">
            <Target className="w-4 h-4 text-indigo-600 flex-shrink-0" />
            <span>High correctness & code quality weights drive 56.3% of cumulative rating.</span>
          </div>
        </div>
      </div>

      {/* Detailed Rubric Dimension Matrix */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900">Multi-Agent Rubric Diagnostic</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {studentProgress.categoryWiseScores.map((cat, i) => (
            <div key={i} className="p-4 rounded-xl border border-slate-100 bg-slate-50/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                <span className="text-xs font-mono font-bold text-slate-700">{cat.scoreDisplay}</span>
              </div>
              <h4 className="text-xs font-bold text-slate-800">{cat.name}</h4>
              <p className="text-[11px] text-slate-500">
                {cat.name === 'Correctness' && 'Sandbox assertions pass rate'}
                {cat.name === 'Time Complexity' && 'Asymptotic Big-O runtime profile'}
                {cat.name === 'Space Complexity' && 'Auxiliary memory & bucket alloc'}
                {cat.name === 'Code Quality' && 'Clean architecture & syntax style'}
                {cat.name === 'Similarity (Originality)' && 'AST uniqueness vs cohort code'}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
