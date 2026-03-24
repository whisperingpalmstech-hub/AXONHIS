"use client";
import React, { useEffect, useState, useMemo } from "react";
import {
  FileText, CheckCircle2, XCircle, RefreshCw, Send,
  AlertTriangle, Loader2, Search, Edit3, Fingerprint,
  Mail, MessageSquare, Globe, Printer, FileSignature, Clock, Database, UploadCloud
} from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { reportingApi } from "@/lib/reporting-api";
import type { LabReportOut } from "@/lib/reporting-api";

// We mock a logged in pathologist/HOD for signing
const SIGNER_INFO = {
  id: "USR-PATH-900",
  name: "Dr. Alistair Vance",
  designation: "Chief Pathologist"
};

type TabType = "PENDING_RELEASE" | "SIGNATURE_QUEUE" | "RELEASED" | "ARCHIVE";

export default function SmartReportingPage() {
  const [activeTab, setActiveTab] = useState<TabType>("SIGNATURE_QUEUE");
  const [reports, setReports] = useState<LabReportOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [selectedReport, setSelectedReport] = useState<LabReportOut | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [isAmendOpen, setIsAmendOpen] = useState(false);
  const [amendReason, setAmendReason] = useState("");
  const [amendComments, setAmendComments] = useState("");

  const [selectedForBulk, setSelectedForBulk] = useState<Set<string>>(new Set());
  const [bulkChannels, setBulkChannels] = useState({ email: true, sms: false, portal: true });

  const fetchReports = async (statusFilter?: string) => {
    setLoading(true);
    setError("");
    try {
      const res = await reportingApi.getReports({ status: statusFilter });
      setReports(res || []);
    } catch (err: any) {
      console.error("Failed to fetch reports from backend", err);
      setError("Failed to connect to the reporting engine data stream.");
    }
    setLoading(false);
  };

  useEffect(() => {
    // Map tabs to statuses
    let apiStatus = "";
    if (activeTab === "SIGNATURE_QUEUE") apiStatus = "PENDING_RELEASE";
    else if (activeTab === "PENDING_RELEASE") apiStatus = "PENDING_RELEASE";
    else if (activeTab === "RELEASED") apiStatus = "RELEASED";
    else apiStatus = "";

    fetchReports(apiStatus);
    setSelectedForBulk(new Set());
  }, [activeTab]);

  const displayedReports = useMemo(() => {
    if (activeTab === "SIGNATURE_QUEUE") return reports.filter(r => !r.is_signed && r.status === "PENDING_RELEASE");
    if (activeTab === "PENDING_RELEASE") return reports.filter(r => r.is_signed && r.status === "PENDING_RELEASE");
    if (activeTab === "RELEASED") return reports.filter(r => r.status === "RELEASED");
    return reports;
  }, [reports, activeTab]);

  const handleSign = async (report: LabReportOut) => {
    try {
      await reportingApi.signReport(report.id, {
        signer_id: SIGNER_INFO.id,
        signer_name: SIGNER_INFO.name,
        signer_designation: SIGNER_INFO.designation
      });
      setSuccess(`Report ${report.id} digitally signed.`);
      fetchReports("PENDING_RELEASE");
      setIsViewerOpen(false);
    } catch (e: any) { setError(e.message||"Failed to sign."); }
  };

  const handleRelease = async (report: LabReportOut) => {
    try {
      const channels = [];
      if (bulkChannels.email) channels.push("email");
      if (bulkChannels.sms) channels.push("sms");
      if (bulkChannels.portal) channels.push("portal");

      await reportingApi.releaseReport(report.id, {
        releaser_id: SIGNER_INFO.id,
        releaser_name: SIGNER_INFO.name,
        channels,
        recipients: ["patient_contact", "dr_desktop"]
      });
      setSuccess(`Report ${report.id} successfully released & dispatched.`);
      fetchReports("PENDING_RELEASE");
    } catch (e: any) { setError(e.message||"Failed to release."); }
  };

  const handleBulkRelease = async () => {
    if (selectedForBulk.size === 0) return;
    try {
      const channels = [];
      if (bulkChannels.email) channels.push("email");
      if (bulkChannels.sms) channels.push("sms");
      if (bulkChannels.portal) channels.push("portal");

      const ids = Array.from(selectedForBulk);
      await reportingApi.bulkRelease({
        report_ids: ids,
        releaser_id: SIGNER_INFO.id,
        releaser_name: SIGNER_INFO.name,
        channels
      });
      setSuccess(`${ids.length} reports bulk-released successfully via Handover Protocol.`);
      setSelectedForBulk(new Set());
      fetchReports("PENDING_RELEASE");
    } catch (e: any) { setError(e.message); }
  };

  const handleAmend = async () => {
    if (!selectedReport) return;
    try {
       await reportingApi.amendReport(selectedReport.id, {
         amender_id: SIGNER_INFO.id,
         amender_name: SIGNER_INFO.name,
         changes_made: { details: "Edited comments" },
         reason: amendReason,
         new_result_values: selectedReport.result_values,
         new_comments: amendComments
       });
       setSuccess("Report amended and re-routed for signature.");
       fetchReports("RELEASED");
       setIsAmendOpen(false);
    } catch (e: any) { setError(e.message); }
  };

  const openViewer = (report: LabReportOut) => {
    setSelectedReport(report);
    setIsViewerOpen(true);
  };

  const toggleBulk = (id: string) => {
    const s = new Set(selectedForBulk);
    if (s.has(id)) s.delete(id); else s.add(id);
    setSelectedForBulk(s);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <TopNav title="Smart Reporting & Report Release Engine" />
      <div className="flex-1 p-6 max-w-[1400px] mx-auto w-full space-y-6">

        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
              <FileSignature size={28} className="text-blue-600"/> Report Handover Desk
            </h1>
            <p className="text-slate-400 font-bold uppercase tracking-[0.1em] text-[10px] mt-1">Smart Engine • Digital Authorizations • Omni-Channel Handover</p>
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600 bg-white px-4 py-2 border border-slate-200 rounded-lg shadow-sm">
            <Fingerprint size={16} className="text-indigo-600"/> Account: {SIGNER_INFO.name} ({SIGNER_INFO.designation})
          </div>
        </div>

        {error && <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded-xl flex items-center justify-between text-xs font-bold"><div className="flex gap-2"><AlertTriangle size={14}/>{error}</div><button onClick={()=>setError("")}><XCircle size={16}/></button></div>}
        {success && <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-xl flex items-center justify-between text-xs font-bold"><div className="flex gap-2"><CheckCircle2 size={14}/>{success}</div><button onClick={()=>setSuccess("")}><XCircle size={16}/></button></div>}

        {/* TABS */}
        <div className="flex p-1 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-x-auto w-max">
           {[
             { id: "SIGNATURE_QUEUE", l: "Signature Queue", icon: Edit3, color: "text-amber-600", bg: "bg-amber-100" },
             { id: "PENDING_RELEASE", l: "Ready For Release", icon: Send, color: "text-blue-600", bg: "bg-blue-100" },
             { id: "RELEASED", l: "Successfully Released", icon: CheckCircle2, color: "text-emerald-600", bg: "bg-emerald-100" },
             { id: "ARCHIVE", l: "Audit & Amendments", icon: Database, color: "text-slate-600", bg: "bg-slate-100" },
           ].map(t => (
             <button key={t.id} onClick={()=>setActiveTab(t.id as TabType)} className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-[11px] font-black uppercase tracking-wider transition-all cursor-pointer ${activeTab===t.id?"bg-slate-900 text-white shadow-lg":"text-slate-400 hover:text-slate-900 hover:bg-slate-50"}`}>
               <t.icon size={15} className={activeTab===t.id?"text-white":t.color}/> {t.l}
             </button>
           ))}
        </div>

        {/* ACTION BAR (Only for READY FOR RELEASE) */}
        {activeTab === "PENDING_RELEASE" && (
          <div className="card bg-white p-4 flex flex-wrap items-center justify-between gap-4 border-l-4 border-l-blue-500 shadow-sm rounded-xl">
             <div className="flex flex-col">
               <h3 className="text-sm font-black text-slate-800">Bulk Distribution Handover</h3>
               <p className="text-[10px] text-slate-500 font-bold uppercase">Select formatted reports below to broadcast simultaneously.</p>
             </div>
             <div className="flex items-center gap-6">
               <div className="flex gap-4">
                 <label className="flex items-center gap-2 text-[10px] font-black uppercase text-slate-600 cursor-pointer">
                   <input type="checkbox" checked={bulkChannels.email} onChange={e=>setBulkChannels({...bulkChannels, email: e.target.checked})} className="rounded text-blue-600 focus:ring-blue-500 bg-slate-100 border-none w-4 h-4"/>
                   <Mail size={14} className="text-blue-500"/> E-Mail
                 </label>
                 <label className="flex items-center gap-2 text-[10px] font-black uppercase text-slate-600 cursor-pointer">
                   <input type="checkbox" checked={bulkChannels.portal} onChange={e=>setBulkChannels({...bulkChannels, portal: e.target.checked})} className="rounded text-blue-600 focus:ring-blue-500 bg-slate-100 border-none w-4 h-4"/>
                   <Globe size={14} className="text-indigo-500"/> Patient Portal
                 </label>
                 <label className="flex items-center gap-2 text-[10px] font-black uppercase text-slate-600 cursor-pointer">
                   <input type="checkbox" checked={bulkChannels.sms} onChange={e=>setBulkChannels({...bulkChannels, sms: e.target.checked})} className="rounded text-blue-600 focus:ring-blue-500 bg-slate-100 border-none w-4 h-4"/>
                   <MessageSquare size={14} className="text-emerald-500"/> SMS Notify
                 </label>
               </div>
               <div className="h-8 w-px bg-slate-200"></div>
               <button onClick={handleBulkRelease} disabled={selectedForBulk.size===0} className="btn bg-blue-600 hover:bg-blue-700 text-white shadow focus:ring-4 focus:ring-blue-100 disabled:opacity-50 flex items-center gap-2 cursor-pointer">
                 <UploadCloud size={16}/> Broadcast {selectedForBulk.size > 0 ? selectedForBulk.size : ""} Reports
               </button>
             </div>
          </div>
        )}

        {/* REPORT QUEUE TABLE */}
        <div className="card bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-200">
           <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
             <div className="relative">
               <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/>
               <input type="text" placeholder="Search Patient or UHID..." className="pl-9 pr-4 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-100 outline-none w-64"/>
             </div>
             <button onClick={()=>fetchReports()} className="text-slate-400 hover:text-slate-800 p-1 bg-white rounded-md shadow-sm border border-slate-200 cursor-pointer"><RefreshCw size={14}/></button>
           </div>
           
           <div className="overflow-x-auto">
             <table className="w-full text-left">
               <thead>
                 <tr className="bg-white border-b border-slate-100 text-[10px] font-black uppercase text-slate-400">
                   {activeTab === "PENDING_RELEASE" && <th className="py-3 px-4 w-10 text-center"><input type="checkbox" className="rounded border-slate-300 text-blue-600" onChange={(e)=>{if(e.target.checked) setSelectedForBulk(new Set(displayedReports.map(r=>r.id))); else setSelectedForBulk(new Set());}}/></th>}
                   <th className="py-3 px-4">Tracking UID</th>
                   <th className="py-3 px-4">Patient Profile</th>
                   <th className="py-3 px-4">Primary Test</th>
                   <th className="py-3 px-4">Department</th>
                   <th className="py-3 px-4">Validation State</th>
                   <th className="py-3 px-4 text-right">Actions</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-slate-50">
                 {displayedReports.length === 0 ? (
                   <tr><td colSpan={7} className="py-20 text-center flex flex-col items-center justify-center text-slate-400"><FileText size={48} className="text-slate-200 mb-3"/><span className="text-sm font-bold uppercase tracking-wider">Queue is currently empty</span></td></tr>
                 ) : (
                   displayedReports.map(rp => (
                     <tr key={rp.id} className="hover:bg-blue-50/50 transition-colors group">
                       {activeTab === "PENDING_RELEASE" && (
                         <td className="py-4 px-4 text-center">
                           <input type="checkbox" checked={selectedForBulk.has(rp.id)} onChange={()=>toggleBulk(rp.id)} className="rounded text-blue-600 cursor-pointer"/>
                         </td>
                       )}
                       <td className="py-4 px-4"><div className="text-xs font-mono font-black text-slate-800">{rp.id}</div><div className="text-[9px] text-slate-400 font-mono mt-0.5">S: {rp.sample_id}</div></td>
                       <td className="py-4 px-4"><div className="text-sm font-black text-slate-900">{rp.patient_name}</div><div className="text-[10px] text-slate-500 font-bold">{rp.patient_uhid}</div></td>
                       <td className="py-4 px-4"><div className="text-xs font-bold text-slate-800">{rp.test_details?.name || "Multiple Panels"}</div></td>
                       <td className="py-4 px-4"><span className="px-2 py-0.5 rounded text-[9px] font-black uppercase border bg-slate-100 text-slate-600 border-slate-200">{rp.department?.replace(/_/g," ")}</span></td>
                       <td className="py-4 px-4">
                         <div className="flex flex-col gap-1 items-start">
                           {rp.is_signed ? (
                             <span className="flex items-center gap-1 px-2 py-0.5 text-[9px] font-black uppercase border bg-emerald-50 text-emerald-700 border-emerald-200 rounded"><CheckCircle2 size={10}/> Signed: {rp.signed_by_name}</span>
                           ) : (
                             <span className="flex items-center gap-1 px-2 py-0.5 text-[9px] font-black uppercase border bg-amber-50 text-amber-700 border-amber-200 rounded animate-pulse"><AlertTriangle size={10}/> Unsigned</span>
                           )}
                           {rp.abnormal_flags && Object.keys(rp.abnormal_flags).length > 0 && <span className="text-[9px] font-black px-1.5 py-0.5 bg-rose-100 text-rose-700 rounded w-max">Contains Abnormalities</span>}
                         </div>
                       </td>
                       <td className="py-4 px-4 text-right">
                         <div className="flex items-center justify-end gap-2">
                            {activeTab === "SIGNATURE_QUEUE" && (
                              <button onClick={()=>openViewer(rp)} className="btn btn-sm bg-amber-500 hover:bg-amber-600 text-white shadow-sm flex items-center gap-1 text-[10px] font-black cursor-pointer"><Fingerprint size={12}/> Review & Sign</button>
                            )}
                            {activeTab === "PENDING_RELEASE" && (
                              <>
                                <button onClick={()=>openViewer(rp)} className="p-1.5 text-slate-400 hover:text-blue-600 rounded bg-white shadow-sm border border-slate-200 cursor-pointer"><Search size={14}/></button>
                                <button onClick={()=>handleRelease(rp)} className="btn btn-sm btn-secondary hover:bg-blue-600 hover:text-white flex items-center gap-1 text-[10px] font-black cursor-pointer"><Send size={12}/> Quick Release</button>
                              </>
                            )}
                            {activeTab === "RELEASED" && (
                              <>
                                <button onClick={()=>openViewer(rp)} className="p-1.5 text-slate-400 hover:text-slate-800 rounded bg-white shadow-sm border border-slate-200 cursor-pointer"><Printer size={14}/></button>
                                <button onClick={()=>{setSelectedReport(rp); setAmendComments(rp.interpretative_comments||""); setIsAmendOpen(true);}} className="p-1.5 text-slate-400 hover:text-rose-600 rounded bg-white shadow-sm border border-slate-200 cursor-pointer" title="Amend / Correct Report"><Edit3 size={14}/></button>
                              </>
                            )}
                         </div>
                       </td>
                     </tr>
                   ))
                 )}
               </tbody>
             </table>
           </div>
        </div>

      </div>

      {/* REPORT VIEWER MODAL (Simulation of Print PDF/Formatting) */}
      {isViewerOpen && selectedReport && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 py-10">
          <div className="bg-slate-200 w-full max-w-4xl h-full rounded-2xl flex flex-col shadow-2xl overflow-hidden border border-slate-300">
             <div className="bg-slate-800 text-white p-4 flex justify-between items-center shadow-md z-10">
               <div className="flex items-center gap-3">
                 <FileText className="text-blue-400" size={24}/>
                 <div>
                   <h2 className="font-bold text-sm">AxonHIS Smart PDF Viewer</h2>
                   <p className="text-[10px] text-slate-400 font-mono uppercase tracking-widest">{selectedReport.id}</p>
                 </div>
               </div>
               <button onClick={()=>setIsViewerOpen(false)} className="text-slate-400 hover:text-white transition-colors cursor-pointer"><XCircle size={24}/></button>
             </div>

             {/* Document Canvas Frame */}
             <div className="flex-1 overflow-y-auto p-4 md:p-8 flex justify-center custom-scroller">
                
                {/* Simulated A4 Report Paper */}
                <div className="w-[210mm] min-h-[297mm] bg-white shadow-lg p-10 font-serif flex flex-col relative text-slate-900">
                   
                   {/* Header Branding */}
                   <div className="flex justify-between items-center border-b-2 border-slate-900 pb-6 mb-6">
                     <div>
                       <h1 className="text-3xl font-black text-slate-900 tracking-tight">AXON<span className="text-blue-600 font-light">HEALTH</span></h1>
                       <p className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mt-1">Department of {selectedReport.department?.replace("_"," ")}</p>
                     </div>
                     <div className="text-right text-[10px] font-mono leading-relaxed text-slate-600">
                       <p>Report Date: {new Date(selectedReport.created_at).toLocaleDateString()}</p>
                       <p>Sample ID: {selectedReport.sample_id}</p>
                       <p>Version: V{selectedReport.current_version}</p>
                     </div>
                   </div>

                   {/* Patient Info Card */}
                   <div className="grid grid-cols-2 gap-4 mb-8 bg-slate-50 border border-slate-200 p-4 font-sans text-xs">
                     <div><span className="text-slate-400 uppercase font-black text-[9px]">Patient Name</span><p className="font-black text-sm">{selectedReport.patient_name}</p></div>
                     <div><span className="text-slate-400 uppercase font-black text-[9px]">UHID / Medical Rec #</span><p className="font-mono font-bold text-slate-700">{selectedReport.patient_uhid}</p></div>
                     <div><span className="text-slate-400 uppercase font-black text-[9px]">Report Status</span><p className="font-bold text-slate-800 uppercase">{selectedReport.status.replace("_"," ")}</p></div>
                     <div><span className="text-slate-400 uppercase font-black text-[9px]">Ref. Doctor</span><p className="font-bold text-slate-800">OPD Physician</p></div>
                   </div>

                   {/* Test Label */}
                   <h2 className="text-center font-black uppercase text-sm border-b border-dashed border-slate-300 pb-2 mb-6">Test: {selectedReport.test_details?.name}</h2>

                   {/* Result Data Table */}
                   <table className="w-full text-left font-sans text-xs mb-8">
                     <thead><tr className="border-b border-slate-800 uppercase text-[9px] font-black text-slate-500">
                       <th className="py-2">Parameter</th><th className="py-2 text-center">Result</th><th className="py-2">Flag</th><th className="py-2 text-right">Reference Interval</th>
                     </tr></thead>
                     <tbody className="divide-y divide-slate-100">
                       {Object.entries(selectedReport.result_values || {}).map(([key, val]) => {
                         const isAbnormal = selectedReport.abnormal_flags && selectedReport.abnormal_flags[key];
                         return (
                           <tr key={key}>
                             <td className="py-3 font-bold text-slate-800">{key}</td>
                             <td className="py-3 text-center">
                               <span className={`tabular-nums font-black text-sm ${isAbnormal?"text-rose-600":"text-emerald-700"}`}>{val as any}</span>
                             </td>
                             <td className="py-3 font-bold">{isAbnormal?<span className="bg-rose-100 text-rose-700 px-1 rounded text-[10px]">{isAbnormal}</span>:""}</td>
                             <td className="py-3 text-right text-slate-500 font-mono tracking-tight">{selectedReport.reference_ranges?.[key]||"—"}</td>
                           </tr>
                         )
                       })}
                     </tbody>
                   </table>

                   {/* Smart Interpretation Comment AI */}
                   {selectedReport.interpretative_comments && (
                     <div className="mb-10 bg-blue-50/50 border-l-4 border-blue-500 p-4 font-sans">
                        <h4 className="flex items-center gap-1 font-black text-[10px] uppercase text-blue-800 mb-2"><MessageSquare size={12}/> Clinical Interpretation</h4>
                        <p className="text-xs text-slate-700 leading-relaxed italic border-l-2 border-slate-300 pl-3">"{selectedReport.interpretative_comments}"</p>
                     </div>
                   )}

                   {/* Footnotes & Signatures */}
                   <div className="mt-auto pt-10 border-t border-slate-200 grid grid-cols-2 gap-10">
                     <div className="text-[9px] text-slate-400 font-sans leading-relaxed">
                       * Generated electronically by AxonHIS Smart Engine.<br/>
                       * This is a digitally secured document. Unauthorized alteration is strongly prohibited under Federal Law.<br/>
                       * Page 1 of 1
                     </div>
                     <div className="flex flex-col items-center justify-end">
                       {selectedReport.is_signed ? (
                         <div className="mt-4 flex flex-col items-center border-t border-slate-800 pt-2 w-48 text-center text-[10px]">
                           <span className="font-black text-slate-900 text-xs italic">{selectedReport.signed_by_name}</span>
                           <span className="text-slate-500 font-bold uppercase">{selectedReport.signed_by_designation}</span>
                           <span className="text-slate-400 font-mono scale-90 block mt-1">[{selectedReport.signed_at || "Digital Auth"}]</span>
                         </div>
                       ) : (
                         <div className="text-[10px] text-rose-400 font-bold uppercase border-2 border-dashed border-rose-200 p-4 text-center">
                           Awaiting Digital Signature Authorization
                         </div>
                       )}
                     </div>
                   </div>
                </div>

             </div>
             
             {/* Signature Control Panel Floor */}
             {!selectedReport.is_signed && activeTab === "SIGNATURE_QUEUE" && (
                <div className="bg-white p-4 border-t border-slate-300 flex items-center justify-between shadow-[0_-10px_40px_rgba(0,0,0,0.1)] z-20">
                   <div className="flex flex-col">
                     <span className="text-[10px] font-black uppercase text-slate-500">Authorization Module</span>
                     <span className="text-xs font-bold text-slate-800 flex items-center gap-1"><Fingerprint size={12} className="text-indigo-600"/> Authenticated as: {SIGNER_INFO.name}</span>
                   </div>
                   <button onClick={() => handleSign(selectedReport)} className="btn bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-200 flex items-center gap-2 cursor-pointer font-black px-8 py-3 outline-none focus:ring-4 focus:ring-indigo-100">
                     <Fingerprint size={18}/> Authorize & Append Digital Signature
                   </button>
                </div>
             )}
          </div>
        </div>
      )}

      {/* AMENDMENT MODAL */}
      {isAmendOpen && selectedReport && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl flex flex-col gap-4">
             <div className="flex items-center gap-2 text-rose-600 border-b border-slate-100 pb-3">
               <AlertTriangle size={24}/><div><h2 className="font-black">Amend Released Report</h2><p className="text-[10px] uppercase font-bold text-slate-400">Creates Version {selectedReport.current_version + 1}</p></div>
             </div>
             <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded border text-justify leading-relaxed">
               You are about to issue a formal amendment on a released report. The previous version will be archived in the audit logs, and a re-signature will be required.
             </p>
             <div className="flex flex-col gap-1">
               <label className="text-[10px] font-black uppercase text-slate-500">Reason for Amendment (Required for Compliance)</label>
               <input type="text" value={amendReason} onChange={e=>setAmendReason(e.target.value)} placeholder="e.g. Corrected clinical interpretation regarding iron." className="input-field text-sm font-bold"/>
             </div>
             <div className="flex flex-col gap-1">
               <label className="text-[10px] font-black uppercase text-slate-500">Override Interpretative Comments (Optional)</label>
               <textarea value={amendComments} onChange={e=>setAmendComments(e.target.value)} rows={3} className="input-field text-sm leading-relaxed"></textarea>
             </div>
             <div className="mt-4 flex justify-end gap-2">
               <button onClick={()=>setIsAmendOpen(false)} className="btn btn-secondary cursor-pointer">Cancel</button>
               <button onClick={handleAmend} disabled={!amendReason.trim()} className="btn bg-rose-600 text-white shadow focus:ring-4 focus:ring-rose-100 cursor-pointer disabled:opacity-50">Process Amendment</button>
             </div>
          </div>
        </div>
      )}

      <style jsx global>{`
        .custom-scroller::-webkit-scrollbar { width: 8px; }
        .custom-scroller::-webkit-scrollbar-track { background: transparent; }
        .custom-scroller::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
      `}</style>
    </div>
  );
}
