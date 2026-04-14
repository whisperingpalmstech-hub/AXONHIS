'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  PlusCircle, 
  FileText, 
  Download, 
  PieChart as PieChartIcon, 
  TrendingUp, 
  ArrowRight,
  BookOpen,
  Settings,
  MoreVertical,
  Search,
  Calendar,
  Wallet,
  Printer
} from 'lucide-react';
import { TopNav } from "@/components/ui/TopNav";
import { api } from "@/lib/api";

export default function AccountingDashboard() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({ 
    start: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const data = await api.get<any[]>('/accounting/journals');
      setEntries(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch journal entries:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, []);

  const exportTally = async () => {
    try {
      const data = await api.get<any>(`/accounting/export/tally?start_date=${dateRange.start}T00:00:00Z&end_date=${dateRange.end}T23:59:59Z`);
      const blob = new Blob([data.data], { type: 'text/xml' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename || `tally_export.xml`;
      a.click();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <TopNav title="Accounting Dashboard" />
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight uppercase">Accounting Central</h1>
            <p className="text-slate-500 font-medium ml-0.5">Unified Ledger, Journals & ERP Synchronization</p>
          </div>
          <div className="flex items-center gap-3">
            <Link 
              href="/dashboard/accounting/chart-of-accounts"
              className="px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all border border-slate-200 shadow-sm flex items-center gap-2"
            >
              <BookOpen className="w-4 h-4 text-slate-400" />
              Chart of Accounts
            </Link>
            <Link 
              href="/dashboard/accounting/new-journal"
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all shadow-lg shadow-blue-600/20 flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              New Journal Entry
            </Link>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white border border-slate-200 p-6 rounded-3xl relative overflow-hidden group shadow-sm">
            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Pending Journals</p>
            <div className="flex items-end justify-between mt-2">
              <h3 className="text-3xl font-black text-slate-900">
                {Array.isArray(entries) ? entries.filter(e => e.status === 'DRAFT').length : 0}
              </h3>
              <span className="text-amber-600 bg-amber-50 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-tighter border border-amber-100">Action Required</span>
            </div>
          </div>
          
          <div className="bg-white border border-slate-200 p-6 rounded-3xl relative overflow-hidden group shadow-sm">
            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Monthly Credits</p>
            <div className="flex items-end justify-between mt-2">
              <h3 className="text-3xl font-black text-slate-900">
                ₹ {Array.isArray(entries) ? entries.filter(e => e.status === 'POSTED').reduce((acc, curr) => acc + parseFloat(curr.total_credit), 0).toLocaleString() : '0.00'}
              </h3>
              <span className="text-emerald-600 font-black text-[10px] uppercase tracking-tight flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> +12.5% vs Prev.
              </span>
            </div>
          </div>

          <div className="bg-white border border-slate-200 p-6 rounded-3xl relative overflow-hidden group shadow-sm">
            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">ERP Status</p>
            <div className="flex items-end justify-between mt-2">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.6)]" />
                <h3 className="text-xl font-black text-slate-800 uppercase tracking-tighter">Connected</h3>
              </div>
              <div className="flex gap-2">
                <button 
                  onClick={exportTally}
                  className="px-3 py-1.5 bg-slate-900 border border-slate-800 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-blue-600/10 transition-all flex items-center gap-1.5 hover:bg-slate-800 active:scale-95"
                  title="Download Tally ERP9 XML"
                >
                  <Download className="w-3.3 h-3.3" /> Tally ERP.9
                </button>
                <button 
                  onClick={() => window.print()}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-blue-600/20 transition-all flex items-center gap-1.5 active:scale-95"
                  title="Generate PDF Report"
                >
                  <FileText className="w-3.3 h-3.3" /> Download PDF
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Transaction Table Section */}
        <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm flex-1 flex flex-col">
          <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-50/50">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider">Recent Journal Vouchers</h3>
            </div>
            <div className="flex items-center gap-2">
                 <button 
                  onClick={() => window.print()}
                  className="p-2 bg-white border border-slate-200 rounded-xl text-slate-400 hover:text-slate-600 shadow-sm transition-all"
                 >
                   <Printer className="w-4 h-4" />
                 </button>
                 <div className="flex items-center gap-2 bg-white border border-slate-200 px-3 py-1.5 rounded-xl shadow-sm">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <input 
                    type="date" 
                    className="bg-transparent text-[10px] text-slate-700 outline-none font-bold"
                    value={dateRange.start}
                    onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                  />
                  <span className="text-slate-300 font-black text-[10px]">TO</span>
                  <input 
                    type="date" 
                    className="bg-transparent text-[10px] text-slate-700 outline-none font-bold"
                    value={dateRange.end}
                    onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                  />
               </div>
               <button className="p-2 bg-white border border-slate-200 rounded-xl text-slate-400 hover:text-slate-600 shadow-sm transition-all">
                 <Search className="w-4 h-4" />
               </button>
            </div>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50/50 text-slate-400 text-[10px] font-black uppercase tracking-widest border-b border-slate-100">
                  <th className="px-8 py-5">Voucher #</th>
                  <th className="px-8 py-5">Date</th>
                  <th className="px-8 py-5">Description</th>
                  <th className="px-8 py-5 text-right">Debit</th>
                  <th className="px-8 py-5 text-right">Credit</th>
                  <th className="px-8 py-5 text-center">Status</th>
                  <th className="px-8 py-5 text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr><td colSpan={7} className="px-8 py-20 text-center text-slate-400 font-medium">Quantifying Ledger Accounts...</td></tr>
                ) : !Array.isArray(entries) || entries.length === 0 ? (
                  <tr><td colSpan={7} className="px-8 py-20 text-center text-slate-400 italic">No transactions recorded for this period.</td></tr>
                ) : entries.map(entry => (
                  <tr key={entry.id} className="group hover:bg-slate-50/50 transition-all duration-300">
                    <td className="px-8 py-4 font-mono text-xs font-bold text-blue-600">{entry.entry_number}</td>
                    <td className="px-8 py-4 text-xs font-bold text-slate-500">{new Date(entry.entry_date).toLocaleDateString()}</td>
                    <td className="px-8 py-4">
                      <p className="text-xs font-bold text-slate-700 truncate max-w-xs">{entry.description}</p>
                    </td>
                    <td className="px-8 py-4 text-right font-mono text-xs font-black text-emerald-600">₹ {parseFloat(entry.total_debit).toLocaleString()}</td>
                    <td className="px-8 py-4 text-right font-mono text-xs font-black text-slate-900">₹ {parseFloat(entry.total_credit).toLocaleString()}</td>
                    <td className="px-8 py-4 text-center">
                      <span className={`text-[10px] font-black uppercase px-2.5 py-1 rounded-lg border shadow-sm ${
                        entry.status === 'POSTED' 
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
                        : 'bg-amber-50 text-amber-700 border-amber-100'
                      }`}>
                        {entry.status}
                      </span>
                    </td>
                    <td className="px-8 py-4 text-right">
                       <button className="p-2 text-slate-300 hover:text-slate-600 transition-all">
                         <MoreVertical className="w-4 h-4" />
                       </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-slate-400">
             <span>Showing most recent journal entries</span>
             <div className="flex gap-2">
               <button className="px-3 py-1 bg-white border border-slate-200 rounded-md hover:bg-slate-100">Prev</button>
               <button className="px-3 py-1 bg-white border border-slate-200 rounded-md hover:bg-slate-100">Next</button>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
