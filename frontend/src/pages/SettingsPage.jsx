import { User, Bell, Shield, Key } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const SettingsPage = ({ role }) => {
  const { user } = useAuth();
  
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Account Settings</h1>
        <p className="text-slate-500 text-sm mt-1">Manage your account preferences and configurations.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col md:flex-row min-h-[450px]">
        <div className="w-full md:w-56 bg-slate-50 border-r border-slate-200 p-6 space-y-1">
          <button className="w-full flex items-center px-4 py-2.5 bg-indigo-50 text-indigo-700 font-medium rounded-xl text-sm">
            <User className="w-4 h-4 mr-3" /> Profile
          </button>
          <button className="w-full flex items-center px-4 py-2.5 text-slate-600 hover:bg-slate-100 font-medium rounded-xl text-sm">
            <Bell className="w-4 h-4 mr-3" /> Notifications
          </button>
          <button className="w-full flex items-center px-4 py-2.5 text-slate-600 hover:bg-slate-100 font-medium rounded-xl text-sm">
            <Shield className="w-4 h-4 mr-3" /> Privacy
          </button>
        </div>

        <div className="flex-1 p-8">
          <h2 className="text-base font-bold text-slate-800 mb-6 border-b border-slate-100 pb-2">Profile Information</h2>
          <form className="space-y-4 max-w-md">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Full Name</label>
              <input 
                type="text" 
                defaultValue={user?.name || (role === 'student' ? "Vignesh" : "Prof. Smith")}
                className="w-full bg-white border border-slate-300 rounded-lg py-2 px-3 text-sm text-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Institution</label>
              <input 
                type="text" 
                defaultValue="Keshav Memorial Institute of Technology"
                className="w-full bg-white border border-slate-300 rounded-lg py-2 px-3 text-sm text-slate-800"
              />
            </div>
            <div className="pt-2">
              <button type="button" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm">
                Save Changes
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
