import React, { useState } from 'react';
import { Copy, Check, Sparkles, Code2, ArrowRight } from 'lucide-react';

interface CodeDiffViewerProps {
  originalCode: string;
  revisedCode: string;
  language?: string;
}

export const CodeDiffViewer: React.FC<CodeDiffViewerProps> = ({
  originalCode,
  revisedCode,
  language = 'C++'
}) => {
  const [viewMode, setViewMode] = useState<'split' | 'revised'>('split');
  const [copied, setCopied] = useState(false);

  const handleCopyRevised = () => {
    navigator.clipboard.writeText(revisedCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-slate-950/80 border-b border-slate-800 gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-purple-500/10 rounded-lg text-purple-400 border border-purple-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">AI-Optimized Solution Comparison</h4>
            <p className="text-xs text-slate-400">Side-by-side AST & logic refinement</p>
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

      {/* Code Area */}
      {viewMode === 'split' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-800 font-mono text-xs">
          {/* Left: Original Code */}
          <div className="p-4 bg-slate-900/50">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800/80 text-slate-400">
              <span className="font-semibold text-rose-400 flex items-center gap-1.5">
                <Code2 className="w-3.5 h-3.5" /> Original Submission ({language})
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                Score: 85/100
              </span>
            </div>
            <pre className="text-slate-300 overflow-x-auto leading-relaxed whitespace-pre font-mono selection:bg-rose-500/30">
              {originalCode.trim()}
            </pre>
          </div>

          {/* Right: AI Revised Code */}
          <div className="p-4 bg-slate-950/40">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800/80 text-slate-400">
              <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" /> AI Suggested Refinement
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-semibold">
                Target: 92/100 (+7)
              </span>
            </div>
            <pre className="text-emerald-100/90 overflow-x-auto leading-relaxed whitespace-pre font-mono selection:bg-emerald-500/30">
              {revisedCode.trim()}
            </pre>
          </div>
        </div>
      ) : (
        <div className="p-5 font-mono text-xs bg-slate-900">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800 text-slate-400">
            <span className="text-emerald-400 font-semibold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" /> Full AI Optimized Code ({language})
            </span>
          </div>
          <pre className="text-slate-200 overflow-x-auto leading-relaxed whitespace-pre font-mono">
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
