export type Role = 'student' | 'instructor';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: Role;
  avatar: string;
  rollNumber: string;
  institution: string;
  department: string;
  year: string;
}

export type Difficulty = 'Easy' | 'Medium' | 'Hard';
export type ProblemOrigin = 'instructor_assigned' | 'self_practice';
export type StudentAssignmentStatus = 'Not Started' | 'In Progress' | 'Submitted' | 'Reviewed';

export interface ProblemExample {
  input: string;
  output: string;
  explanation?: string;
}

export interface TestCase {
  id: string;
  input: string;
  expectedOutput: string;
  isHidden?: boolean;
}

export interface Problem {
  id: string;
  title: string;
  slug: string;
  difficulty: Difficulty;
  tags: string[];
  acceptanceRate: string;
  description: string;
  examples: ProblemExample[];
  constraints: string[];
  testCases: TestCase[];
  starterCode: Record<string, string>;
  solutionCode: Record<string, string>;
  optimalComplexity: {
    time: string;
    space: string;
  };
  origin?: ProblemOrigin;
  assignmentId?: string;
  instructorName?: string;
  dueDate?: string;
  studentStatus?: StudentAssignmentStatus;
}

export interface TestCaseResult {
  id: string;
  testCaseNumber: number;
  input: string;
  expectedOutput: string;
  actualOutput: string;
  passed: boolean;
  executionTimeMs: number;
  memoryMb: number;
  stdout?: string;
  stderr?: string;
}

export interface MultiDimensionalScore {
  correctness: {
    score: number;
    max: number;
    notes: string;
  };
  timeComplexity: {
    score: number;
    max: number;
    detected: string;
    optimal: string;
    notes: string;
  };
  spaceComplexity: {
    score: number;
    max: number;
    detected: string;
    optimal: string;
    notes: string;
  };
  codeQuality: {
    score: number;
    max: number;
    styleScore: number;
    structureScore: number;
    notes: string;
  };
  similarity: {
    score: number;
    max: number;
    originalityPercent: number;
    plagiarismRisk: 'Low' | 'Medium' | 'High';
    notes: string;
  };
  overallScore: number;
}

export interface IterationTimelineStep {
  stage: string;
  score: number;
  note: string;
  timestamp?: string;
}

export interface ScoreProjection {
  currentScore: number;
  projectedScore: number;
  improvementDelta: number;
  focusAreas: string[];
  iterationTimeline: IterationTimelineStep[];
}

export interface AssessmentResult {
  submissionId: string;
  problemId: string;
  problemTitle: string;
  timestamp: string;
  language: string;
  code: string;
  status: 'Accepted' | 'Partial' | 'Wrong Answer' | 'Time Limit Exceeded' | 'Runtime Error';
  executionTime: string;
  memory: string;
  multiScores: MultiDimensionalScore;
  explainableFeedback: string;
  suggestedImprovements: string[];
  recommendedTopics: string[];
  practiceProblems: {
    id: string;
    title: string;
    difficulty: Difficulty;
    tags: string[];
  }[];
  scoreProjection: ScoreProjection;
  aiRevisedCode: string;
  testResults: TestCaseResult[];
  isAssignedSubmission?: boolean;
  instructorFeedbackNotes?: string;
}

export interface SubmissionItem {
  id: string;
  problemId: string;
  problemTitle: string;
  score: number;
  status: 'Passed' | 'Partial' | 'Failed';
  language: string;
  date: string;
  timeSpent?: string;
  passedTestCases: number;
  totalTestCases: number;
  feedbackSummary?: string;
  origin?: ProblemOrigin;
  assignmentId?: string;
}

export interface CategoryScore {
  name: string;
  percentage: number;
  color: string;
  scoreDisplay: string;
}

export interface StudentProgress {
  overallScore: number;
  problemsSolved: number;
  totalProblems: number;
  currentStreak: number;
  rankDisplay: string;
  rankNumber: number;
  totalStudents: number;
  progressPercent: number;
  topicsCovered: number;
  totalTopics: number;
  hoursSpent: string;
  weakTopics: string[];
  categoryWiseScores: CategoryScore[];
  scoreTrend: { date: string; score: number }[];
}

export interface StudentRosterItem {
  id: string;
  name: string;
  rollNumber: string;
  email: string;
  avatar: string;
  submissionsCount: number;
  avgScore: number;
  trend: 'up' | 'down' | 'neutral';
  weakTopics: string[];
  status: 'On Track' | 'At Risk' | 'Needs Attention';
  department: string;
  year: string;
}

export interface AssignedProblemItem {
  problemId: string;
  problemTitle: string;
  difficulty: Difficulty;
  studentStatus: StudentAssignmentStatus;
  score?: number;
}

export interface Assignment {
  id: string;
  title: string;
  description: string;
  course: string;
  instructorName?: string;
  problemsCount: number;
  problemIds: string[];
  assignedProblems?: AssignedProblemItem[];
  submittedCount: number;
  totalCount: number;
  avgScore: number;
  dueDate: string;
  postedDate?: string;
  status: 'Active' | 'Upcoming' | 'Closed';
  studentStatus?: StudentAssignmentStatus;
}

export interface SimilarityAlert {
  id: string;
  problemId: string;
  problemTitle: string;
  studentA: { id: string; name: string; rollNumber: string; submissionId: string };
  studentB: { id: string; name: string; rollNumber: string; submissionId: string };
  similarityPercentage: number;
  riskLevel: 'High' | 'Medium' | 'Low';
  matchedLinesCount: number;
  timestamp: string;
  studentACodeSnippet: string;
  studentBCodeSnippet: string;
  aiAuditNotes: string;
}

export interface ReportItem {
  id: string;
  title: string;
  description: string;
  type: 'Performance' | 'Assignment' | 'Topic' | 'At-Risk';
  generatedDate: string;
  fileSize: string;
  format: 'PDF' | 'CSV' | 'XLSX';
}
