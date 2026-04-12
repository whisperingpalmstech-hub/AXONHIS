"use client";
import React, { useState, useEffect } from "react";
import { TopNav } from "@/components/TopNav";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
function authHeaders() { const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null; return { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }; }

export default function CliniciansPage() {
  const [clinicians, setClinicians] = useState<any[]>([]);
  const [orgs, setOrgs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<any>({});
  const [search, setSearch] = useState("");

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/v1/md/clinicians`, { headers: authHeaders() }).then(r=>r.ok?r.json():[]),
      fetch(`${API}/api/v1/md/organizations`, { headers: authHeaders() }).then(r=>r.ok?r.json():[]),
    ]).then(([c,o])=>{setClinicians(c);setOrgs(o);}).finally(()=>setLoading(false));
  }, []);

  const handleCreate = async () => {
    const res = await fetch(`${API}/api/v1/md/clinicians`, { method:"POST", headers:authHeaders(), body:JSON.stringify(form) });
    if(res.ok){setClinicians([...clinicians,await res.json()]);setShowModal(false);setForm({});}
  };
  const filtered = clinicians.filter(c=>!search||c.display_name?.toLowerCase().includes(search.toLowerCase())||c.code?.toLowerCase().includes(search.toLowerCase()));
  const getTypeColor = (t:string) => { switch(t){ case"DOCTOR":return"bg-blue-50 text-blue-700 border-blue-200";case"NURSE":return"bg-emerald-50 text-emerald-700 border-emerald-200";default:return"bg-amber-50 text-amber-700 border-amber-200";} };

  return (<div><TopNav title="Clinician Registry" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Clinician Management</h2><p className="text-sm text-slate-500">Manage doctors, nurses, and technicians</p></div>
        <button onClick={()=>setShowModal(true)} className="btn-primary"><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>Add Clinician</button>
      </div>
      <div className="relative"><svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg><input className="input-field !pl-10" placeholder="Search clinicians..." value={search} onChange={e=>setSearch(e.target.value)}/></div>
      {loading?<div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div>:
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.length===0?<div className="col-span-full text-center py-16 text-slate-400">No clinicians found.</div>:
        filtered.map(c=>(
          <div key={c.clinician_id} className="bg-white rounded-2xl border border-slate-200 p-5 hover:shadow-md transition-all group">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center text-white font-bold text-lg shrink-0 shadow-lg shadow-teal-500/20">{c.display_name?.charAt(0)||"?"}</div>
              <div className="flex-1 min-w-0"><h3 className="font-bold text-slate-800 truncate">{c.display_name}</h3><p className="text-xs text-slate-500 font-mono">{c.code||"—"}</p>
                <div className="flex items-center gap-2 mt-2"><span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${getTypeColor(c.clinician_type)}`}>{c.clinician_type}</span><span className={`w-2 h-2 rounded-full ${c.active_flag?"bg-emerald-400":"bg-slate-300"}`}></span></div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-slate-400 block">Email</span><span className="text-slate-700 truncate block">{c.email||"—"}</span></div>
              <div><span className="text-slate-400 block">Phone</span><span className="text-slate-700">{c.mobile_number||"—"}</span></div>
            </div>
          </div>))}
      </div>}
      {showModal&&(<div className="modal-overlay" onClick={()=>setShowModal(false)}><div className="modal-content" onClick={e=>e.stopPropagation()}>
        <div className="modal-header"><h3 className="font-bold text-lg">Add Clinician</h3><button onClick={()=>setShowModal(false)} className="text-slate-400 hover:text-slate-600"><svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button></div>
        <div className="modal-body space-y-4">
          <div><label className="input-label">Organization *</label><select className="input-field" value={form.organization_id||""} onChange={e=>setForm({...form,organization_id:e.target.value})}><option value="">Select</option>{orgs.map(o=><option key={o.organization_id} value={o.organization_id}>{o.name}</option>)}</select></div>
          <div className="grid grid-cols-2 gap-4"><div><label className="input-label">Display Name *</label><input className="input-field" value={form.display_name||""} onChange={e=>setForm({...form,display_name:e.target.value})}/></div><div><label className="input-label">Code</label><input className="input-field" value={form.code||""} onChange={e=>setForm({...form,code:e.target.value})}/></div></div>
          <div className="grid grid-cols-2 gap-4"><div><label className="input-label">Type</label><select className="input-field" value={form.clinician_type||"DOCTOR"} onChange={e=>setForm({...form,clinician_type:e.target.value})}><option value="DOCTOR">Doctor</option><option value="NURSE">Nurse</option><option value="TECHNICIAN">Technician</option></select></div><div><label className="input-label">Email</label><input className="input-field" type="email" value={form.email||""} onChange={e=>setForm({...form,email:e.target.value})}/></div></div>
        </div>
        <div className="modal-footer"><button className="btn-secondary" onClick={()=>setShowModal(false)}>Cancel</button><button className="btn-primary" onClick={handleCreate}>Create</button></div>
      </div></div>)}
    </div></div>);
}
