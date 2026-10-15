import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertTriangle, ArrowLeft, BookOpen, CheckCircle2, Clock3, Code2, HardDrive, Lightbulb, Sparkles, TrendingUp, XCircle } from 'lucide-react';
import { useAuth } from '../../context/useAuth';
import { CircularGauge } from '../common/CircularGauge';
import { CompilerFeedback } from './CompilerFeedback';

type R = Record<string, any>;
type Submission = { submission_id: string; student_id: string; problem_id: string; assignment_id: number | null; language: string; code: string; status: string; overall_score: number | null; correctness_score: number | null; complexity_score: number | null; style_score: number | null; complexity_details: R | null; score_breakdown: R | null; execution_result: R | null; feedback: unknown; recommendations: unknown; improved_code: unknown; projected_score: unknown; created_at: string };
const obj = (x: unknown): R => x && typeof x === 'object' && !Array.isArray(x) ? x as R : {};
const str = (x: unknown) => typeof x === 'string' ? x : '';
const list = (x: unknown): string[] => Array.isArray(x) ? x.filter((v): v is string => typeof v === 'string' && !!v.trim()) : [];
const num = (x: unknown): number | null => typeof x === 'number' && Number.isFinite(x) ? x : null;
const formatScore = (score: number) => Number(score.toFixed(1));
const explainComplexity = (value: string, dimension: 'time' | 'space') => {
  const normalized = value.replace(/\s/g, '').toLowerCase();
  const resource = dimension === 'time' ? 'work' : 'extra memory';
  if (normalized === 'o(1)') return `O(1) means ${resource} stays roughly constant as the input grows.`;
  if (normalized === 'o(logn)') return `O(log n) means ${resource} grows slowly as the input grows.`;
  if (normalized === 'o(n)') return `O(n) means ${resource} grows in proportion to the input size.`;
  if (normalized === 'o(nlogn)') return `O(n log n) means ${resource} grows a little faster than the input size.`;
  if (normalized === 'o(n^2)' || normalized === 'o(n²)') return `O(n²) means ${resource} can grow with the square of the input size.`;
  return '';
};
const grade = (n: number) => n >= 90 ? 'Excellent (A)' : n >= 80 ? 'Very Good (B)' : n >= 70 ? 'Good (C)' : n >= 60 ? 'Satisfactory (D)' : 'Needs Improvement (F)';
const parseSuggestion = (value: unknown): R | null => {
  if (typeof value === 'string') {
    try {
      const parsed: unknown = JSON.parse(value);
      return obj(parsed);
    } catch {
      return { improved_code: value };
    }
  }
  return value && typeof value === 'object' && !Array.isArray(value) ? value as R : null;
};

