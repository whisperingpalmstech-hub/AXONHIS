"use client";
import React, { useEffect, useState } from "react";
import { ipdApi as api } from "@/lib/ipd-api";

export default function VisitorMlcDashboard() {
  const [activeTab, setActiveTab] = useState("visitors");
  const [admissions, setAdmissions] = useState<any[]>([]);
  const [selectedAdm, setSelectedAdm] = useState("");
  const [visitors, setVisitors] = useState<any[]>([]);
  const [passes, setPasses] = useState<any[]>([]);
  const [mlcCases, setMlcCases] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [showVisitorModal, setShowVisitorModal] = useState(false);
  const [showMlcModal, setShowMlcModal] = useState(false);
  const [showPassModal, setShowPassModal] = useState(false);
  const [loading, setLoading] = useState(false);

  const [newVisitor, setNewVisitor] = useState({ visitor_name: "", relationship: "", contact_number: "", id_proof: "Aadhaar Card" });
  const [newMlc, setNewMlc] = useState({ case_type: "Road Accident", incident_details: "", police_station: "", fir_number: "", officer_name: "", officer_badge: "", registered_by: "System Admin" });

  useEffect(() => { fetchAdmissions(); fetchMlcCases(); fetchNotifications(); }, []);

  const fetchAdmissions = async () => {
    try {
      const res = await api.getBillingDashboard();
      setAdmissions(res as any || []);
    } catch (e) { console.error(e); }
  };

  const fetchMlcCases = async () => {
    try {
      const res = await api.getAllMlcCases();
      setMlcCases(res as any || []);
    } catch (e) { console.error(e); }
  };

  const fetchNotifications = async () => {
    try {
      const res = await api.getSecurityNotifications();
      setNotifications(res as any || []);
    } catch (e) { console.error(e); }
  };

  const selectAdmission = async (admNo: string) => {
    setSelectedAdm(admNo);
    try {
      const v = await api.getVisitors(admNo);
      setVisitors(v as any || []);
      const p = await api.getVisitorPasses(admNo);
      setPasses(p as any || []);
    } catch (e) { console.error(e); }
  };

  const handleRegisterVisitor = async () => {
    if (!selectedAdm || !newVisitor.visitor_name) return alert("Select admission & fill visitor name");
    const adm = admissions.find((a: any) => a.admission_number === selectedAdm);
    try {
      await api.registerVisitor({ ...newVisitor, admission_number: selectedAdm, patient_uhid: adm?.patient_uhid || "" });
      setNewVisitor({ visitor_name: "", relationship: "", contact_number: "", id_proof: "Aadhaar Card" });
      await selectAdmission(selectedAdm);
      setShowVisitorModal(false);
    } catch (e) { alert("Error registering visitor"); }
  };

  const handleGeneratePass = async (visitorId: string) => {
    try {
      await api.generateVisitorPass({ visitor_id: visitorId, admission_number: selectedAdm, ward_name: "IPD Ward", pass_type: "Standard" });
      await selectAdmission(selectedAdm);
    } catch (e) { alert("Error generating pass"); }
  };

  const handleRegisterMlc = async () => {
    if (!selectedAdm) return alert("Select an admission first");
    const adm = admissions.find((a: any) => a.admission_number === selectedAdm);
    try {
      await api.registerMlcCase({ ...newMlc, admission_number: selectedAdm, patient_uhid: adm?.patient_uhid || "" });
      setNewMlc({ case_type: "Road Accident", incident_details: "", police_station: "", fir_number: "", officer_name: "", officer_badge: "", registered_by: "System Admin" });
      setShowMlcModal(false);
      fetchMlcCases();
      fetchNotifications();
    } catch (e) { alert("Error registering MLC case"); }
  };

  const handleMarkRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      fetchNotifications();
    } catch (e) { console.error(e); }
  };

  const tabs = [
    { id: "visitors", label: "👥 Visitor Management", color: "bg-blue-600" },
    { id: "mlc", label: "⚖️ Medico-Legal Cases", color: "bg-red-600" },
    { id: "security", label: "🔔 Security Alerts", color: "bg-amber-600" },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Visitor Management & MLC Engine</h1>
          <p className="text-gray-500 text-sm mt-1">Manage visitor access, medico-legal cases, and security notifications</p>
        </div>
        <div className="flex items-center gap-3">
          {notifications.filter((n: any) => !n.is_read).length > 0 && (
            <span className="bg-red-500 text-white text-xs px-2.5 py-1 rounded-full animate-pulse font-bold">
              {notifications.filter((n: any) => !n.is_read).length} Alerts
            </span>
          )}
          <button onClick={() => { fetchAdmissions(); fetchMlcCases(); fetchNotifications(); }} className="bg-white border px-4 py-2 rounded-lg text-sm hover:bg-gray-50 shadow-sm">⟳ Refresh</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${activeTab === t.id ? `${t.color} text-white shadow-lg` : 'text-gray-600 hover:text-gray-900 hover:bg-white'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab: Visitor Management */}
      {activeTab === "visitors" && (
        <div className="grid grid-cols-3 gap-6">
          {/* Left: Admission Selection */}
          <div className="col-span-1 bg-white rounded-xl border shadow-sm p-5">
            <h3 className="font-semibold text-sm mb-3 text-gray-700 uppercase tracking-wide">Active Admissions</h3>
            <div className="space-y-2 max-h-[60vh] overflow-y-auto">
              {admissions.map((a: any) => (
                <button key={a.admission_number} onClick={() => selectAdmission(a.admission_number)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${selectedAdm === a.admission_number ? 'border-blue-500 bg-blue-50 shadow-sm' : 'border-gray-100 hover:border-gray-300 hover:bg-gray-50'}`}>
                  <div className="font-semibold text-sm">{a.patient_name}</div>
                  <div className="text-xs text-gray-500">{a.admission_number}</div>
                </button>
              ))}
              {admissions.length === 0 && <p className="text-sm text-gray-400 italic">No active admissions</p>}
            </div>
          </div>

          {/* Right: Visitor Details */}
          <div className="col-span-2 space-y-5">
            {selectedAdm ? (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-lg">Visitors for {selectedAdm}</h3>
                  <button onClick={() => setShowVisitorModal(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 shadow-sm">+ Register Visitor</button>
                </div>

                {/* Registered Visitors Table */}
                <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left px-4 py-3 font-medium text-gray-600">Visitor Name</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-600">Relationship</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-600">Contact</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-600">ID Proof</th>
                        <th className="text-left px-4 py-3 font-medium text-gray-600">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visitors.map((v: any) => (
                        <tr key={v.id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="px-4 py-3 font-semibold">{v.visitor_name}</td>
                          <td className="px-4 py-3">{v.relationship}</td>
                          <td className="px-4 py-3">{v.contact_number}</td>
                          <td className="px-4 py-3"><span className="bg-gray-100 text-xs px-2 py-0.5 rounded">{v.id_proof}</span></td>
                          <td className="px-4 py-3">
                            <button onClick={() => handleGeneratePass(v.id)} className="bg-green-50 text-green-700 text-xs px-3 py-1.5 rounded-lg hover:bg-green-100 font-medium">Generate Pass</button>
                          </td>
                        </tr>
                      ))}
                      {visitors.length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 italic">No visitors registered yet</td></tr>}
                    </tbody>
                  </table>
                </div>

                {/* Active Passes */}
                <div className="bg-white rounded-xl border shadow-sm p-5">
                  <h4 className="font-semibold mb-3 text-gray-700">Active Visitor Passes</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {passes.map((p: any) => (
                      <div key={p.id} className="border rounded-lg p-4 bg-gradient-to-br from-blue-50 to-indigo-50 relative overflow-hidden">
                        <div className="absolute top-2 right-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${p.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{p.status}</span>
                        </div>
                        <div className="text-lg font-black text-blue-800 font-mono">{p.pass_number}</div>
                        <div className="text-xs text-gray-600 mt-1">Ward: {p.ward_name} | Type: {p.pass_type}</div>
                        <div className="text-xs text-gray-500 mt-1">Date: {p.visit_date}</div>
                      </div>
                    ))}
                    {passes.length === 0 && <p className="text-sm text-gray-400 italic col-span-2">No passes generated</p>}
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-xl border shadow-sm p-16 text-center">
                <div className="text-5xl mb-4">👈</div>
                <p className="text-gray-500">Select an admission from the left panel to manage visitors</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: MLC Cases */}
      {activeTab === "mlc" && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-lg">Medico-Legal Cases Registry</h3>
            <button onClick={() => setShowMlcModal(true)} className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700 shadow-sm">+ Register MLC Case</button>
          </div>

          <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-red-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-red-800">Admission No</th>
                  <th className="text-left px-4 py-3 font-medium text-red-800">Patient UHID</th>
                  <th className="text-left px-4 py-3 font-medium text-red-800">Case Type</th>
                  <th className="text-left px-4 py-3 font-medium text-red-800">FIR No.</th>
                  <th className="text-left px-4 py-3 font-medium text-red-800">Police Station</th>
                  <th className="text-left px-4 py-3 font-medium text-red-800">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-red-800">Registered</th>
                </tr>
              </thead>
              <tbody>
                {mlcCases.map((m: any) => (
                  <tr key={m.id} className="border-b border-gray-50 hover:bg-red-50/30">
                    <td className="px-4 py-3 font-mono text-xs">{m.admission_number}</td>
                    <td className="px-4 py-3">{m.patient_uhid}</td>
                    <td className="px-4 py-3">
                      <span className="bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded-full font-semibold">{m.case_type}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{m.fir_number || '-'}</td>
                    <td className="px-4 py-3">{m.police_station || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${m.status === 'Active' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'}`}>{m.status}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{new Date(m.registered_at).toLocaleString()}</td>
                  </tr>
                ))}
                {mlcCases.length === 0 && <tr><td colSpan={7} className="px-4 py-12 text-center text-gray-400 italic">No MLC cases registered</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Security Notifications */}
      {activeTab === "security" && (
        <div className="space-y-4">
          <h3 className="font-bold text-lg">Security & Compliance Alerts</h3>
          {notifications.length === 0 && <div className="bg-white rounded-xl border p-12 text-center text-gray-400 italic">No security notifications</div>}
          {notifications.map((n: any) => (
            <div key={n.id} className={`rounded-xl border p-5 flex items-start gap-4 transition-all ${n.is_read ? 'bg-white border-gray-200' : 'bg-amber-50 border-amber-300 shadow-md'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-lg ${n.notification_type === 'MLC Alert' ? 'bg-red-100' : 'bg-amber-100'}`}>
                {n.notification_type === 'MLC Alert' ? '⚠️' : '🔔'}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">{n.notification_type}</span>
                  {!n.is_read && <span className="bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold">NEW</span>}
                </div>
                <p className="text-sm text-gray-800 mt-1">{n.message}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-400">{new Date(n.created_at).toLocaleString()}</span>
                  {!n.is_read && (
                    <button onClick={() => handleMarkRead(n.id)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">Mark as Read</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Register Visitor */}
      {showVisitorModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" onClick={() => setShowVisitorModal(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-4">Register New Visitor</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">Visitor Name *</label>
                <input className="w-full border rounded-lg p-2.5 text-sm" value={newVisitor.visitor_name} onChange={e => setNewVisitor({...newVisitor, visitor_name: e.target.value})}/>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Relationship</label>
                  <select className="w-full border rounded-lg p-2.5 text-sm" value={newVisitor.relationship} onChange={e => setNewVisitor({...newVisitor, relationship: e.target.value})}>
                    <option value="">Select</option>
                    <option>Father</option><option>Mother</option><option>Brother</option><option>Sister</option>
                    <option>Spouse</option><option>Son</option><option>Daughter</option><option>Friend</option><option>Other</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Contact Number</label>
                  <input className="w-full border rounded-lg p-2.5 text-sm" value={newVisitor.contact_number} onChange={e => setNewVisitor({...newVisitor, contact_number: e.target.value})}/>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">ID Proof</label>
                <select className="w-full border rounded-lg p-2.5 text-sm" value={newVisitor.id_proof} onChange={e => setNewVisitor({...newVisitor, id_proof: e.target.value})}>
                  <option>Aadhaar Card</option><option>Driving License</option><option>Passport</option><option>Voter ID</option><option>PAN Card</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowVisitorModal(false)} className="flex-1 border py-2.5 rounded-lg text-sm hover:bg-gray-50">Cancel</button>
              <button onClick={handleRegisterVisitor} className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg text-sm hover:bg-blue-700 font-medium shadow-sm">Register Visitor</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Register MLC Case */}
      {showMlcModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" onClick={() => setShowMlcModal(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-1 text-red-700">⚖️ Register Medico-Legal Case</h3>
            <p className="text-xs text-gray-500 mb-4">This will flag the admission and send a security alert.</p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">Admission Number *</label>
                <select className="w-full border rounded-lg p-2.5 text-sm" value={selectedAdm} onChange={e => setSelectedAdm(e.target.value)}>
                  <option value="">Select Admission</option>
                  {admissions.map((a: any) => <option key={a.admission_number} value={a.admission_number}>{a.admission_number} — {a.patient_name}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Case Type *</label>
                  <select className="w-full border rounded-lg p-2.5 text-sm" value={newMlc.case_type} onChange={e => setNewMlc({...newMlc, case_type: e.target.value})}>
                    <option>Road Accident</option><option>Assault</option><option>Burn Injury</option><option>Poisoning</option><option>Animal Bite</option><option>Drowning</option><option>Unnatural Death</option><option>Other</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">FIR Number</label>
                  <input className="w-full border rounded-lg p-2.5 text-sm" placeholder="FIR-XXXX-YYYY" value={newMlc.fir_number} onChange={e => setNewMlc({...newMlc, fir_number: e.target.value})}/>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">Incident Details</label>
                <textarea className="w-full border rounded-lg p-2.5 text-sm" rows={2} value={newMlc.incident_details} onChange={e => setNewMlc({...newMlc, incident_details: e.target.value})}/>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Police Station</label>
                  <input className="w-full border rounded-lg p-2.5 text-sm" value={newMlc.police_station} onChange={e => setNewMlc({...newMlc, police_station: e.target.value})}/>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Officer Name</label>
                  <input className="w-full border rounded-lg p-2.5 text-sm" value={newMlc.officer_name} onChange={e => setNewMlc({...newMlc, officer_name: e.target.value})}/>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">Officer Badge Number</label>
                <input className="w-full border rounded-lg p-2.5 text-sm" value={newMlc.officer_badge} onChange={e => setNewMlc({...newMlc, officer_badge: e.target.value})}/>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowMlcModal(false)} className="flex-1 border py-2.5 rounded-lg text-sm hover:bg-gray-50">Cancel</button>
              <button onClick={handleRegisterMlc} className="flex-1 bg-red-600 text-white py-2.5 rounded-lg text-sm hover:bg-red-700 font-medium shadow-sm">Register MLC Case</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
