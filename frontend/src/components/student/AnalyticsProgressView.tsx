import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart as LineChartIcon,
  PieChart as PieChartIcon,
  TrendingUp,
  Award,
  Zap,
  Target,
  CheckCircle2,
  BookOpen,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { CircularGauge } from '../common/CircularGauge';
import { ScoreTrendLineChart, CategoryDonutChart } from '../common/ChartComponents';
import { TOPIC_MASTERY, RUBRIC_AGENTS } from '../../data/learningInsights';

export const AnalyticsProgressView: React.FC = () => {
  const navigate = useNavigate();
  const { studentProgress } = useApp();
  const [timeframe, setTimeframe] = useState<'month' | 'semester' | 'all'>('month');

  const topicMastery = TOPIC_MASTERY;
  const lowestTopic = [...topicMastery].sort((a, b) => a.mastery - b.mastery)[0];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Unified Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Analytics & Learning Progress
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Comprehensive algorithmic performance diagnostics, syllabus completion, and 5D rubric evaluation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value as any)}
            className="bg-white border border-slate-200 text-xs font-semibold text-slate-700 rounded-2xl px-3.5 py-2.5 shadow-xs focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="month">This Month (May)</option>
            <option value="semester">Spring Semester 2026</option>
            <option value="all">All-Time Cumulative</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-amber-200/80 p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-extrabold uppercase text-amber-700">Next Study Sprint</span>
            <h2 className="mt-1 text-lg font-extrabold text-slate-900">{lowestTopic.name}</h2>
            <p className="mt-1 text-xs text-slate-500 leading-relaxed">
              Mastery is currently {lowestTopic.mastery}%. {lowestTopic.nextAction}
            </p>
          </div>
          <button
            onClick={() => navigate('/feedback?tab=practice')}
            className="px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>Open Practice Plan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
          <span className="text-xs font-extrabold uppercase text-slate-500">Evaluator Coverage</span>
          <div className="mt-3 grid grid-cols-5 gap-1.5">
            {RUBRIC_AGENTS.map((agent) => (
              <div key={agent.key} className="h-9 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-[10px] font-bold text-indigo-700">
                {agent.key.slice(0, 2).toUpperCase()}
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] text-slate-500 leading-relaxed">
            Every submission is explained through five independent evaluator outputs.
          </p>
        </div>
      </div>

      {/* TOP SECTION: Syllabus Completion & Key Quantitative Metrics */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
          {/* Left: Progress Gauge */}
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <CircularGauge
              score={studentProgress.progressPercent}
              maxScore={100}
              size={130}
              strokeWidth={10}
              color="#3b82f6"
              showPercent
              sublabel="Progress"
            />
            <div className="text-center sm:text-left space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Syllabus Mastery
              </span>
              <h2 className="text-2xl font-extrabold text-slate-900">
                Your Learning Progress
              </h2>
              <p className="text-xs text-slate-500 max-w-xs leading-relaxed">
                You are pacing 14% faster than average cohort completion benchmarks.
              </p>
            </div>
          </div>

          {/* Right: 4 Key Metric Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full lg:w-auto">
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Score</span>
                <Award className="w-4 h-4 text-indigo-600" />
              </div>
              <span className="text-xl font-extrabold text-slate-900 font-mono block">
                {studentProgress.overallScore} <span className="text-xs text-slate-400 font-normal">/100</span>
              </span>
              <span className="text-[11px] text-slate-500 font-medium block">Average</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Rank</span>
                <Zap className="w-4 h-4 text-purple-600" />
              </div>
              <span className="text-xl font-extrabold text-purple-700 font-mono block">
                #6
              </span>
              <span className="text-[11px] text-slate-500 font-medium block">of 48 Students</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Solved</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              </div>
              <span className="text-xl font-extrabold text-slate-900 font-mono block">
                {studentProgress.problemsSolved} <span className="text-xs text-slate-400 font-normal">/ {studentProgress.totalProblems}</span>
              </span>
              <span className="text-[11px] text-slate-500 font-medium block">{studentProgress.topicsCovered} Topics Done</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Time</span>
                <Clock className="w-4 h-4 text-amber-600" />
              </div>
              <span className="text-xl font-extrabold text-slate-900 font-mono block">
                {studentProgress.hoursSpent}
              </span>
              <span className="text-[11px] text-slate-500 font-medium block">Total Sandbox</span>
            </div>
          </div>
        </div>
      </div>

      {/* MIDDLE SECTION: Progress Over Time Trend & 5D Category Weighting Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Overall Score Trend (Col span 7) */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <LineChartIcon className="w-4 h-4 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Score & Skill Progression Trend</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">Apr 1 – Apr 29, 2026</span>
          </div>

          <div className="pt-2">
            <ScoreTrendLineChart data={studentProgress.scoreTrend} height={210} />
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Starting baseline: <strong className="font-mono text-slate-700">65/100</strong></span>
            <span>Current peak: <strong className="font-mono text-emerald-600">85/100</strong></span>
          </div>
        </div>

        {/* Right: Category Wise Scores Donut Chart (Col span 5) */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2">
                <PieChartIcon className="w-4 h-4 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Category Wise Scores</h3>
              </div>
              <span className="text-xs text-indigo-600 font-semibold bg-indigo-50 px-2 py-0.5 rounded-md">5D Weighting</span>
            </div>

            <CategoryDonutChart categories={studentProgress.categoryWiseScores} />
          </div>

          <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/70 text-xs text-slate-600 flex items-center gap-2.5">
            <Target className="w-4 h-4 text-indigo-600 flex-shrink-0" />
            <span>High correctness & code quality drive 56.3% of cumulative rating.</span>
          </div>
        </div>
      </div>

      {/* BOTTOM SECTION: Topic Mastery & Multi-Agent Rubric Diagnostic */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Topic Mastery Breakdown (Col span 6) */}
        <div className="lg:col-span-6 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Topic Mastery Breakdown</h3>
              </div>
              <Sparkles className="w-4 h-4 text-purple-600" />
            </div>

            <div className="space-y-3.5 mt-4">
              {topicMastery.map((topic, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700">{topic.name}</span>
                    <span className="font-mono font-bold text-slate-800">{topic.mastery}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${topic.mastery}%`, backgroundColor: topic.color }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => navigate('/feedback?tab=practice')}
            className="w-full mt-4 py-2.5 text-xs font-bold text-indigo-600 hover:text-indigo-700 bg-indigo-50/70 hover:bg-indigo-100 rounded-2xl transition-all text-center flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <span>Practice Low Mastery Topics</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Right: Multi-Agent Rubric Diagnostic Matrix (Col span 6) */}
        <div className="lg:col-span-6 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Multi-Agent Rubric Diagnostic</h3>
            </div>
            <span className="text-xs text-slate-400 font-medium">5 Evaluator Agents</span>
          </div>

          <div className="space-y-2.5 mt-2">
            {studentProgress.categoryWiseScores.map((cat, i) => (
              <div key={i} className="p-3.5 rounded-2xl border border-slate-100 bg-slate-50/60 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color }} />
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">{cat.name}</h4>
                    <p className="text-[11px] text-slate-500 leading-tight">
                      {cat.name === 'Correctness' && 'Sandbox assertions pass rate'}
                      {cat.name === 'Time Complexity' && 'Asymptotic Big-O runtime profile'}
                      {cat.name === 'Space Complexity' && 'Auxiliary memory & bucket allocation'}
                      {cat.name === 'Code Quality' && 'Clean architecture & syntax style'}
                      {cat.name === 'Similarity (Originality)' && 'AST uniqueness vs cohort code'}
                    </p>
                  </div>
                </div>

                <span className="text-xs font-mono font-extrabold text-slate-800 bg-white px-2.5 py-1 rounded-xl border border-slate-200/80 shadow-xs flex-shrink-0">
                  {cat.scoreDisplay}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
