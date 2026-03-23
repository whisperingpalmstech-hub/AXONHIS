"use client";

import React, { useState, useEffect } from "react";
import { opdVisitsApi, type OpdVisit, type VisitComplaint, type VisitClassification, type DoctorRecommendation, type ContextSnapshot } from "@/lib/opd-visits-api";
import {
  Stethoscope, Activity, FileText, Settings, Search, Edit2, Play, AlertCircle, RefreshCw, Calendar, CheckCircle2, Mic, Bot
} from "lucide-react";
import { api } from "@/lib/api";

type TabTypes = "intake" | "queue" | "questionnaires" | "analytics";

interface PatientRecord { id: string; first_name: string; last_name: string; patient_uuid?: string; }
interface DoctorRecord { id: string; full_name: string; email: string; }

export default function OpdVisitsPage() {
  const [activeTab, setActiveTab] = useState<TabTypes>("intake");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [doctors, setDoctors] = useState<DoctorRecord[]>([]);

  // Queue State
  const [queue, setQueue] = useState<OpdVisit[]>([]);

  // Intake State
  const [patientId, setPatientId] = useState("");
  const [rawComplaint, setRawComplaint] = useState("");
  const [intakeStep, setIntakeStep] = useState(1);
  const [currentVisit, setCurrentVisit] = useState<OpdVisit | null>(null);
  const [complaintRes, setComplaintRes] = useState<VisitComplaint | null>(null);
  const [classRes, setClassRes] = useState<VisitClassification | null>(null);
  const [docRec, setDocRec] = useState<DoctorRecommendation | null>(null);
  const [contextSnap, setContextSnap] = useState<ContextSnapshot | null>(null);

  // Analytics State
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => {
    loadBaseData();
  }, []);

  useEffect(() => {
    if (activeTab === "queue") loadQueue();
    else if (activeTab === "analytics") loadAnalytics();
  }, [activeTab]);

  const loadBaseData = async () => {
    try {
      const p = await api.get<any>("/patients");
      setPatients(Array.isArray(p) ? p : p?.items || []);
      const d = await api.get<any>("/auth/users");
      setDoctors(Array.isArray(d) ? d : d?.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadQueue = async () => {
    setLoading(true);
    try {
      await opdVisitsApi.listVisits({ status: "created", priority_tag: "emergency" }); // Just getting a generic list
      const res = await opdVisitsApi.listVisits();
      setQueue(res || []);
    } catch (e: any) {
      console.error(e);
    }
    setLoading(false);
  };

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const data = await opdVisitsApi.computeAnalytics(new Date().toISOString().split("T")[0]);
      setAnalytics(data);
    } catch (e: any) {
      console.error(e);
    }
    setLoading(false);
  };

  const getPatientName = (id: string) => {
    const pt = patients.find(p => p.id === id);
    return pt ? `${pt.first_name} ${pt.last_name}` : id.slice(0, 8);
  };

  const getDoctorName = (id?: string) => {
    if (!id) return "Unassigned";
    const d = doctors.find(doc => doc.id === id);
    return d ? d.full_name : id.slice(0, 8);
  };

  // ── Intake Flow ──────────────────────────────────
  const startIntake = async () => {
    if (!patientId) { setError("Select patient first"); return; }
    setLoading(true); setError("");
    try {
      // 1. Create Visit
      const p = patients.find(x => x.id === patientId);
      const visit = await opdVisitsApi.createVisit({
        patient_id: patientId,
        patient_uhid: p?.patient_uuid || "",
        visit_source: "front_office"
      });
      setCurrentVisit(visit);

      // 2. Fetch context
      const resC = await opdVisitsApi.aggregateContext(visit.id);
      setContextSnap(resC);

      setIntakeStep(2);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  const captureAIComplaint = async () => {
    if (!rawComplaint || !currentVisit) return;
    setLoading(true); setError("");
    try {
      const cRes = await opdVisitsApi.captureComplaint({
        visit_id: currentVisit.id,
        raw_complaint_text: rawComplaint,
        input_mode: "typed"
      });
      setComplaintRes(cRes);

      const clRes = await opdVisitsApi.classifyVisit({
        visit_id: currentVisit.id,
        vitals_snapshot: { spo2: 98, bp_sys: 120, hr: 80, temp: 37 } // Mocking vitals for now
      });
      setClassRes(clRes);

      const dRes = await opdVisitsApi.recommendDoctor(currentVisit.id);
      setDocRec(dRes);

      setIntakeStep(3);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  const finalizeVisit = async () => {
    if (!currentVisit || !docRec) return;
    setLoading(true); setError("");
    try {
      await opdVisitsApi.selectDoctor(currentVisit.id, {
        selected_doctor_id: doctors[0]?.id || currentVisit.patient_id, // Hack fallback to first doctor
        selection_mode: "auto"
      });
      
      const v = await opdVisitsApi.getVisit(currentVisit.id);
      setCurrentVisit(v);

      setIntakeStep(4);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  const resetIntake = () => {
    setIntakeStep(1); setPatientId(""); setRawComplaint("");
    setCurrentVisit(null); setComplaintRes(null); setClassRes(null); setDocRec(null); setContextSnap(null);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3 text-slate-800">
            <Bot className="text-indigo-600" size={32} />
            OPD Visit Intelligence
          </h1>
          <p className="text-slate-500 mt-1">AI-driven patient intake, triage, and orchestration.</p>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-center gap-2"><AlertCircle size={18} /> {error}</div>}

      <div className="flex bg-white rounded-lg p-1 shadow-sm w-fit border border-slate-200">
        {[
          { id: "intake", icon: Mic, label: "AI Intake" },
          { id: "queue", icon: Activity, label: "Live Queue" },
          { id: "questionnaires", icon: FileText, label: "Questionnaires" },
          { id: "analytics", icon: Activity, label: "Analytics" }
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as TabTypes)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium transition-all ${
              activeTab === t.id ? "bg-indigo-50 text-indigo-700 shadow-sm" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* ═════════ INTAKE TAB ═════════ */}
      {activeTab === "intake" && (
        <div className="space-y-6">
          <div className="flex items-center gap-12 text-sm font-medium text-slate-400 mb-8 border-b pb-4">
            <div className={intakeStep >= 1 ? "text-indigo-600 flex items-center gap-2" : "flex items-center gap-2"}><span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center">1</span> Patient</div>
            <div className={intakeStep >= 2 ? "text-indigo-600 flex items-center gap-2" : "flex items-center gap-2"}><span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center">2</span> AI Intake</div>
            <div className={intakeStep >= 3 ? "text-indigo-600 flex items-center gap-2" : "flex items-center gap-2"}><span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center">3</span> Triage & Routing</div>
            <div className={intakeStep >= 4 ? "text-emerald-600 flex items-center gap-2" : "flex items-center gap-2"}><span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center">4</span> Confirmed</div>
          </div>

          <div className="grid grid-cols-3 gap-6">
            
            {/* Step 1 & 2 Workspace */}
            <div className="col-span-2 space-y-6">
              {intakeStep === 1 && (
                <div className="card p-8 text-center bg-indigo-50/30 border-dashed border-2">
                  <h3 className="text-xl font-bold mb-6">Select Patient for New Visit</h3>
                  <select className="input-field max-w-sm mx-auto mb-6" value={patientId} onChange={e => setPatientId(e.target.value)}>
                    <option value="">-- Select Patient --</option>
                    {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.patient_uuid})</option>)}
                  </select>
                  <button onClick={startIntake} disabled={loading || !patientId} className="btn-primary">Start AI Intake Session</button>
                </div>
              )}

              {intakeStep === 2 && (
                <div className="card p-6 shadow-md border-indigo-100">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-bold text-lg flex items-center gap-2"><Mic className="text-indigo-500" /> Patient Complaint</h3>
                    <div className="badge bg-slate-100 text-slate-700">{currentVisit?.visit_id}</div>
                  </div>
                  <textarea 
                    className="w-full border rounded-lg p-4 h-32 text-lg mb-4 focus:ring-2 focus:ring-indigo-500 outline-none" 
                    placeholder="Patient describes symptoms... (e.g. 'I have severe chest pain and dizziness since morning')"
                    value={rawComplaint} onChange={e => setRawComplaint(e.target.value)}
                  />
                  <button onClick={captureAIComplaint} disabled={loading || !rawComplaint} className="btn-primary w-full flex justify-center gap-2 py-3 text-lg">
                    <Bot /> Analyze with AI Engine
                  </button>
                </div>
              )}

              {intakeStep === 3 && complaintRes && classRes && docRec && (
                <div className="card p-6 shadow-md border-indigo-100 space-y-6">
                  <div>
                    <h3 className="font-bold text-lg flex items-center gap-2 mb-4"><CheckCircle2 className="text-emerald-500" /> AI Findings</h3>
                    <div className="bg-slate-50 p-4 rounded-xl space-y-4">
                      <div>
                        <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Extracted Symptoms</span>
                        <div className="flex gap-2 mt-2">
                          {complaintRes.structured_symptoms?.map((s,i) => <span key={i} className="badge bg-purple-100 text-purple-700">{s}</span>)}
                        </div>
                      </div>
                      <div>
                        <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">ICPC Classification</span>
                        <div className="flex gap-2 mt-2">
                          {complaintRes.icpc_codes?.map((c: any,i) => <span key={i} className="badge bg-blue-100 text-blue-700">{c.code} - {c.label}</span>) || "None"}
                        </div>
                      </div>
                      <div className="flex justify-between items-center bg-white p-3 rounded-lg border">
                        <div>
                          <div className="font-bold text-sm">AI Severity Score</div>
                          <div className="text-xs text-slate-500">Based on complaint analysis</div>
                        </div>
                        <div className="text-xl font-black text-rose-600">{complaintRes.severity_score}/10</div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className={`p-4 rounded-xl border-2 ${classRes.category === 'emergency_opd' ? 'border-rose-500 bg-rose-50' : 'border-amber-500 bg-amber-50'}`}>
                      <span className="text-sm font-bold opacity-70 uppercase">Triage Result</span>
                      <div className="text-xl font-bold mt-1 uppercase">{classRes.category.replace('_',' ')}</div>
                      <p className="text-xs mt-2 opacity-80">{classRes.classification_reason}</p>
                    </div>
                    
                    <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm">
                      <span className="text-sm font-bold text-slate-500 uppercase">Recommended Routing</span>
                      <div className="text-lg font-bold mt-1 text-indigo-700">{docRec.recommended_specialty}</div>
                      <div className="text-xs text-slate-500 mt-2">Select Doctor:</div>
                      <select className="w-full mt-1 border rounded p-1 text-sm bg-slate-50">
                        {doctors.map(d => <option key={d.id} value={d.id}>{d.full_name}</option>)}
                      </select>
                    </div>
                  </div>

                  <button onClick={finalizeVisit} disabled={loading} className="btn-primary w-full py-3">Confirm Routing & Add to Queue</button>
                </div>
              )}

              {intakeStep === 4 && (
                <div className="card p-12 text-center border-emerald-500 border-2 bg-emerald-50">
                  <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircle2 size={40} />
                  </div>
                  <h2 className="text-2xl font-bold text-emerald-800 mb-2">Visit Created Successfully!</h2>
                  <p className="text-emerald-600 mb-6">Patient routed to <strong>{currentVisit?.department || "Specialty"}</strong>.</p>
                  <button onClick={resetIntake} className="btn-primary bg-emerald-600 hover:bg-emerald-700">Start Next Intake</button>
                </div>
              )}
            </div>

            {/* Context Sidebar */}
            <div className="col-span-1">
              <div className="card p-5 sticky top-6">
                <h3 className="font-bold flex items-center gap-2 mb-4"><Activity size={16} /> Patient Clinical Context</h3>
                
                {contextSnap ? (
                  <div className="space-y-4 text-sm">
                    <div className="bg-slate-50 p-3 rounded-lg border">
                      <div className="text-xs font-bold text-slate-500 uppercase">Summary</div>
                      <div className="font-medium mt-1">{contextSnap.context_summary}</div>
                    </div>
                    
                    <div>
                      <div className="text-xs font-bold text-slate-500 uppercase mb-2">Previous Diagnoses</div>
                      {contextSnap.previous_diagnoses.length > 0 ? (
                        <div className="space-y-2">
                          {contextSnap.previous_diagnoses.slice(0,3).map((d: any, i) => (
                            <div key={i} className="flex justify-between items-center text-xs bg-slate-50 p-2 rounded">
                              <span className="truncate max-w-[120px] font-semibold">{d.department || "General"}</span>
                              <span className="text-slate-400">{d.date?.slice(0,10)}</span>
                            </div>
                          ))}
                        </div>
                      ) : <p className="text-slate-400 text-xs italic">No history.</p>}
                    </div>
                  </div>
                ) : (
                  <div className="text-center p-8 text-slate-400 text-sm">
                    Select a patient to pull context engine data.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═════════ QUEUE TAB ═════════ */}
      {activeTab === "queue" && (
        <div className="card p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold">Today's Intelligent OPD Queue</h2>
            <button onClick={loadQueue} className="btn-secondary"><RefreshCw size={14} className="mr-2" /> Refresh</button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-600 border-b">
                <tr>
                  <th className="py-3 px-4">Visit ID</th>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Doctor</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {queue.map(v => (
                  <tr key={v.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-mono font-medium">{v.visit_id}</td>
                    <td className="py-3 px-4 font-semibold">{getPatientName(v.patient_id)}</td>
                    <td className="py-3 px-4 text-slate-500 capitalize">{v.visit_type.replace('_',' ')}</td>
                    <td className="py-3 px-4">
                      <span className={`badge ${
                        v.priority_tag === 'emergency' ? 'bg-rose-100 text-rose-700' :
                        v.priority_tag === 'priority' ? 'bg-amber-100 text-amber-700' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {v.priority_tag.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="badge bg-blue-50 text-blue-700 capitalize border border-blue-200">{v.status.replace('_',' ')}</span>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-700">{getDoctorName(v.doctor_id)}</td>
                  </tr>
                ))}
                {queue.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-slate-400">Queue is empty.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ═════════ ANALYTICS TAB ═════════ */}
      {activeTab === "analytics" && analytics && (
        <div className="space-y-6">
          <div className="grid grid-cols-4 gap-6">
            <div className="card p-5 bg-gradient-to-br from-indigo-500 to-indigo-600 text-white">
              <div className="text-indigo-100 text-sm font-medium mb-1">Total Visits Today</div>
              <div className="text-4xl font-black">{analytics.total_visits}</div>
            </div>
            <div className="card p-5">
              <div className="text-slate-500 text-sm font-medium mb-1">Emergency Triage</div>
              <div className="text-3xl font-black text-rose-600">{analytics.emergency_visits}</div>
            </div>
            <div className="card p-5">
              <div className="text-slate-500 text-sm font-medium mb-1">Priority Triage</div>
              <div className="text-3xl font-black text-amber-500">{analytics.priority_visits}</div>
            </div>
            <div className="card p-5">
              <div className="text-slate-500 text-sm font-medium mb-1">Routine</div>
              <div className="text-3xl font-black text-emerald-500">{analytics.routine_visits}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="card p-6">
              <h3 className="font-bold text-lg mb-4">Top Specialties Recommended</h3>
              <div className="space-y-4">
                {analytics.top_specialties?.map((s: any, i: number) => (
                  <div key={i} className="flex justify-between items-center">
                    <span className="font-medium text-slate-700">{s.specialty}</span>
                    <span className="badge bg-indigo-50 text-indigo-700 font-bold">{s.count} visits</span>
                  </div>
                )) || <div className="text-slate-400 italic">No data</div>}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
