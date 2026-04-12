"use client";
import { useTranslation } from "@/i18n";


import React, { useEffect, useState } from "react";
import {
  Package, Search, CheckCircle2, XCircle, Barcode, FileText,
  Truck, Clock, AlertCircle, RefreshCw, Shield, AlertTriangle,
  Loader2, Activity, MapPin, FlaskConical, Thermometer, Box,
  ArrowRight, Eye, ChevronDown, ChevronUp, Bell
} from "lucide-react";
import { crApi } from "@/lib/cr-api";
import type {
  CRReceipt, CRVerification, CRRouting, CRStorage,
  CRCustodyEntry, CRAlert, CRAuditEntry, CRDashboardStats
} from "@/lib/cr-api";

type TabTypes = "dashboard" | "receive" | "verify" | "routing" | "storage" | "alerts" | "audit";

const DEPARTMENTS = [
  "BIOCHEMISTRY", "HEMATOLOGY", "CLINICAL_PATHOLOGY", "SEROLOGY",
  "MICROBIOLOGY", "HISTOPATHOLOGY", "IMMUNOLOGY", "MOLECULAR_BIOLOGY",
  "CYTOLOGY", "URINALYSIS"
];

const REJECTION_REASONS = [
  "INSUFFICIENT_VOLUME", "INCORRECT_CONTAINER", "HEMOLYZED", "CLOTTED",
  "LABEL_MISMATCH", "TRANSPORT_DELAY", "WRONG_SAMPLE_TYPE", "CONTAMINATED", "EXPIRED", "OTHER"
];

