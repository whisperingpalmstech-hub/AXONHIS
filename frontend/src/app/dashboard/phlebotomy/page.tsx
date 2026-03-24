"use client";

import React, { useEffect, useState } from "react";
import {
  Syringe, Search, CheckCircle2, XCircle, Barcode, FileText,
  User, Truck, Clock, AlertCircle, RefreshCw, Shield,
  Upload, Package, Loader2, Activity, MapPin, FlaskConical
} from "lucide-react";
import { api } from "@/lib/api";
import { phlebotomyApi } from "@/lib/phlebotomy-api";
import type { WorklistItem, SampleCollectionRecord, TransportBatch, AuditEntry } from "@/lib/phlebotomy-api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
const authHeaders = () => ({
  Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("access_token") : ""}`,
  "Content-Type": "application/json",
});

type TabTypes = "worklist" | "collect" | "transport" | "audit";

const CONTAINERS = ["EDTA_TUBE", "PLAIN_TUBE", "CITRATE_TUBE", "HEPARIN_TUBE", "FLUORIDE_TUBE", "URINE_CUP", "SWAB_TUBE", "BIOPSY_JAR", "OTHER"];
const LOCATIONS = ["OPD", "IPD", "EMERGENCY", "HOME", "BEDSIDE", "PHLEBOTOMY_CENTER"];
const VERIFY_METHODS = ["UHID", "MOBILE", "ID_CARD", "BIOMETRIC"];

export default function PhlebotomyPage() {
  const [activeTab, setActiveTab] = useState<TabTypes>("worklist");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Worklist
  const [worklist, setWorklist] = useState<WorklistItem[]>([]);
  const [filterLocation, setFilterLocation] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [selectedItem, setSelectedItem] = useState<WorklistItem | null>(null);

  // Collection
  const [collectorName, setCollectorName] = useState("");
  const [containerType, setContainerType] = useState("PLAIN_TUBE");
  const [collectionLocation, setCollectionLocation] = useState("OPD");
  const [verifyMethod, setVerifyMethod] = useState("UHID");
  const [verified, setVerified] = useState(false);
  const [notes, setNotes] = useState("");
  const [quantityMl, setQuantityMl] = useState("");

  // Collected samples
  const [samples, setSamples] = useState<SampleCollectionRecord[]>([]);
  const [selectedSamples, setSelectedSamples] = useState<string[]>([]);

  // Transport
  const [batches, setBatches] = useState<TransportBatch[]>([]);
  const [transportPersonnel, setTransportPersonnel] = useState("");
  const [transportMethod, setTransportMethod] = useState("MANUAL");

  // Audit
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);

  // Doctors for collector list
  const [doctors, setDoctors] = useState<any[]>([]);

  useEffect(() => {
    loadWorklist();
    loadDoctors();
  }, []);

  useEffect(() => {
    if (activeTab === "transport") { loadSamples(); loadBatches(); }
    if (activeTab === "audit") loadAudit();
  }, [activeTab]);

  const loadDoctors = async () => {
    try { const d = await api.get<any>("/auth/users"); setDoctors(Array.isArray(d) ? d : d?.items || []); } catch {}
  };

  const loadWorklist = async () => {
    setLoading(true); setError("");
    try {
      const items = await phlebotomyApi.getWorklist({
        location: filterLocation || undefined,
        priority: filterPriority || undefined,
      });
      setWorklist(items || []);
    } catch (e: any) { setError(e.message || "Failed to load worklist"); }
    setLoading(false);
  };

  const loadSamples = async () => {
    try { const s = await phlebotomyApi.listSamples(); setSamples(s || []); } catch {}
  };

  const loadBatches = async () => {
    try { const b = await phlebotomyApi.listTransportBatches(); setBatches(b || []); } catch {}
  };

  const loadAudit = async () => {
    try { const a = await phlebotomyApi.getAuditTrail(undefined, undefined, 50); setAuditTrail(a || []); } catch {}
  };

  const handleVerifyPatient = async () => {
    if (!selectedItem) return;
    setLoading(true); setError("");
    try {
      const r = await phlebotomyApi.verifyPatient({
        worklist_id: selectedItem.id,
        verification_method: verifyMethod,
        verified_by: collectorName || "System",
      });
      setVerified(r.verified);
      if (r.verified) setError("");
      else setError("Verification failed");
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleCollectSample = async () => {
    if (!selectedItem || !collectorName) { setError("Select a worklist item and enter collector name"); return; }
    if (!verified) { setError("Please verify patient identity first"); return; }
    setLoading(true); setError("");
    try {
      const sample = await phlebotomyApi.collectSample({
        worklist_id: selectedItem.id,
        collector_name: collectorName,
        container_type: containerType,
        collection_location: collectionLocation,
        identity_verified: true,
        identity_method: verifyMethod,
        notes: notes || undefined,
        quantity_ml: quantityMl ? parseFloat(quantityMl) : undefined,
      });
      alert(`Sample collected! ID: ${sample.sample_id}\nBarcode: ${sample.barcode}`);
      setSelectedItem(null); setVerified(false); setNotes(""); setQuantityMl("");
      loadWorklist();
    } catch (e: any) { setError(e.message || "Collection failed"); }
    setLoading(false);
  };

  const handleUploadConsent = async () => {
    if (!selectedItem) return;
    try {
      await phlebotomyApi.uploadConsent({
        worklist_id: selectedItem.id,
        file_name: `consent_${selectedItem.test_code}_${Date.now()}.pdf`,
        file_url: `/uploads/consents/consent_${Date.now()}.pdf`,
        file_format: "PDF",
        uploaded_by: collectorName || "System",
      });
      alert("Consent uploaded successfully!");
      loadWorklist();
      setSelectedItem({ ...selectedItem, consent_uploaded: true });
    } catch (e: any) { setError(e.message); }
  };

  const toggleSampleSelection = (sampleId: string) => {
    setSelectedSamples(prev =>
      prev.includes(sampleId) ? prev.filter(s => s !== sampleId) : [...prev, sampleId]
    );
  };

  const handleCreateTransportBatch = async () => {
    if (selectedSamples.length === 0 || !transportPersonnel) { setError("Select samples and enter transport personnel"); return; }
    setLoading(true); setError("");
    try {
      const batch = await phlebotomyApi.createTransportBatch({
        sample_ids: selectedSamples,
        transport_personnel: transportPersonnel,
        transport_method: transportMethod,
      });
      alert(`Transport batch created: ${batch.batch_id}`);
      setSelectedSamples([]);
      loadSamples(); loadBatches();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleReceiveBatch = async (batchId: string) => {
    const receivedBy = prompt("Received by (name):");
    if (!receivedBy) return;
    try {
      await phlebotomyApi.receiveTransportBatch(batchId, receivedBy);
      alert("Batch received at Central Lab!");
      loadBatches(); loadSamples();
    } catch (e: any) { setError(e.message); }
  };

  const priBadge = (p: string) => p === "STAT" ? "bg-rose-100 text-rose-700 border-rose-200" : p === "URGENT" ? "bg-amber-100 text-amber-700 border-amber-200" : "bg-emerald-100 text-emerald-700 border-emerald-200";
  const statusBadge = (s: string) => {
    if (s === "COLLECTED") return "bg-blue-100 text-blue-700";
    if (s === "IN_TRANSIT") return "bg-amber-100 text-amber-700";
    if (s === "RECEIVED_IN_LAB") return "bg-emerald-100 text-emerald-700";
    if (s === "PROCESSING") return "bg-purple-100 text-purple-700";
    if (s === "REJECTED") return "bg-red-100 text-red-700";
    return "bg-yellow-100 text-yellow-700";
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3 text-slate-800">
            <Syringe className="text-indigo-600" size={32} />
            Phlebotomy & Sample Collection
          </h1>
          <p className="text-slate-500 mt-1">Patient Verification • Sample Collection • Barcode Labels • Transport Tracking</p>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-center gap-2 border border-red-200"><AlertCircle size={18} /> {error}</div>}

      {/* Tabs */}
      <div className="flex bg-white rounded-lg p-1 shadow-sm w-fit border border-slate-200">
        {[
          { id: "worklist" as TabTypes, label: "Collection Worklist", icon: Syringe },
          { id: "collect" as TabTypes, label: "Collect Sample", icon: FlaskConical },
          { id: "transport" as TabTypes, label: "Transport & Receiving", icon: Truck },
          { id: "audit" as TabTypes, label: "Audit Trail", icon: Shield },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium transition-all ${activeTab === tab.id ? "bg-indigo-50 text-indigo-700 shadow-sm" : "text-slate-600 hover:bg-slate-50"}`}>
            <tab.icon size={16} /> {tab.label}
          </button>
        ))}
      </div>

      {/* ═══════ WORKLIST TAB ═══════ */}
      {activeTab === "worklist" && (
        <div className="card p-6 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><Syringe size={20} className="text-indigo-500" /> Pending Collections</h3>
            <button onClick={loadWorklist} className="btn-secondary flex items-center gap-2"><RefreshCw size={14} /> Refresh</button>
          </div>

          {/* Filters */}
          <div className="flex gap-3 items-center">
            <select className="input-field w-40" value={filterLocation} onChange={e => setFilterLocation(e.target.value)}>
              <option value="">All Locations</option>
              {LOCATIONS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
            <select className="input-field w-40" value={filterPriority} onChange={e => setFilterPriority(e.target.value)}>
              <option value="">All Priorities</option>
              <option value="STAT">STAT</option>
              <option value="URGENT">URGENT</option>
              <option value="ROUTINE">ROUTINE</option>
            </select>
            <button onClick={loadWorklist} className="btn-primary px-4 py-2 text-sm">Apply Filters</button>
          </div>

          {loading ? (
            <div className="text-center py-10 text-slate-400 flex items-center justify-center gap-2"><Loader2 size={20} className="animate-spin" /> Loading worklist...</div>
          ) : worklist.length === 0 ? (
            <div className="text-center py-16 border-2 border-dashed rounded-lg text-slate-400">
              <Syringe size={48} className="mx-auto mb-3 opacity-30" />
              No pending collections. Orders must be confirmed in LIS Orders first.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-slate-600 border-b">
                  <tr>
                    <th className="py-3 px-4">Patient</th>
                    <th className="py-3 px-4">UHID</th>
                    <th className="py-3 px-4">Test</th>
                    <th className="py-3 px-4">Sample</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Location</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Consent</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {worklist.map(item => (
                    <tr key={item.id} className={`hover:bg-slate-50 ${selectedItem?.id === item.id ? "bg-indigo-50" : ""}`}>
                      <td className="py-3 px-4 font-semibold text-slate-800">{item.patient_name || "—"}</td>
                      <td className="py-3 px-4 text-slate-500 font-mono text-xs">{item.patient_uhid || item.patient_id.slice(0, 8)}</td>
                      <td className="py-3 px-4 font-medium text-slate-700">{item.test_name}</td>
                      <td className="py-3 px-4 text-slate-500">{item.sample_type}</td>
                      <td className="py-3 px-4"><span className={`badge border font-bold text-xs ${priBadge(item.priority)}`}>{item.priority}</span></td>
                      <td className="py-3 px-4 text-slate-500 flex items-center gap-1"><MapPin size={12} /> {item.collection_location}</td>
                      <td className="py-3 px-4"><span className={`badge font-bold text-xs ${statusBadge(item.status)}`}>{item.status.replace(/_/g, " ")}</span></td>
                      <td className="py-3 px-4">
                        {item.consent_required ? (
                          item.consent_uploaded ? <span className="text-emerald-600 font-bold text-xs flex items-center gap-1"><CheckCircle2 size={14} /> Done</span>
                            : <span className="text-red-500 font-bold text-xs flex items-center gap-1"><AlertCircle size={14} /> Required</span>
                        ) : <span className="text-slate-400 text-xs">N/A</span>}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {item.status === "PENDING_COLLECTION" && (
                          <button onClick={() => { setSelectedItem(item); setVerified(false); setActiveTab("collect"); }}
                            className="btn-primary py-1.5 px-3 text-xs inline-flex items-center gap-1">
                            <Syringe size={12} /> Collect
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

      {/* ═══════ COLLECT SAMPLE TAB ═══════ */}
      {activeTab === "collect" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Verification & Collection Form */}
          <div className="space-y-6">
            {/* Selected item info */}
            {selectedItem ? (
              <div className="card p-6 border-indigo-200">
                <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 mb-4"><FileText size={18} className="text-indigo-500" /> Selected Order Item</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div><span className="text-slate-500">Patient</span><div className="font-semibold text-slate-800">{selectedItem.patient_name || "—"}</div></div>
                  <div><span className="text-slate-500">UHID</span><div className="font-mono text-slate-700">{selectedItem.patient_uhid || selectedItem.patient_id.slice(0, 8)}</div></div>
                  <div><span className="text-slate-500">Test</span><div className="font-semibold text-slate-800">{selectedItem.test_name}</div></div>
                  <div><span className="text-slate-500">Sample Type</span><div className="text-slate-700">{selectedItem.sample_type}</div></div>
                  <div><span className="text-slate-500">Order #</span><div className="font-mono text-indigo-600 font-bold">{selectedItem.order_number}</div></div>
                  <div><span className="text-slate-500">Priority</span><span className={`badge border font-bold text-xs ${priBadge(selectedItem.priority)}`}>{selectedItem.priority}</span></div>
                </div>

                {/* Consent block */}
                {selectedItem.consent_required && !selectedItem.consent_uploaded && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="font-bold text-red-700 flex items-center gap-2 mb-2"><AlertCircle size={16} /> Consent Required</div>
                    <p className="text-sm text-red-600 mb-3">This test requires patient consent before sample collection.</p>
                    <button onClick={handleUploadConsent} className="btn-primary bg-red-600 hover:bg-red-700 flex items-center gap-2 text-sm">
                      <Upload size={14} /> Upload Consent Document
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="card p-12 text-center border-dashed border-2">
                <Syringe size={48} className="mx-auto mb-4 text-slate-300" />
                <h3 className="font-bold text-slate-600 mb-2">No Item Selected</h3>
                <p className="text-slate-400 text-sm mb-4">Go to the Worklist tab and click &quot;Collect&quot; on a pending item.</p>
                <button onClick={() => setActiveTab("worklist")} className="btn-secondary text-sm">Go to Worklist</button>
              </div>
            )}

            {/* Patient Verification */}
            {selectedItem && (
              <div className="card p-6">
                <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 mb-4"><User size={18} className="text-indigo-500" /> Patient Verification</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1">Verification Method</label>
                    <select className="input-field" value={verifyMethod} onChange={e => setVerifyMethod(e.target.value)}>
                      {VERIFY_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1">Verified By</label>
                    <input className="input-field" placeholder="Collector / Nurse name" value={collectorName} onChange={e => setCollectorName(e.target.value)} />
                  </div>
                  <button onClick={handleVerifyPatient} disabled={loading || !collectorName}
                    className={`w-full py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${verified ? "bg-emerald-600 text-white" : "btn-primary"}`}>
                    {verified ? <><CheckCircle2 size={18} /> Patient Verified ✓</> : <><Shield size={18} /> Verify Patient Identity</>}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right: Collection Details */}
          {selectedItem && (
            <div className="card p-6 space-y-4">
              <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><FlaskConical size={18} className="text-indigo-500" /> Collection Details</h3>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">Container Type</label>
                  <select className="input-field" value={containerType} onChange={e => setContainerType(e.target.value)}>
                    {CONTAINERS.map(c => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1">Collection Location</label>
                  <select className="input-field" value={collectionLocation} onChange={e => setCollectionLocation(e.target.value)}>
                    {LOCATIONS.map(l => <option key={l} value={l}>{l}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">Collector Name *</label>
                <input className="input-field" placeholder="Phlebotomist name" value={collectorName} onChange={e => setCollectorName(e.target.value)} />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">Quantity (ml)</label>
                <input className="input-field" type="number" placeholder="e.g. 5" value={quantityMl} onChange={e => setQuantityMl(e.target.value)} />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">Notes</label>
                <textarea className="input-field" rows={2} placeholder="Collection notes..." value={notes} onChange={e => setNotes(e.target.value)} />
              </div>

              {/* Status indicators */}
              <div className="flex gap-3">
                <div className={`flex-1 p-3 rounded-lg border text-center text-sm font-semibold ${verified ? "bg-emerald-50 border-emerald-300 text-emerald-700" : "bg-slate-50 border-slate-200 text-slate-400"}`}>
                  {verified ? "✓ Identity Verified" : "⏳ Awaiting Verification"}
                </div>
                {selectedItem.consent_required && (
                  <div className={`flex-1 p-3 rounded-lg border text-center text-sm font-semibold ${selectedItem.consent_uploaded ? "bg-emerald-50 border-emerald-300 text-emerald-700" : "bg-red-50 border-red-300 text-red-700"}`}>
                    {selectedItem.consent_uploaded ? "✓ Consent Uploaded" : "⚠ Consent Missing"}
                  </div>
                )}
              </div>

              <button onClick={handleCollectSample} disabled={loading || !verified || !collectorName || (selectedItem.consent_required && !selectedItem.consent_uploaded)}
                className="btn-primary w-full py-3 flex items-center justify-center gap-2 text-lg disabled:opacity-40">
                <Syringe size={20} /> Collect Sample & Generate Barcode
              </button>
            </div>
          )}
        </div>
      )}

      {/* ═══════ TRANSPORT TAB ═══════ */}
      {activeTab === "transport" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Collected samples for dispatch */}
            <div className="card p-6">
              <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 mb-4"><Package size={18} className="text-indigo-500" /> Collected Samples</h3>
              <button onClick={loadSamples} className="btn-secondary text-xs mb-3 flex items-center gap-1"><RefreshCw size={12} /> Refresh</button>
              {samples.filter(s => s.status === "COLLECTED").length === 0 ? (
                <div className="text-center py-8 text-slate-400 border-2 border-dashed rounded-lg">No collected samples pending dispatch</div>
              ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {samples.filter(s => s.status === "COLLECTED").map(s => (
                    <div key={s.id} onClick={() => toggleSampleSelection(s.sample_id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all flex justify-between items-center ${selectedSamples.includes(s.sample_id) ? "bg-indigo-50 border-indigo-300 ring-1 ring-indigo-200" : "bg-white border-slate-200 hover:border-slate-400"}`}>
                      <div>
                        <div className="font-semibold text-sm text-slate-800">{s.test_name}</div>
                        <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                          <Barcode size={12} /> {s.barcode} • {s.sample_type}
                        </div>
                      </div>
                      {selectedSamples.includes(s.sample_id) && <CheckCircle2 size={18} className="text-indigo-600" />}
                    </div>
                  ))}
                </div>
              )}

              {selectedSamples.length > 0 && (
                <div className="mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg space-y-3">
                  <div className="font-bold text-indigo-700">{selectedSamples.length} samples selected for dispatch</div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1">Transport Personnel *</label>
                    <input className="input-field" placeholder="Name" value={transportPersonnel} onChange={e => setTransportPersonnel(e.target.value)} />
                  </div>
                  <select className="input-field" value={transportMethod} onChange={e => setTransportMethod(e.target.value)}>
                    <option value="MANUAL">Manual Carry</option>
                    <option value="PNEUMATIC_TUBE">Pneumatic Tube</option>
                    <option value="COURIER">Courier</option>
                  </select>
                  <button onClick={handleCreateTransportBatch} disabled={loading || !transportPersonnel}
                    className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-40">
                    <Truck size={16} /> Dispatch to Central Receiving
                  </button>
                </div>
              )}
            </div>

            {/* Right: Transport Batches */}
            <div className="card p-6">
              <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 mb-4"><Truck size={18} className="text-indigo-500" /> Transport Batches</h3>
              <button onClick={loadBatches} className="btn-secondary text-xs mb-3 flex items-center gap-1"><RefreshCw size={12} /> Refresh</button>
              {batches.length === 0 ? (
                <div className="text-center py-8 text-slate-400 border-2 border-dashed rounded-lg">No transport batches yet</div>
              ) : (
                <div className="space-y-3">
                  {batches.map(b => (
                    <div key={b.id} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-bold text-slate-800 font-mono">{b.batch_id}</div>
                          <div className="text-xs text-slate-400 mt-0.5">{b.sample_count} samples • {b.transport_method} • {b.transport_personnel}</div>
                        </div>
                        <span className={`badge font-bold text-xs ${b.status === "RECEIVED" ? "bg-emerald-100 text-emerald-700" : b.status === "IN_TRANSIT" ? "bg-amber-100 text-amber-700" : "bg-blue-100 text-blue-700"}`}>
                          {b.status}
                        </span>
                      </div>
                      {b.dispatch_time && <div className="text-xs text-slate-400 flex items-center gap-1"><Clock size={12} /> Dispatched: {new Date(b.dispatch_time).toLocaleString()}</div>}
                      {b.received_time && <div className="text-xs text-emerald-600 flex items-center gap-1"><CheckCircle2 size={12} /> Received: {new Date(b.received_time).toLocaleString()} by {b.received_by}</div>}
                      {b.status === "DISPATCHED" && (
                        <button onClick={() => handleReceiveBatch(b.batch_id)} className="btn-primary mt-3 py-1.5 px-3 text-xs flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700">
                          <CheckCircle2 size={14} /> Confirm Received at Lab
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══════ AUDIT TAB ═══════ */}
      {activeTab === "audit" && (
        <div className="card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2"><Shield size={20} className="text-indigo-500" /> Phlebotomy Audit Trail</h3>
            <button onClick={loadAudit} className="btn-secondary flex items-center gap-2"><RefreshCw size={14} /> Refresh</button>
          </div>
          {auditTrail.length === 0 ? (
            <div className="text-center py-12 text-slate-400 border-2 border-dashed rounded-lg">No audit entries yet. Actions will be logged as samples are collected.</div>
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
    </div>
  );
}
