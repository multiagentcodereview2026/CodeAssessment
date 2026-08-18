import { FileText, Download, Clock, CheckCircle2, AlertTriangle, BookOpen } from 'lucide-react';

const mockReports = [
  { id: 1, name: 'Performance Report', description: 'Comprehensive overview of student grades and class averages.', lastGenerated: 'Today, 10:30 AM', icon: FileText, color: 'text-blue-500', bg: 'bg-blue-50' },
  { id: 2, name: 'Assignment Report', description: 'Detailed statistics on submission rates and average scores per assignment.', lastGenerated: 'Yesterday, 04:15 PM', icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-50' },
  { id: 3, name: 'Topic Wise Report', description: 'Analysis of class strengths and weaknesses across different coding topics.', lastGenerated: '02 May, 11:00 AM', icon: BookOpen, color: 'text-purple-500', bg: 'bg-purple-50' },
  { id: 4, name: 'At-Risk Students Report', description: 'List of students falling below the 60% threshold with specific weak areas.', lastGenerated: '01 May, 09:00 AM', icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-50' },
];

const InstructorReports = () => {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Class Reports</h1>
        <p className="text-slate-500 text-sm mt-1">Generate and export detailed analytics on class performance.</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {mockReports.map((report) => (
          <div key={report.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex items-center justify-between hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-4 flex-1">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${report.bg} ${report.color}`}>
                <report.icon className="w-6 h-6" />
              </div>
              
              <div>
                <h3 className="font-semibold text-slate-800 text-base">{report.name}</h3>
                <p className="text-slate-500 text-xs mt-0.5">{report.description}</p>
                <div className="flex items-center text-xs text-slate-400 mt-2 font-medium">
                  <Clock className="w-3.5 h-3.5 mr-1" /> Last Generated: {report.lastGenerated}
                </div>
              </div>
            </div>

            <div className="flex space-x-3 ml-4">
              <button className="flex items-center px-4 py-2 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-xs font-medium transition-colors border border-emerald-100">
                <Download className="w-3.5 h-3.5 mr-1.5" /> Export CSV
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InstructorReports;
