import React, { useState } from 'react';
import { Eye, EyeOff, GraduationCap, Users } from 'lucide-react';

// --- HELPER COMPONENTS (ICONS) ---

export const GoogleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 48 48">
    <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8-6.627 0-12-5.373-12-12s12-5.373 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-2.641-.21-5.236-.611-7.743z" />
    <path fill="#FF3D00" d="M6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 16.318 4 9.656 8.337 6.306 14.691z" />
    <path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238C29.211 35.091 26.715 36 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z" />
    <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303c-.792 2.237-2.231 4.166-4.087 5.571l6.19 5.238C42.022 35.026 44 30.038 44 24c0-2.641-.21-5.236-.611-7.743z" />
  </svg>
);

// --- TYPE DEFINITIONS ---

export interface Testimonial {
  avatarSrc: string;
  name: string;
  handle: string;
  text: string;
}

export interface SignInPageProps {
  title?: React.ReactNode;
  description?: React.ReactNode;
  heroImageSrc?: string;
  testimonials?: Testimonial[];
  onSignIn?: (event: React.FormEvent<HTMLFormElement>) => void;
  onGoogleSignIn?: () => void;
  onResetPassword?: () => void;
  onCreateAccount?: () => void;
  // Optional enhancements for project integration
  mode?: 'login' | 'register';
  onToggleMode?: (mode: 'login' | 'register') => void;
  role?: 'student' | 'instructor';
  onRoleChange?: (role: 'student' | 'instructor') => void;
  error?: string;
  success?: string;
  isSubmitting?: boolean;
  topRightElement?: React.ReactNode;
  brandingLogo?: React.ReactNode;
}

// --- SUB-COMPONENTS ---

export const GlassInputWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="rounded-2xl border border-border bg-foreground/5 backdrop-blur-sm transition-colors focus-within:border-violet-400/70 focus-within:bg-violet-500/10">
    {children}
  </div>
);

export const TestimonialCard = ({ testimonial, delay }: { testimonial: Testimonial; delay: string }) => (
  <div className={`animate-testimonial ${delay} flex items-start gap-3 rounded-3xl bg-card/40 dark:bg-zinc-800/40 backdrop-blur-xl border border-white/10 p-5 w-64 shadow-xl`}>
    <img src={testimonial.avatarSrc} className="h-10 w-10 object-cover rounded-2xl shrink-0 border border-white/20" alt="avatar" />
    <div className="text-sm leading-snug min-w-0">
      <p className="flex items-center gap-1 font-medium truncate text-white dark:text-zinc-100">{testimonial.name}</p>
      <p className="text-white/70 dark:text-zinc-400 text-xs truncate">{testimonial.handle}</p>
      <p className="mt-1 text-white/90 dark:text-zinc-300 text-xs line-clamp-3">{testimonial.text}</p>
    </div>
  </div>
);

// --- MAIN COMPONENT ---

