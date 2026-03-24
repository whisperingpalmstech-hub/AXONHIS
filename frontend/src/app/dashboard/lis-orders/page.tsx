"use client";

import React, { useEffect, useState } from "react";
import {
  FlaskConical, Plus, CheckCircle2, XCircle, Barcode, ScanLine,
  Users, FileText, ChevronRight, Search,
  Layers, Microscope, TestTube2, Syringe, Loader2, User, Stethoscope
} from "lucide-react";
import { api } from "@/lib/api";
import { lisApi } from "@/lib/lis-api";
import type { TestOrderOut, PanelOut, PhlebotomyItem, TestOrderItem } from "@/lib/lis-api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
const authHeaders = () => ({
  Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("access_token") : ""}`,
  "Content-Type": "application/json",
});

const PRIORITIES = ["ROUTINE", "URGENT", "STAT"];

const AVAILABLE_TESTS: TestOrderItem[] = [
  { test_code: "CBC", test_name: "Complete Blood Count", sample_type: "BLOOD", priority: "ROUTINE", price: 350 },
  { test_code: "LIPID", test_name: "Lipid Profile", sample_type: "BLOOD", priority: "ROUTINE", price: 600 },
  { test_code: "HBA1C", test_name: "HbA1c - Glycated Hemoglobin", sample_type: "BLOOD", priority: "ROUTINE", price: 500 },
  { test_code: "LFT", test_name: "Liver Function Test", sample_type: "BLOOD", priority: "ROUTINE", price: 800 },
  { test_code: "KFT", test_name: "Kidney Function Test", sample_type: "BLOOD", priority: "ROUTINE", price: 700 },
  { test_code: "THYROID", test_name: "Thyroid Profile (T3, T4, TSH)", sample_type: "BLOOD", priority: "ROUTINE", price: 900 },
  { test_code: "FBS", test_name: "Fasting Blood Sugar", sample_type: "BLOOD", priority: "ROUTINE", price: 100 },
  { test_code: "URINE_RE", test_name: "Urine Routine Examination", sample_type: "URINE", priority: "ROUTINE", price: 200 },
  { test_code: "CRP", test_name: "C-Reactive Protein", sample_type: "BLOOD", priority: "URGENT", price: 450 },
  { test_code: "ESR", test_name: "Erythrocyte Sedimentation Rate", sample_type: "BLOOD", priority: "ROUTINE", price: 150 },
  { test_code: "TROP", test_name: "Troponin I/T", sample_type: "BLOOD", priority: "STAT", price: 1200 },
  { test_code: "HB", test_name: "Hemoglobin", sample_type: "BLOOD", priority: "ROUTINE", price: 80 },
  { test_code: "ECG", test_name: "Electrocardiogram", sample_type: "OTHER", priority: "ROUTINE", price: 300 },
  { test_code: "VITD", test_name: "Vitamin D (25-Hydroxy)", sample_type: "BLOOD", priority: "ROUTINE", price: 1100 },
  { test_code: "VITB12", test_name: "Vitamin B12", sample_type: "BLOOD", priority: "ROUTINE", price: 900 },
];

interface PatientRecord { id: string; patient_uuid?: string; first_name: string; last_name: string; gender?: string; }
interface DoctorRecord { id: string; username: string; full_name?: string; email?: string; role?: string; }

type TabTypes = "new_order" | "orders" | "panels" | "worklist" | "scan";

export default function LISOrdersPage() {
  const [activeTab, setActiveTab] = useState<TabTypes>("new_order");
  const [orders, setOrders] = useState<TestOrderOut[]>([]);
  const [panels, setPanels] = useState<PanelOut[]>([]);
  const [worklist, setWorklist] = useState<PhlebotomyItem[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<TestOrderOut | null>(null);

  // Patient lookup
  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<PatientRecord | null>(null);
  const [patientsLoading, setPatientsLoading] = useState(false);
  const [showPatientDrop, setShowPatientDrop] = useState(false);

  // Doctor lookup
  const [doctors, setDoctors] = useState<DoctorRecord[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorRecord | null>(null);

  // New order form
  const [orderSource, setOrderSource] = useState("OPD_BILLING");
  const [orderPriority, setOrderPriority] = useState("ROUTINE");
  const [clinicalIndication, setClinicalIndication] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [selectedTests, setSelectedTests] = useState<TestOrderItem[]>([]);
  const [testSearch, setTestSearch] = useState("");

  // Prescription scan
  const [prescriptionText, setPrescriptionText] = useState("");
  const [scanResults, setScanResults] = useState<string[]>([]);

  useEffect(() => { loadDoctors(); loadPanels(); loadWorklist(); }, []);

  useEffect(() => {
    const t = setTimeout(() => fetchPatients(patientSearch), 300);
    return () => clearTimeout(t);
  }, [patientSearch]);

  const fetchPatients = async (q: string) => {
    setPatientsLoading(true);
    try {
      const url = q.length > 0
        ? `${API}/api/v1/patients/search?query=${encodeURIComponent(q)}&limit=15`
        : `${API}/api/v1/patients/?limit=20`;
      const res = await fetch(url, { headers: authHeaders() });
      if (res.ok) { const d = await res.json(); setPatients(Array.isArray(d) ? d : d.items || []); }
    } catch { /* */ } finally { setPatientsLoading(false); }
  };

  const loadDoctors = async () => {
    try { const d = await api.get<any>("/auth/users"); setDoctors(Array.isArray(d) ? d : d?.items || []); } catch { /* */ }
  };
  const loadPanels = async () => { try { setPanels(await lisApi.listPanels()); } catch { /* */ } };
  const loadWorklist = async () => { try { setWorklist(await lisApi.getPhlebotomyWorklist()); } catch { /* */ } };
  const loadPatientOrders = async (pid: string) => { try { setOrders(await lisApi.getPatientOrders(pid)); } catch { /* */ } };

  const toggleTest = (test: TestOrderItem) => {
    const exists = selectedTests.find(t => t.test_code === test.test_code);
    if (exists) setSelectedTests(selectedTests.filter(t => t.test_code !== test.test_code));
    else setSelectedTests([...selectedTests, { ...test }]);
  };
  const updateTestPriority = (code: string, p: string) => setSelectedTests(selectedTests.map(t => t.test_code === code ? { ...t, priority: p } : t));
  const totalPrice = selectedTests.reduce((s, t) => s + (t.price || 0), 0);

  const handleCreateOrder = async () => {
    if (!selectedPatient || selectedTests.length === 0) { alert("Please select a patient and at least one test."); return; }
    try {
      const order = await lisApi.createOrder({
        patient_id: selectedPatient.id,
        ordering_doctor: selectedDoctor ? (selectedDoctor.full_name || selectedDoctor.username) : undefined,
        department_source: orderSource, order_source: orderSource, priority: orderPriority,
        clinical_indication: clinicalIndication, provisional_diagnosis: diagnosis, items: selectedTests,
      });
      alert(`Order created: ${order.order_number}`);
      setSelectedTests([]); setSelectedOrder(order); setActiveTab("orders"); loadPatientOrders(selectedPatient.id);
    } catch (err: any) { alert("Order creation failed: " + (err?.message || "Unknown error")); }
  };

  const handleConfirmOrder = async (id: string) => {
    try {
      const o = await lisApi.confirmOrder(id);
      alert(`Order ${o.order_number} confirmed!`); setSelectedOrder(o); loadWorklist();
      if (selectedPatient) loadPatientOrders(selectedPatient.id);
    } catch (err: any) { alert("Confirm failed: " + (err?.message || "")); }
  };

  const handleCancelOrder = async (id: string) => {
    const reason = prompt("Cancellation reason:"); if (!reason) return;
    try {
      const o = await lisApi.cancelOrder(id, reason);
      alert(`Order ${o.order_number} cancelled.`); setSelectedOrder(o);
      if (selectedPatient) loadPatientOrders(selectedPatient.id);
    } catch (err: any) { alert("Cancel failed: " + (err?.message || "")); }
  };

  const handleScan = async () => {
    if (!prescriptionText.trim()) return;
    try { const r = await lisApi.scanPrescription(prescriptionText); setScanResults(r.detected_tests || []); } catch { alert("Scan failed."); }
  };

  const addScannedTests = () => {
    const nw: TestOrderItem[] = [];
    for (const name of scanResults) {
      const m = AVAILABLE_TESTS.find(t => t.test_name === name);
      if (m && !selectedTests.find(t => t.test_code === m.test_code)) nw.push({ ...m });
    }
    setSelectedTests([...selectedTests, ...nw]); setScanResults([]); setPrescriptionText(""); setActiveTab("new_order");
  };

  const filteredTests = AVAILABLE_TESTS.filter(t =>
    t.test_name.toLowerCase().includes(testSearch.toLowerCase()) || t.test_code.toLowerCase().includes(testSearch.toLowerCase())
  );

  const priBadge = (p: string) => p === "STAT" ? "bg-rose-100 text-rose-700 border-rose-200" : p === "URGENT" ? "bg-amber-100 text-amber-700 border-amber-200" : "bg-emerald-100 text-emerald-700 border-emerald-200";
  const statusBadge = (s: string) => s === "CANCELLED" ? "bg-red-100 text-red-700" : s === "CONFIRMED" || s === "BILLED" ? "bg-blue-100 text-blue-700" : s === "COMPLETED" ? "bg-emerald-100 text-emerald-700" : "bg-yellow-100 text-yellow-700";

  // Shared patient picker
  const PatientPicker = ({ onSelect }: { onSelect?: (p: PatientRecord) => void }) => (
    <div className="relative">
      <label className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-1.5"><User size={14} /> Select Patient *</label>
      <div className="relative">
        <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
        <input
          className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 text-sm"
          placeholder="Search by patient name..."
          value={patientSearch}
          onChange={e => { setPatientSearch(e.target.value); setSelectedPatient(null); setShowPatientDrop(true); }}
          onFocus={() => setShowPatientDrop(true)}
        />
      </div>
      {selectedPatient && (
        <div className="mt-1.5 p-2 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 font-semibold flex items-center gap-2">
          <CheckCircle2 size={14} /> {selectedPatient.first_name} {selectedPatient.last_name}
          <span className="text-slate-400 ml-auto">{selectedPatient.patient_uuid || selectedPatient.id.slice(0, 8)}</span>
        </div>
      )}
      {showPatientDrop && !selectedPatient && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-52 overflow-y-auto">
          {patientsLoading ? (
            <div className="p-3 text-center text-slate-400 text-sm flex items-center justify-center gap-2"><Loader2 size={14} className="animate-spin" /> Loading...</div>
          ) : patients.length === 0 ? (
            <div className="p-3 text-center text-slate-400 text-sm">No patients found</div>
          ) : patients.map(pt => (
            <button key={pt.id} onClick={() => {
              setSelectedPatient(pt); setPatientSearch(`${pt.first_name} ${pt.last_name}`); setShowPatientDrop(false);
              onSelect?.(pt);
            }} className={`w-full text-left px-4 py-2.5 text-sm hover:bg-indigo-50 transition-colors flex items-center justify-between border-b border-slate-100 last:border-0`}>
              <div>
                <span className="font-semibold text-slate-800">{pt.first_name} {pt.last_name}</span>
                {pt.gender && <span className="text-slate-400 text-xs ml-2">{pt.gender}</span>}
              </div>
              <span className="text-xs text-slate-400 font-mono">{pt.patient_uuid || pt.id.slice(0, 8)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3 text-slate-800">
            <FlaskConical className="text-indigo-600" size={32} />
            LIS Test Order Management
          </h1>
          <p className="text-slate-500 mt-1">Order Lab Tests • Barcode Generation • Phlebotomy Routing • Prescription Scanning</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex bg-white rounded-lg p-1 shadow-sm w-fit border border-slate-200">
        {[
          { id: "new_order" as TabTypes, label: "New Order", icon: Plus },
          { id: "orders" as TabTypes, label: "Patient Orders", icon: FileText },
          { id: "panels" as TabTypes, label: "Test Panels", icon: Layers },
          { id: "worklist" as TabTypes, label: "Phlebotomy Worklist", icon: Syringe },
          { id: "scan" as TabTypes, label: "Prescription Scan", icon: ScanLine },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium transition-all ${activeTab === tab.id ? "bg-indigo-50 text-indigo-700 shadow-sm" : "text-slate-600 hover:bg-slate-50"}`}
          >
            <tab.icon size={16} /> {tab.label}
          </button>
        ))}
      </div>

      {/* ═══════ NEW ORDER ═══════ */}
      {activeTab === "new_order" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Patient & Clinical */}
          <div className="card p-6 space-y-4">
            <h3 className="font-bold text-lg flex items-center gap-2 text-slate-800"><Users size={18} className="text-indigo-500" /> Patient & Clinical Info</h3>
            <PatientPicker />

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-1.5"><Stethoscope size={14} /> Ordering Doctor</label>
              <select className="input-field" value={selectedDoctor?.id || ""} onChange={e => setSelectedDoctor(doctors.find(d => d.id === e.target.value) || null)}>
                <option value="">-- Select Doctor --</option>
                {doctors.map(d => <option key={d.id} value={d.id}>{d.full_name || d.username}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Order Source</label>
              <select className="input-field" value={orderSource} onChange={e => setOrderSource(e.target.value)}>
                <option value="OPD_BILLING">OPD Billing</option>
                <option value="DOCTOR_DESK">Doctor Desk</option>
                <option value="IPD_CHARGES">IPD Charges</option>
                <option value="WALKIN_DIAGNOSTIC">Walk-in Diagnostic</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Priority</label>
              <select className="input-field" value={orderPriority} onChange={e => setOrderPriority(e.target.value)}>
                {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <textarea className="input-field" rows={2} placeholder="Clinical Indication" value={clinicalIndication} onChange={e => setClinicalIndication(e.target.value)} />
            <textarea className="input-field" rows={2} placeholder="Provisional Diagnosis" value={diagnosis} onChange={e => setDiagnosis(e.target.value)} />
          </div>

          {/* Center: Test Selection */}
          <div className="card p-6 space-y-4">
            <h3 className="font-bold text-lg flex items-center gap-2 text-slate-800"><Microscope size={18} className="text-indigo-500" /> Select Tests</h3>
            <div className="relative">
              <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
              <input className="input-field pl-10" placeholder="Search tests..." value={testSearch} onChange={e => setTestSearch(e.target.value)} />
            </div>
            <div className="max-h-[460px] overflow-y-auto space-y-2 pr-1">
              {filteredTests.map(test => {
                const sel = selectedTests.some(t => t.test_code === test.test_code);
                return (
                  <button key={test.test_code} onClick={() => toggleTest(test)}
                    className={`w-full text-left p-3 rounded-lg border transition-all text-sm flex justify-between items-center ${sel ? "bg-indigo-50 border-indigo-300" : "bg-white border-slate-200 hover:border-slate-400"}`}>
                    <div>
                      <div className="font-semibold text-slate-800">{test.test_name}</div>
                      <div className="text-xs text-slate-400 mt-0.5">{test.test_code} • {test.sample_type}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono font-bold text-slate-700">₹{test.price}</div>
                      {sel && <CheckCircle2 size={16} className="text-emerald-500 mt-1 ml-auto" />}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right: Order Summary */}
          <div className="card p-6 space-y-4">
            <h3 className="font-bold text-lg flex items-center gap-2 text-slate-800"><TestTube2 size={18} className="text-indigo-500" /> Order Summary</h3>

            {selectedPatient && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm space-y-1">
                <div className="flex justify-between"><span className="text-slate-500">Patient</span><span className="font-semibold text-slate-800">{selectedPatient.first_name} {selectedPatient.last_name}</span></div>
                {selectedDoctor && <div className="flex justify-between"><span className="text-slate-500">Doctor</span><span className="font-semibold text-slate-800">{selectedDoctor.full_name || selectedDoctor.username}</span></div>}
                <div className="flex justify-between"><span className="text-slate-500">Source</span><span className="text-slate-700">{orderSource.replace("_", " ")}</span></div>
              </div>
            )}

            {selectedTests.length === 0 ? (
              <div className="text-center text-slate-400 py-12 border-2 border-dashed rounded-lg">No tests selected yet</div>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {selectedTests.map((t, i) => (
                  <div key={i} className="bg-white border border-slate-200 rounded-lg p-3 flex justify-between items-center shadow-sm">
                    <div>
                      <div className="font-semibold text-sm text-slate-800">{t.test_name}</div>
                      <div className="flex gap-2 mt-1">
                        <select className="text-xs border border-slate-200 rounded px-1.5 py-0.5 bg-white" value={t.priority} onChange={e => updateTestPriority(t.test_code, e.target.value)}>
                          {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                        </select>
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-bold ${priBadge(t.priority)}`}>{t.priority}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm font-bold text-slate-700">₹{t.price}</span>
                      <button onClick={() => toggleTest(t)} className="text-red-400 hover:text-red-600 transition-colors"><XCircle size={16} /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="border-t pt-4 space-y-3">
              <div className="flex justify-between font-bold text-lg text-slate-800">
                <span>Total</span>
                <span className="text-indigo-600">₹{totalPrice.toLocaleString()}</span>
              </div>
              <button onClick={handleCreateOrder} disabled={selectedTests.length === 0 || !selectedPatient}
                className="btn-primary w-full py-3 flex items-center justify-center gap-2 disabled:opacity-40">
                <FlaskConical size={18} /> Create Lab Order ({selectedTests.length} tests)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══════ PATIENT ORDERS ═══════ */}
      {activeTab === "orders" && (
        <div className="space-y-4">
          <div className="card p-6">
            <div className="max-w-md mb-4">
              <PatientPicker onSelect={(pt) => loadPatientOrders(pt.id)} />
            </div>

            {selectedPatient && (
              <div className="text-sm text-emerald-600 font-semibold flex items-center gap-2 mb-4">
                <CheckCircle2 size={14} /> Showing orders for: {selectedPatient.first_name} {selectedPatient.last_name}
              </div>
            )}

            {selectedOrder && (
              <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3 shadow-sm mb-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-xl font-bold text-slate-800 flex items-center gap-2"><FileText size={20} className="text-indigo-500" /> {selectedOrder.order_number}</div>
                    <div className="text-sm text-slate-500 mt-1">Source: {selectedOrder.order_source} • Doctor: {selectedOrder.ordering_doctor || "N/A"}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`badge border font-bold ${priBadge(selectedOrder.priority)}`}>{selectedOrder.priority}</span>
                    <span className={`badge font-bold ${statusBadge(selectedOrder.status)}`}>{selectedOrder.status}</span>
                  </div>
                </div>

                {selectedOrder.clinical_indication && (
                  <div className="text-sm text-slate-600"><span className="text-slate-400">Indication:</span> {selectedOrder.clinical_indication}</div>
                )}

                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-600 border-b">
                      <tr>
                        <th className="py-3 px-4">Test</th>
                        <th className="py-3 px-4">Sample</th>
                        <th className="py-3 px-4">Priority</th>
                        <th className="py-3 px-4">Barcode</th>
                        <th className="py-3 px-4 text-right">Price</th>
                        <th className="py-3 px-4">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {(selectedOrder.items || []).map((item, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          <td className="py-3 px-4 font-semibold text-slate-800">{item.test_name}</td>
                          <td className="py-3 px-4 text-slate-500">{item.sample_type}</td>
                          <td className="py-3 px-4"><span className={`badge border font-bold text-xs ${priBadge(item.priority)}`}>{item.priority}</span></td>
                          <td className="py-3 px-4 font-mono text-xs flex items-center gap-1">{item.barcode ? <><Barcode size={14} className="text-slate-400" /> {item.barcode}</> : "—"}</td>
                          <td className="py-3 px-4 text-right font-mono font-bold text-slate-700">₹{item.price}</td>
                          <td className="py-3 px-4"><span className={`badge font-bold text-xs ${statusBadge(item.status)}`}>{item.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="flex gap-3 pt-2">
                  {selectedOrder.status === "DRAFT" && (
                    <>
                      <button onClick={() => handleConfirmOrder(selectedOrder.id)} className="btn-primary flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700">
                        <CheckCircle2 size={16} /> Confirm & Send to Phlebotomy
                      </button>
                      <button onClick={() => handleCancelOrder(selectedOrder.id)} className="btn-secondary text-red-600 border-red-200 hover:bg-red-50 flex items-center gap-2">
                        <XCircle size={16} /> Cancel Order
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {orders.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-bold text-slate-700">All Orders</h3>
                {orders.map(o => (
                  <button key={o.id} onClick={() => setSelectedOrder(o)}
                    className={`w-full text-left p-4 rounded-lg border transition-all flex justify-between items-center bg-white shadow-sm hover:shadow-md
                      ${selectedOrder?.id === o.id ? "border-indigo-400 ring-1 ring-indigo-200" : "border-slate-200 hover:border-slate-400"}`}>
                    <div>
                      <span className="font-bold text-slate-800">{o.order_number}</span>
                      <span className="text-slate-400 text-sm ml-3">{(o.items || []).length} tests</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`badge border font-bold text-xs ${priBadge(o.priority)}`}>{o.priority}</span>
                      <span className={`badge font-bold text-xs ${statusBadge(o.status)}`}>{o.status}</span>
                      <ChevronRight size={16} className="text-slate-400" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════ PANELS ═══════ */}
      {activeTab === "panels" && (
        <div className="card p-6 space-y-4">
          <h3 className="font-bold text-lg text-slate-800">Available Test Panels & Profiles</h3>
          {(panels || []).length === 0 ? (
            <div className="text-center text-slate-400 py-12 border-2 border-dashed rounded-lg">No panels configured. Panels can be created via API.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {panels.map(panel => (
                <div key={panel.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="font-bold text-lg text-slate-800">{panel.panel_name}</div>
                      <div className="text-xs text-slate-400">{panel.panel_code} • {panel.category || "General"}</div>
                    </div>
                    <div className="text-xl font-bold text-indigo-600">₹{panel.total_price}</div>
                  </div>
                  {panel.description && <div className="text-sm text-slate-500 mb-3">{panel.description}</div>}
                  <div className="space-y-1">
                    {(panel.panel_items || []).map((pi, i) => (
                      <div key={i} className="text-sm flex justify-between py-1 border-b border-slate-100 last:border-0">
                        <span className="text-slate-700">{pi.test_name}</span>
                        <span className="text-slate-400">{pi.sample_type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═══════ PHLEBOTOMY WORKLIST ═══════ */}
      {activeTab === "worklist" && (
        <div className="card p-6 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-lg flex items-center gap-2 text-slate-800"><Syringe size={20} className="text-indigo-500" /> Phlebotomy Sample Collection Worklist</h3>
            <button onClick={loadWorklist} className="btn-secondary flex items-center gap-2"><Loader2 size={14} /> Refresh</button>
          </div>
          {(worklist || []).length === 0 ? (
            <div className="text-center text-slate-400 py-16 border-2 border-dashed rounded-lg">
              <Syringe size={48} className="mx-auto mb-3 opacity-30" />
              No pending samples. Confirm orders to populate worklist.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-slate-600 border-b">
                  <tr>
                    <th className="py-3 px-4">Order #</th>
                    <th className="py-3 px-4">Test</th>
                    <th className="py-3 px-4">Sample Type</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Barcode</th>
                    <th className="py-3 px-4">Location</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {worklist.map((w, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-mono font-bold text-indigo-600">{w.order_number}</td>
                      <td className="py-3 px-4 font-semibold text-slate-800">{w.test_name}</td>
                      <td className="py-3 px-4 text-slate-500">{w.sample_type}</td>
                      <td className="py-3 px-4"><span className={`badge border font-bold text-xs ${priBadge(w.priority)}`}>{w.priority}</span></td>
                      <td className="py-3 px-4 font-mono text-xs flex items-center gap-1"><Barcode size={14} className="text-slate-400" /> {w.barcode || "—"}</td>
                      <td className="py-3 px-4 text-slate-500">{w.collection_location || "OPD"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════ PRESCRIPTION SCAN ═══════ */}
      {activeTab === "scan" && (
        <div className="card p-8 max-w-2xl mx-auto space-y-6">
          <div className="text-center mb-4">
            <ScanLine size={48} className="mx-auto text-indigo-500 mb-4" />
            <h2 className="text-2xl font-bold text-slate-800">Prescription OCR Scanner</h2>
            <p className="text-slate-500">Paste or type prescription text below. The engine will detect laboratory tests automatically.</p>
          </div>
          <textarea
            className="w-full border border-slate-300 rounded-lg p-4 h-40 text-sm font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder={"Paste prescription text here...\n\nExample:\nCBC\nLipid Profile\nHbA1c\nThyroid Profile"}
            value={prescriptionText} onChange={e => setPrescriptionText(e.target.value)}
          />
          <button onClick={handleScan} className="btn-primary w-full py-3 flex items-center justify-center gap-2 text-lg">
            <ScanLine size={18} /> Scan & Detect Tests
          </button>
          {scanResults.length > 0 && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 space-y-3">
              <h4 className="font-bold text-emerald-700 flex items-center gap-2"><CheckCircle2 size={18} /> Detected Tests ({scanResults.length})</h4>
              <div className="space-y-2">
                {scanResults.map((name, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-emerald-800"><CheckCircle2 size={14} className="text-emerald-500" /> {name}</div>
                ))}
              </div>
              <button onClick={addScannedTests} className="btn-primary bg-emerald-600 hover:bg-emerald-700 flex items-center gap-2">
                <Plus size={16} /> Add All to New Order
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
