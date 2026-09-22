import React, { useState } from 'react';
import {
  FileSpreadsheet,
  Download,
  FileText,
  Calendar,
  CheckCircle,
  Sparkles,
  Printer,
  Plus,
  Filter
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ReportItem } from '../../types';
import { Modal } from '../common/Modal';

export const ReportsExportView: React.FC = () => {
  const { reports, generateReport, courses, showToast } = useApp();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reportTitle, setReportTitle] = useState('');
  const [reportType, setReportType] = useState<'Performance' | 'Assignment' | 'Topic' | 'At-Risk'>('Performance');
  const [reportFormat, setReportFormat] = useState<'PDF' | 'CSV' | 'XLSX'>('PDF');

  const handleDownload = (report: ReportItem) => {
    setDownloadingId(report.id);
    setTimeout(() => {
      setDownloadingId(null);
      
      let content = `Report: ${report.title}\nType: ${report.type}\nGenerated Date: ${report.generatedDate}\nFormat: ${report.format}\nStatus: Verified\nPlatform: AutoGrade AI v2.4\n\n`;
      if (report.format === 'CSV') {
        content += `Student_ID,Name,Course,Problems_Solved,Average_Score,Status\n`;
        content += `24BD1A058Z,Vignesh Reddy,CSE-301,24,82.6,On Track\n`;
        content += `24BD1A0586,Mani Greeva,CSE-301,21,79.0,On Track\n`;
        content += `24BD1A058K,Nayaneesh,CSE-301,18,74.5,Needs Attention\n`;
        content += `24BD1A058V,Pavan Reddy,CSE-301,12,58.2,At Risk\n`;
      } else {
        content += `Summary:\n${report.description}\n\nExecutive Metrics:\n- Cohort Enrolled: 48 Students\n- Median Score: 78.4%\n- Pass Rate: 92.1%\n- AI Rubric Calibrated: Yes\n`;
      }

      const element = document.createElement('a');
      const file = new Blob([content], { type: report.format === 'CSV' ? 'text/csv' : 'text/plain' });
      element.href = URL.createObjectURL(file);
      element.download = `${report.title.replace(/\s+/g, '_')}.${report.format.toLowerCase()}`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);

      showToast(`Downloaded "${report.title}" (${report.format})`, 'success');
    }, 800);
  };

  const handleCreateReport = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportTitle.trim()) return;

    generateReport({
      id: `rep-${Date.now()}`,
      title: reportTitle.trim(),
      description: `Custom ${reportType} analysis generated for academic accreditation compliance.`,
      type: reportType,
      generatedDate: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
      fileSize: reportFormat === 'PDF' ? '3.8 MB' : '420 KB',
      format: reportFormat
    });

    setIsModalOpen(false);
    setReportTitle('');
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Institutional Reports & Exports
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Export accreditation documents, cohort grade distribution PDFs, and concept breakdown CSVs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 rounded-2xl text-xs font-bold border border-slate-200 shadow-xs flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <Printer className="w-4 h-4 text-slate-500" />
            <span>Print Summary</span>
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Generate Report</span>
          </button>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reports.map((report) => (
          <div
            key={report.id}
            className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-xs hover:border-emerald-300 card-hover transition-all flex flex-col justify-between space-y-5 group"
          >
            <div className="flex items-start gap-4">
              <div className="p-3.5 bg-emerald-50 text-emerald-600 rounded-2xl flex-shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                <FileText className="w-6 h-6" />
              </div>
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-700 transition-colors">
                    {report.title}
                  </h3>
                  <span className="px-2.5 py-0.5 text-[10px] font-bold font-mono uppercase rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                    {report.format}
                  </span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  {report.description}
                </p>
                <div className="flex items-center gap-3 text-xs text-slate-400 font-mono pt-2">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    {report.generatedDate}
                  </span>
                  <span>• {report.fileSize}</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleDownload(report)}
              disabled={downloadingId === report.id}
              className="w-full py-3 bg-slate-900 hover:bg-emerald-600 text-white rounded-2xl text-xs font-bold shadow-xs flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer disabled:opacity-50"
            >
              {downloadingId === report.id ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Preparing Document...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download {report.format} File</span>
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      {/* Generate Report Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Generate Custom Class Report"
        subtitle="Select analysis category, cohort, and export format"
      >
        <form onSubmit={handleCreateReport} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Report Title</label>
            <input
              type="text"
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              placeholder="e.g. Mid-Term Comprehensive Algorithmic Mastery Report"
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Report Category</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value as any)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium cursor-pointer"
              >
                <option value="Performance">Class Performance</option>
                <option value="Assignment">Assignment Analysis</option>
                <option value="Topic">Topic Mastery Heatmap</option>
                <option value="At-Risk">At-Risk Intervention</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Export Format</label>
              <select
                value={reportFormat}
                onChange={(e) => setReportFormat(e.target.value as any)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium cursor-pointer"
              >
                <option value="PDF">PDF (Visual Document)</option>
                <option value="CSV">CSV (Spreadsheet Data)</option>
                <option value="XLSX">XLSX (Workbook)</option>
              </select>
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
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-95 cursor-pointer"
            >
              Generate & Save
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
