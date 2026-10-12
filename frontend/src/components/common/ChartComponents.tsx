import React from 'react';
import { CategoryScore } from '../../types';

interface ScoreTrendProps {
  data: { date: string; score: number }[];
  height?: number;
}

export const ScoreTrendLineChart: React.FC<ScoreTrendProps> = ({ data, height = 180 }) => {
  if (!data || data.length === 0) return null;
  const width = 720;
  const viewHeight = Math.max(180, height);
  const padding = { top: 12, right: 14, bottom: 34, left: 42 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = viewHeight - padding.top - padding.bottom;
  const chartData = data.map((point, index) => ({
    ...point,
    label: `Attempt ${index + 1}`,
    shortDate: Number.isNaN(Date.parse(point.date))
      ? point.date
      : new Date(point.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
  }));
  const points = chartData.map((point, index) => ({
    ...point,
    x: padding.left + (chartData.length === 1 ? graphWidth / 2 : index / (chartData.length - 1) * graphWidth),
    y: padding.top + (100 - Math.max(0, Math.min(100, point.score))) / 100 * graphHeight,
  }));
  const line = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
  const area = `${line} L ${points[points.length - 1].x} ${padding.top + graphHeight} L ${points[0].x} ${padding.top + graphHeight} Z`;
  const tickEvery = Math.max(1, Math.ceil((points.length - 1) / 5));
  const visibleTickIndices = new Set(points.map((_, index) => index).filter((index) => index % tickEvery === 0 || index === points.length - 1));

  return (
    <div className="h-full w-full min-w-0" role="img" aria-label={`Score trend across ${data.length} assessed problems`}>
      <svg viewBox={`0 0 ${width} ${viewHeight}`} className="block h-auto w-full" preserveAspectRatio="xMidYMid meet">
        <defs><linearGradient id="assessmentScoreFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4f46e5" stopOpacity="0.14"/><stop offset="100%" stopColor="#4f46e5" stopOpacity="0.01"/></linearGradient></defs>
        {[0, 25, 50, 75, 100].map((value) => {
          const y = padding.top + (100 - value) / 100 * graphHeight;
          return <g key={value}><line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#e8edf4" strokeDasharray={value === 0 ? undefined : '3 4'}/><text x={padding.left - 9} y={y + 4} textAnchor="end" fill="#94a3b8" fontSize="11">{value}</text></g>;
        })}
        <path d={area} fill="url(#assessmentScoreFill)"/>
        <path d={line} fill="none" stroke="#4f46e5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
        {points.map((point, index) => {
          const exactDate = new Date(point.date);
          const detail = Number.isNaN(exactDate.getTime()) ? point.date : exactDate.toLocaleString();
          return <g key={`${point.date}-${index}`}>
            <circle cx={point.x} cy={point.y} r="4" fill="white" stroke="#4f46e5" strokeWidth="2.5"><title>{`${point.label} · ${Number(point.score).toFixed(1)} / 100 · ${detail}`}</title></circle>
            {visibleTickIndices.has(index) && <text x={point.x} y={viewHeight - 9} textAnchor="middle" fill="#64748b" fontSize="11">{point.shortDate}</text>}
          </g>;
        })}
      </svg>
    </div>
  );
};

export const CategoryDonutChart: React.FC<{ categories: CategoryScore[] }> = ({ categories }) => {
  const size = 160;
  const strokeWidth = 24;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let accumulatedPercent = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {categories.map((cat, idx) => {
            const strokeDasharray = `${(cat.percentage / 100) * circumference} ${circumference}`;
            const strokeDashoffset = -((accumulatedPercent / 100) * circumference);
            accumulatedPercent += cat.percentage;

            return (
              <circle
                key={idx}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke={cat.color}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                fill="transparent"
                className="transition-all duration-700 ease-out hover:opacity-80"
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-xs text-slate-400 font-medium">Evaluation</span>
          <span className="text-sm font-bold text-slate-800">Weights</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 text-xs">
        {categories.map((cat, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color }} />
            <span className="text-slate-600 font-medium">{cat.name}</span>
            <span className="text-slate-400 font-mono ml-auto">({cat.scoreDisplay})</span>
          </div>
        ))}
      </div>
    </div>
  );
};

interface ScoreDistProps {
  distribution: { range: string; count: number; heightPercent: number }[];
}

export const ScoreDistributionBarChart: React.FC<ScoreDistProps> = ({ distribution }) => {
  if (!Array.isArray(distribution) || distribution.length === 0) {
    return <p className="py-10 text-center text-sm text-slate-500">No graded submissions yet.</p>;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-end justify-between gap-3 h-36 pt-4 px-2 border-b border-slate-200">
        {distribution.map((item, idx) => (
          <div key={idx} className="flex-1 flex flex-col items-center gap-2 group h-full justify-end">
            <div className="text-xs font-mono font-bold text-slate-700 group-hover:text-indigo-600 transition-colors">
              {item.count}
            </div>
            <div className="w-full max-w-[42px] bg-slate-100 rounded-t-md overflow-hidden flex items-end h-full">
              <div
                className="w-full bg-emerald-500 hover:bg-emerald-600 rounded-t-md transition-all duration-500 ease-out group-hover:brightness-95"
                style={{
                  height: `${item.heightPercent}%`,
                  backgroundColor: idx >= 3 ? '#10b981' : idx === 2 ? '#3b82f6' : '#f59e0b'
                }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="flex justify-between gap-3 px-2 text-[11px] font-mono text-slate-500">
        {distribution.map((item, idx) => (
          <span key={idx} className="flex-1 text-center font-medium">
            {item.range}
          </span>
        ))}
      </div>
    </div>
  );
};

export const LearningSummarySparkline: React.FC = () => {
  const points = [
    { x: 0, y: 35 },
    { x: 20, y: 28 },
    { x: 40, y: 32 },
    { x: 60, y: 18 },
    { x: 80, y: 22 },
    { x: 100, y: 8 }
  ];

  const path = points.reduce((acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`), '');

  return (
    <svg viewBox="0 0 100 40" className="w-full h-10 select-none">
      <path d={path} fill="none" stroke="#4f46e5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="2" fill="#4f46e5" />
      ))}
    </svg>
  );
};
