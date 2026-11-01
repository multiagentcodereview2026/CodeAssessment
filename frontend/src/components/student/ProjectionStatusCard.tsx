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
  const [now, setNow] = React.useState(() => Date.now());
  const retryAt = Date.parse(text(projection.next_retry_at));
  const quotaWait = projection.phase === 'waiting_quota' && projection.pending === true && Number.isFinite(retryAt);
  React.useEffect(() => {
    if (!quotaWait) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [quotaWait, retryAt]);
  const remaining = quotaWait ? Math.max(0, Math.ceil((retryAt - now) / 1000)) : 0;
  const pending = projection.pending === true;
  const measured = projection.available === true && projection.verified === true && number(projection.projected_score) != null;
  const noGain = projection.verified === true && (projection.status === 'no_gain' || number(projection.expected_improvement) === 0 || projection.available === false);
  const message = text(projection.message);
  if (!pending && !measured && !noGain && !message) return null;
  const theme = pending ? 'projection-pending' : measured && !noGain ? 'projection-measured' : noGain ? 'projection-neutral' : 'projection-warning';
  const comparisons = record(projection.comparison);
  const components = record(projection.stage_components);
  const breakdown = record(projection.score_breakdown);
  const gain = number(projection.expected_improvement);
  const phase = text(projection.phase);
  const phaseTitle = phase === 'waiting_quota' ? 'Waiting for AI quota' : phase === 'generating' ? 'Generating your guide and private candidate…' : phase === 'alignment' ? 'Checking guide alignment…' : phase === 'judging' ? 'Running candidate tests…' : phase === 'scoring' ? 'Calculating candidate score…' : 'Preparing revision verification…';
  return <section className={`projection-card rounded-xl border p-4 ${theme}`} aria-busy={pending && !paused}>
    <div role="status" aria-live="polite" className="flex items-center gap-2 text-sm font-bold">
      {pending && !paused && <LoaderCircle aria-hidden="true" className="h-4 w-4 shrink-0 animate-spin motion-reduce:animate-none" />}
      {pending ? paused ? 'Automatic checking paused' : phaseTitle : noGain ? 'Verified — no score increase' : measured ? 'Measured candidate score' : 'Score projection unavailable'}
    </div>
    {pending ? <>
      <p className="mt-2 text-sm">{paused ? 'The result has not been confirmed on this page. Check again for the latest saved status.' : connectionLost ? 'The connection was interrupted. We’re checking again; your saved assessment is safe.' : message || 'Your guide and measured candidate score appear together after the improvement checks pass.'}</p>
      {quotaWait && <p className="mt-2 text-xs">{remaining > 0 ? `Next check in ${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, '0')}.` : 'Waiting for the queued check to start.'} Your existing draft is kept.</p>}
      {slow && !paused && <p className="mt-2 text-xs">This is taking longer. The result will appear here automatically when verification finishes.</p>}
      {paused && <button type="button" onClick={onCheckAgain} className="mt-3 rounded-md bg-indigo-700 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-800">Check again</button>}
    </> : <>
      {measured && <div className="mt-2 flex flex-wrap items-end gap-x-3 gap-y-1">
        <span className="font-mono text-2xl font-extrabold">{mark(projection.current_score)} → {mark(projection.projected_score)}/100</span>
        {gain != null && <span className={`text-sm font-bold ${gain < 0 ? 'text-amber-800' : ''}`}>{gain > 0 ? '+' : ''}{mark(gain)} pts</span>}
      </div>}
      <p className="mt-2 text-xs leading-relaxed">{message || 'Submit your own revision for a new assessment.'}</p>
      {measured && <details className="projection-calculation mt-3 rounded-lg border p-3">
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
      {!measured && !noGain && projection.retry_allowed !== false && <button type="button" onClick={onRetry} disabled={retrying} className="mt-3 rounded-md bg-amber-700 px-3 py-2 text-xs font-semibold text-white hover:bg-amber-800 disabled:cursor-wait disabled:opacity-60">{retrying ? 'Requesting verification…' : projection.policy_update_available === true ? 'Recheck with corrected rule' : projection.resume_saved_draft === true ? 'Verify saved draft again' : 'Retry score projection'}</button>}
    </>}
    {error && <p role="alert" className="mt-2 text-xs text-rose-700">{error}</p>}
  </section>;
};
