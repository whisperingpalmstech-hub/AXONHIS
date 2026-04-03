"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function getHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

interface PrescriptionItem {
  id: string;
  worklist_id: string;
  drug_id: string | null;
  medication_name: string;
  dosage_instructions: string;
  quantity_prescribed: number;
  doctor_notes: string;
  is_non_formulary: boolean;
  substituted_for: string | null;
}

interface WorklistItem {
  id: string;
  patient_id: string | null;
  patient_name: string;
  uhid: string;
  visit_id: string | null;
  doctor_name: string;
  prescription_id: string;
  prescription_date: string;
  status: string;
  created_at: string;
  prescriptions: PrescriptionItem[];
}

interface AuditLog {
  id: string;
  worklist_id: string;
  pharmacist_id: string;
  action_type: string;
  details: Record<string, unknown>;
  timestamp: string;
}

const STATUS_COLORS: Record<string, string> = {
  Pending: "bg-amber-100 text-amber-800 border-amber-200",
  "In Progress": "bg-blue-100 text-blue-800 border-blue-200",
  Dispensed: "bg-emerald-100 text-emerald-800 border-emerald-200",
  Completed: "bg-green-100 text-green-800 border-green-200",
};

const PRIORITY_COLORS: Record<string, string> = {
  STAT: "bg-red-500 text-white",
  URGENT: "bg-orange-500 text-white",
  ROUTINE: "bg-slate-200 text-slate-700",
};

