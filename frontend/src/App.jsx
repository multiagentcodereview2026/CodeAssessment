import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet, useLocation, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import Login from './pages/Login';
import StudentLayout from './layouts/StudentLayout';
import SolverLayout from './layouts/SolverLayout';
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
import { ClassAnalyticsView } from './components/instructor/ClassAnalyticsView';
import { SimilarityReviewView } from './components/instructor/SimilarityReviewView';
import { ReportsExportView } from './components/instructor/ReportsExportView';
import { SettingsView } from './components/common/SettingsView';

import { AnimatePresence } from 'framer-motion';

class RouteErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    // Keep an actionable diagnostic during development instead of hiding it
    // behind a blank white page.
    console.error('Route rendering error:', error);
    this.setState({ message: error?.message || 'Unknown rendering error' });
  }

  componentDidUpdate(previousProps) {
    if (previousProps.locationKey !== this.props.locationKey && this.state.hasError) {
      this.setState({ hasError: false, message: '' });
    }
  }

  render() {
    if (this.state.hasError) {
      return <main className="min-h-screen grid place-items-center bg-slate-50 p-6">
        <section className="max-w-md rounded-2xl border border-rose-200 bg-white p-6 text-center shadow-sm">
          <h1 className="text-lg font-bold text-slate-900">We could not display this page</h1>
          <p className="mt-2 text-sm text-slate-600">Your submission was saved. Return to the submissions list and open it again.</p>
          {this.state.message && <pre className="mt-3 overflow-auto rounded-lg bg-slate-100 p-3 text-left text-xs text-rose-700">{this.state.message}</pre>}
          <Link className="mt-5 inline-block rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white" to="/submissions">View submissions</Link>
        </section>
      </main>;
    }
    return this.props.children;
  }
}

// Protected Route Wrapper for Students
const ProtectedStudentRoute = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'student') return <Navigate to="/instructor/dashboard" replace />;
  return <Outlet />;
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
    <RouteErrorBoundary locationKey={location.pathname}>
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Original Login Page */}
        <Route path="/login" element={<Login />} />
        
        {/* Student Feature Routes */}
        <Route path="/" element={<ProtectedStudentRoute />}>
          <Route element={<StudentLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<StudentDashboard />} />
            <Route path="problems" element={<ProblemsListView />} />
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
          <Route element={<SolverLayout />}>
            <Route path="problems/:id" element={<ProblemWorkspace />} />
            <Route path="workspace" element={<ProblemWorkspace />} />
          </Route>
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
    </RouteErrorBoundary>
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
