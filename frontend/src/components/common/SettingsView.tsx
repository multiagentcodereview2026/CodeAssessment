import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/useAuth';
import { useTheme, ThemeMode } from '../../context/ThemeContext';
import {
  Check,
  CheckCircle2,
  Code2,
  Cpu,
  Database,
  Eye,
  EyeOff,
  Laptop,
  LockKeyhole,
  Monitor,
  Moon,
  Settings2,
  Sun,
  UserRound
} from 'lucide-react';

type SettingsTab = 'profile' | 'preferences' | 'engine';

export const SettingsView: React.FC = () => {
  const { currentUser, currentRole } = useApp();
  const { user, updateAccount } = useAuth();
  const { theme, resolvedTheme, setTheme } = useTheme();

  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const isInstructor = currentRole === 'instructor';
  const accentText = isInstructor ? 'text-emerald-600' : 'text-indigo-600';
  const accentBgSubtle = isInstructor ? 'bg-emerald-50' : 'bg-indigo-50';
  const accentBorderActive = isInstructor
    ? 'border-emerald-600 ring-2 ring-emerald-500/20 bg-emerald-50/50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 dark:border-emerald-500'
    : 'border-indigo-600 ring-2 ring-indigo-500/20 bg-indigo-50/50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 dark:border-indigo-500';

  const tabClass = (active: boolean) =>
    `inline-flex min-h-10 items-center gap-2 border-b-2 px-3 text-sm font-semibold transition-colors focus:outline-none focus-visible:ring-2 ${
      isInstructor ? 'focus-visible:ring-emerald-500' : 'focus-visible:ring-indigo-500'
    } ${
      active
        ? isInstructor
          ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400'
          : 'border-indigo-700 text-indigo-800 dark:text-indigo-400'
        : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
    }`;

  const accountName = user?.name || user?.username || currentUser.name || '—';
  const accountEmail = user?.email || currentUser.email || '—';
  const accountId = user?.id || currentUser.id || '—';
  const roleLabel = isInstructor ? 'Instructor' : 'Student';

  const savePassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setPasswordMessage(null);
    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: 'error', text: 'The new passwords do not match.' });
      return;
    }
    setBusy(true);
    try {
      await updateAccount({ current_password: currentPassword, new_password: newPassword });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPasswordMessage({ type: 'success', text: 'Password changed and saved securely.' });
    } catch (error) {
      setPasswordMessage({ type: 'error', text: error instanceof Error ? error.message : 'Unable to change password.' });
    } finally {
      setBusy(false);
    }
  };

  const messageClass = (type: 'success' | 'error') =>
    `mt-3 rounded-lg px-3 py-2 text-sm ${
      type === 'success' ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300'
    }`;

  return (
    <main className="mx-auto w-full min-w-0 max-w-7xl space-y-6 pb-12 animate-fadeIn">
      <header className="border-b border-slate-200 pb-5">
        <p className={`text-xs font-bold uppercase tracking-[0.14em] ${isInstructor ? 'text-emerald-600' : 'text-indigo-700'}`}>
          Account
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Settings</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Review your account and customize your interface theme, workspace behavior, and security preferences.
        </p>
      </header>

      <div className="border-b border-slate-200" role="tablist" aria-label="Settings sections">
        <div className="flex gap-2 overflow-x-auto">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'profile'}
            onClick={() => setActiveTab('profile')}
            className={tabClass(activeTab === 'profile')}
          >
            <UserRound className="h-4 w-4" />
            Profile
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'preferences'}
            onClick={() => setActiveTab('preferences')}
            className={tabClass(activeTab === 'preferences')}
          >
            <Settings2 className="h-4 w-4" />
            Preferences
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'engine'}
            onClick={() => setActiveTab('engine')}
            className={tabClass(activeTab === 'engine')}
          >
            <Cpu className="h-4 w-4" />
            AI &amp; execution
          </button>
        </div>
      </div>

      {/* Tab: Profile */}
      {activeTab === 'profile' && (
        <section role="tabpanel" className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-5">
            <article className="min-w-0 rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
              <div className="flex items-start gap-3 border-b border-slate-100 pb-4">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100">
                  <UserRound className="h-5 w-5 text-slate-700" />
                </span>
                <div>
                  <h2 className="font-semibold text-slate-900">Signed-in account</h2>
                  <p className="mt-1 text-sm text-slate-500">These details come from your authenticated account.</p>
                </div>
              </div>
              <dl className="mt-5 grid gap-x-6 gap-y-5 sm:grid-cols-2">
                <div>
                  <dt className="text-xs font-semibold text-slate-500">Name</dt>
                  <dd className="mt-1.5 break-words text-sm font-medium text-slate-900">{accountName}</dd>
                </div>
                <div>
                  <dt className="text-xs font-semibold text-slate-500">Email</dt>
                  <dd className="mt-1.5 break-words text-sm font-medium text-slate-900">{accountEmail}</dd>
                </div>
                <div>
                  <dt className="text-xs font-semibold text-slate-500">Account type</dt>
                  <dd className="mt-1.5 text-sm font-medium text-slate-900">{roleLabel}</dd>
                </div>
                <div>
                  <dt className="text-xs font-semibold text-slate-500">Account ID</dt>
                  <dd className="mt-1.5 break-all font-mono text-sm text-slate-700">{accountId}</dd>
                </div>
              </dl>
            </article>

            <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
              <div className="flex items-start gap-3 border-b border-slate-100 pb-4">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50">
                  <LockKeyhole className="h-5 w-5 text-amber-700" />
                </span>
                <div>
                  <h2 className="font-semibold text-slate-900">Change password</h2>
                  <p className="mt-1 text-sm text-slate-500">Choose a new password with at least 12 characters.</p>
                </div>
              </div>
              <form className="mt-5 grid gap-4 md:grid-cols-3" onSubmit={savePassword}>
                <label className="text-sm font-medium text-slate-700">
                  Current password
                  <input
                    required
                    type="password"
                    autoComplete="current-password"
                    value={currentPassword}
                    onChange={(event) => setCurrentPassword(event.target.value)}
                    className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  New password
                  <div className="relative mt-1.5">
                    <input
                      required
                      minLength={12}
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      value={newPassword}
                      onChange={(event) => setNewPassword(event.target.value)}
                      className="block w-full rounded-lg border border-slate-300 px-3 py-2.5 pr-10 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                      aria-label={showPassword ? 'Hide new password' : 'Show new password'}
                      className="absolute inset-y-0 right-2 flex items-center text-slate-500"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Confirm new password
                  <input
                    required
                    minLength={12}
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  />
                </label>
                <div className="md:col-span-3">
                  <button
                    disabled={busy}
                    className={`min-h-10 rounded-lg ${
                      isInstructor ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-slate-900 hover:bg-slate-800'
                    } px-4 text-sm font-semibold text-white disabled:opacity-50 cursor-pointer transition-colors`}
                  >
                    Update password
                  </button>
                  {passwordMessage && (
                    <p role="status" className={messageClass(passwordMessage.type)}>
                      {passwordMessage.text}
                    </p>
                  )}
                </div>
              </form>
            </article>
          </div>

          <aside className="rounded-xl border border-slate-200 bg-slate-50 p-5 self-start shadow-xs">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
              <LockKeyhole className="h-4 w-4 text-slate-600" />
              Account security
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Password changes are verified with your current password and stored as a secure hash. Your session remains protected across reloads.
            </p>
          </aside>
        </section>
      )}

      {/* Tab: Preferences (Theme Toggle + Workspace Behavior) */}
      {activeTab === 'preferences' && (
        <section role="tabpanel" className="space-y-5">
          {/* Appearance & Dark Theme Switcher */}
          <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="flex items-start gap-3">
                <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${accentBgSubtle} ${accentText}`}>
                  {resolvedTheme === 'dark' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
                </span>
                <div>
                  <h2 className="font-semibold text-slate-900 text-base">Appearance &amp; Dark Theme</h2>
                  <p className="mt-1 text-sm leading-6 text-slate-600 max-w-xl">
                    Choose your preferred display theme. Your setting is persisted in your browser and automatically applied across all student and instructor pages.
                  </p>
                </div>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 self-start">
                <span
                  className={`inline-block h-2 w-2 rounded-full ${
                    resolvedTheme === 'dark' ? (isInstructor ? 'bg-emerald-400' : 'bg-indigo-400') : 'bg-amber-400'
                  }`}
                />
                Active: <strong className="text-slate-900 dark:text-slate-100 font-bold">{resolvedTheme === 'dark' ? 'Dark' : 'Light'} Mode</strong>
                {theme === 'system' && <span className="text-slate-400 font-normal">(System)</span>}
              </div>
            </div>

            {/* Theme Selection Grid */}
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              {/* Light Option */}
              <button
                type="button"
                onClick={() => setTheme('light')}
                className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                  theme === 'light'
                    ? accentBorderActive
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                }`}
              >
                <div className="flex w-full items-center justify-between">
                  <span className={`p-2 rounded-lg ${theme === 'light' ? accentBgSubtle : 'bg-slate-100 dark:bg-slate-800'}`}>
                    <Sun className={`h-5 w-5 ${theme === 'light' ? accentText : 'text-slate-600 dark:text-slate-400'}`} />
                  </span>
                  {theme === 'light' && <Check className={`h-5 w-5 ${accentText}`} />}
                </div>
                <p className="mt-3 font-bold text-sm text-slate-900 dark:text-slate-100">Light theme</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-300 leading-relaxed">
                  Clean, high-clarity daylight aesthetic with soft contrast.
                </p>
              </button>

              {/* Dark Option */}
              <button
                type="button"
                onClick={() => setTheme('dark')}
                className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                  theme === 'dark'
                    ? accentBorderActive
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                }`}
              >
                <div className="flex w-full items-center justify-between">
                  <span className={`p-2 rounded-lg ${theme === 'dark' ? (isInstructor ? 'bg-emerald-50 dark:bg-emerald-900/30' : 'bg-indigo-50 dark:bg-indigo-900/30') : 'bg-slate-100 dark:bg-slate-800'}`}>
                    <Moon className={`h-5 w-5 ${theme === 'dark' ? accentText : 'text-slate-600 dark:text-slate-400'}`} />
                  </span>
                  {theme === 'dark' && <Check className={`h-5 w-5 ${accentText}`} />}
                </div>
                <p className="mt-3 font-bold text-sm text-slate-900 dark:text-slate-100">Dark theme</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-300 leading-relaxed">
                  Deep slate background designed for low eye strain during long coding sessions.
                </p>
              </button>

              {/* System Option */}
              <button
                type="button"
                onClick={() => setTheme('system')}
                className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                  theme === 'system'
                    ? accentBorderActive
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                }`}
              >
                <div className="flex w-full items-center justify-between">
                  <span className={`p-2 rounded-lg ${theme === 'system' ? (isInstructor ? 'bg-emerald-50 dark:bg-emerald-900/30' : 'bg-indigo-50 dark:bg-indigo-900/30') : 'bg-slate-100 dark:bg-slate-800'}`}>
                    <Laptop className={`h-5 w-5 ${theme === 'system' ? accentText : 'text-slate-600 dark:text-slate-400'}`} />
                  </span>
                  {theme === 'system' && <Check className={`h-5 w-5 ${accentText}`} />}
                </div>
                <p className="mt-3 font-bold text-sm text-slate-900 dark:text-slate-100">System sync</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-300 leading-relaxed">
                  Automatically changes when your computer or browser switches day/night modes.
                </p>
              </button>
            </div>
          </article>

          {/* Workspace behavior */}
          <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
            <div className="flex items-start gap-3">
              <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${accentBgSubtle} ${accentText}`}>
                <Monitor className="h-5 w-5" />
              </span>
              <div>
                <h2 className="font-semibold text-slate-900">Workspace behavior</h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Code drafts are saved in this browser as you work. A saved draft is local to this device and survives page reloads.
                </p>
              </div>
            </div>
            <div className="mt-5 flex items-start gap-2.5 rounded-lg border border-emerald-200 bg-emerald-50/70 p-3 text-sm text-emerald-900 dark:border-emerald-500/30 dark:bg-emerald-950/40 dark:text-emerald-200">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <p>Automatic local draft saving is active in the code workspace.</p>
            </div>
          </article>

          {/* Run and submit explanation */}
          <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100">
                <Code2 className="h-5 w-5 text-slate-700" />
              </span>
              <div>
                <h2 className="font-semibold text-slate-900">Run and submit</h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Run checks the visible sample cases. Submit sends your solution for the full server-side assessment, which evaluates hidden test cases and AI rubric metrics.
                </p>
              </div>
            </div>
          </article>
        </section>
      )}

      {/* Tab: Engine */}
      {activeTab === 'engine' && (
        <section role="tabpanel" className="grid min-w-0 gap-4 lg:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
            <div className="flex items-start gap-3">
              <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${accentBgSubtle} ${accentText}`}>
                <Cpu className="h-5 w-5" />
              </span>
              <div>
                <h2 className="font-semibold text-slate-900">Assessment service</h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Code assessment and evaluation are configured by the server. Personal API keys and model controls are not exposed in the browser client.
                </p>
              </div>
            </div>
            <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs font-semibold text-slate-700">Configuration is managed by your platform administrator</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                This keeps service credentials and evaluation settings safe and synchronized across users.
              </p>
            </div>
          </article>

          <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100">
                <Database className="h-5 w-5 text-slate-700" />
              </span>
              <div>
                <h2 className="font-semibold text-slate-900">Execution environment</h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Programs run in an isolated execution sandbox. Time limits, memory limits, and compiler flags follow problem specifications.
                </p>
              </div>
            </div>
            <p className="mt-5 text-xs leading-5 text-slate-500">
              No editable execution values are exposed because this application maintains server-enforced consistency across all evaluation environments.
            </p>
          </article>
        </section>
      )}
    </main>
  );
};
export default SettingsView;
