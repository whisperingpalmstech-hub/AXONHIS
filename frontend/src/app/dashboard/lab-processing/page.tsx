"use client";
import React, { useEffect, useState, useCallback, useMemo } from "react";
import {
  CheckCircle2, XCircle, FileText, Clock, AlertCircle, RefreshCw, Shield,
  AlertTriangle, Loader2, FlaskConical, ArrowRight, Eye, Settings,
  ClipboardList, Database, Zap, Filter, Layers, BarChart3, Binary, User,
  Calendar, History, Check, X, Sliders, Cpu, MessageSquare, Send,
  Play, Pause, ArrowUpDown, Download, Upload, Plus, Trash2
} from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { procApi } from "@/lib/proc-api";
import type {
  WorklistItem, ResultEntry, ResultFlag, DeltaCheck,
  ResultComment, QCResult, AuditEntry, ProcessingStats
} from "@/lib/proc-api";

type TabTypes = "dashboard"|"worklist"|"results"|"qc"|"audit"|"settings";
const DEPARTMENTS = ["BIOCHEMISTRY","HEMATOLOGY","CLINICAL_PATHOLOGY","SEROLOGY","MICROBIOLOGY","HISTOPATHOLOGY","IMMUNOLOGY","MOLECULAR_BIOLOGY","CYTOLOGY","URINALYSIS"];
const RESULT_TYPES = ["NUMERIC","TEXT","QUALITATIVE","IMAGE"];
const STATUS_FLOW = ["PENDING","IN_PROGRESS","RESULT_ENTERED","AWAITING_VALIDATION","VALIDATED","RELEASED"];

