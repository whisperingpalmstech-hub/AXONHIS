'use client';

import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  PieChart as PieChartIcon, 
  ArrowUpRight, 
  ArrowDownRight, 
  Calendar, 
  Printer, 
  Download,
  Wallet,
  Building2,
  Scale
} from 'lucide-react';
import { TopNav } from "@/components/ui/TopNav";
import { api } from "@/lib/api";

export default function FinancialReportsPage() {
  const [activeTab, setActiveTab] = useState<'pnl' | 'bs' | 'trial'>('pnl');
  const [pnlData, setPnlData] = useState<any>(null);
  const [bsData, setBsData] = useState<any>(null);
  const [trialData, setTrialData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'pnl') {
        const data = await api.get<any>(`/accounting/reports/profit-and-loss?start_date=${dateRange.start}&end_date=${dateRange.end}`);
        setPnlData(data);
      } else if (activeTab === 'bs') {
        const data = await api.get<any>(`/accounting/reports/balance-sheet`);
        setBsData(data);
      } else {
        const data = await api.get<any[]>(`/accounting/reports/trial-balance`);
        setTrialData(data);
      }
    } catch (error) {
      console.error('Failed to fetch report data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab, dateRange]);

  const renderPnL = () => {
    if (!pnlData) return null;
    return (
      <div className="space-y-6 animate-in fade-in duration-500">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Revenue */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-emerald-50 flex justify-between items-center">
               <h3 className="text-emerald-700 font-bold flex items-center gap-2">
                 <ArrowUpRight className="w-4 h-4" /> REVENUE
               </h3>
               <span className="text-xl font-black text-slate-900">₹ {(pnlData?.total_revenue || 0).toLocaleString()}</span>
            </div>
            <div className="p-5 space-y-3">
               {(pnlData?.revenue || []).map((item: any, i: number) => (
                 <div key={i} className="flex justify-between items-center group">
                   <span className="text-slate-600 font-medium">{item.name}</span>
                   <span className="font-mono text-slate-900 font-bold">₹ {item.amount.toLocaleString()}</span>
                 </div>
               ))}
               {(pnlData?.revenue?.length || 0) === 0 && <p className="text-slate-400 italic text-sm">No revenue recognized in this period.</p>}
            </div>
          </div>

          {/* Expenses */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 bg-rose-50 flex justify-between items-center">
               <h3 className="text-rose-700 font-bold flex items-center gap-2">
                 <ArrowDownRight className="w-4 h-4" /> OPERATING EXPENSES
               </h3>
               <span className="text-xl font-black text-slate-900">₹ {(pnlData?.total_expense || 0).toLocaleString()}</span>
            </div>
            <div className="p-5 space-y-3">
               {(pnlData?.expense || []).map((item: any, i: number) => (
                 <div key={i} className="flex justify-between items-center group">
                   <span className="text-slate-600 font-medium">{item.name}</span>
                   <span className="font-mono text-slate-900 font-bold">₹ {item.amount.toLocaleString()}</span>
                 </div>
               ))}
               {(pnlData?.expense?.length || 0) === 0 && <p className="text-slate-400 italic text-sm">No expenses recorded in this period.</p>}
            </div>
          </div>
        </div>

        {/* Net Profit Banner */}
        <div className={`p-6 rounded-2xl border flex justify-between items-center ${(pnlData?.net_profit || 0) >= 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'}`}>
           <div>
             <h4 className="text-slate-500 font-bold uppercase tracking-widest text-xs">Net {(pnlData?.net_profit || 0) >= 0 ? 'Profit' : 'Loss'} for Period</h4>
             <p className="text-slate-400 text-xs">{new Date(dateRange.start).toLocaleDateString()} to {new Date(dateRange.end).toLocaleDateString()}</p>
           </div>
           <div className="text-right">
             <span className={`text-4xl font-black ${(pnlData?.net_profit || 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
               ₹ {(pnlData?.net_profit || 0).toLocaleString()}
             </span>
             <p className="text-[10px] font-bold text-slate-400 mt-1 uppercase tracking-tight">Financial Position Adjusted</p>
           </div>
        </div>
      </div>
    );
  };

  const renderBS = () => {
    if (!bsData) return null;
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in slide-in-from-right-5 duration-500">
        <div className="space-y-6">
           <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6">
             <h3 className="text-blue-700 font-black flex items-center gap-2 mb-6 border-b border-slate-100 pb-4 uppercase tracking-wider text-sm">
               <ArrowUpRight className="w-4 h-4" /> Assets
             </h3>
             <div className="space-y-3">
                {(bsData?.assets || []).map((item: any, i: number) => (
                  <div key={i} className="flex justify-between items-center group">
                    <span className="text-slate-600 font-bold uppercase text-[10px] tracking-widest">{item.name}</span>
                    <span className="font-mono text-slate-900 font-bold">₹ {item.amount.toLocaleString()}</span>
                  </div>
                ))}
                <div className="pt-4 mt-6 border-t border-slate-100 flex justify-between">
                  <span className="text-slate-800 font-black uppercase text-xs">Total Assets</span>
                  <span className="text-blue-700 font-black">₹ {(bsData?.total_assets || 0).toLocaleString()}</span>
                </div>
             </div>
           </div>
        </div>
        <div className="space-y-6">
           <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6">
             <h3 className="text-rose-700 font-black flex items-center gap-2 mb-6 border-b border-slate-100 pb-4 uppercase tracking-wider text-sm">
               <ArrowDownRight className="w-4 h-4" /> Liabilities
             </h3>
             <div className="space-y-3">
                {(bsData?.liabilities || []).map((item: any, i: number) => (
                  <div key={i} className="flex justify-between items-center group">
                    <span className="text-slate-600 font-bold uppercase text-[10px] tracking-widest">{item.name}</span>
                    <span className="font-mono text-slate-900 font-bold">₹ {item.amount.toLocaleString()}</span>
                  </div>
                ))}
                <div className="pt-4 mt-6 border-t border-slate-100 flex justify-between">
                  <span className="text-slate-800 font-black uppercase text-xs">Total Liabilities</span>
                  <span className="text-rose-700 font-black">₹ {(bsData?.total_liabilities || 0).toLocaleString()}</span>
                </div>
             </div>
           </div>
           
           <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-6 shadow-sm">
             <h3 className="text-indigo-800 font-black flex items-center gap-2 mb-6 border-b border-indigo-200/50 pb-4 uppercase tracking-wider text-sm">
               <Scale className="w-4 h-4" /> Equity
             </h3>
             <div className="space-y-3">
                {(bsData?.equity || []).map((item: any, i: number) => (
                  <div key={i} className="flex justify-between items-center group">
                    <span className="text-slate-700 font-bold uppercase text-[10px] tracking-widest">{item.name}</span>
                    <span className="font-mono text-indigo-900 font-bold">₹ {item.amount.toLocaleString()}</span>
                  </div>
                ))}
                <div className="pt-4 mt-6 border-t border-indigo-200 flex justify-between">
                  <span className="text-indigo-900 font-black uppercase text-xs">Total Equity</span>
                  <span className="text-indigo-700 font-black">₹ {(bsData?.total_equity || 0).toLocaleString()}</span>
                </div>
             </div>
           </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <TopNav title="Financial Intelligence" />
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
              <BarChart3 className="text-blue-600" size={32}/> Financial Reports
            </h1>
            <p className="text-slate-500 font-medium ml-11">Profit & Loss • Balance Sheet • Trial Balance</p>
          </div>
          <div className="flex items-center gap-3">
             {activeTab === 'pnl' && (
               <div className="flex items-center gap-2 bg-white border border-slate-200 px-4 py-2 rounded-xl shadow-sm">
                 <Calendar className="w-4 h-4 text-slate-400" />
                 <input 
                   type="date" 
                   className="bg-transparent text-xs text-slate-700 outline-none font-bold"
                   value={dateRange.start}
                   onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                 />
                 <span className="text-slate-300 font-black text-[10px]">TO</span>
                 <input 
                   type="date" 
                   className="bg-transparent text-xs text-slate-700 outline-none font-bold"
                   value={dateRange.end}
                   onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                 />
               </div>
             )}
             <button 
               onClick={() => window.print()}
               className="p-2.5 bg-white hover:bg-slate-50 text-slate-500 rounded-xl border border-slate-200 transition-all shadow-sm"
               title="Print Report"
             >
               <Printer className="w-5 h-5" />
             </button>
             <button 
               onClick={() => {
                 const data = activeTab === 'pnl' ? pnlData : activeTab === 'bs' ? bsData : trialData;
                 const headers = activeTab === 'trial' ? "Code,Account Name,Balance\n" : "Category,Amount\n";
                 let csvContent = "data:text/csv;charset=utf-8," + headers;
                 
                 if (Array.isArray(data)) {
                   data.forEach(row => {
                     csvContent += `${row.account_code},${row.account_name},${row.current_balance}\n`;
                   });
                 } else {
                   // P&L or BS map
                   Object.entries(data).forEach(([key, val]: any) => {
                     csvContent += `${key},${val}\n`;
                   });
                 }

                 const encodedUri = encodeURI(csvContent);
                 const link = document.createElement("a");
                 link.setAttribute("href", encodedUri);
                 link.setAttribute("download", `axonhis_report_${activeTab}.csv`);
                 document.body.appendChild(link);
                 link.click();
               }}
               className="p-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl shadow-md shadow-blue-600/20 transition-all"
               title="Download Professional CSV Template"
             >
               <Download className="w-5 h-5" />
             </button>
             <button 
               onClick={async () => {
                 try {
                   alert("Synchronizing General Ledger with Tally ERP. Compiling XML voucher payload...");
                   const response = await api.get<any>(`/accounting/export/tally?start_date=${dateRange.start}T00:00:00Z&end_date=${dateRange.end}T23:59:59Z`);
                   const xmlData = response.data;
                   const filename = response.filename || `axonhis_tally_sync.xml`;
                   const encodedUri = "data:text/xml;charset=utf-8," + encodeURIComponent(xmlData);
                   const link = document.createElement("a");
                   link.setAttribute("href", encodedUri);
                   link.setAttribute("download", filename);
                   document.body.appendChild(link);
                   link.click();
                 } catch (err) {
                   console.error("Tally sync failed:", err);
                   alert("Tally synchronization failed. Make sure you have posted Journal Entries in this period.");
                 }
               }}
               className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl shadow-lg shadow-slate-900/20 transition-all font-black text-[10px] tracking-widest uppercase flex items-center gap-2"
               title="Sync & Export to Tally ERP9 (XML)"
             >
               <Wallet className="w-4 h-4 text-emerald-400" /> Tally ERP Sync
             </button>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex gap-1.5 p-1.5 bg-white/50 backdrop-blur border border-slate-200 rounded-2xl w-fit shadow-sm">
          {[
            { id: "pnl", label: "Profit & Loss", icon: <BarChart3 className="w-4 h-4" /> },
            { id: "bs", label: "Balance Sheet", icon: <Building2 className="w-4 h-4" /> },
            { id: "trial", label: "Trial Balance", icon: <Wallet className="w-4 h-4" /> },
          ].map(tab => (
            <button 
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase transition-all ${
                activeTab === tab.id ? "bg-white text-blue-700 shadow-sm border border-slate-200/50" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* Dynamic Content area */}
        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center space-y-4">
             <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
             <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">Quantifying Ledgers...</p>
          </div>
        ) : (
          <div className="animate-in fade-in slide-in-from-bottom-2 duration-700">
            {activeTab === 'pnl' && renderPnL()}
            {activeTab === 'bs' && renderBS()}
            {activeTab === 'trial' && (
              <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
                 <table className="w-full text-left">
                   <thead>
                      <tr className="bg-slate-50/80 text-slate-500 text-[10px] font-black uppercase tracking-widest border-b border-slate-200">
                        <th className="px-6 py-4">Code</th>
                        <th className="px-6 py-4">Account Name</th>
                        <th className="px-6 py-4">Type</th>
                        <th className="px-6 py-4 text-right">Running Balance</th>
                      </tr>
                   </thead>
                   <tbody className="divide-y divide-slate-100 font-medium">
                      {(trialData || []).map((row, i) => (
                        <tr key={i} className="hover:bg-slate-50/50 transition-all">
                          <td className="px-6 py-4 font-mono text-blue-600 text-xs font-bold">{row.account_code}</td>
                          <td className="px-6 py-4 text-slate-800 font-bold">{row.account_name}</td>
                          <td className="px-6 py-4">
                            <span className="text-[10px] font-black uppercase tracking-widest bg-slate-100 border border-slate-200 px-2 py-1 rounded text-slate-500">
                              {row.account_type}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right font-mono text-slate-900 font-black">₹ {row.balance.toLocaleString()}</td>
                        </tr>
                      ))}
                      {(trialData || []).length === 0 && (
                        <tr><td colSpan={4} className="px-6 py-12 text-center text-slate-400 italic">No ledger accounts found.</td></tr>
                      )}
                   </tbody>
                 </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
