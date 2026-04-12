"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

export default function DevicesPage() {
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<any>({ device_class: "DIAGNOSTIC" });
  const [orgs, setOrgs] = useState<any[]>([]);

  const load = useCallback(async () => {
    try { const data = await apiFetch("/devices"); setDevices(data); } catch { setDevices([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); apiFetch("/organizations").then(setOrgs).catch(() => {}); }, [load]);

  const handleCreate = async () => {
    try {
      await apiPost("/devices", { ...form, organization_id: form.organization_id || orgs[0]?.organization_id });
      setShowModal(false); setForm({ device_class: "DIAGNOSTIC" }); load();
    } catch(e) { alert("Error: " + e); }
  };

  const classColors: Record<string,string> = { CARDIAC: "from-red-500 to-rose-600", VITAL_SIGNS: "from-green-500 to-emerald-600", DIAGNOSTIC: "from-blue-500 to-indigo-600", KIOSK: "from-amber-500 to-orange-600", IMAGING: "from-purple-500 to-violet-600" };
  const classIcons: Record<string,string> = { CARDIAC: "❤️", VITAL_SIGNS: "🩺", DIAGNOSTIC: "🔬", KIOSK: "🏧", IMAGING: "📸" };

  return (<div><TopNav title="Device Hub" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Device Hub</h2><p className="text-sm text-slate-500">{devices.length} devices registered</p></div>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ Register Device</button>
      </div>

      {loading ? <div className="flex justify-center py-16"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      devices.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-blue-50 flex items-center justify-center text-4xl">🔬</div>
          <h3 className="text-lg font-bold text-slate-700">No Devices Registered</h3>
          <p className="text-sm text-slate-500 mt-1 mb-4">Register your first medical device</p>
          <button onClick={() => setShowModal(true)} className="btn-primary">Register Device</button>
        </div>
      ) :
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {devices.map(d => (
          <div key={d.device_id} className="bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all">
            <div className={`h-2 bg-gradient-to-r ${classColors[d.device_class] || "from-slate-400 to-slate-500"}`}></div>
            <div className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="text-2xl">{classIcons[d.device_class] || "🔧"}</div>
                <div><h3 className="font-bold text-slate-800">{d.device_name}</h3><p className="text-xs text-slate-400 font-mono">{d.device_code}</p></div>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between"><span className="text-slate-400">Class:</span><span className="badge badge-info">{d.device_class}</span></div>
                <div className="flex justify-between"><span className="text-slate-400">Manufacturer:</span><span className="font-semibold">{d.manufacturer || "—"}</span></div>
                <div className="flex justify-between"><span className="text-slate-400">Integration:</span><span className="font-semibold">{d.integration_method || "—"}</span></div>
                <div className="flex justify-between"><span className="text-slate-400">Status:</span><span className="badge badge-success">{d.status || "ACTIVE"}</span></div>
                <div className="flex justify-between"><span className="text-slate-400">Registered:</span><span>{d.created_at ? new Date(d.created_at).toLocaleDateString() : "—"}</span></div>
              </div>
            </div>
          </div>
        ))}
      </div>}

      {showModal && (<div className="modal-overlay" onClick={() => setShowModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header bg-gradient-to-r from-blue-50 to-indigo-50"><h3 className="font-bold text-lg">Register Device</h3><button onClick={() => setShowModal(false)} className="text-xl">&times;</button></div>
        <div className="modal-body space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="input-label">Device Code *</label><input className="input-field" placeholder="e.g. ECG-001" value={form.device_code || ""} onChange={e => setForm({...form, device_code: e.target.value})} /></div>
            <div><label className="input-label">Device Name *</label><input className="input-field" value={form.device_name || ""} onChange={e => setForm({...form, device_name: e.target.value})} /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="input-label">Device Class *</label><select className="input-field" value={form.device_class} onChange={e => setForm({...form, device_class: e.target.value})}><option value="DIAGNOSTIC">Diagnostic</option><option value="CARDIAC">Cardiac</option><option value="VITAL_SIGNS">Vital Signs</option><option value="IMAGING">Imaging</option><option value="KIOSK">Kiosk</option></select></div>
            <div><label className="input-label">Manufacturer</label><input className="input-field" value={form.manufacturer || ""} onChange={e => setForm({...form, manufacturer: e.target.value})} /></div>
          </div>
          <div><label className="input-label">Integration Method</label><select className="input-field" value={form.integration_method || ""} onChange={e => setForm({...form, integration_method: e.target.value})}><option value="">None</option><option value="HL7v2">HL7v2</option><option value="FHIR">FHIR</option><option value="DICOM">DICOM</option><option value="REST_API">REST API</option><option value="USB">USB</option><option value="BLUETOOTH">Bluetooth</option></select></div>
        </div>
        <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button><button className="btn-primary" onClick={handleCreate}>Register</button></div>
      </div></div>)}
    </div></div>);
}
