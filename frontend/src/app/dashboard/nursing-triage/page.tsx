"use client";

import React, { useState, useEffect } from "react";
import { 
  nursingTriageApi, type NursingWorklist, type NursingVitals, type NursingAssessment
} from "@/lib/nursing-triage-api";
import {
  Stethoscope, Activity, ClipboardList, Thermometer, Droplet, 
  UploadCloud, AlertTriangle, HeartPulse, Clock, CheckCircle, Search
} from "lucide-react";
import { api } from "@/lib/api";

type TabTypes = "worklist" | "triage" | "doctor_view";

export default function NursingTriagePage() {
  const [activeTab, setActiveTab] = useState<TabTypes>("worklist");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [patients, setPatients] = useState<any[]>([]);
  const [worklist, setWorklist] = useState<NursingWorklist[]>([]);
  const [activePatient, setActivePatient] = useState<any | null>(null);
  const [simPatientId, setSimPatientId] = useState("");
  
  // Vitals State
  const [vitalsData, setVitalsData] = useState({
    blood_pressure_systolic: "", blood_pressure_diastolic: "",
    heart_rate: "", respiratory_rate: "", temperature_celsius: "",
    oxygen_saturation_spo2: "", height_cm: "", weight_kg: "",
    blood_glucose: "", pain_score: ""
  });
  const [abnormalAlert, setAbnormalAlert] = useState<string | null>(null);

  // Template State
  const [assessmentData, setAssessmentData] = useState({
    chief_complaint: "", allergy_information: "", past_medical_history: "",
    medication_history: "", family_history: "", nursing_observations: ""
  });

  // Upload State
  const [docType, setDocType] = useState("lab");
  const [fileName, setFileName] = useState("");

  useEffect(() => {
    loadBaseData();
  }, []);

  const loadBaseData = async () => {
    setLoading(true);
    try {
      const p = await api.get<any>("/patients/");
      setPatients(Array.isArray(p) ? p : p?.items || []);
      const wl = await nursingTriageApi.getWorklist();
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

  const seedWorklist = async () => {
    if (patients.length === 0) return alert("Add patients first");
    const targetId = simPatientId || patients[Math.max(0, patients.length - 1)].id;
    try {
      await nursingTriageApi.addWorklist({
        visit_id: "00000000-0000-0000-0000-000000000000",
        patient_id: targetId,
        priority_level: "normal"
      });
      loadBaseData();
    } catch (e: any) { setError(e.message); }
  };

  // ── Worklist Actions ──────────────────────────
  const startTriage = async (wl: NursingWorklist) => {
    try {
      await nursingTriageApi.updateStatus(wl.id, "in_progress");
      setActivePatient({ ...wl, name: getPatientName(wl.patient_id), uhid: getPatientUhid(wl.patient_id) });
      setActiveTab("triage");
      loadBaseData();
    } catch (e: any) { setError(e.message); }
  };

  // ── Vitals Engine Actions ───────────────────────
  const fetchDeviceData = () => {
    setVitalsData(prev => ({
      ...prev,
      blood_pressure_systolic: "185", // Auto-fill with high BP for alert test
      blood_pressure_diastolic: "115",
      heart_rate: "105",
      oxygen_saturation_spo2: "90", // Low O2
      temperature_celsius: "37.1"
    }));
  };

  const submitVitals = async () => {
    if (!activePatient) return;
    try {
      const res = await nursingTriageApi.recordVitals({
        visit_id: activePatient.visit_id,
        patient_id: activePatient.patient_id,
        blood_pressure_systolic: vitalsData.blood_pressure_systolic ? Number(vitalsData.blood_pressure_systolic) : undefined,
        blood_pressure_diastolic: vitalsData.blood_pressure_diastolic ? Number(vitalsData.blood_pressure_diastolic) : undefined,
        heart_rate: vitalsData.heart_rate ? Number(vitalsData.heart_rate) : undefined,
        respiratory_rate: vitalsData.respiratory_rate ? Number(vitalsData.respiratory_rate) : undefined,
        temperature_celsius: vitalsData.temperature_celsius ? Number(vitalsData.temperature_celsius) : undefined,
        oxygen_saturation_spo2: vitalsData.oxygen_saturation_spo2 ? Number(vitalsData.oxygen_saturation_spo2) : undefined,
        height_cm: vitalsData.height_cm ? Number(vitalsData.height_cm) : undefined,
        weight_kg: vitalsData.weight_kg ? Number(vitalsData.weight_kg) : undefined,
      });
      alert(`Vitals registered successfully! Calculated BMI: ${res.bmi || 'N/A'}`);
      
      // Local abnormal mock check for UI
      if (res.oxygen_saturation_spo2 && res.oxygen_saturation_spo2 < 92) {
        setAbnormalAlert("Abnormal Vitals Detected: SpO2 < 92%. Visit Priority Automatically Escalated.");
      }
    } catch (e: any) { setError(e.message); }
  };

  const submitAssessment = async () => {
    if (!activePatient) return;
    try {
      await nursingTriageApi.recordAssessment({
        visit_id: activePatient.visit_id,
        patient_id: activePatient.patient_id,
        template_used: "General Nursing Assessment",
        ...assessmentData
      });
      alert("Clinical history captured and bound to patient timeline.");
    } catch (e: any) { setError(e.message); }
  };

  const submitUpload = async () => {
    if (!activePatient || !fileName) return;
    try {
      await nursingTriageApi.uploadDocument({
        visit_id: activePatient.visit_id,
        patient_id: activePatient.patient_id,
        document_type: docType,
        file_path: `/storage/${fileName}`,
        file_format: "pdf"
      });
      alert("Document verified and attached to EHR repostiory.");
    } catch (e: any) { setError(e.message); }
  };

  const completeTriageProcess = async () => {
    if (!activePatient) return;
    try {
      await nursingTriageApi.updateStatus(activePatient.id, "completed");
      setActivePatient(null);
      setActiveTab("worklist");
      loadBaseData();
      alert("Triage Completed. Real-time Doctor Notification dispatched.");
    } catch(e: any) { setError(e.message); }
  };

  // ── Render ──────────────────────────
  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3 text-slate-800">
            <Stethoscope className="text-teal-600" size={32} />
            Opd Nursing Triage Engine
          </h1>
          <p className="text-slate-500 mt-1">Record vitals, perform clinical templates, and detect risks automatically.</p>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-center gap-2"><AlertTriangle size={18} /> {error}</div>}

      <div className="flex bg-white rounded-lg p-1 shadow-sm w-fit border border-slate-200">
        {[
          { id: "worklist", icon: ClipboardList, label: "Worklist Dashboard" },
          { id: "triage", icon: Activity, label: "Active Triage" },
          { id: "doctor_view", icon: HeartPulse, label: "Doctor Context Viewer" }
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as TabTypes)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium transition-all ${
              activeTab === t.id ? "bg-teal-50 text-teal-700 border-teal-100 shadow-sm" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* ═ WORKLIST DASHBOARD ═ */}
      {activeTab === "worklist" && (
        <div className="card p-0 overflow-hidden border border-slate-200">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
            <h3 className="font-bold text-slate-700">Patients Pending Triage</h3>
            <div className="flex items-center gap-2">
              <select className="border border-slate-300 rounded text-xs px-2 py-1.5 focus:border-teal-500 focus:outline-none" value={simPatientId} onChange={e => setSimPatientId(e.target.value)}>
                <option value="">Latest Patient</option>
                {patients.slice().reverse().map(p => (
                  <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
                ))}
              </select>
              <button onClick={seedWorklist} className="btn-secondary text-xs border border-slate-300">Simulate Patient Arrival</button>
            </div>
          </div>
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-semibold border-b">
              <tr>
                <th className="px-6 py-4">UHID</th>
                <th className="px-6 py-4">Patient Name</th>
                <th className="px-6 py-4">Priority Tag</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {worklist.length === 0 ? (
                <tr><td colSpan={5} className="p-8 text-center text-slate-400">No patients waiting in queue.</td></tr>
              ) : worklist.map((wl) => (
                <tr key={wl.id} className="border-b hover:bg-slate-50">
                  <td className="px-6 py-4 font-mono">{getPatientUhid(wl.patient_id)}</td>
                  <td className="px-6 py-4 font-bold text-slate-700">{getPatientName(wl.patient_id)}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${
                      wl.priority_level === 'emergency' ? 'bg-rose-100 text-rose-700' :
                      wl.priority_level === 'priority' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {wl.priority_level}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs border ${
                      wl.triage_status === 'completed' ? 'border-emerald-200 text-emerald-700 bg-emerald-50' :
                      wl.triage_status === 'in_progress' ? 'border-blue-200 text-blue-700 bg-blue-50' : 'border-slate-200'
                    }`}>
                      {wl.triage_status.replace('_',' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {wl.triage_status !== 'completed' && (
                      <button onClick={() => startTriage(wl)} className="btn-primary text-xs bg-teal-600 hover:bg-teal-700">Start Triage</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ═ ACTIVE TRIAGE DASHBOARD ═ */}
      {activeTab === "triage" && (
        !activePatient ? (
           <div className="card p-12 text-center text-slate-400">Please select a patient from the Worklist Dashboard.</div>
        ) : (
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12">
              <div className="bg-teal-700 text-white p-6 rounded-xl flex justify-between items-center shadow-md">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                    <CheckCircle size={32} className="text-white"/>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">{activePatient.name}</h2>
                    <p className="text-teal-100 mt-1">UHID: {activePatient.uhid} | Triage Active Timestamp: {new Date().toLocaleTimeString()}</p>
                  </div>
                </div>
                <button onClick={completeTriageProcess} className="bg-emerald-500 hover:bg-emerald-400 text-white font-bold py-3 px-6 rounded-lg shadow-sm border border-emerald-400">
                  Complete Triage & Notify Doctor
                </button>
              </div>
            </div>

            {/* Vitals Panel */}
            <div className="col-span-4 space-y-6">
              <div className="card p-6 border-slate-200 shadow-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10"><Activity size={64}/></div>
                <h3 className="font-bold text-lg text-slate-800 mb-4 flex justify-between items-center z-10 relative">
                  Clinical Vitals
                  <button onClick={fetchDeviceData} className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1 rounded font-medium border border-indigo-100 hover:bg-indigo-100 flex items-center gap-1">
                    <HeartPulse size={12}/> Pull from Devices
                  </button>
                </h3>
                
                {abnormalAlert && (
                  <div className="mb-4 bg-rose-50 border border-rose-200 text-rose-700 p-3 rounded text-sm font-bold flex items-start gap-2">
                    <AlertTriangle size={18} className="shrink-0 mt-0.5"/>
                    {abnormalAlert}
                  </div>
                )}
                
                <div className="grid grid-cols-2 gap-4 relative z-10">
                  <div><label className="text-xs font-bold text-slate-500 uppercase">SYS BP (mmHg)</label><input type="number" className="input-field mt-1" value={vitalsData.blood_pressure_systolic} onChange={e=>setVitalsData({...vitalsData, blood_pressure_systolic: e.target.value})}/></div>
                  <div><label className="text-xs font-bold text-slate-500 uppercase">DIA BP (mmHg)</label><input type="number" className="input-field mt-1" value={vitalsData.blood_pressure_diastolic} onChange={e=>setVitalsData({...vitalsData, blood_pressure_diastolic: e.target.value})}/></div>
                  <div><label className="text-xs font-bold text-slate-500 uppercase">Heart Rate</label><input type="number" className="input-field mt-1" value={vitalsData.heart_rate} onChange={e=>setVitalsData({...vitalsData, heart_rate: e.target.value})}/></div>
                  <div><label className="text-xs font-bold text-rose-500 uppercase">SpO2 (%)</label><input type="number" className="input-field mt-1 border-rose-200 focus:border-rose-400" value={vitalsData.oxygen_saturation_spo2} onChange={e=>setVitalsData({...vitalsData, oxygen_saturation_spo2: e.target.value})}/></div>
                  <div><label className="text-xs font-bold text-slate-500 uppercase">Temp. (°C)</label><input type="number" className="input-field mt-1" value={vitalsData.temperature_celsius} onChange={e=>setVitalsData({...vitalsData, temperature_celsius: e.target.value})}/></div>
                  <div><label className="text-xs font-bold text-slate-500 uppercase">Resp. Rate</label><input type="number" className="input-field mt-1" value={vitalsData.respiratory_rate} onChange={e=>setVitalsData({...vitalsData, respiratory_rate: e.target.value})}/></div>
                  <div><label className="text-xs font-bold text-slate-500 uppercase">Weight (kg)</label><input type="number" className="input-field mt-1" value={vitalsData.weight_kg} onChange={e=>setVitalsData({...vitalsData, weight_kg: e.target.value})}/></div>
                  <div><label className="text-xs font-bold text-slate-500 uppercase">Height (cm)</label><input type="number" className="input-field mt-1" value={vitalsData.height_cm} onChange={e=>setVitalsData({...vitalsData, height_cm: e.target.value})}/></div>
                </div>
                <button onClick={submitVitals} className="btn-secondary w-full mt-6 flex justify-center items-center gap-2 border-slate-300">
                   <Thermometer size={16}/> Record & Evaluate Risk
                </button>
              </div>

              {/* Document upload box */}
              <div className="card p-5 border-slate-200 border-dashed bg-slate-50">
                 <h4 className="font-bold text-slate-700 mb-2 flex items-center gap-2"><UploadCloud size={16}/> External Documents</h4>
                 <div className="space-y-3">
                    <select className="input-field" value={docType} onChange={e=>setDocType(e.target.value)}>
                      <option value="lab">Outside Lab Report (PDF)</option>
                      <option value="radiology">Imaging CD (DICOM Link)</option>
                      <option value="prescription">Old Prescription</option>
                    </select>
                    <input type="text" className="input-field" placeholder="Upload file trace/name" value={fileName} onChange={e=>setFileName(e.target.value)}/>
                    <button onClick={submitUpload} className="btn-primary w-full bg-slate-800 text-white">Attach to Chart</button>
                 </div>
              </div>
            </div>

            {/* Assessment Panel */}
            <div className="col-span-8">
              <div className="card p-6 h-full shadow-sm">
                <h3 className="font-bold text-lg text-slate-800 mb-6 flex justify-between items-center border-b pb-4">
                  Clinical History & Nursing Assessment
                  <span className="badge bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs">General Template</span>
                </h3>
                
                <div className="space-y-5">
                  <div>
                    <label className="text-sm font-bold text-slate-700 mb-1 block">Chief Complaint (Reason for Visit)</label>
                    <textarea className="input-field min-h-[80px]" value={assessmentData.chief_complaint} onChange={e=>setAssessmentData({...assessmentData, chief_complaint: e.target.value})} placeholder="e.g. Chest pain radiating to left arm..."/>
                  </div>
                  <div className="grid grid-cols-2 gap-5">
                    <div>
                      <label className="text-sm font-bold text-slate-700 mb-1 block">Allergies</label>
                      <input type="text" className="input-field" value={assessmentData.allergy_information} onChange={e=>setAssessmentData({...assessmentData, allergy_information: e.target.value})} placeholder="e.g. Penicillin"/>
                    </div>
                    <div>
                      <label className="text-sm font-bold text-slate-700 mb-1 block">Current Medications</label>
                      <input type="text" className="input-field" value={assessmentData.medication_history} onChange={e=>setAssessmentData({...assessmentData, medication_history: e.target.value})} placeholder="Medications brought by patient"/>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-bold text-slate-700 mb-1 block">Past Medical History / Surgeries</label>
                    <textarea className="input-field min-h-[60px]" value={assessmentData.past_medical_history} onChange={e=>setAssessmentData({...assessmentData, past_medical_history: e.target.value})} placeholder="Chronic conditions, past surgeries..."/>
                  </div>
                  <div>
                    <label className="text-sm font-bold text-slate-700 mb-1 block">Nursing Observations (Triage Notes)</label>
                    <textarea className="input-field min-h-[60px] bg-amber-50" value={assessmentData.nursing_observations} onChange={e=>setAssessmentData({...assessmentData, nursing_observations: e.target.value})} placeholder="Any additional contextual risk identifiers observed..."/>
                  </div>
                  <button onClick={submitAssessment} className="btn-primary bg-indigo-600 hover:bg-indigo-700 px-8 ml-auto block">Save Clinical History</button>
                </div>
              </div>
            </div>

          </div>
        )
      )}

      {/* ═ DOCTOR DASHBOARD VIEW ═ */}
      {activeTab === "doctor_view" && (
        <div className="card p-12 bg-slate-900 text-white rounded-2xl shadow-2xl relative overflow-hidden">
          <div className="text-center mb-8 pb-8 border-b border-slate-700 relative z-10">
            <HeartPulse size={48} className="mx-auto text-rose-500 mb-4" />
            <h2 className="text-3xl font-black">Doctor Console Context Preview</h2>
            <p className="text-slate-400 mt-2">When triage completes, this highly structured timeline payload is passed to the doctor.</p>
          </div>
          <div className="text-center text-slate-300">
             <Search size={32} className="mx-auto text-slate-500 mb-4 opacity-50"/>
             <span className="font-mono text-xs block opacity-50">GET /api/v1/nursing-triage/doctor-context/{'{visit_id}'}</span>
          </div>
        </div>
      )}
    </div>
  );
}
