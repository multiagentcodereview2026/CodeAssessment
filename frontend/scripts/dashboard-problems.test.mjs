import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { createServer } from 'vite';

const server = await createServer({ configFile: false, server: { middlewareMode: true }, appType: 'custom' });
const { dashboardProblems, dashboardProblemUrl, deadlineTime } = await server.ssrLoadModule('/src/components/student/dashboardProblems.ts');
const { assignmentDisplayStatus } = await server.ssrLoadModule('/src/lib/assignmentStatus.ts');
after(() => server.close());
const courses = [{ id: 1, course_code: 'REAL101' }];
const catalogue = [{ id: 'leetcode-7', title: 'Reverse Integer', difficulty: 'Medium', category: 'Math' }];
const assignment = (overrides = {}) => ({ id: 8, course_id: 1, status: 'ACTIVE', due_date: '2026-11-26T00:00:00', problems: ['leetcode-7'], problem_titles: ['Assigned Reverse Integer'], ...overrides });
const now = Date.parse('2026-11-25T00:00:00Z');

test('dashboard excludes expired, closed, upcoming, unenrolled and invalid-deadline assignments', () => {
  const result = dashboardProblems(courses, [assignment({ due_date: '2026-11-25T00:00:00Z' }),
    assignment({ status: 'CLOSED' }), assignment({ status: 'UPCOMING' }),
    assignment({ course_id: 99 }), assignment({ due_date: 'invalid' })], catalogue, now);
  assert.equal(result.length, 1);
  assert.equal(result[0].isInstructorAssigned, undefined);
  assert.equal(result[0].id, 'leetcode-7');
});

test('same problem in different assignments retains each assignment context', () => {
  const result = dashboardProblems(courses, [assignment({ id: 9, due_date: null }), assignment()], catalogue, now);
  assert.deepEqual(result.map(item => item.assignmentId), [8, 9, undefined]);
  assert.equal(result[0].courseCode, 'REAL101');
  assert.equal(result[0].title, 'Assigned Reverse Integer');
  assert.equal(dashboardProblemUrl(result[0]), '/problems/leetcode-7?assignmentId=8');
  assert.equal(dashboardProblemUrl(result[1]), '/problems/leetcode-7?assignmentId=9');
  assert.equal(dashboardProblemUrl(result[2]), '/problems/leetcode-7');
});

test('private course questions work without appearing in the public catalogue', () => {
  const result = dashboardProblems(courses, [assignment({ problems: ['instructor-1'], problem_titles: ['Private question'] })], [], now);
  assert.equal(result[0].id, 'instructor-1');
  assert.equal(result[0].title, 'Private question');
  assert.deepEqual(result[0].optimalComplexity, { time: '—', space: '—' });
  assert.equal(dashboardProblems([], [], [], now).length, 0);
});

test('legacy UTC deadlines and explicit offsets are interpreted consistently', () => {
  assert.equal(deadlineTime('2026-11-25T00:00:00'), now);
  assert.equal(deadlineTime('2026-11-25T05:30:00+05:30'), now);
});

test('instructor and student deadline displays agree at the closing boundary', () => {
  assert.equal(assignmentDisplayStatus('ACTIVE', '2026-11-25T00:00:00', now), 'Closed');
  assert.equal(assignmentDisplayStatus('ACTIVE', '2026-11-25T05:30:00+05:30', now - 1), 'Active');
  assert.equal(assignmentDisplayStatus('ACTIVE', null, now), 'Active');
  assert.equal(assignmentDisplayStatus('CLOSED', null, now), 'Closed');
  assert.equal(assignmentDisplayStatus('UPCOMING', null, now), 'Upcoming');
});
