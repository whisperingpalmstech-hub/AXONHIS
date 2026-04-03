"use client";

import React, { useState, useEffect } from "react";
import { doctorDeskApi } from "@/lib/doctor-desk-api";
import { api } from "@/lib/api";
import {
  Stethoscope, Users, Activity, PenTool, Mic, BrainCircuit, Syringe, Pill,
  Target, Plus, CheckCircle, AlertTriangle, Heart, Thermometer, FileText,
  History, Search, ClipboardList, Eye, X, ChevronDown, ChevronRight, RefreshCw
} from "lucide-react";
import { useTranslation } from "@/i18n";
import { TopNav } from "@/components/ui/TopNav";

type Tab = "notes" | "vitals" | "complaints" | "history" | "examination" | "diagnosis" | "orders" | "prescriptions";

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
    { key: "vitals", label: "Vitals", icon: Heart, color: "text-rose-600" },
    { key: "complaints", label: "Complaints", icon: ClipboardList, color: "text-amber-600" },
    { key: "history", label: "History", icon: History, color: "text-purple-600" },
    { key: "examination", label: "Examination", icon: Eye, color: "text-teal-600" },
    { key: "diagnosis", label: "Diagnosis (ICD-10)", icon: Target, color: "text-red-600" },
    { key: "notes", label: "SOAP Notes", icon: PenTool, color: "text-indigo-600" },
    { key: "prescriptions", label: "Prescriptions", icon: Pill, color: "text-emerald-600" },
    { key: "orders", label: "Orders (CPOE)", icon: Syringe, color: "text-sky-600" },
  ];

  return (
    <div className="p-4 md:p-6 max-w-[1800px] mx-auto h-screen overflow-hidden flex flex-col">
      <TopNav title="nav.doctorDesk" />
      <div className="flex justify-between items-center shrink-0 mb-4">
        <div>
          <h1 className="text-2xl font-black flex items-center gap-3 text-indigo-900"><BrainCircuit className="text-indigo-600" size={28} /> EMR Doctor Desk</h1>
          <p className="text-slate-500 text-sm">Complete Clinical Consultation • CPOE • Billing Integration</p>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex gap-4">
        {/* LEFT: WORKLIST */}
        <div className="w-72 bg-white border border-slate-200 rounded-xl flex flex-col overflow-hidden shadow-sm shrink-0">
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white p-3">
            <h3 className="font-bold flex items-center gap-2 text-sm mb-2"><Users size={16}/> Patient Worklist</h3>
            <div className="flex items-center gap-1.5">
              <select className="border border-slate-700 bg-slate-800 rounded text-xs px-1.5 py-1 flex-1" value={simPatientId} onChange={e => setSimPatientId(e.target.value)}>
                <option value="">Latest Patient</option>
                {patients.slice().reverse().map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}
              </select>
              <button onClick={seedDoctorQueue} className="bg-indigo-600 hover:bg-indigo-500 text-white p-1.5 rounded"><Plus size={14}/></button>
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
        <div className="flex-1 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm flex flex-col">
          {!activePatient ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 space-y-3">
              <Stethoscope size={56} className="text-slate-200" />
              <h2 className="text-lg font-bold">Waiting for Patient</h2>
              <p className="text-sm">Select from worklist to begin consultation</p>
            </div>
          ) : (
            <>
              {/* PATIENT HEADER */}
              <div className="bg-gradient-to-r from-slate-50 to-indigo-50/30 border-b px-5 py-3 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700 font-bold">
                    {activePatient.detail?.first_name?.[0]}{activePatient.detail?.last_name?.[0]}
                  </div>
                  <div>
                    <h2 className="text-lg font-black text-slate-800">{activePatient.detail?.first_name} {activePatient.detail?.last_name}</h2>
                    <p className="text-slate-500 text-xs">UHID: {activePatient.detail?.uhid} • Age: {activePatient.detail?.date_of_birth ? new Date().getFullYear() - new Date(activePatient.detail.date_of_birth).getFullYear() : '--'} • Blood: {activePatient.detail?.blood_group || '--'}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={()=>setTimelineMode(!timelineMode)} className={`text-xs px-3 py-1.5 rounded-lg border font-medium ${timelineMode ? 'bg-indigo-100 border-indigo-300 text-indigo-700' : 'border-slate-300 text-slate-600 hover:bg-slate-50'}`}><Activity size={14} className="inline mr-1"/>Timeline</button>
                  <button onClick={()=>setShowIpdModal(true)} className="text-xs px-3 py-1.5 rounded-lg border border-rose-200 bg-rose-50 text-rose-600 font-bold hover:bg-rose-100"><AlertTriangle size={14} className="inline mr-1"/>Admit IPD</button>
                  <button onClick={concludeConsultation} className="text-xs px-4 py-1.5 rounded-lg bg-emerald-600 text-white font-bold hover:bg-emerald-700 shadow-sm"><CheckCircle size={14} className="inline mr-1"/>Complete & Generate Summary</button>
                </div>
              </div>

              {/* TAB BAR */}
              <div className="flex border-b bg-slate-50 px-2 shrink-0 overflow-x-auto">
                {TABS.map(tab => (
                  <button key={tab.key} onClick={()=>setActiveTab(tab.key)}
                    className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-bold border-b-2 transition-all whitespace-nowrap ${activeTab === tab.key ? `border-indigo-600 ${tab.color} bg-white` : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
                    <tab.icon size={14}/> {tab.label}
                    {tab.key === "complaints" && complaints.length > 0 && <span className="bg-amber-100 text-amber-700 text-[10px] px-1.5 rounded-full">{complaints.length}</span>}
                    {tab.key === "diagnosis" && diagnoses.length > 0 && <span className="bg-red-100 text-red-700 text-[10px] px-1.5 rounded-full">{diagnoses.length}</span>}
                    {tab.key === "prescriptions" && rxs.length > 0 && <span className="bg-emerald-100 text-emerald-700 text-[10px] px-1.5 rounded-full">{rxs.length}</span>}
                    {tab.key === "orders" && orders.length > 0 && <span className="bg-sky-100 text-sky-700 text-[10px] px-1.5 rounded-full">{orders.length}</span>}
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
