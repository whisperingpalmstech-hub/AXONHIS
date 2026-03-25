"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, BadgeCheck, Syringe, PackageCheck, CornerDownLeft, 
  RotateCcw, History, AlertTriangle, FileText, CheckCircle2 
} from "lucide-react";

// Helper for native date formatting
const formatDate = (dateString: string) => {
  const d = new Date(dateString);
  return d.toLocaleDateString("en-GB", { day: '2-digit', month: 'short' }) + ", " + 
         d.toLocaleTimeString("en-GB", { hour: '2-digit', minute: '2-digit' });
};

interface NarcoticsOrder {
  id: string;
  patient_name: string;
  uhid: string;
  admission_number: string;
  ward: string;
  bed_number: string;
  prescribing_doctor: string;
  medication_name: string;
  dosage: string;
  requested_quantity: number;
  order_date: string;
  status: string;
  dispenses: any[];
  returns: any[];
}

export default function NarcoticsWorkbench() {
  const [activeTab, setActiveTab] = useState("Validation");
  const [orders, setOrders] = useState<NarcoticsOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<NarcoticsOrder | null>(null);

  // Forms
  const [remarks, setRemarks] = useState("");
  const [batchNum, setBatchNum] = useState("");
  const [dispenseQty, setDispenseQty] = useState("");
  const [nurseName, setNurseName] = useState("");

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const rs = await fetch(`${u}/api/v1/pharmacy/narcotics/orders`);
      if (rs.ok) {
        const data = await rs.json();
        setOrders(data);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchOrders();
  }, [activeTab]);

  const handleValidation = async (action: "Approve" | "Reject") => {
    if (!selectedOrder) return;
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const rs = await fetch(`${u}/api/v1/pharmacy/narcotics/orders/${selectedOrder.id}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, remarks })
      });
      if (!rs.ok) {
        const err = await rs.json();
        throw new Error(err.detail || "Request failed");
      }
      alert(`Order ${action}d successfully. Check audit logs.`);
      setRemarks("");
      setSelectedOrder(null);
      fetchOrders();
    } catch (e: any) {
      alert("Error: " + e.message);
    }
  };

  const handleDispense = async () => {
    if (!selectedOrder) return;
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const rs = await fetch(`${u}/api/v1/pharmacy/narcotics/orders/${selectedOrder.id}/dispense`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          batch_number: batchNum,
          dispensed_quantity: parseFloat(dispenseQty)
        })
      });
      if (!rs.ok) {
        const err = await rs.json();
        throw new Error(err.detail || "Request failed");
      }
      alert("Narcotics precisely dispensed. Inventory deducted.");
      setBatchNum(""); setDispenseQty("");
      setSelectedOrder(null);
      fetchOrders();
    } catch (e: any) {
      alert("Error: " + e.message);
    }
  };

  const filteredOrders = orders.filter(o => {
    if (activeTab === "Validation") return o.status === "Pending Validation";
    if (activeTab === "Dispensing") return o.status === "Approved";
    if (activeTab === "Delivery") return o.status === "Dispensed";
    if (activeTab === "Ampoule Tracking") return o.status === "Delivered" || o.status === "Completed";
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 font-sans">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-rose-900/50">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <ShieldAlert className="w-8 h-8 text-rose-500" />
              Narcotics Store Dashboard
            </h1>
            <p className="text-slate-400 mt-2">Controlled Schedule-X Dispensing & Compliance Matrix</p>
          </div>
          <button 
            onClick={fetchOrders}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg transition-colors border border-slate-700"
          >
            <RotateCcw className="w-4 h-4" /> Refresh Matrix
          </button>
        </div>

        {/* Tab Nav */}
        <div className="flex space-x-2 mb-6 bg-slate-800/50 p-1.5 rounded-xl border border-slate-700/50 w-fit">
          {["Validation", "Dispensing", "Delivery", "Ampoule Tracking"].map(tab => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); setSelectedOrder(null); }}
              className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab 
                  ? "bg-rose-600 shadow-[0_0_15px_rgba(225,29,72,0.4)] text-white" 
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
              }`}
            >
              {tab === "Validation" && <BadgeCheck className="w-4 h-4 inline mr-2" />}
              {tab === "Dispensing" && <Syringe className="w-4 h-4 inline mr-2" />}
              {tab === "Delivery" && <PackageCheck className="w-4 h-4 inline mr-2" />}
              {tab === "Ampoule Tracking" && <CornerDownLeft className="w-4 h-4 inline mr-2" />}
              {tab}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Left Column - Worklist */}
          <div className="col-span-12 lg:col-span-5 flex flex-col gap-4">
            <h3 className="text-lg font-semibold text-slate-300 flex items-center gap-2">
              <History className="w-5 h-5 text-slate-400" /> 
              {activeTab} Queue ({filteredOrders.length})
            </h3>
            
            <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl h-[600px] overflow-y-auto">
              {loading ? (
                <div className="p-8 text-center text-slate-500">Loading secure queue...</div>
              ) : filteredOrders.length === 0 ? (
                <div className="p-8 text-center text-slate-500 flex flex-col items-center">
                  <CheckCircle2 className="w-12 h-12 mb-3 text-emerald-500/50" />
                  No pending tasks in {activeTab}.
                </div>
              ) : (
                <div className="divide-y divide-slate-700/50">
                  {filteredOrders.map(o => (
                    <div 
                      key={o.id}
                      onClick={() => setSelectedOrder(o)}
                      className={`p-5 cursor-pointer hover:bg-slate-700/30 transition-colors ${
                        selectedOrder?.id === o.id ? "bg-slate-700/50 border-l-4 border-rose-500" : "border-l-4 border-transparent"
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-semibold text-rose-400">{o.medication_name}</span>
                        <span className="text-xs bg-slate-900 border border-slate-700 px-2 py-1 rounded text-slate-300">
                          Qty: {o.requested_quantity}
                        </span>
                      </div>
                      <div className="text-sm text-slate-300">{o.patient_name} ({o.uhid})</div>
                      <div className="text-xs text-slate-500 mt-1">Ward: {o.ward} | Dr. {o.prescribing_doctor}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Action Panel */}
          <div className="col-span-12 lg:col-span-7">
            {!selectedOrder ? (
              <div className="bg-slate-800/20 border border-slate-700/30 rounded-2xl h-[600px] flex items-center justify-center text-slate-500 flex-col">
                <FileText className="w-16 h-16 mb-4 opacity-50" />
                Select a restricted order from the queue to process.
              </div>
            ) : (
              <div className="bg-slate-800/80 border border-slate-700 rounded-2xl h-[600px] p-8 flex flex-col relative overflow-hidden shadow-xl">
                {/* Security Watermark */}
                <div className="absolute top-10 right-10 opacity-5 rotate-12 pointer-events-none">
                  <ShieldAlert className="w-64 h-64" />
                </div>

                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-6">
                    <span className="bg-rose-500/20 text-rose-400 border border-rose-500/50 px-3 py-1 rounded-full text-xs font-bold tracking-widest uppercase flex items-center gap-2">
                       <AlertTriangle className="w-3 h-3" /> Schedule X Narcotics
                    </span>
                    <span className="text-sm text-slate-400 flex-1 text-right">
                      Ord: {formatDate(selectedOrder.order_date)}
                    </span>
                  </div>

                  <h2 className="text-2xl font-bold mb-1">{selectedOrder.medication_name} ({selectedOrder.dosage})</h2>
                  <p className="text-xl text-rose-300 mb-6 font-mono">Rx Qty: {selectedOrder.requested_quantity}</p>

                  <div className="grid grid-cols-2 gap-4 mb-8 bg-slate-900/50 p-5 rounded-xl border border-slate-700/50">
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Patient</div>
                      <div className="font-semibold">{selectedOrder.patient_name}</div>
                      <div className="text-sm text-slate-400">{selectedOrder.uhid} - {selectedOrder.admission_number}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Location / Dr</div>
                      <div className="font-semibold">{selectedOrder.ward} - {selectedOrder.bed_number}</div>
                      <div className="text-sm text-slate-400">Dr. {selectedOrder.prescribing_doctor}</div>
                    </div>
                  </div>

                  {/* Dynamic Action Forms based on Tab */}
                  
                  {activeTab === "Validation" && (
                    <div className="space-y-4 bg-slate-900/40 p-5 rounded-xl border border-slate-700/50">
                      <h4 className="font-semibold text-rose-400 border-b border-slate-700/50 pb-2 mb-4">Pharmacist In-Charge Validation</h4>
                      <div>
                        <label className="block text-sm text-slate-400 mb-2">Compliance Remarks (Required for Rejection)</label>
                        <textarea 
                          value={remarks} onChange={e => setRemarks(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:border-rose-500 focus:ring-1 focus:ring-rose-500 outline-none h-24"
                          placeholder="e.g. Protocol verified, dose appropriate..."
                        />
                      </div>
                      <div className="flex gap-4 pt-2">
                        <button onClick={() => handleValidation("Approve")} className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-lg shadow-lg flex items-center justify-center gap-2 transition-all">
                          <CheckCircle2 className="w-5 h-5"/> Authorize Dispensing
                        </button>
                        <button onClick={() => handleValidation("Reject")} className="flex-1 bg-slate-700 hover:bg-rose-900/80 text-rose-400 font-semibold py-3 rounded-lg border border-slate-600 hover:border-rose-500 transition-all">
                          Reject Order
                        </button>
                      </div>
                    </div>
                  )}

                  {activeTab === "Dispensing" && (
                     <div className="space-y-4 bg-slate-900/40 p-5 rounded-xl border border-slate-700/50 mt-4">
                     <h4 className="font-semibold text-rose-400 border-b border-slate-700/50 pb-2">Record Dispensation</h4>
                     <div className="grid grid-cols-2 gap-4">
                       <div>
                          <label className="block text-sm text-slate-400 mb-2">Batch Number</label>
                          <input type="text" value={batchNum} onChange={e => setBatchNum(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 outline-none"
                            placeholder="Scan or type..." />
                       </div>
                       <div>
                          <label className="block text-sm text-slate-400 mb-2">Dispensed Qty</label>
                          <input type="number" value={dispenseQty} onChange={e => setDispenseQty(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 outline-none font-mono text-rose-300"
                            placeholder="Strict match..." />
                       </div>
                     </div>
                     <button onClick={handleDispense} className="w-full bg-rose-600 hover:bg-rose-500 text-white font-semibold py-3 rounded-lg shadow-[0_0_15px_rgba(225,29,72,0.3)] mt-4 items-center justify-center flex gap-2">
                       <Syringe className="w-5 h-5"/> Dispense from Narcotics Vault
                     </button>
                   </div>
                  )}

                  {/* Delivery dummy display */}
                  {activeTab === "Delivery" && (
                    <div className="p-6 bg-emerald-900/20 text-emerald-300 border border-emerald-500/30 rounded-xl text-center">
                      <PackageCheck className="w-12 h-12 mx-auto mb-3 opacity-80" />
                      <h3 className="text-xl font-bold">Ready for Nursing Collect</h3>
                      <p className="mt-2 text-sm opacity-80">This module is locked until Duty Nurse provides authorization signature via Handover Tablet.</p>
                      <button className="mt-6 bg-slate-800 text-slate-300 px-6 py-2 rounded-full border border-slate-600 hover:bg-slate-700">Acknowledge Handover (Mock)</button>
                    </div>
                  )}

                  {/* Ampoules */}
                  {activeTab === "Ampoule Tracking" && (
                    <div className="p-6 bg-slate-900/50 border border-amber-500/30 rounded-xl">
                      <div className="flex items-center gap-3 mb-4">
                        <CornerDownLeft className="w-6 h-6 text-amber-500" />
                        <h3 className="font-bold text-lg text-amber-500">Empty Ampoule Return Audit</h3>
                      </div>
                      <p className="text-slate-400 text-sm mb-6">By law, empty narcotics ampoules must be accounted for by the returning nurse before finalizing the episode.</p>
                      
                      {selectedOrder.returns?.length > 0 ? (
                        <div className="bg-emerald-900/20 border border-emerald-500/20 p-4 rounded-lg">
                          Returns Processed: <strong className="text-emerald-400">{selectedOrder.returns.length}</strong> Ampoules Validated.
                        </div>
                      ) : (
                        <div className="text-center p-4 bg-slate-800 rounded border border-dashed border-slate-600 text-slate-500">
                          Awaiting Nurse Physical Return...
                        </div>
                      )}
                    </div>
                  )}

                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
