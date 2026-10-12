import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/useAuth';
import { CheckCircle2, Code2, Cpu, Database, LockKeyhole, Monitor, Settings2, UserRound } from 'lucide-react';

type SettingsTab = 'profile' | 'preferences' | 'engine';

const tabClass = (active: boolean) => `inline-flex min-h-10 items-center gap-2 border-b-2 px-3 text-sm font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${active ? 'border-indigo-700 text-indigo-800' : 'border-transparent text-slate-500 hover:text-slate-800'}`;

export const SettingsView: React.FC = () => {
  const { currentUser, currentRole } = useApp();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const accountName = user?.name || user?.username || currentUser.name || '—';
  const accountEmail = user?.email || currentUser.email || '—';
  const accountId = user?.id || currentUser.id || '—';
  const roleLabel = currentRole === 'instructor' ? 'Instructor' : 'Student';

  return (
    <main className="mx-auto w-full min-w-0 max-w-7xl space-y-6 pb-12">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-indigo-700">Account</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Settings</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Review your account and learn how workspace and assessment settings are managed.</p>
      </header>

      <div className="border-b border-slate-200" role="tablist" aria-label="Settings sections">
        <div className="flex gap-2 overflow-x-auto">
          <button type="button" role="tab" aria-selected={activeTab === 'profile'} onClick={() => setActiveTab('profile')} className={tabClass(activeTab === 'profile')}><UserRound className="h-4 w-4"/>Profile</button>
          <button type="button" role="tab" aria-selected={activeTab === 'preferences'} onClick={() => setActiveTab('preferences')} className={tabClass(activeTab === 'preferences')}><Settings2 className="h-4 w-4"/>Preferences</button>
          <button type="button" role="tab" aria-selected={activeTab === 'engine'} onClick={() => setActiveTab('engine')} className={tabClass(activeTab === 'engine')}><Cpu className="h-4 w-4"/>AI &amp; execution</button>
        </div>
      </div>

      {activeTab === 'profile' && <section role="tabpanel" className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <article className="min-w-0 rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
          <div className="flex items-start gap-3 border-b border-slate-100 pb-4"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100"><UserRound className="h-5 w-5 text-slate-700"/></span><div><h2 className="font-semibold text-slate-900">Signed-in account</h2><p className="mt-1 text-sm text-slate-500">These details come from your authenticated account.</p></div></div>
          <dl className="mt-5 grid gap-x-6 gap-y-5 sm:grid-cols-2">
            <div><dt className="text-xs font-semibold text-slate-500">Name</dt><dd className="mt-1.5 break-words text-sm font-medium text-slate-900">{accountName}</dd></div>
            <div><dt className="text-xs font-semibold text-slate-500">Email</dt><dd className="mt-1.5 break-words text-sm font-medium text-slate-900">{accountEmail}</dd></div>
            <div><dt className="text-xs font-semibold text-slate-500">Account type</dt><dd className="mt-1.5 text-sm font-medium text-slate-900">{roleLabel}</dd></div>
            <div><dt className="text-xs font-semibold text-slate-500">Account ID</dt><dd className="mt-1.5 break-all font-mono text-sm text-slate-700">{accountId}</dd></div>
          </dl>
        </article>
        <aside className="rounded-xl border border-slate-200 bg-slate-50 p-5"><div className="flex items-center gap-2 text-sm font-semibold text-slate-900"><LockKeyhole className="h-4 w-4 text-slate-600"/>Managed account details</div><p className="mt-2 text-sm leading-6 text-slate-600">Name and email are controlled by your account record. Editing and institution details will appear here when profile updates are supported by the service.</p></aside>
      </section>}

      {activeTab === 'preferences' && <section role="tabpanel" className="space-y-4">
        <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50"><Monitor className="h-5 w-5 text-indigo-700"/></span><div><h2 className="font-semibold text-slate-900">Workspace behavior</h2><p className="mt-1 text-sm leading-6 text-slate-600">Code drafts are saved in this browser as you work. A saved draft is local to this device and is not a server account preference.</p></div></div><div className="mt-5 flex items-start gap-2.5 rounded-lg border border-emerald-200 bg-emerald-50/70 p-3 text-sm text-emerald-900"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0"/><p>Automatic local draft saving is active in the code workspace.</p></div></article>
        <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100"><Code2 className="h-5 w-5 text-slate-700"/></span><div><h2 className="font-semibold text-slate-900">Run and submit</h2><p className="mt-1 text-sm leading-6 text-slate-600">Run checks the visible sample cases. Submit sends your solution for the full server-side assessment, which may include private cases.</p></div></div></article>
      </section>}

      {activeTab === 'engine' && <section role="tabpanel" className="grid min-w-0 gap-4 lg:grid-cols-2">
        <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50"><Cpu className="h-5 w-5 text-indigo-700"/></span><div><h2 className="font-semibold text-slate-900">Assessment service</h2><p className="mt-1 text-sm leading-6 text-slate-600">Code assessment and evaluation are configured by the server. Personal API keys and model controls are not managed from this page.</p></div></div><div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-3"><p className="text-xs font-semibold text-slate-700">Configuration is managed by your platform administrator</p><p className="mt-1 text-xs leading-5 text-slate-500">This keeps service credentials and evaluation settings out of the browser.</p></div></article>
        <article className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100"><Database className="h-5 w-5 text-slate-700"/></span><div><h2 className="font-semibold text-slate-900">Execution environment</h2><p className="mt-1 text-sm leading-6 text-slate-600">Programs run in the configured execution service. Time limits and compiler settings follow the problem and server configuration.</p></div></div><p className="mt-5 text-xs leading-5 text-slate-500">No editable execution values are exposed because this app does not currently save per-user overrides.</p></article>
      </section>}
    </main>
  );
};
