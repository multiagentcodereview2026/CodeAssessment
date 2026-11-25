// Legacy API timestamps without a timezone suffix represent UTC.
export const deadlineTime = (value: string) => Date.parse(/[zZ]$|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`);

export function assignmentDisplayStatus(status: string, dueDate?: string | null, now = Date.now()): 'Active' | 'Upcoming' | 'Closed' {
  if (status === 'CLOSED' || (dueDate && !(deadlineTime(dueDate) > now))) return 'Closed';
  return status === 'ACTIVE' ? 'Active' : status === 'UPCOMING' ? 'Upcoming' : 'Closed';
}
