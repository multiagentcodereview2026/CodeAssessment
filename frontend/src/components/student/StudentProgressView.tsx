import React, { useState } from 'react';
import {
  TrendingUp,
  CheckCircle2,
  BookOpen,
  Clock,
  Sparkles,
  Award,
  GraduationCap,
  Code2,
  Calendar,
  Layers,
  ArrowRight,
  Flame
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { CircularGauge } from '../common/CircularGauge';
import { ScoreTrendLineChart } from '../common/ChartComponents';
import { DifficultyBadge } from '../common/Badge';

export const StudentProgressView: React.FC = () => {
  const { studentProgress, problems, openProblemWorkspace } = useApp();
  // Strictly only 2 independent modes: 'assigned' (Instructor Coursework) vs 'practice' (Self-Paced Practice). NO 'all' tab.
  const [activeTab, setActiveTab] = useState<'assigned' | 'practice'>('assigned');

  // Breakdown metrics
  const assignedProblems = problems.filter(p => p.origin === 'instructor_assigned');
  const practiceProblems = problems.filter(p => p.origin !== 'instructor_assigned');

  const assignedSolved = assignedProblems.filter(p => p.studentStatus === 'Submitted').length;
  const practiceSolved = practiceProblems.filter(p => p.studentStatus === 'Submitted').length;

  const courseworkTopics = [
    { name: 'Arrays & Two Pointers', mastery: 95, color: '#10b981', count: '2/2 Solved' },
    { name: 'Hash Map & Lookup', mastery: 90, color: '#3b82f6', count: '1/1 Solved' },
    { name: 'Linked Lists & Pointers', mastery: 80, color: '#06b6d4', count: '1/1 Solved' }
  ];

  const practiceTopics = [
    { name: 'Trees & DFS/BFS', mastery: 75, color: '#8b5cf6', count: '4 Solved' },
    { name: 'Graphs & Topological Sort', mastery: 50, color: '#f59e0b', count: '3 Solved' },
    { name: 'Dynamic Programming & Memo', mastery: 45, color: '#ef4444', count: '2 Solved' }
  ];

  const currentTopics = activeTab === 'assigned' ? courseworkTopics : practiceTopics;
  const displayedProblems = activeTab === 'assigned' ? assignedProblems : practiceProblems;

  const courseworkTrend = [
    { date: 'Assignment 1', score: 70 },
    { date: 'Assignment 2', score: 85 }
  ];

  const practiceTrend = [
    { date: 'Week 1', score: 65 },
    { date: 'Week 2', score: 75 },
    { date: 'Week 3', score: 82 },
    { date: 'Week 4', score: 88 }
  ];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Header & Independent Mode Selector */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {activeTab === 'assigned' ? 'Instructor Coursework Progress' : 'Self-Paced Practice Progress'}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {activeTab === 'assigned'
              ? 'Syllabus completion and grade standing for CSE-301 Section A.'
              : 'Independent skill progression across algorithmic patterns in the sandbox.'}
          </p>
        </div>

        {/* 2 Purely Independent Tabs (NO "All" tab) */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-100 rounded-2xl border border-slate-200/80 self-start md:self-auto">
          <button
            onClick={() => setActiveTab('assigned')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'assigned'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GraduationCap className="w-4 h-4" />
            <span>Instructor Coursework ({assignedSolved}/{assignedProblems.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('practice')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'practice'
                ? 'bg-purple-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Code2 className="w-4 h-4" />
            <span>Self-Paced Practice ({practiceSolved}/{practiceProblems.length})</span>
          </button>
        </div>
      </div>

      {/* Main Mode Stats Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
          {/* Progress Gauge */}
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <CircularGauge
              score={
                activeTab === 'assigned'
                  ? Math.round((assignedSolved / (assignedProblems.length || 1)) * 100)
                  : Math.round((practiceSolved / (practiceProblems.length || 1)) * 100)
              }
              maxScore={100}
              size={120}
              strokeWidth={9}
              color={activeTab === 'assigned' ? '#4f46e5' : '#9333ea'}
              showPercent
              sublabel={activeTab === 'assigned' ? 'Completed' : 'Mastery'}
            />
            <div className="text-center sm:text-left space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {activeTab === 'assigned' ? 'CSE-301 Section A' : 'Sandbox Independent Track'}
              </span>
              <h2 className="text-2xl font-extrabold text-slate-900">
                {activeTab === 'assigned'
                  ? 'Course Assignments Completion'
                  : 'Independent Practice Mastery'}
              </h2>
              <p className="text-xs text-slate-500 max-w-sm">
                {activeTab === 'assigned'
                  ? 'Tracks mandatory coursework graded by Prof. Sarah Miller.'
                  : 'Tracks independent practice problems solved without instructor deadlines.'}
              </p>
            </div>
          </div>

          {/* 3 Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full lg:w-auto">
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-center gap-3.5">
              <div className={`p-2.5 rounded-xl ${activeTab === 'assigned' ? 'bg-indigo-100 text-indigo-700' : 'bg-purple-100 text-purple-700'}`}>
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  {activeTab === 'assigned' ? 'Assignments Solved' : 'Practice Solved'}
                </span>
                <span className="text-lg font-extrabold text-slate-900 font-mono">
                  {activeTab === 'assigned' ? `${assignedSolved} / ${assignedProblems.length}` : `${practiceSolved} / ${practiceProblems.length}`}
                </span>
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-center gap-3.5">
              <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-xl">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  {activeTab === 'assigned' ? 'Class Rank' : 'Practice Accuracy'}
                </span>
                <span className="text-lg font-extrabold text-emerald-600 font-mono">
                  {activeTab === 'assigned' ? 'Rank #6 / 48' : '85.0%'}
                </span>
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex items-center gap-3.5">
              <div className="p-2.5 bg-amber-100 text-amber-700 rounded-xl">
                {activeTab === 'assigned' ? <Clock className="w-5 h-5" /> : <Flame className="w-5 h-5" />}
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  {activeTab === 'assigned' ? 'Submission Pace' : 'Practice Streak'}
                </span>
                <span className="text-lg font-extrabold text-slate-900 font-mono">
                  {activeTab === 'assigned' ? '100% On-Time' : '7 Days 🔥'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Progress Chart & Topic Mastery */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">
                {activeTab === 'assigned' ? 'Coursework Score Growth' : 'Practice Score Progression'}
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {activeTab === 'assigned' ? 'Spring 2026' : 'Last 30 Days'}
            </span>
          </div>

          <ScoreTrendLineChart
            data={activeTab === 'assigned' ? courseworkTrend : practiceTrend}
            height={200}
          />
        </div>

        {/* Topic Mastery Breakdown */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900">
              {activeTab === 'assigned' ? 'Coursework Topics' : 'Practice Topics'}
            </h3>
            <Sparkles className="w-4 h-4 text-purple-600" />
          </div>

          <div className="space-y-3.5">
            {currentTopics.map((topic, i) => (
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
      </div>

      {/* Mode-Specific Problems Directory */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              {activeTab === 'assigned' ? 'Instructor Coursework Directory' : 'Self-Paced Practice Directory'}
            </h3>
            <p className="text-xs text-slate-400">Click any challenge to open in sandbox</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayedProblems.map((prob) => {
            const isAssigned = prob.origin === 'instructor_assigned';
            const isDone = prob.studentStatus === 'Submitted';

            return (
              <div
                key={prob.id}
                onClick={() => openProblemWorkspace(prob.id)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer bg-slate-50/50 hover:bg-white flex flex-col justify-between group ${
                  isAssigned ? 'border-indigo-200/80 hover:border-indigo-500' : 'border-slate-200/80 hover:border-purple-400'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <DifficultyBadge difficulty={prob.difficulty} />
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      isDone ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {isDone ? '✓ Solved' : 'Pending'}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {prob.title}
                  </h4>

                  <span className={`inline-block mt-2 text-[10px] font-bold px-2 py-0.5 rounded ${
                    isAssigned ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-purple-50 text-purple-700 border border-purple-200'
                  }`}>
                    {isAssigned ? '🎓 Coursework' : '💡 Practice'}
                  </span>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-indigo-600">
                  <span>{isDone ? 'Review in Sandbox' : 'Solve Challenge'}</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
