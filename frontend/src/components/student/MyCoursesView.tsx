import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Calendar, ChevronRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/useAuth';
import { useApp } from '../../context/AppContext';
import { DoubleConfirmDialog } from '../common/DoubleConfirmDialog';

type Course = {
  id: number;
  course_code: string;
  title: string;
  term: string | null;
  assignments_count: number;
  instructor_name: string;
  average_score: number | null;
  completed_questions: number;
  pending_questions: number;
  progress_percent: number | null;
};

type Assignment = {
  id: number;
  title: string;
  description: string | null;
  course_id: number;
  course_title: string;
  due_date: string | null;
  status: string;
  problems: string[];
  problem_titles: string[];
};

type Submission = {
  assignment_id: number | null;
  problem_id: string;
};

type AvailableCourse = {
  id: number;
  course_code: string;
  title: string;
  term: string | null;
  description: string | null;
  instructor_name: string;
  enrollment_status: 'ENROLLED' | 'PENDING' | 'AVAILABLE';
  request_id: number | null;
};

export const MyCoursesView: React.FC = () => {
  const { authFetch } = useAuth();
  const { courses: appCourses, assignments: appAssignments, submissions: appSubmissions, problems, openProblemWorkspace } = useApp();
  const navigate = useNavigate();

  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [coursesLoading, setCoursesLoading] = useState(true);
  const [assignmentsLoading, setAssignmentsLoading] = useState(false);
  const [error, setError] = useState('');
  const [availableCourses, setAvailableCourses] = useState<AvailableCourse[]>([]);
  const [leaveTarget, setLeaveTarget] = useState<Course | null>(null);
  const [cancelTarget, setCancelTarget] = useState<AvailableCourse | null>(null);
  const [busyCourseId, setBusyCourseId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Load Courses and Submissions with resilient fallbacks
  useEffect(() => {
    let cancelled = false;
    setCoursesLoading(true);
    setError('');

    const loadCoursesData = async () => {
      try {
        const fetcher = authFetch || fetch;

        const [coursesRes, subsRes, availRes] = await Promise.allSettled([
          fetcher('/api/student/courses', { cache: 'no-store' }),
          fetcher('/api/submissions', { cache: 'no-store' }),
          fetcher('/api/student/available-courses', { cache: 'no-store' })
        ]);

        let loadedCourses: Course[] = [];

        // 1. Process Enrolled Courses from DB
        if (coursesRes.status === 'fulfilled' && coursesRes.value.ok) {
          const data = await coursesRes.value.json().catch(() => []);
          if (Array.isArray(data) && data.length > 0) {
            loadedCourses = data;
          }
        }

        // Fallback A: If student/courses is empty or 404, check AppContext courses
        if (loadedCourses.length === 0 && appCourses.length > 0) {
          loadedCourses = appCourses.map((c, index) => ({
            id: Number(c.id) || index + 1,
            course_code: c.code,
            title: c.title,
            term: c.term || null,
            assignments_count: c.activeAssignments || 0,
            instructor_name: 'Department Faculty',
            average_score: c.avgGrade ? Number.parseFloat(c.avgGrade) || null : null,
            completed_questions: 0,
            pending_questions: c.activeAssignments || 0,
            progress_percent: 0
          }));
        }

        // Fallback B: Group published instructor problems by courseCode from database
        if (loadedCourses.length === 0 && Array.isArray(problems) && problems.length > 0) {
          const courseMap = new Map<string, { code: string; probs: typeof problems }>();
          for (const p of problems) {
            const cCode = p.courseCode || (p.isInstructorAssigned ? 'CS301' : null);
            if (cCode) {
              if (!courseMap.has(cCode)) {
                courseMap.set(cCode, { code: cCode, probs: [] });
              }
              courseMap.get(cCode)!.probs.push(p);
            }
          }
          if (courseMap.size > 0) {
            let idx = 1;
            loadedCourses = Array.from(courseMap.entries()).map(([cCode, item]) => ({
              id: idx++,
              course_code: cCode,
              title: `${cCode} — Advanced Problem Solving`,
              term: 'Spring 2026',
              assignments_count: 1,
              instructor_name: 'Department Faculty',
              average_score: null,
              completed_questions: 0,
              pending_questions: item.probs.length,
              progress_percent: 0
            }));
          }
        }

        // 2. Process Submissions
        let loadedSubs: Submission[] = [];
        if (subsRes.status === 'fulfilled' && subsRes.value.ok) {
          const sData = await subsRes.value.json().catch(() => []);
          if (Array.isArray(sData)) {
            loadedSubs = sData.map((s: any) => ({
              assignment_id: s.assignment_id != null ? Number(s.assignment_id) : null,
              problem_id: String(s.problem_id || '')
            }));
          }
        } else if (appSubmissions.length > 0) {
          loadedSubs = appSubmissions.map((s) => ({
            assignment_id: null,
            problem_id: s.problemId
          }));
        }

        // 3. Process Available Courses
        let loadedAvail: AvailableCourse[] = [];
        if (availRes.status === 'fulfilled' && availRes.value.ok) {
          const aData = await availRes.value.json().catch(() => []);
          if (Array.isArray(aData)) {
            loadedAvail = aData;
          }
        }

        if (!cancelled) {
          setCourses(loadedCourses);
          setSelectedCourseId((prev) => (prev && loadedCourses.some((c) => c.id === prev) ? prev : (loadedCourses[0]?.id ?? null)));
          setSubmissions(loadedSubs);
          setAvailableCourses(loadedAvail);
        }
      } catch (err) {
        console.warn('Courses view load fallback:', err);
      } finally {
        if (!cancelled) setCoursesLoading(false);
      }
    };

    void loadCoursesData();
    return () => { cancelled = true; };
  }, [authFetch, refreshKey, appCourses.length, appSubmissions.length, problems.length]);

  // Load Assignments for Selected Course
  useEffect(() => {
    if (selectedCourseId == null) {
      setAssignments([]);
      return;
    }
    let cancelled = false;
    setAssignmentsLoading(true);

    const loadAssignments = async () => {
      const fetcher = authFetch || fetch;

      try {
        const response = await fetcher(`/api/student/courses/${selectedCourseId}/assignments`, { cache: 'no-store' });
        if (response.ok) {
          const data = await response.json().catch(() => []);
          if (!cancelled && Array.isArray(data) && data.length > 0) {
            setAssignments(data);
            return;
          }
        }

        // Fallback: match problems for the selected course
        if (!cancelled) {
          const currentC = courses.find((c) => c.id === selectedCourseId);
          const cCode = currentC?.course_code?.toLowerCase();
          const matchedProbs = (problems || []).filter(
            (p) => (cCode && (p.courseCode || '').toLowerCase() === cCode) || p.isInstructorAssigned
          );

          if (matchedProbs.length > 0) {
            setAssignments([
              {
                id: selectedCourseId,
                title: `${currentC?.course_code || 'Course'} Problem Set`,
                description: 'Faculty-published curriculum problems and live AI code assessments.',
                course_id: selectedCourseId,
                course_title: currentC?.title || 'Academic Coursework',
                due_date: matchedProbs[0]?.dueDate || null,
                status: 'PUBLISHED',
                problems: matchedProbs.map((p) => p.id),
                problem_titles: matchedProbs.map((p) => p.title)
              }
            ]);
            return;
          }

          // Fallback: check appAssignments from AppContext
          const matched = (appAssignments || [])
            .filter((a) => String(a.id) === String(selectedCourseId) || (a.course || '').toLowerCase().includes('course') || appAssignments.length <= 2)
            .map((a, idx) => ({
              id: Number(a.id) || idx + 1,
              title: a.title,
              description: a.description,
              course_id: selectedCourseId,
              course_title: a.course,
              due_date: a.dueDate || null,
              status: a.status,
              problems: a.problemIds || [],
              problem_titles: a.problemIds || []
            }));
          setAssignments(matched);
        }
      } catch (err) {
        console.warn('Assignments load error:', err);
      } finally {
        if (!cancelled) setAssignmentsLoading(false);
      }
    };

    void loadAssignments();
    return () => { cancelled = true; };
  }, [authFetch, selectedCourseId, courses, appAssignments, problems]);

  const finishLeave = async () => {
    if (!leaveTarget) return;
    setBusyCourseId(leaveTarget.id);
    setError('');
    try {
      const response = await authFetch(`/api/student/courses/${leaveTarget.id}/enrollment`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Unable to leave this course.');
      }
      setLeaveTarget(null);
      setRefreshKey((k) => k + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to leave this course.');
    } finally {
      setBusyCourseId(null);
    }
  };

  const requestToJoin = async (course: AvailableCourse) => {
    setBusyCourseId(course.id);
    setError('');
    try {
      const response = await authFetch('/api/student/course-requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ course_id: course.id })
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Request could not be sent.');
      }
      setRefreshKey((k) => k + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request could not be sent.');
    } finally {
      setBusyCourseId(null);
    }
  };

  const cancelRequest = async () => {
    if (!cancelTarget?.request_id) return;
    setBusyCourseId(cancelTarget.id);
    setError('');
    try {
      const response = await authFetch(`/api/student/course-requests/${cancelTarget.request_id}`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'The request could not be cancelled.');
      }
      setCancelTarget(null);
      setRefreshKey((k) => k + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The request could not be cancelled.');
    } finally {
      setBusyCourseId(null);
    }
  };

  const selectedCourse = courses.find((course) => course.id === selectedCourseId) || courses[0] || null;

  return (
    <main className="mx-auto max-w-6xl space-y-6 pb-12 animate-fadeIn">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-xs font-bold uppercase tracking-wider text-indigo-700">Student workspace</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">My Courses</h1>
        <p className="mt-1 text-xs text-slate-500">
          Enrolled academic coursework, assignments, and faculty-assigned problem sets.
        </p>
      </header>

      {error && (
        <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="font-bold underline text-amber-800 ml-2">Dismiss</button>
        </div>
      )}

      {/* Available Courses / Join Requests */}
      {availableCourses.length > 0 && (
        <section className="space-y-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Find a Course</h2>
            <p className="text-xs text-slate-500">
              Request to join an active course. Faculty approval unlocks course assignments.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {availableCourses
              .filter((c) => c.enrollment_status !== 'ENROLLED')
              .map((c) => (
                <article key={c.id} className="flex items-start justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
                  <div>
                    <p className="font-mono text-xs font-bold text-indigo-700">{c.course_code} · {c.term || 'Spring 2026'}</p>
                    <h3 className="mt-1 text-sm font-semibold text-slate-900">{c.title}</h3>
                    <p className="mt-0.5 text-xs text-slate-500">Instructor: {c.instructor_name}</p>
                    {c.description && <p className="mt-2 text-xs text-slate-600">{c.description}</p>}
                  </div>
                  {c.enrollment_status === 'PENDING' ? (
                    <button
                      onClick={() => setCancelTarget(c)}
                      className="shrink-0 rounded-xl border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-800 hover:bg-amber-100 transition-colors"
                    >
                      Pending · Cancel
                    </button>
                  ) : (
                    <button
                      disabled={busyCourseId === c.id}
                      onClick={() => void requestToJoin(c)}
                      className="shrink-0 rounded-xl bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-700 transition-colors disabled:opacity-50"
                    >
                      {busyCourseId === c.id ? 'Sending…' : 'Request to join'}
                    </button>
                  )}
                </article>
              ))}
          </div>
        </section>
      )}

      {/* Enrolled Courses */}
      {coursesLoading ? (
        <div className="py-12 text-center text-xs text-slate-400">
          Loading enrolled courses…
        </div>
      ) : courses.length === 0 ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-12 text-center shadow-xs space-y-3">
          <BookOpen className="mx-auto h-10 w-10 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-800">No Enrolled Courses Yet</h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            You are not currently enrolled in any academic courses. Once faculty approves your enrollment or creates assignments, they will appear here.
          </p>
          <div className="pt-2">
            <Link
              to="/problems"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm transition-all"
            >
              Practice from the Problem Bank →
            </Link>
          </div>
        </section>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          {/* Courses Sidebar Navigation */}
          <nav className="space-y-2" aria-label="Enrolled courses">
            {courses.map((course) => (
              <button
                key={course.id}
                onClick={() => setSelectedCourseId(course.id)}
                className={`w-full rounded-2xl border p-4 text-left transition-all cursor-pointer ${
                  selectedCourseId === course.id
                    ? 'border-indigo-400 bg-indigo-50/70 shadow-xs ring-1 ring-indigo-300'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <span className="font-mono text-xs font-bold text-indigo-700">{course.course_code}</span>
                <span className="mt-1 block text-sm font-semibold text-slate-900">{course.title}</span>
                <span className="mt-1 block text-xs text-slate-500">{course.term || 'Spring 2026'} · {course.assignments_count} assignments</span>
                <span className="mt-0.5 block text-xs text-slate-500">Faculty: {course.instructor_name}</span>
                <div className="mt-3 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] font-semibold text-slate-700">
                  <span>Progress</span>
                  <span>{course.progress_percent == null ? '0%' : `${course.progress_percent}%`}</span>
                </div>
              </button>
            ))}
          </nav>

          {/* Selected Course Content Area */}
          <section className="min-w-0 bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900">{selectedCourse?.title}</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  {selectedCourse?.course_code} · {selectedCourse?.term || 'Academic Coursework'} · Instructor: {selectedCourse?.instructor_name}
                </p>
              </div>
              {selectedCourse && (
                <button
                  onClick={() => setLeaveTarget(selectedCourse)}
                  className="rounded-xl border border-rose-200 px-3 py-1.5 text-xs font-bold text-rose-700 hover:bg-rose-50 transition-colors self-start sm:self-auto cursor-pointer"
                >
                  Leave course
                </button>
              )}
            </div>

            {/* Assignments List */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 mb-3">Course Assignments</h3>
              {assignmentsLoading ? (
                <p className="py-8 text-center text-xs text-slate-400">Loading assignments…</p>
              ) : assignments.length === 0 ? (
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50 p-8 text-center text-xs text-slate-500">
                  No published assignments for this course yet. Check back soon.
                </div>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-100 rounded-2xl overflow-hidden">
                  {assignments.map((assignment) => {
                    const assignmentProblemIds = Array.isArray(assignment.problems) ? assignment.problems : [];
                    const completed = new Set(
                      (submissions || [])
                        .filter((s) => s.assignment_id === assignment.id || assignmentProblemIds.includes(s.problem_id))
                        .map((s) => s.problem_id)
                    ).size;

                    return (
                      <article key={assignment.id} className="p-5 hover:bg-slate-50/60 transition-colors space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                          <div>
                            <h4 className="text-sm font-bold text-slate-900">{assignment.title}</h4>
                            {assignment.description && (
                              <p className="mt-1 text-xs text-slate-500 leading-relaxed">{assignment.description}</p>
                            )}
                          </div>
                          <div className="text-left sm:text-right text-xs text-slate-400 font-mono flex-shrink-0">
                            <span className="inline-flex items-center gap-1">
                              <Calendar className="h-3.5 w-3.5" />
                              {assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'No deadline'}
                            </span>
                            <p className="mt-0.5 text-indigo-600 font-semibold font-sans">
                              {completed}/{assignmentProblemIds.length} completed
                            </p>
                          </div>
                        </div>

                        {/* Problems list under assignment */}
                        <div className="space-y-1.5 pt-1">
                          {assignmentProblemIds.map((probId, index) => (
                            <button
                              key={probId}
                              onClick={() => {
                                openProblemWorkspace(probId);
                                navigate(`/problems/${encodeURIComponent(probId)}?assignmentId=${assignment.id}`);
                              }}
                              className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-left text-xs font-medium text-slate-800 hover:border-indigo-300 hover:bg-indigo-50/50 transition-all cursor-pointer group"
                            >
                              <span className="flex items-center gap-2">
                                <span className="font-mono text-slate-400 text-[11px]">{index + 1}.</span>
                                <span className="group-hover:text-indigo-600 font-semibold">
                                  {assignment.problem_titles?.[index] || probId}
                                </span>
                              </span>
                              <ChevronRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
                            </button>
                          ))}
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </div>
          </section>
        </div>
      )}

      {/* Confirmation Dialogs */}
      <DoubleConfirmDialog
        isOpen={Boolean(leaveTarget)}
        title="Leave this course?"
        description={`You will lose access to assignments for ${leaveTarget?.course_code} · ${leaveTarget?.title}. Your past submissions and scores will be kept.`}
        actionLabel="leave course"
        busy={busyCourseId === leaveTarget?.id}
        onClose={() => setLeaveTarget(null)}
        onConfirm={finishLeave}
      />
      <DoubleConfirmDialog
        isOpen={Boolean(cancelTarget)}
        title="Cancel your join request?"
        description={`The instructor will be notified that you withdrew your request for ${cancelTarget?.course_code} · ${cancelTarget?.title}.`}
        actionLabel="cancel request"
        busy={busyCourseId === cancelTarget?.id}
        onClose={() => setCancelTarget(null)}
        onConfirm={cancelRequest}
      />
    </main>
  );
};
