import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  CalendarCheck,
  FileCheck2,
  Award,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
  Download,
  Plus,
  BookOpen,
  ChevronRight,
  Clock,
  Sparkles,
  AlertTriangle,
  Target
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreDistributionBarChart } from '../common/ChartComponents';

export const InstructorDashboard: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentUser,
    instructorStats,
    assignments,
    similarityAlerts
  } = useApp();

  const urgentAssignment = [...assignments].sort((a, b) => {
    const aRatio = a.totalCount ? a.submittedCount / a.totalCount : 1;
    const bRatio = b.totalCount ? b.submittedCount / b.totalCount : 1;
    return aRatio - bRatio;
  })[0];
  const topSimilarityAlert = [...similarityAlerts].sort((a, b) => b.similarityPercentage - a.similarityPercentage)[0];
  const completionRate = urgentAssignment?.totalCount
    ? Math.round((urgentAssignment.submittedCount / urgentAssignment.totalCount) * 100)
    : 0;

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Banner (Clean Greeting & Primary CTAs - Jakob's & Fitts's Law) */}
      <div className="flex flex-col justify-between gap-5 border-b border-slate-200 pb-6 sm:flex-row sm:items-end">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-emerald-700">Faculty workspace</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-[2rem]">
            Welcome back, {currentUser.name.split(' ')[0]}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Review course activity, assessment results, and student progress.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => navigate('/instructor/problems')}
            className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-emerald-600 px-4 text-sm font-semibold text-white transition hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
          >
            <Plus className="w-4 h-4" />
            <span>Create Question</span>
          </button>
          <button
            onClick={() => navigate('/instructor/reports')}
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
          >
            <Download className="w-4 h-4" />
            <span>Export Reports</span>
          </button>
        </div>
      </div>

      {/* 4 Key Stat Cards (Miller's Law & Serial Position Effect: Key metrics first) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Students */}
        <button type="button"
          onClick={() => navigate('/instructor/students')}
          className="w-full rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Total Students</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {instructorStats.totalStudents}
          </div>
          <div className="mt-2 text-xs text-slate-500 flex items-center justify-between">
            <span>Across your courses</span>
            <span className="text-emerald-600 font-semibold flex items-center gap-0.5">
              Roster <ChevronRight className="w-3 h-3" />
            </span>
          </div>
        </button>

        {/* Active Questions */}
        <button type="button"
          onClick={() => navigate('/instructor/problems')}
          className="w-full rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Active assignments</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
              <CalendarCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {instructorStats.activeAssignments}
          </div>
          <div className="mt-2 flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>Currently in your courses</span>
            <span className="flex items-center gap-0.5 font-semibold text-emerald-700">
              Problem Bank <ChevronRight className="w-3 h-3" />
            </span>
          </div>
        </button>

        {/* Submissions */}
        <button type="button"
          onClick={() => navigate('/instructor/reports')}
          className="w-full rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Submissions Evaluated</span>
            <div className="rounded-lg bg-emerald-50 p-2 text-emerald-700">
              <FileCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {instructorStats.totalSubmissions}
          </div>
          <div className="mt-2 text-xs font-medium text-slate-500">
            Saved in your assessment history
          </div>
        </button>

        {/* Avg Score */}
        <button type="button"
          onClick={() => navigate('/instructor/analytics')}
          className="w-full rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Avg. Class Score</span>
            <div className="p-2 bg-amber-50 text-amber-600 rounded-xl">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {instructorStats.averageScore == null ? 'N/A' : `${instructorStats.averageScore}%`}
          </div>
          <div className="mt-2 text-xs text-slate-500 font-medium">
            Cohort Average
          </div>
        </button>
      </div>

      {/* Similarity Alert Banner (Von Restorff Effect: High contrast standout for priority alerts) */}
      {similarityAlerts.length > 0 && topSimilarityAlert && (
        <div className="flex flex-col justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50 p-5 sm:flex-row sm:items-center"
        >
          <div className="flex items-center gap-3.5">
            <div className="p-3 bg-rose-600 text-white rounded-2xl shadow-md shadow-rose-600/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-rose-950">
                Similarity Review: {similarityAlerts.length} candidate pair{similarityAlerts.length === 1 ? '' : 's'} need attention
              </h4>
              <p className="text-xs text-rose-700 mt-0.5">
                {topSimilarityAlert.studentA?.name || 'A student'} and {topSimilarityAlert.studentB?.name || 'another student'} have a same-problem overlap candidate on {topSimilarityAlert.problemTitle}.
              </p>
            </div>
          </div>
          <button onClick={() => navigate('/instructor/similarity')} className="flex cursor-pointer items-center gap-1.5 self-start rounded-lg bg-amber-800 px-4 py-2 text-xs font-semibold text-white transition hover:bg-amber-900 focus:outline-none focus:ring-2 focus:ring-amber-600 focus:ring-offset-2 sm:self-auto">
            <span>Review AST Diff</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Faculty Triage Rail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <button
          onClick={() => navigate('/instructor/problems')}
          className="rounded-xl border border-slate-200 bg-white p-5 text-left transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-amber-700 uppercase">Turnout Watch</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900">{urgentAssignment?.title || 'No active assignments'}</h3>
          <p className="mt-1 text-xs text-slate-500 leading-relaxed">
            {urgentAssignment
              ? `${completionRate}% submitted. Prioritize reminders before grading pressure piles up.`
              : 'Create a course problem to start tracking submissions.'}
          </p>
        </button>

        <button
          onClick={() => navigate('/instructor/analytics')}
          className="rounded-xl border border-slate-200 bg-white p-5 text-left transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase text-slate-500">Class overview</span>
            <Target className="h-4 w-4 text-emerald-700" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900">Complexity Reasoning</h3>
          <p className="mt-1 text-xs text-slate-500 leading-relaxed">
            Class average is {instructorStats.averageScore == null ? 'unavailable' : `${instructorStats.averageScore}%`}. Use rubric analytics to find topics that need a short reteach.
          </p>
        </button>

        <button
          onClick={() => navigate('/instructor/similarity')}
          className="rounded-xl border border-slate-200 bg-white p-5 text-left transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase text-slate-500">Similarity review</span>
            <AlertTriangle className="h-4 w-4 text-amber-700" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900">
            {topSimilarityAlert ? 'Review candidate available' : 'No active flags'}
          </h3>
          <p className="mt-1 text-xs text-slate-500 leading-relaxed">
            {topSimilarityAlert && topSimilarityAlert.studentA && topSimilarityAlert.studentB
              ? `${topSimilarityAlert.studentA.name} and ${topSimilarityAlert.studentB.name} have a submission flagged for review.`
              : 'No unresolved similarity candidates.'}
          </p>
        </button>
      </div>

      {/* Middle Grid: Class Performance Analytics & Recent Assignments (Proximity & Miller's Law) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Class Performance Overview & Distribution (Col span 7) */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Class Performance Overview</h3>
              <p className="text-xs text-slate-400 mt-0.5">Score distribution across {instructorStats.totalStudents} enrolled students</p>
            </div>
            <button
              onClick={() => navigate('/instructor/analytics')}
              className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 cursor-pointer"
            >
              <span>Detailed Analytics</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">Average Score</span>
              <span className="text-2xl font-extrabold text-slate-800 font-mono mt-1 block">
                {instructorStats.averageScore == null ? 'N/A' : `${instructorStats.averageScore}%`}
              </span>
            </div>
            <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-100">
              <span className="text-[10px] font-bold uppercase text-emerald-600 block tracking-wider">Highest Score</span>
              <span className="text-2xl font-extrabold text-emerald-700 font-mono mt-1 block">
                {instructorStats.highestScore == null ? 'N/A' : `${instructorStats.highestScore}%`}
              </span>
            </div>
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-100">
              <span className="text-[10px] font-bold uppercase text-rose-600 block tracking-wider">Lowest Score</span>
              <span className="text-2xl font-extrabold text-rose-700 font-mono mt-1 block">
                {instructorStats.lowestScore == null ? 'N/A' : `${instructorStats.lowestScore}%`}
              </span>
            </div>
          </div>

          <div>
            <span className="text-xs font-bold text-slate-700 mb-3 block">Score Distribution Breakdown:</span>
            <ScoreDistributionBarChart distribution={instructorStats.scoreDistribution} />
          </div>
        </div>

        {/* Right: Recent Assignments (Col span 5) */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Active Course Problems</h3>
                <p className="text-xs text-slate-400 mt-0.5">Real-time submission & grading progress</p>
              </div>
              <button
                onClick={() => navigate('/instructor/problems')}
                className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 cursor-pointer"
              >
                <span>View All</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-3.5">
              {assignments.map((asg) => (
                <div
                  key={asg.id}
                  className="p-4 rounded-2xl bg-slate-50 border border-slate-200/70 space-y-2.5 hover:bg-white hover:border-emerald-300 card-hover transition-all"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-900">{asg.title}</h4>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 border border-emerald-200">
                      {asg.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-600 font-mono">
                    <span>
                      Submissions: <strong className="text-slate-900">{asg.submittedCount}/{asg.totalCount}</strong>
                    </span>
                    <span>
                      Avg: <strong className="text-emerald-600">{asg.avgScore == null ? 'N/A' : `${asg.avgScore}%`}</strong>
                    </span>
                  </div>

                  {/* Progress bar (Peak-End Rule: visual completion feedback) */}
                  <div className="w-full bg-slate-200/80 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-600 h-full rounded-full transition-all duration-500"
                      style={{ width: `${asg.totalCount && asg.totalCount > 0 ? Math.min(100, Math.round((asg.submittedCount / asg.totalCount) * 100)) : 0}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Serial Position Effect: Concluding high-impact primary action at the end */}
          <button
            onClick={() => navigate('/instructor/students')}
            className="w-full py-3.5 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl text-xs font-bold shadow-md flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer mt-5"
          >
            <span>Open Full Student Roster ({instructorStats.totalStudents} Students)</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
