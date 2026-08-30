import React, { useState } from 'react';
import {
  FileSpreadsheet,
  Download,
  FileText,
  Calendar,
  CheckCircle,
  Sparkles,
  Printer
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { ReportItem } from '../../types';

export const ReportsExportView: React.FC = () => {
  const { reports } = useApp();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownload = (report: ReportItem) => {
    setDownloadingId(report.id);
    setTimeout(() => {
      setDownloadingId(null);
      // create synthetic download link
      const element = document.createElement('a');
      const file = new Blob([`Report: ${report.title}\nGenerated: ${report.generatedDate}\nAI Assessment Engine v2.4\nStatus: Verified`], {
        type: 'text/plain'
      });
      element.href = URL.createObjectURL(file);
      element.download = `${report.title.replace(/\s+/g, '_')}_2026.${report.format.toLowerCase()}`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }, 1000);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Institutional Reports & Analytics Exports
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Export accreditation documents, cohort grade distribution PDFs, and concept breakdown CSVs.
          </p>
        </div>

        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-bold border border-slate-200 shadow-xs flex items-center gap-2 transition-colors"
        >
          <Printer className="w-4 h-4 text-slate-500" />
          <span>Print Summary</span>
        </button>
      </div>

      {/* Reports Grid (Matches Step 5 in diagram) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {reports.map((report) => (
          <div
            key={report.id}
            className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs hover:border-indigo-300 transition-all flex flex-col justify-between space-y-4 group"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl flex-shrink-0 group-hover:scale-105 transition-transform">
                <FileText className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900">{report.title}</h3>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-slate-100 text-slate-700">
                    {report.format}
                  </span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  {report.description}
                </p>
                <div className="flex items-center gap-3 text-xs text-slate-400 font-mono pt-2">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {report.generatedDate}
                  </span>
                  <span>• {report.fileSize}</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleDownload(report)}
              disabled={downloadingId === report.id}
              className="w-full py-2.5 bg-slate-900 hover:bg-indigo-600 text-white rounded-xl text-xs font-bold shadow-xs flex items-center justify-center gap-2 transition-colors cursor-pointer disabled:opacity-50"
            >
              {downloadingId === report.id ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Preparing Document...</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Download {report.format}</span>
                </>
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
