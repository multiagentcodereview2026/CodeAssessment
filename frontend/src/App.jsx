import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProblemList from './pages/ProblemList';
import CodeEditor from './pages/CodeEditor';
import SubmissionResult from './pages/SubmissionResult';
import StudentLayout from './layouts/StudentLayout';
import InstructorLayout from './layouts/InstructorLayout';
import InstructorDashboard from './pages/InstructorDashboard';
import StudentSubmissions from './pages/StudentSubmissions';
import StudentAnalytics from './pages/StudentAnalytics';
import StudentProfile from './pages/StudentProfile';
import InstructorTablePage from './pages/InstructorTablePage';
import InstructorReports from './pages/InstructorReports';
import SettingsPage from './pages/SettingsPage';

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

const mockCourses = [
  { id: 'CS101', name: 'Intro to Programming', students: 120, avgScore: '78%' },
  { id: 'CS201', name: 'Data Structures & Algorithms', students: 85, avgScore: '89%' },
  { id: 'CS301', name: 'Advanced Algorithms', students: 48, avgScore: '81%' },
];

const mockStudents = [
  { id: '24BD1A058Z', name: 'Vignesh (24BD1A058Z)', course: 'Data Structures', grade: 'A', status: 'Active' },
  { id: '24BD1A0586', name: 'Mani Greeva (24BD1A0586)', course: 'Data Structures', grade: 'A-', status: 'Active' },
  { id: '24BD1A058K', name: 'Nayaneesh (24BD1A058K)', course: 'Algorithms', grade: 'B+', status: 'Active' },
  { id: '24BD1A058V', name: 'Pavan (24BD1A058V)', course: 'Algorithms', grade: 'B', status: 'At Risk' },
  { id: '24BD1A059V', name: 'Karthikeya (24BD1A059V)', course: 'Intro to Programming', grade: 'A', status: 'Active' },
];

const mockAssignments = [
  { title: 'Array Manipulation & Two Sum', course: 'CS201', dueDate: '10 May, 2026', subs: '80 / 85' },
  { title: 'Binary Search & Tree Traversals', course: 'CS301', dueDate: '15 May, 2026', subs: '40 / 48' },
  { title: 'Stack & Valid Parentheses', course: 'CS201', dueDate: '20 May, 2026', subs: '48 / 48' },
];

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      {/* Student Routes */}
      <Route path="/" element={<ProtectedStudentRoute />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="problems" element={<ProblemList />} />
        <Route path="problems/:id" element={<CodeEditor />} />
        <Route path="submissions" element={<StudentSubmissions />} />
        <Route path="submissions/:id" element={<SubmissionResult />} />
        <Route path="analytics" element={<StudentAnalytics />} />
        <Route path="profile" element={<StudentProfile />} />
        <Route path="settings" element={<SettingsPage role="student" />} />
      </Route>

      {/* Instructor Routes */}
      <Route path="/instructor" element={<ProtectedInstructorRoute />}>
        <Route index element={<Navigate to="/instructor/dashboard" replace />} />
        <Route path="dashboard" element={<InstructorDashboard />} />
        <Route path="courses" element={
          <InstructorTablePage title="Course Management" description="Manage your assigned courses and curriculums." columns={['Course Code', 'Course Name', 'Enrolled', 'Avg Score']} data={mockCourses} />
        } />
        <Route path="students" element={
          <InstructorTablePage title="Student Roster" description="View and manage student performance." columns={['Roll No', 'Name', 'Course', 'Grade', 'Status']} data={mockStudents} />
        } />
        <Route path="assignments" element={
          <InstructorTablePage title="Assignments" description="Create and grade coding assignments." columns={['Title', 'Course', 'Due Date', 'Submissions']} data={mockAssignments} />
        } />
        <Route path="reports" element={<InstructorReports />} />
        <Route path="settings" element={<SettingsPage role="instructor" />} />
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;
