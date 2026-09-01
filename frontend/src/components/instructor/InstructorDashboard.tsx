import React, { useState } from 'react';
import {
  Users,
  CalendarCheck,
  FileCheck2,
  Award,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
  Plus,
  BookOpen,
  BarChart3,
  Mail,
  ChevronRight,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreDistributionBarChart } from '../common/ChartComponents';
import { HISTOGRAM_BUCKET_STUDENTS, BucketStudent } from './ClassAnalyticsView';
import { Modal } from '../common/Modal';

export const InstructorDashboard: React.FC = () => {
  const {
    currentUser,
    instructorStats,
    assignments,
    setCurrentView,
    similarityAlerts
  } = useApp();

  const [selectedBucketRange, setSelectedBucketRange] = useState<string | null>('0-20');
  const [inspectedStudent, setInspectedStudent] = useState<BucketStudent | null>(null);

  const currentBucketStudents = selectedBucketRange ? HISTOGRAM_BUCKET_STUDENTS[selectedBucketRange] || [] : [];

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

      {/* HISTOGRAM & INTERACTIVE STUDENT INSPECTOR */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-emerald-600" />
              <h3 className="text-base font-bold text-slate-900">Score Distribution Histogram (0 - 100)</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Click any bar to instantly reveal the students in that score range</p>
          </div>
          <button
            onClick={() => setCurrentView('instructor-analytics')}
            className="text-xs font-bold text-emerald-600 hover:underline self-start sm:self-auto"
          >
            Full Class Analytics →
          </button>
        </div>

        <div className="pt-2">
          <ScoreDistributionBarChart
            distribution={instructorStats.scoreDistribution}
            onSelectBucket={(range) => setSelectedBucketRange(range)}
            selectedRange={selectedBucketRange}
          />
        </div>

        {/* REVEALED STUDENTS ACCORDION / CONTAINER */}
        {selectedBucketRange && (
          <div className="mt-6 pt-6 border-t border-slate-200 space-y-4 animate-fadeIn">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gradient-to-r from-slate-900 to-indigo-950 p-4 rounded-2xl text-white">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-indigo-600 rounded-xl">
                  <Users className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-extrabold">
                      Students in Score Range {selectedBucketRange}%
                    </h4>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-extrabold bg-white/20 text-white">
                      {currentBucketStudents.length} {currentBucketStudents.length === 1 ? 'Student' : 'Students'}
                    </span>
                  </div>
                  <p className="text-[11px] text-indigo-200">
                    Showing students currently standing in the {selectedBucketRange}% performance bucket.
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSelectedBucketRange(null)}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors self-start sm:self-auto cursor-pointer"
                title="Close list"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Students Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {currentBucketStudents.map((stu) => (
                <div
                  key={stu.id}
                  onClick={() => setInspectedStudent(stu)}
                  className="p-4 bg-slate-50/80 hover:bg-white border border-slate-200/80 hover:border-indigo-400 rounded-2xl shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <img
                          src={stu.avatar}
                          alt={stu.name}
                          className="w-10 h-10 rounded-full object-cover ring-2 ring-indigo-500/20"
                        />
                        <div>
                          <h5 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                            {stu.name}
                          </h5>
                          <span className="text-[11px] text-slate-400 font-mono">
                            {stu.rollNumber} • {stu.department}
                          </span>
                        </div>
                      </div>

                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold ${
                          stu.status === 'At Risk'
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : stu.status === 'Needs Attention'
                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                            : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        }`}
                      >
                        {stu.status}
                      </span>
                    </div>

                    {/* Metrics Row */}
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200/60 text-xs font-mono">
                      <div className="p-2 bg-white rounded-xl border border-slate-100">
                        <span className="text-[10px] text-slate-400 uppercase font-sans block font-semibold">Average Grade</span>
                        <span className={`text-base font-extrabold ${
                          stu.avgScore < 40 ? 'text-rose-600' : stu.avgScore < 70 ? 'text-amber-600' : 'text-emerald-600'
                        }`}>
                          {stu.avgScore}%
                        </span>
                      </div>
                      <div className="p-2 bg-white rounded-xl border border-slate-100">
                        <span className="text-[10px] text-slate-400 uppercase font-sans block font-semibold">Submissions</span>
                        <span className="text-base font-extrabold text-slate-800">
                          {stu.submissionsCount}
                        </span>
                      </div>
                    </div>

                    {/* Identified Weak Topics */}
                    <div className="space-y-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Identified Gaps:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {stu.weakTopics.map((wt, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200"
                          >
                            ⚠️ {wt}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-center justify-between text-xs">
                    <span className="text-indigo-600 font-bold group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                      <span>Inspect Student Report</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </span>

                    <a
                      href={`mailto:${stu.email}`}
                      onClick={(e) => e.stopPropagation()}
                      className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                      title="Send Email"
                    >
                      <Mail className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

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
              className="text-xs font-bold text-emerald-600 hover:underline cursor-pointer"
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

      {/* STUDENT DETAIL MODAL */}
      {inspectedStudent && (
        <Modal
          isOpen={!!inspectedStudent}
          onClose={() => setInspectedStudent(null)}
          title={`Student Performance Report: ${inspectedStudent.name}`}
          subtitle={`Roll: ${inspectedStudent.rollNumber} • ${inspectedStudent.department} • ${inspectedStudent.year}`}
          maxWidth="2xl"
        >
          <div className="space-y-6 text-xs">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 block font-semibold">Submissions</span>
                <span className="text-2xl font-mono font-extrabold text-slate-800 mt-1 block">
                  {inspectedStudent.submissionsCount}
                </span>
              </div>
              <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200">
                <span className="text-emerald-700 block font-semibold">Average Grade</span>
                <span className="text-2xl font-mono font-extrabold text-emerald-700 mt-1 block">
                  {inspectedStudent.avgScore}%
                </span>
              </div>
              <div className="p-3.5 bg-purple-50 rounded-xl border border-purple-200">
                <span className="text-purple-700 block font-semibold">Cohort Status</span>
                <span className="text-sm font-extrabold text-purple-800 mt-2 block">
                  {inspectedStudent.status}
                </span>
              </div>
            </div>

            {/* AI Diagnostics */}
            <div className="p-4 bg-slate-900 text-white rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-indigo-400 font-bold">
                <Sparkles className="w-4 h-4" />
                <span>AI Algorithmic Diagnostic</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Student shows specific challenges in {inspectedStudent.weakTopics.join(' and ')}. Recommend targeted reinforcement challenges and guided tutoring on complexity bottlenecks.
              </p>
            </div>

            {/* Identified gaps */}
            <div>
              <span className="font-bold text-slate-800 mb-2 block">Identified Concept Gaps:</span>
              <div className="flex flex-wrap gap-2">
                {inspectedStudent.weakTopics.map((wt, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 font-bold"
                  >
                    ⚠️ {wt}
                  </span>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <a
                href={`mailto:${inspectedStudent.email}`}
                className="inline-flex items-center gap-1.5 text-indigo-600 font-bold hover:underline"
              >
                <Mail className="w-4 h-4" />
                <span>Send Direct Feedback Email</span>
              </a>

              <button
                onClick={() => setInspectedStudent(null)}
                className="px-4 py-2 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 cursor-pointer"
              >
                Close Report
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
