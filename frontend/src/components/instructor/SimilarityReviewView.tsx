import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Check, ChevronDown, Code2, LoaderCircle, ShieldAlert, Users } from 'lucide-react';
import { useAuth } from '../../context/useAuth';

type StudentSubmission = {
  id: string; name: string; rollNumber: string; submissionId: string; language?: string;
  overallScore?: number | null; correctnessScore?: number | null; timeScore?: number | null;
  spaceScore?: number | null; styleScore?: number | null; rank?: number;
};
type SimilarityCase = {
  id: string; studentA: StudentSubmission; studentB: StudentSubmission;
  studentACodeSnippet: string; studentBCodeSnippet: string;
};
type SimilarityCluster = {
  id: string; courseId: number; courseTitle: string; problemId: string; problemTitle: string;
  members: StudentSubmission[]; pairCount: number; caseIds: string[];
};
type ApproachGroup = {
  id: string; courseId: number; courseTitle: string; problemId: string; problemTitle: string;
  approachLabel: string; approachSummary: string; members: StudentSubmission[]; explanation: string;
};
type Course = { id: number; title: string; course_code?: string };
type CaseResponse = { cases: SimilarityCase[]; clusters: SimilarityCluster[]; approach_groups?: ApproachGroup[] };

const score = (value?: number | null) => value === null || value === undefined ? '—' : `${Math.round(value)}%`;

