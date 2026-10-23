import React, { useState } from 'react';
import { Copy, Check, Sparkles, Code2, ArrowRight, Target, TrendingUp } from 'lucide-react';

interface CodeDiffViewerProps {
  originalCode: string;
  revisedCode: string;
  language?: string;
  currentScore?: number;
  projectedScore?: number;
  improvementDelta?: number;
}

export const CodeDiffViewer: React.FC<CodeDiffViewerProps> = ({
  originalCode,
  revisedCode,
  language = 'C++',
  currentScore = 85,
  projectedScore = 92,
  improvementDelta = 7
}) => {
  const [viewMode, setViewMode] = useState<'split' | 'revised'>('split');
  const [copied, setCopied] = useState(false);

  const handleCopyRevised = () => {
    navigator.clipboard.writeText(revisedCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between px-5 py-4 bg-slate-950 border-b border-slate-800 gap-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-purple-500/10 rounded-xl text-purple-300 border border-purple-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">AI-Optimized Solution Comparison</h4>
            <p className="text-xs text-slate-400">Bounded review pane for AST, naming, and complexity refinement</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-800 p-0.5 rounded-lg border border-slate-700 text-xs">
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                viewMode === 'split' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Side-by-Side Diff
            </button>
            <button
              onClick={() => setViewMode('revised')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                viewMode === 'revised' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              AI Revised Only
            </button>
          </div>

          <button
            onClick={handleCopyRevised}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied' : 'Copy Revised'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-0 bg-slate-900 border-b border-slate-800">
        <div className="px-5 py-3 border-b md:border-b-0 md:border-r border-slate-800">
          <span className="text-[10px] font-bold uppercase text-slate-500">Original</span>
          <div className="mt-1 flex items-center gap-2 text-rose-300 font-mono text-xs">
            <Code2 className="w-3.5 h-3.5" />
            <span>{currentScore}/100 submission</span>
          </div>
        </div>
        <div className="px-5 py-3 border-b md:border-b-0 md:border-r border-slate-800">
          <span className="text-[10px] font-bold uppercase text-slate-500">Target</span>
          <div className="mt-1 flex items-center gap-2 text-emerald-300 font-mono text-xs">
            <Target className="w-3.5 h-3.5" />
            <span>{projectedScore}/100 revised solution</span>
          </div>
        </div>
        <div className="px-5 py-3">
          <span className="text-[10px] font-bold uppercase text-slate-500">Expected Gain</span>
          <div className="mt-1 flex items-center gap-2 text-indigo-300 font-mono text-xs">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+{improvementDelta} rubric points</span>
          </div>
        </div>
      </div>

      {/* Code Area */}
      {viewMode === 'split' ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 divide-y xl:divide-y-0 xl:divide-x divide-slate-800 font-mono text-xs bg-slate-950">
          {/* Left: Original Code */}
          <div className="p-4 bg-slate-900">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800/80 text-slate-400">
              <span className="font-semibold text-rose-400 flex items-center gap-1.5">
                <Code2 className="w-3.5 h-3.5" /> Original Submission ({language})
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                Score: {currentScore}/100
              </span>
            </div>
            <pre className="max-h-[430px] text-slate-300 overflow-auto leading-relaxed whitespace-pre font-mono selection:bg-rose-500/30 custom-scrollbar pr-4">
              {originalCode.trim()}
            </pre>
          </div>

          {/* Right: AI Revised Code */}
          <div className="p-4 bg-slate-950">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800/80 text-slate-400">
              <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" /> AI Suggested Refinement
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-semibold">
                Target: {projectedScore}/100 (+{improvementDelta})
              </span>
            </div>
            <pre className="max-h-[430px] text-emerald-100/90 overflow-auto leading-relaxed whitespace-pre font-mono selection:bg-emerald-500/30 custom-scrollbar pr-4">
              {revisedCode.trim()}
            </pre>
          </div>
        </div>
      ) : (
        <div className="p-5 font-mono text-xs bg-slate-950">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800 text-slate-400">
            <span className="text-emerald-400 font-semibold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" /> Full AI Optimized Code ({language})
            </span>
          </div>
          <pre className="max-h-[520px] text-slate-200 overflow-auto leading-relaxed whitespace-pre font-mono custom-scrollbar pr-4">
            {revisedCode.trim()}
          </pre>
        </div>
      )}

      {/* Footer Key Changes */}
      <div className="px-4 py-3 bg-slate-950 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
          <span>Key optimizations: Bucket pre-allocation with <code className="text-purple-300">reserve()</code> & semantic variable naming.</span>
        </div>
        <div className="flex items-center gap-1 text-slate-500">
          <span>Iterative Engine v2.4</span>
          <ArrowRight className="w-3 h-3" />
        </div>
      </div>
    </div>
  );
};
