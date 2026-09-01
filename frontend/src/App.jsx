import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import Login from './pages/Login';
import StudentLayout from './layouts/StudentLayout';
import InstructorLayout from './layouts/InstructorLayout';

// Student Feature Components from git
import { StudentDashboard } from './components/student/StudentDashboard';
import { ProblemsListView } from './components/student/ProblemsListView';
import { ProblemWorkspace } from './components/student/ProblemWorkspace';
import { AssessmentResultView } from './components/student/AssessmentResultView';
import { SubmissionsList } from './components/student/SubmissionsList';
import { AnalyticsProgressView } from './components/student/AnalyticsProgressView';
import { FeedbackRecommendationsView } from './components/student/FeedbackRecommendationsView';
import { StudentProfileView } from './components/student/StudentProfileView';

// Instructor Feature Components from git
import { InstructorDashboard } from './components/instructor/InstructorDashboard';
import { CoursesManagerView } from './components/instructor/CoursesManagerView';
import { StudentRosterView } from './components/instructor/StudentRosterView';
import { AssignmentsManagerView } from './components/instructor/AssignmentsManagerView';
import { ClassAnalyticsView } from './components/instructor/ClassAnalyticsView';
import { SimilarityReviewView } from './components/instructor/SimilarityReviewView';
import { ReportsExportView } from './components/instructor/ReportsExportView';
import { SettingsView } from './components/common/SettingsView';

import { AnimatePresence } from 'framer-motion';

// Protected Route Wrapper for Students
const ProtectedStudentRoute = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'student') return <Navigate to="/instructor/dashboard" replace />;
  return <StudentLayout />;
};

// Protected Route Wrapper for Instructors
const ProtectedInstructorRoute = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'instructor') return <Navigate to="/dashboard" replace />;
  return <InstructorLayout />;
};

function AppRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Original Login Page */}
        <Route path="/login" element={<Login />} />
        
        {/* Student Feature Routes */}
        <Route path="/" element={<ProtectedStudentRoute />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<StudentDashboard />} />
          <Route path="problems" element={<ProblemsListView />} />
          <Route path="problems/:id" element={<ProblemWorkspace />} />
          <Route path="workspace" element={<ProblemWorkspace />} />
          <Route path="submissions" element={<SubmissionsList />} />
          <Route path="submissions/:id" element={<AssessmentResultView />} />
          <Route path="result" element={<AssessmentResultView />} />
          <Route path="analytics" element={<AnalyticsProgressView />} />
          <Route path="progress" element={<AnalyticsProgressView />} />
          <Route path="feedback" element={<FeedbackRecommendationsView />} />
          <Route path="recommendations" element={<FeedbackRecommendationsView />} />
          <Route path="profile" element={<StudentProfileView />} />
          <Route path="settings" element={<SettingsView />} />
        </Route>

        {/* Instructor Feature Routes */}
        <Route path="/instructor" element={<ProtectedInstructorRoute />}>
          <Route index element={<Navigate to="/instructor/dashboard" replace />} />
          <Route path="dashboard" element={<InstructorDashboard />} />
          <Route path="courses" element={<CoursesManagerView />} />
          <Route path="students" element={<StudentRosterView />} />
          <Route path="assignments" element={<Navigate to="/instructor/problems" replace />} />
          <Route path="problems" element={<ProblemsListView />} />
          <Route path="analytics" element={<ClassAnalyticsView />} />
          <Route path="similarity" element={<SimilarityReviewView />} />
          <Route path="reports" element={<ReportsExportView />} />
          <Route path="settings" element={<SettingsView />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AppProvider>
    </AuthProvider>
  );
}

export default App;
