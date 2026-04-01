"use client";
import { useTranslation } from "@/i18n";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import {
  CheckCircle2, XCircle, Clock, AlertCircle, RefreshCw, Shield,
  AlertTriangle, Loader2, FlaskConical, ArrowRight, Eye, Settings,
  ClipboardList, Database, Zap, Cpu, History, Search, Download, Trash2, 
  Activity, ArrowUpRight, ArrowDownRight, Server, Link, PowerOff, Power
} from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { analyzerApi } from "@/lib/analyzer-api";
import type {
  AnalyzerDevice, AnalyzerWorklistItem, AnalyzerResult, ReagentUsage,
  DeviceError, DeviceAudit, AnalyzerDashStats
} from "@/lib/analyzer-api";

type TabTypes = "dashboard"|"devices"|"worklists"|"results"|"reagents"|"errors"|"audit";

const DEPARTMENTS = ["BIOCHEMISTRY","HEMATOLOGY","CLINICAL_PATHOLOGY","SEROLOGY","MICROBIOLOGY","IMMUNOLOGY"];
const PROTOCOLS = ["HL7", "ASTM", "SERIAL", "TCP_IP"];

export default function AnalyzerIntegrationPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabTypes>("dashboard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [stats, setStats] = useState<AnalyzerDashStats|null>(null);

  // States per tab
  const [devices, setDevices] = useState<AnalyzerDevice[]>([]);
  const [worklists, setWorklists] = useState<AnalyzerWorklistItem[]>([]);
  const [results, setResults] = useState<AnalyzerResult[]>([]);
  const [reagents, setReagents] = useState<ReagentUsage[]>([]);
  const [errors, setErrors] = useState<DeviceError[]>([]);
  const [audits, setAudits] = useState<DeviceAudit[]>([]);

  // Filters
  const [deptFilter, setDeptFilter] = useState("");
  const [deviceFilter, setDeviceFilter] = useState("");

  const tabs = useMemo(() => [
    { id:"dashboard", label:"Hub Overview", icon:Activity },
    { id:"devices", label:"Device Gateway", icon:Server, badge:stats?.offline_devices||0, badgeColor:"bg-rose-500" },
    { id:"worklists", label:"Worklists", icon:ClipboardList, badge:stats?.pending_worklists||0 },
    { id:"results", label:"Results Inbox", icon:Database, badge:stats?.unverified_results||0 },
    { id:"reagents", label:"Reagents", icon:FlaskConical, badge:stats?.low_stock_reagents||0, badgeColor:"bg-amber-500" },
    { id:"errors", label:"Error Log", icon:AlertTriangle, badge:stats?.unresolved_errors||0, badgeColor:"bg-rose-500" },
    { id:"audit", label:"Audit Trail", icon:History },
  ], [stats]);

  const fetchDashboard = useCallback(async () => { try { const s = await analyzerApi.getDashboard(); setStats(s); } catch(e:any) { console.error(e); } }, []);
  const fetchDevices = useCallback(async () => { setLoading(true); try { const items = await analyzerApi.listDevices({ department:deptFilter||undefined }); setDevices(items||[]); } catch(e:any) { setError(e.message); } setLoading(false); }, [deptFilter]);
  const fetchWorklists = useCallback(async () => { setLoading(true); try { const items = await analyzerApi.listWorklists({ device_id:deviceFilter||undefined }); setWorklists(items||[]); } catch(e:any) { setError(e.message); } setLoading(false); }, [deviceFilter]);
  const fetchResults = useCallback(async () => { setLoading(true); try { const items = await analyzerApi.listResults({ device_id:deviceFilter||undefined }); setResults(items||[]); } catch(e:any) { setError(e.message); } setLoading(false); }, [deviceFilter]);
  const fetchReagents = useCallback(async () => { setLoading(true); try { const items = await analyzerApi.listReagents({ device_id:deviceFilter||undefined }); setReagents(items||[]); } catch(e:any) { console.error(e); } setLoading(false); }, [deviceFilter]);
  const fetchErrors = useCallback(async () => { setLoading(true); try { const items = await analyzerApi.listErrors({ device_id:deviceFilter||undefined }); setErrors(items||[]); } catch(e:any) { console.error(e); } setLoading(false); }, [deviceFilter]);
  const fetchAudits = useCallback(async () => { setLoading(true); try { const items = await analyzerApi.getAudit({ limit:50 }); setAudits(items||[]); } catch(e:any) { console.error(e); } setLoading(false); }, []);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);
  useEffect(() => {
    if (activeTab==="devices") fetchDevices();
    if (activeTab==="worklists") fetchWorklists();
    if (activeTab==="results") fetchResults();
    if (activeTab==="reagents") fetchReagents();
    if (activeTab==="errors") fetchErrors();
    if (activeTab==="audit") fetchAudits();
  }, [activeTab, fetchDevices, fetchWorklists, fetchResults, fetchReagents, fetchErrors, fetchAudits]);

  const handleSync = async () => {
    setLoading(true);
    await Promise.all([fetchDashboard(), fetchDevices(), fetchWorklists(), fetchResults(), fetchReagents(), fetchErrors(), fetchAudits()]);
    setLoading(false); setSuccess("Communication systems synchronized.");
  };

  const getStatusColor = (s:string) => {
    if (s==="ONLINE") return "bg-emerald-100 text-emerald-700 border-emerald-200";
    if (s==="OFFLINE") return "bg-slate-100 text-slate-700 border-slate-200";
    if (s==="ERROR" || s==="FAILED") return "bg-rose-100 text-rose-700 border-rose-200";
    if (s==="MAINTENANCE") return "bg-amber-100 text-amber-700 border-amber-200";
    if (s==="MATCHED") return "bg-blue-100 text-blue-700 border-blue-200";
    if (s==="MISMATCH") return "bg-rose-100 text-rose-700 border-rose-200 animate-pulse";
    if (s==="IMPORTED") return "bg-emerald-100 text-emerald-700 border-emerald-200";
    return "bg-slate-100 text-slate-700 border-slate-200";
  };

  const handleUpdateDeviceStatus = async (id:string, newStatus:string) => {
    try { await analyzerApi.updateDeviceStatus(id, newStatus, "Admin"); setSuccess(`Device status updated to ${newStatus}`); fetchDevices(); fetchDashboard(); } catch(e:any) { setError(e.message); }
  };

  const handleVerifyResult = async (id:string) => {
    try { await analyzerApi.verifyResult(id, "Technician"); await analyzerApi.importResult(id); setSuccess("Result verified and imported to LIS."); fetchResults(); fetchDashboard(); } catch(e:any) { setError(e.message); }
  };

  const handleResolveError = async (id:string) => {
    try { await analyzerApi.resolveError(id, "Admin"); setSuccess("Error marked as resolved."); fetchErrors(); fetchDashboard(); } catch(e:any) { setError(e.message); }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <TopNav title="Analyzer & Device Integration Engine" />
      <div className="flex-1 p-6 max-w-[1400px] mx-auto w-full space-y-5">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Analyzer Hub</h1>
            <p className="text-slate-400 font-bold uppercase tracking-[0.15em] text-[10px] mt-1">Bi-directional ASTM / HL7 Device Interface</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleSync} disabled={loading} className="btn btn-secondary flex items-center gap-2 shadow-sm cursor-pointer">
              {loading?<Loader2 size={16} className="animate-spin"/>:<RefreshCw size={16}/>} Poll Devices
            </button>
            <button onClick={() => setSuccess("Analyzer Registration Interface opened.")} className="btn bg-indigo-600 text-white flex items-center gap-2 shadow-sm focus:ring-4 focus:ring-indigo-100 cursor-pointer">
              <Link size={16}/> Add New Analyzer
            </button>
          </div>
        </div>

        {/* Alerts */}
        {error && <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded-xl flex items-center justify-between text-xs font-bold"><div className="flex items-center gap-2"><AlertCircle size={14}/>{error}</div><button onClick={()=>setError("")} className="cursor-pointer"><XCircle size={16}/></button></div>}
        {success && <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-xl flex items-center justify-between text-xs font-bold"><div className="flex items-center gap-2"><CheckCircle2 size={14}/>{success}</div><button onClick={()=>setSuccess("")} className="cursor-pointer"><XCircle size={16}/></button></div>}

        {/* Tabs */}
        <div className="flex p-1 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-x-auto scroller-hide">
          {tabs.map(tab=>(
            <button key={tab.id} onClick={()=>setActiveTab(tab.id as TabTypes)} className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-[11px] font-black uppercase tracking-wider transition-all whitespace-nowrap cursor-pointer ${activeTab===tab.id?"bg-slate-900 text-white shadow-lg":"text-slate-400 hover:text-slate-900 hover:bg-slate-100"}`}>
              <tab.icon size={15}/>{tab.label}
              {tab.badge!==undefined&&tab.badge>0&&<span className={`px-1.5 py-0.5 rounded-full text-[9px] font-black ml-1 ${activeTab===tab.id?"bg-indigo-500 text-white":(tab.badgeColor||"bg-indigo-100 text-indigo-600")}`}>{tab.badge}</span>}
            </button>
          ))}
        </div>

        {/* ═══ TAB 1: DASHBOARD ═══ */}
        {activeTab==="dashboard"&&(
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {[
                {l:"Total Devices",v:stats?.total_devices||0,icon:Server,c:"text-indigo-600",bg:"bg-indigo-50"},
                {l:"Online",v:stats?.online_devices||0,icon:Activity,c:"text-emerald-600",bg:"bg-emerald-50"},
                {l:"Offline",v:stats?.offline_devices||0,icon:PowerOff,c:"text-slate-600",bg:"bg-slate-100"},
                {l:"Pending Worklists",v:stats?.pending_worklists||0,icon:ClipboardList,c:"text-blue-600",bg:"bg-blue-50"},
                {l:"Mismatched Results",v:stats?.unverified_results||0,icon:AlertCircle,c:"text-rose-600",bg:"bg-rose-50"},
                {l:"Low Reagents",v:stats?.low_stock_reagents||0,icon:FlaskConical,c:"text-amber-600",bg:"bg-amber-50"},
              ].map((m,i)=>(
                <div key={i} className="card p-4 flex flex-col items-center text-center hover:scale-[1.02] transition-transform cursor-pointer bg-white">
                  <div className={`p-3 rounded-xl ${m.bg} mb-2`}><m.icon size={20} className={m.c}/></div>
                  <div className="text-2xl font-black text-slate-800 tabular-nums">{m.v}</div>
                  <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{m.l}</div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="card p-6 bg-white space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-black text-sm text-slate-900 uppercase">Device Connectivity Map</h3>
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded font-black uppercase">Live Polling Active</span>
                </div>
                <div className="p-8 border-2 border-dashed border-slate-100 rounded-2xl flex flex-col items-center justify-center text-center">
                   <Server size={48} className="text-slate-200 mb-4"/>
                   <p className="text-sm font-bold text-slate-400">Select <span className="text-indigo-500">Device Gateway</span> tab to map HL7 endpoints and manage instrument configurations.</p>
                </div>
              </div>
              
              <div className="bg-slate-900 rounded-2xl p-6 text-white shadow-xl flex flex-col space-y-5">
                <div><h3 className="font-black text-lg">System Metrics</h3><p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">Today's Throughput</p></div>
                
                <div className="flex-1 flex flex-col justify-center space-y-6">
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1"><span>Results Processed (Today)</span><span className="text-indigo-400">{stats?.results_today||0}</span></div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden"><div className="bg-indigo-500 h-full" style={{width:`${Math.min(100, (stats?.results_today||0)/10)}%`}}/></div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1"><span>Device Error Rate</span><span className="text-rose-400">{stats?.total_devices ? Math.round(((stats?.error_devices||0)/(stats?.total_devices||1))*100) : 0}%</span></div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden"><div className="bg-rose-500 h-full" style={{width:`${stats?.total_devices ? Math.round(((stats?.error_devices||0)/(stats?.total_devices||1))*100) : 0}%`}}/></div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1"><span>Active Maintenance</span><span className="text-amber-400">{stats?.maintenance_devices||0}</span></div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden"><div className="bg-amber-500 h-full" style={{width:`${stats?.total_devices ? Math.round(((stats?.maintenance_devices||0)/(stats?.total_devices||1))*100) : 0}%`}}/></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ═══ TAB 2: DEVICE GATEWAY ═══ */}
        {activeTab==="devices"&&(
          <div className="card bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3"><Server size={18} className="text-indigo-600"/><h3 className="text-sm font-black text-slate-900 uppercase">Registered Analyzers</h3></div>
              <select className="input-field w-auto text-[10px] font-bold py-1.5 cursor-pointer" value={deptFilter} onChange={e=>setDeptFilter(e.target.value)}>
                <option value="">All Departments</option>{DEPARTMENTS.map(d=><option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="overflow-x-auto"><table className="w-full text-left">
              <thead><tr className="bg-slate-50 border-b border-slate-100">
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Device</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Model Info</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Department</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Protocol</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Connection</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Status</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase text-right">Actions</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {devices.length===0?<tr><td colSpan={7} className="py-16 text-center text-slate-400 text-xs font-bold uppercase">No devices registered.</td></tr>:
                devices.map(dev=>(
                  <tr key={dev.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-5"><div className="font-black text-slate-900 text-xs">{dev.device_name}</div><div className="text-[10px] text-slate-400 font-mono">{dev.device_code}</div></td>
                    <td className="py-4 px-5"><div className="font-bold text-slate-800 text-xs">{dev.manufacturer||"—"}</div><div className="text-[10px] text-slate-500">{dev.model||"—"}</div></td>
                    <td className="py-4 px-5 text-[10px] font-bold text-slate-500">{dev.department.replace(/_/g," ")}</td>
                    <td className="py-4 px-5"><span className="px-2 py-0.5 rounded text-[9px] font-black uppercase border bg-indigo-50 text-indigo-700 border-indigo-200">{dev.protocol}</span></td>
                    <td className="py-4 px-5"><div className="text-[10px] font-mono text-slate-600">{dev.ip_address?`${dev.ip_address}:${dev.port}`:dev.connection_string||"Unconfigured"}</div></td>
                    <td className="py-4 px-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border flex-inline items-center gap-1 w-max ${getStatusColor(dev.status)}`}>{dev.status==="ONLINE"&&<div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse inline-block mr-1"/>}{dev.status}</span></td>
                    <td className="py-4 px-5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {dev.status==="ONLINE"?<button onClick={()=>handleUpdateDeviceStatus(dev.id,"OFFLINE")} className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-[9px] font-bold cursor-pointer">Stop</button>
                        :<button onClick={()=>handleUpdateDeviceStatus(dev.id,"ONLINE")} className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-[9px] font-bold cursor-pointer">Connect</button>}
                        <button className="p-1.5 text-slate-400 hover:text-indigo-600 rounded cursor-pointer"><Settings size={14}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </div>
        )}

        {/* ═══ TAB 3: WORKLISTS ═══ */}
        {activeTab==="worklists"&&(
           <div className="card bg-white rounded-2xl overflow-hidden shadow-sm">
             <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
               <div className="flex items-center gap-3"><ClipboardList size={18} className="text-indigo-600"/><h3 className="text-sm font-black text-slate-900 uppercase">Worklist Outbox to Analyzers</h3></div>
               <button onClick={()=>setSuccess("Broadcast to all analyzers initiated")} className="btn btn-sm btn-secondary cursor-pointer">Broadcast All Pending</button>
             </div>
             <div className="overflow-x-auto"><table className="w-full text-left">
               <thead><tr className="bg-slate-50 border-b border-slate-100">
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Device Target</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Sample BC</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Patient UHID</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">LIS Test</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Analyzer Map</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Status</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase text-right">Sent Time</th>
               </tr></thead>
               <tbody className="divide-y divide-slate-100">
                 {worklists.length===0?<tr><td colSpan={7} className="py-16 text-center text-slate-400 text-xs font-bold uppercase">No worklist transmissions.</td></tr>:
                 worklists.map(wl=>(
                   <tr key={wl.id} className="hover:bg-slate-50 transition-colors">
                     <td className="py-3 px-5 text-xs font-bold text-indigo-600">{devices.find(d=>d.id===wl.device_id)?.device_name||"Unknown Device"}</td>
                     <td className="py-3 px-5 text-xs font-mono font-bold">{wl.barcode}</td>
                     <td className="py-3 px-5 text-[10px] font-bold text-slate-600">{wl.patient_uhid}</td>
                     <td className="py-3 px-5 text-xs font-bold">{wl.test_code}</td>
                     <td className="py-3 px-5 text-[10px] font-mono p-1 bg-slate-100 rounded text-slate-500 w-max">{wl.analyzer_test_code||"Unmapped"}</td>
                     <td className="py-3 px-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${getStatusColor(wl.status)}`}>{wl.status}</span></td>
                     <td className="py-3 px-5 text-right text-[10px] text-slate-400 font-mono">{wl.sent_at?new Date(wl.sent_at).toLocaleString():"—"}</td>
                   </tr>
                 ))}
               </tbody>
             </table></div>
           </div>
        )}

        {/* ═══ TAB 4: RESULTS INBOX ═══ */}
        {activeTab==="results"&&(
           <div className="card bg-white rounded-2xl overflow-hidden shadow-sm">
             <div className="flex items-center justify-between bg-slate-50/50 p-5 border-b border-slate-100">
               <div className="flex items-center gap-3"><Database size={18} className="text-indigo-600"/><div><h3 className="text-sm font-black text-slate-900 uppercase">Analyzer Result Inbox & Matching</h3><p className="text-[9px] text-slate-400 uppercase font-bold mt-0.5">Automated Sample-ID to Order mapping</p></div></div>
               <div className="flex items-center gap-2">
                 <button onClick={()=>fetchResults()} className="btn btn-sm btn-secondary cursor-pointer"><RefreshCw size={14}/> Reload Inbox</button>
               </div>
             </div>
             <div className="overflow-x-auto"><table className="w-full text-left">
               <thead><tr className="bg-slate-50 border-b border-slate-100">
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Device Source</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Sample ID</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Test Map</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Result Value</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Match Status</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Received</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase text-right">Actions</th>
               </tr></thead>
               <tbody className="divide-y divide-slate-100">
                 {results.length===0?<tr><td colSpan={7} className="py-16 text-center text-slate-400 text-xs font-bold uppercase">No results received.</td></tr>:
                 results.map(res=>(
                   <tr key={res.id} className="hover:bg-slate-50 transition-colors">
                     <td className="py-3 px-5 text-[10px] font-bold text-slate-600">{devices.find(d=>d.id===res.device_id)?.device_name||"Unknown"}</td>
                     <td className="py-3 px-5"><div className="text-xs font-mono font-black text-slate-900">{res.sample_id}</div>{res.is_qc_sample&&<span className="text-[9px] bg-amber-100 text-amber-700 px-1 rounded font-bold">QC SAMPLE</span>}</td>
                     <td className="py-3 px-5 text-[10px] font-bold"><span className="text-indigo-600">{res.test_code}</span> <span className="text-slate-400 font-mono">({res.analyzer_test_code||"—"})</span></td>
                     <td className="py-3 px-5"><span className="text-sm font-black text-slate-900 tabular-nums">{res.result_numeric||res.result_value||"—"}</span> <span className="text-[10px] text-slate-500">{res.result_unit}</span> {res.result_flag&&<span className="ml-1 text-[9px] bg-rose-100 text-rose-700 px-1 rounded">{res.result_flag}</span>}</td>
                     <td className="py-3 px-5">
                       <div className="flex flex-col gap-1">
                         <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border w-max ${getStatusColor(res.status)}`}>{res.status}</span>
                         {res.match_confidence != null && <span className="text-[9px] text-slate-400 font-bold">Confidence: {res.match_confidence*100}%</span>}
                       </div>
                     </td>
                     <td className="py-3 px-5 text-[9px] text-slate-400 font-mono">{res.received_at?new Date(res.received_at).toLocaleTimeString():"—"}</td>
                     <td className="py-3 px-5 text-right">
                       {res.status!=="IMPORTED"&&<button onClick={()=>handleVerifyResult(res.id)} className="px-3 py-1 bg-indigo-600 text-white rounded-lg text-[9px] font-black uppercase cursor-pointer hover:bg-indigo-700 active:scale-95 transition-all shadow">Verify & Import LIS</button>}
                     </td>
                   </tr>
                 ))}
               </tbody>
             </table></div>
           </div>
        )}

        {/* ═══ TAB 5: REAGENTS ═══ */}
        {activeTab==="reagents"&&(
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             <div className="md:col-span-1 space-y-4">
                <div className="card p-5 bg-white space-y-4">
                  <div className="flex items-center gap-2"><FlaskConical size={18} className="text-indigo-600"/><h3 className="font-black text-sm text-slate-900">Inventory Tracker</h3></div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Tracks per-test consumption and syncs with Central Inventory.</p>
                  <button className="w-full btn btn-secondary cursor-pointer">Register Reagent Lot</button>
                </div>
             </div>
             <div className="md:col-span-2 card bg-white">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center"><h3 className="text-xs font-black uppercase text-slate-900">Consumption Logs</h3></div>
                <div className="overflow-x-auto"><table className="w-full text-left">
                  <thead><tr className="border-b border-slate-100 text-[9px] font-black text-slate-400 uppercase">
                    <th className="py-3 px-4">Device</th><th className="py-3 px-4">Reagent/Test</th><th className="py-3 px-4 text-center">Used</th><th className="py-3 px-4 text-right">Stock Level</th>
                  </tr></thead>
                  <tbody className="divide-y divide-slate-50">
                    {reagents.length===0?<tr><td colSpan={4} className="py-12 text-center text-slate-400 text-[10px] font-bold uppercase">No tracking data.</td></tr>:
                    reagents.map(r=>(
                      <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-4 text-[10px] font-bold text-slate-600">{devices.find(d=>d.id===r.device_id)?.device_name||"Unknown"}</td>
                        <td className="py-3 px-4"><div className="text-xs font-black text-slate-800">{r.reagent_name}</div><div className="text-[9px] text-slate-500">Test: {r.test_code} | Lot: {r.reagent_lot||"N/A"}</div></td>
                        <td className="py-3 px-4 text-center"><span className="text-xs font-bold bg-slate-100 px-2 py-0.5 rounded tabular-nums">-{r.quantity_used} {r.unit}</span></td>
                        <td className="py-3 px-4 text-right">
                          <div className={`text-xs font-black tabular-nums ${r.is_low_stock?"text-rose-600":"text-emerald-600"}`}>{r.current_stock||"—"}</div>
                          {r.is_low_stock&&<span className="text-[9px] uppercase font-bold text-rose-500 animate-pulse">Low Stock</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
             </div>
          </div>
        )}

        {/* ═══ TAB 6: ERRORS ═══ */}
        {activeTab==="errors"&&(
           <div className="card bg-white rounded-2xl overflow-hidden shadow-sm">
             <div className="p-5 border-b border-rose-100 bg-rose-50/30 flex items-center gap-3">
               <AlertTriangle size={18} className="text-rose-600"/><h3 className="text-sm font-black text-rose-900 uppercase">Device Error Monitor</h3>
             </div>
             <div className="overflow-x-auto"><table className="w-full text-left">
               <thead><tr className="border-b border-slate-100 text-[10px] font-black text-slate-400 uppercase">
                 <th className="py-3 px-5">Time</th><th className="py-3 px-5">Device</th><th className="py-3 px-5">Error Type</th><th className="py-3 px-5">Details</th><th className="py-3 px-5 text-right">Action</th>
               </tr></thead>
               <tbody className="divide-y divide-slate-100">
                 {errors.length===0?<tr><td colSpan={5} className="py-16 text-center text-emerald-600 text-xs font-bold uppercase">All systems nominal. No errors detected.</td></tr>:
                 errors.map(err=>(
                   <tr key={err.id} className={`transition-colors ${err.is_resolved?"bg-slate-50/50":"bg-rose-50/10 hover:bg-rose-50/30"}`}>
                     <td className="py-3 px-5 text-[10px] font-mono text-slate-500">{new Date(err.occurred_at||"").toLocaleString()}</td>
                     <td className="py-3 px-5 text-[10px] font-bold">{devices.find(d=>d.id===err.device_id)?.device_name||"Unknown"}</td>
                     <td className="py-3 px-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${err.severity==="CRITICAL"?"bg-rose-100 text-rose-700 border-rose-200 animate-pulse":err.severity==="ERROR"?"bg-orange-100 text-orange-700 border-orange-200":err.is_resolved?"bg-slate-100 text-slate-500 border-slate-200":"bg-amber-100 text-amber-700 border-amber-200"}`}>{err.error_type}</span></td>
                     <td className="py-3 px-5"><div className="text-xs font-bold text-slate-800">{err.message}</div>{err.raw_data&&<div className="text-[9px] font-mono text-slate-400 mt-1 truncate max-w-xs">{err.raw_data}</div>}</td>
                     <td className="py-3 px-5 text-right">
                       {!err.is_resolved?<button onClick={()=>handleResolveError(err.id)} className="px-3 py-1 bg-slate-900 text-white rounded text-[9px] font-bold cursor-pointer hover:bg-black">Resolve</button>
                       :<span className="text-[9px] uppercase font-bold text-emerald-600">Resolved by {err.resolved_by}</span>}
                     </td>
                   </tr>
                 ))}
               </tbody>
             </table></div>
           </div>
        )}

        {/* ═══ TAB 7: AUDIT TRAIL ═══ */}
        {activeTab==="audit"&&(
          <div className="card bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/30">
              <div className="flex items-center gap-3"><History size={20} className="text-indigo-600"/><div><h3 className="font-black text-sm text-slate-900">Communication Audit Trail</h3><p className="text-[10px] text-slate-400 font-bold uppercase">Low-level HL7/ASTM message logging</p></div></div>
              <button onClick={()=>{setSuccess("Trace export started.");setTimeout(()=>alert("Download generated."),200);}} className="btn btn-sm btn-secondary cursor-pointer"><Download size={14}/> Export Trace Log</button>
            </div>
            <div className="overflow-x-auto"><table className="w-full text-left">
              <thead><tr className="border-b border-slate-100 text-[10px] font-black text-slate-400 uppercase">
                <th className="py-3 px-5">Timestamp</th><th className="py-3 px-5 text-center">Dir</th><th className="py-3 px-5">Event Action</th><th className="py-3 px-5">Device Link</th><th className="py-3 px-5">Status</th><th className="py-3 px-5 text-right">Payload</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {audits.length===0?<tr><td colSpan={6} className="py-16 text-center text-slate-400 text-xs font-bold">No gateway activity.</td></tr>:
                audits.map((log,i)=>(
                  <tr key={i} className="hover:bg-slate-50 transition-colors group">
                    <td className="py-3 px-5 text-[10px] font-mono text-slate-400">{new Date(log.performed_at!).toLocaleString()}</td>
                    <td className="py-3 px-5 text-center">{log.direction==="IN"?<ArrowDownRight size={14} className="text-emerald-500 mx-auto"/>:<ArrowUpRight size={14} className="text-blue-500 mx-auto"/>}</td>
                    <td className="py-3 px-5 text-[10px] font-black text-slate-700 uppercase">{log.action.replace(/_/g," ")}</td>
                    <td className="py-3 px-5 text-[10px] font-bold text-indigo-600">{devices.find(d=>d.id===log.device_id)?.device_name||"System"}</td>
                    <td className="py-3 px-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${log.status==="SUCCESS"?"bg-emerald-50 text-emerald-700 border-emerald-200":"bg-rose-50 text-rose-700 border-rose-200"}`}>{log.status}</span></td>
                    <td className="py-3 px-5 text-right text-[9px] font-mono text-slate-500 truncate max-w-[150px]">{log.data_transmitted||log.data_received||"—"}</td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </div>
        )}

      </div>
      
      <style jsx global>{`
        .scroller-hide::-webkit-scrollbar{display:none}
        .scroller-hide{-ms-overflow-style:none;scrollbar-width:none}
      `}</style>
    </div>
  );
}
