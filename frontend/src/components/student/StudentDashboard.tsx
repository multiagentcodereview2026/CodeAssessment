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
  Target
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/Badge';
import { LearningSummarySparkline } from '../common/ChartComponents';
import { MOCK_PROBLEMS } from '../../mock/data';

export const StudentDashboard: React.FC = () => {
  const {
    currentUser,
    studentProgress,
    submissions,
    openProblemWorkspace,
    openAssessmentResult,
    setCurrentView
  } = useApp();

  return (
    <div className="space-y-6 pb-12">
      {/* Top Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 p-6 rounded-3xl text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-indigo-500/10 to-transparent pointer-events-none" />
        
        <div className="space-y-1.5 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-indigo-300" />
            <span>AI Code Intelligence Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Hello, {currentUser.name}! 👋
          </h1>
          <p className="text-sm text-slate-300">
            Keep coding, keep improving! Your algorithmic accuracy is up 6.4% this week.
          </p>
        </div>

        <div className="flex items-center gap-3 relative z-10">
          <button
            onClick={() => openProblemWorkspace('prob-1')}
            className="px-4 py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-bold shadow-lg shadow-indigo-500/30 flex items-center gap-2 transition-transform active:scale-95"
          >
            <Zap className="w-4 h-4" />
            Resume "Two Sum"
          </button>
        </div>
      </div>

      {/* Top 4 Key Stat Cards (Matching diagram step 2) */}
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

        {/* Rank */}
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

      {/* AI Projected Score Action Card */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-purple-900/10 via-indigo-900/10 to-transparent border border-purple-200/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-2.5 bg-purple-600 text-white rounded-xl shadow-md shadow-purple-600/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900">
                Projected Score After Revision Available
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-extrabold uppercase bg-purple-100 text-purple-800 rounded-full">
                +7 pts Gain
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              Applying AI recommendations on <strong className="text-slate-800">Two Sum</strong> will boost your score from <span className="font-mono font-bold text-slate-800">85</span> to <span className="font-mono font-bold text-emerald-600">92/100</span>.
            </p>
          </div>
        </div>

        <button
          onClick={() => openAssessmentResult()}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all flex items-center gap-1.5 flex-shrink-0"
        >
          <span>View Detailed Feedback</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Middle Grid: Recent Submissions & Side Panels (Matching Step 2) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Submissions Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Recent Submissions</h2>
              <p className="text-xs text-slate-400">Your latest evaluations & AI assessments</p>
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
                        onClick={() => {
                          openAssessmentResult(sub.id);
                        }}
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

      {/* Assigned Problems Quick Launcher */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Active Course Assignments</h3>
            <p className="text-xs text-slate-400">Assigned by Prof. Sarah Miller • Due May 10</p>
          </div>
          <button
            onClick={() => setCurrentView('problems')}
            className="text-xs font-semibold text-indigo-600 hover:underline"
          >
            See All Problems ({MOCK_PROBLEMS.length})
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {MOCK_PROBLEMS.slice(0, 3).map((prob) => (
            <div
              key={prob.id}
              onClick={() => openProblemWorkspace(prob.id)}
              className="p-4 rounded-xl border border-slate-200 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer bg-slate-50/50 hover:bg-white flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    prob.difficulty === 'Easy' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {prob.difficulty}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Acc: {prob.acceptanceRate}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-800 group-hover:text-indigo-600 transition-colors">
                  {prob.title}
                </h4>
                <div className="flex flex-wrap gap-1 mt-2">
                  {prob.tags.slice(0, 2).map((tag, tIdx) => (
                    <span key={tIdx} className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600">
                <span>Code in Sandbox</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
