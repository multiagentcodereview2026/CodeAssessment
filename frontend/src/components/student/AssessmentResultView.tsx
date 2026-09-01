import React from 'react';
import {
  CheckCircle2,
  Clock,
  HardDrive,
  Sparkles,
  ArrowRight,
  ChevronRight,
  TrendingUp,
  Target,
  ArrowLeft,
  Share2,
  Play,
  GraduationCap,
  Code2,
  Lightbulb,
  Check,
  Cpu,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { CircularGauge } from '../common/CircularGauge';
import { ScoreBar } from '../common/ScoreBar';
import { CodeDiffViewer } from '../common/CodeDiffViewer';
import { DifficultyBadge } from '../common/Badge';

export const AssessmentResultView: React.FC = () => {
  const {
    activeAssessment,
    setCurrentView,
    goBackToDashboard,
    openProblemWorkspace
  } = useApp();

  const {
    submissionId,
    problemTitle,
    language,
    executionTime,
    memory,
    multiScores,
    explainableFeedback,
    suggestedImprovements,
    recommendedTopics,
    practiceProblems,
    scoreProjection,
    aiRevisedCode,
    code,
    testResults,
    isAssignedSubmission
  } = activeAssessment;

  return (
    <div className="space-y-6 pb-16 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <button
          onClick={goBackToDashboard}
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-indigo-600 transition-colors p-2 hover:bg-slate-100 rounded-xl cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setCurrentView('scores')}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-colors"
          >
            Detailed Score Matrix
          </button>
          <button
            onClick={() => openProblemWorkspace(activeAssessment.problemId)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Iterate & Re-Submit</span>
          </button>
        </div>
      </div>

      {/* Mode Indicator Banner */}
      <div className={`p-3.5 px-5 rounded-2xl border text-xs font-semibold flex items-center justify-between ${
        isAssignedSubmission
          ? 'bg-indigo-50 border-indigo-200 text-indigo-900'
          : 'bg-purple-50 border-purple-200 text-purple-900'
      }`}>
        <div className="flex items-center gap-2">
          {isAssignedSubmission ? <GraduationCap className="w-4 h-4 text-indigo-600" /> : <Code2 className="w-4 h-4 text-purple-600" />}
          <span>
            {isAssignedSubmission
              ? 'Instructor Coursework Submission • Graded for CSE-301 Section A'
              : 'Self-Paced Practice Submission • Independent Sandbox Assessment'}
          </span>
        </div>
        <span className="font-mono text-[11px] text-slate-500">ID: {submissionId}</span>
      </div>

      {/* Hero Section: Submission Status & Headline */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 flex-1">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Accepted • All {testResults.length} Test Cases Passed</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {problemTitle}
            </h1>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 font-mono pt-1">
              <span>Language: <strong className="text-slate-800 font-sans">{language}</strong></span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Time: <strong className="text-slate-800">{executionTime}</strong>
              </span>
              <span className="flex items-center gap-1">
                <HardDrive className="w-3.5 h-3.5 text-slate-400" />
                Memory: <strong className="text-slate-800">{memory}</strong>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-200/80">
            <CircularGauge
              score={multiScores.overallScore}
              maxScore={100}
              size={90}
              strokeWidth={8}
              color="#10b981"
              sublabel="Score"
            />
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                Overall Score
              </span>
              <span className="text-xl font-extrabold text-emerald-600 block font-mono">
                {multiScores.overallScore} / 100
              </span>
              <span className="text-xs text-slate-500 font-medium">
                Grade: Excellent
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* EXPLAINABILITY HERO SECTION (DOMINANT & PROMINENTLY LARGER) */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LARGE PROMINENT EXPLAINABILITY CARD (Col span 8) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-7 shadow-lg border border-indigo-800/40 relative overflow-hidden space-y-6">
            <div className="flex items-center justify-between border-b border-indigo-800/60 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-indigo-600 text-white rounded-xl shadow-md">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-lg font-extrabold text-white tracking-tight">
                    AI Explainable Code Feedback
                  </h2>
                  <p className="text-xs text-indigo-200">
                    Comprehensive algorithmic analysis and line-by-line reasoning
                  </p>
                </div>
              </div>

              <span className="px-3 py-1 bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 rounded-full text-xs font-mono font-bold">
                AST Confidence: 99.4%
              </span>
            </div>

            {/* Primary Explainable Narrative (Large & Readable) */}
            <div className="p-5 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-300 block">
                Algorithmic Evaluation & Insight:
              </span>
              <p className="text-sm sm:text-base leading-relaxed text-slate-100 font-medium">
                "{explainableFeedback}"
              </p>
            </div>

            {/* Specific Key Improvements & Action Items */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                Actionable Optimization Steps:
              </h3>
              <div className="space-y-2.5">
                {suggestedImprovements.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-slate-900/80 rounded-xl border border-slate-800 flex items-start gap-3 text-xs leading-relaxed text-slate-200"
                  >
                    <div className="p-1 bg-indigo-500/20 text-indigo-400 rounded-lg flex-shrink-0 mt-0.5">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Score Projection Callout */}
            <div className="p-4 bg-emerald-950/40 rounded-2xl border border-emerald-500/30 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-emerald-400 block">
                  Projected Score After Applying Revision:
                </span>
                <span className="text-2xl font-extrabold text-emerald-300 font-mono">
                  {scoreProjection.projectedScore} / 100
                </span>
              </div>
              <span className="px-3 py-1.5 bg-emerald-500/20 text-emerald-300 rounded-xl text-xs font-bold border border-emerald-400/30">
                +{scoreProjection.improvementDelta} pts Projected Boost
              </span>
            </div>
          </div>

          {/* AI Code Diff Refactoring */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs space-y-3">
            <div>
              <h3 className="text-base font-bold text-slate-900">
                AI Suggested Code Optimization Diff
              </h3>
              <p className="text-xs text-slate-500">
                Side-by-side AST comparison of your submitted code vs AI optimized implementation.
              </p>
            </div>

            <CodeDiffViewer
              originalCode={code}
              revisedCode={aiRevisedCode}
              language={language}
            />
          </div>
        </div>

        {/* COMPACT COMPANION CARD: MULTI-DIMENSIONAL SCORES (Col span 4) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
            <div className="pb-3 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Rubric Scores Summary
                </h3>
                <p className="text-[11px] text-slate-400">5-agent evaluation rubric</p>
              </div>
              <span className="text-xs font-mono font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
                {multiScores.overallScore}/100
              </span>
            </div>

            <div className="space-y-4">
              <ScoreBar
                label="Correctness"
                score={multiScores.correctness.score}
                maxScore={multiScores.correctness.max}
                barColor="#3b82f6"
                details={multiScores.correctness.notes}
              />

              <ScoreBar
                label="Time Complexity"
                score={multiScores.timeComplexity.score}
                maxScore={multiScores.timeComplexity.max}
                barColor="#06b6d4"
                optimalBadge={`${multiScores.timeComplexity.detected}`}
                details={multiScores.timeComplexity.notes}
              />

              <ScoreBar
                label="Space Complexity"
                score={multiScores.spaceComplexity.score}
                maxScore={multiScores.spaceComplexity.max}
                barColor="#f59e0b"
                optimalBadge={`${multiScores.spaceComplexity.detected}`}
                details={multiScores.spaceComplexity.notes}
              />

              <ScoreBar
                label="Code Quality"
                score={multiScores.codeQuality.score}
                maxScore={multiScores.codeQuality.max}
                barColor="#8b5cf6"
                details={multiScores.codeQuality.notes}
              />

              <ScoreBar
                label="Similarity"
                score={multiScores.similarity.score}
                maxScore={multiScores.similarity.max}
                barColor="#10b981"
                optimalBadge={`Risk: ${multiScores.similarity.plagiarismRisk}`}
                details={multiScores.similarity.notes}
              />
            </div>
          </div>

          {/* Recommended Practice Problems */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
            <div className="pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">
                Recommended Practice
              </h3>
              <p className="text-[11px] text-slate-400">Targeted reinforcement challenges</p>
            </div>

            <div className="space-y-2.5">
              {practiceProblems.map((prob) => (
                <div
                  key={prob.id}
                  onClick={() => openProblemWorkspace('prob-1')}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 hover:bg-white hover:border-indigo-400 transition-all cursor-pointer flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-bold text-slate-800 block">
                      {prob.title}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {prob.tags.join(', ')}
                    </span>
                  </div>
                  <DifficultyBadge difficulty={prob.difficulty} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
