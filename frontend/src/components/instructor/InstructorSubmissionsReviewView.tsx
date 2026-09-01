import React, { useState } from 'react';
import {
  FileCheck2,
  Search,
  Filter,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Clock,
  Eye,
  MessageSquare,
  Send,
  GraduationCap,
  ShieldCheck,
  Check
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { SubmissionItem } from '../../types';
import { Modal } from '../common/Modal';
import { StatusBadge } from '../common/Badge';

export const InstructorSubmissionsReviewView: React.FC = () => {
  const { submissions, assignments, studentRoster, goBackToDashboard } = useApp();
  const [search, setSearch] = useState('');
  const [selectedAssignmentFilter, setSelectedAssignmentFilter] = useState('all');
  const [selectedSubmission, setSelectedSubmission] = useState<SubmissionItem | null>(null);
  const [instructorComment, setInstructorComment] = useState('');
  const [feedbackSent, setFeedbackSent] = useState(false);

  // Filter only assigned submissions for instructor review
  const filteredSubmissions = submissions.filter((sub) => {
    const matchSearch = sub.problemTitle.toLowerCase().includes(search.toLowerCase()) || sub.id.toLowerCase().includes(search.toLowerCase());
    const matchAssignment = selectedAssignmentFilter === 'all' || sub.assignmentId === selectedAssignmentFilter;
    return matchSearch && matchAssignment;
  });

  const handleSendFeedback = (e: React.FormEvent) => {
    e.preventDefault();
    if (!instructorComment.trim()) return;
    setFeedbackSent(true);
    setTimeout(() => {
      setFeedbackSent(false);
      setSelectedSubmission(null);
      setInstructorComment('');
    }, 1200);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Breadcrumb Navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={goBackToDashboard}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-emerald-700 transition-colors p-2 hover:bg-slate-100 rounded-xl cursor-pointer"
        >
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>Back to Instructor Dashboard</span>
        </button>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Student Submissions & AI Feedback Review
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Inspect incoming student code, AI assessment diagnostics, and attach instructor feedback.
          </p>
        </div>

        <span className="text-xs font-semibold text-slate-700 bg-white border border-slate-200 px-3.5 py-1.5 rounded-xl shadow-xs">
          Total Submissions Evaluated: <strong className="text-indigo-600 font-mono">152</strong>
        </span>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by problem or submission ID..."
            className="w-full pl-10 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500 font-medium"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <span className="text-xs font-semibold text-slate-500">Filter Assignment:</span>
          <select
            value={selectedAssignmentFilter}
            onChange={(e) => setSelectedAssignmentFilter(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Assignments</option>
            {assignments.map((asg) => (
              <option key={asg.id} value={asg.id}>
                {asg.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Submissions Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3.5 px-6">Submission ID</th>
                <th className="py-3.5 px-6">Assigned Question</th>
                <th className="py-3.5 px-6">Score</th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6">AI Assessment Summary</th>
                <th className="py-3.5 px-6">Date</th>
                <th className="py-3.5 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredSubmissions.map((sub) => (
                <tr
                  key={sub.id}
                  onClick={() => setSelectedSubmission(sub)}
                  className="hover:bg-indigo-50/30 transition-colors cursor-pointer group"
                >
                  <td className="py-4 px-6 font-mono font-bold text-indigo-700">
                    {sub.id}
                  </td>

                  <td className="py-4 px-6 font-bold text-slate-800">
                    <div>
                      <span>{sub.problemTitle}</span>
                      <span className="text-[10px] text-slate-400 font-mono ml-2 font-normal">({sub.language})</span>
                    </div>
                  </td>

                  <td className="py-4 px-6 font-mono font-extrabold text-sm">
                    <span className={sub.score >= 80 ? 'text-emerald-600' : 'text-indigo-600'}>
                      {sub.score} / 100
                    </span>
                  </td>

                  <td className="py-4 px-6">
                    <StatusBadge status={sub.status} />
                  </td>

                  <td className="py-4 px-6 text-slate-600 text-[11px] max-w-xs truncate">
                    {sub.feedbackSummary || 'Optimal time complexity achieved.'}
                  </td>

                  <td className="py-4 px-6 text-slate-400 font-mono text-[11px]">
                    {sub.date}
                  </td>

                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedSubmission(sub);
                      }}
                      className="px-3 py-1.5 bg-slate-100 group-hover:bg-indigo-600 group-hover:text-white rounded-xl font-bold text-xs text-slate-700 transition-colors inline-flex items-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Review</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Submission Review & Instructor Feedback Modal */}
      {selectedSubmission && (
        <Modal
          isOpen={!!selectedSubmission}
          onClose={() => setSelectedSubmission(null)}
          title={`Reviewing Submission ${selectedSubmission.id}`}
          subtitle={`Problem: ${selectedSubmission.problemTitle} • Language: ${selectedSubmission.language}`}
          maxWidth="2xl"
        >
          <div className="space-y-5 text-xs">
            {/* Top Score Summary */}
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 font-semibold block">AI Score</span>
                <span className="text-2xl font-mono font-extrabold text-emerald-600 mt-1 block">
                  {selectedSubmission.score}/100
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 font-semibold block">Tests Passed</span>
                <span className="text-2xl font-mono font-extrabold text-slate-800 mt-1 block">
                  {selectedSubmission.passedTestCases}/{selectedSubmission.totalTestCases}
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 font-semibold block">Plagiarism Risk</span>
                <span className="text-base font-bold text-emerald-600 mt-2 block">
                  Low (8%)
                </span>
              </div>
            </div>

            {/* AI Explainable Feedback Callout */}
            <div className="p-4 bg-slate-900 text-white rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-indigo-400 font-bold">
                <Sparkles className="w-4 h-4" />
                <span>AI Automated Assessment Report</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {selectedSubmission.feedbackSummary ||
                  'The student achieved linear O(N) runtime utilizing an optimal hash map. Edge cases with negative bounds passed with zero runtime exceptions. Code structure conforms to standard readability guidelines.'}
              </p>
            </div>

            {/* Instructor Manual Feedback Form */}
            <form onSubmit={handleSendFeedback} className="space-y-3 pt-2 border-t border-slate-100">
              <label className="block font-bold text-slate-800">
                Add Instructor Notes / Feedback for Student:
              </label>
              <textarea
                value={instructorComment}
                onChange={(e) => setInstructorComment(e.target.value)}
                placeholder="e.g. Well executed logic! Keep this standard for the upcoming midterm exam."
                rows={3}
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-indigo-500 font-sans"
              />

              <div className="flex items-center justify-between pt-2">
                <span className="text-[11px] text-slate-400">
                  Feedback will be visible on the student's dashboard.
                </span>

                <button
                  type="submit"
                  disabled={feedbackSent}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  {feedbackSent ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Feedback Saved!</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Save & Send Feedback</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </Modal>
      )}
    </div>
  );
};
