import React, { useState } from 'react';
import {
  Sparkles,
  Search,
  Bell,
  ArrowRightLeft,
  ChevronDown,
  LogOut,
  ShieldCheck,
  User
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const Navbar: React.FC = () => {
  const {
    currentUser,
    currentRole,
    switchRole,
    logout,
    setCurrentView,
    similarityAlerts
  } = useApp();

  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200 shadow-xs">
      <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Left: Brand Logo */}
        <div className="flex items-center gap-3">
          <div
            onClick={() => setCurrentView(currentRole === 'student' ? 'dashboard' : 'instructor-dashboard')}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-lg text-slate-900 tracking-tight">
                  Auto<span className="text-indigo-600">Grade</span>
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200 px-1.5 py-0.2 rounded">
                  AI v2.4
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                Intelligent Code Assessment Platform
              </p>
            </div>
          </div>
        </div>

        {/* Center: Search Bar */}
        <div className="hidden md:flex flex-1 max-w-md mx-4">
          <div className="relative w-full">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search problems, topics, submissions, code snippets..."
              className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 hover:bg-slate-100/80 focus:bg-white border border-slate-200 focus:border-indigo-500 rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/10 placeholder:text-slate-400"
            />
          </div>
        </div>

        {/* Right: Role Switcher, Alerts & Profile */}
        <div className="flex items-center gap-3">
          {/* Quick Role Toggle */}
          <button
            onClick={() => switchRole(currentRole === 'student' ? 'instructor' : 'student')}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-700 border border-slate-200 transition-all active:scale-95"
            title={`Switch to ${currentRole === 'student' ? 'Instructor' : 'Student'} view`}
          >
            <ArrowRightLeft className="w-3.5 h-3.5 text-indigo-600" />
            <span className="hidden sm:inline">
              Switch to <strong className="text-indigo-600 capitalize">{currentRole === 'student' ? 'Instructor' : 'Student'}</strong>
            </span>
            <span className="sm:hidden capitalize">{currentRole === 'student' ? 'Inst' : 'Stud'}</span>
          </button>

          {/* Notifications Dropdown */}
          <div className="relative">
            <button
              onClick={() => setNotifOpen(!notifOpen)}
              className="relative p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-600 rounded-full ring-2 ring-white" />
            </button>

            {notifOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-slate-100 py-3 z-50 animate-fadeIn">
                <div className="px-4 pb-2 border-b border-slate-100 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Notifications
                  </span>
                  <span className="text-[10px] text-indigo-600 font-semibold cursor-pointer hover:underline">
                    Mark read
                  </span>
                </div>
                <div className="divide-y divide-slate-50 max-h-64 overflow-y-auto">
                  <div
                    onClick={() => {
                      setCurrentView('dashboard');
                      setNotifOpen(false);
                    }}
                    className="p-3 hover:bg-amber-50/50 text-xs transition-colors cursor-pointer"
                  >
                    <p className="font-semibold text-amber-800 flex items-center gap-1">
                      <GraduationCap className="w-3.5 h-3.5 text-amber-600" /> New Instructor Assignment
                    </p>
                    <p className="text-slate-600 text-[11px] mt-0.5">Prof. Sarah Miller posted "Two Sum" for CSE-301</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">5m ago • Mandatory</span>
                  </div>
                  <div className="p-3 hover:bg-slate-50 text-xs transition-colors cursor-pointer">
                    <p className="font-semibold text-slate-800">Two Sum submission analyzed</p>
                    <p className="text-slate-500 text-[11px] mt-0.5">Scored 85/100 • AI Revision available (+7 pts)</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">10m ago</span>
                  </div>
                  {currentRole === 'instructor' && similarityAlerts.length > 0 && (
                    <div
                      onClick={() => {
                        setCurrentView('instructor-similarity');
                        setNotifOpen(false);
                      }}
                      className="p-3 hover:bg-rose-50/50 text-xs transition-colors cursor-pointer"
                    >
                      <p className="font-semibold text-rose-700 flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5" /> High Similarity Alert (89%)
                      </p>
                      <p className="text-slate-600 text-[11px] mt-0.5">Sai Kiran & Harish N. flagged on Two Sum</p>
                      <span className="text-[10px] text-slate-400 mt-1 block">30m ago</span>
                    </div>
                  )}
                  <div className="p-3 hover:bg-slate-50 text-xs transition-colors cursor-pointer">
                    <p className="font-semibold text-slate-800">DSA Assignment 1 due soon</p>
                    <p className="text-slate-500 text-[11px] mt-0.5">10 May 2026 deadline</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">2h ago</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Pill & Dropdown */}
          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex items-center gap-2.5 p-1.5 pl-2.5 rounded-full hover:bg-slate-100 border border-slate-200 transition-colors"
            >
              <div className="text-left hidden lg:block">
                <div className="text-xs font-bold text-slate-800 leading-tight">
                  {currentUser.name}
                </div>
                <div className="text-[10px] text-slate-500 font-medium capitalize">
                  {currentUser.role}
                </div>
              </div>
              <img
                src={currentUser.avatar}
                alt={currentUser.name}
                className="w-8 h-8 rounded-full object-cover ring-2 ring-indigo-500/20"
              />
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 mr-1" />
            </button>

            {profileOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 z-50 animate-fadeIn">
                <div className="px-4 py-2.5 border-b border-slate-100">
                  <p className="text-xs font-bold text-slate-800">{currentUser.name}</p>
                  <p className="text-[11px] text-slate-500 truncate">{currentUser.email}</p>
                  <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-semibold uppercase bg-indigo-50 text-indigo-700 rounded-md">
                    {currentUser.institution}
                  </span>
                </div>

                <div className="py-1">
                  <button
                    onClick={() => {
                      setCurrentView(currentRole === 'student' ? 'profile' : 'instructor-dashboard');
                      setProfileOpen(false);
                    }}
                    className="w-full px-4 py-2 text-xs text-left font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <User className="w-3.5 h-3.5 text-slate-400" />
                    My Profile & Institution
                  </button>
                  <button
                    onClick={() => {
                      logout();
                      setProfileOpen(false);
                    }}
                    className="w-full px-4 py-2 text-xs text-left font-medium text-rose-600 hover:bg-rose-50 flex items-center gap-2"
                  >
                    <LogOut className="w-3.5 h-3.5 text-rose-500" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
