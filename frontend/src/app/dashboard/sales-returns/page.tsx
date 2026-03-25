"use client";
import React, { useState, useEffect, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

interface ReturnItem {
  id: string;
  medication_name: string;
  batch_number: string | null;
  quantity_sold: number;
  quantity_returned: number;
  unit_price: number;
  refund_amount: number;
  reason_text: string | null;
  is_eligible: boolean;
  eligibility_note: string | null;
  stock_restored: boolean;
}

interface Refund {
  id: string;
  refund_amount: number;
  refund_mode: string;
  transaction_ref: string | null;
  refunded_at: string;
}

interface SalesReturn {
  id: string;
  return_number: string;
  sale_id: string | null;
  bill_number: string | null;
  patient_name: string | null;
  uhid: string | null;
  mobile: string | null;
  pharmacist_name: string | null;
  total_refund_amount: number;
  net_refund: number;
  status: string;
  sale_date: string | null;
  return_date: string;
  notes: string | null;
  created_at: string;
  items: ReturnItem[];
  refund: Refund | null;
}

interface AuditLog {
  id: string;
  return_id: string;
  pharmacist_id: string | null;
  action_type: string;
  details: Record<string, unknown>;
  timestamp: string;
}

interface ReturnReason {
  id: string;
  reason_code: string;
  reason_text: string;
  requires_approval: boolean;
}

const STATUS_BADGE: Record<string, string> = {
  Pending: "bg-amber-100 text-amber-800 border-amber-200",
  Completed: "bg-emerald-100 text-emerald-800 border-emerald-200",
  Rejected: "bg-rose-100 text-rose-800 border-rose-200",
};

export default function SalesReturnsPage() {
  const [returns, setReturns] = useState<SalesReturn[]>([]);
  const [selectedReturn, setSelectedReturn] = useState<SalesReturn | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [reasons, setReasons] = useState<ReturnReason[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [activeTab, setActiveTab] = useState<"details" | "refund" | "audit">("details");
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: string; text: string } | null>(null);

  // New Return Form
  const [showNewReturn, setShowNewReturn] = useState(false);
  const [newReturn, setNewReturn] = useState({
    bill_number: "",
    patient_name: "",
    uhid: "",
    mobile: "",
    notes: "",
  });
  const [newItems, setNewItems] = useState<
    {
      medication_name: string;
      quantity_sold: number;
      quantity_returned: number;
      unit_price: number;
      reason_text: string;
      batch_number: string;
    }[]
  >([]);

  // Refund form
  const [refundMode, setRefundMode] = useState("Cash");
  const [refundRef, setRefundRef] = useState("");

  const loadReturns = useCallback(async () => {
    setIsLoading(true);
    try {
      const url = statusFilter
        ? `${API}/api/v1/pharmacy/sales-returns?status=${statusFilter}`
        : `${API}/api/v1/pharmacy/sales-returns`;
      const res = await fetch(url);
      if (res.ok) setReturns(await res.json());
    } catch (e) { console.error(e); }
    setIsLoading(false);
  }, [statusFilter]);

  const loadReasons = async () => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/sales-returns/config/reasons`);
      if (res.ok) setReasons(await res.json());
    } catch (e) { console.error(e); }
  };

  const loadAudit = async (returnId: string) => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/sales-returns/${returnId}/audit`);
      if (res.ok) setAuditLogs(await res.json());
    } catch (e) { console.error(e); }
  };

  useEffect(() => { loadReturns(); loadReasons(); }, [loadReturns]);

  const selectReturn = (r: SalesReturn) => {
    setSelectedReturn(r);
    setActiveTab("details");
    setMsg(null);
    loadAudit(r.id);
  };

  const addItemRow = () => {
    setNewItems([...newItems, {
      medication_name: "", quantity_sold: 0, quantity_returned: 0,
      unit_price: 0, reason_text: "Unused medication", batch_number: "",
    }]);
  };

  const removeItemRow = (idx: number) => {
    setNewItems(newItems.filter((_, i) => i !== idx));
  };

  const submitReturn = async () => {
    if (!newReturn.patient_name || newItems.length === 0) {
      setMsg({ type: "error", text: "Patient name and at least one item required" });
      return;
    }
    setMsg(null);
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/sales-returns`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newReturn,
          sale_date: new Date().toISOString(),
          items: newItems,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setMsg({ type: "success", text: `Return ${data.return_number} created!` });
        setShowNewReturn(false);
        setNewReturn({ bill_number: "", patient_name: "", uhid: "", mobile: "", notes: "" });
        setNewItems([]);
        loadReturns();
      } else {
        const err = await res.json();
        setMsg({ type: "error", text: err.detail || "Failed to create return" });
      }
    } catch (e) {
      setMsg({ type: "error", text: "Network error" });
    }
  };

  const processRefund = async () => {
    if (!selectedReturn) return;
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/sales-returns/${selectedReturn.id}/refund`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refund_mode: refundMode, transaction_ref: refundRef || null }),
      });
      if (res.ok) {
        setMsg({ type: "success", text: "Refund processed & stock restored!" });
        loadReturns();
        loadAudit(selectedReturn.id);
        // Refresh selected
        const r2 = await fetch(`${API}/api/v1/pharmacy/sales-returns/${selectedReturn.id}`);
        if (r2.ok) setSelectedReturn(await r2.json());
      } else {
        const err = await res.json();
        setMsg({ type: "error", text: err.detail || "Refund failed" });
      }
    } catch (e) {
      setMsg({ type: "error", text: "Network error" });
    }
  };

  const seedMock = async () => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/sales-returns/seed-mock`, { method: "POST" });
      if (res.ok) {
        setMsg({ type: "success", text: "Mock return seeded!" });
        loadReturns();
      }
    } catch (e) { console.error(e); }
  };

  const seedReasons = async () => {
    await fetch(`${API}/api/v1/pharmacy/sales-returns/config/seed-reasons`, { method: "POST" });
    loadReasons();
    setMsg({ type: "success", text: "Return reasons seeded!" });
  };

  const totalNewRefund = newItems.reduce((a, i) => a + i.quantity_returned * i.unit_price, 0);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <svg className="w-7 h-7 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
            </svg>
            OP Pharmacy Sales Returns
          </h1>
          <p className="text-slate-500 text-sm mt-1">Process medication returns, validate eligibility, generate refund receipts &amp; restore stock.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={seedReasons} className="px-3 py-2 bg-slate-100 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-200 transition">Seed Reasons</button>
          <button onClick={seedMock} className="px-3 py-2 bg-slate-100 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-200 transition">Seed Mock</button>
          <button onClick={() => { setShowNewReturn(true); setSelectedReturn(null); }} className="px-4 py-2 bg-rose-600 text-white rounded-xl text-sm font-semibold hover:bg-rose-700 transition-all shadow-sm">+ New Return</button>
        </div>
      </div>

      {msg && (
        <div className={`px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${msg.type === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-100" : "bg-rose-50 text-rose-700 border border-rose-100"}`}>
          {msg.type === "success" ? "✅" : "⚠️"} {msg.text}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Returns", value: returns.length, bg: "from-slate-500 to-slate-700", icon: "📦" },
          { label: "Pending", value: returns.filter(r => r.status === "Pending").length, bg: "from-amber-500 to-orange-600", icon: "⏳" },
          { label: "Completed", value: returns.filter(r => r.status === "Completed").length, bg: "from-emerald-500 to-green-600", icon: "✅" },
          { label: "Total Refunded", value: `₹${returns.filter(r => r.status === "Completed").reduce((a, r) => a + r.net_refund, 0).toFixed(2)}`, bg: "from-rose-500 to-pink-600", icon: "💰" },
        ].map((s, i) => (
          <div key={i} className={`bg-gradient-to-br ${s.bg} rounded-xl p-4 text-white shadow-lg`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium opacity-80">{s.label}</p>
                <p className="text-2xl font-bold mt-1">{s.value}</p>
              </div>
              <span className="text-3xl opacity-50">{s.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Main Layout */}
      <div className="flex gap-5 min-h-[600px]">
        {/* Left: Return List */}
        <div className="w-[400px] flex flex-col bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-4 border-b bg-slate-50/80">
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-widest mb-3">Return Transactions</h2>
            <div className="flex gap-2">
              {["", "Pending", "Completed"].map(s => (
                <button key={s} onClick={() => setStatusFilter(s)} className={`px-3 py-1 text-xs rounded-full font-medium transition-all ${statusFilter === s ? "bg-rose-600 text-white shadow-sm" : "bg-slate-100 text-slate-500 hover:bg-slate-200"}`}>
                  {s || "All"}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-50">
            {isLoading ? (
              <div className="flex items-center justify-center h-40 text-slate-400">Loading...</div>
            ) : returns.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-slate-400">
                <p className="text-sm">No return transactions</p>
                <p className="text-xs mt-1">Click &quot;Seed Mock&quot; or &quot;New Return&quot;</p>
              </div>
            ) : returns.map(r => (
              <div key={r.id} onClick={() => selectReturn(r)} className={`p-4 cursor-pointer transition-all hover:bg-rose-50/50 ${selectedReturn?.id === r.id ? "bg-rose-50 border-l-4 border-l-rose-600" : "border-l-4 border-l-transparent"}`}>
                <div className="flex items-start justify-between mb-1">
                  <div>
                    <p className="font-bold text-sm text-slate-800">{r.patient_name}</p>
                    <p className="text-xs text-slate-500">{r.return_number} • {r.uhid}</p>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${STATUS_BADGE[r.status] || "bg-gray-100"}`}>{r.status}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500 mt-2">
                  <span>{r.items.length} items</span>
                  <span>•</span>
                  <span className="font-semibold text-rose-600">₹{r.net_refund.toFixed(2)}</span>
                  <span>•</span>
                  <span>{new Date(r.return_date).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Detail / New Return Form */}
        <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
          {showNewReturn ? (
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <svg className="w-5 h-5 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                New Return Transaction
              </h2>

              {/* Patient Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Patient Name *</label>
                  <input value={newReturn.patient_name} onChange={e => setNewReturn({ ...newReturn, patient_name: e.target.value })} className="border rounded-lg px-3 py-2 w-full text-sm" placeholder="e.g. Rahul Sharma" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">UHID</label>
                  <input value={newReturn.uhid} onChange={e => setNewReturn({ ...newReturn, uhid: e.target.value })} className="border rounded-lg px-3 py-2 w-full text-sm" placeholder="e.g. UHID1234" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Bill Number</label>
                  <input value={newReturn.bill_number} onChange={e => setNewReturn({ ...newReturn, bill_number: e.target.value })} className="border rounded-lg px-3 py-2 w-full text-sm" placeholder="e.g. BILL-001" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Mobile</label>
                  <input value={newReturn.mobile} onChange={e => setNewReturn({ ...newReturn, mobile: e.target.value })} className="border rounded-lg px-3 py-2 w-full text-sm" placeholder="e.g. 9876543210" />
                </div>
              </div>

              {/* Items */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest">Return Items</h3>
                  <button onClick={addItemRow} className="px-3 py-1.5 bg-rose-50 text-rose-700 rounded-lg text-xs font-bold hover:bg-rose-100 transition">+ Add Item</button>
                </div>

                {newItems.length === 0 && <p className="text-slate-400 text-sm py-4 text-center border rounded-xl border-dashed">Click &quot;Add Item&quot; to add medications for return</p>}

                {newItems.map((item, idx) => (
                  <div key={idx} className="border border-slate-100 rounded-xl p-4 mb-3 bg-slate-50/50 shadow-sm">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold text-slate-500">Item #{idx + 1}</span>
                      <button onClick={() => removeItemRow(idx)} className="text-rose-500 text-xs hover:underline">Remove</button>
                    </div>
                    <div className="grid grid-cols-3 gap-3 mb-3">
                      <div className="col-span-2">
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Medication *</label>
                        <input value={item.medication_name} onChange={e => { const u = [...newItems]; u[idx].medication_name = e.target.value; setNewItems(u); }} className="border rounded-lg px-3 py-2 w-full text-sm" placeholder="e.g. Paracetamol 650mg" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Batch #</label>
                        <input value={item.batch_number} onChange={e => { const u = [...newItems]; u[idx].batch_number = e.target.value; setNewItems(u); }} className="border rounded-lg px-3 py-2 w-full text-sm" />
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-3 mb-3">
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Qty Sold</label>
                        <input type="number" min="0" value={item.quantity_sold} onChange={e => { const u = [...newItems]; u[idx].quantity_sold = parseFloat(e.target.value) || 0; setNewItems(u); }} className="border rounded-lg px-3 py-2 w-full text-sm" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Qty Return</label>
                        <input type="number" min="0" value={item.quantity_returned} onChange={e => { const u = [...newItems]; u[idx].quantity_returned = parseFloat(e.target.value) || 0; setNewItems(u); }} className="border rounded-lg px-3 py-2 w-full text-sm" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Unit Price (₹)</label>
                        <input type="number" min="0" step="0.01" value={item.unit_price} onChange={e => { const u = [...newItems]; u[idx].unit_price = parseFloat(e.target.value) || 0; setNewItems(u); }} className="border rounded-lg px-3 py-2 w-full text-sm" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Refund</label>
                        <p className="text-lg font-bold text-rose-700 mt-1">₹{(item.quantity_returned * item.unit_price).toFixed(2)}</p>
                      </div>
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Return Reason</label>
                      <select value={item.reason_text} onChange={e => { const u = [...newItems]; u[idx].reason_text = e.target.value; setNewItems(u); }} className="border rounded-lg px-3 py-2 w-full text-sm bg-white">
                        <option>Unused medication</option>
                        <option>Wrong medication dispensed</option>
                        <option>Adverse drug reaction</option>
                        <option>Patient refusal</option>
                        <option>Medication expired before use</option>
                        <option>Dosage changed by doctor</option>
                        <option>Duplicate dispensing</option>
                        {reasons.map(r => <option key={r.id} value={r.reason_text}>{r.reason_text}</option>)}
                      </select>
                    </div>
                  </div>
                ))}
              </div>

              {/* Summary */}
              {newItems.length > 0 && (
                <div className="border-t pt-4 flex justify-between items-center">
                  <span className="font-medium text-slate-600">Total Refund</span>
                  <span className="text-2xl font-bold text-rose-700">₹{totalNewRefund.toFixed(2)}</span>
                </div>
              )}

              <div className="flex gap-3">
                <button onClick={() => setShowNewReturn(false)} className="flex-1 py-3 border rounded-xl text-slate-600 font-medium hover:bg-slate-50">Cancel</button>
                <button onClick={submitReturn} disabled={newItems.length === 0} className="flex-1 py-3 bg-gradient-to-r from-rose-600 to-pink-700 text-white font-bold rounded-xl hover:from-rose-700 hover:to-pink-800 disabled:opacity-50 shadow-lg transition-all">Submit Return Request</button>
              </div>
            </div>
          ) : !selectedReturn ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300">
              <svg className="w-20 h-20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={0.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
              </svg>
              <p className="text-lg font-medium">Select a return transaction</p>
              <p className="text-sm mt-1">or create a new return</p>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="p-5 bg-gradient-to-r from-rose-600 to-pink-700 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold">{selectedReturn.return_number}</h2>
                    <p className="text-rose-200 text-sm mt-0.5">{selectedReturn.patient_name} • UHID: {selectedReturn.uhid} • Bill: {selectedReturn.bill_number}</p>
                  </div>
                  <span className={`text-xs font-bold px-3 py-1 rounded-full ${selectedReturn.status === "Completed" ? "bg-green-400/20 text-green-100" : "bg-white/20 text-white"}`}>{selectedReturn.status}</span>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b bg-slate-50/50">
                {([
                  { key: "details", label: "Return Items" },
                  { key: "refund", label: "Process Refund" },
                  { key: "audit", label: "Audit Trail" },
                ] as { key: "details" | "refund" | "audit"; label: string }[]).map(tab => (
                  <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`px-5 py-3 text-sm font-medium transition-all border-b-2 ${activeTab === tab.key ? "border-rose-600 text-rose-700 bg-white" : "border-transparent text-slate-500 hover:text-slate-700"}`}>{tab.label}</button>
                ))}
              </div>

              <div className="flex-1 overflow-y-auto p-5">
                {activeTab === "details" && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest">Returned Medications</h3>
                    {selectedReturn.items.map((item, i) => (
                      <div key={i} className="border border-slate-100 rounded-xl p-4 bg-slate-50/50 shadow-sm">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="font-bold text-slate-800">{item.medication_name}</p>
                            <p className="text-xs text-slate-500">Batch: {item.batch_number || "N/A"} • Reason: {item.reason_text}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            {item.is_eligible ? (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">ELIGIBLE</span>
                            ) : (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 border border-rose-200">INELIGIBLE</span>
                            )}
                            {item.stock_restored && <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">STOCK RESTORED</span>}
                          </div>
                        </div>
                        <div className="grid grid-cols-4 gap-3 text-sm">
                          <div><span className="text-[10px] text-slate-400 uppercase font-bold block">Sold</span>{item.quantity_sold}</div>
                          <div><span className="text-[10px] text-slate-400 uppercase font-bold block">Returned</span>{item.quantity_returned}</div>
                          <div><span className="text-[10px] text-slate-400 uppercase font-bold block">Unit Price</span>₹{item.unit_price}</div>
                          <div><span className="text-[10px] text-slate-400 uppercase font-bold block">Refund</span><span className="font-bold text-rose-700">₹{item.refund_amount.toFixed(2)}</span></div>
                        </div>
                        {!item.is_eligible && item.eligibility_note && (
                          <p className="mt-2 text-xs text-rose-600 bg-rose-50 px-3 py-1.5 rounded-lg">⚠ {item.eligibility_note}</p>
                        )}
                      </div>
                    ))}
                    <div className="border-t pt-4 flex justify-between items-center text-lg">
                      <span className="font-medium text-slate-600">Net Refund Amount</span>
                      <span className="text-2xl font-bold text-rose-700">₹{selectedReturn.net_refund.toFixed(2)}</span>
                    </div>
                  </div>
                )}

                {activeTab === "refund" && (
                  <div className="space-y-5">
                    {selectedReturn.refund ? (
                      <div className="border border-emerald-100 rounded-xl p-5 bg-emerald-50/50">
                        <h3 className="text-sm font-bold text-emerald-800 mb-3">✅ Refund Completed</h3>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div><span className="text-[10px] text-slate-400 uppercase font-bold block">Amount</span>₹{selectedReturn.refund.refund_amount}</div>
                          <div><span className="text-[10px] text-slate-400 uppercase font-bold block">Mode</span>{selectedReturn.refund.refund_mode}</div>
                          <div><span className="text-[10px] text-slate-400 uppercase font-bold block">Reference</span>{selectedReturn.refund.transaction_ref || "N/A"}</div>
                          <div><span className="text-[10px] text-slate-400 uppercase font-bold block">Date</span>{new Date(selectedReturn.refund.refunded_at).toLocaleString()}</div>
                        </div>
                      </div>
                    ) : (
                      <>
                        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest">Process Refund</h3>
                        <div className="border rounded-xl p-5 bg-slate-50/50">
                          <div className="text-center mb-5">
                            <p className="text-sm text-slate-500">Refund Amount</p>
                            <p className="text-4xl font-bold text-rose-700">₹{selectedReturn.net_refund.toFixed(2)}</p>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Refund Mode</label>
                              <select value={refundMode} onChange={e => setRefundMode(e.target.value)} className="border rounded-lg px-3 py-2 w-full text-sm bg-white">
                                <option>Cash</option>
                                <option>Card</option>
                                <option>UPI</option>
                                <option>Wallet</option>
                              </select>
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Transaction Ref</label>
                              <input value={refundRef} onChange={e => setRefundRef(e.target.value)} className="border rounded-lg px-3 py-2 w-full text-sm" placeholder="Optional" />
                            </div>
                          </div>
                          <button onClick={processRefund} className="w-full mt-5 bg-gradient-to-r from-rose-600 to-pink-700 text-white font-bold py-3.5 rounded-xl hover:from-rose-700 hover:to-pink-800 transition-all shadow-lg">Process Refund &amp; Restore Stock</button>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {activeTab === "audit" && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest">Immutable Audit Trail</h3>
                    {auditLogs.length === 0 ? (
                      <p className="text-slate-400 text-sm py-6 text-center">No audit records</p>
                    ) : auditLogs.map(log => (
                      <div key={log.id} className="border rounded-xl p-4 bg-slate-50/50 shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full">{log.action_type}</span>
                          <span className="text-xs text-slate-400">{new Date(log.timestamp).toLocaleString()}</span>
                        </div>
                        <pre className="mt-2 text-xs bg-white rounded-lg p-2 border text-slate-600 overflow-x-auto">{JSON.stringify(log.details, null, 2)}</pre>
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
