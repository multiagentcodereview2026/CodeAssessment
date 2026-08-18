import { Search, Filter, Eye } from 'lucide-react';

const InstructorTablePage = ({ title, description, columns, data }) => {
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
          <p className="text-slate-500 text-sm mt-1">{description}</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
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
              <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                {Object.values(row).map((val, vIdx) => (
                  <td key={vIdx} className={`px-6 py-4 ${vIdx === 0 ? 'font-medium text-slate-800' : 'text-slate-600'}`}>
                    {val}
                  </td>
                ))}
                <td className="px-6 py-4 text-right">
                  <button className="text-emerald-600 hover:text-emerald-800 font-medium text-sm inline-flex items-center">
                    <Eye className="w-4 h-4 mr-1" /> View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default InstructorTablePage;
