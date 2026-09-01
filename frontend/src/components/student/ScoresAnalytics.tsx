import React, { useState } from 'react';
import {
  LineChart as LineChartIcon,
  PieChart as PieChartIcon,
  TrendingUp,
  Award,
  Zap,
  Target,
  GraduationCap,
  Code2,
  Calendar,
  Clock,
  Sparkles,
  ChevronRight,
  ArrowLeft,
  CheckCircle2,
  Layers,
  Cpu
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreTrendLineChart, CategoryDonutChart } from '../common/ChartComponents';
import { DifficultyBadge, StatusBadge } from '../common/Badge';
import { ScoreBar } from '../common/ScoreBar';
import { CircularGauge } from '../common/CircularGauge';

export const ScoresAnalytics: React.FC = () => {
  const { problems, submissions, selectedProblemId, setSelectedProblemId, openProblemWorkspace, setCurrentView } = useApp();
  
  // Active selected problem for specific analysis
  const [modeFilter, setModeFilter] = useState<'assigned' | 'self'>('assigned');
  const [activeProblemId, setActiveProblemId] = useState<string>(selectedProblemId || 'prob-1');

  const selectedProblem = problems.find(p => p.id === activeProblemId) || problems[0];
  const isAssigned = selectedProblem.origin === 'instructor_assigned';

  // Problem-specific submissions
  const problemSubmissions = submissions.filter(s => s.problemId === selectedProblem.id);
  const latestSubmission = problemSubmissions[0];

  // Specific problem score data
  const problemScore = latestSubmission ? latestSubmission.score : 85;
  const isPassed = latestSubmission ? latestSubmission.status === 'Passed' : true;

  // Filtered problem list for dropdown
  const filteredProblems = problems.filter(p => {
    if (modeFilter === 'assigned') return p.origin === 'instructor_assigned';
    if (modeFilter === 'self') return p.origin !== 'instructor_assigned';
    return true;
  });

  // Problem attempt trend data
  const problemAttemptTrend = [
    { date: 'Attempt 1', score: 65 },
    { date: 'Attempt 2', score: 72 },
    { date: 'Attempt 3', score: problemScore }
  ];

  const problemCategoryScores = [
    { name: 'Correctness', percentage: 28.5, color: '#3b82f6', scoreDisplay: '20/25' },
    { name: 'Time Complexity', percentage: 18.7, color: '#06b6d4', scoreDisplay: '18/25' },
    { name: 'Space Complexity', percentage: 14.5, color: '#f59e0b', scoreDisplay: '12/15' },
    { name: 'Code Quality', percentage: 27.8, color: '#8b5cf6', scoreDisplay: '18/20' },
    { name: 'Similarity (Originality)', percentage: 10.6, color: '#10b981', scoreDisplay: '17/20' }
  ];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Breadcrumb & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentView('dashboard')}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Problem Score Analysis
            </h1>
            <p className="text-xs text-slate-500">
              Deep-dive multi-agent rubric breakdown and attempt progression for a specific challenge.
            </p>
          </div>
        </div>

        <button
          onClick={() => openProblemWorkspace(selectedProblem.id)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all self-start sm:self-auto cursor-pointer"
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Open in Workspace</span>
        </button>
      </div>

      {/* Problem Selector & Mode Filter Toolbar */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1 w-full md:w-auto">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
            Select Problem to Analyze:
          </label>
          <select
            value={activeProblemId}
            onChange={(e) => {
              setActiveProblemId(e.target.value);
              setSelectedProblemId(e.target.value);
            }}
            className="w-full md:w-80 bg-slate-50 hover:bg-slate-100 text-slate-900 font-bold text-sm rounded-xl px-3.5 py-2.5 border border-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            {filteredProblems.map((prob) => (
              <option key={prob.id} value={prob.id}>
                {prob.title} ({prob.difficulty}) — {prob.origin === 'instructor_assigned' ? '🎓 Assigned' : '💡 Practice'}
              </option>
            ))}
          </select>
        </div>

        {/* Mode Filter Pills - Strictly 2 Independent Modes */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-100/80 rounded-2xl border border-slate-200/80">
          <button
            onClick={() => {
              setModeFilter('assigned');
              const firstAssigned = problems.find(p => p.origin === 'instructor_assigned');
              if (firstAssigned) {
                setActiveProblemId(firstAssigned.id);
                setSelectedProblemId(firstAssigned.id);
              }
            }}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              modeFilter === 'assigned' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GraduationCap className="w-3.5 h-3.5" />
            <span>Coursework Scorecards</span>
          </button>
          <button
            onClick={() => {
              setModeFilter('self');
              const firstSelf = problems.find(p => p.origin !== 'instructor_assigned');
              if (firstSelf) {
                setActiveProblemId(firstSelf.id);
                setSelectedProblemId(firstSelf.id);
              }
            }}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              modeFilter === 'self' ? 'bg-purple-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Practice Scorecards</span>
          </button>
        </div>
      </div>

      {/* Selected Problem Overview Banner */}
      <div className={`p-6 rounded-3xl border shadow-xs transition-all ${
        isAssigned
          ? 'bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 text-white border-indigo-700/60'
          : 'bg-gradient-to-r from-slate-900 via-purple-950 to-slate-900 text-white border-purple-800/60'
      }`}>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`px-2.5 py-0.5 text-[11px] font-extrabold uppercase rounded-full ${
                isAssigned ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-400/30' : 'bg-purple-500/20 text-purple-300 border border-purple-400/30'
              }`}>
                {isAssigned ? '🎓 Instructor Coursework Challenge' : '💡 Self-Paced Practice Challenge'}
              </span>
              <DifficultyBadge difficulty={selectedProblem.difficulty} />
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              {selectedProblem.title}
            </h2>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 font-mono pt-1">
              <span>Acceptance: <strong className="text-white">{selectedProblem.acceptanceRate}</strong></span>
              <span>Optimal Time: <strong className="text-emerald-400">{selectedProblem.optimalComplexity.time}</strong></span>
              <span>Optimal Space: <strong className="text-emerald-400">{selectedProblem.optimalComplexity.space}</strong></span>
              {isAssigned && selectedProblem.dueDate && (
                <span className="text-amber-300">Due: {selectedProblem.dueDate}</span>
              )}
            </div>
          </div>

          {/* Problem Score Circular Gauge */}
          <div className="flex items-center gap-4 bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/15">
            <CircularGauge
              score={problemScore}
              maxScore={100}
              size={96}
              strokeWidth={8}
              color={problemScore >= 80 ? '#10b981' : '#3b82f6'}
              sublabel="Score"
            />
            <div className="text-left">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-300 block">
                {isAssigned ? 'Assignment Grade' : 'Practice Score'}
              </span>
              <span className="text-lg font-extrabold text-emerald-400 block font-mono">
                {problemScore} / 100
              </span>
              <span className="text-xs text-slate-300 font-medium">
                {isPassed ? 'Passed (All Assertions)' : 'Partial Evaluation'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: 5D Rubric Breakdown & Attempt Progression for this Problem */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Multi-Agent Rubric Scores (Col span 7) */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">
                5D Rubric Breakdown for "{selectedProblem.title}"
              </h3>
              <p className="text-xs text-slate-400">Independent AI evaluation agents profile</p>
            </div>
            <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">
              {problemScore} / 100
            </span>
          </div>

          <div className="space-y-4">
            <ScoreBar
              label="Correctness (Test Pass Ratio)"
              score={20}
              maxScore={25}
              barColor="#3b82f6"
              details="All sandbox test cases verified with zero memory overflow."
            />

            <ScoreBar
              label="Time Complexity"
              score={18}
              maxScore={25}
              barColor="#06b6d4"
              optimalBadge={`Detected: ${selectedProblem.optimalComplexity.time}`}
              details={`Optimal asymptotic Big-O runtime achieved (${selectedProblem.optimalComplexity.time}).`}
            />

            <ScoreBar
              label="Space Complexity"
              score={12}
              maxScore={15}
              barColor="#f59e0b"
              optimalBadge={`Detected: ${selectedProblem.optimalComplexity.space}`}
              details="Standard auxiliary allocation. Can optimize memory footprint via bucket pre-allocation."
            />

            <ScoreBar
              label="Code Quality & Structure"
              score={18}
              maxScore={20}
              barColor="#8b5cf6"
              details="Clean modular formatting. Identifier naming can be slightly more descriptive."
            />

            <ScoreBar
              label="Originality & Plagiarism"
              score={17}
              maxScore={20}
              barColor="#10b981"
              optimalBadge="Risk: Low"
              details="High AST semantic uniqueness compared to peer cohort."
            />
          </div>
        </div>

        {/* Right: Attempt Progression & AI Feedback on this Problem (Col span 5) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Attempt Progression Trend */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <LineChartIcon className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">Attempt Progression</h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">3 Iterations</span>
            </div>

            <ScoreTrendLineChart data={problemAttemptTrend} height={160} />

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-mono">
              <span>Attempt 1: <strong>65 pts</strong></span>
              <span className="text-emerald-600 font-bold">Latest: {problemScore} pts (+20)</span>
            </div>
          </div>

          {/* AI Explainability Box */}
          <div className="bg-slate-900 text-white rounded-3xl p-6 shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-indigo-300 text-xs font-bold">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>AI Problem Diagnostic</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Your solution for <strong>{selectedProblem.title}</strong> achieves optimal asymptotic time complexity {selectedProblem.optimalComplexity.time}. Consider applying bucket reservation to boost space efficiency from 12/15 to 15/15.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
