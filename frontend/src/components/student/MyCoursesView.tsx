import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Calendar, ChevronRight } from 'lucide-react';
import { useAuth } from '../../context/useAuth';
import { DoubleConfirmDialog } from '../common/DoubleConfirmDialog';

type Course = { id: number; course_code: string; title: string; term: string | null; assignments_count: number; instructor_name: string; average_score: number | null; completed_questions: number; pending_questions: number; progress_percent: number | null };
type Assignment = { id: number; title: string; description: string | null; course_id: number; course_title: string; due_date: string | null; status: string; problems: string[]; problem_titles: string[] };
type Submission = { assignment_id: number | null; problem_id: string };
type AvailableCourse = { id: number; course_code: string; title: string; term: string | null; description: string | null; instructor_name: string; enrollment_status: 'ENROLLED' | 'PENDING' | 'AVAILABLE'; request_id: number | null };

export const MyCoursesView: React.FC = () => {
  const { authFetch } = useAuth();
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

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      authFetch('/api/student/courses', { cache: 'no-store' }),
      authFetch('/api/submissions', { cache: 'no-store' }),
      authFetch('/api/student/available-courses', { cache: 'no-store' })
    ]).then(async ([coursesResponse, submissionsResponse, availableResponse]) => {
      if (!coursesResponse.ok || !submissionsResponse.ok || !availableResponse.ok) throw new Error('Your course data could not be loaded.');
      const [courseData, submissionData, availableData] = await Promise.all([coursesResponse.json(), submissionsResponse.json(), availableResponse.json()]);
      if (cancelled) return;
      const nextCourses = Array.isArray(courseData) ? courseData : [];
      setCourses(nextCourses);
      setSelectedCourseId(nextCourses[0]?.id ?? null);
      setSubmissions(Array.isArray(submissionData) ? submissionData : []);
      setAvailableCourses(Array.isArray(availableData) ? availableData : []);
    }).catch((loadError: unknown) => {
      if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'Your course data could not be loaded.');
    }).finally(() => {
      if (!cancelled) setCoursesLoading(false);
    });
    return () => { cancelled = true; };
  }, [authFetch, refreshKey]);

  const finishLeave = async () => {
    if (!leaveTarget) return;
    setBusyCourseId(leaveTarget.id); setError('');
    try {
      const response = await authFetch(`/api/student/courses/${leaveTarget.id}/enrollment`, { method: 'DELETE' });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || 'You could not leave this course.');
      setLeaveTarget(null);
      setRefreshKey((key) => key + 1);
    } catch (leaveError) {
      setError(leaveError instanceof Error ? leaveError.message : 'You could not leave this course.');
    } finally { setBusyCourseId(null); }
  };

  const requestToJoin = async (course: AvailableCourse) => {
    setBusyCourseId(course.id); setError('');
    try {
      const response = await authFetch('/api/student/course-requests', { method: 'POST', body: JSON.stringify({ course_id: course.id }) });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || 'Your request could not be sent.');
      setRefreshKey((key) => key + 1);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Your request could not be sent.');
    } finally { setBusyCourseId(null); }
  };

  const cancelRequest = async () => {
    if (!cancelTarget?.request_id) return;
    setBusyCourseId(cancelTarget.id); setError('');
    try {
      const response = await authFetch(`/api/student/course-requests/${cancelTarget.request_id}`, { method: 'DELETE' });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || 'The request could not be cancelled.');
      setCancelTarget(null);
      setRefreshKey((key) => key + 1);
    } catch (cancelError) {
      setError(cancelError instanceof Error ? cancelError.message : 'The request could not be cancelled.');
    } finally { setBusyCourseId(null); }
  };

  useEffect(() => {
    if (selectedCourseId == null) {
      setAssignments([]);
      return;
    }
    let cancelled = false;
    setAssignmentsLoading(true);
    authFetch(`/api/student/courses/${selectedCourseId}/assignments`, { cache: 'no-store' })
      .then(async (response) => {
        if (!response.ok) throw new Error('Assignments could not be loaded.');
        return response.json();
      })
      .then((data) => {
        if (!cancelled) setAssignments(Array.isArray(data) ? data : []);
      })
      .catch((loadError: unknown) => {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'Assignments could not be loaded.');
      })
      .finally(() => {
        if (!cancelled) setAssignmentsLoading(false);
      });
    return () => { cancelled = true; };
  }, [authFetch, selectedCourseId]);

  const selectedCourse = courses.find((course) => course.id === selectedCourseId);

  return (
    <main className="mx-auto max-w-6xl space-y-6 pb-12 animate-fadeIn font-sans">
      {/* Header */}
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 dark:border-white/10 pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-indigo-600 dark:text-indigo-400">
            Student workspace
          </p>
          <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            My Courses
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-600 dark:text-zinc-400">
            Request to join active courses, track assignments, and access instructor-curated problem sets.
          </p>
        </div>
      </header>

      {error && (
        <p role="alert" className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </p>
      )}

      {/* Find a Course */}
      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            Find a course
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-zinc-400 mt-0.5">
            Request to join an active course. The instructor must approve your request before assignments become available.
          </p>
        </div>

        {availableCourses.length === 0 ? (
          <p className="rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#121217] p-5 text-sm text-slate-500 dark:text-zinc-400">
            No active courses are available to request right now.
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {availableCourses
              .filter((course) => course.enrollment_status !== 'ENROLLED')
              .map((course) => (
                <article
                  key={course.id}
                  className="flex items-start justify-between gap-4 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 shadow-xs hover:border-indigo-400 dark:hover:border-white/25 card-hover transition-all"
                >
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
                        {course.course_code}
                      </span>
                      <span className="text-xs font-semibold text-slate-500 dark:text-zinc-400">
                        {course.term || 'No term'}
                      </span>
                    </div>

                    <h3 className="mt-2 text-base font-bold text-slate-900 dark:text-white tracking-tight">
                      {course.title}
                    </h3>

                    <p className="text-xs text-slate-500 dark:text-zinc-400">
                      Instructor: <span className="font-semibold text-slate-700 dark:text-zinc-300">{course.instructor_name}</span>
                    </p>

                    {course.description && (
                      <p className="mt-2 text-xs text-slate-600 dark:text-zinc-400 leading-relaxed line-clamp-2">
                        {course.description}
                      </p>
                    )}
                  </div>

                  {course.enrollment_status === 'PENDING' ? (
                    <button
                      onClick={() => setCancelTarget(course)}
                      className="shrink-0 rounded-xl border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 px-3.5 py-2 text-xs font-bold text-amber-400 transition-all cursor-pointer ring-1 ring-amber-500/20"
                    >
                      Request pending · Cancel
                    </button>
                  ) : (
                    <button
                      disabled={busyCourseId === course.id}
                      onClick={() => void requestToJoin(course)}
                      className="shrink-0 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-xs font-bold text-white shadow-md shadow-indigo-600/30 transition-all cursor-pointer active:scale-95 disabled:opacity-50 ring-1 ring-white/10"
                    >
                      {busyCourseId === course.id ? 'Sending…' : 'Request to join'}
                    </button>
                  )}
                </article>
              ))}
          </div>
        )}
      </section>

      {/* Enrolled Courses */}
      {coursesLoading ? (
        <p className="py-8 text-sm text-slate-500 dark:text-zinc-400">Loading enrolled courses…</p>
      ) : courses.length === 0 ? (
        <section className="rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#121217] py-12 px-6 text-center">
          <BookOpen className="mx-auto h-9 w-9 text-slate-400 dark:text-zinc-500" />
          <p className="mt-3 text-base font-bold text-slate-800 dark:text-white tracking-tight">No enrolled courses</p>
          <p className="mt-1 text-sm text-slate-500 dark:text-zinc-400">Courses assigned to your account will appear here.</p>
          <Link
            to="/problems"
            className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/30 transition-all cursor-pointer"
          >
            Practice from the Problem Bank
          </Link>
        </section>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
          <nav className="space-y-2.5" aria-label="Enrolled courses">
            {courses.map((course) => {
              const isSelected = selectedCourseId === course.id;
              return (
                <button
                  key={course.id}
                  onClick={() => setSelectedCourseId(course.id)}
                  className={`w-full rounded-2xl border p-4 text-left transition-all cursor-pointer ${
                    isSelected
                      ? 'border-indigo-500/60 bg-indigo-50 dark:bg-indigo-950/20 shadow-sm ring-1 ring-indigo-500/40'
                      : 'border-slate-200 dark:border-white/10 bg-white dark:bg-[#121217] hover:border-slate-300 dark:hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
                      {course.course_code}
                    </span>
                    <span className="text-[11px] font-semibold text-slate-500 dark:text-zinc-400">
                      {course.term || 'No term'}
                    </span>
                  </div>

                  <span className="mt-2 block font-bold text-slate-900 dark:text-white tracking-tight text-sm">
                    {course.title}
                  </span>

                  <span className="mt-1 block text-xs text-slate-500 dark:text-zinc-400">
                    Instructor: <span className="text-slate-700 dark:text-zinc-300 font-medium">{course.instructor_name}</span>
                  </span>

                  <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-white/8 flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-600 dark:text-zinc-400">
                      Progress: <span className="font-bold text-indigo-600 dark:text-indigo-400">{course.progress_percent == null ? '0%' : `${course.progress_percent}%`}</span>
                    </span>
                    <span className="text-[11px] text-slate-400 dark:text-zinc-500">
                      {course.assignments_count} assignments
                    </span>
                  </div>
                </button>
              );
            })}
          </nav>

          <section className="min-w-0">
            <div className="mb-4 flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {selectedCourse?.title}
                </h2>
                <p className="mt-1 text-xs text-slate-500 dark:text-zinc-400">
                  <span className="font-semibold text-indigo-400">{selectedCourse?.course_code}</span> · {selectedCourse?.term || 'No term'} · Instructor: <span className="text-zinc-300">{selectedCourse?.instructor_name}</span>
                </p>
                <p className="mt-1 text-xs font-semibold text-slate-600 dark:text-zinc-400">
                  Course progress: <span className="font-bold text-indigo-400">{selectedCourse?.progress_percent == null ? 'No assigned questions yet' : `${selectedCourse.progress_percent}%`}</span> · Average assessed score: <span className="font-bold text-emerald-400">{selectedCourse?.average_score == null ? 'Not yet assessed' : `${selectedCourse.average_score}%`}</span>
                </p>
              </div>

              {selectedCourse && (
                <button
                  onClick={() => setLeaveTarget(selectedCourse)}
                  className="rounded-xl border border-rose-500/40 bg-rose-500/10 hover:bg-rose-500/20 px-3.5 py-2 text-xs font-bold text-rose-400 transition-all cursor-pointer shrink-0"
                >
                  Leave course
                </button>
              )}
            </div>

            {assignmentsLoading ? (
              <p className="py-8 text-sm text-slate-500 dark:text-zinc-400">Loading assignments…</p>
            ) : assignments.length === 0 ? (
              <p className="rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#121217] py-8 text-center text-sm text-slate-500 dark:text-zinc-400">
                No published assignments for this course yet.
              </p>
            ) : (
              <div className="space-y-4">
                {assignments.map((assignment) => {
                  const completed = new Set(
                    submissions
                      .filter((submission) => submission.assignment_id === assignment.id)
                      .map((submission) => submission.problem_id)
                  ).size;

                  return (
                    <article
                      key={assignment.id}
                      className="rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 shadow-xs space-y-4"
                    >
                      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                        <div>
                          <h3 className="font-bold text-base text-slate-900 dark:text-white tracking-tight">
                            {assignment.title}
                          </h3>
                          {assignment.description && (
                            <p className="mt-1 text-xs sm:text-sm text-slate-600 dark:text-zinc-400">
                              {assignment.description}
                            </p>
                          )}
                        </div>

                        <div className="text-left text-xs text-slate-500 dark:text-zinc-400 sm:text-right shrink-0">
                          <span className="inline-flex items-center gap-1 font-semibold text-slate-700 dark:text-zinc-300">
                            <Calendar className="h-3.5 w-3.5 text-indigo-400" />
                            {assignment.due_date ? new Date(assignment.due_date).toLocaleString() : 'No due date'}
                          </span>
                          {(assignment.status === 'CLOSED' || (assignment.due_date && Date.now() >= Date.parse(assignment.due_date))) && (
                            <p className="font-bold text-amber-400 mt-0.5">Closed · View only</p>
                          )}
                          <p className="mt-1 text-slate-500 dark:text-zinc-400">
                            <span className="font-bold text-slate-700 dark:text-zinc-300">{completed}</span> of {assignment.problems.length} problems submitted
                          </p>
                        </div>
                      </div>

                      <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-white/8">
                        {assignment.problems.map((problemId, index) => (
                          <button
                            key={problemId}
                            onClick={() => navigate(`/problems/${encodeURIComponent(problemId)}?assignmentId=${assignment.id}`)}
                            className="flex w-full items-center justify-between rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-[#16161d] px-4 py-3 text-left text-sm hover:border-indigo-400 dark:hover:border-white/25 hover:bg-indigo-50/40 dark:hover:bg-[#1a1a24] transition-all cursor-pointer group"
                          >
                            <span className="flex items-center gap-2">
                              <span className="text-xs font-bold text-indigo-500 dark:text-indigo-400">
                                {index + 1}.
                              </span>
                              <span className="font-medium text-slate-800 dark:text-zinc-200 group-hover:text-indigo-600 dark:group-hover:text-white transition-colors">
                                {assignment.problem_titles[index] || problemId}
                              </span>
                            </span>
                            <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition-all" />
                          </button>
                        ))}
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      )}
      <DoubleConfirmDialog isOpen={Boolean(leaveTarget)} title="Leave this course?" description={`You will lose access to assignments for ${leaveTarget?.course_code} · ${leaveTarget?.title}. Your past submissions and scores will be kept.`} actionLabel="leave course" busy={busyCourseId === leaveTarget?.id} onClose={() => setLeaveTarget(null)} onConfirm={finishLeave} />
      <DoubleConfirmDialog isOpen={Boolean(cancelTarget)} title="Cancel your join request?" description={`The instructor will be notified that you withdrew your request for ${cancelTarget?.course_code} · ${cancelTarget?.title}.`} actionLabel="cancel request" busy={busyCourseId === cancelTarget?.id} onClose={() => setCancelTarget(null)} onConfirm={cancelRequest} />
    </main>
  );
};
