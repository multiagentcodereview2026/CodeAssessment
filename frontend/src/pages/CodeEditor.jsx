import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Send, ArrowLeft, Code, AlertCircle, CheckCircle2, XCircle, Terminal } from 'lucide-react';
import { useAuth } from '../context/useAuth';

const CodeEditor = () => {
  const { id } = useParams();
  const problemId = id || "two-sum";
  const navigate = useNavigate();
  const { user, authFetch } = useAuth();

  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState("python");
  const [codeDrafts, setCodeDrafts] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Track code draft changes per language
  const currentCode = codeDrafts[language] ?? "";

  // Load problem details once when problemId changes
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setErrorMessage(null);
    setConsoleOutput(null);

    authFetch(`/api/problems/${problemId}`)
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Failed to load problem (${res.status})`);
        }
        return res.json();
      })
      .then((data) => {
        if (!isMounted) return;
        setProblem(data);
        const starters = data.starter_codes || {};
        setCodeDrafts({
          python: starters.python || "",
          cpp: starters.cpp || "",
          c: starters.c || "",
          java: starters.java || "",
          javascript: starters.javascript || "",
        });
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setErrorMessage(err.message || "Unable to load problem from server.");
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [problemId]);

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    if (!(newLang in codeDrafts) && problem?.starter_codes?.[newLang]) {
      setCodeDrafts(prev => ({
        ...prev,
        [newLang]: problem.starter_codes[newLang]
      }));
    }
  };

  const handleCodeChange = (newVal) => {
    setCodeDrafts(prev => ({
      ...prev,
      [language]: newVal || ""
    }));
  };

  const handleQuickRun = async () => {
    setIsRunning(true);
    setConsoleOutput(null);
    setErrorMessage(null);

    try {
      const response = await authFetch('/api/submissions/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem_id: problemId,
          language,
          code: currentCode
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Execution request failed');
      }

      setConsoleOutput(data);
    } catch (e) {
      setConsoleOutput({
        execution_status: "error",
        passed_cases: 0,
        failed_cases: 0,
        total_cases: 0,
        runtime_ms: 0,
        stderr: e.message || "Failed to execute code on server."
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await authFetch('/api/submissions/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: user?.username || "24BD1A058Z",
          problem_id: problemId,
          language,
          code: currentCode
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Submission failed to process');
      }

      sessionStorage.setItem('latest_evaluation', JSON.stringify(data));
      navigate(`/submissions/${data.submission_id}`);
    } catch (e) {
      setErrorMessage(e.message || 'Submission evaluation failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500 font-medium h-[calc(100vh-6rem)] flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <Code className="w-8 h-8 text-indigo-400 mb-4 animate-bounce" />
          Loading Problem Environment...
        </div>
      </div>
    );
  }

  if (!problem) {
    return (
      <div className="p-8 text-center text-slate-600 h-[calc(100vh-6rem)] flex flex-col items-center justify-center space-y-4">
        <AlertCircle className="w-10 h-10 text-red-500" />
        <h2 className="text-lg font-bold text-slate-800">Problem Not Found</h2>
        <p className="text-sm text-slate-500">{errorMessage || `Could not find problem "${problemId}"`}</p>
        <button
          onClick={() => navigate('/problems')}
          className="px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Back to Problem Catalogue
        </button>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }} 
      animate={{ opacity: 1, scale: 1 }} 
      transition={{ duration: 0.4 }}
      className="h-[calc(100vh-6rem)] flex flex-col md:flex-row gap-6 max-w-7xl mx-auto"
    >
      {/* Left: Problem Details */}
      <div className="w-full md:w-1/2 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden hover:shadow-lg transition-all duration-300">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center">
            <button onClick={() => navigate('/problems')} className="text-slate-400 hover:text-slate-600 mr-4 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h2 className="font-semibold text-slate-800 text-sm">Problem Details</h2>
          </div>
          {problem.category && (
            <span className="text-xs px-2.5 py-0.5 bg-slate-100 text-slate-600 rounded-full font-medium">
              {problem.category}
            </span>
          )}
        </div>
        
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-slate-800">{problem.title}</h1>
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
              problem.difficulty === 'Easy' ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' :
              problem.difficulty === 'Hard' ? 'bg-red-50 text-red-600 border border-red-100' :
              'bg-amber-50 text-amber-600 border border-amber-100'
            }`}>
              {problem.difficulty}
            </span>
          </div>

          <p className="text-slate-600 leading-relaxed whitespace-pre-wrap text-sm">{problem.description}</p>

          {problem.examples && problem.examples.length > 0 && (
            <div>
              <h3 className="font-semibold text-slate-800 mb-3 text-sm">Examples:</h3>
              <div className="space-y-3">
                {problem.examples.map((ex, idx) => (
                  <motion.div 
                    key={idx} 
                    initial={{ opacity: 0, x: -10 }} 
                    animate={{ opacity: 1, x: 0 }} 
                    transition={{ delay: 0.05 * idx }}
                    className="bg-slate-50 p-3.5 rounded-xl border border-slate-100 font-mono text-xs hover:border-indigo-100 transition-colors"
                  >
                    <div className="mb-1"><span className="text-slate-500 font-semibold">Input:</span> <span className="text-slate-800">{ex.input}</span></div>
                    <div className="mb-1"><span className="text-slate-500 font-semibold">Output:</span> <span className="text-slate-800">{ex.output}</span></div>
                    {ex.explanation && <div><span className="text-slate-500 font-semibold">Explanation:</span> <span className="text-slate-600">{ex.explanation}</span></div>}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {problem.constraints && problem.constraints.length > 0 && (
            <div>
              <h3 className="font-semibold text-slate-800 mb-2 text-sm">Constraints:</h3>
              <ul className="list-disc pl-5 space-y-1 text-slate-600 text-xs font-mono">
                {problem.constraints.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Console / Run Output */}
          <AnimatePresence>
            {consoleOutput && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }} 
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="mt-4 p-4 bg-slate-900 text-slate-200 rounded-xl font-mono text-xs shadow-inner space-y-2"
              >
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
                  <span className="flex items-center text-slate-400 font-semibold">
                    <Terminal className="w-3.5 h-3.5 mr-1.5" /> Output Console
                  </span>
                  {consoleOutput.runtime_ms !== undefined && (
                    <span className="text-slate-500 text-[11px]">{consoleOutput.runtime_ms} ms</span>
                  )}
                </div>

                {consoleOutput.compile_status && consoleOutput.compile_status !== "success" ? (
                  <div className="text-red-400">
                    <div className="font-bold flex items-center mb-1">
                      <XCircle className="w-4 h-4 mr-1.5" /> Compilation Error
                    </div>
                    <pre className="text-red-300 text-[11px] whitespace-pre-wrap">{consoleOutput.compile_error || consoleOutput.stderr}</pre>
                  </div>
                ) : consoleOutput.total_cases > 0 ? (
                  <div>
                    <div className={`font-bold flex items-center mb-1.5 ${
                      consoleOutput.passed_cases === consoleOutput.total_cases ? 'text-emerald-400' : 'text-amber-400'
                    }`}>
                      {consoleOutput.passed_cases === consoleOutput.total_cases ? (
                        <CheckCircle2 className="w-4 h-4 mr-1.5" />
                      ) : (
                        <AlertCircle className="w-4 h-4 mr-1.5" />
                      )}
                      Test Cases: {consoleOutput.passed_cases} / {consoleOutput.total_cases} Passed
                    </div>
                    {consoleOutput.stdout && (
                      <div className="text-slate-300 text-[11px] bg-slate-950/60 p-2 rounded">
                        <span className="text-slate-500 font-semibold block mb-1">Stdout:</span>
                        <pre className="whitespace-pre-wrap">{consoleOutput.stdout}</pre>
                      </div>
                    )}
                    {consoleOutput.stderr && (
                      <div className="text-red-300 text-[11px] bg-red-950/40 p-2 rounded mt-2">
                        <span className="text-red-400 font-semibold block mb-1">Stderr:</span>
                        <pre className="whitespace-pre-wrap">{consoleOutput.stderr}</pre>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-slate-400">
                    {consoleOutput.stderr ? (
                      <pre className="text-red-300 text-[11px] whitespace-pre-wrap">{consoleOutput.stderr}</pre>
                    ) : (
                      <pre className="text-slate-300 text-[11px] whitespace-pre-wrap">{consoleOutput.stdout || "Execution finished with no output."}</pre>
                    )}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Submission Error Banner */}
          {errorMessage && (
            <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start">
              <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Submission Failed</p>
                <p className="mt-0.5 text-red-600">{errorMessage}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right: Monaco Editor */}
      <div className="w-full md:w-1/2 bg-[#1e1e1e] rounded-2xl flex flex-col overflow-hidden shadow-lg border border-slate-800 hover:shadow-2xl transition-all duration-300">
        <div className="px-4 py-3 bg-[#2d2d2d] flex justify-between items-center border-b border-[#404040]">
          <div className="flex items-center text-slate-300 text-sm font-medium">
            <Code className="w-4 h-4 mr-2 text-indigo-400" /> Code Editor
          </div>
          <select 
            value={language}
            onChange={(e) => handleLanguageChange(e.target.value)}
            className="bg-[#1e1e1e] border border-[#404040] text-xs rounded-md px-2.5 py-1 text-slate-300 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
          >
            <option value="python">Python 3.11</option>
            <option value="cpp">C++ (GCC 13)</option>
            <option value="c">C (GCC 13)</option>
            <option value="java">Java 17</option>
            <option value="javascript">JavaScript (Node.js)</option>
          </select>
        </div>

        <div className="flex-1 relative pt-2">
          <Editor
            height="100%"
            language={
              language === "cpp" || language === "c" ? "cpp" :
              language === "python" ? "python" :
              language === "java" ? "java" : "javascript"
            }
            theme="vs-dark"
            value={currentCode}
            onChange={handleCodeChange}
            options={{
              minimap: { enabled: false },
              fontSize: 13.5,
              fontFamily: 'JetBrains Mono, Menlo, Monaco, monospace',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 4,
            }}
          />
        </div>
        
        <div className="p-4 bg-[#2d2d2d] border-t border-[#404040] flex space-x-3">
          <button 
            onClick={handleQuickRun}
            disabled={isRunning || isSubmitting}
            className="flex-1 py-2.5 bg-[#404040] hover:bg-[#4a4a4a] text-white rounded-lg text-xs font-medium transition-colors flex items-center justify-center disabled:opacity-50 cursor-pointer"
          >
            <Play className={`w-4 h-4 mr-2 ${isRunning ? 'text-slate-400 animate-pulse' : 'text-emerald-400'}`} />
            {isRunning ? 'Running Tests...' : 'Run Public Tests'}
          </button>
          <button 
            onClick={handleSubmit}
            disabled={isSubmitting || isRunning}
            className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50 flex items-center justify-center shadow-md shadow-indigo-600/30 cursor-pointer"
          >
            <Send className={`w-4 h-4 mr-2 ${isSubmitting ? 'animate-pulse' : ''}`} />
            {isSubmitting ? 'Evaluating (10 Multi-Agent Steps)...' : 'Submit for Full Judging'}
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default CodeEditor;
