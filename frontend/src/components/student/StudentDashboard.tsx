import React from 'react';
import {
  Flame,
  Award,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  Sparkles,
  GraduationCap,
  AlertCircle,
  X,
  Code2,
  ListOrdered,
  LineChart,
  Lightbulb
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const StudentDashboard: React.FC = () => {
  const {
    currentUser,
    studentProgress,
    problems,
    setCurrentView,
    activeBroadcast,
    dismissBroadcast
  } = useApp();

  const instructorAssignedProblems = problems.filter(p => p.origin === 'instructor_assigned');
  const selfPracticeProblems = problems.filter(p => p.origin !== 'instructor_assigned');
  const pendingAssignedCount = instructorAssignedProblems.filter(p => p.studentStatus !== 'Submitted').length;

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* 1. Dynamic Broadcast Alert from Instructor */}
      {activeBroadcast && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-fadeIn">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-amber-500 text-white rounded-xl shadow-xs flex-shrink-0">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-800 bg-amber-200 px-2 py-0.5 rounded">
                  Course Notice
                </span>
                <span className="text-xs font-semibold text-slate-700">CSE-301 Section A</span>
              </div>
              <p className="text-xs font-medium text-slate-800 mt-1 leading-snug">
                {activeBroadcast}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <button
              onClick={() => setCurrentView('problems')}
              className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold shadow-xs flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <span>View Coursework</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={dismissBroadcast}
              className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-amber-100 transition-colors cursor-pointer"
              title="Dismiss notice"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* 2. Top Welcome Banner */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500">
            <span>{currentUser.institution}</span>
            <span>•</span>
            <span className="font-mono text-slate-700 font-bold">Roll: {currentUser.rollNumber}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            Hello, {currentUser.name}! 👋
          </h1>
          <p className="text-xs text-slate-500 max-w-xl">
            {pendingAssignedCount > 0
              ? `You have ${pendingAssignedCount} pending assignment task(s) for CSE-301. Keep up your progress!`
              : 'All pending course assignments are up to date! Continue with your practice track.'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setCurrentView('problems')}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all cursor-pointer"
          >
            <GraduationCap className="w-4 h-4" />
            <span>Open Coursework</span>
          </button>

          <button
            onClick={() => setCurrentView('recommendations')}
            className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-purple-600 text-white text-xs font-bold shadow-xs flex items-center gap-2 transition-all cursor-pointer"
          >
            <Code2 className="w-4 h-4" />
            <span>Practice Sandbox</span>
          </button>
        </div>
      </div>

      {/* 3. 4 Key Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Academic Score */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Overall Score</span>
            <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {studentProgress.overallScore}
            </span>
            <span className="text-xs text-slate-400 font-mono">/ 100</span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-600 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>Grade: A (Excellent)</span>
          </div>
        </div>

        {/* Cohort Rank */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Class Standing</span>
            <div className="p-1.5 bg-purple-50 text-purple-600 rounded-lg">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-extrabold text-purple-700 font-sans">
              {studentProgress.rankDisplay}
            </span>
          </div>
          <div className="mt-2 text-xs text-purple-600 font-medium">
            CSE-301 Section A (48 Students)
          </div>
        </div>

        {/* Pending Coursework Tasks */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Coursework Tasks</span>
            <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {instructorAssignedProblems.length - pendingAssignedCount}
            </span>
            <span className="text-xs text-slate-400 font-mono">/ {instructorAssignedProblems.length} Solved</span>
          </div>
          <div className="mt-2 text-xs text-emerald-600 font-medium">
            {pendingAssignedCount === 0 ? 'All Tasks Complete' : `${pendingAssignedCount} Task Pending`}
          </div>
        </div>

        {/* Active Streak */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Practice Streak</span>
            <div className="p-1.5 bg-amber-50 text-amber-600 rounded-lg">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {studentProgress.currentStreak}
            </span>
            <span className="text-xs text-slate-500 font-semibold">Days</span>
          </div>
          <div className="mt-2 text-xs text-amber-600 font-semibold flex items-center gap-1">
            <Flame className="w-3.5 h-3.5 fill-amber-500" />
            <span>Active learning streak 🔥</span>
          </div>
        </div>
      </div>

      {/* 4. Quick Portal Launchpads */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => setCurrentView('problems')}
          className="bg-white p-6 rounded-3xl border border-slate-200/80 hover:border-indigo-500 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <GraduationCap className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
              Assigned Coursework
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Solve mandatory coding questions assigned by Prof. Sarah Miller.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-indigo-600">
            <span>View Tasks ({instructorAssignedProblems.length})</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        <div
          onClick={() => setCurrentView('recommendations')}
          className="bg-white p-6 rounded-3xl border border-slate-200/80 hover:border-purple-400 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <Code2 className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 group-hover:text-purple-600 transition-colors">
              Practice Sandbox
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Explore self-paced algorithmic challenges without deadlines.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-purple-600">
            <span>Start Practice ({selfPracticeProblems.length})</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        <div
          onClick={() => setCurrentView('scores')}
          className="bg-white p-6 rounded-3xl border border-slate-200/80 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-2xl bg-slate-100 text-slate-700 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <LineChart className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
              Problem Scorecard
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Inspect multi-agent rubric breakdown and attempt progression.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-indigo-600">
            <span>Open Scorecard</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        <div
          onClick={() => setCurrentView('submissions')}
          className="bg-white p-6 rounded-3xl border border-slate-200/80 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-2xl bg-slate-100 text-slate-700 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <ListOrdered className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
              Submissions History
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Review full AI evaluation reports and test pass records.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-indigo-600">
            <span>View Records</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>
    </div>
  );
};
