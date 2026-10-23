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
  AnnouncementItem,
  Difficulty
} from '../types';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { useAuth } from './AuthContext';

interface ToastInfo {
  id: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
}

const EMPTY_STUDENT_PROGRESS: StudentProgress = {
  overallScore: 0,
  problemsSolved: 0,
  totalProblems: 0,
  currentStreak: 0,
  rankPercentile: '—',
  progressPercent: 0,
  topicsCovered: 0,
  totalTopics: 0,
  hoursSpent: '0h',
  weakTopics: [],
  categoryWiseScores: [],
  scoreTrend: []
};

const EMPTY_INSTRUCTOR_STATS = {
  totalStudents: 0,
  totalSubmissions: 0,
  activeAssignments: 0,
  classAvg: 'N/A'
};

const EMPTY_ASSESSMENT: AssessmentResult = {
  id: '',
  problemId: '',
  problemTitle: '',
  language: '',
  code: '',
  overallScore: 0,
  correctness: 0,
  performance: 0,
  codeQuality: 0,
  security: 0,
  complexity: { time: '—', space: '—' },
  feedback: {
    summary: 'No assessment generated yet.',
    strengths: [],
    improvements: [],
    suggestions: []
  },
  testCaseResults: [],
  executionTime: 0,
  memoryUsage: 0,
  scoreProjection: {
    currentScore: 0,
    projectedScore: 0,
    improvementDelta: 0,
    focusAreas: []
  }
};

const mapApiProblem = (p: any): Problem => ({
  id: String(p.id),
  slug: String(p.slug || p.id),
  title: String(p.title || p.id),
  difficulty: (['Easy', 'Medium', 'Hard'].includes(p.difficulty) ? p.difficulty : 'Medium') as Difficulty,
  tags: Array.isArray(p.topic_tags) && p.topic_tags.length ? p.topic_tags : [p.category || 'Algorithms'],
  acceptanceRate: p.acceptance_rate || '—',
  description: p.description || '',
  examples: Array.isArray(p.examples) ? p.examples : [],
  constraints: Array.isArray(p.constraints) ? p.constraints : [],
  testCases: (p.test_cases || []).map((tc: any, idx: number) => ({
    id: String(tc.id || `${p.id}-tc-${idx + 1}`),
    input: String(tc.input || ''),
    expectedOutput: String(tc.expected_output || tc.output || ''),
    isHidden: Boolean(tc.is_hidden)
  })),
  starterCode: p.starter_codes || {},
  solutionCode: p.solution_code || {},
  optimalComplexity: {
    time: p.optimal_time || p.target_time_complexity || 'O(N)',
    space: p.optimal_space || p.target_space_complexity || 'O(1)'
  },
  isInstructorAssigned: Boolean(p.is_instructor_assigned),
  courseCode: p.course_code || '',
  dueDate: p.due_date || ''
});

const mapApiSubmission = (record: any, problemTitleMap: Map<string, string>): SubmissionItem => {
  const execution = record.execution_result || {};
  const feedback = record.feedback && typeof record.feedback === 'object' ? record.feedback : {};
  const passed = Number(execution.passed_cases || 0);
  const total = Number(execution.total_cases || (passed + Number(execution.failed_cases || 0)));
  const passedAll = total > 0 && passed === total;
  return {
    id: record.submission_id || String(record.id),
    problemId: record.problem_id,
    problemSlug: record.problem_id,
    problemTitle: problemTitleMap.get(record.problem_id) || record.problem_title || record.problem_id,
    score: Math.round(Number(record.overall_score ?? 0)),
    evaluationStatus: String(record.status || 'EVALUATED'),
    feedbackSummary: typeof feedback.summary === 'string' ? feedback.summary : (typeof feedback.mentor_feedback === 'string' ? feedback.mentor_feedback : ''),
    status: passedAll ? 'Passed' : passed > 0 ? 'Partial' : 'Failed',
    language: record.language || '—',
    source: record.source === 'INSTRUCTOR_ASSIGNED' || record.assignment_id != null ? 'Instructor Assigned' : 'Independent Practice',
    date: record.created_at ? new Date(record.created_at).toLocaleString() : 'Saved submission',
    executionTime: `${execution.runtime_ms || 0} ms`,
    passedTestCases: passed,
    totalTestCases: total
  };
};

