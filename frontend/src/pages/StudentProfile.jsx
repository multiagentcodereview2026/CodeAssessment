import { Mail, MapPin, Building, Calendar, Edit } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const StudentProfile = () => {
  const { user } = useAuth();
  
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Student Profile</h1>
        <p className="text-slate-500 text-sm mt-1">Manage your personal and academic information.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="h-28 bg-indigo-600 relative"></div>
        
        <div className="px-8 pb-8 relative">
          <div className="flex justify-between items-end mb-6 -mt-10">
            <div className="w-20 h-20 bg-white rounded-full p-1 shadow-md">
              <div className="w-full h-full bg-indigo-100 rounded-full flex items-center justify-center text-2xl font-bold text-indigo-700">
                {user?.name?.charAt(0) || 'S'}
              </div>
            </div>
            <button className="px-4 py-2 bg-indigo-50 text-indigo-600 font-medium rounded-lg text-sm hover:bg-indigo-100 transition-colors">
              Edit Profile
            </button>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-800">{user?.name || 'Student'} ({user?.id || '24BD1A058Z'})</h2>
            <div className="flex items-center text-slate-500 text-xs mt-1 space-x-4">
              <span className="flex items-center"><Mail className="w-3.5 h-3.5 mr-1" /> {user?.email || 'student@kmit.in'}</span>
              <span className="flex items-center"><MapPin className="w-3.5 h-3.5 mr-1" /> Hyderabad, India</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-800 border-b border-slate-100 pb-2 text-sm">Academic Details</h3>
              <div className="grid grid-cols-2 gap-y-3 text-xs">
                <div className="text-slate-500">Roll Number</div>
                <div className="font-medium text-slate-800">{user?.id || '24BD1A058Z'}</div>
                
                <div className="text-slate-500">Institution</div>
                <div className="font-medium text-slate-800">Keshav Memorial Institute of Technology</div>
                
                <div className="text-slate-500">Department</div>
                <div className="font-medium text-slate-800">Computer Science & Engineering</div>
                
                <div className="text-slate-500">Year</div>
                <div className="font-medium text-slate-800">2nd Year</div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold text-slate-800 border-b border-slate-100 pb-2 text-sm">Achievements</h3>
              <div className="flex flex-wrap gap-2">
                <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-lg text-xs font-medium">🏆 Top 10% Class</span>
                <span className="px-2.5 py-1 bg-purple-50 text-purple-700 border border-purple-100 rounded-lg text-xs font-medium">🔥 7 Day Streak</span>
                <span className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-100 rounded-lg text-xs font-medium">⭐ 24 Solved</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentProfile;
