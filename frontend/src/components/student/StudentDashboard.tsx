import React from 'react';
import { useNavigate } from 'react-router-dom';
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
import { MOCK_PROBLEMS } from '../../mock/data';

export const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentUser,
    studentProgress,
    submissions,
    openProblemWorkspace,
    openAssessmentResult
  } = useApp();

  const handleResumeChallenge = (probId: string = 'prob-1') => {
    openProblemWorkspace(probId);
    navigate(`/problems/${probId}`);
  };

  const handleInspectReport = (subId?: string) => {
    openAssessmentResult(subId);
    navigate('/result');
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 p-6 sm:p-8 rounded-3xl text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-indigo-500/10 to-transparent pointer-events-none" />
        
        <div className="relative z-10">
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Hello, {currentUser.name}! 👋
          </h1>
        </div>

        <div className="flex items-center gap-3 relative z-10">
          <button
            onClick={() => handleResumeChallenge('prob-1')}
            className="px-5 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <Zap className="w-4 h-4 text-amber-300" />
            <span>Resume "Two Sum"</span>
          </button>
        </div>
      </div>

      {/* Top 4 Key Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Score */}
        <div
          onClick={() => navigate('/analytics')}
          className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:border-indigo-300 card-hover cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Overall Score</span>
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
              {studentProgress.overallScore}
            </span>
            <span className="text-xs text-slate-400 font-mono">/ 100</span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-600 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>Excellent</span>
          </div>
        </div>

        {/* Problems Solved */}
        <div
          onClick={() => navigate('/problems')}
          className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:border-indigo-300 card-hover cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Problems Solved</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
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
        <div
          onClick={() => navigate('/progress')}
          className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:border-indigo-300 card-hover cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Current Streak</span>
            <div className="p-2 bg-amber-50 text-amber-600 rounded-xl">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
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
        <div
          onClick={() => navigate('/analytics')}
          className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:border-indigo-300 card-hover cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Cohort Rank</span>
            <div className="p-2 bg-purple-50 text-purple-600 rounded-xl">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-purple-700 font-mono">
              #6
            </span>
          </div>
          <div className="mt-2 text-xs text-purple-600 font-medium truncate">
            Rank #6 of 48 peers
          </div>
        </div>
      </div>

      {/* AI Projected Score Action Card */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-purple-900/10 via-indigo-900/10 to-transparent border border-purple-200/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xs">
        <div className="flex items-start gap-3.5">
          <div className="p-3 bg-purple-600 text-white rounded-2xl shadow-md shadow-purple-600/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900">
                Projected Score After Revision Available
              </h3>
              <span className="px-2.5 py-0.5 text-[10px] font-extrabold uppercase bg-purple-100 text-purple-800 rounded-full">
                +7 pts Gain
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1">
              Applying AI recommendations on <strong className="text-slate-800">Two Sum</strong> will boost your score from <span className="font-mono font-bold text-slate-800">85</span> to <span className="font-mono font-bold text-emerald-600">92/100</span>.
            </p>
          </div>
        </div>

        <button
          onClick={() => handleInspectReport()}
          className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-2xl shadow-md shadow-purple-600/20 transition-all flex items-center gap-2 flex-shrink-0 cursor-pointer active:scale-95"
        >
          <span>View Detailed Feedback</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Middle Grid: Recent Submissions & Side Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Submissions Table */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900">Recent Submissions</h2>
              <p className="text-xs text-slate-400 mt-0.5">Your latest evaluations & AI assessments</p>
            </div>
            <button
              onClick={() => navigate('/submissions')}
              className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400 border-b border-slate-100 font-medium">
                  <th className="pb-3.5 font-semibold">Problem</th>
                  <th className="pb-3.5 font-semibold">Score</th>
                  <th className="pb-3.5 font-semibold">Status</th>
                  <th className="pb-3.5 font-semibold">Date & Time</th>
                  <th className="pb-3.5 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.slice(0, 5).map((sub) => (
                  <tr 
                    key={sub.id} 
                    onClick={() => handleInspectReport(sub.id)}
                    className="hover:bg-slate-50/70 transition-colors group cursor-pointer"
                  >
                    <td className="py-4 font-bold text-slate-800">
                      <div className="flex items-center gap-2">
                        <span>{sub.problemTitle}</span>
                        <span className="text-[10px] text-slate-400 font-mono">({sub.language})</span>
                      </div>
                    </td>
                    <td className="py-4 font-mono font-bold">
                      <span className={sub.score >= 80 ? 'text-emerald-600' : sub.score >= 60 ? 'text-indigo-600' : 'text-rose-600'}>
                        {sub.score} / 100
                      </span>
                    </td>
                    <td className="py-4">
                      <StatusBadge status={sub.status} />
                    </td>
                    <td className="py-4 text-slate-500 font-mono text-[11px]">
                      {sub.date}
                    </td>
                    <td className="py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleInspectReport(sub.id)}
                        className="px-3 py-1.5 text-xs font-bold text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors cursor-pointer"
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

        {/* Right 1 Col: Weak Topics & Learning Summary */}
        <div className="space-y-6">
          {/* Weak Topics */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Weak Topics</h3>
              <Target className="w-4 h-4 text-amber-500" />
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              AI identified lower test pass rates on these algorithmic patterns:
            </p>
            <div className="flex flex-wrap gap-2">
              {studentProgress.weakTopics.map((topic, i) => (
                <button
                  key={i}
                  onClick={() => navigate('/problems')}
                  className="px-3 py-1 text-xs font-semibold rounded-xl bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200/80 transition-colors cursor-pointer"
                >
                  {topic}
                </button>
              ))}
            </div>
            <button
              onClick={() => navigate('/feedback?tab=practice')}
              className="w-full py-2.5 text-xs font-bold text-indigo-600 bg-indigo-50/60 hover:bg-indigo-100 rounded-2xl transition-all text-center block cursor-pointer"
            >
              View Targeted AI Practice →
            </button>
          </div>
        </div>
      </div>

      {/* Assigned Problems Quick Launcher */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900">Active Course Assignments</h3>
            <p className="text-xs text-slate-400 mt-0.5">Assigned coursework with automated AI grading</p>
          </div>
          <button
            onClick={() => navigate('/problems')}
            className="text-xs font-bold text-indigo-600 hover:underline cursor-pointer"
          >
            See All Problems ({MOCK_PROBLEMS.length})
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {MOCK_PROBLEMS.slice(0, 3).map((prob) => (
            <div
              key={prob.id}
              onClick={() => handleResumeChallenge(prob.id)}
              className="p-5 rounded-2xl border border-slate-200 hover:border-indigo-400 hover:shadow-md card-hover transition-all cursor-pointer bg-slate-50/50 hover:bg-white flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-lg">
                    {prob.courseCode || 'CS201'}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Acc: {prob.acceptanceRate}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  {prob.title}
                </h4>
                <div className="flex flex-wrap gap-1 mt-2">
                  {prob.tags.slice(0, 2).map((tag, tIdx) => (
                    <span key={tIdx} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
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
