import type { Problem } from '../../types';
import { deadlineTime } from '../../lib/assignmentStatus';
export { deadlineTime } from '../../lib/assignmentStatus';

type Course = { id: number; course_code: string };
type Assignment = { id: number; course_id: number; status: string; due_date: string | null; problems: string[]; problem_titles: string[] };
type CatalogueProblem = { id: string; title: string; difficulty: string; topic_tags?: string[]; category?: string };

export function dashboardProblems(courses: Course[], assignments: Assignment[], catalogue: CatalogueProblem[], now = Date.now()): Problem[] {
  const problem = (id: string, title: string, record?: CatalogueProblem): Problem => ({
    id, title, slug: id,
    difficulty: record?.difficulty === 'Easy' || record?.difficulty === 'Hard' ? record.difficulty : 'Medium',
    tags: record?.topic_tags?.length ? record.topic_tags : [record?.category || 'Algorithms'],
    acceptanceRate: '—', description: '', examples: [], constraints: [], testCases: [],
    starterCode: {}, solutionCode: {}, optimalComplexity: { time: '—', space: '—' },
  });
  const courseMap = new Map(courses.map(course => [course.id, course]));
  const records = new Map(catalogue.map(item => [item.id, item]));
  const assigned = assignments.filter(item => courseMap.has(item.course_id) && item.status === 'ACTIVE'
    && (!item.due_date || deadlineTime(item.due_date) > now))
    .sort((a, b) => (a.due_date ? deadlineTime(a.due_date) : Infinity) - (b.due_date ? deadlineTime(b.due_date) : Infinity))
    .flatMap(item => item.problems.map((id, index) => ({
      ...problem(id, item.problem_titles[index] || records.get(id)?.title || id, records.get(id)),
      isInstructorAssigned: true, assignmentId: item.id,
      courseCode: courseMap.get(item.course_id)!.course_code, dueDate: item.due_date || '',
    })));
  return [...assigned, ...catalogue.map(item => problem(item.id, item.title, item))];
}

export function dashboardProblemUrl(problem: Pick<Problem, 'id' | 'assignmentId'>): string {
  const path = `/problems/${encodeURIComponent(problem.id)}`;
  return problem.assignmentId != null ? `${path}?assignmentId=${problem.assignmentId}` : path;
}
