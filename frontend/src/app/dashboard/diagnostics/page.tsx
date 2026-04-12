"use client";
import { useTranslation } from "@/i18n";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/ui/TopNav";
import {
  Activity, CheckCircle2, Clock, Search, Plus, BarChart3, 
  FileText, ShieldCheck, Printer, FileSignature, Loader2, X, AlertTriangle, ArrowRight
} from "lucide-react";
import { WorkflowPipeline } from "@/components/ui/WorkflowPipeline";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

const WORKFLOW_STATES: Record<string, { badge: string; label: string }> = {
  PENDING_ACCEPTANCE: { badge: "badge-warning", label: "Pending Acceptance" },
  IN_PROGRESS: { badge: "badge-info", label: "In Progress" },
  PROVISIONALLY_RELEASED: { badge: "badge-warning", label: "Provisionally Released" },
  VALIDATED: { badge: "badge-success", label: "Validated" },
  FINALIZED: { badge: "badge-success", label: "Finalized" },
  AMENDED: { badge: "badge-error", label: "Amended" },
};

type TabKey = "dashboard" | "workbench" | "validation" | "handover";

export default function DiagnosticsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<any>(null);
  const [records, setRecords] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Modals
  const [showResultEntryModal, setShowResultEntryModal] = useState<any>(null);
  const [showValidationModal, setShowValidationModal] = useState<any>(null);
  const [showPrintModal, setShowPrintModal] = useState<any>(null);
  
  // Forms
  const [resultForm, setResultForm] = useState({ findings_richtext: "", impression: "", structured_data: {} });
  const [validationForm, setValidationForm] = useState({ action: "APPROVED", comments: "", modified_findings: "", modified_impression: "" });
  const [handoverForm, setHandoverForm] = useState({ delivery_method: "PRINT_WITH_HEADER", recipient: "" });

  const currentUser = typeof window !== "undefined" ? localStorage.getItem("user_id") || "tech-123" : "tech-123";

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const headers = authHeaders();
      const [metricRes, recordRes] = await Promise.all([
        fetch(`${API}/api/v1/diagnostics/dashboard/metrics`, { headers }),
        fetch(`${API}/api/v1/diagnostics/workbench`, { headers }),
      ]);
      if (metricRes.ok) setMetrics(await metricRes.json());
      if (recordRes.ok) setRecords(await recordRes.json());
    } catch (e) { console.error("Failed to load diagnostic data:", e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAccept = async (id: string) => {
    try {
      const res = await fetch(`${API}/api/v1/diagnostics/workbench/${id}/accept?technician_id=${currentUser}`, {
        method: "POST", headers: authHeaders()
      });
      if (res.ok) {
         loadData();
      } else {
         const err = await res.json();
         alert(err.detail || "Failed to accept procedure");
      }
    } catch (e: any) { alert(e.message || "Network error while accepting procedure"); }
  };

  const handleSubmitResult = async () => {
    try {
      const wbId = showResultEntryModal.id;
      // enter result
      const res = await fetch(`${API}/api/v1/diagnostics/workbench/${wbId}/results`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify({
          technician_id: currentUser,
          structured_data: resultForm.structured_data,
          findings_richtext: resultForm.findings_richtext,
          impression: resultForm.impression
        })
      });
      if (!res.ok) {
         const err = await res.json();
         throw new Error(err.detail || "Failed to save results");
      }

      // auto provisional release
      const provRes = await fetch(`${API}/api/v1/diagnostics/workbench/${wbId}/provisional-release`, {
        method: "POST", headers: authHeaders()
      });
      if (!provRes.ok) {
          const err = await provRes.json();
          throw new Error(err.detail || "Failed to provisionally release");
      }

      setShowResultEntryModal(null);
      setResultForm({ findings_richtext: "", impression: "", structured_data: {} });
      loadData();
    } catch (e: any) { alert(e.message); }
  };

  const handleValidate = async () => {
    try {
      const wbId = showValidationModal.id;
      const res = await fetch(`${API}/api/v1/diagnostics/workbench/${wbId}/validate`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify({
          doctor_id: currentUser,
          action: validationForm.action,
          comments: validationForm.comments,
          modified_findings: validationForm.modified_findings || undefined,
          modified_impression: validationForm.modified_impression || undefined
        })
      });
      if (!res.ok) {
         const err = await res.json();
         throw new Error(err.detail || "Validation failed");
      }
      setShowValidationModal(null);
      loadData();
    } catch (e: any) { alert(e.message); }
  };

  const handleHandover = async (wbId: string) => {
    try {
      const res = await fetch(`${API}/api/v1/diagnostics/workbench/${wbId}/handover`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify({
          delivery_method: handoverForm.delivery_method,
          recipient: handoverForm.recipient,
          handled_by: currentUser
        })
      });
      if (res.ok) {
        if (handoverForm.delivery_method.includes('PRINT')) {
           // We find the record to pass it to the print modal
           const recordToPrint = records.find(r => r.id === wbId);
           setShowPrintModal(recordToPrint);
        } else {
           alert("Report Emailed Directly via Portal!");
        }
        loadData();
      } else {
        const err = await res.json();
        alert(err.detail || "Failed Handover");
      }
    } catch (e: any) { alert(e.message || "Network error during handover"); }
  };

  const filteredRecords = records.filter((r: any) => {
    const term = searchTerm.toLowerCase();
    return !searchTerm || r.order.uhid?.toLowerCase().includes(term) || r.order.template_id?.toLowerCase().includes(term);
  });

  const listPending = filteredRecords.filter(r => ["PENDING_ACCEPTANCE", "IN_PROGRESS"].includes(r.workflow_state));
  const listValidation = filteredRecords.filter(r => ["PROVISIONALLY_RELEASED"].includes(r.workflow_state));
  const listFinalized = filteredRecords.filter(r => ["FINALIZED", "VALIDATED"].includes(r.workflow_state));

  const TABS: { key: TabKey; label: string; icon: any; count?: number }[] = [
    { key: "dashboard", label: "Dashboard", icon: BarChart3 },
    { key: "workbench", label: "Workbench", icon: Activity, count: listPending.length },
    { key: "validation", label: "Validation", icon: ShieldCheck, count: listValidation.length },
    { key: "handover", label: "Report Handover", icon: Printer, count: listFinalized.length },
  ];

  return (
    <div>
      <TopNav title="Diagnostic Procedures Module" />

      <div className="p-6 space-y-6">
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key}
                onClick={() => { setActiveTab(tab.key); setSearchTerm(""); }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
                  isActive ? "bg-white text-[var(--accent-primary)] shadow-sm border border-[var(--border)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-slate-50"
                }`}>
                <Icon size={16} />
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span className={`text-[10px] font-bold rounded-full px-1.5 py-0.5 min-w-[18px] text-center ${
                    tab.key === "validation" ? "bg-red-100 text-red-700" : "bg-slate-200 text-slate-600"
                  }`}>{tab.count}</span>
                )}
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 size={28} className="animate-spin text-[var(--accent-primary)]" />
          </div>
        ) : (
          <>
            {activeTab === "dashboard" && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="card card-body !p-4 border-l-4 border-yellow-500">
                  <Activity size={24} className="text-yellow-600 mb-2" />
                  <p className="text-2xl font-bold">{metrics?.pending_procedures || 0}</p>
                  <p className="text-xs text-slate-500 uppercase font-semibold">Pending Acceptance</p>
                </div>
                <div className="card card-body !p-4 border-l-4 border-blue-500">
                  <Clock size={24} className="text-blue-600 mb-2" />
                  <p className="text-2xl font-bold">{metrics?.procedures_in_progress || 0}</p>
                  <p className="text-xs text-slate-500 uppercase font-semibold">In Progress</p>
                </div>
                <div className="card card-body !p-4 border-l-4 border-red-500">
                  <ShieldCheck size={24} className="text-red-600 mb-2" />
                  <p className="text-2xl font-bold">{metrics?.awaiting_validation || 0}</p>
                  <p className="text-xs text-slate-500 uppercase font-semibold">Awaiting Validation</p>
                </div>
                <div className="card card-body !p-4 border-l-4 border-green-500">
                  <CheckCircle2 size={24} className="text-green-600 mb-2" />
                  <p className="text-2xl font-bold">{metrics?.completed_reports || 0}</p>
                  <p className="text-xs text-slate-500 uppercase font-semibold">Completed Reports</p>
                </div>
              </div>
            )}

            {activeTab === "workbench" && (
              <div className="space-y-4">
                <div className="relative max-w-sm">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input placeholder="Search by UHID..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="input-field pl-9" />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {listPending.map(r => (
                    <div key={r.id} className="card card-body !p-5">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-lg">{r.order.template_id}</span>
                            <span className={WORKFLOW_STATES[r.workflow_state]?.badge || "badge-neutral"}>{WORKFLOW_STATES[r.workflow_state]?.label}</span>
                          </div>
                          <p className="text-sm text-slate-600 font-medium">UHID: {r.order.uhid} | Enc: {r.order.encounter_type}</p>
                          <p className="text-xs bg-slate-100 px-2 py-1 rounded inline-block mt-1">Priority: {r.order.priority}</p>
                        </div>
                      </div>
                      
                      <div className="flex gap-2 w-full mt-4">
                        {r.workflow_state === "PENDING_ACCEPTANCE" && (
                          <button onClick={() => handleAccept(r.id)} className="btn-primary flex-1 btn-sm">Accept Procedure</button>
                        )}
                        {r.workflow_state === "IN_PROGRESS" && (
                          <button onClick={() => setShowResultEntryModal(r)} className="btn bg-violet-600 text-white hover:bg-violet-700 flex-1 btn-sm">Enter Results</button>
                        )}
                      </div>
                    </div>
                  ))}
                  {listPending.length === 0 && <p className="text-slate-500">No pending workbench records.</p>}
                </div>
              </div>
            )}

            {activeTab === "validation" && (
              <div className="space-y-4">
                 <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {listValidation.map(r => (
                    <div key={r.id} className="card card-body !p-5 border-l-4 border-red-400">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-lg">{r.order.template_id}</span>
                            <span className="badge-warning">Awaiting Validation</span>
                          </div>
                          <p className="text-sm text-slate-600 font-medium">UHID: {r.order.uhid} | Tech: {r.assigned_technician_id}</p>
                        </div>
                        <FileSignature size={32} className="text-slate-300" />
                      </div>
                      <button onClick={() => setShowValidationModal(r)} className="btn-primary w-full mt-2">Review & Sign</button>
                    </div>
                  ))}
                  {listValidation.length === 0 && <p className="text-slate-500">All reports validated.</p>}
                 </div>
              </div>
            )}

            {activeTab === "handover" && (
              <div className="space-y-4">
                 <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {listFinalized.map(r => (
                    <div key={r.id} className="card card-body !p-5 border-l-4 border-green-500">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-lg">{r.order.template_id}</span>
                            <span className="badge-success">Finalized & Signed</span>
                          </div>
                          <p className="text-sm text-slate-600 font-medium">UHID: {r.order.uhid} | Dr: {r.assigned_doctor_id}</p>
                        </div>
                        <Printer size={32} className="text-slate-300" />
                      </div>
                      <div className="flex gap-2">
                        <select className="input-field !text-sm flex-1" value={handoverForm.delivery_method} onChange={e => setHandoverForm(p => ({...p, delivery_method: e.target.value}))}>
                          <option value="PRINT_WITH_HEADER">Print (Letterhead)</option>
                          <option value="PRINT_WITHOUT_HEADER">Print (Blank)</option>
                          <option value="EMAIL">Email via Portal</option>
                        </select>
                        <button onClick={() => handleHandover(r.id)} className="btn-primary flex-1">Issue Handover</button>
                      </div>
                    </div>
                  ))}
                  {listFinalized.length === 0 && <p className="text-slate-500">No finalized reports awaiting handover.</p>}
                 </div>
              </div>
            )}
          </>
        )}
      </div>

      {showResultEntryModal && (
        <div className="modal-overlay">
          <div className="modal-content max-w-3xl">
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2">
                <FileText size={18} className="text-violet-600" /> Result Entry Workbench - {showResultEntryModal.order.template_id}
              </h3>
              <button onClick={() => setShowResultEntryModal(null)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4 h-[60vh] overflow-y-auto">
                <p className="text-sm bg-slate-100 p-2 rounded text-slate-700">Entering diagnostic findings and measurement data for Patient UHID: <b>{showResultEntryModal.order.uhid}</b></p>
                
                <div>
                  <label className="input-label">Detailed Findings (Rich Text Area)</label>
                  <textarea className="input-field h-40" placeholder="Type examination findings here..." value={resultForm.findings_richtext} onChange={e => setResultForm(p=>({...p, findings_richtext: e.target.value}))}></textarea>
                </div>

                <div>
                  <label className="input-label">Impression / Conclusion</label>
                  <textarea className="input-field h-20" placeholder="Type provisional impression here..." value={resultForm.impression} onChange={e => setResultForm(p=>({...p, impression: e.target.value}))}></textarea>
                </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowResultEntryModal(null)} className="btn-secondary">Cancel</button>
              <button onClick={handleSubmitResult} className="btn bg-violet-600 text-white hover:bg-violet-700">Submit for Doctor Review</button>
            </div>
          </div>
        </div>
      )}

      {showValidationModal && (
        <div className="modal-overlay">
          <div className="modal-content max-w-3xl">
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2">
                <FileSignature size={18} className="text-red-600" /> Doctor Result Validation - {showValidationModal.order.template_id}
              </h3>
              <button onClick={() => setShowValidationModal(null)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4 h-[60vh] overflow-y-auto">
                <div className="bg-slate-50 p-3 rounded border text-sm text-slate-600">
                  <p><b>Technician Notes:</b> Submitted for Review.</p>
                </div>
                
                <div>
                  <label className="input-label">Amend Findings (Optional)</label>
                  <textarea className="input-field h-40" placeholder="Edit the findings..." value={validationForm.modified_findings} onChange={e => setValidationForm(p=>({...p, modified_findings: e.target.value}))}></textarea>
                </div>

                <div>
                  <label className="input-label">Amend Impression (Optional)</label>
                  <textarea className="input-field h-20" placeholder="Edit the impression..." value={validationForm.modified_impression} onChange={e => setValidationForm(p=>({...p, modified_impression: e.target.value}))}></textarea>
                </div>

                <div>
                  <label className="input-label">Action</label>
                  <select className="input-field" value={validationForm.action} onChange={e => setValidationForm(p=>({...p, action: e.target.value}))}>
                    <option value="APPROVED">Approve & Digitally Sign Report</option>
                    <option value="REJECTED_FOR_REDO">Reject (Send back to technician)</option>
                  </select>
                </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowValidationModal(null)} className="btn-secondary">Cancel</button>
              <button onClick={handleValidate} className="btn-primary flex items-center gap-2"><CheckCircle2 size={16}/> Finalize Validation</button>
            </div>
          </div>
        </div>
      )}

      {showPrintModal && (
        <div className="modal-overlay">
          <div className="modal-content max-w-4xl bg-slate-200 p-8">
            <div className="flex justify-between items-center mb-4">
               <h3 className="font-semibold text-slate-800">Print Preview Manager</h3>
               <div className="flex gap-2">
                 <button onClick={() => { window.print(); setShowPrintModal(null); }} className="btn-primary flex items-center gap-2"><Printer size={16}/> Print Now</button>
                 <button onClick={() => setShowPrintModal(null)} className="btn-ghost p-1 rounded bg-white"><X size={18} /></button>
               </div>
            </div>
            {/* Simulated A4 Paper */}
            <div className="bg-white w-full shadow-lg mx-auto p-12 min-h-[600px] text-slate-800 print-area relative">
               {handoverForm.delivery_method === "PRINT_WITH_HEADER" && (
                  <div className="border-b-2 border-slate-800 pb-4 mb-6 flex justify-between items-end">
                    <div>
                      <h1 className="text-2xl font-bold text-violet-800">AXONHIS Medical Hub</h1>
                      <p className="text-sm">Department of Diagnostics</p>
                    </div>
                    <div className="text-right text-xs text-slate-500">
                      <p>123 Clinical Way, San Francisco, CA</p>
                      <p>Tel: +1-800-AXON-HIS</p>
                    </div>
                 </div>
               )}
               
               <div className="flex justify-between mb-8 text-sm">
                   <div>
                      <p><b>Patient UHID:</b> {showPrintModal.order?.uhid}</p>
                      <p><b>Encounter:</b> {showPrintModal.order?.encounter_type}</p>
                      <p><b>Procedure:</b> {showPrintModal.order?.template_id}</p>
                   </div>
                   <div className="text-right">
                      <p><b>Report Date:</b> {new Date().toLocaleDateString()}</p>
                      <p><b>Status:</b> FINALIZED</p>
                   </div>
               </div>

               <div className="mb-12">
                   <h2 className="text-lg font-bold border-b pb-2 mb-4">Clinical Findings</h2>
                   <p className="text-sm whitespace-pre-wrap">{showPrintModal.validation?.modified_findings || showPrintModal.result_entry?.findings_richtext || "Findings as captured by technician..."}</p>
               </div>

               <div className="mb-12">
                   <h2 className="text-lg font-bold border-b pb-2 mb-4">Final Impression</h2>
                   <p className="text-sm whitespace-pre-wrap font-semibold">{showPrintModal.validation?.modified_impression || showPrintModal.result_entry?.impression || "Normal diagnostic study..."}</p>
               </div>

               <div className="absolute bottom-12 right-12 text-center">
                   <div className="border-t border-slate-400 w-48 mx-auto pt-2 mt-24">
                      <p className="font-bold text-sm">Validating Physician</p>
                      <p className="text-xs text-slate-500">Electronically Signed</p>
                      <p className="text-[10px] text-slate-400 mt-1">Hash: {showPrintModal.id.split("-")[1]}-DIGITAL</p>
                   </div>
               </div>
            </div>
            
            <style jsx>{`
              @media print {
                body * {
                  visibility: hidden;
                }
                .print-area, .print-area * {
                  visibility: visible;
                }
                .print-area {
                  position: absolute;
                  left: 0;
                  top: 0;
                  width: 100%;
                  box-shadow: none;
                  margin: 0;
                  padding: 20px;
                }
              }
            `}</style>
          </div>
        </div>
      )}

    </div>
  );
}
