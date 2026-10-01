import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  UserProfile,
  Role,
  Problem,
  AssessmentResult,
  SubmissionItem,
  StudentProgress,
  StudentRosterItem,
  Assignment,
  SimilarityAlert,
  ReportItem,
  CourseItem,
  AnnouncementItem
} from '../types';
import {
  MOCK_STUDENT_USER,
  MOCK_PROBLEMS,
  MOCK_DEFAULT_ASSESSMENT,
} from '../mock/data';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { useAuth } from './useAuth';

// Bump this whenever the server-side practice corpus changes. Problem metadata
// may be invalidated, but editor drafts must remain independent of catalogue
// updates so a student's work is never erased by a frontend deployment.
const PROBLEM_BANK_VERSION = 'newfacade-stdio-v2-empty-editors';

interface ToastInfo {
  id: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
}

const EMPTY_INSTRUCTOR_STATS = {
  totalStudents: 0,
  activeAssignments: 0,
  totalSubmissions: 0,
  classAvg: '0%',
  averageScore: null as number | null,
  highestScore: null as number | null,
  lowestScore: null as number | null,
  scoreDistribution: [] as Array<{ range: string; count: number; heightPercent: number }>,
  students: [] as Array<{ id: string; name: string; subs: number; avg: string; status: string }>,
};

const EMPTY_STUDENT_PROGRESS: StudentProgress = {
  overallScore: null,
  problemsSolved: 0,
  totalProblems: 0,
  currentStreak: 0,
  rankPercentile: 'N/A',
  progressPercent: 0,
  topicsCovered: 0,
  totalTopics: 0,
  hoursSpent: 'N/A',
  weakTopics: [],
  categoryWiseScores: [],
  scoreTrend: [],
};

interface AppContextType {
  currentUser: UserProfile;
  updateCurrentUser: (profile: Partial<UserProfile>) => void;
  currentRole: Role;
  currentView: string;
  setCurrentView: (view: string) => void;
  problems: Problem[];
  addProblem: (problem: Problem) => void;
  updateProblem: (problem: Problem) => void;
  deleteProblem: (id: string) => void;
  selectedProblemId: string;
  setSelectedProblemId: (id: string) => void;
  selectedProblem: Problem;
  activeAssessment: AssessmentResult;
  setActiveAssessment: (result: AssessmentResult) => void;
  submissions: SubmissionItem[];
  addSubmission: (submission: SubmissionItem, assessment: AssessmentResult) => void;
  studentProgress: StudentProgress;
  courses: CourseItem[];
  addCourse: (course: CourseItem) => void;
  deleteCourse: (id: string) => void;
  studentRoster: StudentRosterItem[];
  selectedStudent: StudentRosterItem | null;
  setSelectedStudent: (student: StudentRosterItem | null) => void;
  addStudent: (student: StudentRosterItem) => void;
  deleteStudent: (id: string) => void;
  assignments: Assignment[];
  addAssignment: (assignment: Assignment) => void;
  deleteAssignment: (id: string) => void;
  similarityAlerts: SimilarityAlert[];
  dismissSimilarityAlert: (id: string) => void;
  reports: ReportItem[];
  generateReport: (report: ReportItem) => void;
  instructorStats: typeof EMPTY_INSTRUCTOR_STATS;
  announcements: AnnouncementItem[];
  dismissAnnouncement: (id: string) => void;
  openProblemWorkspace: (problemId: string) => void;
  openAssessmentResult: (submissionId?: string) => void;
  showToast: (message: string, type?: 'success' | 'info' | 'warning' | 'error') => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const auth = useAuth();
  const [currentRole, setCurrentRole] = useState<Role>('student');
  const [currentUser, setCurrentUser] = useState<UserProfile>(MOCK_STUDENT_USER);
  const [currentView, setCurrentView] = useState<string>('dashboard');

