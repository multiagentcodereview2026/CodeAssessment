import React, { useState } from 'react';
import {
  ShieldAlert,
  Users,
  Code2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Sparkles,
  ArrowRight,
  Check
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const SimilarityReviewView: React.FC = () => {
  const { similarityAlerts, dismissSimilarityAlert, showToast } = useApp();
  const [selectedAlertIndex, setSelectedAlertIndex] = useState<number>(0);

  const activeAlert = similarityAlerts[selectedAlertIndex] || similarityAlerts[0];

  const handleDismiss = (id: string) => {
    dismissSimilarityAlert(id);
    setSelectedAlertIndex(0);
  };

  const handleRequestReview = (id: string) => {
    showToast(`Investigation scheduled with ${activeAlert.studentA.name} & ${activeAlert.studentB.name}`, 'warning');
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Code Similarity & Plagiarism Shield
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            AST-level token matching, semantic clone detection, and cohort cross-checking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-rose-700 bg-rose-50 px-3.5 py-2 rounded-2xl border border-rose-200 flex items-center gap-1.5 shadow-xs">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <span>{similarityAlerts.length} Flagged Case(s)</span>
          </span>
        </div>
      </div>

      {similarityAlerts.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
            <Check className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800">Zero Similarity Incidents</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            All current submissions have passed AST-token uniqueness checks and semantic clone benchmarks.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Incident Selector Pills if multiple */}
          {similarityAlerts.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {similarityAlerts.map((alert, idx) => (
                <button
                  key={alert.id}
                  onClick={() => setSelectedAlertIndex(idx)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
                    selectedAlertIndex === idx
                      ? 'bg-rose-600 text-white shadow-md shadow-rose-600/20'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <span>Incident #{idx + 1}</span>
                  <span className="font-mono text-[10px] opacity-80">{alert.similarityPercentage}% Match</span>
                </button>
              ))}
            </div>
          )}

          {/* Top alert banner */}
          <div className="bg-rose-50 border border-rose-200 rounded-3xl p-6 sm:p-7 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs">
            <div className="flex items-start gap-4">
              <div className="p-3.5 bg-rose-600 text-white rounded-2xl shadow-md shadow-rose-600/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-extrabold text-rose-950">
                    High Similarity Detected ({activeAlert.similarityPercentage}%)
                  </h3>
                  <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase bg-rose-200 text-rose-900 rounded-md">
                    Risk: {activeAlert.riskLevel}
                  </span>
                </div>
                <p className="text-xs text-rose-800">
                  Problem: <strong>{activeAlert.problemTitle}</strong> • Flagged on {activeAlert.timestamp}
                </p>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2.5">
              <button
                onClick={() => handleDismiss(activeAlert.id)}
                className="px-4 py-2.5 bg-white hover:bg-slate-100 text-slate-700 rounded-2xl text-xs font-bold border border-slate-200 transition-all hover:scale-105 active:scale-95 cursor-pointer shadow-xs"
              >
                Dismiss Flag
              </button>
              <button
                onClick={() => handleRequestReview(activeAlert.id)}
                className="px-5 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-2xl text-xs font-bold shadow-md shadow-rose-600/20 transition-all hover:scale-105 active:scale-95 cursor-pointer"
              >
                Request Viva / Review
              </button>
            </div>
          </div>

          {/* Side-by-Side Student Code Comparison */}
          <div className="bg-slate-900 rounded-3xl border border-slate-800 overflow-hidden shadow-xl">
            <div className="p-4 sm:p-5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-xs">
                <Code2 className="w-4 h-4 text-indigo-400" />
                <span>Pairwise AST Token & Structural Comparison</span>
              </div>
              <span className="text-xs font-mono text-rose-400 bg-rose-500/10 px-3 py-1 rounded-lg border border-rose-500/20">
                {activeAlert.matchedLinesCount} Token-Matched Blocks
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-800 font-mono text-xs">
              {/* Student A */}
              <div className="p-5 sm:p-6 bg-slate-900/60">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                  <div>
                    <span className="text-sm font-bold text-white block">{activeAlert.studentA.name}</span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Roll: {activeAlert.studentA.rollNumber} • Sub: {activeAlert.studentA.submissionId}
                    </span>
                  </div>
                  <span className="text-xs px-2.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded-md border border-indigo-500/30">
                    Student A
                  </span>
                </div>
                <pre className="text-slate-300 leading-relaxed overflow-x-auto whitespace-pre custom-scrollbar">
                  {activeAlert.studentACodeSnippet}
                </pre>
              </div>

              {/* Student B */}
              <div className="p-5 sm:p-6 bg-slate-950/60">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                  <div>
                    <span className="text-sm font-bold text-white block">{activeAlert.studentB.name}</span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Roll: {activeAlert.studentB.rollNumber} • Sub: {activeAlert.studentB.submissionId}
                    </span>
                  </div>
                  <span className="text-xs px-2.5 py-0.5 bg-rose-500/20 text-rose-300 rounded-md border border-rose-500/30">
                    Student B
                  </span>
                </div>
                <pre className="text-slate-300 leading-relaxed overflow-x-auto whitespace-pre custom-scrollbar">
                  {activeAlert.studentBCodeSnippet}
                </pre>
              </div>
            </div>

            {/* AI Audit Explanation */}
            <div className="p-5 bg-slate-950 border-t border-slate-800 text-xs text-slate-300 space-y-1.5">
              <div className="flex items-center gap-1.5 text-purple-400 font-bold">
                <Sparkles className="w-4 h-4" />
                <span>AI Plagiarism Audit Notes:</span>
              </div>
              <p className="text-slate-400 font-sans leading-relaxed">
                {activeAlert.aiAuditNotes}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
