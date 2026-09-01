import React, { useState, useRef, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
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
  Bell,
  LogOut,
  ChevronDown,
  Sparkles,
  CheckCircle2,
  Clock,
  ExternalLink,
  ShieldCheck,
  X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

const StudentLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [unreadNotifs, setUnreadNotifs] = useState(3);

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

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar Navigation */}
      <motion.nav 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="w-64 bg-white border-r border-slate-200 fixed h-full flex flex-col z-20"
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
      <div className="ml-64 flex-1 flex flex-col min-h-screen">
        <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-30 glass">
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm font-semibold text-slate-700"
          >
            {navItems.find(item => item.path === location.pathname || (item.path !== '/dashboard' && location.pathname.startsWith(item.path)))?.name || 'Overview'}
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
                          {unreadNotifs} New
                        </span>
                      </div>
                      <button
                        onClick={() => setUnreadNotifs(0)}
                        className="text-[11px] font-semibold text-indigo-600 hover:underline cursor-pointer"
                      >
                        Mark all read
                      </button>
                    </div>

                    <div className="space-y-2 text-xs max-h-72 overflow-y-auto custom-scrollbar">
                      <div 
                        onClick={() => {
                          setNotifOpen(false);
                          navigate('/result');
                        }}
                        className="p-3 bg-indigo-50/50 hover:bg-indigo-50 rounded-2xl border border-indigo-100 cursor-pointer transition-colors space-y-1"
                      >
                        <div className="flex items-center gap-2 text-indigo-700 font-bold text-xs">
                          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                          <span>AI Evaluation Complete</span>
                        </div>
                        <p className="text-slate-600 text-[11px] leading-tight">
                          "Two Sum" scored 85/100 with optimal O(n) hash map complexity.
                        </p>
                        <span className="text-[10px] text-slate-400 font-mono">10 mins ago</span>
                      </div>

                      <div 
                        onClick={() => {
                          setNotifOpen(false);
                          navigate('/problems');
                        }}
                        className="p-3 bg-slate-50 hover:bg-slate-100/80 rounded-2xl border border-slate-200/70 cursor-pointer transition-colors space-y-1"
                      >
                        <div className="flex items-center gap-2 text-slate-800 font-bold text-xs">
                          <Clock className="w-3.5 h-3.5 text-amber-500" />
                          <span>Assignment Deadline Approaching</span>
                        </div>
                        <p className="text-slate-600 text-[11px] leading-tight">
                          "Binary Search & Tree Traversals" due in 3 days.
                        </p>
                        <span className="text-[10px] text-slate-400 font-mono">2 hours ago</span>
                      </div>

                      <div 
                        onClick={() => {
                          setNotifOpen(false);
                          navigate('/feedback');
                        }}
                        className="p-3 bg-slate-50 hover:bg-slate-100/80 rounded-2xl border border-slate-200/70 cursor-pointer transition-colors space-y-1"
                      >
                        <div className="flex items-center gap-2 text-slate-800 font-bold text-xs">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Mentor Feedback Published</span>
                        </div>
                        <p className="text-slate-600 text-[11px] leading-tight">
                          Instructor reviewed your Reverse Linked List submission.
                        </p>
                        <span className="text-[10px] text-slate-400 font-mono">Yesterday</span>
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
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm shadow-inner mr-2.5 group-hover:bg-indigo-200 transition-colors">
                  {displayName.charAt(0).toUpperCase()}
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-xs font-bold text-slate-700 group-hover:text-indigo-600 transition-colors">{displayName}</span>
                  <span className="text-[10px] font-medium text-slate-400 font-mono">{displayId}</span>
                </div>
                <ChevronDown className={`w-4 h-4 ml-2 text-slate-400 group-hover:text-indigo-600 transition-transform ${profileOpen ? 'rotate-180' : ''}`} />
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
                    {/* User header */}
                    <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100 space-y-0.5">
                      <span className="font-bold text-slate-900 block">{displayName}</span>
                      <span className="text-[11px] text-slate-400 font-mono block truncate">{displayEmail}</span>
                      <span className="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800 font-mono">
                        Student ID: {displayId}
                      </span>
                    </div>

                    <div className="pt-1 space-y-1">
                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/profile');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 hover:bg-slate-100 hover:text-indigo-600 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <User className="w-4 h-4 text-slate-400" />
                        <span>View Profile</span>
                      </button>

                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/submissions');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 hover:bg-slate-100 hover:text-indigo-600 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <ListOrdered className="w-4 h-4 text-slate-400" />
                        <span>My Submissions</span>
                      </button>

                      <button
                        onClick={() => {
                          setProfileOpen(false);
                          navigate('/settings');
                        }}
                        className="w-full px-3 py-2 text-left text-slate-700 hover:bg-slate-100 hover:text-indigo-600 rounded-xl font-semibold flex items-center gap-2.5 transition-colors cursor-pointer"
                      >
                        <Settings className="w-4 h-4 text-slate-400" />
                        <span>Settings</span>
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

        <main className="flex-1 p-8 overflow-y-auto relative custom-scrollbar">
          <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-indigo-50/50 to-transparent -z-10 pointer-events-none"></div>
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
    </div>
  );
};

export default StudentLayout;
