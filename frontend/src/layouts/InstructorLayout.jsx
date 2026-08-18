import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, BookOpen, FileText, Settings, Bell, LogOut, ChevronDown, GraduationCap, BarChart3 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const InstructorLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const navItems = [
    { name: 'Dashboard', path: '/instructor/dashboard', icon: LayoutDashboard },
    { name: 'Courses', path: '/instructor/courses', icon: BookOpen },
    { name: 'Students', path: '/instructor/students', icon: Users },
    { name: 'Assignments', path: '/instructor/assignments', icon: FileText },
    { name: 'Reports', path: '/instructor/reports', icon: BarChart3 },
    { name: 'Settings', path: '/instructor/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar Navigation */}
      <nav className="w-64 bg-white border-r border-slate-200 fixed h-full flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-200">
          <div className="bg-emerald-600 p-1.5 rounded-lg mr-2">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-slate-800 tracking-tight">Kod<span className="text-emerald-600">acharya</span></span>
        </div>
        
        <div className="flex-1 py-6 px-4 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive 
                    ? 'bg-emerald-50 text-emerald-700 shadow-sm shadow-emerald-100/50' 
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <item.icon className={`w-4 h-4 mr-3 ${isActive ? 'text-emerald-600' : 'text-slate-400'}`} />
                {item.name}
              </Link>
            );
          })}
        </div>

        <div className="p-4 border-t border-slate-200">
          <button 
            onClick={handleLogout}
            className="flex w-full items-center px-3 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-red-600 transition-colors"
          >
            <LogOut className="w-4 h-4 mr-3 text-slate-400" />
            Sign Out
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="ml-64 flex-1 flex flex-col min-h-screen">
        <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="text-sm font-medium text-slate-500">
            {navItems.find(item => location.pathname.startsWith(item.path))?.name || 'Overview'}
          </div>
          
          <div className="flex items-center space-x-5">
            <button className="relative text-slate-400 hover:text-slate-600 transition-colors">
              <Bell className="w-5 h-5" />
            </button>
            <div className="h-6 w-px bg-slate-200"></div>
            <div className="flex items-center cursor-pointer group">
              <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold text-sm shadow-inner mr-2">
                {user?.name?.charAt(0) || 'I'}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-slate-700 group-hover:text-emerald-600 transition-colors">{user?.name || 'Instructor'}</span>
                <span className="text-[10px] font-medium text-slate-400">Faculty Portal</span>
              </div>
              <ChevronDown className="w-4 h-4 ml-2 text-slate-400" />
            </div>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto relative">
          <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-emerald-50/50 to-transparent -z-10 pointer-events-none"></div>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default InstructorLayout;
