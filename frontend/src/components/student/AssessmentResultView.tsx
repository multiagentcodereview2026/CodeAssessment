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
  Play
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
    testResults
  } = activeAssessment;

  return (
    <div className="space-y-6 pb-16 animate-fadeIn">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <button
          onClick={() => setCurrentView('submissions')}
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Submissions</span>
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Share2 className="w-3.5 h-3.5 text-slate-500" />
            <span>Export Report</span>
          </button>
          <button
            onClick={() => openProblemWorkspace(activeAssessment.problemId)}
            className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Iterate & Re-Submit</span>
          </button>
        </div>
      </div>

      {/* Main Top Banner: Accepted Status & Circular Score (Matches Step 5 in diagram) */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          {/* Left info */}
          <div className="space-y-3 flex-1">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Accepted • All test cases passed!</span>
            </div>

            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                {problemTitle}
              </h1>
              <p className="text-xs text-slate-500 mt-1">
                Evaluated by Multi-Agent AI Assessment Engine • Rubric v2.4
              </p>
            </div>

            {/* Metadata Pills */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 pt-1 font-mono">
              <span className="bg-slate-100 px-2.5 py-1 rounded-lg">
                ID: <strong className="text-slate-800">{submissionId}</strong>
              </span>
              <span className="bg-slate-100 px-2.5 py-1 rounded-lg">
                Language: <strong className="text-slate-800 font-sans">{language}</strong>
              </span>
              <span className="bg-slate-100 px-2.5 py-1 rounded-lg flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Time: <strong className="text-slate-800">{executionTime}</strong>
              </span>
              <span className="bg-slate-100 px-2.5 py-1 rounded-lg flex items-center gap-1">
                <HardDrive className="w-3.5 h-3.5 text-slate-400" />
                Memory: <strong className="text-slate-800">{memory}</strong>
              </span>
            </div>
          </div>

          {/* Right Circular Gauge (Matching diagram 85/100) */}
          <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-200/80 self-center md:self-auto">
            <CircularGauge
              score={multiScores.overallScore}
              maxScore={100}
              size={110}
              strokeWidth={9}
              color="#10b981"
              sublabel="Score"
            />
            <div className="text-left">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Overall Grade
              </span>
              <span className="text-lg font-extrabold text-emerald-600 block">
                Excellent (A)
              </span>
              <span className="text-xs text-slate-500 font-medium">
                Top 15% in cohort
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Multi-Dimensional Scores & Explainable Feedback (Step 5) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Multi-Dimensional Scores (Col span 7) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Multi-Dimensional Score Breakdown</h3>
              <p className="text-xs text-slate-400">Independent rubric agent evaluations</p>
            </div>
            <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">
              {multiScores.overallScore} / 100
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
              optimalBadge={`${multiScores.timeComplexity.detected} (Opt: ${multiScores.timeComplexity.optimal})`}
              details={multiScores.timeComplexity.notes}
            />

            <ScoreBar
              label="Space Complexity"
              score={multiScores.spaceComplexity.score}
              maxScore={multiScores.spaceComplexity.max}
              barColor="#f59e0b"
              optimalBadge={`${multiScores.spaceComplexity.detected} (Opt: ${multiScores.spaceComplexity.optimal})`}
              details={multiScores.spaceComplexity.notes}
            />

            <ScoreBar
              label="Code Quality & Structure"
              score={multiScores.codeQuality.score}
              maxScore={multiScores.codeQuality.max}
              barColor="#8b5cf6"
              details={multiScores.codeQuality.notes}
            />

            <ScoreBar
              label="Similarity / Originality"
              score={multiScores.similarity.score}
              maxScore={multiScores.similarity.max}
              barColor="#10b981"
              optimalBadge={`Risk: ${multiScores.similarity.plagiarismRisk}`}
              details={multiScores.similarity.notes}
            />
          </div>

          {/* Test Case Results Summary */}
          <div className="mt-4 pt-4 border-t border-slate-100">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">Test Case Results:</span>
              <span className="font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                Passed {testResults.length} / {testResults.length}
              </span>
            </div>
          </div>
        </div>

        {/* Explainable Feedback & AI Synthesis (Col span 5) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Explainable Feedback Callout */}
          <div className="bg-gradient-to-br from-indigo-900 to-slate-900 text-white rounded-2xl p-6 shadow-md relative overflow-hidden">
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 bg-indigo-500/20 text-indigo-300 rounded-lg">
                <Sparkles className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold tracking-tight text-indigo-200 uppercase">
                Explainable Feedback
              </h3>
            </div>
            <p className="text-xs leading-relaxed text-slate-200">
              "{explainableFeedback}"
            </p>
            <div className="mt-4 pt-3 border-t border-indigo-800/80 flex items-center justify-between text-[11px] text-indigo-300">
              <span>Agent Confidence: 99.4%</span>
              <span className="font-mono">AST Verifier #409</span>
            </div>
          </div>

          {/* Score Projection Card (Matches Step 7 in diagram) */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Score Projection</h3>
                <p className="text-xs text-slate-400">Target score after recommended revisions</p>
              </div>
              <TrendingUp className="w-4 h-4 text-emerald-600" />
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-50/70 border border-emerald-200/80">
              <div>
                <span className="text-xs font-semibold text-emerald-800">
                  Projected Score After Improvement
                </span>
                <div className="flex items-baseline gap-1 mt-0.5">
                  <span className="text-3xl font-extrabold text-emerald-700 font-mono">
                    {scoreProjection.projectedScore}
                  </span>
                  <span className="text-xs font-mono text-emerald-600">/ 100</span>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-extrabold text-emerald-600 bg-emerald-100/80 px-2.5 py-1 rounded-full">
                  +{scoreProjection.improvementDelta} pts
                </span>
                <p className="text-[11px] text-slate-500 mt-1">From current {scoreProjection.currentScore}</p>
              </div>
            </div>

            {/* Focus Areas */}
            <div>
              <span className="text-xs font-bold text-slate-700 mb-2 block">Focus Areas:</span>
              <div className="space-y-1.5">
                {scoreProjection.focusAreas.map((area, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs text-slate-600">
                    <Target className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" />
                    <span>{area}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Iteration Timeline */}
            <div className="pt-3 border-t border-slate-100">
              <span className="text-xs font-bold text-slate-700 mb-2 block">Iteration Loop Timeline:</span>
              <div className="relative pl-4 space-y-3 before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                {scoreProjection.iterationTimeline.map((step, idx) => (
                  <div key={idx} className="relative text-xs">
                    <div className={`absolute -left-4 top-1 w-2.5 h-2.5 rounded-full border-2 border-white ${
                      idx === 1 ? 'bg-indigo-600 ring-2 ring-indigo-200' : idx === 2 ? 'bg-emerald-500' : 'bg-slate-400'
                    }`} />
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-800">{step.stage}</span>
                      <span className="font-mono font-bold text-indigo-600">{step.score} pts</span>
                    </div>
                    <p className="text-[11px] text-slate-500">{step.note}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Revised Code Side-by-Side Comparison */}
      <div className="space-y-2">
        <h3 className="text-base font-bold text-slate-900">AI Code Revision & Optimization Diff</h3>
        <p className="text-xs text-slate-500">
          Compare your submitted solution with the AI engine's proposed refactor to hit {scoreProjection.projectedScore}/100.
        </p>
        <CodeDiffViewer
          originalCode={code}
          revisedCode={aiRevisedCode}
          language={language}
        />
      </div>

      {/* Recommendations & Next Steps Grid (Matches Step 6 in diagram) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Suggested Improvements Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900">Suggested Improvements</h3>
            <Sparkles className="w-4 h-4 text-purple-600" />
          </div>

          <ul className="space-y-2.5 text-xs text-slate-600">
            {suggestedImprovements.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 flex-shrink-0" />
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>

          <div className="pt-3 border-t border-slate-100">
            <span className="text-xs font-bold text-slate-700 mb-2 block">Recommended Topics:</span>
            <div className="flex flex-wrap gap-2">
              {recommendedTopics.map((topic, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentView('problems')}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 transition-colors"
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Recommended Practice Problems Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Practice Problems</h3>
                <p className="text-xs text-slate-400">Targeted reinforcement based on this submission</p>
              </div>
              <Target className="w-4 h-4 text-indigo-600" />
            </div>

            <div className="space-y-3">
              {practiceProblems.map((prob, idx) => (
                <div
                  key={prob.id}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between group hover:bg-white hover:border-indigo-300 transition-all"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-800">
                        {idx + 1}. {prob.title}
                      </span>
                      <DifficultyBadge difficulty={prob.difficulty} />
                    </div>
                    <div className="flex gap-1.5">
                      {prob.tags.map((t, tIdx) => (
                        <span key={tIdx} className="text-[10px] text-slate-500 font-mono">
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => openProblemWorkspace(prob.id)}
                    className="p-2 text-slate-400 group-hover:text-indigo-600 group-hover:bg-indigo-50 rounded-xl transition-colors cursor-pointer"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => setCurrentView('problems')}
            className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all cursor-pointer mt-4"
          >
            <span>Start Practice Suite</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
