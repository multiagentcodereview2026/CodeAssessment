import React, { useState } from 'react';
import {
  TrendingUp,
  CheckCircle2,
  BookOpen,
  Clock,
  Sparkles,
  Award,
  ChevronDown
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { CircularGauge } from '../common/CircularGauge';
import { ScoreTrendLineChart } from '../common/ChartComponents';

export const StudentProgressView: React.FC = () => {
  const { studentProgress, setCurrentView } = useApp();
  const [timeframe, setTimeframe] = useState<'month' | 'semester' | 'all'>('month');

  const topicMastery = [
    { name: 'Arrays & Two Pointers', mastery: 95, color: '#10b981' },
    { name: 'Hash Map & Lookup', mastery: 90, color: '#3b82f6' },
    { name: 'Trees & DFS/BFS', mastery: 75, color: '#8b5cf6' },
    { name: 'Linked Lists & Pointers', mastery: 80, color: '#06b6d4' },
    { name: 'Graphs & Topological Sort', mastery: 50, color: '#f59e0b' },
    { name: 'Dynamic Programming & Memo', mastery: 45, color: '#ef4444' }
  ];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Learning Progress
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Syllabus mastery tracking and automated skill progression.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value as any)}
              className="bg-white border border-slate-200 text-xs font-semibold text-slate-700 rounded-xl px-3 py-2 pr-8 focus:outline-none focus:border-indigo-500"
            >
              <option value="month">This Month (May)</option>
              <option value="semester">Spring Semester 2026</option>
              <option value="all">All-Time Cumulative</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Stats Card (Matches Step 8 in diagram) */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
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
                Syllabus Completion
              </span>
              <h2 className="text-2xl font-extrabold text-slate-900">
                Your Progress
              </h2>
              <p className="text-xs text-slate-500 max-w-xs">
                You are pacing 14% faster than average cohort completion rates.
              </p>
            </div>
          </div>

          {/* Right: 3 Key Quantitative Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full lg:w-auto">
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-center gap-3.5">
              <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-xl">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Problems Solved
                </span>
                <span className="text-lg font-extrabold text-slate-900 font-mono">
                  {studentProgress.problemsSolved} <span className="text-xs text-slate-400">/ {studentProgress.totalProblems}</span>
                </span>
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-center gap-3.5">
              <div className="p-2.5 bg-indigo-100 text-indigo-700 rounded-xl">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Topics Covered
                </span>
                <span className="text-lg font-extrabold text-slate-900 font-mono">
                  {studentProgress.topicsCovered} <span className="text-xs text-slate-400">/ {studentProgress.totalTopics}</span>
                </span>
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-center gap-3.5">
              <div className="p-2.5 bg-purple-100 text-purple-700 rounded-xl">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Hours Spent
                </span>
                <span className="text-lg font-extrabold text-slate-900 font-mono">
                  {studentProgress.hoursSpent}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Over Time Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Progress Over Time</h3>
            </div>
            <span className="text-xs font-mono text-slate-400">Apr 1 – Apr 29</span>
          </div>

          <ScoreTrendLineChart data={studentProgress.scoreTrend} height={200} />
        </div>

        {/* Topic Mastery breakdown */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900">Topic Mastery</h3>
            <Sparkles className="w-4 h-4 text-purple-600" />
          </div>

          <div className="space-y-3.5">
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

          <button
            onClick={() => setCurrentView('recommendations')}
            className="w-full mt-2 py-2 text-xs font-bold text-indigo-600 hover:text-indigo-700 bg-indigo-50/50 hover:bg-indigo-50 rounded-xl transition-colors text-center"
          >
            Practice Low Mastery Topics →
          </button>
        </div>
      </div>
    </div>
  );
};
