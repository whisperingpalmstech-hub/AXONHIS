"use client";

import React, { useEffect, useState, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  ClipboardList, AlertTriangle, Users, Heart, Shield,
  CheckCircle2, Clock, User, Star, FileText, Bell,
  Activity, Bed, Stethoscope, ChevronDown, X
} from "lucide-react";
import { ipdApi } from "@/lib/ipd-api";
import { useTranslation } from "@/i18n";

type NursingTab = "WORKLIST" | "COVERSHEETS" | "NOTES";

const PRIORITY_CONFIG: Record<string, { color: string; bg: string; border: string; icon: React.ReactNode }> = {
  Critical: { color: "text-red-700", bg: "bg-red-50", border: "border-red-200", icon: <AlertTriangle size={14} className="text-red-600"/> },
  VIP: { color: "text-blue-700", bg: "bg-blue-50", border: "border-blue-200", icon: <Star size={14} className="text-blue-600"/> },
  Review: { color: "text-amber-700", bg: "bg-amber-50", border: "border-amber-200", icon: <Clock size={14} className="text-amber-600"/> },
  Normal: { color: "text-slate-600", bg: "bg-slate-50", border: "border-slate-200", icon: <User size={14} className="text-slate-500"/> },
};

export default function NursingIPDDashboard() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<NursingTab>("WORKLIST");
  const [worklist, setWorklist] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Accept Patient Modal
  const [showAcceptModal, setShowAcceptModal] = useState<any>(null);
  const [acceptPriority, setAcceptPriority] = useState("Normal");

  // Nursing Notes Modal
  const [showNotesModal, setShowNotesModal] = useState<string | null>(null);
  const [noteType, setNoteType] = useState("Initial Assessment");
  const [noteText, setNoteText] = useState("");

  // Care Assignment Modal
  const [showAssignModal, setShowAssignModal] = useState<string | null>(null);
  const [assignData, setAssignData] = useState({
    primary_nurse_name: "",
    shift_nurse_name: "",
    ward_supervisor_name: "",
  });

  // Accepted patients (coversheets)
  const [coversheets, setCoversheets] = useState<any[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const wl = await ipdApi.getNursingWorklist();
      setWorklist(wl);
    } catch (e) {
      console.error("Nursing data fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleAcceptPatient = async () => {
    if (!showAcceptModal) return;
    try {
      const result = await ipdApi.acceptPatient({
        admission_number: showAcceptModal.admission_number,
        priority_status: acceptPriority,
      });
      setCoversheets(prev => [...prev, result]);
      setShowAcceptModal(null);
      setAcceptPriority("Normal");
      fetchData(); // Refresh worklist
    } catch (e) {
      console.error("Accept patient error:", e);
    }
  };

  const handleAddNote = async () => {
    if (!showNotesModal || !noteText.trim()) return;
    try {
      await ipdApi.addNursingNote(showNotesModal, {
        note_type: noteType,
        clinical_note: noteText,
      });
      setShowNotesModal(null);
      setNoteText("");
      setNoteType("Initial Assessment");
    } catch (e) {
      console.error("Add note error:", e);
    }
  };

  const handleAssignCare = async () => {
    if (!showAssignModal) return;
    try {
      await ipdApi.assignNursingCare(showAssignModal, assignData);
      setShowAssignModal(null);
      setAssignData({ primary_nurse_name: "", shift_nurse_name: "", ward_supervisor_name: "" });
    } catch (e) {
      console.error("Assign care error:", e);
    }
  };

  const pendingCount = worklist.filter(w => w.status === "Pending Acceptance").length;
  const acceptedCount = worklist.filter(w => w.status === "Accepted").length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50/30 to-slate-100">
      <TopNav title="Nursing IPD" />
      <div className="max-w-[1520px] mx-auto px-8 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-slate-800 flex items-center gap-3">
              <div className="bg-gradient-to-br from-purple-600 to-indigo-700 text-white p-2.5 rounded-xl shadow-lg shadow-purple-200">
                <Stethoscope size={24}/>
              </div>
              {t('nursingIpd.title') || 'Nursing Coversheet & Ward Acceptance'}
            </h1>
            <p className="text-slate-500 font-medium mt-1">{t('nursingIpd.subtitle') || 'IPD Patient Acceptance, Coversheets & Nursing Documentation'}</p>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-slate-500 font-bold text-xs uppercase mb-1 flex items-center gap-2">
              <ClipboardList size={14}/> {t('nursingIpd.totalWorklist') || 'Total Worklist'}
            </div>
            <div className="text-3xl font-black text-slate-800">{worklist.length}</div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-amber-200 shadow-sm">
            <div className="text-amber-600 font-bold text-xs uppercase mb-1 flex items-center gap-2">
              <Clock size={14}/> Pending Acceptance
            </div>
            <div className="text-3xl font-black text-amber-600">{pendingCount}</div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-emerald-200 shadow-sm">
            <div className="text-emerald-600 font-bold text-xs uppercase mb-1 flex items-center gap-2">
              <CheckCircle2 size={14}/> {t('nursingIpd.accepted') || 'Accepted'}
            </div>
            <div className="text-3xl font-black text-emerald-600">{acceptedCount}</div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-red-200 shadow-sm">
            <div className="text-red-600 font-bold text-xs uppercase mb-1 flex items-center gap-2">
              <AlertTriangle size={14}/> Critical
            </div>
            <div className="text-3xl font-black text-red-600">
              {coversheets.filter(c => c.priority_status === "Critical").length}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 p-1.5 bg-white/50 backdrop-blur border border-slate-200 rounded-2xl w-fit mb-8 shadow-sm">
          {[
            { id: "WORKLIST", label: t('nursingIpd.tabWorklist') || 'Admission Worklist', icon: <ClipboardList size={16}/> },
            { id: "COVERSHEETS", label: t('nursingIpd.tabCoversheets') || 'Accepted Patients', icon: <FileText size={16}/> },
            { id: "NOTES", label: t('nursingIpd.tabNotes') || 'Nursing Notes', icon: <Heart size={16}/> },
          ].map(tObj => (
            <button key={tObj.id} onClick={() => setActiveTab(tObj.id as NursingTab)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
                activeTab === tObj.id ? "bg-white text-purple-700 shadow-sm border border-slate-200/50" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100/50"
              }`}>
              {tObj.icon} {tObj.label}
              {tObj.id === "WORKLIST" && pendingCount > 0 && (
                <span className="bg-amber-100 text-amber-600 text-[10px] px-1.5 py-0.5 rounded-full ml-1">{pendingCount}</span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-400 font-medium">Loading nursing worklist...</div>
        ) : (
          <div className="space-y-6">

            {/* WORKLIST TAB */}
            {activeTab === "WORKLIST" && (
              <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                      <th className="p-4 font-bold">{t('nursingIpd.colAdmNo') || 'Admission No'}</th>
                      <th className="p-4 font-bold">{t('nursingIpd.colUHID') || 'Patient UHID'}</th>
                      <th className="p-4 font-bold">{t('nursingIpd.colBed') || 'Bed / Ward'}</th>
                      <th className="p-4 font-bold">{t('nursingIpd.colAdmittingDoctor') || 'Admitting Doctor'}</th>
                      <th className="p-4 font-bold">{t('nursingIpd.colTime') || 'Admission Time'}</th>
                      <th className="p-4 font-bold">{t('nursingIpd.colStatus') || 'Status'}</th>
                      <th className="p-4 font-bold text-right">{t('nursingIpd.colActions') || 'Actions'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {worklist.length === 0 ? (
                      <tr><td colSpan={7} className="p-8 text-center text-slate-400 font-medium">No patients awaiting nursing acceptance</td></tr>
                    ) : (
                      worklist.map(w => (
                        <tr key={w.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="p-4 font-mono text-sm font-bold text-slate-700">{w.admission_number}</td>
                          <td className="p-4 text-sm font-mono text-slate-600">{w.patient_uhid}</td>
                          <td className="p-4 text-sm font-medium text-slate-600">
                            <span className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-md text-xs font-bold">
                              {w.bed_number || "—"}
                            </span>
                            <span className="ml-1 text-xs text-slate-400">{w.ward_name}</span>
                          </td>
                          <td className="p-4 text-sm font-medium text-slate-600">{w.admitting_doctor || "—"}</td>
                          <td className="p-4 text-sm text-slate-500">{new Date(w.admission_time).toLocaleString()}</td>
                          <td className="p-4">
                            {w.status === "Pending Acceptance" ? (
                              <span className="bg-amber-50 text-amber-700 border border-amber-200 text-xs font-bold px-2.5 py-1 rounded-lg inline-flex items-center gap-1">
                                <Clock size={12}/> Pending
                              </span>
                            ) : (
                              <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold px-2.5 py-1 rounded-lg inline-flex items-center gap-1">
                                <CheckCircle2 size={12}/> Accepted
                              </span>
                            )}
                          </td>
                          <td className="p-4 text-right">
                            {w.status === "Pending Acceptance" ? (
                              <button onClick={() => setShowAcceptModal(w)}
                                className="text-xs font-bold bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors shadow-sm shadow-purple-200 inline-flex items-center gap-1.5">
                                <CheckCircle2 size={14}/> Accept Patient
                              </button>
                            ) : (
                              <div className="flex justify-end gap-2">
                                <button onClick={() => setShowNotesModal(w.admission_number)}
                                  className="text-xs font-bold bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-100 transition-colors">
                                  + Note
                                </button>
                                <button onClick={() => setShowAssignModal(w.admission_number)}
                                  className="text-xs font-bold bg-teal-50 text-teal-700 px-3 py-1.5 rounded-lg hover:bg-teal-100 transition-colors">
                                  Assign
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* COVERSHEETS TAB */}
            {activeTab === "COVERSHEETS" && (
              <div className="space-y-4">
                {coversheets.length === 0 ? (
                  <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400 font-medium">
                    No patients accepted yet. Accept patients from the Worklist tab.
                  </div>
                ) : (
                  coversheets.map(cs => {
                    const prio = PRIORITY_CONFIG[cs.priority_status] || PRIORITY_CONFIG.Normal;
                    return (
                      <div key={cs.id} className={`bg-white border ${prio.border} rounded-2xl shadow-sm p-6`}>
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-3 mb-2">
                              <span className="font-mono text-sm font-bold text-slate-800">{cs.admission_number}</span>
                              <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold ${prio.bg} ${prio.color} ${prio.border} border`}>
                                {prio.icon} {cs.priority_status}
                              </span>
                            </div>
                            <div className="grid grid-cols-3 gap-x-8 gap-y-1 text-sm">
                              <div><span className="text-slate-400">UHID:</span> <span className="font-mono font-bold text-slate-700">{cs.patient_uhid}</span></div>
                              <div><span className="text-slate-400">Doctor:</span> <span className="font-medium text-slate-700">{cs.treating_doctor_name || "—"}</span></div>
                              <div><span className="text-slate-400">Accepted By:</span> <span className="font-medium text-slate-700">{cs.accepted_by_nurse_name || "—"}</span></div>
                              <div><span className="text-slate-400">Accepted:</span> <span className="text-slate-600">{cs.acceptance_time ? new Date(cs.acceptance_time).toLocaleString() : "—"}</span></div>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => setShowNotesModal(cs.admission_number)}
                              className="text-xs font-bold bg-indigo-50 text-indigo-700 px-3 py-2 rounded-lg hover:bg-indigo-100 transition-colors">
                              + Nursing Note
                            </button>
                            <button onClick={() => setShowAssignModal(cs.admission_number)}
                              className="text-xs font-bold bg-teal-50 text-teal-700 px-3 py-2 rounded-lg hover:bg-teal-100 transition-colors">
                              Assign Care
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* NOTES TAB - Placeholder */}
            {activeTab === "NOTES" && (
              <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center">
                <Heart size={48} className="text-purple-200 mx-auto mb-4"/>
                <h3 className="text-lg font-bold text-slate-700 mb-1">Nursing Notes Timeline</h3>
                <p className="text-sm text-slate-400">Add clinical notes to accepted patients from the Worklist or Coversheets tab.</p>
              </div>
            )}

          </div>
        )}
      </div>

      {/* ACCEPT PATIENT MODAL */}
      {showAcceptModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2">
                <Shield size={20} className="text-purple-600"/> Accept Patient to Ward
              </h3>
              <button onClick={() => setShowAcceptModal(null)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-400">Admission No:</span><span className="font-mono font-bold">{showAcceptModal.admission_number}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Patient UHID:</span><span className="font-mono font-bold">{showAcceptModal.patient_uhid}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Bed:</span><span className="font-bold">{showAcceptModal.bed_number || "—"}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Doctor:</span><span className="font-bold">{showAcceptModal.admitting_doctor || "—"}</span></div>
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-2">Patient Priority Status</label>
              <div className="grid grid-cols-4 gap-2">
                {(["Normal", "Review", "VIP", "Critical"] as const).map(p => {
                  const cfg = PRIORITY_CONFIG[p];
                  return (
                    <button key={p} onClick={() => setAcceptPriority(p)}
                      className={`flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all text-xs font-bold ${
                        acceptPriority === p
                          ? `${cfg.bg} ${cfg.color} ${cfg.border} shadow-sm`
                          : "border-slate-200 text-slate-400 hover:border-slate-300"
                      }`}>
                      {cfg.icon}
                      {p}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowAcceptModal(null)} className="px-4 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg transition-colors">Cancel</button>
              <button onClick={handleAcceptPatient}
                className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-sm font-bold transition-colors shadow-sm shadow-purple-200">
                Confirm Acceptance
              </button>
            </div>
          </div>
        </div>
      )}

      {/* NURSING NOTES MODAL */}
      {showNotesModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2">
                <FileText size={20} className="text-indigo-600"/> Add Nursing Note
              </h3>
              <button onClick={() => setShowNotesModal(null)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Admission</label>
              <div className="bg-slate-50 px-3 py-2 rounded-lg border border-slate-200 text-sm font-mono font-bold text-slate-700">{showNotesModal}</div>
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Note Type</label>
              <select value={noteType} onChange={e => setNoteType(e.target.value)}
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:border-indigo-500">
                <option>Initial Assessment</option>
                <option>Shift Handover</option>
                <option>Progress Note</option>
                <option>Special Instructions</option>
                <option>Observation</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Clinical Note</label>
              <textarea value={noteText} onChange={e => setNoteText(e.target.value)}
                rows={4} placeholder="e.g. Patient arrived conscious and stable. Complains of abdominal pain..."
                className="w-full p-3 border border-slate-300 rounded-lg text-sm outline-none focus:border-indigo-500 resize-none"/>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowNotesModal(null)} className="px-4 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg transition-colors">Cancel</button>
              <button onClick={handleAddNote} disabled={!noteText.trim()}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-bold transition-colors">
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CARE ASSIGNMENT MODAL */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2">
                <Users size={20} className="text-teal-600"/> Assign Nursing Care
              </h3>
              <button onClick={() => setShowAssignModal(null)} className="text-slate-400 hover:text-slate-600"><X size={18}/></button>
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Admission</label>
              <div className="bg-slate-50 px-3 py-2 rounded-lg border border-slate-200 text-sm font-mono font-bold text-slate-700">{showAssignModal}</div>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Primary Nurse</label>
                <input value={assignData.primary_nurse_name} onChange={e => setAssignData({...assignData, primary_nurse_name: e.target.value})}
                  placeholder="e.g. Nurse Priya Sharma" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:border-teal-500"/>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Shift Nurse</label>
                <input value={assignData.shift_nurse_name} onChange={e => setAssignData({...assignData, shift_nurse_name: e.target.value})}
                  placeholder="e.g. Nurse Ritu Verma" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:border-teal-500"/>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Ward Supervisor</label>
                <input value={assignData.ward_supervisor_name} onChange={e => setAssignData({...assignData, ward_supervisor_name: e.target.value})}
                  placeholder="e.g. Sr. Nurse Kapoor" className="w-full p-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:border-teal-500"/>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowAssignModal(null)} className="px-4 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg transition-colors">Cancel</button>
              <button onClick={handleAssignCare}
                className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-sm font-bold transition-colors">
                Assign Staff
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
