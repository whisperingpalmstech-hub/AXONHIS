"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Bed, ClipboardList, BedDouble, AlertTriangle, Users, FileSignature, 
  MapPin, CheckCircle2, Clock, Plus, Building2, UserPlus, Search, ChevronDown, Check, X
} from "lucide-react";
import {
  ipdApi, type DashboardStats, type IpdAdmissionRequest, type IpdBedMaster
} from "@/lib/ipd-api";
import { api } from "@/lib/api";

interface PatientOption { id: string; first_name: string; last_name: string; patient_uuid: string; dob?: string; gender?: string; primary_phone?: string; }

type Tab = "DASHBOARD" | "REQUESTS" | "ADMISSIONS" | "BEDS";

export default function IPDDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>("DASHBOARD");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [requests, setRequests] = useState<IpdAdmissionRequest[]>([]);
  const [admissions, setAdmissions] = useState<any[]>([]);
  const [beds, setBeds] = useState<IpdBedMaster[]>([]);
  const [loading, setLoading] = useState(false);
  
  const [showReqModal, setShowReqModal] = useState(false);
  const [showAllocModal, setShowAllocModal] = useState(false);
  const [allocReqId, setAllocReqId] = useState<string | null>(null);

  // Phase 14 Modals
  const [showChecklistModal, setShowChecklistModal] = useState<string | null>(null);
  const [showEstimateModal, setShowEstimateModal] = useState<{reqId: string, category: string, uhid: string} | null>(null);
  const [currentEstimate, setCurrentEstimate] = useState<any>(null);
  const [checklistData, setChecklistData] = useState<any>(null);

  // Dropdowns
  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [patientSearch, setPatientSearch] = useState("");
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<PatientOption | null>(null);
  const patientRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const dbStats = await ipdApi.getDashboardStats();
      if (dbStats) setStats(dbStats);

      if (activeTab === "REQUESTS" || activeTab === "DASHBOARD") setRequests(await ipdApi.getPendingRequests() || []);
      if (activeTab === "ADMISSIONS" || activeTab === "DASHBOARD") setAdmissions(await ipdApi.getAdmissions() || []);
      if (activeTab === "BEDS" || activeTab === "DASHBOARD") {
        setBeds(await ipdApi.getAllBeds() || []);
      }
      
      const pts = await api.get<PatientOption[]>('/patients/?skip=0&limit=100');
      if (pts) setPatients(pts);

    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }, [activeTab]);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (patientRef.current && !patientRef.current.contains(e.target as Node)) setShowPatientDropdown(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const filteredPatients = patients.filter(p =>
    `${p.first_name} ${p.last_name} ${p.patient_uuid}`.toLowerCase().includes(patientSearch.toLowerCase())
  );

  const handleCreateRequest = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedPatient) return;
    const fd = new FormData(e.currentTarget);
    try {
      await ipdApi.createAdmissionRequest({
        patient_name: `${selectedPatient.first_name} ${selectedPatient.last_name}`,
        patient_uhid: selectedPatient.patient_uuid,
        gender: selectedPatient.gender || fd.get("gender"),
        date_of_birth: selectedPatient.dob || fd.get("date_of_birth"),
        mobile_number: selectedPatient.primary_phone || fd.get("mobile_number"),
        blood_group: fd.get("blood_group"),
        admitting_doctor: fd.get("admitting_doctor"),
        treating_doctor: fd.get("treating_doctor"),
        specialty: fd.get("specialty"),
        reason_for_admission: fd.get("reason_for_admission"),
        admission_category: fd.get("admission_category"),
        admission_source: fd.get("admission_source"),
        preferred_bed_category: fd.get("preferred_bed_category"),
        expected_admission_date: new Date(fd.get("expected_admission_date") as string).toISOString()
      });
      setShowReqModal(false);
      setSelectedPatient(null); setPatientSearch('');
      fetchData();
    } catch (error) {
      alert("Failed to create request");
    }
  };

  const handleAllocateBed = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!allocReqId) return;
    const fd = new FormData(e.currentTarget);
    const bedId = fd.get("bed_id") as string;
    try {
      // Must be approved first
      await ipdApi.updateRequestStatus(allocReqId, "Approved");
      await ipdApi.allocateBed(allocReqId, bedId);
      setShowAllocModal(false);
      setAllocReqId(null);
      fetchData();
    } catch (error) {
      alert("Failed to allocate bed");
    }
  };

  const markHousekeepingCleaned = async (bedId: string) => {
    if (confirm(`Mark bed ${bedId} as cleaned?`)) {
      await ipdApi.markBedCleaned(bedId);
      fetchData();
    }
  };

  const getBedStatusColor = (status: string) => {
    switch(status) {
      case 'Available': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'Occupied': return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'Under Housekeeping': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'Reserved': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <TopNav title="IPD Admission" />
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
              <BedDouble className="text-blue-600" size={32}/>
              Admission & Bed Management
            </h1>
            <p className="text-slate-500 font-medium mt-1">IPD Workflows, Bed Allocation & Occupancy Dashboard</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setShowReqModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl font-bold transition-all shadow-md shadow-blue-200">
              <UserPlus size={18}/> New Admission
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 p-1.5 bg-white/50 backdrop-blur border border-slate-200 rounded-2xl w-fit mb-8 shadow-sm">
          {[
            { id: "DASHBOARD", label: "Occupancy Dashboard", icon: <Building2 size={16}/> },
            { id: "REQUESTS", label: "Pending Admissions", icon: <ClipboardList size={16}/> },
            { id: "ADMISSIONS", label: "Active Admissions", icon: <FileSignature size={16}/> },
            { id: "BEDS", label: "Bed Availability", icon: <Bed size={16}/> }
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id as Tab)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
                activeTab === t.id ? "bg-white text-blue-700 shadow-sm border border-slate-200/50" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100/50"
              }`}>
              {t.icon} {t.label}
              {t.id === "REQUESTS" && requests.length > 0 && (
                <span className="bg-rose-100 text-rose-600 text-[10px] px-1.5 py-0.5 rounded-full ml-1">{requests.length}</span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-400 font-medium">Syncing with Wards...</div>
        ) : (
          <div className="space-y-6">
            
            {activeTab === "DASHBOARD" && stats && (
              <div className="grid grid-cols-5 gap-4">
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <div className="text-slate-500 font-bold mb-1 flex items-center gap-2"><Bed size={16}/> Total Beds</div>
                  <div className="text-4xl font-black text-slate-800">{stats.total_beds}</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <div className="text-slate-500 font-bold mb-1 flex items-center gap-2"><Users size={16} className="text-rose-500"/> Occupied</div>
                  <div className="text-4xl font-black text-rose-600">{stats.occupied_beds}</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <div className="text-slate-500 font-bold mb-1 flex items-center gap-2"><CheckCircle2 size={16} className="text-emerald-500"/> Available</div>
                  <div className="text-4xl font-black text-emerald-600">{stats.available_beds}</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <div className="text-slate-500 font-bold mb-1 flex items-center gap-2"><AlertTriangle size={16} className="text-amber-500"/> Housekeeping</div>
                  <div className="text-4xl font-black text-amber-600">{stats.housekeeping_beds}</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <div className="text-slate-500 font-bold mb-1 flex items-center gap-2"><ClipboardList size={16} className="text-blue-500"/> Pending Reg</div>
                  <div className="text-4xl font-black text-blue-600">{stats.pending_requests}</div>
                </div>
              </div>
            )}

            {activeTab === "REQUESTS" && (
              <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                      <th className="p-4 font-bold">Request ID</th>
                      <th className="p-4 font-bold">Patient</th>
                      <th className="p-4 font-bold">Category</th>
                      <th className="p-4 font-bold">Admitting Dr.</th>
                      <th className="p-4 font-bold">Pref. Bed</th>
                      <th className="p-4 font-bold">Date</th>
                      <th className="p-4 font-bold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {requests.length === 0 ? (
                      <tr><td colSpan={7} className="p-8 text-center text-slate-400 font-medium">No pending admission requests</td></tr>
                    ) : (
                      requests.map(r => (
                        <tr key={r.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="p-4 font-mono text-sm font-bold text-slate-700">{r.request_id}</td>
                          <td className="p-4">
                            <div className="font-bold text-slate-800 text-sm">{r.patient_name}</div>
                            <div className="text-xs text-slate-500 font-mono">{r.patient_uhid}</div>
                          </td>
                          <td className="p-4 text-sm font-medium text-slate-600">{r.admission_category}</td>
                          <td className="p-4 text-sm font-medium text-slate-600">{r.admitting_doctor}</td>
                          <td className="p-4 text-sm font-medium text-slate-600">{r.preferred_bed_category}</td>
                          <td className="p-4 text-sm font-medium text-slate-600">{new Date(r.expected_admission_date).toLocaleDateString()}</td>
                          <td className="p-4 text-right">
                            <div className="flex justify-end gap-2">
                              <button onClick={() => { 
                                ipdApi.generateCostEstimate(r.id, {selected_bed_category: r.preferred_bed_category, planned_procedures: [], planned_services: []})
                                  .then(e => { setCurrentEstimate(e); setShowEstimateModal({reqId: r.id, category: r.preferred_bed_category, uhid: r.patient_uhid}); })
                              }} className="text-xs font-bold bg-amber-50 text-amber-700 px-3 py-1.5 rounded-lg hover:bg-amber-100 flex items-center gap-1">
                                AI Estimate
                              </button>
                              <button onClick={() => {setAllocReqId(r.id); setShowAllocModal(true);}} className="text-xs font-bold bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg hover:bg-blue-100">
                                Allocate
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === "ADMISSIONS" && (
             <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                      <th className="p-4 font-bold">Admission No</th>
                      <th className="p-4 font-bold">Patient UHID</th>
                      <th className="p-4 font-bold">Doctor</th>
                      <th className="p-4 font-bold">Time</th>
                      <th className="p-4 font-bold">Status</th>
                      <th className="p-4 font-bold text-right">Workflow</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {admissions.length === 0 ? (
                      <tr><td colSpan={6} className="p-8 text-center text-slate-400 font-medium">No active admissions</td></tr>
                    ) : (
                      admissions.map(a => (
                        <tr key={a.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="p-4 font-mono text-sm font-bold text-slate-700">{a.admission_number}</td>
                          <td className="p-4 text-sm font-mono text-slate-600">{a.patient_uhid}</td>
                          <td className="p-4 text-sm font-medium text-slate-600">{a.admitting_doctor}</td>
                          <td className="p-4 text-sm font-medium text-slate-500">{new Date(a.admission_time).toLocaleString()}</td>
                          <td className="p-4 text-sm font-bold text-emerald-600">{a.status}</td>
                          <td className="p-4 text-right">
                             <button onClick={() => { 
                               ipdApi.getChecklist(a.admission_number)
                               .then(d => { if(d) setChecklistData(d); else setChecklistData({admission_number: a.admission_number}); setShowChecklistModal(a.admission_number); })
                               .catch(() => { setChecklistData({admission_number: a.admission_number}); setShowChecklistModal(a.admission_number); });
                             }} className="text-xs font-bold bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg hover:bg-purple-100">
                                Checklist
                             </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === "BEDS" && (
              <div className="grid grid-cols-4 gap-4">
                {beds.length === 0 ? (
                  <div className="col-span-4 p-8 text-center text-slate-400 font-medium border-2 border-dashed border-slate-200 rounded-2xl">
                    No bed master data found. Plz register beds in Wards Module.
                  </div>
                ) : (
                  beds.map(b => {
                    const status = b.status || 'Available';
                    return (
                      <div key={b.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col hover:border-blue-300 transition-colors">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="font-black text-slate-800">{b.bed_code}</div>
                            <div className="text-xs text-slate-500 font-bold">{b.bed_type}</div>
                          </div>
                          <span className={`text-[10px] uppercase font-black px-2 py-1 rounded-md border ${getBedStatusColor(status)}`}>
                            {status}
                          </span>
                        </div>
                        
                        {status === "cleaning" && (
                          <button onClick={() => markHousekeepingCleaned(b.id)} className="mt-auto pt-3 text-xs font-bold text-emerald-600 flex items-center justify-center gap-1 hover:text-emerald-700">
                            <CheckCircle2 size={14}/> Mark Cleaned
                          </button>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}

          </div>
        )}

      </div>

      {/* MODALS */}
      {showReqModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateRequest} className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-black text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-3 mb-4"><UserPlus size={22} className="text-blue-600"/> Initiate Admission Request</h3>
            
            <div ref={patientRef} className="relative mb-4">
              <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Select Patient</label>
              <div className="relative">
                <Search size={14} className="absolute left-3 top-3 text-slate-400"/>
                <input
                  value={selectedPatient ? `${selectedPatient.first_name} ${selectedPatient.last_name} (${selectedPatient.patient_uuid})` : patientSearch}
                  onChange={e => { setPatientSearch(e.target.value); setSelectedPatient(null); setShowPatientDropdown(true); }}
                  onFocus={() => setShowPatientDropdown(true)}
                  placeholder="Search patient by name or UHID..."
                  className="w-full p-2.5 pl-9 pr-8 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none"
                  required
                />
              </div>
              {showPatientDropdown && filteredPatients.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-48 overflow-y-auto">
                  {filteredPatients.map(p => (
                    <button key={p.id} type="button" onClick={() => { setSelectedPatient(p); setShowPatientDropdown(false); setPatientSearch(''); }}
                      className="w-full text-left px-4 py-2 hover:bg-blue-50 flex items-center justify-between text-sm border-b border-slate-50">
                      <div><span className="font-bold text-slate-800">{p.first_name} {p.last_name}</span><span className="text-[10px] text-slate-400 ml-2 font-mono">{p.patient_uuid}</span></div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {selectedPatient && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex gap-4 text-sm mb-4">
                <div><span className="text-slate-500 font-bold block text-[10px] uppercase">Gender</span><span className="font-medium text-slate-800">{selectedPatient.gender || '—'}</span></div>
                <div><span className="text-slate-500 font-bold block text-[10px] uppercase">DOB</span><span className="font-medium text-slate-800">{selectedPatient.dob || '—'}</span></div>
                <div><span className="text-slate-500 font-bold block text-[10px] uppercase">Phone</span><span className="font-medium text-slate-800">{selectedPatient.primary_phone || '—'}</span></div>
              </div>
            )}

            {!selectedPatient?.gender && <input name="gender" placeholder="Gender" className="w-full p-2.5 border rounded-lg text-sm hidden"/>}
            {!selectedPatient?.dob && <input type="date" name="date_of_birth" placeholder="DOB" className="w-full p-2.5 border rounded-lg text-sm hidden"/>}
            {!selectedPatient?.primary_phone && <input name="mobile_number" placeholder="Mobile" className="w-full p-2.5 border rounded-lg text-sm hidden"/>}

            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Admitting Dr.</label><input name="admitting_doctor" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-500" placeholder="e.g. Dr. House"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Treating Dr.</label><input name="treating_doctor" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-500" placeholder="e.g. Dr. Cuddy"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Specialty</label><input name="specialty" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-500" placeholder="e.g. Cardiology"/></div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Category</label>
                <select name="admission_category" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-500">
                  <option>Emergency</option><option>Planned Admission</option><option>Day Care Admission</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Source</label>
                <select name="admission_source" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-500">
                  <option>OPD</option><option>Emergency</option><option>Referral</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Pref. Bed Category</label>
                <select name="preferred_bed_category" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-500">
                  <option>General Ward</option><option>Semi-Private</option><option>Private Room</option><option>ICU</option>
                </select>
              </div>
            </div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">Expected Date</label><input type="datetime-local" name="expected_admission_date" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-500"/></div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">Reason</label><input name="reason_for_admission" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-500" placeholder="Clinical reason"/></div>

            <div className="flex justify-end gap-2 pt-4">
              <button type="button" onClick={() => setShowReqModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold cursor-pointer">Cancel</button>
              <button type="submit" disabled={!selectedPatient} className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white px-5 py-2 rounded-lg text-sm font-bold cursor-pointer transition-colors">Create Request</button>
            </div>
          </form>
        </div>
      )}

      {showAllocModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleAllocateBed} className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 space-y-4">
            <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><CheckCircle2 size={20} className="text-emerald-600"/> Allocate Bed</h3>
            <p className="text-xs text-slate-500">Approving admission and allocating a bed for request.</p>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Select Available Bed</label>
            <select name="bed_id" required className="w-full p-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:border-blue-500">
              <option value="">— Choose Bed —</option>
              {beds.filter(b => b.status === "available" || b.status === "cleaning").map(b => (
                <option key={b.id} value={b.bed_code}>{b.bed_code} - {b.bed_type}</option>
              ))}
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAllocModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold cursor-pointer">Cancel</button>
              <button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-bold cursor-pointer">Allocate</button>
            </div>
          </form>
        </div>
      )}

      {showEstimateModal && currentEstimate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-black text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-2"><CheckCircle2 size={20} className="text-amber-500"/> AI Cost Estimation</h3>
            <div>
              <p className="text-xs text-slate-500 uppercase font-bold mb-1">Request Overview</p>
              <div className="bg-slate-50 p-3 rounded-lg text-sm border border-slate-200">
                <div className="flex justify-between mb-1"><span className="text-slate-500">Patient UHID:</span><span className="font-bold">{showEstimateModal.uhid}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Bed Category:</span><span className="font-bold">{showEstimateModal.category}</span></div>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase font-bold mb-1">Projected Cost Variance</p>
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 p-4 rounded-xl">
                 <div className="text-center text-2xl font-black text-amber-700">
                   ₹{currentEstimate.estimated_cost_lower.toLocaleString()} <span className="text-amber-400 font-medium">to</span> ₹{currentEstimate.estimated_cost_upper.toLocaleString()}
                 </div>
                 <p className="text-[10px] text-center text-amber-600 mt-2 font-bold uppercase">Estimated baseline + room & board + expected tests</p>
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <button onClick={() => setShowEstimateModal(null)} className="px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg text-sm font-bold transition-colors">Close</button>
            </div>
          </div>
        </div>
      )}

      {showChecklistModal && checklistData && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-black text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-2"><ClipboardList size={20} className="text-purple-600"/> Admission Checklist</h3>
            <div className="space-y-3 pt-2">
              {[
                { id: "registration_completed", label: "Front-office Registration Finished" },
                { id: "identity_proof_verified", label: "Govt Identity Proof Verified" },
                { id: "consent_taken", label: "Admission Consent Signed" },
                { id: "deposit_collected", label: "Security Deposit Paid" }
              ].map(chk => (
                <div key={chk.id} className="flex items-center gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <input type="checkbox" checked={checklistData[chk.id]} id={chk.id} 
                     onChange={e => setChecklistData({...checklistData, [chk.id]: e.target.checked})}
                     className="w-5 h-5 text-purple-600 rounded border-slate-300 focus:ring-purple-500"/>
                  <label htmlFor={chk.id} className="text-sm font-bold text-slate-700 cursor-pointer select-none">{chk.label}</label>
                </div>
              ))}
            </div>
            
            <div className="flex justify-between items-center pt-4">
              {checklistData.is_complete ? (
                 <span className="text-emerald-600 font-bold flex items-center gap-1 text-sm"><Check size={16}/> Cleared for Ward Transport</span>
              ) : (
                 <span className="text-amber-500 font-bold flex items-center gap-1 text-sm"><AlertTriangle size={16}/> Clearance Pending</span>
              )}
              <div className="flex gap-2">
                <button onClick={() => setShowChecklistModal(null)} className="px-3 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg transition-colors">Cancel</button>
                <button onClick={() => {
                  ipdApi.updateChecklist(showChecklistModal, checklistData).then(()=>setShowChecklistModal(null));
                }} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-bold transition-colors">Save Details</button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
