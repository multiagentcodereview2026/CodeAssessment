export const TOPIC_MASTERY = [
  { name: 'Arrays & Two Pointers', mastery: 95, color: '#10b981', nextAction: 'Attempt medium sliding-window variants.' },
  { name: 'Hash Map & Lookup', mastery: 90, color: '#3b82f6', nextAction: 'Practice collision-style edge cases.' },
  { name: 'Linked Lists & Pointers', mastery: 80, color: '#06b6d4', nextAction: 'Revise pointer rewiring diagrams.' },
  { name: 'Trees & DFS/BFS', mastery: 75, color: '#8b5cf6', nextAction: 'Compare recursive and iterative traversals.' },
  { name: 'Graphs & Topological Sort', mastery: 50, color: '#f59e0b', nextAction: 'Start with BFS queue tracing.' },
  { name: 'Dynamic Programming & Memo', mastery: 45, color: '#ef4444', nextAction: 'Write state definitions before code.' }
];

export const RUBRIC_AGENTS = [
  { key: 'correctness', label: 'Correctness Agent', contractField: 'multiScores.correctness', backendOwner: 'sandbox test runner' },
  { key: 'timeComplexity', label: 'Time Complexity Agent', contractField: 'multiScores.timeComplexity', backendOwner: 'AST complexity profiler' },
  { key: 'spaceComplexity', label: 'Space Complexity Agent', contractField: 'multiScores.spaceComplexity', backendOwner: 'memory allocation analyzer' },
  { key: 'codeQuality', label: 'Code Quality Agent', contractField: 'multiScores.codeQuality', backendOwner: 'style and modularity reviewer' },
  { key: 'similarity', label: 'Originality Agent', contractField: 'multiScores.similarity', backendOwner: 'AST similarity service' }
];

export const COHORT_WEAKNESS_STATS = [
  {
    topic: 'Dynamic Programming',
    failRate: '42.5%',
    studentsCount: 19,
    severity: 'High',
    action: 'Assign DP State Builder Drill',
    reason: 'Students are jumping into code before defining states and transitions.'
  },
  {
    topic: 'Graphs (BFS/DFS)',
    failRate: '36.8%',
    studentsCount: 16,
    severity: 'High',
    action: 'Schedule Traversal Lab',
    reason: 'Queue/visited-set mistakes are causing repeated nodes and timeout failures.'
  },
  {
    topic: 'Trees & Recursion',
    failRate: '28.1%',
    studentsCount: 12,
    severity: 'Medium',
    action: 'Publish Recursion Trace Set',
    reason: 'Base-case handling is inconsistent on empty tree and single-node inputs.'
  },
  {
    topic: 'Linked Lists',
    failRate: '18.4%',
    studentsCount: 8,
    severity: 'Low',
    action: 'Share Pointer Diagram Notes',
    reason: 'Most errors are localized pointer order mistakes during reversal.'
  },
  {
    topic: 'Arrays & Two Pointers',
    failRate: '8.2%',
    studentsCount: 4,
    severity: 'Low',
    action: 'Offer Optional Challenge',
    reason: 'The cohort is mostly strong here; stretch problems are enough.'
  }
];

export const BACKEND_FIELD_GUIDE = [
  { feature: 'Question notices', endpoint: 'GET /api/announcements', payload: 'AnnouncementItem[]' },
  { feature: 'Problem bank cards', endpoint: 'GET /api/problems', payload: 'Problem[] with dueDate, testCases.isHidden, optimalComplexity' },
  { feature: 'Student revision plan', endpoint: 'GET /api/submissions/:id/assessment', payload: 'AssessmentResult.scoreProjection and suggestedImprovements' },
  { feature: 'Instructor triage', endpoint: 'GET /api/instructor/overview', payload: 'Assignment[], SimilarityAlert[], rubric aggregates' }
];
