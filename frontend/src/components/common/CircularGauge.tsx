import React from 'react';

interface CircularGaugeProps {
  score: number;
  maxScore?: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  label?: string;
  sublabel?: string;
  showPercent?: boolean;
}

export const CircularGauge: React.FC<CircularGaugeProps> = ({
  score,
  maxScore = 100,
  size = 96,
  strokeWidth = 8,
  color,
  label,
  sublabel,
  showPercent = false
}) => {
  const percentage = Math.min(100, Math.max(0, (score / maxScore) * 100));
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // dynamic color based on score if not explicitly passed
  const autoColor =
    percentage >= 80 ? '#10b981' : percentage >= 60 ? '#3b82f6' : percentage >= 40 ? '#f59e0b' : '#ef4444';
  const strokeColor = color || autoColor;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#e2e8f0"
          strokeWidth={strokeWidth}
          fill="transparent"
          className="transition-all duration-300"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        {label ? (
          <span className="text-xs font-semibold text-slate-500">{label}</span>
        ) : null}
        <div className="flex items-baseline justify-center">
          <span className="text-xl font-bold tracking-tight text-slate-800">
            {Math.round(score)}
          </span>
          {showPercent ? (
            <span className="text-xs font-semibold text-slate-500 ml-0.5">%</span>
          ) : (
            <span className="text-xs font-normal text-slate-400">/{maxScore}</span>
          )}
        </div>
        {sublabel ? (
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">{sublabel}</span>
        ) : null}
      </div>
    </div>
  );
};
