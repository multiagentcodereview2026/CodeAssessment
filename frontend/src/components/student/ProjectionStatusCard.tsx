import React from 'react';
import { LoaderCircle } from 'lucide-react';

type RecordValue = Record<string, unknown>;
const record = (value: unknown): RecordValue => value && typeof value === 'object' && !Array.isArray(value) ? value as RecordValue : {};
const number = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? value : null;
const text = (value: unknown) => typeof value === 'string' ? value : '';
const mark = (value: unknown) => { const n = number(value); return n == null ? '—' : String(Number(n.toFixed(1))); };

type Props = {
  projection: RecordValue;
  slow: boolean;
  paused: boolean;
  connectionLost: boolean;
  retrying: boolean;
  error: string;
  onCheckAgain: () => void;
  onRetry: () => void;
};

export const ProjectionStatusCard: React.FC<Props> = ({ projection, slow, paused, connectionLost, retrying, error, onCheckAgain, onRetry }) => {
  const pending = projection.pending === true;
  const measured = projection.available === true && projection.verified === true && number(projection.projected_score) != null;
  const noGain = projection.verified === true && (projection.status === 'no_gain' || number(projection.expected_improvement) === 0 || projection.available === false);
  const message = text(projection.message);
  if (!pending && !measured && !noGain && !message) return null;
  const theme = pending ? 'border-indigo-200 bg-indigo-50 text-indigo-950' : measured && !noGain ? 'border-emerald-200 bg-emerald-50 text-emerald-950' : noGain ? 'border-slate-200 bg-slate-50 text-slate-900' : 'border-amber-200 bg-amber-50 text-amber-950';
  const comparisons = record(projection.comparison);
  const components = record(projection.stage_components);
  const breakdown = record(projection.score_breakdown);
  const gain = number(projection.expected_improvement);
  return <section className={`rounded-xl border p-4 ${theme}`} aria-busy={pending && !paused}>
    <div role="status" aria-live="polite" className="flex items-center gap-2 text-sm font-bold">
      {pending && !paused && <LoaderCircle aria-hidden="true" className="h-4 w-4 shrink-0 animate-spin motion-reduce:animate-none" />}
      {pending ? paused ? 'Automatic checking paused' : slow ? 'Still checking your projected score…' : 'Calculating projected score…' : noGain ? 'Verified — no score increase' : measured ? 'Measured candidate score' : 'Score projection unavailable'}
    </div>
    {pending ? <>
      <p className="mt-2 text-sm">{paused ? 'The result has not been confirmed on this page. Check again for the latest saved status.' : connectionLost ? 'The connection was interrupted. We’re checking again; your saved assessment is safe.' : 'We’re checking an improved solution against this learning step, running the tests, and calculating its score. You can keep reviewing the guidance below.'}</p>
      {slow && !paused && <p className="mt-2 text-xs">This is taking longer. The result will appear here automatically when verification finishes.</p>}
      {paused && <button type="button" onClick={onCheckAgain} className="mt-3 rounded-md bg-indigo-700 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-800">Check again</button>}
    </> : <>
      {measured && <div className="mt-2 flex flex-wrap items-end gap-x-3 gap-y-1">
        <span className="font-mono text-2xl font-extrabold">{mark(projection.current_score)} → {mark(projection.projected_score)}/100</span>
        {gain != null && <span className={`text-sm font-bold ${gain < 0 ? 'text-amber-800' : ''}`}>{gain > 0 ? '+' : ''}{mark(gain)} pts</span>}
      </div>}
      <p className="mt-2 text-xs leading-relaxed">{message || 'Submit your own revision for a new assessment.'}</p>
      {measured && <details className="mt-3 rounded-lg border border-current/15 bg-white/60 p-3">
        <summary className="cursor-pointer text-xs font-semibold">How this score was calculated</summary>
        <div className="mt-3 overflow-x-auto"><table className="w-full text-left text-xs">
          <caption className="mb-2 text-left">Current → candidate. Contributions are marks out of 100 using this submission’s saved weights.</caption>
          <thead><tr><th className="py-2 pr-3">Component</th><th className="pr-3">Score (%)</th><th className="pr-3">Weight</th><th>Contribution</th></tr></thead>
          <tbody>{(['correctness', 'time', 'space', 'style'] as const).map(key => {
            const pair = record(comparisons[key]);
            const current = record(pair.current);
            const candidate = record(pair.candidate || breakdown[key]);
            const weight = number(candidate.weight);
            return <tr key={key} className="border-t border-current/10"><th className="py-2 pr-3 font-medium">{{ correctness: 'Correctness', time: 'Time', space: 'Space', style: 'Style' }[key]}</th><td className="pr-3">{mark(current.score)} → {mark(candidate.score ?? components[key])}</td><td className="pr-3">{weight == null ? '—' : mark(weight * 100) + '%'}</td><td>{mark(current.weighted)} → {mark(candidate.weighted)}</td></tr>;
          })}</tbody>
        </table></div>
        <p className="mt-2 text-xs">Final score = the smaller of the weighted total and correctness, rounded without exceeding correctness.</p>
        {projection.alignment_review === 'ai_reviewed' && <p className="mt-2 text-xs">Guidance alignment was reviewed by AI. The candidate score was calculated after execution and assessment; your own implementation still needs a separate assessment.</p>}
        {projection.alignment_review !== 'ai_reviewed' && <>
          <p className="mt-2 text-xs">This saved result has no guidance alignment review. Recheck to request updated guidance and verification.</p>
          <button type="button" onClick={onRetry} disabled={retrying} className="mt-2 rounded-md border border-current px-3 py-2 text-xs font-semibold disabled:opacity-60">{retrying ? 'Requesting verification…' : 'Recheck with current guidance'}</button>
        </>}
      </details>}
      {!measured && !noGain && <button type="button" onClick={onRetry} disabled={retrying} className="mt-3 rounded-md bg-amber-700 px-3 py-2 text-xs font-semibold text-white hover:bg-amber-800 disabled:cursor-wait disabled:opacity-60">{retrying ? 'Requesting verification…' : 'Retry score projection'}</button>}
    </>}
    {error && <p role="alert" className="mt-2 text-xs text-rose-700">{error}</p>}
  </section>;
};
