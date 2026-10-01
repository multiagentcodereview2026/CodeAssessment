import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, Search, UserPlus, UserRoundMinus } from 'lucide-react';
import { useAuth } from '../../context/useAuth';
import { Modal } from '../common/Modal';

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

type StudentHit = { student_id: string; name: string };

type Tab = 'students' | 'assignments';

export const CourseDetailsView: React.FC = () => {
  const { courseId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { authFetch } = useAuth();
  const [course, setCourse] = useState<Course | null>(null);
  const [students, setStudents] = useState<Enrollment[]>([]);
  const [assignments, setAssignments] = useState<CourseAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [matches, setMatches] = useState<StudentHit[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [busy, setBusy] = useState(false);
  const activeTab: Tab = searchParams.get('tab') === 'assignments' ? 'assignments' : 'students';
  
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editCode, setEditCode] = useState('');
  const [editTitle, setEditTitle] = useState('');
  const [editTerm, setEditTerm] = useState('');
  const [editDescription, setEditDescription] = useState('');

  const handleUpdateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editTitle.trim() || !courseId) return;
    setBusy(true);
    setError('');
    try {
      const response = await authFetch(`/api/instructor/courses/${courseId}`, {
        method: 'PATCH',
        body: JSON.stringify({
          title: editTitle.trim(),
          term: editTerm.trim() || null,
          description: editDescription.trim() || null
        })
      });
      if (!response.ok) throw new Error('Failed to update course.');
      setIsEditModalOpen(false);
      await loadCourseData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update course.');
    } finally {
      setBusy(false);
    }
  };

  const loadCourseData = useCallback(async () => {
    if (!courseId) return;
    setError('');
    try {
      const [courseResponse, rosterResponse, assignmentResponse] = await Promise.all([
        authFetch(`/api/instructor/courses/${courseId}`, { cache: 'no-store' }),
        authFetch(`/api/instructor/courses/${courseId}/students`, { cache: 'no-store' }),
        authFetch(`/api/instructor/courses/${courseId}/assignments`, { cache: 'no-store' })
      ]);
      if (!courseResponse.ok) throw new Error('Course could not be loaded.');
      if (!rosterResponse.ok || !assignmentResponse.ok) throw new Error('Course details could not be loaded.');
      const [courseData, rosterData, assignmentData] = await Promise.all([
        courseResponse.json(),
        rosterResponse.json(),
        assignmentResponse.json()
      ]);
      setCourse(courseData);
      setStudents(Array.isArray(rosterData) ? rosterData : []);
      setAssignments(Array.isArray(assignmentData) ? assignmentData : []);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Course details could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, [authFetch, courseId]);

  useEffect(() => {
    void loadCourseData();
  }, [loadCourseData]);

  const searchStudents = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!search.trim()) return;
    setBusy(true);
    setError('');
    try {
      const response = await authFetch(`/api/instructor/students?query=${encodeURIComponent(search.trim())}`);
      if (!response.ok) throw new Error('Student search failed.');
      const data = await response.json();
      setMatches(Array.isArray(data) ? data : []);
      setSelectedStudentId('');
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : 'Student search failed.');
    } finally {
      setBusy(false);
    }
  };

  const enrollStudent = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!courseId || !selectedStudentId) return;
    setBusy(true);
    setError('');
    try {
      const response = await authFetch('/api/instructor/enrollments', {
        method: 'POST',
        body: JSON.stringify({ course_id: Number(courseId), student_id: selectedStudentId })
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || 'Enrollment could not be saved.');
      }
      setSearch('');
      setMatches([]);
      setSelectedStudentId('');
      await loadCourseData();
    } catch (enrollError) {
      setError(enrollError instanceof Error ? enrollError.message : 'Enrollment could not be saved.');
    } finally {
      setBusy(false);
    }
  };

  const deactivateEnrollment = async (enrollmentId: number) => {
    setBusy(true);
    setError('');
    try {
      const response = await authFetch(`/api/instructor/enrollments/${enrollmentId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Enrollment could not be deactivated.');
      await loadCourseData();
    } catch (removeError) {
      setError(removeError instanceof Error ? removeError.message : 'Enrollment could not be deactivated.');
    } finally {
      setBusy(false);
    }
  };

  const changeTab = (tab: Tab) => setSearchParams({ tab });

  if (loading) return <div className="p-8 text-sm text-slate-500">Loading course…</div>;
  if (!course) {
    return <section className="space-y-4 p-8">
      <p className="text-sm text-rose-700">{error || 'Course not found.'}</p>
      <Link to="/instructor/courses" className="text-sm font-semibold text-emerald-700">Back to courses</Link>
    </section>;
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 pb-12">
      <Link to="/instructor/courses" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-emerald-700">
        <ArrowLeft className="h-4 w-4" /> Courses
      </Link>

      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="font-mono text-xs font-bold text-emerald-700">{course.course_code} · {course.term || 'No term'}</p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{course.title}</h1>
          {course.description && <p className="mt-2 max-w-2xl text-sm text-slate-600">{course.description}</p>}
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
            onClick={() => navigate(`/instructor/assignments?courseId=${course.id}`)}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600"
          >
            <BookOpen className="h-4 w-4" /> Create assignment
          </button>
        </div>
      </header>

      <nav className="flex gap-5 border-b border-slate-200" aria-label="Course views">
        <button onClick={() => changeTab('students')} className={`border-b-2 px-1 pb-3 text-sm font-semibold ${activeTab === 'students' ? 'border-emerald-700 text-emerald-800' : 'border-transparent text-slate-500'}`}>
          Students ({students.length})
        </button>
        <button onClick={() => changeTab('assignments')} className={`border-b-2 px-1 pb-3 text-sm font-semibold ${activeTab === 'assignments' ? 'border-emerald-700 text-emerald-800' : 'border-transparent text-slate-500'}`}>
          Assignments ({assignments.length})
        </button>
        <button onClick={() => navigate(`/instructor/analytics?courseId=${course.id}`)} className="pb-3 text-sm font-semibold text-slate-500 hover:text-emerald-800">
          Analytics
        </button>
      </nav>

      {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>}

      {activeTab === 'students' ? (
        <section className="space-y-5">
          <form onSubmit={searchStudents} className="flex max-w-2xl gap-2">
            <label className="sr-only" htmlFor="student-search">Find an existing student</label>
            <input id="student-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search student name or ID" className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm" />
            <button disabled={busy || !search.trim()} className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold disabled:opacity-50">
              <Search className="h-4 w-4" /> Search
            </button>
          </form>

          {matches.length > 0 && (
            <form onSubmit={enrollStudent} className="flex max-w-2xl gap-2">
              <label className="sr-only" htmlFor="student-result">Select a student to enroll</label>
              <select id="student-result" value={selectedStudentId} onChange={(event) => setSelectedStudentId(event.target.value)} className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm">
                <option value="">Select student</option>
                {matches.map((match) => <option key={match.student_id} value={match.student_id}>{match.name} · {match.student_id}</option>)}
              </select>
              <button disabled={busy || !selectedStudentId} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
                <UserPlus className="h-4 w-4" /> Enroll
              </button>
            </form>
          )}

          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <div className="grid grid-cols-[1fr_auto_auto] gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase text-slate-500">
              <span>Student</span><span>Enrolled</span><span>Action</span>
            </div>
            {students.length === 0 ? <p className="px-4 py-8 text-center text-sm text-slate-500">No students enrolled in this course yet.</p> : students.map((student) => (
              <div key={student.id} className="grid grid-cols-[1fr_auto_auto] items-center gap-4 border-b border-slate-100 px-4 py-3 text-sm last:border-0">
                <div><div className="font-semibold text-slate-900">{student.student_name || student.student_id}</div><div className="font-mono text-xs text-slate-500">{student.student_id}</div></div>
                <time className="text-xs text-slate-500">{new Date(student.enrollment_date).toLocaleDateString()}</time>
                <button title="Deactivate enrollment" disabled={busy} onClick={() => void deactivateEnrollment(student.id)} className="rounded-md p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-700 disabled:opacity-50"><UserRoundMinus className="h-4 w-4" /></button>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          {assignments.length === 0 ? <p className="px-4 py-8 text-center text-sm text-slate-500">No assignments for this course yet.</p> : assignments.map((assignment) => (
            <article key={assignment.id} className="flex flex-col gap-3 border-b border-slate-100 p-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
              <div><h2 className="font-semibold text-slate-900">{assignment.title}</h2><p className="mt-1 text-xs text-slate-500">{assignment.problem_titles.join(' · ') || 'No problems attached'} · {assignment.status}</p></div>
              <div className="text-left text-xs text-slate-600 sm:text-right"><div>{assignment.submitted_count}/{assignment.total_students} submissions</div><div>{assignment.avg_score == null ? 'No graded submissions yet' : `Average ${assignment.avg_score}%`}</div></div>
            </article>
          ))}
        </section>
      )}

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Course"
        subtitle="Update course details"
      >
        <form onSubmit={handleUpdateCourse} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Course Code</label>
            <input
              type="text"
              value={editCode}
              disabled
              className="w-full px-3.5 py-2.5 bg-slate-100 border border-slate-200 rounded-xl focus:outline-none font-mono text-xs cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Course Title</label>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 text-xs"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Academic Term</label>
            <input
              type="text"
              value={editTerm}
              onChange={(e) => setEditTerm(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 text-xs"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Description</label>
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 text-xs"
              rows={3}
            />
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(false)}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-95 cursor-pointer disabled:opacity-50"
            >
              Save Changes
            </button>
          </div>
        </form>
      </Modal>
    </main>
  );
};
