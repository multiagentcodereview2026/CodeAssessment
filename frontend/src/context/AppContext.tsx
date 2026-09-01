import React, { createContext, useContext, useState, ReactNode } from 'react';
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
  StudentAssignmentStatus,
  AppNotification
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

export const INITIAL_NOTIFICATIONS: AppNotification[] = [
  {
    id: 'notif-1',
    title: 'New Instructor Assignment',
    message: 'Prof. Sarah Miller posted "Two Sum" for CSE-301 Section A.',
    timestamp: '5m ago',
    isRead: false,
    type: 'assignment',
    actionTarget: {
      view: 'workspace',
      problemId: 'prob-1'
    }
  },
  {
    id: 'notif-2',
    title: 'Two Sum Evaluation Complete',
    message: 'Scored 85/100. AI optimization diff available (+7 pts boost).',
    timestamp: '15m ago',
    isRead: false,
    type: 'submission',
    actionTarget: {
      view: 'result',
      submissionId: 'SUB90124'
    }
  },
  {
    id: 'notif-3',
    title: 'High Similarity Alert Detected',
    message: 'Sai Kiran & Harish N. have 89% AST code token similarity on Two Sum.',
    timestamp: '30m ago',
    isRead: false,
    type: 'similarity',
    actionTarget: {
      view: 'instructor-analytics'
    }
  },
  {
    id: 'notif-4',
    title: 'Coursework Deadline Approaching',
    message: 'DSA Assignment 1 is due on 10 May 2026 for CSE-301.',
    timestamp: '2h ago',
    isRead: true,
    type: 'alert',
    actionTarget: {
      view: 'problems'
    }
  }
];

