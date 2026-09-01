import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Navbar } from './components/common/Navbar';
import { Sidebar } from './components/common/Sidebar';
import { AuthPage } from './components/auth/AuthPage';

// Student Components
import { StudentDashboard } from './components/student/StudentDashboard';
import { ProblemWorkspace } from './components/student/ProblemWorkspace';
import { AssessmentResultView } from './components/student/AssessmentResultView';
import { SubmissionsList } from './components/student/SubmissionsList';
import { ScoresAnalytics } from './components/student/ScoresAnalytics';
import { FeedbackHistory } from './components/student/FeedbackHistory';
import { StudentProgressView } from './components/student/StudentProgressView';
import { StudentProfileView } from './components/student/StudentProfileView';
import { ProblemsListView } from './components/student/ProblemsListView';
import { RecommendationsView } from './components/student/RecommendationsView';

// Instructor Components
import { InstructorDashboard } from './components/instructor/InstructorDashboard';
import { StudentRosterView } from './components/instructor/StudentRosterView';
import { ClassAnalyticsView } from './components/instructor/ClassAnalyticsView';
import { AssignmentsManagerView } from './components/instructor/AssignmentsManagerView';
import { InstructorSubmissionsReviewView } from './components/instructor/InstructorSubmissionsReviewView';
import { SimilarityReviewView } from './components/instructor/SimilarityReviewView';
import { ReportsExportView } from './components/instructor/ReportsExportView';
import { CoursesManagerView } from './components/instructor/CoursesManagerView';
import { SettingsView } from './components/common/SettingsView';

const MainLayout: React.FC = () => {
  const { isAuthenticated, currentView, currentRole } = useApp();

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const renderContent = () => {
    switch (currentView) {
      // Student Views
      case 'dashboard':
        return <StudentDashboard />;
      case 'problems':
        return <ProblemsListView />;
      case 'workspace':
        return <ProblemWorkspace />;
      case 'result':
        return <AssessmentResultView />;
      case 'submissions':
        return <SubmissionsList />;
      case 'scores':
        return <ScoresAnalytics />;
      case 'feedback':
        return <FeedbackHistory />;
      case 'recommendations':
        return <RecommendationsView />;
      case 'progress':
        return <StudentProgressView />;
      case 'profile':
        return <StudentProfileView />;
      case 'settings':
        return <SettingsView />;

      // Instructor Views (Strictly Assignment Dispatch, Submissions Review & Moderation)
      case 'instructor-dashboard':
        return <InstructorDashboard />;
      case 'instructor-assignments':
        return <AssignmentsManagerView />;
      case 'instructor-submissions':
        return <InstructorSubmissionsReviewView />;
      case 'instructor-students':
        return <StudentRosterView />;
      case 'instructor-analytics':
        return <ClassAnalyticsView />;
      case 'instructor-similarity':
        return <SimilarityReviewView />;
      case 'instructor-courses':
        return <CoursesManagerView />;
      case 'instructor-reports':
        return <ReportsExportView />;
      case 'instructor-settings':
        return <SettingsView />;

      default:
        return currentRole === 'student' ? <StudentDashboard /> : <InstructorDashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col selection:bg-indigo-500 selection:text-white">
      <Navbar />
      <div className="flex-1 flex max-w-[1600px] w-full mx-auto">
        <Sidebar />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-full">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <MainLayout />
    </AppProvider>
  );
}
