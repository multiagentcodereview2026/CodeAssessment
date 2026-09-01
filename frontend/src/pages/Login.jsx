import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { GraduationCap, Code2, Users, ArrowRight, ShieldCheck, Mail, Lock, User, Sparkles, Eye, EyeOff } from 'lucide-react';

const Login = () => {
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [role, setRole] = useState('student');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { login, register } = useAuth();
  const navigate = useNavigate();

  // Auto-fill demo credentials for login mode
  useEffect(() => {
    if (mode === 'login') {
      if (role === 'student') {
        setUsername('demo_student');
        setPassword('demo_student');
      } else {
        setUsername('demo_instructor');
        setPassword('demo_instructor');
      }
    } else {
      setUsername('');
      setPassword('');
      setEmail('');
    }
    setError('');
    setSuccess('');
  }, [role, mode]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    setSuccess('');

    try {
      if (mode === 'register') {
        if (!email) {
          setError('Email is required for registration.');
          setIsSubmitting(false);
          return;
        }
        await register(username, email, password, role);
        setSuccess('Account created! Signing you in...');
        // Auto-login after registration
        const user = await login(username, password, role);
        setTimeout(() => {
          if (role === 'instructor' || user.role === 'instructor') {
            navigate('/instructor/dashboard');
          } else {
            navigate('/dashboard');
          }
        }, 500);
      } else {
        const user = await login(username, password, role);
        if (role === 'instructor' || user.role === 'instructor') {
          navigate('/instructor/dashboard');
        } else {
          navigate('/dashboard');
        }
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const accentColor = role === 'student' ? 'indigo' : 'emerald';

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <motion.div
          animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
          className={`absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full bg-${accentColor}-100/40 blur-3xl`}
        />
        <motion.div
          animate={{ x: [0, -20, 0], y: [0, 30, 0] }}
          transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
          className={`absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full bg-${accentColor}-200/30 blur-3xl`}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-[1000px] bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-slate-200/50 flex flex-col md:flex-row overflow-hidden border border-slate-100/80 relative z-10"
      >
        {/* Left Side: Form */}
        <div className="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="flex items-center space-x-2 mb-10"
          >
            <div className={`p-2 rounded-xl bg-${accentColor}-600 transition-colors duration-500 shadow-lg shadow-${accentColor}-600/30`}>
              <Code2 className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-slate-800 tracking-tight">
              {role === 'student' ? (
                <>Code<span className="text-indigo-600">Vedha</span></>
              ) : (
                <>Kod<span className="text-emerald-600">acharya</span></>
              )}
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h2 className="text-3xl font-bold text-slate-800 mb-2">
              {mode === 'login' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-slate-500 text-sm mb-8">
              {mode === 'login'
                ? 'Sign in to access your AI-powered assessment dashboard.'
                : 'Register to start your coding journey with AI evaluation.'}
            </p>
          </motion.div>

          {/* Role Toggle */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="flex bg-slate-100 p-1 rounded-xl mb-6"
          >
            <button
              onClick={() => setRole('student')}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-300 ${
                role === 'student' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <div className="flex items-center justify-center"><GraduationCap className="w-4 h-4 mr-2" /> Student</div>
            </button>
            <button
              onClick={() => setRole('instructor')}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-300 ${
                role === 'instructor' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <div className="flex items-center justify-center"><Users className="w-4 h-4 mr-2" /> Instructor</div>
            </button>
          </motion.div>

          {/* Login/Register Toggle */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="flex bg-slate-50 p-1 rounded-xl mb-6 border border-slate-200"
          >
            <button
              onClick={() => setMode('login')}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all duration-300 ${
                mode === 'login' ? `bg-${accentColor}-600 text-white shadow-sm` : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setMode('register')}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all duration-300 ${
                mode === 'register' ? `bg-${accentColor}-600 text-white shadow-sm` : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Register
            </button>
          </motion.div>

          <AnimatePresence mode="wait">
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4 text-xs font-semibold text-red-600 bg-red-50 p-3 rounded-lg border border-red-100"
              >
                {error}
              </motion.div>
            )}
            {success && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4 text-xs font-semibold text-emerald-600 bg-emerald-50 p-3 rounded-lg border border-emerald-100 flex items-center"
              >
                <Sparkles className="w-4 h-4 mr-2" /> {success}
              </motion.div>
            )}
          </AnimatePresence>

          <motion.form
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45 }}
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">
                Username
              </label>
              <div className="relative">
                <User className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. demo_student"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 transition-all"
                />
              </div>
            </div>

            <AnimatePresence>
              {mode === 'register' && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="e.g. student@kmit.in"
                      className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 transition-all"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">Password</label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  required
                  className="w-full pl-10 pr-12 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {mode === 'login' && (
              <div className="flex items-center justify-between mt-2">
                <label className="flex items-center cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500" />
                  <span className="ml-2 text-sm text-slate-500">Remember me</span>
                </label>
                <a href="#" className={`text-sm font-medium hover:underline text-${accentColor}-600`}>
                  Forgot password?
                </a>
              </div>
            )}

            <motion.button
              type="submit"
              disabled={isSubmitting}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              className={`w-full py-3.5 rounded-xl text-white font-semibold flex items-center justify-center transition-all shadow-lg cursor-pointer ${
                role === 'student'
                  ? 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-600/30'
                  : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/30'
              } ${isSubmitting ? 'opacity-80' : ''}`}
            >
              {isSubmitting ? (
                <div className="flex items-center">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                  {mode === 'login' ? 'Signing in...' : 'Creating account...'}
                </div>
              ) : (
                <>{mode === 'login' ? 'Sign In' : 'Create Account'} <ArrowRight className="w-4 h-4 ml-2" /></>
              )}
            </motion.button>
          </motion.form>

          <p className="text-center text-xs text-slate-400 mt-6">
            {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
              className={`font-semibold text-${accentColor}-600 hover:underline`}
            >
              {mode === 'login' ? 'Register here' : 'Sign in'}
            </button>
          </p>
        </div>

        {/* Right Side: Showcase */}
        <div className={`hidden md:flex w-1/2 p-12 flex-col justify-between text-white ${
          role === 'student' ? 'bg-indigo-600' : 'bg-emerald-600'
        } transition-colors duration-500 relative overflow-hidden`}>

          <div className="absolute top-0 right-0 -mt-20 -mr-20 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-0 -mb-20 -ml-20 w-64 h-64 bg-black/10 rounded-full blur-3xl"></div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="relative z-10"
          >
            <ShieldCheck className="w-12 h-12 text-white/90 mb-6" />
            <h3 className="text-3xl font-bold mb-4">
              {role === 'student' ? 'Master Algorithms with AI' : 'Explainable AI Grading'}
            </h3>
            <p className="text-white/80 text-lg leading-relaxed">
              {role === 'student'
                ? 'Submit your code and get instant, multi-dimensional feedback from 10 specialized LangGraph agents. Improve your correctness, complexity, and style.'
                : 'Automate code assessments with deep explainability. Track class performance, identify at-risk students, and generate comprehensive reports instantly.'}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
            className="relative z-10 bg-white/10 border border-white/20 p-6 rounded-2xl backdrop-blur-sm"
          >
            <div className="flex items-center space-x-4 mb-4">
              <div className="flex -space-x-2">
                {[1,2,3].map(i => (
                  <div key={i} className="w-8 h-8 rounded-full border-2 border-transparent bg-white/20 flex items-center justify-center text-xs font-bold">
                    User
                  </div>
                ))}
              </div>
              <span className="text-sm font-medium text-white/90">Trusted by KMIT Faculty</span>
            </div>
            <p className="text-sm text-white/70 italic">"The multi-agent feedback is phenomenally accurate and genuinely helps students improve."</p>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