interface AppContextType {
  currentUser: UserProfile;
  currentRole: Role;
  switchRole: (role: Role) => void;
  currentView: string;
  setCurrentView: (view: string) => void;
  selectedProblemId: string;
  setSelectedProblemId: (id: string) => void;
  selectedProblem: Problem;
  problems: Problem[];
  createProblem: (problem: Problem) => void;
  activeAssessment: AssessmentResult;
  setActiveAssessment: (result: AssessmentResult) => void;
  submissions: SubmissionItem[];
  addSubmission: (submission: SubmissionItem, assessment: AssessmentResult) => void;
  studentProgress: StudentProgress;
  studentRoster: StudentRosterItem[];
  selectedStudent: StudentRosterItem | null;
  setSelectedStudent: (student: StudentRosterItem | null) => void;
  assignments: Assignment[];
  addAssignment: (assignment: Assignment, newProblem?: Problem) => void;
  updateProblemStatus: (problemId: string, status: StudentAssignmentStatus) => void;
  similarityAlerts: SimilarityAlert[];
  reports: ReportItem[];
  instructorStats: typeof MOCK_INSTRUCTOR_STATS;
  isAuthenticated: boolean;
  login: (role: Role) => void;
  logout: () => void;
  openProblemWorkspace: (problemId: string) => void;
  openAssessmentResult: (submissionId?: string) => void;
  activeBroadcast: string | null;
  dismissBroadcast: () => void;
  mobileMenuOpen: boolean;
  setMobileMenuOpen: (open: boolean) => void;
  notifications: AppNotification[];
  markNotificationAsRead: (id: string) => void;
  markAllNotificationsAsRead: () => void;
  handleNotificationClick: (notif: AppNotification) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentRole, setCurrentRole] = useState<Role>('student');
  const [currentUser, setCurrentUser] = useState<UserProfile>(MOCK_STUDENT_USER);
  const [currentView, setCurrentView] = useState<string>('dashboard');
  const [problems, setProblems] = useState<Problem[]>(MOCK_PROBLEMS);
  const [selectedProblemId, setSelectedProblemId] = useState<string>('prob-1');
  const [activeAssessment, setActiveAssessment] = useState<AssessmentResult>(MOCK_DEFAULT_ASSESSMENT);
  const [submissions, setSubmissions] = useState<SubmissionItem[]>(MOCK_RECENT_SUBMISSIONS);
  const [studentProgress, setStudentProgress] = useState<StudentProgress>(MOCK_STUDENT_PROGRESS);
  const [studentRoster, setStudentRoster] = useState<StudentRosterItem[]>(MOCK_STUDENT_ROSTER);
  const [selectedStudent, setSelectedStudent] = useState<StudentRosterItem | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>(MOCK_ASSIGNMENTS);
  const [similarityAlerts, setSimilarityAlerts] = useState<SimilarityAlert[]>(MOCK_SIMILARITY_ALERTS);
  const [reports, setReports] = useState<ReportItem[]>(MOCK_REPORTS);
  const [instructorStats, setInstructorStats] = useState(MOCK_INSTRUCTOR_STATS);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [notifications, setNotifications] = useState<AppNotification[]>(INITIAL_NOTIFICATIONS);
  const [activeBroadcast, setActiveBroadcast] = useState<string | null>(
    '📢 Instructor Notice: Prof. Sarah Miller posted a new challenge "Two Sum" for CSE-301. Please solve before May 10!'
  );
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

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
  };

  const logout = () => {
    setIsAuthenticated(false);
  };

  const selectedProblem = problems.find(p => p.id === selectedProblemId) || problems[0];

  const openProblemWorkspace = (problemId: string) => {
    setSelectedProblemId(problemId);
    setCurrentView('workspace');
  };

  const openAssessmentResult = (_submissionId?: string) => {
    setCurrentView('result');
  };

  const createProblem = (newProblem: Problem) => {
    setProblems(prev => [newProblem, ...prev]);
  };

  const updateProblemStatus = (problemId: string, status: StudentAssignmentStatus) => {
    setProblems(prev =>
      prev.map(p => (p.id === problemId ? { ...p, studentStatus: status } : p))
    );
  };

  const markNotificationAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, isRead: true } : n))
    );
  };

  const markAllNotificationsAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
  };

  const handleNotificationClick = (notif: AppNotification) => {
    markNotificationAsRead(notif.id);
    if (notif.actionTarget.problemId) {
      openProblemWorkspace(notif.actionTarget.problemId);
    } else if (notif.actionTarget.submissionId) {
      openAssessmentResult(notif.actionTarget.submissionId);
    } else if (notif.actionTarget.view) {
      setCurrentView(notif.actionTarget.view);
    }
  };

  const addAssignment = (newAssignment: Assignment, newProblem?: Problem) => {
    setAssignments(prev => [newAssignment, ...prev]);
    
    if (newProblem) {
      setProblems(prev => [newProblem, ...prev]);
    } else {
      setProblems(prev =>
        prev.map(p =>
          newAssignment.problemIds.includes(p.id)
            ? {
                ...p,
                origin: 'instructor_assigned',
                assignmentId: newAssignment.id,
                instructorName: newAssignment.instructorName || 'Prof. Sarah Miller',
                dueDate: newAssignment.dueDate,
                studentStatus: 'Not Started'
              }
            : p
        )
      );
    }

    setInstructorStats(prev => ({
      ...prev,
      activeAssignments: prev.activeAssignments + 1
    }));

    // Trigger dynamic broadcast banner & push real notification
    setActiveBroadcast(
      `📢 New Assignment Posted: "${newAssignment.title}" by ${newAssignment.instructorName || 'Prof. Sarah Miller'} • Due ${newAssignment.dueDate}. Please solve!`
    );

    const newNotif: AppNotification = {
      id: `notif-${Date.now()}`,
      title: 'New Instructor Assignment',
      message: `Prof. Sarah Miller posted "${newAssignment.title}" for CSE-301.`,
      timestamp: 'Just now',
      isRead: false,
      type: 'assignment',
      actionTarget: {
        view: 'workspace',
        problemId: newProblem ? newProblem.id : newAssignment.problemIds[0]
      }
    };
    setNotifications(prev => [newNotif, ...prev]);
  };

  const addSubmission = (newSub: SubmissionItem, newAssessment: AssessmentResult) => {
    setSubmissions(prev => [newSub, ...prev]);
    setActiveAssessment(newAssessment);
    
    updateProblemStatus(newSub.problemId, 'Submitted');

    setStudentProgress(prev => ({
      ...prev,
      overallScore: Number(((prev.overallScore * prev.problemsSolved + newSub.score) / (prev.problemsSolved + 1)).toFixed(1)),
      problemsSolved: Math.min(prev.totalProblems, prev.problemsSolved + 1)
    }));

    // Add evaluation notification
    const newNotif: AppNotification = {
      id: `notif-${Date.now()}`,
      title: `${newSub.problemTitle} Evaluated`,
      message: `Scored ${newSub.score}/100. Multi-agent explainable report is ready.`,
      timestamp: 'Just now',
      isRead: false,
      type: 'submission',
      actionTarget: {
        view: 'result',
        submissionId: newSub.id
      }
    };
    setNotifications(prev => [newNotif, ...prev]);

    setCurrentView('result');
  };

  const dismissBroadcast = () => {
    setActiveBroadcast(null);
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        currentRole,
        switchRole,
        currentView,
        setCurrentView,
        selectedProblemId,
        setSelectedProblemId,
        selectedProblem,
        problems,
        createProblem,
        activeAssessment,
        setActiveAssessment,
        submissions,
        addSubmission,
        studentProgress,
        studentRoster,
        selectedStudent,
        setSelectedStudent,
        assignments,
        addAssignment,
        updateProblemStatus,
        similarityAlerts,
        reports,
        instructorStats,
        isAuthenticated,
        login,
        logout,
        openProblemWorkspace,
        openAssessmentResult,
        activeBroadcast,
        dismissBroadcast,
        mobileMenuOpen,
        setMobileMenuOpen,
        notifications,
        markNotificationAsRead,
        markAllNotificationsAsRead,
        handleNotificationClick
      }}
    >
      {children}
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
