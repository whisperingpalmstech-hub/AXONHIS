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
  medication_name: string;
  drug_id: string;
  dispensed_quantity: number;
  prescribed_quantity: number;
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
  items: IPDispenseRecordOut[];
}

interface IPReturnItemOut {
  id: string;
  dispense_record_id: string;
  batch_id: string | null;
  batch_number: string | null;
  drug_id: string | null;
  medication_name: string;
  return_quantity: number;
  reason: string;
  condition: string | null;
  is_restockable: boolean;
}

interface IPReturnOut {
  id: string;
  request_type: string;
  issue_id: string;
  patient_id: string | null;
  patient_name: string;
  uhid: string;
  admission_number: string;
  ward: string | null;
  bed_number: string | null;
  status: string;
  requested_by: string;
  request_date: string;
  processed_by: string | null;
  processed_date: string | null;
  remarks: string | null;
  items: IPReturnItemOut[];
}

interface IPReturnLogOut {
  id: string;
  action_type: string;
  details: any;
  timestamp: string;
}

const STATUS_COLORS: Record<string, string> = {
  Pending: "bg-amber-100 text-amber-800 border-amber-200",
  Accepted: "bg-emerald-100 text-emerald-800 border-emerald-200",
  Rejected: "bg-rose-100 text-rose-800 border-rose-200",
};

