'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Building2, 
  Wallet, 
  TrendingUp, 
  ArrowUpRight, 
  Plus, 
  Search, 
  ChevronRight,
  Filter,
  MoreVertical,
  BookOpen,
  Scale,
  X,
  AlertCircle
} from 'lucide-react';
import { TopNav } from "@/components/ui/TopNav";
import { api } from "@/lib/api";

interface Account {
  id: string;
  account_code: string;
  account_name: string;
  account_type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
  current_balance: string;
}

export default function ChartOfAccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  
  // Account Form State
  const [newAcc, setNewAcc] = useState({
    account_code: '',
    account_name: '',
    account_type: 'ASSET',
    description: ''
  });

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const data = await api.get<Account[]>('/accounting/accounts');
      setAccounts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleCreateOrUpdateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      if (editingId) {
        await api.put(`/accounting/accounts/${editingId}`, newAcc);
      } else {
        await api.post('/accounting/accounts', newAcc);
      }
      setShowModal(false);
      setEditingId(null);
      setNewAcc({ account_code: '', account_name: '', account_type: 'ASSET', description: '' });
      fetchAccounts();
    } catch (err: any) {
      setError(err.message || 'Failed to save account.');
      console.error('Failed to save account:', err);
    }
  };

  const startEdit = (acc: Account) => {
    setEditingId(acc.id);
    setNewAcc({
      account_code: acc.account_code,
      account_name: acc.account_name,
      account_type: acc.account_type,
      description: '' // Backend might not return description in list, we could fetch it if needed
    });
    setShowModal(true);
  };

  const handleStatusToggle = async (id: string, currentStatus: string) => {
    try {
      const newStatus = currentStatus === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
      await api.post(`/accounting/accounts/${id}/status`, { status: newStatus });
      fetchAccounts();
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const filteredAccounts = Array.isArray(accounts) ? accounts.filter(acc => 
    acc.account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    acc.account_code.includes(searchTerm)
  ) : [];

  const getAccountIcon = (type: string) => {
    switch(type) {
      case 'ASSET': return <Building2 className="w-4 h-4 text-blue-600" />;
      case 'LIABILITY': return <Wallet className="w-4 h-4 text-rose-600" />;
      case 'REVENUE': return <ArrowUpRight className="w-4 h-4 text-emerald-600" />;
      case 'EXPENSE': return <TrendingUp className="w-4 h-4 text-amber-600" />;
      default: return <Scale className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans relative">
      <TopNav title="Chart of Accounts" />
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
        
        {/* Header Section */}
        <div className="bg-white border border-slate-200 p-8 rounded-[2rem] shadow-sm flex flex-col md:flex-row justify-between items-center gap-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-600" />
          <div className="flex items-center gap-5 relative z-10">
            <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl shadow-inner">
              <BookOpen className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-slate-800 tracking-tighter uppercase">Chart of Accounts</h1>
              <p className="text-slate-500 font-medium tracking-tight">Manage your financial backbone and ledgers</p>
            </div>
          </div>
          <button 
            onClick={() => setShowModal(true)}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-[2rem] font-black uppercase text-[10px] tracking-[0.2em] transition-all shadow-lg shadow-blue-600/20 flex items-center gap-3 relative z-10 active:scale-95"
          >
            <Plus className="w-4 h-4" />
            Create New Account
          </button>
        </div>

        {/* Filters and Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-1">
            <div className="bg-slate-900 border border-slate-800 p-3 rounded-2xl flex items-center gap-3 focus-within:ring-2 focus-within:ring-blue-600 transition-all shadow-xl">
              <Search className="w-4 h-4 text-slate-500" />
              <input 
                type="text" 
                placeholder="Search code or name..." 
                className="bg-transparent text-sm text-white outline-none w-full font-bold"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm flex items-center gap-4">
             <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl"><Scale className="w-5 h-5" /></div>
             <div>
               <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Total Assets</p>
               <p className="text-sm font-black text-slate-800">{accounts.filter(a => a.account_type === 'ASSET').length} Accounts</p>
             </div>
          </div>
          <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm flex items-center gap-4">
             <div className="p-2 bg-blue-50 text-blue-600 rounded-xl"><ArrowUpRight className="w-5 h-5" /></div>
             <div>
               <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Revenue Stream</p>
               <p className="text-sm font-black text-slate-800">{accounts.filter(a => a.account_type === 'REVENUE').length} Accounts</p>
             </div>
          </div>
          <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm flex items-center gap-4">
             <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl"><Filter className="w-5 h-5" /></div>
             <div>
               <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Control Accounts</p>
               <p className="text-sm font-black text-slate-800">8 Groups</p>
             </div>
          </div>
        </div>

        {/* Ledger Table */}
        <div className="bg-white border border-slate-200 rounded-[2.5rem] overflow-hidden shadow-sm flex-1">
           <table className="w-full text-left">
             <thead>
               <tr className="bg-slate-50/80 text-slate-400 text-[10px] font-black uppercase tracking-widest border-b border-slate-200">
                 <th className="px-8 py-5">Code</th>
                 <th className="px-8 py-5">Account Name</th>
                 <th className="px-8 py-5">Type</th>
                 <th className="px-8 py-5 text-right">Balance</th>
                 <th className="px-8 py-5 text-center">Status</th>
                 <th className="px-8 py-5 text-right">Actions</th>
               </tr>
             </thead>
             <tbody className="divide-y divide-slate-100">
               {loading ? (
                 <tr><td colSpan={6} className="px-8 py-24 text-center text-slate-400 font-medium">Synchronizing Ledger with Database...</td></tr>
               ) : filteredAccounts.length === 0 ? (
                 <tr><td colSpan={6} className="px-8 py-24 text-center text-slate-400 italic">No accounts found. Start by creating one!</td></tr>
               ) : filteredAccounts.map(acc => (
                 <tr key={acc.id} className="group hover:bg-slate-50/50 transition-all duration-300">
                   <td className="px-8 py-4 font-mono text-xs font-bold text-slate-900 leading-none">{acc.account_code}</td>
                   <td className="px-8 py-4">
                     <span className="text-sm font-black text-slate-700 tracking-tight">{acc.account_name}</span>
                   </td>
                   <td className="px-8 py-4">
                     <div className="flex items-center gap-2">
                       {getAccountIcon(acc.account_type)}
                       <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mt-0.5">{acc.account_type}</span>
                     </div>
                   </td>
                   <td className="px-8 py-4 text-right font-mono text-sm font-black text-slate-900 leading-none">
                     ₹ {parseFloat(acc.current_balance).toLocaleString()}
                   </td>
                   <td className="px-8 py-4 text-center leading-none">
                     <span className={`text-[8px] font-black uppercase px-2 py-1 rounded-md border shadow-sm leading-none inline-block ${
                       acc.status === 'ACTIVE' 
                       ? 'bg-emerald-50 text-emerald-600 border-emerald-100' 
                       : 'bg-slate-100 text-slate-500 border-slate-200'
                     }`}>
                       {acc.status}
                     </span>
                   </td>
                   <td className="px-8 py-4 text-right leading-none relative group/item">
                     <button className="p-2 text-slate-300 hover:text-blue-600 transition-all leading-none focus:outline-none">
                       <MoreVertical className="w-4 h-4" />
                     </button>
                     <div className="absolute right-8 top-0 hidden group-hover/item:flex flex-col bg-white border border-slate-200 rounded-xl shadow-xl z-20 py-1 min-w-[140px] animate-in slide-in-from-right-1">
                        <Link 
                          href="/dashboard/accounting/reports"
                          className="px-4 py-2 text-[10px] font-black uppercase text-slate-600 hover:bg-slate-50 hover:text-blue-600 text-left transition-all"
                        >
                          View Ledger
                        </Link>
                        <button 
                          onClick={() => startEdit(acc)}
                          className="px-4 py-2 text-[10px] font-black uppercase text-slate-600 hover:bg-slate-50 hover:text-blue-600 text-left transition-all"
                        >
                          Edit Account
                        </button>
                        <button 
                          onClick={() => handleStatusToggle(acc.id, acc.status)}
                          className={`px-4 py-2 text-[10px] font-black uppercase text-left transition-all ${
                            acc.status === 'ACTIVE' ? 'text-rose-600 hover:bg-rose-50' : 'text-emerald-600 hover:bg-emerald-50'
                          }`}
                        >
                          {acc.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                        </button>
                     </div>
                   </td>
                 </tr>
               ))}
             </tbody>
           </table>
        </div>
      </div>

      {/* Account Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-[2.5rem] w-full max-w-lg shadow-2xl border border-slate-200 overflow-hidden animate-in zoom-in-95 duration-300">
             <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
               <div>
                 <h2 className="text-2xl font-black text-slate-800 uppercase tracking-tight">
                   {editingId ? 'Update Ledger Account' : 'New Ledger Account'}
                 </h2>
                 <p className="text-slate-500 text-xs font-medium">
                   {editingId ? 'Modify existing ledger details' : 'Define a new entry in the Chart of Accounts'}
                 </p>
               </div>
               <button onClick={() => { setShowModal(false); setEditingId(null); }} className="p-2.5 bg-white border border-slate-200 text-slate-400 rounded-xl hover:text-slate-600 transition-all">
                 <X className="w-5 h-5" />
               </button>
             </div>
             <form onSubmit={handleCreateOrUpdateAccount} className="p-8 space-y-5">
               {error && (
                 <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl flex items-center gap-3 text-rose-700 text-xs font-bold animate-in fade-in slide-in-from-top-1">
                   <AlertCircle className="w-4 h-4" />
                   {error}
                 </div>
               )}
               <div className="grid grid-cols-2 gap-4">
                 <div className="space-y-1.5">
                   <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Account Code</label>
                   <input 
                     required
                     className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold text-slate-800 outline-none focus:ring-2 focus:ring-blue-600"
                     placeholder="e.g. 1001"
                     value={newAcc.account_code}
                     onChange={e => setNewAcc({...newAcc, account_code: e.target.value})}
                   />
                 </div>
                 <div className="space-y-1.5">
                   <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Account Type</label>
                   <select 
                     className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold text-slate-800 outline-none focus:ring-2 focus:ring-blue-600"
                     value={newAcc.account_type}
                     onChange={e => setNewAcc({...newAcc, account_type: e.target.value as any})}
                   >
                     <option value="ASSET">ASSET</option>
                     <option value="LIABILITY">LIABILITY</option>
                     <option value="EQUITY">EQUITY</option>
                     <option value="REVENUE">REVENUE</option>
                     <option value="EXPENSE">EXPENSE</option>
                   </select>
                 </div>
               </div>
               <div className="space-y-1.5">
                 <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Account Name</label>
                 <input 
                   required
                   className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold text-slate-800 outline-none focus:ring-2 focus:ring-blue-600"
                   placeholder="e.g. Cash at Bank"
                   value={newAcc.account_name}
                   onChange={e => setNewAcc({...newAcc, account_name: e.target.value})}
                 />
               </div>
               <div className="space-y-1.5">
                 <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Description</label>
                 <textarea 
                   className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-medium text-slate-800 outline-none focus:ring-2 focus:ring-blue-600 h-24"
                   placeholder="Optional description..."
                   value={newAcc.description}
                   onChange={e => setNewAcc({...newAcc, description: e.target.value})}
                 />
               </div>
               <div className="flex justify-end gap-3 pt-4">
                 <button 
                  type="button"
                  onClick={() => { setShowModal(false); setEditingId(null); }}
                  className="px-6 py-3 text-[10px] font-black uppercase text-slate-400 hover:text-slate-600 transition-all"
                 >
                   Cancel
                 </button>
                 <button 
                  type="submit"
                  className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-black uppercase text-[10px] tracking-widest shadow-lg shadow-blue-600/20 transition-all active:scale-95"
                 >
                   {editingId ? 'Update Account' : 'Save Account'}
                 </button>
               </div>
             </form>
          </div>
        </div>
      )}
    </div>
  );
}
