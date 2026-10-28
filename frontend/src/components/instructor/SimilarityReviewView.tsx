import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Check, ChevronDown, Code2, LoaderCircle, Users } from 'lucide-react';
import { useAuth } from '../../context/useAuth';

type StudentSubmission = {
  id: string; name: string; rollNumber: string; submissionId: string; language?: string;
  submittedAt?: string;
  overallScore?: number | null; correctnessScore?: number | null; timeScore?: number | null;
  spaceScore?: number | null; styleScore?: number | null; rank?: number;
};
type SimilarityCase = {
  id: string; studentA: StudentSubmission; studentB: StudentSubmission;
  studentACodeSnippet: string; studentBCodeSnippet: string;
  similarityPercentage?: number; similarityMethod?: string;
};
type SimilarityCluster = {
  id: string; courseId: number; courseTitle: string; assignmentId?: number; assignmentTitle?: string; problemId: string; problemTitle: string;
  members: StudentSubmission[]; pairCount: number; caseIds: string[];
  groupKind?: 'code_overlap' | 'structural' | 'individual'; groupLabel?: string;
  approachSummary?: string; evidenceSummary?: string[]; representativeCode?: string;
};
type ApproachGroup = {
  id: string; courseId: number; courseTitle: string; assignmentId?: number; assignmentTitle?: string; problemId: string; problemTitle: string;
  approachLabel: string; approachSummary: string; members: StudentSubmission[]; explanation: string;
};
type Course = { id: number; title: string; course_code?: string };
type CaseResponse = { cases: SimilarityCase[]; clusters: SimilarityCluster[]; approach_groups?: ApproachGroup[]; submission_groups?: SimilarityCluster[] };
type ReviewItem = { id: string; kind: 'code-overlap' | 'approach'; problemTitle: string; members: StudentSubmission[]; detail: SimilarityCluster | ApproachGroup };

