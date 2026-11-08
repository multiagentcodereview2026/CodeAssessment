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
    easy: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-400 dark:border-emerald-500/30 border font-semibold',
    medium: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/15 dark:text-amber-400 dark:border-amber-500/30 border font-semibold',
    hard: 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-500/15 dark:text-rose-400 dark:border-rose-500/30 border font-semibold',
    passed: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-400 dark:border-emerald-500/30 border font-semibold',
    partial: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/15 dark:text-amber-400 dark:border-amber-500/30 border font-semibold',
    failed: 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-500/15 dark:text-rose-400 dark:border-rose-500/30 border font-semibold',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-white/10 dark:text-zinc-200 dark:border-white/12 border font-medium',
    ai: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/15 dark:text-purple-400 dark:border-purple-500/30 border font-semibold',
    purple: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/15 dark:text-purple-400 dark:border-purple-500/30 border font-semibold',
    amber: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/15 dark:text-amber-400 dark:border-amber-500/30 border font-semibold'
  }[variant];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full tracking-wide ${sizeClasses} ${variantClasses}`}>
      {children}
    </span>
  );
};

export const DifficultyBadge: React.FC<{ difficulty: Difficulty }> = ({ difficulty }) => {
  const variant = difficulty === 'Easy' ? 'easy' : difficulty === 'Medium' ? 'medium' : 'hard';
  return <Badge variant={variant}>{difficulty}</Badge>;
};

export const StatusBadge: React.FC<{ status: 'Passed' | 'Partial' | 'Failed' | 'Accepted' | string }> = ({ status }) => {
  const norm = (status || '').toLowerCase();
  const isPassed = norm === 'accepted' || norm === 'passed';
  const isPartial = norm === 'partial';
  const variant = isPassed ? 'passed' : isPartial ? 'partial' : 'failed';

  return (
    <Badge variant={variant}>
      {isPassed ? (
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
      ) : isPartial ? (
        <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
      ) : (
        <XCircle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400 shrink-0" />
      )}
      <span>{status}</span>
    </Badge>
  );
};
