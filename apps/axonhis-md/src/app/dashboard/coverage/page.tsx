"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

export default function Page() {
  const [payers, setPayers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [form, setForm] = useState<any>({ payer_type: "COMMERCIAL", status: "ACTIVE" });
  const [linkForm, setLinkForm] = useState<any>({});
  const [patients, setPatients] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [payerData, patientData] = await Promise.all([
        apiFetch("/payers"),
        apiFetch("/patients")
      ]);
      setPayers(payerData);
      setPatients(patientData);
    } catch { setPayers([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const handleCreatePayer = async () => {
    if (!form.payer_name || form.payer_name.trim() === "") {
      alert("Insurance Name is required");
      return;
    }
    setSaving(true);
    try {
      await apiPost("/payers", {
        organization_id: "11111111-1111-1111-1111-111111111111",
        payer_name: form.payer_name,
        payer_type: form.payer_type || "COMMERCIAL",
        payer_code: form.code || "",
      });
      setShowModal(false);
      setForm({ payer_type: "COMMERCIAL", status: "ACTIVE" });
      load();
    } catch (e: any) { alert("Error creating insurance: " + e.message); }
    finally { setSaving(false); }
  };

  const handleLinkPatient = async () => {
    setSaving(true);
    try {
      await apiPost("/coverage", {
        patient_id: linkForm.patient_id,
        payer_id: linkForm.payer_id,
        policy_number: linkForm.policy_number,
        member_reference: linkForm.group_number,
        effective_from: linkForm.coverage_start_date,
        effective_to: linkForm.coverage_end_date,
      });
      setShowLinkModal(false);
      setLinkForm({});
      alert("Patient linked to insurance successfully!");
    } catch (e: any) { alert("Error linking patient: " + e.message); }
    finally { setSaving(false); }
  };

  return (<div><TopNav title="Insurance & Coverage" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Insurance & Coverage</h2><p className="text-sm text-slate-500">{payers.length} insurance providers</p></div>
        <div className="flex gap-2">
          <button className="btn-primary" onClick={() => setShowModal(true)}>+ Add Insurance</button>
          <button className="btn-secondary" onClick={() => setShowLinkModal(true)}>+ Link Patient</button>
        </div>
      </div>

      {loading ? <div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      payers.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-slate-50 flex items-center justify-center text-4xl">\ud83d\udee1\ufe0f</div>
          <h3 className="text-lg font-bold text-slate-700">No Insurance Providers</h3>
          <p className="text-sm text-slate-500 mt-1">Add insurance providers to get started</p>
        </div>
      ) :
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm overflow-x-auto">
        <table className="data-table min-w-full"><thead><tr><th>#</th><th>Insurance Name</th><th>Code</th><th>Type</th><th>Status</th></tr></thead>
          <tbody>{payers.map((item: any, i: number) => (
            <tr key={item.payer_id || i} className="hover:bg-teal-50/30">
              <td className="text-xs text-slate-400 font-mono">{i + 1}</td>
              <td className="font-semibold text-slate-800">{item.payer_name || "—"}</td>
              <td className="text-sm text-slate-600 font-mono">{item.payer_code || "—"}</td>
              <td><span className="badge badge-info">{item.payer_type || "—"}</span></td>
              <td><span className={`badge ${item.active_flag ? "badge-success" : "badge-neutral"}`}>{item.active_flag ? "Active" : "Inactive"}</span></td>
            </tr>))}</tbody></table>
      </div>}

      {/* Add Insurance Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add New Insurance Provider</h3>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Insurance Name *</label>
                <input type="text" className="input-field" value={form.payer_name || ""} onChange={e => setForm({...form, payer_name: e.target.value})} placeholder="e.g. Blue Cross" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Type</label>
                  <select className="input-field" value={form.payer_type || "COMMERCIAL"} onChange={e => setForm({...form, payer_type: e.target.value})}>
                    <option value="COMMERCIAL">Commercial</option>
                    <option value="GOVERNMENT">Government</option>
                    <option value="SELF_PAY">Self Pay</option>
                    <option value="MIXED">Mixed</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Code</label>
                  <input type="text" className="input-field" value={form.code || ""} onChange={e => setForm({...form, code: e.target.value})} placeholder="e.g. BC001" />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={saving}>Cancel</button>
              <button type="button" className="btn-primary" onClick={handleCreatePayer} disabled={saving}>{saving ? "Saving..." : "Add Insurance"}</button>
            </div>
          </div>
        </div>
      )}

      {/* Link Patient Modal */}
      {showLinkModal && (
        <div className="modal-overlay" onClick={() => setShowLinkModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Link Patient to Insurance</h3>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Patient</label>
                <select className="input-field" value={linkForm.patient_id || ""} onChange={e => setLinkForm({...linkForm, patient_id: e.target.value})}>
                  <option value="">Select Patient</option>
                  {patients.map((p: any) => (
                    <option key={p.patient_id} value={p.patient_id}>{p.full_name || p.first_name + " " + p.last_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Insurance Provider</label>
                <select className="input-field" value={linkForm.payer_id || ""} onChange={e => setLinkForm({...linkForm, payer_id: e.target.value})}>
                  <option value="">Select Insurance</option>
                  {payers.map((p: any) => (
                    <option key={p.payer_id} value={p.payer_id}>{p.payer_name || p.display_name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Policy Number</label>
                  <input type="text" className="input-field" value={linkForm.policy_number || ""} onChange={e => setLinkForm({...linkForm, policy_number: e.target.value})} placeholder="e.g. POL-12345" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Group Number</label>
                  <input type="text" className="input-field" value={linkForm.group_number || ""} onChange={e => setLinkForm({...linkForm, group_number: e.target.value})} placeholder="e.g. GRP-67890" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Coverage Start</label>
                  <input type="date" className="input-field" value={linkForm.coverage_start_date || ""} onChange={e => setLinkForm({...linkForm, coverage_start_date: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Coverage End</label>
                  <input type="date" className="input-field" value={linkForm.coverage_end_date || ""} onChange={e => setLinkForm({...linkForm, coverage_end_date: e.target.value})} />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowLinkModal(false)} disabled={saving}>Cancel</button>
              <button type="button" className="btn-primary" onClick={handleLinkPatient} disabled={saving || !linkForm.patient_id || !linkForm.payer_id}>{saving ? "Linking..." : "Link Patient"}</button>
            </div>
          </div>
        </div>
      )}
    </div></div>);
}
