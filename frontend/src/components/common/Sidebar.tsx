import React from 'react';
import {
  LayoutDashboard,
  Code2,
  ListOrdered,
  LineChart,
  Lightbulb,
  TrendingUp,
  User,
  Settings,
  Users,
  CalendarCheck,
  BarChart3,
  ShieldAlert,
  FileSpreadsheet,
  BookOpen,
  GraduationCap,
  Sparkles,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const Sidebar: React.FC = () => {
  const {
    currentRole,
    currentView,
    setCurrentView,
    similarityAlerts,
    mobileMenuOpen,
    setMobileMenuOpen
  } = useApp();

  const handleNavClick = (viewId: string) => {
    setCurrentView(viewId);
    setMobileMenuOpen(false);
  };

  const studentNavItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'problems', label: 'Problem Bank', icon: Code2 },
    { id: 'submissions', label: 'Submissions', icon: ListOrdered },
    { id: 'scores', label: 'Problem Scores', icon: LineChart },
    { id: 'progress', label: 'Learning Progress', icon: TrendingUp },
    { id: 'recommendations', label: 'AI Recommendations', icon: Lightbulb },
    { id: 'profile', label: 'Profile', icon: User }
  ];

  // Essential, focused instructor navigation items (Only 5 core items)
  const instructorNavItems = [
    { id: 'instructor-dashboard', label: 'Dashboard Overview', icon: LayoutDashboard },
    { id: 'instructor-assignments', label: 'Assign Questions', icon: CalendarCheck },
    { id: 'instructor-submissions', label: 'Submissions & Feedback', icon: FileSpreadsheet },
    { id: 'instructor-students', label: 'Assigned Students (48)', icon: Users },
    {
      id: 'instructor-analytics',
      label: 'Class Analytics & Plagiarism',
      icon: BarChart3,
      badge: similarityAlerts.length > 0 ? similarityAlerts.length : undefined
    }
  ];

  const navContent = (
    <div className="flex flex-col justify-between h-full p-4 text-xs">
      <div className="space-y-6">
        {/* Mobile Header with close button */}
        <div className="flex md:hidden items-center justify-between pb-3 border-b border-slate-100">
          <span className="font-extrabold text-sm text-slate-800">
            Navigation Menu
          </span>
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Role badge */}
        <div className="px-3.5 py-2.5 bg-slate-50 border border-slate-200/80 rounded-2xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${currentRole === 'student' ? 'bg-indigo-600' : 'bg-emerald-600'}`} />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
              {currentRole === 'student' ? 'Student Workspace' : 'Instructor Portal'}
            </span>
          </div>
          <span className="text-[10px] font-mono font-bold text-slate-500 bg-white px-2 py-0.5 rounded-lg border border-slate-200">
            {currentRole === 'student' ? 'CSE-301' : '48 Cohort'}
          </span>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1.5">
          {(currentRole === 'student' ? studentNavItems : instructorNavItems).map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id || (item.id === 'problems' && currentView === 'workspace') || (item.id === 'submissions' && currentView === 'result');

            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold transition-all cursor-pointer ${
                  isActive
                    ? currentRole === 'student'
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'bg-emerald-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                    isActive ? 'bg-white text-rose-700' : 'bg-rose-100 text-rose-700'
                  }`}>
                    {item.badge} Alert
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer status */}
      <div className="pt-4 border-t border-slate-100">
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-[11px] text-slate-500">
          <div className="flex items-center gap-1.5 font-bold text-slate-800 mb-0.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>AI Multi-Agent Active</span>
          </div>
          <p className="text-[10px] text-slate-400">
            {currentRole === 'student' ? 'AutoGrade Sandbox Ready' : '48 Student Gradebook Synced'}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <aside className="w-60 flex-shrink-0 bg-white border-r border-slate-200/80 min-h-[calc(100vh-4rem)] hidden md:block">
        {navContent}
      </aside>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex animate-fadeIn">
          <div
            onClick={() => setMobileMenuOpen(false)}
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs"
          />
          <div className="relative w-72 max-w-[85vw] bg-white h-full shadow-2xl z-10 animate-slideRight">
            {navContent}
          </div>
        </div>
      )}
    </>
  );
};
