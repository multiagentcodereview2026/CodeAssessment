import React from 'react';
import {
  Lightbulb,
  Sparkles,
  Target,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Code2
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';

export const RecommendationsView: React.FC = () => {
  const { activeAssessment, openProblemWorkspace, setCurrentView } = useApp();
  const { suggestedImprovements, recommendedTopics, practiceProblems } = activeAssessment;

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          AI Recommendations & Practice Suite
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Adaptive algorithmic learning path synthesized from your recent submissions.
        </p>
      </div>

      {/* Suggested Improvements Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-2xl">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Personalized Algorithmic Improvements
            </h2>
            <p className="text-xs text-slate-400">Synthesized from rubric agent evaluations</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {suggestedImprovements.map((imp, idx) => (
            <div key={idx} className="p-4 rounded-2xl bg-purple-50/40 border border-purple-100 flex flex-col justify-between space-y-3">
              <div className="space-y-2">
                <span className="text-[11px] font-extrabold text-purple-700 uppercase tracking-wider bg-purple-100 px-2 py-0.5 rounded">
                  Action Item #{idx + 1}
                </span>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  {imp}
                </p>
              </div>
              <div className="text-[11px] text-purple-600 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-purple-500" />
                <span>+2.5 score potential</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Topics */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">Recommended Topic Clusters</h3>
          </div>
          <span className="text-xs text-slate-400">High syllabus weight</span>
        </div>

        <div className="flex flex-wrap gap-3">
          {recommendedTopics.map((topic, idx) => (
            <div
              key={idx}
              onClick={() => setCurrentView('problems')}
              className="p-4 rounded-2xl bg-slate-50 border border-slate-200 hover:border-indigo-400 hover:bg-white transition-all cursor-pointer flex items-center justify-between min-w-[200px] flex-1 group"
            >
              <div>
                <span className="text-xs font-bold text-slate-800 group-hover:text-indigo-600 transition-colors">
                  {topic}
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">3 Practice problems</p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
            </div>
          ))}
        </div>
      </div>

      {/* Practice Problems Grid */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">Targeted Practice Problems</h3>
          </div>
          <button
            onClick={() => setCurrentView('problems')}
            className="text-xs font-bold text-indigo-600 hover:underline"
          >
            Explore all
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {practiceProblems.map((prob, idx) => (
            <div
              key={prob.id}
              className="p-5 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-4 hover:border-indigo-400 hover:bg-white transition-all group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold font-mono text-slate-400">#{idx + 1}</span>
                  <DifficultyBadge difficulty={prob.difficulty} />
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  {prob.title}
                </h4>
                <div className="flex flex-wrap gap-1 mt-2">
                  {prob.tags.map((t, tIdx) => (
                    <span key={tIdx} className="text-[10px] bg-slate-200/60 text-slate-700 px-1.5 py-0.5 rounded">
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={() => openProblemWorkspace('prob-1')}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Start Practice</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
