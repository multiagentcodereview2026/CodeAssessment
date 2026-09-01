import React, { useState } from 'react';
import {
  Plus,
  Calendar,
  CheckCircle2,
  Clock,
  ArrowRight,
  FileCode2,
  Trash2,
  GraduationCap,
  Cpu,
  Layers,
  Send,
  Code2,
  HardDrive
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { Assignment, Problem, Difficulty, TestCase } from '../../types';
import { Modal } from '../common/Modal';

export const AssignmentsManagerView: React.FC = () => {
  const { assignments, addAssignment, problems, currentUser } = useApp();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [tabType, setTabType] = useState<'custom' | 'existing'>('custom');

  // Existing selection form
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [course, setCourse] = useState('CSE-301 Data Structures');
  const [dueDate, setDueDate] = useState('15 June, 2026');
  const [selectedProbIds, setSelectedProbIds] = useState<string[]>(['prob-1', 'prob-2']);

  // Custom question form with explicit test cases & time complexity
  const [customTitle, setCustomTitle] = useState('');
  const [customDesc, setCustomDesc] = useState('');
  const [customDiff, setCustomDiff] = useState<Difficulty>('Medium');
  const [customTags, setCustomTags] = useState('Dynamic Programming, Arrays');
  const [customTimeComplexity, setCustomTimeComplexity] = useState('O(N)');
  const [customSpaceComplexity, setCustomSpaceComplexity] = useState('O(1)');
  const [customTimeLimit, setCustomTimeLimit] = useState('1.5 seconds');

  // Dynamic test cases list explicitly provided by instructor
  const [customTestCases, setCustomTestCases] = useState<Array<{ id: string; input: string; expectedOutput: string; isHidden: boolean }>>([
    { id: 'tc-1', input: 'nums = [2, 7, 11, 15], target = 9', expectedOutput: '[0, 1]', isHidden: false },
    { id: 'tc-2', input: 'nums = [3, 2, 4], target = 6', expectedOutput: '[1, 2]', isHidden: false },
    { id: 'tc-3', input: 'nums = [3, 3], target = 6', expectedOutput: '[0, 1]', isHidden: true }
  ]);

  const handleAddTestCase = () => {
    const nextNum = customTestCases.length + 1;
    setCustomTestCases([
      ...customTestCases,
      {
        id: `tc-${Date.now()}`,
        input: `nums = [${nextNum}, ${nextNum + 1}], target = ${nextNum * 2 + 1}`,
        expectedOutput: `[0, 1]`,
        isHidden: false
      }
    ]);
  };

  const handleRemoveTestCase = (id: string) => {
    if (customTestCases.length <= 1) return;
    setCustomTestCases(customTestCases.filter(tc => tc.id !== id));
  };

  const handleUpdateTestCase = (id: string, field: 'input' | 'expectedOutput' | 'isHidden', value: any) => {
    setCustomTestCases(
      customTestCases.map(tc => (tc.id === id ? { ...tc, [field]: value } : tc))
    );
  };

  const handleToggleProb = (id: string) => {
    if (selectedProbIds.includes(id)) {
      setSelectedProbIds(selectedProbIds.filter((p) => p !== id));
    } else {
      setSelectedProbIds([...selectedProbIds, id]);
    }
  };

  const handleCreateAssignment = (e: React.FormEvent) => {
    e.preventDefault();

    if (tabType === 'custom') {
      if (!customTitle.trim()) return;

      const newProbId = `prob-cust-${Date.now()}`;
      const newCustomProblem: Problem = {
        id: newProbId,
        title: customTitle,
        slug: customTitle.toLowerCase().replace(/\s+/g, '-'),
        difficulty: customDiff,
        tags: customTags.split(',').map(t => t.trim()).filter(Boolean),
        acceptanceRate: '55.0%',
        origin: 'instructor_assigned',
        instructorName: currentUser.name || 'Prof. Sarah Miller',
        dueDate: dueDate,
        studentStatus: 'Not Started',
        description: customDesc || `Implement an optimal algorithm for ${customTitle}.\n\nEnsure your solution adheres to the required Asymptotic Time Complexity ${customTimeComplexity} and Space Complexity ${customSpaceComplexity}.`,
        examples: customTestCases.slice(0, 2).map((tc, idx) => ({
          input: tc.input,
          output: tc.expectedOutput,
          explanation: `Example verification case ${idx + 1}.`
        })),
        constraints: [
          `Time Complexity Requirement: ${customTimeComplexity}`,
          `Space Complexity Requirement: ${customSpaceComplexity}`,
          `Execution Limit: ${customTimeLimit}`,
          '1 <= n <= 10^5'
        ],
        testCases: customTestCases.map((tc, i) => ({
          id: `tc-${i + 1}`,
          input: tc.input,
          expectedOutput: tc.expectedOutput,
          isHidden: tc.isHidden
        })),
        starterCode: {
          'cpp': `class Solution {\npublic:\n    // Time Requirement: ${customTimeComplexity}\n    // Space Requirement: ${customSpaceComplexity}\n    vector<int> solve() {\n        // Your code here\n    }\n};`,
          'python': `class Solution:\n    # Time Requirement: ${customTimeComplexity}\n    # Space Requirement: ${customSpaceComplexity}\n    def solve(self):\n        # Your code here\n        pass`,
          'java': `class Solution {\n    // Time Requirement: ${customTimeComplexity}\n    // Space Requirement: ${customSpaceComplexity}\n    public int[] solve() {\n        // Your code here\n        return new int[]{};\n    }\n}`,
          'typescript': `function solve(): void {\n    // Time: ${customTimeComplexity}, Space: ${customSpaceComplexity}\n}`
        },
        solutionCode: {},
        optimalComplexity: {
          time: customTimeComplexity,
          space: customSpaceComplexity
        }
      };

      const newAssignment: Assignment = {
        id: `asg-${Date.now()}`,
        title: `Assignment: ${customTitle}`,
        description: customDesc || `Mandatory coursework for ${course}. Required Time Complexity: ${customTimeComplexity}.`,
        course,
        instructorName: currentUser.name || 'Prof. Sarah Miller',
        problemsCount: 1,
        problemIds: [newProbId],
        assignedProblems: [
          { problemId: newProbId, problemTitle: customTitle, difficulty: customDiff, studentStatus: 'Not Started' }
        ],
        submittedCount: 0,
        totalCount: 48,
        avgScore: 0,
        dueDate,
        postedDate: 'Today',
        status: 'Active',
        studentStatus: 'Not Started'
      };

      addAssignment(newAssignment, newCustomProblem);
    } else {
      if (!title.trim()) return;

      const newAssignment: Assignment = {
        id: `asg-${Date.now()}`,
        title,
        description: description || 'Algorithmic problem set with sandbox complexity limits.',
        course,
        instructorName: currentUser.name || 'Prof. Sarah Miller',
        problemsCount: selectedProbIds.length,
        problemIds: selectedProbIds,
        submittedCount: 0,
        totalCount: 48,
        avgScore: 0,
        dueDate,
        postedDate: 'Today',
        status: 'Active',
        studentStatus: 'Not Started'
      };

      addAssignment(newAssignment);
    }

    setIsModalOpen(false);
    setTitle('');
    setDescription('');
    setCustomTitle('');
    setCustomDesc('');
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 mb-1">
            <GraduationCap className="w-4 h-4" />
            <span>CSE-301 Section A • 48 Students Enrolled</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Assignments & Coding Questions Dispatcher
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Create and post custom coding questions with explicit test cases, runtime constraints, and Big-O time complexity requirements to your student cohort.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-5 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all active:scale-95 cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>+ Post Custom Question</span>
        </button>
      </div>

      {/* Assignment Cards */}
      <div className="space-y-4">
        {assignments.map((asg) => (
          <div
            key={asg.id}
            className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs hover:border-emerald-300 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
          >
            <div className="flex items-start gap-4">
              <div className="p-3.5 bg-emerald-50 text-emerald-600 rounded-2xl flex-shrink-0">
                <FileCode2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h3 className="text-base font-extrabold text-slate-900">{asg.title}</h3>
                  <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-800">
                    {asg.status}
                  </span>
                  <span className="text-xs font-mono text-slate-500 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    Due: {asg.dueDate}
                  </span>
                </div>
                <p className="text-xs text-slate-500 max-w-xl">{asg.description}</p>
                <div className="flex items-center gap-4 text-xs text-slate-500 pt-2 font-mono">
                  <span>Course: <strong className="text-slate-700 font-sans">{asg.course}</strong></span>
                  <span>Problems: <strong className="text-slate-700">{asg.problemsCount}</strong></span>
                </div>
              </div>
            </div>

            {/* Submission Rate & Average */}
            <div className="flex items-center gap-6 w-full md:w-auto justify-between md:justify-end border-t md:border-t-0 pt-4 md:pt-0 border-slate-100">
              <div className="text-right">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Cohort Submissions</span>
                <span className="text-sm font-extrabold text-slate-900 font-mono">
                  {asg.submittedCount} / {asg.totalCount}
                </span>
              </div>

              <div className="text-right">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Class Average</span>
                <span className="text-sm font-extrabold text-emerald-600 font-mono">
                  {asg.avgScore ? `${asg.avgScore}%` : 'Pending'}
                </span>
              </div>

              <button
                onClick={() => setCurrentView('instructor-submissions')}
                className="px-4 py-2.5 bg-slate-900 hover:bg-emerald-600 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
              >
                Review Submissions
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Post Question / Create Assignment Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Post Custom Coding Question to Students"
        subtitle="Specify required time complexity, sandbox limits, and test cases for AI auto-evaluation"
        maxWidth="2xl"
      >
        {/* Toggle between custom creation vs picking existing */}
        <div className="flex border-b border-slate-200 mb-5 text-xs font-bold">
          <button
            type="button"
            onClick={() => setTabType('custom')}
            className={`py-2.5 px-4 border-b-2 transition-all cursor-pointer ${
              tabType === 'custom'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-400 hover:text-slate-700'
            }`}
          >
            + Post Custom Coding Question (Explicit Test Cases & Big-O)
          </button>
          <button
            type="button"
            onClick={() => setTabType('existing')}
            className={`py-2.5 px-4 border-b-2 transition-all cursor-pointer ${
              tabType === 'existing'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-400 hover:text-slate-700'
            }`}
          >
            Assign from Problem Bank
          </button>
        </div>

        <form onSubmit={handleCreateAssignment} className="space-y-4 text-xs">
          {tabType === 'custom' ? (
            <>
              {/* Question Title & Difficulty */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <label className="block font-bold text-slate-700 mb-1">Question Title *</label>
                  <input
                    type="text"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    required
                    placeholder="e.g. Longest Palindromic Substring"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Difficulty</label>
                  <select
                    value={customDiff}
                    onChange={(e) => setCustomDiff(e.target.value as Difficulty)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-semibold"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
              </div>

              {/* Explicit Time Complexity & Space Complexity Requirements */}
              <div className="p-4 bg-emerald-50/60 rounded-2xl border border-emerald-200/80 space-y-3">
                <div className="flex items-center gap-2 text-emerald-900 font-bold">
                  <Cpu className="w-4 h-4 text-emerald-600" />
                  <span>Explicit Complexity Constraints for AI Evaluator</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block font-bold text-emerald-900 mb-1">
                      Required Time Complexity *
                    </label>
                    <select
                      value={customTimeComplexity}
                      onChange={(e) => setCustomTimeComplexity(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-emerald-300 rounded-xl font-mono font-bold text-emerald-800 focus:outline-none focus:border-emerald-600 cursor-pointer"
                    >
                      <option value="O(1)">O(1) - Constant</option>
                      <option value="O(log N)">O(log N) - Logarithmic</option>
                      <option value="O(N)">O(N) - Linear</option>
                      <option value="O(N log N)">O(N log N) - Linearithmic</option>
                      <option value="O(N^2)">O(N^2) - Quadratic</option>
                      <option value="O(2^N)">O(2^N) - Exponential</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-bold text-emerald-900 mb-1">
                      Required Space Complexity *
                    </label>
                    <select
                      value={customSpaceComplexity}
                      onChange={(e) => setCustomSpaceComplexity(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-emerald-300 rounded-xl font-mono font-bold text-emerald-800 focus:outline-none focus:border-emerald-600 cursor-pointer"
                    >
                      <option value="O(1)">O(1) Auxiliary Space</option>
                      <option value="O(N)">O(N) Linear Memory</option>
                      <option value="O(N^2)">O(N^2) Matrix Space</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-bold text-emerald-900 mb-1">
                      Execution Timeout Limit
                    </label>
                    <input
                      type="text"
                      value={customTimeLimit}
                      onChange={(e) => setCustomTimeLimit(e.target.value)}
                      placeholder="e.g. 1.5 seconds"
                      className="w-full px-3 py-2 bg-white border border-emerald-300 rounded-xl font-mono text-emerald-800 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Problem Description & Constraints */}
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Problem Description & Algorithmic Specification *
                </label>
                <textarea
                  value={customDesc}
                  onChange={(e) => setCustomDesc(e.target.value)}
                  rows={2}
                  placeholder="Enter detailed problem statement, input formats, edge cases, and algorithmic bounds..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-sans"
                />
              </div>

              {/* Explicit Test Cases Builder */}
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-indigo-600" />
                    <span className="font-extrabold text-slate-900">
                      Explicit Test Cases Suite ({customTestCases.length})
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={handleAddTestCase}
                    className="px-3 py-1 bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-300 rounded-xl font-bold transition-all flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>+ Add Test Case</span>
                  </button>
                </div>

                <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
                  {customTestCases.map((tc, index) => (
                    <div
                      key={tc.id}
                      className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-xs space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-extrabold text-slate-800">
                            Test Case #{index + 1}
                          </span>
                          <label className="inline-flex items-center gap-1.5 text-[11px] text-slate-600 cursor-pointer ml-2">
                            <input
                              type="checkbox"
                              checked={tc.isHidden}
                              onChange={(e) => handleUpdateTestCase(tc.id, 'isHidden', e.target.checked)}
                              className="rounded text-indigo-600 focus:ring-0"
                            />
                            <span>Hidden Evaluation Test</span>
                          </label>
                        </div>

                        {customTestCases.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveTestCase(tc.id)}
                            className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                            title="Remove Test Case"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-[11px]">
                        <div>
                          <label className="block text-slate-400 font-sans text-[10px] mb-0.5 font-bold">
                            Input Arguments:
                          </label>
                          <input
                            type="text"
                            value={tc.input}
                            onChange={(e) => handleUpdateTestCase(tc.id, 'input', e.target.value)}
                            required
                            placeholder="e.g. nums = [1, 2, 3], target = 4"
                            className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 font-mono text-slate-800"
                          />
                        </div>

                        <div>
                          <label className="block text-slate-400 font-sans text-[10px] mb-0.5 font-bold">
                            Expected Return Output:
                          </label>
                          <input
                            type="text"
                            value={tc.expectedOutput}
                            onChange={(e) => handleUpdateTestCase(tc.id, 'expectedOutput', e.target.value)}
                            required
                            placeholder="e.g. [0, 2]"
                            className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 font-mono text-slate-800"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            /* Pick from Existing Problem Bank */
            <>
              <div>
                <label className="block font-bold text-slate-700 mb-1">Assignment Title *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  placeholder="e.g. Dynamic Programming & Memoization Lab"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Instructions / Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Provide context and complexity constraints for students..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-sans"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-2">Select Problems from Bank to Assign:</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto p-2 bg-slate-50 rounded-xl border border-slate-200">
                  {problems.map((prob) => {
                    const selected = selectedProbIds.includes(prob.id);
                    return (
                      <div
                        key={prob.id}
                        onClick={() => handleToggleProb(prob.id)}
                        className={`p-2.5 rounded-lg border cursor-pointer flex items-center justify-between text-xs transition-colors ${
                          selected ? 'bg-emerald-50 border-emerald-300 text-emerald-900 font-bold' : 'bg-white border-slate-200 text-slate-700'
                        }`}
                      >
                        <span>{prob.title}</span>
                        <span className="text-[10px] text-slate-400">{prob.difficulty}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {/* Target Cohort & Due Date */}
          <div className="grid grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Target Course Cohort</label>
              <select
                value={course}
                onChange={(e) => setCourse(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
              >
                <option>CSE-301 Data Structures (48 Students)</option>
                <option>CSE-402 Advanced Algorithms</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Due Date</label>
              <input
                type="text"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Publish Question & Dispatch to 48 Students</span>
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
