import React, { useEffect, useState } from 'react';
import {
  User,
  Mail,
  School,
  Building,
  Calendar,
  KeyRound,
  Edit3,
  Check,
  ShieldCheck,
  Award
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/useAuth';
import { Modal } from '../common/Modal';

export const StudentProfileView: React.FC = () => {
  const { currentUser } = useApp();
  const { user, updateAccount } = useAuth();
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [name, setName] = useState(currentUser.name);
  const [institution, setInstitution] = useState(currentUser.institution);
  const [department, setDepartment] = useState(currentUser.department);
  const [year, setYear] = useState(currentUser.year);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    setName(currentUser.name);
    setInstitution(currentUser.institution);
    setDepartment(currentUser.department);
    setYear(currentUser.year);
  }, [currentUser.name, currentUser.institution, currentUser.department, currentUser.year]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveError('');
    try {
      await updateAccount({
        full_name: name,
        institution,
        department,
        year
      });
      setSavedSuccess(true);
      window.setTimeout(() => {
        setSavedSuccess(false);
        setIsEditOpen(false);
      }, 800);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Unable to save your profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Student Profile
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage academic profile, institutional enrollment, and verified student credentials.
          </p>
        </div>

        <button
          onClick={() => setIsEditOpen(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>Edit Profile</span>
        </button>
      </div>

      {/* Main Profile Card (Matches diagram profile layout) */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
        {/* Banner */}
        <div className="h-32 bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 relative">
          <div className="absolute top-4 right-4 flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 backdrop-blur text-white text-xs font-semibold border border-white/20">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Academic Verification Active</span>
          </div>
        </div>

        {/* Profile info */}
        <div className="px-6 sm:px-8 pb-8 pt-0 relative">
          {/* Avatar */}
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 -mt-12 mb-6">
            <div className="flex items-end gap-4">
              <div className="w-24 h-24 rounded-2xl bg-indigo-600 border-4 border-white shadow-xl flex items-center justify-center text-white text-3xl font-extrabold select-none">
                V
              </div>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-slate-900">{currentUser.name}</h2>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-md">
                    Student
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-mono">{currentUser.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-mono bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
                Roll: <strong className="text-slate-800">{user?.username || currentUser.rollNumber}</strong>
              </span>
            </div>
          </div>

          {/* Institutional details grid (Matching diagram) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-100 text-xs">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-start gap-3">
              <div className="p-2 bg-indigo-100 text-indigo-700 rounded-xl">
                <KeyRound className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Roll Number
                </span>
                <span className="text-sm font-extrabold text-slate-800 font-mono mt-0.5 block">
                  {user?.username || currentUser.rollNumber}
                </span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-start gap-3">
              <div className="p-2 bg-emerald-100 text-emerald-700 rounded-xl">
                <School className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Institution
                </span>
                <span className="text-sm font-extrabold text-slate-800 mt-0.5 block">
                  {currentUser.institution}
                </span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-start gap-3">
              <div className="p-2 bg-purple-100 text-purple-700 rounded-xl">
                <Building className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Department
                </span>
                <span className="text-sm font-extrabold text-slate-800 mt-0.5 block">
                  {currentUser.department}
                </span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-start gap-3">
              <div className="p-2 bg-amber-100 text-amber-700 rounded-xl">
                <Calendar className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Academic Year
                </span>
                <span className="text-sm font-extrabold text-slate-800 mt-0.5 block">
                  {currentUser.year}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Profile Modal */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Edit Student Profile"
        subtitle="Update academic details and institutional records"
      >
        <form onSubmit={handleSave} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Institution</label>
            <input
              type="text"
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              required
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500"
            />
          </div>

          {saveError && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{saveError}</p>}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Department</label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                required
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block font-bold text-slate-700 mb-1">Academic Year</label>
              <input
                type="text"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                required
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsEditOpen(false)}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
            >
              {savedSuccess ? <Check className="w-4 h-4 text-emerald-300" /> : null}
              <span>{saving ? 'Saving…' : savedSuccess ? 'Saved!' : 'Save Changes'}</span>
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
