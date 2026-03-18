"use client";
import React, { useState, useEffect } from "react";
import { 
  Activity, 
  Clock, 
  Calendar, 
  CheckCircle2, 
  AlertCircle, 
  Camera, 
  FileText, 
  Users, 
  ChevronRight,
  Plus,
  Search,
  Mic,
  ArrowRight,
  PieChart,
  HardDrive,
  X,
  TrendingUp,
  Monitor,
  User,
  Activity as ActivityIcon
} from "lucide-react";

interface RadiologyOrder {
  id: string;
  requested_modality: string;
  requested_study: string;
  priority: string;
  status: string;
  patient_id: string;
  ordered_at: string;
}

interface ImagingStudy {
  id: string;
  imaging_order_id: string;
  modality: string;
  status: string;
  machine_id?: string;
}

interface RadiologyReport {
  id: string;
  study_id: string;
  status: string;
  reported_at: string;
}

export default function RadiologyDashboard() {
  const [activeTab, setActiveTab] = useState<"queue" | "schedule" | "studies" | "reporting">("queue");
  const [orders, setOrders] = useState<RadiologyOrder[]>([]);
  const [studies, setStudies] = useState<ImagingStudy[]>([]);
  const [reports, setReports] = useState<RadiologyReport[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Use a predictable API URL with protocol and no extra slashes
  const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500").replace(/\/$/, "");

  // Modals
  const [showNewStudyModal, setShowNewStudyModal] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);

  // New Study State
  const [patients, setPatients] = useState<any[]>([]);
  const [encounters, setEncounters] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    patient_id: "",
    encounter_id: "",
    modality: "X-Ray",
    study_name: "",
    priority: "routine"
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
    fetchMetadata();
  }, []);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  // Auto-select latest encounter when patient is selected
  useEffect(() => {
    if (formData.patient_id && encounters.length > 0) {
      const patientEncounters = encounters
        .filter(e => e.patient_id === formData.patient_id)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      
      if (patientEncounters.length > 0) {
        setFormData(prev => ({ ...prev, encounter_id: patientEncounters[0].id }));
      } else {
        setFormData(prev => ({ ...prev, encounter_id: "" }));
      }
    }
  }, [formData.patient_id, encounters]);

  const handleProcessOrder = async (order: RadiologyOrder) => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token");
      const headers = { 
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      };

      // Create a unique Clinical Study Record
      const studyData = {
        imaging_order_id: order.id,
        study_uid: `RAD-${Date.now()}-${Math.random().toString(36).substr(2, 5).toUpperCase()}`,
        modality: order.requested_modality,
        status: "scheduled"
      };

      const res = await fetch(`${API_URL}/api/v1/radiology/studies`, {
        method: "POST",
        headers,
        body: JSON.stringify(studyData)
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Failed to initialize RIS study: ${errText}`);
      }
      
      alert("Imaging Study Initialized. Switching to Active Studies.");
      setActiveTab("studies");
      fetchData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const headers = { "Authorization": `Bearer ${token}` };
      const [oRes, sRes, rRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/radiology/orders`, { headers }),
        fetch(`${API_URL}/api/v1/radiology/studies`, { headers }),
        fetch(`${API_URL}/api/v1/radiology/reports`, { headers })
      ]);
      
      if (oRes.ok) setOrders(await oRes.json());
      if (sRes.ok) setStudies(await sRes.json());
      if (rRes.ok) setReports(await rRes.json());
    } catch (err) {
      console.error("Radiology global fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [impression, setImpression] = useState("");

  const handleStartScan = async (studyId: string) => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_URL}/api/v1/radiology/start-study?study_id=${studyId}&machine_id=RAD-01`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Could not start scan");
      alert("Scan Started. Room RAD-01 occupied.");
      fetchData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteScan = async (studyId: string) => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_URL}/api/v1/radiology/complete-study?study_id=${studyId}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Could not complete scan");
      alert("Scan Completed. Charges posted to billing.");
      fetchData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDraftReport = async (studyId: string) => {
     try {
        const token = localStorage.getItem("access_token");
        const res = await fetch(`${API_URL}/api/v1/radiology/report`, {
          method: "POST",
          headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ study_id: studyId, report_text: "" })
        });
        if (!res.ok) throw new Error("Failed to create report draft");
        const draft = await res.json();
        setSelectedReport(draft);
        fetchData();
     } catch (err: any) {
        alert(err.message);
     }
  };

  const handleFinalizeReport = async () => {
    if (!selectedReport) return;
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_URL}/api/v1/radiology/report/${selectedReport.id}/finalize?impression=${encodeURIComponent(impression)}&critical_flag=false`, {
        method: "PUT",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Finalization failed");
      alert("Report Finalized and Results Published.");
      setSelectedReport(null);
      setImpression("");
      fetchData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetadata = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const headers = { 
        "Authorization": `Bearer ${token}`,
        "Accept": "application/json"
      };
      
      // Hit direct endpoints (clean)
      const [pRes, eRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/patients/?limit=100`, { headers }),
        fetch(`${API_URL}/api/v1/encounters/?limit=100`, { headers })
      ]);
      
      if (pRes.ok) setPatients(await pRes.json());
      if (eRes.ok) setEncounters(await eRes.json());
    } catch (err) {
      console.error("Radiology metadata fetch failed:", err);
    }
  };

  const handleCreateStudy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.patient_id || !formData.encounter_id || !formData.study_name) {
      alert("Missing mandatory clinical fields.");
      return;
    }
    
    setSubmitting(true);
    const token = localStorage.getItem("access_token");
    const headers = { 
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    };

    try {
      // 1. Core Order - Hit endpoint WITHOUT trailing slash (matches backend @router.post(""))
      const ordersUrl = `${API_URL}/api/v1/orders`;
      console.log(`Initiating Core Order: ${ordersUrl}`);
      
      const orderRes = await fetch(ordersUrl, {
        method: "POST",
        headers,
        body: JSON.stringify({
          patient_id: formData.patient_id,
          encounter_id: formData.encounter_id,
          order_type: "RADIOLOGY_ORDER",
          priority: formData.priority.toUpperCase(),
          items: [{
            item_type: "radiology_test",
            item_name: `${formData.modality}: ${formData.study_name}`,
            quantity: 1,
            unit_price: 100.0
          }]
        })
      });
      
      if (!orderRes.ok) {
        const errText = await orderRes.text();
        throw new Error(`Core Hospital Order Failed (Status ${orderRes.status}): ${errText}`);
      }
      
      const coreOrder = await orderRes.json();
      console.log("Stage 1 Success:", coreOrder.id);

      // 2. Radiology Record - Hit /api/v1/radiology/order
      const radUrl = `${API_URL}/api/v1/radiology/order`;
      console.log(`Initiating RIS Study: ${radUrl}`);
      
      const radRes = await fetch(radUrl, {
        method: "POST",
        headers,
        body: JSON.stringify({
          order_id: coreOrder.id,
          encounter_id: formData.encounter_id,
          patient_id: formData.patient_id,
          requested_modality: formData.modality,
          requested_study: formData.study_name,
          priority: formData.priority
        })
      });

      if (!radRes.ok) {
        const errText = await radRes.text();
        throw new Error(`Radiology Record Creation Failed: ${errText}`);
      }

      setShowNewStudyModal(false);
      alert("Imaging Study Initialized and Logged.");
      fetchData();
    } catch (err: any) {
      console.error("Radiology Detailed Error:", err);
      if (err.message === "Failed to fetch") {
        alert("Networking Failure: The browser could not reach the backend at " + API_URL + ". Ensure your dev server or backend container is running on port 9500.");
      } else {
        alert(err.message);
      }
    } finally {
      setSubmitting(false);
    }
  };

  // Derivative stats
  const pendingOrdersCount = orders.filter(o => o.status === "pending").length;
  const inProgressCount = studies.filter(s => s.status === "scanning").length;
  const reportsNeededCount = studies.filter(s => s.status === "completed").length;

  return (
    <div className="p-8 bg-slate-50 min-h-screen relative font-sans text-slate-900">
      {/* Header */}
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Radiology Information System</h1>
          <p className="text-slate-500 mt-1 font-medium flex items-center gap-2">
            <ActivityIcon size={16} className="text-indigo-500" /> Phase 11 &ndash; Synchronized Clinical Integration
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => setShowAnalyticsModal(true)}
            className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-slate-600 font-bold hover:bg-slate-50 transition shadow-sm flex items-center gap-2"
          >
            <PieChart size={18} /> Analytics
          </button>
          <button 
            onClick={() => setShowNewStudyModal(true)}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition shadow-lg shadow-indigo-100 flex items-center gap-2"
          >
            <Plus size={18} /> New Study
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard icon={<Clock className="text-amber-500" />} label="Pending Orders" value={pendingOrdersCount.toString()} color="amber" />
        <StatCard icon={<Calendar className="text-indigo-500" />} label="Total Studies" value={studies.length.toString()} color="indigo" />
        <StatCard icon={<ActivityIcon className="text-emerald-500" />} label="In Progress" value={inProgressCount.toString()} color="emerald" />
        <StatCard icon={<CheckCircle2 className="text-slate-500" />} label="Reports Pending" value={reportsNeededCount > 0 ? reportsNeededCount.toString() : "0"} color="slate" />
      </div>

      {/* Main Content Areas */}
      <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden">
        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-100 p-2">
          <TabButton active={activeTab === "queue"} onClick={() => setActiveTab("queue")} icon={<Users size={18} />} label="Orders Queue" />
          <TabButton active={activeTab === "schedule"} onClick={() => setActiveTab("schedule")} icon={<Calendar size={18} />} label="Scan Schedule" />
          <TabButton active={activeTab === "studies"} onClick={() => setActiveTab("studies")} icon={<Camera size={18} />} label="Active Studies" />
          <TabButton active={activeTab === "reporting"} onClick={() => setActiveTab("reporting")} icon={<FileText size={18} />} label="Reporting Hub" />
        </div>

        {/* Dynamic Content */}
        <div className="p-6">
          {activeTab === "queue" && (
            <div className="space-y-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-slate-800">Imaging Order Queue</h3>
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
                  <input type="text" placeholder="Search Patient ID..." className="pl-10 pr-4 py-2 bg-slate-50 border-none rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none w-64" />
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      <th className="px-4 py-3">Modality</th>
                      <th className="px-4 py-3">Study / Procedure</th>
                      <th className="px-4 py-3">Patient ID</th>
                      <th className="px-4 py-3">Priority</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {orders.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-12 text-center text-slate-400 italic">No real-time imaging orders found in database.</td>
                      </tr>
                    ) : orders.map(order => (
                      <tr key={order.id} className="hover:bg-slate-50 transition group">
                        <td className="px-4 py-4">
                          <span className="px-2 py-1 bg-indigo-50 text-indigo-600 rounded-lg text-[10px] font-bold uppercase tracking-tight">{order.requested_modality}</span>
                        </td>
                        <td className="px-4 py-4 font-bold text-slate-700">{order.requested_study}</td>
                        <td className="px-4 py-4 text-xs font-mono text-slate-500">{order.patient_id.substring(0, 13)}...</td>
                        <td className="px-4 py-4">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            order.priority.toLowerCase() === "stat" ? "bg-rose-100 text-rose-600" : 
                            order.priority.toLowerCase() === "urgent" ? "bg-amber-100 text-amber-600" : 
                            "bg-slate-100 text-slate-600"
                          }`}>
                            {order.priority.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                           <div className="flex items-center gap-2">
                             <div className={`w-1.5 h-1.5 rounded-full ${order.status === "pending" ? "bg-amber-400" : "bg-indigo-400"}`} />
                             <span className="text-sm font-medium text-slate-600 capitalize">{order.status}</span>
                           </div>
                        </td>
                        <td className="px-4 py-4 text-right">
                          <button 
                            onClick={() => handleProcessOrder(order)}
                            className="p-2 text-indigo-600 hover:bg-indigo-100 rounded-lg transition"
                            title="Process Order / Initialize Study"
                          >
                            <ArrowRight size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "reporting" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 text-slate-900">
               <div className="lg:col-span-1 space-y-4">
                  <h3 className="font-bold text-slate-800 flex items-center gap-2">
                    <Clock size={18} className="text-indigo-500" /> Interpretation Worklist
                  </h3>
                  <div className="space-y-3">
                    {reports.length === 0 && studies.filter(s => s.status === "completed").length === 0 && <p className="text-xs text-slate-400 italic p-4">No reports currently in workflow.</p>}
                    {reports.map(report => (
                       <div key={report.id} onClick={() => setSelectedReport(report)}>
                          <ReportingListItem 
                             patient={`Patient ${report.id.substring(0,4)}`} 
                             study={`Modality Scan ID ${report.study_id.substring(0,4)}`} 
                             priority={report.status === "draft" ? "DRAFT" : "FINAL"} 
                             time={new Date(report.reported_at).toLocaleTimeString()} 
                          />
                       </div>
                    ))}
                    {studies.filter(s => s.status === "completed" && !reports.some(r => r.study_id === s.id)).map(study => (
                       <div key={study.id} onClick={() => handleCreateDraftReport(study.id)}>
                          <ReportingListItem 
                             patient={`Patient ${study.id.substring(0,4)}`} 
                             study={`${study.modality} Study`} 
                             priority="PENDING" 
                             time="Scan Completed" 
                          />
                       </div>
                    ))}
                  </div>
               </div>
               
               <div className="lg:col-span-2 bg-slate-50 rounded-2xl p-6 border border-slate-100 min-h-[500px] flex flex-col">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h4 className="font-bold text-slate-900">
                        {selectedReport 
                          ? `Rad-Workstation: ${selectedReport.study_id.substring(0,8)}` 
                          : "Radiologist Workstation"}
                      </h4>
                      <p className="text-xs text-slate-500">
                        {selectedReport ? "Modality: LIVE DICOM FEED" : "DICOM Viewer + Structured Reporting"}
                      </p>
                    </div>
                    <div className="flex gap-2">
                       <button className="p-2 bg-white rounded-lg border border-slate-200 text-slate-500 hover:text-indigo-600 transition"><Mic size={18} /></button>
                       <button 
                          onClick={handleFinalizeReport}
                          disabled={!selectedReport || !impression}
                          className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold shadow-md shadow-indigo-100 disabled:opacity-50"
                        >
                          Finalize Report
                       </button>
                    </div>
                  </div>
                  
                  <div className="flex-1 bg-black rounded-xl border border-slate-800 flex flex-col items-center justify-center text-slate-600 gap-4 relative group overflow-hidden">
                     {selectedReport ? (
                        <div className="flex flex-col items-center gap-3">
                           <Monitor size={48} className="text-emerald-500 animate-pulse" />
                           <p className="text-xs font-mono text-emerald-500 uppercase tracking-widest bg-emerald-950 px-2 py-1 rounded">Locked on Study: {selectedReport.study_id.substring(0,10)}</p>
                        </div>
                     ) : (
                        <>
                           <HardDrive size={48} className="opacity-20 group-hover:scale-110 transition duration-500" />
                           <p className="text-xs font-mono opacity-50 uppercase tracking-widest">Connect to PACS / Load Study UID</p>
                        </>
                     )}
                     
                     <div className="absolute top-2 left-2 flex gap-1">
                        <div className="w-1.5 h-1.5 bg-rose-500 rounded-full" />
                        <div className="w-1.5 h-1.5 bg-amber-500 rounded-full" />
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                     </div>
                  </div>
                  
                  <div className="mt-6 bg-white rounded-xl border border-slate-200 p-4">
                     <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Clinical Impression & Findings</label>
                     <textarea 
                        className="w-full text-sm text-slate-700 min-h-[120px] outline-none resize-none placeholder:italic"
                        placeholder="Type or dictate clinical findings here..."
                        value={impression}
                        onChange={(e) => setImpression(e.target.value)}
                        disabled={!selectedReport}
                     ></textarea>
                  </div>
               </div>
            </div>
          )}
          
          {(activeTab === "studies") && (
            <div className="space-y-4">
               <h3 className="font-bold text-slate-800">Active / Completed Studies</h3>
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {studies.length === 0 && <p className="col-span-full py-20 text-center text-slate-400 italic">No studies recorded.</p>}
                  {studies.map(study => (
                    <div key={study.id} className="p-4 bg-white border border-slate-100 rounded-2xl shadow-sm hover:shadow-md transition">
                       <div className="flex justify-between items-start mb-3">
                          <span className="px-2 py-1 bg-indigo-50 text-indigo-600 rounded-lg text-[10px] font-bold uppercase">{study.modality}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            study.status === "scheduled" ? "bg-slate-100 text-slate-600" :
                            study.status === "scanning" ? "bg-amber-100 text-amber-600 animate-pulse" :
                            "bg-emerald-100 text-emerald-600"
                          }`}>{study.status.toUpperCase()}</span>
                       </div>
                       <p className="text-sm font-bold text-slate-800 mb-1">Study ID: {study.id.substring(0,8)}</p>
                       <p className="text-xs text-slate-500 font-mono">Order ID: {study.imaging_order_id.substring(0,8)}</p>
                       <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-50">
                          {study.status === "scheduled" && (
                             <button 
                                onClick={() => handleStartScan(study.id)}
                                className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 text-amber-600 rounded-lg text-[10px] font-bold hover:bg-amber-100 transition"
                             >
                                <Activity size={12}/> START SCAN
                             </button>
                          )}
                          {study.status === "scanning" && (
                             <button 
                                onClick={() => handleCompleteScan(study.id)}
                                className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-600 rounded-lg text-[10px] font-bold hover:bg-emerald-100 transition"
                             >
                                <CheckCircle2 size={12}/> COMPLETE SCAN
                             </button>
                          )}
                          {study.status === "completed" && (
                             <span className="text-[10px] font-bold text-slate-400 italic">Awaiting Report</span>
                          )}
                       </div>
                    </div>
                  ))}
               </div>
            </div>
          )}

          {(activeTab === "schedule") && (
            <div className="py-20 text-center text-slate-400">
               <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100">
                 <Calendar size={24} />
               </div>
               <p className="font-bold text-slate-600">Scan Schedule Initialized</p>
               <p className="text-xs">Database slots are being synchronization with ward availability.</p>
            </div>
          )}
        </div>
      </div>

      {/* New Study Modal */}
      {showNewStudyModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-white rounded-[32px] shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200 text-slate-900">
            <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-indigo-50/50">
              <div>
                <h2 className="text-2xl font-black text-slate-900">Initialize New Study</h2>
                <p className="text-sm text-slate-500 font-medium">Create direct imaging request</p>
              </div>
              <button 
                onClick={() => setShowNewStudyModal(false)}
                className="p-2 hover:bg-white rounded-full transition text-slate-400 hover:text-rose-500"
              >
                <X size={24} />
              </button>
            </div>
            
            <form onSubmit={handleCreateStudy} className="p-8 space-y-5">
              <div className="space-y-2">
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Patient</label>
                <div className="relative">
                  <User className="absolute left-3 top-3 text-slate-400" size={18} />
                  <select 
                    required
                    className="w-full pl-10 pr-4 py-3 bg-slate-50 border-none rounded-2xl text-sm font-medium focus:ring-2 focus:ring-indigo-500 outline-none appearance-none cursor-pointer"
                    value={formData.patient_id}
                    onChange={(e) => setFormData({...formData, patient_id: e.target.value})}
                  >
                    <option value="">Select Patient</option>
                    {patients.map(p => (
                      <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.patient_uuid})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Encounter</label>
                <div className="relative">
                  <ActivityIcon className="absolute left-3 top-3 text-slate-400" size={18} />
                  <select 
                    required
                    className="w-full pl-10 pr-4 py-3 bg-slate-50 border-none rounded-2xl text-sm font-medium focus:ring-2 focus:ring-indigo-500 outline-none appearance-none cursor-pointer text-slate-900"
                    value={formData.encounter_id}
                    onChange={(e) => setFormData({...formData, encounter_id: e.target.value})}
                  >
                    <option value="">Select Encounter</option>
                    {encounters.filter(e => e.patient_id === formData.patient_id).map(e => {
                      const date = new Date(e.created_at).toLocaleDateString();
                      return <option key={e.id} value={e.id} className="text-slate-900">{e.encounter_type} - {date}</option>;
                    })}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Modality</label>
                  <select 
                    className="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl text-sm font-medium focus:ring-2 focus:ring-indigo-500 outline-none appearance-none cursor-pointer"
                    value={formData.modality}
                    onChange={(e) => setFormData({...formData, modality: e.target.value})}
                  >
                    <option>X-Ray</option>
                    <option>CT Scan</option>
                    <option>MRI</option>
                    <option>Ultrasound</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Priority</label>
                  <select 
                    className="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl text-sm font-medium focus:ring-2 focus:ring-indigo-500 outline-none appearance-none cursor-pointer"
                    value={formData.priority}
                    onChange={(e) => setFormData({...formData, priority: e.target.value})}
                  >
                    <option value="routine">Routine</option>
                    <option value="urgent">Urgent</option>
                    <option value="stat">STAT</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Study Name / Procedure</label>
                <div className="relative">
                  <Monitor className="absolute left-3 top-3 text-slate-400" size={18} />
                  <input 
                    type="text"
                    required
                    placeholder="e.g. Chest AP View"
                    className="w-full pl-10 pr-4 py-3 bg-slate-50 border-none rounded-2xl text-sm font-medium focus:ring-2 focus:ring-indigo-500 outline-none text-slate-900"
                    value={formData.study_name}
                    onChange={(e) => setFormData({...formData, study_name: e.target.value})}
                  />
                </div>
              </div>

              <div className="pt-4">
                <button 
                  disabled={submitting}
                  className="w-full py-4 bg-indigo-600 text-white rounded-[20px] font-extrabold text-lg hover:bg-indigo-700 transition shadow-xl shadow-indigo-100 disabled:opacity-50 flex items-center justify-center gap-3"
                >
                  {submitting ? "Initializing..." : <>Initialize Request <ChevronRight size={20}/></>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Analytics Modal */}
      {showAnalyticsModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-white rounded-[32px] shadow-2xl w-full max-w-4xl overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-8 border-b border-slate-100 flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-black text-slate-900 flex items-center gap-3">
                  <PieChart size={28} className="text-indigo-600" /> Radiology Department Analytics
                </h2>
                <p className="text-sm text-slate-500 font-medium">Live Operational Metrics & Insights</p>
              </div>
              <button 
                onClick={() => setShowAnalyticsModal(false)}
                className="p-2 hover:bg-slate-50 rounded-full transition text-slate-400"
              >
                <X size={24} />
              </button>
            </div>
            
            <div className="p-8 grid grid-cols-1 md:grid-cols-3 gap-8 text-slate-900 font-sans">
               <div className="space-y-6">
                  <div className="p-4 bg-indigo-50 rounded-2xl border border-indigo-100">
                     <p className="text-xs font-bold text-indigo-400 uppercase mb-4 tracking-widest">Orders by Modality</p>
                     <div className="space-y-3">
                        {["X-Ray", "CT Scan", "MRI", "Ultrasound"].map(m => {
                          const count = orders.filter(o => o.requested_modality === m).length;
                          const total = orders.length || 1;
                          const percentage = Math.round((count / total) * 100);
                          return (
                            <div key={m}>
                               <div className="flex justify-between text-xs font-bold text-slate-600 mb-1">
                                  <span>{m}</span>
                                  <span>{count}</span>
                                </div>
                               <div className="w-full h-1.5 bg-white rounded-full overflow-hidden">
                                  <div className="h-full bg-indigo-500 rounded-full" style={{width: `${percentage}%`}}></div>
                               </div>
                            </div>
                          )
                        })}
                     </div>
                  </div>
                  
                  <div className="p-6 bg-slate-900 rounded-3xl text-white shadow-xl shadow-indigo-900/10">
                     <TrendingUp size={32} className="text-indigo-400 mb-4" />
                     <p className="text-3xl font-black mb-1">94%</p>
                     <p className="text-[10px] font-bold text-indigo-300 uppercase underline decoration-2 underline-offset-4 tracking-tighter">Throughput Efficiency</p>
                  </div>
               </div>
               
               <div className="md:col-span-2 space-y-6 text-center">
                  <div className="grid grid-cols-2 gap-4">
                     <div className="p-6 bg-white border border-slate-100 rounded-[24px] shadow-sm">
                        <CheckCircle2 size={24} className="text-emerald-500 mb-2 mx-auto" />
                        <p className="text-2xl font-black text-slate-900 tracking-tight">{studies.filter(s => s.status === "completed").length}</p>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Completed Scans</p>
                     </div>
                     <div className="p-6 bg-white border border-slate-100 rounded-[24px] shadow-sm">
                        <AlertCircle size={24} className="text-rose-500 mb-2 mx-auto" />
                        <p className="text-2xl font-black text-slate-900 tracking-tight">{orders.filter(o => o.priority.toLowerCase() === "stat").length}</p>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Stat Requests</p>
                     </div>
                  </div>
                  
                  <div className="relative h-64 bg-slate-50 rounded-[32px] border border-dashed border-slate-200 flex flex-col items-center justify-center p-8 gap-4 group">
                     <div className="flex items-end gap-2 h-32">
                        {[40, 70, 45, 90, 65, 80, 55].map((h, i) => (
                          <div key={i} className="w-6 bg-indigo-200 rounded-t-lg group-hover:bg-indigo-500 transition-colors duration-500 shadow-sm" style={{height: `${h}%`}}></div>
                        ))}
                     </div>
                     <p className="text-[11px] font-bold text-slate-400 uppercase tracking-tighter">Scanning Volume &ndash; Past 7 Days</p>
                  </div>
               </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: any, label: string, value: string, color: string }) {
  const colorMap: any = {
    amber: "border-amber-100 bg-amber-50/30",
    indigo: "border-indigo-100 bg-indigo-50/30",
    emerald: "border-emerald-100 bg-emerald-50/30",
    slate: "border-slate-100 bg-slate-50/30"
  };
  
  return (
    <div className={`p-6 rounded-3xl border ${colorMap[color]} transition hover:shadow-lg hover:shadow-slate-200/50 group`}>
      <div className="w-10 h-10 rounded-xl bg-white border border-slate-100 flex items-center justify-center mb-4 shadow-sm group-hover:scale-110 transition">
        {icon}
      </div>
      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-black text-slate-900 tracking-tight">{value}</p>
    </div>
  );
}

function TabButton({ active, onClick, icon, label }: { active: boolean, onClick: any, icon: any, label: string }) {
  return (
    <button 
      onClick={onClick}
      className={`px-6 py-3 rounded-2xl flex items-center gap-3 transition-all duration-300 font-bold text-sm ${
        active 
          ? "bg-slate-900 text-white shadow-lg translate-y-[-2px]" 
          : "text-slate-500 hover:text-indigo-600 hover:bg-slate-50"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function ReportingListItem({ patient, study, priority, time }: { patient: string, study: string, priority: string, time: string }) {
  return (
    <div className="flex items-center gap-4 p-4 bg-white border border-slate-100 rounded-2xl hover:border-indigo-200 transition group cursor-pointer shadow-sm">
       <div className={`w-1 h-8 rounded-full ${
         priority === "STAT" || priority === "PENDING" ? "bg-rose-500" : priority === "URGENT" || priority === "DRAFT" ? "bg-amber-500" : "bg-emerald-500"
       }`} />
       <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-slate-800 truncate">{patient}</p>
          <p className="text-[11px] text-slate-500 font-medium truncate">{study}</p>
       </div>
       <div className="text-right text-slate-900">
          <p className="text-[10px] font-bold text-slate-400 mb-1 tracking-tight">{time}</p>
          <div className="flex items-center gap-1 justify-end">
            <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${
               priority === "FINAL" ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-400"
            }`}>{priority}</span>
            <ChevronRight size={14} className="text-slate-300 group-hover:text-indigo-500 group-hover:translate-x-1 transition" />
          </div>
       </div>
    </div>
  );
}
