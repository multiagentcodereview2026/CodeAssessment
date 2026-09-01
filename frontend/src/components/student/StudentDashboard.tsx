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
  BookOpen,
  Code2
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge, DifficultyBadge } from '../common/Badge';
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
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* 1. Dynamic Broadcast Alert from Instructor */}
      {activeBroadcast && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-500/15 via-orange-500/10 to-amber-500/5 border border-amber-300/80 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-fadeIn">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-amber-500 text-white rounded-xl shadow-xs flex-shrink-0">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-extrabold uppercase tracking-wider text-amber-800 bg-amber-200/80 px-2 py-0.5 rounded">
                  Instructor Assignment
                </span>
                <span className="text-xs font-semibold text-slate-700">Course: CSE-301</span>
              </div>
              <p className="text-xs font-medium text-slate-800 mt-1 leading-snug">
                {activeBroadcast}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <button
              onClick={() => {
                const firstPending = instructorAssignedProblems.find(p => p.studentStatus !== 'Submitted') || instructorAssignedProblems[0];
                if (firstPending) openProblemWorkspace(firstPending.id);
                else openProblemWorkspace('prob-1');
              }}
              className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold shadow-xs flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <span>Solve Question</span>
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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 p-6 rounded-3xl text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-indigo-500/10 to-transparent pointer-events-none" />
        
        <div className="space-y-1.5 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-indigo-300" />
            <span>AI Code Intelligence & Grading Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Hello, {currentUser.name}! 👋
          </h1>
          <p className="text-sm text-slate-300">
            {pendingAssignedCount > 0
              ? `You have ${pendingAssignedCount} pending assignment(s) posted by your instructor.`
              : 'All instructor assignments are completed! Keep your streak going with self-paced practice.'}
          </p>
        </div>

        <div className="flex items-center gap-3 relative z-10">
          <button
            onClick={() => {
              const target = instructorAssignedProblems.find(p => p.studentStatus !== 'Submitted') || selfPracticeProblems[0];
              if (target) openProblemWorkspace(target.id);
            }}
            className="px-4 py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-bold shadow-lg shadow-indigo-500/30 flex items-center gap-2 transition-transform active:scale-95 cursor-pointer"
          >
            <Zap className="w-4 h-4" />
            <span>Resume Priority Problem</span>
          </button>
        </div>
      </div>

      {/* 3. Top 4 Key Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Score */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-indigo-200 transition-colors">
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
            <span>Excellent</span>
            <span className="text-slate-400 font-normal ml-auto">(+3.2% vs avg)</span>
          </div>
        </div>

        {/* Problems Solved */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-indigo-200 transition-colors">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Problems Solved</span>
            <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {studentProgress.problemsSolved}
            </span>
            <span className="text-xs text-slate-400 font-mono">/ {studentProgress.totalProblems}</span>
          </div>
          <div className="mt-2 text-xs text-slate-500 flex items-center justify-between">
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden mr-2">
              <div
                className="bg-emerald-500 h-full rounded-full"
                style={{ width: `${(studentProgress.problemsSolved / studentProgress.totalProblems) * 100}%` }}
              />
            </div>
            <span className="font-mono text-[11px] font-semibold text-slate-600">80%</span>
          </div>
        </div>

        {/* Current Streak */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-indigo-200 transition-colors">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Current Streak</span>
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

        {/* Cohort Rank */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-indigo-200 transition-colors">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Cohort Rank</span>
            <div className="p-1.5 bg-purple-50 text-purple-600 rounded-lg">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-extrabold text-purple-700 font-sans">
              {studentProgress.rankPercentile}
            </span>
          </div>
          <div className="mt-2 text-xs text-purple-600 font-medium">
            CSE-301 Section A (48 peers)
          </div>
        </div>
      </div>

      {/* 4. TYPE 1: INSTRUCTOR ASSIGNED QUESTIONS SECTION */}
      <div className="bg-white rounded-3xl border border-indigo-200/90 shadow-sm p-6 sm:p-7 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-700 rounded-xl">
              <GraduationCap className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-extrabold text-slate-900">
                  Instructor Assigned Questions
                </h2>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-indigo-100 text-indigo-800 rounded-full">
                  Mandatory • Graded
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Questions assigned by Prof. Sarah Miller for gradebook evaluation.
              </p>
            </div>
          </div>

          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
            Pending Tasks: <strong className="text-indigo-600 font-mono">{pendingAssignedCount}</strong> / {instructorAssignedProblems.length}
          </span>
        </div>

        {instructorAssignedProblems.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {instructorAssignedProblems.map((prob) => (
              <div
                key={prob.id}
                onClick={() => openProblemWorkspace(prob.id)}
                className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between group ${
                  prob.studentStatus === 'Submitted'
                    ? 'bg-emerald-50/40 border-emerald-200 hover:border-emerald-400'
                    : prob.studentStatus === 'In Progress'
                    ? 'bg-indigo-50/40 border-indigo-300 hover:border-indigo-500 shadow-xs'
                    : 'bg-white border-slate-200 hover:border-indigo-400 hover:shadow-md'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2.5">
                    <DifficultyBadge difficulty={prob.difficulty} />
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      prob.studentStatus === 'Submitted'
                        ? 'bg-emerald-100 text-emerald-800'
                        : prob.studentStatus === 'In Progress'
                        ? 'bg-indigo-100 text-indigo-800 animate-pulse'
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {prob.studentStatus || 'Not Started'}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {prob.title}
                  </h3>

                  <p className="text-xs text-slate-500 line-clamp-2 mt-1.5 leading-relaxed">
                    {prob.description.replace(/[`*]/g, '')}
                  </p>

                  <div className="flex items-center gap-2 mt-3 text-[11px] text-slate-500 font-mono">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Due: {prob.dueDate || '10 May, 2026'}</span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100/80 flex items-center justify-between text-xs font-bold">
                  <span className="text-[11px] text-slate-400 font-sans">
                    By {prob.instructorName || 'Prof. Sarah Miller'}
                  </span>
                  <span className="text-indigo-600 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                    <span>{prob.studentStatus === 'Submitted' ? 'Review Submission' : 'Solve Assigned'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-slate-800">No Pending Instructor Assignments</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Your instructor hasn't posted new tasks at this moment. You can freely practice self-paced challenges below!
            </p>
          </div>
        )}
      </div>

      {/* 5. TYPE 2: SELF-PACED PRACTICE SANDBOX (MANUAL LEARNING) */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-50 text-purple-700 rounded-xl">
              <Code2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-extrabold text-slate-900">
                  Self-Paced Practice Sandbox
                </h2>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-slate-100 text-slate-700 rounded-full">
                  Independent Learning
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Practice any problem manually at your own pace without instructor deadlines.
              </p>
            </div>
          </div>

          <button
            onClick={() => setCurrentView('problems')}
            className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
          >
            <span>Explore All ({selfPracticeProblems.length})</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {selfPracticeProblems.slice(0, 4).map((prob) => (
            <div
              key={prob.id}
              onClick={() => openProblemWorkspace(prob.id)}
              className="p-4 rounded-2xl border border-slate-200 hover:border-purple-400 hover:shadow-md transition-all cursor-pointer bg-slate-50/50 hover:bg-white flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <DifficultyBadge difficulty={prob.difficulty} />
                  <span className="text-[10px] text-slate-400 font-mono">
                    Acc: {prob.acceptanceRate}
                  </span>
                </div>

                <h4 className="text-sm font-bold text-slate-900 group-hover:text-purple-600 transition-colors">
                  {prob.title}
                </h4>

                <div className="flex flex-wrap gap-1 mt-2">
                  {prob.tags.slice(0, 2).map((t, idx) => (
                    <span key={idx} className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-purple-600">
                <span>Practice Sandbox</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6. Middle Grid: Recent Submissions & Weak Topics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Submissions Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Recent Submissions</h2>
              <p className="text-xs text-slate-400">Your latest evaluations across assigned & practice tasks</p>
            </div>
            <button
              onClick={() => setCurrentView('submissions')}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400 border-b border-slate-100 font-medium">
                  <th className="pb-3 font-semibold">Problem</th>
                  <th className="pb-3 font-semibold">Mode</th>
                  <th className="pb-3 font-semibold">Score</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Date & Time</th>
                  <th className="pb-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.slice(0, 5).map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-50/70 transition-colors group">
                    <td className="py-3.5 font-bold text-slate-800">
                      <div className="flex items-center gap-2">
                        <span>{sub.problemTitle}</span>
                        <span className="text-[10px] text-slate-400 font-mono">({sub.language})</span>
                      </div>
                    </td>
                    <td className="py-3.5">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        sub.origin === 'instructor_assigned' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {sub.origin === 'instructor_assigned' ? 'Assigned' : 'Practice'}
                      </span>
                    </td>
                    <td className="py-3.5 font-mono font-bold">
                      <span className={sub.score >= 80 ? 'text-emerald-600' : sub.score >= 60 ? 'text-indigo-600' : 'text-rose-600'}>
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
                        className="px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
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

        {/* Right 1 Col: Weak Topics & Learning Summary Sparkline */}
        <div className="space-y-6">
          {/* Weak Topics */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-900">Weak Topics</h3>
              <Target className="w-4 h-4 text-amber-500" />
            </div>
            <p className="text-xs text-slate-500 mb-3">
              AI identified lower test pass rates on these algorithmic patterns:
            </p>
            <div className="flex flex-wrap gap-2 mb-4">
              {studentProgress.weakTopics.map((topic, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentView('problems')}
                  className="px-3 py-1 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200/80 transition-colors"
                >
                  {topic}
                </button>
              ))}
            </div>
            <button
              onClick={() => setCurrentView('recommendations')}
              className="w-full py-2 text-xs font-bold text-indigo-600 bg-indigo-50/50 hover:bg-indigo-50 rounded-xl transition-colors text-center block"
            >
              View Targeted AI Practice →
            </button>
          </div>

          {/* Learning Summary Chart */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-slate-900">Learning Summary</h3>
              <span className="text-[11px] font-mono text-slate-400">This Month</span>
            </div>
            <div className="my-2">
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
