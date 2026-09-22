import { Eye } from 'lucide-react';
import { motion } from 'framer-motion';

const InstructorTablePage = ({ title, description, columns, data }) => {
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center mb-6"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
          <p className="text-slate-500 text-sm mt-1">{description}</p>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
      >
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
              <tr>
                {columns.map((col, idx) => (
                  <th key={idx} className="px-6 py-4 font-medium">{col}</th>
                ))}
                <th className="px-6 py-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <motion.tr 
                  key={idx} 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="border-b border-slate-100 hover:bg-slate-50 transition-colors group"
                >
                  {Object.values(row).map((val, vIdx) => (
                    <td key={vIdx} className={`px-6 py-4 ${vIdx === 0 ? 'font-medium text-slate-800 group-hover:text-indigo-600 transition-colors' : 'text-slate-600'}`}>
                      {val}
                    </td>
                  ))}
                  <td className="px-6 py-4 text-right">
                    <motion.button 
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="text-emerald-600 hover:text-emerald-800 font-medium text-sm inline-flex items-center transition-colors"
                    >
                      <Eye className="w-4 h-4 mr-1" /> View Details
                    </motion.button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
};

export default InstructorTablePage;
