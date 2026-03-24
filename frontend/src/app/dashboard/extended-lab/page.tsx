"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Home, Truck, Globe2, FlaskConical, Wrench, ShieldCheck, AlertTriangle,
  CheckCircle2, Clock, Plus, Activity, MapPin, Phone, CalendarDays,
  BarChart3, ClipboardList, Building2, Users, Search, ChevronDown
} from "lucide-react";
import {
  extendedLabApi, type HomeCollection, type OutsourceLab,
  type QCRecord, type EquipmentRecord
} from "@/lib/extended-lab-api";
import { api } from "@/lib/api";

// Types from DB
interface PatientOption { id: string; first_name: string; last_name: string; patient_uuid: string; address?: string; primary_phone?: string; }
interface LabTestOption { id: string; code: string; name: string; category: string; }

type Tab = "HOME" | "OUTSOURCE" | "QC" | "EQUIPMENT" | "DASHBOARD";

export default function ExtendedLabPage() {
  const [activeTab, setActiveTab] = useState<Tab>("DASHBOARD");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");

  // Data
  const [homeCollections, setHomeCollections] = useState<HomeCollection[]>([]);
  const [outsourceLabs, setOutsourceLabs] = useState<OutsourceLab[]>([]);
  const [qcRecords, setQcRecords] = useState<QCRecord[]>([]);
  const [equipment, setEquipment] = useState<EquipmentRecord[]>([]);

  // Modals
  const [showHomeModal, setShowHomeModal] = useState(false);
  const [showQCModal, setShowQCModal] = useState(false);
  const [showEquipModal, setShowEquipModal] = useState(false);
  const [showLabModal, setShowLabModal] = useState(false);

  // DB-backed dropdown data
  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [labTests, setLabTests] = useState<LabTestOption[]>([]);
  const [patientSearch, setPatientSearch] = useState("");
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<PatientOption | null>(null);
  const [selectedTests, setSelectedTests] = useState<string[]>([]);
  const patientRef = useRef<HTMLDivElement>(null);

  // Fetch patients & tests for dropdowns
  const fetchDropdownData = useCallback(async () => {
    try {
      const [pts, tests] = await Promise.all([
        api.get<PatientOption[]>('/patients/?skip=0&limit=100'),
        api.get<LabTestOption[]>('/lab/tests')
      ]);
      setPatients(pts || []);
      setLabTests(tests || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchDropdownData(); }, [fetchDropdownData]);

  // Close patient dropdown when clicking outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (patientRef.current && !patientRef.current.contains(e.target as Node)) setShowPatientDropdown(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const filteredPatients = patients.filter(p =>
    `${p.first_name} ${p.last_name} ${p.patient_uuid}`.toLowerCase().includes(patientSearch.toLowerCase())
  );

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === "HOME" || activeTab === "DASHBOARD") setHomeCollections(await extendedLabApi.getHomeCollections() || []);
      if (activeTab === "OUTSOURCE" || activeTab === "DASHBOARD") setOutsourceLabs(await extendedLabApi.getOutsourceLabs() || []);
      if (activeTab === "QC" || activeTab === "DASHBOARD") setQcRecords(await extendedLabApi.getQCs() || []);
      if (activeTab === "EQUIPMENT" || activeTab === "DASHBOARD") setEquipment(await extendedLabApi.getEquipment() || []);
    } catch { /* empty DB is fine */ }
    setLoading(false);
  }, [activeTab]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // --- Handlers ---
  const handleCreateHomeReq = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedPatient) return;
    const fd = new FormData(e.currentTarget);
    await extendedLabApi.createHomeCollection({
      patient_name: `${selectedPatient.first_name} ${selectedPatient.last_name}`,
      patient_uhid: selectedPatient.patient_uuid,
      address: fd.get("address") || selectedPatient.address || '',
      test_requested: selectedTests.join(', '),
      preferred_collection_time: new Date().toISOString()
    });
    setShowHomeModal(false); setSelectedPatient(null); setSelectedTests([]); setPatientSearch('');
    setSuccess("Home collection request created"); fetchData();
  };

  const handleRecordQC = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    await extendedLabApi.recordQC({
      test_name: fd.get("test_name"), equipment_id: fd.get("equipment_id"),
      result_value: parseFloat(fd.get("result_value") as string),
      expected_value: parseFloat(fd.get("expected_value") as string)
    });
    setShowQCModal(false); setSuccess("QC result recorded"); fetchData();
  };

  const handleAddEquipment = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    await extendedLabApi.addEquipment({
      equipment_id: fd.get("equipment_id"), equipment_name: fd.get("equipment_name"),
      maintenance_schedule: fd.get("maintenance_schedule"),
      last_calibration_date: new Date().toISOString(), next_maintenance_date: fd.get("next_maintenance_date"),
      service_history: "Initial registration"
    });
    setShowEquipModal(false); setSuccess("Equipment registered"); fetchData();
  };

  const handleAddLab = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    await extendedLabApi.registerOutsourceLab({
      lab_name: fd.get("lab_name"), contact_details: fd.get("contact_details"),
      test_capabilities: fd.get("test_capabilities")
    });
    setShowLabModal(false); setSuccess("Outsource lab registered"); fetchData();
  };

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: "DASHBOARD", label: "Operations Dashboard", icon: <BarChart3 size={14}/> },
    { key: "HOME", label: "Home Collection", icon: <Home size={14}/> },
    { key: "OUTSOURCE", label: "Outsource Labs", icon: <Globe2 size={14}/> },
    { key: "QC", label: "Quality Control", icon: <FlaskConical size={14}/> },
    { key: "EQUIPMENT", label: "Equipment & Calibration", icon: <Wrench size={14}/> },
  ];

  const qcPassRate = qcRecords.length > 0 ? Math.round((qcRecords.filter(q => q.is_passed).length / qcRecords.length) * 100) : 100;
  const overdueEquipment = equipment.filter(e => e.is_overdue).length;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <TopNav title="LIS Extended Services & Quality Management" />
      <div className="flex-1 p-6 max-w-[1500px] mx-auto w-full space-y-6">

        {/* TAB HEADER */}
        <div className="flex justify-between items-center bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div>
            <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2"><ShieldCheck className="text-teal-600"/> Extended Lab Operations</h1>
            <p className="text-slate-500 font-bold text-[10px] uppercase tracking-widest mt-1">Home Collection • Outsource Labs • QC Management • Equipment Tracking</p>
          </div>
          <div className="flex bg-slate-100 p-1 rounded-xl shadow-inner border border-slate-200">
            {tabs.map(t => (
              <button key={t.key} onClick={() => setActiveTab(t.key)} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-[11px] font-black transition-all ${activeTab === t.key ? 'bg-teal-600 text-white shadow' : 'text-slate-500 hover:text-teal-600'}`}>
                {t.icon} {t.label}
              </button>
            ))}
          </div>
        </div>

        {success && <div className="p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-lg text-xs font-bold flex gap-2 items-center"><CheckCircle2 size={14}/>{success}<button className="ml-auto text-emerald-600" onClick={() => setSuccess("")}>✕</button></div>}

        {/* ==================== OPERATIONS DASHBOARD ==================== */}
        {activeTab === "DASHBOARD" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-teal-500 to-teal-700 text-white p-5 rounded-xl shadow-lg">
                <div className="text-3xl font-black">{homeCollections.length}</div>
                <div className="text-teal-100 text-xs font-bold uppercase mt-1">Home Collections</div>
                <Home size={28} className="mt-2 opacity-30"/>
              </div>
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-700 text-white p-5 rounded-xl shadow-lg">
                <div className="text-3xl font-black">{outsourceLabs.length}</div>
                <div className="text-indigo-100 text-xs font-bold uppercase mt-1">Partner Labs</div>
                <Globe2 size={28} className="mt-2 opacity-30"/>
              </div>
              <div className={`bg-gradient-to-br ${qcPassRate >= 90 ? 'from-emerald-500 to-emerald-700' : 'from-rose-500 to-rose-700'} text-white p-5 rounded-xl shadow-lg`}>
                <div className="text-3xl font-black">{qcPassRate}%</div>
                <div className="text-white/70 text-xs font-bold uppercase mt-1">QC Pass Rate</div>
                <Activity size={28} className="mt-2 opacity-30"/>
              </div>
              <div className={`bg-gradient-to-br ${overdueEquipment > 0 ? 'from-amber-500 to-amber-700' : 'from-slate-500 to-slate-700'} text-white p-5 rounded-xl shadow-lg`}>
                <div className="text-3xl font-black">{equipment.length}</div>
                <div className="text-white/70 text-xs font-bold uppercase mt-1">Equipment Tracked{overdueEquipment > 0 && <span className="text-amber-200"> ({overdueEquipment} overdue)</span>}</div>
                <Wrench size={28} className="mt-2 opacity-30"/>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <button onClick={() => { setActiveTab("HOME"); setShowHomeModal(true); }} className="bg-white border border-slate-200 hover:border-teal-400 p-4 rounded-xl flex items-center gap-3 transition-all shadow-sm hover:shadow-md cursor-pointer">
                <div className="w-10 h-10 bg-teal-100 rounded-lg flex items-center justify-center"><Plus size={16} className="text-teal-700"/></div>
                <div className="text-left"><div className="font-black text-slate-800 text-sm">New Collection</div><div className="text-[10px] text-slate-400 font-bold">Home Pickup Request</div></div>
              </button>
              <button onClick={() => { setActiveTab("OUTSOURCE"); setShowLabModal(true); }} className="bg-white border border-slate-200 hover:border-indigo-400 p-4 rounded-xl flex items-center gap-3 transition-all shadow-sm hover:shadow-md cursor-pointer">
                <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center"><Building2 size={16} className="text-indigo-700"/></div>
                <div className="text-left"><div className="font-black text-slate-800 text-sm">Register Lab</div><div className="text-[10px] text-slate-400 font-bold">Partner Laboratory</div></div>
              </button>
              <button onClick={() => { setActiveTab("QC"); setShowQCModal(true); }} className="bg-white border border-slate-200 hover:border-emerald-400 p-4 rounded-xl flex items-center gap-3 transition-all shadow-sm hover:shadow-md cursor-pointer">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center"><FlaskConical size={16} className="text-emerald-700"/></div>
                <div className="text-left"><div className="font-black text-slate-800 text-sm">Record QC</div><div className="text-[10px] text-slate-400 font-bold">Daily QC Entry</div></div>
              </button>
              <button onClick={() => { setActiveTab("EQUIPMENT"); setShowEquipModal(true); }} className="bg-white border border-slate-200 hover:border-amber-400 p-4 rounded-xl flex items-center gap-3 transition-all shadow-sm hover:shadow-md cursor-pointer">
                <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center"><Wrench size={16} className="text-amber-700"/></div>
                <div className="text-left"><div className="font-black text-slate-800 text-sm">Add Equipment</div><div className="text-[10px] text-slate-400 font-bold">Calibration Tracking</div></div>
              </button>
            </div>

            {/* Accreditation Banner */}
            <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-5 rounded-xl text-white flex items-center justify-between">
              <div>
                <h3 className="font-black text-lg flex items-center gap-2"><ShieldCheck size={20}/> Accreditation Compliance Engine</h3>
                <p className="text-slate-400 text-xs mt-1">NABH • CAP • ISO 15189 — Audit trail reports, QC compliance reports, incident tracking actively monitored.</p>
              </div>
              <div className="flex gap-3">
                <div className="bg-emerald-600/20 border border-emerald-500/30 px-3 py-2 rounded-lg text-center"><div className="text-lg font-black">{qcRecords.length}</div><div className="text-[9px] uppercase opacity-70">QC Checks</div></div>
                <div className="bg-indigo-600/20 border border-indigo-500/30 px-3 py-2 rounded-lg text-center"><div className="text-lg font-black">{equipment.length}</div><div className="text-[9px] uppercase opacity-70">Equipment</div></div>
              </div>
            </div>
          </div>
        )}

        {/* ==================== HOME COLLECTION ==================== */}
        {activeTab === "HOME" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-black text-slate-800 flex items-center gap-2"><Home size={20} className="text-teal-600"/> Home Collection Requests</h2>
              <button onClick={() => setShowHomeModal(true)} className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1 cursor-pointer shadow-sm"><Plus size={14}/> New Request</button>
            </div>
            {homeCollections.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-slate-300">
                <Home size={48} className="text-slate-300 mb-4"/><h3 className="text-slate-500 font-bold">No Home Collection Requests</h3>
                <p className="text-slate-400 text-xs mt-2">Click "New Request" to create one.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {homeCollections.map(hc => (
                  <div key={hc.id} className="bg-white border border-slate-200 rounded-xl shadow-sm p-4 relative overflow-hidden">
                    <div className={`absolute top-0 right-0 px-3 py-1 text-[9px] font-black uppercase rounded-bl-lg ${hc.status === 'Pending' ? 'bg-amber-100 text-amber-800' : hc.status === 'Scheduled' ? 'bg-blue-100 text-blue-800' : 'bg-emerald-100 text-emerald-800'}`}>{hc.status}</div>
                    <h3 className="font-black text-slate-800">{hc.patient_name}</h3>
                    <p className="text-[10px] font-mono text-slate-400">{hc.patient_uhid}</p>
                    <div className="mt-3 space-y-1 text-xs text-slate-600">
                      <div className="flex items-center gap-2"><MapPin size={12} className="text-teal-500"/> {hc.address}</div>
                      <div className="flex items-center gap-2"><ClipboardList size={12} className="text-indigo-500"/> {hc.test_requested}</div>
                      <div className="flex items-center gap-2"><Clock size={12} className="text-slate-400"/> {new Date(hc.created_at).toLocaleString()}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ==================== OUTSOURCE LABS ==================== */}
        {activeTab === "OUTSOURCE" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-black text-slate-800 flex items-center gap-2"><Globe2 size={20} className="text-indigo-600"/> Outsource Laboratory Network</h2>
              <button onClick={() => setShowLabModal(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1 cursor-pointer shadow-sm"><Plus size={14}/> Register Lab</button>
            </div>
            {outsourceLabs.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-slate-300">
                <Globe2 size={48} className="text-slate-300 mb-4"/><h3 className="text-slate-500 font-bold">No Partner Labs Registered</h3>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {outsourceLabs.map(lab => (
                  <div key={lab.id} className="bg-white border border-slate-200 rounded-xl shadow-sm p-5">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center"><Building2 size={18} className="text-indigo-700"/></div>
                      <div><h3 className="font-black text-slate-800">{lab.lab_name}</h3><p className="text-[10px] text-slate-400"> {lab.is_active ? "Active" : "Inactive"}</p></div>
                    </div>
                    <div className="text-xs text-slate-600 space-y-1">
                      <div className="flex items-center gap-2"><Phone size={12}/> {lab.contact_details}</div>
                      <div className="mt-2"><span className="text-[9px] font-bold uppercase text-slate-400">Capabilities:</span> <span className="text-xs text-indigo-700 font-bold">{lab.test_capabilities}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ==================== QUALITY CONTROL ==================== */}
        {activeTab === "QC" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-black text-slate-800 flex items-center gap-2"><FlaskConical size={20} className="text-emerald-600"/> Laboratory Quality Control</h2>
              <button onClick={() => setShowQCModal(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1 cursor-pointer shadow-sm"><Plus size={14}/> Record QC</button>
            </div>
            {qcRecords.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-slate-300">
                <FlaskConical size={48} className="text-slate-300 mb-4"/><h3 className="text-slate-500 font-bold">No QC Records</h3>
              </div>
            ) : (
              <div className="overflow-x-auto bg-white rounded-xl shadow-sm border border-slate-200">
                <table className="w-full text-left text-sm">
                  <thead className="bg-emerald-50 border-b border-emerald-100 text-[10px] uppercase font-black text-emerald-800">
                    <tr><th className="p-3">Test</th><th className="p-3">Equipment</th><th className="p-3">Result / Expected</th><th className="p-3">Status</th><th className="p-3">Date</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {qcRecords.map(qc => (
                      <tr key={qc.id} className="hover:bg-slate-50">
                        <td className="p-3 font-bold text-slate-700">{qc.test_name}</td>
                        <td className="p-3 font-mono text-xs text-slate-500">{qc.equipment_id}</td>
                        <td className="p-3"><span className="font-bold">{qc.result_value}</span> <span className="text-slate-400">/ {qc.expected_value}</span></td>
                        <td className="p-3">
                          {qc.is_passed ? (
                            <span className="text-[10px] font-black uppercase bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full border border-emerald-200 flex items-center gap-1 w-max"><CheckCircle2 size={12}/> PASS</span>
                          ) : (
                            <span className="text-[10px] font-black uppercase bg-rose-100 text-rose-700 px-2 py-1 rounded-full border border-rose-200 flex items-center gap-1 w-max"><AlertTriangle size={12}/> FAIL</span>
                          )}
                        </td>
                        <td className="p-3 text-xs text-slate-400">{new Date(qc.qc_date).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ==================== EQUIPMENT ==================== */}
        {activeTab === "EQUIPMENT" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-black text-slate-800 flex items-center gap-2"><Wrench size={20} className="text-amber-600"/> Equipment Calibration & Maintenance</h2>
              <button onClick={() => setShowEquipModal(true)} className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1 cursor-pointer shadow-sm"><Plus size={14}/> Add Equipment</button>
            </div>
            {equipment.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-slate-300">
                <Wrench size={48} className="text-slate-300 mb-4"/><h3 className="text-slate-500 font-bold">No Equipment Registered</h3>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {equipment.map(eq => (
                  <div key={eq.id} className={`bg-white p-4 rounded-xl shadow-sm border-l-4 ${eq.is_overdue ? 'border-l-rose-500 border border-rose-200' : 'border-l-emerald-500 border border-slate-200'}`}>
                    <div className="flex justify-between items-start">
                      <div><h3 className="font-black text-slate-800">{eq.equipment_name}</h3><p className="text-[10px] font-mono text-slate-400">{eq.equipment_id}</p></div>
                      {eq.is_overdue && <span className="text-[9px] font-black uppercase bg-rose-100 text-rose-700 px-2 py-0.5 rounded border border-rose-200 flex items-center gap-1"><AlertTriangle size={10}/> OVERDUE</span>}
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                      <div><span className="text-[9px] uppercase font-bold text-slate-400 block">Schedule</span>{eq.maintenance_schedule}</div>
                      <div><span className="text-[9px] uppercase font-bold text-slate-400 block">Last Calibration</span>{new Date(eq.last_calibration_date).toLocaleDateString()}</div>
                      <div><span className="text-[9px] uppercase font-bold text-slate-400 block">Next Maintenance</span><span className={eq.is_overdue ? 'text-rose-600 font-bold' : ''}>{new Date(eq.next_maintenance_date).toLocaleDateString()}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ==================== MODALS ==================== */}
      {showHomeModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateHomeReq} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Home size={20} className="text-teal-600"/> New Home Collection</h3>

            {/* Patient Searchable Dropdown */}
            <div ref={patientRef} className="relative">
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Select Patient</label>
              <div className="relative">
                <Search size={14} className="absolute left-3 top-3 text-slate-400"/>
                <input
                  value={selectedPatient ? `${selectedPatient.first_name} ${selectedPatient.last_name} (${selectedPatient.patient_uuid})` : patientSearch}
                  onChange={e => { setPatientSearch(e.target.value); setSelectedPatient(null); setShowPatientDropdown(true); }}
                  onFocus={() => setShowPatientDropdown(true)}
                  placeholder="Search patient by name or UHID..."
                  className="w-full p-2.5 pl-9 pr-8 border border-slate-300 rounded-lg text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-200 outline-none"
                  required
                />
                <ChevronDown size={14} className="absolute right-3 top-3 text-slate-400"/>
              </div>
              {showPatientDropdown && filteredPatients.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-48 overflow-y-auto">
                  {filteredPatients.map(p => (
                    <button key={p.id} type="button" onClick={() => { setSelectedPatient(p); setShowPatientDropdown(false); setPatientSearch(''); }}
                      className="w-full text-left px-4 py-2.5 hover:bg-teal-50 flex items-center justify-between text-sm border-b border-slate-50 cursor-pointer">
                      <div><span className="font-bold text-slate-800">{p.first_name} {p.last_name}</span><span className="text-[10px] text-slate-400 ml-2 font-mono">{p.patient_uuid}</span></div>
                      {p.primary_phone && <span className="text-[10px] text-slate-400">{p.primary_phone}</span>}
                    </button>
                  ))}
                </div>
              )}
              {showPatientDropdown && filteredPatients.length === 0 && patientSearch && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-xl p-3 text-xs text-slate-400 text-center">No patients found</div>
              )}
            </div>

            {/* Auto-filled UHID */}
            {selectedPatient && (
              <div className="bg-teal-50 border border-teal-200 rounded-lg p-3 flex items-center gap-3">
                <div className="w-8 h-8 bg-teal-600 text-white rounded-full flex items-center justify-center text-xs font-black">{selectedPatient.first_name[0]}{selectedPatient.last_name[0]}</div>
                <div><div className="font-bold text-slate-800 text-sm">{selectedPatient.first_name} {selectedPatient.last_name}</div><div className="text-[10px] text-teal-700 font-mono">UHID: {selectedPatient.patient_uuid}</div></div>
              </div>
            )}

            {/* Address - pre-filled from patient */}
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Collection Address</label>
              <input name="address" required placeholder="Collection address" defaultValue={selectedPatient?.address || ''}
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm focus:border-teal-500 outline-none"/>
            </div>

            {/* Test Dropdown (Multi-Select) */}
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Tests Required</label>
              {labTests.length > 0 ? (
                <div className="border border-slate-300 rounded-lg max-h-40 overflow-y-auto">
                  {labTests.map(t => (
                    <label key={t.id} className="flex items-center gap-2 px-3 py-2 hover:bg-slate-50 text-sm border-b border-slate-50 cursor-pointer">
                      <input type="checkbox" checked={selectedTests.includes(t.name)} onChange={e => {
                        if (e.target.checked) setSelectedTests(prev => [...prev, t.name]);
                        else setSelectedTests(prev => prev.filter(x => x !== t.name));
                      }} className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"/>
                      <span className="font-bold text-slate-700">{t.name}</span>
                      <span className="text-[10px] text-slate-400 ml-auto">{t.category} • {t.code}</span>
                    </label>
                  ))}
                </div>
              ) : (
                <input name="test_requested_manual" placeholder="Type test names" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"/>
              )}
              {selectedTests.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {selectedTests.map(t => (
                    <span key={t} className="bg-teal-100 text-teal-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-teal-200 flex items-center gap-1">
                      {t} <button type="button" onClick={() => setSelectedTests(prev => prev.filter(x => x !== t))} className="cursor-pointer text-teal-600 hover:text-teal-800">✕</button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => { setShowHomeModal(false); setSelectedPatient(null); setSelectedTests([]); }} className="px-4 py-2 text-slate-600 text-sm font-bold cursor-pointer">Cancel</button>
              <button type="submit" disabled={!selectedPatient || selectedTests.length === 0} className="bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-bold cursor-pointer">Create Request</button>
            </div>
          </form>
        </div>
      )}

      {showLabModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleAddLab} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Building2 size={20} className="text-indigo-600"/> Register Outsource Lab</h3>
            <input name="lab_name" required placeholder="Laboratory Name" className="w-full p-2.5 border rounded-lg text-sm"/>
            <input name="contact_details" required placeholder="Contact Details" className="w-full p-2.5 border rounded-lg text-sm"/>
            <input name="test_capabilities" required placeholder="Test Capabilities (comma separated)" className="w-full p-2.5 border rounded-lg text-sm"/>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowLabModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold cursor-pointer">Cancel</button>
              <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold cursor-pointer">Register</button>
            </div>
          </form>
        </div>
      )}

      {showQCModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleRecordQC} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><FlaskConical size={20} className="text-emerald-600"/> Record QC Result</h3>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Test Name</label>
              {labTests.length > 0 ? (
                <select name="test_name" required className="w-full p-2.5 border border-slate-300 rounded-lg text-sm focus:border-emerald-500 outline-none">
                  <option value="">— Select Test —</option>
                  {labTests.map(t => <option key={t.id} value={t.name}>{t.name} ({t.code})</option>)}
                </select>
              ) : (
                <input name="test_name" required placeholder="Test Name" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"/>
              )}
            </div>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Equipment</label>
              {equipment.length > 0 ? (
                <select name="equipment_id" required className="w-full p-2.5 border border-slate-300 rounded-lg text-sm focus:border-emerald-500 outline-none">
                  <option value="">— Select Equipment —</option>
                  {equipment.map(eq => <option key={eq.id} value={eq.equipment_id}>{eq.equipment_name} ({eq.equipment_id})</option>)}
                </select>
              ) : (
                <input name="equipment_id" required placeholder="Equipment ID" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"/>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Result Value</label>
                <input name="result_value" type="number" step="0.01" required placeholder="e.g. 95.5" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"/>
              </div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Expected Value</label>
                <input name="expected_value" type="number" step="0.01" required placeholder="e.g. 100" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"/>
              </div>
            </div>
            <p className="text-[10px] text-slate-400 bg-slate-50 p-2 rounded">⚡ Auto-evaluation: PASS if result is within ±10% of expected value.</p>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowQCModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold cursor-pointer">Cancel</button>
              <button type="submit" className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-bold cursor-pointer">Submit QC</button>
            </div>
          </form>
        </div>
      )}

      {showEquipModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleAddEquipment} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Wrench size={20} className="text-amber-600"/> Register Equipment</h3>
            <input name="equipment_id" required placeholder="Equipment ID (e.g. EQ-001)" className="w-full p-2.5 border rounded-lg text-sm"/>
            <input name="equipment_name" required placeholder="Equipment Name" className="w-full p-2.5 border rounded-lg text-sm"/>
            <select name="maintenance_schedule" className="w-full p-2.5 border rounded-lg text-sm" required>
              <option value="Daily">Daily</option><option value="Weekly">Weekly</option><option value="Monthly">Monthly</option><option value="Quarterly">Quarterly</option>
            </select>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">Next Maintenance Date</label>
              <input name="next_maintenance_date" type="datetime-local" required className="w-full p-2.5 border rounded-lg text-sm"/>
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowEquipModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold cursor-pointer">Cancel</button>
              <button type="submit" className="bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-bold cursor-pointer">Register</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
