import React, { useState } from 'react';
import {
  Sparkles,
  Lock,
  Mail,
  ArrowRight,
  GraduationCap,
  Briefcase,
  Layers,
  Cpu,
  ShieldAlert
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { Role } from '../../types';

export const AuthPage: React.FC = () => {
  const { login } = useApp();
  const [selectedRole, setSelectedRole] = useState<Role>('student');
  const [email, setEmail] = useState('student@example.com');
  const [password, setPassword] = useState('••••••••••••');
  const [isRegister, setIsRegister] = useState(false);

  const handleRoleChange = (role: Role) => {
    setSelectedRole(role);
    setEmail(role === 'student' ? 'student@example.com' : 'instructor@university.edu');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login(selectedRole);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background glowing accents */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-xl shadow-indigo-500/25 mb-4">
          <Sparkles className="w-7 h-7 text-white" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-white">
          AutoGrade <span className="text-indigo-400">AI</span>
        </h2>
        <p className="mt-1.5 text-sm text-slate-400">
          Autonomous Code Assessment & Explainable AI Learning Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl relative z-10 px-4">
        <div className="bg-slate-800/90 backdrop-blur-md py-8 px-6 sm:px-10 rounded-3xl border border-slate-700/80 shadow-2xl">
          {/* Header text */}
          <div className="text-center mb-6">
            <h3 className="text-xl font-bold text-white">
              {isRegister ? 'Create an Account' : 'Welcome Back! 👋'}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              {isRegister ? 'Join your cohort and accelerate your coding mastery' : 'Sign in to continue your assessment workspace'}
            </p>
          </div>

          {/* Role selector pill */}
          <div className="grid grid-cols-2 gap-2 p-1.5 bg-slate-900/80 rounded-2xl border border-slate-700/60 mb-6">
            <button
              type="button"
              onClick={() => handleRoleChange('student')}
              className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold transition-all ${
                selectedRole === 'student'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              Student
            </button>
            <button
              type="button"
              onClick={() => handleRoleChange('instructor')}
              className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold transition-all ${
                selectedRole === 'instructor'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              Instructor
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Institutional Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder={selectedRole === 'student' ? 'student@example.com' : 'instructor@university.edu'}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-slate-700 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all font-mono"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-300">Password</label>
                {!isRegister && (
                  <button
                    type="button"
                    className="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    Forgot Password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-slate-700 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all active:scale-[0.99] cursor-pointer"
            >
              <span>{isRegister ? 'Create Account & Start' : 'Sign In to Workspace'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Switch Register/Login */}
          <div className="mt-6 text-center text-xs text-slate-400">
            {isRegister ? (
              <p>
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => setIsRegister(false)}
                  className="text-indigo-400 font-bold hover:underline"
                >
                  Sign In
                </button>
              </p>
            ) : (
              <p>
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => setIsRegister(true)}
                  className="text-indigo-400 font-bold hover:underline"
                >
                  Register
                </button>
              </p>
            )}
          </div>

          {/* Multi-Agent Feature Pills */}
          <div className="mt-8 pt-6 border-t border-slate-700/60 grid grid-cols-3 gap-3 text-center">
            <div className="p-2.5 bg-slate-900/50 rounded-xl border border-slate-700/50">
              <Cpu className="w-4 h-4 text-indigo-400 mx-auto mb-1" />
              <p className="text-[10px] font-bold text-slate-300">AST Profiler</p>
              <p className="text-[9px] text-slate-500">O(N) Complexity</p>
            </div>
            <div className="p-2.5 bg-slate-900/50 rounded-xl border border-slate-700/50">
              <Layers className="w-4 h-4 text-purple-400 mx-auto mb-1" />
              <p className="text-[10px] font-bold text-slate-300">5D Rubric</p>
              <p className="text-[9px] text-slate-500">Multi-Agent</p>
            </div>
            <div className="p-2.5 bg-slate-900/50 rounded-xl border border-slate-700/50">
              <ShieldAlert className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
              <p className="text-[10px] font-bold text-slate-300">Plagiarism Shield</p>
              <p className="text-[9px] text-slate-500">Cohort Match</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
