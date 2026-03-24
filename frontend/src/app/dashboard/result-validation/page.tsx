"use client";
import React, { useEffect, useState, useMemo, useCallback } from "react";
import {
  CheckCircle2, XCircle, AlertCircle, RefreshCw, Shield, Bell, Clock,
  AlertTriangle, Loader2, FlaskConical, Eye, CheckSquare, Settings,
  ClipboardList, Activity, ArrowUpRight, ArrowDownRight, Edit2, Archive, MessageSquare, BarChart3, Users
} from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { validationApi, ValidationWorklist, ValidationPerformance } from "@/lib/validation-api";

type TabTypes = "worklist"|"batch_approval"|"performance"|"rejected";
const DEPARTMENTS = ["BIOCHEMISTRY","HEMATOLOGY","CLINICAL_PATHOLOGY","SEROLOGY","MICROBIOLOGY","IMMUNOLOGY"];
const STAGES = ["PENDING_TECH", "PENDING_SENIOR", "PENDING_PATHOLOGIST", "APPROVED", "REJECTED"];
const PRIORITIES = ["CRITICAL", "URGENT", "ABNORMAL", "NORMAL"];
const VALIDATOR_INFO = { id: "USR-001", name: "Dr. Jane Smith", role: "PATHOLOGIST" }; // Mocked logged-in user

// Priority Color Maps
const priorityColors: Record<string, string> = {
  CRITICAL: "bg-rose-100 text-rose-800 border-rose-300 shadow-[0_0_10px_rgba(225,29,72,0.2)] animate-pulse",
  URGENT: "bg-orange-100 text-orange-800 border-orange-300",
  ABNORMAL: "bg-amber-100 text-amber-800 border-amber-300",
  NORMAL: "bg-emerald-50 text-emerald-700 border-emerald-200"
};