export default function CentralReceivingPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabTypes>("dashboard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Dashboard
  const [stats, setStats] = useState<CRDashboardStats | null>(null);

  // Receive
  const [barcodeInput, setBarcodeInput] = useState("");
  const [receivedBy, setReceivedBy] = useState("");
  const [receiveNotes, setReceiveNotes] = useState("");

  // Receipts list
  const [receipts, setReceipts] = useState<CRReceipt[]>([]);
  const [filterStatus, setFilterStatus] = useState("");
  const [selectedReceipt, setSelectedReceipt] = useState<CRReceipt | null>(null);

  // Verification
  const [verifyChecks, setVerifyChecks] = useState({
    sample_type_correct: true, container_correct: true, volume_adequate: true,
    labeling_correct: true, transport_ok: true, hemolyzed: false, clotted: false,
  });
  const [verifiedBy, setVerifiedBy] = useState("");
  const [verifyRemarks, setVerifyRemarks] = useState("");

  // Rejection
  const [rejectionReason, setRejectionReason] = useState("INSUFFICIENT_VOLUME");
  const [rejectionDetails, setRejectionDetails] = useState("");
  const [rejectedBy, setRejectedBy] = useState("");

  // Routing
  const [routings, setRoutings] = useState<CRRouting[]>([]);
  const [routeBy, setRouteBy] = useState("");
  const [routeDept, setRouteDept] = useState("");

  // Storage
  const [storageList, setStorageList] = useState<CRStorage[]>([]);
  const [storageLocation, setStorageLocation] = useState("");
  const [storageTemp, setStorageTemp] = useState("2-8°C");
  const [storageDuration, setStorageDuration] = useState("24");
  const [storedBy, setStoredBy] = useState("");

  // Chain of custody
  const [custodyChain, setCustodyChain] = useState<CRCustodyEntry[]>([]);
  const [showCustody, setShowCustody] = useState(false);

  // Alerts
  const [alerts, setAlerts] = useState<CRAlert[]>([]);

  // Audit
  const [auditTrail, setAuditTrail] = useState<CRAuditEntry[]>([]);

  useEffect(() => { loadDashboard(); }, []);

  useEffect(() => {
    if (activeTab === "receive") loadReceipts();
    if (activeTab === "routing") loadRoutings();
    if (activeTab === "storage") loadStorage();
    if (activeTab === "alerts") loadAlerts();
    if (activeTab === "audit") loadAudit();
  }, [activeTab]);

  const loadDashboard = async () => {
    try { const s = await crApi.getDashboard(); setStats(s); } catch {}
  };

  const loadReceipts = async () => {
    setLoading(true);
    try {
      const items = await crApi.listReceipts({ status: filterStatus || undefined });
      setReceipts(items || []);
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const loadRoutings = async () => {
    try { const r = await crApi.listRoutings(); setRoutings(r || []); } catch {}
  };

  const loadStorage = async () => {
    try { const s = await crApi.listActiveStorage(); setStorageList(s || []); } catch {}
  };

  const loadAlerts = async () => {
    try { const a = await crApi.listAlerts(); setAlerts(a || []); } catch {}
  };

  const loadAudit = async () => {
    try { const a = await crApi.getAuditTrail(undefined, undefined, 50); setAuditTrail(a || []); } catch {}
  };

  const loadCustody = async (receiptId: string) => {
    try {
      const c = await crApi.getChainOfCustody(receiptId);
      setCustodyChain(c || []);
      setShowCustody(true);
    } catch {}
  };

  // ── Handlers ────────────────────────────────────────────────────────────────

  const handleScanBarcode = async () => {
    if (!barcodeInput || !receivedBy) { setError("Enter barcode and technician name"); return; }
    setLoading(true); setError("");
    try {
      const receipt = await crApi.registerSample({ barcode: barcodeInput, received_by: receivedBy, notes: receiveNotes || undefined });
      alert(`✅ Sample registered!\nSample ID: ${receipt.sample_id}\nPatient: ${receipt.patient_name || "N/A"}\nTest: ${receipt.test_name}`);
      setBarcodeInput(""); setReceiveNotes("");
      loadReceipts(); loadDashboard();
    } catch (e: any) { setError(e.message || "Barcode scan failed"); }
    setLoading(false);
  };

  const handleVerify = async () => {
    if (!selectedReceipt || !verifiedBy) { setError("Select a receipt and enter verifier name"); return; }
    setLoading(true); setError("");
    try {
      const v = await crApi.verifySample({ receipt_id: selectedReceipt.id, ...verifyChecks, verified_by: verifiedBy, remarks: verifyRemarks || undefined });
      alert(`Verification: ${v.overall_result}`);
      setSelectedReceipt(null); loadReceipts(); loadDashboard();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleReject = async () => {
    if (!selectedReceipt || !rejectedBy) { setError("Select a receipt and enter rejector name"); return; }
    setLoading(true); setError("");
    try {
      await crApi.rejectSample({
        receipt_id: selectedReceipt.id, rejection_reason: rejectionReason,
        rejection_details: rejectionDetails || undefined, rejected_by: rejectedBy,
      });
      alert("Sample rejected. Recollection alert generated.");
      setSelectedReceipt(null); loadReceipts(); loadDashboard();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleRoute = async () => {
    if (!selectedReceipt || !routeBy) { setError("Select receipt and enter routing staff"); return; }
    setLoading(true); setError("");
    try {
      const r = await crApi.routeSample({
        receipt_id: selectedReceipt.id,
        target_department: routeDept || undefined,
        routed_by: routeBy,
      });
      alert(`Routed to ${r.target_department}`);
      setSelectedReceipt(null); loadReceipts(); loadRoutings(); loadDashboard();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleReceiveAtDept = async (routingId: string) => {
    const by = prompt("Received by (department staff name):");
    if (!by) return;
    try {
      await crApi.receiveAtDept(routingId, by);
      alert("Sample received at department!");
      loadRoutings(); loadDashboard();
    } catch (e: any) { setError(e.message); }
  };

  const handleStore = async () => {
    if (!selectedReceipt || !storageLocation || !storedBy) { setError("Fill storage details"); return; }
    setLoading(true); setError("");
    try {
      await crApi.storeSample({
        receipt_id: selectedReceipt.id, storage_location: storageLocation,
        storage_temperature: storageTemp, max_duration_hours: parseInt(storageDuration),
        stored_by: storedBy,
      });
      alert("Sample stored successfully");
      setSelectedReceipt(null); loadStorage(); loadDashboard();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleRetrieve = async (storageId: string) => {
    const by = prompt("Retrieved by:");
    if (!by) return;
    try {
      await crApi.retrieveSample(storageId, by);
      alert("Sample retrieved from storage");
      loadStorage(); loadDashboard();
    } catch (e: any) { setError(e.message); }
  };

  const handleAckAlert = async (alertId: string) => {
    const by = prompt("Acknowledged by:");
    if (!by) return;
    try { await crApi.acknowledgeAlert(alertId, by); loadAlerts(); loadDashboard(); } catch {}
  };

  const statusColor = (s: string) => {
    const map: Record<string, string> = {
      RECEIVED: "bg-blue-100 text-blue-700", VERIFIED: "bg-cyan-100 text-cyan-700",
      ACCEPTED: "bg-emerald-100 text-emerald-700", REJECTED: "bg-red-100 text-red-700",
      ROUTED: "bg-purple-100 text-purple-700", STORED: "bg-amber-100 text-amber-700",
      PROCESSING: "bg-indigo-100 text-indigo-700", COMPLETED: "bg-green-100 text-green-700",
    };
    return map[s] || "bg-slate-100 text-slate-700";
  };

  const priBadge = (p: string) => p === "STAT" ? "bg-rose-100 text-rose-700 border-rose-200" : p === "URGENT" ? "bg-amber-100 text-amber-700 border-amber-200" : "bg-emerald-100 text-emerald-700 border-emerald-200";

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3 text-slate-800">
          <Package className="text-indigo-600" size={32} />
          Central Receiving & Specimen Tracking
        </h1>
        <p className="text-slate-500 mt-1">Barcode Scanning • Quality Verification • Department Routing • Chain of Custody</p>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-center gap-2 border border-red-200"><AlertCircle size={18} /> {error} <button onClick={() => setError("")} className="ml-auto text-red-400 hover:text-red-600">✕</button></div>}

      {/* Tabs */}
      <div className="flex bg-white rounded-lg p-1 shadow-sm border border-slate-200 overflow-x-auto">
        {[
          { id: "dashboard" as TabTypes, label: "Dashboard", icon: Activity },
          { id: "receive" as TabTypes, label: "Receive & Scan", icon: Barcode },
          { id: "verify" as TabTypes, label: "Verify & Route", icon: CheckCircle2 },
          { id: "routing" as TabTypes, label: "Dept Routing", icon: ArrowRight },
          { id: "storage" as TabTypes, label: "Storage", icon: Thermometer },
          { id: "alerts" as TabTypes, label: "Alerts", icon: Bell },
          { id: "audit" as TabTypes, label: "Audit", icon: Shield },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.id ? "bg-indigo-50 text-indigo-700 shadow-sm" : "text-slate-600 hover:bg-slate-50"}`}>
            <tab.icon size={16} /> {tab.label}
            {tab.id === "alerts" && stats && stats.active_alerts > 0 && (
              <span className="bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 font-bold">{stats.active_alerts}</span>
            )}
          </button>
        ))}
      </div>

      {/* ═══════ DASHBOARD TAB ═══════ */}
      {activeTab === "dashboard" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-lg text-slate-800">Today&apos;s Overview</h3>
            <button onClick={loadDashboard} className="btn-secondary flex items-center gap-2 text-sm"><RefreshCw size={14} /> Refresh</button>
          </div>

          {/* Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {[
              { label: "Received Today", value: stats?.received_today || 0, color: "bg-blue-50 text-blue-700 border-blue-200", icon: Package },
              { label: "Pending Verify", value: stats?.pending_verification || 0, color: "bg-amber-50 text-amber-700 border-amber-200", icon: Clock },
              { label: "Accepted", value: stats?.accepted || 0, color: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: CheckCircle2 },
              { label: "Rejected", value: stats?.rejected || 0, color: "bg-red-50 text-red-700 border-red-200", icon: XCircle },
              { label: "Routed", value: stats?.routed || 0, color: "bg-purple-50 text-purple-700 border-purple-200", icon: ArrowRight },
              { label: "In Storage", value: stats?.stored || 0, color: "bg-cyan-50 text-cyan-700 border-cyan-200", icon: Thermometer },
              { label: "Active Alerts", value: stats?.active_alerts || 0, color: "bg-rose-50 text-rose-700 border-rose-200", icon: AlertTriangle },
            ].map(s => (
              <div key={s.label} className={`rounded-xl border p-4 ${s.color}`}>
                <s.icon size={20} className="mb-2 opacity-70" />
                <div className="text-3xl font-bold">{s.value}</div>
                <div className="text-xs font-semibold mt-1 opacity-80">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Department Distribution */}
          {stats && Object.keys(stats.department_distribution).length > 0 && (
            <div className="card p-6">
              <h4 className="font-bold text-slate-800 mb-4 flex items-center gap-2"><FlaskConical size={18} className="text-indigo-500" /> Samples by Department</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {Object.entries(stats.department_distribution).map(([dept, count]) => (
                  <div key={dept} className="bg-slate-50 rounded-lg p-3 border text-center">
                    <div className="text-2xl font-bold text-indigo-700">{count}</div>
                    <div className="text-xs text-slate-500 font-semibold mt-1">{dept.replace(/_/g, " ")}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════ RECEIVE TAB ═══════ */}
      {activeTab === "receive" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Barcode Scan Panel */}
          <div className="card p-6 space-y-4">
            <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><Barcode size={20} className="text-indigo-500" /> Scan Barcode</h3>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Sample Barcode *</label>
              <input className="input-field" placeholder="Scan or enter barcode..." value={barcodeInput}
                onChange={e => setBarcodeInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleScanBarcode()} autoFocus />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">CR Technician *</label>
              <input className="input-field" placeholder="Technician name" value={receivedBy} onChange={e => setReceivedBy(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Notes</label>
              <input className="input-field" placeholder="Optional notes" value={receiveNotes} onChange={e => setReceiveNotes(e.target.value)} />
            </div>
            <button onClick={handleScanBarcode} disabled={loading || !barcodeInput || !receivedBy}
              className="btn-primary w-full py-3 flex items-center justify-center gap-2 text-lg disabled:opacity-40">
              <Barcode size={20} /> Register Sample
            </button>
          </div>

          {/* Receipts List */}
          <div className="lg:col-span-2 card p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><Package size={18} className="text-indigo-500" /> Received Samples</h3>
              <div className="flex gap-2">
                <select className="input-field w-36 text-sm" value={filterStatus} onChange={e => { setFilterStatus(e.target.value); }}>
                  <option value="">All Status</option>
                  <option value="RECEIVED">Received</option>
                  <option value="ACCEPTED">Accepted</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="ROUTED">Routed</option>
                  <option value="STORED">Stored</option>
                </select>
                <button onClick={loadReceipts} className="btn-secondary text-sm flex items-center gap-1"><RefreshCw size={12} /> Refresh</button>
              </div>
            </div>
            {loading ? (
              <div className="text-center py-10 text-slate-400 flex items-center justify-center gap-2"><Loader2 size={20} className="animate-spin" /> Loading...</div>
            ) : receipts.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed rounded-lg text-slate-400">
                <Package size={48} className="mx-auto mb-3 opacity-30" />
                No samples received yet. Scan a barcode to register.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-50 text-slate-600 border-b">
                    <tr>
                      <th className="py-3 px-3">Sample ID</th>
                      <th className="py-3 px-3">Patient</th>
                      <th className="py-3 px-3">Test</th>
                      <th className="py-3 px-3">Priority</th>
                      <th className="py-3 px-3">Status</th>
                      <th className="py-3 px-3">Location</th>
                      <th className="py-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {receipts.map(r => (
                      <tr key={r.id} className={`hover:bg-slate-50 ${selectedReceipt?.id === r.id ? "bg-indigo-50" : ""}`}>
                        <td className="py-3 px-3 font-mono text-xs font-bold text-indigo-600">{r.sample_id}</td>
                        <td className="py-3 px-3"><div className="font-semibold text-slate-800">{r.patient_name || "—"}</div><div className="text-xs text-slate-400">{r.patient_uhid || r.patient_id.slice(0, 8)}</div></td>
                        <td className="py-3 px-3 font-medium text-slate-700">{r.test_name}</td>
                        <td className="py-3 px-3"><span className={`badge border font-bold text-xs ${priBadge(r.priority)}`}>{r.priority}</span></td>
                        <td className="py-3 px-3"><span className={`badge font-bold text-xs ${statusColor(r.status)}`}>{r.status}</span></td>
                        <td className="py-3 px-3 text-xs text-slate-500">{r.current_location}</td>
                        <td className="py-3 px-3 text-right space-x-1">
                          <button onClick={() => { setSelectedReceipt(r); setActiveTab("verify"); }} className="btn-secondary py-1 px-2 text-xs" title="Verify">
                            <CheckCircle2 size={12} />
                          </button>
                          <button onClick={() => loadCustody(r.id)} className="btn-secondary py-1 px-2 text-xs" title="Chain of Custody">
                            <Eye size={12} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════ VERIFY & ROUTE TAB ═══════ */}
      {activeTab === "verify" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Selected Sample Info */}
          <div className="space-y-6">
            {selectedReceipt ? (
              <div className="card p-6 border-indigo-200">
                <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 mb-4"><FileText size={18} className="text-indigo-500" /> Sample Details</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div><span className="text-slate-500">Sample ID</span><div className="font-mono font-bold text-indigo-600">{selectedReceipt.sample_id}</div></div>
                  <div><span className="text-slate-500">Patient</span><div className="font-semibold text-slate-800">{selectedReceipt.patient_name || "—"}</div></div>
                  <div><span className="text-slate-500">UHID</span><div className="font-mono text-slate-700">{selectedReceipt.patient_uhid || "—"}</div></div>
                  <div><span className="text-slate-500">Test</span><div className="font-semibold text-slate-800">{selectedReceipt.test_name}</div></div>
                  <div><span className="text-slate-500">Sample Type</span><div>{selectedReceipt.sample_type}</div></div>
                  <div><span className="text-slate-500">Container</span><div>{selectedReceipt.container_type || "—"}</div></div>
                  <div><span className="text-slate-500">Priority</span><span className={`badge border font-bold text-xs ${priBadge(selectedReceipt.priority)}`}>{selectedReceipt.priority}</span></div>
                  <div><span className="text-slate-500">Status</span><span className={`badge font-bold text-xs ${statusColor(selectedReceipt.status)}`}>{selectedReceipt.status}</span></div>
                </div>
              </div>
            ) : (
              <div className="card p-12 text-center border-dashed border-2">
                <Package size={48} className="mx-auto mb-4 text-slate-300" />
                <h3 className="font-bold text-slate-600 mb-2">No Sample Selected</h3>
                <p className="text-slate-400 text-sm">Go to Receive &amp; Scan tab and click the verify button on a sample.</p>
              </div>
            )}

            {/* Quality Verification */}
            {selectedReceipt && (
              <div className="card p-6">
                <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 mb-4"><CheckCircle2 size={18} className="text-indigo-500" /> Quality Verification</h3>
                <div className="space-y-2">
                  {[
                    { key: "sample_type_correct", label: "Sample Type Correct" },
                    { key: "container_correct", label: "Container Type Correct" },
                    { key: "volume_adequate", label: "Volume Adequate" },
                    { key: "labeling_correct", label: "Labeling Accurate" },
                    { key: "transport_ok", label: "Transport Conditions OK" },
                  ].map(c => (
                    <label key={c.key} className="flex items-center justify-between p-3 rounded-lg border hover:bg-slate-50 cursor-pointer">
                      <span className="font-medium text-sm text-slate-700">{c.label}</span>
                      <input type="checkbox" className="w-5 h-5 text-indigo-600 rounded"
                        checked={(verifyChecks as any)[c.key]}
                        onChange={e => setVerifyChecks(prev => ({ ...prev, [c.key]: e.target.checked }))} />
                    </label>
                  ))}
                  {[
                    { key: "hemolyzed", label: "⚠ Hemolyzed" },
                    { key: "clotted", label: "⚠ Clotted" },
                  ].map(c => (
                    <label key={c.key} className="flex items-center justify-between p-3 rounded-lg border border-red-200 bg-red-50 hover:bg-red-100 cursor-pointer">
                      <span className="font-medium text-sm text-red-700">{c.label}</span>
                      <input type="checkbox" className="w-5 h-5 text-red-600 rounded"
                        checked={(verifyChecks as any)[c.key]}
                        onChange={e => setVerifyChecks(prev => ({ ...prev, [c.key]: e.target.checked }))} />
                    </label>
                  ))}
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-semibold text-slate-700 mb-1">Verified By *</label>
                  <input className="input-field" placeholder="Technician name" value={verifiedBy} onChange={e => setVerifiedBy(e.target.value)} />
                </div>
                <div className="mt-3">
                  <label className="block text-sm font-semibold text-slate-700 mb-1">Remarks</label>
                  <input className="input-field" placeholder="Optional remarks" value={verifyRemarks} onChange={e => setVerifyRemarks(e.target.value)} />
                </div>
                <button onClick={handleVerify} disabled={loading || !verifiedBy}
                  className="btn-primary w-full mt-4 py-3 flex items-center justify-center gap-2 disabled:opacity-40">
                  <CheckCircle2 size={18} /> Verify Sample
                </button>
              </div>
            )}
          </div>

          {/* Right: Reject / Route / Store */}
          {selectedReceipt && (
            <div className="space-y-6">
              {/* Route to Department */}
              <div className="card p-6">
                <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 mb-4"><ArrowRight size={18} className="text-purple-500" /> Route to Department</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1">Target Department</label>
                    <select className="input-field" value={routeDept} onChange={e => setRouteDept(e.target.value)}>
                      <option value="">Auto-detect from test</option>
                      {DEPARTMENTS.map(d => <option key={d} value={d}>{d.replace(/_/g, " ")}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1">Routed By *</label>
                    <input className="input-field" placeholder="Staff name" value={routeBy} onChange={e => setRouteBy(e.target.value)} />
                  </div>
                  <button onClick={handleRoute} disabled={loading || !routeBy}
                    className="btn-primary w-full py-2.5 flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-40">
                    <ArrowRight size={16} /> Route Sample
                  </button>
                </div>
              </div>

              {/* Store Sample */}
              <div className="card p-6">
                <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 mb-4"><Thermometer size={18} className="text-cyan-500" /> Temporary Storage</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1">Location *</label>
                    <input className="input-field" placeholder="e.g. Fridge-A3" value={storageLocation} onChange={e => setStorageLocation(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1">Temperature</label>
                    <select className="input-field" value={storageTemp} onChange={e => setStorageTemp(e.target.value)}>
                      <option value="2-8°C">2-8°C (Refrigerated)</option>
                      <option value="-20°C">-20°C (Frozen)</option>
                      <option value="-80°C">-80°C (Deep Frozen)</option>
                      <option value="Room Temp">Room Temperature</option>
                    </select>
                  </div>
                </div>
                <div className="mt-3">
                  <label className="block text-sm font-semibold text-slate-700 mb-1">Stored By *</label>
                  <input className="input-field" placeholder="Technician" value={storedBy} onChange={e => setStoredBy(e.target.value)} />
                </div>
                <button onClick={handleStore} disabled={loading || !storageLocation || !storedBy}
                  className="btn-primary w-full mt-3 py-2.5 flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-40">
                  <Thermometer size={16} /> Store Sample
                </button>
              </div>

              {/* Reject */}
              <div className="card p-6 border-red-200">
                <h3 className="font-bold text-lg text-red-700 flex items-center gap-2 mb-4"><XCircle size={18} /> Reject Sample</h3>
                <div className="space-y-3">
                  <select className="input-field" value={rejectionReason} onChange={e => setRejectionReason(e.target.value)}>
                    {REJECTION_REASONS.map(r => <option key={r} value={r}>{r.replace(/_/g, " ")}</option>)}
                  </select>
                  <input className="input-field" placeholder="Rejection details" value={rejectionDetails} onChange={e => setRejectionDetails(e.target.value)} />
                  <input className="input-field" placeholder="Rejected by" value={rejectedBy} onChange={e => setRejectedBy(e.target.value)} />
                  <button onClick={handleReject} disabled={loading || !rejectedBy}
                    className="w-full py-2.5 rounded-lg font-bold text-white bg-red-600 hover:bg-red-700 flex items-center justify-center gap-2 disabled:opacity-40">
                    <XCircle size={16} /> Reject & Request Recollection
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════ ROUTING TAB ═══════ */}
      {activeTab === "routing" && (
        <div className="card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><ArrowRight size={20} className="text-purple-500" /> Department Routing</h3>
            <button onClick={loadRoutings} className="btn-secondary flex items-center gap-2 text-sm"><RefreshCw size={14} /> Refresh</button>
          </div>
          {routings.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed rounded-lg text-slate-400">No routing records yet</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-slate-600 border-b">
                  <tr>
                    <th className="py-3 px-4">Receipt</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Routed By</th>
                    <th className="py-3 px-4">Routed At</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Received By</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {routings.map(r => (
                    <tr key={r.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-mono text-xs">{r.receipt_id.slice(0, 8)}</td>
                      <td className="py-3 px-4"><span className="badge bg-purple-100 text-purple-700 font-bold text-xs">{r.target_department.replace(/_/g, " ")}</span></td>
                      <td className="py-3 px-4 text-slate-700">{r.routed_by}</td>
                      <td className="py-3 px-4 text-xs text-slate-500">{r.routed_at ? new Date(r.routed_at).toLocaleString() : "—"}</td>
                      <td className="py-3 px-4"><span className={`badge font-bold text-xs ${r.status === "RECEIVED_AT_DEPT" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>{r.status}</span></td>
                      <td className="py-3 px-4 text-slate-600">{r.received_by_dept || "—"}</td>
                      <td className="py-3 px-4 text-right">
                        {r.status === "ROUTED" && (
                          <button onClick={() => handleReceiveAtDept(r.id)} className="btn-primary py-1.5 px-3 text-xs bg-emerald-600 hover:bg-emerald-700 flex items-center gap-1">
                            <CheckCircle2 size={12} /> Confirm Receipt
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ STORAGE TAB ═══════ */}
      {activeTab === "storage" && (
        <div className="card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><Thermometer size={20} className="text-cyan-500" /> Active Sample Storage</h3>
            <button onClick={loadStorage} className="btn-secondary flex items-center gap-2 text-sm"><RefreshCw size={14} /> Refresh</button>
          </div>
          {storageList.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed rounded-lg text-slate-400">No samples currently in storage</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {storageList.map(s => (
                <div key={s.id} className="bg-white border rounded-lg p-4 shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-bold text-slate-800">{s.storage_location}</div>
                    <span className="badge bg-cyan-100 text-cyan-700 font-bold text-xs">{s.storage_temperature}</span>
                  </div>
                  <div className="text-xs text-slate-500 space-y-1">
                    <div>Receipt: <span className="font-mono">{s.receipt_id.slice(0, 8)}</span></div>
                    <div>Stored: {s.stored_at ? new Date(s.stored_at).toLocaleString() : "—"}</div>
                    <div>Max: {s.max_duration_hours}h • By: {s.stored_by}</div>
                  </div>
                  <button onClick={() => handleRetrieve(s.id)}
                    className="btn-primary w-full mt-3 py-1.5 text-xs bg-cyan-600 hover:bg-cyan-700 flex items-center justify-center gap-1">
                    <Box size={12} /> Retrieve Sample
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══════ ALERTS TAB ═══════ */}
      {activeTab === "alerts" && (
        <div className="card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><Bell size={20} className="text-rose-500" /> Sample Alerts</h3>
            <button onClick={loadAlerts} className="btn-secondary flex items-center gap-2 text-sm"><RefreshCw size={14} /> Refresh</button>
          </div>
          {alerts.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed rounded-lg text-slate-400">No alerts at this time</div>
          ) : (
            <div className="space-y-3">
              {alerts.map(a => (
                <div key={a.id} className={`p-4 rounded-lg border ${a.severity === "CRITICAL" ? "bg-red-50 border-red-300" : a.severity === "WARNING" ? "bg-amber-50 border-amber-300" : "bg-blue-50 border-blue-200"}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle size={16} className={a.severity === "CRITICAL" ? "text-red-600" : "text-amber-600"} />
                        <span className="font-bold text-sm">{a.alert_type.replace(/_/g, " ")}</span>
                        <span className={`badge text-xs font-bold ${a.status === "ACTIVE" ? "bg-red-100 text-red-700" : a.status === "ACKNOWLEDGED" ? "bg-amber-100 text-amber-700" : "bg-green-100 text-green-700"}`}>{a.status}</span>
                      </div>
                      <p className="text-sm text-slate-700">{a.message}</p>
                      <div className="text-xs text-slate-400 mt-1">{a.created_at ? new Date(a.created_at).toLocaleString() : ""}</div>
                    </div>
                    {a.status === "ACTIVE" && (
                      <button onClick={() => handleAckAlert(a.id)} className="btn-secondary text-xs py-1 px-3">Acknowledge</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══════ AUDIT TAB ═══════ */}
      {activeTab === "audit" && (
        <div className="card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><Shield size={20} className="text-indigo-500" /> Specimen Audit Trail</h3>
            <button onClick={loadAudit} className="btn-secondary flex items-center gap-2"><RefreshCw size={14} /> Refresh</button>
          </div>
          {auditTrail.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed rounded-lg text-slate-400">No audit entries yet</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-slate-600 border-b">
                  <tr>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Entity</th>
                    <th className="py-3 px-4">Performed By</th>
                    <th className="py-3 px-4">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {auditTrail.map(a => (
                    <tr key={a.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 text-xs text-slate-500 font-mono">{a.performed_at ? new Date(a.performed_at).toLocaleString() : "—"}</td>
                      <td className="py-3 px-4"><span className="badge bg-indigo-100 text-indigo-700 font-bold text-xs">{a.action}</span></td>
                      <td className="py-3 px-4 text-slate-600">{a.entity_type} <span className="text-xs text-slate-400 font-mono">({a.entity_id.slice(0, 8)})</span></td>
                      <td className="py-3 px-4 font-medium text-slate-700">{a.performed_by || "System"}</td>
                      <td className="py-3 px-4 text-xs text-slate-400 max-w-xs truncate">{a.details ? JSON.stringify(a.details).slice(0, 80) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ Chain of Custody Modal ═══════ */}
      {showCustody && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowCustody(false)}>
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-xl w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><Eye size={18} className="text-indigo-500" /> Chain of Custody</h3>
              <button onClick={() => setShowCustody(false)} className="text-slate-400 hover:text-slate-600 text-xl">✕</button>
            </div>
            {custodyChain.length === 0 ? (
              <div className="text-center py-8 text-slate-400">No custody records found</div>
            ) : (
              <div className="space-y-4">
                {custodyChain.map((c, i) => (
                  <div key={c.id} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className={`w-3 h-3 rounded-full ${i === custodyChain.length - 1 ? "bg-indigo-600" : "bg-slate-300"}`} />
                      {i < custodyChain.length - 1 && <div className="w-0.5 h-full bg-slate-200" />}
                    </div>
                    <div className="pb-4">
                      <div className="font-bold text-sm text-slate-800">{c.stage.replace(/_/g, " ")}</div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        <span className="flex items-center gap-1"><MapPin size={10} /> {c.location}</span>
                        <span className="flex items-center gap-1 mt-0.5"><Clock size={10} /> {c.timestamp ? new Date(c.timestamp).toLocaleString() : "—"}</span>
                        <span>Staff: {c.responsible_staff}</span>
                        {c.notes && <div className="mt-1 text-slate-400 italic">{c.notes}</div>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
