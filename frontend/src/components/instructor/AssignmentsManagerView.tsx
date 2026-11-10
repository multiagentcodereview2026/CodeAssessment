import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { BarChart3, Calendar, FileCode2, Plus, Trash2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/useAuth';
import { Assignment } from '../../types';
import { Modal } from '../common/Modal';
import { ScoringWeightsEditor, ScoringWeights } from '../common/ScoringWeightsEditor';
import { DoubleConfirmDialog } from '../common/DoubleConfirmDialog';

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
  const [revisionPolicy, setRevisionPolicy] = useState<'HINTS_ONLY' | 'EXPLAIN_CHANGES' | 'VERIFIED_REFERENCE' | 'GUIDED_STEPS'>('GUIDED_STEPS');
  const [selectedProblemIds, setSelectedProblemIds] = useState<string[]>([]);
  const [assignmentWeights, setAssignmentWeights] = useState<ScoringWeights>();
  const [problemOptions, setProblemOptions] = useState<ProblemOption[]>([]);
  const [problemsLoading, setProblemsLoading] = useState(true);
  const [problemLoadError, setProblemLoadError] = useState('');
  const [saving, setSaving] = useState(false);
  const [archiveTarget, setArchiveTarget] = useState<Assignment | null>(null);

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
      problemWeights: assignmentWeights
        ? Object.fromEntries(selectedProblemIds.map((id) => [id, assignmentWeights]))
        : {},
      submittedCount: 0,
      totalCount: 0,
      avgScore: 0,
      dueDate,
      status: 'Active',
      courseId: Number(course.id)
      ,revisionPolicy
    };

    try {
      await addAssignment(assignment);
      setIsModalOpen(false);
      setTitle('');
      setDescription('');
      setDueDate('');
      setRevisionPolicy('GUIDED_STEPS');
      setSelectedProblemIds([]);
      setAssignmentWeights(undefined);
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
  const [editProblemWeights, setEditProblemWeights] = useState<Record<string, ScoringWeights>>({});
  const [editCourseId, setEditCourseId] = useState('');
  const [editRevisionPolicy, setEditRevisionPolicy] = useState<'HINTS_ONLY' | 'EXPLAIN_CHANGES' | 'VERIFIED_REFERENCE' | 'GUIDED_STEPS'>('GUIDED_STEPS');

  const openEditModal = (assignment: Assignment & { courseId?: number }) => {
    setEditAssignmentId(String(assignment.id));
    setEditTitle(assignment.title);
    setEditDescription(assignment.description || '');
    const deadline = assignment.dueDate ? new Date(assignment.dueDate) : null;
    setEditDueDate(deadline && !Number.isNaN(deadline.getTime()) ? new Date(deadline.getTime() - deadline.getTimezoneOffset() * 60000).toISOString().slice(0, 16) : '');
    setEditStatus(assignment.status.toUpperCase() === 'CLOSED' ? 'CLOSED' : 'ACTIVE');
    setEditHasSubmissions(assignment.submittedCount > 0);
    setEditProblemIds(assignment.problemIds || []);
    setEditProblemWeights(assignment.problemWeights || {});
    setEditCourseId(String(assignment.courseId || ''));
    setEditRevisionPolicy(assignment.revisionPolicy || 'VERIFIED_REFERENCE');
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
          due_date: editDueDate ? new Date(editDueDate).toISOString() : null,
          status: editStatus,
          problem_ids: editHasSubmissions ? undefined : editProblemIds,
          problem_weights: editHasSubmissions ? undefined : Object.fromEntries(Object.entries(editProblemWeights).filter(([id]) => editProblemIds.includes(id))),
          revision_policy: editRevisionPolicy
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
    <main className="space-y-6 pb-12 animate-fadeIn font-sans">
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 dark:border-white/10 pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-emerald-600 dark:text-emerald-400">
            Course Administration
          </p>
          <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Assignments Management
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-600 dark:text-zinc-400">
            Publish coursework, adjust problem rubrics, and monitor student progress across all active cohorts.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          disabled={!courses.length}
          className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-emerald-600/30 transition cursor-pointer disabled:opacity-50"
        >
          <Plus className="h-4 w-4" /> <span>+ Create Assignment</span>
        </button>
      </header>

      {assignments.length === 0 ? (
        <p className="rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#121217] py-12 text-center text-sm text-slate-500 dark:text-zinc-400">
          No assignments published yet. Click &quot;Create Assignment&quot; to assign problems to a course.
        </p>
      ) : (
        <div className="space-y-3">
          {assignments.map((assignment) => (
            <article
              key={assignment.id}
              className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 shadow-xs hover:border-emerald-400 dark:hover:border-white/25 card-hover transition-all sm:flex-row sm:items-center"
            >
              <div className="flex items-start gap-3.5">
                <div className="p-2.5 rounded-xl bg-emerald-500/15 border border-emerald-500/25 text-emerald-400 shrink-0">
                  <FileCode2 className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="font-bold text-base text-slate-900 dark:text-white tracking-tight">{assignment.title}</h2>
                  <p className="mt-1 text-xs text-slate-500 dark:text-zinc-400">
                    <span className="font-semibold text-emerald-500">{assignment.course}</span> · {assignment.problemsCount} problems · <span className="font-medium text-zinc-300">{assignment.status}</span>
                  </p>
                  <p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-500 dark:text-zinc-400">
                    <Calendar className="h-3.5 w-3.5 text-zinc-400" />
                    {assignment.dueDate ? new Date(assignment.dueDate).toLocaleString() : 'No due date'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4 sm:shrink-0">
                <div className="text-left sm:text-right text-xs text-slate-600 dark:text-zinc-400">
                  <div className="font-semibold text-slate-800 dark:text-zinc-200">{assignment.submittedCount}/{assignment.totalCount} submissions</div>
                  <div className="text-zinc-500">{assignment.avgScore == null ? 'No graded submissions yet' : `Average ${assignment.avgScore}%`}</div>
                </div>
                <button
                  title="Edit assignment"
                  onClick={() => openEditModal(assignment)}
                  className="rounded-xl px-3 py-1.5 text-slate-600 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-white/10 font-bold text-xs border border-slate-200 dark:border-white/14 cursor-pointer transition-colors"
                >
                  Edit
                </button>
                <button
                  title="View assignment analytics"
                  onClick={() => navigate(`/instructor/analytics?assignmentId=${assignment.id}`)}
                  className="rounded-xl p-2 text-slate-600 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-white/10 border border-slate-200 dark:border-white/14 cursor-pointer transition-colors"
                >
                  <BarChart3 className="h-4 w-4" />
                </button>
                <button
                  title="Archive assignment"
                  onClick={() => setArchiveTarget(assignment)}
                  className="rounded-xl p-2 text-slate-600 dark:text-zinc-400 hover:bg-rose-500/10 hover:text-rose-400 border border-slate-200 dark:border-white/14 cursor-pointer transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Edit assignment" subtitle={editHasSubmissions ? "Submissions exist. You can update the deadline and status." : "Update assignment details and problems."} maxWidth="xl">
        <form onSubmit={updateAssignment} className="space-y-4 text-sm">
          {editHasSubmissions && (
             <div className="p-3 bg-yellow-50 dark:bg-yellow-950/20 text-yellow-800 dark:text-yellow-300 text-xs rounded-xl border border-yellow-200 dark:border-yellow-500/30">
                This assignment has submissions. Content and problems are locked; the deadline can be extended.
             </div>
          )}
          <label className="block font-semibold text-slate-700 dark:text-zinc-300">Title
            <input value={editTitle} onChange={(event) => setEditTitle(event.target.value)} required disabled={editHasSubmissions} className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5 disabled:bg-slate-100 dark:disabled:bg-[#121217] disabled:text-slate-500 dark:disabled:text-zinc-500" />
          </label>
          <label className="block font-semibold text-slate-700 dark:text-zinc-300">Description
            <textarea value={editDescription} onChange={(event) => setEditDescription(event.target.value)} rows={3} disabled={editHasSubmissions} className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5 disabled:bg-slate-100 dark:disabled:bg-[#121217] disabled:text-slate-500 dark:disabled:text-zinc-500" />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
             <label className="block font-semibold text-slate-700 dark:text-zinc-300">Status
               <select value={editStatus} onChange={(event) => setEditStatus(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5">
                  <option value="ACTIVE">Active</option>
                  <option value="CLOSED">Closed</option>
               </select>
            </label>
            <label className="block font-semibold text-slate-700 dark:text-zinc-300">Due date
              <input type="datetime-local" value={editDueDate} onChange={(event) => setEditDueDate(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5" />
            </label>
          </div>
          <label className="block font-semibold text-slate-700 dark:text-zinc-300">AI learning support
            <select value={editRevisionPolicy} onChange={(event) => setEditRevisionPolicy(event.target.value as typeof editRevisionPolicy)} className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5">
              <option value="HINTS_ONLY">Hints only — no generated revision</option>
              <option value="EXPLAIN_CHANGES">Explain changes — no full code</option>
              <option value="GUIDED_STEPS">Guided steps — one improvement per submission</option>
              <option value="VERIFIED_REFERENCE">Verified reference code after assessment</option>
            </select>
            <span className="mt-1 block text-xs font-normal text-slate-500 dark:text-zinc-400">This setting may be changed after submissions; problem content remains locked.</span>
          </label>
          <fieldset>
            <legend className="mb-2 font-semibold text-slate-700 dark:text-zinc-300">Problem Bank</legend>
            <div className="max-h-56 space-y-1 overflow-y-auto rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-[#16161d]/50 p-2">
              {problemsLoading && <p className="p-3 text-slate-500 dark:text-zinc-400">Loading problems…</p>}
              {problemOptions.map((problem) => {
                const checked = editProblemIds.includes(problem.id);
                return (
                  <label key={problem.id} className={`flex cursor-pointer items-center justify-between gap-3 rounded-lg px-3 py-2 transition-colors ${checked ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200' : 'hover:bg-slate-100 dark:hover:bg-white/5 text-slate-800 dark:text-zinc-200'} ${editHasSubmissions ? 'opacity-70 cursor-not-allowed' : ''}`}>
                    <span className="flex min-w-0 items-center gap-2"><input type="checkbox" checked={checked} disabled={editHasSubmissions} onChange={() => setEditProblemIds(c => c.includes(problem.id) ? c.filter(id=>id!==problem.id) : [...c, problem.id])} /><span className="truncate">{problem.title}</span></span>
                    <span className="shrink-0 text-xs text-slate-500 dark:text-zinc-400">{problem.difficulty}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>
          {editProblemIds.map((id) => <div key={id}><p className="mb-1 text-sm font-semibold text-slate-800 dark:text-zinc-200">{problemOptions.find((p) => p.id === id)?.title || id}</p><ScoringWeightsEditor disabled={editHasSubmissions} value={editProblemWeights[id]} onChange={(weights) => setEditProblemWeights((current) => { const next = { ...current }; if (weights) next[id] = weights; else delete next[id]; return next; })} /></div>)}
          <footer className="flex justify-end gap-2 border-t border-slate-200 dark:border-white/10 pt-4">
            <button type="button" onClick={() => setIsEditModalOpen(false)} className="rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#121217] px-4 py-2 font-semibold text-slate-700 dark:text-zinc-300 hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer">Cancel</button>
            <button type="submit" disabled={saving || (!editHasSubmissions && !editProblemIds.length)} className="rounded-xl bg-emerald-600 hover:bg-emerald-500 px-4 py-2 font-semibold text-white disabled:opacity-50 cursor-pointer">{saving ? 'Saving…' : 'Save changes'}</button>
          </footer>
        </form>
      </Modal>
      <DoubleConfirmDialog
        isOpen={Boolean(archiveTarget)}
        title="Close this assignment?"
        description={`${archiveTarget?.title} will be closed so students cannot continue submitting it. Existing submissions and scores will be kept.`}
        actionLabel="close assignment"
        busy={saving}
        onClose={() => setArchiveTarget(null)}
        onConfirm={async () => { if (!archiveTarget) return; setSaving(true); try { await deleteAssignment(archiveTarget.id); setArchiveTarget(null); } finally { setSaving(false); } }}
      />

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create coding assignment" subtitle="Choose a course and real Problem Bank entries" maxWidth="xl">
        <form onSubmit={createAssignment} className="space-y-4 text-sm">
          <label className="block font-semibold text-slate-700 dark:text-zinc-300">Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} required className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5 placeholder:text-slate-400 dark:placeholder:text-zinc-500" />
          </label>
          <label className="block font-semibold text-slate-700 dark:text-zinc-300">Description
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5 placeholder:text-slate-400 dark:placeholder:text-zinc-500" />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block font-semibold text-slate-700 dark:text-zinc-300">Course
              <select value={courses.some((item) => String(item.id) === selectedCourseId) ? selectedCourseId : String(courses[0]?.id || '')} onChange={(event) => setSelectedCourseId(event.target.value)} required className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5">
                {courses.map((course) => <option key={course.id} value={String(course.id)}>{course.code} · {course.title}</option>)}
              </select>
            </label>
            <label className="block font-semibold text-slate-700 dark:text-zinc-300">Due date
              <input type="datetime-local" value={dueDate} onChange={(event) => setDueDate(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 px-3 py-2.5" />
            </label>
          </div>
          <section className="space-y-2">
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-zinc-100">Scoring weights <span className="font-normal text-slate-500 dark:text-zinc-400">· Optional</span></h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-zinc-400">Customize the rubric for every problem in this assignment. Leave it off to use the default weights.</p>
            </div>
            <ScoringWeightsEditor value={assignmentWeights} onChange={setAssignmentWeights} />
          </section>
          <fieldset>
            <legend className="mb-2 font-semibold text-slate-700 dark:text-zinc-300">Problem Bank</legend>
            <div className="max-h-56 space-y-1 overflow-y-auto rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-[#16161d]/50 p-2">
              {problemsLoading && <p className="p-3 text-slate-500 dark:text-zinc-400">Loading problems…</p>}
              {problemLoadError && <p role="alert" className="p-3 text-rose-700 dark:text-rose-400">{problemLoadError}</p>}
              {!problemsLoading && !problemLoadError && problemOptions.length === 0 && <p className="p-3 text-slate-500 dark:text-zinc-400">No problems are available.</p>}
              {problemOptions.map((problem) => {
                const checked = selectedProblemIds.includes(problem.id);
                return (
                  <label key={problem.id} className={`flex cursor-pointer items-center justify-between gap-3 rounded-lg px-3 py-2 transition-colors ${checked ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200' : 'hover:bg-slate-100 dark:hover:bg-white/5 text-slate-800 dark:text-zinc-200'}`}>
                    <span className="flex min-w-0 items-center gap-2"><input type="checkbox" checked={checked} onChange={() => toggleProblem(problem.id)} /><span className="truncate">{problem.title}</span></span>
                    <span className="shrink-0 text-xs text-slate-500 dark:text-zinc-400">{problem.difficulty}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>
          <footer className="flex justify-end gap-2 border-t border-slate-200 dark:border-white/10 pt-4">
            <button type="button" onClick={() => setIsModalOpen(false)} className="rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#121217] px-4 py-2 font-semibold text-slate-700 dark:text-zinc-300 hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer">Cancel</button>
            <button type="submit" disabled={saving || !courses.length || !selectedProblemIds.length || problemsLoading || Boolean(problemLoadError)} className="rounded-xl bg-emerald-600 hover:bg-emerald-500 px-4 py-2 font-semibold text-white disabled:opacity-50 cursor-pointer">{saving ? 'Saving…' : 'Publish assignment'}</button>
          </footer>
        </form>
      </Modal>
    </main>
  );
};
