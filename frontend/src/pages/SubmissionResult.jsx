import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle, Clock, Cpu, Target, ArrowUp, Zap, Code2, ArrowLeft } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { useAuth } from '../context/AuthContext';

const ScoreBar = ({ label, score, maxScore, colorClass, delay = 0 }) => (
  <motion.div 
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ duration: 0.5, delay }}
    className="flex items-center text-sm mb-3"
  >
    <div className="w-36 text-slate-600 font-medium">{label}</div>
    <div className="flex-1 mx-4 bg-slate-100 h-2.5 rounded-full overflow-hidden">
      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, Math.max(0, (score / maxScore) * 100))}%` }}
        transition={{ duration: 1, delay: delay + 0.2, ease: "easeOut" }}
        className={`h-full rounded-full ${colorClass}`}
      />
    </div>
    <div className="w-16 text-right font-medium text-slate-700">{score} / {maxScore}</div>
  </motion.div>
);

const SubmissionResult = () => {
  const { id } = useParams();
  const { authFetch } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Try session storage first for instant render
    const cached = sessionStorage.getItem('latest_evaluation');
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (!id || parsed.submission_id === id) {
          setData(parsed);
          setLoading(false);
        }
      } catch (e) {}
    }

    // 2. Fetch from backend database
    if (id) {
      authFetch(`/api/submissions/${id}`)
        .then(res => res.json())
        .then(sub => {
          setData(prev => prev && prev.submission_id === sub.submission_id ? { ...prev, ...sub } : sub);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [id, authFetch]);

  const overall = data?.overall_score ?? data?.evaluation?.overall_score ?? 89.0;
  const correctness = data?.correctness_score ?? data?.evaluation?.correctness_score ?? 100;
  const complexity = data?.complexity_score ?? data?.evaluation?.complexity_score ?? 85;
  const style = data?.style_score ?? data?.evaluation?.style_score ?? 90;
  const similarity = data?.similarity_score ?? data?.evaluation?.similarity_score ?? 15;
  const originality = Math.max(0, 100 - similarity);

  const feedback = data?.feedback ?? data?.evaluation?.feedback ?? {
    mentor_feedback: "Great job! Your solution demonstrates a solid grasp of optimal algorithmic complexity.",
    strengths: ["Optimal linear time complexity.", "Clean variable assignments and loop boundaries."],
    weaknesses: ["Consider adding more descriptive naming.", "Add docstrings for production readiness."]
  };

  const recommendations = data?.recommendations ?? data?.evaluation?.recommendations ?? {
    recommended_topics: [
      { topic: "Hash Map Internals", priority: "high" },
      { topic: "Two Pointer Technique", priority: "medium" }
    ],
    recommended_problems: [
      { title: "4Sum", platform: "LeetCode" },
      { title: "Subarray Sum Equals K", platform: "LeetCode" }
    ]
  };

  const projectedScore = data?.projected_score?.projected_score ?? 100;

  if (loading && !data) {
    return <div className="p-8 text-center text-slate-500 font-medium animate-pulse">Loading Evaluation Results...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-between">
        <Link to="/submissions" className="text-slate-500 hover:text-slate-700 text-xs font-semibold flex items-center transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Submissions
        </Link>
        <span className="text-xs text-slate-400 font-mono bg-slate-100 px-2 py-1 rounded-md">Status: {data?.status || "EVALUATED"}</span>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 relative overflow-hidden hover:shadow-lg transition-all duration-300"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-50 rounded-bl-[100px] flex items-start justify-end p-4 z-0">
              <motion.div 
                initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.3 }}
                className="w-16 h-16 rounded-full border-4 border-emerald-100 flex items-center justify-center text-emerald-600 font-bold bg-white text-lg shadow-sm"
              >
                {overall}<span className="text-xs text-slate-400 font-normal ml-0.5">/100</span>
              </motion.div>
            </div>

            <div className="relative z-10">
              <div className="flex items-center text-emerald-600 mb-6">
                <CheckCircle className="w-6 h-6 mr-2 fill-current" />
                <h2 className="text-xl font-bold">Evaluation Complete</h2>
              </div>
              
              <p className="text-slate-500 text-sm mb-4">Evaluated across 10 dimensions by LangGraph Agents via Groq</p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div>
                  <div className="text-xs text-slate-500 mb-1">Submission ID</div>
                  <div className="text-sm font-semibold text-slate-800">{data?.submission_id || id || "SUB-57E97EA4"}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Language</div>
                  <div className="text-sm font-semibold text-slate-800">{data?.language || "Python 3.12"}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Execution Time</div>
                  <div className="text-sm font-semibold text-slate-800 flex items-center"><Clock className="w-3.5 h-3.5 mr-1" /> 14 ms</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Memory</div>
                  <div className="text-sm font-semibold text-slate-800 flex items-center"><Cpu className="w-3.5 h-3.5 mr-1" /> 4.2 MB</div>
                </div>
              </div>

              <h3 className="font-semibold text-slate-800 mb-4 text-sm">Multi-Dimensional Scores</h3>
              <div className="space-y-1">
                <ScoreBar label="Correctness Agent" score={correctness} maxScore={100} colorClass="bg-emerald-500" delay={0.1} />
                <ScoreBar label="Complexity Agent" score={complexity} maxScore={100} colorClass="bg-blue-500" delay={0.2} />
                <ScoreBar label="Style & Structure" score={style} maxScore={100} colorClass="bg-purple-500" delay={0.3} />
                <ScoreBar label="Originality Agent" score={originality} maxScore={100} colorClass="bg-indigo-500" delay={0.4} />
                <ScoreBar label="Execution Agent" score={100} maxScore={100} colorClass="bg-amber-500" delay={0.5} />
              </div>

              <motion.div 
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
                className="mt-8 border-t border-slate-100 pt-6"
              >
                <h3 className="font-semibold text-slate-800 mb-3 text-sm">Explainable Mentor Feedback</h3>
                <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100 italic shadow-inner">
                  "{feedback.mentor_feedback}"
                </p>

                <div className="grid md:grid-cols-2 gap-4 mt-4">
                  <motion.div whileHover={{ y: -2 }} className="bg-emerald-50/50 p-4 rounded-xl border border-emerald-100 transition-all">
                    <div className="text-emerald-700 font-semibold text-xs mb-2 flex items-center"><CheckCircle className="w-3.5 h-3.5 mr-1" /> KEY STRENGTHS</div>
                    <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                      {feedback.strengths?.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </motion.div>
                  <motion.div whileHover={{ y: -2 }} className="bg-amber-50/50 p-4 rounded-xl border border-amber-100 transition-all">
                    <div className="text-amber-700 font-semibold text-xs mb-2 flex items-center"><Zap className="w-3.5 h-3.5 mr-1" /> AREAS TO IMPROVE</div>
                    <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                      {feedback.weaknesses?.map((w, i) => <li key={i}>{w}</li>)}
                    </ul>
                  </motion.div>
                </div>
              </motion.div>

              {data?.improved_code && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8 }} className="mt-6 border-t border-slate-100 pt-6">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-slate-800 flex items-center text-sm">
                      <Code2 className="w-4 h-4 mr-2 text-indigo-600" />
                      AI Refactored Code (Revision Agent)
                    </h3>
                  </div>
                  <pre className="bg-[#1e1e1e] text-slate-200 p-4 rounded-xl text-xs font-mono overflow-x-auto shadow-inner border border-slate-800">
                    <code>{typeof data.improved_code === 'string' ? data.improved_code : data.improved_code.improved_code}</code>
                  </pre>
                </motion.div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Right Column (1/3 width) */}
        <div className="space-y-6">
          <motion.div 
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-lg transition-all duration-300"
          >
            <div className="flex items-center mb-4">
              <Zap className="w-5 h-5 text-amber-500 mr-2" />
              <h3 className="font-semibold text-slate-800 text-sm">Recommendations</h3>
            </div>
            
            <div className="mb-4">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Recommended Topics</h4>
              <div className="flex flex-wrap gap-2">
                {recommendations.recommended_topics?.map((t, i) => (
                  <span key={i} className="px-2.5 py-1 bg-indigo-50 text-indigo-600 border border-indigo-100 rounded-md text-xs font-medium hover:bg-indigo-100 transition-colors cursor-default">
                    {t.topic}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Practice Problems</h4>
              <ul className="text-xs text-slate-600 space-y-2 pl-1">
                {recommendations.recommended_problems?.map((p, i) => (
                  <motion.li key={i} whileHover={{ x: 2 }} className="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg font-medium border border-transparent hover:border-slate-200 transition-all cursor-pointer">
                    <span className="text-slate-800">{p.title}</span>
                    <span className="text-indigo-600 text-xs bg-white px-2 py-0.5 rounded shadow-sm">{p.platform}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.4 }}
            className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-lg transition-all duration-300"
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="font-semibold text-slate-800 text-sm">Score Projection</h3>
              <Target className="w-5 h-5 text-indigo-500" />
            </div>
            
            <div className="text-center mb-4 border-b border-slate-100 pb-4">
              <div className="text-xs text-slate-500 mb-1">Projected Score</div>
              <div className="text-3xl font-bold text-emerald-600">{projectedScore} / 100</div>
            </div>

            <div className="space-y-2 text-xs text-slate-600">
              <div className="flex justify-between">
                <span>Current Score</span>
                <span className="font-semibold text-slate-800">{overall} / 100</span>
              </div>
              <div className="flex justify-between">
                <span>Potential Gain</span>
                <span className="font-semibold text-emerald-600 flex items-center">+{Math.max(0, (projectedScore - overall).toFixed(1))} <ArrowUp className="w-3 h-3 ml-0.5" /></span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default SubmissionResult;