export default function RxWorklistPage() {
  const { t } = useTranslation();
  const [worklist, setWorklist] = useState<WorklistItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<WorklistItem | null>(null);
  const [activeTab, setActiveTab] = useState<"queue" | "dispensing" | "audit">("queue");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDispensing, setIsDispensing] = useState(false);
  const [msg, setMsg] = useState<{ type: string; text: string } | null>(null);

  // Substitute Engine State
  const [showEngineIdx, setShowEngineIdx] = useState<number | null>(null);
  const [engineResults, setEngineResults] = useState<any[]>([]);
  const [isEngineLoading, setIsEngineLoading] = useState(false);

  // Dispensing state
  const [dispenseItems, setDispenseItems] = useState<
    {
      prescription_id: string;
      medication_name: string;
      quantity_prescribed: number;
      quantity_dispensed: number;
      dosage_instructions: string;
      unit_price: number;
      is_non_formulary: boolean;
      substituted_for: string;
      substitute_name: string;
    }[]
  >([]);

  const loadWorklist = useCallback(async () => {
    setIsLoading(true);
    try {
      const url = statusFilter
        ? `${API}/api/v1/pharmacy/sales-worklist?status=${statusFilter}`
        : `${API}/api/v1/pharmacy/sales-worklist`;
      const res = await fetch(url, { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setWorklist(data);
      }
    } catch (e) {
      console.error(e);
    }
    setIsLoading(false);
  }, [statusFilter]);

  useEffect(() => {
    loadWorklist();
  }, [loadWorklist]);

  const loadAuditLogs = async (worklistId: string) => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/sales-worklist/${worklistId}/audit`, {
        headers: getHeaders(),
      });
      if (res.ok) {
        setAuditLogs(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  const selectItem = (item: WorklistItem) => {
    setSelectedItem(item);
    setActiveTab("dispensing");
    setMsg(null);
    setShowEngineIdx(null);
    setEngineResults([]);
    // Populate dispense form from prescriptions
    setDispenseItems(
      item.prescriptions.map((p) => ({
        prescription_id: p.id,
        medication_name: p.medication_name,
        quantity_prescribed: p.quantity_prescribed,
        quantity_dispensed: p.quantity_prescribed,
        dosage_instructions: p.dosage_instructions || "",
        unit_price: 0,
        is_non_formulary: p.is_non_formulary,
        substituted_for: "",
        substitute_name: "",
      }))
    );
    loadAuditLogs(item.id);
  };

  const handleDispense = async () => {
    if (!selectedItem) return;
    setIsDispensing(true);
    setMsg(null);
    try {
      const payload = {
        pharmacist_id: "00000000-0000-0000-0000-000000000001",
        billing_transaction_id: null,
        items: dispenseItems.map((d) => ({
          prescription_id: d.prescription_id,
          drug_id: null,
          medication_name: d.substitute_name || d.medication_name,
          quantity_dispensed: d.quantity_dispensed,
          dosage_instructions: d.dosage_instructions,
          unit_price: d.unit_price,
          is_non_formulary: d.is_non_formulary,
          substituted_for: d.substituted_for || null,
          batches: [],
        })),
      };
      const res = await fetch(
        `${API}/api/v1/pharmacy/sales-worklist/${selectedItem.id}/dispense`,
        {
          method: "POST",
          headers: getHeaders(),
          body: JSON.stringify(payload),
        }
      );
      if (res.ok) {
        setMsg({ type: "success", text: "Medications dispensed successfully! Bill generated." });
        await loadWorklist();
        loadAuditLogs(selectedItem.id);
        // Refresh the selected item
        const updatedRes = await fetch(
          `${API}/api/v1/pharmacy/sales-worklist/${selectedItem.id}`,
          { headers: getHeaders() }
        );
        if (updatedRes.ok) setSelectedItem(await updatedRes.json());
      } else {
        const err = await res.json();
        setMsg({ type: "error", text: err.detail || "Dispensing failed" });
      }
    } catch (e) {
      setMsg({ type: "error", text: "Network error" });
    }
    setIsDispensing(false);
  };

  const handleEngineLookup = async (idx: number, keyword: string) => {
    if (!keyword) return;
    setShowEngineIdx(idx);
    setIsEngineLoading(true);
    setEngineResults([]);
    try {
      // Use existing endpoint, fallback gracefully if not integrated exactly, but we will reuse the inventory intelligence query
      const res = await fetch(`${API}/api/v1/pharmacy/inventory/search?query=${encodeURIComponent(keyword)}`, { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setEngineResults(data);
      }
    } catch (e) {
      console.error(e);
    }
    setIsEngineLoading(false);
  };

  const handleSeedMockData = async () => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/sales-worklist/seed_mock_data`, {
        method: "POST",
        headers: getHeaders(),
      });
      if (res.ok) {
        setMsg({ type: "success", text: "Mock prescription seeded successfully!" });
        loadWorklist();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const filteredWorklist = worklist.filter((w) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        w.patient_name.toLowerCase().includes(q) ||
        w.uhid.toLowerCase().includes(q) ||
        w.doctor_name.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const totalBill = dispenseItems.reduce(
    (a, d) => a + d.quantity_dispensed * d.unit_price,
    0
  );

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <svg
              className="w-7 h-7 text-violet-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z"
              />
            </svg>
            OP Pharmacy {t("rxWorklist.title")}
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Manage OPD prescriptions — review, dispense medications, generate bills &
            update records.
          </p>
        </div>

      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4">
        {[
          {
            label: "Total Prescriptions",
            value: worklist.length,
            color: "bg-gradient-to-br from-violet-500 to-purple-600",
            icon: "📋",
          },
          {
            label: "Pending",
            value: worklist.filter((w) => w.status === "Pending").length,
            color: "bg-gradient-to-br from-amber-500 to-orange-600",
            icon: "⏳",
          },
          {
            label: "In Progress",
            value: worklist.filter((w) => w.status === "In Progress").length,
            color: "bg-gradient-to-br from-blue-500 to-cyan-600",
            icon: "🔄",
          },
          {
            label: "Completed",
            value: worklist.filter((w) => w.status === "Completed").length,
            color: "bg-gradient-to-br from-emerald-500 to-green-600",
            icon: "✅",
          },
        ].map((stat, i) => (
          <div
            key={i}
            className={`${stat.color} rounded-xl p-4 text-white shadow-lg`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium opacity-80">{stat.label}</p>
                <p className="text-3xl font-bold mt-1">{stat.value}</p>
              </div>
              <span className="text-3xl opacity-50">{stat.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Main Layout */}
      <div className="flex gap-5 min-h-[600px]">
        {/* Left: Queue List */}
        <div className="w-[420px] flex flex-col bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          {/* Queue Header */}
          <div className="p-4 border-b bg-slate-50/80">
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-widest mb-3">
              Prescription Queue
            </h2>
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search patient, UHID, doctor..."
              className="w-full border rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-violet-200 focus:border-violet-400 outline-none transition"
            />
            <div className="flex gap-2 mt-3">
              {["", "Pending", "In Progress", "Completed"].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`px-3 py-1 text-xs rounded-full font-medium transition-all ${
                    statusFilter === s
                      ? "bg-violet-600 text-white shadow-sm"
                      : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                  }`}
                >
                  {s || "All"}
                </button>
              ))}
            </div>
          </div>

          {/* Queue Items */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-50">
            {isLoading ? (
              <div className="flex items-center justify-center h-40 text-slate-400">
                <svg className="w-6 h-6 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Loading...
              </div>
            ) : filteredWorklist.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-slate-400">
                <svg
                  className="w-12 h-12 mb-2 text-slate-200"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08"
                  />
                </svg>
                <p className="text-sm">No prescriptions in queue</p>
                <p className="text-xs mt-1 text-slate-400 font-medium italic">Waiting for new clinical orders from Doctor Desk...</p>
              </div>
            ) : (
              filteredWorklist.map((item) => (
                <div
                  key={item.id}
                  onClick={() => selectItem(item)}
                  className={`p-4 cursor-pointer transition-all hover:bg-violet-50/50 ${
                    selectedItem?.id === item.id
                      ? "bg-violet-50 border-l-4 border-l-violet-600"
                      : "border-l-4 border-l-transparent"
                  }`}
                >
                  <div className="flex items-start justify-between mb-1.5">
                    <div>
                      <p className="font-bold text-sm text-slate-800">{item.patient_name}</p>
                      <p className="text-xs text-slate-500">UHID: {item.uhid}</p>
                    </div>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        STATUS_COLORS[item.status] || "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-2">
                    <span className="flex items-center gap-1">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                        />
                      </svg>
                      {item.doctor_name}
                    </span>
                    <span>•</span>
                    <span>{item.prescriptions.length} items</span>
                    <span>•</span>
                    <span>
                      {new Date(item.prescription_date).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Detail Panel */}
        <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
          {!selectedItem ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300">
              <svg className="w-20 h-20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={0.8}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.5a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m0 0a9.06 9.06 0 011.5-.124"
                />
              </svg>
              <p className="text-lg font-medium">Select a prescription from the queue</p>
              <p className="text-sm mt-1">to review, dispense, and generate a bill</p>
            </div>
          ) : (
            <>
              {/* Patient Header */}
              <div className="p-5 bg-gradient-to-r from-violet-600 to-purple-700 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold">{selectedItem.patient_name}</h2>
                    <p className="text-violet-200 text-sm mt-0.5">
                      UHID: {selectedItem.uhid} &bull; Dr. {selectedItem.doctor_name}
                    </p>
                  </div>
                  <span
                    className={`text-xs font-bold px-3 py-1 rounded-full ${
                      selectedItem.status === "Completed"
                        ? "bg-green-400/20 text-green-100"
                        : "bg-white/20 text-white"
                    }`}
                  >
                    {selectedItem.status}
                  </span>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b bg-slate-50/50">
                {(
                  [
                    { key: "dispensing", label: "Dispense & Bill" },
                    { key: "audit", label: "Audit Trail" },
                  ] as { key: "dispensing" | "audit"; label: string }[]
                ).map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`px-5 py-3 text-sm font-medium transition-all border-b-2 ${
                      activeTab === tab.key
                        ? "border-violet-600 text-violet-700 bg-white"
                        : "border-transparent text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-5">
                {msg && (
                  <div
                    className={`mb-4 px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${
                      msg.type === "success"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-100"
                        : "bg-rose-50 text-rose-700 border border-rose-100"
                    }`}
                  >
                    {msg.type === "success" ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                      </svg>
                    )}
                    {msg.text}
                  </div>
                )}

                {activeTab === "dispensing" && (
                  <div className="space-y-4">
                    <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest flex items-center gap-2">
                      <svg
                        className="w-4 h-4 text-violet-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                        />
                      </svg>
                      Medication Dispensing
                    </h3>

                    {dispenseItems.map((d, idx) => (
                      <div
                        key={idx}
                        className="border border-slate-100 rounded-xl p-4 bg-slate-50/50 shadow-sm hover:shadow transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <p className="font-bold text-slate-800">{d.medication_name}</p>
                            <p className="text-xs text-slate-500 mt-0.5">
                              Prescribed Qty: {d.quantity_prescribed} &bull;{" "}
                              {d.dosage_instructions}
                            </p>
                            {d.is_non_formulary && (
                              <span className="mt-1 inline-block px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-[10px] font-bold">
                                NON-FORMULARY
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                              Dispense Qty
                            </label>
                            <input
                              type="number"
                              min="0"
                              value={d.quantity_dispensed}
                              onChange={(e) => {
                                const updated = [...dispenseItems];
                                updated[idx].quantity_dispensed =
                                  parseFloat(e.target.value) || 0;
                                setDispenseItems(updated);
                              }}
                              disabled={selectedItem.status === "Completed"}
                              className="border rounded-lg px-3 py-2 w-full text-sm font-medium disabled:opacity-50 disabled:bg-slate-100"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                              Unit Price (₹)
                            </label>
                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              value={d.unit_price}
                              onChange={(e) => {
                                const updated = [...dispenseItems];
                                updated[idx].unit_price =
                                  parseFloat(e.target.value) || 0;
                                setDispenseItems(updated);
                              }}
                              disabled={selectedItem.status === "Completed"}
                              className="border rounded-lg px-3 py-2 w-full text-sm font-medium disabled:opacity-50 disabled:bg-slate-100"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                              Line Total
                            </label>
                            <p className="text-lg font-bold text-violet-700 mt-1">
                              ₹{(d.quantity_dispensed * d.unit_price).toFixed(2)}
                            </p>
                          </div>
                        </div>

                        {/* Substitute Section */}
                        <div className="mt-4 pt-4 border-t border-slate-100 bg-amber-50/30 -mx-4 px-4 pb-4 rounded-b-xl border border-amber-100/50">
                          <div className="flex justify-between items-center mb-2">
                             <label className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1.5">
                               Substitute Medication Engine
                             </label>
                          </div>
                          <div className="flex gap-3 relative">
                            <input
                              value={d.substitute_name}
                              onChange={(e) => {
                                const updated = [...dispenseItems];
                                updated[idx].substitute_name = e.target.value;
                                updated[idx].substituted_for = e.target.value ? d.medication_name : "";
                                setDispenseItems(updated);
                              }}
                              disabled={selectedItem.status === "Completed"}
                              placeholder="Enter substitute drug name..."
                              className="border border-amber-200 rounded-lg px-3 py-2 w-full text-sm disabled:opacity-50 disabled:bg-slate-100 focus:ring-2 focus:ring-amber-200"
                            />
                            <button 
                              onClick={() => handleEngineLookup(idx, d.medication_name)}
                              disabled={selectedItem.status === "Completed"}
                              className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 font-bold text-white text-xs rounded-lg shadow disabled:opacity-50 flex items-center gap-1 shrink-0"
                            >
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35m1.35-5.65a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                                Engine
                            </button>
                            
                            {/* Dropdown Results */}
                            {showEngineIdx === idx && (
                                <div className="absolute top-12 left-0 w-full bg-white shadow-2xl border border-amber-100 rounded-xl z-10 overflow-hidden divide-y divide-slate-50 max-h-48 overflow-y-auto">
                                    {isEngineLoading ? (
                                        <div className="p-4 text-center text-xs text-amber-500 flex justify-center items-center gap-2 font-medium">
                                            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
                                            Polling Intelligence Engine...
                                        </div>
                                    ) : engineResults.length === 0 ? (
                                        <div className="p-4 text-center text-xs text-slate-500 bg-slate-50 italic">No direct generic alternatives found in stock.</div>
                                    ) : (
                                        engineResults.map((alt, aidx) => (
                                            <div key={aidx} className="flex justify-between items-center p-3 hover:bg-amber-50/50 cursor-pointer group" onClick={() => {
                                                const u = [...dispenseItems];
                                                u[idx].substitute_name = alt.drug_name || alt.generic_name;
                                                u[idx].substituted_for = d.medication_name;
                                                u[idx].unit_price = alt.unit_price || u[idx].unit_price;
                                                setDispenseItems(u);
                                                setShowEngineIdx(null);
                                            }}>
                                               <div>
                                                   <p className="text-sm font-bold text-slate-800">{alt.drug_name}</p>
                                                   <p className="text-[10px] text-slate-500">{alt.strength} &bull; Form: {alt.form}</p>
                                               </div>
                                               <div className="text-right">
                                                    <span className="text-xs font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md">Stock: {alt.quantity_available || 0}</span>
                                                    <p className="text-[11px] font-bold text-slate-400 mt-1">₹{alt.unit_price}</p>
                                               </div>
                                            </div>
                                        ))
                                    )}
                                    <div className="bg-slate-50 border-t p-2 text-center text-[10px] text-slate-400 font-bold uppercase tracking-widest cursor-pointer hover:bg-slate-100 transition" onClick={() => setShowEngineIdx(null)}>Close Engine</div>
                                </div>
                            )}
                          </div>
                          {d.substitute_name && (
                            <p className="mt-2 text-xs text-amber-700 font-medium flex items-center gap-1.5 bg-amber-100 w-max px-2 py-1 rounded">
                              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                              </svg>
                              Substituting <strong>{d.medication_name}</strong> → <strong>{d.substitute_name}</strong>
                            </p>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* Bill Summary */}
                    <div className="border-t pt-4 mt-4">
                      <div className="flex justify-between items-center text-lg">
                        <span className="font-medium text-slate-600">Total Bill Amount</span>
                        <span className="font-bold text-2xl text-violet-700">
                          ₹{totalBill.toFixed(2)}
                        </span>
                      </div>
                    </div>

                    {selectedItem.status !== "Completed" && (
                      <button
                        onClick={handleDispense}
                        disabled={isDispensing || dispenseItems.length === 0}
                        className="w-full mt-3 bg-gradient-to-r from-violet-600 to-purple-700 text-white font-bold py-3.5 rounded-xl hover:from-violet-700 hover:to-purple-800 disabled:opacity-50 transition-all shadow-lg flex justify-center items-center gap-2"
                      >
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        {isDispensing
                          ? "Processing..."
                          : "Dispense Medications & Generate Bill"}
                      </button>
                    )}
                  </div>
                )}

                {activeTab === "audit" && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest">
                      Immutable Audit Trail
                    </h3>
                    {auditLogs.length === 0 ? (
                      <p className="text-slate-400 text-sm py-6 text-center">
                        No audit records yet for this prescription
                      </p>
                    ) : (
                      auditLogs.map((log) => (
                        <div
                          key={log.id}
                          className="border rounded-xl p-4 bg-slate-50/50 shadow-sm"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-bold text-violet-700 bg-violet-50 px-2 py-0.5 rounded-full">
                              {log.action_type}
                            </span>
                            <span className="text-xs text-slate-400">
                              {new Date(log.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500">
                            Pharmacist: {log.pharmacist_id.split("-")[0]}...
                          </p>
                          {log.details && (
                            <pre className="mt-2 text-xs bg-white rounded-lg p-2 border text-slate-600 overflow-x-auto">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          )}
                        </div>
                      ))
                    )}
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
