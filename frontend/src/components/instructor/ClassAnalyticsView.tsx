import React, { useEffect, useState } from 'react';
import { AlertTriangle, BarChart3, Send } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';
import { ScoreDistributionBarChart } from '../common/ChartComponents';

type Scope = { id: number; title: string; course_id?: number; kind: 'course' | 'assignment' };
type Analytics = {
  avg_score?: number | null; class_avg_score?: string | null; highest_score?: number | null; lowest_score?: number | null;
  total_submissions?: number; score_distribution?: Array<{ range: string; count: number; heightPercent: number }>;
  topic_performance?: Array<{ topic: string; average_score?: number | null; deduction_rate?: number | null; students_assessed?: number; students_below_60?: number }>;
  highest_student?: { name: string; average_score: number } | null; lowest_student?: { name: string; average_score: number } | null;
};
type Roster = { status: string };

async function fetchJson<T>(authFetch: ReturnType<typeof useAuth>['authFetch'], url: string): Promise<T> {
  const response = await authFetch(url, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

export const ClassAnalyticsView: React.FC = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [courses, setCourses] = useState<Array<{ id: number; title: string }>>([]);
  const [assignments, setAssignments] = useState<Scope[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [atRiskCount, setAtRiskCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const courseId = searchParams.get('courseId');
  const assignmentId = searchParams.get('assignmentId');
  const activeAssignment = assignments.find((item) => String(item.id) === assignmentId);
  const activeCourse = courses.find((item) => String(item.id) === courseId);
  const scopeValue = assignmentId ? `assignment:${assignmentId}` : courseId ? `course:${courseId}` : 'all';
  const topics = analytics?.topic_performance ?? [];
  const weakest = topics[0];
  const average = analytics?.avg_score ?? (analytics?.class_avg_score ? Number.parseFloat(analytics.class_avg_score) : null);
  const highest = analytics?.highest_student;
  const lowest = analytics?.lowest_student;
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchJson<Array<{ id: number; title: string }>>(auth.authFetch, '/api/instructor/courses'),
      fetchJson<Array<Scope & Analytics>>(auth.authFetch, '/api/instructor/assignments'),
    ]).then(([courseData, assignmentData]) => {
      if (cancelled) return;
      setCourses(Array.isArray(courseData) ? courseData : []);
      setAssignments(Array.isArray(assignmentData) ? assignmentData : []);
    }).catch(() => { if (!cancelled) setError('Could not load your courses and assignments.'); });
    return () => { cancelled = true; };
  }, [auth.authFetch]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true); setError(''); setAnalytics(null);
    const analyticsUrl = assignmentId
      ? null
      : courseId ? `/api/instructor/courses/${encodeURIComponent(courseId)}/analytics` : '/api/instructor/overview';
    const metricsPromise = assignmentId
      ? fetchJson<Scope & Analytics>(auth.authFetch, `/api/instructor/assignments/${encodeURIComponent(assignmentId)}`).catch((error: unknown) => {
        if (error instanceof Error && error.message.includes('(404)')) return null;
        throw error;
      })
      : fetchJson<Analytics>(auth.authFetch, analyticsUrl!);
    const rosterUrl = courseId ? `/api/instructor/roster?course_id=${encodeURIComponent(courseId)}` : '/api/instructor/roster';
    Promise.all([metricsPromise, fetchJson<Roster[]>(auth.authFetch, rosterUrl)]).then(([metrics, roster]) => {
      if (cancelled) return;
      setAnalytics(metrics);
      setAtRiskCount((Array.isArray(roster) ? roster : []).filter((student) => student.status !== 'On Track').length);
      if (assignmentId && !metrics) setError('That assignment is unavailable or has been removed.');
    }).catch(() => { if (!cancelled) setError('Could not load analytics for this scope. Check your connection and retry.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [auth.authFetch, courseId, assignmentId]);

  const scopeTitle = activeAssignment?.title ?? activeCourse?.title ?? 'All courses';
  const openRoster = (topic?: string) => {
    const params = new URLSearchParams();
    if (courseId || activeAssignment?.course_id) params.set('courseId', courseId || String(activeAssignment?.course_id));
    if (topic) params.set('topic', topic);
    navigate(`/instructor/students${params.size ? `?${params.toString()}` : ''}`);
  };
  const changeScope = (value: string) => {
    const params = new URLSearchParams(searchParams);
    params.delete('assignmentId'); params.delete('courseId');
    if (value.startsWith('course:')) params.set('courseId', value.slice('course:'.length));
    if (value.startsWith('assignment:')) {
      const id = value.slice('assignment:'.length);
      params.set('assignmentId', id);
      const assignment = assignments.find((item) => String(item.id) === id);
      if (assignment?.course_id) params.set('courseId', String(assignment.course_id));
    }
    setSearchParams(params);
  };

  return <div className="space-y-6 pb-12 animate-fadeIn">
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"><div><h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Class Performance Analytics</h1><p className="text-xs text-slate-500 mt-1">Evaluated submission results for {scopeTitle}.</p></div>
      <label className="flex items-center gap-2 text-xs font-semibold text-slate-600">Scope:<select value={scopeValue} onChange={(event) => changeScope(event.target.value)} className="bg-white border border-slate-200 text-xs font-semibold text-slate-700 rounded-xl px-3 py-2"><option value="all">All courses</option><optgroup label="Courses">{courses.map((item) => <option key={`course-${item.id}`} value={`course:${item.id}`}>{item.title}</option>)}</optgroup><optgroup label="Assignments">{assignments.map((item) => <option key={`assignment-${item.id}`} value={`assignment:${item.id}`}>{item.title}</option>)}</optgroup></select></label>
    </div>
    {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}<button onClick={() => setSearchParams(new URLSearchParams(searchParams))} className="ml-3 font-bold underline">Retry</button></div>}
    {loading ? <div className="rounded-2xl border bg-white p-12 text-center text-slate-500">Loading analytics…</div> : <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-rose-200 p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4"><div><span className="text-xs font-extrabold uppercase text-rose-700">Remediation Focus</span><h2 className="mt-1 text-lg font-extrabold text-slate-900">{weakest?.topic ?? 'No assessed topics yet'}</h2><p className="mt-1 text-xs text-slate-500">{weakest ? `Average ${weakest.average_score ?? 'N/A'}% across ${weakest.students_assessed ?? 0} assessed students; ${weakest.students_below_60 ?? 0} scored below 60%.` : 'Topic performance appears after student submissions have been evaluated.'}</p></div>{weakest && <button onClick={() => openRoster(weakest.topic)} className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold flex items-center justify-center gap-2"><Send className="w-3.5 h-3.5" />View affected students</button>}</div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs"><span className="text-xs font-extrabold uppercase text-slate-500">At-Risk Watchlist</span><div className="mt-2 flex items-baseline gap-2"><span className="text-3xl font-extrabold text-rose-700 font-mono">{atRiskCount}</span><span className="text-xs text-slate-500">students need attention</span></div><button onClick={() => openRoster()} className="mt-3 text-xs font-semibold text-indigo-600 hover:underline">Open scoped roster</button></div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Metric label="Average Score" value={average == null ? 'N/A' : `${average}%`} detail={average == null ? 'No evaluated submissions' : 'Across latest assessed work'} />
        <Metric label="Highest Score" value={analytics?.highest_score == null ? 'N/A' : `${analytics.highest_score}%`} detail={highest?.name ?? 'No evaluated submissions'} color="text-emerald-700" labelColor="text-emerald-600" />
        <Metric label="Lowest Score" value={analytics?.lowest_score == null ? 'N/A' : `${analytics.lowest_score}%`} detail={lowest?.name ?? 'No evaluated submissions'} color="text-rose-700" labelColor="text-rose-600" />
      </div>
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs p-6 sm:p-8 space-y-4"><div className="flex items-center justify-between pb-3 border-b border-slate-100"><div className="flex items-center gap-2"><BarChart3 className="w-5 h-5 text-indigo-600" /><h3 className="text-base font-bold text-slate-900">Score Distribution (0–100)</h3></div><span className="text-xs font-mono text-slate-400">{analytics?.total_submissions ?? 0} submissions</span></div><ScoreDistributionBarChart distribution={analytics?.score_distribution ?? []} /></div>
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs p-6 sm:p-8 space-y-4"><div className="flex items-center gap-2 pb-3 border-b border-slate-100"><AlertTriangle className="w-5 h-5 text-amber-500" /><h3 className="text-base font-bold text-slate-900">Observed Topic Performance</h3></div>
        {topics.length ? <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b text-slate-400 text-[11px] uppercase"><th className="pb-3">Topic</th><th className="pb-3">Average score</th><th className="pb-3">Below 60%</th><th className="pb-3">Assessed students</th><th className="pb-3 text-right">Action</th></tr></thead><tbody className="divide-y">{topics.map((item) => <tr key={item.topic}><td className="py-3 font-bold text-slate-800">{item.topic}</td><td className="py-3 font-mono">{item.average_score ?? 'N/A'}%</td><td className="py-3 font-mono">{item.students_below_60 ?? 0}</td><td className="py-3 font-mono">{item.students_assessed ?? 0}</td><td className="py-3 text-right"><button onClick={() => openRoster(item.topic)} className="px-2.5 py-1 text-xs font-bold text-indigo-600 hover:bg-indigo-50 rounded-lg">View roster</button></td></tr>)}</tbody></table></div> : <p className="py-8 text-center text-sm text-slate-500">No assessed topic data yet.</p>}
      </div>
    </div>}
  </div>;
};

const Metric: React.FC<{ label: string; value: string; detail: string; color?: string; labelColor?: string }> = ({ label, value, detail, color = 'text-slate-900', labelColor = 'text-slate-400' }) => <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-1"><span className={`text-xs font-bold uppercase tracking-wider ${labelColor}`}>{label}</span><div className={`text-3xl font-extrabold font-mono ${color}`}>{value}</div><span className="text-xs text-slate-500">{detail}</span></div>;
