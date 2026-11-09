import { useState, useRef, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  Users,
  Code2,
  BarChart3,
  ShieldAlert,
  FileSpreadsheet,
  Settings,
  Bell,
  LogOut,
  ChevronDown,
  GraduationCap,
  Sparkles,
  Sun,
  Moon
} from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { useTheme } from '../context/ThemeContext';
import { useNotifications } from '../hooks/useNotifications';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar, SidebarBody, SidebarLink } from '@/components/ui/sidebar';

const InstructorLogo = ({ open }) => (
  <Link
    to="/instructor/dashboard"
    className="flex items-center justify-start gap-3 px-1 py-1 relative z-20 w-full overflow-hidden select-none"
  >
    <div className="w-8 h-8 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/20 shrink-0">
      <GraduationCap className="w-4 h-4" />
    </div>
    <motion.span
      animate={{
        display: open ? "inline-block" : "none",
        opacity: open ? 1 : 0,
      }}
      transition={{ duration: 0.18, ease: "easeInOut" }}
      className="font-bold text-lg text-slate-800 dark:text-white whitespace-pre tracking-tight truncate"
    >
      Kod<span className="text-emerald-600 dark:text-emerald-400">acharya</span>
    </motion.span>
  </Link>
);

const InstructorLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();
  const { notifications, unreadCount, markRead, markAllRead } = useNotifications();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);

  const notifRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems = [
    { name: 'Dashboard', path: '/instructor/dashboard', icon: LayoutDashboard },
    { name: 'Courses', path: '/instructor/courses', icon: BookOpen },
    { name: 'Course Rosters', path: '/instructor/students', icon: Users },
    { name: 'Problem Bank', path: '/instructor/problems', icon: Code2 },
    { name: 'Class Analytics', path: '/instructor/analytics', icon: BarChart3 },
    { name: 'Similarity & Plagiarism', path: '/instructor/similarity', icon: ShieldAlert },
    { name: 'Reports', path: '/instructor/reports', icon: FileSpreadsheet },
    { name: 'Settings', path: '/instructor/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const displayName = user?.name || user?.username || 'Prof. Pavithra K.';
  const displayEmail = user?.email || 'pavithra.k@geethanjali.edu.in';

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-black flex flex-col md:flex-row w-full">
      {/* Modern Expandable Sidebar */}
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen}>
        <SidebarBody className="justify-between gap-6 md:sticky md:top-0 h-screen border-r border-slate-200/80 dark:border-neutral-800/80 bg-white/90 dark:bg-black/95 backdrop-blur-md z-30">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
            <div className="h-14 flex items-center">
              <InstructorLogo open={sidebarOpen} />
            </div>
            
            <div className="mt-4 flex flex-col gap-1">
              {navItems.map((item, idx) => {
                const isActive = location.pathname === item.path || (item.path !== '/instructor/dashboard' && location.pathname.startsWith(item.path));
                const Icon = item.icon;
                return (
                  <SidebarLink
                    key={idx}
                    link={{
                      label: item.name,
                      href: item.path,
                      active: isActive,
                      icon: (
                        <Icon className={`h-5 w-5 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-500 dark:text-neutral-400'}`} />
                      ),
                    }}
                    className={isActive ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-500/25' : ''}
                  />
                );
              })}
            </div>
          </div>

          {/* User profile & Sign Out at bottom of sidebar */}
          <div className="border-t border-slate-200/80 dark:border-neutral-800 pt-3 flex flex-col gap-1 w-full overflow-hidden">
            <SidebarLink
              link={{
                label: displayName,
                href: '/instructor/settings',
                icon: (
                  <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white text-[10px] font-bold shrink-0 shadow-xs">
                    {displayName.charAt(0).toUpperCase()}
                  </div>
                ),
              }}
            />
            <SidebarLink
              link={{
                label: 'Sign Out',
                onClick: handleLogout,
                icon: <LogOut className="w-5 h-5 text-rose-500 shrink-0" />,
              }}
              className="text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30"
            />
          </div>
        </SidebarBody>
      </Sidebar>

      {/* Main Content Area */}
      <div className="flex min-w-0 flex-1 flex-col min-h-screen">
        <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between border-b border-slate-200/80 dark:border-white/10 bg-white/95 dark:bg-black/90 backdrop-blur-md px-4 md:px-8">
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm font-semibold text-slate-700 dark:text-slate-200"
          >
            {navItems.find(item => item.path === location.pathname || (item.path !== '/instructor/dashboard' && location.pathname.startsWith(item.path)))?.name || 'Overview'}
          </motion.div>
          
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Quick Theme Toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/10 transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40"
            >
              {resolvedTheme === 'dark' ? (
                <Sun className="w-5 h-5 text-amber-400" />
              ) : (
                <Moon className="w-5 h-5 text-slate-600" />
              )}
            </button>

            {/* Notifications Dropdown */}
            <div className="relative" ref={notifRef}>
              <button 
                onClick={() => setNotifOpen(!notifOpen)}
                className="relative p-2 rounded-xl text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/10 transition-all cursor-pointer"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-emerald-600 rounded-full border-2 border-white pulse-glow"></span>
                )}
              </button>

              <AnimatePresence>
                {notifOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-[#121217] rounded-3xl shadow-2xl border border-slate-200/90 dark:border-white/12 p-4 z-50 space-y-3"
                  >
                    <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-white/10">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold text-slate-900 dark:text-white">Alerts & Notifications</span>
                        <span className="px-2 py-0.2 rounded-full bg-emerald-50 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 font-mono text-[10px] font-bold">
                          {unreadCount} New
                        </span>
                      </div>
                      <button
                        onClick={() => {
                          void markAllRead();
                        }}
                        className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 hover:underline cursor-pointer"
                      >
                        Mark all read
                      </button>
                    </div>

                    <div className="max-h-72 space-y-2 overflow-y-auto custom-scrollbar">
                      {notifications.length === 0 ? (
                        <p className="py-8 text-center text-xs text-slate-500">No alerts or notifications yet.</p>
                      ) : (
                        notifications.map((n) => (
                          <button
                            key={n.id}
                            onClick={async () => {
                              await markRead(n.id);
                              setNotifOpen(false);
                              if (n.target_url) navigate(n.target_url);
                            }}
                            className={`w-full p-3 rounded-2xl border text-left transition-colors cursor-pointer ${
                              n.is_read
                                ? 'bg-white dark:bg-[#16161d] border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/5'
                                : 'bg-emerald-50/60 dark:bg-emerald-950/40 border-emerald-100 dark:border-emerald-900/40 hover:bg-emerald-50 dark:hover:bg-emerald-950/60'
                            }`}
                          >
                            <span className="text-xs font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                              <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                              {n.title}
                            </span>
                            <span className="block text-[11px] text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                              {n.message}
                            </span>
                            <span className="block text-[10px] font-mono text-slate-400 mt-1">
                              {new Date(n.created_at).toLocaleString()}
                            </span>
                          </button>
                        ))
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </header>

        <main className="relative min-w-0 flex-1 overflow-x-hidden overflow-y-auto p-4 pb-24 custom-scrollbar md:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
              className="mx-auto h-full w-full min-w-0 max-w-7xl"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Mobile quick bottom navigation */}
      <nav aria-label="Instructor navigation" className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-black/95 backdrop-blur border-t border-slate-200 dark:border-white/10 px-2 py-2 grid grid-cols-5 gap-1">
        {navItems.slice(0, 5).map((item) => {
          const isActive = location.pathname === item.path || (item.path !== '/instructor/dashboard' && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[10px] font-bold transition-colors ${
                isActive ? 'bg-emerald-600 text-white' : 'text-slate-500 dark:text-neutral-400 hover:bg-slate-100 dark:hover:bg-white/10'
              }`}
            >
              <item.icon className="w-4 h-4" />
              <span className="truncate max-w-full">{item.name.split(' ')[0]}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
};

export default InstructorLayout;
