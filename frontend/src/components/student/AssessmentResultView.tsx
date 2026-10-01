import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, CheckCircle2, XCircle } from 'lucide-react';
import { useAuth } from '../../context/useAuth';

type Submission = {
  submission_id: string;
  student_id: string;
  problem_id: string;
  assignment_id: number | null;
  language: string;
  code: string;
  status: string;
  overall_score: number | null;
  correctness_score: number | null;
  complexity_score: number | null;
  style_score: number | null;
  similarity_score: number | null;
  complexity_details: Record<string, unknown> | null;
  execution_result: Record<string, any> | null;
  feedback: unknown;
  recommendations: unknown;
  improved_code: unknown;
  projected_score: unknown;
  created_at: string;
};

const formatStoredValue = (value: unknown) => {
  if (value == null) return 'No saved details.';
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
};

export const AssessmentResultView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { authFetch } = useAuth();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [problemTitle, setProblemTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) {
      setError('Choose a saved submission from your history.');
      setLoading(false);
      return;
    }
    let cancelled = false;
    const load = async () => {
      try {
        const response = await authFetch(`/api/submissions/${encodeURIComponent(id)}`, { cache: 'no-store' });
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || 'Submission could not be loaded.');
        }
        const data: Submission = await response.json();
        const problemResponse = await authFetch(`/api/problems/${encodeURIComponent(data.problem_id)}`, { cache: 'no-store' });
        const problem = problemResponse.ok ? await problemResponse.json() : null;
        if (cancelled) return;
        setSubmission(data);
        setProblemTitle(problem?.title || data.problem_id);
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'Submission could not be loaded.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [authFetch, id]);

  if (loading) return <main className="mx-auto max-w-5xl py-12 text-sm text-slate-500">Loading saved assessment…</main>;
  if (!submission) {
    return <main className="mx-auto max-w-3xl space-y-4 py-12">
      <p role="alert" className="text-sm text-rose-700">{error || 'Submission not found.'}</p>
      <Link to="/submissions" className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-700"><ArrowLeft className="h-4 w-4" /> Submission history</Link>
    </main>;
  }

  const execution = submission.execution_result || {};
  const results = Array.isArray(execution.results) ? execution.results : [];
  const passedCases = Number(execution.passed_cases || 0);
  const totalCases = Number(execution.total_cases || passedCases + Number(execution.failed_cases || 0));
  const scores = [
    ['Correctness', submission.correctness_score],
    ['Complexity', submission.complexity_score],
    ['Style', submission.style_score],
    ['Similarity', submission.similarity_score]
  ] as const;

  return (
    <main className="mx-auto max-w-5xl space-y-6 pb-12">
      <Link to="/submissions" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-indigo-700"><ArrowLeft className="h-4 w-4" /> Submission history</Link>

      <header className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-end">
        <div>
          <p className="font-mono text-xs text-slate-500">{submission.submission_id} · {submission.language}</p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{problemTitle}</h1>
          <p className="mt-1 text-xs text-slate-500">Saved {new Date(submission.created_at).toLocaleString()}</p>
          {submission.assignment_id != null && <Link to="/courses" className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-indigo-700"><BookOpen className="h-3.5 w-3.5" /> Assignment #{submission.assignment_id}</Link>}
          {submission.assignment_id == null && <p className="mt-2 text-xs text-slate-500">Independent practice</p>}
        </div>
        <div className="text-left sm:text-right">
          <p className="text-xs font-semibold uppercase text-slate-500">Overall score</p>
          <p className="font-mono text-3xl font-bold text-slate-900">{submission.overall_score == null ? 'N/A' : `${submission.overall_score}/100`}</p>
          <p className="text-sm text-slate-600">{submission.status}</p>
        </div>
      </header>

      <section className="grid gap-3 sm:grid-cols-4" aria-label="Assessment scores">
        {scores.map(([label, score]) => <article key={label} className="border-b border-slate-200 p-3 sm:border-b-0 sm:border-r">
          <p className="text-xs text-slate-500">{label}</p>
          <p className="mt-1 font-mono text-xl font-bold text-slate-900">{score == null ? 'N/A' : `${score}%`}</p>
        </article>)}
      </section>

      <section className="border-y border-slate-200 py-5">
        <div className="flex items-center justify-between">
          <div><h2 className="font-semibold text-slate-900">Execution</h2><p className="mt-1 text-xs text-slate-500">{passedCases}/{totalCases} test cases passed · {execution.runtime_ms ?? '—'} ms</p></div>
          {totalCases > 0 && passedCases === totalCases ? <CheckCircle2 className="h-5 w-5 text-emerald-700" /> : <XCircle className="h-5 w-5 text-rose-700" />}
        </div>
        {results.length > 0 && <div className="mt-4 divide-y divide-slate-100">
          {results.map((result, index) => <div key={result.test_case_id || index} className="flex items-center justify-between py-2 text-sm">
            <span>Case {index + 1}{result.is_hidden ? ' · hidden' : ''}</span>
            <span className={String(result.status).toLowerCase() === 'accepted' ? 'text-emerald-700' : 'text-rose-700'}>{result.is_hidden ? 'Hidden case' : String(result.status || 'Unknown')}</span>
          </div>)}
        </div>}
      </section>

      {submission.complexity_details && <section className="border-b border-slate-200 py-5">
        <h2 className="font-semibold text-slate-900">Complexity analysis</h2>
        <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-50 p-4 text-xs text-slate-700">{formatStoredValue(submission.complexity_details)}</pre>
      </section>}

      <section className="grid gap-6 md:grid-cols-2">
        <div className="border-b border-slate-200 py-5"><h2 className="font-semibold text-slate-900">Saved feedback</h2><pre className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{formatStoredValue(submission.feedback)}</pre></div>
        <div className="border-b border-slate-200 py-5"><h2 className="font-semibold text-slate-900">Recommendations</h2><pre className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{formatStoredValue(submission.recommendations)}</pre></div>
      </section>

      <details className="border-y border-slate-200 py-4">
        <summary className="cursor-pointer font-semibold text-slate-900">Submitted source code</summary>
        <pre className="mt-4 max-h-[32rem] overflow-auto rounded-lg bg-slate-950 p-4 text-xs leading-relaxed text-slate-100"><code>{submission.code}</code></pre>
      </details>

      {submission.improved_code != null && <details className="border-b border-slate-200 py-4">
        <summary className="cursor-pointer font-semibold text-slate-900">Saved revised code suggestion</summary>
        <pre className="mt-4 max-h-[32rem] overflow-auto rounded-lg bg-slate-950 p-4 text-xs leading-relaxed text-slate-100"><code>{formatStoredValue(submission.improved_code)}</code></pre>
      </details>}
    </main>
  );
};
