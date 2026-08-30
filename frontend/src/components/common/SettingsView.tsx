import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  ShieldCheck,
  Zap,
  Sliders,
  Check,
  Save
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const SettingsView: React.FC = () => {
  const { currentRole } = useApp();
  const [saved, setSaved] = useState(false);
  const [autoSave, setAutoSave] = useState(true);
  const [aiSuggestions, setAiSuggestions] = useState(true);
  const [similarityThreshold, setSimilarityThreshold] = useState('75');
  const [sandboxTimeout, setSandboxTimeout] = useState('2000');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Platform & Engine Settings
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure sandbox execution limits, compiler optimizations, and multi-agent AI assessment parameters.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* General Preferences */}
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-5">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <Sliders className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">General Workspace Preferences</h2>
          </div>

          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-800 block">Automatic Code Auto-Save</span>
                <span className="text-slate-500">Persist workspace buffer to local session every 10 seconds</span>
              </div>
              <input
                type="checkbox"
                checked={autoSave}
                onChange={(e) => setAutoSave(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <div>
                <span className="font-bold text-slate-800 block">Real-time AI Code Suggestions</span>
                <span className="text-slate-500">Provide inline AST optimization hints and complexity estimations</span>
              </div>
              <input
                type="checkbox"
                checked={aiSuggestions}
                onChange={(e) => setAiSuggestions(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Sandbox & AI Engine (Instructor Only / Advanced) */}
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-5">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <Cpu className="w-5 h-5 text-purple-600" />
            <h2 className="text-base font-bold text-slate-900">Sandbox & Multi-Agent Evaluation Engine</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Execution Timeout Limit (ms)
              </label>
              <input
                type="number"
                value={sandboxTimeout}
                onChange={(e) => setSandboxTimeout(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Default: 2000 ms per test case</span>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Plagiarism Similarity Alert Threshold (%)
              </label>
              <input
                type="number"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Trigger alert above 75% match</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end">
          <button
            type="submit"
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-xs shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all cursor-pointer"
          >
            {saved ? <Check className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
            <span>{saved ? 'Settings Saved!' : 'Save Preferences'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
