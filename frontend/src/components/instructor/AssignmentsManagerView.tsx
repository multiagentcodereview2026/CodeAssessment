import React, { useState } from 'react';
import {
  CalendarCheck,
  Plus,
  Calendar,
  BookOpen,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
  FileCode2,
  Trash2,
  GraduationCap,
  Layers,
  Send
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { Assignment, Problem, Difficulty } from '../../types';
import { Modal } from '../common/Modal';

export const AssignmentsManagerView: React.FC = () => {
  const { assignments, addAssignment, problems, currentUser } = useApp();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [tabType, setTabType] = useState<'existing' | 'custom'>('existing');

  // Existing selection form
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [course, setCourse] = useState('CSE-301 Data Structures');
  const [dueDate, setDueDate] = useState('15 June, 2026');
  const [selectedProbIds, setSelectedProbIds] = useState<string[]>(['prob-1', 'prob-2']);

  // Custom question form
  const [customTitle, setCustomTitle] = useState('');
  const [customDesc, setCustomDesc] = useState('');
  const [customDiff, setCustomDiff] = useState<Difficulty>('Medium');
  const [customTags, setCustomTags] = useState('Dynamic Programming, Arrays');

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
        tags: customTags.split(',').map(t => t.trim()),
        acceptanceRate: '50.0%',
        origin: 'instructor_assigned',
        instructorName: currentUser.name || 'Prof. Sarah Miller',
        dueDate: dueDate,
        studentStatus: 'Not Started',
        description: customDesc || `Implement an efficient algorithm for ${customTitle}. Ensure optimal time and space complexity.`,
        examples: [
          { input: 'nums = [1, 2, 3]', output: '[6]', explanation: 'Computed output based on constraints.' }
        ],
        constraints: ['1 <= nums.length <= 10^5', 'Time Limit: 2.0 seconds'],
        testCases: [
          { id: 'tc-c1', input: 'nums = [1, 2, 3]', expectedOutput: '[6]' }
        ],
        starterCode: {
          'cpp': `class Solution {\npublic:\n    // Implement your solution here\n};`,
          'python': `class Solution:\n    # Implement your solution here\n    pass`,
          'java': `class Solution {\n    // Implement your solution here\n}`,
          'typescript': `function solve(): void {\n    // Implement solution\n}`
        },
        solutionCode: {},
        optimalComplexity: { time: 'O(N)', space: 'O(1)' }
      };

      const newAssignment: Assignment = {
        id: `asg-${Date.now()}`,
        title: title.trim() || `Course Challenge: ${customTitle}`,
        description: description || `Instructor assigned coding challenge for ${course}.`,
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
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Assignments & Challenge Dispatcher
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Post mandatory coding questions to students or schedule graded problem sets for your cohort.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all active:scale-95 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>+ Post Question / Assignment</span>
        </button>
      </div>

      {/* Assignment Cards */}
      <div className="space-y-4">
        {assignments.map((asg) => (
          <div
            key={asg.id}
            className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs hover:border-emerald-300 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl flex-shrink-0">
                <FileCode2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h3 className="text-base font-bold text-slate-900">{asg.title}</h3>
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-800">
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
                <span className="text-[11px] text-slate-400 uppercase font-semibold block">Submissions</span>
                <span className="text-sm font-extrabold text-slate-900 font-mono">
                  {asg.submittedCount} / {asg.totalCount}
                </span>
              </div>

              <div className="text-right">
                <span className="text-[11px] text-slate-400 uppercase font-semibold block">Average Score</span>
                <span className="text-sm font-extrabold text-emerald-600 font-mono">
                  {asg.avgScore ? `${asg.avgScore}%` : 'Pending'}
                </span>
              </div>

              <button className="px-3.5 py-2 bg-slate-900 hover:bg-emerald-600 text-white rounded-xl text-xs font-bold transition-colors">
                Gradebook
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Post Question / Create Assignment Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Post Assignment to Students"
        subtitle="Questions posted here will immediately appear as mandatory coursework on student dashboards"
        maxWidth="xl"
      >
        {/* Toggle between picking existing vs creating a new question */}
        <div className="flex border-b border-slate-200 mb-4 text-xs font-bold">
          <button
            type="button"
            onClick={() => setTabType('existing')}
            className={`py-2 px-4 border-b-2 transition-all ${
              tabType === 'existing'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-400 hover:text-slate-700'
            }`}
          >
            Assign from Problem Bank
          </button>
          <button
            type="button"
            onClick={() => setTabType('custom')}
            className={`py-2 px-4 border-b-2 transition-all ${
              tabType === 'custom'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-400 hover:text-slate-700'
            }`}
          >
            + Post Custom Coding Question
          </button>
        </div>

        <form onSubmit={handleCreateAssignment} className="space-y-4 text-xs">
          {tabType === 'existing' ? (
            <>
              <div>
                <label className="block font-bold text-slate-700 mb-1">Assignment Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  placeholder="e.g. Dynamic Programming & Memoization Lab"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Instructions / Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Provide context and complexity constraints for students..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-sans"
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
          ) : (
            <>
              <div>
                <label className="block font-bold text-slate-700 mb-1">Question Title</label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  required
                  placeholder="e.g. Longest Substring Without Repeating Characters"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Difficulty</label>
                  <select
                    value={customDiff}
                    onChange={(e) => setCustomDiff(e.target.value as Difficulty)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Topic Tags (comma-separated)</label>
                  <input
                    type="text"
                    value={customTags}
                    onChange={(e) => setCustomTags(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Problem Description & Constraints</label>
                <textarea
                  value={customDesc}
                  onChange={(e) => setCustomDesc(e.target.value)}
                  rows={3}
                  placeholder="Enter problem statement, examples, and algorithmic constraints..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-sans"
                />
              </div>
            </>
          )}

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Target Course Cohort</label>
              <select
                value={course}
                onChange={(e) => setCourse(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
              >
                <option>CSE-301 Data Structures</option>
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
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Publish & Notify Students</span>
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
