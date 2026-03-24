"use client";

import React, { useEffect, useState, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Activity, Heart, ThermometerSun, Wind, Droplets,
  AlertTriangle, Shield, ClipboardList, TrendingUp,
  Plus, X, ChevronDown, Stethoscope, Brain,
  Apple, Eye, FileText, BarChart3
} from "lucide-react";
import { ipdApi } from "@/lib/ipd-api";

type VTab = "VITALS" | "ASSESSMENT" | "RISKS" | "OBSERVATIONS";

export default function NursingVitalsDashboard() {
  const [activeTab, setActiveTab] = useState<VTab>("VITALS");
  const [admissionNo, setAdmissionNo] = useState("");
  const [worklist, setWorklist] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<any>(null);

  // Vitals
  const [vitalsHistory, setVitalsHistory] = useState<any[]>([]);
  const [showVitalsModal, setShowVitalsModal] = useState(false);
  const [vitalsForm, setVitalsForm] = useState({
    temperature: "", pulse_rate: "", respiratory_rate: "",
    bp_systolic: "", bp_diastolic: "", spo2: "",
    height_cm: "", weight_kg: "", blood_glucose: "",
    pain_score: "", gcs_score: ""
  });

  // Assessment
  const [assessment, setAssessment] = useState<any>(null);
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [assessmentForm, setAssessmentForm] = useState({
    presenting_complaints: "", medical_history: "", surgical_history: "",
    allergy_information: "", medication_history: "", family_history: "",
    smoking_status: "Never", alcohol_consumption: "None", exercise_habits: ""
  });

  // Risks
  const [risks, setRisks] = useState<any[]>([]);
  const [showRiskModal, setShowRiskModal] = useState(false);
  const [riskForm, setRiskForm] = useState({ risk_type: "Fall Risk", risk_score: "", risk_level: "Low" });

  // Pain
  const [showPainModal, setShowPainModal] = useState(false);
  const [painForm, setPainForm] = useState({ pain_scale: "NRS", score: "", location: "", character: "" });

  // Nutrition
  const [showNutritionModal, setShowNutritionModal] = useState(false);
  const [nutritionForm, setNutritionForm] = useState({ bmi: "", dietary_habits: "Vegetarian", appetite_status: "Good", malnutrition_risk: "Low" });

  // Observations
  const [observations, setObservations] = useState<any[]>([]);
  const [showObsModal, setShowObsModal] = useState(false);
  const [obsForm, setObsForm] = useState({ observation_type: "General", note: "" });

  const fetchWorklist = useCallback(async () => {
    try {
      const wl = await ipdApi.getNursingWorklist();
      setWorklist(wl.filter((w: any) => w.status === "Accepted"));
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { fetchWorklist(); }, [fetchWorklist]);

  const selectPatient = async (w: any) => {
    setSelectedPatient(w);
    setAdmissionNo(w.admission_number);
    try {
      const [vitals, obs, riskList] = await Promise.all([
        ipdApi.getVitalsHistory(w.admission_number).catch(() => []),
        ipdApi.getObservations(w.admission_number).catch(() => []),
        ipdApi.getRiskAssessments(w.admission_number).catch(() => []),
      ]);
      setVitalsHistory(vitals);
      setObservations(obs);
      setRisks(riskList);
      try {
        const a = await ipdApi.getNursingAssessment(w.admission_number);
        setAssessment(a);
      } catch { setAssessment(null); }
    } catch (e) { console.error(e); }
  };

  const handleRecordVitals = async () => {
    if (!admissionNo) return;
    const payload: any = {};
    if (vitalsForm.temperature) payload.temperature = parseFloat(vitalsForm.temperature);
    if (vitalsForm.pulse_rate) payload.pulse_rate = parseInt(vitalsForm.pulse_rate);
    if (vitalsForm.respiratory_rate) payload.respiratory_rate = parseInt(vitalsForm.respiratory_rate);
    if (vitalsForm.bp_systolic) payload.bp_systolic = parseInt(vitalsForm.bp_systolic);
    if (vitalsForm.bp_diastolic) payload.bp_diastolic = parseInt(vitalsForm.bp_diastolic);
    if (vitalsForm.spo2) payload.spo2 = parseFloat(vitalsForm.spo2);
    if (vitalsForm.height_cm) payload.height_cm = parseFloat(vitalsForm.height_cm);
    if (vitalsForm.weight_kg) payload.weight_kg = parseFloat(vitalsForm.weight_kg);
    if (vitalsForm.blood_glucose) payload.blood_glucose = parseFloat(vitalsForm.blood_glucose);
    if (vitalsForm.pain_score) payload.pain_score = parseInt(vitalsForm.pain_score);
    if (vitalsForm.gcs_score) payload.gcs_score = parseInt(vitalsForm.gcs_score);
    try {
      const result = await ipdApi.recordVitals(admissionNo, payload);
      setVitalsHistory(prev => [result, ...prev]);
      setShowVitalsModal(false);
      setVitalsForm({ temperature: "", pulse_rate: "", respiratory_rate: "", bp_systolic: "", bp_diastolic: "", spo2: "", height_cm: "", weight_kg: "", blood_glucose: "", pain_score: "", gcs_score: "" });
    } catch (e) { console.error(e); }
  };

  const handleSaveAssessment = async () => {
    if (!admissionNo) return;
    try {
      const result = await ipdApi.saveNursingAssessment(admissionNo, assessmentForm);
      setAssessment(result);
      setShowAssessmentModal(false);
    } catch (e) { console.error(e); }
  };

  const handleAddRisk = async () => {
    if (!admissionNo) return;
    try {
      const payload = { ...riskForm, risk_score: riskForm.risk_score ? parseInt(riskForm.risk_score) : undefined };
      const result = await ipdApi.addRiskAssessment(admissionNo, payload);
      setRisks(prev => [result, ...prev]);
      setShowRiskModal(false);
      setRiskForm({ risk_type: "Fall Risk", risk_score: "", risk_level: "Low" });
    } catch (e) { console.error(e); }
  };

  const handleAddPain = async () => {
    if (!admissionNo || !painForm.score) return;
    try {
      const result = await ipdApi.addPainScore(admissionNo, { ...painForm, score: parseInt(painForm.score) });
      setShowPainModal(false);
      setPainForm({ pain_scale: "NRS", score: "", location: "", character: "" });
    } catch (e) { console.error(e); }
  };

  const handleAddNutrition = async () => {
    if (!admissionNo) return;
    try {
      const payload = { ...nutritionForm, bmi: nutritionForm.bmi ? parseFloat(nutritionForm.bmi) : undefined };
      await ipdApi.addNutritionAssessment(admissionNo, payload);
      setShowNutritionModal(false);
      setNutritionForm({ bmi: "", dietary_habits: "Vegetarian", appetite_status: "Good", malnutrition_risk: "Low" });
    } catch (e) { console.error(e); }
  };

  const handleAddObs = async () => {
    if (!admissionNo || !obsForm.note.trim()) return;
    try {
      const result = await ipdApi.addObservation(admissionNo, obsForm);
      setObservations(prev => [result, ...prev]);
      setShowObsModal(false);
      setObsForm({ observation_type: "General", note: "" });
    } catch (e) { console.error(e); }
  };

  const alertVitals = vitalsHistory.filter(v => v.alert_triggered);

  const getPainColor = (s: number) => s <= 3 ? "text-emerald-600" : s <= 6 ? "text-amber-600" : "text-red-600";
  const getRiskColor = (l: string) => l === "Low" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : l === "Moderate" ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-red-50 text-red-700 border-red-200";

  const renderTrendChart = (key: string, label: string, color: string, min: number, max: number) => {
    const data = [...vitalsHistory].reverse().filter(v => v[key] != null);
    if (data.length < 2) return null;
    return (
      <div className="bg-white border text-sm border-slate-200 rounded-xl p-4 flex-1">
        <div className="font-bold text-slate-600 truncate">{label} Trend</div>
        <div className="flex items-end gap-1 h-20 mt-4 border-b border-dashed border-slate-200 relative pb-1">
          {data.map((d, i) => {
            const val = d[key];
            const pct = Math.max(0, Math.min(100, ((val - min) / (max - min)) * 100));
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end cursor-pointer">
                <div className={`w-full rounded-t-sm ${color} opacity-70 hover:opacity-100 transition-all`} style={{ height: `${pct}%`, minHeight: '4px', maxWidth: '20px' }}></div>
                <div className="absolute bottom-full mb-1 bg-slate-800 text-white text-[10px] py-0.5 px-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                  {val}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/20 to-slate-100">
      <TopNav title="Vitals Monitoring" />
      <div className="max-w-[1600px] mx-auto px-8 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-slate-800 flex items-center gap-3">
              <div className="bg-gradient-to-br from-rose-500 to-red-600 text-white p-2.5 rounded-xl shadow-lg shadow-rose-200">
                <Activity size={24}/>
              </div>
              Nursing Assessment & Vitals Monitor
            </h1>
            <p className="text-slate-500 font-medium mt-1">Continuous patient monitoring, clinical assessments & risk tracking</p>
          </div>
        </div>

        <div className="grid grid-cols-[300px_1fr] gap-6">

          {/* LEFT: Patient Selector */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-500 uppercase">Accepted Patients</h3>
            <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-1">
              {worklist.length === 0 ? (
                <div className="bg-white border border-slate-200 rounded-xl p-6 text-center text-sm text-slate-400">No accepted patients</div>
              ) : worklist.map(w => (
                <button key={w.id} onClick={() => selectPatient(w)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    selectedPatient?.admission_number === w.admission_number
                      ? "bg-white border-blue-300 shadow-md shadow-blue-100"
                      : "bg-white/70 border-slate-200 hover:border-slate-300 hover:bg-white"
                  }`}>
                  <div className="font-mono text-xs font-bold text-blue-700">{w.admission_number}</div>
                  <div className="text-sm font-medium text-slate-700 mt-0.5">UHID: {w.patient_uhid}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Bed: {w.bed_number} • {w.ward_name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* RIGHT: Content Area */}
          <div>
            {!selectedPatient ? (
              <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center">
                <Activity size={56} className="text-slate-200 mx-auto mb-4"/>
                <h3 className="text-lg font-bold text-slate-600">Select a Patient</h3>
                <p className="text-sm text-slate-400 mt-1">Choose an accepted patient from the left panel to view vitals & assessments</p>
              </div>
            ) : (
              <>
                {/* Alert Banner */}
                {alertVitals.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 flex items-start gap-3">
                    <AlertTriangle size={20} className="text-red-600 mt-0.5 shrink-0"/>
                    <div>
                      <div className="text-sm font-bold text-red-700">⚠ Active Vitals Alerts</div>
                      {alertVitals.slice(0, 3).map(v => (
                        <div key={v.id} className="text-xs text-red-600 mt-1">{v.alert_message} — {new Date(v.recorded_at).toLocaleString()}</div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Stats Row */}
                <div className="grid grid-cols-5 gap-3 mb-6">
                  {[
                    { label: "Vitals Recorded", value: vitalsHistory.length, icon: <Heart size={14}/>, color: "text-rose-600" },
                    { label: "Alerts", value: alertVitals.length, icon: <AlertTriangle size={14}/>, color: "text-red-600" },
                    { label: "Risk Assessments", value: risks.length, icon: <Shield size={14}/>, color: "text-amber-600" },
                    { label: "Observations", value: observations.length, icon: <Eye size={14}/>, color: "text-indigo-600" },
                    { label: "Latest SpO2", value: vitalsHistory[0]?.spo2 ? `${vitalsHistory[0].spo2}%` : "—", icon: <Droplets size={14}/>, color: "text-blue-600" },
                  ].map((s, i) => (
                    <div key={i} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className={`text-[10px] font-bold uppercase flex items-center gap-1.5 ${s.color}`}>{s.icon} {s.label}</div>
                      <div className="text-2xl font-black text-slate-800 mt-1">{s.value}</div>
                    </div>
                  ))}
                </div>

                {/* Tabs */}
                <div className="flex gap-2 p-1.5 bg-white/50 backdrop-blur border border-slate-200 rounded-2xl w-fit mb-6 shadow-sm">
                  {([
                    { id: "VITALS", label: "Vitals", icon: <Heart size={15}/> },
                    { id: "ASSESSMENT", label: "Clinical Assessment", icon: <ClipboardList size={15}/> },
                    { id: "RISKS", label: "Risk & Pain", icon: <Shield size={15}/> },
                    { id: "OBSERVATIONS", label: "Observations", icon: <Eye size={15}/> },
                  ] as const).map(t => (
                    <button key={t.id} onClick={() => setActiveTab(t.id)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                        activeTab === t.id ? "bg-white text-blue-700 shadow-sm border border-slate-200/50" : "text-slate-500 hover:text-slate-700"
                      }`}>
                      {t.icon} {t.label}
                    </button>
                  ))}
                </div>

                {/* VITALS TAB */}
                {activeTab === "VITALS" && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-bold text-slate-600">Patient Vitals</h3>
                      <button onClick={() => setShowVitalsModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-bold shadow-sm shadow-rose-200 transition-colors">
                        <Plus size={16}/> Record Vitals
                      </button>
                    </div>

                    {vitalsHistory.filter(v => v.bp_systolic != null || v.temperature != null).length >= 2 && (
                      <div className="flex gap-4">
                        {renderTrendChart("bp_systolic", "Systolic BP", "bg-indigo-500", 80, 200)}
                        {renderTrendChart("temperature", "Temp °C", "bg-rose-500", 35, 41)}
                        {renderTrendChart("pulse_rate", "Heart Rate", "bg-amber-500", 40, 160)}
                        {renderTrendChart("spo2", "SpO2 %", "bg-blue-500", 85, 100)}
                      </div>
                    )}

                    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
                      <table className="w-full text-left border-collapse text-sm">
                        <thead>
                          <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-[10px] uppercase tracking-wider">
                            <th className="p-3 font-bold">Time</th>
                            <th className="p-3 font-bold">Temp °C</th>
                            <th className="p-3 font-bold">Pulse</th>
                            <th className="p-3 font-bold">RR</th>
                            <th className="p-3 font-bold">BP</th>
                            <th className="p-3 font-bold">SpO2</th>
                            <th className="p-3 font-bold">BMI</th>
                            <th className="p-3 font-bold">Glucose</th>
                            <th className="p-3 font-bold">Pain</th>
                            <th className="p-3 font-bold">Alert</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {vitalsHistory.length === 0 ? (
                            <tr><td colSpan={10} className="p-8 text-center text-slate-400 font-medium">No vitals recorded yet</td></tr>
                          ) : vitalsHistory.map(v => (
                            <tr key={v.id} className={`hover:bg-slate-50/50 ${v.alert_triggered ? "bg-red-50/40" : ""}`}>
                              <td className="p-3 text-slate-600 text-xs">{new Date(v.recorded_at).toLocaleString()}</td>
                              <td className="p-3 font-bold">{v.temperature ?? "—"}</td>
                              <td className="p-3 font-bold">{v.pulse_rate ?? "—"}</td>
                              <td className="p-3 font-bold">{v.respiratory_rate ?? "—"}</td>
                              <td className="p-3 font-bold">{v.bp_systolic && v.bp_diastolic ? `${v.bp_systolic}/${v.bp_diastolic}` : "—"}</td>
                              <td className={`p-3 font-bold ${v.spo2 && v.spo2 < 92 ? "text-red-600" : ""}`}>{v.spo2 ? `${v.spo2}%` : "—"}</td>
                              <td className="p-3">{v.bmi ?? "—"}</td>
                              <td className="p-3">{v.blood_glucose ?? "—"}</td>
                              <td className={`p-3 font-bold ${v.pain_score != null ? getPainColor(v.pain_score) : ""}`}>{v.pain_score != null ? `${v.pain_score}/10` : "—"}</td>
                              <td className="p-3">{v.alert_triggered ? <span className="text-[10px] font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">⚠ ALERT</span> : <span className="text-emerald-500 text-xs">OK</span>}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* ASSESSMENT TAB */}
                {activeTab === "ASSESSMENT" && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-bold text-slate-600">Initial Nursing Assessment</h3>
                      <button onClick={() => { if (assessment) setAssessmentForm(assessment); setShowAssessmentModal(true); }}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow-sm transition-colors">
                        <ClipboardList size={16}/> {assessment ? "Update" : "Create"} Assessment
                      </button>
                    </div>
                    {assessment ? (
                      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                        <div className="grid grid-cols-2 gap-6 text-sm">
                          {[
                            { label: "Presenting Complaints", value: assessment.presenting_complaints },
                            { label: "Medical History", value: assessment.medical_history },
                            { label: "Surgical History", value: assessment.surgical_history },
                            { label: "Allergy Information", value: assessment.allergy_information },
                            { label: "Medication History", value: assessment.medication_history },
                            { label: "Family History", value: assessment.family_history },
                          ].map(f => (
                            <div key={f.label}>
                              <div className="text-[10px] font-bold text-slate-400 uppercase mb-1">{f.label}</div>
                              <div className="text-slate-700 font-medium">{f.value || "—"}</div>
                            </div>
                          ))}
                        </div>
                        <div className="border-t border-slate-100 pt-4 grid grid-cols-3 gap-4 text-sm">
                          <div><span className="text-slate-400 text-xs font-bold">Smoking:</span> <span className="font-medium ml-1">{assessment.smoking_status || "—"}</span></div>
                          <div><span className="text-slate-400 text-xs font-bold">Alcohol:</span> <span className="font-medium ml-1">{assessment.alcohol_consumption || "—"}</span></div>
                          <div><span className="text-slate-400 text-xs font-bold">Exercise:</span> <span className="font-medium ml-1">{assessment.exercise_habits || "—"}</span></div>
                        </div>
                        <div className="text-[11px] text-slate-400">Assessed by: {assessment.assessed_by_name} • {assessment.assessed_at ? new Date(assessment.assessed_at).toLocaleString() : ""}</div>
                      </div>
                    ) : (
                      <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center text-slate-400 text-sm">
                        No assessment recorded yet. Click "Create Assessment" to begin.
                      </div>
                    )}
                    {/* Quick actions */}
                    <div className="grid grid-cols-2 gap-3">
                      <button onClick={() => setShowNutritionModal(true)} className="bg-white border border-slate-200 rounded-xl p-4 text-left hover:border-green-300 hover:bg-green-50/30 transition-all">
                        <div className="flex items-center gap-2 text-sm font-bold text-green-700"><Apple size={16}/> Nutrition Assessment</div>
                        <div className="text-xs text-slate-400 mt-1">BMI, dietary habits, malnutrition risk</div>
                      </button>
                      <button onClick={() => setShowPainModal(true)} className="bg-white border border-slate-200 rounded-xl p-4 text-left hover:border-orange-300 hover:bg-orange-50/30 transition-all">
                        <div className="flex items-center gap-2 text-sm font-bold text-orange-700"><ThermometerSun size={16}/> Pain Assessment</div>
                        <div className="text-xs text-slate-400 mt-1">NRS scale, pain location & character</div>
                      </button>
                    </div>
                  </div>
                )}

                {/* RISKS TAB */}
                {activeTab === "RISKS" && (
                  <div className="space-y-4">
                    <div className="flex justify-end">
                      <button onClick={() => setShowRiskModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-sm font-bold shadow-sm transition-colors">
                        <Plus size={16}/> Add Risk Assessment
                      </button>
                    </div>
                    {risks.length === 0 ? (
                      <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center text-slate-400 text-sm">No risk assessments recorded</div>
                    ) : (
                      <div className="grid grid-cols-2 gap-3">
                        {risks.map(r => (
                          <div key={r.id} className={`border rounded-xl p-4 shadow-sm ${getRiskColor(r.risk_level)}`}>
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-bold text-sm">{r.risk_type}</div>
                                <div className="text-xs mt-1">Score: {r.risk_score ?? "—"} • Level: <span className="font-bold">{r.risk_level}</span></div>
                              </div>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getRiskColor(r.risk_level)}`}>{r.risk_level}</span>
                            </div>
                            <div className="text-[11px] mt-2 opacity-70">{r.assessed_by_name} • {new Date(r.assessed_at).toLocaleString()}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* OBSERVATIONS TAB */}
                {activeTab === "OBSERVATIONS" && (
                  <div className="space-y-4">
                    <div className="flex justify-end">
                      <button onClick={() => setShowObsModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow-sm transition-colors">
                        <Plus size={16}/> Add Observation
                      </button>
                    </div>
                    {observations.length === 0 ? (
                      <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center text-slate-400 text-sm">No observations recorded</div>
                    ) : (
                      <div className="space-y-2">
                        {observations.map(o => (
                          <div key={o.id} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${o.observation_type === "Critical" ? "bg-red-50 text-red-700 border-red-200" : o.observation_type === "Shift Handover" ? "bg-blue-50 text-blue-700 border-blue-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}>{o.observation_type}</span>
                              <span className="text-[11px] text-slate-400">{new Date(o.recorded_at).toLocaleString()}</span>
                            </div>
                            <div className="text-sm text-slate-700">{o.note}</div>
                            <div className="text-[11px] text-slate-400 mt-1">— {o.recorded_by_name}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* VITALS MODAL */}
      {showVitalsModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Heart size={20} className="text-rose-600"/> Record Vitals</h3>
              <button onClick={() => setShowVitalsModal(false)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { key: "temperature", label: "Temperature (°C)", ph: "e.g. 37.2" },
                { key: "pulse_rate", label: "Pulse Rate (bpm)", ph: "e.g. 78" },
                { key: "respiratory_rate", label: "Respiratory Rate", ph: "e.g. 18" },
                { key: "bp_systolic", label: "BP Systolic (mmHg)", ph: "e.g. 120" },
                { key: "bp_diastolic", label: "BP Diastolic (mmHg)", ph: "e.g. 80" },
                { key: "spo2", label: "SpO2 (%)", ph: "e.g. 98" },
                { key: "height_cm", label: "Height (cm)", ph: "e.g. 170" },
                { key: "weight_kg", label: "Weight (kg)", ph: "e.g. 72" },
                { key: "blood_glucose", label: "Blood Glucose (mg/dL)", ph: "e.g. 110" },
                { key: "pain_score", label: "Pain Score (0-10)", ph: "e.g. 3" },
                { key: "gcs_score", label: "GCS Score (3-15)", ph: "e.g. 15" },
              ].map(f => (
                <div key={f.key}>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{f.label}</label>
                  <input value={(vitalsForm as any)[f.key]} onChange={e => setVitalsForm({...vitalsForm, [f.key]: e.target.value})}
                    placeholder={f.ph} className="w-full p-2 border border-slate-300 rounded-lg text-sm outline-none focus:border-rose-500 mt-1"/>
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowVitalsModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg">Cancel</button>
              <button onClick={handleRecordVitals} className="px-5 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-bold shadow-sm">Save Vitals</button>
            </div>
          </div>
        </div>
      )}

      {/* ASSESSMENT MODAL */}
      {showAssessmentModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><ClipboardList size={20} className="text-indigo-600"/> Nursing Assessment</h3>
              <button onClick={() => setShowAssessmentModal(false)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>
            <div className="space-y-3">
              {[
                { key: "presenting_complaints", label: "Presenting Complaints" },
                { key: "medical_history", label: "Medical History" },
                { key: "surgical_history", label: "Surgical History" },
                { key: "allergy_information", label: "Allergy Information" },
                { key: "medication_history", label: "Medication History" },
                { key: "family_history", label: "Family History" },
              ].map(f => (
                <div key={f.key}>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{f.label}</label>
                  <textarea value={(assessmentForm as any)[f.key]} onChange={e => setAssessmentForm({...assessmentForm, [f.key]: e.target.value})}
                    rows={2} className="w-full p-2 border border-slate-300 rounded-lg text-sm outline-none focus:border-indigo-500 mt-1 resize-none"/>
                </div>
              ))}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Smoking</label>
                  <select value={assessmentForm.smoking_status} onChange={e => setAssessmentForm({...assessmentForm, smoking_status: e.target.value})}
                    className="w-full p-2 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                    <option>Never</option><option>Former</option><option>Current</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Alcohol</label>
                  <select value={assessmentForm.alcohol_consumption} onChange={e => setAssessmentForm({...assessmentForm, alcohol_consumption: e.target.value})}
                    className="w-full p-2 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                    <option>None</option><option>Occasional</option><option>Regular</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Exercise</label>
                  <input value={assessmentForm.exercise_habits} onChange={e => setAssessmentForm({...assessmentForm, exercise_habits: e.target.value})}
                    placeholder="e.g. Daily walking" className="w-full p-2 border border-slate-300 rounded-lg text-sm mt-1 outline-none"/>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowAssessmentModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg">Cancel</button>
              <button onClick={handleSaveAssessment} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold">Save Assessment</button>
            </div>
          </div>
        </div>
      )}

      {/* RISK MODAL */}
      {showRiskModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Shield size={20} className="text-amber-600"/> Risk Assessment</h3>
              <button onClick={() => setShowRiskModal(false)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Risk Type</label>
                <select value={riskForm.risk_type} onChange={e => setRiskForm({...riskForm, risk_type: e.target.value})}
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                  <option>Fall Risk</option><option>Pressure Ulcer</option><option>Infection Risk</option><option>Mobility Assessment</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Score</label>
                <input value={riskForm.risk_score} onChange={e => setRiskForm({...riskForm, risk_score: e.target.value})}
                  placeholder="e.g. 7" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none"/>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Risk Level</label>
                <select value={riskForm.risk_level} onChange={e => setRiskForm({...riskForm, risk_level: e.target.value})}
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                  <option>Low</option><option>Moderate</option><option>High</option><option>Critical</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowRiskModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button onClick={handleAddRisk} className="px-5 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-sm font-bold">Add Risk</button>
            </div>
          </div>
        </div>
      )}

      {/* PAIN MODAL */}
      {showPainModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><ThermometerSun size={20} className="text-orange-600"/> Pain Assessment</h3>
              <button onClick={() => setShowPainModal(false)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Scale</label>
                  <select value={painForm.pain_scale} onChange={e => setPainForm({...painForm, pain_scale: e.target.value})}
                    className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                    <option value="NRS">NRS (0-10)</option><option value="VAS">VAS</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Score (0-10)</label>
                  <input type="number" min="0" max="10" value={painForm.score} onChange={e => setPainForm({...painForm, score: e.target.value})}
                    className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none"/>
                </div>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Location</label>
                <input value={painForm.location} onChange={e => setPainForm({...painForm, location: e.target.value})}
                  placeholder="e.g. Lower abdomen" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none"/>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Character</label>
                <select value={painForm.character} onChange={e => setPainForm({...painForm, character: e.target.value})}
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                  <option value="">Select...</option><option>Sharp</option><option>Dull</option><option>Burning</option><option>Aching</option><option>Throbbing</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowPainModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button onClick={handleAddPain} disabled={!painForm.score} className="px-5 py-2.5 bg-orange-600 hover:bg-orange-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-bold">Record Pain</button>
            </div>
          </div>
        </div>
      )}

      {/* NUTRITION MODAL */}
      {showNutritionModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Apple size={20} className="text-green-600"/> Nutrition Assessment</h3>
              <button onClick={() => setShowNutritionModal(false)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">BMI</label>
                <input value={nutritionForm.bmi} onChange={e => setNutritionForm({...nutritionForm, bmi: e.target.value})} placeholder="e.g. 24.5"
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none"/>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Dietary Habits</label>
                  <select value={nutritionForm.dietary_habits} onChange={e => setNutritionForm({...nutritionForm, dietary_habits: e.target.value})}
                    className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                    <option>Vegetarian</option><option>Non-Vegetarian</option><option>Vegan</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase">Appetite</label>
                  <select value={nutritionForm.appetite_status} onChange={e => setNutritionForm({...nutritionForm, appetite_status: e.target.value})}
                    className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                    <option>Good</option><option>Poor</option><option>Anorexia</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Malnutrition Risk</label>
                <select value={nutritionForm.malnutrition_risk} onChange={e => setNutritionForm({...nutritionForm, malnutrition_risk: e.target.value})}
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                  <option>Low</option><option>Moderate</option><option>High</option>
                </select>
                {nutritionForm.malnutrition_risk === "High" && (
                  <div className="text-[11px] text-amber-600 font-bold mt-1">⚠ Dietician services will be notified automatically</div>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowNutritionModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button onClick={handleAddNutrition} className="px-5 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-bold">Save Nutrition</button>
            </div>
          </div>
        </div>
      )}

      {/* OBSERVATION MODAL */}
      {showObsModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Eye size={20} className="text-indigo-600"/> Add Observation</h3>
              <button onClick={() => setShowObsModal(false)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Type</label>
                <select value={obsForm.observation_type} onChange={e => setObsForm({...obsForm, observation_type: e.target.value})}
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none">
                  <option>General</option><option>Critical</option><option>Shift Handover</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Note</label>
                <textarea value={obsForm.note} onChange={e => setObsForm({...obsForm, note: e.target.value})}
                  rows={4} placeholder="e.g. Patient resting comfortably, vitals stable..."
                  className="w-full p-2.5 border border-slate-300 rounded-lg text-sm mt-1 outline-none resize-none"/>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowObsModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button onClick={handleAddObs} disabled={!obsForm.note.trim()} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-bold">Save Observation</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
