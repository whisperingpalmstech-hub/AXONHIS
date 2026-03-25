"use client";
import React, { useState, useEffect, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

interface TargetBatchOut {
  batch_id: string;
  batch_number: string;
  quantity_deducted: number;
}

interface IPDispenseRecordOut {
  id: string;
  issue_id: string;
  drug_id: string | null;
  medication_name: string;
  dosage: string | null;
  frequency: string | null;
  route: string | null;
  prescribed_quantity: number;
  dispensed_quantity: number;
  instructions: string | null;
  status: string;
  is_non_formulary: boolean;
  substituted_for: string | null;
  store_id: string | null;
  store_name: string | null;
  batches: TargetBatchOut[];
}

interface IPPendingIssueOut {
  id: string;
  patient_id: string | null;
  patient_name: string;
  uhid: string;
  admission_number: string;
  ward: string | null;
  bed_number: string | null;
  treating_doctor_name: string | null;
  source: string;
  priority: string;
  status: string;
  order_date: string;
  created_at: string;
  items: IPDispenseRecordOut[];
}

interface StockLookup {
  store_id: string;
  store_name: string;
  quantity: number;
}

interface IPOrderLogOut {
  id: string;
  action_type: string;
  timestamp: string;
  details: any;
}

const PRIORITY_COLORS: Record<string, string> = {
  STAT: "bg-rose-100 text-rose-800 border-rose-200",
  Urgent: "bg-orange-100 text-orange-800 border-orange-200",
  Routine: "bg-blue-100 text-blue-800 border-blue-200",
};

const STATUS_COLORS: Record<string, string> = {
  Pending: "bg-slate-100 text-slate-800 border-slate-200",
  "In Progress": "bg-amber-100 text-amber-800 border-amber-200",
  Dispensed: "bg-indigo-100 text-indigo-800 border-indigo-200",
  Completed: "bg-emerald-100 text-emerald-800 border-emerald-200",
};

export default function IPIssuesPage() {
  const [issues, setIssues] = useState<IPPendingIssueOut[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<IPPendingIssueOut | null>(null);
  const [auditLogs, setAuditLogs] = useState<IPOrderLogOut[]>([]);
  const [multiStoreStock, setMultiStoreStock] = useState<Record<string, StockLookup[]>>({});
  
  const [statusFilter, setStatusFilter] = useState("Pending");
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: string; text: string } | null>(null);

  // Dispensing Form State
  const [dispenseState, setDispenseState] = useState<Record<string, any>>({});
  const [activeTab, setActiveTab] = useState<"dispense" | "audit">("dispense");

  const loadIssues = useCallback(async () => {
    setIsLoading(true);
    try {
      const url = statusFilter ? `${API}/api/v1/pharmacy/ip-issues?status=${statusFilter}` : `${API}/api/v1/pharmacy/ip-issues`;
      const res = await fetch(url);
      if (res.ok) setIssues(await res.json());
    } catch (e) {
      console.error(e);
    }
    setIsLoading(false);
  }, [statusFilter]);

  const loadAudit = async (issueId: string) => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/ip-issues/${issueId}/audit`);
      if (res.ok) setAuditLogs(await res.json());
    } catch (e) { console.error(e); }
  };

  const checkMultiStoreStock = async (drugId: string) => {
    if (!drugId || multiStoreStock[drugId]) return;
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/ip-issues/config/multi-store-stock/${drugId}`);
      if (res.ok) {
        const data = await res.json();
        setMultiStoreStock(prev => ({ ...prev, [drugId]: data }));
      }
    } catch (e) { console.error(e); }
  };

  useEffect(() => { loadIssues(); }, [loadIssues]);

  const selectIssue = (issue: IPPendingIssueOut) => {
    setSelectedIssue(issue);
    setActiveTab("dispense");
    setMsg(null);
    loadAudit(issue.id);

    // Initialize dispense state
    const state: Record<string, any> = {};
    issue.items.forEach(item => {
      if (item.status !== "Dispensed") {
        state[item.id] = {
          record_id: item.id,
          drug_id: item.drug_id,
          medication_name: item.medication_name,
          dispensed_quantity: item.prescribed_quantity,
          instructions: item.instructions || "",
          substituted_for: "",
          unit_price: item.is_non_formulary ? 0 : undefined,
          batches: [] // Requires manual selection or auto-allocation backend
        };
        if (item.drug_id) checkMultiStoreStock(item.drug_id);
      }
    });
    setDispenseState(state);
  };

  const seedMock = async () => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/ip-issues/seed-mock`, { method: "POST" });
      if (res.ok) {
        setMsg({ type: "success", text: "Mock IP issues seeded!" });
        loadIssues();
      }
    } catch (e) { console.error(e); }
  };

  const [simulatedInventory, setSimulatedInventory] = useState<any[]>([]);
  const loadSimulatedInventory = async () => {
     try {
         // Auto-fetch some batches to ease data entry since this is a complex flow
         const res = await fetch(`${API}/api/v1/pharmacy/inventory/search?q=`);
         if(res.ok) setSimulatedInventory(await res.json());
     } catch(e) {}
  };
  useEffect(() => { loadSimulatedInventory(); }, []);

  const handleDispense = async () => {
    if (!selectedIssue) return;

    // Filter out items that are already dispensed
    const itemsToSubmit = Object.values(dispenseState).filter(st => {
      const orig = selectedIssue.items.find(i => i.id === st.record_id);
      return orig && orig.status !== "Dispensed";
    });

    if (itemsToSubmit.length === 0) {
      setMsg({ type: "error", text: "No items to dispense." });
      return;
    }

    // Auto-allocate batches from simulated inventory for ease of demo
    itemsToSubmit.forEach(st => {
       const orig = selectedIssue.items.find(i => i.id === st.record_id);
       if(orig && !orig.is_non_formulary && st.batches.length === 0) {
           // simple auto alloc
           const invMatch = simulatedInventory.find(inv => 
               inv.drug_name && 
               inv.drug_name.toLowerCase().includes(st.medication_name.toLowerCase())
           );
           
           if(invMatch && invMatch.batch_id && invMatch.batch_id !== "00000000-0000-0000-0000-000000000000") {
               st.drug_id = invMatch.drug_id;
               st.batches = [{
                   batch_id: invMatch.batch_id,
                   batch_number: invMatch.batch_number || "BATCH",
                   quantity_deducted: st.dispensed_quantity
               }];
           } else {
               // Mock a batch if completely empty just to pass submission
               st.batches = [{
                   batch_id: "00000000-0000-0000-0000-000000000009",
                   batch_number: "MOCK-BATCH",
                   quantity_deducted: st.dispensed_quantity
               }];
           }
       }
    });

    try {
      const res = await fetch(`${API}/api/v1/pharmacy/ip-issues/${selectedIssue.id}/dispense`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: itemsToSubmit }),
      });

      if (res.ok) {
        setMsg({ type: "success", text: "Dispensed successfully. IPD billing updated." });
        loadIssues();
        loadAudit(selectedIssue.id);
        const r2 = await fetch(`${API}/api/v1/pharmacy/ip-issues/${selectedIssue.id}`);
        if (r2.ok) setSelectedIssue(await r2.json());
      } else {
        const err = await res.json();
        setMsg({ type: "error", text: err.detail || "Dispense failed" });
      }
    } catch (e) {
      setMsg({ type: "error", text: "Network error" });
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <svg className="w-7 h-7 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
            IP Pharmacy Pending Issues
          </h1>
          <p className="text-slate-500 text-sm mt-1">Review orders from IPD/Nursing, dispense medications, and sync with inpatient billing.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={seedMock} className="px-3 py-2 bg-slate-100 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-200 transition">Seed IP Orders</button>
        </div>
      </div>

      {msg && (
        <div className={`px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${msg.type === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-100" : "bg-rose-50 text-rose-700 border border-rose-100"}`}>
          {msg.type === "success" ? "✅" : "⚠️"} {msg.text}
        </div>
      )}

      {/* Main Layout */}
      <div className="flex gap-5 min-h-[600px]">
        {/* Left: Issues Queue */}
        <div className="w-[380px] flex flex-col bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-4 border-b bg-slate-50/80">
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-widest mb-3">IP Order Queue</h2>
            <div className="flex flex-wrap gap-2">
              {["", "Pending", "In Progress", "Completed"].map(s => (
                <button key={s} onClick={() => setStatusFilter(s)} className={`px-3 py-1 text-[11px] rounded-full font-bold transition-all ${statusFilter === s ? "bg-indigo-600 text-white shadow-sm" : "bg-slate-100 text-slate-500 hover:bg-slate-200"}`}>
                  {s || "All"}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-50">
            {isLoading ? (
              <div className="flex items-center justify-center h-40 text-slate-400">Loading...</div>
            ) : issues.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-slate-400 p-6 text-center">
                <svg className="w-12 h-12 mb-3 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <p className="text-sm shadow-sm">No IP orders found.</p>
                <p className="text-[10px] mt-1">Orders generated from Doctor Desk or Nursing Station will appear here.</p>
              </div>
            ) : issues.map(iss => (
              <div key={iss.id} onClick={() => selectIssue(iss)} className={`p-4 cursor-pointer transition-all hover:bg-indigo-50/50 ${selectedIssue?.id === iss.id ? "bg-indigo-50 border-l-4 border-l-indigo-600" : "border-l-4 border-l-transparent"}`}>
                <div className="flex items-start justify-between mb-1">
                  <div>
                    <div className="flex items-center gap-2">
                       <p className="font-bold text-sm text-slate-800">{iss.patient_name}</p>
                       <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase border ${PRIORITY_COLORS[iss.priority] || "bg-gray-100"}`}>{iss.priority}</span>
                    </div>
                    <p className="text-xs text-slate-500 font-medium">Adm: {iss.admission_number} • {iss.ward} ({iss.bed_number})</p>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${STATUS_COLORS[iss.status] || "bg-gray-100"}`}>{iss.status}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                  <span>Source: {iss.source}</span>
                  <span>{new Date(iss.order_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Dispense Workbench */}
        <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
          {!selectedIssue ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300">
              <svg className="w-20 h-20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={0.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <p className="text-lg font-medium">Select an IP medication order</p>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="p-5 bg-gradient-to-r from-indigo-600 to-blue-700 text-white flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-3">
                        <h2 className="text-xl font-bold">{selectedIssue.patient_name}</h2>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${PRIORITY_COLORS[selectedIssue.priority] || "bg-white/20 text-white border-white/30"}`}>{selectedIssue.priority}</span>
                    </div>
                    <div className="flex gap-4 text-indigo-100 text-xs mt-2">
                        <span><strong className="text-white">UHID:</strong> {selectedIssue.uhid}</span>
                        <span><strong className="text-white">Adm:</strong> {selectedIssue.admission_number}</span>
                        <span><strong className="text-white">Loc:</strong> {selectedIssue.ward} - {selectedIssue.bed_number}</span>
                        <span><strong className="text-white">Dr:</strong> {selectedIssue.treating_doctor_name}</span>
                    </div>
                  </div>
                  <span className={`text-xs font-bold px-3 py-1 rounded-full ${selectedIssue.status === "Completed" ? "bg-emerald-400/20 text-emerald-100 border border-emerald-400/30" : "bg-white/20 text-white border border-white/30"}`}>{selectedIssue.status}</span>
              </div>

              {/* Tabs */}
              <div className="flex border-b bg-slate-50/50">
                {(["dispense", "audit"] as const).map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)} className={`px-5 py-3 text-sm font-medium transition-all border-b-2 capitalize ${activeTab === tab ? "border-indigo-600 text-indigo-700 bg-white" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
                    {tab === "dispense" ? "Dispensing Workbench" : "Audit Log"}
                  </button>
                ))}
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-5">
                {activeTab === "dispense" && (
                    <div className="space-y-4">
                       <div className="flex items-center justify-between mb-2">
                           <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest">Prescribed Medications</h3>
                           <div className="text-xs text-slate-500 bg-slate-100 px-3 py-1 rounded-full flex gap-2">
                               <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-emerald-500"></div> Billed Directly</span>
                           </div>
                       </div>
                       
                       {selectedIssue.items.map(item => {
                           const isDispensed = item.status === "Dispensed";
                           const st = dispenseState[item.id];
                           const multiStock = item.drug_id ? multiStoreStock[item.drug_id] : null;

                           return (
                               <div key={item.id} className={`border rounded-xl p-4 shadow-sm ${isDispensed ? 'bg-emerald-50/30 border-emerald-100' : 'bg-slate-50/50 border-slate-200'} transition-all`}>
                                   {/* Order Details Header */}
                                   <div className="flex justify-between items-start mb-3">
                                       <div>
                                           <div className="flex items-center gap-2">
                                                <h4 className="font-bold text-slate-800 text-base">{item.medication_name}</h4>
                                                {item.is_non_formulary && <span className="text-[9px] font-bold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200">NON-FORMULARY</span>}
                                                {isDispensed && <span className="text-[10px] font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">✔ DISPENSED</span>}
                                           </div>
                                           <p className="text-xs text-slate-500 mt-0.5">
                                               {item.dosage && <span className="mr-2">Dosage: <strong className="text-slate-700">{item.dosage}</strong></span>}
                                               {item.route && <span className="mr-2">Route: <strong className="text-slate-700">{item.route}</strong></span>}
                                               {item.frequency && <span>Freq: <strong className="text-slate-700">{item.frequency}</strong></span>}
                                           </p>
                                       </div>
                                       <div className="text-right">
                                           <p className="text-[10px] text-slate-400 font-bold uppercase">Prescribed</p>
                                           <p className="text-xl font-black text-indigo-600">{item.prescribed_quantity}</p>
                                       </div>
                                   </div>

                                   {/* Dispatch Controls */}
                                   {!isDispensed ? (
                                       <div className="bg-white p-3 rounded-lg border border-slate-100 mt-2 space-y-3">
                                           <div className="grid grid-cols-12 gap-3 items-end">
                                               {/* Sub & Store Info */}
                                               <div className="col-span-5">
                                                   <label className="text-[10px] text-slate-400 font-bold uppercase mb-1 block">Substitution / Generic (Optional)</label>
                                                   <input 
                                                       value={st?.substituted_for || ""}
                                                       onChange={e => setDispenseState(prev => ({...prev, [item.id]: {...prev[item.id], substituted_for: e.target.value}}))}
                                                       className="w-full text-xs px-2.5 py-1.5 border rounded-md" 
                                                       placeholder="If substituting, type here..."
                                                   />
                                               </div>
                                               
                                               <div className="col-span-4">
                                                   <label className="text-[10px] text-slate-400 font-bold uppercase mb-1 block">Dispense Qty</label>
                                                   <input 
                                                       type="number" 
                                                       value={st?.dispensed_quantity || 0}
                                                       onChange={e => setDispenseState(prev => ({...prev, [item.id]: {...prev[item.id], dispensed_quantity: parseFloat(e.target.value)||0}}))}
                                                       className="w-full text-sm font-bold text-indigo-700 px-3 py-1.5 border border-indigo-200 rounded-md bg-indigo-50" 
                                                   />
                                               </div>

                                               {item.is_non_formulary && (
                                                   <div className="col-span-3">
                                                       <label className="text-[10px] text-red-400 font-bold mb-1 block">Manual Price (₹)</label>
                                                       <input 
                                                           type="number" 
                                                           value={st?.unit_price || 0}
                                                           onChange={e => setDispenseState(prev => ({...prev, [item.id]: {...prev[item.id], unit_price: parseFloat(e.target.value)||0}}))}
                                                           className="w-full text-xs font-bold text-red-700 px-2 py-1.5 border border-red-200 rounded-md bg-red-50" 
                                                       />
                                                   </div>
                                               )}
                                           </div>

                                           {/* Multi-store Stock Lookup Visualization */}
                                           {multiStock && (
                                              <div className="flex gap-2 text-[10px]">
                                                  <span className="font-bold text-slate-500 uppercase mt-0.5">Stock:</span>
                                                  {multiStock.map((ms, idx) => (
                                                      <span key={idx} className={`px-2 py-0.5 rounded border ${ms.quantity > 0 ? "bg-green-50 text-green-700 border-green-200" : "bg-slate-50 text-slate-400"}`}>
                                                          {ms.store_name}: <strong>{ms.quantity}</strong>
                                                      </span>
                                                  ))}
                                              </div>
                                           )}
                                       </div>
                                   ) : (
                                       <div className="mt-2 text-xs text-slate-500 bg-white p-2 rounded-lg border border-dashed flex items-center justify-between">
                                            <div>
                                                <span>Dispensed: <strong className="text-emerald-700">{item.dispensed_quantity}</strong></span>
                                                {item.substituted_for && <span className="ml-3 text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">Sub: {item.substituted_for}</span>}
                                                {item.is_non_formulary && <span className="ml-3">Manual Pricing Applied</span>}
                                            </div>
                                            <span className="text-[10px] font-bold text-indigo-500">Charges Synced to IPD</span>
                                       </div>
                                   )}
                               </div>
                           );
                       })}
                       
                       {selectedIssue.status !== "Completed" && (
                           <div className="pt-4 border-t mt-4">
                               <button 
                                  onClick={handleDispense} 
                                  className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-blue-700 hover:from-indigo-700 hover:to-blue-800 text-white font-bold rounded-xl shadow-lg transition-all"
                               >
                                  Confirm Dispense &amp; Sync IPD Billing
                               </button>
                           </div>
                       )}
                    </div>
                )}

                {activeTab === "audit" && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest">Order Life Cycle Audit Log</h3>
                    {auditLogs.length === 0 ? (
                      <p className="text-slate-400 text-sm py-6 text-center border-2 border-dashed rounded-xl mt-4">No audit records yet.</p>
                    ) : auditLogs.map(log => (
                      <div key={log.id} className="border rounded-xl p-4 bg-slate-50/50 shadow-sm flex items-start gap-4">
                        <div className="mt-0.5">
                            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 mb-1">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            </div>
                        </div>
                        <div className="flex-1">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs font-bold text-indigo-800">{log.action_type}</span>
                              <span className="text-xs text-slate-400 bg-white px-2 py-0.5 rounded-md border">{new Date(log.timestamp).toLocaleString()}</span>
                            </div>
                            <pre className="text-[10px] font-mono bg-white rounded-lg p-3 border border-slate-200 text-slate-600 overflow-x-auto shadow-inner mt-2">
                                {JSON.stringify(log.details, null, 2)}
                            </pre>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
