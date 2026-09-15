import { useState, useRef, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  BookOpen,
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
  AlertTriangle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

const InstructorLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [unreadNotifs, setUnreadNotifs] = useState(2);

  const profileRef = useRef(null);
  const notifRef = useRef(null);

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
    { name: 'Dashboard', path: '/instructor/dashboard', icon: LayoutDashboard },
    { name: 'Courses', path: '/instructor/courses', icon: BookOpen },
    { name: 'Student Roster', path: '/instructor/students', icon: Users },
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
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar Navigation */}
      <motion.nav 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="hidden md:flex w-64 bg-white border-r border-slate-200 fixed h-full flex-col z-20"
      >
        <div className="h-16 flex items-center px-6 border-b border-slate-200">
          <div className="bg-emerald-600 p-1.5 rounded-lg mr-2 shadow-sm shadow-emerald-500/30">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-slate-800 tracking-tight">Kod<span className="text-emerald-600">acharya</span></span>
        </div>
        
        <div className="flex-1 py-4 px-4 space-y-1 overflow-y-auto custom-scrollbar">
          {navItems.map((item, index) => {
            const isActive = location.pathname === item.path || (item.path !== '/instructor/dashboard' && location.pathname.startsWith(item.path));
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
                      ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-500/25' 
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
      <div className="md:ml-64 flex-1 flex flex-col min-h-screen">
        <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 flex items-center justify-between px-4 md:px-8 sticky top-0 z-30 glass">
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm font-semibold text-slate-700"
          >
            {navItems.find(item => item.path === location.pathname || (item.path !== '/instructor/dashboard' && location.pathname.startsWith(item.path)))?.name || 'Overview'}
          </motion.div>
          
          <div className="flex items-center space-x-5">
            {/* Notifications Dropdown */}
            <div className="relative" ref={notifRef}>
              <button 
                onClick={() => setNotifOpen(!notifOpen)}
                className="relative p-2 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-all cursor-pointer"
              >
                <Bell className="w-5 h-5" />
                {unreadNotifs > 0 && (
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
                    className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-3xl shadow-2xl border border-slate-200/90 p-4 z-50 space-y-3"
                  >
                    <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold text-slate-900">Faculty Alerts</span>
                        <span className="px-2 py-0.2 rounded-full bg-emerald-50 text-emerald-700 font-mono text-[10px] font-bold">
                          {unreadNotifs} New
                        </span>
                      </div>
                      <button
                        onClick={() => setUnreadNotifs(0)}
                        className="text-[11px] font-semibold text-emerald-600 hover:underline cursor-pointer"
                      >
                        Mark all read
                      </button>
                    </div>

                    <div className="space-y-2 text-xs max-h-72 overflow-y-auto custom-scrollbar">
                      <div 
                        onClick={() => {
                          setNotifOpen(false);
                          navigate('/instructor/similarity');
                        }}
                        className="p-3 bg-rose-50/70 hover:bg-rose-50 rounded-2xl border border-rose-100 cursor-pointer transition-colors space-y-1"
                      >
                        <div className="flex items-center gap-2 text-rose-800 font-bold text-xs">
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                          <span>Similarity Alert Flagged</span>
                        </div>
                        <p className="text-rose-700 text-[11px] leading-tight">
                          Two students flagged with 89% AST code token similarity on "Two Sum".
                        </p>
                        <span className="text-[10px] text-slate-400 font-mono">15 mins ago</span>
                      </div>

                      <div 
                        onClick={() => {
                          setNotifOpen(false);
                          navigate('/instructor/problems');
                        }}
                        className="p-3 bg-slate-50 hover:bg-slate-100/80 rounded-2xl border border-slate-200/70 cursor-pointer transition-colors space-y-1"
                      >
                        <div className="flex items-center gap-2 text-slate-800 font-bold text-xs">
                          <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Cohort Submissions Completed</span>
                        </div>
                        <p className="text-slate-600 text-[11px] leading-tight">
                          40 of 48 students submitted Assignment #1 with an average of 78.4%.
                        </p>
                        <span className="text-[10px] text-slate-400 font-mono">1 hour ago</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="h-6 w-px bg-slate-200"></div>

            {/* Profile Dropdown */}
            <div className="relative" ref={profileRef}>
              <div 
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center cursor-pointer group p-1.5 rounded-2xl hover:bg-slate-100/80 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold text-sm shadow-inner mr-2.5 group-hover:bg-emerald-200 transition-colors">
                  {displayName.charAt(0).toUpperCase()}
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-xs font-bold text-slate-700 group-hover:text-emerald-600 transition-colors">{displayName}</span>
                  <span className="text-[10px] font-medium text-slate-400">Faculty Portal</span>
                </div>
                <ChevronDown className={`w-4 h-4 ml-2 text-slate-400 group-hover:text-emerald-600 transition-transform ${profileOpen ? 'rotate-180' : ''}`} />
              </div>

              <AnimatePresence>
                {profileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-64 bg-white rounded-3xl shadow-2xl border border-slate-200/90 p-3 z-50 space-y-2 text-xs"
                  >
                    <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 space-y-0.5">
                      <span className="font-bold text-slate-900 block">{displayName}</span>
                      <span className="text-[11px] text-slate-400 font-mono block truncate">{displayEmail}</span>
                      <span className="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 font-mono">
                        Associate Professor
                      </span>
                    </div>

                    <div className="pt-1 space-y-1">
                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/instructor/courses');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 hover:bg-slate-100 hover:text-emerald-600 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <BookOpen className="w-4 h-4 text-slate-400" />
                        <span>My Courses</span>
                      </button>

                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/instructor/students');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 hover:bg-slate-100 hover:text-emerald-600 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <Users className="w-4 h-4 text-slate-400" />
                        <span>Student Roster</span>
                      </button>

                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/instructor/settings');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 hover:bg-slate-100 hover:text-emerald-600 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <Settings className="w-4 h-4 text-slate-400" />
                        <span>Faculty Settings</span>
                      </button>
                    </div>

                    <div className="pt-1 border-t border-slate-100">
                      <button
                        onClick={handleLogout}
                        className="w-full px-3 py-2 text-left text-rose-600 hover:bg-rose-50 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
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

        <main className="flex-1 p-4 md:p-8 pb-24 overflow-y-auto relative custom-scrollbar">
          <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-emerald-50/50 to-transparent -z-10 pointer-events-none"></div>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
              className="h-full max-w-7xl mx-auto"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur border-t border-slate-200 px-2 py-2 grid grid-cols-5 gap-1">
        {navItems.slice(0, 5).map((item) => {
          const isActive = location.pathname === item.path || (item.path !== '/instructor/dashboard' && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[10px] font-bold transition-colors ${
                isActive ? 'bg-emerald-600 text-white' : 'text-slate-500 hover:bg-slate-100'
              }`}
            >
              <item.icon className="w-4 h-4" />
              <span className="truncate max-w-full">{item.name.split(' ')[0]}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default InstructorLayout;
