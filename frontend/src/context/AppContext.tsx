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
  ReportItem
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

interface AppContextType {
  currentUser: UserProfile;
  currentRole: Role;
  switchRole: (role: Role) => void;
  currentView: string;
  setCurrentView: (view: string) => void;
  selectedProblemId: string;
  setSelectedProblemId: (id: string) => void;
  selectedProblem: Problem;
  activeAssessment: AssessmentResult;
  setActiveAssessment: (result: AssessmentResult) => void;
  submissions: SubmissionItem[];
  addSubmission: (submission: SubmissionItem, assessment: AssessmentResult) => void;
  studentProgress: StudentProgress;
  studentRoster: StudentRosterItem[];
  selectedStudent: StudentRosterItem | null;
  setSelectedStudent: (student: StudentRosterItem | null) => void;
  assignments: Assignment[];
  addAssignment: (assignment: Assignment) => void;
  similarityAlerts: SimilarityAlert[];
  reports: ReportItem[];
  instructorStats: typeof MOCK_INSTRUCTOR_STATS;
  isAuthenticated: boolean;
  login: (role: Role) => void;
  logout: () => void;
  openProblemWorkspace: (problemId: string) => void;
  openAssessmentResult: (submissionId?: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentRole, setCurrentRole] = useState<Role>('student');
  const [currentUser, setCurrentUser] = useState<UserProfile>(MOCK_STUDENT_USER);
  const [currentView, setCurrentView] = useState<string>('dashboard');
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

  const selectedProblem = MOCK_PROBLEMS.find(p => p.id === selectedProblemId) || MOCK_PROBLEMS[0];

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

    setCurrentView('result');
  };

  const addAssignment = (newAssignment: Assignment) => {
    setAssignments(prev => [newAssignment, ...prev]);
    setInstructorStats(prev => ({
      ...prev,
      activeAssignments: prev.activeAssignments + 1
    }));
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
        similarityAlerts,
        reports,
        instructorStats,
        isAuthenticated,
        login,
        logout,
        openProblemWorkspace,
        openAssessmentResult
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
