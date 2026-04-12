"use client";
import { useTranslation } from "@/i18n";


import React, { useState, useEffect } from "react";
import { ClipboardList, FlaskConical, ScanLine, Pill, Wrench, Plus, RefreshCw, ChevronRight, Clock, CheckCircle2, XCircle, AlertTriangle, Activity } from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { ipdApi } from "@/lib/ipd-api";

const ORDER_TYPES = [
  { key: "Laboratory", label: "Lab Test", icon: FlaskConical, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200" },
  { key: "Radiology", label: "Imaging", icon: ScanLine, color: "text-purple-600", bg: "bg-purple-50", border: "border-purple-200" },
  { key: "Medication", label: "Medication", icon: Pill, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200" },
  { key: "Procedure", label: "Procedure", icon: Wrench, color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200" },
];

const STATUS_COLORS: Record<string, string> = {
  Ordered: "bg-blue-100 text-blue-700 border-blue-200",
  Scheduled: "bg-indigo-100 text-indigo-700 border-indigo-200",
  "In Progress": "bg-amber-100 text-amber-700 border-amber-200",
  Completed: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Cancelled: "bg-rose-100 text-rose-700 border-rose-200",
};

const PRIORITY_COLORS: Record<string, string> = {
  Routine: "bg-slate-100 text-slate-600",
  Urgent: "bg-amber-100 text-amber-700",
  STAT: "bg-rose-100 text-rose-700",
};

export default function IpdOrdersPage() {
  const { t } = useTranslation();
  const [patients, setPatients] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ordersLoading, setOrdersLoading] = useState(false);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState("Laboratory");

  // Lab form
  const [labForm, setLabForm] = useState({ test_name: "", sample_type: "Blood", clinical_indication: "", priority: "Routine" });
  // Radiology form
  const [radForm, setRadForm] = useState({ imaging_type: "X-Ray", target_area: "", clinical_indication: "", priority: "Routine" });
  // Medication form
  const [medForm, setMedForm] = useState({ medicine_name: "", dosage: "", frequency: "BID", route: "Oral", duration_days: 5, priority: "Routine" });
  // Procedure form
  const [procForm, setProcForm] = useState({ procedure_service_name: "", department: "", scheduling_notes: "", priority: "Routine" });

  useEffect(() => { fetchPatients(); }, []);
  useEffect(() => { if (selectedPatient) fetchOrders(); }, [selectedPatient]);

  const fetchPatients = async () => {
    try {
      const res: any = await ipdApi.getDoctorWorklist();
      if (Array.isArray(res)) setPatients(res);
      else if (res && Array.isArray(res.data)) setPatients(res.data);
      else setPatients([]);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchOrders = async () => {
    if (!selectedPatient) return;
    setOrdersLoading(true);
    try {
      const res: any = await ipdApi.getPatientOrders(selectedPatient.admission_number);
      const arr = Array.isArray(res) ? res : (res?.data || []);
      setOrders(arr);
    } catch (e) { console.error(e); }
    finally { setOrdersLoading(false); }
  };

  const openOrderModal = (type: string) => {
    setModalType(type);
    setShowModal(true);
  };

  const submitOrder = async () => {
    if (!selectedPatient) return;
    const adm = selectedPatient.admission_number;
    try {
      if (modalType === "Laboratory") await ipdApi.createLabOrder(adm, labForm);
      else if (modalType === "Radiology") await ipdApi.createRadiologyOrder(adm, radForm);
      else if (modalType === "Medication") await ipdApi.createMedicationOrder(adm, medForm);
      else if (modalType === "Procedure") await ipdApi.createProcedureOrder(adm, procForm);
      setShowModal(false);
      resetForms();
      fetchOrders();
    } catch (e) { console.error(e); alert("Error creating order"); }
  };

  const resetForms = () => {
    setLabForm({ test_name: "", sample_type: "Blood", clinical_indication: "", priority: "Routine" });
    setRadForm({ imaging_type: "X-Ray", target_area: "", clinical_indication: "", priority: "Routine" });
    setMedForm({ medicine_name: "", dosage: "", frequency: "BID", route: "Oral", duration_days: 5, priority: "Routine" });
    setProcForm({ procedure_service_name: "", department: "", scheduling_notes: "", priority: "Routine" });
  };

  const updateStatus = async (orderId: string, newStatus: string) => {
    try {
      await ipdApi.updateOrderStatus(orderId, { new_status: newStatus });
      fetchOrders();
    } catch (e) { console.error(e); }
  };

  const getTypeInfo = (type: string) => ORDER_TYPES.find(t => t.key === type) || ORDER_TYPES[0];

  const countByType = (type: string) => orders.filter(o => o.order_type === type).length;
  const countByStatus = (status: string) => orders.filter(o => o.status === status).length;

  return (
    <div className="min-h-screen bg-slate-50 relative">
      <TopNav title={t("ipdOrders.title")} />

      <div className="flex h-[calc(100vh-64px)] overflow-hidden">
        {/* LEFT PANEL: PATIENT LIST */}
        <div className="w-80 bg-white border-r border-slate-200 flex flex-col overflow-y-auto shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
          <div className="p-4 border-b border-slate-100 sticky top-0 bg-white/90 backdrop-blur-sm z-20">
            <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <ClipboardList size={18} className="text-indigo-600" />
              Admitted Patients
            </h2>
            <p className="text-xs text-slate-500 mt-1">{t("ipdOrders.selectPatient")}</p>
          </div>
          <div className="p-3 space-y-2">
            {loading ? (
              <div className="text-sm text-slate-500 text-center py-10 animate-pulse">Loading patients...</div>
            ) : patients.length === 0 ? (
              <div className="text-sm text-slate-400 text-center py-10">No patients found.</div>
            ) : (
              patients.map((p, i) => (
                <div key={i} onClick={() => setSelectedPatient(p)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${selectedPatient?.admission_number === p.admission_number ? 'border-indigo-400 bg-indigo-50/50 shadow-sm' : 'border-slate-100 hover:border-slate-200 hover:shadow-sm hover:bg-slate-50'}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <div className="font-bold text-slate-800 text-sm">{p.patient_uhid}</div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">{p.status || 'Active'}</span>
                  </div>
                  <div className="text-xs text-slate-500 truncate">ADM: <span className="text-slate-700 font-medium">{p.admission_number}</span></div>
                  <div className="text-xs text-slate-500 mt-1">Dr. {p.doctor_name}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* MAIN CONTENT */}
        <div className="flex-1 flex flex-col bg-slate-50/50 overflow-y-auto">
          {!selectedPatient ? (
            <div className="m-auto flex flex-col items-center text-slate-400 max-w-sm text-center">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-6 shadow-inner">
                <ClipboardList size={32} className="text-slate-300" />
              </div>
              <h2 className="text-xl font-bold text-slate-700 mb-2">Select a Patient</h2>
              <p className="text-sm leading-relaxed">Choose an admitted patient to place and manage clinical orders (Lab, Radiology, Medication, Procedures).</p>
            </div>
          ) : (
            <div className="w-full max-w-7xl mx-auto p-6 lg:p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

              {/* PATIENT HEADER */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm mb-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-indigo-500 to-purple-500"></div>
                <div className="flex justify-between items-center pl-3">
                  <div>
                    <h2 className="text-xl font-bold text-slate-800 tracking-tight">{selectedPatient.patient_uhid}</h2>
                    <div className="flex items-center gap-3 text-xs text-slate-500 mt-1 font-medium">
                      <span className="flex items-center gap-1"><Activity size={14} className="text-slate-400" /> {selectedPatient.admission_number}</span>
                      <span className="w-1 h-1 rounded-full bg-slate-300"></span>
                      <span>Dr. {selectedPatient.doctor_name}</span>
                    </div>
                  </div>
                  <button onClick={fetchOrders} className="flex items-center gap-2 px-3 py-2 text-sm font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors">
                    <RefreshCw size={14} /> Refresh
                  </button>
                </div>
              </div>

              {/* ORDER TYPE BUTTONS */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {ORDER_TYPES.map(t => (
                  <button key={t.key} onClick={() => openOrderModal(t.key)}
                    className={`flex items-center gap-3 p-4 rounded-xl border ${t.border} ${t.bg} hover:shadow-md transition-all group`}
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${t.bg} ${t.color} shadow-sm border ${t.border}`}>
                      <t.icon size={20} />
                    </div>
                    <div className="text-left">
                      <div className={`text-sm font-bold ${t.color}`}>{t.label} Order</div>
                      <div className="text-xs text-slate-500">{countByType(t.key)} placed</div>
                    </div>
                    <Plus size={16} className="ml-auto text-slate-400 group-hover:text-slate-600 transition-colors" />
                  </button>
                ))}
              </div>

              {/* STATS ROW */}
              <div className="grid grid-cols-5 gap-3 mb-6">
                {["Ordered", "Scheduled", "In Progress", "Completed", "Cancelled"].map(s => (
                  <div key={s} className={`text-center p-3 rounded-xl border ${STATUS_COLORS[s]} text-xs font-bold`}>
                    <div className="text-lg">{countByStatus(s)}</div>
                    <div>{s}</div>
                  </div>
                ))}
              </div>

              {/* ORDERS TABLE */}
              <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
                <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                  <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2"><ClipboardList size={16} className="text-slate-500" /> All Orders ({orders.length})</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 border-b border-slate-200 text-xs text-slate-500 uppercase font-bold tracking-wider">
                      <tr>
                        <th className="p-4 px-6">Type</th>
                        <th className="p-4 px-6">Date</th>
                        <th className="p-4 px-6">Priority</th>
                        <th className="p-4 px-6">Doctor</th>
                        <th className="p-4 px-6">Status</th>
                        <th className="p-4 px-6">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {ordersLoading ? (
                        <tr><td colSpan={6} className="p-8 text-center text-slate-400 animate-pulse">Loading orders...</td></tr>
                      ) : orders.length === 0 ? (
                        <tr><td colSpan={6} className="p-8 text-center text-slate-400">No orders placed yet. Use the buttons above to create orders.</td></tr>
                      ) : (
                        orders.map((o, i) => {
                          const info = getTypeInfo(o.order_type);
                          return (
                            <tr key={i} className="hover:bg-slate-50 transition-colors">
                              <td className="p-4 px-6">
                                <div className="flex items-center gap-2">
                                  <div className={`w-7 h-7 rounded-md flex items-center justify-center ${info.bg} ${info.color} border ${info.border}`}>
                                    <info.icon size={14} />
                                  </div>
                                  <span className="font-medium text-slate-800">{o.order_type}</span>
                                </div>
                              </td>
                              <td className="p-4 px-6 text-slate-500 whitespace-nowrap">{new Date(o.order_date).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td>
                              <td className="p-4 px-6">
                                <span className={`text-xs font-bold px-2 py-0.5 rounded ${PRIORITY_COLORS[o.priority] || "bg-slate-100 text-slate-600"}`}>{o.priority}</span>
                              </td>
                              <td className="p-4 px-6 text-slate-600 whitespace-nowrap">{o.doctor_name}</td>
                              <td className="p-4 px-6">
                                <span className={`text-xs font-bold px-2.5 py-1 rounded-md border ${STATUS_COLORS[o.status] || "bg-slate-100 text-slate-600 border-slate-200"}`}>{o.status}</span>
                              </td>
                              <td className="p-4 px-6 whitespace-nowrap">
                                {o.status === "Ordered" && (
                                  <div className="flex gap-1">
                                    <button onClick={() => updateStatus(o.id, "In Progress")} className="text-xs px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 font-bold transition-colors">Start</button>
                                    <button onClick={() => updateStatus(o.id, "Cancelled")} className="text-xs px-2 py-1 rounded bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100 font-bold transition-colors">Cancel</button>
                                  </div>
                                )}
                                {o.status === "In Progress" && (
                                  <button onClick={() => updateStatus(o.id, "Completed")} className="text-xs px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 font-bold transition-colors flex items-center gap-1"><CheckCircle2 size={12} /> Complete</button>
                                )}
                                {(o.status === "Completed" || o.status === "Cancelled") && (
                                  <span className="text-xs text-slate-400">—</span>
                                )}
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ORDER CREATION MODAL */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
                {(() => { const info = getTypeInfo(modalType); return <><info.icon size={18} className={info.color} /> New {info.label} Order</>; })()}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 text-xl font-bold">&times;</button>
            </div>
            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">

              {/* LAB ORDER FORM */}
              {modalType === "Laboratory" && (
                <>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Test Name</label>
                    <input type="text" value={labForm.test_name} onChange={e => setLabForm({ ...labForm, test_name: e.target.value })}
                      className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" placeholder="e.g. Complete Blood Count" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Sample Type</label>
                      <select value={labForm.sample_type} onChange={e => setLabForm({ ...labForm, sample_type: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                        <option>Blood</option><option>Urine</option><option>Serum</option><option>Sputum</option><option>CSF</option><option>Stool</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Priority</label>
                      <select value={labForm.priority} onChange={e => setLabForm({ ...labForm, priority: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                        <option>Routine</option><option>Urgent</option><option>STAT</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Clinical Indication</label>
                    <textarea value={labForm.clinical_indication} onChange={e => setLabForm({ ...labForm, clinical_indication: e.target.value })}
                      className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1 resize-y" rows={2} placeholder="Reason for test..." />
                  </div>
                </>
              )}

              {/* RADIOLOGY ORDER FORM */}
              {modalType === "Radiology" && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Imaging Type</label>
                      <select value={radForm.imaging_type} onChange={e => setRadForm({ ...radForm, imaging_type: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                        <option>X-Ray</option><option>Ultrasound</option><option>CT Scan</option><option>MRI</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Priority</label>
                      <select value={radForm.priority} onChange={e => setRadForm({ ...radForm, priority: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                        <option>Routine</option><option>Urgent</option><option>STAT</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Target Area / Body Part</label>
                    <input type="text" value={radForm.target_area} onChange={e => setRadForm({ ...radForm, target_area: e.target.value })}
                      className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" placeholder="e.g. Chest PA, Abdomen" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Clinical Indication</label>
                    <textarea value={radForm.clinical_indication} onChange={e => setRadForm({ ...radForm, clinical_indication: e.target.value })}
                      className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1 resize-y" rows={2} placeholder="Reason for imaging..." />
                  </div>
                </>
              )}

              {/* MEDICATION ORDER FORM */}
              {modalType === "Medication" && (
                <>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Medicine Name</label>
                    <input type="text" value={medForm.medicine_name} onChange={e => setMedForm({ ...medForm, medicine_name: e.target.value })}
                      className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" placeholder="e.g. Paracetamol 500mg" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Dosage</label>
                      <input type="text" value={medForm.dosage} onChange={e => setMedForm({ ...medForm, dosage: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" placeholder="e.g. 500mg" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Frequency</label>
                      <select value={medForm.frequency} onChange={e => setMedForm({ ...medForm, frequency: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                        <option>OD</option><option>BID</option><option>TID</option><option>QID</option><option>SOS</option>
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Route</label>
                      <select value={medForm.route} onChange={e => setMedForm({ ...medForm, route: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                        <option>Oral</option><option>IV</option><option>IM</option><option>SC</option><option>Topical</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Duration (days)</label>
                      <input type="number" value={medForm.duration_days} onChange={e => setMedForm({ ...medForm, duration_days: parseInt(e.target.value) || 0 })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" min="1" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Priority</label>
                      <select value={medForm.priority} onChange={e => setMedForm({ ...medForm, priority: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                        <option>Routine</option><option>Urgent</option><option>STAT</option>
                      </select>
                    </div>
                  </div>
                </>
              )}

              {/* PROCEDURE ORDER FORM */}
              {modalType === "Procedure" && (
                <>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Service / Procedure Name</label>
                    <input type="text" value={procForm.procedure_service_name} onChange={e => setProcForm({ ...procForm, procedure_service_name: e.target.value })}
                      className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" placeholder="e.g. Physiotherapy, Dialysis" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Department</label>
                      <input type="text" value={procForm.department} onChange={e => setProcForm({ ...procForm, department: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1" placeholder="e.g. Physiotherapy" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Priority</label>
                      <select value={procForm.priority} onChange={e => setProcForm({ ...procForm, priority: e.target.value })}
                        className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1">
                        <option>Routine</option><option>Urgent</option><option>STAT</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Scheduling Notes</label>
                    <textarea value={procForm.scheduling_notes} onChange={e => setProcForm({ ...procForm, scheduling_notes: e.target.value })}
                      className="w-full text-sm border border-slate-200 rounded-lg p-2.5 outline-none focus:border-indigo-500 focus:ring-1 resize-y" rows={2} placeholder="Special instructions..." />
                  </div>
                </>
              )}

              <button onClick={submitOrder}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg text-sm transition-colors mt-2 flex items-center justify-center gap-2">
                <Plus size={16} /> Place {getTypeInfo(modalType).label} Order
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
