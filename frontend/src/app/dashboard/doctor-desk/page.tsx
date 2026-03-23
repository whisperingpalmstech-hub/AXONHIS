"use client";

import React, { useState, useEffect } from "react";
import { doctorDeskApi } from "@/lib/doctor-desk-api";
import { api } from "@/lib/api";
import {
  Stethoscope, Users, Calendar, Activity, ClipboardList, PenTool,
  Mic, BrainCircuit, Syringe, Pill, FileText, Download, Target, Plus, CheckCircle
} from "lucide-react";

export default function DoctorDeskPage() {
  const [loading, setLoading] = useState(false);
  const DOCTOR_ID = "00000000-0000-0000-0000-000000000009";

  const [patients, setPatients] = useState<any[]>([]);
  const [worklist, setWorklist] = useState<any[]>([]);
  const [activePatient, setActivePatient] = useState<any | null>(null);

  // EMR Timeline State
  const [timelineMode, setTimelineMode] = useState(false);
  const [timelineNodes, setTimelineNodes] = useState<any[]>([]);

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

  useEffect(() => {
    loadBaseData();
  }, []);

  const loadBaseData = async () => {
    setLoading(true);
    try {
      const p = await api.get<any>("/patients");
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
    return pt ? pt.uhid : "---";
  };

  const seedDoctorQueue = async () => {
    if (patients.length === 0) return alert("Add patients first");
    await doctorDeskApi.seedPatient({
      doctor_id: DOCTOR_ID,
      visit_id: "00000000-0000-0000-0000-000000000000",
      patient_id: patients[0].id,
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
    alert("Consultation complete. Patient discharged. Clinical Summary Generated.");
    setActivePatient(null);
    setNoteData({chief_complaint:"", history_present_illness:"", plan:""});
    setRxs([]); setOrders([]); setAiSuggestions(null);
    loadBaseData();
  };

  return (
    <div className="p-4 md:p-8 max-w-[1600px] mx-auto space-y-6 h-screen overflow-hidden flex flex-col">
      <div className="flex justify-between items-center shrink-0">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3 text-indigo-900">
            <BrainCircuit className="text-indigo-600" size={32} />
            AI Doctor Desk
          </h1>
          <p className="text-slate-500 mt-1">Intelligent EMR, AI Scribing, and Clinical Decision Support.</p>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex gap-6">
        
        {/* LEFT COMPONENT: WORKLIST DASHBOARD */}
        <div className="w-80 bg-white border border-slate-200 rounded-xl flex flex-col overflow-hidden shadow-sm shrink-0">
          <div className="bg-slate-900 text-white p-4 flex justify-between items-center">
            <h3 className="font-bold flex items-center gap-2"><Users size={18}/> Waitlist</h3>
            <button onClick={seedDoctorQueue} className="text-xs text-indigo-200 hover:text-white"><Plus size={16}/></button>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-2 relative">
            {worklist.filter(w=>w.status==='waiting').length === 0 && <div className="text-center p-8 text-slate-400 text-sm">Queue empty.</div>}
            {worklist.filter(w=>w.status==='waiting').map(wl => (
              <div key={wl.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg hover:border-indigo-300 transition-colors cursor-pointer group">
                 <div className="flex justify-between items-start mb-2">
                   <div>
                     <p className="font-bold text-slate-800 text-sm leading-tight">{getPatientName(wl.patient_id)}</p>
                     <p className="text-xs text-slate-500">{getPatientUhid(wl.patient_id)}</p>
                   </div>
                   <span className="bg-indigo-100 text-indigo-800 text-[10px] uppercase font-bold px-2 py-0.5 rounded">TOKEN {wl.queue_position || 'NN'}</span>
                 </div>
                 <button onClick={()=>callPatient(wl)} className="w-full bg-white border border-slate-300 text-xs py-1.5 rounded text-slate-600 group-hover:bg-indigo-600 group-hover:text-white group-hover:border-indigo-600 font-medium transition-colors">Call to Chamber</button>
              </div>
            ))}
            
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest px-2 pt-4 pb-1 border-t mt-4">Consultation In Progress</h4>
             {worklist.filter(w=>w.status==='in_consultation').map(wl => (
              <div key={wl.id} className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                 <div className="flex justify-between items-center mb-1">
                   <p className="font-bold text-emerald-900 text-sm">{getPatientName(wl.patient_id)}</p>
                   <Activity size={14} className="text-emerald-500 animate-pulse"/>
                 </div>
                 <button onClick={()=>callPatient(wl)} className="text-xs text-emerald-700 font-bold hover:underline">Return to Profile →</button>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT COMPONENT: ACTIVE CONSULTATION UI OR STANDBY */}
        <div className="flex-1 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm flex flex-col">
          {!activePatient ? (
             <div className="flex-1 flex flex-col items-center justify-center text-slate-400 space-y-4">
               <Stethoscope size={64} className="text-slate-200" />
               <h2 className="text-xl font-bold">Waiting for Next Patient</h2>
               <p className="text-sm">Select a patient from the Worklist to begin consultation.</p>
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
                       <p className="text-slate-500 text-sm font-medium">UHID: {activePatient.detail?.uhid} • Age: {new Date().getFullYear() - new Date(activePatient.detail?.date_of_birth).getFullYear()} • Blood: {activePatient.detail?.blood_group}</p>
                     </div>
                  </div>
                  <div className="flex gap-2">
                     <button onClick={()=>setTimelineMode(!timelineMode)} className={`btn-secondary text-sm ${timelineMode?'bg-slate-200':''}`}><Activity size={16}/> EMR Timeline</button>
                     <button onClick={concludeConsultation} className="btn-primary text-sm bg-emerald-600 hover:bg-emerald-700"><CheckCircle size={16}/> Complete & Summary</button>
                  </div>
              </div>

              {/* MAIN BODY AREA */}
               <div className="flex-1 overflow-hidden flex relative">
                  
                  {/* WORKSPACE AREA */}
                  <div className={`p-6 overflow-y-auto space-y-6 ${timelineMode ? 'w-2/3 border-r border-slate-200' : 'w-full'}`}>
                      
                      {/* AI SCRIBE OR MANUAL SOAP */}
                      <div className="border border-slate-200 rounded-xl overflow-hidden">
                          <div className="bg-indigo-50 border-b border-indigo-100 p-3 flex justify-between items-center">
                              <h3 className="font-bold text-indigo-900 flex items-center gap-2"><PenTool size={16}/> Clinical Encounter Notes</h3>
                              <div className="flex gap-2">
                                 <button onClick={injectTemplate} className="text-xs bg-white border border-indigo-200 px-2 py-1 rounded text-indigo-700 hover:bg-slate-50">Insert Template</button>
                                 <button onClick={simulateScribeDictation} className={`text-xs px-3 py-1 rounded flex items-center gap-1 font-bold text-white shadow-sm transition-all ${scribeListening ? 'bg-rose-500 animate-pulse' : 'bg-indigo-600 hover:bg-indigo-700'}`}>
                                    <Mic size={14}/> {scribeListening ? 'Dictation Active...' : 'AI Voice Scribe'}
                                 </button>
                              </div>
                          </div>
                          <div className="p-4 grid grid-cols-2 gap-4">
                              <div className="col-span-2">
                                <label className="text-xs font-bold text-slate-500 block mb-1">Chief Complaint (Symptoms)</label>
                                <textarea className="w-full border-slate-300 rounded-md text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" rows={2} value={noteData.chief_complaint} onChange={e=>setNoteData({...noteData, chief_complaint:e.target.value})} />
                              </div>
                              <div className="col-span-2">
                                <label className="text-xs font-bold text-slate-500 block mb-1">History of Present Illness</label>
                                <textarea className="w-full border-slate-300 rounded-md text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" rows={3} value={noteData.history_present_illness} onChange={e=>setNoteData({...noteData, history_present_illness:e.target.value})} />
                              </div>
                              <div className="col-span-2">
                                <label className="text-xs font-bold text-slate-500 block mb-1">Assessment & Plan</label>
                                <textarea className="w-full border-slate-300 rounded-md text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" rows={2} value={noteData.plan} onChange={e=>setNoteData({...noteData, plan:e.target.value})} />
                              </div>
                          </div>
                      </div>

                      {/* AI DIAGNOSIS SUPPORT */}
                      <div className="border border-slate-200 rounded-xl overflow-hidden bg-gradient-to-br from-slate-50 to-indigo-50/30">
                          <div className="p-3 border-b border-slate-200 flex justify-between items-center">
                             <h3 className="font-bold text-slate-800 flex items-center gap-2"><Target size={16} className="text-rose-500"/> AI Clinical Decision Support</h3>
                             <button onClick={runAIDiagnosticSimulation} className="text-xs bg-slate-800 text-white px-3 py-1 rounded-full font-bold shadow-sm hover:bg-slate-700 flex items-center gap-1 transition-all">{aiAnalyzing ? <Activity size={12} className="animate-spin"/> : <BrainCircuit size={12}/>} Predict Diagnostics</button>
                          </div>
                          <div className="p-4">
                             {!aiSuggestions ? (
                                <p className="text-xs text-slate-500 text-center py-4">Run the CDSS Predictor to scan patient parameters against known topologies.</p>
                             ) : (
                                <div className="space-y-4">
                                  <div>
                                    <h4 className="text-xs font-bold bg-indigo-100 text-indigo-800 px-2 py-0.5 inline-block rounded mb-2 w-full uppercase">Possible Differential Diagnoses</h4>
                                    <div className="flex flex-wrap gap-2">
                                      {aiSuggestions.suggested_diagnoses.map((dx:string, i:number)=><span key={i} className="text-sm font-medium bg-white border border-slate-200 px-3 py-1 rounded-full">{dx}</span>)}
                                    </div>
                                  </div>
                                  <div className="flex gap-4">
                                     <div className="flex-1">
                                         <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-1">Suggested Lab Work</h4>
                                         <div className="space-y-1">
                                            {aiSuggestions.recommended_lab_tests.map((lb:string, i:number)=>
                                               <div key={i} className="flex justify-between items-center text-xs bg-white border border-slate-200 p-2 rounded">
                                                  {lb} <button onClick={()=>commitOrder(lb, "Laboratory")} className="text-indigo-600 hover:text-indigo-800 font-bold">Order <Plus size={10} className="inline"/></button>
                                               </div>
                                            )}
                                         </div>
                                     </div>
                                     <div className="flex-1">
                                         <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-1">Suggested Imaging</h4>
                                         <div className="space-y-1">
                                            {aiSuggestions.recommended_imaging_studies.map((img:string, i:number)=>
                                                <div key={i} className="flex justify-between items-center text-xs bg-white border border-slate-200 p-2 rounded">
                                                  {img} <button onClick={()=>commitOrder(img, "Radiology")} className="text-indigo-600 hover:text-indigo-800 font-bold">Order <Plus size={10} className="inline"/></button>
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
                                <h3 className="font-bold text-slate-800 flex items-center gap-2"><Pill size={16} className="text-emerald-600"/> Structured e-Prescriptions</h3>
                             </div>
                             <div className="p-3 border-b border-slate-100 bg-white flex gap-2">
                                 <input type="text" className="text-xs p-1.5 border border-slate-300 rounded flex-1 focus:outline-none focus:border-indigo-500" placeholder="Natural Rx: Amox 500mg BID 7 days" value={voiceRxStr} onChange={e=>setVoiceRxStr(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')commitVoicePrescription()}} />
                                 <button onClick={commitVoicePrescription} className="bg-indigo-600 text-white rounded p-1.5"><Mic size={14}/></button>
                             </div>
                             <div className="flex-1 p-2 bg-slate-50 overflow-y-auto space-y-2">
                                {rxs.length===0 && <p className="text-xs text-slate-400 text-center pt-8">No medications added.</p>}
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
                                <h3 className="font-bold text-slate-800 flex items-center gap-2"><Syringe size={16} className="text-sky-600"/> LIS / RIS Order Dispatch</h3>
                             </div>
                             <div className="flex-1 p-2 bg-slate-50 overflow-y-auto space-y-2">
                                {orders.length===0 && <p className="text-xs text-slate-400 text-center pt-10">No diagnostic orders placed.</p>}
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
    </div>
  );
}