  // Shared persistent problems state
  const [problems, setProblems] = useState<Problem[]>(() => {
    try {
      if (localStorage.getItem('codevedha_problem_bank_version') !== PROBLEM_BANK_VERSION) {
        localStorage.removeItem('codevedha_problems');
        localStorage.setItem('codevedha_problem_bank_version', PROBLEM_BANK_VERSION);
      }
      const saved = localStorage.getItem('codevedha_problems');
      if (saved) return JSON.parse(saved);
    } catch {}
    return MOCK_PROBLEMS;
  });

  const [selectedProblemId, setSelectedProblemId] = useState<string>('prob-1');
  const [activeAssessment, setActiveAssessment] = useState<AssessmentResult>(MOCK_DEFAULT_ASSESSMENT);
  const [submissions, setSubmissions] = useState<SubmissionItem[]>([]);
  const [studentProgress, setStudentProgress] = useState<StudentProgress>(EMPTY_STUDENT_PROGRESS);
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [studentRoster, setStudentRoster] = useState<StudentRosterItem[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<StudentRosterItem | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [similarityAlerts, setSimilarityAlerts] = useState<SimilarityAlert[]>([]);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [instructorStats, setInstructorStats] = useState(EMPTY_INSTRUCTOR_STATS);
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);
  const [toasts, setToasts] = useState<ToastInfo[]>([]);

  useEffect(() => {
    if (!auth?.user) {
      setCourses([]);
      setAssignments([]);
      setStudentRoster([]);
      setSubmissions([]);
      setInstructorStats(EMPTY_INSTRUCTOR_STATS);
      return;
    }

    const role: Role = auth.user.role === 'instructor' ? 'instructor' : 'student';
    const profileBase = MOCK_STUDENT_USER;

    setCurrentRole(role);
    setCurrentUser({
      ...profileBase,
      id: auth.user.id || profileBase.id,
      name: auth.user.name || auth.user.username || profileBase.name,
      email: auth.user.email || profileBase.email,
      role,
      avatar: profileBase.avatar,
      rollNumber: profileBase.rollNumber,
      institution: profileBase.institution,
      department: role === 'instructor' ? 'Computer Science' : profileBase.department,
      year: profileBase.year
    });
    if (role === 'instructor') {
      let cancelled = false;
      const loadInstructorOverview = async () => {
        try {
          const response = await auth.authFetch('/api/instructor/overview', { cache: 'no-store' });
          if (!response.ok) throw new Error('Instructor overview unavailable');
          const overview = await response.json();
          if (cancelled) return;
          const parsedAverageScore = overview.class_avg_score == null
            ? null
            : Number.parseFloat(String(overview.class_avg_score).replace(/%/g, ''));
          const averageScoreValue = Number.isFinite(parsedAverageScore) ? parsedAverageScore : null;

          setInstructorStats({
            totalStudents: Number(overview.total_students ?? 0),
            activeAssignments: Number(overview.active_assignments ?? 0),
            totalSubmissions: Number(overview.total_submissions ?? 0),
            classAvg: overview.class_avg_score ?? 'N/A',
            averageScore: averageScoreValue,
            highestScore: overview.highest_score == null ? null : Number(overview.highest_score),
            lowestScore: overview.lowest_score == null ? null : Number(overview.lowest_score),
            scoreDistribution: Array.isArray(overview.score_distribution) ? overview.score_distribution : [],
            students: Array.isArray(overview.students) ? overview.students : []
          });

          const courseResponse = await auth.authFetch('/api/instructor/courses', { cache: 'no-store' });
          if (courseResponse.ok) {
            const courseData = await courseResponse.json();
            if (!cancelled && Array.isArray(courseData)) {
              const mappedCourses = courseData.map((course: any) => ({
                id: String(course.id),
                code: course.course_code,
                title: course.title,
                term: course.term || 'N/A',
                studentsCount: Number(course.student_count ?? 0),
                activeAssignments: Number(course.assignment_count ?? 0),
                avgGrade: course.avg_score != null ? `${course.avg_score}%` : 'N/A'
              }));
              setCourses(mappedCourses);
            }
          }

          const assignmentResponse = await auth.authFetch('/api/instructor/assignments', { cache: 'no-store' });
          if (assignmentResponse.ok) {
            const assignmentData = await assignmentResponse.json();
            if (!cancelled && Array.isArray(assignmentData)) {
              const courseMap = new Map<string, string>();
              const currentCourses = await auth.authFetch('/api/instructor/courses', { cache: 'no-store' }).then(res => res.ok ? res.json() : []);
              if (Array.isArray(currentCourses)) {
                currentCourses.forEach((course: any) => {
                  courseMap.set(String(course.id), String(course.title));
                });
              }

              setAssignments(assignmentData.map((assignment: any) => ({
                id: String(assignment.id),
                title: assignment.title,
                description: assignment.description || 'No description provided.',
                course: courseMap.get(String(assignment.course_id)) || `Course ${assignment.course_id}`,
                problemsCount: Array.isArray(assignment.problems) ? assignment.problems.length : 0,
                problemIds: Array.isArray(assignment.problems) ? assignment.problems : [],
                submittedCount: Number(assignment.submitted_count ?? 0),
                totalCount: Number(assignment.total_students ?? 0),
                avgScore: assignment.avg_score == null ? null : Number(assignment.avg_score),
                dueDate: assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'No due date',
                status: assignment.status === 'ACTIVE' ? 'Active' : assignment.status === 'UPCOMING' ? 'Upcoming' : 'Closed'
              })));
            }
          }
        } catch (error) {
          console.error('Unable to load instructor overview:', error);
          if (!cancelled) {
            setInstructorStats(EMPTY_INSTRUCTOR_STATS);
            setCourses([]);
            setAssignments([]);
          }
        }
      };

      void loadInstructorOverview();
      return () => { cancelled = true; };
    }
  }, [auth?.user, auth?.authFetch]);

