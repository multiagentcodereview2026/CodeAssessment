import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  Search,
  UserPlus,
  UserRoundMinus,
  Download,
  FileSpreadsheet,
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
type CsvEnrollmentResult = { studentId: string; status: 'enrolled' | 'already_enrolled' | 'failed'; message?: string };

const parseStudentIdCsv = (text: string): string[] => {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = '';
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (character === '"') {
      if (quoted && text[index + 1] === '"') {
        cell += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === ',' && !quoted) {
      row.push(cell.trim());
      cell = '';
    } else if ((character === '\n' || character === '\r') && !quoted) {
      if (character === '\r' && text[index + 1] === '\n') index += 1;
      row.push(cell.trim());
      if (row.some(Boolean)) rows.push(row);
      row = [];
      cell = '';
    } else {
      cell += character;
    }
  }

  if (quoted) throw new Error('The CSV contains an unfinished quoted value.');
  row.push(cell.trim());
  if (row.some(Boolean)) rows.push(row);
  if (rows.length < 2) throw new Error('Add a header and at least one student ID to the CSV.');

  const headers = rows[0].map((header) => header.replace(/^\uFEFF/, '').trim().toLowerCase().replace(/[\s-]+/g, '_'));
  const idIndex = headers.findIndex((header) => ['student_id', 'studentid', 'id', 'username'].includes(header));
  if (idIndex < 0) throw new Error('The CSV must include a Student ID column. Download the template for the correct format.');

  const uniqueIds = new Set<string>();
  for (const dataRow of rows.slice(1)) {
    const studentId = (dataRow[idIndex] || '').trim();
    if (studentId) uniqueIds.add(studentId);
  }
  if (!uniqueIds.size) throw new Error('No student IDs were found in the CSV.');
  if (uniqueIds.size > 500) throw new Error('Upload up to 500 unique student IDs at a time.');
  return [...uniqueIds];
};

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
  const [addStudentMode, setAddStudentMode] = useState<'single' | 'csv'>('single');
  const [csvFileName, setCsvFileName] = useState('');
  const [csvStudentIds, setCsvStudentIds] = useState<string[]>([]);
  const [csvResults, setCsvResults] = useState<CsvEnrollmentResult[]>([]);
  const [csvError, setCsvError] = useState('');

  const resetAddStudentForm = () => {
    setNewStudentId('');
    setAddStudentMode('single');
    setCsvFileName('');
    setCsvStudentIds([]);
    setCsvResults([]);
    setCsvError('');
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
    const refresh = () => void loadCourseData();
    const timer = window.setInterval(refresh, 60_000);
    window.addEventListener('focus', refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener('focus', refresh);
    };
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

  const handleCsvFile = async (file?: File) => {
    setCsvResults([]);
    setCsvError('');
    setCsvStudentIds([]);
    setCsvFileName(file?.name || '');
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv') && file.type !== 'text/csv') {
      setCsvError('Choose a .csv file.');
      return;
    }
    try {
      setCsvStudentIds(parseStudentIdCsv(await file.text()));
    } catch (parseError) {
      setCsvError(parseError instanceof Error ? parseError.message : 'The CSV file could not be read.');
    }
  };

  const downloadCsvTemplate = () => {
    const template = new Blob(['student_id\n'], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(template);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'student-enrollment-template.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const enrollStudentsFromCsv = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!courseId || !csvStudentIds.length) return;

    setBusy(true);
    setCsvError('');
    const existingIds = new Set(students.map((student) => student.student_id.trim().toLowerCase()));
    const results: CsvEnrollmentResult[] = [];
    for (const studentId of csvStudentIds) {
      if (existingIds.has(studentId.toLowerCase())) {
        results.push({ studentId, status: 'already_enrolled', message: 'Already enrolled' });
        continue;
      }
      try {
        const response = await authFetch('/api/instructor/enrollments', {
          method: 'POST',
          body: JSON.stringify({ course_id: Number(courseId), student_id: studentId }),
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
          results.push({ studentId, status: 'failed', message: body.detail || 'Could not enroll' });
        } else {
          existingIds.add(studentId.toLowerCase());
          results.push({ studentId, status: 'enrolled' });
        }
      } catch {
        results.push({ studentId, status: 'failed', message: 'Network error' });
      }
      setCsvResults([...results]);
    }
    setCsvResults(results);
    if (results.some((result) => result.status === 'enrolled')) await loadCourseData();
    setBusy(false);
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
        className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Courses
      </Link>

      {/* Course Header */}
      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 dark:border-white/10 pb-5 sm:flex-row sm:items-end">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="text-xs font-extrabold uppercase tracking-[0.14em] text-emerald-600 dark:text-emerald-400">Course Administration</span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-bold text-[11px]">
              {course.course_code} • {course.term || 'No term'}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {course.title}
          </h1>

          {course.description && (
            <p className="mt-2 max-w-2xl text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              {course.description}
            </p>
          )}
        </div>

        <div className="flex gap-2.5">
          <button
            onClick={() => {
              setEditCode(course.course_code);
              setEditTitle(course.title);
              setEditTerm(course.term || '');
              setEditDescription(course.description || '');
              setIsEditModalOpen(true);
            }}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] px-4 py-2.5 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-neutral-800 shadow-xs transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            Edit course
          </button>

          <button
            onClick={() =>
              navigate(
                `/instructor/assignments?courseId=${course.id}`,
              )
            }
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-emerald-500 shadow-md shadow-emerald-600/20 transition-all hover:scale-105 active:scale-95 cursor-pointer ring-1 ring-white/20"
          >
            <BookOpen className="h-4 w-4" />
            Create assignment
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav
        className="flex gap-6 border-b border-slate-200 dark:border-white/10"
        aria-label="Course views"
      >
        <button
          onClick={() => changeTab('students')}
          className={`border-b-2 px-1 pb-3 text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
            activeTab === 'students'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Students ({students.length})
        </button>

        <button
          onClick={() => changeTab('assignments')}
          className={`border-b-2 px-1 pb-3 text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
            activeTab === 'assignments'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Assignments ({assignments.length})
        </button>

        <button
          onClick={() => changeTab('requests')}
          className={`border-b-2 px-1 pb-3 text-xs sm:text-sm font-bold transition-colors cursor-pointer ${activeTab === 'requests' ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400' : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'}`}
        >
          Join Requests ({joinRequests.length})
        </button>

        <button
          onClick={() =>
            navigate(
              `/instructor/analytics?courseId=${course.id}`,
            )
          }
          className="pb-3 text-xs sm:text-sm font-bold text-slate-500 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors cursor-pointer"
        >
          Analytics
        </button>
      </nav>

      {/* Error */}
      {error && (
        <p
          role="alert"
          className="rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50 dark:bg-rose-950/20 px-4 py-3 text-xs font-semibold text-rose-700 dark:text-rose-400"
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
          <div className="flex flex-col justify-between gap-3 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] p-5 shadow-xs sm:flex-row sm:items-center">
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white text-base">
                Course Students
              </h2>

              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Enroll a registered student account in this course.
              </p>
            </div>

            <button
              type="button"
              onClick={openAddStudentModal}
              disabled={busy}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-emerald-600/20 transition-all active:scale-95 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
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
              className="min-w-0 flex-1 rounded-xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#16161d] px-3.5 py-2.5 text-xs text-slate-900 dark:text-white outline-none focus:border-emerald-500 placeholder:text-slate-400"
            />

            <button
              type="submit"
              disabled={busy || !search.trim()}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] px-4 py-2.5 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-neutral-800 disabled:opacity-50 cursor-pointer shadow-xs transition-colors"
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
                className="min-w-0 flex-1 rounded-xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#16161d] px-3.5 py-2.5 text-xs text-slate-900 dark:text-white outline-none focus:border-emerald-500 cursor-pointer"
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
                className="inline-flex items-center gap-2 rounded-xl bg-slate-900 dark:bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50 cursor-pointer transition-colors shadow-xs"
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
              <p className="max-w-2xl rounded-xl border border-slate-200 dark:border-white/12 bg-slate-50 dark:bg-[#121217] px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                No registered student account found. Ask the student to create an account first, then search by their Student ID or name.
              </p>
            )}

          {/* Roster */}
          <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] shadow-xs">
            <div className="grid grid-cols-[1fr_auto_auto] gap-4 border-b border-slate-200 dark:border-white/10 bg-slate-50/80 dark:bg-[#16161d] px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              <span>Student</span>
              <span>Enrolled</span>
              <span>Action</span>
            </div>

            {students.length === 0 ? (
              <p className="px-4 py-8 text-center text-xs text-slate-500 dark:text-slate-400">
                No students enrolled in this course yet.
              </p>
            ) : (
              students.map((student) => (
                <div
                  key={student.id}
                  className="grid grid-cols-[1fr_auto_auto] items-center gap-4 border-b border-slate-100 dark:border-white/5 px-4 py-3 text-xs last:border-0 hover:bg-slate-50/50 dark:hover:bg-white/[0.02] transition-colors"
                >
                  <div>
                    <div className="font-bold text-slate-900 dark:text-white">
                      {student.student_name ||
                        student.student_id}
                    </div>

                    <div className="font-mono text-[11px] text-slate-400">
                      Student ID: {student.student_id}
                    </div>

                    {student.student_email && (
                      <div className="mt-0.5 text-[11px] text-slate-400">
                        {student.student_email}
                      </div>
                    )}
                  </div>

                  <time className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                    {new Date(
                      student.enrollment_date,
                    ).toLocaleDateString()}
                  </time>

                  <button
                    title="Deactivate enrollment"
                    disabled={busy}
                    onClick={() => setEnrollmentRemoveTarget(student)}
                    className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 hover:text-rose-600 dark:hover:text-rose-400 disabled:opacity-50 cursor-pointer transition-colors"
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
          <div><h2 className="text-base font-bold text-slate-900 dark:text-white">Student join requests</h2><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Approve a request to create the student’s active course enrollment, or reject it. Students can request again after a rejection.</p></div>
          {joinRequests.length === 0 ? <p className="rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] px-4 py-10 text-center text-xs text-slate-500 dark:text-slate-400">No pending requests for this course.</p> : <div className="divide-y divide-slate-200 dark:divide-white/5 rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] overflow-hidden">{joinRequests.map((joinRequest) => <article key={joinRequest.id} className="flex flex-col justify-between gap-3 p-4 sm:flex-row sm:items-center"><div><p className="font-bold text-slate-900 dark:text-white">{joinRequest.student_name}</p><p className="font-mono text-xs text-slate-400">Student ID: {joinRequest.student_id}</p><p className="mt-1 text-xs text-slate-400">Requested {new Date(joinRequest.requested_at).toLocaleString()}</p></div><div className="flex gap-2"><button disabled={busy} onClick={() => setRequestRejectTarget(joinRequest)} className="rounded-xl border border-rose-200 dark:border-rose-900/40 px-3 py-2 text-xs font-bold text-rose-700 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 disabled:opacity-50 cursor-pointer transition-colors">Reject</button><button disabled={busy} onClick={() => void decideJoinRequest(joinRequest, 'approve')} className="rounded-xl bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-xs font-bold text-white shadow-sm disabled:opacity-50 cursor-pointer transition-colors">Approve and enroll</button></div></article>)}</div>}
        </section>
      ) : (
        /* =====================================================
           ASSIGNMENTS TAB
        ===================================================== */
        <section className="overflow-hidden rounded-2xl border border-slate-200 dark:border-white/12 bg-white dark:bg-[#121217] shadow-xs">
          {assignments.length === 0 ? (
            <p className="px-4 py-8 text-center text-xs text-slate-500 dark:text-slate-400">
              No assignments for this course yet.
            </p>
          ) : (
            assignments.map((assignment) => (
              <article
                key={assignment.id}
                className="flex flex-col gap-3 border-b border-slate-100 dark:border-white/5 p-4 last:border-0 hover:bg-slate-50/50 dark:hover:bg-white/[0.02] transition-colors sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <h2 className="font-bold text-slate-900 dark:text-white text-sm">
                    {assignment.title}
                  </h2>

                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {assignment.problem_titles.join(' · ') ||
                      'No problems attached'}{' '}
                    · {assignment.status}
                  </p>
                </div>

                <div className="text-left text-xs text-slate-600 dark:text-slate-400 sm:text-right font-mono">
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
            <label className="mb-1 block font-bold text-slate-700 dark:text-zinc-300">
              Course Code
            </label>

            <input
              type="text"
              value={editCode}
              disabled
              className="w-full cursor-not-allowed rounded-xl border border-slate-200 dark:border-white/10 bg-slate-100 dark:bg-[#16161d] text-slate-500 dark:text-zinc-400 px-3.5 py-2.5 font-mono text-xs focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700 dark:text-zinc-300">
              Course Title
            </label>

            <input
              type="text"
              value={editTitle}
              onChange={(e) =>
                setEditTitle(e.target.value)
              }
              required
              className="w-full rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 px-3.5 py-2.5 text-xs focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700 dark:text-zinc-300">
              Academic Term
            </label>

            <input
              type="text"
              value={editTerm}
              onChange={(e) =>
                setEditTerm(e.target.value)
              }
              className="w-full rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 px-3.5 py-2.5 text-xs focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700 dark:text-zinc-300">
              Description
            </label>

            <textarea
              value={editDescription}
              onChange={(e) =>
                setEditDescription(e.target.value)
              }
              className="w-full rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-[#16161d] text-slate-900 dark:text-zinc-100 placeholder:text-slate-400 dark:placeholder:text-zinc-500 px-3.5 py-2.5 text-xs focus:border-emerald-500 focus:outline-none"
              rows={3}
            />
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-slate-100 dark:border-white/10 pt-4">
            <button
              type="button"
              onClick={() =>
                setIsEditModalOpen(false)
              }
              disabled={busy}
              className="cursor-pointer rounded-xl px-4 py-2 font-bold text-slate-600 dark:text-zinc-400 hover:bg-slate-100 dark:hover:bg-white/10 disabled:opacity-50"
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
        <div className="space-y-4">
          <div className="grid grid-cols-2 rounded-xl bg-slate-100 p-1 dark:bg-white/5" role="tablist" aria-label="Add students">
            <button type="button" role="tab" aria-selected={addStudentMode === 'single'} onClick={() => setAddStudentMode('single')} disabled={busy} className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${addStudentMode === 'single' ? 'bg-white text-slate-900 shadow-sm dark:bg-white/10 dark:text-white' : 'text-slate-500 dark:text-zinc-400'}`}>
              Add one student
            </button>
            <button type="button" role="tab" aria-selected={addStudentMode === 'csv'} onClick={() => setAddStudentMode('csv')} disabled={busy} className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${addStudentMode === 'csv' ? 'bg-white text-slate-900 shadow-sm dark:bg-white/10 dark:text-white' : 'text-slate-500 dark:text-zinc-400'}`}>
              Upload CSV
            </button>
          </div>

          {addStudentMode === 'single' ? (
            <form onSubmit={enrollStudentById} className="space-y-4">
              <div>
                <label htmlFor="new-student-id" className="mb-1.5 block text-xs font-bold text-slate-700 dark:text-zinc-300">Student ID</label>
                <input id="new-student-id" type="text" value={newStudentId} onChange={(event) => setNewStudentId(event.target.value)} placeholder="e.g. 22BD1A0501" disabled={busy} autoFocus className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-500 focus:bg-white dark:border-white/10 dark:bg-[#16161d] dark:text-zinc-100 dark:placeholder:text-zinc-500" />
                <p className="mt-1 text-xs text-slate-400 dark:text-zinc-500">Enter the Student ID used to sign in. Only active, registered student accounts can be enrolled.</p>
              </div>
              <div className="rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 dark:border-emerald-500/20 dark:bg-emerald-950/20">
                <p className="text-xs leading-5 text-emerald-800 dark:text-emerald-300">The student must register first. Once enrolled, this course appears in their My Courses section the next time they sign in or refresh it.</p>
              </div>
              <div className="flex items-center justify-end gap-3 border-t border-slate-100 pt-4 dark:border-white/10">
                <button type="button" onClick={closeAddStudentModal} disabled={busy} className="cursor-pointer rounded-xl px-4 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-100 disabled:opacity-50 dark:text-zinc-400 dark:hover:bg-white/10">Cancel</button>
                <button type="submit" disabled={busy || !newStudentId.trim()} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-bold text-white shadow-md shadow-emerald-600/20 transition-all hover:bg-emerald-700 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50">
                  <UserPlus className="h-4 w-4" />{busy ? 'Enrolling...' : 'Enroll Student'}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={enrollStudentsFromCsv} className="space-y-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/[0.03]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-800 dark:text-zinc-100">Upload your class list</p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-zinc-400">Add one ID per row under <code>student_id</code>. Students need active registered accounts.</p>
                  </div>
                  <button type="button" onClick={downloadCsvTemplate} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-white/10 dark:bg-white/5 dark:text-zinc-200 dark:hover:bg-white/10">
                    <Download className="h-4 w-4" />Download template
                  </button>
                </div>
                <label htmlFor="student-csv" className="mt-4 flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed border-slate-300 bg-white px-4 py-6 text-center hover:border-emerald-500 dark:border-white/15 dark:bg-[#16161d]">
                  <FileSpreadsheet className="mb-2 h-5 w-5 text-emerald-600" />
                  <span className="text-sm font-semibold text-slate-700 dark:text-zinc-200">{csvFileName || 'Choose a CSV file'}</span>
                  <span className="mt-1 text-xs text-slate-400">Up to 500 unique student IDs</span>
                  <input id="student-csv" type="file" accept=".csv,text/csv" disabled={busy} className="sr-only" onChange={(event) => void handleCsvFile(event.target.files?.[0])} />
                </label>
              </div>

              {csvError && <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:bg-rose-950/30 dark:text-rose-300">{csvError}</p>}
              {csvStudentIds.length > 0 && csvResults.length === 0 && <p className="text-sm text-slate-600 dark:text-zinc-300">Ready to enroll <strong>{csvStudentIds.length}</strong> student{csvStudentIds.length === 1 ? '' : 's'} from this file.</p>}

              {csvResults.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-800 dark:text-zinc-100">
                    {csvResults.filter((result) => result.status === 'enrolled').length} enrolled · {csvResults.filter((result) => result.status === 'already_enrolled').length} already enrolled · {csvResults.filter((result) => result.status === 'failed').length} failed
                  </p>
                  <ul className="max-h-44 space-y-1 overflow-y-auto rounded-lg border border-slate-200 p-2 text-xs dark:border-white/10">
                    {csvResults.map((result) => <li key={result.studentId} className="flex justify-between gap-3 py-1"><span className="font-mono text-slate-700 dark:text-zinc-200">{result.studentId}</span><span className={result.status === 'failed' ? 'text-rose-600 dark:text-rose-300' : result.status === 'enrolled' ? 'text-emerald-700 dark:text-emerald-300' : 'text-slate-500'}>{result.message || (result.status === 'enrolled' ? 'Enrolled' : 'Already enrolled')}</span></li>)}
                  </ul>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 border-t border-slate-100 pt-4 dark:border-white/10">
                <button type="button" onClick={closeAddStudentModal} disabled={busy} className="cursor-pointer rounded-xl px-4 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-100 disabled:opacity-50 dark:text-zinc-400 dark:hover:bg-white/10">{csvResults.length ? 'Done' : 'Cancel'}</button>
                <button type="submit" disabled={busy || !csvStudentIds.length || csvResults.length > 0} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-bold text-white shadow-md shadow-emerald-600/20 transition-all hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50">
                  <FileSpreadsheet className="h-4 w-4" />{busy ? 'Enrolling students...' : 'Enroll all students'}
                </button>
              </div>
            </form>
          )}
        </div>
      </Modal>
    </main>
  );
};
