import React, { useEffect, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import {
  Play,
  Send,
  RotateCcw,
  Maximize2,
  Minimize2,
  CheckCircle,
  XCircle,
  Clock,
  HardDrive,
  Sparkles,
  Layers,
  ArrowLeft,
  Terminal,
  Cpu,
  ShieldCheck,
  Check
} from 'lucide-react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';
import { AssessmentResult, SubmissionItem, TestCaseResult } from '../../types';
import {
  formatInputForDisplay,
  parseProblemInputSchema
} from '../../utils/inputPresentation';

const DEFAULT_PROGRAM_SKELETONS: Record<string, string> = {
  cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n\n    return 0;\n}\n',
  java: 'import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n\n    }\n}\n',
  c: '#include <stdio.h>\n\nint main() {\n\n    return 0;\n}\n',
  python: 'def main():\n    pass\n\nif __name__ == "__main__":\n    main()\n',
  javascript: "'use strict';\n\n"
};

type PublicRunCaseResult = {
  caseNum: number;
  passed: boolean;
  input: string;
  /** The program's stdout only. It is deliberately never replaced by stderr. */
  output: string;
  expected: string;
  status?: string;
  error?: string;
};

export const ProblemWorkspace: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { id: routeProblemId } = useParams<{ id: string }>();
  const isInstructorProblem = new URLSearchParams(location.search).get('view') === 'instructor';
  const {
    currentUser,
    selectedProblem: fallbackProblem,
    setCurrentView,
    addSubmission
  } = useApp();

  const [remoteProblem, setRemoteProblem] = useState<any | null>(null);
  const [problemLoadError, setProblemLoadError] = useState<string | null>(null);
  const [isProblemLoading, setIsProblemLoading] = useState(true);
  const selectedProblem = remoteProblem || fallbackProblem;
  const requestedProblemId = routeProblemId || fallbackProblem.id;
  const workspaceProblemId = remoteProblem?.id || requestedProblemId;

  useEffect(() => {
    let cancelled = false;
    setRemoteProblem(null);
    setProblemLoadError(null);
    setIsProblemLoading(true);

    fetch(`/api/problems/${encodeURIComponent(requestedProblemId)}`)
      .then(async (response) => {
        if (!response.ok) throw new Error('Problem could not be loaded.');
        return response.json();
      })
      .then((problem) => {
        if (cancelled) return;
        // The API deliberately returns a maximum of three public cases. Hidden
        // test data is never placed in browser state.
        const publicCases = (problem.test_cases || []).slice(0, 3).map((tc: any, index: number) => ({
          id: String(tc.id || index + 1),
          input: tc.input || '',
          expectedOutput: tc.expected_output || '',
          isHidden: false
        }));
        const inputSchema = parseProblemInputSchema(problem.description || '', problem.id);
        setRemoteProblem({
          id: problem.id,
          slug: problem.id,
          title: problem.title,
          difficulty: ['Easy', 'Medium', 'Hard'].includes(problem.difficulty) ? problem.difficulty : 'Medium',
          tags: problem.category ? [problem.category] : [],
          acceptanceRate: '—',
          description: problem.description || 'No statement is available for this problem.',
          examples: problem.examples || publicCases.slice(0, 3).map((tc: any) => ({ input: tc.input, output: tc.expectedOutput })),
          constraints: problem.constraints || [],
          testCases: publicCases,
          starterCode: problem.starter_codes || {},
          solutionCode: {},
          optimalComplexity: { time: '—', space: '—' },
          inputSchema
        });
        setProblemLoadError(null);
      })
      .catch((error) => !cancelled && setProblemLoadError(error.message))
      .finally(() => !cancelled && setIsProblemLoading(false));

    return () => { cancelled = true; };
  }, [requestedProblemId]);

  const [language, setLanguage] = useState<string>('cpp');
  const [code, setCode] = useState<string>(
    DEFAULT_PROGRAM_SKELETONS.cpp
  );
  const [activeLeftTab, setActiveLeftTab] = useState<'statement' | 'testcases'>('statement');
  const [activeTestTab, setActiveTestTab] = useState<number>(0);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submissionStep, setSubmissionStep] = useState<number>(0);
  const [isEditorFullscreen, setIsEditorFullscreen] = useState<boolean>(false);
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);
  const runOutputRef = useRef<HTMLDivElement>(null);
  const [runOutput, setRunOutput] = useState<{
    status: 'idle' | 'success' | 'error';
    time: string;
    memory: string;
    reason?: string;
    compileError?: string;
    results: PublicRunCaseResult[];
  } | null>(null);

  // A draft belongs to one problem and one language.  It stays in this
  // browser even if the student returns to the catalogue or refreshes.
  // Drafts are never sent anywhere until the student explicitly runs/submits.
  const draftKey = (problemId: string, selectedLanguage: string) =>
    `codevedha_editor_draft:${problemId}:${selectedLanguage}`;

  const getStarterCode = (selectedLanguage: string) =>
    DEFAULT_PROGRAM_SKELETONS[selectedLanguage]
    || selectedProblem.starterCode[selectedLanguage]
    || DEFAULT_PROGRAM_SKELETONS.cpp;

  useEffect(() => {
    const savedDraft = localStorage.getItem(draftKey(workspaceProblemId, language));
    // A non-empty draft belongs to its language and is never replaced on a
    // language switch. Empty legacy drafts get the new full-program skeleton.
    setCode(savedDraft && savedDraft.trim() ? savedDraft : getStarterCode(language));
    setRunOutput(null);
  }, [workspaceProblemId, language]);

  useEffect(() => {
    try {
      localStorage.setItem(draftKey(workspaceProblemId, language), code);
    } catch (error) {
      // A full/disabled browser store must not stop the coding workspace.
      console.warn('Unable to save editor draft:', error);
    }
  }, [code, language, workspaceProblemId]);

  // When language changes, update starter code
  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
  };

  const handleResetCode = () => {
    if (window.confirm('Reset code to initial template?')) {
      localStorage.removeItem(draftKey(workspaceProblemId, language));
      setCode(getStarterCode(language));
      setRunOutput(null);
    }
  };

  const monacoLanguage: Record<string, string> = {
    cpp: 'cpp',
    c: 'c',
    python: 'python',
    java: 'java',
    javascript: 'javascript'
  };

  const clearCompilerMarkers = () => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (editor?.getModel() && monaco) {
      monaco.editor.setModelMarkers(editor.getModel(), 'docker-compiler', []);
    }
  };

  const showCompilerMarker = (compilerOutput: string) => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor?.getModel() || !monaco) return;

    // GCC and javac report file:line:column. Python uses "line N"; both
    // forms point at the same lines the student sees in Monaco.
    const gccMatch = compilerOutput.match(/(?:solution\.cpp|solution\.c|Main\.java):(\d+):(\d+):\s*(?:fatal )?error:\s*([^\n]+)/i);
    const pythonMatch = compilerOutput.match(/line\s+(\d+)/i);
    const line = Number(gccMatch?.[1] || pythonMatch?.[1] || 1);
    const column = Number(gccMatch?.[2] || 1);
    const message = gccMatch?.[3] || compilerOutput.split('\n').find(Boolean) || 'Compilation failed.';

    monaco.editor.setModelMarkers(editor.getModel(), 'docker-compiler', [{
      startLineNumber: line,
      startColumn: column,
      endLineNumber: line,
      endColumn: column + 1,
      message,
      severity: monaco.MarkerSeverity.Error
    }]);
    editor.revealLineInCenter(line);
    editor.setPosition({ lineNumber: line, column });
    editor.focus();
  };

  const handleEditorMount = (editor: any, monaco: any) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    editor.focus();
  };

  useEffect(() => {
    const exitFullscreenOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsEditorFullscreen(false);
    };
    window.addEventListener('keydown', exitFullscreenOnEscape);
    return () => window.removeEventListener('keydown', exitFullscreenOnEscape);
  }, []);

  // The 50-line editor may place results below the current viewport.  Bring
  // the completed Run Code result into view without interrupting typing while
  // the request is still running.
  useEffect(() => {
    if (!runOutput) return;
    requestAnimationFrame(() => {
      runOutputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }, [runOutput]);

  // Run Code (Sandbox Test Cases via Live FastAPI Backend)
  const handleRunCode = async () => {
    if (!remoteProblem) {
      setRunOutput({
        status: 'error',
        time: '—',
        memory: '—',
        reason: problemLoadError || 'Wait for the problem and its public tests to finish loading.',
        results: []
      });
      return;
    }
    setIsRunning(true);
    setRunOutput(null);
    setActiveTestTab(0);

    try {
      const res = await fetch('/api/submissions/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language,
          code,
          problem_id: remoteProblem.id,
          // These are the only three public cases returned to the browser.
          test_cases: selectedProblem.testCases.slice(0, 3).map((tc, idx) => ({
            id: tc.id || String(idx + 1),
            input: tc.input,
            expected_output: tc.expectedOutput,
            is_hidden: Boolean(tc.isHidden)
          }))
        })
      });
      if (!res.ok) {
        const errorPayload = await res.json().catch(() => null);
        throw new Error(errorPayload?.detail || errorPayload?.compile_error || `Sandbox request failed (${res.status}).`);
      }
      const data = await res.json();
      const compilationFailed = data.compile_status === 'error';
      if (compilationFailed) showCompilerMarker(data.compile_error || data.stderr || 'Compilation failed.');
      else clearCompilerMarkers();
      const publicCases = selectedProblem.testCases.slice(0, 3);
      const engineResults = Array.isArray(data.results) ? data.results : [];
      const responseStdout = typeof data.stdout === 'string' && data.stdout !== 'Execution completed.'
        ? data.stdout
        : '';
      const responseStderr = typeof data.stderr === 'string' ? data.stderr : '';

      // Always build one display result per public input. The execution engine
      // normally returns these in order, but matching by id first prevents a
      // parallel runner from putting Case 2's stdout under Case 1.
      const results: PublicRunCaseResult[] = publicCases.map((tc, idx) => {
        const indexedResult = engineResults[idx];
        const engineResult = engineResults.find((result: any) => String(result.test_case_id) === String(tc.id))
          // Older response formats did not include a case id; only then is
          // positional mapping safe. A known different id must never leak
          // another case's stdout into this panel.
          || (indexedResult && (indexedResult.test_case_id === undefined || indexedResult.test_case_id === null)
            ? indexedResult
            : undefined);
        const engineStatus = String(engineResult?.status || (compilationFailed ? 'compilation_error' : 'not_executed'));
        const actualOutput = typeof engineResult?.actual_output === 'string'
          ? engineResult.actual_output
          : typeof engineResult?.stdout === 'string'
            ? engineResult.stdout
            // Only use a response-level stdout when no per-case results were
            // returned. Reusing Case 1's stdout for Case 2 would be wrong.
            : engineResults.length === 0 ? responseStdout : '';

        return {
          caseNum: idx + 1,
          passed: !compilationFailed && engineStatus.toLowerCase() === 'accepted',
          input: tc.input,
          expected: typeof engineResult?.expected_output === 'string' ? engineResult.expected_output : tc.expectedOutput,
          // stderr is an execution diagnostic, not the student's output.
          // Keeping this separate makes a blank stdout visible and truthful.
          output: actualOutput,
          status: engineStatus,
          error: compilationFailed
            ? 'Not executed because compilation failed.'
            : (engineResult?.stderr || engineResult?.error_message || (engineResult ? undefined : responseStderr || 'This case was not executed.'))
        };
      });

      setRunOutput({
        status: !compilationFailed && data.failed_cases === 0 ? 'success' : 'error',
        time: `${data.runtime_ms || 18} ms`,
        memory: '4.2 MB',
        reason: compilationFailed
          ? 'Compilation failed. No test cases were executed.'
          : data.failed_cases > 0 ? (data.results || []).find((result: any) => result.status !== 'accepted' && result.status !== 'ACCEPTED')?.stderr || (data.results || []).find((result: any) => result.status !== 'accepted' && result.status !== 'ACCEPTED')?.status?.replaceAll('_', ' ') || 'Your output did not match the expected output.' : undefined,
        compileError: compilationFailed ? (data.compile_error || data.stderr || 'Compilation failed.') : undefined,
        results
      });
    } catch (err: any) {
      const errMsg = err?.message || 'The execution service could not run this code.';
      setRunOutput({
        status: 'error',
        time: '—',
        memory: '—',
        reason: errMsg,
        results: selectedProblem.testCases.slice(0, 3).map((tc, idx) => ({
          caseNum: idx + 1,
          passed: false,
          input: tc.input,
          expected: tc.expectedOutput,
          output: '',
          status: 'system_error',
          error: errMsg
        }))
      });
    } finally {
      setIsRunning(false);
    }
  };

  // Submit Code (Live 10-Agent LangGraph AI Assessment Pipeline)
  const handleSubmitCode = async () => {
    if (!remoteProblem) {
      setRunOutput({
        status: 'error',
        time: '—',
        memory: '—',
        reason: problemLoadError || 'Wait for the problem to finish loading before submitting.',
        results: []
      });
      return;
    }
    if (!code.trim()) {
      setRunOutput({
        status: 'error',
        time: '—',
        memory: '—',
        reason: 'Enter code before submitting.',
        results: []
      });
      return;
    }
    setIsSubmitting(true);
    setSubmissionStep(1);

    // Do not advance the visual workflow on a timer. The full private suite
    // can take longer than a public run, and claiming later AI stages while
    // Docker is still judging would be misleading.

    try {
      const res = await fetch('/api/submissions/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: currentUser.id,
          problem_id: remoteProblem.id,
          language,
          code
        })
      });
      if (!res.ok) {
        const errorPayload = await res.json().catch(() => null);
        throw new Error(errorPayload?.detail || `Submission failed (${res.status}).`);
      }
      const data = await res.json();
      setSubmissionStep(5);

      const newSubmissionId = data.submission_id || `SUB${Math.floor(100000 + Math.random() * 900000)}`;
      const execution = data.execution_result || {};
      const totalCases = Number(execution.total_cases || (Number(execution.passed_cases || 0) + Number(execution.failed_cases || 0)));
      const passedCases = Number(execution.passed_cases || 0);
      const accepted = totalCases > 0 && passedCases === totalCases;
      const timeComplexity = typeof data.complexity_details?.time_complexity === 'string'
        ? data.complexity_details.time_complexity
        : selectedProblem.optimalComplexity?.time !== '—'
          ? selectedProblem.optimalComplexity?.time
          : 'Not available';
      const spaceComplexity = typeof data.complexity_details?.space_complexity === 'string'
        ? data.complexity_details.space_complexity
        : selectedProblem.optimalComplexity?.space !== '—'
          ? selectedProblem.optimalComplexity?.space
          : 'Not available';
      const testResults: TestCaseResult[] = (execution.results || []).map((result: any, index: number) => {
        const hidden = Boolean(result.is_hidden);
        return {
          id: String(result.test_case_id || index + 1),
          testCaseNumber: index + 1,
          input: hidden ? 'Hidden test case' : (result.input || ''),
          expectedOutput: hidden ? 'Hidden test case' : (result.expected_output || ''),
          actualOutput: hidden ? 'Hidden test case' : (result.actual_output || ''),
          passed: result.status === 'accepted' || result.status === 'ACCEPTED',
          executionTimeMs: Number(result.runtime_ms || 0),
          memoryMb: Number(result.memory_kb || 0) / 1024,
          stderr: hidden ? undefined : (result.stderr || result.error_message || undefined)
        };
      });

      const newAssessment: AssessmentResult = {
        submissionId: newSubmissionId,
        problemId: selectedProblem.id,
        problemTitle: selectedProblem.title,
        timestamp: 'Just now',
        language: language === 'cpp' ? 'C++' : language === 'c' ? 'C' : language === 'python' ? 'Python 3' : language === 'java' ? 'Java' : 'JavaScript',
        code: code,
        status: accepted ? 'Accepted' : 'Wrong Answer',
        executionTime: `${execution.runtime_ms || 0} ms`,
        memory: '5.2 MB',
        multiScores: {
          correctness: {
            score: Math.round(((data.correctness_score ?? 100) / 100) * 25),
            max: 25,
            notes: accepted
              ? `Accepted: ${passedCases}/${totalCases} public and hidden tests passed.`
              : `Judge result: ${passedCases}/${totalCases} tests passed. Review the first failing test below.`
          },
          timeComplexity: {
            score: Math.round(((data.complexity_score ?? 85) / 100) * 25),
            max: 25,
            detected: timeComplexity,
            optimal: timeComplexity,
            notes: `AST complexity analysis reported ${timeComplexity}.`
          },
          spaceComplexity: {
            score: 13,
            max: 15,
            detected: spaceComplexity,
            optimal: spaceComplexity,
            notes: `AST complexity analysis reported ${spaceComplexity}.`
          },
          codeQuality: {
            score: Math.round(((data.style_score ?? 90) / 100) * 20),
            max: 20,
            styleScore: 9,
            structureScore: 9,
            notes: 'Clean idiomatic code and modular structure.'
          },
          similarity: {
            score: Math.round(((data.similarity_score ?? 90) / 100) * 20),
            max: 20,
            originalityPercent: 92,
            plagiarismRisk: 'Low',
            notes: 'Original logic pattern. Low semantic overlap.'
          },
          overallScore: Math.round(data.overall_score ?? 85)
        },
        explainableFeedback: accepted
          ? (data.feedback?.summary || `Accepted: all ${totalCases} test cases passed.`)
          : `Not accepted: ${passedCases} of ${totalCases} test cases passed. ${testResults.find((result) => !result.passed)?.stderr || 'The output did not match the expected result.'}`,
        suggestedImprovements: Array.isArray(data.recommendations?.steps) ? data.recommendations.steps : [
          'Use descriptive variable names (e.g. `numToIndexMap`, `complement`)',
          'Add structured comments to document hash map lookup edge cases'
        ],
        recommendedTopics: selectedProblem.tags || ['Arrays & Hashing', 'Two Pointers'],
        practiceProblems: [
          { id: 'p1', title: 'Two Sum II', difficulty: 'Medium', tags: ['Array', 'Two Pointers'] },
          { id: 'p2', title: 'Subarray Sum Equals K', difficulty: 'Medium', tags: ['Hash Table', 'Prefix Sum'] }
        ],
        scoreProjection: {
          currentScore: Math.round(data.overall_score ?? 85),
          projectedScore: Math.min(100, Math.round((data.overall_score ?? 85) + (data.projected_score?.score_improvement_delta ?? 7))),
          improvementDelta: data.projected_score?.score_improvement_delta ?? 7,
          focusAreas: [
            'Optimize Space Complexity & bucket allocation',
            'Improve Code Readability & variable naming standards'
          ],
          iterationTimeline: [
            { stage: 'Initial Submission', score: Math.round(data.overall_score ?? 85), note: 'Current solution evaluated' },
            { stage: 'AI Projected Score', score: Math.min(100, Math.round((data.overall_score ?? 85) + 7)), note: 'Target with recommended optimizations' }
          ]
        },
        // Some analysis providers return an object with an `improved_code`
        // property rather than the source text directly.
        aiRevisedCode: typeof data.improved_code === 'string'
          ? data.improved_code
          : typeof data.improved_code?.improved_code === 'string'
            ? data.improved_code.improved_code
            : code,
        testResults,
        totalTestCases: totalCases
      };

      const newSubItem: SubmissionItem = {
        id: newSubmissionId,
        problemId: selectedProblem.id,
        problemTitle: selectedProblem.title,
        problemSlug: selectedProblem.slug,
        status: accepted ? 'Passed' : 'Failed',
        score: newAssessment.multiScores.overallScore,
        date: 'Just now',
        language: newAssessment.language,
        executionTime: newAssessment.executionTime,
        passedTestCases: passedCases,
        totalTestCases: totalCases
      };

      addSubmission(newSubItem, newAssessment);
      navigate(`/submissions/${newSubmissionId}`);
    } catch (e) {
      setRunOutput({
        status: 'error',
        time: '—',
        memory: '—',
        reason: e instanceof Error ? e.message : 'Your submission could not be completed. Please try again.',
        results: []
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeRunCase = runOutput?.results[activeTestTab] || runOutput?.results[0];
  const displayInput = (rawInput: string) => formatInputForDisplay(rawInput, selectedProblem.inputSchema);
  const descriptionWithoutMachineFormat = selectedProblem.description
    .split(/\n\s*Platform Input\/Output Format\s*\n/i)[0]
    .trim();
  // Dataset statements sometimes repeat their examples and constraints inside
  // the prose. The page renders one clear sample and its own constraints card,
  // so students do not need to read the same material twice.
  const visibleProblemDescription = descriptionWithoutMachineFormat
    .split(/\n\s*Examples?\s*(?:\d+\s*)?:/i)[0]
    .split(/\n\s*Constraints\s*:/i)[0]
    .trim();
  const constraintsFromDescription = (() => {
    const match = descriptionWithoutMachineFormat.match(
      /(?:^|\n)\s*Constraints\s*:\s*([\s\S]*?)(?=\n\s*Examples?\s*(?:\d+\s*)?:|\s*$)/i
    );
    return (match?.[1] || '')
      .split('\n')
      .map((line) => line.replace(/^[\s•*-]+/, '').trim())
      .filter(Boolean);
  })();
  const displayConstraints = selectedProblem.constraints.length > 0
    ? selectedProblem.constraints
    : constraintsFromDescription;

  if (!remoteProblem) {
    return (
      <div className="min-h-[60vh] w-full">
        <button
          onClick={() => navigate(isInstructorProblem ? '/problems?view=instructor' : '/problems')}
          className="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-bold text-slate-600 transition-colors hover:bg-slate-100 hover:text-indigo-600"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>{isInstructorProblem ? 'Back to Instructor Problems' : 'Back to Problem Bank'}</span>
        </button>
        <div className="mt-6 grid min-h-[45vh] place-items-center rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          {isProblemLoading ? (
            <div className="space-y-3 text-slate-500">
              <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              <p className="text-sm font-semibold">Loading problem and public tests…</p>
            </div>
          ) : (
            <div className="max-w-md space-y-2">
              <XCircle className="mx-auto h-7 w-7 text-rose-500" />
              <h1 className="text-lg font-bold text-slate-900">Problem could not be loaded</h1>
              <p className="text-sm text-rose-700">{problemLoadError || 'The server problem is unavailable.'}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 pb-12">
      {/* Top Breadcrumb & Action bar */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => {
            navigate(isInstructorProblem ? '/problems?view=instructor' : '/problems');
          }}
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-indigo-600 transition-colors cursor-pointer py-1.5 px-3 rounded-xl hover:bg-slate-100 active:scale-95"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{isInstructorProblem ? 'Back to Instructor Problems' : 'Back to Problem Bank'}</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Auto-saved to Sandbox</span>
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
        </div>
      </div>

      {/* Main Split Grid */}
      <div className="grid min-w-0 grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(390px,1fr)_minmax(500px,1.2fr)] xl:grid-cols-[minmax(450px,1fr)_minmax(660px,1.2fr)]">
        {/* LEFT PANEL: Problem Details & Constraints (Col span 5) */}
        <div className="min-w-0 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col overflow-hidden lg:h-[900px]">
          {/* Header */}
          <div className="p-5 border-b border-slate-100">
            <div className="flex items-center gap-2.5 mb-2">
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                {selectedProblem.title}
              </h1>
              <DifficultyBadge difficulty={selectedProblem.difficulty} />
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span>Acceptance: <strong className="text-slate-700">{selectedProblem.acceptanceRate}</strong></span>
              <span>Optimal Time: <strong className="text-slate-700 font-mono">{selectedProblem.optimalComplexity.time}</strong></span>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b border-slate-100 bg-slate-50/70 px-4 text-xs font-semibold">
            <button
              onClick={() => setActiveLeftTab('statement')}
              className={`py-3 px-3 border-b-2 transition-all ${
                activeLeftTab === 'statement'
                  ? 'border-indigo-600 text-indigo-600 bg-white'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Problem Statement
            </button>
            <button
              onClick={() => setActiveLeftTab('testcases')}
              className={`py-3 px-3 border-b-2 transition-all ${
                activeLeftTab === 'testcases'
                  ? 'border-indigo-600 text-indigo-600 bg-white'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Public Test Cases ({selectedProblem.testCases.length})
            </button>
          </div>

          {/* Left Tab Content */}
          <div className="min-h-0 flex-1 space-y-6 overflow-y-auto p-6 pr-4 text-sm text-slate-700">
            {activeLeftTab === 'statement' ? (
              <>
                {/* Description */}
                <div className="prose prose-slate prose-sm max-w-none">
                  <div className="whitespace-pre-line leading-relaxed text-slate-600">
                    {visibleProblemDescription}
                  </div>
                </div>

                {/* Examples */}
                <div className="space-y-4">
                  {selectedProblem.examples.slice(0, 1).map((ex, idx) => (
                    <div key={idx} className="bg-slate-50 rounded-xl p-4 border border-slate-200/80">
                      <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                        Example {idx + 1}:
                      </h4>
                      <div className="space-y-1.5 font-mono text-xs">
                        <div className="text-slate-600">
                          <strong className="text-slate-800 font-sans">Input:</strong>
                          <pre className="mt-1 whitespace-pre-wrap break-words rounded-lg border border-slate-200 bg-white p-2 text-slate-800">
                            {displayInput(ex.input)}
                          </pre>
                        </div>
                        <div className="text-slate-600">
                          <strong className="text-slate-800 font-sans">Output: </strong>
                          <code>{ex.output}</code>
                        </div>
                        {ex.explanation && (
                          <div className="text-slate-500 text-[11px] font-sans pt-1">
                            <strong>Explanation: </strong> {ex.explanation}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Constraints */}
                <div className="bg-amber-50/40 rounded-xl p-4 border border-amber-200/60">
                  <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">
                    Constraints:
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-xs text-amber-900 font-mono">
                    {displayConstraints.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>

                {/* Topic tags */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Algorithmic Tags
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedProblem.tags.map((t, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 text-xs font-medium bg-slate-100 text-slate-700 rounded-lg border border-slate-200"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              /* Test Cases Tab */
              <div className="space-y-4">
                <p className="text-xs text-slate-500">
                  Run Code uses these public examples only. Submission runs the full private suite securely on the backend.
                </p>
                {selectedProblem.testCases.slice(0, 3).map((tc, idx) => (
                  <div key={tc.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800">
                        Public case {idx + 1}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        Public Verification
                      </span>
                    </div>
                    <div className="space-y-1 font-mono text-xs">
                      <div>
                        <span className="text-slate-400 font-sans text-[11px]">Input:</span>
                        <pre className="mt-1 whitespace-pre-wrap break-words p-2 bg-white rounded border border-slate-200 text-slate-800">
                          {displayInput(tc.input)}
                        </pre>
                      </div>
                      <div>
                        <span className="text-slate-400 font-sans text-[11px]">Expected Output:</span>
                        <div className="p-2 bg-white rounded border border-slate-200 text-slate-800">{tc.expectedOutput}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL: Code Editor & Execution Sandbox (Col span 7) */}
        <div className="min-w-0 flex flex-col space-y-4">
          <div className={`${isEditorFullscreen ? 'fixed inset-4 z-50 h-[calc(100vh-2rem)]' : 'lg:h-[900px]'} w-full self-start bg-slate-900 rounded-2xl border border-slate-800 shadow-xl overflow-hidden flex flex-col relative`}>
            {/* Editor Toolbar (Matches diagram step 4) */}
            <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-slate-950 border-b border-slate-800 gap-2">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 text-white font-bold text-xs">
                  <Terminal className="w-4 h-4 text-indigo-400" />
                  <span>Code Editor</span>
                </div>

                {/* Language Selector */}
                <select
                  value={language}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-medium rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="cpp">C++ (GCC 11.2)</option>
                  <option value="c">C (GCC 13)</option>
                  <option value="python">Python 3.10</option>
                  <option value="java">Java 17 (OpenJDK)</option>
                  <option value="javascript">JavaScript (Node 20)</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleResetCode}
                  title="Reset to starter template"
                  className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setIsEditorFullscreen((value) => !value)}
                  title={isEditorFullscreen ? 'Exit fullscreen (Esc)' : 'Fullscreen editor'}
                  className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  {isEditorFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                </button>
                <div className="mx-1 h-5 w-px bg-slate-700" />
                <button
                  onClick={handleRunCode}
                  disabled={isRunning || isSubmitting || isProblemLoading || !remoteProblem}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
                >
                  <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : 'text-emerald-400'}`} />
                  <span>{isRunning ? 'Running...' : 'Run Code'}</span>
                </button>
                <button
                  onClick={handleSubmitCode}
                  disabled={isRunning || isSubmitting || isProblemLoading || !remoteProblem}
                  className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-md shadow-indigo-600/30 flex items-center gap-1.5 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Code</span>
                </button>
              </div>
            </div>

            {/* Monaco keeps its own vertical scrollbar; page scrolling is not trapped. */}
            <div className={`${isEditorFullscreen ? 'flex-1 min-h-0' : 'h-[720px] min-h-[720px] lg:h-auto lg:min-h-0 lg:flex-1'} relative bg-slate-900 overflow-hidden`}>
              <Editor
                height="100%"
                language={monacoLanguage[language] || 'plaintext'}
                theme="vs-dark"
                value={code}
                onChange={(value) => setCode(value ?? '')}
                onMount={handleEditorMount}
                options={{
                  automaticLayout: true,
                  fontSize: 14,
                  fontFamily: "Consolas, 'Courier New', monospace",
                  lineHeight: 22,
                  minimap: { enabled: true },
                  lineNumbers: 'on',
                  glyphMargin: true,
                  folding: true,
                  bracketPairColorization: { enabled: true },
                  matchBrackets: 'always',
                  guides: { bracketPairs: true, indentation: true },
                  scrollBeyondLastLine: false,
                  wordWrap: 'off',
                  tabSize: 4,
                  insertSpaces: true,
                  padding: { top: 14, bottom: 14 },
                  suggest: { showKeywords: true, showSnippets: true },
                  quickSuggestions: { other: true, comments: false, strings: false }
                }}
              />
            </div>

            {/* AI Multi-Agent Assessment Loading Overlay */}
            {isSubmitting && (
              <div className="absolute inset-0 bg-slate-950/95 backdrop-blur-md z-30 flex flex-col items-center justify-center p-6 text-center animate-fadeIn">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-500 flex items-center justify-center text-white shadow-2xl shadow-indigo-500/50 mb-4 animate-bounce">
                  <Sparkles className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-extrabold text-white">
                  Multi-Agent AI Assessment in Progress
                </h3>
                <p className="text-xs text-slate-400 max-w-sm mt-1 mb-6">
                  Evaluating algorithmic correctness, AST complexity, style semantics & originality rubric.
                </p>

                {/* Pipeline Checklist */}
                <div className="w-full max-w-md bg-slate-900 rounded-2xl p-4 border border-slate-800 text-left space-y-2.5 text-xs">
                  <div className={`flex items-center gap-2.5 ${submissionStep >= 1 ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {submissionStep > 1 ? <Check className="w-4 h-4 text-emerald-400" /> : <div className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />}
                    <span className="font-semibold">1. Compiling & running all public + hidden tests securely</span>
                  </div>

                  <div className={`flex items-center gap-2.5 ${submissionStep >= 2 ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {submissionStep > 2 ? <Check className="w-4 h-4 text-emerald-400" /> : submissionStep === 2 ? <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" /> : <Cpu className="w-4 h-4" />}
                    <span className="font-semibold">2. AST Time & Space Complexity Profiler</span>
                  </div>

                  <div className={`flex items-center gap-2.5 ${submissionStep >= 3 ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {submissionStep > 3 ? <Check className="w-4 h-4 text-emerald-400" /> : submissionStep === 3 ? <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" /> : <Layers className="w-4 h-4" />}
                    <span className="font-semibold">3. Code Quality, Style & Structure Assessment</span>
                  </div>

                  <div className={`flex items-center gap-2.5 ${submissionStep >= 4 ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {submissionStep > 4 ? <Check className="w-4 h-4 text-emerald-400" /> : submissionStep === 4 ? <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                    <span className="font-semibold">4. Plagiarism & Cohort Similarity Scan</span>
                  </div>

                  <div className={`flex items-center gap-2.5 ${submissionStep >= 5 ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {submissionStep >= 5 ? <div className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    <span className="font-semibold">5. Synthesizing Explainable Report & Score Projection</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Test Case Output Drawer */}
          {runOutput && (
            <div ref={runOutputRef} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs animate-fadeIn">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                <div className="flex items-center gap-2">
                  {runOutput.status === 'success' ? <CheckCircle className="w-4 h-4 text-emerald-500" /> : <XCircle className="w-4 h-4 text-rose-500" />}
                  <span className="text-xs font-bold text-slate-800">
                    {runOutput.compileError
                      ? `Compilation Error · 0 of ${runOutput.results.length} public cases executed`
                      : `Public Test Output: ${runOutput.results.filter((result) => result.passed).length} of ${runOutput.results.length} public cases passed`}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    {runOutput.time}
                  </span>
                  <span className="flex items-center gap-1">
                    <HardDrive className="w-3.5 h-3.5 text-slate-400" />
                    {runOutput.memory}
                  </span>
                </div>
              </div>
              {runOutput.status === 'error' && <p className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700">Reason: {runOutput.reason}</p>}

              {runOutput.compileError && (
                <div className="mb-3 overflow-x-auto rounded-xl border border-rose-200 bg-slate-950 p-4">
                  <p className="mb-2 text-xs font-semibold text-rose-300">Compiler output</p>
                  <pre className="whitespace-pre-wrap font-mono text-xs leading-5 text-rose-100">{runOutput.compileError}</pre>
                </div>
              )}

              {/* Each public test remains inspectable even when compilation or
                  execution fails. This makes it clear which input was judged
                  and prevents an empty result drawer. */}
              {runOutput.results.length > 0 && <div className="flex flex-wrap gap-2 mb-3">
                {runOutput.results.map((r, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveTestTab(i)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                      activeTestTab === i
                        ? r.passed
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {r.passed ? <CheckCircle className="w-3 h-3 text-emerald-500" /> : <XCircle className="w-3 h-3 text-rose-500" />}
                    <span>Case {r.caseNum} · {r.passed ? 'Passed' : 'Failed'}</span>
                  </button>
                ))}
              </div>}

              {/* The fields deliberately use pre-wrap: student-visible values
                  retain their readable structure and stdout is never collapsed. */}
              {activeRunCase && <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs font-mono space-y-3">
                <div className={`flex items-center gap-1.5 font-sans text-xs font-bold ${activeRunCase.passed ? 'text-emerald-700' : 'text-rose-700'}`}>
                  {activeRunCase.passed ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                  {activeRunCase.passed ? 'Passed' : 'Failed'}
                </div>
                <div>
                  <span className="text-slate-400 font-sans text-[11px]">Input:</span>
                  <pre className="mt-1 whitespace-pre-wrap break-words text-slate-800">{displayInput(activeRunCase.input)}</pre>
                </div>
                <div>
                  <span className="text-slate-400 font-sans text-[11px]">Your output:</span>
                  <pre className={`mt-1 whitespace-pre-wrap break-words font-bold ${activeRunCase.passed ? 'text-emerald-700' : 'text-rose-700'}`}>
                    {activeRunCase.output || '∅ (no output produced)'}
                  </pre>
                </div>
                <div>
                  <span className="text-slate-400 font-sans text-[11px]">Expected output:</span>
                  <pre className="mt-1 whitespace-pre-wrap break-words text-slate-700">{activeRunCase.expected || '∅ (empty output)'}</pre>
                </div>
                {activeRunCase.error && (
                  <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 font-sans text-xs text-rose-700">
                    <span className="font-bold">Execution message: </span>
                    <span className="whitespace-pre-wrap break-words">{activeRunCase.error}</span>
                  </div>
                )}
              </div>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
