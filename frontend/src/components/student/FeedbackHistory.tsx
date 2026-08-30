import React, { useState } from 'react';
import {
  MessageSquareText,
  Sparkles,
  Calendar,
  ArrowRight,
  Search
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const FeedbackHistory: React.FC = () => {
  const { submissions, openAssessmentResult, openProblemWorkspace } = useApp();
  const [search, setSearch] = useState('');

  const filtered = submissions.filter((s) =>
    s.problemTitle.toLowerCase().includes(search.toLowerCase()) ||
    (s.feedbackSummary && s.feedbackSummary.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            AI Feedback & Insights
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Personalized algorithmic coaching and explainable feedback history.
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search feedback notes..."
            className="w-full pl-10 pr-4 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* List of Feedback Cards (Matches diagram feedback view) */}
      <div className="space-y-4">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="bg-white rounded-2xl border border-slate-200/80 p-5 sm:p-6 shadow-xs hover:border-indigo-300 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl flex-shrink-0">
                <MessageSquareText className="w-5 h-5" />
              </div>

              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-3">
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {item.problemTitle}
                  </h3>
                  <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {item.date}
                  </span>
                  <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                    {item.language}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed font-sans">
                  {item.feedbackSummary || 'Code passed test validations. Evaluated against multi-agent rubric.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 self-end sm:self-center flex-shrink-0">
              {/* Score pill matching diagram */}
              <div className={`px-3 py-1.5 rounded-xl font-mono font-bold text-xs flex items-center gap-1 ${
                item.score >= 85 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                item.score >= 70 ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
                item.score >= 60 ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                'bg-rose-50 text-rose-700 border border-rose-200'
              }`}>
                <span>{item.score}</span>
              </div>

              <button
                onClick={() => openAssessmentResult(item.id)}
                className="px-3 py-1.5 bg-slate-900 hover:bg-indigo-600 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Full Report</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
