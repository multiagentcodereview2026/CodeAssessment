import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowDownRight, ArrowUpRight, BookOpen, ClipboardList, RefreshCw, Search, Send, Sparkles, Target, Users, X } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/useAuth';
import { StudentRosterItem } from '../../types';
import { Modal } from '../common/Modal';

type ApiRosterItem = {
  id: string; name: string; rollNumber: string; email?: string | null; department?: string | null;
  submissions_count: number; avg_score?: number | null; trend?: 'up' | 'down' | 'neutral' | null;
  weak_topics: string[]; status: 'On Track' | 'At Risk' | 'Needs Attention';
};

export const StudentRosterView: React.FC = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseId = searchParams.get('courseId');
  const topicParam = searchParams.get('topic');
  const { selectedStudent, setSelectedStudent } = useApp();
  const [studentRoster, setStudentRoster] = useState<StudentRosterItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [filterTopic, setFilterTopic] = useState(topicParam || 'all');
  const [filterStatus, setFilterStatus] = useState('all');

  const loadRoster = useCallback(async () => {
    setLoading(true); setLoadError('');
    try {
      const rosterUrl = courseId ? `/api/instructor/roster?course_id=${encodeURIComponent(courseId)}` : '/api/instructor/roster';
      const response = await auth.authFetch(rosterUrl, { cache: 'no-store' });
      if (!response.ok) throw new Error('Could not load the live course roster.');
      const data: ApiRosterItem[] = await response.json();
      setStudentRoster((Array.isArray(data) ? data : []).map((student) => ({
        id: student.id, name: student.name, rollNumber: student.rollNumber, email: student.email || '', avatar: '',
        submissionsCount: Number(student.submissions_count ?? 0), avgScore: Number(student.avg_score ?? 0),
        trend: student.trend === 'up' || student.trend === 'down' ? student.trend : 'neutral',
        weakTopics: Array.isArray(student.weak_topics) ? student.weak_topics : [], status: student.status || 'On Track',
        department: student.department || 'Not specified', year: 'Active enrollment',
      })));
    } catch (error) {
      console.error('Unable to load live instructor roster:', error);
      setStudentRoster([]); setLoadError('We could not load the roster. Refresh the page to try again.');
    } finally { setLoading(false); }
  }, [auth.authFetch, courseId]);

  useEffect(() => {
    void loadRoster();
    const refresh = () => void loadRoster();
    const timer = window.setInterval(refresh, 60_000);
    window.addEventListener('focus', refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener('focus', refresh);
    };
  }, [loadRoster]);
  useEffect(() => { setFilterTopic(topicParam || 'all'); }, [topicParam]);
  const allTopics = useMemo(() => Array.from(new Set(studentRoster.flatMap((student) => student.weakTopics))), [studentRoster]);
  const atRiskCount = studentRoster.filter((student) => student.status === 'At Risk').length;
  const needsAttentionCount = studentRoster.filter((student) => student.status === 'Needs Attention').length;
  const mostCommonWeakTopic = allTopics.map((topic) => ({ topic, count: studentRoster.filter((student) => student.weakTopics.includes(topic)).length })).sort((a, b) => b.count - a.count)[0];
  const filtered = studentRoster.filter((student) => (
    (student.name.toLowerCase().includes(search.toLowerCase()) || student.rollNumber.toLowerCase().includes(search.toLowerCase()))
    && (filterTopic === 'all' || student.weakTopics.includes(filterTopic))
    && (filterStatus === 'all' || student.status.toLowerCase() === filterStatus.toLowerCase())
  ));

  const emptyMessage = studentRoster.length ? 'No students match these filters.' : 'No students are enrolled in your active courses yet.';

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-emerald-600">Course Rosters</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Student Performance Roster
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-600">
            Live enrollment, assessment results, score trends, and weak-topic alerts across your courses. Refreshes automatically after new evaluations.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 sm:shrink-0">
          <span className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 shadow-2xs whitespace-nowrap">
            Total Enrolled: <strong className="text-emerald-600 font-mono text-xs ml-0.5">{studentRoster.length}</strong>
          </span>

          <button
            type="button"
            onClick={() => void loadRoster()}
            disabled={loading}
            className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition disabled:opacity-50 cursor-pointer whitespace-nowrap"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/instructor/courses')}
            className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-emerald-600 px-3.5 text-xs font-semibold text-white shadow-2xs hover:bg-emerald-700 transition cursor-pointer whitespace-nowrap"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Manage Courses</span>
          </button>
        </div>
      </header>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <button onClick={() => setFilterStatus('at risk')} className="text-left bg-white rounded-2xl border border-rose-200/80 p-4 shadow-2xs hover:border-rose-400 transition-all cursor-pointer">
          <div className="flex justify-between items-center"><span className="text-xs font-bold uppercase text-rose-700">At Risk</span><AlertTriangle className="w-4 h-4 text-rose-500" /></div>
          <div className="mt-2 flex items-baseline gap-2"><span className="text-2xl font-extrabold text-rose-700 font-mono">{atRiskCount}</span><span className="text-xs text-slate-500">students</span></div>
          <p className="mt-1 text-[11px] text-slate-500">Average score below 50%.</p>
        </button>

        <button onClick={() => setFilterStatus('needs attention')} className="text-left bg-white rounded-2xl border border-amber-200/80 p-4 shadow-2xs hover:border-amber-400 transition-all cursor-pointer">
          <div className="flex justify-between items-center"><span className="text-xs font-bold uppercase text-amber-700">Needs Attention</span><Target className="w-4 h-4 text-amber-500" /></div>
          <div className="mt-2 flex items-baseline gap-2"><span className="text-2xl font-extrabold text-amber-700 font-mono">{needsAttentionCount}</span><span className="text-xs text-slate-500">students</span></div>
          <p className="mt-1 text-[11px] text-slate-500">Low scores, weak topics, or no coursework submissions.</p>
        </button>

        <button onClick={() => mostCommonWeakTopic && setFilterTopic(mostCommonWeakTopic.topic)} className="text-left bg-white rounded-2xl border border-emerald-200/80 p-4 shadow-2xs hover:border-emerald-400 transition-all cursor-pointer">
          <div className="flex justify-between items-center"><span className="text-xs font-bold uppercase text-emerald-700">Common Gap</span><ClipboardList className="w-4 h-4 text-emerald-500" /></div>
          <div className="mt-2 text-sm font-extrabold text-slate-900">{mostCommonWeakTopic?.topic || 'No assessed weak topics'}</div>
          <p className="mt-1 text-[11px] text-slate-500">{mostCommonWeakTopic ? `${mostCommonWeakTopic.count} students show this gap.` : 'Appears after evaluated submissions.'}</p>
        </button>
      </div>

      {/* Main Table Container */}
      <main className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by student name or ID..."
              className="h-9 w-full rounded-xl border border-slate-200 bg-slate-50/70 py-1.5 pl-9 pr-8 text-xs text-slate-900 outline-none transition-all placeholder:text-slate-400 focus:border-emerald-500 focus:bg-white focus:ring-1 focus:ring-emerald-100"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-500">
              Weak Area:
              <select
                value={filterTopic}
                onChange={(event) => setFilterTopic(event.target.value)}
                className="h-9 rounded-xl border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-700 outline-none transition-all hover:border-slate-300 focus:border-emerald-500 cursor-pointer"
              >
                <option value="all">All Topics</option>
                {allTopics.map((topic) => (
                  <option key={topic} value={topic}>{topic}</option>
                ))}
              </select>
            </label>

            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-500">
              Status:
              <select
                value={filterStatus}
                onChange={(event) => setFilterStatus(event.target.value)}
                className="h-9 rounded-xl border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-700 outline-none transition-all hover:border-slate-300 focus:border-emerald-500 cursor-pointer"
              >
                <option value="all">All Statuses</option>
                <option value="on track">On Track</option>
                <option value="needs attention">Needs Attention</option>
                <option value="at risk">At Risk</option>
              </select>
            </label>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200/80 bg-slate-50/75 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4">Student</th>
                <th className="py-3 px-4">Submissions</th>
                <th className="py-3 px-4">Avg Score</th>
                <th className="py-3 px-4">Trend</th>
                <th className="py-3 px-4">Weak Topics</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading && <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">Loading the live roster…</td></tr>}
              {!loading && loadError && <tr><td colSpan={6} className="px-6 py-12 text-center text-rose-600">{loadError}<button onClick={() => void loadRoster()} className="ml-3 font-bold underline cursor-pointer">Retry</button></td></tr>}
              {!loading && !loadError && filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <p className="font-bold text-slate-700">{emptyMessage}</p>
                    <p className="mt-1 text-slate-500">{studentRoster.length ? 'Clear a filter or search term to view the roster.' : 'Open a course, choose Manage Class, then enroll a registered student account.'}</p>
                    {!studentRoster.length && (
                      <button onClick={() => navigate('/instructor/courses')} className="mt-4 text-emerald-600 font-bold hover:underline cursor-pointer">
                        Go to Courses
                      </button>
                    )}
                  </td>
                </tr>
              )}
              {!loading && !loadError && filtered.map((student) => (
                <tr key={student.id} onClick={() => setSelectedStudent(student)} className="hover:bg-emerald-50/30 transition-colors cursor-pointer group">
                  <td className="py-3.5 px-4">
                    <div>
                      <span className="font-bold text-slate-900 block group-hover:text-emerald-700">{student.name}</span>
                      <span className="text-[11px] text-slate-400 font-mono">{student.rollNumber} • {student.department}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-700">{student.submissionsCount}</td>
                  <td className="py-3.5 px-4 font-mono font-extrabold text-sm">
                    <span className={student.avgScore >= 75 ? 'text-emerald-600' : student.avgScore >= 60 ? 'text-teal-700' : student.avgScore ? 'text-rose-600' : 'text-slate-400'}>
                      {student.avgScore ? `${student.avgScore}%` : 'N/A'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    {student.trend === 'up' ? (
                      <span className="inline-flex items-center gap-1 font-bold text-emerald-600"><ArrowUpRight className="w-4 h-4" />Improving</span>
                    ) : student.trend === 'down' ? (
                      <span className="inline-flex items-center gap-1 font-bold text-rose-600"><ArrowDownRight className="w-4 h-4" />Declining</span>
                    ) : (
                      <span className="text-slate-400 font-mono font-bold">No change</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex flex-wrap gap-1.5">
                      {student.weakTopics.length ? student.weakTopics.map((topic) => (
                        <span key={topic} className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                          {topic}
                        </span>
                      )) : (
                        <span className="text-slate-400">No assessed gaps</span>
                      )}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={(event) => { event.stopPropagation(); setSelectedStudent(student); }}
                      className="px-2.5 py-1.5 bg-slate-100 hover:bg-emerald-600 hover:text-white rounded-lg font-bold text-xs text-slate-700 transition-colors cursor-pointer"
                    >
                      Inspect Profile
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>

      {/* Student Diagnostic Modal */}
      {selectedStudent && (
        <Modal isOpen onClose={() => setSelectedStudent(null)} title={`Student Diagnostic: ${selectedStudent.name}`} subtitle={`Student ID: ${selectedStudent.rollNumber} • ${selectedStudent.department}`} maxWidth="2xl">
          <div className="space-y-6 text-xs">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
                <span className="text-slate-400 block font-semibold">Submissions</span>
                <span className="text-2xl font-mono font-extrabold text-slate-800 mt-1 block">{selectedStudent.submissionsCount}</span>
              </div>
              <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-200">
                <span className="text-emerald-700 block font-semibold">Average Grade</span>
                <span className="text-2xl font-mono font-extrabold text-emerald-700 mt-1 block">{selectedStudent.avgScore ? `${selectedStudent.avgScore}%` : 'N/A'}</span>
              </div>
              <div className="p-4 bg-purple-50 rounded-2xl border border-purple-200">
                <span className="text-purple-700 block font-semibold">Cohort Status</span>
                <span className="text-xs font-extrabold text-purple-800 mt-2 block">{selectedStudent.status}</span>
              </div>
            </div>

            <div className="p-5 bg-slate-900 text-white rounded-3xl space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <Sparkles className="w-4 h-4" />
                <span>Performance Summary</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {selectedStudent.submissionsCount
                  ? `This summary is calculated from evaluated coursework submissions. ${selectedStudent.weakTopics.length ? `Focus follow-up work on ${selectedStudent.weakTopics.join(', ')}.` : 'No weak topic is currently detected.'}`
                  : 'No coursework has been submitted yet. Assign or activate coursework, then use the first evaluated submission as the baseline.'}
              </p>
            </div>

            <div>
              <span className="font-bold text-slate-800 mb-2 block">Identified Concept Gaps</span>
              <div className="flex flex-wrap gap-2">
                {selectedStudent.weakTopics.length ? selectedStudent.weakTopics.map((topic) => (
                  <span key={topic} className="px-3.5 py-1.5 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 font-bold">
                    ⚠️ {topic}
                  </span>
                )) : (
                  <span className="text-slate-500">No gaps detected from evaluated work.</span>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              {selectedStudent.email ? (
                <a href={`mailto:${selectedStudent.email}`} className="inline-flex items-center gap-1.5 text-emerald-600 font-bold hover:underline">
                  <Send className="w-4 h-4" />
                  Send Direct Feedback Email
                </a>
              ) : (
                <span className="text-slate-400">No email available</span>
              )}
              <button onClick={() => setSelectedStudent(null)} className="px-5 py-2.5 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 cursor-pointer">
                Close Report
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
