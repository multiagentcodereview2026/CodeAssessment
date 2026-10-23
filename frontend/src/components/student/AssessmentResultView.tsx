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
  Lightbulb,
  CheckSquare2
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { CircularGauge } from '../common/CircularGauge';
import { CodeDiffViewer } from '../common/CodeDiffViewer';
import { DifficultyBadge } from '../common/Badge';

export const AssessmentResultView: React.FC = () => {
  const navigate = useNavigate();
  const {
    activeAssessment,
    openProblemWorkspace,
    setCurrentView
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

  const scoreItems = [
    {
      label: 'Correctness',
      score: multiScores.correctness.score,
      max: multiScores.correctness.max,
      color: 'bg-blue-500',
      detail: multiScores.correctness.notes
    },
    {
      label: 'Time',
      score: multiScores.timeComplexity.score,
      max: multiScores.timeComplexity.max,
      color: 'bg-cyan-500',
      detail: `${multiScores.timeComplexity.detected} detected, ${multiScores.timeComplexity.optimal} target`
    },
    {
      label: 'Space',
      score: multiScores.spaceComplexity.score,
      max: multiScores.spaceComplexity.max,
      color: 'bg-amber-500',
      detail: `${multiScores.spaceComplexity.detected} detected, ${multiScores.spaceComplexity.optimal} target`
    },
    {
      label: 'Quality',
      score: multiScores.codeQuality.score,
      max: multiScores.codeQuality.max,
      color: 'bg-violet-500',
      detail: multiScores.codeQuality.notes
    },
    {
      label: 'Originality',
      score: multiScores.similarity.score,
      max: multiScores.similarity.max,
      color: 'bg-emerald-500',
      detail: `${multiScores.similarity.originalityPercent}% original, ${multiScores.similarity.plagiarismRisk.toLowerCase()} risk`
    }
  ];

  return (
    <div className="space-y-6 pb-16 animate-fadeIn">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <button
          onClick={() => navigate('/submissions')}
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-indigo-600 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Submissions</span>
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Share2 className="w-3.5 h-3.5 text-slate-500" />
            <span>Export Report</span>
          </button>
          <button
            onClick={() => {
              openProblemWorkspace(activeAssessment.problemId);
              navigate(`/problems/${activeAssessment.problemId}`);
            }}
            className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all hover:scale-105 active:scale-95 cursor-pointer"
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

      {/* Explainability First: Improvement Guidance & Compact Evidence */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-8 bg-gradient-to-br from-indigo-950 via-slate-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-lg relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-indigo-400 via-emerald-400 to-amber-300" />
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
            <div className="space-y-4 flex-1">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-indigo-500/20 text-indigo-200 rounded-2xl border border-indigo-400/20">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[11px] font-extrabold tracking-wider text-indigo-200 uppercase">
                    Explainable Feedback
                  </span>
                  <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight">
                    What to improve next
                  </h2>
                </div>
              </div>

              <p className="text-sm sm:text-base leading-relaxed text-slate-100 max-w-3xl">
                {explainableFeedback}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {suggestedImprovements.slice(0, 3).map((item, idx) => (
                  <div key={idx} className="rounded-2xl bg-white/8 border border-white/10 p-4">
                    <div className="flex items-center gap-2 text-emerald-300 font-bold text-xs">
                      <CheckSquare2 className="w-4 h-4" />
                      <span>Improvement {idx + 1}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-200 leading-relaxed">{item}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="w-full lg:w-64 rounded-2xl bg-white/8 border border-white/10 p-4 flex-shrink-0">
              <span className="text-[11px] font-bold uppercase text-slate-300">Projected Gain</span>
              <div className="mt-3 flex items-end justify-between">
                <div>
                  <span className="text-4xl font-extrabold text-emerald-300 font-mono">
                    +{scoreProjection.improvementDelta}
                  </span>
                  <span className="ml-1 text-xs text-slate-300">pts</span>
                </div>
                <TrendingUp className="w-6 h-6 text-emerald-300" />
              </div>
              <div className="mt-4 h-2 rounded-full bg-white/10 overflow-hidden">
                <div
                  className="h-full rounded-full bg-emerald-400"
                  style={{ width: `${Math.min(100, scoreProjection.projectedScore)}%` }}
                />
              </div>
              <p className="mt-3 text-xs text-slate-300 leading-relaxed">
                Current {scoreProjection.currentScore}/100. Target {scoreProjection.projectedScore}/100 after revision.
              </p>
            </div>
          </div>
        </div>

        {/* Compact Multi-Dimensional Scores */}
        <div className="xl:col-span-4 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">5D Score Evidence</h3>
              <p className="text-xs text-slate-400">Compact rubric signals</p>
            </div>
            <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">
              {multiScores.overallScore} / 100
            </span>
          </div>

          <div className="space-y-2.5">
            {scoreItems.map((item) => {
              const width = Math.min(100, Math.round((item.score / item.max) * 100));
              return (
                <div key={item.label} className="rounded-2xl bg-slate-50 border border-slate-200/70 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-bold text-slate-800">{item.label}</span>
                    <span className="text-xs font-mono font-extrabold text-slate-800">{item.score}/{item.max}</span>
                  </div>
                  <div className="mt-2 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${item.color}`} style={{ width: `${width}%` }} />
                  </div>
                  <p className="mt-1.5 text-[11px] text-slate-500 leading-snug line-clamp-2">{item.detail}</p>
                </div>
              );
            })}
          </div>

          {/* Test Case Results Summary */}
          <div className="pt-3 border-t border-slate-100">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">Test Case Results:</span>
              <span className="font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                Passed {testResults.length} / {testResults.length}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-xs">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <Lightbulb className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-900">Focus Areas</span>
              <p className="mt-1 text-[11px] text-slate-500 leading-relaxed">
                {scoreProjection.focusAreas.join(', ')}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-900">Iteration Path</span>
              <p className="mt-1 text-[11px] text-slate-500 leading-relaxed">
                {scoreProjection.iterationTimeline.map(step => `${step.stage}: ${step.score}`).join(' -> ')}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <Target className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-900">Recommended Topics</span>
              <p className="mt-1 text-[11px] text-slate-500 leading-relaxed">
                {recommendedTopics.join(', ')}
              </p>
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
        <div className="rounded-3xl bg-white border border-slate-200/80 p-3 shadow-xs">
          <CodeDiffViewer
            originalCode={code}
            revisedCode={aiRevisedCode}
            language={language}
            currentScore={scoreProjection.currentScore}
            projectedScore={scoreProjection.projectedScore}
            improvementDelta={scoreProjection.improvementDelta}
          />
        </div>
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
                    onClick={() => {
                      openProblemWorkspace(prob.id);
                      navigate(`/problems/${prob.id}`);
                    }}
                    className="p-2 text-slate-400 group-hover:text-indigo-600 group-hover:bg-indigo-50 rounded-xl transition-colors cursor-pointer"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => {
              setCurrentView('problems');
              navigate('/problems');
            }}
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
