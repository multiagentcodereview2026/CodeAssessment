import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { useTheme } from '../context/ThemeContext';
import { SignInPage } from '@/components/ui/sign-in';
import { Code2, Sun, Moon } from 'lucide-react';

const Login = () => {
  const [role, setRole] = useState('student'); // 'student' | 'instructor'
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const { login, register } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleSignIn = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    setSuccess('');

    const formData = new FormData(e.currentTarget);
    const emailOrUsername = (formData.get('email') || '').toString().trim();
    const password = (formData.get('password') || '').toString();
    const username = (formData.get('username') || '').toString().trim();

    try {
      if (mode === 'register') {
        if (!username) {
          setError('Username is required for registration.');
          setIsSubmitting(false);
          return;
        }
        if (!emailOrUsername || !emailOrUsername.includes('@')) {
          setError('A valid email address containing "@" is required for registration.');
          setIsSubmitting(false);
          return;
        }
        if (password.length < 12) {
          setError('Password must be at least 12 characters long.');
          setIsSubmitting(false);
          return;
        }

        await register(username, emailOrUsername, password, 'student');
        setSuccess('Account created successfully! Signing you in...');

        const user = await login(username, password, 'student');
        setTimeout(() => {
          if (user.role === 'instructor') {
            navigate('/instructor/dashboard');
          } else {
            navigate('/dashboard');
          }
        }, 500);
      } else {
        if (!emailOrUsername) {
          setError('Username or email is required.');
          setIsSubmitting(false);
          return;
        }
        if (!password) {
          setError('Password is required.');
          setIsSubmitting(false);
          return;
        }

        const user = await login(emailOrUsername, password, role);
        if (role === 'instructor' || user.role === 'instructor') {
          navigate('/instructor/dashboard');
        } else {
          navigate('/dashboard');
        }
      }
    } catch (err) {
      const message = err.message || 'Authentication failed. Please check your credentials.';
      setError(
        mode === 'login' && message === 'Invalid credentials'
          ? 'Sign-in failed. Check your username/email, password, and selected account role. If you are new, click Create Account.'
          : message
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = () => {
    alert(
      "Password Reset: Please contact your lab coordinator or institutional administrator at admin@kmit.in to reset your portal password."
    );
  };

  // Branding Title based on Role and Mode
  const getTitle = () => {
    if (mode === 'register') {
      return (
        <span className="font-semibold text-foreground tracking-tight">
          Join <span className="text-indigo-600 dark:text-indigo-400">CodeVedha</span>
        </span>
      );
    }
    if (role === 'instructor') {
      return (
        <span className="font-semibold text-foreground tracking-tight">
          Welcome to <span className="text-emerald-600 dark:text-emerald-400">Kodacharya</span>
        </span>
      );
    }
    return (
      <span className="font-semibold text-foreground tracking-tight">
        Welcome to <span className="text-indigo-600 dark:text-indigo-400">CodeVedha</span>
      </span>
    );
  };

  const getDescription = () => {
    if (mode === 'register') {
      return "Register your student account to begin your AI-evaluated algorithmic mastery.";
    }
    if (role === 'instructor') {
      return "Access explainable AI grading rubrics, live class analytics, and assignments.";
    }
    return "Sign in to access your multi-agent AI programming assessment dashboard.";
  };

  const brandingLogo = (
    <div className="flex items-center gap-3">
      <div className={`p-2.5 rounded-2xl ${
        role === 'student' ? 'bg-indigo-600 text-white shadow-indigo-600/30' : 'bg-emerald-600 text-white shadow-emerald-600/30'
      } shadow-lg transition-colors`}>
        <Code2 className="w-6 h-6" />
      </div>
      <div>
        <div className="text-xl font-bold tracking-tight text-foreground flex items-center gap-1.5">
          {role === 'student' ? (
            <>
              Code<span className="text-indigo-600 dark:text-indigo-400">Vedha</span>
            </>
          ) : (
            <>
              Kod<span className="text-emerald-600 dark:text-emerald-400">acharya</span>
            </>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          {role === 'student' ? 'Intelligent Code Assessment Platform' : 'Instructor Evaluation Portal'}
        </p>
      </div>
    </div>
  );

  const topRightElement = (
    <button
      type="button"
      onClick={toggleTheme}
      title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
      aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
      className="p-3 rounded-2xl border border-border bg-card/80 backdrop-blur-md text-foreground hover:bg-secondary shadow-sm transition-all cursor-pointer flex items-center justify-center"
    >
      {resolvedTheme === 'dark' ? (
        <Sun className="w-4 h-4 text-amber-400" />
      ) : (
        <Moon className="w-4 h-4 text-slate-700" />
      )}
    </button>
  );

  return (
    <SignInPage
      title={getTitle()}
      description={getDescription()}
      heroImageSrc="https://cdn.21st.dev/assets/mirror/ec/ecff1664e7fc3185d0e947571f984ea5fa3de9580fb0e73a03cd9c9b3461cb09.jpg"
      onSignIn={handleSignIn}
      onResetPassword={handleResetPassword}
      mode={mode}
      onToggleMode={(newMode) => {
        setMode(newMode);
        setError('');
        setSuccess('');
      }}
      role={role}
      onRoleChange={(newRole) => {
        setRole(newRole);
        setError('');
        setSuccess('');
      }}
      error={error}
      success={success}
      isSubmitting={isSubmitting}
      topRightElement={topRightElement}
      brandingLogo={brandingLogo}
    />
  );
};

export default Login;
