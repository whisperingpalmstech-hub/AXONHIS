"use client";
import { useTranslation } from "@/i18n";

import React, { useEffect, useState, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Siren, Users, AlertTriangle, Bed, Heart, Shield, Clock, Plus, Search,
  Activity, Thermometer, MapPin, ChevronDown, X, FileText, Stethoscope,
  Zap, Eye, Brain, Baby, CheckCircle2, AlertCircle, ClipboardList, LogOut,
  CreditCard, PenTool, Pill, TestTube
} from "lucide-react";
import { api } from "@/lib/api";
import { WorkflowPipeline } from "@/components/ui/WorkflowPipeline";

type Tab = "COMMAND_CENTER" | "PATIENTS" | "TRIAGE" | "BED_MAP" | "MLC" | "COVER_SHEET" | "DISCHARGE";

const ZONE_COLORS: Record<string, { bg: string; text: string; border: string; label: string }> = {
  red: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200", label: "er.zoneResuscitation" },
  yellow: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", label: "er.zoneAcuteCare" },
  green: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200", label: "er.zoneFastTrack" },
  peds: { bg: "bg-violet-50", text: "text-violet-700", border: "border-violet-200", label: "er.zonePediatrics" },
  obs: { bg: "bg-sky-50", text: "text-sky-700", border: "border-sky-200", label: "er.zoneObservation" },
};

const TRIAGE_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  resuscitation: { bg: "bg-red-100", text: "text-red-800", dot: "bg-red-500" },
  emergent: { bg: "bg-orange-100", text: "text-orange-800", dot: "bg-orange-500" },
  urgent: { bg: "bg-yellow-100", text: "text-yellow-800", dot: "bg-yellow-500" },
  less_urgent: { bg: "bg-green-100", text: "text-green-800", dot: "bg-green-500" },
  non_urgent: { bg: "bg-blue-100", text: "text-blue-800", dot: "bg-blue-500" },
  dead: { bg: "bg-gray-100", text: "text-gray-800", dot: "bg-gray-800" },
};

