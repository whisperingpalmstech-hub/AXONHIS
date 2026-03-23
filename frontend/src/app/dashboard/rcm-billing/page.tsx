"use client";

import React, { useState, useEffect } from "react";
import { rcmApi } from "@/lib/rcm-api";
import { api } from "@/lib/api";
import {
  Banknote, Calculator, Receipt, Search, TrendingUp, AlertCircle, 
  CheckCircle, Plus, FileText, Download, ShieldCheck, Tag
} from "lucide-react";

export default function EnterpriseRCMBilling() {
  const [patients, setPatients] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>({ daily_revenue: 0, total_outstanding_ar: 0 });
  
  // Selected Context
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [activeBill, setActiveBill] = useState<any>(null);
  
  // Modals / Overlays
  const [showEstimator, setShowEstimator] = useState(false);
  const [estimatorResult, setEstimatorResult] = useState<any>(null);
  const [estQuery, setEstQuery] = useState({ service_name: "General Consultation", patient_category: "standard" });
  
  // Bill Mutations
  const [paymentAmount, setPaymentAmount] = useState<string>("");
  const [paymentMode, setPaymentMode] = useState<string>("card");
  const [discountVal, setDiscountVal] = useState<string>("");

  useEffect(() => {
    loadBaseData();
  }, []);

  const loadBaseData = async () => {
    try {
      const p = await api.get<any>("/patients");
      setPatients(Array.isArray(p) ? p : p?.items || []);
      const ax = await rcmApi.getDailyRevenue();
      setAnalytics(ax);
    } catch (e) {
      console.error("Failed to load base RCM data");
    }
  };

  const calculateEstimate = async () => {
    try {
      const res = await rcmApi.getCostEstimate(estQuery);
      setEstimatorResult(res);
    } catch (e) {
      alert("Estimation engine failure.");
    }
  };

  const selectPatientForBilling = async (pt: any) => {
    setSelectedPatient(pt);
    // Attempt to fetch active bill
    try {
      // Mock visit ID for now linking globally
      const vid = "00000000-0000-0000-0000-000000000000";
      const bill = await rcmApi.getBillInfo(vid);
      setActiveBill(bill);
    } catch (e:any) {
      if(e.response?.status === 404) {
         setActiveBill(null);
      }
    }
  };

  const initializeNewBill = async () => {
    if(!selectedPatient) return;
    try {
      const res = await rcmApi.initializeBill({
        visit_id: "00000000-0000-0000-0000-000000000000",
        patient_id: selectedPatient.id,
        payer: { payer_type: "self_pay" },
        services: [{ service_name: "General Consultation", quantity: 1, is_auto_billed: false }]
      });
      setActiveBill(res);
      loadBaseData();
    } catch (e) {
      alert("Failed creating bill. Ensure tariff exists.");
    }
  };

  const handleApplyDiscount = async () => {
     if(!activeBill || !discountVal) return;
     try {
       const res = await rcmApi.applyDiscount(activeBill.id, {
         discount_type: "percentage",
         discount_value: parseFloat(discountVal),
         reason: "Manual Admin Discount"
       });
       setActiveBill(res);
       setDiscountVal("");
       loadBaseData();
     } catch(e) { alert("Discount failed"); }
  };

  const handleCollectPayment = async () => {
     if(!activeBill || !paymentAmount) return;
     try {
       const res = await rcmApi.collectPayment(activeBill.id, {
         payment_mode: paymentMode,
         amount: parseFloat(paymentAmount),
         transaction_reference: "TXN-"+Math.floor(Math.random()*100000)
       });
       setActiveBill(res);
       setPaymentAmount("");
       loadBaseData();
     } catch(e) { alert("Payment failed"); }
  };

  const handleAddAutoService = async () => {
    if(!activeBill) return;
    try {
      const res = await rcmApi.addService(activeBill.id, {
        service_name: "CBC Diagnostics", quantity: 1, is_auto_billed: true
      });
      setActiveBill(res);
    } catch (e) {}
  };

  return (
    <div className="p-4 md:p-8 max-w-[1600px] mx-auto space-y-6 flex flex-col h-screen overflow-hidden">
      
      {/* 10. Financial Reporting Headers */}
      <div className="flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3 text-emerald-900">
            <Banknote className="text-emerald-600" size={32} />
            Enterprise Billing & RCM Engine
          </h1>
          <p className="text-slate-500 mt-1">Multi-Payer, Unified Tariff Selection, and Auto-Settlement Pipelines.</p>
        </div>
        <div className="flex gap-4">
           {/* BI Analytics Top Banner */}
           <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 px-5 flex items-center gap-4">
               <div>
                  <p className="text-[10px] uppercase font-bold text-emerald-600 mb-0.5">Today's Revenue Collected</p>
                  <p className="text-xl font-black text-emerald-900">₹{analytics.daily_revenue?.toFixed(2) || '0.00'}</p>
               </div>
               <TrendingUp className="text-emerald-400 opacity-50" size={28}/>
           </div>
           <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 px-5 flex items-center gap-4">
               <div>
                  <p className="text-[10px] uppercase font-bold text-rose-600 mb-0.5">Outstanding A/R Balance</p>
                  <p className="text-xl font-black text-rose-900">₹{analytics.total_outstanding_ar?.toFixed(2) || '0.00'}</p>
               </div>
               <AlertCircle className="text-rose-400 opacity-50" size={28}/>
           </div>
           <button onClick={()=>setShowEstimator(true)} className="btn-secondary ml-4 self-center"><Calculator size={18}/> Pre-Consult Estimator</button>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex gap-6">
         
         {/* Patient Selector Rail */}
         <div className="w-80 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm flex flex-col shrink-0">
             <div className="p-3 bg-slate-50 border-b border-slate-200">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-2.5 text-slate-400"/>
                  <input type="text" placeholder="Search Patient Accounts..." className="w-full text-sm pl-8 pr-3 py-2 border border-slate-300 rounded focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500" />
                </div>
             </div>
             <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {patients.map(p => (
                   <button key={p.id} onClick={()=>selectPatientForBilling(p)} className={`w-full text-left p-3 rounded-lg border transition-all ${selectedPatient?.id === p.id ? 'bg-emerald-50 border-emerald-500 shadow-sm' : 'bg-white border-slate-200 hover:border-emerald-300'}`}>
                      <p className="font-bold text-slate-800 flex justify-between">{p.first_name} {p.last_name} <span className="text-[10px] uppercase bg-slate-100 px-2 py-0.5 rounded text-slate-500 border">{p.uhid}</span></p>
                      <p className="text-xs text-slate-500 mt-1">Status: Open Accounts</p>
                   </button>
                ))}
             </div>
         </div>

         {/* MAIN BILLING WORKSPACE */}
         <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col overflow-hidden">
             {!selectedPatient ? (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
                   <Receipt size={64} className="mb-4 text-slate-200"/>
                   <h2 className="text-lg font-bold text-slate-500">Select Patient Account</h2>
                   <p className="text-sm text-center max-w-sm mt-2">Open the global financial ledger for the active patient to modify tariffs, apply rule-based pricing adjustments, or collect terminal payments.</p>
                </div>
             ) : (
                <div className="flex flex-col h-full">
                   {/* Patient Header */}
                   <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
                       <div>
                          <h2 className="text-xl font-black text-slate-800">{selectedPatient.first_name} {selectedPatient.last_name}</h2>
                          <p className="text-sm font-medium text-slate-500">Contact: {selectedPatient.phone_number} • Ledger Access Authorized</p>
                       </div>
                       {!activeBill && (
                           <button onClick={initializeNewBill} className="btn-primary bg-emerald-600 hover:bg-emerald-700">Initialize Master Bill</button>
                       )}
                   </div>

                   {/* Ledger Content */}
                   {!activeBill ? (
                      <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">No active invoice generated for this consultation period.</div>
                   ) : (
                      <div className="flex-1 overflow-y-auto flex">
                          
                          {/* Services Frame */}
                          <div className="w-2/3 p-6 border-r border-slate-200 space-y-6">
                              <div className="flex justify-between items-center">
                                 <h3 className="font-bold text-slate-800 flex items-center gap-2"><FileText size={18}/> Active Service Lines (INV: {activeBill.bill_number})</h3>
                                 <div className="flex gap-2">
                                    <span className={`px-3 py-1 text-xs font-bold uppercase rounded-full ${activeBill.status==='paid'?'bg-emerald-100 text-emerald-700':activeBill.status==='partially_paid'?'bg-amber-100 text-amber-700':'bg-rose-100 text-rose-700'}`}>STATUS: {activeBill.status}</span>
                                    <span className="px-3 py-1 bg-indigo-100 text-indigo-700 font-bold uppercase rounded-full text-xs">Payer: {activeBill.payer?.payer_type}</span>
                                 </div>
                              </div>

                              <table className="w-full text-sm">
                                <thead className="bg-slate-50 border-y border-slate-200 text-slate-500 uppercase text-[10px] font-bold tracking-widest text-left">
                                  <tr>
                                    <th className="py-3 px-4">Particulars</th>
                                    <th className="py-3 px-4 text-center">Qty</th>
                                    <th className="py-3 px-4 text-right">Rate</th>
                                    <th className="py-3 px-4 text-right">Total</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {activeBill.services.map((svc:any)=>(
                                    <tr key={svc.id} className="border-b border-slate-100 hover:bg-slate-50">
                                      <td className="py-3 px-4 font-bold text-slate-800">
                                         {svc.service_name} 
                                         {svc.is_auto_billed && <span className="ml-2 bg-rose-100 text-rose-700 text-[10px] px-1.5 py-0.5 rounded-sm uppercase">Auto-Billed</span>}
                                      </td>
                                      <td className="py-3 px-4 text-center text-slate-600">{svc.quantity}</td>
                                      <td className="py-3 px-4 text-right text-slate-600">₹{svc.base_rate}</td>
                                      <td className="py-3 px-4 text-right font-bold text-slate-800">₹{svc.total_cost}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>

                              <button onClick={handleAddAutoService} className="text-xs text-indigo-600 font-bold hover:underline">+ Simulate Async Order Push (Post-Consult Billing test)</button>

                              {/* Receipt Sub-Total Blocks */}
                              <div className="flex flex-col items-end pt-4 space-y-2 text-sm max-w-sm ml-auto">
                                 <div className="flex justify-between w-full border-b pb-2"><span className="text-slate-500">Gross Total</span><span className="font-bold">₹{activeBill.gross_amount}</span></div>
                                 <div className="flex justify-between w-full border-b pb-2"><span className="text-rose-500">Discounts ({activeBill.discounts?.length} lines)</span><span className="font-bold text-rose-600">- ₹{activeBill.discount_amount}</span></div>
                                 <div className="flex justify-between w-full border-b pb-2"><span className="text-emerald-500">Paid Receipts ({activeBill.payments?.length} lines)</span><span className="font-bold text-emerald-600">- ₹{activeBill.paid_amount}</span></div>
                                 <div className="flex justify-between w-full pt-2"><span className="text-slate-800 font-black text-lg">Net Payable</span><span className="font-black text-lg text-rose-600">₹{activeBill.balance_amount}</span></div>
                              </div>
                          </div>

                          {/* Settlement Tools frame */}
                          <div className="w-1/3 p-6 bg-slate-50 space-y-6">
                              
                              {/* Discounts Tool */}
                              <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
                                 <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2 mb-3"><Tag size={16}/> Apply Discretionary Concession</h4>
                                 <div className="flex gap-2">
                                    <input type="number" placeholder="% value" value={discountVal} onChange={e=>setDiscountVal(e.target.value)} className="w-full border-slate-300 rounded text-sm p-2 focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500"/>
                                    <button onClick={handleApplyDiscount} className="bg-slate-800 text-white rounded px-4 text-sm font-bold min-w-max hover:bg-slate-700">Apply Rule</button>
                                 </div>
                                 <p className="text-[10px] text-slate-400 mt-2">Requires Level-2 Auth Clearance.</p>
                              </div>

                              {/* Payment Collection */}
                              {activeBill.balance_amount > 0 ? (
                                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 shadow-sm relative overflow-hidden">
                                  <div className="absolute -right-4 -top-4 opacity-10 text-emerald-600"><Banknote size={100}/></div>
                                  <h4 className="font-bold text-emerald-950 flex items-center gap-2 mb-3 relative z-10"><ShieldCheck size={18}/> Terminal Settlement</h4>
                                  
                                  <div className="space-y-3 relative z-10">
                                     <select value={paymentMode} onChange={e=>setPaymentMode(e.target.value)} className="w-full text-sm rounded border-emerald-200 shadow-sm p-2">
                                        <option value="card">Credit / Debit Card via EDC</option>
                                        <option value="cash">Counter Cash Receipt</option>
                                        <option value="online">Generate Digital UPI Link</option>
                                     </select>
                                     <input type="number" placeholder="Collect Amount" value={paymentAmount} onChange={e=>setPaymentAmount(e.target.value)} className="w-full border-emerald-200 rounded text-sm p-2" />
                                     <button onClick={handleCollectPayment} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm py-2 rounded shadow transition-all">Settle Funds →</button>
                                  </div>
                               </div>
                              ) : (
                                <div className="bg-emerald-600 rounded-lg p-6text-white text-center py-8 text-white shadow-lg shadow-emerald-600/20">
                                   <CheckCircle size={48} className="mx-auto mb-3 opacity-80" />
                                   <h3 className="font-black text-xl mb-1">Bill Settled Fully</h3>
                                   <p className="text-emerald-100 text-xs mb-4">Patient liability resolved. Accounting entries posted.</p>
                                   <button className="bg-white text-emerald-800 font-bold px-4 py-2 rounded text-sm w-full shadow hover:bg-emerald-50">Print Official Receipt</button>
                                </div>
                              )}
                          </div>
                      </div>
                   )}
                </div>
             )}
         </div>

      </div>

      {/* 1. Pre-Consult Billing Estimator Modal */}
      {showEstimator && (
         <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 animate-in fade-in">
             <div className="bg-white rounded-xl shadow-2xl w-[500px] overflow-hidden">
                 <div className="bg-slate-800 p-4 shrink-0 flex justify-between items-center text-white">
                    <h3 className="font-bold flex items-center gap-2"><Calculator size={18}/> Intelligent Estimator Matrix</h3>
                    <button onClick={()=>setShowEstimator(false)} className="text-slate-400 hover:text-white font-bold">&times;</button>
                 </div>
                 <div className="p-6 space-y-4">
                     <div>
                       <label className="text-xs font-bold text-slate-500 block mb-1">Search HIS Service</label>
                       <input type="text" className="w-full border-slate-300 rounded text-sm" value={estQuery.service_name} onChange={e=>setEstQuery({...estQuery, service_name: e.target.value})} />
                     </div>
                     <div>
                       <label className="text-xs font-bold text-slate-500 block mb-1">Select Payer Strategy</label>
                       <select className="w-full border-slate-300 rounded text-sm" value={estQuery.patient_category} onChange={e=>setEstQuery({...estQuery, patient_category: e.target.value})}>
                          <option value="standard">Standard Outpatient (Self-Pay)</option>
                          <option value="corporate">Corporate Tariff Matrix</option>
                          <option value="insurance">Insurance Approved Network</option>
                       </select>
                     </div>
                     <button onClick={calculateEstimate} className="bg-indigo-600 text-white w-full rounded py-2 font-bold shadow hover:bg-indigo-700">Compute Prognostic Costs</button>

                     {estimatorResult && (
                       <div className="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-center">
                          <p className="text-xs text-emerald-700 font-bold uppercase tracking-wider mb-1">Computed Final Tariff ({estimatorResult.tariff_applied})</p>
                          <h4 className="text-3xl font-black text-emerald-900 block">₹{estimatorResult.estimated_cost}</h4>
                          <p className="text-xs text-slate-500 mt-2 text-left bg-white p-2 rounded border border-slate-200 inline-block mx-auto">This estimate guarantees pricing according to the algorithmic tariff mapping prior to consultation.</p>
                       </div>
                     )}
                 </div>
             </div>
         </div>
      )}

    </div>
  );
}
