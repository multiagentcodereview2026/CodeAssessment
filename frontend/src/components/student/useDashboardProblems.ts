import { useEffect, useState } from 'react';
import { useAuth } from '../../context/useAuth';
import { dashboardProblems } from './dashboardProblems';
import type { Problem } from '../../types';

export function useDashboardProblems() {
  const { user, authFetch } = useAuth();
  const [state, setState] = useState({ owner: '', problems: [] as Problem[], loading: true, error: '' });
  const owner = user?.id || '';
  useEffect(() => {
    let cancelled = false;
    setState({ owner, problems: [], loading: true, error: '' });
    if (!owner) return () => { cancelled = true; };
    const load = async () => {
      const read = async (url: string) => {
        const response = await authFetch(url, { cache: 'no-store' });
        if (!response.ok) throw new Error('Dashboard problems could not be loaded. Open My Courses or the Problem Bank to retry.');
        return response.json();
      };
      try {
        const [courses, catalogue] = await Promise.all([read('/api/student/courses'), read('/api/problems')]);
        const assignments = await Promise.all(courses.map((course: { id: number }) => read(`/api/student/courses/${course.id}/assignments`)));
        if (!cancelled) setState({ owner, problems: dashboardProblems(courses, assignments.flat(), catalogue), loading: false, error: '' });
      } catch (error) {
        if (!cancelled) setState({ owner, problems: [], loading: false, error: error instanceof Error ? error.message : 'Dashboard problems could not be loaded.' });
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [owner, authFetch]);
  return state.owner === owner ? state : { problems: [] as Problem[], loading: true, error: '' };
}
