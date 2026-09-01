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
  StudentAssignmentStatus
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
  const [activeBroadcast, setActiveBroadcast] = useState<string | null>(
    '📢 Instructor Notice: Prof. Sarah Miller posted a new challenge "Two Sum" for CSE-301. Please solve before May 10!'
  );

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

  const addAssignment = (newAssignment: Assignment, newProblem?: Problem) => {
    setAssignments(prev => [newAssignment, ...prev]);
    
    // If a new problem was created specifically for this assignment, add it to problems catalog
    if (newProblem) {
      setProblems(prev => [newProblem, ...prev]);
    } else {
      // Mark selected existing problem IDs as instructor_assigned
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

    // Trigger notification banner for students
    setActiveBroadcast(
      `📢 New Assignment Posted: "${newAssignment.title}" by ${newAssignment.instructorName || 'Prof. Sarah Miller'} • Due ${newAssignment.dueDate}. Please solve!`
    );
  };

  const addSubmission = (newSub: SubmissionItem, newAssessment: AssessmentResult) => {
    setSubmissions(prev => [newSub, ...prev]);
    setActiveAssessment(newAssessment);
    
    // update problem studentStatus
    updateProblemStatus(newSub.problemId, 'Submitted');

    // update student progress
    setStudentProgress(prev => ({
      ...prev,
      overallScore: Number(((prev.overallScore * prev.problemsSolved + newSub.score) / (prev.problemsSolved + 1)).toFixed(1)),
      problemsSolved: Math.min(prev.totalProblems, prev.problemsSolved + 1)
    }));

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
        dismissBroadcast
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
