"use client";

import React, { useState, useEffect } from "react";
import { doctorDeskApi } from "@/lib/doctor-desk-api";
import { api } from "@/lib/api";
import {
  Stethoscope, Users, Calendar, Activity, ClipboardList, PenTool,
  Mic, BrainCircuit, Syringe, Pill, FileText, Download, Target, Plus, CheckCircle,
  AlertTriangle
} from "lucide-react";import { useTranslation } from "@/i18n";

export default function DoctorDeskPage() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const DOCTOR_ID = "00000000-0000-0000-0000-000000000009";

  const [patients, setPatients] = useState<any[]>([]);
  const [worklist, setWorklist] = useState<any[]>([]);
  const [activePatient, setActivePatient] = useState<any | null>(null);

  // EMR Timeline State
  const [timelineMode, setTimelineMode] = useState(false);
  const [timelineNodes, setTimelineNodes] = useState<any[]>([]);
  const [simPatientId, setSimPatientId] = useState("");

  // SOAP Note State
  const [noteData, setNoteData] = useState({ chief_complaint: "", history_present_illness: "", plan: "" });
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [scribeListening, setScribeListening] = useState(false);

  // AI Suggestions
  const [aiSuggestions, setAiSuggestions] = useState<any>(null);

  // Prescriptions & Orders
  const [rxs, setRxs] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [voiceRxStr, setVoiceRxStr] = useState("");
  const [manualDiagnostic, setManualDiagnostic] = useState("");
  const [manualDiagnosticType, setManualDiagnosticType] = useState("Laboratory");

  // IPD Admission Modal
  const [showIpdModal, setShowIpdModal] = useState(false);
  const [ipdNotes, setIpdNotes] = useState({ current_health: "", doses_to_give: "", plan_of_action: "" });

  useEffect(() => {
    loadBaseData();
  }, []);

  const loadBaseData = async () => {
    setLoading(true);
    try {
      const p = await api.get<any>("/patients/");
      setPatients(Array.isArray(p) ? p : p?.items || []);
      const wl = await doctorDeskApi.getWorklist(DOCTOR_ID);
      setWorklist(wl);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const getPatientName = (id: string) => {
    const pt = patients.find(p => p.id === id);
    return pt ? `${pt.first_name} ${pt.last_name}` : "Unknown";
  };
  const getPatientUhid = (id: string) => {
    const pt = patients.find(p => p.id === id);
    return pt ? (pt.uhid || pt.patient_uuid || "---") : "---";
  };

  const seedDoctorQueue = async () => {
    if (patients.length === 0) return alert(t("docDesk.addPatientsFirst") || "Add patients first");
    const targetId = simPatientId || patients[Math.max(0, patients.length - 1)].id;
    await doctorDeskApi.seedPatient({
      doctor_id: DOCTOR_ID,
      visit_id: "00000000-0000-0000-0000-000000000000",
      patient_id: targetId,
      priority_indicator: "normal"
    });
    loadBaseData();
  };

  const callPatient = async (wl: any) => {
    await doctorDeskApi.updateStatus(wl.id, "in_consultation");
    const pt = patients.find(p => p.id === wl.patient_id);
    setActivePatient({ ...wl, detail: pt });
    
    // Fetch timeline
    const tl = await doctorDeskApi.getTimeline(wl.patient_id);
    setTimelineNodes(tl.chronological_nodes || []);
    loadBaseData();
  };

  const injectTemplate = () => {
    setNoteData({
      chief_complaint: "Patient presents for regular follow up.",
      history_present_illness: "Denies chest pain, shortness of breath, or palpitations.",
      plan: "Continue current medications. Follow up in 3 months."
    });
  };

  const simulateScribeDictation = async () => {
    setScribeListening(true);
    setTimeout(async () => {
      setScribeListening(false);
      const res = await doctorDeskApi.transcribeVoice({ doctor_id: DOCTOR_ID, audio_data_base64: "dummy" });
      setNoteData({ ...noteData, chief_complaint: res.structured_note.chief_complaint, history_present_illness: res.structured_note.history_present_illness, plan: res.structured_note.plan });
    }, 2000);
  };

  const runAIDiagnosticSimulation = async () => {
    if(!noteData.chief_complaint) return alert("Type symptoms in chief complaint first.");
    setAiAnalyzing(true);
    try {
      const rec = await doctorDeskApi.getAISuggestions(noteData.chief_complaint);
      setAiSuggestions(rec);
    } catch(e) {}
    setAiAnalyzing(false);
  };

  const commitVoicePrescription = async () => {
    if(!voiceRxStr) return;
    const res = await doctorDeskApi.parseVoicePrescription({
        visit_id: activePatient.visit_id, doctor_id: DOCTOR_ID, text: voiceRxStr
    });
    setRxs([...rxs, res]);
    setVoiceRxStr("");
  };

  const commitOrder = async (testName: string, type: string) => {
    const res = await doctorDeskApi.placeOrder({
      visit_id: activePatient.visit_id, doctor_id: DOCTOR_ID,
      order_type: type, test_name: testName
    });
    setOrders([...orders, res]);
  };

  const concludeConsultation = async () => {
    await doctorDeskApi.saveNote({ ...noteData, doctor_id: DOCTOR_ID, visit_id: activePatient.visit_id });
    await doctorDeskApi.updateStatus(activePatient.id, "completed");
    await doctorDeskApi.generateSummary(activePatient.visit_id, DOCTOR_ID);
    alert(t("docDesk.consultationComplete") || "Consultation complete. Patient discharged. Clinical Summary Generated.");
    setActivePatient(null);
    setNoteData({chief_complaint:"", history_present_illness:"", plan:""});
    setRxs([]); setOrders([]); setAiSuggestions(null);
    loadBaseData();
  };

  const recommendAdmission = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!activePatient) return;
    try {
      const resp = await fetch(`http://localhost:9500/api/v1/ipd/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
        body: JSON.stringify({
          patient_name: `${activePatient.detail?.first_name} ${activePatient.detail?.last_name}`,
          patient_uhid: activePatient.detail?.uhid || activePatient.patient_id,
          gender: activePatient.detail?.gender || "Unknown",
          date_of_birth: activePatient.detail?.date_of_birth || "2000-01-01",
          mobile_number: activePatient.detail?.primary_phone || "9999999999",
          admitting_doctor: `Dr. AI Desk`, treating_doctor: `Dr. AI Desk`,
          specialty: "General Medicine",
          reason_for_admission: noteData.chief_complaint || "Clinical observation recommended",
          admission_category: "Emergency",
          admission_source: "OPD",
          preferred_bed_category: "General Ward",
          expected_admission_date: new Date().toISOString(),
          clinical_notes: `Current Health: ${ipdNotes.current_health}\nMedications/Doses: ${ipdNotes.doses_to_give}\nPlan of Action: ${ipdNotes.plan_of_action}`
        })
      });

      if (resp.ok) {
        alert("Admission request with clinical context strongly recommended. Sent to IPD Ward Desk for Bed Allocation!");
        setShowIpdModal(false);
        setIpdNotes({current_health: "", doses_to_give: "", plan_of_action: ""});
      } else {
        alert("Error sending admission push to IPD.");
      }
    } catch (e) {
      alert("Network Error while pushing to IPD.");
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-[1600px] mx-auto space-y-6 h-screen overflow-hidden flex flex-col">
      <div className="flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3 text-indigo-900">
            <BrainCircuit className="text-indigo-600" size={32} />
            {t("docDesk.aiDoctorDesk")}
          </h1>
          <p className="text-slate-500 mt-1">{t("docDesk.deskSubtitle")}</p>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex gap-6">
        
        {/* LEFT COMPONENT: WORKLIST DASHBOARD */}
        <div className="w-80 bg-white border border-slate-200 rounded-xl flex flex-col overflow-hidden shadow-sm shrink-0">
          <div className="bg-slate-900 text-white p-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-bold flex items-center gap-2"><Users size={18}/> {t("docDesk.waitlist")}</h3>
            </div>
            <div className="flex items-center gap-2">
              <select className="border border-slate-700 bg-slate-800 rounded text-xs px-2 py-1.5 focus:border-indigo-500 focus:outline-none flex-1" value={simPatientId} onChange={e => setSimPatientId(e.target.value)}>
                <option value="">{t("docDesk.latestPatient")}</option>
                {patients.slice().reverse().map(p => (
                  <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
                ))}
              </select>
              <button onClick={seedDoctorQueue} className="text-xs bg-slate-800 border border-slate-700 hover:bg-slate-700 text-white px-2 py-1.5 rounded flex items-center justify-center" title={t("docDesk.simulateEntry")}><Plus size={14}/></button>
            </div>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-2 relative">
            {worklist.filter(w=>w.status==='waiting').length === 0 && <div className="text-center p-8 text-slate-400 text-sm">{t("docDesk.queueEmpty")}</div>}
            {worklist.filter(w=>w.status==='waiting').map(wl => (
              <div key={wl.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg hover:border-indigo-300 transition-colors cursor-pointer group">
                 <div className="flex justify-between items-start mb-2">
                   <div>
                     <p className="font-bold text-slate-800 text-sm leading-tight">{getPatientName(wl.patient_id)}</p>
                     <p className="text-xs text-slate-500">{getPatientUhid(wl.patient_id)}</p>
                   </div>
                   <span className="bg-indigo-100 text-indigo-800 text-[10px] uppercase font-bold px-2 py-0.5 rounded">{t("docDesk.token")} {wl.queue_position || 'NN'}</span>
                 </div>
                 <button onClick={()=>callPatient(wl)} className="w-full bg-white border border-slate-300 text-xs py-1.5 rounded text-slate-600 group-hover:bg-indigo-600 group-hover:text-white group-hover:border-indigo-600 font-medium transition-colors">{t("docDesk.callToChamber")}</button>
              </div>
            ))}
            
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest px-2 pt-4 pb-1 border-t mt-4">{t("docDesk.consultationInProgress")}</h4>
             {worklist.filter(w=>w.status==='in_consultation').map(wl => (
              <div key={wl.id} className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                 <div className="flex justify-between items-center mb-1">
                   <p className="font-bold text-emerald-900 text-sm">{getPatientName(wl.patient_id)}</p>
                   <Activity size={14} className="text-emerald-500 animate-pulse"/>
                 </div>
                 <button onClick={()=>callPatient(wl)} className="text-xs text-emerald-700 font-bold hover:underline">{t("docDesk.returnToProfile")} →</button>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT COMPONENT: ACTIVE CONSULTATION UI OR STANDBY */}
        <div className="flex-1 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm flex flex-col">
          {!activePatient ? (
             <div className="flex-1 flex flex-col items-center justify-center text-slate-400 space-y-4">
               <Stethoscope size={64} className="text-slate-200" />
               <h2 className="text-xl font-bold">{t("docDesk.waitingForNextPatient")}</h2>
               <p className="text-sm">{t("docDesk.selectFromWorklist")}</p>
             </div>
          ) : (
            <>
              {/* PATIENT HEADER */}
              <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex justify-between items-center shrink-0">
                  <div className="flex items-center gap-4">
                     <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700 font-bold text-lg">
                        {activePatient.detail?.first_name?.[0]}{activePatient.detail?.last_name?.[0]}
                     </div>
                     <div>
                       <h2 className="text-xl font-black text-slate-800">{activePatient.detail?.first_name} {activePatient.detail?.last_name}</h2>
                       <p className="text-slate-500 text-sm font-medium">{t("docDesk.uhid")}: {activePatient.detail?.uhid} • {t("docDesk.age")}: {new Date().getFullYear() - new Date(activePatient.detail?.date_of_birth).getFullYear()} • {t("docDesk.blood")}: {activePatient.detail?.blood_group}</p>
                     </div>
                  </div>
                  <div className="flex gap-2">
                     <button onClick={()=>setTimelineMode(!timelineMode)} className={`btn-secondary text-sm ${timelineMode?'bg-slate-200':''}`}><Activity size={16}/> {t("docDesk.emrTimeline")}</button>
                     <button onClick={()=>setShowIpdModal(true)} className="btn-secondary text-sm bg-rose-50 text-rose-600 border-rose-200 hover:bg-rose-100 hover:text-rose-700 font-bold"><AlertTriangle size={16}/> {t("docDesk.recommendAdmission")}</button>
                     <button onClick={concludeConsultation} className="btn-primary text-sm bg-emerald-600 hover:bg-emerald-700"><CheckCircle size={16}/> {t("docDesk.completeSummary")}</button>
                  </div>
              </div>

              {/* MAIN BODY AREA */}
               <div className="flex-1 overflow-hidden flex relative">
                  
                  {/* WORKSPACE AREA */}
                  <div className={`p-6 overflow-y-auto space-y-6 ${timelineMode ? 'w-2/3 border-r border-slate-200' : 'w-full'}`}>
                      
                      {/* AI SCRIBE OR MANUAL SOAP */}
                      <div className="border border-slate-200 rounded-xl overflow-hidden">
                          <div className="bg-indigo-50 border-b border-indigo-100 p-3 flex justify-between items-center">
                              <h3 className="font-bold text-indigo-900 flex items-center gap-2"><PenTool size={16}/> {t("docDesk.clinicalEncounterNotes")}</h3>
                              <div className="flex gap-2">
                                 <button onClick={injectTemplate} className="text-xs bg-white border border-indigo-200 px-2 py-1 rounded text-indigo-700 hover:bg-slate-50">{t("docDesk.insertTemplate")}</button>
                                 <button onClick={simulateScribeDictation} className={`text-xs px-3 py-1 rounded flex items-center gap-1 font-bold text-white shadow-sm transition-all ${scribeListening ? 'bg-rose-500 animate-pulse' : 'bg-indigo-600 hover:bg-indigo-700'}`}>
                                    <Mic size={14}/> {scribeListening ? t("docDesk.dictationActive") : t("docDesk.aiVoiceScribe")}
                                 </button>
                              </div>
                          </div>
                          <div className="p-4 grid grid-cols-2 gap-4">
                              <div className="col-span-2">
                                <label className="text-xs font-bold text-slate-500 block mb-1">{t("docDesk.chiefComplaint")}</label>
                                <textarea className="w-full border-slate-300 rounded-md text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" rows={2} value={noteData.chief_complaint} onChange={e=>setNoteData({...noteData, chief_complaint:e.target.value})} />
                              </div>
                              <div className="col-span-2">
                                <label className="text-xs font-bold text-slate-500 block mb-1">{t("docDesk.historyPresentIllness")}</label>
                                <textarea className="w-full border-slate-300 rounded-md text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" rows={3} value={noteData.history_present_illness} onChange={e=>setNoteData({...noteData, history_present_illness:e.target.value})} />
                              </div>
                              <div className="col-span-2">
                                <label className="text-xs font-bold text-slate-500 block mb-1">{t("docDesk.assessmentPlan")}</label>
                                <textarea className="w-full border-slate-300 rounded-md text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" rows={2} value={noteData.plan} onChange={e=>setNoteData({...noteData, plan:e.target.value})} />
                              </div>
                          </div>
                      </div>

                      {/* AI DIAGNOSIS SUPPORT */}
                      <div className="border border-slate-200 rounded-xl overflow-hidden bg-gradient-to-br from-slate-50 to-indigo-50/30">
                          <div className="p-3 border-b border-slate-200 flex justify-between items-center">
                             <h3 className="font-bold text-slate-800 flex items-center gap-2"><Target size={16} className="text-rose-500"/> {t("docDesk.aiSupportTitle")}</h3>
                             <button onClick={runAIDiagnosticSimulation} className="text-xs bg-slate-800 text-white px-3 py-1 rounded-full font-bold shadow-sm hover:bg-slate-700 flex items-center gap-1 transition-all">{aiAnalyzing ? <Activity size={12} className="animate-spin"/> : <BrainCircuit size={12}/>} {t("docDesk.predictDiagnostics")}</button>
                          </div>
                          <div className="p-4">
                             {!aiSuggestions ? (
                                <p className="text-xs text-slate-500 text-center py-4">{t("docDesk.runCDSSPrompt")}</p>
                             ) : (
                                <div className="space-y-4">
                                  <div>
                                    <h4 className="text-xs font-bold bg-indigo-100 text-indigo-800 px-2 py-0.5 inline-block rounded mb-2 w-full uppercase">{t("docDesk.possibleDiffDx")}</h4>
                                    <div className="flex flex-wrap gap-2">
                                      {aiSuggestions.suggested_diagnoses.map((dx:string, i:number)=><span key={i} className="text-sm font-medium bg-white border border-slate-200 px-3 py-1 rounded-full">{dx}</span>)}
                                    </div>
                                  </div>
                                  <div className="flex gap-4">
                                     <div className="flex-1">
                                         <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-1">{t("docDesk.suggestedLabWork")}</h4>
                                         <div className="space-y-1">
                                            {aiSuggestions.recommended_lab_tests.map((lb:string, i:number)=>
                                               <div key={i} className="flex justify-between items-center text-xs bg-white border border-slate-200 p-2 rounded">
                                                  {lb} <button onClick={()=>commitOrder(lb, "Laboratory")} className="text-indigo-600 hover:text-indigo-800 font-bold">{t("docDesk.orderBtn")} <Plus size={10} className="inline"/></button>
                                               </div>
                                            )}
                                         </div>
                                     </div>
                                     <div className="flex-1">
                                         <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-1">{t("docDesk.suggestedImaging")}</h4>
                                         <div className="space-y-1">
                                            {aiSuggestions.recommended_imaging_studies.map((img:string, i:number)=>
                                                <div key={i} className="flex justify-between items-center text-xs bg-white border border-slate-200 p-2 rounded">
                                                  {img} <button onClick={()=>commitOrder(img, "Radiology")} className="text-indigo-600 hover:text-indigo-800 font-bold">{t("docDesk.orderBtn")} <Plus size={10} className="inline"/></button>
                                               </div>
                                            )}
                                         </div>
                                     </div>
                                  </div>
                                </div>
                             )}
                          </div>
                      </div>

                      {/* PRESCRIPTIONS & ORDERS COMPILATION */}
                      <div className="grid grid-cols-2 gap-4">
                         
                         {/* Prescriptions Panel */}
                         <div className="border border-slate-200 rounded-xl overflow-hidden flex flex-col h-64">
                             <div className="bg-slate-50 border-b border-slate-200 p-3 flex justify-between items-center">
                                <h3 className="font-bold text-slate-800 flex items-center gap-2"><Pill size={16} className="text-emerald-600"/> {t("docDesk.structuredPrescriptions")}</h3>
                             </div>
                             <div className="p-3 border-b border-slate-100 bg-white flex gap-2">
                                 <input type="text" className="text-xs p-1.5 border border-slate-300 rounded flex-1 focus:outline-none focus:border-indigo-500" placeholder={t("docDesk.naturalRxPlaceholder")} value={voiceRxStr} onChange={e=>setVoiceRxStr(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')commitVoicePrescription()}} />
                                 <button onClick={commitVoicePrescription} className="bg-indigo-600 text-white rounded p-1.5"><Mic size={14}/></button>
                             </div>
                             <div className="flex-1 p-2 bg-slate-50 overflow-y-auto space-y-2">
                                {rxs.length===0 && <p className="text-xs text-slate-400 text-center pt-8">{t("docDesk.noMedicationsAdded")}</p>}
                                {rxs.map((r,i)=>(
                                  <div key={i} className="bg-white p-2 text-xs border border-emerald-100 border-l-2 border-l-emerald-500 rounded relative shadow-sm">
                                      <p className="font-bold">{r.medicine_name} <span className="text-slate-500 font-normal">{r.strength || ''}</span></p>
                                      <p className="text-slate-600">{r.dosage} • {r.frequency} • {r.duration}</p>
                                  </div>
                                ))}
                             </div>
                         </div>
                         
                         {/* Active Orders Panel */}
                         <div className="border border-slate-200 rounded-xl overflow-hidden flex flex-col h-64">
                             <div className="bg-slate-50 border-b border-slate-200 p-3 flex justify-between items-center">
                                <h3 className="font-bold text-slate-800 flex items-center gap-2"><Syringe size={16} className="text-sky-600"/> {t("docDesk.lisRisOrderDispatch")}</h3>
                             </div>
                             <div className="p-2 border-b border-slate-100 bg-white flex gap-1">
                                <select className="text-xs border border-slate-300 rounded p-1.5 focus:outline-none" value={manualDiagnosticType} onChange={e=>setManualDiagnosticType(e.target.value)}>
                                   <option>{t("docDesk.typeLab")}</option><option>{t("docDesk.typeRadiology")}</option><option>{t("docDesk.typeProcedure")}</option>
                                </select>
                                <input type="text" className="text-xs p-1.5 border border-slate-300 rounded flex-1 focus:outline-none focus:border-indigo-500" placeholder={t("docDesk.mriBrainPlaceholder")} value={manualDiagnostic} onChange={e=>setManualDiagnostic(e.target.value)} onKeyDown={e=>{if(e.key==='Enter') {commitOrder(manualDiagnostic, manualDiagnosticType); setManualDiagnostic("");}}} />
                                <button onClick={()=>{commitOrder(manualDiagnostic, manualDiagnosticType); setManualDiagnostic("");}} className="bg-sky-600 text-white rounded px-2 hover:bg-sky-700 font-bold text-xs"><Plus size={14} className="inline"/> {t("docDesk.addBtn")}</button>
                             </div>
                             <div className="flex-1 p-2 bg-slate-50 overflow-y-auto space-y-2">
                                {orders.length===0 && <p className="text-xs text-slate-400 text-center pt-8">{t("docDesk.noDiagnosticOrders placed")}</p>}
                                {orders.map((o,i)=>(
                                  <div key={i} className="bg-white p-2 text-xs border border-sky-100 border-l-2 border-l-sky-500 rounded relative shadow-sm flex items-center justify-between">
                                      <div>
                                        <p className="font-bold">{o.test_name}</p>
                                        <p className="text-slate-600">{o.order_type}</p>
                                      </div>
                                      <CheckCircle size={14} className="text-sky-500"/>
                                  </div>
                                ))}
                             </div>
                         </div>
                      </div>

                  </div>

                  {/* TIMELINE PANEL (RIGHT SLIDEOUT) */}
                  {timelineMode && (
                      <div className="w-1/3 bg-slate-50 border-l border-slate-200 overflow-y-auto flex flex-col p-4 animate-in slide-in-from-right absolute right-0 top-0 bottom-0 shadow-[-10px_0_20px_rgba(0,0,0,0.05)]">
                          <h3 className="font-bold text-lg text-slate-800 mb-6 flex items-center gap-2 border-b pb-2"><Activity size={20} className="text-indigo-600"/> Enterprise EMR Timeline</h3>
                          <div className="relative border-l-2 border-slate-300 ml-3 space-y-8 pb-8">
                             {timelineNodes.map((n, i)=>(
                               <div key={i} className="relative pl-6">
                                  <span className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 border-white ${
                                     n.node_type === 'lab_result' ? 'bg-sky-500' :
                                     n.node_type === 'rx' ? 'bg-emerald-500' :
                                     n.node_type === 'diagnosis' ? 'bg-rose-500' : 'bg-indigo-500'
                                  }`}></span>
                                  <div className="bg-white border text-sm border-slate-200 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                                    <span className="text-[10px] font-bold text-slate-400 block mb-1 uppercase">{n.node_type} • {n.date}</span>
                                    <p className="font-bold text-slate-800">{n.title}</p>
                                    <p className="text-slate-600 mt-1 line-clamp-3">{n.details}</p>
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
            <h3 className="text-xl font-black text-rose-800 flex items-center gap-2 mb-2"><AlertTriangle size={22} className="text-rose-600"/> {t("docDesk.clinicalHandoverIPD")}</h3>
            <p className="text-sm text-slate-600 mb-4">{t("docDesk.clinicalHandoverSubtitle")}</p>
            
            <div>
               <label className="text-xs font-bold text-slate-500 uppercase block mb-1">{t("docDesk.currentHealthVitals")}</label>
               <textarea required value={ipdNotes.current_health} onChange={e=>setIpdNotes({...ipdNotes, current_health: e.target.value})} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400" rows={2} placeholder="e.g. Pt is hemodynamically stable..." />
            </div>

            <div>
               <label className="text-xs font-bold text-slate-500 uppercase block mb-1">{t("docDesk.dosesMedications")}</label>
               <textarea required value={ipdNotes.doses_to_give} onChange={e=>setIpdNotes({...ipdNotes, doses_to_give: e.target.value})} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400" rows={2} placeholder="e.g. IV Fluids 1L Normal Saline STAT..." />
            </div>

            <div>
               <label className="text-xs font-bold text-slate-500 uppercase block mb-1">{t("docDesk.planOfAction")}</label>
               <textarea required value={ipdNotes.plan_of_action} onChange={e=>setIpdNotes({...ipdNotes, plan_of_action: e.target.value})} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400" rows={2} placeholder="e.g. Keep NPO. Awaiting CT Abdomen results..." />
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-100 mt-2">
              <button type="button" onClick={() => setShowIpdModal(false)} className="px-5 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg">{t("docDesk.cancel")}</button>
              <button type="submit" className="bg-rose-600 hover:bg-rose-700 text-white px-6 py-2 rounded-xl text-sm font-bold transition-all shadow-md shadow-rose-200 flex items-center gap-2">
                 <Target size={16}/> {t("docDesk.pushAdmission")}
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}
