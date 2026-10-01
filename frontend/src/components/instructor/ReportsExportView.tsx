import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  Download,
  Calendar,
  Printer,
  Plus
} from 'lucide-react';
import { useAuth } from '../../context/useAuth';
import { Modal } from '../common/Modal';

type Course = { id: number; course_code: string; title: string };

export const ReportsExportView: React.FC = () => {
  const { authFetch } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCourseId, setSelectedCourseId] = useState<string>('');

  useEffect(() => {
    authFetch('/api/instructor/courses')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setCourses(data);
      })
      .catch(console.error);
  }, [authFetch]);

  const handleDownload = async (courseId: number) => {
    setDownloadingId(courseId);
    try {
      const response = await authFetch(`/api/instructor/courses/${courseId}/export`);
      if (!response.ok) throw new Error('Export failed');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Course_${courseId}_Export.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download export');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleCreateReport = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;
    setIsModalOpen(false);
    handleDownload(Number(selectedCourseId));
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Institutional Reports & Exports
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Export cohort grade distribution and concept breakdown CSVs.
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
            <span>Export Course CSV</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {courses.map((course) => (
          <div
            key={course.id}
            className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-xs hover:border-emerald-300 card-hover transition-all flex flex-col justify-between space-y-5 group"
          >
            <div className="flex items-start gap-4">
              <div className="p-3.5 bg-emerald-50 text-emerald-600 rounded-2xl flex-shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-700 transition-colors">
                    {course.title}
                  </h3>
                  <span className="px-2.5 py-0.5 text-[10px] font-bold font-mono uppercase rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                    CSV
                  </span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  {course.course_code} Full Analytics Export
                </p>
                <div className="flex items-center gap-3 text-xs text-slate-400 font-mono pt-2">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    {new Date().toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleDownload(course.id)}
              disabled={downloadingId === course.id}
              className="w-full py-3 bg-slate-900 hover:bg-emerald-600 text-white rounded-2xl text-xs font-bold shadow-xs flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-95 cursor-pointer disabled:opacity-50"
            >
              {downloadingId === course.id ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Preparing CSV...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download CSV</span>
                </>
              )}
            </button>
          </div>
        ))}
        {courses.length === 0 && (
          <div className="col-span-1 md:col-span-2 text-center py-12 text-slate-500">
            No active courses found to export.
          </div>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Export Course Analytics"
        subtitle="Download a full CSV of student performance for a specific course."
      >
        <form onSubmit={handleCreateReport} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Select Course</label>
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 font-medium cursor-pointer"
            >
              <option value="" disabled>Select a course</option>
              {courses.map(c => (
                <option key={c.id} value={String(c.id)}>{c.course_code} - {c.title}</option>
              ))}
            </select>
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
              Export CSV
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
