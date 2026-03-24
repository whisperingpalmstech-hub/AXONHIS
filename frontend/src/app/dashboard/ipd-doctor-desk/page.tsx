"use client";

import React, { useState, useEffect } from "react";
import { User, Activity, AlertCircle, Phone, Stethoscope, Plus, Save, FileText, ActivitySquare, ShieldAlert } from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { ipdApi } from "@/lib/ipd-api";

export default function IpdDoctorDeskPage() {
  const [patients, setPatients] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState("COVERSHEET");
  const [loading, setLoading] = useState(true);

  // Coversheet State
  const [coversheet, setCoversheet] = useState<any>(null);
  const [csForm, setCsForm] = useState({ primary_diagnosis: "", clinical_summary: "" });

  // Diagnoses State
  const [diagnoses, setDiagnoses] = useState<any[]>([]);
  const [showDiagModal, setShowDiagModal] = useState(false);
  const [diagForm, setDiagForm] = useState({ diagnosis_type: "Provisional", description: "", icd10_code: "" });

  // Treatment Plans State
  const [treatments, setTreatments] = useState<any[]>([]);
  const [showTpModal, setShowTpModal] = useState(false);
  const [tpForm, setTpForm] = useState({ therapy_type: "Medication", instructions: "" });

  // Progress Notes State
  const [progressNotes, setProgressNotes] = useState<any[]>([]);
  const [showPnModal, setShowPnModal] = useState(false);
  const [pnForm, setPnForm] = useState({ notes: "" });

  // Procedures State
  const [procedures, setProcedures] = useState<any[]>([]);
  const [showProcModal, setShowProcModal] = useState(false);
  const [procForm, setProcForm] = useState({ procedure_name: "", procedure_date: new Date().toISOString().slice(0, 16), notes: "" });

  useEffect(() => {
    fetchWorklist();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      fetchPatientData();
    }
  }, [selectedPatient]);

  const fetchWorklist = async () => {
    try {
      const res: any = await ipdApi.getDoctorWorklist();
      if (Array.isArray(res)) setPatients(res);
      else if (res && Array.isArray(res.data)) setPatients(res.data);
      else setPatients([]);
    } catch (error) {
      console.error("Error fetching worklist", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientData = async () => {
    try {
      const q = selectedPatient.admission_number;
      // Fetch coversheet
      const cs = await ipdApi.getDoctorCoversheet(q);
      setCoversheet(cs);
      if (cs) {
        setCsForm({ primary_diagnosis: cs.primary_diagnosis || "", clinical_summary: cs.clinical_summary || "" });
      }

      // Fetch all other data concurrently
      const [dgRes, tpRes, pnRes, procRes] = await Promise.all([
        ipdApi.getDiagnoses(q),
        ipdApi.getTreatmentPlans(q),
        ipdApi.getProgressNotes(q),
        ipdApi.getClinicalProcedures(q)
      ]);
      const extractData = (r: any) => Array.isArray(r) ? r : (r && Array.isArray(r.data)) ? r.data : [];
      setDiagnoses(extractData(dgRes));
      setTreatments(extractData(tpRes));
      setProgressNotes(extractData(pnRes));
      setProcedures(extractData(procRes));

    } catch (error) {
      console.error("Error fetching patient clinical data", error);
    }
  };

  const handleUpdateCoversheet = async () => {
    try {
      await ipdApi.updateDoctorCoversheet(selectedPatient.admission_number, csForm);
      fetchPatientData();
      alert("Coversheet updated.");
    } catch (e) {
      console.error(e);
      alert("Error updating coversheet.");
    }
  };

  const submitDiagnosis = async () => {
    try {
      await ipdApi.addDiagnosis(selectedPatient.admission_number, diagForm);
      setShowDiagModal(false);
      setDiagForm({ diagnosis_type: "Provisional", description: "", icd10_code: "" });
      fetchPatientData();
    } catch (e) { console.error(e); }
  };

  const submitTreatment = async () => {
    try {
      await ipdApi.addTreatmentPlan(selectedPatient.admission_number, tpForm);
      setShowTpModal(false);
      setTpForm({ therapy_type: "Medication", instructions: "" });
      fetchPatientData();
    } catch (e) { console.error(e); }
  };

  const submitProgressNote = async () => {
    try {
      await ipdApi.addProgressNote(selectedPatient.admission_number, pnForm);
      setShowPnModal(false);
      setPnForm({ notes: "" });
      fetchPatientData();
    } catch (e) { console.error(e); }
  };

  const submitProcedure = async () => {
    try {
      if (!procForm.procedure_name) return alert("Procedure name required");
      const d = { ...procForm, procedure_date: new Date(procForm.procedure_date).toISOString() };
      await ipdApi.addClinicalProcedure(selectedPatient.admission_number, d);
      setShowProcModal(false);
      setProcForm({ procedure_name: "", procedure_date: new Date().toISOString().slice(0, 16), notes: "" });
      fetchPatientData();
    } catch (e) { console.error(e); }
  };

  return (
    <div className="min-h-screen bg-slate-50 relative">
      <TopNav title="IPD Doctor Desk" />

      <div className="flex h-[calc(100vh-64px)] overflow-hidden">
        {/* LEFT PANEL : WORKLIST */}
        <div className="w-80 bg-white border-r border-slate-200 flex flex-col overflow-y-auto z-10 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
          <div className="p-4 border-b border-slate-100 sticky top-0 bg-white/90 backdrop-blur-sm z-20">
            <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <Stethoscope size={18} className="text-indigo-600" />
              My Admitted Patients
            </h2>
            <div className="mt-3">
              <input type="text" placeholder="Search admitted patients..." className="w-full text-sm placeholder:text-slate-400 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all" />
            </div>
          </div>
          
          <div className="p-3 space-y-2">
            {loading ? (
              <div className="text-sm text-slate-500 text-center py-10 animate-pulse">Loading worklist...</div>
            ) : patients.length === 0 ? (
              <div className="text-sm text-slate-500 text-center py-10">No admitted patients found.</div>
            ) : (
              patients.map((p, i) => (
                <div key={i} onClick={() => setSelectedPatient(p)}
                  className={`p-3 rounded-xl border ${selectedPatient?.admission_number === p.admission_number ? 'border-indigo-400 bg-indigo-50/50 shadow-sm' : 'border-slate-100 lg:border-transparent lg:hover:border-slate-200 lg:hover:shadow-sm lg:hover:bg-slate-50 cursor-pointer'} transition-all group`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <div className="font-bold text-slate-800 text-sm group-hover:text-indigo-700">{p.patient_uhid}</div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">{p.status || 'Admitted'}</span>
                  </div>
                  <div className="text-xs text-slate-500 mb-2 truncate">ADM: <span className="text-slate-700 font-medium">{p.admission_number}</span></div>
                  <div className="flex gap-2">
                    <div className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200 flex items-center gap-1.5 font-medium"><ActivitySquare size={12}/>{p.bed_uuid ? "Bed Allocated" : "Pending Bed"}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* MAIN CONTENT PANEL */}
        <div className="flex-1 flex flex-col items-center bg-slate-50/50 relative overflow-y-auto">
          {!selectedPatient ? (
            <div className="m-auto flex flex-col items-center text-slate-400 max-w-sm text-center">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-6 shadow-inner">
                <Stethoscope size={32} className="text-slate-300" />
              </div>
              <h2 className="text-xl font-bold text-slate-700 mb-2">Select a Patient</h2>
              <p className="text-sm leading-relaxed">Choose an admitted patient from the worklist to review their clinical coversheet, document diagnoses, and manage their treatment plan.</p>
            </div>
          ) : (
            <div className="w-full max-w-6xl p-6 lg:p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* PATIENT HEADER */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                <div className="flex gap-4 items-center pl-2">
                  <div className="w-14 h-14 bg-indigo-50 rounded-full flex justify-center items-center text-indigo-600 shadow-inner">
                    <User size={28} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-800 tracking-tight leading-tight">{selectedPatient.patient_uhid} Data</h2>
                    <div className="flex items-center gap-3 text-xs text-slate-500 mt-1.5 font-medium">
                      <span className="flex items-center gap-1.5"><ActivitySquare size={14} className="text-slate-400"/> {selectedPatient.admission_number}</span>
                      <span className="w-1 h-1 rounded-full bg-slate-300"></span>
                      <span className="flex items-center gap-1.5"><ShieldAlert size={14} className="text-slate-400"/> Dr. {selectedPatient.admitting_doctor || "Not assigned"}</span>
                      {coversheet?.verified_at && (
                        <>
                          <span className="w-1 h-1 rounded-full bg-slate-300"></span>
                          <span className="text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 flex items-center gap-1"><Activity size={12}/> Verified</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* TABS */}
              <div className="flex border-b border-slate-200 mb-6 sticky top-0 bg-slate-50/90 backdrop-blur-md z-10 pt-2">
                {["COVERSHEET", "DIAGNOSES", "TREATMENT PLAN", "PROGRESS NOTES", "PROCEDURES"].map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)}
                    className={`px-5 py-3 text-sm font-bold border-b-2 transition-all ${activeTab === tab ? "border-indigo-600 text-indigo-600" : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"}`}>
                    {tab.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {/* TAB CONTENT */}
              <div className="space-y-6">

                {/* COVERSHEET */}
                {activeTab === "COVERSHEET" && (
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                      <h3 className="text-base font-bold text-slate-800 flex items-center gap-2"><FileText size={18} className="text-slate-500"/> Clinical Coversheet</h3>
                      <button onClick={handleUpdateCoversheet} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold shadow-sm transition-colors">
                        <Save size={16}/> Save Updates
                      </button>
                    </div>
                    <div className="p-6 space-y-6">
                      <div className="grid grid-cols-1 gap-6">
                        <div>
                          <label className="block text-xs font-bold text-slate-600 mb-2 uppercase tracking-wide">Primary Diagnosis Overview</label>
                          <input type="text" value={csForm.primary_diagnosis} onChange={e => setCsForm({...csForm, primary_diagnosis: e.target.value})}
                            className="w-full text-sm bg-slate-50 border border-slate-300 rounded-lg px-4 py-3 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-medium text-slate-800 transition-all shadow-sm"
                            placeholder="e.g. Acute Appendicitis (K35)"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-600 mb-2 uppercase tracking-wide">Clinical Summary & Case Context</label>
                          <textarea rows={6} value={csForm.clinical_summary} onChange={e => setCsForm({...csForm, clinical_summary: e.target.value})}
                            className="w-full text-sm bg-slate-50 border border-slate-300 rounded-lg px-4 py-3 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-slate-800 transition-all shadow-sm resize-y"
                            placeholder="Enter detailed clinical summary upon admission..."
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* DIAGNOSES */}
                {activeTab === "DIAGNOSES" && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-sm font-bold text-slate-700">ICD-10 Diagnoses</div>
                      <button onClick={() => setShowDiagModal(true)} className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 rounded-lg text-sm font-bold transition-colors">
                        <Plus size={16}/> Add Diagnosis
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {diagnoses.length === 0 ? (
                         <div className="col-span-full text-center py-10 bg-white rounded-xl border border-slate-200 border-dashed text-slate-400 text-sm">No diagnoses recorded yet.</div>
                      ) : (
                        diagnoses.map((d, i) => (
                          <div key={i} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-2">
                              <span className={`text-xs font-bold px-2 py-0.5 rounded border ${d.diagnosis_type === 'Confirmed' ? 'bg-rose-50 text-rose-700 border-rose-200' : d.diagnosis_type === 'Provisional' ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                                {d.diagnosis_type}
                              </span>
                              {d.icd10_code && <span className="text-xs bg-slate-800 text-white px-2 py-0.5 rounded font-mono font-medium">{d.icd10_code}</span>}
                            </div>
                            <div className="text-sm font-medium text-slate-800 mb-3">{d.description}</div>
                            <div className="text-xs text-slate-500 flex justify-between items-center border-t border-slate-100 pt-3 mt-auto">
                              <span>By: {d.diagnosed_by_name}</span>
                              <span>{new Date(d.diagnosed_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short'})}</span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {/* TREATMENT PLAN */}
                {activeTab === "TREATMENT PLAN" && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-sm font-bold text-slate-700">Treatment Directives</div>
                      <button onClick={() => setShowTpModal(true)} className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 rounded-lg text-sm font-bold transition-colors">
                        <Plus size={16}/> Add Directive
                      </button>
                    </div>
                    <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
                      <table className="w-full text-left border-collapse text-sm">
                        <thead className="bg-slate-50 border-b border-slate-200 text-xs text-slate-500 uppercase font-bold tracking-wider">
                          <tr>
                            <th className="p-4 px-6">Date</th>
                            <th className="p-4 px-6">Therapy Type</th>
                            <th className="p-4 px-6">Instructions</th>
                            <th className="p-4 px-6">Doctor</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {treatments.length === 0 ? (
                            <tr><td colSpan={4} className="p-8 text-center text-slate-400">No treatment plans recorded.</td></tr>
                          ) : (
                            treatments.map((t, i) => (
                              <tr key={i} className="hover:bg-slate-50 transition-colors">
                                <td className="p-4 px-6 text-slate-500 whitespace-nowrap">{new Date(t.created_at).toLocaleDateString()}</td>
                                <td className="p-4 px-6 font-medium text-slate-800">
                                  <span className="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-md border border-indigo-100 text-xs font-bold">{t.therapy_type}</span>
                                </td>
                                <td className="p-4 px-6 text-slate-600 max-w-md">{t.instructions}</td>
                                <td className="p-4 px-6 text-slate-500 whitespace-nowrap">{t.created_by_name}</td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* PROGRESS NOTES */}
                {activeTab === "PROGRESS NOTES" && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-sm font-bold text-slate-700">Daily Clinical Progress</div>
                      <button onClick={() => setShowPnModal(true)} className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 text-white hover:bg-indigo-700 rounded-lg text-sm font-bold transition-colors shadow-sm">
                        <Plus size={16}/> New Note
                      </button>
                    </div>
                    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
                      {progressNotes.map((pn, i) => (
                        <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                          <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-slate-50 bg-indigo-100 text-indigo-600 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10 mx-auto">
                            <FileText size={16} />
                          </div>
                          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold text-indigo-600">{new Date(pn.recorded_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>
                              <span className="text-xs font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">Dr. {pn.doctor_name}</span>
                            </div>
                            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{pn.notes}</p>
                          </div>
                        </div>
                      ))}
                      {progressNotes.length === 0 && (
                        <div className="text-center py-10 text-slate-400 text-sm">No progress notes.</div>
                      )}
                    </div>
                  </div>
                )}

                {/* PROCEDURES */}
                {activeTab === "PROCEDURES" && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-sm font-bold text-slate-700">Clinical Procedures</div>
                      <button onClick={() => setShowProcModal(true)} className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 rounded-lg text-sm font-bold transition-colors">
                        <Plus size={16}/> Record Procedure
                      </button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {procedures.length === 0 ? (
                         <div className="col-span-full text-center py-10 bg-white rounded-xl border border-slate-200 border-dashed text-slate-400 text-sm">No procedures recorded.</div>
                      ) : (
                        procedures.map((p, i) => (
                          <div key={i} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-3">
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <h4 className="text-sm font-bold text-slate-800">{p.procedure_name}</h4>
                                <div className="text-xs text-slate-500 mt-1">{new Date(p.procedure_date).toLocaleString()}</div>
                              </div>
                              <div className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-xs font-bold whitespace-nowrap">Completed</div>
                            </div>
                            {p.notes && <div className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">{p.notes}</div>}
                            <div className="text-xs font-medium text-slate-500 mt-auto pt-3 border-t border-slate-100">Performed by: {p.performing_doctor}</div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

              </div>
            </div>
          )}
        </div>
      </div>

      {/* MODALS */}
      {showDiagModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-base font-bold text-slate-800">Add Diagnosis</h2>
              <button onClick={() => setShowDiagModal(false)} className="text-slate-400 hover:text-slate-600">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Diagnosis Type</label>
                <select value={diagForm.diagnosis_type} onChange={e => setDiagForm({...diagForm, diagnosis_type: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                  <option>Provisional</option>
                  <option>Confirmed</option>
                  <option>Secondary</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">ICD-10 Code (Optional)</label>
                <input type="text" value={diagForm.icd10_code} onChange={e => setDiagForm({...diagForm, icd10_code: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" placeholder="e.g. K35" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Description</label>
                <textarea value={diagForm.description} onChange={e => setDiagForm({...diagForm, description: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" rows={3}></textarea>
              </div>
              <button onClick={submitDiagnosis} className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-sm transition-colors mt-2">Save Diagnosis</button>
            </div>
          </div>
        </div>
      )}

      {showTpModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-base font-bold text-slate-800">Add Treatment Directive</h2>
              <button onClick={() => setShowTpModal(false)} className="text-slate-400 hover:text-slate-600">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Therapy Type</label>
                <select value={tpForm.therapy_type} onChange={e => setTpForm({...tpForm, therapy_type: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                  <option>Medication</option>
                  <option>Investigation</option>
                  <option>Procedure</option>
                  <option>Supportive</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Instructions</label>
                <textarea value={tpForm.instructions} onChange={e => setTpForm({...tpForm, instructions: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" rows={4} placeholder="e.g. IV antibiotics for 5 days..."></textarea>
              </div>
              <button onClick={submitTreatment} className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-sm transition-colors mt-2">Add Directive</button>
            </div>
          </div>
        </div>
      )}

      {showPnModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-base font-bold text-slate-800">Dr. Progress Note</h2>
              <button onClick={() => setShowPnModal(false)} className="text-slate-400 hover:text-slate-600">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Clinical Observations & Updates</label>
                <textarea value={pnForm.notes} onChange={e => setPnForm({...pnForm, notes: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-3 outline-none focus:border-indigo-500 focus:ring-1 font-medium bg-amber-50/30" rows={6} placeholder="Patient condition stable. Tolerating oral diet well..."></textarea>
              </div>
              <button onClick={submitProgressNote} className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-sm transition-colors mt-2 text-center flex justify-center items-center gap-2"><Save size={16}/> Save Note</button>
            </div>
          </div>
        </div>
      )}

      {showProcModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
             <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-base font-bold text-slate-800">Record Clinical Procedure</h2>
              <button onClick={() => setShowProcModal(false)} className="text-slate-400 hover:text-slate-600">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Procedure Name</label>
                <input type="text" value={procForm.procedure_name} onChange={e => setProcForm({...procForm, procedure_name: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" placeholder="e.g. Central Line Insertion"/>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Date & Time</label>
                <input type="datetime-local" value={procForm.procedure_date} onChange={e => setProcForm({...procForm, procedure_date: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Clinical Notes / Findings</label>
                <textarea value={procForm.notes} onChange={e => setProcForm({...procForm, notes: e.target.value})} className="w-full text-sm border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" rows={3}></textarea>
              </div>
              <button onClick={submitProcedure} className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-sm transition-colors mt-2">Save Procedure Record</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
