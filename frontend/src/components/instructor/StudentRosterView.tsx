import React, { useState } from 'react';
import {
  Search,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  Sparkles,
  Plus,
  Trash2,
  X,
  Target,
  Send,
  ClipboardList
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StudentRosterItem } from '../../types';
import { Modal } from '../common/Modal';

export const StudentRosterView: React.FC = () => {
  const { studentRoster, selectedStudent, setSelectedStudent, addStudent, deleteStudent, courses } = useApp();
  const [search, setSearch] = useState('');
  const [filterTopic, setFilterTopic] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // New Student Form State
  const [newName, setNewName] = useState('');
  const [newRoll, setNewRoll] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newDept, setNewDept] = useState('CSE');

  const allTopics = Array.from(new Set(studentRoster.flatMap((s) => s.weakTopics)));
  const atRiskCount = studentRoster.filter((s) => s.status === 'At Risk').length;
  const needsAttentionCount = studentRoster.filter((s) => s.status === 'Needs Attention').length;
  const mostCommonWeakTopic = allTopics
    .map((topic) => ({
      topic,
      count: studentRoster.filter((student) => student.weakTopics.includes(topic)).length
    }))
    .sort((a, b) => b.count - a.count)[0];

  const filtered = studentRoster.filter((s) => {
    const matchSearch = s.name.toLowerCase().includes(search.toLowerCase()) || s.rollNumber.toLowerCase().includes(search.toLowerCase());
    const matchTopic = filterTopic === 'all' || s.weakTopics.includes(filterTopic);
    const matchStatus = filterStatus === 'all' || s.status.toLowerCase() === filterStatus.toLowerCase();
    return matchSearch && matchTopic && matchStatus;
  });

  const handleEnrollStudent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newRoll.trim()) return;

    const newStudent: StudentRosterItem = {
      id: `stu-${Date.now()}`,
      name: newName.trim(),
      rollNumber: newRoll.trim().toUpperCase(),
      email: newEmail.trim() || `${newRoll.toLowerCase()}@geethanjali.edu.in`,
      avatar: `https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80`,
      submissionsCount: 0,
      avgScore: 0,
      trend: 'neutral',
      weakTopics: ['Arrays', 'Loops'],
      status: 'On Track',
      department: newDept,
      year: 'B.Tech 3rd Year'
    };

    addStudent(newStudent);
    setIsAddModalOpen(false);
    setNewName('');
    setNewRoll('');
    setNewEmail('');
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Student Performance Roster
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Cohort roster, algorithmic diagnostics, individual score trends, and weak topic alerts.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-600 bg-white px-3.5 py-2.5 rounded-2xl border border-slate-200 shadow-xs">
            Total Enrolled: <strong className="text-slate-900 font-mono text-sm ml-1">{studentRoster.length}</strong>
          </span>

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Enroll Student</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => setFilterStatus('at risk')}
          className="text-left bg-white rounded-2xl border border-rose-200/80 p-5 shadow-xs hover:border-rose-400 hover:shadow-md transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold uppercase text-rose-700">At Risk</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-700 font-mono">{atRiskCount}</span>
            <span className="text-xs text-slate-500">students</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Click to filter urgent intervention cases.</p>
        </button>

        <button
          onClick={() => setFilterStatus('needs attention')}
          className="text-left bg-white rounded-2xl border border-amber-200/80 p-5 shadow-xs hover:border-amber-400 hover:shadow-md transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold uppercase text-amber-700">Needs Attention</span>
            <Target className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-amber-700 font-mono">{needsAttentionCount}</span>
            <span className="text-xs text-slate-500">students</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Good candidates for remedial practice sets.</p>
        </button>

        <button
          onClick={() => mostCommonWeakTopic && setFilterTopic(mostCommonWeakTopic.topic)}
          className="text-left bg-white rounded-2xl border border-emerald-200/80 p-5 shadow-xs hover:border-emerald-400 hover:shadow-md transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold uppercase text-emerald-700">Common Gap</span>
            <ClipboardList className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-sm font-extrabold text-slate-900">
            {mostCommonWeakTopic?.topic || 'No weak topics'}
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            {mostCommonWeakTopic ? `${mostCommonWeakTopic.count} students show this gap.` : 'Roster looks healthy.'}
          </p>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-3xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by student name or roll number..."
            className="w-full pl-10 pr-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 focus:bg-white transition-colors"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-500">Weak Area:</span>
            <select
              value={filterTopic}
              onChange={(e) => setFilterTopic(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium text-slate-700 focus:outline-none focus:border-emerald-500 cursor-pointer"
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
              className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 font-medium text-slate-700 focus:outline-none focus:border-emerald-500 cursor-pointer"
            >
              <option value="all">All Statuses</option>
              <option value="on track">On Track</option>
              <option value="needs attention">Needs Attention</option>
              <option value="at risk">At Risk</option>
            </select>
          </div>
        </div>
      </div>

      {/* Roster Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-4 px-6">Student</th>
                <th className="py-4 px-6">Submissions</th>
                <th className="py-4 px-6">Avg Score</th>
                <th className="py-4 px-6">Trend</th>
                <th className="py-4 px-6">Weak Topics</th>
                <th className="py-4 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((stu) => (
                <tr
                  key={stu.id}
                  onClick={() => setSelectedStudent(stu)}
                  className="hover:bg-emerald-50/30 transition-colors cursor-pointer group"
                >
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <img
                        src={stu.avatar}
                        alt={stu.name}
                        className="w-10 h-10 rounded-full object-cover ring-2 ring-slate-100 group-hover:ring-emerald-200"
                      />
                      <div>
                        <span className="font-bold text-slate-900 block group-hover:text-emerald-700 transition-colors">
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
                      {stu.avgScore ? `${stu.avgScore}%` : 'N/A'}
                    </span>
                  </td>

                  <td className="py-4 px-6">
                    {stu.trend === 'up' ? (
                      <span className="inline-flex items-center gap-1 font-bold text-emerald-600 font-mono">
                        <ArrowUpRight className="w-4 h-4" />
                        <span>+3.8%</span>
                      </span>
                    ) : stu.trend === 'down' ? (
                      <span className="inline-flex items-center gap-1 font-bold text-rose-600 font-mono">
                        <ArrowDownRight className="w-4 h-4" />
                        <span>-4.2%</span>
                      </span>
                    ) : (
                      <span className="text-slate-400 font-mono font-bold">~ 0.0%</span>
                    )}
                  </td>

                  <td className="py-4 px-6">
                    <div className="flex flex-wrap gap-1.5">
                      {stu.weakTopics.map((wt, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-0.5 rounded-lg text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200"
                        >
                          {wt}
                        </span>
                      ))}
                    </div>
                  </td>

                  <td className="py-4 px-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedStudent(stu);
                        }}
                        className="px-3 py-1.5 bg-slate-100 hover:bg-emerald-600 hover:text-white rounded-xl font-bold text-xs text-slate-700 transition-colors"
                      >
                        Inspect Profile
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteStudent(stu.id);
                        }}
                        title="Remove Student"
                        className="p-1.5 text-slate-300 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Enroll Student Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Enroll Student in Cohort"
        subtitle="Add student details, roll number, and department mapping"
      >
        <form onSubmit={handleEnrollStudent} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Student Full Name</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g. Vignesh Reddy"
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Roll / Student ID</label>
              <input
                type="text"
                value={newRoll}
                onChange={(e) => setNewRoll(e.target.value)}
                placeholder="e.g. 24BD1A058Z"
                required
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-mono uppercase"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Department</label>
              <select
                value={newDept}
                onChange={(e) => setNewDept(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium cursor-pointer"
              >
                <option value="CSE">CSE</option>
                <option value="IT">IT</option>
                <option value="AI & DS">AI & DS</option>
                <option value="ECE">ECE</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">University Email (Optional)</label>
            <input
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="e.g. student@geethanjali.edu.in"
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
            />
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsAddModalOpen(false)}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-95 cursor-pointer"
            >
              Enroll Student
            </button>
          </div>
        </form>
      </Modal>

      {/* Student Deep-Dive Drawer / Modal */}
      {selectedStudent && (
        <Modal
          isOpen={!!selectedStudent}
          onClose={() => setSelectedStudent(null)}
          title={`Student Diagnostic: ${selectedStudent.name}`}
          subtitle={`Roll: ${selectedStudent.rollNumber} • ${selectedStudent.department} • ${selectedStudent.year}`}
          maxWidth="2xl"
        >
          <div className="space-y-6 text-xs">
            {/* Top Quick Stats */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
                <span className="text-slate-400 block font-semibold">Submissions</span>
                <span className="text-2xl font-mono font-extrabold text-slate-800 mt-1 block">
                  {selectedStudent.submissionsCount}
                </span>
              </div>
              <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-200">
                <span className="text-emerald-700 block font-semibold">Average Grade</span>
                <span className="text-2xl font-mono font-extrabold text-emerald-700 mt-1 block">
                  {selectedStudent.avgScore ? `${selectedStudent.avgScore}%` : 'N/A'}
                </span>
              </div>
              <div className="p-4 bg-purple-50 rounded-2xl border border-purple-200">
                <span className="text-purple-700 block font-semibold">Cohort Status</span>
                <span className="text-xs font-extrabold text-purple-800 mt-2 block">
                  {selectedStudent.status}
                </span>
              </div>
            </div>

            {/* AI Diagnostics */}
            <div className="p-5 bg-slate-900 text-white rounded-3xl space-y-2">
              <div className="flex items-center gap-2 text-indigo-400 font-bold">
                <Sparkles className="w-4 h-4" />
                <span>AI Multi-Agent Diagnostic Summary</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Student demonstrates solid algorithmic logic on linear scans and hash maps. Recommended to focus on tree traversals and dynamic programming state transitions.
              </p>
            </div>

            {/* Weak Topics */}
            <div>
              <span className="font-bold text-slate-800 mb-2 block">Identified Concept Gaps:</span>
              <div className="flex flex-wrap gap-2">
                {selectedStudent.weakTopics.map((wt, i) => (
                  <span
                    key={i}
                    className="px-3.5 py-1.5 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 font-bold"
                  >
                    ⚠️ {wt}
                  </span>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-4 rounded-2xl bg-indigo-50 border border-indigo-200">
                <span className="text-[10px] uppercase font-bold text-indigo-700">Action 1</span>
                <p className="mt-1 text-xs font-bold text-slate-900">Assign targeted practice</p>
                <p className="mt-1 text-[11px] text-slate-600">Use weak topics to choose problem clusters.</p>
              </div>
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200">
                <span className="text-[10px] uppercase font-bold text-amber-700">Action 2</span>
                <p className="mt-1 text-xs font-bold text-slate-900">Review latest AI report</p>
                <p className="mt-1 text-[11px] text-slate-600">Look for complexity and edge-case deductions.</p>
              </div>
              <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200">
                <span className="text-[10px] uppercase font-bold text-emerald-700">Action 3</span>
                <p className="mt-1 text-xs font-bold text-slate-900">Send feedback note</p>
                <p className="mt-1 text-[11px] text-slate-600">Close the loop with a concrete next task.</p>
              </div>
            </div>

            {/* Contact / Action triggers */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <a
                href={`mailto:${selectedStudent.email}`}
                className="inline-flex items-center gap-1.5 text-emerald-600 font-bold hover:underline"
              >
                <Send className="w-4 h-4" />
                <span>Send Direct Feedback Email</span>
              </a>

              <button
                onClick={() => setSelectedStudent(null)}
                className="px-5 py-2.5 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 cursor-pointer"
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