const SimilarityGroupDetails: React.FC<{
  cluster: SimilarityCluster;
  cases: SimilarityCase[];
  codesBySubmission: Map<string, string>;
}> = ({ cluster, cases, codesBySubmission }) => {
  const representative = cluster.members[0];
  const cosinePairs = cases
    .filter((item) => cluster.caseIds.includes(item.id) && Number.isFinite(item.similarityPercentage))
    .sort((left, right) => (left.studentA.id + left.studentB.id).localeCompare(right.studentA.id + right.studentB.id));
  const averageCosine = cosinePairs.length
    ? cosinePairs.reduce((total, item) => total + (item.similarityPercentage || 0), 0) / cosinePairs.length
    : null;

  return <section className="overflow-hidden rounded-3xl border border-emerald-200 bg-white shadow-sm">
    <header className="border-b border-emerald-100 bg-emerald-50 px-5 py-4 sm:px-6"><p className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-700">Selected group</p><h2 className="mt-1 text-lg font-extrabold text-slate-900">{cluster.problemTitle}</h2><p className="mt-1 text-xs text-slate-600">{cluster.courseTitle} · {cluster.assignmentTitle || `Assignment #${cluster.assignmentId ?? '—'}`} · {cluster.groupLabel || 'Submission group'} · {cluster.members.length} students in this group</p></header>
    <div className="space-y-5 p-5 sm:p-6">
      <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="flex items-center gap-2"><Users className="h-4 w-4 text-emerald-600" /><h3 className="text-sm font-extrabold text-slate-900">Group members ({cluster.members.length})</h3></div><p className="mt-3 font-mono text-sm leading-7 text-slate-700">{cluster.members.map((member) => member.id).join(' · ')}</p></section>
      {cluster.evidenceSummary && cluster.evidenceSummary.length > 0 && <section className="rounded-2xl border border-sky-200 bg-sky-50 p-4"><h3 className="text-sm font-extrabold text-sky-950">Why this group was formed</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-xs leading-relaxed text-sky-900">{cluster.evidenceSummary.map((item) => <li key={item}>{item}</li>)}</ul><p className="mt-3 text-[11px] text-sky-800">Automated evidence is for instructor review only. It is not a grade or a misconduct decision.</p></section>}
      <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-sm font-extrabold text-emerald-950">How similar are the code patterns?</h3><p className="mt-1 max-w-2xl text-xs leading-relaxed text-emerald-800">This comparison highlights similar code structure, even when students use different variable names.</p></div><p className="text-2xl font-extrabold text-emerald-700">{averageCosine === null ? 'Unavailable' : `${averageCosine.toFixed(1)}%`}</p></div>{cosinePairs.length > 0 ? <><p className="mt-3 text-xs text-emerald-900">Pairwise similarity for students in this group:</p><ul className="mt-2 space-y-1 text-xs text-emerald-900">{cosinePairs.map((pair) => <li key={pair.id} className="flex flex-wrap justify-between gap-2"><span>{pair.studentA.id} and {pair.studentB.id}</span><strong>{(pair.similarityPercentage || 0).toFixed(1)}% similar code patterns</strong></li>)}</ul></> : <p className="mt-3 text-xs text-emerald-900">This group was formed from a similar overall approach; there is no direct code-pattern comparison to show.</p>}<p className="mt-2 text-[11px] text-emerald-800">This is a review signal only. Similar patterns can occur when students solve the same problem; it is not a grade or a plagiarism verdict.</p></section>
      {representative && <article className="overflow-hidden rounded-2xl border border-slate-200"><div className="border-b border-slate-100 bg-slate-50 p-4"><span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-extrabold text-emerald-800">Representative submission</span><p className="mt-3 font-mono text-xs text-slate-600">{representative.submissionId} · {representative.language || 'Unknown language'}</p></div><details className="border-t border-slate-200 bg-slate-950"><summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-xs font-bold text-white"><Code2 className="h-4 w-4 text-emerald-400" />View representative code</summary><pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap break-words border-t border-slate-800 p-4 font-mono text-xs leading-relaxed text-slate-300">{cluster.representativeCode || codesBySubmission.get(representative.submissionId) || 'No source code stored.'}</pre></details></article>}
    </div>
  </section>;
};

const ApproachGroupDetails: React.FC<{ group: ApproachGroup }> = ({ group }) => <section className="rounded-2xl border border-sky-200 bg-sky-50 p-4"><p className="text-sm font-extrabold text-sky-950">{group.problemTitle} · {group.approachLabel}</p><p className="mt-2 text-xs leading-relaxed text-sky-900">{group.explanation}</p><p className="mt-3 font-mono text-xs text-sky-800">Student IDs: {group.members.map((member) => member.id).join(' · ')}</p></section>;

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

  const reviewItems = useMemo<ReviewItem[]>(() => {
    const overlapProblemKeys = new Set(clusters.map((cluster) => `${cluster.courseId}:${cluster.assignmentId ?? 'course'}:${cluster.problemId}`));
    const directOverlap = clusters.map((cluster) => ({ id: cluster.id, kind: 'code-overlap' as const, problemTitle: cluster.problemTitle, members: cluster.members, detail: cluster }));
    const approachOnly = approachGroups
      .filter((group) => !overlapProblemKeys.has(`${group.courseId}:${group.assignmentId ?? 'course'}:${group.problemId}`))
      .map((group) => ({ id: group.id, kind: 'approach' as const, problemTitle: group.problemTitle, members: group.members, detail: group }));
    return [...directOverlap, ...approachOnly].sort((left, right) => left.problemTitle.localeCompare(right.problemTitle));
  }, [clusters, approachGroups]);
  const problemSections = useMemo(() => {
    const sections = new Map<string, { title: string; items: ReviewItem[] }>();
    for (const item of reviewItems) {
      const cluster = item.detail as SimilarityCluster;
      const key = `${cluster.courseId}:${cluster.assignmentId ?? 'course'}:${cluster.problemId}`;
      const section = sections.get(key) ?? { title: item.problemTitle, items: [] };
      section.items.push(item);
      sections.set(key, section);
    }
    return [...sections.values()];
  }, [reviewItems]);
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
      // This review page only shows shared implementations, so hide groups
      // that contain a single student's submission.
      const nextClusters = Array.isArray(data.submission_groups)
        ? data.submission_groups.filter((group) => Array.isArray(group.members) && group.members.length >= 2)
        : [];
      setCases(Array.isArray(data.cases) ? data.cases : []);
      setClusters(nextClusters);
      const nextApproachGroups: ApproachGroup[] = [];
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
        <p className="mt-1 text-xs sm:text-sm text-slate-500">Groups are shown only when at least two students share a code pattern or implementation approach. This is instructor-only analysis, not a grade or misconduct finding.</p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-xs font-semibold text-slate-600">Course:
          <select value={courseId} onChange={(event) => setCourseId(event.target.value)} className="ml-2 rounded-xl border border-slate-200 bg-white px-3 py-2">
            <option value="all">All courses</option>
            {courses.map((course) => <option key={course.id} value={String(course.id)}>{course.course_code ? `${course.course_code} · ` : ''}{course.title}</option>)}
          </select>
        </label>
      </div>
    </div>

    {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}<button onClick={() => void loadCases()} className="ml-3 font-bold underline">Retry</button></div>}
    {loading ? <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center text-slate-500"><LoaderCircle className="mx-auto mb-3 h-6 w-6 animate-spin" />Loading evaluated submissions…</div>
      : reviewItems.length === 0 ? <div className="space-y-3 rounded-3xl border border-slate-200 bg-white p-12 text-center"><div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600"><Check className="h-6 w-6" /></div><h2 className="text-base font-bold text-slate-800">No submission groups found</h2><p className="mx-auto max-w-lg text-sm text-slate-500">There are no evaluated submissions for instructor-assigned problems in this scope.</p></div>
      : <>
        <section className="space-y-6">{problemSections.map((section) => <div key={section.title} className="space-y-3"><div className="flex items-center justify-between"><h2 className="text-base font-extrabold text-slate-900">{section.title}</h2><span className="text-xs font-semibold text-slate-500">{section.items.length} group{section.items.length === 1 ? '' : 's'}</span></div>{section.items.map((item, index) => { const open = item.kind === 'code-overlap' ? selectedClusterId === item.id : selectedApproachId === item.id; const detail = item.detail as SimilarityCluster; return <div key={item.id} className="space-y-2"><button type="button" aria-expanded={open} onClick={() => { if (item.kind === 'code-overlap') { setSelectedClusterId(open ? '' : item.id); setSelectedApproachId(''); } else { setSelectedApproachId(open ? '' : item.id); setSelectedClusterId(''); } }} className={`flex w-full flex-col gap-3 rounded-2xl border p-4 text-left transition sm:flex-row sm:items-center sm:justify-between ${open ? 'border-emerald-400 bg-emerald-50' : 'border-slate-200 bg-white hover:border-emerald-300 hover:bg-slate-50'}`}><div><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-extrabold uppercase text-emerald-800">Group {index + 1}</span><p className="text-sm font-bold text-slate-900">{detail.groupLabel || 'Submission group'}</p></div><p className="mt-2 flex items-center gap-1.5 text-xs text-slate-600"><Users className="h-3.5 w-3.5" />{item.members.length} student{item.members.length === 1 ? '' : 's'}</p><p className="mt-2 font-mono text-[11px] text-slate-500">{item.members.map((member) => member.id).join(' · ')}</p></div><ChevronDown className={`h-4 w-4 shrink-0 text-slate-500 transition ${open ? 'rotate-180' : ''}`} /></button>{open && (item.kind === 'code-overlap' ? <SimilarityGroupDetails cluster={detail} cases={cases} codesBySubmission={codesBySubmission} /> : <ApproachGroupDetails group={item.detail as ApproachGroup} />)}</div>; })}</div>)}</section>
      </>}
  </div>;
};
