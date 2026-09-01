import React, { useState } from 'react';
import {
  BookOpen,
  Users,
  CalendarCheck,
  Plus,
  ArrowRight,
  GraduationCap,
  Layers,
  Trash2,
  Settings2
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { Modal } from '../common/Modal';

export const CoursesManagerView: React.FC = () => {
  const { courses, addCourse, deleteCourse, setCurrentView } = useApp();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCode, setNewCode] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [newTerm, setNewTerm] = useState('Spring 2026');

  const handleCreateCourse = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    addCourse({
      id: `c-${Date.now()}`,
      code: newCode.trim().toUpperCase() || 'CSE-305',
      title: newTitle.trim(),
      term: newTerm,
      studentsCount: 0,
      activeAssignments: 0,
      avgGrade: 'N/A'
    });

    setIsModalOpen(false);
    setNewCode('');
    setNewTitle('');
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Courses & Cohorts Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Configure academic courses, roster enrollment, and automated grading settings.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>+ Add Course</span>
        </button>
      </div>

      {/* Course Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {courses.map((course) => (
          <div
            key={course.id}
            className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-xs hover:border-emerald-300 transition-all flex flex-col justify-between space-y-6 group card-hover relative"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 bg-emerald-50 text-emerald-700 font-mono font-bold text-xs rounded-xl border border-emerald-200">
                  {course.code}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400">{course.term}</span>
                  <button
                    onClick={() => deleteCourse(course.id)}
                    title="Delete Course"
                    className="text-slate-300 hover:text-rose-600 p-1 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <h2 className="text-lg font-bold text-slate-900 group-hover:text-emerald-700 transition-colors">
                {course.title}
              </h2>

              <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-100 text-center">
                <div
                  onClick={() => setCurrentView('instructor-students')}
                  className="p-3 rounded-2xl bg-slate-50 border border-slate-100 hover:bg-emerald-50/50 cursor-pointer transition-colors"
                >
                  <span className="text-[10px] text-slate-400 font-semibold block">Students</span>
                  <span className="text-base font-extrabold text-slate-800 font-mono mt-0.5 block">
                    {course.studentsCount}
                  </span>
                </div>

                <div
                  onClick={() => setCurrentView('instructor-assignments')}
                  className="p-3 rounded-2xl bg-slate-50 border border-slate-100 hover:bg-emerald-50/50 cursor-pointer transition-colors"
                >
                  <span className="text-[10px] text-slate-400 font-semibold block">Assignments</span>
                  <span className="text-base font-extrabold text-slate-800 font-mono mt-0.5 block">
                    {course.activeAssignments}
                  </span>
                </div>

                <div
                  onClick={() => setCurrentView('instructor-analytics')}
                  className="p-3 rounded-2xl bg-emerald-50 border border-emerald-100 hover:bg-emerald-100/60 cursor-pointer transition-colors"
                >
                  <span className="text-[10px] text-emerald-700 font-semibold block">Avg Score</span>
                  <span className="text-base font-extrabold text-emerald-700 font-mono mt-0.5 block">
                    {course.avgGrade}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <button
                onClick={() => setCurrentView('instructor-students')}
                className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 cursor-pointer"
              >
                <span>View Cohort Roster</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setCurrentView('instructor-assignments')}
                className="px-4 py-2 bg-slate-900 hover:bg-emerald-600 text-white rounded-xl text-xs font-bold transition-all hover:scale-105 active:scale-95 cursor-pointer"
              >
                Manage Class
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add Course Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add New Academic Course"
        subtitle="Set up course code, title, and academic term"
      >
        <form onSubmit={handleCreateCourse} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Course Code</label>
            <input
              type="text"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              placeholder="e.g. CSE-305"
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-mono text-xs"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Course Title</label>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Design & Analysis of Algorithms"
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 text-xs"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Academic Term</label>
            <input
              type="text"
              value={newTerm}
              onChange={(e) => setNewTerm(e.target.value)}
              placeholder="e.g. Spring 2026"
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 text-xs"
            />
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
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-95 cursor-pointer"
            >
              Create Course
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
