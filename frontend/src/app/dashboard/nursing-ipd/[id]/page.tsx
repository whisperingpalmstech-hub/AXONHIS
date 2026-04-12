"use client";
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  Activity, HeartPulse, Droplets, Thermometer, ChevronLeft, 
  User, Calendar, Stethoscope, AlertTriangle, FileText,
  Pill, TestTube, Beaker, Clock, Edit3, Save, CheckCircle, Scan, X
} from "lucide-react";
import { nursingApi } from "@/lib/nursing-api";

type CoverTab = "COMPLAINTS" | "DIAGNOSIS" | "NOTES" | "VITALS" | "MAR" | "IO_CHART" | "LAB";

export default function IpdNursingCoversheet() {
  const params = useParams();
  const router = useRouter();
  const admission_number = params.id as string;
  const [activeTab, setActiveTab] = useState<CoverTab>("VITALS");

  // Real Backend State
  const [loading, setLoading] = useState(true);
  const [vitalsData, setVitalsData] = useState<any[]>([]);
  const [notesData, setNotesData] = useState<any[]>([]);
  const [marQueue, setMarQueue] = useState<any[]>([]);
  const [inboundDeliveries, setInboundDeliveries] = useState<any[]>([]);

  // Form State
  const [newNote, setNewNote] = useState("");
  
  // Modals
  const [showVitalsModal, setShowVitalsModal] = useState(false);
  const [vitalsForm, setVitalsForm] = useState({ hr: "", bp_s: "", bp_d: "", spo2: "", temp: "", rr: "" });

  const [showScanModal, setShowScanModal] = useState<any>(null);
  const [scanCode, setScanCode] = useState("");

  // UI Interactive States
  const [complaints, setComplaints] = useState<any[]>([]);
  const [showComplaintModal, setShowComplaintModal] = useState(false);
  const [complaintForm, setComplaintForm] = useState({ title: "", details: "" });

  const [diagnoses, setDiagnoses] = useState<any[]>([]);
  const [newDiagnosis, setNewDiagnosis] = useState("");

  const [ioRecords, setIoRecords] = useState<any[]>([]);
  const [showIoModal, setShowIoModal] = useState<"Intake" | "Output" | null>(null);
  const [ioForm, setIoForm] = useState({ category: "", volume: "" });

  const [labs, setLabs] = useState<any[]>([]);
  const [showPdfAlert, setShowPdfAlert] = useState(false);

  // Computations
  const totalIntake = ioRecords.filter(r => r.type === "Intake").reduce((acc, curr) => acc + curr.value, 0);
  const totalOutput = ioRecords.filter(r => r.type === "Output").reduce((acc, curr) => acc + Math.abs(curr.value), 0);
  const netBalance = totalIntake - totalOutput;

  // Generic Handlers
  const handleAddComplaint = () => {
    if (!complaintForm.title) return;
    setComplaints([{ id: Date.now(), title: complaintForm.title, details: complaintForm.details, severity: "New Complaint", clx: "bg-indigo-100 text-indigo-700", duration: "Just Now" }, ...complaints]);
    setComplaintForm({ title: "", details: "" });
    setShowComplaintModal(false);
  };
  const handleLinkDiagnosis = () => {
    if (!newDiagnosis) return;
    setDiagnoses([...diagnoses, { id: Date.now(), type: "Comorbidity", label: "Comorbidity", clx: "bg-emerald-100 text-emerald-700", desc: newDiagnosis, status: "Active" }]);
    setNewDiagnosis("");
  };
  const handleAddIo = () => {
    if (!ioForm.volume) return;
    const isIntake = showIoModal === "Intake";
    setIoRecords([...ioRecords, { id: Date.now(), time: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit' }), type: showIoModal!, category: ioForm.category || (isIntake ? "Oral Fluid" : "Urine"), value: isIntake ? parseInt(ioForm.volume) : -parseInt(ioForm.volume), typeClx: isIntake ? "bg-blue-100 text-blue-700" : "bg-amber-100 text-amber-700", valClx: isIntake ? "text-blue-600" : "text-amber-600" }]);
    setIoForm({ category: "", volume: "" });
    setShowIoModal(null);
  };
  const handleOrderLab = () => {
    // Navigate strictly to the Enterprise Orders Desk for this patient
    router.push(`/dashboard/ipd-orders?admission_number=${admission_number}&uhid=UHID-9928`);
  };

  const handleDownloadPDF = (labTitle: string) => {
    setShowPdfAlert(true);
    setTimeout(() => {
      setShowPdfAlert(false);
      // Generate a dynamic enterprise PDF Blob on the fly natively
      const pdfContent = `
        %PDF-1.4
        1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
        2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
        3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj
        4 0 obj <</Length 200>> stream
        BT
        /F1 24 Tf
        100 700 Td
        (AXONHIS LAB REPORT) Tj
        0 -40 Td
        /F1 14 Tf
        (Patient: Sneha Joshi [UHID-9928]) Tj
        0 -30 Td
        (Test: ${labTitle}) Tj
        0 -30 Td
        (Status: VERIFIED AND RELEASED) Tj
        0 -50 Td
        (Results are strictly confidential.) Tj
        ET
        endstream
        endobj
        5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold>> endobj
        xref
        0 6
        0000000000 65535 f
        0000000009 00000 n
        0000000052 00000 n
        0000000101 00000 n
        0000000216 00000 n
        0000000466 00000 n
        trailer <</Size 6 /Root 1 0 R>>
        startxref
        553
        %%EOF
      `;
      const blob = new Blob([pdfContent.trim().replace(/^\s+/gm, '')], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    }, 1500);
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await nursingApi.getCoversheet(admission_number);
      if (data.vitals) setVitalsData(data.vitals);
      if (data.notes) setNotesData(data.notes);
      if (data.mar && data.mar.length > 0) setMarQueue(data.mar);
      
      // Fetch inbound "Dispensed" Pharmacy records
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9500'}/api/v1/pharmacy/ip-issues?status=Dispensed`);
      if (res.ok) {
         const issues = await res.json();
         // strictly bind by admission_number
         setInboundDeliveries(issues.filter((i: any) => i.admission_number === admission_number));
      }
    } catch (e) {
      console.error("Failed to fetch coversheet", e);
    } finally {
      setLoading(false);
    }
  }, [admission_number]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Submit Handlers
  const handleSaveNote = async () => {
    if (!newNote.trim()) return;
    try {
      await nursingApi.addClinicalNote({
        admission_number,
        patient_uhid: "UHID-9928",
        note_type: "Progress Note Update",
        clinical_note: newNote
      });
      setNewNote("");
      fetchData();
    } catch(e) {
      console.error(e);
      // Fallback for demo
      setNotesData([{ title: "Progress Note Update", recorded_at: new Date().toISOString(), clinical_note: newNote, nurse_uuid: "Me" }, ...notesData]);
      setNewNote("");
    }
  };

  const handleSubmitVitals = async () => {
    try {
      await nursingApi.logVitals({
        admission_number,
        patient_uhid: "UHID-9928",
        heart_rate: parseInt(vitalsForm.hr) || null,
        blood_pressure_sys: parseInt(vitalsForm.bp_s) || null,
        blood_pressure_dia: parseInt(vitalsForm.bp_d) || null,
        spo2: parseFloat(vitalsForm.spo2) || null,
        temperature_f: parseFloat(vitalsForm.temp) || null,
        respiratory_rate: parseInt(vitalsForm.rr) || null,
      });
      setShowVitalsModal(false);
      setVitalsForm({ hr: "", bp_s: "", bp_d: "", spo2: "", temp: "", rr: "" });
      fetchData();
    } catch(e) {
      console.error(e);
      // Fallback UI update
      setVitalsData([{ 
        heart_rate: vitalsForm.hr, blood_pressure_sys: vitalsForm.bp_s, blood_pressure_dia: vitalsForm.bp_d, 
        spo2: vitalsForm.spo2, temperature_f: vitalsForm.temp, is_abnormal: false 
      }, ...vitalsData]);
      setShowVitalsModal(false);
    }
  };

  const handleAdministerDrug = () => {
    if (!scanCode.trim() || !showScanModal) return;
    setMarQueue(marQueue.map(m => m.id === showScanModal.id ? { ...m, is_administered: true, batch_number: scanCode } : m));
    setShowScanModal(null);
    setScanCode("");
  };

  const handleNursingAcceptance = async (issueId: string, accepted: boolean, rejectionReason?: string) => {
    try {
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9500'}/api/v1/pharmacy/ip-issues/${issueId}/nursing-acceptance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ accepted, rejection_reason: rejectionReason || null })
      });
      if (resp.ok) fetchData();
    } catch (error) { console.error("Acceptance failed", error); }
  };

  const latestVitals = vitalsData.length > 0 ? vitalsData[0] : { heart_rate: 84, blood_pressure_sys: 120, blood_pressure_dia: 80, spo2: 98, temperature_f: 98.6 };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* PERSISTENT PATIENT CONTEXT BAR */}
      <div className="bg-slate-900 text-white border-b border-indigo-900 sticky top-0 z-10 flex-shrink-0 shadow-lg shadow-indigo-900/20">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center gap-6">
            <button onClick={() => router.back()} className="text-slate-400 hover:text-white transition">
              <ChevronLeft size={24} />
            </button>
            <div className="flex items-center gap-4 border-r border-slate-700 pr-6">
              <div className="bg-indigo-600 rounded-full w-12 h-12 flex items-center justify-center font-black text-xl shadow-inner border border-indigo-400">
                SJ
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">Sneha Joshi</h1>
                <div className="flex items-center gap-2 text-sm text-indigo-200 mt-0.5">
                  <span className="font-bold">{admission_number}</span> • <span className="font-mono">UHID-9928</span> • <span>42Y / F</span>
                </div>
              </div>
            </div>
            <div className="flex-1 grid grid-cols-4 gap-6 px-4">
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Location</span>
                <span className="text-sm font-semibold flex items-center gap-1.5"><Activity size={14} className="text-emerald-400"/> Ward 4 • Bed A2</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Consulting</span>
                <span className="text-sm font-semibold flex items-center gap-1.5"><Stethoscope size={14} className="text-amber-400"/> Dr. R. K. Sharma</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Primary Dx</span>
                <span className="text-sm font-semibold text-white">Acute Appendicitis</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Allergies</span>
                <span className="text-sm font-bold text-rose-400 flex items-center gap-1.5"><AlertTriangle size={14}/> Penicillin</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* TABS NAVIGATION */}
      <div className="bg-white border-b border-slate-200 sticky top-[81px] z-10 shadow-sm">
        <div className="max-w-[1600px] mx-auto px-6">
          <div className="flex gap-1 overflow-x-auto scroolbar-hide">
            {[
              { id: "COMPLAINTS", label: "Complaints & Hx", icon: <User size={16}/> },
              { id: "DIAGNOSIS", label: "Diagnosis", icon: <Stethoscope size={16}/> },
              { id: "VITALS", label: "Vitals trending", icon: <HeartPulse size={16}/> },
              { id: "NOTES", label: "Clinical Notes", icon: <FileText size={16}/> },
              { id: "MAR", label: "Drug Chart (MAR)", icon: <Pill size={16}/> },
              { id: "IO_CHART", label: "Intake/Output", icon: <Droplets size={16}/> },
              { id: "LAB", label: "Labs & Samples", icon: <TestTube size={16}/> },
            ].map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id as CoverTab)}
                className={`flex items-center gap-2 px-5 py-3.5 border-b-2 text-sm font-bold transition-all whitespace-nowrap ${
                  activeTab === tab.id 
                    ? "border-indigo-600 text-indigo-700 bg-indigo-50/50" 
                    : "border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50"
                }`}>
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 max-w-[1600px] w-full mx-auto p-6 overflow-y-auto">
        {loading ? <div className="text-center mt-20 text-slate-400 font-bold animate-pulse">Loading Charting Engine...</div> : <>
        
        {/* VITALS TAB */}
        {activeTab === "VITALS" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-between items-center bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
              <h2 className="text-base font-black text-slate-800 uppercase">Recent Vitals</h2>
              <button onClick={() => setShowVitalsModal(true)} className="px-4 py-2 bg-rose-600 text-white font-bold text-sm rounded-lg hover:bg-rose-700 transition shadow-sm">
                + New Charting
              </button>
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-red-200/50 shadow-sm shadow-red-100/50">
                <span className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5"><HeartPulse size={14} className="text-red-500"/> Heart Rate</span>
                <div className="mt-2 text-3xl font-black text-slate-800">{latestVitals.heart_rate || '-'} <span className="text-base opacity-40">bpm</span></div>
              </div>
              <div className="bg-white p-5 rounded-2xl border border-blue-200/50 shadow-sm shadow-blue-100/50">
                <span className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5"><Activity size={14} className="text-blue-500"/> BP</span>
                <div className="mt-2 text-3xl font-black text-slate-800">{latestVitals.blood_pressure_sys || '-'}/{latestVitals.blood_pressure_dia || '-'} <span className="text-base opacity-40">mmHg</span></div>
              </div>
              <div className="bg-white p-5 rounded-2xl border border-emerald-200/50 shadow-sm shadow-emerald-100/50">
                <span className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5"><Droplets size={14} className="text-emerald-500"/> SpO2</span>
                <div className="mt-2 text-3xl font-black text-slate-800">{latestVitals.spo2 || '-'} <span className="text-base opacity-40">%</span></div>
              </div>
              <div className={`${latestVitals.is_abnormal || latestVitals.temperature_f > 100 ? "bg-amber-50 border-amber-300 shadow-amber-200/50" : "bg-white border-amber-200/50 shadow-amber-100/50"} p-5 rounded-2xl border shadow-sm relative overflow-hidden`}>
                {(latestVitals.is_abnormal || latestVitals.temperature_f > 100) && <div className="absolute top-0 right-0 bg-amber-500 text-white text-[9px] font-bold px-2 py-1 rounded-bl-lg">ABNORMAL</div>}
                <span className="text-xs font-bold text-amber-700 uppercase flex items-center gap-1.5"><Thermometer size={14}/> Temp</span>
                <div className="mt-2 text-3xl font-black text-amber-600">{latestVitals.temperature_f || '-'} <span className="text-base opacity-40">°F</span></div>
              </div>
            </div>
            
            {/* Vitals Trend Chart Mockup tied to state counts */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
               <h3 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2"><Activity size={16} className="text-indigo-500"/> Trending Graph</h3>
               <div className="h-64 flex items-end gap-2 px-2 border-b border-l border-slate-200 pb-2 bg-slate-50/30 rounded-bl-lg">
                 {[72, 75, 78, 80, 84, 82, 85, latestVitals.heart_rate || 88].map((val, i) => (
                   <div key={i} className="flex-1 bg-slate-100 rounded-t-md relative group hover:bg-slate-200 transition overflow-hidden border border-slate-200/50 border-b-0">
                      <div className="absolute bottom-0 w-full bg-gradient-to-t from-indigo-500 to-indigo-400 rounded-t-md transition-all" style={{ height: `${val}%` }}/>
                   </div>
                 ))}
               </div>
               <div className="flex justify-between mt-2 text-[10px] font-bold text-slate-400">
                 <span>00:00</span><span>04:00</span><span>08:00</span><span>12:00</span><span>16:00</span><span>20:00</span><span>Now</span>
               </div>
            </div>
          </div>
        )}

        {/* MAR TAB */}
        {activeTab === "MAR" && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden animate-in fade-in zoom-in-95 duration-500">
            {/* The Nursing Acceptance Inbound Gateway */}
            {inboundDeliveries.length > 0 && (
              <div className="bg-amber-50 p-6 border-b border-amber-200 animate-in slide-in-from-top-4">
                 <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-black text-amber-800 uppercase tracking-widest flex items-center gap-2"><Beaker size={16}/> INBOUND PHARMACY DELIVERIES PENDING NURSING ACCEPTANCE</h3>
                    <span className="text-[10px] font-bold bg-amber-600 text-white px-2 py-0.5 rounded-full shadow-sm">{inboundDeliveries.length} Requires Sign-Off</span>
                 </div>
                 
                 <div className="grid grid-cols-2 gap-4">
                    {inboundDeliveries.map(delivery => (
                        <div key={delivery.id} className="bg-white p-4 rounded-xl shadow-sm border border-amber-200 flex flex-col justify-between">
                            <div>
                                <p className="text-xs font-bold text-slate-500 font-mono mb-1">Issue Route: {delivery.id}</p>
                                {delivery.items.map((item: any, idx: number) => (
                                   <div key={idx} className="flex justify-between items-center text-sm py-1 border-b border-slate-50 last:border-0">
                                       <span className="font-bold text-slate-700">{item.medication_name}</span>
                                       <span className="font-mono text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded text-[10px] font-bold">{item.dispensed_quantity} UNIT</span>
                                   </div>
                                ))}
                            </div>
                            <div className="mt-4 pt-3 border-t border-amber-100 flex gap-2">
                                <button onClick={() => handleNursingAcceptance(delivery.id, true)} className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-lg text-xs transition shadow-sm border border-emerald-700 text-center">Accept Package</button>
                                <button onClick={() => handleNursingAcceptance(delivery.id, false, "Not Required / Patient Discharged")} className="flex-1 bg-rose-50 text-rose-700 hover:bg-rose-100 font-bold py-2 rounded-lg text-xs transition border border-rose-200 text-center">Reject Delivery</button>
                            </div>
                        </div>
                    ))}
                 </div>
              </div>
            )}

            <div className="p-5 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-white flex justify-between items-center">
              <div>
                <h2 className="text-xl font-black text-slate-800 flex items-center gap-2"><Pill className="text-indigo-500"/> Electronic MAR</h2>
                <p className="text-sm text-slate-500 mt-1 font-medium">Scan pharmacy barcodes before marking administered to ensure 5-Rights adherence.</p>
              </div>
              <div className="flex gap-2 text-sm font-bold">
                <span className="px-3 py-1.5 bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-lg flex items-center gap-1.5"><CheckCircle size={14}/> Clear for administration</span>
              </div>
            </div>
            <table className="w-full text-left">
              <thead className="bg-slate-50/80 border-b border-slate-200">
                <tr className="text-[10px] text-slate-500 uppercase tracking-widest">
                  <th className="p-4 font-bold">Medication Formulation</th>
                  <th className="p-4 font-bold">Dose / Route</th>
                  <th className="p-4 font-bold">Frequency</th>
                  <th className="p-4 font-bold">Time Slot</th>
                  <th className="p-4 font-bold text-right">Action Gate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {marQueue.map((m, i) => (
                  <tr key={i} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-5 font-bold text-slate-800 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center"><Beaker size={14}/></div>
                      {m.medication_name || m.drug}
                    </td>
                    <td className="p-5 text-sm font-mono font-semibold text-slate-700">{m.route}</td>
                    <td className="p-5 text-sm font-medium text-slate-600 px-3 py-1 rounded bg-slate-100 w-fit">{m.frequency || m.freq}</td>
                    <td className="p-5 font-mono text-sm text-slate-600 font-bold">{m.scheduled_slot || m.slot}</td>
                    <td className="p-5 text-right">
                      {m.is_administered || m.given ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-bold border border-emerald-200 shadow-sm">
                          <CheckCircle size={14}/> Administered {m.batch_number && `(${m.batch_number})`}
                        </span>
                      ) : (
                        <button onClick={() => setShowScanModal(m)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 shadow-sm shadow-indigo-200 flex items-center gap-1.5 ml-auto transition-transform active:scale-95">
                          <Scan size={14}/> Scan & Administer
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* CLINICAL NOTES TAB */}
        {activeTab === "NOTES" && (
          <div className="grid grid-cols-3 gap-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="col-span-2 space-y-4">
              {notesData.length === 0 ? (
                <div className="text-center p-12 bg-white rounded-2xl border border-slate-200 shadow-sm text-slate-400 font-bold">No progress notes yet.</div>
              ) : notesData.map((n, i) => (
                <div key={i} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition cursor-default">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2"><Edit3 size={14} className="text-indigo-400"/> {n.title || n.note_type}</h3>
                    <span className="text-[11px] text-slate-500 font-mono bg-slate-100/80 border border-slate-200 px-2.5 py-1 rounded-md">
                      {new Date(n.recorded_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-600 text-sm leading-relaxed whitespace-pre-line bg-slate-50 p-3 rounded-xl border border-slate-100">{n.text || n.clinical_note}</p>
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                       <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center text-[10px] font-bold text-purple-700">RN</div>
                       <span className="text-xs font-bold text-slate-600">{n.user || n.nurse_uuid || "Staff"}</span>
                    </div>
                    <div className="text-[10px] font-bold text-emerald-600 flex items-center gap-1"><CheckCircle size={12}/> Digitally Signed</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="col-span-1 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm h-fit sticky top-[160px]">
              <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2 uppercase tracking-tight text-sm"><Edit3 size={16} className="text-indigo-600"/> Document New Note</h3>
              <textarea 
                value={newNote} onChange={e => setNewNote(e.target.value)}
                placeholder="Type structured shift note or observation here..."
                className="w-full text-sm p-4 bg-slate-50 border border-slate-200 rounded-xl min-h-[220px] resize-none outline-none focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-50 transition shadow-inner"
              />
              <button disabled={!newNote.trim()} onClick={handleSaveNote} className="w-full mt-4 bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 active:bg-indigo-800 disabled:bg-slate-300 disabled:text-slate-500 flex justify-center items-center gap-2 transition">
                <Save size={16}/> Sign & Save to Chart
              </button>
            </div>
          </div>
        )}

        {/* COMPLAINTS TAB */}
        {activeTab === "COMPLAINTS" && (
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm animate-in fade-in zoom-in-95 duration-300">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-black text-slate-800 flex items-center gap-2"><User className="text-indigo-500" /> Chief Complaints & History</h2>
              <button onClick={() => setShowComplaintModal(true)} className="px-4 py-2 bg-indigo-50 text-indigo-700 font-bold text-sm rounded-lg hover:bg-indigo-100 transition shadow-sm border border-indigo-200">
                + Add Complaint
              </button>
            </div>
            <div className="space-y-4">
              {complaints.map(c => (
                <div key={c.id} className="p-4 border border-slate-200 rounded-xl bg-slate-50 flex justify-between items-center">
                  <div>
                    <h4 className="font-bold text-slate-800 text-base">{c.title}</h4>
                    <p className="text-sm text-slate-600 mt-1">{c.details}</p>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs font-bold px-2 py-1 rounded ${c.clx}`}>{c.severity}</span>
                    <p className="text-xs text-slate-500 mt-2 font-mono">Duration: {c.duration}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* DIAGNOSIS TAB */}
        {activeTab === "DIAGNOSIS" && (
          <div className="grid grid-cols-3 gap-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="col-span-2 space-y-4">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2"><Stethoscope size={18} className="text-indigo-500"/> Active Diagnoses</h3>
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr className="text-xs text-slate-500 uppercase tracking-wider">
                        <th className="p-4 font-bold">Type</th>
                        <th className="p-4 font-bold">ICD-10 Code & Description</th>
                        <th className="p-4 font-bold text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {diagnoses.map(d => (
                        <tr key={d.id}>
                          <td className="p-4"><span className={`text-xs font-bold px-2 py-1 rounded ${d.clx}`}>{d.label}</span></td>
                          <td className="p-4 font-bold text-slate-800">{d.desc}</td>
                          <td className="p-4 text-right"><span className={`text-xs font-bold ${d.status === 'Active' ? 'text-emerald-600' : 'text-slate-500'} flex items-center justify-end gap-1`}>{d.status === 'Active' && <CheckCircle size={14}/>} {d.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            <div className="col-span-1 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm h-fit">
              <h3 className="font-bold text-slate-800 mb-4 text-sm">Add Diagnosis</h3>
              <input type="text" value={newDiagnosis} onChange={e => setNewDiagnosis(e.target.value)} placeholder="Search ICD-10 code..." className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-indigo-500 outline-none text-sm mb-4" />
              <button disabled={!newDiagnosis} onClick={handleLinkDiagnosis} className="w-full bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 shadow-sm transition disabled:opacity-50">
                + Link Diagnosis
              </button>
            </div>
          </div>
        )}

        {/* IO_CHART TAB */}
        {activeTab === "IO_CHART" && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden animate-in zoom-in-95 duration-500">
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
               <h2 className="text-xl font-black text-slate-800 flex items-center gap-2"><Droplets className="text-blue-500"/> Fluid Balance (I/O Chart)</h2>
               <div className="flex gap-3">
                 <button onClick={() => setShowIoModal("Intake")} className="px-4 py-2 bg-blue-50 text-blue-700 font-bold text-sm rounded-lg border border-blue-200 shadow-sm hover:bg-blue-100">+ Add Intake</button>
                 <button onClick={() => setShowIoModal("Output")} className="px-4 py-2 bg-amber-50 text-amber-700 font-bold text-sm rounded-lg border border-amber-200 shadow-sm hover:bg-amber-100">+ Add Output</button>
               </div>
            </div>
            <div className="grid grid-cols-4 bg-slate-800 text-white p-4">
              <div className="text-center border-r border-slate-700"><p className="text-xs text-slate-400 font-bold uppercase">Total Intake (24h)</p><p className="text-2xl font-black mt-1 text-blue-400">{totalIntake} <span className="text-sm">mL</span></p></div>
              <div className="text-center border-r border-slate-700"><p className="text-xs text-slate-400 font-bold uppercase">Total Output (24h)</p><p className="text-2xl font-black mt-1 text-amber-400">{totalOutput} <span className="text-sm">mL</span></p></div>
              <div className="text-center col-span-2"><p className="text-xs text-slate-400 font-bold uppercase">Net Balance</p><p className={`text-2xl font-black mt-1 ${netBalance >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{netBalance > 0 ? "+" : ""}{netBalance} <span className="text-sm">mL</span></p></div>
            </div>
            <table className="w-full text-left mt-4 border-t border-slate-200">
              <thead className="bg-slate-50 text-xs text-slate-500 uppercase tracking-widest border-b border-slate-200">
                <tr><th className="p-4 font-bold">Time</th><th className="p-4 font-bold">Type</th><th className="p-4 font-bold">Category</th><th className="p-4 font-bold text-right">Volume (mL)</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {ioRecords.map(r => (
                  <tr key={r.id}>
                    <td className="p-4 text-sm font-mono">{r.time}</td>
                    <td className="p-4"><span className={`text-xs px-2 py-1 rounded font-bold ${r.typeClx}`}>{r.type}</span></td>
                    <td className="p-4 text-sm font-bold">{r.category}</td>
                    <td className={`p-4 text-right font-mono font-bold ${r.valClx}`}>{r.value > 0 ? "+" : ""}{r.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* LAB TAB */}
        {activeTab === "LAB" && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden animate-in fade-in duration-500">
            <div className="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
               <h2 className="text-xl font-black text-slate-800 flex items-center gap-2"><TestTube className="text-purple-500"/> Laboratory & Samples</h2>
               <button onClick={handleOrderLab} className="px-4 py-2 bg-purple-600 text-white font-bold text-sm rounded-lg hover:bg-purple-700 shadow-sm flex items-center gap-2 transition active:scale-95">
                 + Order New Lab
               </button>
            </div>
            <div className="p-6 space-y-4">
              {showPdfAlert && (
                <div className="bg-emerald-50 text-emerald-800 p-3 rounded-xl border border-emerald-200 font-bold text-sm animate-in fade-in flex items-center gap-2">
                  <CheckCircle size={16}/> Initializing PDF Download module...
                </div>
              )}
               {labs.map(l => (
                 <div key={l.id} className="border border-slate-200 rounded-xl p-5 flex justify-between items-center hover:bg-slate-50 transition">
                   <div className="flex items-center gap-4">
                     <div className={`w-10 h-10 ${l.ready ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'} rounded-full flex items-center justify-center font-bold relative`}>
                       {l.ready ? <CheckCircle size={20}/> : <Clock size={20}/>}
                       {l.ready && <div className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full border-2 border-white animate-pulse"></div>}</div>
                     <div><h4 className="font-bold text-slate-800">{l.title}</h4><p className="text-xs text-slate-500 mt-1 font-mono">{l.time}</p></div>
                   </div>
                   <div className="text-right">
                     <span className={`${l.ready ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'} text-xs font-bold px-3 py-1.5 rounded-lg border`}>{l.status}</span>
                     {l.ready && <button onClick={(e) => { e.stopPropagation(); handleDownloadPDF(l.title); }} className="block mt-2 text-xs font-bold text-indigo-600 hover:underline cursor-pointer">View Report PDF</button>}
                   </div>
                 </div>
               ))}
            </div>
          </div>
        )}

        </>}
      </div>

      {/* VITALS RECORDING MODAL */}
      {showVitalsModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 bg-slate-900 border-b border-slate-800 text-white flex justify-between items-center">
               <h3 className="text-xl font-bold flex items-center gap-2"><HeartPulse className="text-rose-400"/> Record Vitals</h3>
               <button onClick={() => setShowVitalsModal(false)} className="text-slate-400 hover:text-white transition"><X size={20}/></button>
            </div>
            <div className="p-6 grid grid-cols-2 gap-5">
              <div><label className="text-xs font-bold text-slate-500 uppercase">Heart Rate (bpm)</label>
                <input type="number" value={vitalsForm.hr} onChange={e => setVitalsForm({...vitalsForm, hr: e.target.value})} className="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-indigo-500 outline-none font-bold" placeholder="e.g. 84"/>
              </div>
              <div><label className="text-xs font-bold text-slate-500 uppercase">SpO2 (%)</label>
                <input type="number" value={vitalsForm.spo2} onChange={e => setVitalsForm({...vitalsForm, spo2: e.target.value})} className="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-indigo-500 outline-none font-bold" placeholder="e.g. 98"/>
              </div>
              <div><label className="text-xs font-bold text-slate-500 uppercase">Temp (°F)</label>
                <input type="number" value={vitalsForm.temp} onChange={e => setVitalsForm({...vitalsForm, temp: e.target.value})} className="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-indigo-500 outline-none font-bold" placeholder="e.g. 98.6"/>
              </div>
              <div><label className="text-xs font-bold text-slate-500 uppercase">Resp. Rate</label>
                <input type="number" value={vitalsForm.rr} onChange={e => setVitalsForm({...vitalsForm, rr: e.target.value})} className="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-indigo-500 outline-none font-bold" placeholder="e.g. 18"/>
              </div>
              <div className="col-span-2 flex gap-4">
                <div className="flex-1"><label className="text-xs font-bold text-slate-500 uppercase">BP Systolic</label>
                  <input type="number" value={vitalsForm.bp_s} onChange={e => setVitalsForm({...vitalsForm, bp_s: e.target.value})} className="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-indigo-500 outline-none font-bold" placeholder="120"/>
                </div>
                <div className="flex-1"><label className="text-xs font-bold text-slate-500 uppercase">BP Diastolic</label>
                  <input type="number" value={vitalsForm.bp_d} onChange={e => setVitalsForm({...vitalsForm, bp_d: e.target.value})} className="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-indigo-500 outline-none font-bold" placeholder="80"/>
                </div>
              </div>
            </div>
            <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-end gap-3">
              <button onClick={() => setShowVitalsModal(false)} className="px-5 py-2.5 font-bold text-slate-500 hover:text-slate-700">Cancel</button>
              <button onClick={handleSubmitVitals} className="px-6 py-2.5 font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md">Sign & Verify</button>
            </div>
          </div>
        </div>
      )}

      {/* MAR SCAN MODAL */}
      {showScanModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
             <div className="p-8 text-center border-b border-slate-100">
                <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 border-4 border-white shadow-md">
                   <Scan size={32}/>
                </div>
                <h3 className="text-2xl font-black text-slate-800">Drug Verification</h3>
                <p className="text-slate-500 text-sm mt-2 font-medium">Please scan the pharmacy barcode for <strong className="text-indigo-600 border-b border-indigo-200">{showScanModal.medication_name || showScanModal.drug}</strong> to confirm identity.</p>
             </div>
             <div className="p-6 bg-slate-50 space-y-4">
                <div>
                   <label className="text-xs font-bold text-slate-500 uppercase block mb-2">Simulate Barcode Scan (Batch/Lot No.)</label>
                   <input type="text" autoFocus value={scanCode} onChange={e => setScanCode(e.target.value)}
                     className="w-full p-4 bg-white border-2 border-slate-200 rounded-xl font-mono text-center tracking-[0.2em] font-bold text-lg focus:border-indigo-500 shadow-inner outline-none"
                     placeholder="||||| ||| || |||"
                   />
                </div>
                <div className="flex gap-3 pt-2">
                  <button onClick={() => setShowScanModal(null)} className="flex-1 py-3 font-bold text-slate-500 bg-white border border-slate-200 rounded-xl hover:bg-slate-50">Cancel</button>
                  <button onClick={handleAdministerDrug} disabled={!scanCode} className="flex-1 py-3 font-bold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2 outline-none">
                    <CheckCircle size={18}/> Administer
                  </button>
                </div>
             </div>
          </div>
        </div>
      )}

      {/* COMPLAINTS MODAL */}
      {showComplaintModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 bg-slate-900 border-b border-slate-800 text-white flex justify-between items-center">
               <h3 className="text-xl font-bold">Add Complaint</h3>
               <button onClick={() => setShowComplaintModal(false)} className="text-slate-400 hover:text-white transition"><X size={20}/></button>
            </div>
            <div className="p-6 space-y-4">
               <div>
                 <label className="text-xs font-bold text-slate-500 uppercase">Complaint Outline</label>
                 <input type="text" value={complaintForm.title} onChange={e => setComplaintForm({...complaintForm, title: e.target.value})} className="w-full mt-1 p-3 border border-slate-200 rounded-xl outline-none focus:border-indigo-500" placeholder="e.g. Sharp chest pain"/>
               </div>
               <div>
                 <label className="text-xs font-bold text-slate-500 uppercase">Description / Details</label>
                 <textarea value={complaintForm.details} onChange={e => setComplaintForm({...complaintForm, details: e.target.value})} className="w-full mt-1 p-3 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 h-24 resize-none" placeholder="..." />
               </div>
               <button onClick={handleAddComplaint} className="w-full bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700">Add to Profile</button>
            </div>
          </div>
        </div>
      )}

      {/* I/O CHART MODAL */}
      {showIoModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 bg-slate-900 border-b border-slate-800 text-white flex justify-between items-center">
               <h3 className="text-xl font-bold flex items-center gap-2"><Droplets className={showIoModal === 'Intake' ? 'text-blue-400' : 'text-amber-400'}/> Record {showIoModal}</h3>
               <button onClick={() => setShowIoModal(null)} className="text-slate-400 hover:text-white transition"><X size={20}/></button>
            </div>
            <div className="p-6 space-y-4">
               <div>
                 <label className="text-xs font-bold text-slate-500 uppercase">Volume (mL)</label>
                 <input type="number" autoFocus value={ioForm.volume} onChange={e => setIoForm({...ioForm, volume: e.target.value})} className="w-full mt-1 p-3 border border-slate-200 rounded-xl outline-none text-xl font-black bg-slate-50 focus:border-indigo-500" placeholder="0"/>
               </div>
               <div>
                 <label className="text-xs font-bold text-slate-500 uppercase">Category</label>
                 <input type="text" value={ioForm.category} onChange={e => setIoForm({...ioForm, category: e.target.value})} className="w-full mt-1 p-3 border border-slate-200 rounded-xl outline-none focus:border-indigo-500" placeholder={showIoModal === "Intake" ? "e.g. Oral/IV Fluid" : "e.g. Urine/Drain"}/>
               </div>
               <button onClick={handleAddIo} className={`w-full text-white font-bold py-3 rounded-xl ${showIoModal === 'Intake' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-amber-500 hover:bg-amber-600'}`}>Log to Chart</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
