import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CalendarCheck,
  Plus,
  Calendar,
  BookOpen,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
  FileCode2,
  Trash2,
  BarChart3
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { Assignment } from '../../types';
import { Modal } from '../common/Modal';
import { MOCK_PROBLEMS } from '../../mock/data';

export const AssignmentsManagerView: React.FC = () => {
  const navigate = useNavigate();
  const { assignments, addAssignment, deleteAssignment, courses } = useApp();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedAsgForAnalytics, setSelectedAsgForAnalytics] = useState<Assignment | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [course, setCourse] = useState(courses[0]?.code ? `${courses[0].code} ${courses[0].title}` : 'CSE-301 Data Structures');
  const [dueDate, setDueDate] = useState('15 June, 2026');
  const [selectedProbIds, setSelectedProbIds] = useState<string[]>(['prob-1', 'prob-2']);

  const handleToggleProb = (id: string) => {
    if (selectedProbIds.includes(id)) {
      setSelectedProbIds(selectedProbIds.filter((p) => p !== id));
    } else {
      setSelectedProbIds([...selectedProbIds, id]);
    }
  };

  const handleCreateAssignment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const newAssignment: Assignment = {
      id: `asg-${Date.now()}`,
      title: title.trim(),
      description: description.trim() || 'Algorithmic problem set with automated multi-agent rubric grading.',
      course,
      problemsCount: selectedProbIds.length,
      problemIds: selectedProbIds,
      submittedCount: 0,
      totalCount: 48,
      avgScore: 0,
      dueDate,
      status: 'Active'
    };

    addAssignment(newAssignment);
    setIsModalOpen(false);
    setTitle('');
    setDescription('');
  };

  const handleOpenAnalytics = (asg: Assignment) => {
    navigate('/instructor/analytics');
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Assignments Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Create, schedule, and configure sandbox constraints and automated AI grading rubrics.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>+ Create Assignment</span>
        </button>
      </div>

      {/* Assignment Cards */}
      <div className="space-y-4">
        {assignments.map((asg) => (
          <div
            key={asg.id}
            className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-xs hover:border-emerald-300 card-hover transition-all flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6"
          >
            <div className="flex items-start gap-4">
              <div className="p-3.5 bg-emerald-50 text-emerald-600 rounded-2xl flex-shrink-0 shadow-xs">
                <FileCode2 className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h3 className="text-base font-bold text-slate-900">{asg.title}</h3>
                  <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                    {asg.status}
                  </span>
                  <span className="text-xs font-mono text-slate-500 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    Due: {asg.dueDate}
                  </span>
                </div>
                <p className="text-xs text-slate-500 max-w-xl">{asg.description}</p>
                <div className="flex items-center gap-4 text-xs text-slate-500 pt-1 font-mono">
                  <span>Course: <strong className="text-slate-800 font-sans">{asg.course}</strong></span>
                  <span>Problems: <strong className="text-slate-800">{asg.problemsCount}</strong></span>
                </div>
              </div>
            </div>

            {/* Submission Rate & Average */}
            <div className="flex items-center gap-6 w-full lg:w-auto justify-between lg:justify-end border-t lg:border-t-0 pt-4 lg:pt-0 border-slate-100">
              <div className="text-right">
                <span className="text-[11px] text-slate-400 uppercase font-semibold block">Submissions</span>
                <span className="text-sm font-extrabold text-slate-900 font-mono">
                  {asg.submittedCount} / {asg.totalCount}
                </span>
              </div>

              <div className="text-right">
                <span className="text-[11px] text-slate-400 uppercase font-semibold block">Average Score</span>
                <span className="text-sm font-extrabold text-emerald-600 font-mono">
                  {asg.avgScore ? `${asg.avgScore}%` : 'N/A'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleOpenAnalytics(asg)}
                  className="px-4 py-2.5 bg-slate-900 hover:bg-emerald-600 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 hover:scale-105 active:scale-95 cursor-pointer"
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  <span>Analytics</span>
                </button>
                <button
                  onClick={() => deleteAssignment(asg.id)}
                  title="Delete Assignment"
                  className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Assignment Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Coding Assignment"
        subtitle="Configure problem sets, due dates, and grading constraints"
        maxWidth="xl"
      >
        <form onSubmit={handleCreateAssignment} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Assignment Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g. Dynamic Programming & Memoization Lab"
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Instructions / Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Provide context and complexity constraints..."
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-sans"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Course Cohort</label>
              <select
                value={course}
                onChange={(e) => setCourse(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium cursor-pointer"
              >
                {courses.map(c => (
                  <option key={c.id} value={`${c.code} ${c.title}`}>
                    {c.code} - {c.title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Due Date</label>
              <input
                type="text"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
              />
            </div>
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-2">Select Problems from Bank:</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-2 bg-slate-50 rounded-xl border border-slate-200">
              {MOCK_PROBLEMS.map((prob) => {
                const selected = selectedProbIds.includes(prob.id);
                return (
                  <div
                    key={prob.id}
                    onClick={() => handleToggleProb(prob.id)}
                    className={`p-2.5 rounded-xl border cursor-pointer flex items-center justify-between text-xs transition-all ${
                      selected ? 'bg-emerald-50 border-emerald-300 text-emerald-900 font-bold shadow-xs' : 'bg-white border-slate-200 text-slate-700'
                    }`}
                  >
                    <span>{prob.title}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{prob.difficulty}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-95 cursor-pointer"
            >
              Publish Assignment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
