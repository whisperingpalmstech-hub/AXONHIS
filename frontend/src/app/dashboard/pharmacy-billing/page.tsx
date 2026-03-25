"use client";

import React, { useState, useEffect } from "react";
import { 
  Receipt, CreditCard, Banknote, ShieldCheck, 
  BarChart3, FileText, CheckCircle, Search, ScrollText, AlertTriangle
} from "lucide-react";

const formatDate = (dateString: string) => {
  const d = new Date(dateString);
  return d.toLocaleDateString("en-GB", { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute:'2-digit' });
};

interface Bill {
  id: string;
  bill_number: string;
  billing_type: string;
  net_payable: number;
  payment_status: string;
  created_at: string;
  bill_items: any[];
}

export default function PharmacyBillingComplianceEngine() {
  const [activeTab, setActiveTab] = useState("Billing & Settlements");
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);

  // Mocks for new payment
  const [payingBill, setPayingBill] = useState<Bill | null>(null);
  const [paymentMode, setPaymentMode] = useState("CASH");
  const [amountPaid, setAmountPaid] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const rs = await fetch(`${u}/api/v1/pharmacy/billing-compliance/bills`);
      if (rs.ok) {
        setBills(await rs.json());
      }
    } catch(e) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const processPayment = async () => {
    if(!payingBill || !amountPaid) return alert("Enter amount.");
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const res = await fetch(`${u}/api/v1/pharmacy/billing-compliance/payments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bill_id: payingBill.id,
          amount_paid: parseFloat(amountPaid),
          payment_mode: paymentMode,
          transaction_reference: "MANUAL-" + Math.floor(Math.random() * 1000)
        })
      });
      if(res.ok) {
        alert("Payment applied successfully!");
        setPayingBill(null);
        setAmountPaid("");
        fetchData();
      }
    } catch (e) { alert("Payment Failed"); }
  };

  const generateReport = async (type: string) => {
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const res = await fetch(`${u}/api/v1/pharmacy/billing-compliance/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_type: type })
      });
      if(res.ok) {
        const data = await res.json();
        console.log("Report Payload:", data);
        alert(`Report ${type} Generated!\nCheck console for payload.`);
      }
    } catch(e) { }
  }

  // Create a mock initial bill if table is empty just for demo testing
  const createDemoBill = async () => {
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      await fetch(`${u}/api/v1/pharmacy/billing-compliance/bills`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({
           billing_type: "OP_WALKIN",
           bill_items: [
             { drug_id: "Paracetamol 500mg", quantity: 10, unit_price: 2.0, tax: 5.0 },
             { drug_id: "Amoxicillin Kit", quantity: 1, unit_price: 15.0, tax: 10.0 }
           ]
         })
      });
      fetchData();
    } catch (e) {}
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-6 font-sans">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-indigo-900/10">
          <div>
            <h1 className="text-3xl font-extrabold flex items-center gap-3 text-indigo-900">
              <Receipt className="w-8 h-8 text-indigo-600" />
              Pharmacological Billing & Compliance
            </h1>
            <p className="text-slate-500 mt-2 font-medium">Txn Settlement, Discount Authorization & Ledger Auditing</p>
          </div>
          <button onClick={createDemoBill} className="bg-indigo-100 text-indigo-700 px-4 py-2 rounded-lg font-bold hover:bg-indigo-200 transition-colors">
            + Generate Draft OP Bill
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-2 mb-8 bg-white shadow-sm p-1.5 rounded-xl border border-slate-200 w-fit">
          {["Billing & Settlements", "Revenue & Reports", "Regulatory Compliance"].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-all ${
                activeTab === tab 
                  ? "bg-indigo-600 text-white shadow-md border border-indigo-700" 
                  : "text-slate-500 hover:text-slate-700 hover:bg-slate-100/50"
              }`}
            >
              {tab === "Billing & Settlements" && <CreditCard className="w-4 h-4 inline mr-2" />}
              {tab === "Revenue & Reports" && <BarChart3 className="w-4 h-4 inline mr-2" />}
              {tab === "Regulatory Compliance" && <ShieldCheck className="w-4 h-4 inline mr-2" />}
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "Billing & Settlements" && (
           <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
             <div className="p-6 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
               <h3 className="font-bold text-slate-700 uppercase tracking-widest text-sm flex items-center gap-2">
                 <ScrollText className="w-5 h-5 text-indigo-500" /> Accounts Receivable Ledger
               </h3>
               <div className="bg-white pl-4 pr-2 py-1.5 rounded-lg border border-slate-200 flex items-center gap-2">
                 <Search className="w-4 h-4 text-slate-400" />
                 <input type="text" placeholder="Search Bill No..." className="outline-none text-sm w-48 font-medium text-slate-700" />
               </div>
             </div>
             
             <table className="w-full text-left">
               <thead className="bg-white border-b border-slate-200 text-slate-500 text-xs uppercase font-bold tracking-wider">
                 <tr>
                   <th className="p-4 pl-6">Invoice #</th>
                   <th className="p-4">Context</th>
                   <th className="p-4">Time Issued</th>
                   <th className="p-4">Net Value</th>
                   <th className="p-4">Status</th>
                   <th className="p-4 text-right pr-6">Settlement</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-slate-100">
                 {loading ? (
                   <tr><td colSpan={6} className="p-8 text-center text-slate-400 font-medium">Syncing Ledgers...</td></tr>
                 ) : bills.length === 0 ? (
                   <tr><td colSpan={6} className="p-16 text-center text-slate-400 font-medium bg-slate-50/50">No un-reconciled pharmacy bills generated today.</td></tr>
                 ) : (
                   bills.map(b => (
                     <tr key={b.id} className="hover:bg-indigo-50/30 transition-colors group">
                       <td className="p-4 pl-6 font-bold text-slate-800">{b.bill_number}</td>
                       <td className="p-4"><span className="bg-slate-100 text-slate-600 px-2 py-1 rounded text-xs font-bold">{b.billing_type}</span></td>
                       <td className="p-4 text-sm font-medium text-slate-500">{formatDate(b.created_at)}</td>
                       <td className="p-4 font-black text-slate-700">${b.net_payable.toFixed(2)}</td>
                       <td className="p-4">
                         <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                            b.payment_status === 'PAID' ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' :
                            b.payment_status === 'PARTIAL' ? 'bg-amber-100 text-amber-700 border border-amber-200' :
                            'bg-rose-100 text-rose-700 border border-rose-200'
                         }`}>
                           {b.payment_status}
                         </span>
                       </td>
                       <td className="p-4 pr-6 text-right">
                         {b.payment_status !== 'PAID' ? (
                           <button 
                             onClick={() => setPayingBill(b)}
                             className="text-indigo-600 font-bold text-sm bg-indigo-50 border border-indigo-200 px-4 py-1.5 rounded-lg hover:bg-indigo-600 hover:text-white transition-colors shadow-sm">
                             Settle Due
                           </button>
                         ) : (
                           <button className="text-slate-400 font-bold text-sm bg-slate-100 border border-slate-200 px-4 py-1.5 rounded-lg cursor-not-allowed">
                             Cleared
                           </button>
                         )}
                       </td>
                     </tr>
                   ))
                 )}
               </tbody>
             </table>
           </div>
        )}

        {/* Modal for Partial/Full Payments overlaying Billing Table */}
        {payingBill && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
             <div className="bg-white rounded-3xl w-full max-w-md overflow-hidden shadow-2xl">
               <div className="bg-indigo-900 p-6 flex justify-between items-center text-white">
                 <h3 className="font-black text-xl flex items-center gap-2"><Banknote className="w-5 h-5"/> Process Receipt</h3>
                 <button onClick={() => setPayingBill(null)} className="text-indigo-200 hover:text-white font-bold">X</button>
               </div>
               <div className="p-8">
                 <p className="text-slate-500 mb-6 font-medium">Reconciling Bill: <strong className="text-indigo-900">{payingBill.bill_number}</strong><br/>Pending Liability: <strong>${payingBill.net_payable.toFixed(2)}</strong></p>
                 
                 <div className="space-y-4">
                   <div>
                     <label className="block text-sm font-bold text-slate-600 mb-2">Tender Mode</label>
                     <select value={paymentMode} onChange={e => setPaymentMode(e.target.value)} className="w-full border-2 border-slate-200 p-3 rounded-xl focus:border-indigo-500 outline-none font-bold text-slate-700 bg-slate-50 relative pointer-events-auto">
                        <option value="CASH">Liquid Cash</option>
                        <option value="CREDIT_CARD">Credit/Debit Txn</option>
                        <option value="UPI">UPI / Digital Gateway</option>
                        <option value="INSURANCE">Insurance TPA</option>
                     </select>
                   </div>
                   <div>
                     <label className="block text-sm font-bold text-slate-600 mb-2">Capture Amount ($)</label>
                     <input type="number" value={amountPaid} onChange={e => setAmountPaid(e.target.value)} placeholder={`e.g. ${payingBill.net_payable}`} className="w-full border-2 border-slate-200 p-3 rounded-xl focus:border-indigo-500 outline-none font-bold text-slate-700 bg-white"/>
                   </div>
                   <button onClick={processPayment} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-black py-4 rounded-xl mt-4 shadow-lg shadow-indigo-600/30 transition-transform hover:scale-[1.02]">
                     Confirm & Ledger Auth
                   </button>
                 </div>
               </div>
             </div>
          </div>
        )}

        {activeTab === "Revenue & Reports" && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
             <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm hover:border-indigo-300 transition-colors cursor-pointer" onClick={() => generateReport("DAILY_SALES")}>
               <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center mb-4"><BarChart3 className="w-6 h-6"/></div>
               <h4 className="font-bold text-slate-800">Daily Sales Abstract</h4>
               <p className="text-sm font-medium text-slate-500 mt-2">Generate combined OP/IP revenue aggregation grids.</p>
             </div>
             <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm hover:border-indigo-300 transition-colors cursor-pointer" onClick={() => generateReport("REVENUE_BY_MODE")}>
               <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center mb-4"><Banknote className="w-6 h-6"/></div>
               <h4 className="font-bold text-slate-800">Payment Modes</h4>
               <p className="text-sm font-medium text-slate-500 mt-2">Reconcile Bank Transfers, Cash, and TPA Insurance liabilities.</p>
             </div>
             <div className="bg-white border border-rose-200 p-6 rounded-2xl shadow-sm opacity-60">
               <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-xl flex items-center justify-center mb-4"><FileText className="w-6 h-6"/></div>
               <h4 className="font-bold text-slate-800">Refund/Credit Audits</h4>
               <p className="text-sm font-medium text-slate-500 mt-2">Locked. Requires Level-4 Supervisor privileges.</p>
             </div>
          </div>
        )}

        {activeTab === "Regulatory Compliance" && (
           <div className="bg-slate-900 border border-indigo-500/30 p-12 rounded-3xl shadow-2xl relative overflow-hidden">
             <ShieldCheck className="absolute -right-10 -bottom-10 w-64 h-64 text-indigo-500/10 pointer-events-none" />
             <div className="relative z-10 max-w-2xl">
               <span className="bg-emerald-500/20 text-emerald-400 font-bold uppercase tracking-widest px-3 py-1 rounded-full text-xs mb-6 inline-block">Security First</span>
               <h2 className="text-4xl font-extrabold text-white mb-4">Federal Regulatory Analytics</h2>
               <p className="text-slate-300 text-lg mb-8 font-medium">Generate restricted inspection logs proving Narcotic handling protocols and Discount Authority chains to auditors.</p>
               <button onClick={() => generateReport("COMPLIANCE_NARCOTICS")} className="bg-indigo-600 hover:bg-indigo-500 text-white border border-indigo-400 font-bold px-8 py-4 rounded-xl shadow-lg shadow-indigo-600/20 flex items-center gap-3 transition-colors">
                 <AlertTriangle className="w-5 h-5" /> Compile Narcotics Compliance File
               </button>
             </div>
           </div>
        )}

      </div>
    </div>
  );
}
