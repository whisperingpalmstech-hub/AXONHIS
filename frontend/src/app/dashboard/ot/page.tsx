"use client";
import React, { useState, useEffect } from "react";
import { Activity, Scissors, Calendar, User, Clock, CheckCircle, AlertTriangle, Shield, MapPin, Search, Plus, X } from "lucide-react";
import { useTranslation } from "@/i18n";
import { TopNav } from "@/components/ui/TopNav";

export default function OTDashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<any>(null);
  const [rooms, setRooms] = useState<any[]>([]);
  const [schedules, setSchedules] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("schedules");

  // Modal State
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [selectedRoomId, setSelectedRoomId] = useState("");
  const [surgeryName, setSurgeryName] = useState("");
  const [surgeonName, setSurgeonName] = useState("");

  const fetchData = async () => {
    try {
      const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

      const [resStats, resRooms, resSched, resPat] = await Promise.all([
        fetch(`${api}/api/v1/ot-enhanced/dashboard`, { headers }).catch(() => null),
        fetch(`${api}/api/v1/ot-enhanced/rooms`, { headers }).catch(() => null),
        fetch(`${api}/api/v1/ot-enhanced/schedules`, { headers }).catch(() => null),
        fetch(`${api}/api/v1/patients`, { headers }).catch(() => null)
      ]);

      if (resStats?.ok) setStats(await resStats.json());
      if (resRooms?.ok) setRooms(await resRooms.json());
      if (resSched?.ok) setSchedules(await resSched.json());
      if (resPat?.ok) setPatients(await resPat.json());
      
      setLoading(false);
    } catch (e) {
      console.error("Failed to load OT data", e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeedRooms = async () => {
    const headers = { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
    const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
    await fetch(`${api}/api/v1/ot-enhanced/rooms`, {
      method: 'POST', headers, body: JSON.stringify({ room_code: "OT-A", room_name: "General Surgical Suite", is_laminar_flow: true, has_c_arm: true })
    });
    await fetch(`${api}/api/v1/ot-enhanced/rooms`, {
      method: 'POST', headers, body: JSON.stringify({ room_code: "OT-B", room_name: "Ortho & Trauma", room_type: "specialized", has_laser: true })
    });
    fetchData();
  };

  const handleCreateSurgery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId || !selectedRoomId || !surgeryName) return;

    try {
      const headers = { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

      const patient = patients.find(p => p.id === selectedPatientId);
      if (!patient) return;

      const payload = {
        ot_room_id: selectedRoomId,
        patient_id: patient.id,
        patient_name: `${patient.first_name} ${patient.last_name}`,
        patient_uhid: patient.patient_uuid,
        surgery_name: surgeryName,
        primary_surgeon_name: surgeonName || "Dr. Assigned Admin",
        scheduled_date: new Date().toISOString()
      };

      const res = await fetch(`${api}/api/v1/ot-enhanced/schedules`, {
        method: "POST", headers, body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setShowScheduleModal(false);
        fetchData();
        alert(t("ot.surgeryScheduledSuccessfully"));
      } else {
        alert(t("ot.scheduleError"));
      }
    } catch (err) {
      console.error(err);
      alert(t("ot.scheduleError"));
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <TopNav title={t("ot.operatingTheatre")} />
      
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-black text-rose-800 tracking-tight flex items-center gap-3">
              <Scissors className="text-rose-500" size={32}/> {t("ot.surgeonCommandCenter")}
            </h1>
            <p className="text-rose-500 font-medium mt-1">{t("ot.otSubtitle")}</p>
          </div>
          <div className="flex gap-3">
            <button onClick={handleSeedRooms} className="bg-white border border-rose-200 text-rose-700 hover:bg-rose-50 px-4 py-2 rounded-xl font-bold text-sm shadow-sm transition-colors flex items-center gap-2">
               <Shield size={16}/> {t("ot.constructOtRooms")}
            </button>
            <button onClick={() => setShowScheduleModal(true)} className="bg-rose-600 hover:bg-rose-700 text-white px-5 py-2.5 rounded-xl font-bold transition-all shadow-md shadow-rose-200 flex items-center gap-2">
               <Plus size={18}/> {t("ot.scheduleSurgery")}
            </button>
          </div>
        </div>

        {loading ? (
           <div className="flex flex-col items-center justify-center p-24 text-rose-400 font-bold space-y-4">
             <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-500"></div>
             {t("ot.checkingOt")}
           </div>
        ) : (
          <div className="space-y-6">
            
            {/* KPI STATS */}
            <div className="grid grid-cols-4 gap-4">
               <div className="bg-white rounded-2xl p-5 border border-rose-100 shadow-sm relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-3 opacity-10"><Activity size={64}/></div>
                 <div className="text-rose-500 font-black text-xs uppercase mb-1">{t("ot.totalRooms")}</div>
                 <div className="text-3xl font-black text-slate-800">{stats?.total_rooms || rooms.length}</div>
                 <div className="text-xs font-bold text-emerald-500 mt-2">{stats?.rooms_available || rooms.filter(r => r.status === 'available').length} {t("ot.available")}</div>
               </div>
               <div className="bg-white rounded-2xl p-5 border border-rose-100 shadow-sm relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-3 opacity-10"><Calendar size={64}/></div>
                 <div className="text-indigo-500 font-black text-xs uppercase mb-1">{t("ot.todaysSurgeries")}</div>
                 <div className="text-3xl font-black text-slate-800">{stats?.todays_surgeries || schedules.length}</div>
               </div>
               <div className="bg-white rounded-2xl p-5 border border-rose-100 shadow-sm relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-3 opacity-10"><Clock size={64}/></div>
                 <div className="text-amber-500 font-black text-xs uppercase mb-1">{t("ot.inProgress")}</div>
                 <div className="text-3xl font-black text-slate-800">{stats?.in_progress || schedules.filter(s => s.status === 'incision' || s.status === 'anesthesia_start').length}</div>
               </div>
               <div className="bg-white rounded-2xl p-5 border border-rose-100 shadow-sm relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-3 opacity-10"><CheckCircle size={64}/></div>
                 <div className="text-emerald-500 font-black text-xs uppercase mb-1">{t("ot.completed")}</div>
                 <div className="text-3xl font-black text-slate-800">{stats?.completed_today || schedules.filter(s => s.status === 'completed' || s.status === 'post_op').length}</div>
               </div>
            </div>

            {/* Main Workspace */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[500px]">
              
              <div className="flex gap-0 border-b border-slate-200 bg-slate-50">
                <button onClick={() => setActiveTab('schedules')} className={`flex-1 py-4 text-sm font-bold flex justify-center items-center gap-2 transition-colors ${activeTab === 'schedules' ? 'bg-white text-rose-600 border-b-2 border-rose-600' : 'text-slate-500 hover:text-slate-800'}`}>
                  <Calendar size={16}/> {t("ot.dailySurgicalSchedule")}
                </button>
                <button onClick={() => setActiveTab('rooms')} className={`flex-1 py-4 text-sm font-bold flex justify-center items-center gap-2 transition-colors ${activeTab === 'rooms' ? 'bg-white text-rose-600 border-b-2 border-rose-600' : 'text-slate-500 hover:text-slate-800'}`}>
                  <MapPin size={16}/> {t("ot.otAvailabilityMatrix")}
                </button>
              </div>

              {activeTab === 'schedules' && (
                <div className="p-0">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="bg-rose-50/50 border-b border-rose-100 text-rose-900 text-[10px] uppercase font-black tracking-wider">
                        <th className="p-4">{t("ot.time")}</th>
                        <th className="p-4">{t("ot.patient")}</th>
                        <th className="p-4">{t("ot.surgery")}</th>
                        <th className="p-4">{t("ot.surgeon")}</th>
                        <th className="p-4 text-center">{t("ot.room")}</th>
                        <th className="p-4 text-center">{t("ot.status")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-sm">
                      {schedules.length === 0 ? (
                        <tr><td colSpan={6} className="p-12 text-center text-slate-400 font-bold">{t("ot.noSurgeries")}</td></tr>
                      ) : schedules.map(s => (
                        <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                          <td className="p-4 text-slate-500 font-mono text-xs">{new Date(s.scheduled_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                          <td className="p-4">
                            <span className="font-bold text-slate-800 block">{s.patient_name}</span>
                            <span className="text-xs text-slate-400 font-mono">{s.patient_uhid}</span>
                          </td>
                          <td className="p-4 font-semibold text-rose-900">{s.surgery_name}</td>
                          <td className="p-4 text-slate-600 font-medium">{s.primary_surgeon_name}</td>
                          <td className="p-4 text-center">
                            {(() => {
                               const r = rooms.find(x => x.id === s.ot_room_id);
                               return r ? <span className="bg-slate-200 text-slate-700 px-2 py-1 rounded text-xs font-black">{r.room_code}</span> : '—';
                            })()}
                          </td>
                          <td className="p-4 text-center">
                            <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider ${
                              s.status === 'scheduled' ? 'bg-amber-100 text-amber-700' : 
                              s.status === 'incision' || s.status.includes('in_') ? 'bg-red-100 text-red-700 animate-pulse' : 
                              'bg-emerald-100 text-emerald-700'
                            }`}>
                              {s.status.replace('_', ' ')}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'rooms' && (
                <div className="p-8 grid grid-cols-3 gap-6">
                  {rooms.length === 0 ? (
                    <div className="col-span-3 text-center p-12 text-slate-400 font-bold">{t("ot.noOtRooms")}</div>
                  ) : rooms.map(r => (
                    <div key={r.id} className="border-2 border-slate-100 rounded-2xl p-5 hover:border-rose-200 transition-colors">
                      <div className="flex justify-between items-start mb-4">
                        <div className="w-12 h-12 rounded-xl bg-rose-100 flex items-center justify-center text-rose-600">
                           <Scissors size={24}/>
                        </div>
                        <span className={`px-2.5 py-1 text-[10px] font-black uppercase rounded-lg ${
                          r.status === 'available' ? 'bg-emerald-100 text-emerald-700' : 
                          r.status === 'occupied' ? 'bg-red-100 text-red-700 animate-pulse' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {r.status}
                        </span>
                      </div>
                      <h3 className="font-black text-lg text-slate-800">{r.room_code}</h3>
                      <p className="text-sm font-semibold text-slate-500 mb-3">{r.room_name}</p>
                      
                      <div className="flex flex-wrap gap-2 mt-2">
                        {r.is_laminar_flow && <span className="bg-blue-50 text-blue-600 text-[10px] font-bold px-2 py-1 rounded">{t("ot.laminarFlow")}</span>}
                        {r.has_c_arm && <span className="bg-purple-50 text-purple-600 text-[10px] font-bold px-2 py-1 rounded">{t("ot.cArmEq")}</span>}
                        {r.has_laser && <span className="bg-amber-50 text-amber-600 text-[10px] font-bold px-2 py-1 rounded">{t("ot.laserSuite")}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}

            </div>
          </div>
        )}
      </div>

      {/* SCHEDULE MODAL */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateSurgery} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-5">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2"><Calendar size={22} className="text-rose-600"/> {t("ot.blockOt")}</h3>
              <button type="button" onClick={() => setShowScheduleModal(false)}><X size={20} className="text-slate-400 hover:text-slate-600"/></button>
            </div>
            
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase">{t("ot.selectLivePatient")}</label>
              <select 
                value={selectedPatientId} 
                onChange={e => setSelectedPatientId(e.target.value)} 
                required 
                className="w-full mt-1 p-2.5 border rounded-lg text-sm font-medium outline-none focus:border-rose-400 bg-slate-50"
              >
                <option value="">{t("ot.corePatientRegistry")}</option>
                {patients.map(p => (
                  <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.patient_uuid})</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase">{t("ot.selectOtRoom")}</label>
                <select 
                  value={selectedRoomId} 
                  onChange={e => setSelectedRoomId(e.target.value)} 
                  required 
                  className="w-full mt-1 p-2.5 border rounded-lg text-sm font-medium outline-none focus:border-rose-400 bg-slate-50"
                >
                  <option value="">{t("ot.availableSuites")}</option>
                  {rooms.map(r => (
                    <option key={r.id} value={r.id}>{r.room_code} - {r.room_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase">{t("ot.primarySurgeon")}</label>
                <input 
                  type="text" 
                  value={surgeonName} 
                  onChange={e => setSurgeonName(e.target.value)} 
                  placeholder={t("ot.egDrHouse")}
                  required 
                  className="w-full mt-1 p-2.5 border rounded-lg text-sm font-medium outline-none focus:border-rose-400 bg-slate-50"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-500 uppercase">{t("ot.surgeryProcedure")}</label>
              <input 
                type="text" 
                value={surgeryName} 
                onChange={e => setSurgeryName(e.target.value)} 
                placeholder={t("ot.egAppendectomy")}
                required 
                className="w-full mt-1 p-2.5 border rounded-lg text-sm font-medium outline-none focus:border-rose-400 bg-slate-50"
              />
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-100">
              <button type="button" onClick={() => setShowScheduleModal(false)} className="px-5 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg">{t("ot.cancel")}</button>
              <button type="submit" className="bg-rose-600 hover:bg-rose-700 text-white px-6 py-2 rounded-lg text-sm font-bold transition-colors shadow-md shadow-rose-200 block text-center">{t("ot.commitToBoard")}</button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}
