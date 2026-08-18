import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, Code2, Users, ArrowRight, ShieldCheck, Mail, Lock } from 'lucide-react';

const Login = () => {
  const [role, setRole] = useState('student'); // 'student' or 'instructor'
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  // Effect to automatically fill demo credentials based on role
  useEffect(() => {
    if (role === 'student') {
      setUserId('demo_student');
      setPassword('demo_student');
    } else {
      setUserId('demo_instructor');
      setPassword('demo_instructor');
    }
  }, [role]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const user = await login(userId, role, password);
      if (user.role === 'student') {
        navigate('/dashboard');
      } else {
        navigate('/instructor/dashboard');
      }
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-[1000px] bg-white rounded-3xl shadow-xl flex flex-col md:flex-row overflow-hidden border border-slate-100">
        
        {/* Left Side: Form */}
        <div className="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center">
          <div className="flex items-center space-x-2 mb-10">
            <div className={`p-2 rounded-xl ${role === 'student' ? 'bg-indigo-600' : 'bg-emerald-600'} transition-colors`}>
              <Code2 className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-slate-800 tracking-tight">
              {role === 'student' ? (
                <>Code<span className="text-indigo-600">Vedha</span></>
              ) : (
                <>Kod<span className="text-emerald-600">acharya</span></>
              )}
            </span>
          </div>

          <h2 className="text-3xl font-bold text-slate-800 mb-2">Welcome Back</h2>
          <p className="text-slate-500 text-sm mb-8">Sign in to access your AI-powered assessment dashboard.</p>

          <div className="flex bg-slate-100 p-1 rounded-xl mb-8">
            <button 
              onClick={() => setRole('student')}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all ${
                role === 'student' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <div className="flex items-center justify-center"><GraduationCap className="w-4 h-4 mr-2" /> Student</div>
            </button>
            <button 
              onClick={() => setRole('instructor')}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all ${
                role === 'instructor' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <div className="flex items-center justify-center"><Users className="w-4 h-4 mr-2" /> Instructor</div>
            </button>
          </div>

          {error && <div className="mb-4 text-xs font-semibold text-red-600 bg-red-50 p-3 rounded-lg">{error}</div>}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">
                {role === 'student' ? 'Username / Roll No' : 'Instructor ID'}
              </label>
              <div className="relative">
                <Mail className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="text" 
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder={role === 'student' ? 'e.g. demo_student' : 'e.g. demo_instructor'}
                  required
                  className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">Password</label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={role === 'student' ? 'e.g. demo_student' : 'e.g. demo_instructor'}
                  required
                  className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 transition-all"
                />
              </div>
            </div>

            <div className="flex items-center justify-between mt-2">
              <label className="flex items-center cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500" />
                <span className="ml-2 text-sm text-slate-500">Remember me</span>
              </label>
              <a href="#" className={`text-sm font-medium hover:underline ${role === 'student' ? 'text-indigo-600' : 'text-emerald-600'}`}>
                Forgot password?
              </a>
            </div>

            <button 
              type="submit"
              disabled={isSubmitting}
              className={`w-full py-3.5 rounded-xl text-white font-semibold flex items-center justify-center transition-all shadow-md ${
                role === 'student' 
                  ? 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-600/30' 
                  : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/30'
              }`}
            >
              {isSubmitting ? 'Authenticating...' : 'Sign In'} <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </form>
        </div>

        {/* Right Side: Showcase */}
        <div className={`hidden md:flex w-1/2 p-12 flex-col justify-between text-white ${
          role === 'student' ? 'bg-indigo-600' : 'bg-emerald-600'
        } transition-colors duration-500 relative overflow-hidden`}>
          
          <div className="absolute top-0 right-0 -mt-20 -mr-20 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-0 -mb-20 -ml-20 w-64 h-64 bg-black/10 rounded-full blur-3xl"></div>

          <div className="relative z-10">
            <ShieldCheck className="w-12 h-12 text-white/90 mb-6" />
            <h3 className="text-3xl font-bold mb-4">
              {role === 'student' ? 'Master Algorithms with AI' : 'Explainable AI Grading'}
            </h3>
            <p className="text-white/80 text-lg leading-relaxed">
              {role === 'student' 
                ? 'Submit your code and get instant, multi-dimensional feedback from 10 specialized LangGraph agents. Improve your correctness, complexity, and style.'
                : 'Automate code assessments with deep explainability. Track class performance, identify at-risk students, and generate comprehensive reports instantly.'}
            </p>
          </div>

          <div className="relative z-10 bg-white/10 border border-white/20 p-6 rounded-2xl backdrop-blur-sm">
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
          </div>

        </div>
      </div>
    </div>
  );
};

export default Login;
