import React, { useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Award,
  AlertTriangle,
  Calendar,
  Layers,
  ShieldAlert,
  Code2,
  Sparkles,
  CheckCircle,
  FileSpreadsheet,
  Users,
  Mail,
  UserCheck,
  ChevronRight,
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  X
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ScoreDistributionBarChart } from '../common/ChartComponents';
import { Modal } from '../common/Modal';

export interface BucketStudent {
  id: string;
  name: string;
  rollNumber: string;
  email: string;
  avatar: string;
  avgScore: number;
  submissionsCount: number;
  weakTopics: string[];
  status: 'On Track' | 'Needs Attention' | 'At Risk';
  department: string;
  year: string;
}

export const HISTOGRAM_BUCKET_STUDENTS: Record<string, BucketStudent[]> = {
  '0-20': [
    {
      id: 'stu-b1',
      name: 'Rajesh Kumar',
      rollNumber: '21C51242',
      email: 'rajesh.k@university.edu',
      avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=100&auto=format&fit=crop&q=80',
      avgScore: 18.5,
      submissionsCount: 4,
      weakTopics: ['Dynamic Programming', 'Pointer Logic'],
      status: 'At Risk',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b2',
      name: 'Vikram Sharma',
      rollNumber: '21C51246',
      email: 'vikram.s@university.edu',
      avatar: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&auto=format&fit=crop&q=80',
      avgScore: 15.0,
      submissionsCount: 3,
      weakTopics: ['Recursion Bounds', 'Arrays'],
      status: 'At Risk',
      department: 'CSE',
      year: '3rd Year'
    }
  ],
  '21-40': [
    {
      id: 'stu-5',
      name: 'Karthik P.',
      rollNumber: '21C51252',
      email: 'karthik.p@example.com',
      avatar: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=100&auto=format&fit=crop&q=80',
      avgScore: 38.7,
      submissionsCount: 9,
      weakTopics: ['DP', 'Math'],
      status: 'At Risk',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b3',
      name: 'Suresh Raina',
      rollNumber: '21C51254',
      email: 'suresh.r@university.edu',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
      avgScore: 35.2,
      submissionsCount: 6,
      weakTopics: ['Binary Search', 'Trees'],
      status: 'At Risk',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b4',
      name: 'Manoj Verma',
      rollNumber: '21C51258',
      email: 'manoj.v@university.edu',
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80',
      avgScore: 32.0,
      submissionsCount: 5,
      weakTopics: ['Graphs', 'Hash Table'],
      status: 'At Risk',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b5',
      name: 'Deepak Verma',
      rollNumber: '21C51260',
      email: 'deepak.v@university.edu',
      avatar: 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=100&auto=format&fit=crop&q=80',
      avgScore: 28.4,
      submissionsCount: 7,
      weakTopics: ['Backtracking'],
      status: 'At Risk',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b6',
      name: 'Abhishek Sen',
      rollNumber: '21C51263',
      email: 'abhishek.s@university.edu',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      avgScore: 39.1,
      submissionsCount: 8,
      weakTopics: ['Bit Manipulation'],
      status: 'At Risk',
      department: 'CSE',
      year: '3rd Year'
    }
  ],
  '41-60': [
    {
      id: 'stu-4',
      name: 'Harish N.',
      rollNumber: '21C51245',
      email: 'harish.n@example.com',
      avatar: 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=100&auto=format&fit=crop&q=80',
      avgScore: 54.1,
      submissionsCount: 9,
      weakTopics: ['Graphs', 'Topological Sort'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-3',
      name: 'Sai Kiran',
      rollNumber: '21C51289',
      email: 'sai.kiran@example.com',
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80',
      avgScore: 58.2,
      submissionsCount: 10,
      weakTopics: ['DP', 'Arrays'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b7',
      name: 'Pooja Hegde',
      rollNumber: '21C51270',
      email: 'pooja.h@university.edu',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80',
      avgScore: 48.5,
      submissionsCount: 10,
      weakTopics: ['Heaps & Priority Queues'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b8',
      name: 'Nikhil Rao',
      rollNumber: '21C51272',
      email: 'nikhil.r@university.edu',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
      avgScore: 52.0,
      submissionsCount: 11,
      weakTopics: ['Queue Buffers'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b9',
      name: 'Tanvi Shah',
      rollNumber: '21C51275',
      email: 'tanvi.s@university.edu',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      avgScore: 57.4,
      submissionsCount: 8,
      weakTopics: ['Trie Structures'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b10',
      name: 'Aman Gupta',
      rollNumber: '21C51278',
      email: 'aman.g@university.edu',
      avatar: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=100&auto=format&fit=crop&q=80',
      avgScore: 44.0,
      submissionsCount: 7,
      weakTopics: ['Greedy Bounds'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b11',
      name: 'Ritu Raj',
      rollNumber: '21C51280',
      email: 'ritu.r@university.edu',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80',
      avgScore: 59.0,
      submissionsCount: 12,
      weakTopics: ['Linked List Cycles'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b12',
      name: 'Gaurav Joshi',
      rollNumber: '21C51282',
      email: 'gaurav.j@university.edu',
      avatar: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&auto=format&fit=crop&q=80',
      avgScore: 46.5,
      submissionsCount: 8,
      weakTopics: ['Binary Search'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b13',
      name: 'Divya K.',
      rollNumber: '21C51285',
      email: 'divya.k@university.edu',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      avgScore: 53.8,
      submissionsCount: 9,
      weakTopics: ['String Matching'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b14',
      name: 'Varun Tej',
      rollNumber: '21C51288',
      email: 'varun.t@university.edu',
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80',
      avgScore: 49.5,
      submissionsCount: 6,
      weakTopics: ['Recursion Trees'],
      status: 'Needs Attention',
      department: 'CSE',
      year: '3rd Year'
    }
  ],
  '61-80': [
    {
      id: 'stu-2',
      name: 'Arjun K.',
      rollNumber: '21C51208',
      email: 'arjun.k@example.com',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
      avgScore: 76.4,
      submissionsCount: 11,
      weakTopics: ['Trees'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-1',
      name: 'Vignesh Reddy',
      rollNumber: '21C51234',
      email: 'vignesh@example.com',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      avgScore: 78.6,
      submissionsCount: 12,
      weakTopics: ['DP', 'Graphs'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b15',
      name: 'Meera Nair',
      rollNumber: '21C51215',
      email: 'meera.n@university.edu',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80',
      avgScore: 74.0,
      submissionsCount: 13,
      weakTopics: ['DP Optimization'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b16',
      name: 'Kavya Sundaram',
      rollNumber: '21C51218',
      email: 'kavya.s@university.edu',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      avgScore: 79.5,
      submissionsCount: 14,
      weakTopics: ['Graph Traversals'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b17',
      name: 'Pranav Bhat',
      rollNumber: '21C51222',
      email: 'pranav.b@university.edu',
      avatar: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&auto=format&fit=crop&q=80',
      avgScore: 67.8,
      submissionsCount: 11,
      weakTopics: ['AVL Trees'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b18',
      name: 'Shreya Joshi',
      rollNumber: '21C51225',
      email: 'shreya.j@university.edu',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80',
      avgScore: 71.2,
      submissionsCount: 12,
      weakTopics: ['Strings'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b19',
      name: 'Aditya Roy',
      rollNumber: '21C51228',
      email: 'aditya.r@university.edu',
      avatar: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=100&auto=format&fit=crop&q=80',
      avgScore: 65.0,
      submissionsCount: 10,
      weakTopics: ['DP Memoization'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b20',
      name: 'Priya Menon',
      rollNumber: '21C51230',
      email: 'priya.m@university.edu',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      avgScore: 77.0,
      submissionsCount: 13,
      weakTopics: ['Monotonic Stack'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    }
  ],
  '81-100': [
    {
      id: 'stu-6',
      name: 'Ananya Sharma',
      rollNumber: '21C51212',
      email: 'ananya.s@example.com',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80',
      avgScore: 96.2,
      submissionsCount: 16,
      weakTopics: ['Bit Manipulation'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b21',
      name: 'Sneha Patel',
      rollNumber: '21C51204',
      email: 'sneha.p@university.edu',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      avgScore: 91.5,
      submissionsCount: 15,
      weakTopics: ['Advanced DP'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b22',
      name: 'Rohan Verma',
      rollNumber: '21C51202',
      email: 'rohan.v@university.edu',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
      avgScore: 88.0,
      submissionsCount: 14,
      weakTopics: ['Graph Flow'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b23',
      name: 'Aditi Deshmukh',
      rollNumber: '21C51206',
      email: 'aditi.d@university.edu',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80',
      avgScore: 86.4,
      submissionsCount: 15,
      weakTopics: ['Trie Trees'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    },
    {
      id: 'stu-b24',
      name: 'Siddharth Roy',
      rollNumber: '21C51210',
      email: 'siddharth.r@university.edu',
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80',
      avgScore: 89.0,
      submissionsCount: 14,
      weakTopics: ['Bitmasks'],
      status: 'On Track',
      department: 'CSE',
      year: '3rd Year'
    }
  ]
};

export const ClassAnalyticsView: React.FC = () => {
  const { instructorStats, similarityAlerts, goBackToDashboard } = useApp();
  const [activeTab, setActiveTab] = useState<'analytics' | 'similarity'>('analytics');
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  // Selected Histogram Range state (defaults to '0-20' so clicking on 2 or any bucket works immediately)
  const [selectedBucketRange, setSelectedBucketRange] = useState<string | null>('0-20');
  const [inspectedStudent, setInspectedStudent] = useState<BucketStudent | null>(null);

  const activeAlert = similarityAlerts[0];

  const topicWeaknessStats = [
    { topic: 'Dynamic Programming', failRate: '42.5%', studentsCount: 19, severity: 'High' },
    { topic: 'Graphs (BFS/DFS)', failRate: '36.8%', studentsCount: 16, severity: 'High' },
    { topic: 'Trees & Recursion', failRate: '28.1%', studentsCount: 12, severity: 'Medium' },
    { topic: 'Linked Lists', failRate: '18.4%', studentsCount: 8, severity: 'Low' },
    { topic: 'Arrays & Two Pointers', failRate: '8.2%', studentsCount: 4, severity: 'Low' }
  ];

  const handleAction = (action: string) => {
    setActionStatus(action);
    setTimeout(() => setActionStatus(null), 3000);
  };

  const currentBucketStudents = selectedBucketRange ? HISTOGRAM_BUCKET_STUDENTS[selectedBucketRange] || [] : [];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Breadcrumb Navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={goBackToDashboard}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-emerald-700 transition-colors p-2 hover:bg-slate-100 rounded-xl cursor-pointer"
        >
          <BarChart3 className="w-4 h-4" />
          <span>← Back to Instructor Dashboard</span>
        </button>
      </div>

      {/* Header */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Class Analytics & Integrity Shield
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Cohort grade metrics, score distributions, and AI plagiarism alerts for CSE-301 Section A.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-100 rounded-2xl border border-slate-200/80 self-start md:self-auto">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'analytics'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Class Performance</span>
          </button>

          <button
            onClick={() => setActiveTab('similarity')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'similarity'
                ? 'bg-rose-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Similarity Alerts ({similarityAlerts.length})</span>
          </button>
        </div>
      </div>

      {/* TAB 1: CLASS PERFORMANCE ANALYTICS */}
      {activeTab === 'analytics' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top 3 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Class Average Score
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900 font-mono">
                  {instructorStats.averageScore}%
                </span>
                <span className="text-xs text-emerald-600 font-bold">+2.4% vs last week</span>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">
                Top Score
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-emerald-700 font-mono">
                  {instructorStats.highestScore}%
                </span>
                <span className="text-xs text-slate-500">(Ananya Sharma)</span>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-rose-600">
                Lowest Score
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-rose-700 font-mono">
                  {instructorStats.lowestScore}%
                </span>
                <span className="text-xs text-rose-600 font-semibold">Needs Support</span>
              </div>
            </div>
          </div>

          {/* Interactive Score Distribution Bar Chart */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">Score Distribution Histogram (0 - 100)</h3>
              </div>
              <span className="text-xs font-mono text-slate-400">48 Enrolled Students • Click any bar to inspect cohort</span>
            </div>

            <div className="pt-2">
              <ScoreDistributionBarChart
                distribution={instructorStats.scoreDistribution}
                onSelectBucket={(range) => setSelectedBucketRange(range)}
                selectedRange={selectedBucketRange}
              />
            </div>

            {/* EXPANDABLE STUDENTS LIST FOR SELECTED HISTOGRAM BAR */}
            {selectedBucketRange && (
              <div className="mt-6 pt-6 border-t border-slate-200 space-y-4 animate-fadeIn">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gradient-to-r from-slate-900 to-indigo-950 p-4 rounded-2xl text-white">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-indigo-600 rounded-xl">
                      <Users className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-extrabold">
                          Students in Score Range {selectedBucketRange}%
                        </h4>
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-extrabold bg-white/20 text-white">
                          {currentBucketStudents.length} {currentBucketStudents.length === 1 ? 'Student' : 'Students'}
                        </span>
                      </div>
                      <p className="text-[11px] text-indigo-200">
                        Detailed roster records for students matching the {selectedBucketRange}% performance bracket.
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedBucketRange(null)}
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors self-start sm:self-auto cursor-pointer"
                    title="Close list"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Students Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {currentBucketStudents.map((stu) => (
                    <div
                      key={stu.id}
                      onClick={() => setInspectedStudent(stu)}
                      className="p-4 bg-slate-50/80 hover:bg-white border border-slate-200/80 hover:border-indigo-400 rounded-2xl shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <img
                              src={stu.avatar}
                              alt={stu.name}
                              className="w-10 h-10 rounded-full object-cover ring-2 ring-indigo-500/20"
                            />
                            <div>
                              <h5 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                                {stu.name}
                              </h5>
                              <span className="text-[11px] text-slate-400 font-mono">
                                {stu.rollNumber} • {stu.department}
                              </span>
                            </div>
                          </div>

                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold ${
                              stu.status === 'At Risk'
                                ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                : stu.status === 'Needs Attention'
                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                            }`}
                          >
                            {stu.status}
                          </span>
                        </div>

                        {/* Metrics Row */}
                        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200/60 text-xs font-mono">
                          <div className="p-2 bg-white rounded-xl border border-slate-100">
                            <span className="text-[10px] text-slate-400 uppercase font-sans block font-semibold">Average Grade</span>
                            <span className={`text-base font-extrabold ${
                              stu.avgScore < 40 ? 'text-rose-600' : stu.avgScore < 70 ? 'text-amber-600' : 'text-emerald-600'
                            }`}>
                              {stu.avgScore}%
                            </span>
                          </div>
                          <div className="p-2 bg-white rounded-xl border border-slate-100">
                            <span className="text-[10px] text-slate-400 uppercase font-sans block font-semibold">Submissions</span>
                            <span className="text-base font-extrabold text-slate-800">
                              {stu.submissionsCount}
                            </span>
                          </div>
                        </div>

                        {/* Identified Weak Topics */}
                        <div className="space-y-1">
                          <span className="text-[10px] uppercase font-bold text-slate-400">Identified Gaps:</span>
                          <div className="flex flex-wrap gap-1.5">
                            {stu.weakTopics.map((wt, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200"
                              >
                                ⚠️ {wt}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-center justify-between text-xs">
                        <span className="text-indigo-600 font-bold group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                          <span>Inspect Student Report</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </span>

                        <a
                          href={`mailto:${stu.email}`}
                          onClick={(e) => e.stopPropagation()}
                          className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                          title="Send Email"
                        >
                          <Mail className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Weak Topics Table */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <h3 className="text-base font-bold text-slate-900">Class-Wide Algorithmic Concept Gaps</h3>
              </div>
              <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-1 rounded-lg">AI Diagnosed</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 font-semibold text-[11px] uppercase">
                    <th className="pb-3">Concept Area</th>
                    <th className="pb-3">Failure Rate</th>
                    <th className="pb-3">Impacted Students</th>
                    <th className="pb-3">Severity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {topicWeaknessStats.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3.5 font-bold text-slate-800">{item.topic}</td>
                      <td className="py-3.5 font-mono text-slate-700">{item.failRate}</td>
                      <td className="py-3.5 font-mono text-slate-700">{item.studentsCount} students</td>
                      <td className="py-3.5">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          item.severity === 'High' ? 'bg-rose-100 text-rose-800' :
                          item.severity === 'Medium' ? 'bg-amber-100 text-amber-800' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {item.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PLAGIARISM & SIMILARITY SHIELD */}
      {activeTab === 'similarity' && activeAlert && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top Banner */}
          <div className="bg-rose-50 border border-rose-200 rounded-3xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-rose-600 text-white rounded-2xl">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-extrabold text-rose-900">
                    High Similarity Alert ({activeAlert.similarityPercentage}%)
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-rose-200 text-rose-900 rounded">
                    Risk: {activeAlert.riskLevel}
                  </span>
                </div>
                <p className="text-xs text-rose-800">
                  Question: <strong>{activeAlert.problemTitle}</strong> • Flagged on {activeAlert.timestamp}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleAction('Flag Dismissed as false positive')}
                className="px-3.5 py-2 bg-white hover:bg-slate-100 text-slate-700 rounded-xl text-xs font-bold border border-slate-200 transition-colors cursor-pointer"
              >
                Dismiss Flag
              </button>
              <button
                onClick={() => handleAction('Review Scheduled with students')}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold shadow-xs transition-all cursor-pointer"
              >
                Request Review
              </button>
            </div>
          </div>

          {actionStatus && (
            <div className="p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-semibold animate-fadeIn">
              ✅ {actionStatus}
            </div>
          )}

          {/* Pairwise AST Code Viewer */}
          <div className="bg-slate-900 rounded-3xl border border-slate-800 overflow-hidden shadow-xl">
            <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-xs">
                <Code2 className="w-4 h-4 text-indigo-400" />
                <span>Pairwise AST Token Comparison</span>
              </div>
              <span className="text-xs font-mono text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded border border-rose-500/20">
                {activeAlert.matchedLinesCount} Token-Matched Blocks
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-800 font-mono text-xs">
              <div className="p-5 bg-slate-900/60">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                  <span className="text-sm font-bold text-white block">{activeAlert.studentA.name} ({activeAlert.studentA.rollNumber})</span>
                  <span className="text-xs px-2 py-0.5 bg-indigo-500/10 text-indigo-300 rounded">Student A</span>
                </div>
                <pre className="text-slate-300 leading-relaxed overflow-x-auto whitespace-pre">
                  {activeAlert.studentACodeSnippet}
                </pre>
              </div>

              <div className="p-5 bg-slate-950/60">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                  <span className="text-sm font-bold text-white block">{activeAlert.studentB.name} ({activeAlert.studentB.rollNumber})</span>
                  <span className="text-xs px-2 py-0.5 bg-rose-500/10 text-rose-300 rounded">Student B</span>
                </div>
                <pre className="text-slate-300 leading-relaxed overflow-x-auto whitespace-pre">
                  {activeAlert.studentBCodeSnippet}
                </pre>
              </div>
            </div>

            <div className="p-4 bg-slate-950 border-t border-slate-800 text-xs text-slate-300 space-y-1">
              <span className="text-purple-400 font-bold flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" /> AI Plagiarism Audit Notes:
              </span>
              <p className="text-slate-400 font-sans leading-relaxed">
                {activeAlert.aiAuditNotes}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* STUDENT DETAIL MODAL */}
      {inspectedStudent && (
        <Modal
          isOpen={!!inspectedStudent}
          onClose={() => setInspectedStudent(null)}
          title={`Student Performance Report: ${inspectedStudent.name}`}
          subtitle={`Roll: ${inspectedStudent.rollNumber} • ${inspectedStudent.department} • ${inspectedStudent.year}`}
          maxWidth="2xl"
        >
          <div className="space-y-6 text-xs">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-slate-400 block font-semibold">Submissions</span>
                <span className="text-2xl font-mono font-extrabold text-slate-800 mt-1 block">
                  {inspectedStudent.submissionsCount}
                </span>
              </div>
              <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200">
                <span className="text-emerald-700 block font-semibold">Average Grade</span>
                <span className="text-2xl font-mono font-extrabold text-emerald-700 mt-1 block">
                  {inspectedStudent.avgScore}%
                </span>
              </div>
              <div className="p-3.5 bg-purple-50 rounded-xl border border-purple-200">
                <span className="text-purple-700 block font-semibold">Cohort Status</span>
                <span className="text-sm font-extrabold text-purple-800 mt-2 block">
                  {inspectedStudent.status}
                </span>
              </div>
            </div>

            {/* AI Diagnostics */}
            <div className="p-4 bg-slate-900 text-white rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-indigo-400 font-bold">
                <Sparkles className="w-4 h-4" />
                <span>AI Algorithmic Diagnostic</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Student shows specific challenges in {inspectedStudent.weakTopics.join(' and ')}. Recommend targeted reinforcement challenges and guided tutoring on complexity bottlenecks.
              </p>
            </div>

            {/* Identified gaps */}
            <div>
              <span className="font-bold text-slate-800 mb-2 block">Identified Concept Gaps:</span>
              <div className="flex flex-wrap gap-2">
                {inspectedStudent.weakTopics.map((wt, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 font-bold"
                  >
                    ⚠️ {wt}
                  </span>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <a
                href={`mailto:${inspectedStudent.email}`}
                className="inline-flex items-center gap-1.5 text-indigo-600 font-bold hover:underline"
              >
                <Mail className="w-4 h-4" />
                <span>Send Direct Feedback Email</span>
              </a>

              <button
                onClick={() => setInspectedStudent(null)}
                className="px-4 py-2 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 cursor-pointer"
              >
                Close Report
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
