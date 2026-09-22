import React from 'react';
import { Difficulty } from '../../types';
import { CheckCircle2, AlertCircle, XCircle } from 'lucide-react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'easy' | 'medium' | 'hard' | 'passed' | 'partial' | 'failed' | 'neutral' | 'ai' | 'purple' | 'amber';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'neutral', size = 'sm' }) => {
  const sizeClasses = size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-xs';

  const variantClasses = {
    easy: 'bg-emerald-50 text-emerald-700 border-emerald-300 border font-bold',
    medium: 'bg-amber-50 text-amber-700 border-amber-300 border font-bold',
    hard: 'bg-rose-50 text-rose-700 border-rose-300 border font-bold',
    passed: 'bg-emerald-100/90 text-emerald-800 border-emerald-300 border font-extrabold shadow-2xs',
    partial: 'bg-amber-100 text-amber-900 border-amber-300 border font-extrabold shadow-2xs',
    failed: 'bg-rose-100 text-rose-800 border-rose-300 border font-extrabold shadow-2xs',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200 border font-medium',
    ai: 'bg-purple-50 text-purple-700 border-purple-200 border font-bold',
    purple: 'bg-purple-50 text-purple-700 border-purple-200 border font-bold',
    amber: 'bg-amber-50 text-amber-700 border-amber-200 border font-bold'
  }[variant];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-xl tracking-wide ${sizeClasses} ${variantClasses}`}>
      {children}
    </span>
  );
};

export const DifficultyBadge: React.FC<{ difficulty: Difficulty }> = ({ difficulty }) => {
  const variant = difficulty === 'Easy' ? 'easy' : difficulty === 'Medium' ? 'medium' : 'hard';
  return <Badge variant={variant}>{difficulty}</Badge>;
};

export const StatusBadge: React.FC<{ status: 'Passed' | 'Partial' | 'Failed' | 'Accepted' }> = ({ status }) => {
  const isPassed = status === 'Accepted' || status === 'Passed';
  const isPartial = status === 'Partial';
  const variant = isPassed ? 'passed' : isPartial ? 'partial' : 'failed';

  return (
    <Badge variant={variant}>
      {isPassed ? (
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
      ) : isPartial ? (
        <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
      ) : (
        <XCircle className="w-3.5 h-3.5 text-rose-600" />
      )}
      <span>{status}</span>
    </Badge>
  );
};
