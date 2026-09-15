import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  ShieldCheck,
  Zap,
  Sliders,
  Check,
  Save,
  User,
  Key,
  Bell
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const SettingsView: React.FC = () => {
  const { currentUser, updateCurrentUser, currentRole, showToast } = useApp();
  const [activeTab, setActiveTab] = useState<'profile' | 'workspace' | 'engine' | 'security'>('profile');

  // Profile Form
  const [name, setName] = useState(currentUser.name);
  const [email, setEmail] = useState(currentUser.email);
  const [institution, setInstitution] = useState(currentUser.institution || 'Geethanjali College of Engg');
  const [department, setDepartment] = useState(currentUser.department || 'Computer Science & Engineering');

  // Preferences
  const [autoSave, setAutoSave] = useState(true);
  const [aiSuggestions, setAiSuggestions] = useState(true);
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [similarityThreshold, setSimilarityThreshold] = useState('75');
  const [sandboxTimeout, setSandboxTimeout] = useState('2000');
  const [apiKey, setApiKey] = useState('sk-langgraph-agent-eval-live-2026');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateCurrentUser({
      name,
      email,
      institution,
      department
    });
    showToast('Platform settings saved successfully!', 'success');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Platform & User Settings
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Configure profile details, sandbox execution limits, compiler optimizations, and multi-agent AI parameters.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex bg-slate-200/60 p-1.5 rounded-2xl border border-slate-200/80 max-w-lg">
        <button
          type="button"
          onClick={() => setActiveTab('profile')}
          className={`flex-1 py-2.5 px-3 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
            activeTab === 'profile'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <User className="w-3.5 h-3.5" />
          <span>Profile</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('workspace')}
          className={`flex-1 py-2.5 px-3 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
            activeTab === 'workspace'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Preferences</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('engine')}
          className={`flex-1 py-2.5 px-3 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
            activeTab === 'engine'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>AI Engine</span>
        </button>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-5">
            <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
              <User className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900">User Profile & Institutional Affiliation</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Institution</label>
                <input
                  type="text"
                  value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Department</label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-medium"
                />
              </div>
            </div>
          </div>
        )}

        {/* Workspace Tab */}
        {activeTab === 'workspace' && (
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-5">
            <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
              <Sliders className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900">Workspace & Notification Preferences</h2>
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

              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <div>
                  <span className="font-bold text-slate-800 block">Email Assessment Notifications</span>
                  <span className="text-slate-500">Receive summary reports when assignments are submitted or graded</span>
                </div>
                <input
                  type="checkbox"
                  checked={emailNotifs}
                  onChange={(e) => setEmailNotifs(e.target.checked)}
                  className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
                />
              </div>
            </div>
          </div>
        )}

        {/* Engine Tab */}
        {activeTab === 'engine' && (
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
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-mono text-xs"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">Default: 2000 ms per test case</span>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Plagiarism Alert Threshold (%)
                </label>
                <input
                  type="number"
                  value={similarityThreshold}
                  onChange={(e) => setSimilarityThreshold(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-mono text-xs"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">Trigger alert above 75% AST match</span>
              </div>

              <div className="sm:col-span-2">
                <label className="block font-bold text-slate-700 mb-1">
                  Multi-Agent Evaluation API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-mono text-xs"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">Connected to local FastAPI backend on port 8000</span>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center justify-end">
          <button
            type="submit"
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl font-bold text-xs shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>
        </div>
      </form>
    </div>
  );
};
