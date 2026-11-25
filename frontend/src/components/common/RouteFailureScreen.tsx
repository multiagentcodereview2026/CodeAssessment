import React from 'react';

export function RouteFailureScreen({ onReload }: { onReload: () => void }) {
  return <main className="min-h-screen grid place-items-center bg-slate-50 dark:bg-black p-6">
    <section role="alert" className="max-w-md rounded-2xl border border-rose-200 dark:border-rose-900/40 bg-white dark:bg-[#121217] p-6 text-center shadow-sm">
      <h1 className="text-lg font-bold text-slate-900 dark:text-zinc-100">We could not display this page</h1>
      <p className="mt-2 text-sm text-slate-600 dark:text-zinc-400">A page resource could not be loaded. Check your connection and reload to get the current version of the app.</p>
      <button type="button" onClick={onReload} className="mt-5 rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-sm font-semibold text-white">Reload page</button>
      <a className="mt-3 block text-sm text-indigo-600 dark:text-indigo-400" href="/">Return to dashboard</a>
    </section>
  </main>;
}
