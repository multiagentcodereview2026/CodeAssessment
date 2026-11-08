import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, ArrowRight, Trash2, Pencil } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { Modal } from '../common/Modal';
import { DoubleConfirmDialog } from '../common/DoubleConfirmDialog';

export const CoursesManagerView: React.FC = () => {
  const navigate = useNavigate();
  const { courses, addCourse, updateCourse, deleteCourse } = useApp();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCode, setNewCode] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [newTerm, setNewTerm] = useState('Spring 2026');
  const [editTarget, setEditTarget] = useState<(typeof courses)[number] | null>(null);
  const [editCode, setEditCode] = useState('');
  const [editTitle, setEditTitle] = useState('');
  const [editTerm, setEditTerm] = useState('');
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [archiveTarget, setArchiveTarget] = useState<(typeof courses)[number] | null>(null);

  const openEditCourse = (course: (typeof courses)[number]) => {
    setEditTarget(course);
    setEditCode(course.code);
    setEditTitle(course.title);
    setEditTerm(course.term || '');
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      await addCourse({
        id: '',
        code: newCode.trim().toUpperCase(),
        title: newTitle.trim(),
        term: newTerm,
        studentsCount: 0,
        activeAssignments: 0,
        avgGrade: 'N/A'
      });

      setIsModalOpen(false);
      setNewCode('');
      setNewTitle('');
    } catch {
      // The context reports the API error; keep the form open for retry.
    }
  };

  const handleUpdateCourse = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!editTarget || !editCode.trim() || !editTitle.trim()) return;
    setIsSavingEdit(true);
    try {
      await updateCourse(editTarget.id, {
        code: editCode.trim().toUpperCase(),
        title: editTitle.trim(),
        term: editTerm.trim()
      });
      setEditTarget(null);
    } catch {
      // AppContext shows the API error and leaves the form open for retry.
    } finally {
      setIsSavingEdit(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-white/10 pb-5">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-[0.14em] text-emerald-600 dark:text-emerald-400">Course Administration</span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            Courses & Cohorts Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Configure academic courses, roster enrollment, and automated grading settings.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer ring-1 ring-white/20 self-start sm:self-auto"
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
            className="bg-white dark:bg-[#121217] rounded-3xl border border-slate-200/80 dark:border-white/12 p-6 sm:p-8 shadow-xs hover:border-emerald-300 dark:hover:border-emerald-500/40 transition-all flex flex-col justify-between space-y-6 group card-hover relative"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 font-bold text-[11px] rounded-full border border-emerald-200 dark:border-emerald-500/30">
                  {course.code}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-medium">{course.term}</span>
                  <button
                    onClick={() => openEditCourse(course)}
                    title="Edit Course"
                    aria-label={`Edit ${course.code}`}
                    className="text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 p-1 transition-colors cursor-pointer"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setArchiveTarget(course)}
                    title="Archive Course"
                    className="text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 p-1 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <h2 className="text-lg font-extrabold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                {course.title}
              </h2>

              <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-100 dark:border-white/10 text-center">
                <div
                  onClick={() => navigate(`/instructor/courses/${course.id}?tab=students`)}
                  className="p-3 rounded-2xl bg-slate-50 dark:bg-[#16161d] border border-slate-100 dark:border-white/8 hover:bg-emerald-50/50 dark:hover:bg-white/[0.04] cursor-pointer transition-colors"
                >
                  <span className="text-[10px] text-slate-400 font-semibold block">Students</span>
                  <span className="text-base font-extrabold text-slate-800 dark:text-white font-mono mt-0.5 block">
                    {course.studentsCount}
                  </span>
                </div>

                <div
                  onClick={() => navigate(`/instructor/courses/${course.id}?tab=assignments`)}
                  className="p-3 rounded-2xl bg-slate-50 dark:bg-[#16161d] border border-slate-100 dark:border-white/8 hover:bg-emerald-50/50 dark:hover:bg-white/[0.04] cursor-pointer transition-colors"
                >
                  <span className="text-[10px] text-slate-400 font-semibold block">Questions</span>
                  <span className="text-base font-extrabold text-slate-800 dark:text-white font-mono mt-0.5 block">
                    {course.activeAssignments}
                  </span>
                </div>

                <div
                  onClick={() => navigate('/instructor/analytics')}
                  className="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-100 dark:border-emerald-800/40 hover:bg-emerald-100/60 cursor-pointer transition-colors"
                >
                  <span className="text-[10px] text-emerald-700 dark:text-emerald-400 font-semibold block">Avg Score</span>
                  <span className="text-base font-extrabold text-emerald-700 dark:text-emerald-400 font-mono mt-0.5 block">
                    {course.avgGrade}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-white/10">
              <button
                onClick={() => navigate(`/instructor/courses/${course.id}?tab=students`)}
                className="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 flex items-center gap-1 cursor-pointer transition-colors"
              >
                <span>View Cohort Roster</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => navigate(`/instructor/courses/${course.id}`)}
                className="px-4 py-2 bg-slate-900 dark:bg-[#1c1c24] hover:bg-emerald-600 dark:hover:bg-emerald-600 text-white rounded-xl text-xs font-bold border border-transparent dark:border-white/10 transition-all hover:scale-105 active:scale-95 cursor-pointer shadow-xs"
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
            <label className="block font-bold text-slate-700 dark:text-zinc-300 mb-1">Course Code</label>
            <input
              type="text"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              placeholder="e.g. CSE-305"
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#16161d] border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500 font-mono text-xs"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 dark:text-zinc-300 mb-1">Course Title</label>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Design & Analysis of Algorithms"
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#16161d] border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500 text-xs"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 dark:text-zinc-300 mb-1">Academic Term</label>
            <input
              type="text"
              value={newTerm}
              onChange={(e) => setNewTerm(e.target.value)}
              placeholder="e.g. Spring 2026"
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#16161d] border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500 text-xs"
            />
          </div>

          <div className="pt-4 border-t border-slate-100 dark:border-white/10 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 text-slate-600 dark:text-zinc-400 hover:bg-slate-100 dark:hover:bg-white/10 rounded-xl font-bold transition-colors cursor-pointer"
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
      <Modal
        isOpen={Boolean(editTarget)}
        onClose={() => { if (!isSavingEdit) setEditTarget(null); }}
        title="Edit Course"
        subtitle="Changes are saved to your instructor account."
      >
        <form onSubmit={handleUpdateCourse} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 dark:text-zinc-300 mb-1">Course Code</label>
            <input value={editCode} onChange={(event) => setEditCode(event.target.value)} required maxLength={40} className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#16161d] border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500 font-mono text-xs" />
          </div>
          <div>
            <label className="block font-bold text-slate-700 dark:text-zinc-300 mb-1">Course Title</label>
            <input value={editTitle} onChange={(event) => setEditTitle(event.target.value)} required maxLength={160} className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#16161d] border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500 text-xs" />
          </div>
          <div>
            <label className="block font-bold text-slate-700 dark:text-zinc-300 mb-1">Academic Term</label>
            <input value={editTerm} onChange={(event) => setEditTerm(event.target.value)} maxLength={80} className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#16161d] border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500 text-xs" />
          </div>
          <div className="pt-4 border-t border-slate-100 dark:border-white/10 flex items-center justify-end gap-3">
            <button type="button" onClick={() => setEditTarget(null)} disabled={isSavingEdit} className="px-4 py-2 text-slate-600 dark:text-zinc-400 hover:bg-slate-100 dark:hover:bg-white/10 rounded-xl font-bold transition-colors disabled:opacity-50 cursor-pointer">Cancel</button>
            <button type="submit" disabled={isSavingEdit || !editCode.trim() || !editTitle.trim()} className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md transition-all disabled:opacity-50 cursor-pointer">{isSavingEdit ? 'Saving…' : 'Save changes'}</button>
          </div>
        </form>
      </Modal>
      <DoubleConfirmDialog
        isOpen={Boolean(archiveTarget)}
        title="Archive this course?"
        description={`Students will no longer see or access ${archiveTarget?.code} · ${archiveTarget?.title}. Existing submissions will be retained.`}
        actionLabel="archive course"
        onClose={() => setArchiveTarget(null)}
        onConfirm={async () => { if (!archiveTarget) return; await deleteCourse(archiveTarget.id); setArchiveTarget(null); }}
      />
    </div>
  );
};
