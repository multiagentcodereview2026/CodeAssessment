import {
  AnnouncementItem,
  AssessmentResult,
  Problem,
  SimilarityAlert,
  Assignment,
  StudentRosterItem
} from '../types';

export interface StudentDashboardPayload {
  announcements: AnnouncementItem[];
  assignedProblems: Problem[];
  recentAssessment: AssessmentResult;
}

export interface InstructorOverviewPayload {
  assignments: Assignment[];
  similarityAlerts: SimilarityAlert[];
  studentRoster: StudentRosterItem[];
  rubricAverages: Record<string, number>;
}

export const FRONTEND_API_CONTRACTS = {
  studentDashboard: 'GET /api/student/dashboard',
  announcements: 'GET /api/announcements',
  markAnnouncementRead: 'PATCH /api/announcements/:id/read',
  instructorOverview: 'GET /api/instructor/overview',
  problemBank: 'GET /api/problems',
  publishQuestion: 'POST /api/problems'
} as const;
