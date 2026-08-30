import React, { useState } from 'react';
import {
  BookOpen,
  Users,
  CalendarCheck,
  Plus,
  ArrowRight,
  GraduationCap,
  Layers
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { Modal } from '../common/Modal';

export const CoursesManagerView: React.FC = () => {
  const { setCurrentView } = useApp();
  const [courses, setCourses] = useState([
    {
      id: 'c1',
      code: 'CSE-301',
      title: 'Data Structures & Algorithms',
      term: 'Spring 2026',
      studentsCount: 48,
      activeAssignments: 3,
      avgGrade: '74.3%'
    },
    {
      id: 'c2',
      code: 'CSE-402',
      title: 'Advanced Algorithmic Design & Optimization',
      term: 'Spring 2026',
      studentsCount: 32,
      activeAssignments: 2,
      avgGrade: '81.0%'
    }
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCode, setNewCode] = useState('');
  const [newTitle, setNewTitle] = useState('');

  const handleCreateCourse = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle) return;
    setCourses([
      ...courses,
      {
        id: `c-${Date.now()}`,
        code: newCode || 'CSE-101',
        title: newTitle,
        term: 'Spring 2026',
        studentsCount: 0,
        activeAssignments: 0,
        avgGrade: 'N/A'
      }
    ]);
    setIsModalOpen(false);
    setNewCode('');
    setNewTitle('');
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Courses & Cohorts Management
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Configure academic courses, roster enrollment, and automated grading settings.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all active:scale-95 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>+ Add Course</span>
        </button>
      </div>

      {/* Course Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {courses.map((course) => (
          <div
            key={course.id}
            className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-xs hover:border-indigo-300 transition-all flex flex-col justify-between space-y-6 group"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 bg-indigo-50 text-indigo-700 font-mono font-bold text-xs rounded-xl border border-indigo-200">
                  {course.code}
                </span>
                <span className="text-xs font-mono text-slate-400">{course.term}</span>
              </div>

              <h2 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                {course.title}
              </h2>

              <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-100 text-center">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 font-semibold block">Students</span>
                  <span className="text-base font-extrabold text-slate-800 font-mono mt-0.5 block">
                    {course.studentsCount}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 font-semibold block">Assignments</span>
                  <span className="text-base font-extrabold text-slate-800 font-mono mt-0.5 block">
                    {course.activeAssignments}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100">
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
                className="text-xs font-bold text-indigo-600 hover:underline flex items-center gap-1"
              >
                <span>View Cohort Roster</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setCurrentView('instructor-assignments')}
                className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-colors"
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
        subtitle="Set up course code and syllabus details"
      >
        <form onSubmit={handleCreateCourse} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Course Code</label>
            <input
              type="text"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              placeholder="e.g. CSE-302"
              required
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-mono"
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
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-md shadow-indigo-600/20"
            >
              Create Course
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
