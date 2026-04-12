"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { apiFetch, apiPost, apiPut, apiDelete } from "@/lib/api";

export default function PatientsPage() {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [form, setForm] = useState<any>({});
  const [selected, setSelected] = useState<any>(null);
  const [orgs, setOrgs] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<any>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try { const data = await apiFetch("/patients"); setPatients(data); } catch { setPatients([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    load();
    apiFetch("/organizations").then(setOrgs).catch(() => {});
  }, [load]);

  const handleCreate = async () => {
    setSaving(true);
    try {
      await apiPost("/patients", {
        organization_id: form.organization_id || orgs[0]?.organization_id,
        display_name: form.display_name,
        mrn: form.mrn || undefined,
        first_name: form.first_name || undefined,
        last_name: form.last_name || undefined,
        dob: form.dob || undefined,
        sex: form.sex || undefined,
        mobile_number: form.mobile_number || undefined,
        email: form.email || undefined,
      });
      setShowModal(false); setForm({}); load();
    } catch(e: any) { alert("Error creating patient: " + e.message); }
    finally { setSaving(false); }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await apiDelete(`/patients/${deleteTarget.patient_id}`);
      setDeleteTarget(null);
      load();
    } catch(e: any) { alert("Error deleting: " + e.message); }
    finally { setDeleting(false); }
  };

  const handleEdit = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await apiPut(`/patients/${selected.patient_id}`, {
        display_name: form.display_name,
        first_name: form.first_name || null,
        last_name: form.last_name || null,
        dob: form.dob || null,
        sex: form.sex || null,
        mobile_number: form.mobile_number || null,
        email: form.email || null,
      });
      setEditModal(false); setForm({}); setSelected(null); load();
    } catch(e: any) { alert("Error updating: " + e.message); }
    finally { setSaving(false); }
  };

  const openEdit = (p: any) => {
    setSelected(p);
    setForm({
      display_name: p.display_name || "",
      first_name: p.first_name || "",
      last_name: p.last_name || "",
      dob: p.dob || "",
      sex: p.sex || "",
      mobile_number: p.mobile_number || "",
      email: p.email || "",
    });
    setEditModal(true);
  };

  const filtered = patients.filter(p => !search ||
    p.display_name?.toLowerCase().includes(search.toLowerCase()) ||
    p.mrn?.toLowerCase().includes(search.toLowerCase()));

  const genderIcon = (sex: string) => {
    if (sex === "MALE") return (<span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-50 text-blue-600 text-xs font-semibold"><svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="10" cy="14" r="5"/><path d="M19 5l-5.4 5.4M19 5h-5M19 5v5"/></svg>Male</span>);
    if (sex === "FEMALE") return (<span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-pink-50 text-pink-600 text-xs font-semibold"><svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="8" r="5"/><path d="M12 13v8M9 18h6"/></svg>Female</span>);
    return <span className="text-xs text-slate-400">—</span>;
  };

  return (<div><TopNav title="Patient Management" subtitle="Registration, identifiers & consent profiles" />
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">Patient Registry</h2>
          <p className="text-sm text-slate-500 mt-0.5">{patients.length} patients registered across all organizations</p>
        </div>
        <button onClick={() => { setForm({ organization_id: orgs[0]?.organization_id }); setShowModal(true); }} className="btn-primary">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>
          Register Patient
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>
        <input className="w-full pl-11 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-400 transition-all" placeholder="Search by name or MRN..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <div className="spinner"></div>
          <p className="text-sm text-slate-400">Loading patients...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">👥</div>
          <h3>No Patients Found</h3>
          <p>{search ? "Try a different search term" : "Register your first patient to get started"}</p>
          {!search && <button onClick={() => setShowModal(true)} className="btn-primary">Register First Patient</button>}
        </div>
      ) : (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-12">#</th>
              <th>MRN</th>
              <th>Patient</th>
              <th>Date of Birth</th>
              <th>Gender</th>
              <th>Contact</th>
              <th>Email</th>
              <th>Status</th>
              <th className="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p, i) => (
              <tr key={p.patient_id} className="group">
                <td className="text-xs text-slate-400 font-mono">{i + 1}</td>
                <td>
                  <span className="inline-block px-2.5 py-1 bg-slate-100 text-slate-700 font-mono text-xs rounded-lg font-semibold">
                    {p.mrn || "—"}
                  </span>
                </td>
                <td>
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                      {p.display_name?.charAt(0)?.toUpperCase() || "?"}
                    </div>
                    <div>
                      <div className="font-semibold text-slate-800 text-sm">{p.display_name}</div>
                      {(p.first_name || p.last_name) && (
                        <div className="text-[11px] text-slate-400">{[p.first_name, p.last_name].filter(Boolean).join(" ")}</div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="text-sm text-slate-600">{p.dob ? new Date(p.dob + "T00:00:00").toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : <span className="text-slate-300">—</span>}</td>
                <td>{genderIcon(p.sex)}</td>
                <td className="text-sm text-slate-600">{p.mobile_number || <span className="text-slate-300">—</span>}</td>
                <td className="text-xs text-slate-500">{p.email || <span className="text-slate-300">—</span>}</td>
                <td><span className="badge badge-dot badge-success">Active</span></td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                    <button
                      type="button"
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); openEdit(p); }}
                      style={{ width: 32, height: 32, display: "inline-flex", alignItems: "center", justifyContent: "center", borderRadius: 8, border: "1px solid #e2e8f0", background: "white", cursor: "pointer", fontSize: 14 }}
                      title="Edit patient"
                    >✏️</button>
                    <button
                      type="button"
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); setDeleteTarget(p); }}
                      style={{ width: 32, height: 32, display: "inline-flex", alignItems: "center", justifyContent: "center", borderRadius: 8, border: "1px solid #fca5a5", background: "#fef2f2", cursor: "pointer", fontSize: 14 }}
                      title="Delete patient"
                    >🗑️</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      )}

      {/* Create Modal */}
      {showModal && (<div className="modal-overlay" onClick={() => setShowModal(false)}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center text-white text-lg">👤</div>
              <div><h3 className="font-bold text-lg">Register New Patient</h3><p className="text-xs text-slate-400">All fields marked * are required</p></div>
            </div>
            <button onClick={() => setShowModal(false)}>&times;</button>
          </div>
          <div className="modal-body space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">Display Name *</label><input className="input-field" placeholder="Full display name" value={form.display_name || ""} onChange={e => setForm({...form, display_name: e.target.value})} /></div>
              <div><label className="input-label">MRN (Auto-generated if empty)</label><input className="input-field" placeholder="e.g. MRN-001" value={form.mrn || ""} onChange={e => setForm({...form, mrn: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">First Name</label><input className="input-field" value={form.first_name || ""} onChange={e => setForm({...form, first_name: e.target.value})} /></div>
              <div><label className="input-label">Last Name</label><input className="input-field" value={form.last_name || ""} onChange={e => setForm({...form, last_name: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div><label className="input-label">Date of Birth</label><input type="date" className="input-field" value={form.dob || ""} onChange={e => setForm({...form, dob: e.target.value})} /></div>
              <div><label className="input-label">Gender</label>
                <select className="input-field" value={form.sex || ""} onChange={e => setForm({...form, sex: e.target.value})}>
                  <option value="">Select gender</option><option value="MALE">Male</option><option value="FEMALE">Female</option><option value="OTHER">Other</option>
                </select>
              </div>
              <div><label className="input-label">Phone</label><input className="input-field" placeholder="+971..." value={form.mobile_number || ""} onChange={e => setForm({...form, mobile_number: e.target.value})} /></div>
            </div>
            <div><label className="input-label">Email Address</label><input type="email" className="input-field" placeholder="patient@email.com" value={form.email || ""} onChange={e => setForm({...form, email: e.target.value})} /></div>
          </div>
          <div className="modal-footer">
            <button className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn-primary" onClick={handleCreate} disabled={saving || !form.display_name}>
              {saving ? "Registering..." : "Register Patient"}
            </button>
          </div>
        </div>
      </div>)}

      {/* Edit Modal */}
      {editModal && (<div className="modal-overlay" onClick={() => setEditModal(false)}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">{selected?.display_name?.charAt(0)}</div>
              <div><h3 className="font-bold text-lg">Edit Patient</h3><p className="text-xs text-slate-400">MRN: {selected?.mrn}</p></div>
            </div>
            <button onClick={() => setEditModal(false)}>&times;</button>
          </div>
          <div className="modal-body space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">Display Name *</label><input className="input-field" value={form.display_name || ""} onChange={e => setForm({...form, display_name: e.target.value})} /></div>
              <div><label className="input-label">MRN</label><input className="input-field bg-slate-50 cursor-not-allowed" value={selected?.mrn || ""} disabled /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">First Name</label><input className="input-field" value={form.first_name || ""} onChange={e => setForm({...form, first_name: e.target.value})} /></div>
              <div><label className="input-label">Last Name</label><input className="input-field" value={form.last_name || ""} onChange={e => setForm({...form, last_name: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div><label className="input-label">Date of Birth</label><input type="date" className="input-field" value={form.dob || ""} onChange={e => setForm({...form, dob: e.target.value})} /></div>
              <div><label className="input-label">Gender</label>
                <select className="input-field" value={form.sex || ""} onChange={e => setForm({...form, sex: e.target.value})}>
                  <option value="">Select</option><option value="MALE">Male</option><option value="FEMALE">Female</option><option value="OTHER">Other</option>
                </select>
              </div>
              <div><label className="input-label">Phone</label><input className="input-field" value={form.mobile_number || ""} onChange={e => setForm({...form, mobile_number: e.target.value})} /></div>
            </div>
            <div><label className="input-label">Email Address</label><input type="email" className="input-field" value={form.email || ""} onChange={e => setForm({...form, email: e.target.value})} /></div>
          </div>
          <div className="modal-footer">
            <button className="btn-secondary" onClick={() => setEditModal(false)}>Cancel</button>
            <button className="btn-primary" onClick={handleEdit} disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </div>)}
      {/* Delete Confirmation Modal */}
      {deleteTarget && (<div className="modal-overlay" onClick={() => setDeleteTarget(null)}>
        <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
          <div style={{ padding: 24, textAlign: "center" }}>
            <div style={{ width: 56, height: 56, borderRadius: "50%", background: "#fef2f2", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px", fontSize: 28 }}>⚠️</div>
            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Delete Patient?</h3>
            <p style={{ fontSize: 14, color: "#64748b", marginBottom: 24 }}>Are you sure you want to delete <strong>{deleteTarget.display_name}</strong>? This action cannot be undone and will remove all associated records.</p>
            <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
              <button type="button" className="btn-secondary" onClick={() => setDeleteTarget(null)} disabled={deleting}>Cancel</button>
              <button type="button" onClick={confirmDelete} disabled={deleting} style={{ padding: "10px 24px", borderRadius: 10, border: "none", background: "#ef4444", color: "white", fontWeight: 600, cursor: "pointer", fontSize: 14 }}>
                {deleting ? "Deleting..." : "Yes, Delete"}
              </button>
            </div>
          </div>
        </div>
      </div>)}
    </div>
  </div>);
}
