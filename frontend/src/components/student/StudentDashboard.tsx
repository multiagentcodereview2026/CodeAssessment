import React from 'react';
import {
  Flame,
  Award,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  Sparkles,
  Zap,
  ChevronRight,
  Clock,
  Target,
  GraduationCap,
  Calendar,
  AlertCircle,
  X,
  Code2
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/Badge';
import { LearningSummarySparkline } from '../common/ChartComponents';

export const StudentDashboard: React.FC = () => {
  const {
    currentUser,
    studentProgress,
    submissions,
    problems,
    openProblemWorkspace,
    openAssessmentResult,
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
              className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-amber-100 transition-colors"
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
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all cursor-pointer"
          >
            <GraduationCap className="w-4 h-4" />
            <span>Open Coursework</span>
          </button>

          <button
            onClick={() => setCurrentView('recommendations')}
            className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-purple-600 text-white text-xs font-bold shadow-xs flex items-center gap-2 transition-all cursor-pointer"
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

      {/* 4. Main Grid: Recent Submissions & Weak Topics Diagnostic */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Submissions Table */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900">Recent Evaluations</h2>
              <p className="text-xs text-slate-400">Your latest AI assessment reports and grades</p>
            </div>
            <button
              onClick={() => setCurrentView('submissions')}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <span>View All Records</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400 border-b border-slate-100 font-medium">
                  <th className="pb-3 font-semibold">Problem</th>
                  <th className="pb-3 font-semibold">Score</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Date & Time</th>
                  <th className="pb-3 font-semibold text-right">Report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.slice(0, 5).map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-50/70 transition-colors group">
                    <td className="py-3.5 font-bold text-slate-800">
                      <div className="flex items-center gap-2">
                        <span>{sub.problemTitle}</span>
                        <span className="text-[10px] text-slate-400 font-mono font-normal">({sub.language})</span>
                      </div>
                    </td>
                    <td className="py-3.5 font-mono font-bold">
                      <span className={sub.score >= 80 ? 'text-emerald-600' : 'text-indigo-600'}>
                        {sub.score} / 100
                      </span>
                    </td>
                    <td className="py-3.5">
                      <StatusBadge status={sub.status} />
                    </td>
                    <td className="py-3.5 text-slate-500 font-mono text-[11px]">
                      {sub.date}
                    </td>
                    <td className="py-3.5 text-right">
                      <button
                        onClick={() => openAssessmentResult(sub.id)}
                        className="px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                      >
                        Inspect AI Report
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right 1 Col: Weak Topics Diagnostic & Learning Summary */}
        <div className="space-y-6">
          {/* Weak Topics Diagnostic */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Concept Diagnostics</h3>
              <Target className="w-4 h-4 text-amber-500" />
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Targeted concepts identified by multi-agent analysis for reinforcement:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {studentProgress.weakTopics.map((topic, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentView('recommendations')}
                  className="px-3 py-1 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200/80 transition-colors"
                >
                  {topic}
                </button>
              ))}
            </div>
            <button
              onClick={() => setCurrentView('recommendations')}
              className="w-full py-2 text-xs font-bold text-indigo-600 bg-indigo-50/50 hover:bg-indigo-50 rounded-xl transition-colors text-center block mt-2 cursor-pointer"
            >
              View Targeted AI Practice →
            </button>
          </div>

          {/* Learning Summary */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Practice Activity</h3>
              <span className="text-[11px] font-mono text-slate-400">This Month</span>
            </div>
            <div className="my-1">
              <LearningSummarySparkline />
            </div>
            <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>{studentProgress.hoursSpent}</span>
              </div>
              <span className="font-semibold text-indigo-600">85% Accuracy Target</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
