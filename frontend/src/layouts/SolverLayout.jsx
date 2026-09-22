import { Outlet } from 'react-router-dom';

/** Focused student workspace: authenticated, but intentionally sidebar-free. */
const SolverLayout = () => (
  <main className="relative min-h-screen w-full overflow-x-hidden bg-slate-50 px-5 py-4 md:px-6 md:py-6 lg:px-8">
    <div className="pointer-events-none absolute inset-x-0 top-0 -z-0 h-64 bg-gradient-to-b from-indigo-50/60 to-transparent" />
    <div className="relative z-10 mx-auto w-full min-w-0 max-w-[1800px]">
      <Outlet />
    </div>
  </main>
);

export default SolverLayout;
