import { useState, useRef, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Code2,
  BookOpen,
  ListOrdered,
  LineChart,
  MessageSquareText,
  User,
  Settings,
  Bell,
  LogOut,
  ChevronDown,
  BellRing,
  Sun,
  Moon
} from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { useTheme } from '../context/ThemeContext';
import { useNotifications } from '../hooks/useNotifications';
import { motion, AnimatePresence } from 'framer-motion';

const StudentLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();
  const { notifications, unreadCount, notificationError, markRead, markAllRead } = useNotifications();
  
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);

  const profileRef = useRef(null);
  const notifRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'My Courses', path: '/courses', icon: BookOpen },
    { name: 'Problems', path: '/problems', icon: Code2 },
    { name: 'Submissions', path: '/submissions', icon: ListOrdered },
    { name: 'Analytics & Progress', path: '/analytics', icon: LineChart },
    { name: 'Feedback & Insights', path: '/feedback', icon: MessageSquareText },
    { name: 'Profile', path: '/profile', icon: User },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const displayName = user?.name || user?.username || 'Vignesh Reddy';
  const displayId = user?.username || user?.id || '24BD1A058Z';
  const displayEmail = user?.email || '24bd1a058z@geethanjali.edu.in';
  const notificationCount = unreadCount;

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar Navigation */}
      <motion.nav 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="hidden md:flex w-64 bg-white border-r border-slate-200 fixed h-full flex-col z-20"
      >
        <div className="h-16 flex items-center px-6 border-b border-slate-200">
          <div className="bg-indigo-600 p-1.5 rounded-lg mr-2 shadow-sm shadow-indigo-500/30">
            <Code2 className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-slate-800 tracking-tight">Code<span className="text-indigo-600">Vedha</span></span>
        </div>
        
        <div className="flex-1 py-4 px-4 space-y-1 overflow-y-auto custom-scrollbar">
          {navItems.map((item, index) => {
            const isActive = location.pathname === item.path || (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
            return (
              <motion.div
                key={item.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03 }}
              >
                <Link
                  to={item.path}
                  className={`flex items-center px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                    isActive 
                      ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/25' 
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <item.icon className={`w-4 h-4 mr-3 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.name}</span>
                </Link>
              </motion.div>
            );
          })}
        </div>

        <div className="p-4 border-t border-slate-200">
          <button 
            onClick={handleLogout}
            className="flex w-full items-center px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-600 hover:bg-rose-50 hover:text-rose-600 transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4 mr-3 text-slate-400" />
            Sign Out
          </button>
        </div>
      </motion.nav>

      {/* Main Content Area */}
      <div className="md:ml-64 flex min-w-0 flex-1 flex-col min-h-screen">
        <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-8">
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm font-semibold text-slate-700"
          >
            {navItems.find(item => item.path === location.pathname || (item.path !== '/dashboard' && location.pathname.startsWith(item.path)))?.name || 'Overview'}
          </motion.div>
          
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Quick Theme Toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-all cursor-pointer"
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
                aria-label={`Notifications${notificationCount ? `, ${notificationCount} unread` : ''}`}
                aria-expanded={notifOpen}
                className="relative p-2 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-all cursor-pointer"
              >
                <Bell className="w-5 h-5" />
                {notificationCount > 0 && (
                  <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-indigo-600 rounded-full border-2 border-white pulse-glow"></span>
                )}
              </button>

              <AnimatePresence>
                {notifOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-3xl shadow-2xl border border-slate-200/90 p-4 z-50 space-y-3"
                  >
                    <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold text-slate-900">Notifications</span>
                        <span className="px-2 py-0.2 rounded-full bg-indigo-50 text-indigo-700 font-mono text-[10px] font-bold">
                          {notificationCount} New
                        </span>
                      </div>
                      <button
                        onClick={() => {
                          void markAllRead();
                        }}
                        className="text-[11px] font-semibold text-indigo-600 hover:underline cursor-pointer"
                      >
                        Mark all read
                      </button>
                    </div>

                    {notificationError && <p role="alert" className="rounded-lg bg-rose-50 p-2 text-xs text-rose-700">{notificationError}</p>}
                    <div className="max-h-72 space-y-2 overflow-y-auto custom-scrollbar">
                      {notifications.length === 0 ? <p className="py-8 text-center text-xs text-slate-500">No notifications yet.</p> : notifications.map((notification) => <button key={notification.id} onClick={async () => { await markRead(notification.id); setNotifOpen(false); if (notification.target_url) navigate(notification.target_url); }} className={`w-full rounded-2xl border p-3 text-left transition-colors ${notification.is_read ? 'border-slate-200 bg-white hover:bg-slate-50' : 'border-indigo-100 bg-indigo-50/60 hover:bg-indigo-50'}`}><span className="flex items-center gap-2 text-xs font-bold text-slate-800"><BellRing className="h-3.5 w-3.5 text-indigo-600" />{notification.title}</span><span className="mt-1 block text-[11px] leading-relaxed text-slate-600">{notification.message}</span><span className="mt-1 block text-[10px] font-mono text-slate-400">{new Date(notification.created_at).toLocaleString()}</span></button>)}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="h-6 w-px bg-slate-200"></div>

            {/* Profile Dropdown */}
            <div className="relative" ref={profileRef}>
              <button
                type="button"
                onClick={() => setProfileOpen(!profileOpen)}
                aria-label="Open account menu"
                aria-expanded={profileOpen}
                aria-haspopup="true"
                className={`flex items-center cursor-pointer group p-1.5 rounded-2xl transition-colors text-left ${
                  profileOpen ? 'bg-slate-100 dark:bg-slate-800/80' : 'hover:bg-slate-100/80 dark:hover:bg-slate-800/60'
                }`}
              >
                <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-950/80 border border-indigo-200/60 dark:border-indigo-800/60 flex items-center justify-center text-indigo-700 dark:text-indigo-300 font-bold text-sm shadow-inner mr-2.5 group-hover:bg-indigo-200 dark:group-hover:bg-indigo-900/80 transition-colors">
                  {displayName.charAt(0).toUpperCase()}
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{displayName}</span>
                  <span className="text-[10px] font-medium text-slate-400 dark:text-slate-400 font-mono">{displayId}</span>
                </div>
                <ChevronDown className={`w-4 h-4 ml-2 text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-transform ${profileOpen ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {profileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-64 bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200/90 dark:border-slate-800 p-3 z-50 space-y-2 text-xs"
                  >
                    {/* User header */}
                    <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-700/60 space-y-0.5">
                      <span className="font-bold text-slate-900 dark:text-white block">{displayName}</span>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono block truncate">{displayEmail}</span>
                      <span className="inline-block mt-1 px-2.5 py-0.5 rounded-lg text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200/60 dark:border-indigo-500/30 text-indigo-700 dark:text-indigo-300 font-mono">
                        Student ID: {displayId}
                      </span>
                    </div>

                    <div className="pt-1 space-y-1">
                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/profile');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <User className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                        <span>View Profile</span>
                      </button>

                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/submissions');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <ListOrdered className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                        <span>My Submissions</span>
                      </button>

                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/settings');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <Settings className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                        <span>Settings</span>
                      </button>
                    </div>

                    <div className="pt-1 border-t border-slate-100 dark:border-slate-800">
                      <button
                        onClick={handleLogout}
                        className="w-full px-3 py-2 text-left text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <LogOut className="w-4 h-4 text-rose-500" />
                        <span>Sign Out</span>
                      </button>
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

      <nav aria-label="Student navigation" className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur border-t border-slate-200 px-2 py-2 grid grid-cols-5 gap-1">
        {navItems.slice(0, 5).map((item) => {
          const isActive = location.pathname === item.path || (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[10px] font-bold transition-colors ${
                isActive ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:bg-slate-100'
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

export default StudentLayout;
