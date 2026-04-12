"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

export default function SpecialtiesPage() {
  const [specialties, setSpecialties] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<any>({});

  const load = useCallback(async () => {
    try { const data = await apiFetch("/specialties"); setSpecialties(data); } catch { setSpecialties([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const handleCreate = async () => { try { await apiPost("/specialties", form); setShowModal(false); setForm({}); load(); } catch(e) { alert("Error: " + e); } };

  const colorMap = ["from-blue-500 to-indigo-600","from-emerald-500 to-green-600","from-violet-500 to-purple-600","from-rose-500 to-pink-600","from-amber-500 to-orange-600","from-cyan-500 to-teal-600","from-sky-500 to-blue-600","from-red-500 to-rose-600"];

  return (<div><TopNav title="Specialty Experience Packs" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Specialty Profiles</h2><p className="text-sm text-slate-500">Configure clinical experience packs per specialty</p></div>
        <button onClick={() => setShowModal(true)} className="btn-primary">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>Add Specialty</button>
      </div>

      {loading ? <div className="flex justify-center py-16"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      specialties.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-violet-50 flex items-center justify-center text-4xl">\u2b50</div>
          <h3 className="text-lg font-bold text-slate-700">No Specialties</h3>
          <p className="text-sm text-slate-500 mt-1 mb-4">Add your first specialty profile</p>
          <button onClick={() => setShowModal(true)} className="btn-primary">Add Specialty</button>
        </div>
      ) :
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {specialties.map((s, i) => (
          <div key={s.specialty_profile_id} className="bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group">
            <div className={`h-2 bg-gradient-to-r ${colorMap[i % colorMap.length]}`}></div>
            <div className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colorMap[i % colorMap.length]} flex items-center justify-center text-white font-bold`}>{s.code?.charAt(0) || "S"}</div>
                <div><h3 className="font-bold text-slate-800 text-sm group-hover:text-teal-700 transition-colors">{s.name}</h3><p className="text-[10px] font-mono text-slate-400">{s.code}</p></div>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">{s.description || "No description"}</p>
              <div className="mt-3 flex items-center gap-2"><span className={`badge ${s.active_flag !== false ? "badge-success" : "badge-error"}`}>{s.active_flag !== false ? "Active" : "Inactive"}</span></div>
            </div>
          </div>
        ))}
      </div>}

      {showModal && (<div className="modal-overlay" onClick={() => setShowModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header bg-gradient-to-r from-violet-50 to-purple-50"><h3 className="font-bold text-lg">Add Specialty</h3><button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button></div>
        <div className="modal-body space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="input-label">Code *</label><input className="input-field" placeholder="e.g. CARDIOLOGY" value={form.code || ""} onChange={e => setForm({...form, code: e.target.value})} /></div>
            <div><label className="input-label">Name *</label><input className="input-field" value={form.name || ""} onChange={e => setForm({...form, name: e.target.value})} /></div>
          </div>
          <div><label className="input-label">Description</label><textarea className="input-field" rows={3} value={form.description || ""} onChange={e => setForm({...form, description: e.target.value})} /></div>
        </div>
        <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button><button className="btn-primary" onClick={handleCreate}>Create</button></div>
      </div></div>)}
    </div></div>);
}
