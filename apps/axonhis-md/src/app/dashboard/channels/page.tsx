"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

export default function ChannelsPage() {
  const [channels, setChannels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<any>({ channel_type: "CLINIC" });
  const [orgs, setOrgs] = useState<any[]>([]);

  const load = useCallback(async () => {
    try { const data = await apiFetch("/channels"); setChannels(data); } catch { setChannels([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); apiFetch("/organizations").then(setOrgs).catch(() => {}); }, [load]);

  const handleCreate = async () => {
    try {
      await apiPost("/channels", { ...form, organization_id: form.organization_id || orgs[0]?.organization_id });
      setShowModal(false); setForm({ channel_type: "CLINIC" }); load();
    } catch(e) { alert("Error: " + e); }
  };

  const typeColors: Record<string,string> = { CLINIC: "from-blue-500 to-indigo-600", TELECONSULT: "from-green-500 to-emerald-600", HEALTH_ATM: "from-amber-500 to-orange-600", HYBRID: "from-purple-500 to-violet-600" };

  return (<div><TopNav title="Care Channels" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Care Channels</h2><p className="text-sm text-slate-500">{channels.length} channels configured</p></div>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ Add Channel</button>
      </div>

      {loading ? <div className="flex justify-center py-16"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {channels.map(c => (
          <div key={c.channel_id} className="bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-lg transition-all">
            <div className={`h-2 bg-gradient-to-r ${typeColors[c.channel_type] || "from-slate-400 to-slate-500"}`}></div>
            <div className="p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${typeColors[c.channel_type] || "from-slate-400 to-slate-500"} flex items-center justify-center text-white font-bold`}>{c.name?.charAt(0)}</div>
                <div><h3 className="font-bold text-slate-800">{c.name}</h3><p className="text-xs text-slate-400 font-mono">{c.code}</p></div>
              </div>
              <div className="flex items-center justify-between mt-3">
                <span className="badge badge-info">{c.channel_type}</span>
                <span className="badge badge-success">{c.status || "ACTIVE"}</span>
              </div>
              <p className="text-[10px] text-slate-400 mt-2">Created: {c.created_at ? new Date(c.created_at).toLocaleDateString() : "—"}</p>
            </div>
          </div>
        ))}
      </div>}

      {showModal && (<div className="modal-overlay" onClick={() => setShowModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header"><h3 className="font-bold text-lg">Add Channel</h3><button onClick={() => setShowModal(false)} className="text-xl">&times;</button></div>
        <div className="modal-body space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="input-label">Code *</label><input className="input-field" value={form.code || ""} onChange={e => setForm({...form, code: e.target.value})} /></div>
            <div><label className="input-label">Name *</label><input className="input-field" value={form.name || ""} onChange={e => setForm({...form, name: e.target.value})} /></div>
          </div>
          <div><label className="input-label">Channel Type</label><select className="input-field" value={form.channel_type} onChange={e => setForm({...form, channel_type: e.target.value})}><option value="CLINIC">Clinic</option><option value="TELECONSULT">Teleconsult</option><option value="HEALTH_ATM">Health ATM</option><option value="HYBRID">Hybrid</option></select></div>
        </div>
        <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button><button className="btn-primary" onClick={handleCreate}>Create</button></div>
      </div></div>)}
    </div></div>);
}
