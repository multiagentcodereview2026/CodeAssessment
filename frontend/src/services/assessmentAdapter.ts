import type { AssessmentResult, Problem } from '../types';

export function toProblem(data: any): Problem {
  return { id: data.id, slug: data.id, title: data.title, description: data.description || '',
    difficulty: data.difficulty || 'Easy', tags: [data.category || 'Programming'], acceptanceRate: '-',
    examples: data.examples || [], constraints: data.constraints || [],
    testCases: (data.test_cases || []).map((tc: any, i: number) => ({ id: String(tc.id || i), input: tc.input, expectedOutput: tc.expected_output, isHidden: !!tc.is_hidden })),
    starterCode: data.starter_codes || {}, solutionCode: {},
    optimalComplexity: { time: data.optimal_time || 'Not assessed', space: data.optimal_space || 'Not assessed' },
    isInstructorAssigned: !!data.is_instructor_assigned, courseCode: data.course_code, dueDate: data.due_date };
}

export function toAssessment(data: any, problem?: any): AssessmentResult {
  const execution = data.execution_result || {};
  const passed = Number(execution.passed_cases || 0), total = Number(execution.total_cases || 0);
  const accepted = total > 0 && passed === total && execution.compile_status === 'success';
  const score = (value: any, notes = '') => ({ score: value == null ? 0 : Number(value), max: value == null ? 0 : 100, notes: value == null ? 'Not assessed' : notes });
  const complexity = data.complexity_details || {};
  const feedback = data.feedback || {};
  const improvements = feedback.improvement_steps || data.recommendations?.learning_path || [];
  const overall = Number(data.overall_score ?? 0);
  const assessed = ['correctness_score', 'complexity_score', 'style_score', 'similarity_score'].filter(key => data[key] != null).length;
  const originality = data.similarity_score == null ? null : 100 - data.similarity_score;
  const last = execution.last_failed_case;
  return {
    submissionId: data.submission_id || '', problemId: data.problem_id || '', problemTitle: problem?.title || data.problem_title || data.problem_id || '',
    timestamp: data.created_at || '', language: data.language || '', code: data.code || '',
    status: accepted ? 'Accepted' : execution.execution_status === 'time_limit_exceeded' ? 'Time Limit Exceeded' : execution.execution_status === 'runtime_error' ? 'Runtime Error' : 'Wrong Answer',
    executionTime: `${execution.runtime_ms ?? 0} ms`, memory: execution.memory_kb ? `${(execution.memory_kb / 1024).toFixed(1)} MB` : 'Not measured',
    multiScores: {
      correctness: score(data.correctness_score, `${passed}/${total} tests passed`),
      timeComplexity: { ...score(data.complexity_score), detected: complexity.time_complexity || 'Not assessed', optimal: complexity.expected_time_complexity || 'Not specified' },
      spaceComplexity: { ...score(null), detected: complexity.space_complexity || 'Not assessed', optimal: complexity.expected_space_complexity || 'Not specified', notes: 'Included in the combined complexity score' },
      codeQuality: { ...score(data.style_score, data.style_details?.summary), styleScore: 0, structureScore: 0 },
      similarity: { ...score(originality), originalityPercent: originality ?? 0, plagiarismRisk: 'Low' }, overallScore: overall,
    },
    explainableFeedback: `${feedback.mentor_feedback || `${passed}/${total} tests passed.`}\n\n${assessed}/4 rubric dimensions assessed. The overall score is normalized over available evidence.`,
    suggestedImprovements: improvements, recommendedTopics: (data.recommendations?.recommended_topics || []).map((item: any) => item.topic), practiceProblems: [],
    scoreProjection: { currentScore: overall, projectedScore: overall, improvementDelta: 0, focusAreas: improvements,
      iterationTimeline: [{ stage: 'Current assessment', score: overall, note: 'Re-submit to measure improvement' }] },
    aiRevisedCode: typeof data.improved_code === 'string' ? data.improved_code : data.improved_code?.improved_code || data.code || '',
    testResults: (execution.results || []).map((r: any, i: number) => ({ id: String(r.test_case_id || i), testCaseNumber: i + 1,
      input: r.is_hidden ? 'Hidden test case' : r.input || '', expectedOutput: r.is_hidden ? 'Hidden test case' : r.expected_output || '',
      actualOutput: r.is_hidden ? 'Hidden test case' : r.actual_output || '', passed: String(r.status).toLowerCase() === 'accepted',
      executionTimeMs: r.runtime_ms || 0, memoryMb: (r.memory_kb || 0) / 1024, isHidden: !!r.is_hidden,
      verdict: r.status, stderr: r.is_hidden ? undefined : r.stderr || r.error_message })),
    totalTestCases: total,
    lastFailedCase: last ? { ordinal: last.ordinal, status: last.status, isHidden: !!last.is_hidden, reason: last.is_hidden ? undefined : last.reason } : undefined,
  };
}
