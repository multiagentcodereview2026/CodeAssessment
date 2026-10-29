import React, { useEffect, useRef } from 'react';

export type ScoringWeights = { correctness: number; time: number; space: number; style: number };
export const DEFAULT_SCORING_WEIGHTS: ScoringWeights = { correctness: 30, time: 35, space: 25, style: 10 };

export function ScoringWeightsEditor({ value, onChange, disabled = false }: {
  value?: ScoringWeights; onChange: (value?: ScoringWeights) => void; disabled?: boolean;
}) {
  const firstInput = useRef<HTMLInputElement>(null);
  const total = Object.values(value || DEFAULT_SCORING_WEIGHTS).reduce((sum, weight) => sum + weight, 0);
  const valid = Math.abs(total - 100) < 0.000001;
  useEffect(() => { firstInput.current?.setCustomValidity(valid ? '' : 'Weights must total 100%.'); }, [valid]);
  return <fieldset disabled={disabled} className="space-y-2 rounded-lg border border-slate-200 p-3 text-sm">
    <label className="flex items-center gap-2"><input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked ? { ...DEFAULT_SCORING_WEIGHTS } : undefined)} />Customize scoring weights</label>
    {value ? <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{(Object.keys(DEFAULT_SCORING_WEIGHTS) as (keyof ScoringWeights)[]).map((key, index) => <label key={key} className="capitalize">{key} %<input ref={index === 0 ? firstInput : undefined} type="number" required min={0} max={100} step="0.1" value={Number.isNaN(value[key]) ? '' : value[key]} onChange={(event) => onChange({ ...value, [key]: event.target.valueAsNumber })} className="mt-1 w-full rounded border border-slate-300 p-2" /></label>)}</div> : <p className="text-xs text-slate-500">Default: correctness 30% · time 35% · space 25% · style 10%.</p>}
    {value && <p className={valid ? 'text-xs text-slate-500' : 'text-xs text-red-700'}>Total: {Number.isFinite(total) ? total : '—'}% (must equal 100%).</p>}
    <p className="text-xs text-slate-500">Final score is the lower of weighted quality and correctness. Weights freeze after the first submission.</p>
  </fieldset>;
}