export default function ERDashboard() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<Tab>("COMMAND_CENTER");
  const [stats, setStats] = useState<any>(null);
  const [encounters, setEncounters] = useState<any[]>([]);
  const [beds, setBeds] = useState<any[]>([]);
  const [mlcCases, setMlcCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showRegModal, setShowRegModal] = useState(false);
  const [showTriageModal, setShowTriageModal] = useState<string | null>(null);
  const [showMlcModal, setShowMlcModal] = useState<string | null>(null);
  const [showBedAssignModal, setShowBedAssignModal] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedEncounter, setSelectedEncounter] = useState<any>(null);
  const [coverSheetTab, setCoverSheetTab] = useState("complaints");
  const [clinicalNotes, setClinicalNotes] = useState<any[]>([]);
  const [diagnoses, setDiagnoses] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [dueForDischarge, setDueForDischarge] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [s, e, b, m] = await Promise.all([
        api.get<any>("/er/dashboard").catch(() => null),
        api.get<any[]>("/er/encounters").catch(() => []),
        api.get<any[]>("/er/beds").catch(() => []),
        api.get<any[]>("/er/mlc").catch(() => []),
      ]);
      if (s) setStats(s);
      setEncounters(e || []);
      setBeds(b || []);
      setMlcCases(m || []);
    } catch (err) { console.error(err); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const fetchDueForDischarge = async () => {
    try {
      const d = await api.get<any[]>("/er/due-for-discharge").catch(() => []);
      setDueForDischarge(d || []);
    } catch { }
  };

  const fetchClinicalNotes = async (encId: string) => {
    try {
      const n = await api.get<any[]>(`/er/notes/${encId}`).catch(() => []);
      setClinicalNotes(n || []);
    } catch { }
  };

  const fetchDiagnoses = async (encId: string) => {
    try {
      const d = await api.get<any[]>(`/er/diagnoses/${encId}`).catch(() => []);
      setDiagnoses(d || []);
    } catch { }
  };

  const fetchOrders = async (encId: string) => {
    try {
      const o = await api.get<any[]>(`/er/orders/${encId}`).catch(() => []);
      setOrders(o || []);
    } catch { }
  };

  const openCoverSheet = (enc: any) => {
    setSelectedEncounter(enc);
    setActiveTab("COVER_SHEET");
    setCoverSheetTab("complaints");
    fetchClinicalNotes(enc.id);
    fetchDiagnoses(enc.id);
    fetchOrders(enc.id);
  };

  const handleSaveNote = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/er/notes", {
        er_encounter_id: selectedEncounter?.id,
        note_type: fd.get("note_type"),
        content: fd.get("content"),
        structured_data: {
          medical_hx: fd.get("medical_hx") || undefined,
          surgical_hx: fd.get("surgical_hx") || undefined,
          allergies: fd.get("allergies") || undefined,
          medications: fd.get("medications") || undefined,
          temperature: fd.get("temperature") || undefined,
          pulse: fd.get("pulse") || undefined,
          bp: fd.get("bp") || undefined,
          spo2: fd.get("spo2") || undefined,
          rr: fd.get("rr") || undefined,
          gcs: fd.get("gcs") || undefined,
          pain: fd.get("pain") || undefined,
          glucose: fd.get("glucose") || undefined,
        }
      });
      alert("✓ Saved successfully");
      if (selectedEncounter) fetchClinicalNotes(selectedEncounter.id);
      (e.target as HTMLFormElement).reset();
    } catch { alert("Failed to save note"); }
    setSaving(false);
  };

  const handleAddDiagnosis = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/er/diagnoses", {
        er_encounter_id: selectedEncounter?.id,
        icd_code: fd.get("icd_code"),
        diagnosis_description: fd.get("diagnosis_description"),
        diagnosis_type: fd.get("diagnosis_type"),
        is_primary: fd.get("is_primary") === "on",
      });
      alert("✓ Diagnosis added");
      if (selectedEncounter) fetchDiagnoses(selectedEncounter.id);
      (e.target as HTMLFormElement).reset();
    } catch { alert("Failed to add diagnosis"); }
    setSaving(false);
  };

  const handlePlaceOrder = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/er/orders", {
        er_encounter_id: selectedEncounter?.id,
        order_type: fd.get("order_type"),
        order_description: fd.get("order_description"),
        priority: fd.get("priority") || "stat",
      });
      alert("✓ Order placed → Routed to " + fd.get("order_type")?.toString().toUpperCase() + " module");
      if (selectedEncounter) fetchOrders(selectedEncounter.id);
      (e.target as HTMLFormElement).reset();
    } catch { alert("Failed to place order"); }
    setSaving(false);
  };

  const handleDischarge = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/er/discharge", {
        er_encounter_id: fd.get("er_encounter_id"),
        discharge_type: fd.get("discharge_type"),
        discharge_summary: fd.get("discharge_summary"),
        follow_up_instructions: fd.get("follow_up_instructions"),
        payment_mode: fd.get("payment_mode"),
        total_amount: fd.get("total_amount") ? parseFloat(fd.get("total_amount") as string) : undefined,
        paid_amount: fd.get("paid_amount") ? parseFloat(fd.get("paid_amount") as string) : undefined,
        disposition: fd.get("disposition"),
      });
      alert("Patient discharged. Bed auto-released.");
      fetchData();
      fetchDueForDischarge();
      setActiveTab("COMMAND_CENTER");
    } catch { alert("Discharge failed"); }
  };

  const handleBedAssign = async (bedId: string) => {
    if (!showBedAssignModal) return;
    try {
      await api.post("/er/beds/assign", {
        er_encounter_id: showBedAssignModal,
        bed_id: bedId,
      });
      setShowBedAssignModal(null);
      fetchData();
    } catch { alert("Bed assignment failed"); }
  };

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/er/register", {
        registration_type: fd.get("registration_type"),
        patient_name: fd.get("patient_name"),
        age: fd.get("age") ? parseInt(fd.get("age") as string) : undefined,
        gender: fd.get("gender"),
        mobile: fd.get("mobile"),
        chief_complaint: fd.get("chief_complaint"),
        mode_of_arrival: fd.get("mode_of_arrival"),
      });
      setShowRegModal(false);
      fetchData();
    } catch { alert(t("er.regFailed")); }
  };

  const handleTriage = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/er/triage", {
        er_encounter_id: showTriageModal,
        triage_category: fd.get("triage_category"),
        temperature: fd.get("temperature") ? parseFloat(fd.get("temperature") as string) : undefined,
        pulse: fd.get("pulse") ? parseInt(fd.get("pulse") as string) : undefined,
        bp_systolic: fd.get("bp_systolic") ? parseInt(fd.get("bp_systolic") as string) : undefined,
        bp_diastolic: fd.get("bp_diastolic") ? parseInt(fd.get("bp_diastolic") as string) : undefined,
        respiratory_rate: fd.get("respiratory_rate") ? parseInt(fd.get("respiratory_rate") as string) : undefined,
        spo2: fd.get("spo2") ? parseFloat(fd.get("spo2") as string) : undefined,
        gcs_score: fd.get("gcs_score") ? parseInt(fd.get("gcs_score") as string) : undefined,
        pain_score: fd.get("pain_score") ? parseInt(fd.get("pain_score") as string) : undefined,
        triage_notes: fd.get("triage_notes"),
      });
      setShowTriageModal(null);
      fetchData();
    } catch { alert(t("er.triageFailed")); }
  };

  const handleCreateMlc = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/er/mlc", {
        er_encounter_id: showMlcModal,
        mlc_type: fd.get("mlc_type"),
        priority: fd.get("priority"),
        police_station: fd.get("police_station"),
        fir_number: fd.get("fir_number"),
        injury_description: fd.get("injury_description"),
      });
      setShowMlcModal(null);
      fetchData();
    } catch { alert(t("er.mlcFailed")); }
  };

  const handleSeedBeds = async () => {
    await api.post("/er/seed-beds", {});
    fetchData();
  };

  const updateStatus = async (id: string, newStatus: string) => {
    try {
      await api.put(`/er/encounters/${id}/status`, { status: newStatus });
      fetchData();
    } catch { alert(t("er.updateStatusFailed")); }
  };

  const filteredEncounters = encounters.filter(e =>
    `${e.patient_name} ${e.er_number} ${e.chief_complaint || ""}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const map: Record<string, string> = {
      registered: "bg-blue-100 text-blue-700",
      triaged: "bg-amber-100 text-amber-700",
      in_treatment: "bg-emerald-100 text-emerald-700",
      observation: "bg-sky-100 text-sky-700",
      due_for_discharge: "bg-purple-100 text-purple-700",
      discharged: "bg-slate-100 text-slate-600",
    };
    return map[status] || "bg-slate-100 text-slate-600";
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <TopNav title="Emergency Room" />
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
              <Siren className="text-red-500" size={32}/>{t("er.emergencyDepartment")}</h1>
            <p className="text-slate-500 font-medium mt-1">{t("er.digitalCommandCenter")}</p>
          </div>
          <div className="flex gap-3">
            <button onClick={handleSeedBeds} className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2.5 rounded-xl font-bold transition-all text-sm">
              <Bed size={16}/>{t("er.seedBeds")}</button>
            <button onClick={() => setShowRegModal(true)} className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-xl font-bold transition-all shadow-md shadow-red-200">
              <Plus size={18}/>{t("er.registerErPatient")}</button>
          </div>
        </div>

        {/* Workflow */}
        <div className="mb-6">
          <WorkflowPipeline title={t("er.erPatientFlow")} colorScheme="amber" steps={[
            { label: t("er.reg"), status: "done" },
            { label: t("er.triageEsi"), status: "active" },
            { label: t("er.bedAssign"), status: "pending" },
            { label: t("er.tx"), status: "pending" },
            { label: t("er.disposition"), status: "pending" },
            { label: t("er.dischargeAdmit"), status: "pending" },
          ]} />
        </div>

        {/* Tabs */}
        <div className="flex gap-2 p-1.5 bg-white/50 backdrop-blur border border-slate-200 rounded-2xl w-fit mb-6 shadow-sm">
          {[
            { id: "COMMAND_CENTER", label: t("er.commandCenter"), icon: <Activity size={16}/> },
            { id: "PATIENTS", label: t("er.patientList"), icon: <Users size={16}/> },
            { id: "TRIAGE", label: t("er.triageQueue"), icon: <Stethoscope size={16}/> },
            { id: "BED_MAP", label: t("er.bedMap"), icon: <MapPin size={16}/> },
            { id: "COVER_SHEET", label: "Nursing Cover Sheet", icon: <ClipboardList size={16}/> },
            { id: "DISCHARGE", label: "Discharge", icon: <LogOut size={16}/> },
            { id: "MLC", label: t("er.mlcCasesTab"), icon: <Shield size={16}/> },
          ].map(tObj => (
            <button key={tObj.id} onClick={() => {
              setActiveTab(tObj.id as Tab);
              if (tObj.id === "DISCHARGE") fetchDueForDischarge();
            }}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
                activeTab === tObj.id ? "bg-white text-red-700 shadow-sm border border-slate-200/50" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100/50"
              }`}>
              {tObj.icon} {tObj.label}
              {tObj.id === "TRIAGE" && encounters.filter(e => e.status === "registered").length > 0 && (
                <span className="bg-red-100 text-red-600 text-[10px] px-1.5 py-0.5 rounded-full ml-1 animate-pulse">{encounters.filter(e => e.status === "registered").length}</span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-400 font-medium">{t("er.loadingErData")}</div>
        ) : (
          <div className="space-y-6">

            {/* COMMAND CENTER */}
            {activeTab === "COMMAND_CENTER" && stats && (
              <div className="space-y-6">
                <div className="grid grid-cols-5 gap-4">
                  <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                    <div className="text-slate-500 font-bold text-xs mb-1 flex items-center gap-1"><Users size={14}/>{t("er.totalActive")}</div>
                    <div className="text-4xl font-black text-slate-800">{stats.total_patients}</div>
                  </div>
                  <div className="bg-white p-5 rounded-2xl border border-red-100 shadow-sm">
                    <div className="text-red-500 font-bold text-xs mb-1 flex items-center gap-1"><AlertTriangle size={14}/>{t("er.critical")}</div>
                    <div className="text-4xl font-black text-red-600">{stats.critical}</div>
                  </div>
                  <div className="bg-white p-5 rounded-2xl border border-amber-100 shadow-sm">
                    <div className="text-amber-500 font-bold text-xs mb-1 flex items-center gap-1"><Clock size={14}/>{t("er.awaitingTriage")}</div>
                    <div className="text-4xl font-black text-amber-600">{stats.awaiting_triage}</div>
                  </div>
                  <div className="bg-white p-5 rounded-2xl border border-emerald-100 shadow-sm">
                    <div className="text-emerald-500 font-bold text-xs mb-1 flex items-center gap-1"><Bed size={14}/>{t("er.bedsAvailable")}</div>
                    <div className="text-4xl font-black text-emerald-600">{stats.beds_available}<span className="text-lg text-slate-400">/{stats.beds_total}</span></div>
                  </div>
                  <div className="bg-white p-5 rounded-2xl border border-purple-100 shadow-sm">
                    <div className="text-purple-500 font-bold text-xs mb-1 flex items-center gap-1"><Shield size={14}/>{t("er.mlcCases")}</div>
                    <div className="text-4xl font-black text-purple-600">{stats.mlc_cases}</div>
                  </div>
                </div>

                {/* Zone Occupancy */}
                {stats.zone_occupancy && (
                  <div>
                    <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider mb-3">{t("er.zoneOccupancy")}</h3>
                    <div className="grid grid-cols-5 gap-4">
                      {Object.entries(stats.zone_occupancy).map(([zone, data]: [string, any]) => {
                        const zc = ZONE_COLORS[zone] || ZONE_COLORS.green;
                        const pct = data.total > 0 ? Math.round((data.occupied / data.total) * 100) : 0;
                        return (
                          <div key={zone} className={`p-4 rounded-2xl border ${zc.border} ${zc.bg}`}>
                            <div className={`text-xs font-black uppercase ${zc.text} mb-2`}>{t(zc.label)}</div>
                            <div className="flex justify-between items-end">
                              <div className={`text-2xl font-black ${zc.text}`}>{data.occupied}<span className="text-sm font-medium">/{data.total}</span></div>
                              <div className={`text-xs font-bold ${zc.text} opacity-70`}>{pct}%</div>
                            </div>
                            <div className="mt-2 h-2 bg-white/50 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full transition-all ${zone === 'red' ? 'bg-red-500' : zone === 'yellow' ? 'bg-amber-500' : zone === 'peds' ? 'bg-violet-500' : zone === 'obs' ? 'bg-sky-500' : 'bg-emerald-500'}`}
                                style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* PATIENT LIST */}
            {activeTab === "PATIENTS" && (
              <div>
                <div className="mb-4 relative">
                  <Search size={16} className="absolute left-3 top-3 text-slate-400"/>
                  <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="Search by name, ER number, complaint..."
                    className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:border-red-400 outline-none"/>
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                        <th className="p-4 font-bold">{t("er.erHash")}</th>
                        <th className="p-4 font-bold">{t("er.patient")}</th>
                        <th className="p-4 font-bold">{t("er.complaint")}</th>
                        <th className="p-4 font-bold">{t("er.priority")}</th>
                        <th className="p-4 font-bold">{t("er.zone")}</th>
                        <th className="p-4 font-bold">{t("er.status")}</th>
                        <th className="p-4 font-bold">{t("er.arrival")}</th>
                        <th className="p-4 font-bold text-right">{t("er.actions")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredEncounters.length === 0 ? (
                        <tr><td colSpan={8} className="p-8 text-center text-slate-400 font-medium">{t("er.noActiveErPatients")}</td></tr>
                      ) : (
                        filteredEncounters.map(enc => {
                          const tc = enc.priority ? TRIAGE_COLORS[enc.priority] : null;
                          return (
                            <tr key={enc.id} className="hover:bg-slate-50/50 transition-colors">
                              <td className="p-4 font-mono text-sm font-bold text-slate-700">{enc.er_number}</td>
                              <td className="p-4">
                                <div className="font-bold text-slate-800 text-sm flex items-center gap-2">
                                  {enc.patient_name}
                                  {enc.is_critical && <AlertTriangle size={14} className="text-red-500"/>}
                                  {enc.is_mlc && <Shield size={14} className="text-purple-500"/>}
                                  {enc.is_allergy && <AlertCircle size={14} className="text-orange-500"/>}
                                </div>
                                <div className="text-xs text-slate-500">{enc.age ? `${enc.age}y` : ''} {enc.gender || ''}</div>
                              </td>
                              <td className="p-4 text-sm text-slate-600 max-w-[200px] truncate">{enc.chief_complaint || '—'}</td>
                              <td className="p-4">
                                {tc ? (
                                  <span className={`text-[10px] uppercase font-black px-2 py-1 rounded-md ${tc.bg} ${tc.text}`}>
                                    <span className={`inline-block w-2 h-2 rounded-full ${tc.dot} mr-1`}></span>
                                    {enc.priority}
                                  </span>
                                ) : <span className="text-xs text-slate-400">{t("er.pending")}</span>}
                              </td>
                              <td className="p-4">
                                {enc.zone ? (
                                  <span className={`text-[10px] uppercase font-black px-2 py-1 rounded-md ${ZONE_COLORS[enc.zone]?.bg} ${ZONE_COLORS[enc.zone]?.text}`}>
                                    {ZONE_COLORS[enc.zone]?.label ? t(ZONE_COLORS[enc.zone].label) : enc.zone}
                                  </span>
                                ) : <span className="text-xs text-slate-400">—</span>}
                              </td>
                              <td className="p-4">
                                <span className={`text-[10px] uppercase font-black px-2 py-1 rounded-md ${getStatusBadge(enc.status)}`}>
                                  {enc.status.replace(/_/g, ' ')}
                                </span>
                              </td>
                              <td className="p-4 text-xs text-slate-500 font-medium">{new Date(enc.arrival_time).toLocaleTimeString()}</td>
                              <td className="p-4 text-right">
                                <div className="flex justify-end gap-1.5 flex-wrap">
                                  {enc.status === "registered" && (
                                    <button onClick={() => setShowTriageModal(enc.id)} className="text-[10px] font-bold bg-amber-50 text-amber-700 px-2.5 py-1 rounded-lg hover:bg-amber-100 whitespace-nowrap">{t("er.triage")}</button>
                                  )}
                                  {enc.status === "triaged" && (
                                    <button onClick={() => updateStatus(enc.id, "in_treatment")} className="text-[10px] font-bold bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-lg hover:bg-emerald-100 whitespace-nowrap">{t("er.startTx")}</button>
                                  )}
                                  {(enc.status === "in_treatment" || enc.status === "observation") && (
                                    <button onClick={() => openCoverSheet(enc)} className="text-[10px] font-bold bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-lg hover:bg-indigo-100 whitespace-nowrap">Cover Sheet</button>
                                  )}
                                  {enc.status === "in_treatment" && (
                                    <button onClick={() => updateStatus(enc.id, "observation")} className="text-[10px] font-bold bg-sky-50 text-sky-700 px-2.5 py-1 rounded-lg hover:bg-sky-100 whitespace-nowrap">{t("er.observe")}</button>
                                  )}
                                  {(enc.status === "in_treatment" || enc.status === "observation") && (
                                    <button onClick={() => updateStatus(enc.id, "due_for_discharge")} className="text-[10px] font-bold bg-purple-50 text-purple-700 px-2.5 py-1 rounded-lg hover:bg-purple-100 whitespace-nowrap">{t("er.planDC")}</button>
                                  )}
                                  {enc.status === "due_for_discharge" && (
                                    <button onClick={() => { fetchDueForDischarge(); setActiveTab("DISCHARGE"); }} className="text-[10px] font-bold bg-rose-50 text-rose-700 px-2.5 py-1 rounded-lg hover:bg-rose-100 whitespace-nowrap">Discharge</button>
                                  )}
                                  {!enc.is_mlc && (
                                    <button onClick={() => setShowMlcModal(enc.id)} className="text-[10px] font-bold bg-purple-50 text-purple-700 px-2.5 py-1 rounded-lg hover:bg-purple-100">{t("er.mlc")}</button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TRIAGE QUEUE */}
            {activeTab === "TRIAGE" && (
              <div className="grid grid-cols-3 gap-4">
                {encounters.filter(e => e.status === "registered").length === 0 ? (
                  <div className="col-span-3 p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400 font-medium">
                    <Stethoscope size={32} className="mx-auto mb-2 opacity-50"/>{t("er.noPatientsAwaitingTriage")}</div>
                ) : (
                  encounters.filter(e => e.status === "registered").map(enc => (
                    <div key={enc.id} className="bg-white p-5 rounded-2xl border border-red-100 shadow-sm hover:shadow-md transition-all">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <div className="font-black text-slate-800">{enc.patient_name}</div>
                          <div className="text-xs text-slate-500 font-mono">{enc.er_number}</div>
                        </div>
                        <span className="bg-red-100 text-red-600 text-[10px] font-black px-2 py-1 rounded-md animate-pulse">{t("er.awaitingTriage")}</span>
                      </div>
                      <div className="text-sm text-slate-600 mb-3">{enc.chief_complaint || 'No complaint recorded'}</div>
                      <div className="flex gap-2 text-xs text-slate-500 mb-4">
                        <span>{enc.age ? `${enc.age}y` : '—'}</span>
                        <span>•</span>
                        <span>{enc.gender || '—'}</span>
                        <span>•</span>
                        <span>{enc.mode_of_arrival || 'Walk-in'}</span>
                      </div>
                      <button onClick={() => setShowTriageModal(enc.id)}
                        className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded-xl font-bold text-sm transition-colors flex items-center justify-center gap-2">
                        <Stethoscope size={14}/>{t("er.startTriageAssessment")}</button>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* BED MAP */}
            {activeTab === "BED_MAP" && (
              <div className="space-y-6">
                {/* Assign prompt */}
                {encounters.filter(e => e.status === "triaged" && !beds.some(b => b.occupied_by_er_encounter_id === e.id)).length > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-amber-800 font-bold text-sm">
                      <AlertTriangle size={16}/> {encounters.filter(e => e.status === "triaged" && !beds.some(b => b.occupied_by_er_encounter_id === e.id)).length} triaged patients awaiting bed assignment
                    </div>
                    <select onChange={e => { if (e.target.value) setShowBedAssignModal(e.target.value); }} className="border rounded-lg px-3 py-1.5 text-sm font-bold bg-white">
                      <option value="">Select patient to assign...</option>
                      {encounters.filter(e => e.status === "triaged").map(e => (
                        <option key={e.id} value={e.id}>{e.patient_name} ({e.er_number})</option>
                      ))}
                    </select>
                  </div>
                )}
                {Object.entries(ZONE_COLORS).map(([zone, zc]) => {
                  const zoneBeds = beds.filter(b => b.zone === zone);
                  if (zoneBeds.length === 0) return null;
                  return (
                    <div key={zone}>
                      <h3 className={`text-sm font-black uppercase tracking-wider mb-3 ${zc.text}`}>
                        <MapPin size={14} className="inline mr-1"/> {t(zc.label)} ({zoneBeds.filter(b => b.status === "available").length}/{zoneBeds.length} available)
                      </h3>
                      <div className="grid grid-cols-6 gap-3">
                        {zoneBeds.map(bed => (
                          <div key={bed.id} onClick={() => {
                            if (bed.status === 'available' && showBedAssignModal) handleBedAssign(bed.id);
                            else if (bed.status === 'available' && encounters.filter(e => e.status === 'triaged').length > 0) {
                              const triaged = encounters.filter(e => e.status === 'triaged');
                              if (triaged.length === 1) { setShowBedAssignModal(triaged[0].id); handleBedAssign(bed.id); }
                            }
                          }} className={`p-3 rounded-xl border-2 transition-all cursor-pointer ${
                            bed.status === 'available' ? `${zc.bg} ${zc.border} hover:shadow-md ${showBedAssignModal ? 'ring-2 ring-emerald-400 animate-pulse' : ''}` :
                            bed.status === 'occupied' ? 'bg-slate-800 border-slate-700' :
                            'bg-amber-50 border-amber-200 border-dashed'
                          }`}>
                            <div className="flex justify-between items-center mb-1">
                              <span className={`font-black text-sm ${bed.status === 'occupied' ? 'text-white' : zc.text}`}>{bed.bed_code}</span>
                              {bed.is_monitored && <Activity size={12} className={bed.status === 'occupied' ? 'text-emerald-400' : 'text-slate-400'}/>}
                              {bed.has_ventilator && <Zap size={12} className={bed.status === 'occupied' ? 'text-amber-400' : 'text-slate-400'}/>}
                            </div>
                            <div className={`text-[10px] font-bold uppercase ${bed.status === 'occupied' ? 'text-slate-300' : 'text-slate-500'}`}>
                              {bed.bed_type} • {bed.status}
                            </div>
                            {bed.patient_gender && (
                              <div className={`text-[10px] mt-1 font-bold ${bed.patient_gender === 'male' ? 'text-blue-300' : 'text-pink-300'}`}>
                                {bed.patient_gender === 'male' ? '♂' : '♀'}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
                {beds.length === 0 && (
                  <div className="p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400">
                    <Bed size={32} className="mx-auto mb-2 opacity-50"/>
                    <p className="font-medium">{t("er.noErBeds")}</p>
                  </div>
                )}
              </div>
            )}

            {/* NURSING COVER SHEET */}
            {activeTab === "COVER_SHEET" && selectedEncounter && (
              <div>
                {/* Patient banner */}
                <div className="bg-gradient-to-r from-slate-800 to-slate-700 text-white p-5 rounded-t-2xl flex items-center justify-between">
                  <div>
                    <div className="text-2xl font-black">{selectedEncounter.patient_name}</div>
                    <div className="text-slate-300 text-sm font-medium mt-1">
                      {selectedEncounter.er_number} • {selectedEncounter.age}y {selectedEncounter.gender} • Zone: {selectedEncounter.zone?.toUpperCase()}
                      {selectedEncounter.is_critical && <span className="ml-2 bg-red-500 text-white text-[10px] px-2 py-0.5 rounded-full font-black animate-pulse">CRITICAL</span>}
                      {selectedEncounter.is_mlc && <span className="ml-2 bg-purple-500 text-white text-[10px] px-2 py-0.5 rounded-full font-black">MLC</span>}
                    </div>
                  </div>
                  <button onClick={() => setActiveTab("PATIENTS")} className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg font-bold text-sm">← Back to Patients</button>
                </div>

                {/* Cover sheet sub-tabs */}
                <div className="bg-white border-b border-slate-200 px-4 flex gap-1 overflow-x-auto">
                  {[
                    { id: "complaints", label: "Complaints", icon: <FileText size={14}/> },
                    { id: "history", label: "History", icon: <ClipboardList size={14}/> },
                    { id: "examination", label: "Examination", icon: <Stethoscope size={14}/> },
                    { id: "diagnosis", label: "Diagnosis", icon: <Brain size={14}/> },
                    { id: "orders", label: "Orders", icon: <TestTube size={14}/> },
                    { id: "notes", label: "Clinical Notes", icon: <PenTool size={14}/> },
                  ].map(st => (
                    <button key={st.id} onClick={() => setCoverSheetTab(st.id)}
                      className={`flex items-center gap-1.5 px-4 py-3 text-sm font-bold border-b-2 transition-all whitespace-nowrap ${
                        coverSheetTab === st.id ? 'border-red-500 text-red-700' : 'border-transparent text-slate-500 hover:text-slate-700'
                      }`}>{st.icon} {st.label}</button>
                  ))}
                </div>

                <div className="bg-white p-6 min-h-[400px] rounded-b-2xl border border-slate-200 border-t-0">
                  {coverSheetTab === "complaints" && (
                    <div className="space-y-4">
                      <form onSubmit={handleSaveNote} className="space-y-4">
                        <input type="hidden" name="note_type" value="complaint" />
                        <h3 className="font-black text-slate-800">Chief Complaint & Presenting Symptoms</h3>
                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
                          <span className="text-[10px] font-black text-amber-600 uppercase">Recorded at Triage</span>
                          <p className="text-sm font-bold text-slate-800 mt-1">{selectedEncounter.chief_complaint || '— No complaint recorded at triage'}</p>
                          {selectedEncounter.presenting_complaints && <p className="text-sm text-slate-600 mt-1">{selectedEncounter.presenting_complaints}</p>}
                        </div>
                        <textarea name="content" rows={4} required placeholder="Enter additional complaints, ICPC coding, symptom onset, severity, duration..." className="w-full p-3 border rounded-xl text-sm outline-none focus:border-red-400 resize-none"/>
                        <button type="submit" disabled={saving} className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg font-bold text-sm disabled:opacity-50">{saving ? 'Saving...' : 'Save Complaint Note → Backend'}</button>
                      </form>

                      {/* Previously saved complaint notes */}
                      {clinicalNotes.filter(n => n.note_type === "complaint").length > 0 && (
                        <div className="space-y-2">
                          <h4 className="text-xs font-black text-slate-500 uppercase">Saved Complaint Records ({clinicalNotes.filter(n => n.note_type === "complaint").length})</h4>
                          {clinicalNotes.filter(n => n.note_type === "complaint").map((n: any) => (
                            <div key={n.id} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                              <div className="flex justify-between text-xs text-slate-400 mb-1">
                                <span className="font-bold">{n.authored_by_name} ({n.authored_by_role})</span>
                                <span>{new Date(n.authored_at).toLocaleString()}</span>
                              </div>
                              <p className="text-sm text-slate-700">{n.content}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {coverSheetTab === "history" && (
                    <form onSubmit={handleSaveNote} className="space-y-4">
                      <input type="hidden" name="note_type" value="history" />
                      <h3 className="font-black text-slate-800">Patient History</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div><label className="text-[10px] font-bold text-slate-500 uppercase">Medical History</label><textarea name="medical_hx" rows={2} className="w-full p-2.5 border rounded-lg text-sm resize-none" placeholder="Diabetes, Hypertension..."/></div>
                        <div><label className="text-[10px] font-bold text-slate-500 uppercase">Surgical History</label><textarea name="surgical_hx" rows={2} className="w-full p-2.5 border rounded-lg text-sm resize-none" placeholder="Appendectomy 2019..."/></div>
                        <div><label className="text-[10px] font-bold text-slate-500 uppercase">Known Allergies</label><input name="allergies" className="w-full p-2.5 border rounded-lg text-sm" placeholder="Penicillin, NSAIDs..."/></div>
                        <div><label className="text-[10px] font-bold text-slate-500 uppercase">Current Medications</label><input name="medications" className="w-full p-2.5 border rounded-lg text-sm" placeholder="Metformin 500mg BD..."/></div>
                      </div>
                      <textarea name="content" rows={3} placeholder="Additional history notes (lifestyle, vaccinations, family history)..." className="w-full p-3 border rounded-xl text-sm outline-none focus:border-red-400 resize-none"/>
                      <button type="submit" disabled={saving} className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg font-bold text-sm disabled:opacity-50">{saving ? 'Saving...' : 'Save History → Backend'}</button>
                    </form>
                  )}

                  {/* Previously saved history notes */}
                  {coverSheetTab === "history" && clinicalNotes.filter(n => n.note_type === "history").length > 0 && (
                    <div className="mt-4 space-y-2">
                      <h4 className="text-xs font-black text-slate-500 uppercase">Saved History Records</h4>
                      {clinicalNotes.filter(n => n.note_type === "history").map((n: any) => (
                        <div key={n.id} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                          <div className="flex justify-between text-xs text-slate-400 mb-1"><span>{n.authored_by_name}</span><span>{new Date(n.authored_at).toLocaleString()}</span></div>
                          <p className="text-sm text-slate-700">{n.content}</p>
                          {n.structured_data && <pre className="text-xs text-slate-500 mt-1 bg-white p-2 rounded">{JSON.stringify(n.structured_data, null, 2)}</pre>}
                        </div>
                      ))}
                    </div>
                  )}

                  {coverSheetTab === "examination" && (
                    <form onSubmit={handleSaveNote} className="space-y-4">
                      <input type="hidden" name="note_type" value="examination" />
                      <h3 className="font-black text-slate-800">Vital Signs & Physical Examination</h3>
                      <div className="grid grid-cols-4 gap-4">
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1"><Thermometer size={16} className="text-rose-500"/><span className="text-[10px] font-bold text-slate-500 uppercase">Temp (°C)</span></div>
                          <input name="temperature" type="number" step="0.1" className="w-full p-2 border rounded-lg text-sm font-bold bg-white" placeholder="36.5"/>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1"><Heart size={16} className="text-red-500"/><span className="text-[10px] font-bold text-slate-500 uppercase">Pulse (bpm)</span></div>
                          <input name="pulse" type="number" className="w-full p-2 border rounded-lg text-sm font-bold bg-white" placeholder="72"/>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1"><Activity size={16} className="text-indigo-500"/><span className="text-[10px] font-bold text-slate-500 uppercase">BP (sys/dia)</span></div>
                          <input name="bp" type="text" className="w-full p-2 border rounded-lg text-sm font-bold bg-white" placeholder="120/80"/>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1"><Zap size={16} className="text-sky-500"/><span className="text-[10px] font-bold text-slate-500 uppercase">SpO₂ (%)</span></div>
                          <input name="spo2" type="number" step="0.1" className="w-full p-2 border rounded-lg text-sm font-bold bg-white" placeholder="98"/>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1"><Activity size={16} className="text-emerald-500"/><span className="text-[10px] font-bold text-slate-500 uppercase">RR (/min)</span></div>
                          <input name="rr" type="number" className="w-full p-2 border rounded-lg text-sm font-bold bg-white" placeholder="16"/>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1"><Brain size={16} className="text-violet-500"/><span className="text-[10px] font-bold text-slate-500 uppercase">GCS (3-15)</span></div>
                          <input name="gcs" type="number" min="3" max="15" className="w-full p-2 border rounded-lg text-sm font-bold bg-white" placeholder="15"/>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1"><AlertCircle size={16} className="text-amber-500"/><span className="text-[10px] font-bold text-slate-500 uppercase">Pain (0-10)</span></div>
                          <input name="pain" type="number" min="0" max="10" className="w-full p-2 border rounded-lg text-sm font-bold bg-white" placeholder="0"/>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1"><TestTube size={16} className="text-rose-400"/><span className="text-[10px] font-bold text-slate-500 uppercase">Glucose</span></div>
                          <input name="glucose" type="number" className="w-full p-2 border rounded-lg text-sm font-bold bg-white" placeholder="100"/>
                        </div>
                      </div>
                      <textarea name="content" rows={3} placeholder="Physical examination findings, systems review..." className="w-full p-3 border rounded-xl text-sm outline-none focus:border-red-400 resize-none"/>
                      <button type="submit" disabled={saving} className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg font-bold text-sm disabled:opacity-50">{saving ? 'Saving...' : 'Save Vitals & Examination → Backend'}</button>
                    </form>
                  )}

                  {/* Previously saved exam notes */}
                  {coverSheetTab === "examination" && clinicalNotes.filter(n => n.note_type === "examination").length > 0 && (
                    <div className="mt-4 space-y-2">
                      <h4 className="text-xs font-black text-slate-500 uppercase">Previous Examination Records</h4>
                      {clinicalNotes.filter(n => n.note_type === "examination").map((n: any) => (
                        <div key={n.id} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                          <div className="flex justify-between text-xs text-slate-400 mb-1"><span>{n.authored_by_name}</span><span>{new Date(n.authored_at).toLocaleString()}</span></div>
                          {n.structured_data && (
                            <div className="grid grid-cols-4 gap-2 text-xs mb-2">
                              {n.structured_data.temperature && <span className="bg-white px-2 py-1 rounded border">Temp: {n.structured_data.temperature}°C</span>}
                              {n.structured_data.pulse && <span className="bg-white px-2 py-1 rounded border">Pulse: {n.structured_data.pulse}</span>}
                              {n.structured_data.bp && <span className="bg-white px-2 py-1 rounded border">BP: {n.structured_data.bp}</span>}
                              {n.structured_data.spo2 && <span className="bg-white px-2 py-1 rounded border">SpO₂: {n.structured_data.spo2}%</span>}
                            </div>
                          )}
                          <p className="text-sm text-slate-700">{n.content}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {coverSheetTab === "diagnosis" && (
                    <div className="space-y-4">
                      <h3 className="font-black text-slate-800">Clinical Diagnosis (ICD-10)</h3>
                      <form onSubmit={handleAddDiagnosis} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                        <div className="grid grid-cols-3 gap-4">
                          <input name="icd_code" placeholder="ICD-10 Code (e.g. S52.5)" className="p-2.5 border rounded-lg text-sm font-mono bg-white"/>
                          <input name="diagnosis_description" required placeholder="Diagnosis Description" className="p-2.5 border rounded-lg text-sm col-span-2 bg-white"/>
                        </div>
                        <div className="flex gap-4 items-center">
                          <select name="diagnosis_type" className="p-2.5 border rounded-lg text-sm bg-white"><option value="working">Working</option><option value="confirmed">Confirmed</option><option value="differential">Differential</option><option value="final">Final</option></select>
                          <label className="flex items-center gap-2 text-sm font-bold text-slate-600"><input type="checkbox" name="is_primary" /> Primary Diagnosis</label>
                          <button type="submit" disabled={saving} className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg font-bold text-sm ml-auto disabled:opacity-50">{saving ? 'Saving...' : 'Add Diagnosis → Backend'}</button>
                        </div>
                      </form>

                      {/* Display saved diagnoses */}
                      {diagnoses.length > 0 && (
                        <div>
                          <h4 className="text-xs font-black text-slate-500 uppercase mb-2">Recorded Diagnoses ({diagnoses.length})</h4>
                          <table className="w-full text-left text-sm border rounded-xl overflow-hidden">
                            <thead><tr className="bg-slate-50 text-xs text-slate-500 uppercase"><th className="p-3">ICD-10</th><th className="p-3">Description</th><th className="p-3">Type</th><th className="p-3">Primary</th><th className="p-3">By</th></tr></thead>
                            <tbody className="divide-y divide-slate-100">
                              {diagnoses.map((d: any) => (
                                <tr key={d.id} className="hover:bg-slate-50">
                                  <td className="p-3 font-mono font-bold text-indigo-600">{d.icd_code || '—'}</td>
                                  <td className="p-3 font-bold text-slate-800">{d.diagnosis_description}</td>
                                  <td className="p-3"><span className="text-[10px] font-black uppercase bg-slate-100 px-2 py-0.5 rounded">{d.diagnosis_type}</span></td>
                                  <td className="p-3">{d.is_primary ? '✓ Yes' : '—'}</td>
                                  <td className="p-3 text-xs text-slate-500">{d.recorded_by_name}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                      {diagnoses.length === 0 && <p className="text-center text-slate-400 text-sm py-4">No diagnoses recorded yet. Add one above.</p>}
                    </div>
                  )}

                  {coverSheetTab === "orders" && (
                    <div className="space-y-4">
                      <h3 className="font-black text-slate-800">Place Clinical Orders</h3>
                      <p className="text-sm text-slate-500">Orders automatically route to LIS, RIS, or Pharmacy modules.</p>
                      <form onSubmit={handlePlaceOrder} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="text-[10px] font-bold text-slate-500 uppercase">Order Type</label>
                            <select name="order_type" className="w-full p-2.5 border rounded-lg text-sm bg-white">
                              <option value="lab">🧪 Laboratory Test</option>
                              <option value="radiology">📡 Radiology Imaging</option>
                              <option value="medication">💊 Medication / Rx</option>
                              <option value="procedure">🔧 Procedure</option>
                              <option value="consult">👨‍⚕️ Consultation</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-[10px] font-bold text-slate-500 uppercase">Priority</label>
                            <select name="priority" className="w-full p-2.5 border rounded-lg text-sm bg-white">
                              <option value="stat">STAT (Immediate)</option>
                              <option value="urgent">Urgent</option>
                              <option value="routine">Routine</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-[10px] font-bold text-slate-500 uppercase">Description</label>
                            <input name="order_description" required className="w-full p-2.5 border rounded-lg text-sm bg-white" placeholder="CBC, X-Ray Chest AP..."/>
                          </div>
                        </div>
                        <button type="submit" disabled={saving} className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-lg font-bold text-sm disabled:opacity-50">{saving ? 'Placing...' : 'Place Order → Route to Module'}</button>
                      </form>

                      {/* Display placed orders */}
                      {orders.length > 0 && (
                        <div>
                          <h4 className="text-xs font-black text-slate-500 uppercase mb-2">Active Orders ({orders.length})</h4>
                          <table className="w-full text-left text-sm border rounded-xl overflow-hidden">
                            <thead><tr className="bg-slate-50 text-xs text-slate-500 uppercase"><th className="p-3">Type</th><th className="p-3">Description</th><th className="p-3">Priority</th><th className="p-3">Status</th><th className="p-3">Ordered By</th><th className="p-3">Time</th></tr></thead>
                            <tbody className="divide-y divide-slate-100">
                              {orders.map((o: any) => (
                                <tr key={o.id} className="hover:bg-slate-50">
                                  <td className="p-3"><span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${o.order_type === 'lab' ? 'bg-blue-100 text-blue-700' : o.order_type === 'radiology' ? 'bg-violet-100 text-violet-700' : o.order_type === 'medication' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'}`}>{o.order_type}</span></td>
                                  <td className="p-3 font-bold text-slate-800">{o.order_description}</td>
                                  <td className="p-3"><span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${o.priority === 'stat' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>{o.priority}</span></td>
                                  <td className="p-3"><span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${o.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>{o.status}</span></td>
                                  <td className="p-3 text-xs text-slate-500">{o.ordered_by_name}</td>
                                  <td className="p-3 text-xs text-slate-500">{new Date(o.ordered_at).toLocaleTimeString()}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                      {orders.length === 0 && <p className="text-center text-slate-400 text-sm py-4">No orders placed yet for this encounter.</p>}
                    </div>
                  )}

                  {coverSheetTab === "notes" && (
                    <div className="space-y-4">
                      <h3 className="font-black text-slate-800">Clinical & Nursing Notes</h3>
                      <form onSubmit={handleSaveNote} className="bg-slate-50 p-4 rounded-xl border space-y-3">
                        <select name="note_type" className="p-2.5 border rounded-lg text-sm bg-white">
                          <option value="observation">Observation Note</option>
                          <option value="shift_note">Shift Handover Note</option>
                          <option value="soap">SOAP Note</option>
                          <option value="procedure_note">Procedure Note</option>
                        </select>
                        <textarea name="content" rows={4} required placeholder="Enter clinical note..." className="w-full p-3 border rounded-xl text-sm resize-none"/>
                        <button type="submit" className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg font-bold text-sm">Save Note</button>
                      </form>
                      <div className="space-y-2">
                        {clinicalNotes.map((n: any) => (
                          <div key={n.id} className="bg-white border border-slate-200 rounded-xl p-4">
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-[10px] font-black uppercase bg-slate-100 text-slate-600 px-2 py-0.5 rounded">{n.note_type}</span>
                              <span className="text-xs text-slate-400">{n.authored_by_name} • {new Date(n.authored_at).toLocaleString()}</span>
                            </div>
                            <p className="text-sm text-slate-700">{n.content}</p>
                          </div>
                        ))}
                        {clinicalNotes.length === 0 && <p className="text-center text-slate-400 text-sm py-4">No clinical notes recorded yet.</p>}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* DISCHARGE WORKFLOW */}
            {activeTab === "DISCHARGE" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-black text-slate-800 flex items-center gap-2"><LogOut size={22} className="text-rose-500"/> ER Discharge Management</h2>
                  <button onClick={fetchDueForDischarge} className="text-sm font-bold text-slate-500 hover:text-slate-700">↻ Refresh</button>
                </div>

                {dueForDischarge.length === 0 ? (
                  <div className="p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400">
                    <LogOut size={32} className="mx-auto mb-2 opacity-50"/>
                    <p className="font-medium">No patients currently due for discharge</p>
                    <p className="text-xs mt-1">Mark patients as "Plan DC" from the Patient List to begin the discharge workflow.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-6">
                    {/* Patient cards */}
                    <div className="space-y-3">
                      <h3 className="text-xs font-black text-slate-500 uppercase">Due for Discharge ({dueForDischarge.length})</h3>
                      {dueForDischarge.map(enc => (
                        <div key={enc.id} onClick={() => setSelectedEncounter(enc)}
                          className={`bg-white p-4 rounded-xl border-2 cursor-pointer transition-all ${
                            selectedEncounter?.id === enc.id ? 'border-rose-500 shadow-md' : 'border-slate-200 hover:border-slate-300'
                          }`}>
                          <div className="font-bold text-slate-800">{enc.patient_name}</div>
                          <div className="text-xs text-slate-500 font-mono">{enc.er_number}</div>
                          <div className="text-xs text-slate-500 mt-1">{enc.chief_complaint}</div>
                        </div>
                      ))}
                    </div>

                    {/* Discharge form */}
                    <div className="col-span-2">
                      {selectedEncounter ? (
                        <form onSubmit={handleDischarge} className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
                          <div className="bg-slate-800 text-white p-4">
                            <div className="font-black text-lg">{selectedEncounter.patient_name}</div>
                            <div className="text-slate-300 text-sm">{selectedEncounter.er_number} • Arrived: {new Date(selectedEncounter.arrival_time).toLocaleString()}</div>
                          </div>
                          <input type="hidden" name="er_encounter_id" value={selectedEncounter.id} />
                          <div className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-[10px] font-bold text-slate-500 uppercase">Discharge Type *</label>
                                <select name="discharge_type" required className="w-full p-2.5 border rounded-lg text-sm">
                                  <option value="normal">Normal Discharge</option>
                                  <option value="dama">DAMA (Against Medical Advice)</option>
                                  <option value="lama">LAMA (Left Against Advice)</option>
                                  <option value="death">Death</option>
                                  <option value="absconded">Absconded</option>
                                </select>
                              </div>
                              <div>
                                <label className="text-[10px] font-bold text-slate-500 uppercase">Disposition</label>
                                <select name="disposition" className="w-full p-2.5 border rounded-lg text-sm">
                                  <option value="home">Discharge to Home</option>
                                  <option value="ipd_admit">Transfer to IPD Admission</option>
                                  <option value="transfer_other">Transfer to Another Facility</option>
                                  <option value="morgue">Morgue</option>
                                </select>
                              </div>
                            </div>
                            <div>
                              <label className="text-[10px] font-bold text-slate-500 uppercase">Discharge Summary</label>
                              <textarea name="discharge_summary" rows={3} className="w-full p-2.5 border rounded-lg text-sm resize-none" placeholder="Clinical summary, treatment provided, outcome..."/>
                            </div>
                            <div>
                              <label className="text-[10px] font-bold text-slate-500 uppercase">Follow-up Instructions</label>
                              <textarea name="follow_up_instructions" rows={2} className="w-full p-2.5 border rounded-lg text-sm resize-none" placeholder="Follow-up in 7 days with orthopedics..."/>
                            </div>

                            {/* Payment */}
                            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                              <h4 className="text-sm font-black text-slate-700 mb-3 flex items-center gap-2"><CreditCard size={16}/> Billing & Payment Settlement</h4>
                              <div className="grid grid-cols-3 gap-4">
                                <div>
                                  <label className="text-[10px] font-bold text-slate-500 uppercase">Total Amount (₹)</label>
                                  <input name="total_amount" type="number" step="0.01" className="w-full p-2.5 border rounded-lg text-sm font-bold" placeholder="0.00"/>
                                </div>
                                <div>
                                  <label className="text-[10px] font-bold text-slate-500 uppercase">Amount Paid (₹)</label>
                                  <input name="paid_amount" type="number" step="0.01" className="w-full p-2.5 border rounded-lg text-sm font-bold" placeholder="0.00"/>
                                </div>
                                <div>
                                  <label className="text-[10px] font-bold text-slate-500 uppercase">Payment Mode</label>
                                  <select name="payment_mode" className="w-full p-2.5 border rounded-lg text-sm">
                                    <option value="cash">Cash</option>
                                    <option value="card">Card</option>
                                    <option value="upi">UPI</option>
                                    <option value="cheque">Cheque</option>
                                    <option value="insurance">Insurance</option>
                                  </select>
                                </div>
                              </div>
                            </div>

                            <button type="submit" className="w-full bg-rose-600 hover:bg-rose-700 text-white py-3 rounded-xl font-bold text-sm transition-colors flex items-center justify-center gap-2">
                              <LogOut size={18}/> Complete Discharge & Auto-Release Bed
                            </button>
                          </div>
                        </form>
                      ) : (
                        <div className="bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl p-12 text-center text-slate-400">
                          <p className="font-medium">Select a patient from the list to process discharge</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* MLC CASES */}
            {activeTab === "MLC" && (
              <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                      <th className="p-4 font-bold">MLC #</th>
                      <th className="p-4 font-bold">{t("er.type")}</th>
                      <th className="p-4 font-bold">{t("er.priority")}</th>
                      <th className="p-4 font-bold">{t("er.policeStation")}</th>
                      <th className="p-4 font-bold">{t("er.fir")}</th>
                      <th className="p-4 font-bold">{t("er.status")}</th>
                      <th className="p-4 font-bold">{t("er.created")}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {mlcCases.length === 0 ? (
                      <tr><td colSpan={7} className="p-8 text-center text-slate-400 font-medium">{t("er.noMlcCases")}</td></tr>
                    ) : (
                      mlcCases.map(m => (
                        <tr key={m.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="p-4 font-mono text-sm font-bold text-slate-700">{m.mlc_number}</td>
                          <td className="p-4 text-sm font-medium text-slate-600">{m.mlc_type || '—'}</td>
                          <td className="p-4"><span className={`text-[10px] font-black uppercase px-2 py-1 rounded-md ${
                            m.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                          }`}>{m.priority}</span></td>
                          <td className="p-4 text-sm text-slate-600">{m.police_station || '—'}</td>
                          <td className="p-4 text-sm font-mono text-slate-600">{m.fir_number || '—'}</td>
                          <td className="p-4"><span className="text-[10px] font-black uppercase px-2 py-1 rounded-md bg-emerald-100 text-emerald-700">{m.status}</span></td>
                          <td className="p-4 text-xs text-slate-500">{new Date(m.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* REGISTRATION MODAL */}
      {showRegModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleRegister} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2"><Siren size={22} className="text-red-500"/>{t("er.erRegistration")}</h3>
              <button type="button" onClick={() => setShowRegModal(false)}><X size={20} className="text-slate-400 hover:text-slate-600"/></button>
            </div>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.registrationType")}</label>
              <select name="registration_type" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-red-400">
                <option value="urgent">{t("er.urgentType")}</option>
                <option value="normal">{t("er.normalType")}</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.patientNameStar")}</label><input name="patient_name" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-red-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.age")}</label><input name="age" type="number" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-red-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.gender")}</label>
                <select name="gender" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-red-400">
                  <option value="">—</option><option value="male">{t("er.male")}</option><option value="female">{t("er.female")}</option><option value="other">{t("er.other")}</option>
                </select>
              </div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.mobile")}</label><input name="mobile" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-red-400"/></div>
            </div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.modeOfArrival")}</label>
              <select name="mode_of_arrival" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-red-400">
                <option value="walk_in">{t("er.walkIn")}</option><option value="ambulance">{t("er.ambulance")}</option><option value="police">{t("er.police")}</option><option value="referral">{t("er.referral")}</option>
              </select>
            </div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.chiefComplaintStar")}</label><textarea name="chief_complaint" required rows={2} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-red-400 resize-none"/></div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowRegModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">{t("er.cancel")}</button>
              <button type="submit" className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">{t("er.registerPatient")}</button>
            </div>
          </form>
        </div>
      )}

      {/* TRIAGE MODAL */}
      {showTriageModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleTriage} className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2"><Stethoscope size={22} className="text-amber-500"/>{t("er.esiTriageAssessment")}</h3>
              <button type="button" onClick={() => setShowTriageModal(null)}><X size={20} className="text-slate-400"/></button>
            </div>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.triageCategoryStar")}</label>
              <select name="triage_category" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-amber-400">
                <option value="resuscitation">{t("er.esi1")}</option>
                <option value="emergent">{t("er.esi2")}</option>
                <option value="urgent">{t("er.esi3")}</option>
                <option value="less_urgent">{t("er.esi4")}</option>
                <option value="non_urgent">{t("er.esi5")}</option>
              </select>
            </div>
            <h4 className="text-xs font-black text-slate-600 uppercase pt-2">{t("er.vitalSigns")}</h4>
            <div className="grid grid-cols-4 gap-3">
              <div><label className="text-[10px] font-bold text-slate-400">Temp (°C)</label><input name="temperature" type="number" step="0.1" className="w-full p-2 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-400">{t("er.pulse")}</label><input name="pulse" type="number" className="w-full p-2 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-400">{t("er.bpSys")}</label><input name="bp_systolic" type="number" className="w-full p-2 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-400">{t("er.bpDia")}</label><input name="bp_diastolic" type="number" className="w-full p-2 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-400">{t("er.rr")}</label><input name="respiratory_rate" type="number" className="w-full p-2 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-400">SpO2 %</label><input name="spo2" type="number" step="0.1" className="w-full p-2 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-400">{t("er.gcs")}</label><input name="gcs_score" type="number" min="3" max="15" className="w-full p-2 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-400">{t("er.pain010")}</label><input name="pain_score" type="number" min="0" max="10" className="w-full p-2 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
            </div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.triageNotes")}</label><textarea name="triage_notes" rows={2} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-amber-400 resize-none"/></div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowTriageModal(null)} className="px-4 py-2 text-slate-600 text-sm font-bold">{t("er.cancel")}</button>
              <button type="submit" className="bg-amber-600 hover:bg-amber-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">{t("er.saveTriage")}</button>
            </div>
          </form>
        </div>
      )}

      {/* MLC MODAL */}
      {showMlcModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateMlc} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2"><Shield size={22} className="text-purple-600"/>{t("er.createMlcCase")}</h3>
              <button type="button" onClick={() => setShowMlcModal(null)}><X size={20} className="text-slate-400"/></button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.mlcType")}</label>
                <select name="mlc_type" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400">
                  <option value="rta">{t("er.roadTrafficAccident")}</option><option value="assault">{t("er.assault")}</option><option value="poisoning">{t("er.poisoning")}</option>
                  <option value="burns">{t("er.burns")}</option><option value="sexual_assault">{t("er.sexualAssault")}</option><option value="other">{t("er.other")}</option>
                </select>
              </div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.priority")}</label>
                <select name="priority" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400">
                  <option value="high">{t("er.high")}</option><option value="medium">{t("er.medium")}</option><option value="low">{t("er.low")}</option>
                </select>
              </div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.policeStation")}</label><input name="police_station" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.firNumber")}</label><input name="fir_number" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400"/></div>
            </div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">{t("er.injuryDescription")}</label><textarea name="injury_description" rows={2} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400 resize-none"/></div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowMlcModal(null)} className="px-4 py-2 text-slate-600 text-sm font-bold">{t("er.cancel")}</button>
              <button type="submit" className="bg-purple-600 hover:bg-purple-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">{t("er.createMlc")}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
