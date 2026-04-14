'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Save, 
  X, 
  Plus, 
  Trash2, 
  AlertCircle, 
  CheckCircle2,
  Info,
  Layers,
  Calculator,
  Calendar
} from 'lucide-react';
import { TopNav } from "@/components/ui/TopNav";
import { api } from "@/lib/api";

interface Account {
  id: string;
  account_code: string;
  account_name: string;
}

interface JournalLine {
  account_id: string;
  description: string;
  debit_amount: string;
  credit_amount: string;
}

export default function NewJournalEntry() {
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [description, setDescription] = useState('');
  const [entryDate, setEntryDate] = useState(new Date().toISOString().split('T')[0]);
  const [lines, setLines] = useState<JournalLine[]>([
    { account_id: '', description: '', debit_amount: '0', credit_amount: '0' },
    { account_id: '', description: '', debit_amount: '0', credit_amount: '0' }
  ]);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const data = await api.get<Account[]>('/accounting/accounts');
        setAccounts(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Failed to fetch accounts:', err);
      }
    };
    fetchAccounts();
  }, []);

  const addLine = () => {
    setLines([...lines, { account_id: '', description: '', debit_amount: '0', credit_amount: '0' }]);
  };

  const removeLine = (index: number) => {
    if (lines.length <= 2) return;
    const newLines = [...lines];
    newLines.splice(index, 1);
    setLines(newLines);
  };

  const handleLineChange = (index: number, field: keyof JournalLine, value: string) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], [field]: value };
    setLines(newLines);
  };

  const totalDebit = lines.reduce((acc, curr) => acc + (parseFloat(curr.debit_amount) || 0), 0);
  const totalCredit = lines.reduce((acc, curr) => acc + (parseFloat(curr.credit_amount) || 0), 0);
  const difference = Math.abs(totalDebit - totalCredit);
  const isBalanced = difference < 0.01 && totalDebit > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isBalanced) {
      setError('Journal must be balanced (Total Debits must equal Total Credits).');
      return;
    }
    
    setIsSubmitting(true);
    setError('');

    try {
      const payload = {
        description,
        entry_date: entryDate,
        lines: lines.map(l => ({
          account_id: l.account_id,
          description: l.description,
          debit_amount: parseFloat(l.debit_amount) || 0,
          credit_amount: parseFloat(l.credit_amount) || 0
        }))
      };

      await api.post('/accounting/journals', payload);
      router.push('/dashboard/accounting');
    } catch (err: any) {
      setError(err.message || 'Failed to create journal entry.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <TopNav title="Journal Vouchers" />
      <div className="flex-1 p-8 max-w-6xl mx-auto w-full space-y-6">
        
        {/* Top Navigation & Status */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => router.back()}
              className="p-2.5 bg-white hover:bg-slate-50 rounded-xl text-slate-400 transition-all border border-slate-200 shadow-sm"
            >
              <X className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-3xl font-black text-slate-800 tracking-tight uppercase">New Journal Entry</h1>
              <p className="text-slate-500 font-medium">Record a manual double-entry transaction</p>
            </div>
          </div>
          
          <div className="bg-white border border-slate-200 px-6 py-4 rounded-2xl flex items-center gap-6 shadow-sm">
            <div className="text-center">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Total Debits</p>
              <p className="text-xl font-black text-emerald-600">₹ {totalDebit.toLocaleString()}</p>
            </div>
            <div className="w-px h-8 bg-slate-100" />
            <div className="text-center">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Total Credits</p>
              <p className="text-xl font-black text-slate-900">₹ {totalCredit.toLocaleString()}</p>
            </div>
          </div>
        </div>

        {isBalanced && (
          <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-1 shadow-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <p className="text-emerald-700 text-sm font-bold tracking-tight">Voucher is balanced and ready for submission.</p>
          </div>
        )}

        {!isBalanced && totalDebit > 0 && (
          <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl flex items-center gap-3 shadow-sm">
            <AlertCircle className="w-5 h-5 text-rose-600" />
            <p className="text-rose-700 text-sm font-bold tracking-tight">
              Voucher is imbalanced by ₹ {difference.toLocaleString()}
            </p>
          </div>
        )}

        {error && (
          <div className="bg-rose-100 border border-rose-300 p-4 rounded-xl flex items-center gap-3 shadow-md">
            <AlertCircle className="w-5 h-5 text-rose-600" />
            <p className="text-rose-800 text-sm font-bold">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 pb-20">
          {/* Header Metadata */}
          <div className="bg-white border border-slate-200 p-8 rounded-3xl shadow-sm relative overflow-hidden">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
              <div className="md:col-span-2 space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Info className="w-3 h-3" />
                  Voucher Narration
                </label>
                <textarea 
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-slate-800 focus:outline-none focus:ring-4 focus:ring-blue-600/10 transition-all text-sm font-medium h-32"
                  placeholder="Briefly describe why this transaction is being recorded..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Calendar className="w-3 h-3" />
                  Posting Date
                </label>
                <input 
                  required
                  type="date" 
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-slate-800 focus:outline-none focus:ring-4 focus:ring-blue-600/10 transition-all font-bold text-sm"
                  value={entryDate}
                  onChange={(e) => setEntryDate(e.target.value)}
                />
                <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
                  <div className="flex items-center gap-2 text-blue-700 mb-1">
                    <Calculator className="w-4 h-4" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-blue-600">ID Generation</span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-relaxed font-bold">Voucher number will be generated on post.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Dynamic Lines Table */}
          <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm">
            <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
               <h3 className="text-sm font-black text-slate-700 flex items-center gap-2 uppercase tracking-wider">
                 <Layers className="w-5 h-5 text-blue-600" />
                 Account Allocations
               </h3>
               <button 
                type="button"
                onClick={addLine}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-blue-700 rounded-xl font-black transition-all flex items-center gap-2 border border-slate-200 text-[10px] uppercase tracking-widest shadow-sm"
               >
                 <Plus className="w-3 h-3 shadow-none" />
                 Add Line
               </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50/80 text-slate-400 text-[10px] font-black uppercase tracking-widest border-b border-slate-100">
                    <th className="px-8 py-4 text-left">Ledger Account</th>
                    <th className="px-8 py-4 text-left">Note</th>
                    <th className="px-8 py-4 text-right w-36">Debit</th>
                    <th className="px-8 py-4 text-right w-36">Credit</th>
                    <th className="px-8 py-4 text-center w-16"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {lines.map((line, idx) => (
                    <tr key={idx} className="group hover:bg-slate-50/50 transition-colors">
                      <td className="px-8 py-4">
                        <select 
                          required
                          className="w-full bg-white border border-slate-200 rounded-xl p-2.5 text-slate-700 text-xs font-bold focus:ring-2 focus:ring-blue-600 outline-none transition-all"
                          value={line.account_id}
                          onChange={(e) => handleLineChange(idx, 'account_id', e.target.value)}
                        >
                          <option value="">Select Account...</option>
                          {accounts.map(acc => (
                             <option key={acc.id} value={acc.id}>[{acc.account_code}] {acc.account_name}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-8 py-4">
                        <input 
                          className="w-full bg-transparent border-b border-slate-100 p-2 text-slate-800 text-xs font-medium focus:border-blue-600 outline-none transition-all"
                          placeholder="Line description..."
                          value={line.description}
                          onChange={(e) => handleLineChange(idx, 'description', e.target.value)}
                        />
                      </td>
                      <td className="px-8 py-4">
                        <input 
                          type="number" 
                          step="0.01"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 text-right font-mono text-emerald-600 font-black text-xs focus:ring-2 focus:ring-emerald-500 outline-none"
                          value={line.debit_amount}
                          onChange={(e) => handleLineChange(idx, 'debit_amount', e.target.value)}
                        />
                      </td>
                      <td className="px-8 py-4">
                        <input 
                          type="number" 
                          step="0.01"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 text-right font-mono text-slate-900 font-black text-xs focus:ring-2 focus:ring-blue-500 outline-none"
                          value={line.credit_amount}
                          onChange={(e) => handleLineChange(idx, 'credit_amount', e.target.value)}
                        />
                      </td>
                      <td className="px-8 py-4 text-center">
                        <button 
                          type="button"
                          onClick={() => removeLine(idx)}
                          className="p-2 text-slate-300 hover:text-rose-500 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Submit Actions */}
          <div className="flex justify-end items-center gap-6">
            <button 
              type="button"
              onClick={() => router.back()}
              className="px-6 py-4 text-slate-400 font-black uppercase text-[10px] tracking-[0.2em] hover:text-slate-600 transition-all"
            >
              Discard
            </button>
            <button 
              type="submit"
              disabled={!isBalanced || isSubmitting}
              className={`px-10 py-4 rounded-2xl font-black uppercase text-[10px] tracking-[0.2em] transition-all shadow-lg flex items-center gap-3 ${
                isBalanced && !isSubmitting
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-600/20 active:scale-95'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
              }`}
            >
              {isSubmitting ? 'Processing...' : (
                <>
                  Post Voucher
                  <Save className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
