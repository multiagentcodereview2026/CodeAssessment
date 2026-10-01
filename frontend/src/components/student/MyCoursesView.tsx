import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Calendar, ChevronRight } from 'lucide-react';
import { useAuth } from '../../context/useAuth';

type Course = { id: number; course_code: string; title: string; term: string | null; assignments_count: number };
type Assignment = { id: number; title: string; description: string | null; course_id: number; course_title: string; due_date: string | null; status: string; problems: string[]; problem_titles: string[] };
type Submission = { assignment_id: number | null; problem_id: string };

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

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      authFetch('/api/student/courses', { cache: 'no-store' }),
      authFetch('/api/submissions', { cache: 'no-store' })
    ]).then(async ([coursesResponse, submissionsResponse]) => {
      if (!coursesResponse.ok || !submissionsResponse.ok) throw new Error('Your course data could not be loaded.');
      const [courseData, submissionData] = await Promise.all([coursesResponse.json(), submissionsResponse.json()]);
      if (cancelled) return;
      const nextCourses = Array.isArray(courseData) ? courseData : [];
      setCourses(nextCourses);
      setSelectedCourseId(nextCourses[0]?.id ?? null);
      setSubmissions(Array.isArray(submissionData) ? submissionData : []);
    }).catch((loadError: unknown) => {
      if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'Your course data could not be loaded.');
    }).finally(() => {
      if (!cancelled) setCoursesLoading(false);
    });
    return () => { cancelled = true; };
  }, [authFetch]);

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
    <main className="mx-auto max-w-6xl space-y-6 pb-12">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-xs font-bold uppercase text-indigo-700">Student workspace</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">My Courses</h1>
      </header>

      {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>}
      {coursesLoading ? <p className="py-8 text-sm text-slate-500">Loading enrolled courses…</p> : courses.length === 0 ? (
        <section className="border-y border-slate-200 py-10 text-center">
          <BookOpen className="mx-auto h-8 w-8 text-slate-400" />
          <p className="mt-3 font-semibold text-slate-800">No enrolled courses</p>
          <p className="mt-1 text-sm text-slate-500">Courses assigned to your account will appear here.</p>
          <Link to="/problems" className="mt-4 inline-block text-sm font-semibold text-indigo-700">Practice from the Problem Bank</Link>
        </section>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <nav className="space-y-2" aria-label="Enrolled courses">
            {courses.map((course) => (
              <button key={course.id} onClick={() => setSelectedCourseId(course.id)} className={`w-full rounded-lg border p-4 text-left ${selectedCourseId === course.id ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
                <span className="font-mono text-xs font-bold text-indigo-700">{course.course_code}</span>
                <span className="mt-1 block font-semibold text-slate-900">{course.title}</span>
                <span className="mt-1 block text-xs text-slate-500">{course.term || 'No term'} · {course.assignments_count} assignments</span>
              </button>
            ))}
          </nav>

          <section className="min-w-0">
            <div className="mb-4 flex items-end justify-between border-b border-slate-200 pb-3">
              <div>
                <h2 className="text-lg font-bold text-slate-900">{selectedCourse?.title}</h2>
                <p className="text-xs text-slate-500">Assignments available to your enrollment</p>
              </div>
            </div>
            {assignmentsLoading ? <p className="py-8 text-sm text-slate-500">Loading assignments…</p> : assignments.length === 0 ? (
              <p className="border-y border-slate-200 py-8 text-center text-sm text-slate-500">No published assignments for this course yet.</p>
            ) : (
              <div className="divide-y divide-slate-200 border-y border-slate-200">
                {assignments.map((assignment) => {
                  const completed = new Set(submissions.filter((submission) => submission.assignment_id === assignment.id).map((submission) => submission.problem_id)).size;
                  return (
                    <article key={assignment.id} className="space-y-3 py-5">
                      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                        <div>
                          <h3 className="font-semibold text-slate-900">{assignment.title}</h3>
                          {assignment.description && <p className="mt-1 text-sm text-slate-600">{assignment.description}</p>}
                        </div>
                        <div className="text-left text-xs text-slate-500 sm:text-right">
                          <span className="inline-flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'No due date'}</span>
                          <p className="mt-1">{completed}/{assignment.problems.length} problems submitted</p>
                        </div>
                      </div>
                      <div className="space-y-2">
                        {assignment.problems.map((problemId, index) => (
                          <button key={problemId} onClick={() => navigate(`/problems/${encodeURIComponent(problemId)}?assignmentId=${assignment.id}`)} className="flex w-full items-center justify-between rounded-md border border-slate-200 px-3 py-2.5 text-left text-sm hover:border-indigo-300 hover:bg-indigo-50">
                            <span><span className="mr-2 font-mono text-xs text-slate-400">{index + 1}.</span>{assignment.problem_titles[index] || problemId}</span>
                            <ChevronRight className="h-4 w-4 text-slate-400" />
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
    </main>
  );
};