export default function LabProcessingPage() {
  const [activeTab, setActiveTab] = useState<TabTypes>("dashboard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [stats, setStats] = useState<ProcessingStats|null>(null);
  const [worklist, setWorklist] = useState<WorklistItem[]>([]);
  const [activeDept, setActiveDept] = useState("");
  const [wlStatus, setWlStatus] = useState("PENDING");
  const [selectedItem, setSelectedItem] = useState<WorklistItem|null>(null);
  const [showResultForm, setShowResultForm] = useState(false);
  const [resultVal, setResultVal] = useState("");
  const [resultNum, setResultNum] = useState("");
  const [resultUnit, setResultUnit] = useState("");
  const [resultType, setResultType] = useState("NUMERIC");
  const [techName, setTechName] = useState("");
  const [resultComments, setResultComments] = useState("");
  const [resultsList, setResultsList] = useState<ResultEntry[]>([]);
  const [resultFilterStatus, setResultFilterStatus] = useState("");
  const [qcList, setQcList] = useState<QCResult[]>([]);
  const [qcDept, setQcDept] = useState("BIOCHEMISTRY");
  const [qcForm, setQcForm] = useState({ test_code:"HB", test_name:"Hemoglobin", lot:"LOT-A12", level:"NORMAL", expected:"14.5", sd:"0.2", actual:"", technician:"" });
  const [auditList, setAuditList] = useState<AuditEntry[]>([]);
  const [batchMode, setBatchMode] = useState(false);
  const [batchItems, setBatchItems] = useState<string[]>([]);
  const [commentLibrary, setCommentLibrary] = useState<string[]>([]);
  const [showDetailModal, setShowDetailModal] = useState<ResultEntry|null>(null);

  const tabs = useMemo(() => [
    { id:"dashboard", label:"Overview", icon:BarChart3 },
    { id:"worklist", label:"Test Worklist", icon:ClipboardList, badge:stats?.total_pending||0 },
    { id:"results", label:"Result Review", icon:FileText, badge:stats?.results_entered||0 },
    { id:"qc", label:"Quality Control", icon:Shield, badge:stats?.qc_failures||0, badgeColor:"bg-rose-500" },
    { id:"audit", label:"Audit Trail", icon:History },
    { id:"settings", label:"Configurations", icon:Settings },
  ], [stats]);

  const loadDashboard = useCallback(async () => { try { const s = await procApi.getDashboard(); setStats(s); } catch(e:any) { console.error(e); } }, []);
  const loadWorklist = useCallback(async () => { setLoading(true); try { const items = await procApi.listWorklist({ department:activeDept||undefined, status:wlStatus||undefined }); setWorklist(items||[]); } catch(e:any) { setError(e.message); } setLoading(false); }, [activeDept, wlStatus]);
  const loadResults = useCallback(async () => { setLoading(true); try { const items = await procApi.listResults({ status:resultFilterStatus||undefined }); setResultsList(items||[]); } catch(e:any) { setError(e.message); } setLoading(false); }, [resultFilterStatus]);
  const loadQCData = useCallback(async () => { setLoading(true); try { const items = await procApi.listQC({ department:qcDept||undefined }); setQcList(items||[]); } catch(e:any) { console.error(e); } setLoading(false); }, [qcDept]);
  const loadAuditData = useCallback(async () => { setLoading(true); try { const items = await procApi.getAuditTrail(undefined,undefined,50); setAuditList(items||[]); } catch(e:any) { console.error(e); } setLoading(false); }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);
  useEffect(() => {
    if (activeTab==="worklist") loadWorklist();
    if (activeTab==="results") loadResults();
    if (activeTab==="qc") loadQCData();
    if (activeTab==="audit") loadAuditData();
  }, [activeTab, loadWorklist, loadResults, loadQCData, loadAuditData]);

  const loadCommentLibrary = async (dept:string) => { try { const lib = await procApi.getCommentLibrary(dept); setCommentLibrary(lib||[]); } catch { setCommentLibrary([]); } };

  const handleSync = async () => { setLoading(true); await Promise.all([loadDashboard(),loadWorklist(),loadResults(),loadQCData(),loadAuditData()]); setLoading(false); setSuccess("System synchronized."); };
  const handleStartProcessing = async (wl:WorklistItem) => { const tech=techName||"Default Tech"; try { await procApi.startProcessing(wl.id,tech); setTechName(tech); loadWorklist(); loadDashboard(); setSelectedItem(wl); setShowResultForm(true); loadCommentLibrary(wl.department); } catch(e:any) { setError(e.message); } };

  const handleSubmitResult = async () => {
    if (!selectedItem) return;
    if (!techName) { setError("Technician signature required."); return; }
    setLoading(true); setError("");
    try {
      await procApi.enterResult({ worklist_id:selectedItem.id, result_type:resultType, result_value:resultType==="NUMERIC"?resultNum:resultVal, result_numeric:resultType==="NUMERIC"?parseFloat(resultNum):undefined, result_unit:resultUnit||undefined, entered_by:techName, comments:resultComments||undefined, result_source:"MANUAL" });
      setSuccess(`Result recorded for ${selectedItem.barcode}.`);
      setShowResultForm(false); setSelectedItem(null); setResultVal(""); setResultNum(""); setResultComments("");
      loadWorklist(); loadDashboard();
    } catch(e:any) { setError(e.message); }
    setLoading(false);
  };

  const handleBatchSubmit = async () => {
    if (batchItems.length===0||!techName) { setError("Select items and provide technician name."); return; }
    setLoading(true);
    try {
      const items = batchItems.map(id => ({ worklist_id:id, result_type:"NUMERIC", result_value:"Normal", result_numeric:0 }));
      await procApi.batchEnterResults({ items, result_source:"BATCH_IMPORT", entered_by:techName });
      setSuccess(`Batch: ${batchItems.length} results submitted.`);
      setBatchItems([]); setBatchMode(false); loadWorklist(); loadDashboard();
    } catch(e:any) { setError(e.message); }
    setLoading(false);
  };

  const handleReviewResult = async (id:string) => { const r=prompt("Pathologist Name:")||"Pathologist"; try { await procApi.reviewResult(id,r,"Verified."); setSuccess("Result reviewed."); loadResults(); loadDashboard(); } catch(e:any) { setError(e.message); } };
  const handleValidateResult = async (id:string) => { const v=prompt("Validator Name:")||"Validator"; try { await procApi.validateResult(id,v,"Validated for release."); setSuccess("Result validated."); loadResults(); loadDashboard(); } catch(e:any) { setError(e.message); } };
  const handleReleaseResult = async (id:string) => { const r=prompt("Released By:")||"Lab Director"; try { await procApi.releaseResult(id,r,"Released to EMR/EHR."); setSuccess("Result released to EMR."); loadResults(); loadDashboard(); } catch(e:any) { setError(e.message); } };
  const handleRejectResult = async (id:string) => { const reason=prompt("Rejection Reason:"); if (!reason) return; try { await procApi.rejectResult(id,"Supervisor",reason); setSuccess("Result rejected."); loadResults(); loadDashboard(); } catch(e:any) { setError(e.message); } };

  const handleAddQC = async () => {
    if (!qcForm.actual||!qcForm.technician) { setError("QC value and technician required."); return; }
    setLoading(true);
    try {
      await procApi.recordQC({ department:qcDept, test_code:qcForm.test_code, test_name:qcForm.test_name, qc_lot_number:qcForm.lot, qc_level:qcForm.level, expected_value:parseFloat(qcForm.expected), expected_sd:parseFloat(qcForm.sd), actual_value:parseFloat(qcForm.actual), performed_by:qcForm.technician, remarks:"Daily control" });
      setSuccess("QC recorded."); setQcForm({...qcForm, actual:""}); loadQCData(); loadDashboard();
    } catch(e:any) { setError(e.message); }
    setLoading(false);
  };

  const handleAddComment = async (resultId:string) => { const text=prompt("Enter comment:"); if (!text) return; try { await procApi.addComment({ result_id:resultId, comment_text:text, added_by:techName||"Technician" }); setSuccess("Comment added."); } catch(e:any) { setError(e.message); } };

  const getStatusColor = (s:string) => {
    if (s.includes("PENDING")) return "bg-amber-100 text-amber-700 border-amber-200";
    if (s.includes("PROGRESS")) return "bg-blue-100 text-blue-700 border-blue-200";
    if (s==="RESULT_ENTERED") return "bg-indigo-100 text-indigo-700 border-indigo-200";
    if (s==="AWAITING_VALIDATION") return "bg-purple-100 text-purple-700 border-purple-200";
    if (s==="VALIDATED") return "bg-emerald-100 text-emerald-700 border-emerald-200";
    if (s==="RELEASED") return "bg-teal-100 text-teal-700 border-teal-200";
    if (s==="REJECTED") return "bg-rose-100 text-rose-700 border-rose-200";
    return "bg-slate-100 text-slate-700 border-slate-200";
  };

  const getStatusActions = (res:ResultEntry) => {
    const actions:Array<{label:string;action:()=>void;color:string}> = [];
    if (res.status==="RESULT_ENTERED") actions.push({ label:"Review", action:()=>handleReviewResult(res.id), color:"bg-blue-600 hover:bg-blue-700" });
    if (res.status==="AWAITING_VALIDATION") actions.push({ label:"Validate", action:()=>handleValidateResult(res.id), color:"bg-purple-600 hover:bg-purple-700" });
    if (res.status==="VALIDATED") actions.push({ label:"Release to EMR", action:()=>handleReleaseResult(res.id), color:"bg-emerald-600 hover:bg-emerald-700" });
    if (res.status!=="RELEASED"&&res.status!=="REJECTED") actions.push({ label:"Reject", action:()=>handleRejectResult(res.id), color:"bg-rose-600 hover:bg-rose-700" });
    actions.push({ label:"Comment", action:()=>handleAddComment(res.id), color:"bg-slate-600 hover:bg-slate-700" });
    return actions;
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <TopNav title="LIS: Test Processing & Result Entry Engine" />
      <div className="flex-1 p-6 max-w-[1400px] mx-auto w-full space-y-5">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Laboratory Processing Engine</h1>
            <p className="text-slate-400 font-bold uppercase tracking-[0.15em] text-[10px] mt-1">HL7 V2.5.1 &bull; ASTM E1394 &bull; ISO 15189 Compliant</p>
          </div>
          <div className="flex items-center gap-3">
            <input type="text" placeholder="Technician Name..." value={techName} onChange={e=>setTechName(e.target.value)} className="px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-bold outline-none w-48 focus:ring-2 focus:ring-indigo-100" />
            <button onClick={handleSync} disabled={loading} className="btn btn-secondary flex items-center gap-2 shadow-sm cursor-pointer">
              {loading?<Loader2 size={16} className="animate-spin"/>:<RefreshCw size={16}/>} Sync
            </button>
          </div>
        </div>

        {/* Alerts */}
        {error && <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded-xl flex items-center justify-between text-xs font-bold"><div className="flex items-center gap-2"><AlertCircle size={14}/>{error}</div><button onClick={()=>setError("")} className="cursor-pointer"><XCircle size={16}/></button></div>}
        {success && <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-xl flex items-center justify-between text-xs font-bold"><div className="flex items-center gap-2"><CheckCircle2 size={14}/>{success}</div><button onClick={()=>setSuccess("")} className="cursor-pointer"><XCircle size={16}/></button></div>}

        {/* Tabs */}
        <div className="flex p-1 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-x-auto">
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
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {[
                {l:"Pending",v:stats?.total_pending||0,icon:Clock,c:"text-amber-600",bg:"bg-amber-50"},
                {l:"In Progress",v:stats?.in_progress||0,icon:Play,c:"text-blue-600",bg:"bg-blue-50"},
                {l:"Results Entered",v:stats?.results_entered||0,icon:FileText,c:"text-indigo-600",bg:"bg-indigo-50"},
                {l:"Awaiting Valid.",v:stats?.awaiting_validation||0,icon:Eye,c:"text-purple-600",bg:"bg-purple-50"},
                {l:"Critical Flags",v:stats?.critical_flags||0,icon:AlertTriangle,c:"text-rose-600",bg:"bg-rose-50"},
                {l:"Delta Alerts",v:stats?.delta_alerts||0,icon:Zap,c:"text-orange-600",bg:"bg-orange-50"},
                {l:"QC Failures",v:stats?.qc_failures||0,icon:Shield,c:"text-slate-600",bg:"bg-slate-100"},
              ].map((m,i)=>(
                <div key={i} className="card p-4 flex flex-col items-center text-center hover:scale-[1.02] transition-transform cursor-pointer bg-white">
                  <div className={`p-3 rounded-xl ${m.bg} mb-2`}><m.icon size={20} className={m.c}/></div>
                  <div className="text-2xl font-black text-slate-800 tabular-nums">{m.v}</div>
                  <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{m.l}</div>
                </div>
              ))}
            </div>

            {/* Status Workflow Diagram */}
            <div className="card p-6 bg-white">
              <h3 className="font-black text-sm text-slate-900 uppercase tracking-wider mb-4">Result Status Lifecycle</h3>
              <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {STATUS_FLOW.map((s,i)=>(
                  <React.Fragment key={s}>
                    <div className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider border whitespace-nowrap ${getStatusColor(s)}`}>{s.replace(/_/g," ")}</div>
                    {i<STATUS_FLOW.length-1&&<ArrowRight size={16} className="text-slate-300 shrink-0"/>}
                  </React.Fragment>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              <div className="lg:col-span-2 card p-6 bg-white">
                <h3 className="font-black text-sm text-slate-900 mb-4">Department Load Distribution</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {DEPARTMENTS.slice(0,6).map(dept=>(
                    <div key={dept} className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 hover:border-indigo-200 transition-colors cursor-pointer group">
                      <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest group-hover:text-indigo-600">{dept.replace(/_/g," ")}</span>
                      <div className="flex items-end justify-between mt-2">
                        <span className="text-2xl font-black text-indigo-600 tabular-nums">{stats?.department_counts?.[dept]||0}</span>
                        <div className="h-8 w-1.5 bg-indigo-100 rounded-full overflow-hidden"><div className="bg-indigo-500 opacity-60 rounded-full" style={{height:`${Math.min(100,(stats?.department_counts?.[dept]||0)*10)}%`}}/></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-slate-900 rounded-2xl p-6 text-white shadow-xl space-y-4">
                <div><h3 className="font-black text-lg">Analyzer Hub</h3><p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">HL7/ASTM Integration</p></div>
                {[{l:"Sync Analyzers",icon:RefreshCw},{l:"Run Daily QC",icon:Shield},{l:"Batch Validation",icon:Layers},{l:"Import Results",icon:Upload}].map((btn,i)=>(
                  <button key={i} onClick={()=>setSuccess(`[${btn.l}] initiated.`)} className="w-full flex items-center justify-between p-3 bg-white/5 hover:bg-white/10 border border-white/5 rounded-xl transition-all cursor-pointer group">
                    <div className="flex items-center gap-3"><div className="p-2 bg-slate-800 rounded-lg"><btn.icon size={16}/></div><span className="text-xs font-bold">{btn.l}</span></div>
                    <ArrowRight size={12} className="opacity-20 group-hover:opacity-100 group-hover:translate-x-1 transition-all"/>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══ TAB 2: WORKLIST ═══ */}
        {activeTab==="worklist"&&(
          <div className="card bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="p-5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-600 rounded-lg text-white"><ClipboardList size={18}/></div>
                <h3 className="text-sm font-black text-slate-900 uppercase">Processing Queue</h3>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={()=>setBatchMode(!batchMode)} className={`btn btn-sm cursor-pointer ${batchMode?"bg-indigo-600 text-white":"btn-secondary"}`}>{batchMode?"Exit Batch":"Batch Mode"}</button>
                {batchMode&&batchItems.length>0&&<button onClick={handleBatchSubmit} className="btn btn-sm bg-emerald-600 text-white cursor-pointer">Submit Batch ({batchItems.length})</button>}
                <select className="input-field w-auto text-[10px] font-bold py-1.5 cursor-pointer" value={activeDept} onChange={e=>setActiveDept(e.target.value)}>
                  <option value="">All Departments</option>
                  {DEPARTMENTS.map(d=><option key={d} value={d}>{d.replace(/_/g," ")}</option>)}
                </select>
                <select className="input-field w-auto text-[10px] font-bold py-1.5 cursor-pointer" value={wlStatus} onChange={e=>setWlStatus(e.target.value)}>
                  <option value="PENDING">Pending</option><option value="IN_PROGRESS">In Progress</option><option value="RESULT_ENTERED">Result Entered</option>
                </select>
              </div>
            </div>
            <div className="overflow-x-auto"><table className="w-full text-left">
              <thead><tr className="bg-slate-50 border-b border-slate-100">
                {batchMode&&<th className="py-3 px-4"/>}
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Specimen</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Patient</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Test</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Dept</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Priority</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Status</th>
                <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase text-right">Actions</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {worklist.length===0?<tr><td colSpan={batchMode?8:7} className="py-16 text-center text-slate-400 text-xs font-bold uppercase">No items in queue.</td></tr>:
                worklist.map(item=>(
                  <tr key={item.id} className="hover:bg-slate-50 transition-colors group">
                    {batchMode&&<td className="py-4 px-4"><input type="checkbox" checked={batchItems.includes(item.id)} onChange={e=>{if(e.target.checked)setBatchItems([...batchItems,item.id]);else setBatchItems(batchItems.filter(x=>x!==item.id));}} className="cursor-pointer w-4 h-4 accent-indigo-600"/></td>}
                    <td className="py-4 px-5"><div className="font-black text-slate-900 text-xs">{item.barcode}</div><div className="text-[10px] text-slate-400">{item.sample_type}</div></td>
                    <td className="py-4 px-5"><div className="font-bold text-slate-800 text-xs">{item.patient_name||"—"}</div><div className="text-[10px] text-indigo-500 font-bold">{item.patient_uhid||"—"}</div></td>
                    <td className="py-4 px-5"><div className="font-black text-slate-900 text-xs">{item.test_name}</div><span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded font-bold text-slate-500">{item.test_code}</span></td>
                    <td className="py-4 px-5 text-[10px] font-bold text-slate-500 uppercase">{item.department.replace(/_/g," ")}</td>
                    <td className="py-4 px-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${item.priority==="STAT"?"bg-rose-50 text-rose-600 border-rose-200 animate-pulse":"bg-slate-100 text-slate-500 border-slate-200"}`}>{item.priority}</span></td>
                    <td className="py-4 px-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${getStatusColor(item.status)}`}>{item.status.replace(/_/g," ")}</span></td>
                    <td className="py-4 px-5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase transition-all cursor-pointer active:scale-95 ${item.status==="PENDING"?"bg-slate-900 text-white hover:bg-black":"bg-indigo-600 text-white hover:bg-indigo-700"}`} onClick={()=>item.status==="PENDING"?handleStartProcessing(item):(setSelectedItem(item),setShowResultForm(true),loadCommentLibrary(item.department))}>{item.status==="PENDING"?"Start":"Enter Result"}</button>
                        <button onClick={()=>setSuccess(`Viewing ${item.barcode}`)} className="p-1.5 bg-slate-100 text-slate-400 hover:text-indigo-600 rounded-lg cursor-pointer"><Eye size={16}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </div>
        )}

        {/* ═══ TAB 3: RESULT REVIEW (Full Lifecycle) ═══ */}
        {activeTab==="results"&&(
          <div className="space-y-5">
            <div className="flex items-center justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div><h3 className="text-lg font-black text-slate-900">Result Validation & Release Queue</h3><p className="text-[10px] text-slate-400 font-bold uppercase mt-1">Full lifecycle: Review → Validate → Release</p></div>
              <select className="input-field w-auto text-[10px] font-bold py-1.5 cursor-pointer" value={resultFilterStatus} onChange={e=>setResultFilterStatus(e.target.value)}>
                <option value="">All Results</option><option value="RESULT_ENTERED">Pending Review</option><option value="AWAITING_VALIDATION">Awaiting Validation</option><option value="VALIDATED">Validated</option><option value="RELEASED">Released</option>
              </select>
            </div>
            <div className="overflow-x-auto card bg-white rounded-2xl">
              <table className="w-full text-left">
                <thead><tr className="bg-slate-50 border-b border-slate-100">
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Test</th>
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Patient</th>
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Result</th>
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Reference</th>
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Flags</th>
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Delta</th>
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Status</th>
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase">Source</th>
                  <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase text-right">Workflow Actions</th>
                </tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {resultsList.length===0?<tr><td colSpan={9} className="py-16 text-center text-slate-400 text-xs font-bold uppercase">No results found.</td></tr>:
                  resultsList.map(res=>(
                    <tr key={res.id} className="hover:bg-slate-50 transition-colors group">
                      <td className="py-4 px-5"><div className="font-black text-slate-900 text-xs">{res.test_name}</div><span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded font-bold text-slate-500">{res.test_code}</span></td>
                      <td className="py-4 px-5 text-[10px] font-bold text-slate-600">{res.patient_id.toString().slice(0,8)}</td>
                      <td className="py-4 px-5"><span className="font-black text-lg text-slate-900 tabular-nums">{res.result_numeric??res.result_value}</span> <span className="text-[10px] text-slate-400 font-bold">{res.result_unit}</span></td>
                      <td className="py-4 px-5 text-[10px] font-bold text-slate-500 tabular-nums">{res.reference_low!==null&&res.reference_high!==null?`${res.reference_low} – ${res.reference_high}`:"-"}</td>
                      <td className="py-4 px-5">{res.flags&&res.flags.length>0?res.flags.map((f,i)=>(<span key={i} className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-black uppercase mr-1 ${f.is_critical?"bg-rose-100 text-rose-700 animate-pulse":"bg-amber-100 text-amber-700"}`}>{f.flag_type.replace(/_/g," ")}</span>)):<span className="text-[10px] text-emerald-600 font-bold">Normal</span>}</td>
                      <td className="py-4 px-5">{res.delta?(<span className={`text-[10px] font-black ${res.delta.is_significant?"text-rose-600":"text-slate-500"}`}>{res.delta.delta_percent}% {res.delta.is_significant?"⚠":"✓"}</span>):<span className="text-[10px] text-slate-400">—</span>}</td>
                      <td className="py-4 px-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${getStatusColor(res.status)}`}>{res.status.replace(/_/g," ")}</span></td>
                      <td className="py-4 px-5 text-[10px] font-bold text-slate-500">{res.result_source.replace(/_/g," ")}</td>
                      <td className="py-4 px-5 text-right">
                        <div className="flex items-center justify-end gap-1.5 flex-wrap">
                          {getStatusActions(res).map((a,i)=>(<button key={i} onClick={a.action} className={`px-2.5 py-1 rounded-lg text-[9px] font-bold text-white cursor-pointer active:scale-95 transition-all ${a.color}`}>{a.label}</button>))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═══ TAB 4: QUALITY CONTROL ═══ */}
        {activeTab==="qc"&&(
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="card p-6 bg-white">
              <div className="flex items-center gap-2 mb-6"><Shield size={20} className="text-indigo-600"/><h3 className="font-black text-sm text-slate-900">QC Entry</h3></div>
              <div className="space-y-4">
                <div><label className="text-[10px] font-black text-slate-400 uppercase mb-1 block">Department</label><select value={qcDept} onChange={e=>setQcDept(e.target.value)} className="input-field text-xs font-bold cursor-pointer">{DEPARTMENTS.map(d=><option key={d} value={d}>{d.replace(/_/g," ")}</option>)}</select></div>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="text-[10px] font-black text-slate-400 uppercase mb-1 block">Control Lot</label><input value={qcForm.lot} onChange={e=>setQcForm({...qcForm,lot:e.target.value})} className="input-field text-xs font-bold"/></div>
                  <div><label className="text-[10px] font-black text-slate-400 uppercase mb-1 block">Expected Mean</label><input type="number" value={qcForm.expected} onChange={e=>setQcForm({...qcForm,expected:e.target.value})} className="input-field text-xs font-bold"/></div>
                </div>
                <div><label className="text-[10px] font-black text-indigo-600 uppercase mb-1 block text-center">Actual Value</label><input type="number" value={qcForm.actual} onChange={e=>setQcForm({...qcForm,actual:e.target.value})} placeholder="0.00" className="input-field text-3xl font-black text-center py-6 border-2 border-indigo-300 focus:border-indigo-600"/></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase mb-1 block">Technician</label><input value={qcForm.technician} onChange={e=>setQcForm({...qcForm,technician:e.target.value})} placeholder="Initials..." className="input-field text-xs font-bold"/></div>
                <button onClick={handleAddQC} disabled={loading} className="w-full py-3 bg-slate-900 text-white rounded-xl font-black text-xs uppercase tracking-wider hover:bg-black active:scale-95 disabled:opacity-50 cursor-pointer">Record QC</button>
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-[10px] text-amber-800 font-bold"><AlertTriangle size={12} className="inline mr-1"/>QC failures will block result release for associated tests.</div>
              </div>
            </div>
            <div className="lg:col-span-2 card bg-white overflow-hidden">
              <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Levey-Jennings Registry</span>
                <div className="flex items-center gap-1"><div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"/><span className="text-[9px] font-black text-slate-500 uppercase">Live</span></div>
              </div>
              <div className="overflow-x-auto"><table className="w-full text-left">
                <thead><tr className="border-b border-slate-100 text-[10px] font-black text-slate-400 uppercase">
                  <th className="py-3 px-5">Date/Lot</th><th className="py-3 px-5">Expected ±SD</th><th className="py-3 px-5">Actual</th><th className="py-3 px-5">Deviation</th><th className="py-3 px-5 text-right">Status</th>
                </tr></thead>
                <tbody className="divide-y divide-slate-50">
                  {qcList.length===0?<tr><td colSpan={5} className="py-16 text-center text-slate-400 text-xs font-bold">No QC records.</td></tr>:
                  qcList.map(qc=>(
                    <tr key={qc.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-5"><div className="text-xs font-bold text-slate-800">{new Date(qc.performed_at!).toLocaleDateString()}</div><div className="text-[9px] text-slate-400">{qc.qc_lot_number}</div></td>
                      <td className="py-3 px-5 text-xs font-bold text-slate-500 tabular-nums">{qc.expected_value} ±{qc.expected_sd}</td>
                      <td className="py-3 px-5"><span className={`text-sm font-black tabular-nums ${qc.status==="FAIL"?"text-rose-600":"text-slate-900"}`}>{qc.actual_value}</span></td>
                      <td className="py-3 px-5"><div className="h-1.5 w-20 bg-slate-100 rounded-full overflow-hidden"><div className={`h-full ${qc.status==="PASS"?"bg-emerald-500":qc.status==="FAIL"?"bg-rose-500":"bg-amber-500"}`} style={{width:`${Math.min(100,Math.abs(qc.actual_value-qc.expected_value)/(qc.expected_sd||1)*20)}%`}}/></div></td>
                      <td className="py-3 px-5 text-right"><span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${qc.status==="PASS"?"bg-emerald-50 text-emerald-700 border-emerald-200":qc.status==="FAIL"?"bg-rose-50 text-rose-700 border-rose-200":"bg-amber-50 text-amber-700 border-amber-200"}`}>{qc.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table></div>
            </div>
          </div>
        )}

        {/* ═══ TAB 5: AUDIT TRAIL ═══ */}
        {activeTab==="audit"&&(
          <div className="card bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/30">
              <div className="flex items-center gap-3"><History size={20} className="text-indigo-600"/><div><h3 className="font-black text-sm text-slate-900">Audit Trail</h3><p className="text-[10px] text-slate-400 font-bold uppercase">Immutable • CFR Part 11 Compliant</p></div></div>
              <button onClick={()=>{setSuccess("Audit export started.");setTimeout(()=>alert("Report generated."),200);}} className="btn btn-sm btn-secondary cursor-pointer"><Download size={14}/> Export</button>
            </div>
            <div className="overflow-x-auto"><table className="w-full text-left">
              <thead><tr className="border-b border-slate-100 text-[10px] font-black text-slate-400 uppercase">
                <th className="py-3 px-5">Timestamp</th><th className="py-3 px-5">Entity</th><th className="py-3 px-5">Action</th><th className="py-3 px-5">User</th><th className="py-3 px-5 text-right">Details</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {auditList.length===0?<tr><td colSpan={5} className="py-16 text-center text-slate-400 text-xs font-bold">No audit events.</td></tr>:
                auditList.map((log,i)=>(
                  <tr key={i} className="hover:bg-slate-50 transition-colors group">
                    <td className="py-3 px-5 text-[10px] font-mono text-slate-400">{new Date(log.performed_at!).toLocaleString()}</td>
                    <td className="py-3 px-5"><div className="text-xs font-black text-slate-700 uppercase">{log.entity_type}</div><div className="text-[9px] text-indigo-400">{log.entity_id.slice(0,12)}</div></td>
                    <td className="py-3 px-5"><div className="flex items-center gap-1.5"><div className={`w-2 h-2 rounded-full ${log.action.includes("CREATE")?"bg-emerald-500":log.action.includes("REJECT")?"bg-rose-500":log.action.includes("RELEASE")?"bg-teal-500":"bg-blue-500"}`}/><span className="text-[10px] font-black text-slate-900 uppercase">{log.action.replace(/_/g," ")}</span></div></td>
                    <td className="py-3 px-5 text-[10px] font-bold text-slate-600">{log.performed_by||"System"}</td>
                    <td className="py-3 px-5 text-right"><button onClick={()=>setSuccess(`Audit detail: ${log.action}`)} className="p-1 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-indigo-600 cursor-pointer"><Eye size={14}/></button></td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </div>
        )}

        {/* ═══ TAB 6: CONFIGURATIONS ═══ */}
        {activeTab==="settings"&&(
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {title:"Reference Ranges",desc:"Configure normal/critical value thresholds per test code for abnormal detection engine.",icon:Sliders,action:"Configure Standards"},
              {title:"Instrument Drivers",desc:"Manage HL7/ASTM analyzer connectivity strings and bi-directional result mapping.",icon:Cpu,action:"Manage Linkages"},
              {title:"Delta Thresholds",desc:"Set percentage-based delta check limits per test. Alerts trigger when exceeded.",icon:ArrowUpDown,action:"Configure Deltas"},
              {title:"Comment Libraries",desc:"Manage department-specific predefined comment templates for standardized remarks.",icon:MessageSquare,action:"Edit Libraries"},
            ].map((cfg,i)=>(
              <div key={i} className="card p-8 bg-white flex flex-col items-center text-center gap-5 hover:scale-[1.01] transition-transform cursor-pointer group">
                <div className="p-6 bg-slate-900 text-white rounded-2xl group-hover:bg-indigo-600 transition-colors shadow-xl"><cfg.icon size={36}/></div>
                <h3 className="text-xl font-black text-slate-900">{cfg.title}</h3>
                <p className="text-sm text-slate-400 max-w-xs">{cfg.desc}</p>
                <button onClick={()=>setSuccess(`[${cfg.action}] opened.`)} className="btn btn-secondary rounded-full px-8 py-3 text-xs font-black uppercase tracking-wider shadow cursor-pointer active:scale-95">{cfg.action}</button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ═══ RESULT ENTRY MODAL ═══ */}
      {showResultForm&&selectedItem&&(
        <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-3xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-6 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-indigo-600 rounded-xl"><FlaskConical size={24}/></div>
                <div><div className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">Result Entry</div><h3 className="text-xl font-black">{selectedItem.test_name}</h3><div className="flex gap-3 mt-1"><span className="text-[10px] bg-white/10 px-2 py-0.5 rounded font-bold">{selectedItem.barcode}</span><span className="text-[10px] text-indigo-300 font-bold">{selectedItem.sample_type} • {selectedItem.department.replace(/_/g," ")}</span></div></div>
              </div>
              <button onClick={()=>{setShowResultForm(false);setSelectedItem(null);}} className="p-2 bg-white/10 hover:bg-rose-500 rounded-xl cursor-pointer"><XCircle size={24}/></button>
            </div>
            <div className="p-6 overflow-y-auto space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div><label className="text-[10px] font-black text-slate-400 uppercase mb-1 block">Technician *</label><input value={techName} onChange={e=>setTechName(e.target.value)} placeholder="E-signature..." className="input-field text-sm font-bold"/></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase mb-1 block">Result Type</label><select value={resultType} onChange={e=>setResultType(e.target.value)} className="input-field text-xs font-bold cursor-pointer">{RESULT_TYPES.map(t=><option key={t} value={t}>{t}</option>)}</select></div>
              </div>
              <div>
                <label className="text-[10px] font-black text-indigo-600 uppercase mb-2 block text-center">Result Value *</label>
                {resultType==="NUMERIC"?<input type="number" step="any" autoFocus value={resultNum} onChange={e=>setResultNum(e.target.value)} placeholder="0.00" className="w-full px-6 py-10 border-2 border-indigo-200 rounded-2xl text-6xl font-black text-center outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 tabular-nums"/>
                :<textarea autoFocus value={resultVal} onChange={e=>setResultVal(e.target.value)} placeholder="Enter qualitative findings..." className="input-field text-sm font-bold h-40"/>}
              </div>
              {resultType==="NUMERIC"&&<div><label className="text-[10px] font-black text-slate-400 uppercase mb-1 block">Unit</label><input value={resultUnit} onChange={e=>setResultUnit(e.target.value)} placeholder="mg/dL, g/dL, etc." className="input-field text-xs font-bold"/></div>}
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase mb-1 block">Comments / Remarks</label>
                <textarea value={resultComments} onChange={e=>setResultComments(e.target.value)} placeholder="Add remarks..." className="input-field text-xs font-bold h-20" />
                {commentLibrary.length>0&&<div className="flex flex-wrap gap-1.5 mt-2">{commentLibrary.map((c,i)=>(<button key={i} onClick={()=>setResultComments(prev=>prev?prev+"; "+c:c)} className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-[9px] font-bold hover:bg-indigo-100 hover:text-indigo-700 cursor-pointer transition-colors">{c}</button>))}</div>}
              </div>
              <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl text-[11px] text-indigo-800 font-bold"><Shield size={14} className="inline mr-1.5"/>Abnormal detection, delta checks, and audit logging are automatic upon submission.</div>
            </div>
            <div className="p-5 bg-slate-50 border-t border-slate-100 flex gap-3">
              <button onClick={()=>{setShowResultForm(false);setSelectedItem(null);}} className="flex-1 py-3 text-xs font-bold text-slate-400 hover:text-rose-600 rounded-xl cursor-pointer">Cancel</button>
              <button onClick={handleSubmitResult} disabled={loading} className="flex-[2] py-3 bg-slate-900 text-white font-black text-xs uppercase rounded-xl hover:bg-black active:scale-95 disabled:opacity-50 cursor-pointer shadow-lg">{loading?"Processing...":"Submit Result"}</button>
            </div>
          </div>
        </div>
      )}

      <style jsx global>{`
        .scroller-hide::-webkit-scrollbar{display:none}
        .scroller-hide{-ms-overflow-style:none;scrollbar-width:none}
      `}</style>
    </div>
  );
}
