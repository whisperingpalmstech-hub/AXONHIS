"use client";
import { useTranslation } from "@/i18n";

import React, { useEffect, useState, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Siren, Users, AlertTriangle, Bed, Heart, Shield, Clock, Plus, Search,
  Activity, Thermometer, MapPin, ChevronDown, X, FileText, Stethoscope,
  Zap, Eye, Brain, Baby, CheckCircle2, AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";
import { WorkflowPipeline } from "@/components/ui/WorkflowPipeline";

type Tab = "COMMAND_CENTER" | "PATIENTS" | "TRIAGE" | "BED_MAP" | "MLC";

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
  const [searchTerm, setSearchTerm] = useState("");

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
            { id: "MLC", label: t("er.mlcCasesTab"), icon: <Shield size={16}/> },
          ].map(tObj => (
            <button key={tObj.id} onClick={() => setActiveTab(tObj.id as Tab)}
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
                                <div className="flex justify-end gap-1.5">
                                  {enc.status === "registered" && (
                                    <button onClick={() => setShowTriageModal(enc.id)} className="text-[10px] font-bold bg-amber-50 text-amber-700 px-2.5 py-1 rounded-lg hover:bg-amber-100 whitespace-nowrap">{t("er.triage")}</button>
                                  )}
                                  {enc.status === "triaged" && (
                                    <button onClick={() => updateStatus(enc.id, "in_treatment")} className="text-[10px] font-bold bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-lg hover:bg-emerald-100 whitespace-nowrap">{t("er.startTx")}</button>
                                  )}
                                  {enc.status === "in_treatment" && (
                                    <button onClick={() => updateStatus(enc.id, "observation")} className="text-[10px] font-bold bg-sky-50 text-sky-700 px-2.5 py-1 rounded-lg hover:bg-sky-100 whitespace-nowrap">{t("er.observe")}</button>
                                  )}
                                  {(enc.status === "in_treatment" || enc.status === "observation") && (
                                    <button onClick={() => updateStatus(enc.id, "due_for_discharge")} className="text-[10px] font-bold bg-purple-50 text-purple-700 px-2.5 py-1 rounded-lg hover:bg-purple-100 whitespace-nowrap">{t("er.planDC")}</button>
                                  )}
                                  {enc.status === "due_for_discharge" && (
                                    <button onClick={() => updateStatus(enc.id, "discharged")} className="text-[10px] font-bold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg hover:bg-slate-200 whitespace-nowrap">{t("er.discharge")}</button>
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
                          <div key={bed.id} className={`p-3 rounded-xl border-2 transition-all ${
                            bed.status === 'available' ? `${zc.bg} ${zc.border} hover:shadow-md` :
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
