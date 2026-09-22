import { User, Bell, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';

const SettingsPage = ({ role }) => {
  const { user } = useAuth();
  
  const displayName = user?.name || user?.username || (role === 'student' ? "Student User" : "Instructor User");
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto space-y-6"
    >
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Account Settings</h1>
        <p className="text-slate-500 text-sm mt-1">Manage your account preferences and configurations.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col md:flex-row min-h-[450px] hover:shadow-md transition-shadow">
        <div className="w-full md:w-56 bg-slate-50 border-r border-slate-200 p-6 space-y-2">
          <motion.button whileHover={{ scale: 1.02, x: 2 }} whileTap={{ scale: 0.98 }} className="w-full flex items-center px-4 py-2.5 bg-indigo-50 text-indigo-700 font-medium rounded-xl text-sm transition-colors shadow-sm shadow-indigo-100/50">
            <User className="w-4 h-4 mr-3" /> Profile
          </motion.button>
          <motion.button whileHover={{ scale: 1.02, x: 2 }} whileTap={{ scale: 0.98 }} className="w-full flex items-center px-4 py-2.5 text-slate-600 hover:bg-slate-100 font-medium rounded-xl text-sm transition-colors">
            <Bell className="w-4 h-4 mr-3" /> Notifications
          </motion.button>
          <motion.button whileHover={{ scale: 1.02, x: 2 }} whileTap={{ scale: 0.98 }} className="w-full flex items-center px-4 py-2.5 text-slate-600 hover:bg-slate-100 font-medium rounded-xl text-sm transition-colors">
            <Shield className="w-4 h-4 mr-3" /> Privacy
          </motion.button>
        </div>

        <div className="flex-1 p-8">
          <h2 className="text-base font-bold text-slate-800 mb-6 border-b border-slate-100 pb-2">Profile Information</h2>
          <form className="space-y-4 max-w-md">
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
              <label className="block text-xs font-medium text-slate-700 mb-1">Full Name</label>
              <input 
                type="text" 
                defaultValue={displayName}
                className="w-full bg-white border border-slate-300 rounded-lg py-2 px-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
              />
            </motion.div>
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
              <label className="block text-xs font-medium text-slate-700 mb-1">Institution</label>
              <input 
                type="text" 
                defaultValue="Keshav Memorial Institute of Technology"
                className="w-full bg-white border border-slate-300 rounded-lg py-2 px-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
              />
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="pt-2">
              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} type="button" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors">
                Save Changes
              </motion.button>
            </motion.div>
          </form>
        </div>
      </div>
    </motion.div>
  );
};

export default SettingsPage;
