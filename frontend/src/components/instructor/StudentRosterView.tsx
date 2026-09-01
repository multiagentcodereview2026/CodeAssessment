import React, { useState } from 'react';
import {
  Search,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  UserCheck,
  AlertTriangle,
  Sparkles,
  ChevronRight,
  Mail,
  School,
  Building,
  Calendar,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StudentRosterItem } from '../../types';
import { Modal } from '../common/Modal';

export const StudentRosterView: React.FC = () => {
  const { studentRoster, selectedStudent, setSelectedStudent, goBackToDashboard } = useApp();
  const [search, setSearch] = useState('');
  const [filterTopic, setFilterTopic] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const allTopics = Array.from(new Set(studentRoster.flatMap((s) => s.weakTopics)));

  const filtered = studentRoster.filter((s) => {
    const matchSearch = s.name.toLowerCase().includes(search.toLowerCase()) || s.rollNumber.toLowerCase().includes(search.toLowerCase());
    const matchTopic = filterTopic === 'all' || s.weakTopics.includes(filterTopic);
    const matchStatus = filterStatus === 'all' || s.status.toLowerCase() === filterStatus.toLowerCase();
    return matchSearch && matchTopic && matchStatus;
  });

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Breadcrumb Navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={goBackToDashboard}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-emerald-700 transition-colors p-2 hover:bg-slate-100 rounded-xl cursor-pointer"
        >
          <UserCheck className="w-4 h-4" />
          <span>← Back to Instructor Dashboard</span>
        </button>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Assigned Student Roster
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Assigned cohort of 48 students for <strong>CSE-301 Section A</strong> • Prof. Sarah Miller.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Assigned Cohort: <strong className="text-emerald-800 font-mono">48 Students</strong></span>
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by student name or roll number..."
            className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500">Weak Area:</span>
            <select
              value={filterTopic}
              onChange={(e) => setFilterTopic(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Topics</option>
              {allTopics.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500">Cohort Status:</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Statuses</option>
              <option value="on track">On Track</option>
              <option value="needs attention">Needs Attention</option>
              <option value="at risk">At Risk</option>
            </select>
          </div>
        </div>
      </div>

      {/* Roster Table (Matches Step 4 in diagram) */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3.5 px-6">Student</th>
                <th className="py-3.5 px-6">Submissions</th>
                <th className="py-3.5 px-6">Avg Score</th>
                <th className="py-3.5 px-6">Trend</th>
                <th className="py-3.5 px-6">Weak Topics</th>
                <th className="py-3.5 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((stu) => (
                <tr
                  key={stu.id}
                  onClick={() => setSelectedStudent(stu)}
                  className="hover:bg-indigo-50/30 transition-colors cursor-pointer group"
                >
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <img
                        src={stu.avatar}
                        alt={stu.name}
                        className="w-9 h-9 rounded-full object-cover ring-1 ring-slate-200"
                      />
                      <div>
                        <span className="font-bold text-slate-900 block group-hover:text-indigo-600 transition-colors">
                          {stu.name}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {stu.rollNumber} • {stu.department}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td className="py-4 px-6 font-mono font-bold text-slate-700">
                    {stu.submissionsCount}
                  </td>

                  <td className="py-4 px-6 font-mono font-extrabold text-sm">
                    <span className={stu.avgScore >= 75 ? 'text-emerald-600' : stu.avgScore >= 60 ? 'text-indigo-600' : 'text-rose-600'}>
                      {stu.avgScore}%
                    </span>
                  </td>

                  <td className="py-4 px-6">
                    {stu.trend === 'up' ? (
                      <span className="inline-flex items-center gap-1 font-bold text-emerald-600 font-mono">
                        <ArrowUpRight className="w-4 h-4" />
                        <span>+3.8%</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 font-bold text-rose-600 font-mono">
                        <ArrowDownRight className="w-4 h-4" />
                        <span>-4.2%</span>
                      </span>
                    )}
                  </td>

                  <td className="py-4 px-6">
                    <div className="flex flex-wrap gap-1.5">
                      {stu.weakTopics.map((wt, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200"
                        >
                          {wt}
                        </span>
                      ))}
                    </div>
                  </td>

                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedStudent(stu);
                      }}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-indigo-600 hover:text-white rounded-lg font-bold text-xs text-slate-700 transition-colors"
                    >
                      Inspect Profile
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Student Deep-Dive Drawer / Modal */}
      {selectedStudent && (
        <Modal
          isOpen={!!selectedStudent}
          onClose={() => setSelectedStudent(null)}
          title={`Student Performance Report: ${selectedStudent.name}`}
          subtitle={`Roll: ${selectedStudent.rollNumber} • ${selectedStudent.department} • ${selectedStudent.year}`}
          maxWidth="2xl"
        >
          <div className="space-y-6 text-xs">
            {/* Top Quick Stats */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 block font-semibold">Submissions</span>
                <span className="text-2xl font-mono font-extrabold text-slate-800 mt-1 block">
                  {selectedStudent.submissionsCount}
                </span>
              </div>
              <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200">
                <span className="text-emerald-700 block font-semibold">Average Grade</span>
                <span className="text-2xl font-mono font-extrabold text-emerald-700 mt-1 block">
                  {selectedStudent.avgScore}%
                </span>
              </div>
              <div className="p-3.5 bg-purple-50 rounded-xl border border-purple-200">
                <span className="text-purple-700 block font-semibold">Cohort Status</span>
                <span className="text-sm font-extrabold text-purple-800 mt-2 block">
                  {selectedStudent.status}
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
                Student shows strong fluency in linear scans and simple data structures. Demonstrates difficulty with recursion depth edge cases and multidimensional DP states. Recommend assigning guided dynamic programming practice.
              </p>
            </div>

            {/* Weak Topics */}
            <div>
              <span className="font-bold text-slate-800 mb-2 block">Identified Concept Gaps:</span>
              <div className="flex flex-wrap gap-2">
                {selectedStudent.weakTopics.map((wt, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 font-bold"
                  >
                    ⚠️ {wt}
                  </span>
                ))}
              </div>
            </div>

            {/* Contact / Action triggers */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <a
                href={`mailto:${selectedStudent.email}`}
                className="inline-flex items-center gap-1.5 text-indigo-600 font-bold hover:underline"
              >
                <Mail className="w-4 h-4" />
                <span>Send Direct Feedback Email</span>
              </a>

              <button
                onClick={() => setSelectedStudent(null)}
                className="px-4 py-2 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800"
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
