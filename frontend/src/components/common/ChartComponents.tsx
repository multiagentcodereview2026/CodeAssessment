import React from 'react';
import { CategoryScore } from '../../types';

interface ScoreTrendProps {
  data: { date: string; score: number }[];
  height?: number;
}

export const ScoreTrendLineChart: React.FC<ScoreTrendProps> = ({ data, height = 180 }) => {
  if (!data || data.length === 0) return null;

  const padding = { top: 20, right: 20, bottom: 30, left: 35 };
  const width = 450;
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  const minScore = 0;
  const maxScore = 100;

  const points = data.map((d, index) => {
    const x = padding.left + (index / (data.length - 1)) * graphWidth;
    const y = padding.top + graphHeight - ((d.score - minScore) / (maxScore - minScore)) * graphHeight;
    return { x, y, ...d };
  });

  const pathD = points.reduce((acc, p, i) => {
    if (i === 0) return `M ${p.x} ${p.y}`;
    const prev = points[i - 1];
    const cx1 = prev.x + (p.x - prev.x) / 2;
    const cy1 = prev.y;
    const cx2 = prev.x + (p.x - prev.x) / 2;
    const cy2 = p.y;
    return `${acc} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${p.x} ${p.y}`;
  }, '');

  const areaD = `${pathD} L ${points[points.length - 1].x} ${padding.top + graphHeight} L ${points[0].x} ${padding.top + graphHeight} Z`;

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto select-none">
        <defs>
          <linearGradient id="scoreTrendGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Y Grid lines */}
        {[0, 25, 50, 75, 100].map(val => {
          const y = padding.top + graphHeight - (val / 100) * graphHeight;
          return (
            <g key={val}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="#f1f5f9"
                strokeWidth="1"
                strokeDasharray={val === 0 ? 'none' : '3,3'}
              />
              <text
                x={padding.left - 8}
                y={y + 3.5}
                fontSize="10"
                textAnchor="end"
                className="fill-slate-400 font-mono"
              >
                {val}
              </text>
            </g>
          );
        })}

        {/* Area fill */}
        <path d={areaD} fill="url(#scoreTrendGradient)" />

        {/* Line */}
        <path d={pathD} fill="none" stroke="#4f46e5" strokeWidth="2.5" strokeLinecap="round" />

        {/* Data points */}
        {points.map((p, i) => (
          <g key={i} className="group cursor-pointer">
            <circle cx={p.x} cy={p.y} r="4" fill="#ffffff" stroke="#4f46e5" strokeWidth="2.5" />
            <circle cx={p.x} cy={p.y} r="8" fill="transparent" className="hover:fill-indigo-500/10" />
            <text
              x={p.x}
              y={padding.top + graphHeight + 18}
              fontSize="10"
              textAnchor="middle"
              className="fill-slate-500 font-medium"
            >
              {p.date}
            </text>
          </g>
        ))}
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
  onSelectBucket?: (range: string) => void;
  selectedRange?: string | null;
}

export const ScoreDistributionBarChart: React.FC<ScoreDistProps> = ({
  distribution,
  onSelectBucket,
  selectedRange
}) => {
  return (
    <div className="space-y-3 select-none">
      <div className="flex items-end justify-between gap-3 h-44 pt-4 px-2 border-b border-slate-200">
        {distribution.map((item, idx) => {
          const isSelected = selectedRange === item.range;

          return (
            <div
              key={idx}
              onClick={() => onSelectBucket && onSelectBucket(item.range)}
              className={`flex-1 flex flex-col items-center gap-2 group h-full justify-end cursor-pointer p-1.5 rounded-xl transition-all ${
                isSelected
                  ? 'bg-indigo-50/80 ring-2 ring-indigo-500 shadow-sm'
                  : 'hover:bg-slate-50'
              }`}
              title={`Score ${item.range}%: ${item.count} students. Click to inspect students.`}
            >
              {/* Count badge */}
              <div
                className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full transition-all ${
                  isSelected
                    ? 'bg-indigo-600 text-white shadow-xs scale-110'
                    : 'text-slate-700 bg-slate-100 group-hover:bg-indigo-100 group-hover:text-indigo-700'
                }`}
              >
                {item.count} {item.count === 1 ? 'student' : 'students'}
              </div>

              {/* Bar */}
              <div className="w-full max-w-[48px] bg-slate-100 rounded-t-xl overflow-hidden flex items-end h-full">
                <div
                  className={`w-full rounded-t-xl transition-all duration-300 ease-out group-hover:brightness-95 ${
                    isSelected ? 'ring-2 ring-indigo-600 brightness-105' : ''
                  }`}
                  style={{
                    height: `${Math.max(item.heightPercent, 12)}%`,
                    backgroundColor:
                      isSelected
                        ? '#4f46e5'
                        : idx >= 3
                        ? '#10b981'
                        : idx === 2
                        ? '#3b82f6'
                        : '#f59e0b'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* X Axis Labels */}
      <div className="flex justify-between gap-3 px-2 text-[11px] font-mono text-slate-500">
        {distribution.map((item, idx) => {
          const isSelected = selectedRange === item.range;
          return (
            <div
              key={idx}
              onClick={() => onSelectBucket && onSelectBucket(item.range)}
              className={`flex-1 text-center font-bold cursor-pointer py-1 rounded transition-colors ${
                isSelected ? 'text-indigo-600 bg-indigo-50 font-extrabold' : 'hover:text-slate-900'
              }`}
            >
              {item.range}%
            </div>
          );
        })}
      </div>

      <p className="text-[11px] text-center text-slate-400 font-medium pt-1">
        💡 Click on any bar (e.g. <span className="font-bold text-slate-600">0-20% (2 students)</span>) to reveal and inspect all students in that grade bracket.
      </p>
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