  // Submission history, accepted ticks, and attempted markers come from
  // PostgreSQL—not mock state—so they survive a browser reload and restart.
  useEffect(() => {
    let cancelled = false;

    if (!auth?.user || auth.user.role !== 'student') {
      setSubmissions([]);
      return () => { cancelled = true; };
    }

    const loadSavedSubmissions = async () => {
      try {
        const response = await auth.authFetch('/api/submissions', { cache: 'no-store' });
        if (!response.ok) throw new Error('Could not load saved submissions.');
        const records = await response.json();
        if (!Array.isArray(records) || cancelled) return;

        const problemIds = [...new Set(records.map((record: any) => record.problem_id).filter(Boolean))];
        const titles = new Map<string, string>();
        await Promise.all(problemIds.map(async (problemId: string) => {
          try {
            const problemResponse = await auth.authFetch(`/api/problems/${encodeURIComponent(problemId)}`, { cache: 'no-store' });
            if (problemResponse.ok) {
              const problem = await problemResponse.json();
              titles.set(problemId, problem.title || problemId);
            }
          } catch {
            // The record remains usable even if a historical problem was removed.
          }
        }));

        if (cancelled) return;
        setSubmissions(records.map((record: any): SubmissionItem => {
          const execution = record.execution_result || {};
          const passed = Number(execution.passed_cases || 0);
          const total = Number(execution.total_cases || (passed + Number(execution.failed_cases || 0)));
          const passedAll = total > 0 && passed === total;
          return {
            id: record.submission_id,
            problemId: record.problem_id,
            problemSlug: record.problem_id,
            problemTitle: titles.get(record.problem_id) || record.problem_id,
            score: Math.round(Number(record.overall_score || 0)),
            status: passedAll ? 'Passed' : passed > 0 ? 'Partial' : 'Failed',
            language: record.language || '—',
            date: record.created_at ? new Date(record.created_at).toLocaleString() : 'Saved submission',
            executionTime: `${execution.runtime_ms || 0} ms`,
            passedTestCases: passed,
            totalTestCases: total
          };
        }));
      } catch (error) {
        console.error('Unable to restore submission history:', error);
      }
    };

    void loadSavedSubmissions();
    return () => { cancelled = true; };
  }, [auth?.user, auth?.authFetch]);

