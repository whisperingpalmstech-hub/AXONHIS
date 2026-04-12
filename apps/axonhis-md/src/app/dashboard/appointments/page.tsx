"use client";
import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

export default function AppointmentsPage() {
  const router = useRouter();
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<any>({ appointment_mode: "IN_PERSON", appointment_type: "NEW" });
  const [filter, setFilter] = useState("");
  const [patients, setPatients] = useState<any[]>([]);
  const [clinicians, setClinicians] = useState<any[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [orgs, setOrgs] = useState<any[]>([]);

  const load = useCallback(async () => {
    try { const data = await apiFetch("/appointments"); setAppointments(data); } catch { setAppointments([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    load();
    apiFetch("/patients").then(setPatients).catch(() => {});
    apiFetch("/clinicians").then(setClinicians).catch(() => {});
    apiFetch("/channels").then(setChannels).catch(() => {});
    apiFetch("/organizations").then(setOrgs).catch(() => {});
  }, [load]);

  const handleCreate = async () => {
    try {
      const payload: any = {
        organization_id: form.organization_id || orgs[0]?.organization_id,
        patient_id: form.patient_id,
        clinician_id: form.clinician_id,
        appointment_mode: form.appointment_mode,
        appointment_type: form.appointment_type,
        slot_start: form.slot_start ? new Date(form.slot_start).toISOString() : undefined,
        slot_end: form.slot_end ? new Date(form.slot_end).toISOString() : (form.slot_start ? new Date(new Date(form.slot_start).getTime() + 30 * 60000).toISOString() : undefined),
        reason_text: form.reason_text || undefined,
        channel_id: form.channel_id || undefined,
      };
      const result = await apiPost("/appointments", payload);
      setShowModal(false); setForm({ appointment_mode: "IN_PERSON", appointment_type: "NEW" }); load();
      if (result.encounter_id) {
        router.push(`/dashboard/encounters?encounter_id=${result.encounter_id}`);
      }
    } catch(e) { alert("Error: " + e); }
  };

  const statusColors: Record<string,string> = { BOOKED: "badge-info", CONFIRMED: "badge-success", CANCELLED: "badge-error", COMPLETED: "badge-neutral", NOSHOW: "badge-warning", SCHEDULED: "badge-info" };
  const modeIcons: Record<string,string> = { IN_PERSON: "🏥", TELECONSULT: "📱", HEALTH_ATM: "🏧", HYBRID: "🔄" };

  const filtered = appointments.filter(a => !filter || a.status === filter);

  return (<div><TopNav title="Appointment Scheduling" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Scheduling Engine</h2><p className="text-sm text-slate-500">{appointments.length} appointments total</p></div>
        <button onClick={() => setShowModal(true)} className="btn-primary">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>Book Appointment</button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["", "BOOKED", "SCHEDULED", "CONFIRMED", "COMPLETED", "CANCELLED", "NOSHOW"].map(s => (
          <button key={s} onClick={() => setFilter(s)} className={`px-4 py-2 rounded-full text-xs font-semibold transition-all ${filter === s ? "bg-teal-600 text-white shadow-md" : "bg-white border border-slate-200 text-slate-600 hover:border-teal-300"}`}>{s || "All"} ({s ? appointments.filter(a => a.status === s).length : appointments.length})</button>
        ))}
      </div>

      {loading ? <div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      filtered.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-sky-50 flex items-center justify-center text-4xl">📅</div>
          <h3 className="text-lg font-bold text-slate-700">No Appointments</h3>
          <p className="text-sm text-slate-500 mt-1 mb-4">Schedule your first appointment</p>
          <button onClick={() => setShowModal(true)} className="btn-primary">Book First Appointment</button>
        </div>
      ) :
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <table className="data-table"><thead><tr><th>Mode</th><th>Patient</th><th>Clinician</th><th>Date & Time</th><th>Type</th><th>Channel</th><th>Status</th></tr></thead>
          <tbody>{filtered.map(a => (
            <tr key={a.appointment_id} className="hover:bg-teal-50/30">
              <td className="text-xl">{modeIcons[a.appointment_mode] || "🏥"}</td>
              <td className="font-semibold text-slate-800">{a.patient_name || "—"}</td>
              <td className="text-sm">{a.clinician_name || "—"}</td>
              <td className="text-sm">{a.slot_start ? new Date(a.slot_start).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" }) : "—"}</td>
              <td><span className="badge badge-neutral">{a.appointment_type || "—"}</span></td>
              <td className="text-xs text-slate-500">{channels.find(c => c.channel_id === a.channel_id)?.name || "—"}</td>
              <td><span className={`badge ${statusColors[a.status] || "badge-neutral"}`}>{a.status || "—"}</span></td>
            </tr>))}</tbody></table>
      </div>}

      {showModal && (<div className="modal-overlay" onClick={() => setShowModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header bg-gradient-to-r from-sky-50 to-blue-50"><h3 className="font-bold text-lg">Book Appointment</h3><button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button></div>
        <div className="modal-body space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="input-label">Patient *</label>
              <select className="input-field" value={form.patient_id || ""} onChange={e => setForm({...form, patient_id: e.target.value})}>
                <option value="">Select Patient...</option>
                {patients.map(p => <option key={p.patient_id} value={p.patient_id}>{p.display_name} {p.mrn ? `(${p.mrn})` : ""}</option>)}
              </select></div>
            <div><label className="input-label">Clinician *</label>
              <select className="input-field" value={form.clinician_id || ""} onChange={e => setForm({...form, clinician_id: e.target.value})}>
                <option value="">Select Clinician...</option>
                {clinicians.map(c => <option key={c.clinician_id} value={c.clinician_id}>{c.display_name} ({c.clinician_type})</option>)}
              </select></div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div><label className="input-label">Mode</label><select className="input-field" value={form.appointment_mode} onChange={e => setForm({...form, appointment_mode: e.target.value})}><option value="IN_PERSON">In-Person</option><option value="TELECONSULT">Teleconsult</option><option value="HEALTH_ATM">Health ATM</option><option value="HYBRID">Hybrid</option></select></div>
            <div><label className="input-label">Type</label><select className="input-field" value={form.appointment_type} onChange={e => setForm({...form, appointment_type: e.target.value})}><option value="NEW">New</option><option value="FOLLOW_UP">Follow-Up</option><option value="EMERGENCY">Emergency</option><option value="WALK_IN">Walk-In</option></select></div>
            <div><label className="input-label">Channel</label>
              <select className="input-field" value={form.channel_id || ""} onChange={e => setForm({...form, channel_id: e.target.value})}>
                <option value="">None</option>
                {channels.map(c => <option key={c.channel_id} value={c.channel_id}>{c.name}</option>)}
              </select></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="input-label">Start Date & Time *</label><input type="datetime-local" className="input-field" value={form.slot_start || ""} onChange={e => setForm({...form, slot_start: e.target.value})} /></div>
            <div><label className="input-label">End Date & Time</label><input type="datetime-local" className="input-field" value={form.slot_end || ""} onChange={e => setForm({...form, slot_end: e.target.value})} /></div>
          </div>
          <div><label className="input-label">Reason</label><textarea className="input-field" rows={2} value={form.reason_text || ""} onChange={e => setForm({...form, reason_text: e.target.value})} /></div>
        </div>
        <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button><button className="btn-primary" onClick={handleCreate}>Book Appointment</button></div>
      </div></div>)}
    </div></div>);
}
