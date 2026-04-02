"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "@/i18n";
import {
  ShieldCheck, Package, RefreshCw, Plus, X, Activity, Thermometer, 
  Clock, CheckCircle2, AlertTriangle, ArrowRightLeft, Beaker
} from "lucide-react";

interface InstrumentSet { id: string; name: string; set_code: string; description: string; department: string; instrument_count: number; condition: string; is_active: boolean; }
interface SterilizationCycle { id: string; cycle_number: string; machine_id: string; method: string; status: string; start_time: string; end_time: string | null; temperature_celsius: number | null; pressure_psi: number | null; exposure_minutes: number | null; bi_result: string | null; ci_result: string | null; notes: string | null; }
interface CSSDDispatch { id: string; set_id: string; cycle_id: string | null; destination_department: string; dispatched_at: string; returned_at: string | null; return_condition: string | null; notes: string | null; }
interface Stats { total_sets: number; serviceable_sets: number; active_cycles: number; completed_today: number; pending_returns: number; damaged_sets: number; }

export default function CSSDDashboard() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"instruments" | "cycles" | "dispatches">("instruments");
  const [loading, setLoading] = useState(true);

  const [sets, setSets] = useState<InstrumentSet[]>([]);
  const [cycles, setCycles] = useState<SterilizationCycle[]>([]);
  const [dispatches, setDispatches] = useState<CSSDDispatch[]>([]);
  const [stats, setStats] = useState<Stats>({ total_sets: 0, serviceable_sets: 0, active_cycles: 0, completed_today: 0, pending_returns: 0, damaged_sets: 0 });

  const [showSetModal, setShowSetModal] = useState(false);
  const [showCycleModal, setShowCycleModal] = useState(false);
  const [showDispatchModal, setShowDispatchModal] = useState(false);

  // Set form
  const [setName, setSetName] = useState("");
  const [setCode, setSetCode] = useState("");
  const [setDesc, setSetDesc] = useState("");
  const [setDept, setSetDept] = useState("General Surgery");
  const [setCount, setSetCount] = useState("10");

  // Cycle form
  const [cycleNumber, setCycleNumber] = useState("");
  const [machineId, setMachineId] = useState("AC-01");
  const [cycleMethod, setCycleMethod] = useState("steam_autoclave");
  const [cycleTemp, setCycleTemp] = useState("134");
  const [cyclePressure, setCyclePressure] = useState("30");
  const [cycleExposure, setCycleExposure] = useState("18");
  const [cycleSetIds, setCycleSetIds] = useState<string[]>([]);

  // Dispatch form  
  const [dispSetId, setDispSetId] = useState("");
  const [dispDest, setDispDest] = useState("OT-1");

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

  const safeFetch = async (url: string, headers: Record<string, string>) => {
    try { const r = await fetch(url, { headers }); return r.ok ? await r.json() : null; }
    catch { return null; }
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      if (!token) { setLoading(false); return; }
      const headers = { Authorization: `Bearer ${token}` };

      const [setsData, cyclesData, dispData, statsData] = await Promise.all([
        safeFetch(`${API}/api/v1/cssd/instrument-sets`, headers),
        safeFetch(`${API}/api/v1/cssd/cycles`, headers),
        safeFetch(`${API}/api/v1/cssd/dispatches`, headers),
        safeFetch(`${API}/api/v1/cssd/stats`, headers),
      ]);

      if (setsData) setSets(setsData);
      if (cyclesData) setCycles(cyclesData);
      if (dispData) setDispatches(dispData);
      if (statsData) setStats(statsData);
    } catch (e) { console.error("CSSD fetch error:", e); }
    setLoading(false);
  }, [API]);

  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 30000); return () => clearInterval(iv); }, [fetchData]);

  const postJSON = async (url: string, body: any) => {
    try {
      const token = localStorage.getItem("access_token");
      return await fetch(url, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify(body) });
    } catch (e) { console.error("Post error:", e); return null; }
  };

  const handleCreateSet = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await postJSON(`${API}/api/v1/cssd/instrument-sets`, { name: setName, set_code: setCode, description: setDesc, department: setDept, instrument_count: parseInt(setCount) });
    if (res?.ok) { setShowSetModal(false); setSetName(""); setSetCode(""); setSetDesc(""); fetchData(); }
    else if (res) {
      try { const err = await res.json(); alert(err.detail || JSON.stringify(err)); }
      catch { alert("An unexpected server error occurred."); }
    } else { alert("Failed to connect to the server."); }
  };

  const handleCreateCycle = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await postJSON(`${API}/api/v1/cssd/cycles`, {
      cycle_number: cycleNumber, machine_id: machineId, method: cycleMethod,
      temperature_celsius: parseFloat(cycleTemp) || null, pressure_psi: parseFloat(cyclePressure) || null,
      exposure_minutes: parseInt(cycleExposure) || null, set_ids: cycleSetIds
    });
    if (res?.ok) { setShowCycleModal(false); setCycleNumber(""); setCycleSetIds([]); fetchData(); }
    else if (res) {
      try { const err = await res.json(); alert(err.detail || JSON.stringify(err)); }
      catch { alert("An unexpected server error occurred."); }
    } else { alert("Failed to connect to the server."); }
  };

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await postJSON(`${API}/api/v1/cssd/dispatches`, { set_id: dispSetId, destination_department: dispDest });
    if (res?.ok) { setShowDispatchModal(false); setDispSetId(""); fetchData(); }
    else if (res) {
      try { const err = await res.json(); alert(err.detail || JSON.stringify(err)); }
      catch { alert("An unexpected server error occurred."); }
    } else { alert("Failed to connect to the server."); }
  };

  const handleReturn = async (id: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API}/api/v1/cssd/dispatches/${id}/return`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ return_condition: "serviceable", notes: "Returned from OT" })
      });
      if (res.ok) fetchData();
      else alert("Failed to process return.");
    } catch { alert("Network error processing return"); }
  };

  const handleUpdateCycleStatus = async (id: string, newStatus: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API}/api/v1/cssd/cycles/${id}/status`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) fetchData();
      else alert("Failed to update cycle status.");
    } catch { alert("Network error updating status"); }
  };

  const statusColor = (s: string) => {
    if (s === "completed" || s === "released") return "text-emerald-400";
    if (s === "in_progress" || s === "loading") return "text-amber-400";
    if (s === "failed") return "text-red-400";
    return "text-slate-400";
  };

  const conditionBadge = (c: string) => {
    if (c === "serviceable") return "bg-emerald-500/20 text-emerald-400";
    if (c === "damaged") return "bg-red-500/20 text-red-400";
    if (c === "under_repair") return "bg-amber-500/20 text-amber-400";
    return "bg-slate-500/20 text-slate-400";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-teal-500/30">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">{t("CSSD Control Center")}</h1>
          </div>
          <p className="text-slate-400 text-sm ml-[52px]">{t("Manage instrument sterilization, autoclave cycles, and sterile supply dispatch in real-time.")}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setShowSetModal(true)} className="px-4 py-2 bg-slate-800 text-slate-300 border border-slate-700 rounded-xl text-sm font-semibold hover:bg-slate-700 hover:text-white transition-all flex items-center gap-2">
            <Plus className="w-4 h-4" /> {t("New Instrument Set")}
          </button>
          <button onClick={() => setShowCycleModal(true)} className="px-4 py-2 bg-teal-500/10 text-teal-400 border border-teal-500/20 rounded-xl text-sm font-semibold hover:bg-teal-500/20 transition-all flex items-center gap-2">
            <Beaker className="w-4 h-4" /> {t("New Cycle")}
          </button>
          <button onClick={() => setShowDispatchModal(true)} className="px-4 py-2 bg-gradient-to-br from-teal-600 to-cyan-600 text-white rounded-xl text-sm font-semibold shadow-lg shadow-teal-500/30 hover:shadow-teal-500/50 hover:-translate-y-0.5 transition-all">
            {t("Dispatch to OT")}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {[
          { label: t("Total Sets"), value: stats.total_sets, icon: <Package className="w-4 h-4" />, color: "text-blue-400" },
          { label: t("Serviceable"), value: stats.serviceable_sets, icon: <CheckCircle2 className="w-4 h-4" />, color: "text-emerald-400" },
          { label: t("Active Cycles"), value: stats.active_cycles, icon: <Activity className="w-4 h-4" />, color: "text-amber-400" },
          { label: t("Completed Today"), value: stats.completed_today, icon: <Clock className="w-4 h-4" />, color: "text-cyan-400" },
          { label: t("Pending Returns"), value: stats.pending_returns, icon: <ArrowRightLeft className="w-4 h-4" />, color: "text-purple-400" },
          { label: t("Damaged"), value: stats.damaged_sets, icon: <AlertTriangle className="w-4 h-4" />, color: "text-red-400" },
        ].map((s, i) => (
          <div key={i} className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={s.color}>{s.icon}</span>
              <span className="text-xs text-slate-500 font-medium">{s.label}</span>
            </div>
            <span className={`text-2xl font-bold ${s.color}`}>{s.value}</span>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {(["instruments", "cycles", "dispatches"] as const).map((t_key) => (
          <button key={t_key} onClick={() => setTab(t_key)}
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${tab === t_key ? "bg-teal-600 text-white shadow-lg shadow-teal-500/30" : "text-slate-400 hover:text-white hover:bg-slate-800"}`}>
            {t_key === "instruments" ? t("Instruments") : t_key === "cycles" ? t("Sterilization Cycles") : t("Dispatches")}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">{t("Loading...")}</div>
        ) : tab === "instruments" ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-xs font-medium">
                  <th className="p-4 text-left">{t("Set Code")}</th>
                  <th className="p-4 text-left">{t("Name")}</th>
                  <th className="p-4 text-left">{t("Department")}</th>
                  <th className="p-4 text-center">{t("Instruments")}</th>
                  <th className="p-4 text-center">{t("Condition")}</th>
                </tr>
              </thead>
              <tbody>
                {sets.length === 0 ? (
                  <tr><td colSpan={5} className="p-12 text-center text-slate-500">{t("No instrument sets registered.")}</td></tr>
                ) : sets.map(s => (
                  <tr key={s.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                    <td className="p-4 text-teal-400 font-mono text-xs">{s.set_code}</td>
                    <td className="p-4 text-white font-medium">{s.name}</td>
                    <td className="p-4 text-slate-400">{s.department || "—"}</td>
                    <td className="p-4 text-center text-slate-300">{s.instrument_count}</td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${conditionBadge(s.condition)}`}>{t(s.condition)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : tab === "cycles" ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-xs font-medium">
                  <th className="p-4 text-left">{t("Cycle #")}</th>
                  <th className="p-4 text-left">{t("Machine")}</th>
                  <th className="p-4 text-left">{t("Method")}</th>
                  <th className="p-4 text-center">{t("Temp (°C)")}</th>
                  <th className="p-4 text-center">{t("Pressure (PSI)")}</th>
                  <th className="p-4 text-center">{t("BI Result")}</th>
                  <th className="p-4 text-center">{t("Status")}</th>
                </tr>
              </thead>
              <tbody>
                {cycles.length === 0 ? (
                  <tr><td colSpan={7} className="p-12 text-center text-slate-500">{t("No sterilization cycles recorded.")}</td></tr>
                ) : cycles.map(c => (
                  <tr key={c.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                    <td className="p-4 text-teal-400 font-mono text-xs">{c.cycle_number}</td>
                    <td className="p-4 text-white">{c.machine_id}</td>
                    <td className="p-4 text-slate-300">{t(c.method)}</td>
                    <td className="p-4 text-center text-amber-400">{c.temperature_celsius ?? "—"}</td>
                    <td className="p-4 text-center text-slate-300">{c.pressure_psi ?? "—"}</td>
                    <td className="p-4 text-center">
                      {c.bi_result ? <span className={`px-2 py-1 rounded-full text-xs font-semibold ${c.bi_result === "pass" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>{t(c.bi_result)}</span> : "—"}
                    </td>
                    <td className="p-4 text-center">
                      <select 
                        value={c.status}
                        onChange={(e) => handleUpdateCycleStatus(c.id, e.target.value)}
                        className={`bg-slate-900 border border-slate-700/50 rounded-lg px-2 py-1.5 text-xs font-semibold focus:outline-none focus:border-teal-500 cursor-pointer hover:bg-slate-800 transition-colors ${statusColor(c.status)}`}
                      >
                        {["loading", "in_progress", "completed", "failed", "released"].map(s => (
                          <option key={s} value={s}>{t(s)}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-xs font-medium">
                  <th className="p-4 text-left">{t("Set ID")}</th>
                  <th className="p-4 text-left">{t("Destination")}</th>
                  <th className="p-4 text-left">{t("Dispatched At")}</th>
                  <th className="p-4 text-center">{t("Returned")}</th>
                  <th className="p-4 text-center">{t("Return Condition")}</th>
                </tr>
              </thead>
              <tbody>
                {dispatches.length === 0 ? (
                  <tr><td colSpan={5} className="p-12 text-center text-slate-500">{t("No dispatches recorded.")}</td></tr>
                ) : dispatches.map(d => (
                  <tr key={d.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                    <td className="p-4 text-teal-400 font-mono text-xs">{d.set_id.substring(0, 8)}...</td>
                    <td className="p-4 text-white font-medium">{d.destination_department}</td>
                    <td className="p-4 text-slate-400">{new Date(d.dispatched_at).toLocaleString()}</td>
                    <td className="p-4 text-center">
                      {d.returned_at ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto" />
                      ) : (
                        <button
                          onClick={() => handleReturn(d.id)}
                          className="px-3 py-1 bg-teal-500/10 hover:bg-teal-500/20 text-teal-400 text-xs rounded-lg border border-teal-500/20 transition-all font-semibold mx-auto block"
                        >
                          {t("Mark Returned")}
                        </button>
                      )}
                    </td>
                    <td className="p-4 text-center">{d.return_condition ? <span className={`px-2 py-1 rounded-full text-xs font-semibold ${conditionBadge(d.return_condition)}`}>{t(d.return_condition)}</span> : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ─── New Instrument Set Modal ─── */}
      {showSetModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-slate-800">
              <h3 className="font-bold text-white">{t("Register Instrument Set")}</h3>
              <button onClick={() => setShowSetModal(false)} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleCreateSet} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">{t("Set Name")}</label>
                <input type="text" required value={setName} onChange={e => setSetName(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-teal-500" placeholder={t("e.g. Major Abdominal Tray")} />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">{t("Set Code")}</label>
                <input type="text" required value={setCode} onChange={e => setSetCode(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-teal-500" placeholder="MAT-001" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">{t("Department")}</label>
                <select value={setDept} onChange={e => setSetDept(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-teal-500">
                  {["General Surgery", "Orthopedics", "Gynecology", "ENT", "Ophthalmology", "Urology", "Cardiology", "Neurosurgery"].map(d => <option key={d} value={d}>{t(d)}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">{t("Instrument Count")}</label>
                <input type="number" min="1" required value={setCount} onChange={e => setSetCount(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-teal-500" />
              </div>
              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setShowSetModal(false)} className="px-4 py-2 text-sm text-slate-400 hover:text-white">{t("Cancel")}</button>
                <button type="submit" className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-teal-500/30">{t("Save Set")}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── New Cycle Modal ─── */}
      {showCycleModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-slate-800">
              <h3 className="font-bold text-white">{t("Start Sterilization Cycle")}</h3>
              <button onClick={() => setShowCycleModal(false)} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleCreateCycle} className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{t("Cycle Number")}</label>
                  <input type="text" required value={cycleNumber} onChange={e => setCycleNumber(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-teal-500" placeholder="CYC-001" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{t("Machine ID")}</label>
                  <select value={machineId} onChange={e => setMachineId(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm">
                    {["AC-01", "AC-02", "AC-03", "ETO-01", "PLASMA-01"].map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">{t("Method")}</label>
                <select value={cycleMethod} onChange={e => setCycleMethod(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm">
                  {[["steam_autoclave", "Steam Autoclave"], ["eto_gas", "ETO Gas"], ["plasma", "Plasma"], ["dry_heat", "Dry Heat"], ["chemical", "Chemical"]].map(([v, l]) => <option key={v} value={v}>{t(l)}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{t("Temp (°C)")}</label>
                  <input type="number" value={cycleTemp} onChange={e => setCycleTemp(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{t("Pressure (PSI)")}</label>
                  <input type="number" value={cyclePressure} onChange={e => setCyclePressure(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{t("Exposure (min)")}</label>
                  <input type="number" value={cycleExposure} onChange={e => setCycleExposure(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm" />
                </div>
              </div>
              {sets.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{t("Load Instrument Sets")}</label>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {sets.map(s => (
                      <label key={s.id} className="flex items-center gap-2 text-slate-300 text-sm cursor-pointer hover:bg-slate-800 px-2 py-1 rounded">
                        <input type="checkbox" checked={cycleSetIds.includes(s.id)} onChange={e => {
                          if (e.target.checked) setCycleSetIds([...cycleSetIds, s.id]);
                          else setCycleSetIds(cycleSetIds.filter(id => id !== s.id));
                        }} className="accent-teal-500" />
                        <span className="text-teal-400 font-mono text-xs">{s.set_code}</span> — {s.name}
                      </label>
                    ))}
                  </div>
                </div>
              )}
              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setShowCycleModal(false)} className="px-4 py-2 text-sm text-slate-400 hover:text-white">{t("Cancel")}</button>
                <button type="submit" className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-teal-500/30">{t("Start Cycle")}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── Dispatch Modal ─── */}
      {showDispatchModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-slate-800">
              <h3 className="font-bold text-white">{t("Dispatch Sterile Set")}</h3>
              <button onClick={() => setShowDispatchModal(false)} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleDispatch} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">{t("Instrument Set")}</label>
                <select required value={dispSetId} onChange={e => setDispSetId(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm">
                  <option value="">-- {t("Select Set")} --</option>
                  {sets.map(s => <option key={s.id} value={s.id}>{s.set_code} — {s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">{t("Destination")}</label>
                <select value={dispDest} onChange={e => setDispDest(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm">
                  {["OT-1", "OT-2", "OT-3", "ER", "ICU Ward", "Labor Room", "Minor OT"].map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setShowDispatchModal(false)} className="px-4 py-2 text-sm text-slate-400 hover:text-white">{t("Cancel")}</button>
                <button type="submit" className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-teal-500/30">{t("Dispatch Now")}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