export const AssessmentResultView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { authFetch } = useAuth();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revisionLoading, setRevisionLoading] = useState(false);
  const [revisionError, setRevisionError] = useState('');
  useEffect(() => {
    if (!id) { setError('Choose a saved submission from your history.'); setLoading(false); return; }
    let cancelled = false;
    (async () => {
      try {
        const response = await authFetch(`/api/submissions/${encodeURIComponent(id)}`, { cache: 'no-store' });
        if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || 'Submission could not be loaded.'); }
        const data: Submission = await response.json();
        const problemResponse = await authFetch(`/api/problems/${encodeURIComponent(data.problem_id)}`, { cache: 'no-store' });
        const problem = problemResponse.ok ? await problemResponse.json() : null;
        if (!cancelled) { setSubmission(data); setTitle(problem?.title || data.problem_id); }
      } catch (e) { if (!cancelled) setError(e instanceof Error ? e.message : 'Submission could not be loaded.'); }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [authFetch, id]);

  const d = useMemo(() => {
    if (!submission) return null;
    const execution = obj(submission.execution_result), rawComplexity = obj(submission.complexity_details), scoreBreakdown = obj(submission.score_breakdown), feedback = obj(submission.feedback), recommendations = obj(submission.recommendations), projection = obj(submission.projected_score);
    const complexity = { ...rawComplexity };
    for (const field of ['reasoning', 'scoring_reason', 'space_scoring_reason', 'optimization_suggestion']) {
      const value = str(complexity[field]);
      if (/private\s+benchmark|verified\s+complexity\s+benchmark/i.test(value)) {
        complexity[field] = field === 'space_scoring_reason'
          ? 'Space complexity was assessed from the submitted code.'
          : field === 'optimization_suggestion'
            ? ''
            : 'Complexity was assessed from the submitted code.';
      }
    }
    const results = Array.isArray(execution.results) ? execution.results : [];
    const passed = Number(execution.passed_cases || 0), total = Number(execution.total_cases || passed + Number(execution.failed_cases || 0));
    const accepted = total > 0 && passed === total;
    const publicCases = results
      .map((result: R, index: number) => ({ result, ordinal: index + 1 }))
      .filter(({ result }: { result: R }) => !(result.is_hidden ?? result.isHidden));
    const publicPassingCases = publicCases.filter(({ result }: { result: R }) => String(result.status).toLowerCase() === 'accepted');
    const failedPublicCases = publicCases.filter(({ result }: { result: R }) => String(result.status).toLowerCase() !== 'accepted');
    const revealedCase = obj(execution.revealed_feedback_case);
    const hasRevealedCase = Boolean(str(revealedCase.status));
    const savedSteps = list(feedback.improvement_steps).length ? list(feedback.improvement_steps) : list(recommendations.steps).length ? list(recommendations.steps) : list(feedback.weaknesses);
    const isGenericFallback = feedback.feedback_source === 'fallback'
      || str(feedback.mentor_feedback).includes('temporarily unavailable')
      || savedSteps.some((step: string) => step.includes('Review the correctness, complexity, and style evidence above'));
    const taskName = `${title} ${submission.problem_id}`.toLowerCase();
    const submittedSource = String(submission.code || '').toLowerCase();
    const mentorText = str(feedback.mentor_feedback);
    const mentionsOtherProblem = /\btwo\s*sum\b|\btwosum\s*\(/i.test(mentorText)
      && !(/\btwo\s*sum\b|\btwosum\s*\(/i.test(taskName));
    const unsupportedHashAdvice = /hash\s*(map|lookup|set)|hashset/i.test(mentorText)
      && !/(unordered_map|hashmap|hashset|\bdict\s*\(|\bmap\s*<|new\s+map)/i.test(submittedSource);
    const unrelatedSavedFeedback = mentionsOtherProblem || unsupportedHashAdvice;
    const evidenceSteps = [
      ...(String(execution.compile_status || '').toLowerCase() !== 'success' ? ['Fix the first compiler diagnostic, then run the public examples again.'] : []),
      ...failedPublicCases.slice(0, 2).map(({ ordinal }: { ordinal: number }) => `Review public test case ${ordinal} and rerun the examples.`),
      ...(hasRevealedCase ? ['Trace the revealed feedback case, compare your output with the expected output, then revise the condition causing the difference.'] : []),
      ...(str(complexity.optimization_suggestion) && str(complexity.optimization_suggestion).toLowerCase() !== 'no optimization suggestion was available.' ? [str(complexity.optimization_suggestion)] : []),
    ];
    const hasCorrectnessIssue = String(execution.compile_status || '').toLowerCase() !== 'success' || failedPublicCases.length > 0 || hasRevealedCase;
    const styleOnlyAdvice = (step: string) => /\b(comment|naming|readability|maintainability|rename)\b/i.test(step);
    const steps = hasCorrectnessIssue
      ? [...evidenceSteps, ...savedSteps.filter((step: string) => !styleOnlyAdvice(step))]
      : (isGenericFallback || unrelatedSavedFeedback)
      ? evidenceSteps.length ? evidenceSteps : [`Review the saved score evidence for ${title || submission.problem_id}; no failed public example or specific code change was recorded.`]
      : savedSteps;
    const evidenceStrengths = [
      ...(passed > 0 ? [`Passed ${passed} of ${total} public examples for ${title || submission.problem_id}.`] : []),
      ...(str(complexity.time_complexity) ? [`The saved analysis reports time complexity ${str(complexity.time_complexity)}${str(complexity.space_complexity) ? ` and space complexity ${str(complexity.space_complexity)}` : ''}.`] : []),
    ];
    const strengths = (isGenericFallback || unrelatedSavedFeedback) ? evidenceStrengths : list(feedback.strengths);
    const time = num(complexity.time_score), space = num(complexity.space_score);
    const correctness = num(submission.correctness_score);
    const timeMax = num(complexity.time_score_max) ?? 25;
    const spaceMax = num(complexity.space_score_max) ?? 25;
    const style = num(submission.style_score);
    const weightedMark = (raw: number | null, rawMax: number, weight: number) => raw == null ? null : (raw / rawMax) * weight;
    const rows = [
      { name: 'Correctness', score: weightedMark(correctness, 100, 20), max: 20, color: 'bg-blue-500', detail: total ? `${passed}/${total} test cases passed. Weight: 20%.` : 'Test result unavailable. Weight: 20%.' },
      { name: 'Time complexity', score: weightedMark(time, timeMax, 30), max: 30, color: 'bg-cyan-500', detail: [str(complexity.time_complexity), str(complexity.time_classification), explainComplexity(str(complexity.time_complexity), 'time'), 'Weight: 30%.'].filter(Boolean).join(' · ') || 'Time analysis unavailable.' },
      { name: 'Space complexity', score: weightedMark(space, spaceMax, 30), max: 30, color: 'bg-amber-500', detail: [str(complexity.space_complexity), str(complexity.space_classification), explainComplexity(str(complexity.space_complexity), 'space'), 'Weight: 30%.'].filter(Boolean).join(' · ') || 'Space analysis unavailable.' },
      { name: 'Style', score: weightedMark(style, 100, 20), max: 20, color: 'bg-violet-500', detail: 'Code style assessment. Weight: 20%.' }
    ];
    const legacyFixedProjection = /top 12%|quick pass on clean naming/i.test(str(projection.motivational_message));
    const compileFailed = String(execution.compile_status || '').toLowerCase() === 'error';
    const compilerDiagnostics = str(execution.compile_error) || str(execution.stderr);
    const scoreGate = obj(scoreBreakdown.correctness_gate);
    const rawScore = num(scoreGate.raw_score);
    const correctnessFactor = num(scoreGate.correctness_factor);
    const scoreCap = num(scoreGate.score_cap);
    const storedProjection = projection.available === false || legacyFixedProjection || str(projection.projection_basis) !== 'correctness_fix_scenario'
      ? null
      : num(projection.projected_score);
    const correctnessNeedsFix = correctness != null && correctness < 100;
    const projected = storedProjection ?? (correctnessNeedsFix && rawScore != null ? Math.max(num(submission.overall_score) ?? 0, rawScore) : null);
    const gain = projected != null && submission.overall_score != null ? Math.max(0, projected - submission.overall_score) : null;
    const projectionAssumptions = storedProjection != null
      ? list(projection.assumptions)
      : projected != null
        ? ['The revised code passes every evaluated test case.', 'Its time complexity, space complexity, and style scores remain unchanged.']
        : [];
    const projectionMessage = storedProjection != null
      ? str(projection.message)
      : projected != null
        ? 'This expected score scenario is calculated from saved assessment evidence. Submit the exact revised code to the judge to confirm it.'
        : '';
    return { execution, complexity, feedback, recommendations, results, publicCases, publicPassingCases, failedPublicCases, revealedCase, hasRevealedCase, hasCorrectnessIssue, passed, total, accepted, steps, strengths, rows, projected, gain, projectionAssumptions, projectionMessage, compileFailed, compilerDiagnostics, isGenericFallback, unrelatedSavedFeedback, rawScore, correctnessFactor, scoreCap };
  }, [submission]);
  const revisedSuggestion = useMemo(() => parseSuggestion(submission?.improved_code), [submission?.improved_code]);
  const revisedCode = str(revisedSuggestion?.improved_code) || str(revisedSuggestion?.code) || str(revisedSuggestion?.suggested_code) || str(revisedSuggestion?.revised_code);
  const taskText = `${title} ${submission?.problem_id || ''}`.toLowerCase();
  const unrelatedTwoSumSuggestion = /\btwo\s*sum\b|\btwosum\s*\(/i.test(revisedCode)
    && !(/\btwo\s*sum\b|\btwosum\s*\(/i.test(taskText));
  const revisionUnavailable = !revisedCode || unrelatedTwoSumSuggestion;
  const revisedChanges = Array.isArray(revisedSuggestion?.changes) ? revisedSuggestion.changes.map(obj) : [];
  const revisedExplanation = str(revisedSuggestion?.improvement_explanation) || str(revisedSuggestion?.change_summary);

  const generateRevision = async () => {
    if (!id || revisionLoading) return;
    setRevisionLoading(true);
    setRevisionError('');
    try {
      const response = await authFetch(`/api/submissions/${encodeURIComponent(id)}/revision`, { method: 'POST' });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || 'Could not generate a revised solution. Please try again.');
      setSubmission(current => current ? { ...current, improved_code: body.improved_code } : current);
    } catch (e) {
      setRevisionError(e instanceof Error ? e.message : 'Could not generate a revised solution. Please try again.');
    } finally {
      setRevisionLoading(false);
    }
  };

  if (loading) return <main className="mx-auto w-full max-w-7xl py-12 text-sm text-slate-500" aria-busy="true">Loading saved assessment…</main>;
  if (!submission || !d) return <main className="mx-auto w-full max-w-3xl space-y-4 py-12"><p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error || 'Submission not found.'}</p><Link to="/submissions" className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-700"><ArrowLeft className="h-4 w-4" />Submission history</Link></main>;
  const score = num(submission.overall_score);
  const savedSummary = str(d.feedback.mentor_feedback) || str(d.feedback.key_insight) || str(d.feedback.summary);
  const evidenceSummary = d.compileFailed
    ? `The saved assessment for ${title || submission.problem_id} shows that this ${submission.language} submission did not compile. Start with the compiler feedback, then rerun the public examples.`
    : d.failedPublicCases.length
      ? `The saved assessment for ${title || submission.problem_id} shows ${d.passed}/${d.total} public examples passed. Start by reviewing public test case ${d.failedPublicCases[0].ordinal}.`
      : d.hasRevealedCase
        ? `The saved assessment includes one revealed feedback case. Compare its input, expected output, and your output to find the condition your solution missed.`
      : d.total
        ? `The saved assessment for ${title || submission.problem_id} shows ${d.passed}/${d.total} public examples passed. The saved explanation was not specific to this problem; use the score evidence below for its complexity and style findings.`
        : `The saved explanation for ${title || submission.problem_id} was not specific to this submission. Review the available assessment evidence below.`;
  const summary = d.hasCorrectnessIssue || d.isGenericFallback || d.unrelatedSavedFeedback
    ? evidenceSummary
    : savedSummary || (d.total ? 'Review the saved evidence and improvement notes below.' : 'No saved feedback summary is available for this submission.');
  const projected = d.projected != null && score != null;

  return <main className="mx-auto w-full min-w-0 max-w-7xl space-y-5 pb-14">
    <div className="flex flex-wrap items-center justify-between gap-3"><Link to="/submissions" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-indigo-700"><ArrowLeft className="h-4 w-4" />Submission history</Link><Link to={`/problems/${encodeURIComponent(submission.problem_id)}${submission.assignment_id != null ? `?assignmentId=${encodeURIComponent(String(submission.assignment_id))}` : ''}`} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white shadow-md shadow-indigo-600/20 hover:bg-indigo-700"><Code2 className="h-4 w-4" />Revise solution</Link></div>
    <header className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6"><div className="flex flex-col justify-between gap-6 md:flex-row md:items-center"><div className="min-w-0 flex-1 space-y-3"><span className={`inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-semibold ${d.accepted ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-rose-200 bg-rose-50 text-rose-700'}`}>{d.accepted ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}{d.total ? `${d.accepted ? 'Accepted' : 'Not accepted'} · ${d.passed}/${d.total} test cases passed` : submission.status}</span><div><h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{title || submission.problem_id}</h1><p className="mt-1 text-sm text-slate-500">Assessment result</p></div><div className="flex flex-wrap gap-2 text-xs text-slate-600"><span className="rounded-md bg-slate-100 px-2.5 py-1 font-mono">ID: <b className="text-slate-800">{submission.submission_id}</b></span><span className="rounded-md bg-slate-100 px-2.5 py-1">Language: <b className="text-slate-800">{submission.language}</b></span>{num(d.execution.runtime_ms) != null && <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2.5 py-1"><Clock3 className="h-3.5 w-3.5" />Runtime: <b>{d.execution.runtime_ms} ms</b></span>}{str(d.complexity.time_complexity) && <span className="rounded-md bg-slate-100 px-2.5 py-1">Time: <b>{d.complexity.time_complexity}</b></span>}<span className="rounded-md bg-slate-100 px-2.5 py-1">Space: <b>{str(d.complexity.space_complexity) || 'Analysis unavailable'}</b></span>{num(d.execution.memory_kb) != null && num(d.execution.memory_kb)! > 0 && <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2.5 py-1"><HardDrive className="h-3.5 w-3.5" />Measured memory: <b>{(d.execution.memory_kb / 1024).toFixed(1)} MB</b></span>}<span className="rounded-md bg-slate-100 px-2.5 py-1">{new Date(submission.created_at).toLocaleString()}</span>{submission.assignment_id != null ? <Link to="/courses" className="inline-flex items-center gap-1 rounded-md bg-indigo-50 px-2.5 py-1 text-indigo-700"><BookOpen className="h-3.5 w-3.5" />Assignment #{submission.assignment_id}</Link> : <span className="rounded-md bg-slate-100 px-2.5 py-1">Independent practice</span>}</div></div><div className="flex items-center gap-4 self-start rounded-xl border border-slate-200 bg-slate-50 p-4 md:self-auto">{score != null && <CircularGauge score={score} maxScore={100} size={110} strokeWidth={9} sublabel="Score" />}<div><span className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500">Overall grade</span><span className="block text-lg font-bold text-slate-900">{score == null ? 'Not scored' : grade(score)}</span>{score != null && <span className="text-xs text-slate-500">Saved evaluation</span>}</div></div></div></header>

    {submission.assignment_id == null && <section className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950"><div><b>This is Independent Practice.</b><span className="ml-1 text-amber-800">It improves your personal practice history, but does not update an instructor course roster or similarity review.</span></div><Link to="/courses" className="rounded-lg bg-amber-700 px-3 py-1.5 text-xs font-bold text-white hover:bg-amber-800">Open My Courses</Link></section>}

    {d.compileFailed && <CompilerFeedback diagnostics={d.compilerDiagnostics || 'Compilation failed. No test cases were run.'} />}

    {(d.failedPublicCases.length > 0 || d.hasRevealedCase) && <section className="rounded-xl border border-rose-200 bg-white p-5"><div className="flex items-center gap-2 border-b border-slate-100 pb-3"><AlertTriangle className="h-4 w-4 text-rose-600"/><div><h2 className="font-bold text-slate-900">First issue to fix</h2><p className="text-xs text-slate-500">Correctness comes before score refinements or style suggestions.</p></div></div>{d.failedPublicCases.slice(0, 1).map(({ result, ordinal }: { result: R; ordinal: number }) => <div key={`public-${ordinal}`} className="mt-3 rounded-lg bg-rose-50 p-4"><div className="flex items-center justify-between gap-3 text-sm"><span className="font-semibold text-slate-900">Public test case {ordinal}</span><span className="text-xs font-semibold capitalize text-rose-700">{String(result.status || 'Failed').replace(/_/g, ' ')}</span></div><p className="mt-2 text-sm text-slate-700">{str(result.error_message) || 'Your output did not match the expected output.'}</p><div className="mt-3 grid gap-3 md:grid-cols-3">{[['Input', result.input], ['Expected output', result.expected_output], ['Your output', result.actual_output]].map(([label, value]) => <div key={String(label)}><p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{label}</p><pre className="mt-1 overflow-auto rounded bg-white p-2 text-xs text-slate-800">{str(value) || '—'}</pre></div>)}</div></div>)}{d.hasRevealedCase && <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-4"><div className="flex items-center justify-between gap-3 text-sm"><span className="font-semibold text-slate-900">Revealed feedback case</span><span className="text-xs font-semibold capitalize text-amber-800">{str(d.revealedCase.status).replace(/_/g, ' ').toLowerCase()}</span></div><p className="mt-2 text-sm text-slate-700">{str(d.revealedCase.reason) || 'This learning case did not pass.'}</p><div className="mt-3 grid gap-3 md:grid-cols-3">{[['Input', d.revealedCase.input], ['Expected output', d.revealedCase.expected_output], ['Your output', d.revealedCase.actual_output]].map(([label, value]) => <div key={String(label)}><p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{label}</p><pre className="mt-1 overflow-auto rounded bg-white p-2 text-xs text-slate-800">{str(value) || '—'}</pre></div>)}</div><p className="mt-3 text-xs text-slate-600">This is one learning case selected from private evaluation. Other private cases remain protected.</p></div>}</section>}

    <div className="grid gap-6 xl:grid-cols-12"><section className="relative min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-900 p-5 text-white sm:p-6 xl:col-span-8"><div className="hidden"/><div className="flex flex-col justify-between gap-6 lg:flex-row"><div className="min-w-0 flex-1 space-y-4"><div className="flex items-center gap-3"><span className="rounded-2xl border border-indigo-400/20 bg-indigo-500/20 p-2.5 text-indigo-200"><Sparkles className="h-5 w-5"/></span><div><span className="text-[11px] font-extrabold uppercase tracking-wider text-indigo-200">Explainable feedback</span><h2 className="text-xl font-extrabold sm:text-2xl">What to improve next</h2></div></div><p className="max-w-3xl text-sm leading-relaxed text-slate-100 sm:text-base">{summary}</p>{d.feedback.feedback_source === 'fallback'&&<p className="rounded-lg border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-xs text-amber-100">AI feedback could not be generated for this submission. The notes below use available analysis only.</p>}{d.steps.length ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{d.steps.slice(0,3).map((step: string,i: number)=><article key={i} className="rounded-2xl border border-white/10 bg-white/[.06] p-4"><div className="flex items-center gap-2 text-xs font-bold text-emerald-300"><CheckCircle2 className="h-4 w-4"/>Improvement {i+1}</div><p className="mt-2 text-xs leading-relaxed text-slate-200">{step}</p></article>)}</div>:<div className="rounded-xl border border-white/10 bg-white/[.04] px-4 py-3 text-sm text-slate-300">No saved improvement steps for this submission.</div>}</div>{projected&&<aside className="w-full shrink-0 rounded-2xl border border-white/10 bg-white/[.06] p-4 lg:w-64"><span className="text-[11px] font-bold uppercase text-slate-300">Expected score scenario</span><div className="mt-3 flex items-end justify-between"><div><span className="font-mono text-4xl font-extrabold text-emerald-300">+{Number((d.gain ?? 0).toFixed(1))}</span><span className="ml-1 text-xs text-slate-300">pts</span></div><TrendingUp className="h-6 w-6 text-emerald-300"/></div><div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-emerald-400" style={{width:`${Math.max(0,Math.min(100,d.projected))}%`}}/></div><p className="mt-3 text-xs text-slate-300">Current {score}/100. Expected {d.projected}/100 if the revision passes every evaluated case.</p>{d.projectionAssumptions.map((assumption: string,index: number)=><p key={index} className="mt-2 text-xs text-slate-300">• {assumption}</p>)}<p className="mt-3 text-xs font-semibold text-amber-200">{d.projectionMessage || 'Submit the exact revised code to receive a verified score.'}</p></aside>}</div></section>
    <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 xl:col-span-4"><div className="flex items-center justify-between border-b border-slate-100 pb-3"><div><h2 className="font-bold text-slate-900">Score evidence</h2><p className="text-xs text-slate-400">Student rubric: correctness 20% · time 30% · space 30% · style 20%</p></div>{score!=null&&<span className="rounded-lg bg-slate-100 px-2.5 py-1 font-mono text-xs font-bold">{score}/100</span>}</div>{d.rawScore!=null&&d.correctnessFactor!=null&&<div className="rounded-lg border border-indigo-100 bg-indigo-50 p-3 text-xs text-indigo-950"><p><b>Raw quality score:</b> {formatScore(d.rawScore)}/100</p><p className="mt-1"><b>Correctness factor:</b> {formatScore(d.correctnessFactor*100)}%</p>{d.scoreCap!=null&&<p className="mt-1"><b>Not accepted cap:</b> {d.scoreCap}/100. Fix every failed case to unlock the full score.</p>}<p className="mt-1"><b>Final score:</b> {score}/100</p></div>}<div className="space-y-2.5">{d.rows.map((row: any)=><article key={row.name} className="rounded-lg border border-slate-200 bg-slate-50 p-3"><div className="flex items-center justify-between"><span className="text-xs font-bold text-slate-800">{row.name}</span><span className="font-mono text-xs font-extrabold">{row.score==null?'—':`${formatScore(row.score)}/${row.max}`}</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200"><div className={`h-full rounded-full ${row.color}`} style={{width:`${row.score==null?0:Math.max(0,Math.min(100,(row.score/row.max)*100))}%`}}/></div><p className="mt-1.5 text-[11px] leading-snug text-slate-500">{row.detail}</p></article>)}</div><div className="border-t border-slate-100 pt-3"><div className="flex items-center justify-between text-xs"><b>Test cases</b><span className={`rounded border px-2 py-0.5 ${d.accepted?'border-emerald-200 bg-emerald-50 text-emerald-700':'border-rose-200 bg-rose-50 text-rose-700'}`}>{d.passed}/{d.total} passed</span></div></div></section></div>
    {(str(d.complexity.reasoning)||str(d.complexity.optimization_suggestion)||str(d.complexity.scoring_reason)||list(d.feedback.strengths).length>0)&&<section className="grid gap-5 md:grid-cols-2">{(str(d.complexity.reasoning)||str(d.complexity.optimization_suggestion)||str(d.complexity.scoring_reason))&&<article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-3"><span className="rounded-xl bg-cyan-50 p-2 text-cyan-700"><Lightbulb className="h-4 w-4"/></span><h2 className="font-bold text-slate-900">Complexity analysis</h2></div>{[d.complexity.reasoning,d.complexity.optimization_suggestion,d.complexity.scoring_reason].filter((x:any)=>typeof x==='string'&&x.trim()).map((x:string,i:number)=><p key={i} className="mt-3 text-sm leading-relaxed text-slate-600">{x}</p>)}</article>}{list(d.feedback.strengths).length>0&&<article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-bold text-slate-900">What went well</h2><ul className="mt-3 space-y-2">{list(d.feedback.strengths).map((x,i)=><li key={i} className="text-sm text-slate-600">• {x}</li>)}</ul></article>}</section>}
{/*
    <div className="grid gap-6 xl:grid-cols-12"><section className="relative min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-900 p-5 text-white sm:p-6 xl:col-span-8"><div className="hidden"/><div className="flex flex-col justify-between gap-6 lg:flex-row"><div className="min-w-0 flex-1 space-y-4"><div className="flex items-center gap-3"><span className="rounded-2xl border border-indigo-400/20 bg-indigo-500/20 p-2.5 text-indigo-200"><Sparkles className="h-5 w-5"/></span><div><span className="text-[11px] font-extrabold uppercase tracking-wider text-indigo-200">Explainable feedback</span><h2 className="text-xl font-extrabold sm:text-2xl">What to improve next</h2></div></div><p className="max-w-3xl text-sm leading-relaxed text-slate-100 sm:text-base">{summary}</p>{d.feedback.feedback_source === 'fallback'&&<p className="rounded-lg border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-xs text-amber-100">AI feedback could not be generated for this submission. The notes below use available analysis only.</p>}{revisionUnavailable&&<div className="space-y-2 rounded-lg border border-amber-300/20 bg-amber-300/10 px-3 py-3 text-xs text-amber-100"><p>A task-specific rewrite was not saved with this assessment. You can request it again now.</p><button type="button" onClick={generateRevision} disabled={revisionLoading} className="rounded-md bg-white/10 px-3 py-2 font-semibold text-white hover:bg-white/20 disabled:cursor-wait disabled:opacity-60">{revisionLoading ? 'Generating task-specific code…' : 'Generate revised code'}</button>{revisionError&&<p role="alert" className="text-rose-200">{revisionError}</p>}</div>}{unrelatedTwoSumSuggestion&&!revisionUnavailable&&<p className="rounded-lg border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-xs text-amber-100">An older code suggestion did not match this problem and has been hidden.</p>}{d.steps.length ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{d.steps.slice(0,3).map((step: string,i: number)=><article key={i} className="rounded-2xl border border-white/10 bg-white/[.06] p-4"><div className="flex items-center gap-2 text-xs font-bold text-emerald-300"><CheckCircle2 className="h-4 w-4"/>Improvement {i+1}</div><p className="mt-2 text-xs leading-relaxed text-slate-200">{step}</p></article>)}</div>:<div className="rounded-xl border border-white/10 bg-white/[.04] px-4 py-3 text-sm text-slate-300">No saved improvement steps for this submission.</div>}</div>{projected&&<aside className="w-full shrink-0 rounded-2xl border border-white/10 bg-white/[.06] p-4 lg:w-64"><span className="text-[11px] font-bold uppercase text-slate-300">Projected gain</span><div className="mt-3 flex items-end justify-between"><div><span className="font-mono text-4xl font-extrabold text-emerald-300">+{Number(d.gain.toFixed(1))}</span><span className="ml-1 text-xs text-slate-300">pts</span></div><TrendingUp className="h-6 w-6 text-emerald-300"/></div><div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-emerald-400" style={{width:`${Math.max(0,Math.min(100,d.projected))}%`}}/></div><p className="mt-3 text-xs text-slate-300">Current {score}/100. Projected {d.projected}/100.</p></aside>}</div></section>
    <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 xl:col-span-4"><div className="flex items-center justify-between border-b border-slate-100 pb-3"><div><h2 className="font-bold text-slate-900">Score evidence</h2><p className="text-xs text-slate-400">Each category is shown on a 100-point scale</p></div>{score!=null&&<span className="rounded-lg bg-slate-100 px-2.5 py-1 font-mono text-xs font-bold">{score}/100</span>}</div><div className="space-y-2.5">{d.rows.map((row: any)=><article key={row.name} className="rounded-lg border border-slate-200 bg-slate-50 p-3"><div className="flex items-center justify-between"><span className="text-xs font-bold text-slate-800">{row.name}</span><span className="font-mono text-xs font-extrabold">{row.score==null?'—':`${formatScore(row.score)}/${row.max}`}</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200"><div className={`h-full rounded-full ${row.color}`} style={{width:`${row.score==null?0:Math.max(0,Math.min(100,row.score))}%`}}/></div><p className="mt-1.5 text-[11px] leading-snug text-slate-500">{row.detail}</p></article>)}</div><div className="border-t border-slate-100 pt-3"><div className="flex items-center justify-between text-xs"><b>Test cases</b><span className={`rounded border px-2 py-0.5 ${d.accepted?'border-emerald-200 bg-emerald-50 text-emerald-700':'border-rose-200 bg-rose-50 text-rose-700'}`}>{d.publicPassingCases.length} passed</span></div></div></section></div>
    {(str(d.complexity.reasoning)||str(d.complexity.optimization_suggestion)||str(d.complexity.scoring_reason)||d.strengths.length>0)&&<section className="grid gap-5 md:grid-cols-2">{(str(d.complexity.reasoning)||str(d.complexity.optimization_suggestion)||str(d.complexity.scoring_reason))&&<article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-3"><span className="rounded-xl bg-cyan-50 p-2 text-cyan-700"><Lightbulb className="h-4 w-4"/></span><h2 className="font-bold text-slate-900">Complexity analysis</h2></div>{[d.complexity.reasoning,d.complexity.optimization_suggestion,d.complexity.scoring_reason].filter((x:any)=>typeof x==='string'&&x.trim()).map((x:string,i:number)=><p key={i} className="mt-3 text-sm leading-relaxed text-slate-600">{x}</p>)}</article>}{d.strengths.length>0&&<article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-bold text-slate-900">What went well</h2><ul className="mt-3 space-y-2">{d.strengths.map((x:string,i:number)=><li key={i} className="text-sm text-slate-600">• {x}</li>)}</ul></article>}</section>}
*/}
    <details className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><summary className="cursor-pointer font-semibold text-slate-800">View submitted source code</summary><pre className="mt-4 max-h-[32rem] overflow-auto rounded-xl bg-slate-950 p-4 text-xs leading-relaxed text-slate-100"><code>{submission.code}</code></pre></details>
    {revisedCode&&!unrelatedTwoSumSuggestion&&<details className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><summary className="cursor-pointer px-5 py-4 font-semibold text-slate-800 marker:text-indigo-600">Suggested revised code</summary><div className="space-y-5 border-t border-slate-100 p-5">{revisedExplanation&&<div className="rounded-xl border border-indigo-100 bg-indigo-50 p-4"><h3 className="text-sm font-bold text-indigo-950">What changed</h3><p className="mt-1 text-sm leading-relaxed text-indigo-900">{revisedExplanation}</p></div>}{revisedChanges.length>0&&<div className="space-y-3"><h3 className="text-sm font-bold text-slate-800">Code improvements</h3>{revisedChanges.map((change:R,index:number)=><article key={index} className="rounded-xl border border-slate-200 p-4"><p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Change {index+1}</p><div className="grid gap-3 md:grid-cols-2">{str(change.line_original)&&<div><p className="mb-1 text-xs font-semibold text-rose-700">Before</p><pre className="whitespace-pre-wrap break-words rounded-lg bg-rose-50 p-3 text-xs text-slate-800"><code>{change.line_original}</code></pre></div>}{str(change.line_improved)&&<div><p className="mb-1 text-xs font-semibold text-emerald-700">After</p><pre className="whitespace-pre-wrap break-words rounded-lg bg-emerald-50 p-3 text-xs text-slate-800"><code>{change.line_improved}</code></pre></div>}</div>{str(change.reason)&&<p className="mt-3 text-sm leading-relaxed text-slate-600">{change.reason}</p>}</article>)}</div>}<div><div className="mb-2 flex items-center justify-between"><h3 className="text-sm font-bold text-slate-800">Full suggested solution</h3><span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-500">{submission.language.toUpperCase()}</span></div><pre className="max-h-[36rem] overflow-auto rounded-xl bg-slate-950 p-4 text-sm leading-relaxed text-slate-100"><code>{revisedCode}</code></pre></div></div></details>}
  </main>;
};
