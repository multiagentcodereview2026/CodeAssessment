import React from 'react';
import {
  LayoutDashboard,
  Code2,
  ListOrdered,
  LineChart,
  MessageSquareText,
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
  Cpu
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const Sidebar: React.FC = () => {
  const { currentRole, currentView, setCurrentView, similarityAlerts } = useApp();

  const studentNavItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'problems', label: 'Problems', icon: Code2 },
    { id: 'submissions', label: 'Submissions', icon: ListOrdered },
    { id: 'scores', label: 'Scores & Analytics', icon: LineChart },
    { id: 'feedback', label: 'Feedback', icon: MessageSquareText },
    { id: 'recommendations', label: 'Recommendations', icon: Lightbulb },
    { id: 'progress', label: 'Progress', icon: TrendingUp },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  const instructorNavItems = [
    { id: 'instructor-dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'instructor-courses', label: 'Courses', icon: BookOpen },
    { id: 'instructor-students', label: 'Students', icon: Users },
    { id: 'instructor-assignments', label: 'Assignments', icon: CalendarCheck },
    { id: 'instructor-problems', label: 'Problem Bank', icon: Code2 },
    { id: 'instructor-analytics', label: 'Class Analytics', icon: BarChart3 },
    {
      id: 'instructor-similarity',
      label: 'Similarity Alerts',
      icon: ShieldAlert,
      badge: similarityAlerts.length > 0 ? similarityAlerts.length : undefined
    },
    { id: 'instructor-reports', label: 'Reports', icon: FileSpreadsheet },
    { id: 'instructor-settings', label: 'Settings', icon: Settings }
  ];

  const navItems = currentRole === 'student' ? studentNavItems : instructorNavItems;

  return (
    <aside className="w-64 flex-shrink-0 bg-white border-r border-slate-200 min-h-[calc(100vh-4rem)] flex flex-col justify-between p-4 hidden md:flex">
      <div className="space-y-6">
        {/* Role identifier badge */}
        <div className="px-3 py-2 bg-slate-50 border border-slate-200/80 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2.5 h-2.5 rounded-full ${currentRole === 'student' ? 'bg-indigo-500' : 'bg-emerald-500'} animate-pulse`} />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              {currentRole} Workspace
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400 bg-white px-1.5 py-0.5 rounded border border-slate-200">
            Active
          </span>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id || (item.id === 'problems' && currentView === 'workspace') || (item.id === 'submissions' && currentView === 'result');

            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/20'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    isActive ? 'bg-white text-indigo-700' : 'bg-rose-100 text-rose-700'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom status box */}
      <div className="pt-4 border-t border-slate-100">
        <div className="p-3 bg-gradient-to-br from-slate-900 to-indigo-950 text-white rounded-xl shadow-xs">
          <div className="flex items-center gap-2 mb-1.5">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-bold text-slate-200">Multi-Agent Engine</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-snug">
            Compiler Sandbox, AST Analysis & Complexity Profiler Ready.
          </p>
          <div className="mt-2.5 flex items-center gap-2 text-[10px] text-emerald-400 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            <span>Sandbox latency: 24ms</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
