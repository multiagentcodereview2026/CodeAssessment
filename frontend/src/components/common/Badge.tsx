import React from 'react';
import { Difficulty } from '../../types';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'easy' | 'medium' | 'hard' | 'passed' | 'partial' | 'failed' | 'neutral' | 'ai' | 'purple' | 'amber';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'neutral', size = 'sm' }) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  const variantClasses = {
    easy: 'bg-emerald-50 text-emerald-700 border-emerald-200 border',
    medium: 'bg-amber-50 text-amber-700 border-amber-200 border',
    hard: 'bg-rose-50 text-rose-700 border-rose-200 border',
    passed: 'bg-emerald-50 text-emerald-700 border-emerald-200 border font-medium',
    partial: 'bg-amber-50 text-amber-700 border-amber-200 border font-medium',
    failed: 'bg-rose-50 text-rose-700 border-rose-200 border font-medium',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200 border',
    ai: 'bg-purple-50 text-purple-700 border-purple-200 border font-medium',
    purple: 'bg-purple-50 text-purple-700 border-purple-200 border',
    amber: 'bg-amber-50 text-amber-700 border-amber-200 border'
  }[variant];

  return (
    <span className={`inline-flex items-center gap-1 rounded-md font-medium tracking-wide ${sizeClasses} ${variantClasses}`}>
      {children}
    </span>
  );
};

export const DifficultyBadge: React.FC<{ difficulty: Difficulty }> = ({ difficulty }) => {
  const variant = difficulty === 'Easy' ? 'easy' : difficulty === 'Medium' ? 'medium' : 'hard';
  return <Badge variant={variant}>{difficulty}</Badge>;
};

export const StatusBadge: React.FC<{ status: 'Passed' | 'Partial' | 'Failed' | 'Accepted' }> = ({ status }) => {
  const variant = status === 'Accepted' || status === 'Passed' ? 'passed' : status === 'Partial' ? 'partial' : 'failed';
  return (
    <Badge variant={variant}>
      <span className={`w-1.5 h-1.5 rounded-full ${variant === 'passed' ? 'bg-emerald-500' : variant === 'partial' ? 'bg-amber-500' : 'bg-rose-500'}`} />
      {status}
    </Badge>
  );
};
