import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Check, ChevronLeft, ChevronRight, Code2, LoaderCircle, ShieldAlert } from 'lucide-react';
import { useAuth } from '../../context/useAuth';

type SimilarityCase = {
  id: string; problemId: string; problemTitle: string; courseId: number; courseTitle: string;
  studentA: { id: string; name: string; rollNumber: string; submissionId: string };
  studentB: { id: string; name: string; rollNumber: string; submissionId: string };
  similarityPercentage: number; riskLevel: 'High' | 'Medium'; matchedLinesCount: number; timestamp: string;
  studentACodeSnippet: string; studentBCodeSnippet: string; aiAuditNotes: string;
  reviewStatus: 'open' | 'review_requested';
};
type Course = { id: number; title: string; course_code?: string };
type CaseResponse = { cases: SimilarityCase[]; total_cases: number };

export const SimilarityReviewView: React.FC = () => {
  const { authFetch } = useAuth();
  const [cases, setCases] = useState<SimilarityCase[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState('all');
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState('');
  const activeIndex = Math.max(0, cases.findIndex((item) => item.id === selectedId));
  const activeCase = cases[activeIndex];
  const codePanels = activeCase ? [
    { student: activeCase.studentA, code: activeCase.studentACodeSnippet, label: 'Student A' },
    { student: activeCase.studentB, code: activeCase.studentBCodeSnippet, label: 'Student B' },
  ] : [];

  const loadCases = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const suffix = courseId === 'all' ? '' : `?course_id=${encodeURIComponent(courseId)}`;
      const response = await authFetch(`/api/instructor/similarity${suffix}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Could not load similarity cases (${response.status}).`);
      const data: CaseResponse = await response.json();
      const nextCases = Array.isArray(data.cases) ? data.cases : [];
      setCases(nextCases);
      setSelectedId((current) => nextCases.some((item) => item.id === current) ? current : nextCases[0]?.id ?? '');
    } catch (loadError) {
      setCases([]);
      setError(loadError instanceof Error ? loadError.message : 'Could not load similarity cases.');
    } finally { setLoading(false); }
  }, [authFetch, courseId]);

  useEffect(() => { void loadCases(); }, [loadCases]);
  useEffect(() => {
    let cancelled = false;
    authFetch('/api/instructor/courses', { cache: 'no-store' }).then(async (response) => {
      if (!response.ok) return;
      const data: Course[] = await response.json();
      if (!cancelled) setCourses(Array.isArray(data) ? data : []);
    }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [authFetch]);

  const updateCase = async (action: 'dismiss' | 'request-review') => {
    if (!activeCase) return;
    setWorking(true); setError('');
    try {
      const response = await authFetch(`/api/instructor/similarity/${encodeURIComponent(activeCase.id)}/${action}`, { method: 'POST' });
      if (!response.ok) throw new Error(`Could not update this case (${response.status}).`);
      if (action === 'dismiss') {
        const next = cases.filter((item) => item.id !== activeCase.id);
        setCases(next); setSelectedId(next[0]?.id ?? '');
      } else {
        setCases((previous) => previous.map((item) => item.id === activeCase.id ? { ...item, reviewStatus: 'review_requested' } : item));
      }
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : 'Could not update this case.');
    } finally { setWorking(false); }
  };

  return <div className="space-y-6 pb-12 animate-fadeIn">
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div><h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Code Similarity Review</h1><p className="text-xs sm:text-sm text-slate-500 mt-1">Review same-problem submissions with at least 72% normalized five-token overlap. Similarity is a review lead, not proof of misconduct.</p></div>
      <div className="flex items-center gap-3"><label className="text-xs font-semibold text-slate-600">Course:<select value={courseId} onChange={(event) => setCourseId(event.target.value)} className="ml-2 rounded-xl border border-slate-200 bg-white px-3 py-2"><option value="all">All courses</option>{courses.map((course) => <option key={course.id} value={String(course.id)}>{course.course_code ? `${course.course_code} · ` : ''}{course.title}</option>)}</select></label><span className="whitespace-nowrap text-xs font-bold text-rose-700 bg-rose-50 px-3 py-2 rounded-2xl border border-rose-200 flex items-center gap-1.5"><ShieldAlert className="w-4 h-4" />{cases.length} candidate{cases.length === 1 ? '' : 's'}</span></div>
    </div>

    {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}<button onClick={() => void loadCases()} className="ml-3 font-bold underline">Retry</button></div>}
    {loading ? <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center text-slate-500"><LoaderCircle className="mx-auto mb-3 h-6 w-6 animate-spin" />Loading evaluated submissions…</div>
      : cases.length === 0 ? <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center space-y-3"><div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600"><Check className="h-6 w-6" /></div><h2 className="text-base font-bold text-slate-800">No overlap candidates found</h2><p className="mx-auto max-w-lg text-sm text-slate-500">There are no evaluated same-problem submission pairs above the token-overlap review threshold for this scope. This screen is a review aid, not a plagiarism verdict.</p></div>
      : activeCase && <div className="space-y-5">
        {cases.length > 1 && <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-3"><button aria-label="Previous candidate" disabled={activeIndex === 0} onClick={() => setSelectedId(cases[activeIndex - 1].id)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 disabled:opacity-40"><ChevronLeft className="h-5 w-5" /></button><span className="text-xs font-bold text-slate-700">Candidate {activeIndex + 1} of {cases.length} · {activeCase.similarityPercentage}% token overlap</span><button aria-label="Next candidate" disabled={activeIndex >= cases.length - 1} onClick={() => setSelectedId(cases[activeIndex + 1].id)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 disabled:opacity-40"><ChevronRight className="h-5 w-5" /></button></div>}
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 sm:p-6 flex flex-col sm:flex-row justify-between gap-4"><div className="flex gap-3"><AlertTriangle className="mt-1 h-5 w-5 shrink-0 text-amber-700" /><div><div className="font-extrabold text-amber-950">Submission overlap candidate · {activeCase.similarityPercentage}%</div><p className="mt-1 text-xs text-amber-900">{activeCase.courseTitle} · {activeCase.problemTitle} · {new Date(activeCase.timestamp).toLocaleString()}</p><p className="mt-2 max-w-3xl text-xs leading-relaxed text-amber-900">{activeCase.aiAuditNotes}</p>{activeCase.reviewStatus === 'review_requested' && <span className="mt-2 inline-block rounded-full bg-indigo-100 px-2.5 py-1 text-[11px] font-bold text-indigo-800">Instructor review requested</span>}</div></div><div className="flex shrink-0 flex-wrap items-center gap-2"><button disabled={working} onClick={() => void updateCase('dismiss')} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-100 disabled:opacity-50">Dismiss candidate</button><button disabled={working || activeCase.reviewStatus === 'review_requested'} onClick={() => void updateCase('request-review')} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-indigo-700 disabled:opacity-50">{activeCase.reviewStatus === 'review_requested' ? 'Review requested' : 'Mark for instructor review'}</button></div></section>
        <section className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-950 shadow-xl"><header className="flex items-center justify-between border-b border-slate-800 px-5 py-4 text-xs font-bold text-white"><span className="flex items-center gap-2"><Code2 className="h-4 w-4 text-indigo-400" />Code comparison · {activeCase.matchedLinesCount} shared token shingles</span><span className="font-mono text-slate-400">{activeCase.studentA.submissionId} / {activeCase.studentB.submissionId}</span></header><div className="grid grid-cols-1 divide-y divide-slate-800 lg:grid-cols-2 lg:divide-x lg:divide-y-0">{codePanels.map((panel) => <div key={panel.student.submissionId} className="min-w-0 p-5"><div className="mb-3 border-b border-slate-800 pb-3"><div className="font-bold text-white">{panel.student.name}</div><div className="text-[11px] text-slate-400">{panel.label} · {panel.student.rollNumber}</div></div><pre className="max-h-[30rem] overflow-auto whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-slate-300">{panel.code || 'No source code stored.'}</pre></div>)}</div></section>
      </div>}
  </div>;
};