export default function IPReturnsPage() {
  const [returns, setReturns] = useState<IPReturnOut[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<IPReturnOut | null>(null);
  const [auditLogs, setAuditLogs] = useState<IPReturnLogOut[]>([]);
  
  const [statusFilter, setStatusFilter] = useState("Pending");
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: string; text: string } | null>(null);

  // Form State for Processing
  const [remarks, setRemarks] = useState("");
  const [refundAmount, setRefundAmount] = useState(0);

  const loadRequests = useCallback(async () => {
    setIsLoading(true);
    try {
      const url = statusFilter ? `${API}/api/v1/pharmacy/ip-returns?status=${statusFilter}` : `${API}/api/v1/pharmacy/ip-returns`;
      const res = await fetch(url);
      if (res.ok) setReturns(await res.json());
    } catch (e) {
      console.error(e);
    }
    setIsLoading(false);
  }, [statusFilter]);

  const loadAudit = async (retId: string) => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/ip-returns/${retId}/audit`);
      if (res.ok) setAuditLogs(await res.json());
    } catch (e) { console.error(e); }
  };

  useEffect(() => { loadRequests(); }, [loadRequests]);

  const selectRequest = (req: IPReturnOut) => {
    setSelectedRequest(req);
    setMsg(null);
    setRemarks("");
    setRefundAmount(0); // Optional field, usually would fetch default charges from the issue.
    loadAudit(req.id);
  };

  const handleProcess = async (action: "Accept" | "Reject") => {
    if (!selectedRequest) return;

    try {
      const res = await fetch(`${API}/api/v1/pharmacy/ip-returns/${selectedRequest.id}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
           action,
           remarks: remarks || `${action}ed by pharmacy`,
           refund_amount_total: refundAmount > 0 ? refundAmount : null
        }),
      });

      if (res.ok) {
        setMsg({ type: "success", text: `Return ${action}ed successfully.` });
        loadRequests();
        loadAudit(selectedRequest.id);
        const r2 = await fetch(`${API}/api/v1/pharmacy/ip-returns/${selectedRequest.id}`);
        if (r2.ok) setSelectedRequest(await r2.json());
      } else {
        const err = await res.json();
        setMsg({ type: "error", text: err.detail || `Failed to ${action}` });
      }
    } catch (e) {
      setMsg({ type: "error", text: "Network error" });
    }
  };

  const handleCancelClick = () => {
      setSelectedRequest(null);
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <svg className="w-7 h-7 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            IP Returns & Rejections
          </h1>
          <p className="text-slate-500 text-sm mt-1">Review Nursing medication return and rejection requests, add stock back, and credit IPD bills.</p>
        </div>
      </div>

      {msg && (
        <div className={`px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${msg.type === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-100" : "bg-rose-50 text-rose-700 border border-rose-100"}`}>
          {msg.type === "success" ? "✅" : "⚠️"} {msg.text}
        </div>
      )}

      {/* Main Layout */}
      <div className="flex gap-5 min-h-[600px]">
        {/* Left: Queue */}
        <div className="w-[380px] flex flex-col bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-4 border-b bg-slate-50/80">
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-widest mb-3">Requests Queue</h2>
            <div className="flex flex-wrap gap-2">
              {["Pending", "Accepted", "Rejected", ""].map(s => (
                <button key={s} onClick={() => setStatusFilter(s)} className={`px-3 py-1 text-[11px] rounded-full font-bold transition-all ${statusFilter === s ? "bg-rose-600 text-white shadow-sm" : "bg-slate-100 text-slate-500 hover:bg-slate-200"}`}>
                  {s || "All"}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-50">
            {isLoading ? (
              <div className="flex items-center justify-center h-40 text-slate-400">Loading...</div>
            ) : returns.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-slate-400 p-6 text-center">
                <svg className="w-12 h-12 mb-3 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <p className="text-sm shadow-sm">No return requests found.</p>
                <p className="text-[10px] mt-1">Pending requests from Nursing will appear here.</p>
              </div>
            ) : returns.map(ret => (
              <div key={ret.id} onClick={() => selectRequest(ret)} className={`p-4 cursor-pointer transition-all hover:bg-rose-50/50 ${selectedRequest?.id === ret.id ? "bg-rose-50 border-l-4 border-l-rose-600" : "border-l-4 border-l-transparent"}`}>
                <div className="flex items-start justify-between mb-1">
                  <div>
                    <div className="flex items-center gap-2">
                       <p className="font-bold text-sm text-slate-800">{ret.patient_name}</p>
                       <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase border bg-white border-slate-200 text-slate-600`}>{ret.request_type}</span>
                    </div>
                    <p className="text-xs text-slate-500 font-medium">Adm: {ret.admission_number} • {ret.ward} ({ret.bed_number})</p>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${STATUS_COLORS[ret.status] || "bg-gray-100"}`}>{ret.status}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                  <span>From: {ret.requested_by}</span>
                  <span>{new Date(ret.request_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Workbench */}
        <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
          {!selectedRequest ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300">
              <svg className="w-20 h-20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={0.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <p className="text-lg font-medium">Select a Return Request</p>
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Header */}
              <div className="p-5 bg-gradient-to-r from-rose-600 to-pink-700 text-white flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-3">
                        <h2 className="text-xl font-bold">{selectedRequest.patient_name}</h2>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase bg-white/20 text-white border-white/30`}>{selectedRequest.request_type}</span>
                    </div>
                    <div className="flex gap-4 text-rose-100 text-xs mt-2">
                        <span><strong className="text-white">UHID:</strong> {selectedRequest.uhid}</span>
                        <span><strong className="text-white">Adm:</strong> {selectedRequest.admission_number}</span>
                        <span><strong className="text-white">Loc:</strong> {selectedRequest.ward} - {selectedRequest.bed_number}</span>
                    </div>
                  </div>
                  <div>
                    <span className={`text-xs font-bold px-3 py-1 rounded-full ${selectedRequest.status === 'Accepted' ? 'bg-emerald-400/20 text-emerald-100 border border-emerald-400/30' : selectedRequest.status === 'Rejected' ? 'bg-red-400/20 text-red-100 border border-red-400/30' : 'bg-white/20 text-white border border-white/30'}`}>{selectedRequest.status}</span>
                  </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-5 grid grid-cols-5 gap-6">
                
                {/* Left Col: Items */}
                <div className="col-span-3 space-y-4">
                  <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest mb-2 border-b pb-2">Requested Items</h3>
                  {selectedRequest.items.map(item => (
                    <div key={item.id} className="border rounded-xl p-4 shadow-sm bg-slate-50/50">
                        <div className="flex justify-between items-start mb-2">
                            <div>
                                <h4 className="font-bold text-slate-800 text-base">{item.medication_name}</h4>
                                <div className="text-[10px] text-slate-500 mt-1 flex gap-2">
                                  {item.batch_number && <span className="bg-slate-200 px-1.5 py-0.5 rounded">Batch: {item.batch_number}</span>}
                                  {!item.is_restockable && <span className="text-rose-600 font-bold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-100">DO NOT RESTOCK</span>}
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-[10px] text-slate-400 font-bold uppercase">{selectedRequest.request_type} QTY</p>
                                <p className="text-xl font-black text-rose-600">{item.return_quantity}</p>
                            </div>
                        </div>

                        <div className="mt-3 text-xs bg-white p-2 rounded-lg border flex flex-col gap-1">
                             <div className="flex justify-between">
                                 <span className="text-slate-500">Reason:</span>
                                 <strong className="text-slate-700">{item.reason}</strong>
                             </div>
                             {item.condition && (
                               <div className="flex justify-between">
                                   <span className="text-slate-500">Condition reported:</span>
                                   <strong className="text-slate-700">{item.condition}</strong>
                               </div>
                             )}
                        </div>
                    </div>
                  ))}
                  
                  {/* Audit Logs visually at the bottom of the items */}
                  {auditLogs.length > 0 && (
                    <div className="mt-6 pt-4 border-t">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Audit Log</h4>
                      <div className="space-y-2">
                          {auditLogs.map(log => (
                            <div key={log.id} className="text-xs flex gap-3 text-slate-600">
                                <span className="w-16 text-slate-400 text-[10px]">{new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                <div>
                                   <strong>{log.action_type}</strong>
                                   {log.details.remarks && <p className="text-[10px] italic">"{log.details.remarks}"</p>}
                                </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                </div>

                {/* Right Col: Process Form */}
                <div className="col-span-2">
                  <div className="bg-slate-50 rounded-xl border p-5 sticky top-0">
                    <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest mb-4">Pharmacy Action</h3>
                    
                    {selectedRequest.status === "Pending" ? (
                      <div className="space-y-4">
                        <div>
                          <label className="text-[10px] text-slate-500 font-bold uppercase mb-1 block">Pharmacy Remarks</label>
                          <textarea 
                             rows={3}
                             value={remarks}
                             onChange={(e) => setRemarks(e.target.value)}
                             className="w-full text-sm p-3 border rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-rose-500"
                             placeholder="Enter inspection remarks / reasoning..."
                          />
                        </div>

                        <div>
                          <label className="text-[10px] text-slate-500 font-bold uppercase mb-1 block">IPD Billing Refund Amount (₹)</label>
                          <div className="relative">
                              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">₹</span>
                              <input 
                                type="number" 
                                value={refundAmount}
                                onChange={(e) => setRefundAmount(parseFloat(e.target.value))}
                                className="w-full text-lg font-bold text-slate-800 pl-8 pr-3 py-2 border rounded-lg"
                                placeholder="0.00"
                              />
                          </div>
                          <p className="text-[10px] text-slate-400 mt-1 leading-tight">This will post a credit adjustment reversing the IPD charges if accepted.</p>
                        </div>

                        <div className="pt-4 space-y-2">
                           <button 
                             onClick={() => handleProcess("Accept")}
                             className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-sm transition-all text-sm"
                           >
                              ✅ Accept {selectedRequest.request_type} & Restock
                           </button>
                           <button 
                             onClick={() => handleProcess("Reject")}
                             className="w-full py-3 bg-white border-2 border-slate-200 hover:border-rose-300 hover:text-rose-600 text-slate-600 font-bold rounded-xl shadow-sm transition-all text-sm"
                           >
                              ❌ Reject Request
                           </button>
                           <button onClick={handleCancelClick} className="w-full py-2 text-xs text-slate-400 hover:text-slate-600">Close Panel</button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-6 bg-white rounded-lg border border-dashed">
                          {selectedRequest.status === "Accepted" ? (
                              <svg className="w-12 h-12 mx-auto text-emerald-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                          ) : (
                              <svg className="w-12 h-12 mx-auto text-rose-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                          )}
                          <h4 className="font-bold text-slate-800">{selectedRequest.status} by Pharmacy</h4>
                          <p className="text-xs text-slate-500 mt-1">Processed: {new Date(selectedRequest.processed_date!).toLocaleString()}</p>
                          {selectedRequest.remarks && <p className="text-sm bg-slate-50 p-2 rounded mt-3 border text-slate-600 italic">"{selectedRequest.remarks}"</p>}
                      </div>
                    )}
                  </div>
                </div>

              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