  useEffect(() => {
    let cancelled = false;
    if (!auth?.user || auth.user.role !== 'student') {
      setStudentProgress(EMPTY_STUDENT_PROGRESS);
      return () => { cancelled = true; };
    }

    const loadStudentAnalytics = async () => {
      try {
        const response = await auth.authFetch(`/api/analytics/student/${encodeURIComponent(auth.user.id)}`, { cache: 'no-store' });
        if (!response.ok) throw new Error('Student analytics unavailable');
        const analytics = await response.json();
        if (cancelled) return;
        const categories = Array.isArray(analytics.category_breakdown)
          ? analytics.category_breakdown.filter((item: any) => item.value != null).map((item: any) => ({
              name: String(item.name),
              percentage: Number(item.value),
              color: String(item.color || '#64748b'),
              scoreDisplay: `${Number(item.value)}%`
            }))
          : [];
        const totalProblems = Number(analytics.total_problems ?? 0);
        const problemsSolved = Number(analytics.problems_solved ?? 0);
        setStudentProgress({
          overallScore: analytics.overall_score == null ? null : Number(analytics.overall_score),
          problemsSolved,
          totalProblems,
          currentStreak: Number(analytics.streak_days ?? 0),
          rankPercentile: 'N/A',
          progressPercent: totalProblems > 0 ? Math.round(problemsSolved / totalProblems * 100) : 0,
          topicsCovered: categories.length,
          totalTopics: categories.length,
          hoursSpent: 'N/A',
          weakTopics: Array.isArray(analytics.weak_topics) ? analytics.weak_topics : [],
          categoryWiseScores: categories,
          scoreTrend: Array.isArray(analytics.score_trend)
            ? analytics.score_trend.map((point: any) => ({ date: String(point.date), score: Number(point.score) }))
            : [],
        });
      } catch (error) {
        console.error('Unable to load student analytics:', error);
        if (!cancelled) setStudentProgress(EMPTY_STUDENT_PROGRESS);
      }
    };

    void loadStudentAnalytics();
    return () => { cancelled = true; };
  }, [auth?.user?.id, auth?.user?.role, auth?.authFetch, submissions.length]);