const mapApiAnnouncement = (a: any): AnnouncementItem => ({
  id: a.id || a.problemId || String(Date.now()),
  title: a.title || 'New question posted',
  message: a.message || '',
  problemId: a.problemId || a.problem_id,
  courseCode: a.courseCode || a.course_code,
  dueDate: a.dueDate || a.due_date,
  createdAt: a.createdAt || a.created_at || 'Just now',
  read: Boolean(a.read)
});

interface AppContextType {
  currentUser: UserProfile;
  updateCurrentUser: (profile: Partial<UserProfile>) => void;
  currentRole: Role;
  switchRole: (role: Role) => void;
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
  isAuthenticated: boolean;
  login: (role: Role) => void;
  logout: () => void;
  openProblemWorkspace: (problemId: string) => void;
  openAssessmentResult: (submissionId?: string) => void;
  showToast: (message: string, type?: 'success' | 'info' | 'warning' | 'error') => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const auth = useAuth();
  const [currentRole, setCurrentRole] = useState<Role>('student');
  const [currentUser, setCurrentUser] = useState<UserProfile>({
    id: '',
    name: '',
    email: '',
    role: 'student',
    avatar: '',
    rollNumber: '',
    institution: 'Engineering College',
    department: 'Computer Science',
    year: '3rd Year'
  });
  const [currentView, setCurrentView] = useState<string>('dashboard');

  const [problems, setProblems] = useState<Problem[]>([]);
  const [selectedProblemId, setSelectedProblemId] = useState<string>('');
  const [activeAssessment, setActiveAssessment] = useState<AssessmentResult>(EMPTY_ASSESSMENT);
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
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [toasts, setToasts] = useState<ToastInfo[]>([]);

  // Sync authenticated user into current state
  useEffect(() => {
    if (!auth?.user) return;
    const role: Role = auth.user.role === 'instructor' ? 'instructor' : 'student';
    setCurrentRole(role);
    setCurrentUser({
      id: String(auth.user.id || auth.user.username || ''),
      name: String(auth.user.name || auth.user.username || ''),
      email: String(auth.user.email || ''),
      role,
      avatar: '',
      rollNumber: String(auth.user.username || auth.user.id || ''),
      institution: 'Engineering College',
      department: 'Computer Science',
      year: '3rd Year'
    });
    setIsAuthenticated(true);
  }, [auth?.user]);

