import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  Search,
  UserPlus,
  UserRoundMinus,
} from 'lucide-react';
import { useAuth } from '../../context/useAuth';
import { Modal } from '../common/Modal';
import { DoubleConfirmDialog } from '../common/DoubleConfirmDialog';

type Course = {
  id: number;
  course_code: string;
  title: string;
  term: string | null;
  description: string | null;
};

type Enrollment = {
  id: number;
  student_id: string;
  student_name: string | null;
  student_email?: string | null;
  enrollment_date: string;
};

type CourseAssignment = {
  id: number;
  title: string;
  status: string;
  due_date: string | null;
  problem_titles: string[];
  submitted_count: number;
  total_students: number;
  avg_score: number | null;
};

type StudentHit = {
  student_id: string;
  name: string;
};

type CourseJoinRequest = { id: number; student_id: string; student_name: string; course_id: number; course_code: string; course_title: string; status: string; requested_at: string };

type Tab = 'students' | 'assignments' | 'requests';

export const CourseDetailsView: React.FC = () => {
  const { courseId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { authFetch } = useAuth();

  const [course, setCourse] = useState<Course | null>(null);
  const [students, setStudents] = useState<Enrollment[]>([]);
  const [assignments, setAssignments] = useState<CourseAssignment[]>([]);
  const [joinRequests, setJoinRequests] = useState<CourseJoinRequest[]>([]);
  const [enrollmentRemoveTarget, setEnrollmentRemoveTarget] = useState<Enrollment | null>(null);
  const [requestRejectTarget, setRequestRejectTarget] = useState<CourseJoinRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Existing student search/enrollment
  const [search, setSearch] = useState('');
  const [matches, setMatches] = useState<StudentHit[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');

  // General loading state
  const [busy, setBusy] = useState(false);

  const tabParam = searchParams.get('tab');
  const activeTab: Tab = tabParam === 'assignments' || tabParam === 'requests' ? tabParam : 'students';

  // Edit course modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editCode, setEditCode] = useState('');
  const [editTitle, setEditTitle] = useState('');
  const [editTerm, setEditTerm] = useState('');
  const [editDescription, setEditDescription] = useState('');

  // Enroll an existing student account by its login/student ID.
  const [isAddStudentModalOpen, setIsAddStudentModalOpen] = useState(false);
  const [newStudentId, setNewStudentId] = useState('');

  const resetAddStudentForm = () => {
    setNewStudentId('');
  };

  const openAddStudentModal = () => {
    setError('');
    resetAddStudentForm();
    setIsAddStudentModalOpen(true);
  };

  const closeAddStudentModal = () => {
    if (busy) return;

    setIsAddStudentModalOpen(false);
    resetAddStudentForm();
  };

  const loadCourseData = useCallback(async () => {
    if (!courseId) return;

    setError('');

    try {
      const [courseResponse, rosterResponse, assignmentResponse, requestResponse] =
        await Promise.all([
          authFetch(`/api/instructor/courses/${courseId}`, {
            cache: 'no-store',
          }),
          authFetch(`/api/instructor/courses/${courseId}/students`, {
            cache: 'no-store',
          }),
          authFetch(`/api/instructor/courses/${courseId}/assignments`, {
            cache: 'no-store',
          }),
          authFetch(`/api/instructor/course-requests?course_id=${courseId}`, { cache: 'no-store' }),
        ]);

      if (!courseResponse.ok) {
        throw new Error('Course could not be loaded.');
      }

      if (!rosterResponse.ok || !assignmentResponse.ok || !requestResponse.ok) {
        throw new Error('Course details could not be loaded.');
      }

      const [courseData, rosterData, assignmentData, requestData] = await Promise.all([
        courseResponse.json(),
        rosterResponse.json(),
        assignmentResponse.json(),
        requestResponse.json(),
      ]);

      setCourse(courseData);
      setStudents(Array.isArray(rosterData) ? rosterData : []);
      setAssignments(Array.isArray(assignmentData) ? assignmentData : []);
      setJoinRequests(Array.isArray(requestData) ? requestData : []);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : 'Course details could not be loaded.',
      );
    } finally {
      setLoading(false);
    }
  }, [authFetch, courseId]);

  useEffect(() => {
    void loadCourseData();
  }, [loadCourseData]);

  const handleUpdateCourse = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!editTitle.trim() || !courseId) return;

    setBusy(true);
    setError('');

    try {
      const response = await authFetch(
        `/api/instructor/courses/${courseId}`,
        {
          method: 'PATCH',
          body: JSON.stringify({
            title: editTitle.trim(),
            term: editTerm.trim() || null,
            description: editDescription.trim() || null,
          }),
        },
      );

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));

        throw new Error(
          body.detail || 'Failed to update course.',
        );
      }

      setIsEditModalOpen(false);
      await loadCourseData();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to update course.',
      );
    } finally {
      setBusy(false);
    }
  };

  // ---------------------------------------------------------
  // Search existing students
  // ---------------------------------------------------------

  const searchStudents = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!search.trim()) return;

    setBusy(true);
    setError('');

    try {
      const response = await authFetch(
        `/api/instructor/students?query=${encodeURIComponent(
          search.trim(),
        )}`,
      );

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));

        throw new Error(
          body.detail || 'Student search failed.',
        );
      }

      const data = await response.json();

      setMatches(Array.isArray(data) ? data : []);
      setSelectedStudentId('');
    } catch (searchError) {
      setError(
        searchError instanceof Error
          ? searchError.message
          : 'Student search failed.',
      );
    } finally {
      setBusy(false);
    }
  };

  // ---------------------------------------------------------
  // Enroll an existing student
  // ---------------------------------------------------------

  const enrollStudent = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!courseId || !selectedStudentId) return;

    setBusy(true);
    setError('');

    try {
      const response = await authFetch('/api/instructor/enrollments', {
        method: 'POST',
        body: JSON.stringify({
          course_id: Number(courseId),
          student_id: selectedStudentId,
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));

        throw new Error(
          body.detail || 'Enrollment could not be saved.',
        );
      }

      setSearch('');
      setMatches([]);
      setSelectedStudentId('');

      await loadCourseData();
    } catch (enrollError) {
      setError(
        enrollError instanceof Error
          ? enrollError.message
          : 'Enrollment could not be saved.',
      );
    } finally {
      setBusy(false);
    }
  };

  // ---------------------------------------------------------
  // ENROLL AN EXISTING STUDENT ACCOUNT
  // ---------------------------------------------------------

  const enrollStudentById = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!courseId) return;

    if (!newStudentId.trim()) {
      setError('Student ID is required.');
      return;
    }

    setBusy(true);
    setError('');

    try {
      const response = await authFetch(
        '/api/instructor/enrollments',
        {
          method: 'POST',
          body: JSON.stringify({
            course_id: Number(courseId),
            student_id: newStudentId.trim(),
          }),
        },
      );

      const body = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          body.detail || 'Student could not be enrolled.',
        );
      }

      // Close modal and clear form
      setIsAddStudentModalOpen(false);
      resetAddStudentForm();

      // Clear existing search state
      setSearch('');
      setMatches([]);
      setSelectedStudentId('');

      // Refresh roster
      await loadCourseData();
    } catch (createError) {
      setError(
        createError instanceof Error
          ? createError.message
          : 'Student could not be enrolled.',
      );
    } finally {
      setBusy(false);
    }
  };

  // ---------------------------------------------------------
  // Deactivate enrollment
  // ---------------------------------------------------------

  const deactivateEnrollment = async (enrollmentId: number): Promise<boolean> => {
    setBusy(true);
    setError('');

    try {
      const response = await authFetch(
        `/api/instructor/enrollments/${enrollmentId}`,
        {
          method: 'DELETE',
        },
      );

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));

        throw new Error(
          body.detail || 'Enrollment could not be deactivated.',
        );
      }

      await loadCourseData();
      return true;
    } catch (removeError) {
      setError(
        removeError instanceof Error
          ? removeError.message
          : 'Enrollment could not be deactivated.',
      );
      return false;
    } finally {
      setBusy(false);
    }
  };

  const decideJoinRequest = async (joinRequest: CourseJoinRequest, decision: 'approve' | 'reject') => {
    setBusy(true); setError('');
    try {
      const response = await authFetch(`/api/instructor/course-requests/${joinRequest.id}/${decision}`, { method: 'POST' });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || 'Course request could not be updated.');
      setRequestRejectTarget(null);
      await loadCourseData();
    } catch (decisionError) {
      setError(decisionError instanceof Error ? decisionError.message : 'Course request could not be updated.');
    } finally { setBusy(false); }
  };

  const changeTab = (tab: Tab) => {
    setSearchParams({ tab });
  };

  if (loading) {
    return (
      <div className="p-8 text-sm text-slate-500">
        Loading course…
      </div>
    );
  }

  if (!course) {
    return (
      <section className="space-y-4 p-8">
        <p className="text-sm text-rose-700">
          {error || 'Course not found.'}
        </p>

        <Link
          to="/instructor/courses"
          className="text-sm font-semibold text-emerald-700"
        >
          Back to courses
        </Link>
      </section>
    );
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 pb-12">

      {/* Back */}
      <Link
        to="/instructor/courses"
        className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-emerald-700"
      >
        <ArrowLeft className="h-4 w-4" />
        Courses
      </Link>

      {/* Course Header */}
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="font-mono text-xs font-bold text-emerald-700">
            {course.course_code} · {course.term || 'No term'}
          </p>

          <h1 className="mt-1 text-2xl font-bold text-slate-900">
            {course.title}
          </h1>

          {course.description && (
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              {course.description}
            </p>
          )}
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => {
              setEditCode(course.course_code);
              setEditTitle(course.title);
              setEditTerm(course.term || '');
              setEditDescription(course.description || '');
              setIsEditModalOpen(true);
            }}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Edit course
          </button>

          <button
            onClick={() =>
              navigate(
                `/instructor/assignments?courseId=${course.id}`,
              )
            }
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600"
          >
            <BookOpen className="h-4 w-4" />
            Create assignment
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav
        className="flex gap-5 border-b border-slate-200"
        aria-label="Course views"
      >
        <button
          onClick={() => changeTab('students')}
          className={`border-b-2 px-1 pb-3 text-sm font-semibold ${
            activeTab === 'students'
              ? 'border-emerald-700 text-emerald-800'
              : 'border-transparent text-slate-500'
          }`}
        >
          Students ({students.length})
        </button>

        <button
          onClick={() => changeTab('assignments')}
          className={`border-b-2 px-1 pb-3 text-sm font-semibold ${
            activeTab === 'assignments'
              ? 'border-emerald-700 text-emerald-800'
              : 'border-transparent text-slate-500'
          }`}
        >
          Assignments ({assignments.length})
        </button>

        <button
          onClick={() => changeTab('requests')}
          className={`border-b-2 px-1 pb-3 text-sm font-semibold ${activeTab === 'requests' ? 'border-emerald-700 text-emerald-800' : 'border-transparent text-slate-500'}`}
        >
          Join Requests ({joinRequests.length})
        </button>

        <button
          onClick={() =>
            navigate(
              `/instructor/analytics?courseId=${course.id}`,
            )
          }
          className="pb-3 text-sm font-semibold text-slate-500 hover:text-emerald-800"
        >
          Analytics
        </button>
      </nav>

      {/* Error */}
      {error && (
        <p
          role="alert"
          className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          {error}
        </p>
      )}

      {/* =====================================================
          STUDENTS TAB
      ===================================================== */}
      {activeTab === 'students' ? (
        <section className="space-y-5">

          {/* Student management header */}
          <div className="flex flex-col justify-between gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:flex-row sm:items-center">
            <div>
              <h2 className="font-semibold text-slate-900">
                Course Students
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Enroll a registered student account in this course.
              </p>
            </div>

            <button
              type="button"
              onClick={openAddStudentModal}
              disabled={busy}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <UserPlus className="h-4 w-4" />
              Add Student
            </button>
          </div>

          {/* Search existing student */}
          <form
            onSubmit={searchStudents}
            className="flex max-w-2xl gap-2"
          >
            <label
              className="sr-only"
              htmlFor="student-search"
            >
              Find an existing student
            </label>

            <input
              id="student-search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search student name or ID"
              className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
            />

            <button
              type="submit"
              disabled={busy || !search.trim()}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold disabled:opacity-50"
            >
              <Search className="h-4 w-4" />
              Search
            </button>
          </form>

          {/* Search results */}
          {matches.length > 0 && (
            <form
              onSubmit={enrollStudent}
              className="flex max-w-2xl gap-2"
            >
              <label
                className="sr-only"
                htmlFor="student-result"
              >
                Select a student to enroll
              </label>

              <select
                id="student-result"
                value={selectedStudentId}
                onChange={(event) =>
                  setSelectedStudentId(event.target.value)
                }
                className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
              >
                <option value="">
                  Select student
                </option>

                {matches.map((match) => (
                  <option
                    key={match.student_id}
                    value={match.student_id}
                  >
                    {match.name} · {match.student_id}
                  </option>
                ))}
              </select>

              <button
                type="submit"
                disabled={busy || !selectedStudentId}
                className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                <UserPlus className="h-4 w-4" />
                Enroll
              </button>
            </form>
          )}

          {/* No search results */}
          {search.trim() &&
            !busy &&
            matches.length === 0 && (
              <p className="max-w-2xl rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                No registered student account found. Ask the student to create an account first, then search by their Student ID or name.
              </p>
            )}

          {/* Roster */}
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <div className="grid grid-cols-[1fr_auto_auto] gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase text-slate-500">
              <span>Student</span>
              <span>Enrolled</span>
              <span>Action</span>
            </div>

            {students.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-slate-500">
                No students enrolled in this course yet.
              </p>
            ) : (
              students.map((student) => (
                <div
                  key={student.id}
                  className="grid grid-cols-[1fr_auto_auto] items-center gap-4 border-b border-slate-100 px-4 py-3 text-sm last:border-0"
                >
                  <div>
                    <div className="font-semibold text-slate-900">
                      {student.student_name ||
                        student.student_id}
                    </div>

                    <div className="font-mono text-xs text-slate-500">
                      Student ID: {student.student_id}
                    </div>

                    {student.student_email && (
                      <div className="mt-1 text-xs text-slate-400">
                        {student.student_email}
                      </div>
                    )}
                  </div>

                  <time className="text-xs text-slate-500">
                    {new Date(
                      student.enrollment_date,
                    ).toLocaleDateString()}
                  </time>

                  <button
                    title="Deactivate enrollment"
                    disabled={busy}
                    onClick={() => setEnrollmentRemoveTarget(student)}
                    className="rounded-md p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-700 disabled:opacity-50"
                  >
                    <UserRoundMinus className="h-4 w-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </section>
      ) : activeTab === 'requests' ? (
        <section className="space-y-4">
          <div><h2 className="text-lg font-semibold text-slate-900">Student join requests</h2><p className="mt-1 text-sm text-slate-500">Approve a request to create the student’s active course enrollment, or reject it. Students can request again after a rejection.</p></div>
          {joinRequests.length === 0 ? <p className="rounded-lg border border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-500">No pending requests for this course.</p> : <div className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">{joinRequests.map((joinRequest) => <article key={joinRequest.id} className="flex flex-col justify-between gap-3 p-4 sm:flex-row sm:items-center"><div><p className="font-semibold text-slate-900">{joinRequest.student_name}</p><p className="font-mono text-xs text-slate-500">Student ID: {joinRequest.student_id}</p><p className="mt-1 text-xs text-slate-400">Requested {new Date(joinRequest.requested_at).toLocaleString()}</p></div><div className="flex gap-2"><button disabled={busy} onClick={() => setRequestRejectTarget(joinRequest)} className="rounded-lg border border-rose-200 px-3 py-2 text-xs font-bold text-rose-700 hover:bg-rose-50 disabled:opacity-50">Reject</button><button disabled={busy} onClick={() => void decideJoinRequest(joinRequest, 'approve')} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-white hover:bg-emerald-800 disabled:opacity-50">Approve and enroll</button></div></article>)}</div>}
        </section>
      ) : (
        /* =====================================================
           ASSIGNMENTS TAB
        ===================================================== */
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          {assignments.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-slate-500">
              No assignments for this course yet.
            </p>
          ) : (
            assignments.map((assignment) => (
              <article
                key={assignment.id}
                className="flex flex-col gap-3 border-b border-slate-100 p-4 last:border-0 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <h2 className="font-semibold text-slate-900">
                    {assignment.title}
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    {assignment.problem_titles.join(' · ') ||
                      'No problems attached'}{' '}
                    · {assignment.status}
                  </p>
                </div>

                <div className="text-left text-xs text-slate-600 sm:text-right">
                  <div>
                    {assignment.submitted_count}/
                    {assignment.total_students} submissions
                  </div>

                  <div>
                    {assignment.avg_score == null
                      ? 'No graded submissions yet'
                      : `Average ${assignment.avg_score}%`}
                  </div>
                </div>
              </article>
            ))
          )}
        </section>
      )}

      {/* =====================================================
          EDIT COURSE MODAL
      ===================================================== */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          if (!busy) {
            setIsEditModalOpen(false);
          }
        }}
        title="Edit Course"
        subtitle="Update course details"
      >
        <form
          onSubmit={handleUpdateCourse}
          className="space-y-4 text-xs"
        >
          <div>
            <label className="mb-1 block font-bold text-slate-700">
              Course Code
            </label>

            <input
              type="text"
              value={editCode}
              disabled
              className="w-full cursor-not-allowed rounded-xl border border-slate-200 bg-slate-100 px-3.5 py-2.5 font-mono text-xs focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">
              Course Title
            </label>

            <input
              type="text"
              value={editTitle}
              onChange={(e) =>
                setEditTitle(e.target.value)
              }
              required
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">
              Academic Term
            </label>

            <input
              type="text"
              value={editTerm}
              onChange={(e) =>
                setEditTerm(e.target.value)
              }
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">
              Description
            </label>

            <textarea
              value={editDescription}
              onChange={(e) =>
                setEditDescription(e.target.value)
              }
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs focus:border-emerald-500 focus:outline-none"
              rows={3}
            />
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={() =>
                setIsEditModalOpen(false)
              }
              disabled={busy}
              className="cursor-pointer rounded-xl px-4 py-2 font-bold text-slate-600 hover:bg-slate-100 disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={busy}
              className="cursor-pointer rounded-xl bg-emerald-600 px-5 py-2 font-bold text-white shadow-md shadow-emerald-600/20 transition-all hover:bg-emerald-700 active:scale-95 disabled:opacity-50"
            >
              {busy ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>
      <DoubleConfirmDialog
        isOpen={Boolean(enrollmentRemoveTarget)}
        title="Remove this student from the course?"
        description={`This deactivates ${enrollmentRemoveTarget?.student_name || enrollmentRemoveTarget?.student_id}'s enrollment. Their saved submissions remain in the system.`}
        actionLabel="remove student"
        busy={busy}
        onClose={() => setEnrollmentRemoveTarget(null)}
        onConfirm={async () => { if (!enrollmentRemoveTarget) return; if (await deactivateEnrollment(enrollmentRemoveTarget.id)) setEnrollmentRemoveTarget(null); }}
      />
      <DoubleConfirmDialog
        isOpen={Boolean(requestRejectTarget)}
        title="Reject this join request?"
        description={`The student will be notified that their request for ${requestRejectTarget?.course_code} · ${requestRejectTarget?.course_title} was rejected. They may request again later.`}
        actionLabel="reject request"
        busy={busy}
        onClose={() => setRequestRejectTarget(null)}
        onConfirm={async () => { if (requestRejectTarget) await decideJoinRequest(requestRejectTarget, 'reject'); }}
      />

      {/* =====================================================
          ADD STUDENT MODAL
      ===================================================== */}
      <Modal
        isOpen={isAddStudentModalOpen}
        onClose={closeAddStudentModal}
        title="Add Student"
        subtitle={
          course
            ? `Enroll a registered student account in ${course.course_code}`
            : 'Enroll a registered student account'
        }
      >
        <form
          onSubmit={enrollStudentById}
          className="space-y-4"
        >
          {/* Student ID */}
          <div>
            <label
              htmlFor="new-student-id"
              className="mb-1.5 block text-xs font-bold text-slate-700"
            >
              Student ID
            </label>

            <input
              id="new-student-id"
              type="text"
              value={newStudentId}
              onChange={(e) =>
                setNewStudentId(e.target.value)
              }
              placeholder="e.g. 22BD1A0501"
              disabled={busy}
              autoFocus
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm outline-none transition focus:border-emerald-500 focus:bg-white"
            />

            <p className="mt-1 text-xs text-slate-400">
              Enter the Student ID used to sign in. Only active, registered student accounts can be enrolled.
            </p>
          </div>

          {/* Information */}
          <div className="rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3">
            <p className="text-xs leading-5 text-emerald-800">
              The student must register first. Once enrolled, this course appears in their My Courses section the next time they sign in or refresh it.
            </p>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={closeAddStudentModal}
              disabled={busy}
              className="rounded-xl px-4 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-100 disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={
                busy ||
                !newStudentId.trim()
              }
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-bold text-white shadow-md shadow-emerald-600/20 transition-all hover:bg-emerald-700 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <UserPlus className="h-4 w-4" />

              {busy ? 'Enrolling...' : 'Enroll Student'}
            </button>
          </div>
        </form>
      </Modal>
    </main>
  );
};
