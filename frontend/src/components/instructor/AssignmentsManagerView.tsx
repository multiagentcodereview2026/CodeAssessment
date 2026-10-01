import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { BarChart3, Calendar, FileCode2, Plus, Trash2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/useAuth';
import { Assignment } from '../../types';
import { Modal } from '../common/Modal';

type ProblemOption = { id: string; title: string; difficulty: string; category?: string };

export const AssignmentsManagerView: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { authFetch } = useAuth();
  const { assignments, addAssignment, deleteAssignment, courses } = useApp();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedCourseId, setSelectedCourseId] = useState(searchParams.get('courseId') || '');
  const [dueDate, setDueDate] = useState('');
  const [selectedProblemIds, setSelectedProblemIds] = useState<string[]>([]);
  const [problemOptions, setProblemOptions] = useState<ProblemOption[]>([]);
  const [problemsLoading, setProblemsLoading] = useState(true);
  const [problemLoadError, setProblemLoadError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    authFetch('/api/problems', { cache: 'no-store' })
      .then(async (response: Response) => {
        if (!response.ok) throw new Error('Problem Bank could not be loaded.');
        return response.json();
      })
      .then((data: unknown) => {
        if (!cancelled) setProblemOptions(Array.isArray(data) ? data : []);
      })
      .catch((error: unknown) => {
        if (!cancelled) setProblemLoadError(error instanceof Error ? error.message : 'Problem Bank could not be loaded.');
      })
      .finally(() => {
        if (!cancelled) setProblemsLoading(false);
      });
    return () => { cancelled = true; };
  }, [authFetch]);

  const toggleProblem = (problemId: string) => {
    setSelectedProblemIds((current) => current.includes(problemId)
      ? current.filter((id) => id !== problemId)
      : [...current, problemId]);
  };

  const createAssignment = async (event: React.FormEvent) => {
    event.preventDefault();
    const course = courses.find((item) => String(item.id) === selectedCourseId) || courses[0];
    if (!course || !title.trim() || selectedProblemIds.length === 0) return;

    setSaving(true);
    const assignment: Assignment & { courseId: number; problemIds: string[] } = {
      id: `pending-${Date.now()}`,
      title: title.trim(),
      description: description.trim(),
      course: `${course.code} ${course.title}`,
      problemsCount: selectedProblemIds.length,
      problemIds: selectedProblemIds,
      submittedCount: 0,
      totalCount: 0,
      avgScore: 0,
      dueDate,
      status: 'Active',
      courseId: Number(course.id)
    };

    try {
      await addAssignment(assignment);
      setIsModalOpen(false);
      setTitle('');
      setDescription('');
      setDueDate('');
      setSelectedProblemIds([]);
    } catch {
      // AppContext displays the API error and leaves the draft available to retry.
    } finally {
      setSaving(false);
    }
  };

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editAssignmentId, setEditAssignmentId] = useState<string>('');
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editDueDate, setEditDueDate] = useState('');
  const [editStatus, setEditStatus] = useState('ACTIVE');
  const [editHasSubmissions, setEditHasSubmissions] = useState(false);
  const [editProblemIds, setEditProblemIds] = useState<string[]>([]);
  const [editCourseId, setEditCourseId] = useState('');

  const openEditModal = (assignment: Assignment & { courseId?: number }) => {
    setEditAssignmentId(String(assignment.id));
    setEditTitle(assignment.title);
    setEditDescription(assignment.description || '');
    setEditDueDate(assignment.dueDate || '');
    setEditStatus(assignment.status.toUpperCase() === 'CLOSED' ? 'CLOSED' : 'ACTIVE');
    setEditHasSubmissions(assignment.submittedCount > 0);
    setEditProblemIds(assignment.problemIds || []);
    setEditCourseId(String(assignment.courseId || ''));
    setIsEditModalOpen(true);
  };

  const updateAssignment = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!editAssignmentId) return;
    setSaving(true);
    
    try {
      const response = await authFetch(`/api/instructor/assignments/${editAssignmentId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: editHasSubmissions ? undefined : editTitle.trim(),
          description: editHasSubmissions ? undefined : editDescription.trim(),
          due_date: editHasSubmissions ? undefined : (editDueDate ? new Date(editDueDate).toISOString() : null),
          status: editStatus,
          problem_ids: editHasSubmissions ? undefined : editProblemIds
        })
      });
      if (!response.ok) {
        const err = await response.json().catch(()=>({}));
        throw new Error(err.detail || 'Failed to update assignment');
      }
      setIsEditModalOpen(false);
      // We can force a reload of assignments by window.location.reload() or rely on context if we update it.
      window.location.reload(); 
    } catch (err) {
       alert(err instanceof Error ? err.message : 'Failed to update assignment');
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="space-y-6 pb-12">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Assignments</h1>
          <p className="mt-1 text-sm text-slate-500">Manage coursework linked to your saved courses.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          disabled={!courses.length}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:opacity-50"
        >
          <Plus className="h-4 w-4" /> Create assignment
        </button>
      </header>

      {assignments.length === 0 ? (
        <p className="border-y border-slate-200 py-10 text-center text-sm text-slate-500">No assignments yet.</p>
      ) : (
        <div className="divide-y divide-slate-200 border-y border-slate-200">
          {assignments.map((assignment) => (
            <article key={assignment.id} className="flex flex-col justify-between gap-4 py-5 sm:flex-row sm:items-center">
              <div className="flex items-start gap-3">
                <FileCode2 className="mt-0.5 h-5 w-5 text-emerald-700" />
                <div>
                  <h2 className="font-semibold text-slate-900">{assignment.title}</h2>
                  <p className="mt-1 text-xs text-slate-500">{assignment.course} · {assignment.problemsCount} problems · {assignment.status}</p>
                  <p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-500"><Calendar className="h-3.5 w-3.5" />{assignment.dueDate}</p>
                </div>
              </div>
              <div className="flex items-center gap-5">
                <div className="text-right text-xs text-slate-600">
                  <div>{assignment.submittedCount}/{assignment.totalCount} submissions</div>
                  <div>{assignment.avgScore == null ? 'No graded submissions yet' : `Average ${assignment.avgScore}%`}</div>
                </div>
                <button title="Edit assignment" onClick={() => openEditModal(assignment)} className="rounded-md p-2 text-slate-600 hover:bg-slate-100 font-semibold text-xs border border-slate-200">Edit</button>
                <button title="View assignment analytics" onClick={() => navigate(`/instructor/analytics?assignmentId=${assignment.id}`)} className="rounded-md p-2 text-slate-600 hover:bg-slate-100"><BarChart3 className="h-4 w-4" /></button>
                <button title="Archive assignment" onClick={() => void deleteAssignment(assignment.id).catch(() => {})} className="rounded-md p-2 text-slate-600 hover:bg-rose-50 hover:text-rose-700"><Trash2 className="h-4 w-4" /></button>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Edit assignment" subtitle={editHasSubmissions ? "Submissions exist. You can only update the status." : "Update assignment details and problems."} maxWidth="xl">
        <form onSubmit={updateAssignment} className="space-y-4 text-sm">
          {editHasSubmissions && (
             <div className="p-3 bg-yellow-50 text-yellow-800 text-xs rounded border border-yellow-200">
                This assignment has submissions. Content, problems, and dates are locked.
             </div>
          )}
          <label className="block font-semibold text-slate-700">Title
            <input value={editTitle} onChange={(event) => setEditTitle(event.target.value)} required disabled={editHasSubmissions} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 disabled:bg-slate-100" />
          </label>
          <label className="block font-semibold text-slate-700">Description
            <textarea value={editDescription} onChange={(event) => setEditDescription(event.target.value)} rows={3} disabled={editHasSubmissions} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 disabled:bg-slate-100" />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
             <label className="block font-semibold text-slate-700">Status
               <select value={editStatus} onChange={(event) => setEditStatus(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5">
                  <option value="ACTIVE">Active</option>
                  <option value="CLOSED">Closed</option>
               </select>
            </label>
            <label className="block font-semibold text-slate-700">Due date
              <input type="date" value={editDueDate} onChange={(event) => setEditDueDate(event.target.value)} disabled={editHasSubmissions} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 disabled:bg-slate-100" />
            </label>
          </div>
          <fieldset>
            <legend className="mb-2 font-semibold text-slate-700">Problem Bank</legend>
            <div className="max-h-56 space-y-1 overflow-y-auto rounded-lg border border-slate-200 p-2">
              {problemsLoading && <p className="p-3 text-slate-500">Loading problems…</p>}
              {problemOptions.map((problem) => {
                const checked = editProblemIds.includes(problem.id);
                return (
                  <label key={problem.id} className={`flex cursor-pointer items-center justify-between gap-3 rounded-md px-3 py-2 ${checked ? 'bg-emerald-50' : 'hover:bg-slate-50'} ${editHasSubmissions ? 'opacity-70 cursor-not-allowed' : ''}`}>
                    <span className="flex min-w-0 items-center gap-2"><input type="checkbox" checked={checked} disabled={editHasSubmissions} onChange={() => setEditProblemIds(c => c.includes(problem.id) ? c.filter(id=>id!==problem.id) : [...c, problem.id])} /><span className="truncate">{problem.title}</span></span>
                    <span className="shrink-0 text-xs text-slate-500">{problem.difficulty}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>
          <footer className="flex justify-end gap-2 border-t border-slate-200 pt-4">
            <button type="button" onClick={() => setIsEditModalOpen(false)} className="rounded-lg border border-slate-300 px-4 py-2 font-semibold text-slate-700">Cancel</button>
            <button type="submit" disabled={saving || (!editHasSubmissions && !editProblemIds.length)} className="rounded-lg bg-emerald-700 px-4 py-2 font-semibold text-white disabled:opacity-50">{saving ? 'Saving…' : 'Save changes'}</button>
          </footer>
        </form>
      </Modal>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create coding assignment" subtitle="Choose a course and real Problem Bank entries" maxWidth="xl">
        <form onSubmit={createAssignment} className="space-y-4 text-sm">
          <label className="block font-semibold text-slate-700">Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} required className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
          </label>
          <label className="block font-semibold text-slate-700">Description
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block font-semibold text-slate-700">Course
              <select value={courses.some((item) => String(item.id) === selectedCourseId) ? selectedCourseId : String(courses[0]?.id || '')} onChange={(event) => setSelectedCourseId(event.target.value)} required className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5">
                {courses.map((course) => <option key={course.id} value={String(course.id)}>{course.code} · {course.title}</option>)}
              </select>
            </label>
            <label className="block font-semibold text-slate-700">Due date
              <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
            </label>
          </div>
          <fieldset>
            <legend className="mb-2 font-semibold text-slate-700">Problem Bank</legend>
            <div className="max-h-56 space-y-1 overflow-y-auto rounded-lg border border-slate-200 p-2">
              {problemsLoading && <p className="p-3 text-slate-500">Loading problems…</p>}
              {problemLoadError && <p role="alert" className="p-3 text-rose-700">{problemLoadError}</p>}
              {!problemsLoading && !problemLoadError && problemOptions.length === 0 && <p className="p-3 text-slate-500">No problems are available.</p>}
              {problemOptions.map((problem) => {
                const checked = selectedProblemIds.includes(problem.id);
                return (
                  <label key={problem.id} className={`flex cursor-pointer items-center justify-between gap-3 rounded-md px-3 py-2 ${checked ? 'bg-emerald-50' : 'hover:bg-slate-50'}`}>
                    <span className="flex min-w-0 items-center gap-2"><input type="checkbox" checked={checked} onChange={() => toggleProblem(problem.id)} /><span className="truncate">{problem.title}</span></span>
                    <span className="shrink-0 text-xs text-slate-500">{problem.difficulty}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>
          <footer className="flex justify-end gap-2 border-t border-slate-200 pt-4">
            <button type="button" onClick={() => setIsModalOpen(false)} className="rounded-lg border border-slate-300 px-4 py-2 font-semibold text-slate-700">Cancel</button>
            <button type="submit" disabled={saving || !courses.length || !selectedProblemIds.length || problemsLoading || Boolean(problemLoadError)} className="rounded-lg bg-emerald-700 px-4 py-2 font-semibold text-white disabled:opacity-50">{saving ? 'Saving…' : 'Publish assignment'}</button>
          </footer>
        </form>
      </Modal>
    </main>
  );
};
