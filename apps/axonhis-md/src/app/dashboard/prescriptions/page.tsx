"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

export default function Page() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<any>({});
  const [saving, setSaving] = useState(false);
  const [encounters, setEncounters] = useState<any[]>([]);

  const load = useCallback(async () => {
    try { 
      const data = await apiFetch("/medications"); 
      setItems(data); 
      const encs = await apiFetch("/encounters");
      setEncounters(encs);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    setSaving(true);
    try {
      await apiPost("/medications", {
        encounter_id: form.encounter_id,
        medication_name: form.medication_name,
        route: form.route,
        dose: form.dose,
        frequency: form.frequency,
        duration: form.duration
      });
      setShowModal(false);
      setForm({});
      load();
    } catch (e: any) { alert("Error: " + e.message); }
    finally { setSaving(false); }
  };

  return (<div><TopNav title="Prescriptions" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Prescriptions</h2><p className="text-sm text-slate-500">{items.length} records</p></div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Add Prescription</button>
      </div>

      {loading ? <div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      items.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-slate-50 flex items-center justify-center text-4xl">\ud83d\udc8a</div>
          <h3 className="text-lg font-bold text-slate-700">No Prescriptions</h3>
          <p className="text-sm text-slate-500 mt-1">Records will appear here once created</p>
        </div>
      ) :
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm overflow-x-auto">
        <table className="data-table min-w-full"><thead><tr><th>#</th><th>Medication</th><th>Dose</th><th>Route</th><th>Frequency</th><th>Created</th></tr></thead>
          <tbody>{items.map((item: any, i: number) => (
            <tr key={item.medication_request_id || i} className="hover:bg-teal-50/30">
              <td className="text-xs text-slate-400 font-mono">{i + 1}</td>
              <td className="font-semibold text-slate-800">{item.medication_name || "—"}</td>
              <td><span className="badge badge-neutral">{item.dose || "—"}</span></td>
              <td><span className="badge badge-neutral">{item.route || "—"}</span></td>
              <td><span className="badge badge-info">{item.frequency || "—"}</span></td>
              <td className="text-xs text-slate-500">{item.created_at ? new Date(item.created_at).toLocaleDateString() : "—"}</td>
            </tr>))}</tbody></table>
      </div>}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">New Prescription</h3>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Encounter</label>
                <select className="input-field" value={form.encounter_id || ""} onChange={e => setForm({...form, encounter_id: e.target.value})}>
                  <option value="">Select Encounter</option>
                  {encounters.map((e: any) => (
                    <option key={e.encounter_id} value={e.encounter_id}>
                      {e.patient_name || e.encounter_id.split('-')[0]} - {new Date(e.started_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Medication Name</label>
                <input type="text" className="input-field" placeholder="e.g. Amoxicillin" value={form.medication_name || ""} onChange={e => setForm({...form, medication_name: e.target.value})} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Dose</label>
                  <input type="text" className="input-field" placeholder="e.g. 500mg" value={form.dose || ""} onChange={e => setForm({...form, dose: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Route</label>
                  <select className="input-field" value={form.route || ""} onChange={e => setForm({...form, route: e.target.value})}>
                    <option value="">Select</option>
                    <option value="ORAL">Oral</option>
                    <option value="IV">IV</option>
                    <option value="TOPICAL">Topical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Frequency</label>
                  <input type="text" className="input-field" placeholder="e.g. BID" value={form.frequency || ""} onChange={e => setForm({...form, frequency: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Duration</label>
                  <input type="text" className="input-field" placeholder="e.g. 7 days" value={form.duration || ""} onChange={e => setForm({...form, duration: e.target.value})} />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={saving}>Cancel</button>
              <button type="button" className="btn-primary" onClick={handleCreate} disabled={saving || !form.medication_name || !form.encounter_id}>{saving ? "Saving..." : "Prescribe"}</button>
            </div>
          </div>
        </div>
      )}
    </div></div>);
}
