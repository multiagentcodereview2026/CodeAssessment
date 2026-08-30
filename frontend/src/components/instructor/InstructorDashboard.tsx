import React from 'react';
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
  BookOpen
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreDistributionBarChart } from '../common/ChartComponents';

export const InstructorDashboard: React.FC = () => {
  const {
    currentUser,
    instructorStats,
    assignments,
    setCurrentView,
    similarityAlerts
  } = useApp();

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 rounded-3xl text-white shadow-xl">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-400/30">
            <span>Spring Semester 2026</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Instructor Command Center
          </h1>
          <p className="text-xs text-slate-300">
            Welcome back, {currentUser.name} • CSE-301 Data Structures & Algorithms
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setCurrentView('instructor-assignments')}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all active:scale-95 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Create Assignment</span>
          </button>
          <button
            onClick={() => setCurrentView('instructor-reports')}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-bold border border-slate-700 flex items-center gap-2 transition-all cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Export Reports</span>
          </button>
        </div>
      </div>

      {/* 4 Key Stat Cards (Matches Step 2 Instructor Overview in diagram) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Students */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Total Students</span>
            <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {instructorStats.totalStudents}
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Enrolled across 2 cohorts
          </div>
        </div>

        {/* Active Assignments */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Active Assignments</span>
            <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <CalendarCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {instructorStats.activeAssignments}
          </div>
          <div className="mt-2 text-xs text-emerald-600 font-semibold">
            All sandbox suites active
          </div>
        </div>

        {/* Submissions */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Submissions</span>
            <div className="p-1.5 bg-purple-50 text-purple-600 rounded-lg">
              <FileCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {instructorStats.totalSubmissions}
          </div>
          <div className="mt-2 text-xs text-purple-600 font-semibold">
            +38 evaluated today
          </div>
        </div>

        {/* Avg Score */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Avg. Class Score</span>
            <div className="p-1.5 bg-amber-50 text-amber-600 rounded-lg">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {instructorStats.averageScore}%
          </div>
          <div className="mt-2 text-xs text-emerald-600 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+4.1% vs last assignment</span>
          </div>
        </div>
      </div>

      {/* Similarity Alert Banner if any flagged cases */}
      {similarityAlerts.length > 0 && (
        <div
          onClick={() => setCurrentView('instructor-similarity')}
          className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-between cursor-pointer hover:bg-rose-100/70 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-rose-600 text-white rounded-xl">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-rose-900">
                Plagiarism & Similarity Alert: {similarityAlerts.length} Flagged Incident Detected
              </h4>
              <p className="text-[11px] text-rose-700">
                Sai Kiran & Harish N. have 89% AST code token similarity on "Two Sum".
              </p>
            </div>
          </div>
          <button className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold shadow-xs">
            Review AST Diff
          </button>
        </div>
      )}

      {/* Middle Grid: Class Performance Analytics & Recent Assignments */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Class Performance Overview & Distribution (Col span 7) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Class Performance Overview</h3>
              <p className="text-xs text-slate-400">Score distribution across 48 enrolled students</p>
            </div>
            <button
              onClick={() => setCurrentView('instructor-analytics')}
              className="text-xs font-bold text-indigo-600 hover:underline"
            >
              Detailed Analytics →
            </button>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] font-bold uppercase text-slate-400 block">Average Score</span>
              <span className="text-xl font-extrabold text-slate-800 font-mono mt-0.5 block">
                {instructorStats.averageScore}%
              </span>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100">
              <span className="text-[10px] font-bold uppercase text-emerald-600 block">Highest Score</span>
              <span className="text-xl font-extrabold text-emerald-700 font-mono mt-0.5 block">
                {instructorStats.highestScore}%
              </span>
            </div>
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-100">
              <span className="text-[10px] font-bold uppercase text-rose-600 block">Lowest Score</span>
              <span className="text-xl font-extrabold text-rose-700 font-mono mt-0.5 block">
                {instructorStats.lowestScore}%
              </span>
            </div>
          </div>

          <div>
            <span className="text-xs font-bold text-slate-700 mb-2 block">Score Distribution:</span>
            <ScoreDistributionBarChart distribution={instructorStats.scoreDistribution} />
          </div>
        </div>

        {/* Right: Recent Assignments (Col span 5) */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Recent Assignments</h3>
                <p className="text-xs text-slate-400">Submission stats and average grades</p>
              </div>
              <button
                onClick={() => setCurrentView('instructor-assignments')}
                className="text-xs font-bold text-indigo-600 hover:underline"
              >
                View All
              </button>
            </div>

            <div className="space-y-3">
              {assignments.map((asg) => (
                <div
                  key={asg.id}
                  className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2 hover:bg-white hover:border-indigo-300 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-900">{asg.title}</h4>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                      {asg.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-600 font-mono">
                    <span>
                      Submissions: <strong className="text-slate-900">{asg.submittedCount}/{asg.totalCount}</strong>
                    </span>
                    <span>
                      Avg: <strong className="text-indigo-600">{asg.avgScore}%</strong>
                    </span>
                  </div>

                  <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-600 h-full rounded-full"
                      style={{ width: `${(asg.submittedCount / asg.totalCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => setCurrentView('instructor-students')}
            className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold shadow-xs flex items-center justify-center gap-2 transition-colors cursor-pointer mt-4"
          >
            <span>Open Full Student Roster (48)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
