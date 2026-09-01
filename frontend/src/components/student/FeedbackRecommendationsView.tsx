import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  MessageSquareText,
  Sparkles,
  Calendar,
  ArrowRight,
  Search,
  BookOpen,
  Target,
  Code2,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { DifficultyBadge } from '../common/Badge';

export const FeedbackRecommendationsView: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { submissions, openAssessmentResult, openProblemWorkspace, activeAssessment } = useApp();

  // Tab State: 'feedback' | 'recommendations' (Strict binary toggle)
  const initialTab = searchParams.get('tab') === 'practice' ? 'recommendations' : 'feedback';
  const [activeTab, setActiveTab] = useState<'feedback' | 'recommendations'>(initialTab);
  const [search, setSearch] = useState('');

  const { recommendedTopics, practiceProblems } = activeAssessment;

  const filteredSubmissions = submissions.filter((s) =>
    s.problemTitle.toLowerCase().includes(search.toLowerCase()) ||
    (s.feedbackSummary && s.feedbackSummary.toLowerCase().includes(search.toLowerCase())) ||
    s.language.toLowerCase().includes(search.toLowerCase())
  );

  const handleOpenReport = (subId: string) => {
    openAssessmentResult(subId);
    navigate('/result');
  };

  const handleStartPractice = (probId: string) => {
    openProblemWorkspace(probId);
    navigate(`/problems/${probId}`);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Unified Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            AI Feedback & Recommendations
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Personalized algorithmic coaching, explainable evaluation history, and adaptive practice path.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600 bg-white px-3.5 py-2.5 rounded-2xl border border-slate-200 shadow-xs">
            Evaluated Submissions: <strong className="text-indigo-600 font-mono text-sm ml-1">{submissions.length}</strong>
          </span>
        </div>
      </div>

      {/* Segmented View Controls (Either 'AI Feedback' or 'Practice & Topics') */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Binary 2-Tab Switcher */}
        <div className="flex bg-slate-200/60 p-1.5 rounded-2xl border border-slate-200/80 max-w-md w-full md:w-auto">
          <button
            onClick={() => setActiveTab('feedback')}
            className={`flex-1 md:flex-initial py-2.5 px-5 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
              activeTab === 'feedback'
                ? 'bg-white text-indigo-600 shadow-sm shadow-indigo-100'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <MessageSquareText className="w-3.5 h-3.5" />
            <span>AI Feedback</span>
            <span className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono font-bold ${activeTab === 'feedback' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'}`}>
              {submissions.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('recommendations')}
            className={`flex-1 md:flex-initial py-2.5 px-5 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
              activeTab === 'recommendations'
                ? 'bg-white text-indigo-600 shadow-sm shadow-indigo-100'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            <span>Practice & Topics</span>
            <span className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono font-bold ${activeTab === 'recommendations' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'}`}>
              {practiceProblems.length}
            </span>
          </button>
        </div>

        {/* Search Bar (Only shown on Feedback tab) */}
        {activeTab === 'feedback' && (
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search feedback notes or code..."
              className="w-full pl-10 pr-4 py-2.5 text-xs bg-white border border-slate-200 rounded-2xl focus:outline-none focus:border-indigo-500 shadow-xs"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* TAB 1: AI FEEDBACK */}
      {activeTab === 'feedback' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquareText className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Recent AI Coaching & Evaluations</h3>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              {filteredSubmissions.length} Submissions Logged
            </span>
          </div>

          <div className="space-y-3">
            {filteredSubmissions.length === 0 ? (
              <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
                No feedback notes found matching your search.
              </div>
            ) : (
              filteredSubmissions.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleOpenReport(item.id)}
                  className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs hover:border-indigo-300 card-hover transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group cursor-pointer"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3.5 bg-indigo-50 text-indigo-600 rounded-2xl flex-shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                      <MessageSquareText className="w-5 h-5" />
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                          {item.problemTitle}
                        </h3>
                        <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          {item.date}
                        </span>
                        <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                          {item.language}
                        </span>
                      </div>

                      <p className="text-xs text-slate-600 leading-relaxed font-sans">
                        {item.feedbackSummary || 'Code passed test validations. Evaluated against multi-agent rubric.'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end sm:self-center flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                    <div className={`px-3 py-1.5 rounded-xl font-mono font-bold text-xs flex items-center gap-1 ${
                      item.score >= 85 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                      item.score >= 70 ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
                      item.score >= 60 ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                      'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      <span>{item.score} / 100</span>
                    </div>

                    <button
                      onClick={() => handleOpenReport(item.id)}
                      className="px-4 py-2 bg-slate-900 hover:bg-indigo-600 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer active:scale-95"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Full Report</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 2: PRACTICE & TOPICS */}
      {activeTab === 'recommendations' && (
        <div className="space-y-6">
          {/* Recommended Topic Clusters */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Recommended Topic Clusters</h3>
              </div>
              <span className="text-xs text-slate-400 font-medium">High syllabus weight</span>
            </div>

            <div className="flex flex-wrap gap-3">
              {recommendedTopics.map((topic, idx) => (
                <div
                  key={idx}
                  onClick={() => navigate('/problems')}
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

          {/* Targeted Practice Problems */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">Targeted Practice Problems</h3>
              </div>
              <button
                onClick={() => navigate('/problems')}
                className="text-xs font-bold text-indigo-600 hover:underline cursor-pointer"
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
                    onClick={() => handleStartPractice(prob.id)}
                    className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-xs flex items-center justify-center gap-1.5 transition-all hover:scale-105 active:scale-95 cursor-pointer"
                  >
                    <Code2 className="w-3.5 h-3.5" />
                    <span>Start Practice</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
