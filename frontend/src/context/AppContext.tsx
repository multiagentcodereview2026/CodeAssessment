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
  MOCK_INSTRUCTOR_USER,
  MOCK_PROBLEMS,
  MOCK_DEFAULT_ASSESSMENT,
  MOCK_RECENT_SUBMISSIONS,
  MOCK_STUDENT_PROGRESS,
  MOCK_STUDENT_ROSTER,
  MOCK_ASSIGNMENTS,
  MOCK_SIMILARITY_ALERTS,
  MOCK_REPORTS,
  MOCK_INSTRUCTOR_STATS
} from '../mock/data';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { useAuth } from './AuthContext';

export const INITIAL_COURSES: CourseItem[] = [
  {
    id: 'c1',
    code: 'CSE-301',
    title: 'Data Structures & Algorithms',
    term: 'Spring 2026',
    studentsCount: 48,
    activeAssignments: 4,
    avgGrade: '74.3%'
  },
  {
    id: 'c2',
    code: 'CSE-402',
    title: 'Advanced Algorithmic Design & Optimization',
    term: 'Spring 2026',
    studentsCount: 32,
    activeAssignments: 2,
    avgGrade: '81.0%'
  }
];

interface ToastInfo {
  id: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
}

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
  instructorStats: typeof MOCK_INSTRUCTOR_STATS;
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
  const [currentUser, setCurrentUser] = useState<UserProfile>(MOCK_STUDENT_USER);
  const [currentView, setCurrentView] = useState<string>('dashboard');

  // Shared persistent problems state
  const [problems, setProblems] = useState<Problem[]>(() => {
    try {
      const saved = localStorage.getItem('codevedha_problems');
      if (saved) return JSON.parse(saved);
    } catch {}
    return MOCK_PROBLEMS;
  });

  const [selectedProblemId, setSelectedProblemId] = useState<string>('prob-1');
  const [activeAssessment, setActiveAssessment] = useState<AssessmentResult>(MOCK_DEFAULT_ASSESSMENT);
  const [submissions, setSubmissions] = useState<SubmissionItem[]>(MOCK_RECENT_SUBMISSIONS);
  const [studentProgress, setStudentProgress] = useState<StudentProgress>(MOCK_STUDENT_PROGRESS);
  const [courses, setCourses] = useState<CourseItem[]>(INITIAL_COURSES);
  const [studentRoster, setStudentRoster] = useState<StudentRosterItem[]>(MOCK_STUDENT_ROSTER);
  const [selectedStudent, setSelectedStudent] = useState<StudentRosterItem | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>(MOCK_ASSIGNMENTS);
  const [similarityAlerts, setSimilarityAlerts] = useState<SimilarityAlert[]>(MOCK_SIMILARITY_ALERTS);
  const [reports, setReports] = useState<ReportItem[]>(MOCK_REPORTS);
  const [instructorStats, setInstructorStats] = useState(MOCK_INSTRUCTOR_STATS);
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>(() => {
    try {
      const saved = localStorage.getItem('codevedha_announcements');
      if (saved) return JSON.parse(saved);
    } catch {}
    return [];
  });
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [toasts, setToasts] = useState<ToastInfo[]>([]);

  useEffect(() => {
    if (!auth?.user) return;

    const role: Role = auth.user.role === 'instructor' ? 'instructor' : 'student';
    const profileBase = role === 'instructor' ? MOCK_INSTRUCTOR_USER : MOCK_STUDENT_USER;

    setCurrentRole(role);
    setCurrentUser({
      ...profileBase,
      id: auth.user.id || profileBase.id,
      name: auth.user.name || auth.user.username || profileBase.name,
      email: auth.user.email || profileBase.email,
      role
    });
    setIsAuthenticated(true);
  }, [auth?.user]);

  // Sync problems to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem('codevedha_problems', JSON.stringify(problems));
    } catch {}
  }, [problems]);

  useEffect(() => {
    try {
      localStorage.setItem('codevedha_announcements', JSON.stringify(announcements));
    } catch {}
  }, [announcements]);

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
      setCurrentUser(MOCK_STUDENT_USER);
      setCurrentView('dashboard');
    } else {
      setCurrentUser(MOCK_INSTRUCTOR_USER);
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
