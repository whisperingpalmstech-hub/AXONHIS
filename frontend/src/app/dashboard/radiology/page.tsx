"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect } from "react";
import { Search, Calendar, Edit3, Image as ImageIcon, Play, UploadCloud, Plus, X, Activity, CheckCircle, FileText, Upload } from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";

export default function RadiologyDashboard() {
  const { t } = useTranslation();
  const [studies, setStudies] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("worklist");

  const [showOrderModal, setShowOrderModal] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [selectedModality, setSelectedModality] = useState("X-ray");
  const [studyName, setStudyName] = useState("");
  
  // Modals
  const [processingOrder, setProcessingOrder] = useState<any>(null);
  const [reportingStudy, setReportingStudy] = useState<any>(null);
  const [reportText, setReportText] = useState("");
  
  // File Upload Demo
  const [dicomUploadOpen, setDicomUploadOpen] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>("");

  const fetchData = async () => {
    try {
      const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      
      const [resOrders, resPat, resRep] = await Promise.all([
        fetch(`${api}/api/v1/radiology/orders`, { headers }),
        fetch(`${api}/api/v1/patients`, { headers }),
        fetch(`${api}/api/v1/radiology/reports`, { headers })
      ]);
      
      if (resOrders.ok) setStudies(await resOrders.json());
      if (resPat.ok) setPatients(await resPat.json());
      if (resRep.ok) setReports(await resRep.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const getPatientName = (id: string) => {
    const p = patients.find(x => x.id === id);
    return p ? `${p.first_name} ${p.last_name}` : id;
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId || !studyName) return;
    try {
      const headers = { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

      const encRes = await fetch(`${api}/api/v1/encounters/`, { headers });
      const encounters = await encRes.json();
      const activeEncId = encounters.find((enc: any) => enc.patient_id === selectedPatientId)?.id;
      if (!activeEncId) { alert("Patient must have an active encounter."); return; }

      const ordRes = await fetch(`${api}/api/v1/orders/`, {
        method: "POST", headers, body: JSON.stringify({
          encounter_id: activeEncId, patient_id: selectedPatientId, order_type: "RADIOLOGY_ORDER", priority: "ROUTINE",
          items: [{ item_type: "radiology", item_name: studyName, quantity: 1, unit_price: 250 }]
        })
      });
      const orderData = await ordRes.json();

      await fetch(`${api}/api/v1/radiology/order`, {
        method: "POST", headers, body: JSON.stringify({
          requested_modality: selectedModality, requested_study: studyName, priority: "routine",
          encounter_id: activeEncId, patient_id: selectedPatientId, order_id: orderData.id
        })
      });

      setShowOrderModal(false);
      fetchData();
    } catch (err) { console.error(err); }
  };

  const executeStudyPipeline = async (order: any) => {
     setProcessingOrder({...order, step: "initiating"});
     const headers = { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
     const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
     
     try {
       // 1. Create Study
       const res1 = await fetch(`${api}/api/v1/radiology/studies`, {
         method: "POST", headers, body: JSON.stringify({
           imaging_order_id: order.id, study_uid: "1.2.840.10008." + Date.now(), modality: order.requested_modality
         })
       });
       const study = await res1.json();
       
       // 2. Start Study (Scanning)
       setProcessingOrder({...order, step: "scanning"});
       await fetch(`${api}/api/v1/radiology/start-study?study_id=${study.id}&machine_id=${order.requested_modality}-A1`, { method: "POST", headers });
       
       // UI Simulation Delay
       await new Promise(r => setTimeout(r, 2000));
       
       // 3. Complete Study (Triggers Billing + Timeline)
       setProcessingOrder({...order, step: "completing"});
       await fetch(`${api}/api/v1/radiology/complete-study?study_id=${study.id}`, { method: "POST", headers });
       
       setProcessingOrder(null);
       fetchData();
     } catch(e) { console.error("Pipeline failed", e); setProcessingOrder(null); }
  };

  const [reportSuccess, setReportSuccess] = useState(false);

  const handleWriteReport = async () => {
    if (!reportingStudy || !reportText) return;
    try {
      const headers = { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      
      // 1. Fetch the actual ImagingStudy tied to this order.
      const studiesRes = await fetch(`${api}/api/v1/radiology/studies`, { headers });
      const allStudies = await studiesRes.json();
      const actualStudy = allStudies.find((s: any) => s.imaging_order_id === reportingStudy.id);
      
      if (!actualStudy) {
        console.error("Study not found for order", reportingStudy.id);
        alert("System Error: No physical study record found for this order. Please process the scan first.");
        return;
      }

      // 2. Create Draft Report
      const draftRes = await fetch(`${api}/api/v1/radiology/report`, {
        method: "POST", headers, body: JSON.stringify({
           study_id: actualStudy.id, 
           report_text: reportText, 
           status: "draft"
        })
      });
      
      if (!draftRes.ok) {
         console.error("Failed to create draft", await draftRes.text());
         return;
      }
      const draftData = await draftRes.json();

      // 3. Finalize Report
      await fetch(`${api}/api/v1/radiology/report/${draftData.id}/finalize?impression=${encodeURIComponent(reportText)}&critical_flag=false`, {
        method: "PUT", headers
      });
      
      setReportSuccess(true);
      setTimeout(() => {
         setReportingStudy(null); 
         setReportText("");
         setReportSuccess(false);
         fetchData(); // Refresh the board
      }, 2000);
      
    } catch(e) { console.error(e); }
  };

  const handleDicomUpload = async (e: any) => {
    e.preventDefault();
    setUploadStatus("Uploading to PACS...");
    try {
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      await fetch(`${api}/api/v1/radiology/dicom/upload`, {
        method: "POST", headers: { "Authorization": `Bearer ${localStorage.getItem("access_token")}` }
      });
      setTimeout(() => {
        setUploadStatus("Upload Successful! Parsed metadata.");
        setTimeout(() => { setDicomUploadOpen(false); setUploadStatus(""); }, 2000);
      }, 1500);
    } catch (err) {
      setUploadStatus("Error reaching DICOM route");
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <TopNav title="Radiology & Imaging (RIS)" />
      
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
              <ImageIcon className="text-indigo-500" size={32}/> Radiology Information System
            </h1>
            <p className="text-slate-500 font-medium mt-1">PACS Interface • Modality Worklist • Reporting</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setDicomUploadOpen(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl font-bold transition-all shadow-md shadow-indigo-200 flex items-center gap-2">
              <UploadCloud size={18}/> Generic DICOM Upload
            </button>
            <button onClick={() => setShowOrderModal(true)} className="bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 px-5 py-2.5 rounded-xl font-bold transition-all shadow-sm flex items-center gap-2">
              <Plus size={18}/> Schedule Scan
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 p-1.5 bg-white border border-slate-200 rounded-2xl w-fit mb-6 shadow-sm overflow-x-auto">
          {[
            { id: "worklist", label: "Modality Worklist", icon: <Calendar size={16}/> },
            { id: "reporting", label: "Reporting Desk", icon: <Edit3 size={16}/> },
            { id: "archives", label: "Published Archives", icon: <FileText size={16}/> },
            { id: "pacs", label: "PACS Viewer", icon: <Play size={16}/> },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
                activeTab === t.id ? "bg-white text-indigo-700 shadow-sm border border-slate-200/50" : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
              }`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {loading ? (
             <div className="p-12 text-center text-slate-400 font-bold">Synchronizing Modalities...</div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[500px]">
            {activeTab === "worklist" && (
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200"><tr className="text-slate-500 text-xs uppercase tracking-wider"><th className="p-4 font-bold">Time</th><th className="p-4 font-bold">Modality</th><th className="p-4 font-bold">Requested Study</th><th className="p-4 font-bold">Patient</th><th className="p-4 font-bold">Status</th><th className="p-4 font-bold text-right">Actions</th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {studies.filter(s => s.status !== 'completed').length === 0 ? <tr><td colSpan={6} className="p-8 text-center text-slate-400 font-bold">No active orders in queue</td></tr> : 
                    studies.filter(s => s.status !== 'completed').map(study => (
                    <tr key={study.id} className="hover:bg-slate-50 transition-colors">
                      <td className="p-4 text-slate-500 text-xs font-mono">{new Date(study.ordered_at).toLocaleString()}</td>
                      <td className="p-4"><span className="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded text-xs font-black uppercase tracking-wider border border-indigo-100">{study.requested_modality}</span></td>
                      <td className="p-4 font-bold text-slate-800">{study.requested_study}</td>
                      <td className="p-4 font-semibold text-slate-600">{getPatientName(study.patient_id)}</td>
                      <td className="p-4"><span className="px-2.5 py-1 rounded text-[10px] bg-amber-100 text-amber-700 font-black uppercase tracking-wider">{study.status.replace('_', ' ')}</span></td>
                      <td className="p-4 text-right">
                         <button onClick={() => executeStudyPipeline(study)} className="bg-indigo-600 text-white rounded-lg px-4 py-2 text-xs font-bold hover:bg-indigo-700 shadow-sm flex items-center justify-end ml-auto gap-2">
                            <Activity size={14}/> Perform Study
                         </button>
                      </td>
                    </tr>
                   ))}
                </tbody>
              </table>
            )}

            {activeTab === "reporting" && (
               <div className="grid grid-cols-2 gap-0 h-full min-h-[500px] border-t border-slate-100 divide-x divide-slate-100">
                 <div className="bg-slate-50 p-4 overflow-y-auto">
                    <h3 className="text-xs font-black text-slate-500 uppercase mb-4 px-2">Completed Studies Awaiting Report</h3>
                    {studies.filter(s => s.status === 'completed').length === 0 ? <p className="text-slate-400 p-2 text-sm font-medium">No completed studies.</p> :
                     studies.filter(s => s.status === 'completed').map(s => (
                       <button key={s.id} onClick={() => setReportingStudy(s)} className={`w-full text-left p-4 rounded-xl border mb-3 transition-colors ${reportingStudy?.id === s.id ? 'bg-white border-indigo-400 shadow-sm' : 'bg-white border-slate-200 hover:border-indigo-300'}`}>
                         <div className="flex justify-between items-center mb-1"><span className="font-bold text-indigo-900">{s.requested_study}</span><CheckCircle size={16} className="text-emerald-500"/></div>
                         <div className="text-sm font-medium text-slate-600">{getPatientName(s.patient_id)}</div>
                         <div className="text-xs text-slate-400 mt-2 font-mono">{new Date(s.ordered_at).toLocaleString()}</div>
                       </button>
                     ))}
                 </div>
                 <div className="p-8 bg-white">
                   {!reportingStudy ? (
                     <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-50"><FileText size={48} className="mb-4"/><p className="font-bold">Select a study to dictate report</p></div>
                   ) : (
                     <div className="space-y-4">
                        <div className="flex items-center justify-between border-b pb-4">
                           <div>
                              <h2 className="text-xl font-black text-slate-800">{reportingStudy.requested_study}</h2>
                              <p className="text-sm font-semibold text-slate-500">Patient: {getPatientName(reportingStudy.patient_id)}</p>
                           </div>
                           <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded text-xs font-bold uppercase">{reportingStudy.requested_modality}</span>
                        </div>
                        <div>
                          <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">Radiologist Impression Form</label>
                          <textarea 
                             rows={10} 
                             value={reportText} 
                             onChange={(e) => setReportText(e.target.value)} 
                             className="w-full p-4 border rounded-xl bg-slate-50 text-slate-700 outline-none focus:border-indigo-400 focus:bg-white transition-all font-serif resize-none" 
                             placeholder="Write detailed diagnostic findings here..." />
                        </div>
                        <button onClick={handleWriteReport} disabled={reportSuccess} className={`${reportSuccess ? 'bg-emerald-500 hover:bg-emerald-500 scale-95 opacity-90' : 'bg-emerald-600 hover:bg-emerald-700'} text-white w-full py-3 rounded-xl font-bold shadow-md shadow-emerald-200 transition-all flex justify-center items-center gap-2`}>
                          <CheckCircle size={18}/> {reportSuccess ? "Report Finalized & Sent" : "Submit Final Report"}
                        </button>
                     </div>
                   )}
                 </div>
               </div>
            )}
            
            {activeTab === "archives" && (
               <div className="p-8">
                 <h2 className="text-xl font-black text-slate-800 mb-6 flex items-center gap-2"><FileText className="text-indigo-500"/> Published Report Archives</h2>
                 {reports.length === 0 ? (
                    <div className="text-center p-12 text-slate-400 font-bold border-2 border-dashed border-slate-200 rounded-2xl">No finalized reports found in the archive.</div>
                 ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {reports.filter((r) => r.status === 'final').map(report => {
                         const study = studies.find((s: any) => s.id === report.study_id); // Mapping the Order ID since our study_id is order_id in this context
                         return (
                           <div key={report.id} className="border border-slate-200 rounded-2xl p-5 hover:shadow-md transition-shadow bg-white">
                             <div className="flex justify-between items-start mb-3">
                               <div>
                                 <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider mb-2 inline-block">FINALIZED</span>
                                 <h3 className="font-bold text-slate-800">{study?.requested_study || "Radiology Scan"}</h3>
                                 <p className="text-xs text-slate-500 font-medium">Patient: {study ? getPatientName(study.patient_id) : "Unknown"}</p>
                               </div>
                               <FileText className="text-slate-300"/>
                             </div>
                             <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 mt-4 h-32 overflow-y-auto">
                               <p className="text-sm font-serif text-slate-700 whitespace-pre-wrap">{report.report_text}</p>
                             </div>
                             <div className="mt-4 text-[10px] font-mono text-slate-400 uppercase">
                               Report ID: {report.id} • Date: {new Date(report.reported_at || report.created_at || Date.now()).toLocaleString()}
                             </div>
                           </div>
                         );
                      })}
                    </div>
                 )}
               </div>
            )}

            {activeTab === "pacs" && (
               <div className="p-16 flex flex-col items-center justify-center text-slate-400 text-center min-h-[500px]">
                 <Play size={48} className="mb-4 opacity-50 text-indigo-500"/>
                 <h2 className="text-xl font-bold text-slate-600">DICOM Viewer GUI Embedded</h2>
                 <p className="max-w-md mt-2 text-sm">Upload a DICOM file to preview web viewer integration.</p>
               </div>
            )}
          </div>
        )}
      </div>

      {processingOrder && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm">
           <div className="bg-white rounded-2xl p-8 max-w-sm w-full text-center shadow-2xl relative">
              <Activity className="mx-auto text-indigo-500 animate-pulse mb-4" size={48}/>
              <h3 className="text-xl font-black text-slate-800 mb-2">Executing Pipeline</h3>
              <p className="text-sm text-slate-500 font-medium mb-4">
                {processingOrder.step === 'initiating' && "Creating DICOM Imaging Study..."}
                {processingOrder.step === 'scanning' && "Acquiring Images from Modality..."}
                {processingOrder.step === 'completing' && "Finalizing Billing & Timeline..."}
              </p>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden"><div className="bg-indigo-600 h-2 rounded-full animate-[pulse_1.5s_ease-in-out_infinite]"></div></div>
           </div>
        </div>
      )}

      {dicomUploadOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleDicomUpload} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-5">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2">
                <UploadCloud size={22} className="text-indigo-500"/> Upload DICOM
              </h3>
              <button type="button" onClick={() => setDicomUploadOpen(false)}><X size={20} className="text-slate-400 hover:text-slate-600"/></button>
            </div>
            <div className="border-2 border-dashed border-slate-300 rounded-2xl p-8 flex flex-col items-center justify-center bg-slate-50 hover:bg-slate-100 cursor-pointer">
               <Upload size={32} className="text-indigo-400 mb-3"/>
               <p className="text-sm font-bold text-slate-600">Drag & Drop .dcm file here</p>
               <input type="file" className="hidden" />
            </div>
            {uploadStatus && <div className="text-center text-sm font-bold text-emerald-600">{uploadStatus}</div>}
            <div className="pt-2"><button type="submit" className="w-full bg-indigo-600 text-white rounded-xl py-3 font-bold hover:bg-indigo-700">Simulate Upload</button></div>
          </form>
        </div>
      )}

      {showOrderModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateOrder} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-5">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2"><Calendar size={22} className="text-indigo-500"/> Schedule Scan</h3>
              <button type="button" onClick={() => setShowOrderModal(false)}><X size={20} className="text-slate-400 hover:text-slate-600"/></button>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase">Select Patient *</label>
              <select value={selectedPatientId} onChange={e => setSelectedPatientId(e.target.value)} required className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50">
                <option value="">— Select from Registry —</option>
                {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase">Modality</label>
                <select value={selectedModality} onChange={e => setSelectedModality(e.target.value)} className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50">
                  <option>X-ray</option><option>CT</option><option>MRI</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase">Study</label>
                <input value={studyName} onChange={e => setStudyName(e.target.value)} required className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50" placeholder="e.g. Brain MRI" />
              </div>
            </div>
            <button type="submit" className="w-full bg-indigo-600 text-white rounded-xl py-3 font-bold hover:bg-indigo-700">Create Order</button>
          </form>
        </div>
      )}
    </div>
  );
}
