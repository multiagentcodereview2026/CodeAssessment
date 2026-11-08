import React from 'react';

interface ScoreBarProps {
  label: string;
  score: number;
  maxScore: number;
  colorClass?: string;
  barColor?: string;
  details?: string;
  optimalBadge?: string;
}

export const ScoreBar: React.FC<ScoreBarProps> = ({
  label,
  score,
  maxScore,
  barColor = '#3b82f6',
  details,
  optimalBadge
}) => {
  const percentage = Math.min(100, Math.max(0, (score / maxScore) * 100));

  return (
    <div className="space-y-1.5 py-1">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-700 dark:text-zinc-200">{label}</span>
          {optimalBadge && (
            <span className="px-1.5 py-0.5 text-[11px] font-mono font-medium bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-zinc-300 rounded border border-slate-200 dark:border-white/10">
              {optimalBadge}
            </span>
          )}
        </div>
        <div className="flex items-baseline gap-1 font-mono">
          <span className="font-bold text-slate-800 dark:text-white">{score}</span>
          <span className="text-xs text-slate-400 dark:text-zinc-500">/{maxScore}</span>
        </div>
      </div>

      <div className="w-full h-2 bg-slate-100 dark:bg-white/10 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${percentage}%`, backgroundColor: barColor }}
        />
      </div>

      {details && (
        <p className="text-xs text-slate-500 dark:text-zinc-400 leading-relaxed pt-0.5">{details}</p>
      )}
    </div>
  );
};
