"use client";

import React, { useState, useEffect } from "react";
import { doctorDeskApi } from "@/lib/doctor-desk-api";
import { api } from "@/lib/api";
import {
  Stethoscope, Users, Activity, PenTool, Mic, BrainCircuit, Syringe, Pill,
  Target, Plus, CheckCircle, AlertTriangle, Heart, Thermometer, FileText,
  History, Search, ClipboardList, Eye, X, ChevronDown, ChevronRight, RefreshCw,
  HeartPulse, MessageSquareText, ScrollText, ScanEye, Sparkles, Shield, Zap,
  Clock, BadgeCheck, Send, Workflow, CircleDot
} from "lucide-react";
import { useTranslation } from "@/i18n";
import { TopNav } from "@/components/ui/TopNav";

type Tab = "notes" | "vitals" | "complaints" | "history" | "examination" | "diagnosis" | "orders" | "prescriptions" | "ai_engine";

export default function DoctorDeskPage() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const DOCTOR_ID = "00000000-0000-0000-0000-000000000009";

  const [patients, setPatients] = useState<any[]>([]);
  const [worklist, setWorklist] = useState<any[]>([]);
  const [activePatient, setActivePatient] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("vitals");
  const [simPatientId, setSimPatientId] = useState("");

  // SOAP Note State
  const [noteData, setNoteData] = useState({ chief_complaint: "", history_present_illness: "", physical_examination: "", diagnosis: "", plan: "" });
  const [scribeListening, setScribeListening] = useState(false);

  // AI Suggestions
  const [aiSuggestions, setAiSuggestions] = useState<any>(null);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);

  // Vitals
  const [vitalsHistory, setVitalsHistory] = useState<any[]>([]);
  const [vitalsForm, setVitalsForm] = useState({ temperature: "", pulse_rate: "", respiratory_rate: "", bp_systolic: "", bp_diastolic: "", spo2: "", height_cm: "", weight_kg: "" });

  // Complaints
  const [complaints, setComplaints] = useState<any[]>([]);
  const [complaintForm, setComplaintForm] = useState({ icpc_code: "", complaint_description: "", duration: "", severity: "moderate" });

  // Medical History
  const [medHistory, setMedHistory] = useState<any[]>([]);
  const [historyForm, setHistoryForm] = useState({ category: "medical", description: "", diagnosed_date: "" });

  // Examinations
  const [examinations, setExaminations] = useState<any[]>([]);
  const [examForm, setExamForm] = useState({ general_examination: "", systemic_examination: { cvs: "", resp: "", gi: "", neuro: "", msk: "" }, local_examination: "" });

  // Diagnoses
  const [diagnoses, setDiagnoses] = useState<any[]>([]);
  const [diagForm, setDiagForm] = useState({ icd_code: "", diagnosis_description: "", diagnosis_type: "provisional", is_primary: false });

  // Prescriptions & Orders
  const [rxs, setRxs] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [voiceRxStr, setVoiceRxStr] = useState("");
  const [manualDiagnostic, setManualDiagnostic] = useState("");
  const [manualDiagnosticType, setManualDiagnosticType] = useState("lab");

  // IPD Modal
  const [showIpdModal, setShowIpdModal] = useState(false);
  const [ipdNotes, setIpdNotes] = useState({ current_health: "", doses_to_give: "", plan_of_action: "" });

  // AI Engine State
  const [aiEngineModule, setAiEngineModule] = useState<"navigate" | "scribe" | "guard" | "pipeline">("navigate");
  const [aiDoctorInput, setAiDoctorInput] = useState("");
  const [aiResult, setAiResult] = useState<any>(null);
  const [aiLoading, setAiLoading] = useState(false);

  // Timeline
  const [timelineMode, setTimelineMode] = useState(false);
  const [timelineNodes, setTimelineNodes] = useState<any[]>([]);

  useEffect(() => { loadBaseData(); }, []);

  const loadBaseData = async () => {
    setLoading(true);
    try {
      const p = await api.get<any>("/patients/");
      setPatients(Array.isArray(p) ? p : p?.items || []);
      const wl = await doctorDeskApi.getWorklist(DOCTOR_ID);
      setWorklist(wl);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const getPatientName = (id: string) => { const pt = patients.find(p => p.id === id); return pt ? `${pt.first_name} ${pt.last_name}` : "Unknown"; };
  const getPatientUhid = (id: string) => { const pt = patients.find(p => p.id === id); return pt ? (pt.uhid || "---") : "---"; };

  const seedDoctorQueue = async () => {
    if (patients.length === 0) return alert("Add patients first");
    const targetId = simPatientId || patients[patients.length - 1].id;
    await doctorDeskApi.seedPatient({ doctor_id: DOCTOR_ID, visit_id: "00000000-0000-0000-0000-000000000000", patient_id: targetId, priority_indicator: "normal" });
    loadBaseData();
  };

  const callPatient = async (wl: any) => {
    await doctorDeskApi.updateStatus(wl.id, "in_consultation");
    const pt = patients.find(p => p.id === wl.patient_id);
    setActivePatient({ ...wl, detail: pt });
    setActiveTab("vitals");
    // Load all clinical data
    try {
      const [tl, v, c, h, e, d] = await Promise.all([
        doctorDeskApi.getTimeline(wl.patient_id),
        doctorDeskApi.getVitals(wl.visit_id).catch(() => []),
        doctorDeskApi.getComplaints(wl.visit_id).catch(() => []),
        doctorDeskApi.getMedicalHistory(wl.patient_id).catch(() => []),
        doctorDeskApi.getExaminations(wl.visit_id).catch(() => []),
        doctorDeskApi.getDiagnoses(wl.visit_id).catch(() => []),
      ]);
      setTimelineNodes(tl.chronological_nodes || []);
      setVitalsHistory(v || []);
      setComplaints(c || []);
      setMedHistory(h || []);
      setExaminations(e || []);
      setDiagnoses(d || []);
    } catch (err) { console.error(err); }
    loadBaseData();
  };

  // ── Vitals ──
  const saveVitals = async () => {
    if (!activePatient) return;
    const res = await doctorDeskApi.addVitals({
      visit_id: activePatient.visit_id, patient_id: activePatient.patient_id,
      ...vitalsForm, bp_systolic: vitalsForm.bp_systolic ? parseInt(vitalsForm.bp_systolic) : null,
      bp_diastolic: vitalsForm.bp_diastolic ? parseInt(vitalsForm.bp_diastolic) : null
    });
    setVitalsHistory([...vitalsHistory, res]);
    setVitalsForm({ temperature: "", pulse_rate: "", respiratory_rate: "", bp_systolic: "", bp_diastolic: "", spo2: "", height_cm: "", weight_kg: "" });
  };

  // ── Complaints ──
  const saveComplaint = async () => {
    if (!activePatient || !complaintForm.complaint_description) return;
    const res = await doctorDeskApi.addComplaint({
      visit_id: activePatient.visit_id, patient_id: activePatient.patient_id,
      encounter_type: "opd", ...complaintForm
    });
    setComplaints([...complaints, res]);
    setComplaintForm({ icpc_code: "", complaint_description: "", duration: "", severity: "moderate" });
  };

  // ── Medical History ──
  const saveMedHistory = async () => {
    if (!activePatient || !historyForm.description) return;
    const res = await doctorDeskApi.addMedicalHistory({ patient_id: activePatient.patient_id, ...historyForm });
    setMedHistory([...medHistory, res]);
    setHistoryForm({ category: "medical", description: "", diagnosed_date: "" });
  };

  // ── Examination ──
  const saveExamination = async () => {
    if (!activePatient) return;
    const res = await doctorDeskApi.addExamination({ visit_id: activePatient.visit_id, patient_id: activePatient.patient_id, ...examForm });
    setExaminations([...examinations, res]);
    setExamForm({ general_examination: "", systemic_examination: { cvs: "", resp: "", gi: "", neuro: "", msk: "" }, local_examination: "" });
  };

  // ── Diagnosis ──
  const saveDiagnosis = async () => {
    if (!activePatient || !diagForm.diagnosis_description) return;
    const res = await doctorDeskApi.addDiagnosis({ visit_id: activePatient.visit_id, patient_id: activePatient.patient_id, ...diagForm });
    setDiagnoses([...diagnoses, res]);
    setDiagForm({ icd_code: "", diagnosis_description: "", diagnosis_type: "provisional", is_primary: false });
  };

  // ── Orders ──
  const commitOrder = async (testName: string, type: string) => {
    const res = await doctorDeskApi.placeOrder({ visit_id: activePatient.visit_id, doctor_id: DOCTOR_ID, order_type: type, test_name: testName });
    setOrders([...orders, res]);
  };

  // ── Prescriptions ──
  const commitVoicePrescription = async () => {
    if (!voiceRxStr) return;
    const res = await doctorDeskApi.parseVoicePrescription({ visit_id: activePatient.visit_id, doctor_id: DOCTOR_ID, text: voiceRxStr });
    setRxs([...rxs, res]);
    setVoiceRxStr("");
  };

  // ── AI ──
  const runAI = async () => {
    if (!noteData.chief_complaint && complaints.length === 0) return alert("Enter complaints first");
    setAiAnalyzing(true);
    const symptoms = noteData.chief_complaint || complaints.map(c => c.complaint_description).join(", ");
    const rec = await doctorDeskApi.getAISuggestions(symptoms);
    setAiSuggestions(rec);
    setAiAnalyzing(false);
  };

  const simulateScribe = async () => {
    setScribeListening(true);
    setTimeout(async () => {
      setScribeListening(false);
      const res = await doctorDeskApi.transcribeVoice({ doctor_id: DOCTOR_ID, audio_data_base64: "dummy" });
      setNoteData({ ...noteData, chief_complaint: res.structured_note.chief_complaint, history_present_illness: res.structured_note.history_present_illness, plan: res.structured_note.plan });
    }, 2000);
  };

  // ── AI Engine (integrated) ──
  const runDeskAI = async () => {
    if (!activePatient) return;
    setAiLoading(true);
    setAiResult(null);
    const pt = activePatient.detail || {};
    const age = pt.date_of_birth ? String(new Date().getFullYear() - new Date(pt.date_of_birth).getFullYear()) : "";
    try {
      const resp = await fetch("http://localhost:9500/api/v1/clinical-workflow/desk/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
        body: JSON.stringify({
          patient_id: activePatient.patient_id,
          visit_id: activePatient.visit_id,
          doctor_input: aiDoctorInput || complaints.map(c => c.complaint_description).join(", ") || noteData.chief_complaint || "General check-up",
          module: aiEngineModule,
          vitals_override: vitalsHistory.length > 0 ? [{
            name: "BP", value: `${vitalsHistory[vitalsHistory.length-1]?.bp_systolic || "-"}/${vitalsHistory[vitalsHistory.length-1]?.bp_diastolic || "-"}`
          }, {
            name: "HR", value: vitalsHistory[vitalsHistory.length-1]?.pulse_rate || ""
          }, {
            name: "SpO2", value: vitalsHistory[vitalsHistory.length-1]?.spo2 || ""
          }, {
            name: "Temp", value: vitalsHistory[vitalsHistory.length-1]?.temperature || ""
          }, {
            name: "RR", value: vitalsHistory[vitalsHistory.length-1]?.respiratory_rate || ""
          }].filter(v => v.value) : [],
          complaints_override: complaints.map(c => c.complaint_description),
          history_override: medHistory.map(h => h.description),
          allergies_override: medHistory.filter(h => h.category === "allergy").map(h => h.description),
          medications_override: medHistory.filter(h => h.category === "medication").map(h => h.description),
        }),
      });
      setAiResult(await resp.json());
    } catch (e: any) { setAiResult({ error: e.message }); }
    setAiLoading(false);
  };

  const concludeConsultation = async () => {
    await doctorDeskApi.saveNote({ ...noteData, doctor_id: DOCTOR_ID, visit_id: activePatient.visit_id });
    await doctorDeskApi.updateStatus(activePatient.id, "completed");
    await doctorDeskApi.generateSummary(activePatient.visit_id, DOCTOR_ID);
    alert("Consultation complete. Clinical Summary Generated & Sent to Billing.");
    setActivePatient(null);
    setNoteData({ chief_complaint: "", history_present_illness: "", physical_examination: "", diagnosis: "", plan: "" });
    setRxs([]); setOrders([]); setAiSuggestions(null); setComplaints([]); setDiagnoses([]); setExaminations([]); setVitalsHistory([]);
    loadBaseData();
  };

  const recommendAdmission = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!activePatient) return;
    try {
      const resp = await fetch(`http://localhost:9500/api/v1/ipd/requests`, {
        method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
        body: JSON.stringify({ patient_name: `${activePatient.detail?.first_name} ${activePatient.detail?.last_name}`, patient_uhid: activePatient.detail?.uhid || activePatient.patient_id, gender: activePatient.detail?.gender || "Unknown", date_of_birth: activePatient.detail?.date_of_birth || "2000-01-01", mobile_number: activePatient.detail?.primary_phone || "9999999999", admitting_doctor: "Dr. AI Desk", treating_doctor: "Dr. AI Desk", specialty: "General Medicine", reason_for_admission: noteData.chief_complaint || "Clinical observation recommended", admission_category: "Emergency", admission_source: "OPD", preferred_bed_category: "General Ward", expected_admission_date: new Date().toISOString(), clinical_notes: `Current Health: ${ipdNotes.current_health}\nMedications: ${ipdNotes.doses_to_give}\nPlan: ${ipdNotes.plan_of_action}` })
      });
      if (resp.ok) { alert("Admission request sent to IPD!"); setShowIpdModal(false); }
      else alert("Error sending admission request.");
    } catch { alert("Network Error."); }
  };

  const TABS: { key: Tab; label: string; icon: any; color: string }[] = [
    { key: "vitals", label: "Vitals", icon: HeartPulse, color: "text-rose-600" },
    { key: "complaints", label: "Complaints", icon: MessageSquareText, color: "text-amber-600" },
    { key: "history", label: "History", icon: ScrollText, color: "text-purple-600" },
    { key: "examination", label: "Examination", icon: ScanEye, color: "text-teal-600" },
    { key: "diagnosis", label: "Diagnosis", icon: CircleDot, color: "text-red-600" },
    { key: "notes", label: "SOAP", icon: PenTool, color: "text-indigo-600" },
    { key: "prescriptions", label: "Rx", icon: Pill, color: "text-emerald-600" },
    { key: "orders", label: "CPOE", icon: Syringe, color: "text-sky-600" },
    { key: "ai_engine", label: "AI Engine", icon: Sparkles, color: "text-fuchsia-600" },
  ];

  return (
    <div className="p-3 md:p-4 max-w-[1900px] mx-auto h-screen overflow-hidden flex flex-col">
      <TopNav title="nav.doctorDesk" />
      <div className="flex justify-between items-center shrink-0 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-200"><Stethoscope className="text-white" size={20} /></div>
          <div>
            <h1 className="text-xl font-black text-slate-800 tracking-tight">Doctor Desk</h1>
            <p className="text-slate-400 text-[11px]">EMR • CPOE • Clinical AI</p>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex gap-4">
        {/* LEFT: WORKLIST */}
        <div className="w-64 bg-white border border-slate-200/80 rounded-2xl flex flex-col overflow-hidden shadow-sm shrink-0">
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-indigo-950 text-white p-3">
            <h3 className="font-bold flex items-center gap-2 text-xs uppercase tracking-wider mb-2"><Users size={14} className="text-indigo-400"/> Worklist</h3>
            <div className="flex items-center gap-1.5">
              <select className="border border-slate-600/50 bg-slate-700/50 backdrop-blur rounded-lg text-[11px] px-2 py-1.5 flex-1 outline-none focus:ring-1 focus:ring-indigo-500" value={simPatientId} onChange={e => setSimPatientId(e.target.value)}>
                <option value="">Latest Patient</option>
                {patients.slice().reverse().map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}
              </select>
              <button onClick={seedDoctorQueue} className="bg-indigo-500 hover:bg-indigo-400 text-white p-1.5 rounded-lg transition-colors shadow-sm"><Plus size={14}/></button>
            </div>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-1.5">
            {worklist.filter(w=>w.status==='waiting').length === 0 && <div className="text-center p-6 text-slate-400 text-xs">Queue empty</div>}
            {worklist.filter(w=>w.status==='waiting').map(wl => (
              <div key={wl.id} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg hover:border-indigo-300 cursor-pointer group" onClick={()=>callPatient(wl)}>
                <p className="font-bold text-slate-800 text-sm">{getPatientName(wl.patient_id)}</p>
                <p className="text-[10px] text-slate-500">{getPatientUhid(wl.patient_id)} • Token {wl.queue_position || '--'}</p>
              </div>
            ))}
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-1 pt-3 pb-1 border-t mt-3">In Consultation</h4>
            {worklist.filter(w=>w.status==='in_consultation').map(wl => (
              <div key={wl.id} className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg cursor-pointer" onClick={()=>callPatient(wl)}>
                <div className="flex justify-between items-center">
                  <p className="font-bold text-emerald-900 text-sm">{getPatientName(wl.patient_id)}</p>
                  <Activity size={12} className="text-emerald-500 animate-pulse"/>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: EMR CONSULTATION */}
        <div className="flex-1 bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-sm flex flex-col">
          {!activePatient ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300 space-y-4">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-100 to-indigo-50 flex items-center justify-center"><Stethoscope size={36} className="text-indigo-300" /></div>
              <h2 className="text-base font-bold text-slate-400">Select a patient</h2>
              <p className="text-xs text-slate-300">Pick from worklist to begin consultation</p>
            </div>
          ) : (
            <>
              {/* PATIENT HEADER */}
              <div className="bg-gradient-to-r from-white via-indigo-50/40 to-violet-50/30 border-b border-slate-100 px-5 py-3 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-200">
                    {activePatient.detail?.first_name?.[0]}{activePatient.detail?.last_name?.[0]}
                  </div>
                  <div>
                    <h2 className="text-base font-black text-slate-800 tracking-tight">{activePatient.detail?.first_name} {activePatient.detail?.last_name}</h2>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-medium">UHID: {activePatient.detail?.uhid}</span>
                      <span className="text-[10px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded font-medium">Age: {activePatient.detail?.date_of_birth ? new Date().getFullYear() - new Date(activePatient.detail.date_of_birth).getFullYear() : '--'}</span>
                      <span className="text-[10px] bg-rose-50 text-rose-600 px-1.5 py-0.5 rounded font-medium">Blood: {activePatient.detail?.blood_group || '--'}</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={()=>setTimelineMode(!timelineMode)} className={`text-[11px] px-3 py-1.5 rounded-lg border font-semibold flex items-center gap-1.5 transition-all ${timelineMode ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'border-slate-200 text-slate-500 hover:bg-slate-50'}`}><Activity size={13}/>Timeline</button>
                  <button onClick={()=>setShowIpdModal(true)} className="text-[11px] px-3 py-1.5 rounded-lg border border-rose-200 bg-rose-50 text-rose-600 font-semibold flex items-center gap-1.5 hover:bg-rose-100 transition-colors"><AlertTriangle size={13}/>Admit IPD</button>
                  <button onClick={concludeConsultation} className="text-[11px] px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold flex items-center gap-1.5 hover:opacity-90 transition-all shadow-sm shadow-emerald-200"><BadgeCheck size={13}/>Complete & Generate Summary</button>
                </div>
              </div>

              {/* TAB BAR */}
              <div className="flex border-b border-slate-100 bg-white px-3 shrink-0 overflow-x-auto gap-0.5 pt-1">
                {TABS.map(tab => (
                  <button key={tab.key} onClick={()=>setActiveTab(tab.key)}
                    className={`flex items-center gap-1.5 px-3 py-2 text-[11px] font-semibold rounded-t-lg transition-all whitespace-nowrap border-b-2 ${activeTab === tab.key ? `border-indigo-600 ${tab.color} bg-indigo-50/50` : 'border-transparent text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}>
                    <tab.icon size={13}/> {tab.label}
                    {tab.key === "complaints" && complaints.length > 0 && <span className="bg-amber-100 text-amber-700 text-[9px] w-4 h-4 rounded-full flex items-center justify-center font-bold">{complaints.length}</span>}
                    {tab.key === "diagnosis" && diagnoses.length > 0 && <span className="bg-red-100 text-red-700 text-[9px] w-4 h-4 rounded-full flex items-center justify-center font-bold">{diagnoses.length}</span>}
                    {tab.key === "prescriptions" && rxs.length > 0 && <span className="bg-emerald-100 text-emerald-700 text-[9px] w-4 h-4 rounded-full flex items-center justify-center font-bold">{rxs.length}</span>}
                    {tab.key === "orders" && orders.length > 0 && <span className="bg-sky-100 text-sky-700 text-[9px] w-4 h-4 rounded-full flex items-center justify-center font-bold">{orders.length}</span>}
                    {tab.key === "ai_engine" && <span className="relative flex h-2 w-2"><span className="animate-ping absolute h-full w-full rounded-full bg-fuchsia-400 opacity-75"></span><span className="relative rounded-full h-2 w-2 bg-fuchsia-500"></span></span>}
                  </button>
                ))}
              </div>

              {/* TAB CONTENT */}
              <div className={`flex-1 overflow-hidden flex ${timelineMode ? '' : ''}`}>
                <div className={`${timelineMode ? 'w-2/3 border-r' : 'w-full'} overflow-y-auto p-5 space-y-4`}>

                  {/* VITALS TAB */}
                  {activeTab === "vitals" && (
                    <div className="space-y-4">
                      <div className="border rounded-xl overflow-hidden">
                        <div className="bg-rose-50 border-b p-3 flex justify-between items-center">
                          <h3 className="font-bold text-rose-900 flex items-center gap-2 text-sm"><Thermometer size={16}/> Record Vitals</h3>
                        </div>
                        <div className="p-4 grid grid-cols-4 gap-3">
                          {[
                            { k: "temperature", label: "Temp (°C)", ph: "37.0" },
                            { k: "pulse_rate", label: "Pulse (bpm)", ph: "72" },
                            { k: "respiratory_rate", label: "RR (/min)", ph: "18" },
                            { k: "spo2", label: "SpO₂ (%)", ph: "98" },
                            { k: "bp_systolic", label: "BP Systolic", ph: "120" },
                            { k: "bp_diastolic", label: "BP Diastolic", ph: "80" },
                            { k: "height_cm", label: "Height (cm)", ph: "170" },
                            { k: "weight_kg", label: "Weight (kg)", ph: "70" },
                          ].map(f => (
                            <div key={f.k}>
                              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">{f.label}</label>
                              <input className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm focus:border-rose-400 focus:outline-none" placeholder={f.ph}
                                value={(vitalsForm as any)[f.k]} onChange={e => setVitalsForm({...vitalsForm, [f.k]: e.target.value})} />
                            </div>
                          ))}
                        </div>
                        <div className="px-4 pb-4"><button onClick={saveVitals} className="bg-rose-600 text-white px-5 py-2 rounded-lg text-sm font-bold hover:bg-rose-700 shadow-sm">Save Vitals (Auto-BMI)</button></div>
                      </div>
                      {vitalsHistory.length > 0 && (
                        <div className="border rounded-xl overflow-hidden">
                          <div className="bg-slate-50 border-b p-3"><h3 className="font-bold text-slate-800 text-sm">Vitals History</h3></div>
                          <table className="w-full text-xs">
                            <thead><tr className="bg-slate-50 text-slate-500">{["Time","Temp","PR","RR","BP","SpO₂","Ht","Wt","BMI"].map(h=><th key={h} className="p-2 text-left font-bold">{h}</th>)}</tr></thead>
                            <tbody>{vitalsHistory.map((v,i)=>(
                              <tr key={i} className="border-t"><td className="p-2">{new Date(v.created_at).toLocaleTimeString()}</td><td className="p-2">{v.temperature||'-'}</td><td className="p-2">{v.pulse_rate||'-'}</td><td className="p-2">{v.respiratory_rate||'-'}</td><td className="p-2">{v.bp_systolic||'-'}/{v.bp_diastolic||'-'}</td><td className="p-2">{v.spo2||'-'}</td><td className="p-2">{v.height_cm||'-'}</td><td className="p-2">{v.weight_kg||'-'}</td><td className="p-2 font-bold text-rose-600">{v.bmi||'-'}</td></tr>
                            ))}</tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}

                  {/* COMPLAINTS TAB */}
                  {activeTab === "complaints" && (
                    <div className="space-y-4">
                      <div className="border rounded-xl overflow-hidden">
                        <div className="bg-amber-50 border-b p-3"><h3 className="font-bold text-amber-900 text-sm flex items-center gap-2"><ClipboardList size={16}/> Clinical Complaints (ICPC)</h3></div>
                        <div className="p-4 grid grid-cols-2 gap-3">
                          <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">ICPC Code</label><input className="w-full border rounded-lg px-2.5 py-1.5 text-sm" placeholder="A01" value={complaintForm.icpc_code} onChange={e=>setComplaintForm({...complaintForm, icpc_code: e.target.value})}/></div>
                          <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Duration</label><input className="w-full border rounded-lg px-2.5 py-1.5 text-sm" placeholder="3 days" value={complaintForm.duration} onChange={e=>setComplaintForm({...complaintForm, duration: e.target.value})}/></div>
                          <div className="col-span-2"><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Complaint Description</label><textarea className="w-full border rounded-lg px-2.5 py-1.5 text-sm" rows={2} placeholder="Describe chief complaint..." value={complaintForm.complaint_description} onChange={e=>setComplaintForm({...complaintForm, complaint_description: e.target.value})}/></div>
                          <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Severity</label>
                            <select className="w-full border rounded-lg px-2.5 py-1.5 text-sm" value={complaintForm.severity} onChange={e=>setComplaintForm({...complaintForm, severity: e.target.value})}>
                              <option value="mild">Mild</option><option value="moderate">Moderate</option><option value="severe">Severe</option>
                            </select>
                          </div>
                        </div>
                        <div className="px-4 pb-4"><button onClick={saveComplaint} className="bg-amber-600 text-white px-5 py-2 rounded-lg text-sm font-bold hover:bg-amber-700">Add Complaint</button></div>
                      </div>
                      {complaints.length > 0 && <div className="space-y-2">{complaints.map((c,i)=>(
                        <div key={i} className="border-l-4 border-amber-400 bg-amber-50 p-3 rounded-r-lg">
                          <div className="flex justify-between"><span className="font-bold text-sm">{c.complaint_description}</span>{c.icpc_code && <span className="bg-amber-200 text-amber-800 text-[10px] px-2 py-0.5 rounded-full font-bold">{c.icpc_code}</span>}</div>
                          <p className="text-xs text-slate-500 mt-1">Duration: {c.duration || '-'} • Severity: {c.severity || '-'}</p>
                        </div>
                      ))}</div>}
                    </div>
                  )}

                  {/* HISTORY TAB */}
                  {activeTab === "history" && (
                    <div className="space-y-4">
                      <div className="border rounded-xl overflow-hidden">
                        <div className="bg-purple-50 border-b p-3"><h3 className="font-bold text-purple-900 text-sm flex items-center gap-2"><History size={16}/> Patient Medical History (Persistent)</h3></div>
                        <div className="p-4 grid grid-cols-3 gap-3">
                          <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Category</label>
                            <select className="w-full border rounded-lg px-2.5 py-1.5 text-sm" value={historyForm.category} onChange={e=>setHistoryForm({...historyForm, category: e.target.value})}>
                              {["medical","surgical","allergy","medication","family","lifestyle","immunization"].map(c=><option key={c} value={c}>{c.charAt(0).toUpperCase()+c.slice(1)}</option>)}
                            </select>
                          </div>
                          <div className="col-span-2"><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Description</label><input className="w-full border rounded-lg px-2.5 py-1.5 text-sm" placeholder="e.g. Diabetes Type 2" value={historyForm.description} onChange={e=>setHistoryForm({...historyForm, description: e.target.value})}/></div>
                        </div>
                        <div className="px-4 pb-4"><button onClick={saveMedHistory} className="bg-purple-600 text-white px-5 py-2 rounded-lg text-sm font-bold hover:bg-purple-700">Add History</button></div>
                      </div>
                      {medHistory.length > 0 && <div className="space-y-2">{medHistory.map((h,i)=>(
                        <div key={i} className="border-l-4 border-purple-400 bg-purple-50 p-3 rounded-r-lg flex justify-between items-center">
                          <div><span className="font-bold text-sm">{h.description}</span><p className="text-xs text-slate-500">Category: {h.category} • Status: {h.status}</p></div>
                          <span className="bg-purple-200 text-purple-800 text-[10px] px-2 py-0.5 rounded-full font-bold uppercase">{h.category}</span>
                        </div>
                      ))}</div>}
                    </div>
                  )}

                  {/* EXAMINATION TAB */}
                  {activeTab === "examination" && (
                    <div className="space-y-4">
                      <div className="border rounded-xl overflow-hidden">
                        <div className="bg-teal-50 border-b p-3"><h3 className="font-bold text-teal-900 text-sm flex items-center gap-2"><Eye size={16}/> Clinical Examination</h3></div>
                        <div className="p-4 space-y-3">
                          <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">General Examination</label><textarea className="w-full border rounded-lg px-2.5 py-1.5 text-sm" rows={2} placeholder="Conscious, oriented, afebrile..." value={examForm.general_examination} onChange={e=>setExamForm({...examForm, general_examination: e.target.value})}/></div>
                          <p className="text-[10px] font-bold text-slate-500 uppercase">Systemic Examination</p>
                          <div className="grid grid-cols-2 gap-3">
                            {[{ k:"cvs", l:"Cardiovascular" },{ k:"resp", l:"Respiratory" },{ k:"gi", l:"Gastrointestinal" },{ k:"neuro", l:"Neurological" },{ k:"msk", l:"Musculoskeletal" }].map(s=>(
                              <div key={s.k}><label className="text-[10px] font-bold text-teal-600 block mb-1">{s.l}</label><input className="w-full border rounded-lg px-2.5 py-1.5 text-sm" placeholder={`${s.l} findings...`} value={(examForm.systemic_examination as any)[s.k]} onChange={e=>setExamForm({...examForm, systemic_examination:{...examForm.systemic_examination, [s.k]: e.target.value}})}/></div>
                            ))}
                          </div>
                          <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Local Examination</label><textarea className="w-full border rounded-lg px-2.5 py-1.5 text-sm" rows={2} value={examForm.local_examination} onChange={e=>setExamForm({...examForm, local_examination: e.target.value})}/></div>
                        </div>
                        <div className="px-4 pb-4"><button onClick={saveExamination} className="bg-teal-600 text-white px-5 py-2 rounded-lg text-sm font-bold hover:bg-teal-700">Save Examination</button></div>
                      </div>
                    </div>
                  )}

                  {/* DIAGNOSIS TAB */}
                  {activeTab === "diagnosis" && (
                    <div className="space-y-4">
                      <div className="border rounded-xl overflow-hidden">
                        <div className="bg-red-50 border-b p-3 flex justify-between items-center">
                          <h3 className="font-bold text-red-900 text-sm flex items-center gap-2"><Target size={16}/> ICD-10 Diagnosis</h3>
                          <button onClick={runAI} className="text-xs bg-slate-800 text-white px-3 py-1 rounded-full font-bold hover:bg-slate-700 flex items-center gap-1">{aiAnalyzing ? <RefreshCw size={12} className="animate-spin"/> : <BrainCircuit size={12}/>} AI Suggest</button>
                        </div>
                        <div className="p-4 grid grid-cols-2 gap-3">
                          <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">ICD-10 Code</label><input className="w-full border rounded-lg px-2.5 py-1.5 text-sm" placeholder="I10" value={diagForm.icd_code} onChange={e=>setDiagForm({...diagForm, icd_code: e.target.value})}/></div>
                          <div><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Type</label>
                            <select className="w-full border rounded-lg px-2.5 py-1.5 text-sm" value={diagForm.diagnosis_type} onChange={e=>setDiagForm({...diagForm, diagnosis_type: e.target.value})}>
                              <option value="provisional">Provisional</option><option value="final">Final</option>
                            </select>
                          </div>
                          <div className="col-span-2"><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Diagnosis Description</label><input className="w-full border rounded-lg px-2.5 py-1.5 text-sm" placeholder="Essential Hypertension" value={diagForm.diagnosis_description} onChange={e=>setDiagForm({...diagForm, diagnosis_description: e.target.value})}/></div>
                          <div className="flex items-center gap-2"><input type="checkbox" checked={diagForm.is_primary} onChange={e=>setDiagForm({...diagForm, is_primary: e.target.checked})}/><span className="text-xs font-bold text-slate-600">Primary Diagnosis</span></div>
                        </div>
                        <div className="px-4 pb-4"><button onClick={saveDiagnosis} className="bg-red-600 text-white px-5 py-2 rounded-lg text-sm font-bold hover:bg-red-700">Add Diagnosis</button></div>
                      </div>
                      {aiSuggestions && (
                        <div className="border rounded-xl bg-gradient-to-br from-slate-50 to-indigo-50/30 p-4 space-y-3">
                          <h4 className="text-xs font-bold text-indigo-800 uppercase">AI Suggested Diagnoses</h4>
                          <div className="flex flex-wrap gap-2">{aiSuggestions.suggested_diagnoses?.map((dx:string,i:number)=><button key={i} onClick={()=>setDiagForm({...diagForm, diagnosis_description: dx})} className="text-xs bg-white border px-3 py-1 rounded-full hover:bg-indigo-50 cursor-pointer">{dx}</button>)}</div>
                        </div>
                      )}
                      {diagnoses.length > 0 && <div className="space-y-2">{diagnoses.map((d,i)=>(
                        <div key={i} className={`border-l-4 ${d.is_primary ? 'border-red-500 bg-red-50' : 'border-slate-300 bg-slate-50'} p-3 rounded-r-lg flex justify-between items-center`}>
                          <div><span className="font-bold text-sm">{d.diagnosis_description}</span><p className="text-xs text-slate-500">{d.icd_code && `ICD: ${d.icd_code} • `}{d.diagnosis_type} {d.is_primary && '• PRIMARY'}</p></div>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${d.diagnosis_type==='final'?'bg-green-200 text-green-800':'bg-yellow-200 text-yellow-800'}`}>{d.diagnosis_type}</span>
                        </div>
                      ))}</div>}
                    </div>
                  )}

                  {/* SOAP NOTES TAB */}
                  {activeTab === "notes" && (
                    <div className="border rounded-xl overflow-hidden">
                      <div className="bg-indigo-50 border-b p-3 flex justify-between items-center">
                        <h3 className="font-bold text-indigo-900 text-sm flex items-center gap-2"><PenTool size={16}/> Clinical SOAP Notes</h3>
                        <button onClick={simulateScribe} className={`text-xs px-3 py-1 rounded flex items-center gap-1 font-bold text-white ${scribeListening ? 'bg-rose-500 animate-pulse' : 'bg-indigo-600 hover:bg-indigo-700'}`}><Mic size={14}/> {scribeListening ? 'Listening...' : 'AI Voice Scribe'}</button>
                      </div>
                      <div className="p-4 space-y-3">
                        {[{k:"chief_complaint",l:"Chief Complaint"},{k:"history_present_illness",l:"History of Present Illness"},{k:"physical_examination",l:"Physical Examination"},{k:"diagnosis",l:"Diagnosis"},{k:"plan",l:"Assessment & Plan"}].map(f=>(
                          <div key={f.k}><label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">{f.l}</label><textarea className="w-full border rounded-lg px-2.5 py-1.5 text-sm focus:border-indigo-400 focus:outline-none" rows={2} value={(noteData as any)[f.k]} onChange={e=>setNoteData({...noteData, [f.k]: e.target.value})}/></div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* PRESCRIPTIONS TAB */}
                  {activeTab === "prescriptions" && (
                    <div className="border rounded-xl overflow-hidden">
                      <div className="bg-emerald-50 border-b p-3"><h3 className="font-bold text-emerald-900 text-sm flex items-center gap-2"><Pill size={16}/> Prescriptions → Pharmacy</h3></div>
                      <div className="p-3 border-b bg-white flex gap-2">
                        <input className="text-sm p-2 border rounded-lg flex-1" placeholder='Type: "Paracetamol 500mg twice daily for 5 days"' value={voiceRxStr} onChange={e=>setVoiceRxStr(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')commitVoicePrescription()}}/>
                        <button onClick={commitVoicePrescription} className="bg-emerald-600 text-white rounded-lg px-3 hover:bg-emerald-700 font-bold text-sm">Add Rx</button>
                      </div>
                      <div className="p-3 space-y-2 max-h-80 overflow-y-auto">
                        {rxs.length===0 && <p className="text-xs text-slate-400 text-center py-6">No medications added</p>}
                        {rxs.map((r,i)=>(<div key={i} className="bg-white p-3 border border-emerald-100 border-l-4 border-l-emerald-500 rounded-lg"><p className="font-bold text-sm">{r.medicine_name} <span className="text-slate-500 font-normal">{r.strength||''}</span></p><p className="text-xs text-slate-600">{r.dosage} • {r.frequency} • {r.duration}</p></div>))}
                      </div>
                    </div>
                  )}

                  {/* ORDERS TAB */}
                  {activeTab === "orders" && (
                    <div className="space-y-4">
                      <div className="border rounded-xl overflow-hidden">
                        <div className="bg-sky-50 border-b p-3"><h3 className="font-bold text-sky-900 text-sm flex items-center gap-2"><Syringe size={16}/> CPOE — Orders → LIS / RIS / Billing</h3></div>
                        <div className="p-3 border-b bg-white flex gap-2">
                          <select className="text-sm border rounded-lg p-2" value={manualDiagnosticType} onChange={e=>setManualDiagnosticType(e.target.value)}>
                            <option value="lab">Laboratory</option><option value="radiology">Radiology</option><option value="procedure">Procedure</option>
                          </select>
                          <input className="text-sm p-2 border rounded-lg flex-1" placeholder="e.g. CBC, MRI Brain, CT Abdomen..." value={manualDiagnostic} onChange={e=>setManualDiagnostic(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'){commitOrder(manualDiagnostic, manualDiagnosticType);setManualDiagnostic("");}}}/>
                          <button onClick={()=>{commitOrder(manualDiagnostic, manualDiagnosticType);setManualDiagnostic("");}} className="bg-sky-600 text-white rounded-lg px-3 hover:bg-sky-700 font-bold text-sm"><Plus size={14} className="inline mr-1"/>Order</button>
                        </div>
                        <div className="p-3 space-y-2 max-h-60 overflow-y-auto">
                          {orders.length===0 && <p className="text-xs text-slate-400 text-center py-6">No orders placed</p>}
                          {orders.map((o,i)=>(<div key={i} className="bg-white p-3 text-sm border border-sky-100 border-l-4 border-l-sky-500 rounded-lg flex justify-between items-center"><div><p className="font-bold">{o.test_name}</p><p className="text-xs text-slate-500">{o.order_type} • {o.status}</p></div><CheckCircle size={16} className="text-sky-500"/></div>))}
                        </div>
                      </div>
                      {aiSuggestions && (
                        <div className="grid grid-cols-2 gap-4">
                          <div className="border rounded-xl p-3"><h4 className="text-[10px] font-bold text-slate-500 uppercase mb-2">AI Suggested Lab Tests</h4><div className="space-y-1">{aiSuggestions.recommended_lab_tests?.map((lb:string,i:number)=>(<div key={i} className="flex justify-between items-center text-xs bg-slate-50 p-2 rounded">{lb}<button onClick={()=>commitOrder(lb,"lab")} className="text-indigo-600 font-bold">Order +</button></div>))}</div></div>
                          <div className="border rounded-xl p-3"><h4 className="text-[10px] font-bold text-slate-500 uppercase mb-2">AI Suggested Imaging</h4><div className="space-y-1">{aiSuggestions.recommended_imaging_studies?.map((img:string,i:number)=>(<div key={i} className="flex justify-between items-center text-xs bg-slate-50 p-2 rounded">{img}<button onClick={()=>commitOrder(img,"radiology")} className="text-indigo-600 font-bold">Order +</button></div>))}</div></div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* AI ENGINE TAB */}
                  {activeTab === "ai_engine" && (
                    <div className="space-y-4">
                      <div className="border border-fuchsia-100 rounded-2xl overflow-hidden shadow-sm">
                        <div className="bg-gradient-to-r from-fuchsia-600 via-violet-600 to-indigo-600 p-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-white/15 backdrop-blur flex items-center justify-center"><Sparkles size={20} className="text-white"/></div>
                            <div>
                              <h3 className="font-bold text-white text-sm tracking-tight">Clinical AI Engine</h3>
                              <p className="text-[10px] text-white/60">Live patient context \u2022 Navigate \u2022 Scribe \u2022 Guard \u2022 Pipeline</p>
                            </div>
                          </div>
                        </div>
                        <div className="p-4 space-y-3 bg-gradient-to-b from-fuchsia-50/30 to-white">
                          {/* Context chips */}
                          <div className="flex flex-wrap gap-1.5">
                            {vitalsHistory.length > 0 && <span className="text-[10px] bg-rose-50 text-rose-600 border border-rose-200 px-2 py-1 rounded-lg font-semibold flex items-center gap-1"><HeartPulse size={10}/> Vitals ({vitalsHistory.length})</span>}
                            {complaints.length > 0 && <span className="text-[10px] bg-amber-50 text-amber-600 border border-amber-200 px-2 py-1 rounded-lg font-semibold flex items-center gap-1"><MessageSquareText size={10}/> Complaints ({complaints.length})</span>}
                            {medHistory.length > 0 && <span className="text-[10px] bg-purple-50 text-purple-600 border border-purple-200 px-2 py-1 rounded-lg font-semibold flex items-center gap-1"><ScrollText size={10}/> History ({medHistory.length})</span>}
                            {diagnoses.length > 0 && <span className="text-[10px] bg-red-50 text-red-600 border border-red-200 px-2 py-1 rounded-lg font-semibold flex items-center gap-1"><CircleDot size={10}/> Dx ({diagnoses.length})</span>}
                            {vitalsHistory.length === 0 && <span className="text-[10px] bg-slate-50 text-slate-400 border border-slate-200 px-2 py-1 rounded-lg flex items-center gap-1"><HeartPulse size={10}/> No vitals</span>}
                            {complaints.length === 0 && <span className="text-[10px] bg-slate-50 text-slate-400 border border-slate-200 px-2 py-1 rounded-lg flex items-center gap-1"><MessageSquareText size={10}/> No complaints</span>}
                          </div>
                          <textarea value={aiDoctorInput} onChange={e => setAiDoctorInput(e.target.value)} rows={2}
                            placeholder="Doctor's clinical input (or leave empty to use loaded complaints)..."
                            className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-fuchsia-500/30 focus:border-fuchsia-400 outline-none transition-all resize-none" />
                          <div className="flex gap-1.5 bg-slate-50 p-1 rounded-xl">
                            {([["navigate", "Compass", Workflow], ["scribe", "Scribe", PenTool], ["guard", "Guard", Shield], ["pipeline", "Full Pipeline", Zap]] as const).map(([m, label, Icon]) => (
                              <button key={m} onClick={() => setAiEngineModule(m as any)}
                                className={`flex-1 text-[11px] px-2 py-2 rounded-lg font-semibold transition-all flex items-center justify-center gap-1.5 ${
                                  aiEngineModule === m ? "bg-white text-fuchsia-700 shadow-sm border border-fuchsia-100" : "text-slate-500 hover:text-slate-700 hover:bg-white/50"
                                }`}>
                                <Icon size={12}/> {label}
                              </button>
                            ))}
                          </div>
                          <button onClick={runDeskAI} disabled={aiLoading}
                            className="w-full py-2.5 bg-gradient-to-r from-fuchsia-600 to-violet-600 text-white rounded-xl font-semibold text-sm hover:shadow-lg hover:shadow-fuchsia-200 disabled:opacity-50 transition-all flex items-center justify-center gap-2">
                            {aiLoading ? <><RefreshCw size={14} className="animate-spin"/> Processing...</> : <><Sparkles size={14}/> Run {aiEngineModule.charAt(0).toUpperCase() + aiEngineModule.slice(1)}</>}
                          </button>
                        </div>
                      </div>

                      {aiLoading && <div className="bg-gradient-to-r from-fuchsia-50 to-violet-50 rounded-2xl border border-fuchsia-100 p-10 text-center"><div className="w-12 h-12 mx-auto rounded-xl bg-fuchsia-100 flex items-center justify-center mb-3 animate-pulse"><BrainCircuit size={24} className="text-fuchsia-600"/></div><p className="text-fuchsia-700 text-sm font-medium">AI analyzing patient data...</p><p className="text-fuchsia-400 text-xs mt-1">{aiEngineModule === "pipeline" ? "Running all 5 modules..." : `Running ${aiEngineModule}...`}</p></div>}

                      {aiResult && !aiLoading && (
                        <div className="space-y-3">
                          {/* Navigator results */}
                          {(aiResult.module_output?.triage || aiResult.navigator?.module_output?.triage) && (() => {
                            const nav = aiResult.module_output || aiResult.navigator?.module_output || {};
                            const triage = nav.triage || {};
                            return (
                              <>
                                <div className="grid grid-cols-3 gap-2">
                                  <div className="bg-blue-50 rounded-lg p-3 text-center border border-blue-200"><p className="text-[10px] text-blue-500 font-bold">FOCUS</p><p className="font-bold text-blue-900 text-sm">{nav.focus_area}</p></div>
                                  <div className={`rounded-lg p-3 text-center text-white ${nav.risk_level === "High" ? "bg-red-600" : nav.risk_level === "Medium" ? "bg-amber-500" : "bg-green-500"}`}><p className="text-[10px] text-white/70 font-bold">RISK</p><p className="font-black text-lg">{nav.risk_level}</p></div>
                                  <div className="bg-slate-800 rounded-lg p-3 text-center text-white"><p className="text-[10px] text-slate-400 font-bold">CONFIDENCE</p><p className="font-black text-lg">{nav.confidence_score ? `${Math.round(nav.confidence_score * 100)}%` : "?"}</p></div>
                                </div>
                                {triage.level && <div className={`rounded-xl p-4 text-white ${triage.level === "ESI-1" ? "bg-red-600" : triage.level === "ESI-2" ? "bg-orange-500" : "bg-yellow-500"}`}><div className="flex justify-between"><div><p className="text-white/70 text-xs">TRIAGE</p><p className="text-xl font-black">{triage.level}</p></div><div className="text-right"><p className="text-white/70 text-xs">SEVERITY</p><p className="text-xl font-black">{triage.severity_score}/10</p></div></div><p className="text-sm text-white/80 mt-1">{triage.primary_impression}</p></div>}
                                {nav.ask_next?.length > 0 && <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-200"><h4 className="font-bold text-indigo-800 text-xs mb-2">🧠 Ask Patient Next:</h4>{nav.ask_next.map((q: string, i: number) => <p key={i} className="text-sm text-indigo-800 py-0.5">• {q}</p>)}</div>}
                                {nav.red_flags?.length > 0 && <div className="bg-red-50 rounded-xl p-3 border border-red-200"><h4 className="font-bold text-red-800 text-xs mb-1">🚨 Red Flags</h4>{nav.red_flags.map((f: string, i: number) => <p key={i} className="text-xs text-red-700">• {f}</p>)}</div>}
                                {nav.suggested_exam?.length > 0 && <div className="bg-emerald-50 rounded-xl p-3 border border-emerald-200"><h4 className="font-bold text-emerald-800 text-xs mb-1">🩺 Suggested Exams</h4>{nav.suggested_exam.map((e: string, i: number) => <p key={i} className="text-xs text-emerald-700">• {e}</p>)}</div>}
                              </>
                            );
                          })()}

                          {/* Scribe results */}
                          {(aiResult.module_output?.items || aiResult.scribe?.module_output?.items) && (() => {
                            const scr = aiResult.module_output || aiResult.scribe?.module_output || {};
                            return (
                              <>
                                <div className="bg-violet-50 rounded-xl p-4 border border-violet-200">
                                  <h4 className="font-bold text-violet-800 text-sm mb-2">📝 {scr.order_set_name} <span className={`ml-2 text-[10px] px-2 py-0.5 rounded-full ${scr.priority_level === "Emergency" ? "bg-red-200 text-red-800" : "bg-green-200 text-green-800"}`}>{scr.priority_level}</span></h4>
                                  <div className="space-y-1">
                                    {scr.items?.filter((i: any) => i.selected).map((item: any, idx: number) => (
                                      <div key={idx} className="flex items-center gap-2 text-xs bg-white rounded-lg p-2 border">
                                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${item.category === "Medication" ? "bg-emerald-100 text-emerald-700" : item.category === "Lab" ? "bg-cyan-100 text-cyan-700" : "bg-violet-100 text-violet-700"}`}>{item.category}</span>
                                        <span className="font-semibold text-slate-800">{item.label}</span>
                                        {item.dose && <span className="text-blue-600">{item.dose}</span>}
                                        {item.priority === "stat" && <span className="text-[9px] bg-red-100 text-red-700 px-1 rounded font-bold">STAT</span>}
                                        <button onClick={() => { commitOrder(item.label, item.category === "Lab" ? "lab" : item.category === "Imaging" ? "radiology" : "procedure"); }} className="ml-auto text-[10px] text-indigo-600 font-bold hover:underline">+ Add to CPOE</button>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                                {scr.draft_soap && (
                                  <div className="bg-white rounded-xl border overflow-hidden">
                                    <div className="bg-slate-800 text-white px-4 py-2 text-sm font-bold">📄 SOAP Note</div>
                                    <div className="p-3 space-y-2 text-xs">
                                      <div className="bg-blue-50 rounded p-2"><span className="font-bold text-blue-700">S:</span> {scr.draft_soap.subjective}</div>
                                      <div className="bg-green-50 rounded p-2"><span className="font-bold text-green-700">O:</span> {scr.draft_soap.objective}</div>
                                      <div className="bg-amber-50 rounded p-2"><span className="font-bold text-amber-700">A:</span> {scr.draft_soap.assessment}</div>
                                      <div className="bg-red-50 rounded p-2"><span className="font-bold text-red-700">P:</span> {scr.draft_soap.plan}</div>
                                    </div>
                                  </div>
                                )}
                              </>
                            );
                          })()}

                          {/* Guardian results */}
                          {(aiResult.guardian?.module_output?.overall_safety || aiResult.pipeline_output?.guardian?.module_output?.overall_safety) && (() => {
                            const g = aiResult.guardian?.module_output || aiResult.pipeline_output?.guardian?.module_output || {};
                            return (
                              <div className={`rounded-xl p-4 text-white ${g.overall_safety === "safe" ? "bg-emerald-600" : g.overall_safety === "caution" ? "bg-amber-500" : "bg-red-600"}`}>
                                <p className="text-white/70 text-xs">SAFETY GUARDIAN</p>
                                <p className="text-2xl font-black">{g.overall_safety?.toUpperCase()}</p>
                                <p className="text-sm text-white/80 mt-1">{g.guardian_summary}</p>
                                {g.allergy_alerts?.length > 0 && <div className="mt-2 space-y-1">{g.allergy_alerts.map((a: any, i: number) => <p key={i} className="text-xs">🚨 {a.proposed_drug} ↔ {a.allergen}: {a.recommendation}</p>)}</div>}
                                {g.drug_interactions?.length > 0 && <div className="mt-2 space-y-1">{g.drug_interactions.map((d: any, i: number) => <p key={i} className="text-xs">💊 {d.drug_a} + {d.drug_b}: {d.description}</p>)}</div>}
                                {g.contraindications?.length > 0 && <div className="mt-2 space-y-1">{g.contraindications.map((c: any, i: number) => <p key={i} className="text-xs">⛔ {c.order} ↔ {c.condition}: {c.recommendation}</p>)}</div>}
                              </div>
                            );
                          })()}

                          {/* ── ORCHESTRATOR: System Summary ── */}
                          {aiResult.system_summary && (
                            <div className="bg-slate-800 rounded-xl p-4 text-white">
                              <p className="text-slate-400 text-[10px] font-bold">SYSTEM SUMMARY — MASTER ORCHESTRATOR</p>
                              <div className="grid grid-cols-4 gap-2 mt-2">
                                <div className="bg-slate-700 rounded-lg p-2 text-center"><p className="text-[10px] text-slate-400">RISK</p><p className={`font-black text-sm ${aiResult.system_summary.overall_risk === "High" ? "text-red-400" : aiResult.system_summary.overall_risk === "Medium" ? "text-amber-400" : "text-emerald-400"}`}>{aiResult.system_summary.overall_risk}</p></div>
                                <div className="bg-slate-700 rounded-lg p-2 text-center"><p className="text-[10px] text-slate-400">TRIAGE</p><p className="font-black text-sm text-white">{aiResult.system_summary.triage || "—"}</p></div>
                                <div className="bg-slate-700 rounded-lg p-2 text-center"><p className="text-[10px] text-slate-400">ORDERS</p><p className="font-black text-sm text-sky-400">{aiResult.system_summary.orders_count}</p></div>
                                <div className="bg-slate-700 rounded-lg p-2 text-center"><p className="text-[10px] text-slate-400">SAFETY</p><p className={`font-black text-sm ${aiResult.system_summary.safety_status === "safe" ? "text-emerald-400" : "text-red-400"}`}>{aiResult.system_summary.safety_status?.toUpperCase()}</p></div>
                              </div>
                              {aiResult.system_summary.primary_impression && <p className="text-sm text-slate-300 mt-2">📋 {aiResult.system_summary.primary_impression}</p>}
                            </div>
                          )}

                          {/* ── ORCHESTRATOR: Patient Instructions ── */}
                          {aiResult.patient_instructions && (
                            <div className="bg-gradient-to-r from-teal-50 to-cyan-50 rounded-xl border border-teal-200 overflow-hidden">
                              <div className="bg-teal-600 text-white px-4 py-2 text-sm font-bold flex items-center gap-2">🗣️ Patient-Friendly Instructions</div>
                              <div className="p-4">
                                <pre className="text-sm text-slate-800 whitespace-pre-wrap font-sans leading-relaxed">{aiResult.patient_instructions}</pre>
                              </div>
                            </div>
                          )}

                          {/* ── ORCHESTRATOR: Handover Card ── */}
                          {aiResult.pipeline_output?.handover?.module_output?.patients?.[0] && (() => {
                            const hp = aiResult.pipeline_output.handover.module_output.patients[0];
                            return (
                              <div className="bg-orange-50 rounded-xl border border-orange-200 overflow-hidden">
                                <div className="bg-orange-600 text-white px-4 py-2 text-sm font-bold">🔄 Shift Handover Card</div>
                                <div className="p-3 space-y-2">
                                  <div className="flex items-center gap-2">
                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold text-white ${hp.status_summary === "Deteriorating" ? "bg-red-500" : hp.status_summary === "Guarded" ? "bg-amber-500" : "bg-emerald-500"}`}>{hp.status_summary}</span>
                                    <span className="text-xs text-slate-600">{hp.vitals_trend?.direction && `Vitals: ${hp.vitals_trend.direction}`}</span>
                                  </div>
                                  {hp.one_liner && <p className="text-sm text-orange-800 font-medium">{hp.one_liner}</p>}
                                  {hp.critical_changes?.length > 0 && <div className="bg-red-50 rounded-lg p-2 border border-red-200">{hp.critical_changes.map((c: string, i: number) => <p key={i} className="text-xs text-red-700">• {c}</p>)}</div>}
                                  {hp.pending_tasks?.length > 0 && <div className="bg-amber-50 rounded-lg p-2 border border-amber-200">{hp.pending_tasks.map((t: string, i: number) => <div key={i} className="flex items-center gap-1.5 text-xs text-amber-800"><input type="checkbox" className="w-3 h-3"/>{t}</div>)}</div>}
                                </div>
                              </div>
                            );
                          })()}

                          {/* ── ORCHESTRATOR: Pipeline Progress ── */}
                          {aiResult.modules_executed && (
                            <div className="flex items-center gap-1 flex-wrap">
                              {["navigator", "scribe", "guardian", "handover", "translator"].map((mod) => (
                                <span key={mod} className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                                  aiResult.modules_executed?.includes(mod)
                                    ? "bg-emerald-100 text-emerald-700"
                                    : aiResult.modules_failed?.includes(mod)
                                    ? "bg-red-100 text-red-700"
                                    : "bg-slate-100 text-slate-400"
                                }`}>
                                  {aiResult.modules_executed?.includes(mod) ? "✅" : aiResult.modules_failed?.includes(mod) ? "❌" : "⏳"} {mod}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* ── ORCHESTRATOR: Validation ── */}
                          {aiResult.validation?.inconsistencies?.length > 0 && (
                            <div className="bg-yellow-50 rounded-xl p-3 border border-yellow-200">
                              <h4 className="font-bold text-yellow-800 text-xs mb-1">⚠️ Consistency Issues</h4>
                              {aiResult.validation.inconsistencies.map((c: string, i: number) => <p key={i} className="text-xs text-yellow-700">• {c}</p>)}
                            </div>
                          )}

                          <details className="text-xs"><summary className="cursor-pointer text-slate-500 font-medium">View raw JSON</summary><pre className="mt-1 bg-slate-900 text-green-400 p-3 rounded-xl overflow-auto max-h-60 text-[10px]">{JSON.stringify(aiResult, null, 2)}</pre></details>
                        </div>
                      )}
                    </div>
                  )}

                </div>

                {/* TIMELINE PANEL */}
                {timelineMode && (
                  <div className="w-1/3 bg-slate-50 overflow-y-auto p-4">
                    <h3 className="font-bold text-sm text-slate-800 mb-4 flex items-center gap-2"><Activity size={16} className="text-indigo-600"/> EMR Timeline</h3>
                    <div className="relative border-l-2 border-slate-300 ml-2 space-y-6">
                      {timelineNodes.map((n,i)=>(
                        <div key={i} className="relative pl-5">
                          <span className={`absolute -left-[7px] top-1 w-3.5 h-3.5 rounded-full border-2 border-white ${n.node_type==='lab_result'?'bg-sky-500':n.node_type==='rx'?'bg-emerald-500':n.node_type==='diagnosis'?'bg-rose-500':'bg-indigo-500'}`}></span>
                          <div className="bg-white border rounded-lg p-2.5 text-xs shadow-sm">
                            <span className="text-[9px] font-bold text-slate-400 uppercase">{n.node_type} • {n.date}</span>
                            <p className="font-bold text-slate-800 mt-0.5">{n.title}</p>
                            <p className="text-slate-500 mt-0.5">{n.details}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* IPD ADMISSION MODAL */}
      {showIpdModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm p-4">
          <form onSubmit={recommendAdmission} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <h3 className="text-xl font-black text-rose-800 flex items-center gap-2"><AlertTriangle size={22} className="text-rose-600"/> Clinical Handover — IPD Admission</h3>
            <div><label className="text-xs font-bold text-slate-500 uppercase block mb-1">Current Health & Vitals</label><textarea required value={ipdNotes.current_health} onChange={e=>setIpdNotes({...ipdNotes, current_health: e.target.value})} className="w-full p-2.5 border rounded-lg text-sm" rows={2} placeholder="e.g. Pt is hemodynamically stable..."/></div>
            <div><label className="text-xs font-bold text-slate-500 uppercase block mb-1">Doses & Medications</label><textarea required value={ipdNotes.doses_to_give} onChange={e=>setIpdNotes({...ipdNotes, doses_to_give: e.target.value})} className="w-full p-2.5 border rounded-lg text-sm" rows={2}/></div>
            <div><label className="text-xs font-bold text-slate-500 uppercase block mb-1">Plan of Action</label><textarea required value={ipdNotes.plan_of_action} onChange={e=>setIpdNotes({...ipdNotes, plan_of_action: e.target.value})} className="w-full p-2.5 border rounded-lg text-sm" rows={2}/></div>
            <div className="flex justify-end gap-2 pt-4 border-t">
              <button type="button" onClick={()=>setShowIpdModal(false)} className="px-5 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg">Cancel</button>
              <button type="submit" className="bg-rose-600 text-white px-6 py-2 rounded-xl text-sm font-bold hover:bg-rose-700">Push to IPD</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