  // Pull all live data from database APIs
  useEffect(() => {
    let cancelled = false;

    const loadLiveDatabaseData = async () => {
      const fetchFn = auth?.authFetch || fetch;

      try {
        // 1. Fetch practice and instructor problems from database
        const [practiceRes, instructorProbRes] = await Promise.allSettled([
          fetchFn('/api/problems', { cache: 'no-store' }),
          fetchFn('/api/instructor-problems', { cache: 'no-store' })
        ]);

        const allProbs: Problem[] = [];
        const titleMap = new Map<string, string>();

        if (practiceRes.status === 'fulfilled' && practiceRes.value.ok) {
          const list = await practiceRes.value.json().catch(() => []);
          if (Array.isArray(list)) {
            list.forEach((p: any) => {
              const mapped = mapApiProblem(p);
              allProbs.push(mapped);
              titleMap.set(mapped.id, mapped.title);
            });
          }
        }

        if (instructorProbRes.status === 'fulfilled' && instructorProbRes.value.ok) {
          const list = await instructorProbRes.value.json().catch(() => []);
          if (Array.isArray(list)) {
            list.forEach((p: any) => {
              const mapped = mapApiProblem({ ...p, is_instructor_assigned: true });
              if (!titleMap.has(mapped.id)) {
                allProbs.push(mapped);
                titleMap.set(mapped.id, mapped.title);
              }
            });
          }
        }

        if (!cancelled && allProbs.length > 0) {
          setProblems(allProbs);
          setSelectedProblemId((prev) => prev || allProbs[0].id);
        }

        // 2. Fetch announcements from database
        try {
          const annRes = await fetchFn('/api/announcements', { cache: 'no-store' });
          if (annRes.ok) {
            const list = await annRes.json().catch(() => []);
            if (!cancelled && Array.isArray(list)) {
              setAnnouncements(list.map(mapApiAnnouncement));
            }
          }
        } catch {}

        // 3. Fetch submissions from database
        try {
          const subRes = await fetchFn('/api/submissions', { cache: 'no-store' });
          if (subRes.ok) {
            const list = await subRes.json().catch(() => []);
            if (!cancelled && Array.isArray(list)) {
              setSubmissions(list.map((r: any) => mapApiSubmission(r, titleMap)));
            }
          }
        } catch {}

        // 4. Fetch student analytics from database
        const studentId = auth?.user?.username || auth?.user?.id;
        if (studentId) {
          try {
            const anRes = await fetchFn(`/api/analytics/student/${encodeURIComponent(studentId)}`, { cache: 'no-store' });
            if (anRes.ok) {
              const an = await anRes.json().catch(() => null);
              if (!cancelled && an) {
                const totalProbs = Number(an.total_problems ?? allProbs.length);
                const solved = Number(an.problems_solved ?? 0);
                setStudentProgress({
                  overallScore: an.overall_score == null ? 0 : Number(an.overall_score),
                  problemsSolved: solved,
                  totalProblems: totalProbs,
                  currentStreak: Number(an.streak_days ?? 0),
                  rankPercentile: an.xp ? `#${Math.max(1, 10 - Math.floor(an.xp / 100))}` : '—',
                  progressPercent: totalProbs > 0 ? Math.round((solved / totalProbs) * 100) : 0,
                  topicsCovered: Array.isArray(an.category_breakdown) ? an.category_breakdown.length : 0,
                  totalTopics: Array.isArray(an.category_breakdown) ? an.category_breakdown.length : 0,
                  hoursSpent: '—',
                  weakTopics: Array.isArray(an.weak_topics) ? an.weak_topics : [],
                  categoryWiseScores: Array.isArray(an.category_breakdown)
                    ? an.category_breakdown.map((item: any) => ({
                        name: String(item.name),
                        percentage: Number(item.value || 0),
                        color: String(item.color || '#059669'),
                        scoreDisplay: `${Number(item.value || 0)}%`
                      }))
                    : [],
                  scoreTrend: Array.isArray(an.score_trend) ? an.score_trend : []
                });
              }
            }
          } catch {}
        }

        // 5. Fetch instructor data if role is instructor
        if (auth?.user?.role === 'instructor') {
          try {
            const [overviewRes, coursesRes, assignRes] = await Promise.allSettled([
              fetchFn('/api/instructor/overview', { cache: 'no-store' }),
              fetchFn('/api/instructor/courses', { cache: 'no-store' }),
              fetchFn('/api/instructor/assignments', { cache: 'no-store' })
            ]);

            if (overviewRes.status === 'fulfilled' && overviewRes.value.ok) {
              const overview = await overviewRes.value.json().catch(() => null);
              if (!cancelled && overview) {
                setInstructorStats({
                  totalStudents: Number(overview.total_students ?? 0),
                  activeAssignments: Number(overview.active_assignments ?? 0),
                  totalSubmissions: Number(overview.total_submissions ?? 0),
                  classAvg: overview.class_avg_score != null ? `${overview.class_avg_score}%` : 'N/A'
                });
                if (Array.isArray(overview.students)) {
                  setStudentRoster(overview.students);
                }
              }
            }

            if (coursesRes.status === 'fulfilled' && coursesRes.value.ok) {
              const cList = await coursesRes.value.json().catch(() => []);
              if (!cancelled && Array.isArray(cList)) {
                setCourses(cList.map((c: any) => ({
                  id: String(c.id),
                  code: c.course_code,
                  title: c.title,
                  term: c.term || 'N/A',
                  studentsCount: Number(c.student_count ?? 0),
                  activeAssignments: Number(c.assignment_count ?? 0),
                  avgGrade: c.avg_score != null ? `${c.avg_score}%` : 'N/A'
                })));
              }
            }

            if (assignRes.status === 'fulfilled' && assignRes.value.ok) {
              const aList = await assignRes.value.json().catch(() => []);
              if (!cancelled && Array.isArray(aList)) {
                setAssignments(aList.map((a: any) => ({
                  id: String(a.id),
                  title: a.title,
                  description: a.description || '',
                  course: a.course_title || `Course ${a.course_id}`,
                  problemsCount: Array.isArray(a.problems) ? a.problems.length : 0,
                  problemIds: Array.isArray(a.problems) ? a.problems : [],
                  submittedCount: Number(a.submitted_count ?? 0),
                  totalCount: Number(a.total_students ?? 0),
                  avgScore: a.avg_score != null ? Number(a.avg_score) : null,
                  dueDate: a.due_date || '',
                  status: a.status === 'ACTIVE' ? 'Active' : 'Closed',
                  revisionPolicy: a.revision_policy || 'GUIDED_STEPS'
                })));
              }
            }
          } catch {}
        }
      } catch (err) {
        console.error('Failed to load live data from database:', err);
      }
    };

    void loadLiveDatabaseData();
    return () => { cancelled = true; };
  }, [auth?.user?.id, auth?.user?.role, auth?.authFetch]);

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

