"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Search, Plus, User, Calendar, Phone, Edit, Trash2, X, Save, Loader2 } from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { useTranslation } from "@/i18n";

interface Patient {
  id: string;
  patient_uuid: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  primary_phone: string;
  status: string;
}

export default function PatientsPage() {
  const [search, setSearch] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();

  // Edit Modal State
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Patient>>({});

  const handleSaveEdit = async () => {
    if (!editingPatient) return;
    setIsSaving(true);
    try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/patients/${editingPatient.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
            body: JSON.stringify({
                first_name: editForm.first_name,
                last_name: editForm.last_name,
                date_of_birth: editForm.date_of_birth,
                gender: editForm.gender,
                primary_phone: editForm.primary_phone,
            })
        });
        if (res.ok) {
            setPatients(patients.map(p => p.id === editingPatient.id ? { ...p, ...editForm } as Patient : p));
            setEditingPatient(null);
        }
    } catch (e) {
        console.error(e);
    } finally {
        setIsSaving(false);
    }
  };

  useEffect(() => {
    const fetchPatients = async () => {
      setLoading(true);
      try {
        const url = search.length > 1 
          ? `/api/v1/patients/search?query=${encodeURIComponent(search)}` 
          : '/api/v1/patients';
          
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}${url}`, {
          headers: {
            "Authorization": `Bearer ${localStorage.getItem("access_token")}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          setPatients(data);
        }
      } catch (err) {
        console.error("Failed to fetch patients", err);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(() => fetchPatients(), 300);
    return () => clearTimeout(debounce);
  }, [search]);

  return (
    <div>
      <TopNav title={t("patients.title")} />
      <div className="p-8 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-700">
              {t("patients.title")}
            </h1>
            <p className="text-[var(--text-secondary)] mt-1">{t("patients.manageRecords")}</p>
          </div>
          <Link href="/dashboard/patients/registration" className="btn-primary flex items-center gap-2 shadow-lg shadow-blue-500/20">
            <Plus size={20} />
            <span>{t("patients.registerNew")}</span>
          </Link>
        </div>

      <div className="card">
        <div className="card-body">
          <div className="relative mb-6">
            <Search className="absolute left-3 top-3 text-[var(--text-secondary)]" size={20} />
            <input 
              type="text"
              placeholder="Search by name, phone, or patient ID..."
              className="input-field pl-10"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {loading ? (
            <div className="py-8 text-center text-[var(--text-secondary)]">Loading...</div>
          ) : patients.length === 0 ? (
            <div className="py-8 text-center text-[var(--text-secondary)]">No patients found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-secondary)] text-sm">
                    <th className="pb-3 font-medium">Patient Details</th>
                    <th className="pb-3 font-medium">Patient ID</th>
                    <th className="pb-3 font-medium">Phone Number</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {patients.map(p => (
                    <tr key={p.id} className="group hover:bg-[var(--bg-secondary)] transition-colors">
                      <td className="py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-[var(--accent-primary)]/10 flex items-center justify-center text-[var(--accent-primary)] font-semibold">
                            {p.first_name[0]}{p.last_name[0]}
                          </div>
                          <div>
                            <div className="font-semibold text-[var(--text-primary)]">{p.first_name} {p.last_name}</div>
                            <div className="text-xs text-[var(--text-secondary)] flex items-center gap-1 mt-1">
                              <Calendar size={12} /> {p.date_of_birth} 
                              <span className="mx-1">•</span> <User size={12} /> {p.gender}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 text-sm font-medium text-[var(--text-secondary)]">{p.patient_uuid}</td>
                      <td className="py-4">
                        <div className="text-sm text-[var(--text-secondary)] flex items-center gap-2">
                          <Phone size={14} /> {p.primary_phone || "N/A"}
                        </div>
                      </td>
                      <td className="py-4">
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          {p.status}
                        </span>
                      </td>
                      <td className="py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <Link href={`/dashboard/patients/${p.id}`} className="p-2 text-blue-600 bg-blue-50 mt-1 hover:bg-blue-100 rounded-md transition-colors" title="View details">
                            <User size={16} />
                          </Link>
                          <button onClick={() => {
                            setEditingPatient(p);
                            setEditForm({
                              first_name: p.first_name,
                              last_name: p.last_name,
                              date_of_birth: p.date_of_birth,
                              gender: p.gender,
                              primary_phone: p.primary_phone || ""
                            });
                          }} className="p-2 text-amber-600 bg-amber-50 mt-1 hover:bg-amber-100 rounded-md transition-colors" title="Edit patient details">
                            <Edit size={16} />
                          </button>
                          <button onClick={async () => {
                            if (!window.confirm("Are you sure you want to delete this patient permanently?")) return;
                            try {
                              const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/patients/${p.id}`, {
                                method: 'DELETE',
                                headers: { "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
                              });
                              if(res.ok) setPatients(patients.filter(pat => pat.id !== p.id));
                            } catch(e) { console.error(e); }
                          }} className="p-2 text-red-600 bg-red-50 mt-1 hover:bg-red-100 rounded-md transition-colors" title="Delete patient">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Edit Patient Modal */}
      {editingPatient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
          <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-5 border-b border-[var(--border)] bg-[var(--bg-secondary)]">
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">Edit Patient Details</h2>
              <button 
                onClick={() => setEditingPatient(null)}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors p-1"
              >
                <X size={20} />
              </button>
            </div>
            
            <form onSubmit={(e) => { e.preventDefault(); handleSaveEdit(); }}>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">First Name <span className="text-red-500">*</span></label>
                    <input 
                      type="text" 
                      className="input-field" 
                      value={editForm.first_name || ""} 
                      onChange={e => setEditForm({...editForm, first_name: e.target.value})} 
                      required
                    />
                  </div>
                  <div>
                    <label className="input-label">Last Name <span className="text-red-500">*</span></label>
                    <input 
                      type="text" 
                      className="input-field" 
                      value={editForm.last_name || ""} 
                      onChange={e => setEditForm({...editForm, last_name: e.target.value})} 
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="input-label">Phone Number <span className="text-red-500">*</span></label>
                  <input 
                    type="tel" 
                    className="input-field" 
                    value={editForm.primary_phone || ""} 
                    onChange={e => setEditForm({...editForm, primary_phone: e.target.value.replace(/\D/g, '').substring(0, 10)})} 
                    pattern="^[0-9]{10}$"
                    title="Please enter exactly 10 digits for the phone number"
                    maxLength={10}
                    minLength={10}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">Date of Birth <span className="text-red-500">*</span></label>
                    <input 
                      type="date" 
                      className="input-field" 
                      value={editForm.date_of_birth || ""} 
                      onChange={e => setEditForm({...editForm, date_of_birth: e.target.value})} 
                      required
                    />
                  </div>
                  <div>
                    <label className="input-label">Gender <span className="text-red-500">*</span></label>
                    <select 
                      className="input-field" 
                      value={editForm.gender || ""} 
                      onChange={e => setEditForm({...editForm, gender: e.target.value})}
                      required
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 p-5 border-t border-[var(--border)] bg-[var(--bg-secondary)]">
                <button 
                  type="button"
                  onClick={() => setEditingPatient(null)}
                  className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] bg-white border border-[var(--border)] rounded-lg hover:bg-gray-50 transition-colors"
                  disabled={isSaving}
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  disabled={isSaving}
                  className="btn-primary flex items-center gap-2"
                >
                  {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