export const SimilarityReviewView: React.FC = () => {
  const { authFetch } = useAuth();
  const [cases, setCases] = useState<SimilarityCase[]>([]);
  const [clusters, setClusters] = useState<SimilarityCluster[]>([]);
  const [approachGroups, setApproachGroups] = useState<ApproachGroup[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState('all');
  const [selectedClusterId, setSelectedClusterId] = useState('');
  const [selectedApproachId, setSelectedApproachId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const selectedCluster = clusters.find((cluster) => cluster.id === selectedClusterId);
  const codesBySubmission = useMemo(() => {
    const result = new Map<string, string>();
    for (const item of cases) {
      result.set(item.studentA.submissionId, item.studentACodeSnippet);
      result.set(item.studentB.submissionId, item.studentBCodeSnippet);
    }
    return result;
  }, [cases]);

  const loadCases = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const suffix = courseId === 'all' ? '' : `?course_id=${encodeURIComponent(courseId)}`;
      const response = await authFetch(`/api/instructor/similarity${suffix}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Could not load similarity groups (${response.status}).`);
      const data: CaseResponse = await response.json();
      const nextClusters = Array.isArray(data.clusters) ? data.clusters : [];
      setCases(Array.isArray(data.cases) ? data.cases : []);
      setClusters(nextClusters);
      const nextApproachGroups = Array.isArray(data.approach_groups) ? data.approach_groups : [];
      setApproachGroups(nextApproachGroups);
      setSelectedClusterId((current) => nextClusters.some((item) => item.id === current) ? current : '');
      setSelectedApproachId((current) => nextApproachGroups.some((item) => item.id === current) ? current : '');
    } catch (loadError) {
      setCases([]); setClusters([]); setApproachGroups([]);
      setError(loadError instanceof Error ? loadError.message : 'Could not load similarity groups.');
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

  return <div className="space-y-6 pb-12 animate-fadeIn">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Code Similarity Review</h1>
        <p className="mt-1 text-xs sm:text-sm text-slate-500">Review same-problem groups. These are instructor-only leads, never student scores or misconduct findings.</p>
      </div>
      <div className="flex items-center gap-3">
        <label className="text-xs font-semibold text-slate-600">Course:
          <select value={courseId} onChange={(event) => setCourseId(event.target.value)} className="ml-2 rounded-xl border border-slate-200 bg-white px-3 py-2">
            <option value="all">All courses</option>
            {courses.map((course) => <option key={course.id} value={String(course.id)}>{course.course_code ? `${course.course_code} · ` : ''}{course.title}</option>)}
          </select>
        </label>
        <span className="flex items-center gap-1.5 whitespace-nowrap rounded-2xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700"><ShieldAlert className="h-4 w-4" />{clusters.length} group{clusters.length === 1 ? '' : 's'}</span>
      </div>
    </div>

    {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}<button onClick={() => void loadCases()} className="ml-3 font-bold underline">Retry</button></div>}
    {loading ? <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center text-slate-500"><LoaderCircle className="mx-auto mb-3 h-6 w-6 animate-spin" />Loading evaluated submissions…</div>
      : clusters.length === 0 && approachGroups.length === 0 ? <div className="space-y-3 rounded-3xl border border-slate-200 bg-white p-12 text-center"><div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600"><Check className="h-6 w-6" /></div><h2 className="text-base font-bold text-slate-800">No review groups found</h2><p className="mx-auto max-w-lg text-sm text-slate-500">There are no same-problem submission groups needing review in this scope.</p></div>
      : <>
        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {clusters.length === 0 && <div className="rounded-2xl border border-slate-200 bg-white p-4 text-xs text-slate-500 md:col-span-2 xl:col-span-3">No direct code-overlap groups were found. Approach groups below are informational only.</div>}
          {clusters.map((cluster, index) => {
            const isOpen = selectedClusterId === cluster.id;
            return <button key={cluster.id} type="button" onClick={() => setSelectedClusterId(isOpen ? '' : cluster.id)} className={`rounded-2xl border p-4 text-left transition ${isOpen ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-slate-50'}`}>
              <div className="flex items-start justify-between gap-2"><div><p className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-600">Group {index + 1}</p><h2 className="mt-1 text-sm font-bold text-slate-900">{cluster.problemTitle}</h2></div><ChevronDown className={`mt-1 h-4 w-4 shrink-0 text-slate-500 transition ${isOpen ? 'rotate-180' : ''}`} /></div>
              <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-600"><Users className="h-3.5 w-3.5" />{cluster.members.length} student{cluster.members.length === 1 ? '' : 's'} · {cluster.pairCount} matching pair{cluster.pairCount === 1 ? '' : 's'}</p>
              <p className="mt-2 truncate font-mono text-[11px] text-slate-500">{cluster.members.map((member) => member.id).join(' · ')}</p>
            </button>;
          })}
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-6"><div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-[10px] font-extrabold uppercase tracking-wider text-sky-700">Algorithm approach groups</p><h2 className="mt-1 text-base font-extrabold text-slate-900">Same technique, different code</h2><p className="mt-1 text-xs text-slate-500">Informational AST classifications only. These do not indicate code overlap or misconduct.</p></div><span className="text-xs font-bold text-slate-500">{approachGroups.length} group{approachGroups.length === 1 ? '' : 's'}</span></div><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{approachGroups.map((group) => { const open = selectedApproachId === group.id; return <button key={group.id} type="button" onClick={() => setSelectedApproachId(open ? '' : group.id)} className={`rounded-2xl border p-4 text-left transition ${open ? 'border-sky-400 bg-sky-50' : 'border-slate-200 hover:border-sky-300'}`}><p className="text-sm font-extrabold text-slate-900">{group.problemTitle}</p><p className="mt-2 inline-block rounded-full bg-sky-100 px-2 py-1 text-[10px] font-bold text-sky-800">{group.approachLabel}</p><p className="mt-3 font-mono text-[11px] text-slate-500">{group.members.length} students · {group.members.map((member) => member.id).join(' · ')}</p></button>; })}</div>{selectedApproachId && (() => { const group = approachGroups.find((item) => item.id === selectedApproachId); return group && <div className="mt-4 rounded-2xl border border-sky-200 bg-sky-50 p-4"><p className="text-sm font-extrabold text-sky-950">{group.problemTitle} · {group.approachLabel}</p><p className="mt-2 text-xs leading-relaxed text-sky-900">{group.explanation}</p><p className="mt-3 font-mono text-xs text-sky-800">Student IDs: {group.members.map((member) => member.id).join(' · ')}</p></div>; })()}</section>

        {selectedCluster && (() => {
          // All members are structurally similar. Show the highest-ranked
          // submission once as representative evidence instead of duplicating
          // the same score and source code for every student.
          const representative = selectedCluster.members[0];
          return <section className="overflow-hidden rounded-3xl border border-indigo-200 bg-white shadow-sm">
            <header className="border-b border-indigo-100 bg-indigo-50 px-5 py-4 sm:px-6"><p className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-600">Selected group</p><h2 className="mt-1 text-lg font-extrabold text-slate-900">{selectedCluster.problemTitle}</h2><p className="mt-1 text-xs text-slate-600">{selectedCluster.courseTitle} · {selectedCluster.members.length} students in this group</p></header>
            <div className="space-y-5 p-5 sm:p-6">
              <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="flex items-center gap-2"><Users className="h-4 w-4 text-indigo-600" /><h3 className="text-sm font-extrabold text-slate-900">Group members ({selectedCluster.members.length})</h3></div><p className="mt-3 font-mono text-sm leading-7 text-slate-700">{selectedCluster.members.map((member) => member.id).join(' · ')}</p></section>
              {representative && <article className="overflow-hidden rounded-2xl border border-slate-200"><div className="flex items-start justify-between gap-3 border-b border-slate-100 bg-slate-50 p-4"><div><span className="rounded-full bg-indigo-100 px-2 py-1 text-[10px] font-extrabold text-indigo-700">Representative submission</span><p className="mt-3 font-mono text-xs text-slate-600">{representative.submissionId} · {representative.language || 'Unknown language'}</p></div><div className="text-right"><p className="text-xl font-extrabold text-emerald-600">{score(representative.overallScore)}</p><p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Overall</p></div></div><dl className="grid grid-cols-2 gap-x-3 gap-y-2 p-4 text-xs sm:grid-cols-4"><div><dt className="text-slate-500">Correctness</dt><dd className="font-bold text-slate-800">{score(representative.correctnessScore)}</dd></div><div><dt className="text-slate-500">Time complexity</dt><dd className="font-bold text-slate-800">{score(representative.timeScore)}</dd></div><div><dt className="text-slate-500">Space complexity</dt><dd className="font-bold text-slate-800">{score(representative.spaceScore)}</dd></div><div><dt className="text-slate-500">Style</dt><dd className="font-bold text-slate-800">{score(representative.styleScore)}</dd></div></dl><details className="border-t border-slate-200 bg-slate-950"><summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-xs font-bold text-white"><Code2 className="h-4 w-4 text-indigo-300" />View representative code</summary><pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap break-words border-t border-slate-800 p-4 font-mono text-xs leading-relaxed text-slate-300">{codesBySubmission.get(representative.submissionId) || 'No source code stored.'}</pre></details></article>}
            </div>
          </section>;
        })()}
      </>}
  </div>;
};