  const switchRole = (role: Role) => {
    setCurrentRole(role);
    if (role === 'student') {
      setCurrentView('dashboard');
    } else {
      setCurrentView('instructor-dashboard');
    }
  };

  const login = (role: Role) => {
    setIsAuthenticated(true);
    switchRole(role);
    showToast(`Signed in as ${role === 'student' ? 'Student' : 'Faculty'}`, 'success');
  };

  const logout = () => {
    setIsAuthenticated(false);
    showToast('Signed out successfully', 'info');
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
    showToast(`Question "${newProb.title}" published!`, 'success');
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
    showToast('Question removed', 'info');
  };

  const selectedProblem = problems.find(p => p.id === selectedProblemId) || problems[0] || ({
    id: '',
    slug: '',
    title: 'No problem selected',
    difficulty: 'Medium',
    tags: [],
    acceptanceRate: '—',
    description: '',
    examples: [],
    constraints: [],
    testCases: [],
    starterCode: {},
    solutionCode: {},
    optimalComplexity: { time: '—', space: '—' },
    isInstructorAssigned: false,
    courseCode: '',
    dueDate: ''
  } as Problem);

  const openProblemWorkspace = (problemId: string) => {
    setSelectedProblemId(problemId);
    setCurrentView('workspace');
  };

  const openAssessmentResult = (_submissionId?: string) => {
    setCurrentView('result');
  };

  const addSubmission = (newSub: SubmissionItem, newAssessment: AssessmentResult) => {
    setSubmissions(prev => [{ ...newSub, evaluationStatus: newSub.evaluationStatus || 'EVALUATED' }, ...prev]);
    setActiveAssessment(newAssessment);
    
    setStudentProgress(prev => ({
      ...prev,
      overallScore: Number(((prev.overallScore * prev.problemsSolved + newSub.score) / (prev.problemsSolved + 1)).toFixed(1)),
      problemsSolved: Math.min(prev.totalProblems, prev.problemsSolved + 1)
    }));

    setInstructorStats(prev => ({
      ...prev,
      totalSubmissions: prev.totalSubmissions + 1
    }));

    showToast('Solution submitted & evaluation completed!', 'success');
    setCurrentView('result');
  };

  const addCourse = (newCourse: CourseItem) => {
    setCourses(prev => [...prev, newCourse]);
    showToast(`Course "${newCourse.code}: ${newCourse.title}" created!`, 'success');
  };

  const deleteCourse = (id: string) => {
    setCourses(prev => prev.filter(c => c.id !== id));
    showToast('Course removed', 'info');
  };

  const addAssignment = (newAssignment: Assignment) => {
    setAssignments(prev => [newAssignment, ...prev]);
    setInstructorStats(prev => ({
      ...prev,
      activeAssignments: prev.activeAssignments + 1
    }));
    showToast(`Assignment "${newAssignment.title}" published!`, 'success');
  };

  const deleteAssignment = (id: string) => {
    setAssignments(prev => prev.filter(a => a.id !== id));
    setInstructorStats(prev => ({
      ...prev,
      activeAssignments: Math.max(0, prev.activeAssignments - 1)
    }));
    showToast('Assignment deleted', 'info');
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
        switchRole,
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
        isAuthenticated,
        login,
        logout,
        openProblemWorkspace,
        openAssessmentResult,
        showToast
      }}
    >
      {children}

      {/* Floating Toast Notification Container */}
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
              className="text-slate-400 hover:text-white p-1 cursor-pointer"
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
