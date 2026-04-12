"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

export default function Page() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<any>({ category: "DIAGNOSTIC" });
  const [saving, setSaving] = useState(false);
  const [patients, setPatients] = useState<any[]>([]);
  const [encounters, setEncounters] = useState<any[]>([]);

  const load = useCallback(async () => {
    try {
      const data = await apiFetch("/service-requests");
      setItems(data);
      const [pts, encs] = await Promise.all([
        apiFetch("/patients"),
        apiFetch("/encounters")
      ]);
      setPatients(pts);
      setEncounters(encs);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    setSaving(true);
    try {
      await apiPost("/service-requests", {
        encounter_id: form.encounter_id,
        request_type: form.request_type || "LAB",
        category: form.category || "DIAGNOSTIC",
        catalog_name: form.catalog_name,
        catalog_code: form.catalog_code,
        priority: form.priority || "ROUTINE",
        status: "ORDERED"
      });
      setShowModal(false);
      setForm({ category: "DIAGNOSTIC" });
      load();
    } catch (e: any) { alert("Error creating order: " + e.message); }
    finally { setSaving(false); }
  };

  return (<div><TopNav title="Clinical Orders" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Clinical Orders</h2><p className="text-sm text-slate-500">{items.length} records</p></div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Add Order</button>
      </div>

      {loading ? <div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      items.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-slate-50 flex items-center justify-center text-4xl">\ud83e\uddea</div>
          <h3 className="text-lg font-bold text-slate-700">No Clinical Orders</h3>
          <p className="text-sm text-slate-500 mt-1">Records will appear here once created</p>
        </div>
      ) :
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm overflow-x-auto">
        <table className="data-table min-w-full"><thead><tr><th>#</th><th>Order Name</th><th>Type</th><th>Category</th><th>Priority</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>{items.map((item: any, i: number) => (
            <tr key={item.service_request_id || i} className="hover:bg-teal-50/30">
              <td className="text-xs text-slate-400 font-mono">{i + 1}</td>
              <td className="font-semibold text-slate-800">{item.catalog_name || "—"}</td>
              <td><span className="badge badge-info">{item.request_type || "—"}</span></td>
              <td><span className="badge badge-neutral">{item.category || "—"}</span></td>
              <td><span className="badge badge-neutral">{item.priority || "—"}</span></td>
              <td><span className={`badge ${item.status === 'ORDERED' ? 'badge-success' : 'badge-neutral'}`}>{item.status || "—"}</span></td>
              <td className="text-xs text-slate-500">{item.created_at ? new Date(item.created_at).toLocaleDateString() : "—"}</td>
            </tr>))}</tbody></table>
      </div>}
      
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">New Clinical Order</h3>
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
                <label className="block text-sm font-medium text-slate-700 mb-1">Order Name</label>
                <input type="text" className="input-field" placeholder="e.g. Complete Blood Count" value={form.catalog_name || ""} onChange={e => setForm({...form, catalog_name: e.target.value})} />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Request Type</label>
                  <select className="input-field" value={form.request_type || "LAB"} onChange={e => setForm({...form, request_type: e.target.value})}>
                    <option value="LAB">Lab Test</option>
                    <option value="IMAGING">Imaging</option>
                    <option value="PROCEDURE">Procedure</option>
                    <option value="REFERRAL">Referral</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
                  <select className="input-field" value={form.category || "DIAGNOSTIC"} onChange={e => setForm({...form, category: e.target.value})}>
                    <option value="DIAGNOSTIC">Diagnostic</option>
                    <option value="THERAPEUTIC">Therapeutic</option>
                    <option value="PREVENTIVE">Preventive</option>
                    <option value="MONITORING">Monitoring</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
                  <select className="input-field" value={form.priority || "ROUTINE"} onChange={e => setForm({...form, priority: e.target.value})}>
                    <option value="ROUTINE">Routine</option>
                    <option value="URGENT">Urgent</option>
                    <option value="STAT">STAT</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={saving}>Cancel</button>
              <button type="button" className="btn-primary" onClick={handleCreate} disabled={saving || !form.catalog_name || !form.encounter_id}>{saving ? "Saving..." : "Create Order"}</button>
            </div>
          </div>
        </div>
      )}
    </div></div>);
}