export default function ResultValidationPage() {
  const [activeTab, setActiveTab] = useState<TabTypes>("worklist");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [worklists, setWorklists] = useState<ValidationWorklist[]>([]);
  const [metrics, setMetrics] = useState<ValidationPerformance|null>(null);

  // Filters
  const [deptFilter, setDeptFilter] = useState("");
  const [stageFilter, setStageFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");

  // Modals & Batch
  const [selectedWorklist, setSelectedWorklist] = useState<ValidationWorklist|null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [correctionMode, setCorrectionMode] = useState(false);
  const [newResultValue, setNewResultValue] = useState("");
  const [remarks, setRemarks] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  
  const [batchSelections, setBatchSelections] = useState<Set<string>>(new Set());

  const fetchWorklist = useCallback(async () => {
    setLoading(true);
    try {
      const w = await validationApi.getWorklists({ department: deptFilter, stage: stageFilter, priority: priorityFilter });
      setWorklists(w || []);
    } catch(e:any) { setError(e.message); }
    setLoading(false);
  }, [deptFilter, stageFilter, priorityFilter]);

  const fetchMetrics = useCallback(async () => {
    try { const m = await validationApi.getMetrics(); setMetrics(m); } catch(e:any) { console.error(e); }
  }, []);

  useEffect(() => {
    fetchWorklist();
    if (activeTab === "performance") fetchMetrics();
  }, [fetchWorklist, activeTab, fetchMetrics]);

  const toggleBatchSelect = (id: string) => {
    const newSet = new Set(batchSelections);
    if(newSet.has(id)) newSet.delete(id); else newSet.add(id);
    setBatchSelections(newSet);
  };

  const handleApprove = async (id: string, sName: string) => {
    try {
      await validationApi.approve(id, { validator_id: VALIDATOR_INFO.id, validator_name: VALIDATOR_INFO.name, stage_name: sName, remarks });
      setSuccess("Result approved and advanced to next stage.");
      setReviewModalOpen(false); setRemarks(""); fetchWorklist();
    } catch(e:any) { setError(e.message); }
  };

  const handleCorrect = async (id: string, sName: string) => {
    if (!newResultValue) return setError("New result value is required.");
    try {
      await validationApi.correct(id, { validator_id: VALIDATOR_INFO.id, validator_name: VALIDATOR_INFO.name, stage_name: sName, new_value: newResultValue, remarks });
      setSuccess("Result corrected successfully.");
      setCorrectionMode(false); fetchWorklist();
    } catch(e:any) { setError(e.message); }
  };

  const handleReject = async (id: string) => {
    if (!rejectionReason) return setError("Rejection reason is required.");
    try {
      await validationApi.reject(id, { validator_id: VALIDATOR_INFO.id, validator_name: VALIDATOR_INFO.name, rejection_reason: rejectionReason, action_taken: "SENT_FOR_RETEST" });
      setSuccess("Result rejected and sent back to processing.");
      setRejectModalOpen(false); setReviewModalOpen(false); setRejectionReason(""); fetchWorklist();
    } catch(e:any) { setError(e.message); }
  };

  const handleBatchApprove = async () => {
    if(batchSelections.size===0) return setError("No items selected for batch validation.");
    try {
      await validationApi.batchApprove(Array.from(batchSelections), VALIDATOR_INFO.id, VALIDATOR_INFO.name, VALIDATOR_INFO.role);
      setSuccess(`Batch approved ${batchSelections.size} non-critical results.`);
      setBatchSelections(new Set()); fetchWorklist(); activeTab==="batch_approval" && setActiveTab("worklist");
    } catch(e:any) { setError(e.message); }
  };

  const openReview = (w: ValidationWorklist) => { setSelectedWorklist(w); setNewResultValue(w.result_value||""); setRemarks(""); setCorrectionMode(false); setReviewModalOpen(true); };

  const tabs = [
    { id: "worklist", label: "Pending Review", icon: ClipboardList },
    { id: "batch_approval", label: "Batch Sign-Off", icon: CheckSquare },
    { id: "rejected", label: "Rejected Inbox", icon: Archive },
    { id: "performance", label: "Validation Analytics", icon: BarChart3 },
  ];

  const filteredWorklists = useMemo(() => {
    if (activeTab === "rejected") return worklists.filter(w => w.validation_stage === "REJECTED");
    if (activeTab === "batch_approval") return worklists.filter(w => w.priority_level !== "CRITICAL" && w.validation_stage !== "APPROVED" && w.validation_stage !== "REJECTED");
    return worklists.filter(w => w.validation_stage !== "REJECTED" && w.validation_stage !== "APPROVED");
  }, [activeTab, worklists]);

  const metricsCards = [
    {l:"Total Validated (24H)",v:metrics?.total_validated||0,icon:CheckCircle2,c:"text-emerald-600",bg:"bg-emerald-50"},
    {l:"Validations Rejected",v:metrics?.total_rejected||0,icon:XCircle,c:"text-rose-600",bg:"bg-rose-50"},
    {l:"Critical Alerts Handled",v:metrics?.critical_alerts||0,icon:AlertTriangle,c:"text-rose-600",bg:"bg-rose-50"},
    {l:"Avg Turnaround Time",v:`${metrics?.avg_turnaround_time_mins||0} m`,icon:Clock,c:"text-indigo-600",bg:"bg-indigo-50"}
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <TopNav title="LIS Result Validation & Approval Engine" />
      <div className="flex-1 p-6 max-w-[1400px] mx-auto w-full space-y-5">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
           <div>
              <h1 className="text-2xl font-black text-slate-900 tracking-tight">Validation Command Center</h1>
              <p className="text-slate-400 font-bold uppercase tracking-[0.15em] text-[10px] mt-1">Multi-Level Clinical Approval Workflow</p>
           </div>
           <div className="flex items-center gap-3">
              <div className="flex flex-col items-end text-right px-4 py-1.5 border-r border-slate-200">
                <span className="text-[10px] uppercase font-black text-slate-400">Current Session</span>
                <span className="text-xs font-bold text-slate-800">{VALIDATOR_INFO.name} ({VALIDATOR_INFO.role})</span>
              </div>
              <button onClick={fetchWorklist} disabled={loading} className="btn btn-secondary cursor-pointer">
                 {loading?<Loader2 size={16} className="animate-spin"/>:<RefreshCw size={16}/>} Sync Queue
              </button>
           </div>
        </div>

        {/* Alerts */}
        {error && <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded-xl flex items-center justify-between text-xs font-bold"><div className="flex items-center gap-2"><AlertCircle size={14}/>{error}</div><button onClick={()=>setError("")}><XCircle size={16}/></button></div>}
        {success && <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-xl flex items-center justify-between text-xs font-bold"><div className="flex items-center gap-2"><CheckCircle2 size={14}/>{success}</div><button onClick={()=>setSuccess("")}><XCircle size={16}/></button></div>}

        {/* Tabs & Global Filters */}
        <div className="flex justify-between items-center bg-white p-1 border border-slate-200 rounded-2xl shadow-sm">
           <div className="flex overflow-x-auto scroller-hide">
             {tabs.map(tab=>(
                <button key={tab.id} onClick={()=>setActiveTab(tab.id as TabTypes)} className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-[11px] font-black uppercase tracking-wider transition-all whitespace-nowrap cursor-pointer ${activeTab===tab.id?"bg-slate-900 text-white shadow-lg":"text-slate-500 hover:text-slate-900 hover:bg-slate-100"}`}>
                   <tab.icon size={15}/>{tab.label}
                   {tab.id==="worklist"&&<span className={`px-1.5 py-0.5 rounded-full text-[9px] font-black ml-1 ${activeTab===tab.id?"bg-indigo-500 text-white":"bg-indigo-100 text-indigo-600"}`}>{worklists.filter(w=>w.validation_stage!=="APPROVED"&&w.validation_stage!=="REJECTED").length}</span>}
                </button>
             ))}
           </div>
           
           {activeTab!=="performance"&&<div className="flex gap-2 px-2 hidden md:flex">
             <select className="input-field py-1.5 text-[10px] w-auto font-bold uppercase truncate max-w-[120px]" value={deptFilter} onChange={e=>setDeptFilter(e.target.value)}>
                <option value="">All Depts</option>{DEPARTMENTS.map(d=><option key={d} value={d}>{d}</option>)}
             </select>
             <select className="input-field py-1.5 text-[10px] w-auto font-bold uppercase truncate max-w-[130px]" value={stageFilter} onChange={e=>setStageFilter(e.target.value)}>
                <option value="">All Stages</option>{STAGES.map(s=><option key={s} value={s}>{s.replace("PENDING_","")}</option>)}
             </select>
             <select className="input-field py-1.5 text-[10px] w-auto font-bold uppercase truncate max-w-[120px]" value={priorityFilter} onChange={e=>setPriorityFilter(e.target.value)}>
                <option value="">All Priorities</option>{PRIORITIES.map(p=><option key={p} value={p}>{p}</option>)}
             </select>
           </div>}
        </div>

        {/* ═══ TAB: PERFORMANCE ANALYTICS ═══ */}
        {activeTab==="performance"&&(
          <div className="space-y-6">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
               {metricsCards.map((m,i)=>(
                 <div key={i} className="card p-5 bg-white flex flex-col items-center text-center">
                    <div className={`p-3 rounded-full ${m.bg} mb-3`}><m.icon size={24} className={m.c}/></div>
                    <div className="text-3xl font-black text-slate-800 tabular-nums">{m.v}</div>
                    <div className="text-[10px] font-black text-slate-400 uppercase mt-1">{m.l}</div>
                 </div>
               ))}
            </div>
            <div className="card p-6 bg-white space-y-4">
               <h3 className="font-black text-sm text-slate-800 uppercase flex items-center gap-2"><Users size={16}/> Validator Workload Distribution</h3>
               <div className="space-y-3 mt-4">
                  {metrics?.workload_distribution && Object.entries(metrics.workload_distribution).length > 0 ? Object.entries(metrics.workload_distribution).map(([name, count])=>(
                     <div key={name}>
                        <div className="flex justify-between text-xs font-bold mb-1"><span>{name}</span><span>{count} records</span></div>
                        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden"><div className="bg-indigo-500 h-full" style={{width:`${Math.min(100,(count as number/100)*100)}%`}}/></div>
                     </div>
                  )) : (
                     <div className="text-xs text-slate-400 font-bold py-4 text-center">No validations recorded in the selected period.</div>
                  )}
               </div>
            </div>
          </div>
        )}

        {/* ═══ TAB: BATCH APPROVAL / WORKLIST / REJECTED ═══ */}
        {activeTab!=="performance"&&(
          <div className="card bg-white rounded-2xl overflow-hidden shadow-sm">
             {activeTab==="batch_approval"&&(
               <div className="bg-indigo-50 p-4 border-b border-indigo-100 flex items-center justify-between">
                  <div className="flex items-center gap-3"><CheckSquare size={18} className="text-indigo-600"/><div><h3 className="text-sm font-black text-indigo-900 uppercase">Mass Validation Mode</h3><p className="text-[10px] text-indigo-700/70 font-bold mt-0.5">Critical results are automatically hidden from batch select to enforce mandatory individual review.</p></div></div>
                  <button onClick={handleBatchApprove} className="btn bg-indigo-600 text-white font-black uppercase text-[10px] px-6">Sign-Off Selected ({batchSelections.size})</button>
               </div>
             )}
             
             <div className="overflow-x-auto"><table className="w-full text-left">
               <thead><tr className="bg-slate-50 border-b border-slate-200">
                 {activeTab==="batch_approval"&&<th className="py-3 px-5 w-12 text-center"><input type="checkbox" className="w-4 h-4 rounded text-indigo-600" onChange={e=>setBatchSelections(e.target.checked ? new Set(filteredWorklists.map(w=>w.id)) : new Set())} checked={batchSelections.size===filteredWorklists.length && filteredWorklists.length>0}/></th>}
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Sample / Demographics</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Test Profile</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Result</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Priority / Stage</th>
                 <th className="py-3 px-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Action</th>
               </tr></thead>
               <tbody className="divide-y divide-slate-100">
                 {filteredWorklists.length===0?<tr><td colSpan={6} className="py-16 text-center text-slate-400 text-xs font-bold uppercase">No results in this queue.</td></tr>:
                 filteredWorklists.map(w => (
                   <tr key={w.id} className="hover:bg-slate-50 transition-colors group">
                     {activeTab==="batch_approval"&&<td className="py-4 px-5 text-center"><input type="checkbox" className="w-4 h-4 rounded text-indigo-600" checked={batchSelections.has(w.id)} onChange={()=>toggleBatchSelect(w.id)}/></td>}
                     <td className="py-4 px-5"><div className="text-xs font-black text-slate-900">{w.patient_name} <span className="text-slate-400 ml-1">({w.patient_uhid})</span></div><div className="text-[10px] font-mono text-slate-500 mt-1">{w.sample_id}</div></td>
                     <td className="py-4 px-5"><div className="text-xs font-bold text-slate-800">{w.test_name}</div><div className="text-[9px] font-black text-indigo-500 tracking-wider">[{w.test_code}] • {w.department.replace(/_/g," ")}</div></td>
                     <td className="py-4 px-5 text-center"><div className="text-[15px] font-black text-slate-900 tabular-nums mx-auto p-1 bg-slate-100 rounded w-max min-w-[60px]">{w.result_value||"—"}</div><div className="text-[9px] text-slate-500 font-bold mt-1">{w.result_unit||""}</div></td>
                     <td className="py-4 px-5">
                       <div className="flex flex-col gap-1.5 items-start">
                         <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest border w-max ${priorityColors[w.priority_level]}`}>{w.priority_level} {w.is_critical_alert&&"⚠️"}</span>
                         <span className="text-[9px] font-bold text-slate-400 uppercase"><Shield size={10} className="inline mr-1"/> {w.validation_stage.replace("PENDING_","")} Waiting</span>
                       </div>
                     </td>
                     <td className="py-4 px-5 text-right">
                       <button onClick={()=>openReview(w)} className={`btn btn-sm cursor-pointer ${w.priority_level==="CRITICAL"?"bg-rose-600 text-white border-none shadow-md":"btn-secondary"}`}>{w.validation_stage==="REJECTED"?"View Trail":w.priority_level==="CRITICAL"?"Perform Critical Review":"Open Review"}</button>
                     </td>
                   </tr>
                 ))}
               </tbody>
             </table></div>
          </div>
        )}

      </div>

      {/* ═══ REVIEW & APPROVE MODAL ═══ */}
      {reviewModalOpen && selectedWorklist && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4 backdrop-blur-sm">
           <div className={`bg-white rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col border-t-4 ${selectedWorklist.priority_level==="CRITICAL"?"border-rose-500":selectedWorklist.priority_level==="URGENT"?"border-orange-500":"border-indigo-500"}`}>
             
             <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                <div>
                   <h2 className="text-xl font-black text-slate-900 truncate pr-4">{selectedWorklist.test_name} Result Validation</h2>
                   <div className="flex items-center gap-3 mt-1text-[11px] font-bold uppercase text-slate-500"><span className="text-indigo-600">{selectedWorklist.patient_name}</span> | Sample: {selectedWorklist.sample_id}</div>
                </div>
                <div className="flex gap-2">
                   <button onClick={()=>{setCorrectionMode(true);setRejectModalOpen(false)}} className={`btn btn-sm btn-secondary ${correctionMode?'!bg-indigo-50 border-indigo-200 text-indigo-700':''}`}><Edit2 size={14}/> Correct Value</button>
                   <button onClick={()=>{setRejectModalOpen(true);setCorrectionMode(false)}} className={`btn btn-sm btn-secondary ${rejectModalOpen?'!bg-rose-50 border-rose-200 text-rose-700':''}`}><XCircle size={14}/> Reject Data</button>
                   <button onClick={()=>{setReviewModalOpen(false);setRejectModalOpen(false);setCorrectionMode(false)}} className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100"><XCircle size={20}/></button>
                </div>
             </div>

             <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-50/50 flex-1 overflow-y-auto">
                {/* Result Block */}
                <div className={`p-6 rounded-2xl border-2 flex flex-col justify-center items-center text-center shadow-sm bg-white ${selectedWorklist.priority_level==="CRITICAL"?"border-rose-200 ring-4 ring-rose-50":"border-slate-100"}`}>
                   <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Recorded Result Value</h3>
                   {!correctionMode ? (
                     <>
                       <div className={`text-5xl font-black tabular-nums ${selectedWorklist.priority_level==="CRITICAL"?"text-rose-600":"text-indigo-600"}`}>{selectedWorklist.result_value||"N/A"}</div>
                       <div className="text-sm font-bold text-slate-500 mt-2">{selectedWorklist.result_unit}</div>
                     </>
                   ) : (
                     <div className="w-full px-4">
                       <input autoFocus type="text" className="input-field text-center text-3xl font-black text-indigo-700 h-16 w-full" value={newResultValue} onChange={(e)=>setNewResultValue(e.target.value)} placeholder="New Value..." />
                       <div className="text-[10px] font-bold text-slate-400 uppercase mt-3">All corrections will be permanently logged in CFR21 Audit Trail under your credentials.</div>
                     </div>
                   )}
                </div>

                {/* Flags / Info Block */}
                <div className="space-y-4">
                   <div className="p-4 bg-white rounded-xl border border-slate-100 shadow-sm space-y-3 relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-2"><Shield size={40} className="text-slate-50 opacity-50"/></div>
                      <div><h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Priority Class</h4><span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase mt-1 inline-block ${priorityColors[selectedWorklist.priority_level]}`}>{selectedWorklist.priority_level} RESULT</span></div>
                      <div><h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Analyzer Source</h4><div className="font-mono text-xs text-slate-700 font-bold mt-1 bg-slate-100 p-1.5 rounded inline-block">{selectedWorklist.analyzer_device_id||"Manual Entry / Not Traced"}</div></div>
                      
                      {selectedWorklist.flags?.length > 0 && selectedWorklist.flags.map(f=>(
                        <div key={f.id} className="mt-3 bg-rose-50 border border-rose-200 p-2.5 rounded-lg">
                           <div className="flex items-center gap-1 text-rose-800 text-xs font-black uppercase"><AlertTriangle size={12}/> System Generated Alert ({f.flag_type})</div>
                           <div className="text-xs text-rose-700 font-bold mt-1">{f.alert_message}</div>
                        </div>
                      ))}
                   </div>
                   
                   <div className="flex flex-col gap-2">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest"><MessageSquare size={12} className="inline mr-1"/> Validation Remarks (Optional)</label>
                      <textarea className="input-field resize-none h-16 text-xs" value={remarks} onChange={e=>setRemarks(e.target.value)} placeholder="Add contextual notes for report..."></textarea>
                   </div>
                </div>
                
                {rejectModalOpen && (
                   <div className="md:col-span-2 bg-rose-50 border border-rose-200 p-4 rounded-xl space-y-3">
                      <label className="text-[10px] font-black text-rose-800 uppercase tracking-widest">Select Rejection Reason</label>
                      <select className="input-field border-rose-300 text-rose-900 bg-white" value={rejectionReason} onChange={e=>setRejectionReason(e.target.value)}>
                         <option value="">-- Choose precise cause --</option>
                         <option value="SAMPLE_CONTAMINATION_SUSPECTED">Sample Contamination Suspected</option>
                         <option value="INSTRUMENT_QC_FAILURE">Instrument QC Failure</option>
                         <option value="CLINICAL_MISMATCH_DELTA">Clinical Mismatch / Delta Alert Fail</option>
                         <option value="PROCEDURAL_ERROR_ENTRY">Procedural Error / Incorrect Entry</option>
                      </select>
                   </div>
                )}
             </div>

             <div className="p-5 border-t border-slate-100 bg-white flex justify-end gap-3 items-center">
                {correctionMode ? (
                  <button onClick={() => handleCorrect(selectedWorklist.id, VALIDATOR_INFO.role)} className="btn bg-indigo-600 text-white font-black"><CheckCircle2 size={16}/> Save Correction & Log Audit</button>
                ) : rejectModalOpen ? (
                  <button onClick={() => handleReject(selectedWorklist.id)} className="btn bg-rose-600 text-white font-black"><XCircle size={16}/> Confirm Rejection</button>
                ) : (
                  <button onClick={() => handleApprove(selectedWorklist.id, VALIDATOR_INFO.role)} className="btn bg-emerald-600 hover:bg-emerald-700 text-white font-black text-sm px-8 py-3 outline outline-4 outline-emerald-100"><Shield size={18}/> Formally Approve Result</button>
                )}
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