export const SignInPage: React.FC<SignInPageProps> = ({
  title = <span className="font-light text-foreground tracking-tighter">Welcome</span>,
  description = "Access your account and continue your journey with us",
  heroImageSrc,
  testimonials = [],
  onSignIn,
  onGoogleSignIn,
  onResetPassword,
  onCreateAccount,
  mode = 'login',
  onToggleMode,
  role,
  onRoleChange,
  error,
  success,
  isSubmitting = false,
  topRightElement,
  brandingLogo,
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const handleCreateAccountClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onToggleMode) {
      onToggleMode(mode === 'login' ? 'register' : 'login');
    }
    onCreateAccount?.();
  };

  return (
    <div className="min-h-[100dvh] flex flex-col md:flex-row font-geist w-full bg-background text-foreground relative">
      {/* Top right floating accessories (e.g. Theme toggle) */}
      {topRightElement && (
        <div className="absolute top-4 right-4 z-30">
          {topRightElement}
        </div>
      )}

      {/* Left column: sign-in / registration form */}
      <section className="flex-1 flex items-center justify-center p-6 sm:p-10 lg:p-12 relative z-10">
        <div className="w-full max-w-md">
          <div className="flex flex-col gap-6">
            
            {/* Branding Logo / Header */}
            {brandingLogo && (
              <div className="animate-element animate-delay-100">
                {brandingLogo}
              </div>
            )}

            {/* Role Switcher Tabs (if role & onRoleChange are passed) */}
            {role && onRoleChange && (
              <div className="animate-element animate-delay-100 flex p-1.5 rounded-2xl bg-foreground/5 border border-border backdrop-blur-sm">
                <button
                  type="button"
                  onClick={() => onRoleChange('student')}
                  className={`flex-1 py-2.5 px-3 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                    role === 'student'
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <GraduationCap className="w-4 h-4" />
                  <span>Student</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onRoleChange('instructor');
                    if (mode === 'register' && onToggleMode) onToggleMode('login');
                  }}
                  className={`flex-1 py-2.5 px-3 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                    role === 'instructor'
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Users className="w-4 h-4" />
                  <span>Instructor</span>
                </button>
              </div>
            )}

            {/* Title & Description */}
            <div className="flex flex-col gap-2">
              <h1 className="animate-element animate-delay-100 text-4xl md:text-5xl font-semibold leading-tight">{title}</h1>
              <p className="animate-element animate-delay-200 text-muted-foreground text-sm sm:text-base">{description}</p>
            </div>

            {/* Error Message Alert */}
            {error && (
              <div className="animate-element animate-delay-200 text-xs font-semibold text-rose-500 bg-rose-500/10 border border-rose-500/20 p-3.5 rounded-2xl">
                {error}
              </div>
            )}

            {/* Success Message Alert */}
            {success && (
              <div className="animate-element animate-delay-200 text-xs font-semibold text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 p-3.5 rounded-2xl">
                {success}
              </div>
            )}

            {/* Form */}
            <form className="space-y-4" onSubmit={onSignIn}>
              {mode === 'register' ? (
                <>
                  <div className="animate-element animate-delay-300">
                    <label className="text-sm font-medium text-muted-foreground block mb-1.5">Username</label>
                    <GlassInputWrapper>
                      <input
                        name="username"
                        type="text"
                        required
                        placeholder="Choose a username (e.g. roll_number)"
                        className="w-full bg-transparent text-sm p-4 rounded-2xl focus:outline-none text-foreground placeholder:text-muted-foreground/60"
                      />
                    </GlassInputWrapper>
                  </div>

                  <div className="animate-element animate-delay-350">
                    <label className="text-sm font-medium text-muted-foreground block mb-1.5">Email Address</label>
                    <GlassInputWrapper>
                      <input
                        name="email"
                        type="email"
                        required
                        placeholder="Enter your student email"
                        className="w-full bg-transparent text-sm p-4 rounded-2xl focus:outline-none text-foreground placeholder:text-muted-foreground/60"
                      />
                    </GlassInputWrapper>
                  </div>
                </>
              ) : (
                <div className="animate-element animate-delay-300">
                  <label className="text-sm font-medium text-muted-foreground block mb-1.5">
                    {role === 'instructor' ? 'Instructor ID or Email' : 'Email Address or Username'}
                  </label>
                  <GlassInputWrapper>
                    <input
                      name="email"
                      type="text"
                      required
                      placeholder={role === 'instructor' ? 'Enter instructor username or email' : 'Enter your email or username'}
                      className="w-full bg-transparent text-sm p-4 rounded-2xl focus:outline-none text-foreground placeholder:text-muted-foreground/60"
                    />
                  </GlassInputWrapper>
                </div>
              )}

              <div className="animate-element animate-delay-400">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm font-medium text-muted-foreground block">Password</label>
                  {mode === 'register' && (
                    <span className="text-[11px] text-muted-foreground/80 font-medium">Min 12 characters</span>
                  )}
                </div>
                <GlassInputWrapper>
                  <div className="relative">
                    <input
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      placeholder={mode === 'register' ? 'Create a strong password (min 12 chars)' : 'Enter your password'}
                      className="w-full bg-transparent text-sm p-4 pr-12 rounded-2xl focus:outline-none text-foreground placeholder:text-muted-foreground/60"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-3 flex items-center cursor-pointer text-muted-foreground hover:text-foreground transition-colors"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </GlassInputWrapper>
              </div>

              {mode === 'login' && (
                <div className="animate-element animate-delay-500 flex items-center justify-between text-sm">
                  <label className="flex items-center gap-3 cursor-pointer select-none">
                    <input type="checkbox" name="rememberMe" className="custom-checkbox" />
                    <span className="text-foreground/90 text-sm">Keep me signed in</span>
                  </label>
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      onResetPassword?.();
                    }}
                    className="hover:underline text-violet-500 hover:text-violet-400 transition-colors text-sm font-medium"
                  >
                    Reset password
                  </a>
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className={`animate-element animate-delay-600 w-full rounded-2xl py-4 font-medium transition-all cursor-pointer shadow-md disabled:opacity-70 flex items-center justify-center gap-2 ${
                  role === 'instructor'
                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20'
                    : 'bg-primary hover:bg-primary/90 text-primary-foreground shadow-primary/20'
                }`}
              >
                {isSubmitting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>{mode === 'register' ? 'Creating account...' : 'Signing in...'}</span>
                  </>
                ) : (
                  <span>{mode === 'register' ? 'Create Account' : 'Sign In'}</span>
                )}
              </button>
            </form>

            {mode === 'login' && (
              <>
                <div className="animate-element animate-delay-700 relative flex items-center justify-center my-1">
                  <span className="w-full border-t border-border"></span>
                  <span className="px-4 text-xs uppercase tracking-wider text-muted-foreground bg-background absolute">Or continue with</span>
                </div>

                <button
                  type="button"
                  onClick={onGoogleSignIn}
                  className="animate-element animate-delay-800 w-full flex items-center justify-center gap-3 border border-border rounded-2xl py-4 hover:bg-secondary transition-colors cursor-pointer text-foreground font-medium text-sm shadow-xs"
                >
                  <GoogleIcon />
                  Continue with Google
                </button>
              </>
            )}

            {/* Toggle between Login and Register (for students) */}
            {role !== 'instructor' && (
              <p className="animate-element animate-delay-900 text-center text-sm text-muted-foreground">
                {mode === 'login' ? (
                  <>
                    New to our platform?{' '}
                    <a
                      href="#"
                      onClick={handleCreateAccountClick}
                      className="text-violet-500 hover:text-violet-400 hover:underline font-medium transition-colors"
                    >
                      Create Account
                    </a>
                  </>
                ) : (
                  <>
                    Already have an account?{' '}
                    <a
                      href="#"
                      onClick={handleCreateAccountClick}
                      className="text-violet-500 hover:text-violet-400 hover:underline font-medium transition-colors"
                    >
                      Sign In
                    </a>
                  </>
                )}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Right column: hero image + testimonials */}
      {heroImageSrc && (
        <section className="hidden md:block flex-1 relative p-4 min-h-[500px]">
          <div
            className="animate-slide-right animate-delay-300 absolute inset-4 rounded-3xl bg-cover bg-center overflow-hidden"
            style={{ backgroundImage: `url(${heroImageSrc})` }}
          >
            {/* Subtle gradient vignette to ensure testimonial cards pop */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-black/10 rounded-3xl pointer-events-none" />
          </div>
          {testimonials.length > 0 && (
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-4 px-6 w-full justify-center z-10">
              <TestimonialCard testimonial={testimonials[0]} delay="animate-delay-1000" />
              {testimonials[1] && (
                <div className="hidden xl:flex">
                  <TestimonialCard testimonial={testimonials[1]} delay="animate-delay-1200" />
                </div>
              )}
              {testimonials[2] && (
                <div className="hidden 2xl:flex">
                  <TestimonialCard testimonial={testimonials[2]} delay="animate-delay-1400" />
                </div>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export default SignInPage;

// --- DEMO IMPLEMENTATION & SAMPLE DATA ---

export const sampleTestimonials: Testimonial[] = [
  {
    avatarSrc: "https://cdn.21st.dev/assets/mirror/9f/9f797e4acee1a4de4f9b4c3aa1cc4e89d7c9efd5dbff1c463d88374ed601d719.jpg",
    name: "Sarah Chen",
    handle: "@sarahdigital",
    text: "Amazing platform! The user experience is seamless and the features are exactly what I needed."
  },
  {
    avatarSrc: "https://cdn.21st.dev/assets/mirror/8d/8d9a61a581c43fe2088f221b7692c95db4b3ad5c0da0c856400c0e5acdcdcea8.jpg",
    name: "Marcus Johnson",
    handle: "@marcustech",
    text: "This service has transformed how I work. Clean design, powerful features, and excellent support."
  },
  {
    avatarSrc: "https://cdn.21st.dev/assets/mirror/a6/a634d4f02fe5b77804943c1d74b8d70e35ffe26454e0e9af9717432a2c72bfde.jpg",
    name: "David Martinez",
    handle: "@davidcreates",
    text: "I've tried many platforms, but this one stands out. Intuitive, reliable, and genuinely helpful for productivity."
  },
];

export const SignInPageDemo = () => {
  const handleSignIn = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const data = Object.fromEntries(formData.entries());
    console.log("Sign In submitted:", data);
    alert(`Sign In Submitted! Check the browser console for form data.`);
  };

  const handleGoogleSignIn = () => {
    console.log("Continue with Google clicked");
    alert("Continue with Google clicked");
  };

  const handleResetPassword = () => {
    alert("Reset Password clicked");
  };

  const handleCreateAccount = () => {
    alert("Create Account clicked");
  };

  return (
    <div className="bg-background text-foreground">
      <SignInPage
        heroImageSrc="https://cdn.21st.dev/assets/mirror/ec/ecff1664e7fc3185d0e947571f984ea5fa3de9580fb0e73a03cd9c9b3461cb09.jpg"
        testimonials={sampleTestimonials}
        onSignIn={handleSignIn}
        onGoogleSignIn={handleGoogleSignIn}
        onResetPassword={handleResetPassword}
        onCreateAccount={handleCreateAccount}
      />
    </div>
  );
};

