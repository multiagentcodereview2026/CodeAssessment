import { Mail, MapPin, Building, Calendar, Edit } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const StudentProfile = () => {
  const { user } = useAuth();
  
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <motion.div 
        initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-bold text-slate-800">Student Profile</h1>
        <p className="text-slate-500 text-sm mt-1">Manage your personal and academic information.</p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
        className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-lg transition-shadow duration-300"
      >
        <div className="h-28 bg-indigo-600 relative overflow-hidden">
          <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-white via-transparent to-transparent"></div>
        </div>
        
        <div className="px-8 pb-8 relative">
          <div className="flex justify-between items-end mb-6 -mt-10">
            <motion.div 
              initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", delay: 0.3 }}
              className="w-20 h-20 bg-white rounded-full p-1 shadow-md"
            >
              <div className="w-full h-full bg-indigo-100 rounded-full flex items-center justify-center text-2xl font-bold text-indigo-700">
                {(user?.name || user?.username || 'S').charAt(0).toUpperCase()}
              </div>
            </motion.div>
            <motion.button 
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-indigo-50 text-indigo-600 font-medium rounded-lg text-sm hover:bg-indigo-100 transition-colors flex items-center"
            >
              <Edit className="w-3.5 h-3.5 mr-1.5" /> Edit Profile
            </motion.button>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-800">{user?.name || user?.username || 'Student'} ({user?.username || '24BD1A058Z'})</h2>
            <div className="flex items-center text-slate-500 text-xs mt-1 space-x-4">
              <span className="flex items-center"><Mail className="w-3.5 h-3.5 mr-1 text-slate-400" /> {user?.email || 'student@kmit.in'}</span>
              <span className="flex items-center"><MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" /> Hyderabad, India</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <motion.div 
              initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}
              className="space-y-4 bg-slate-50 p-5 rounded-xl border border-slate-100"
            >
              <h3 className="font-semibold text-slate-800 border-b border-slate-200 pb-2 text-sm flex items-center">
                <Building className="w-4 h-4 mr-2 text-indigo-500" /> Academic Details
              </h3>
              <div className="grid grid-cols-2 gap-y-3 text-xs">
                <div className="text-slate-500">Roll Number</div>
                <div className="font-medium text-slate-800">{user?.username || '24BD1A058Z'}</div>
                
                <div className="text-slate-500">Institution</div>
                <div className="font-medium text-slate-800">Keshav Memorial Institute of Technology</div>
                
                <div className="text-slate-500">Department</div>
                <div className="font-medium text-slate-800">Computer Science & Engineering</div>
                
                <div className="text-slate-500">Year</div>
                <div className="font-medium text-slate-800">2nd Year</div>
              </div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }}
              className="space-y-4 bg-slate-50 p-5 rounded-xl border border-slate-100"
            >
              <h3 className="font-semibold text-slate-800 border-b border-slate-200 pb-2 text-sm flex items-center">
                <Calendar className="w-4 h-4 mr-2 text-emerald-500" /> Achievements
              </h3>
              <div className="flex flex-wrap gap-2 pt-1">
                <span className="px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-lg text-xs font-medium shadow-sm flex items-center cursor-default hover:bg-emerald-100 transition-colors">🏆 Top 10% Class</span>
                <span className="px-3 py-1.5 bg-purple-50 text-purple-700 border border-purple-100 rounded-lg text-xs font-medium shadow-sm flex items-center cursor-default hover:bg-purple-100 transition-colors">🔥 7 Day Streak</span>
                <span className="px-3 py-1.5 bg-amber-50 text-amber-700 border border-amber-100 rounded-lg text-xs font-medium shadow-sm flex items-center cursor-default hover:bg-amber-100 transition-colors">⭐ 24 Solved</span>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default StudentProfile;
