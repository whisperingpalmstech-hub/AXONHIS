"use client";

import React, { useState, useEffect } from "react";
import { 
  smartQueueApi, type QueueMaster, type QueuePosition, 
  type DigitalSignageDisplay, type CrowdPredictionSnapshot 
} from "@/lib/smart-queue-api";
import {
  Users, MonitorPlay, Compass, RefreshCw, AlertCircle, Map, 
  Clock, TrendingUp, Bell, ArrowRight, UserMinus, Search, Activity
} from "lucide-react";
import { api } from "@/lib/api";
import { useTranslation } from "@/i18n";

type TabTypes = "orchestrator" | "signage" | "wayfinding" | "ai_crowd";

export default function SmartQueuePage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabTypes>("orchestrator");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [doctors, setDoctors] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);

  // Orchestrator State
  const [selectedDept, setSelectedDept] = useState("Cardiology");
  const [queueMaster, setQueueMaster] = useState<QueueMaster | null>(null);
  const [routingRec, setRoutingRec] = useState<any>(null);
  const [mockPatientId, setMockPatientId] = useState("");

  // Signage State
  const [signageData, setSignageData] = useState<DigitalSignageDisplay | null>(null);

  // Wayfinding State
  const [wayfindingTarget, setWayfindingTarget] = useState("203");
  const [wayfindingInstr, setWayfindingInstr] = useState("");

  // Crowd AI State
  const [crowdAI, setCrowdAI] = useState<CrowdPredictionSnapshot | null>(null);

  useEffect(() => {
    loadBaseData();
  }, []);

  const loadBaseData = async () => {
    try {
      const d = await api.get<any>("/auth/users");
      setDoctors(Array.isArray(d) ? d : d?.items || []);
      const p = await api.get<any>("/patients");
      setPatients(Array.isArray(p) ? p : p?.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  // ── 1. Orchestrator Actions ─────────────────────────────────────
  const initializeQueue = async () => {
    setLoading(true); setError("");
    try {
      const qm = await smartQueueApi.createQueue({
        doctor_id: doctors[0]?.id || null, // Mocking first doctor
        department: selectedDept,
        room_number: "Room 101",
        room_status: "open"
      });
      setQueueMaster(qm);

      const routing = await smartQueueApi.getRoutingRecommendation(selectedDept);
      setRoutingRec(routing);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  const addPatientToQueue = async (priority: string) => {
    if (!queueMaster || !mockPatientId) return;
    setLoading(true); setError("");
    try {
      await smartQueueApi.addToQueue({
        queue_id: queueMaster.id,
        visit_id: crypto.randomUUID(), // Would be linked in real integration
        patient_id: mockPatientId,
        priority_level: priority
      });
      alert(t("smartQueue.patientAddedQueue", { priority: priority.toUpperCase() }));
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  // ── 2. Signage Actions ──────────────────────────────────────────
  const fetchSignage = async () => {
    if (!queueMaster) {
      setError(t("smartQueue.initQueueError"));
      setActiveTab("orchestrator");
      return;
    }
    setLoading(true); setError("");
    try {
      const data = await smartQueueApi.getDigitalSignage(queueMaster.id);
      setSignageData(data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  // ── 3. Wayfinding Actions ───────────────────────────────────────
  const fetchWayfinding = async () => {
    if (!wayfindingTarget) return;
    setLoading(true); setError("");
    try {
      const data = await smartQueueApi.getWayfinding(wayfindingTarget);
      setWayfindingInstr(data.instructions);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  // ── 4. Crowd Prediction ─────────────────────────────────────────
  const runCrowdAI = async () => {
    setLoading(true); setError("");
    try {
      const snap = await smartQueueApi.generateCrowdPrediction(selectedDept);
      setCrowdAI(snap);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3 text-slate-800">
            <Users className="text-indigo-600" size={32} />
            {t("smartQueue.smartQueueFlow")}
          </h1>
          <p className="text-slate-500 mt-1">{t("smartQueue.enterpriseFlowSubtitle")}</p>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-center gap-2"><AlertCircle size={18} /> {error}</div>}

      <div className="flex bg-white rounded-lg p-1 shadow-sm w-fit border border-slate-200">
        {[
          { id: "orchestrator", icon: MonitorPlay, label: t("smartQueue.tabOrchestrator") },
          { id: "signage", icon: MonitorPlay, label: t("smartQueue.tabSignage") },
          { id: "wayfinding", icon: Compass, label: t("smartQueue.tabWayfinding") },
          { id: "ai_crowd", icon: TrendingUp, label: t("smartQueue.tabCrowdAi") }
        ].map(t => (
          <button
            key={t.id}
            onClick={() => {
              setActiveTab(t.id as TabTypes);
              if (t.id === "signage" && queueMaster) fetchSignage();
            }}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium transition-all ${
              activeTab === t.id ? "bg-indigo-50 text-indigo-700 shadow-sm" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* ═════════ ORCHESTRATOR ═════════ */}
      {activeTab === "orchestrator" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="card p-6 border-indigo-100">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                {t("smartQueue.centralQueueMaster")}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-slate-600">{t("smartQueue.selectDepartment")}</label>
                  <select className="input-field mt-1" value={selectedDept} onChange={e => setSelectedDept(e.target.value)}>
                    <option value="Cardiology">Cardiology OPD</option>
                    <option value="Neurology">Neurology ER</option>
                    <option value="Dermatology">Dermatology Clinic</option>
                  </select>
                </div>
                <button onClick={initializeQueue} disabled={loading} className="btn-primary w-full">{t("smartQueue.startInstance")}</button>
              </div>

              {queueMaster && (
                <div className="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                  <div className="font-bold text-emerald-800">{t("smartQueue.engineActive")}</div>
                  <div className="text-sm text-emerald-700 mt-2 flex justify-between">
                    <span>{t("smartQueue.target")}: {queueMaster.department} / {queueMaster.room_number}</span>
                    <span className="font-black">{t("smartQueue.length")}: {queueMaster.current_length}</span>
                  </div>
                </div>
              )}

              {routingRec && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm">
                  <span className="font-bold text-blue-800 block mb-1 flex items-center gap-2"><ArrowRight size={14}/> {t("smartQueue.routingRecs")}:</span>
                  {t("smartQueue.bestRoom")}: <span className="font-bold">{routingRec.room_number}</span> ({t("smartQueue.queueLength")}: {routingRec.length})
                </div>
              )}
            </div>

            <div className="card p-6 border-slate-200 opacity-90">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                {t("smartQueue.simulateFlow")}
              </h3>
              {!queueMaster ? (
                <div className="text-center p-8 text-slate-400">{t("smartQueue.initOrchestratorFirst")}</div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <select className="input-field mb-2" value={mockPatientId} onChange={e=>setMockPatientId(e.target.value)}>
                      <option value="">-- {t("smartQueue.simulationPatient")} --</option>
                      {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}
                    </select>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      <button onClick={() => addPatientToQueue('emergency')} className="btn-primary bg-rose-600 hover:bg-rose-700">+ {t("smartQueue.addEmergency")}</button>
                      <button onClick={() => addPatientToQueue('priority')} className="btn-primary bg-amber-600 hover:bg-amber-700">+ {t("smartQueue.addPriority")}</button>
                      <button onClick={() => addPatientToQueue('walk_in')} className="btn-secondary col-span-2">+ {t("smartQueue.addWalkIn")}</button>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-200">
                    <h4 className="font-bold text-sm mb-2 text-slate-600 flex items-center gap-2"><UserMinus size={14}/> {t("smartQueue.recoveryLogic")}</h4>
                    <p className="text-xs text-slate-500 mb-2">{t("smartQueue.recoveryLogicDesc")}</p>
                    <button onClick={() => alert(t("smartQueue.triggerMissedAlert"))} className="btn-secondary w-full">{t("smartQueue.triggerMissed")}</button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═════════ DIGITAL SIGNAGE ═════════ */}
      {activeTab === "signage" && signageData && (
        <div className="bg-slate-900 border-[8px] border-slate-800 rounded-xl p-8 text-white min-h-[400px] shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500 rounded-full blur-[100px] opacity-20 -mr-20 -mt-20"></div>
          
          <div className="flex justify-between items-center mb-10 pb-4 border-b border-white/10 relative z-10">
            <div>
              <h2 className="text-3xl font-black tracking-tight">{signageData.department}</h2>
              <p className="text-indigo-300 font-medium text-lg mt-1">{signageData.doctor_name}</p>
            </div>
            <div className="bg-indigo-600 text-white px-6 py-3 rounded-lg text-center shadow-lg border border-indigo-500">
              <div className="text-sm font-bold opacity-80 uppercase tracking-widest">Room Number</div>
              <div className="text-4xl font-black leading-none mt-1">{signageData.room_number}</div>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-8 relative z-10">
            <div className="col-span-2">
              <div className="bg-white/5 rounded-2xl p-6 border border-white/10 h-full flex flex-col justify-center items-center text-center">
                <div className="text-sm font-bold text-emerald-400 uppercase tracking-widest animate-pulse flex items-center gap-2 mb-4">
                  <MonitorPlay size={16} /> {t("smartQueue.nowServing")}
                </div>
                {signageData.current_patient ? (
                  <>
                    <div className="text-6xl font-black bg-clip-text text-transparent bg-gradient-to-br from-emerald-300 to-teal-500 drop-shadow-sm">
                      #{signageData.current_patient.patient_uhid?.slice(0,6)}
                    </div>
                    <div className={`mt-4 badge ${signageData.current_patient.priority_level === 'emergency' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30 border' : 'bg-slate-800 text-slate-300'}`}>
                      {signageData.current_patient.priority_level.toUpperCase()}
                    </div>
                  </>
                ) : (
                  <div className="text-xl text-slate-500">{t("smartQueue.awaitingPatient")}</div>
                )}
              </div>
            </div>

            <div className="col-span-3 space-y-4">
              <div className="text-sm font-bold text-slate-400 uppercase tracking-widest pl-2 flex items-center gap-2">
                <Clock size={16} /> {t("smartQueue.nextInQueue")}
              </div>
              
              <div className="space-y-3">
                {signageData.next_patients.length > 0 ? signageData.next_patients.map((np, i) => (
                  <div key={i} className="bg-white/5 border border-white/5 rounded-xl p-4 flex justify-between items-center hover:bg-white/10 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-indigo-500/20 text-indigo-300 flex items-center justify-center font-bold text-sm">
                        {np.position_number}
                      </div>
                      <div className="text-2xl font-bold font-mono tracking-tight">{np.patient_uhid?.slice(0,6)}</div>
                    </div>
                    <div className="text-right">
                      {np.priority_level === 'emergency' && <span className="text-rose-400 text-xs font-bold uppercase block mb-1">{t("smartQueue.emergencyCall")}</span>}
                      <span className="text-slate-400 text-sm">{t("smartQueue.estWait")}: <span className="text-white font-bold">{signageData.avg_wait_time_min * (i + 1)} {t("smartQueue.min")}</span></span>
                    </div>
                  </div>
                )) : (
                  <div className="p-8 text-center border border-dashed border-slate-700 rounded-xl text-slate-500">{t("smartQueue.emptyQueue")}</div>
                )}
              </div>
            </div>
          </div>
          
          <div className="mt-8 pt-6 border-t border-white/10 flex justify-between items-center text-slate-400 text-sm relative z-10">
            <div>{t("smartQueue.totalWaiting")}: <strong className="text-white ml-2">{signageData.queue_length}</strong></div>
            <div className="flex items-center gap-2"><Bell size={14} className="text-amber-400" /> {t("smartQueue.notifySms")}</div>
          </div>
        </div>
      )}

      {/* ═════════ WAYFINDING ═════════ */}
      {activeTab === "wayfinding" && (
        <div className="card p-6 max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <Compass size={48} className="mx-auto text-indigo-500 mb-4" />
            <h2 className="text-2xl font-bold">{t("smartQueue.digitalRouteEngine")}</h2>
            <p className="text-slate-500">{t("smartQueue.searchRoom")}</p>
          </div>

          <div className="flex gap-4 mb-8">
            <input 
              type="text" 
              className="input-field flex-1 text-lg" 
              placeholder={t("smartQueue.searchRoomPlaceholder")}
              value={wayfindingTarget} onChange={e=>setWayfindingTarget(e.target.value)}
            />
            <button onClick={fetchWayfinding} disabled={loading} className="btn-primary w-32"><Search size={16}/></button>
          </div>

          {wayfindingInstr && (
            <div className="bg-indigo-50 border-l-4 border-indigo-600 p-6 rounded-r-lg shadow-sm">
              <h4 className="font-bold text-indigo-900 flex items-center gap-2 mb-2"><Map size={16} /> {t("smartQueue.directionsGenerated")}</h4>
              <p className="text-indigo-800 text-lg leading-relaxed">{wayfindingInstr}</p>
            </div>
          )}
        </div>
      )}

      {/* ═════════ AI CROWD PREDITION ═════════ */}
      {activeTab === "ai_crowd" && (
        <div className="card p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2"><TrendingUp className="text-indigo-500"/> {t("smartQueue.opCrowdPrediction")}</h2>
            <button onClick={runCrowdAI} disabled={loading} className="btn-primary">{t("smartQueue.executeModel")}</button>
          </div>

          {crowdAI ? (
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-slate-800 to-indigo-900 rounded-xl p-8 text-white grid grid-cols-3 gap-6 shadow-lg">
                <div className="border-r border-white/20">
                  <div className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-bold">{t("smartQueue.peakBlock")}</div>
                  <div className="text-4xl font-black bg-clip-text text-transparent bg-gradient-to-r from-amber-200 to-orange-400 drop-shadow-sm">
                    {crowdAI.predicted_peak_start} - {crowdAI.predicted_peak_end}
                  </div>
                </div>
                <div className="border-r border-white/20 pl-6">
                  <div className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-bold">{t("smartQueue.inflowEst")}</div>
                  <div className="text-4xl font-black text-emerald-400 drop-shadow-sm">
                    {crowdAI.predicted_inflow_count} <span className="text-lg text-emerald-400/50">{t("smartQueue.pts")}</span>
                  </div>
                </div>
                <div className="pl-6">
                  <div className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-bold">{t("smartQueue.estWaitSurge")}</div>
                  <div className="text-4xl font-black text-rose-400 drop-shadow-sm">
                    45 <span className="text-lg text-rose-400/50">{t("smartQueue.minAvg")}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-4 items-center bg-slate-50 p-4 border rounded-lg">
                <div className="font-bold text-sm text-slate-500 uppercase flex items-center gap-2">
                  <Activity size={16} /> {t("smartQueue.aiTensors")}
                </div>
                <div className="flex gap-2">
                  {crowdAI.factors_used.map((f,i) => <span key={i} className="badge bg-white border capitalize font-medium">{f.replace('_',' ')}</span>)}
                </div>
                <div className="ml-auto text-sm">
                  {t("smartQueue.confidenceSet")}: <strong className="text-indigo-600">{crowdAI.confidence_score * 100}%</strong>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center p-12 text-slate-400 border border-dashed rounded-lg">
              {t("smartQueue.clickExecuteToRun")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
