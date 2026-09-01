import React from 'react';
import {
  Users,
  CalendarCheck,
  FileCheck2,
  Award,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
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
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <span className="font-semibold text-slate-700">Course: CSE-301 Data Structures</span>
            <span>•</span>
            <span className="font-mono text-slate-600">Spring 2026</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Instructor Command Center
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Overview of your assigned cohort (48 students), active coursework, and grading analytics.
          </p>
        </div>

        <button
          onClick={() => setCurrentView('instructor-assignments')}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md shadow-emerald-600/20 flex items-center gap-2 transition-all self-start md:self-auto cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>+ Assign Question / Task</span>
        </button>
      </div>

      {/* 4 Essential Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Assigned Cohort</span>
            <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            48 Students
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            CSE-301 Section A
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Active Assignments</span>
            <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <CalendarCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {assignments.length} Tasks
          </div>
          <div className="mt-1 text-[11px] text-emerald-600 font-medium">
            Syllabus coursework active
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Evaluations</span>
            <div className="p-1.5 bg-purple-50 text-purple-600 rounded-lg">
              <FileCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            152
          </div>
          <div className="mt-1 text-[11px] text-purple-600 font-medium">
            AI evaluated submissions
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Class Avg. Grade</span>
            <div className="p-1.5 bg-amber-50 text-amber-600 rounded-lg">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            77.5%
          </div>
          <div className="mt-1 text-[11px] text-emerald-600 font-medium flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+3.2% vs previous term</span>
          </div>
        </div>
      </div>

      {/* Similarity Alert Banner (If flagged) */}
      {similarityAlerts.length > 0 && (
        <div
          onClick={() => setCurrentView('instructor-analytics')}
          className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-between cursor-pointer hover:bg-rose-100/70 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-rose-600 text-white rounded-xl">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-rose-900">
                Plagiarism Alert: {similarityAlerts.length} Flagged Code Clone Incident
              </h4>
              <p className="text-[11px] text-rose-700">
                Sai Kiran & Harish N. have 89% AST code token similarity on "Two Sum".
              </p>
            </div>
          </div>
          <button className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold shadow-xs">
            Review Incident
          </button>
        </div>
      )}

      {/* Main Grid: Active Assignments & Quick Roster Access */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Active Assignments (Col span 7) */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Active Coursework</h3>
              <p className="text-xs text-slate-400">Assigned problem sets & student submission rates</p>
            </div>
            <button
              onClick={() => setCurrentView('instructor-assignments')}
              className="text-xs font-bold text-emerald-600 hover:underline"
            >
              + Dispatch New Task
            </button>
          </div>

          <div className="space-y-3">
            {assignments.map((asg) => (
              <div
                key={asg.id}
                className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 hover:bg-white hover:border-emerald-300 transition-all"
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
                    Average: <strong className="text-emerald-700">{asg.avgScore ? `${asg.avgScore}%` : 'Pending'}</strong>
                  </span>
                </div>

                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-600 h-full rounded-full"
                    style={{ width: `${(asg.submittedCount / asg.totalCount) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Assigned Students Roster Quick Card (Col span 5) */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Enrolled Cohort</h3>
                <p className="text-xs text-slate-400">48 Students in CSE-301</p>
              </div>
              <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                Active
              </span>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed mb-3">
              Monitor individual student progress, track weakness heatmaps across Dynamic Programming and Graphs, and provide direct feedback on submissions.
            </p>
          </div>

          <div className="space-y-2 pt-3 border-t border-slate-100">
            <button
              onClick={() => setCurrentView('instructor-students')}
              className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold shadow-xs flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <span>View Full Student Roster (48)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => setCurrentView('instructor-submissions')}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-bold transition-colors cursor-pointer"
            >
              Review Student Submissions
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
