import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Flame,
  Award,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  Sparkles,
  Zap,
  ChevronRight,
  Clock,
  Target,
  BookOpen,
  FileText,
  BellRing,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/Badge';

export const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentUser,
    studentProgress,
    submissions,
    problems,
    activeAssessment,
    announcements,
    dismissAnnouncement,
    openProblemWorkspace,
    openAssessmentResult
  } = useApp();

  const assignedProblems = problems.filter((problem) => problem.isInstructorAssigned);
  const activeProblem = assignedProblems[0] || problems[0] || null;
  const latestSubmission = submissions[0];

  const hasWeakTopics = Array.isArray(studentProgress?.weakTopics) && studentProgress.weakTopics.length > 0;
  const weakTopic = hasWeakTopics
    ? studentProgress.weakTopics[0]
    : (activeProblem?.tags?.[0] || 'Arrays & Strings');

  const totalProblems = studentProgress?.totalProblems > 0 ? studentProgress.totalProblems : problems.length;
  const problemsSolved = studentProgress?.problemsSolved ?? 0;
  const solvedPercent = totalProblems > 0 ? Math.min(100, Math.round((problemsSolved / totalProblems) * 100)) : 0;

  const hasOverallScore = studentProgress?.overallScore != null && Number.isFinite(Number(studentProgress.overallScore));
  const overallScore = hasOverallScore ? Number(studentProgress.overallScore).toFixed(1) : null;
  const currentStreak = studentProgress?.currentStreak ?? 0;

  const projection = activeAssessment?.scoreProjection || null;
  const latestAnnouncement = announcements.find((item) => !item.read);

  const displayName = currentUser?.name?.trim() || 'Student';

  const handleResumeChallenge = (probId?: string) => {
    const targetId = probId || activeProblem?.id;
    if (targetId) {
      openProblemWorkspace(targetId);
      navigate(`/problems/${encodeURIComponent(targetId)}`);
    } else {
      navigate('/problems');
    }
  };

  const handleInspectReport = (subId?: string) => {
    const targetId = subId || latestSubmission?.id;
    if (targetId) {
      openAssessmentResult(targetId);
      navigate(`/submissions/${encodeURIComponent(targetId)}`);
    } else {
      navigate('/submissions');
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Banner (Clean Greeting & Primary CTAs) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 rounded-3xl text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-indigo-500/10 to-transparent pointer-events-none" />
        
        <div className="relative z-10">
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Hello, {displayName}! 👋
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-indigo-100/90 leading-relaxed">
            Your next best move is selected from deadlines, weak-topic feedback, and your latest submission evaluations.
          </p>
        </div>

        <div className="flex items-center gap-3 relative z-10">
          {activeProblem ? (
            <button
              onClick={() => handleResumeChallenge(activeProblem.id)}
              className="px-5 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
            >
              <Zap className="w-4 h-4 text-amber-300" />
              <span>
                {submissions.some((s) => s.problemId === activeProblem.id) ? 'Resume' : 'Start'} "{activeProblem.title}"
              </span>
            </button>
          ) : (
            <button
              onClick={() => navigate('/problems')}
              className="px-5 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
            >
              <Zap className="w-4 h-4 text-amber-300" />
              <span>Browse Problem Bank</span>
            </button>
          )}
        </div>
      </div>

      {/* Announcement Notification Banner */}
      {latestAnnouncement && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500 text-white shadow-sm">
              <BellRing className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-sm font-extrabold text-amber-950">{latestAnnouncement.title}</h2>
                {latestAnnouncement.courseCode && (
                  <span className="px-2 py-0.5 rounded-md bg-white border border-amber-200 text-[10px] font-bold text-amber-800">
                    {latestAnnouncement.courseCode}
                  </span>
                )}
                {latestAnnouncement.dueDate && (
                  <span className="px-2 py-0.5 rounded-md bg-amber-100 border border-amber-200 text-[10px] font-bold text-amber-800">
                    Due {latestAnnouncement.dueDate}
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-amber-800 leading-relaxed">
                {latestAnnouncement.message} It is now available in your Instructor Assigned queue.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 md:self-center">
            {latestAnnouncement.problemId && (
              <button
                onClick={() => handleResumeChallenge(latestAnnouncement.problemId)}
                className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold flex items-center gap-2 transition-colors cursor-pointer"
              >
                <span>Solve Now</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={() => dismissAnnouncement(latestAnnouncement.id)}
              className="p-2 text-amber-700 hover:bg-amber-100 rounded-lg transition-colors cursor-pointer"
              title="Dismiss announcement"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Personalized Learning Path: 1. CONTINUE / 2. REVISE / 3. PRACTICE */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <button
          onClick={() => handleResumeChallenge(activeProblem?.id)}
          className="text-left bg-white rounded-2xl border border-indigo-200/80 p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-indigo-700 uppercase">1. Continue</span>
            <Zap className="w-4 h-4 text-indigo-500" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900 truncate">
            {activeProblem ? activeProblem.title : 'Explore Problem Bank'}
          </h3>
          <p className="mt-1 text-xs text-slate-500 leading-relaxed line-clamp-2">
            {activeProblem
              ? `Target ${activeProblem.optimalComplexity?.time && activeProblem.optimalComplexity.time !== '—' ? activeProblem.optimalComplexity.time : 'optimal'} time and ${activeProblem.optimalComplexity?.space && activeProblem.optimalComplexity.space !== '—' ? activeProblem.optimalComplexity.space : 'optimal'} space.`
              : 'Choose a problem from the algorithmic repository to start your session.'}
          </p>
        </button>

        <button
          onClick={() => latestSubmission ? handleInspectReport(latestSubmission.id) : navigate('/problems')}
          className="text-left bg-white rounded-2xl border border-emerald-200/80 p-5 shadow-xs hover:border-emerald-400 hover:shadow-md transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-emerald-700 uppercase">2. Revise</span>
            <FileText className="w-4 h-4 text-emerald-500" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900 truncate">
            {latestSubmission ? latestSubmission.problemTitle : 'No Submissions Yet'}
          </h3>
          <p className="mt-1 text-xs text-slate-500 leading-relaxed line-clamp-2">
            {latestSubmission
              ? `Review your recent score (${latestSubmission.score}/100) and inspect AI revision feedback.`
              : 'Submit your first challenge to unlock AI rubric feedback and score boost recommendations.'}
          </p>
        </button>

        <button
          onClick={() => navigate(hasWeakTopics ? '/feedback' : '/problems')}
          className="text-left bg-white rounded-2xl border border-amber-200/80 p-5 shadow-xs hover:border-amber-400 hover:shadow-md transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-amber-700 uppercase">3. Practice</span>
            <BookOpen className="w-4 h-4 text-amber-500" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900 truncate">
            {hasWeakTopics ? weakTopic : 'Core Algorithms'}
          </h3>
          <p className="mt-1 text-xs text-slate-500 leading-relaxed line-clamp-2">
            {hasWeakTopics
              ? 'Practice is routed from weak-topic detection to close real rubric gaps.'
              : 'Build problem-solving foundations across Arrays, Strings, and core patterns.'}
          </p>
        </button>
      </div>

      {/* Top 4 Key Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Score */}
        <div
          onClick={() => navigate('/analytics')}
          className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:border-indigo-300 card-hover cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Overall Score</span>
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
              {hasOverallScore ? overallScore : '—'}
            </span>
            {hasOverallScore && <span className="text-xs text-slate-400 font-mono">/ 100</span>}
          </div>
          {hasOverallScore ? (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-600 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>
                {Number(overallScore) >= 80 ? 'Excellent' : Number(overallScore) >= 70 ? 'Good' : Number(overallScore) >= 60 ? 'Passing' : 'Needs Practice'}
              </span>
            </div>
          ) : (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
              <span>Not assessed yet</span>
            </div>
          )}
        </div>

        {/* Problems Solved */}
        <div
          onClick={() => navigate('/problems')}
          className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:border-indigo-300 card-hover cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Problems Solved</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
              {problemsSolved}
            </span>
            <span className="text-xs text-slate-400 font-mono">/ {totalProblems}</span>
          </div>
          <div className="mt-2 text-xs text-slate-500 flex items-center justify-between">
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden mr-2">
              <div
                className="bg-emerald-500 h-full rounded-full transition-all"
                style={{ width: `${solvedPercent}%` }}
              />
            </div>
            <span className="font-mono text-[11px] font-semibold text-slate-600">{solvedPercent}%</span>
          </div>
        </div>

        {/* Current Streak */}
        <div
          onClick={() => navigate('/analytics')}
          className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:border-indigo-300 card-hover cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Current Streak</span>
            <div className="p-2 bg-amber-50 text-amber-600 rounded-xl">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
              {currentStreak}
            </span>
            <span className="text-xs text-slate-500 font-semibold">Days</span>
          </div>
          {currentStreak > 0 ? (
            <div className="mt-2 text-xs text-amber-600 font-semibold flex items-center gap-1">
              <Flame className="w-3.5 h-3.5 fill-amber-500" />
              <span>Active learning streak 🔥</span>
            </div>
          ) : (
            <div className="mt-2 text-xs text-slate-400 font-medium flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              <span>Start your streak today</span>
            </div>
          )}
        </div>

        {/* Rank */}
        <div
          onClick={() => navigate('/analytics')}
          className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs hover:border-indigo-300 card-hover cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-500">Cohort Rank</span>
            <div className="p-2 bg-purple-50 text-purple-600 rounded-xl">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
              {studentProgress?.rankPercentile && studentProgress.rankPercentile !== 'N/A'
                ? studentProgress.rankPercentile
                : '—'}
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400 font-medium truncate">
            {studentProgress?.rankPercentile && studentProgress.rankPercentile !== 'N/A'
              ? 'Cohort percentile'
              : problemsSolved > 0
                ? 'Ranking updating soon'
                : 'Solve problems to rank'}
          </div>
        </div>
      </div>

      {/* AI Projected Score Action Card / First-Challenge Action Card */}
      {latestSubmission && projection && projection.improvementDelta > 0 ? (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-purple-900/10 via-indigo-900/10 to-transparent border border-purple-200/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xs">
          <div className="flex items-start gap-3.5">
            <div className="p-3 bg-purple-600 text-white rounded-2xl shadow-md shadow-purple-600/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900">
                  Projected Score After Revision Available
                </h3>
                <span className="px-2.5 py-0.5 text-[10px] font-extrabold uppercase bg-purple-100 text-purple-800 rounded-full">
                  +{projection.improvementDelta} pts Gain
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Applying AI recommendations on <strong className="text-slate-800">{activeAssessment?.problemTitle || latestSubmission.problemTitle}</strong> can boost your score from <span className="font-mono font-bold text-slate-800">{projection.currentScore}</span> to <span className="font-mono font-bold text-emerald-600">{projection.projectedScore}/100</span>.
              </p>
            </div>
          </div>

          <button
            onClick={() => handleInspectReport(latestSubmission.id)}
            className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-2xl shadow-md shadow-purple-600/20 transition-all flex items-center gap-2 flex-shrink-0 cursor-pointer active:scale-95"
          >
            <span>View Detailed Feedback</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-900/10 via-purple-900/10 to-transparent border border-indigo-200/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xs">
          <div className="flex items-start gap-3.5">
            <div className="p-3 bg-indigo-600 text-white rounded-2xl shadow-md shadow-indigo-600/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900">
                  Interactive AI Code Evaluation Ready
                </h3>
                <span className="px-2.5 py-0.5 text-[10px] font-extrabold uppercase bg-indigo-100 text-indigo-800 rounded-full">
                  Sandbox Active
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Solve challenges in our sandbox to receive instant multi-agent grading on correctness, time/space complexity, and code quality.
              </p>
            </div>
          </div>

          <button
            onClick={() => handleResumeChallenge(activeProblem?.id)}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-2xl shadow-md shadow-indigo-600/20 transition-all flex items-center gap-2 flex-shrink-0 cursor-pointer active:scale-95"
          >
            <span>Start Practice</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Middle Grid: Recent Submissions & Side Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Submissions Table */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900">Recent Submissions</h2>
              <p className="text-xs text-slate-400 mt-0.5">Your latest evaluations & AI assessments</p>
            </div>
            <button
              onClick={() => navigate('/submissions')}
              className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400 border-b border-slate-100 font-medium">
                  <th className="pb-3.5 font-semibold">Problem</th>
                  <th className="pb-3.5 font-semibold">Score</th>
                  <th className="pb-3.5 font-semibold">Status</th>
                  <th className="pb-3.5 font-semibold">Date & Time</th>
                  <th className="pb-3.5 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      No submissions recorded yet. Start solving problems to see your history!
                    </td>
                  </tr>
                ) : (
                  submissions.slice(0, 5).map((sub) => (
                    <tr 
                      key={sub.id} 
                      onClick={() => handleInspectReport(sub.id)}
                      className="hover:bg-slate-50/70 transition-colors group cursor-pointer"
                    >
                      <td className="py-4 font-bold text-slate-800">
                        <div className="flex items-center gap-2">
                          <span>{sub.problemTitle}</span>
                          <span className="text-[10px] text-slate-400 font-mono">({sub.language})</span>
                        </div>
                      </td>
                      <td className="py-4 font-mono font-bold">
                        <span className={sub.score == null ? 'text-slate-500' : sub.score >= 80 ? 'text-emerald-600' : sub.score >= 60 ? 'text-indigo-600' : 'text-rose-600'}>
                          {sub.score == null ? 'Pending' : `${sub.score} / 100`}
                        </span>
                      </td>
                      <td className="py-4">
                        <StatusBadge status={sub.status} />
                      </td>
                      <td className="py-4 text-slate-500 font-mono text-[11px]">
                        {sub.date}
                      </td>
                      <td className="py-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => handleInspectReport(sub.id)}
                          className="px-3 py-1.5 text-xs font-bold text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors cursor-pointer"
                        >
                          Inspect AI Report
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right 1 Col: Weak Topics & Learning Summary */}
        <div className="space-y-6">
          {/* Weak Topics */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Weak Topics</h3>
              <Target className="w-4 h-4 text-amber-500" />
            </div>
            {hasWeakTopics ? (
              <>
                <p className="text-xs text-slate-500 leading-relaxed">
                  AI identified lower test pass rates on these algorithmic patterns:
                </p>
                <div className="flex flex-wrap gap-2">
                  {studentProgress.weakTopics.map((topic, i) => (
                    <button
                      key={i}
                      onClick={() => navigate('/problems')}
                      className="px-3 py-1 text-xs font-semibold rounded-xl bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200/80 transition-colors cursor-pointer"
                    >
                      {topic}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => navigate('/feedback')}
                  className="w-full py-2.5 text-xs font-bold text-indigo-600 bg-indigo-50/60 hover:bg-indigo-100 rounded-2xl transition-all text-center block cursor-pointer"
                >
                  View Targeted AI Practice →
                </button>
              </>
            ) : (
              <>
                <p className="text-xs text-slate-500 leading-relaxed">
                  No weak areas detected yet. As you submit code, AI analyzes test pass rates and complexity gaps to highlight topics for improvement.
                </p>
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/60 text-xs text-slate-600 space-y-1">
                  <div className="font-semibold text-slate-800">💡 Next step:</div>
                  <div>Solve practice problems to establish your personalized skill profile.</div>
                </div>
                <button
                  onClick={() => navigate('/problems')}
                  className="w-full py-2.5 text-xs font-bold text-indigo-600 bg-indigo-50/60 hover:bg-indigo-100 rounded-2xl transition-all text-center block cursor-pointer"
                >
                  Browse Practice Problems →
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Course Assignments or Featured Practice Problems */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-7 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              {assignedProblems.length > 0 ? 'Active Course Assignments' : 'Featured Practice Challenges'}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {assignedProblems.length > 0
                ? 'Assigned coursework with automated AI grading'
                : 'Curated problem challenges from the algorithmic practice bank'}
            </p>
          </div>
          <button
            onClick={() => navigate('/problems')}
            className="text-xs font-bold text-indigo-600 hover:underline cursor-pointer"
          >
            See All Problems ({problems.length})
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(assignedProblems.length > 0 ? assignedProblems : problems).slice(0, 3).map((prob) => (
            <div
              key={prob.id}
              onClick={() => handleResumeChallenge(prob.id)}
              className="p-5 rounded-2xl border border-slate-200 hover:border-indigo-400 hover:shadow-md card-hover transition-all cursor-pointer bg-slate-50/50 hover:bg-white flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  {assignedProblems.length > 0 && prob.courseCode ? (
                    <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-lg">
                      {prob.courseCode}
                    </span>
                  ) : (
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg ${
                      prob.difficulty === 'Easy' ? 'text-emerald-700 bg-emerald-50 border border-emerald-200' :
                      prob.difficulty === 'Hard' ? 'text-rose-700 bg-rose-50 border border-rose-200' :
                      'text-amber-700 bg-amber-50 border border-amber-200'
                    }`}>
                      {prob.difficulty}
                    </span>
                  )}
                  {assignedProblems.length > 0 && prob.dueDate ? (
                    <span className="text-[11px] text-slate-400 font-mono">
                      Due: {prob.dueDate}
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-400 font-mono">
                      {prob.tags?.[0] || 'Algorithms'}
                    </span>
                  )}
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  {prob.title}
                </h4>
                <div className="flex flex-wrap gap-1 mt-2">
                  {(prob.tags || []).slice(0, 2).map((tag, tIdx) => (
                    <span key={tIdx} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="mt-3 flex items-center gap-2 text-[11px] font-mono text-slate-500">
                  <Clock className="w-3 h-3" />
                  <span>Opt: {prob.optimalComplexity?.time && prob.optimalComplexity.time !== '—' ? prob.optimalComplexity.time : 'O(N)'} / {prob.optimalComplexity?.space && prob.optimalComplexity.space !== '—' ? prob.optimalComplexity.space : 'O(1)'}</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600">
                <span>Code in Sandbox</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