  // Sync problems to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem('codevedha_problems', JSON.stringify(problems));
    } catch {}
  }, [problems]);

  const showToast = (message: string, type: 'success' | 'info' | 'warning' | 'error' = 'success') => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const updateCurrentUser = (updates: Partial<UserProfile>) => {
    setCurrentUser(prev => ({ ...prev, ...updates }));
    showToast('Profile updated successfully!', 'success');
  };

  const addProblem = (newProb: Problem) => {
    setProblems(prev => [newProb, ...prev]);
    setAnnouncements(prev => [
      {
        id: `ann-${Date.now()}`,
        title: 'New question posted',
        message: `${newProb.title} has been posted${newProb.courseCode ? ` for ${newProb.courseCode}` : ''}.`,
        problemId: newProb.id,
        courseCode: newProb.courseCode,
        dueDate: newProb.dueDate,
        createdAt: 'Just now',
        read: false
      },
      ...prev
    ]);
    showToast(`Question "${newProb.title}" published to Problem Bank!`, 'success');
  };

  const dismissAnnouncement = (id: string) => {
    setAnnouncements(prev => prev.map(item => (
      item.id === id ? { ...item, read: true } : item
    )));
  };

  const updateProblem = (updatedProb: Problem) => {
    setProblems(prev => prev.map(p => (p.id === updatedProb.id ? updatedProb : p)));
    showToast(`Question "${updatedProb.title}" updated successfully!`, 'success');
  };

  const deleteProblem = (id: string) => {
    setProblems(prev => prev.filter(p => p.id !== id));
    showToast('Question removed from Problem Bank', 'info');
  };

  const selectedProblem = problems.find(p => p.id === selectedProblemId) || problems[0] || MOCK_PROBLEMS[0];

  const openProblemWorkspace = (problemId: string) => {
    setSelectedProblemId(problemId);
    setCurrentView('workspace');
  };

  const openAssessmentResult = (_submissionId?: string) => {
    setCurrentView('result');
  };

  const addSubmission = (newSub: SubmissionItem, newAssessment: AssessmentResult) => {
    setSubmissions(prev => [newSub, ...prev]);
    setActiveAssessment(newAssessment);
    
    // update student progress
    setStudentProgress(prev => ({
      ...prev,
      overallScore: Number(((prev.overallScore * prev.problemsSolved + newSub.score) / (prev.problemsSolved + 1)).toFixed(1)),
      problemsSolved: Math.min(prev.totalProblems, prev.problemsSolved + 1)
    }));

    // Update instructor submissions count
    setInstructorStats(prev => ({
      ...prev,
      totalSubmissions: prev.totalSubmissions + 1
    }));

    showToast('AI multi-agent code evaluation completed!', 'success');
    setCurrentView('result');
  };

  const addCourse = async (newCourse: CourseItem) => {
    try {
      const response = await auth.authFetch('/api/instructor/courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_code: newCourse.code,
          title: newCourse.title,
          term: newCourse.term,
          description: newCourse.title
        })
      });

      if (!response.ok) {
        throw new Error('Course creation failed');
      }

      const created = await response.json();
      const savedCourse: CourseItem = {
        id: String(created.id),
        code: created.course_code,
        title: created.title,
        term: created.term || newCourse.term,
        studentsCount: 0,
        activeAssignments: 0,
        avgGrade: 'N/A'
      };

      setCourses(prev => [...prev, savedCourse]);
      showToast(`Course "${savedCourse.code}: ${savedCourse.title}" created!`, 'success');
    } catch (error) {
      console.error('Unable to save course to backend:', error);
      showToast('Unable to save course. Please retry.', 'error');
      throw error;
    }
  };

  const deleteCourse = async (id: string) => {
    const response = await auth.authFetch(`/api/instructor/courses/${encodeURIComponent(id)}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      showToast('Unable to archive course. Please retry.', 'error');
      throw new Error('Course archive failed');
    }
    setCourses(prev => prev.filter(c => c.id !== id));
    showToast('Course archived', 'success');
  };

  const addAssignment = async (newAssignment: Assignment & { courseId?: string | number; problemIds?: string[] }) => {
    const courseId = Number(newAssignment.courseId ?? (courses.find(c => `${c.code} ${c.title}` === newAssignment.course)?.id ?? 0));
    if (!courseId) {
      showToast('Choose a saved course before creating an assignment.', 'error');
      throw new Error('Assignment requires a persisted course');
    }

    try {
      const response = await auth.authFetch('/api/instructor/assignments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newAssignment.title,
          description: newAssignment.description,
          course_id: courseId,
          problem_ids: newAssignment.problemIds || [],
          due_date: newAssignment.dueDate ? new Date(newAssignment.dueDate).toISOString() : null,
          status: newAssignment.status.toUpperCase()
        })
      });

      if (!response.ok) {
        throw new Error('Assignment creation failed');
      }

      const created = await response.json();
      const savedAssignment: Assignment = {
        id: String(created.id),
        title: created.title,
        description: created.description || '',
        course: newAssignment.course,
        problemsCount: Array.isArray(created.problems) ? created.problems.length : newAssignment.problemsCount,
        problemIds: Array.isArray(created.problems) ? created.problems : newAssignment.problemIds || [],
        submittedCount: 0,
        totalCount: 0,
        avgScore: null,
        dueDate: newAssignment.dueDate,
        status: newAssignment.status
      };

      setAssignments(prev => [savedAssignment, ...prev]);
      setInstructorStats(prev => ({
        ...prev,
        activeAssignments: prev.activeAssignments + 1
      }));
      showToast(`Assignment "${savedAssignment.title}" published!`, 'success');
    } catch (error) {
      console.error('Unable to save assignment to backend:', error);
      showToast('Unable to save assignment. Please retry.', 'error');
      throw error;
    }
  };

  const deleteAssignment = async (id: string) => {
    const assignment = assignments.find(item => item.id === id);
    const response = await auth.authFetch(`/api/instructor/assignments/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: 'CLOSED' })
    });
    if (!response.ok) {
      showToast('Unable to archive assignment. Please retry.', 'error');
      throw new Error('Assignment archive failed');
    }
    setAssignments(prev => prev.map(item => item.id === id ? { ...item, status: 'Closed' } : item));
    if (assignment?.status === 'Active') {
      setInstructorStats(prev => ({
        ...prev,
        activeAssignments: Math.max(0, prev.activeAssignments - 1)
      }));
    }
    showToast('Assignment archived', 'success');
  };

  const addStudent = (newStudent: StudentRosterItem) => {
    setStudentRoster(prev => [newStudent, ...prev]);
    setInstructorStats(prev => ({
      ...prev,
      totalStudents: prev.totalStudents + 1
    }));
    showToast(`Student ${newStudent.name} enrolled!`, 'success');
  };

  const deleteStudent = (id: string) => {
    setStudentRoster(prev => prev.filter(s => s.id !== id));
    setInstructorStats(prev => ({
      ...prev,
      totalStudents: Math.max(0, prev.totalStudents - 1)
    }));
    showToast('Student removed from roster', 'info');
  };

  const dismissSimilarityAlert = (id: string) => {
    setSimilarityAlerts(prev => prev.filter(a => a.id !== id));
    showToast('Similarity incident marked as reviewed', 'info');
  };

  const generateReport = (newReport: ReportItem) => {
    setReports(prev => [newReport, ...prev]);
    showToast(`Report "${newReport.title}" generated!`, 'success');
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        updateCurrentUser,
        currentRole,
        currentView,
        setCurrentView,
        problems,
        addProblem,
        updateProblem,
        deleteProblem,
        selectedProblemId,
        setSelectedProblemId,
        selectedProblem,
        activeAssessment,
        setActiveAssessment,
        submissions,
        addSubmission,
        studentProgress,
        courses,
        addCourse,
        deleteCourse,
        studentRoster,
        selectedStudent,
        setSelectedStudent,
        addStudent,
        deleteStudent,
        assignments,
        addAssignment,
        deleteAssignment,
        similarityAlerts,
        dismissSimilarityAlert,
        reports,
        generateReport,
        instructorStats,
        announcements,
        dismissAnnouncement,
        openProblemWorkspace,
        openAssessmentResult,
        showToast
      }}
    >
      {children}

      {/* Floating Toast Notification Container (Doherty Threshold & Peak-End Rule) */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm pointer-events-none">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`pointer-events-auto p-4 rounded-2xl shadow-xl border flex items-center gap-3 animate-fadeIn transform transition-all duration-300 ${
              toast.type === 'success'
                ? 'bg-slate-900 text-white border-emerald-500/40 shadow-emerald-950/20'
                : toast.type === 'error'
                ? 'bg-rose-900 text-white border-rose-500/40 shadow-rose-950/20'
                : toast.type === 'warning'
                ? 'bg-amber-900 text-white border-amber-500/40 shadow-amber-950/20'
                : 'bg-slate-800 text-white border-slate-700 shadow-slate-950/20'
            }`}
          >
            {toast.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            ) : toast.type === 'error' ? (
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            ) : (
              <Info className="w-5 h-5 text-indigo-400 flex-shrink-0" />
            )}
            <p className="text-xs font-semibold leading-snug flex-1">{toast.message}</p>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-400 hover:text-white p-1"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
