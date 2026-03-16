"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Activity, Search, Video, Clock, Plus, X, Loader2, User, Stethoscope, Building2 } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

const authHeaders = () => ({
  "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
  "Content-Type": "application/json",
});

interface Patient { id: string; patient_uuid: string; first_name: string; last_name: string; }

export default function EncountersList() {
  const [encounters, setEncounters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New Encounter Modal
  const [showModal, setShowModal] = useState(false);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [patientsLoading, setPatientsLoading] = useState(false);
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [encounterForm, setEncounterForm] = useState({
    encounter_type: "OP",
    department: "General Medicine",
    status: "in_progress",
  });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const fetchEncounters = async () => {
    try {
      const res = await fetch(`${API}/api/v1/encounters/`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setEncounters(data);
      }
    } catch (err) {
      console.error("Failed to fetch encounters", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchEncounters(); }, []);

  // Fetch patients when modal opens or search changes
  useEffect(() => {
    if (!showModal) return;
    const fetchPatients = async () => {
      setPatientsLoading(true);
      try {
        const url = patientSearch.length > 1
          ? `${API}/api/v1/patients/search?query=${encodeURIComponent(patientSearch)}&limit=10`
          : `${API}/api/v1/patients/?limit=20`;
        const res = await fetch(url, { headers: authHeaders() });
        if (res.ok) {
          const data = await res.json();
          setPatients(Array.isArray(data) ? data : data.items || []);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setPatientsLoading(false);
      }
    };
    const timer = setTimeout(fetchPatients, 300);
    return () => clearTimeout(timer);
  }, [showModal, patientSearch]);

  const openModal = () => {
    setShowModal(true);
    setSelectedPatient(null);
    setPatientSearch("");
    setCreateError("");
    setEncounterForm({ encounter_type: "OP", department: "General Medicine", status: "in_progress" });
  };

  const handleCreateEncounter = async () => {
    if (!selectedPatient) { setCreateError("Please select a patient."); return; }
    setCreating(true);
    setCreateError("");
    try {
      const userRes = await fetch(`${API}/api/v1/auth/me`, { headers: authHeaders() });
      const currentUser = await userRes.json();

      const res = await fetch(`${API}/api/v1/encounters/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          patient_id: selectedPatient.id,
          encounter_type: encounterForm.encounter_type,
          doctor_id: currentUser.id,
          department: encounterForm.department,
          status: encounterForm.status,
        }),
      });

      if (res.ok) {
        setShowModal(false);
        await fetchEncounters();
      } else {
        const err = await res.json();
        setCreateError(err.detail || "Failed to create encounter. Please try again.");
      }
    } catch (e) {
      console.error(e);
      setCreateError("Network error. Please check the backend is running.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* New Encounter Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-lg w-full mx-4 animate-in fade-in zoom-in-95">
            
            {/* Modal Header */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Stethoscope className="text-blue-600" size={22}/> New Encounter
              </h2>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
                <X size={18} className="text-slate-500"/>
              </button>
            </div>

            {/* Patient Search */}
            <div className="mb-5">
              <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1.5"><User size={14}/> Select Patient *</label>
              <div className="relative mb-2">
                <Search size={16} className="absolute left-3 top-2.5 text-slate-400"/>
                <input
                  type="text"
                  className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                  placeholder="Search by name, patient ID..."
                  value={patientSearch}
                  onChange={e => { setPatientSearch(e.target.value); setSelectedPatient(null); }}
                />
              </div>
              {/* Patient List */}
              <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100">
                {patientsLoading ? (
                  <div className="p-3 text-center text-slate-400 text-sm flex items-center justify-center gap-2"><Loader2 size={14} className="animate-spin"/> Loading patients...</div>
                ) : patients.length === 0 ? (
                  <div className="p-3 text-center text-slate-400 text-sm">
                    No patients found. <Link href="/dashboard/patients/registration" className="text-blue-600 hover:underline">Register one first →</Link>
                  </div>
                ) : (
                  patients.map(pt => (
                    <button
                      key={pt.id}
                      onClick={() => setSelectedPatient(pt)}
                      className={`w-full text-left px-4 py-3 text-sm hover:bg-blue-50 transition-colors flex items-center justify-between ${selectedPatient?.id === pt.id ? 'bg-blue-50 border-l-2 border-blue-500' : ''}`}
                    >
                      <div>
                        <span className="font-semibold text-slate-800">{pt.first_name} {pt.last_name}</span>
                        <span className="text-slate-400 text-xs ml-2">{pt.patient_uuid}</span>
                      </div>
                      {selectedPatient?.id === pt.id && <span className="text-blue-600 text-xs font-bold">✓ Selected</span>}
                    </button>
                  ))
                )}
              </div>
              {selectedPatient && (
                <div className="mt-2 p-2 bg-blue-50 rounded-lg text-xs text-blue-700 font-semibold">
                  ✓ Patient: {selectedPatient.first_name} {selectedPatient.last_name} ({selectedPatient.patient_uuid})
                </div>
              )}
            </div>

            {/* Encounter Form */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">Encounter Type</label>
                <select
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  value={encounterForm.encounter_type}
                  onChange={e => setEncounterForm(f => ({ ...f, encounter_type: e.target.value }))}
                >
                  <option value="OP">OP (Out Patient)</option>
                  <option value="IP">IP (In Patient)</option>
                  <option value="ER">ER (Emergency)</option>
                  <option value="FOLLOW_UP">Follow-Up</option>
                  <option value="TELECONSULT">Teleconsultation</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-1"><Building2 size={13}/> Department</label>
                <select
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  value={encounterForm.department}
                  onChange={e => setEncounterForm(f => ({ ...f, department: e.target.value }))}
                >
                  <option>General Medicine</option>
                  <option>Cardiology</option>
                  <option>Orthopedics</option>
                  <option>Pediatrics</option>
                  <option>Neurology</option>
                  <option>Oncology</option>
                  <option>Dermatology</option>
                  <option>Gynecology</option>
                  <option>Ophthalmology</option>
                  <option>ENT</option>
                  <option>Psychiatry</option>
                  <option>Emergency</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">Status</label>
                <select
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  value={encounterForm.status}
                  onChange={e => setEncounterForm(f => ({ ...f, status: e.target.value }))}
                >
                  <option value="in_progress">In Progress (Start Now)</option>
                  <option value="scheduled">Scheduled</option>
                </select>
              </div>
            </div>

            {createError && (
              <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-200">{createError}</div>
            )}

            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowModal(false)} className="px-5 py-2 border border-slate-300 rounded-lg text-slate-700 font-semibold hover:bg-slate-50 transition-colors text-sm">
                Cancel
              </button>
              <button
                onClick={handleCreateEncounter}
                disabled={creating || !selectedPatient}
                className="px-5 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-colors flex items-center gap-2 text-sm disabled:opacity-60"
              >
                {creating ? <><Loader2 size={14} className="animate-spin"/> Creating...</> : <><Plus size={14}/> Create Encounter</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Page Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Activity className="text-[var(--accent-primary)]"/> Today&apos;s Encounters
          </h1>
          <p className="text-[var(--text-secondary)] mt-1">Manage clinical consultations and admissions.</p>
        </div>
        <button onClick={openModal} className="btn-primary flex items-center gap-2">
          <Plus size={18}/> New Quick Encounter
        </button>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 text-[var(--text-secondary)]" size={18}/>
              <input type="text" className="input-field pl-10" placeholder="Search encounters by patient ID or department..."/>
            </div>
            <select className="input-field w-48 border-[var(--border)]">
              <option>All Statuses</option>
              <option>scheduled</option>
              <option>in_progress</option>
              <option>completed</option>
            </select>
          </div>

          {loading ? (
            <div className="text-center py-10 text-[var(--text-secondary)] flex items-center justify-center gap-2">
              <Loader2 size={20} className="animate-spin"/> Loading encounters...
            </div>
          ) : encounters.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-slate-400 text-5xl mb-4">🏥</div>
              <p className="text-[var(--text-secondary)] font-medium">No encounters found.</p>
              <p className="text-sm text-slate-400 mt-1">Click <strong>New Quick Encounter</strong> to start a clinical visit.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Encounter ID</th>
                    <th>Type</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th className="text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {encounters.map(enc => (
                    <tr key={enc.id}>
                      <td className="font-medium text-blue-600">{enc.encounter_uuid}</td>
                      <td>
                        <span className="px-2 py-1 bg-slate-100 text-slate-700 text-xs rounded font-bold">
                          {enc.encounter_type}
                        </span>
                      </td>
                      <td>{enc.department}</td>
                      <td>
                        <span className={`badge ${enc.status === 'in_progress' ? 'badge-warning' : enc.status === 'completed' ? 'badge-success' : 'badge-neutral'}`}>
                          {enc.status}
                        </span>
                      </td>
                      <td className="text-[var(--text-secondary)]">{new Date(enc.created_at).toLocaleString()}</td>
                      <td className="text-right">
                        <Link href={`/dashboard/encounters/${enc.id}`} className="btn-primary py-1.5 px-3 text-sm inline-flex items-center gap-2">
                          <Video size={14}/> Workspace
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
