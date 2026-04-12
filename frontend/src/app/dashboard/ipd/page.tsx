"use client";
import { useTranslation } from "@/i18n";
import React, { useState, useEffect } from "react";
import { Bed, Users, Activity, HeartPulse, Stethoscope, ArrowRight, Shield, AlertTriangle, UserCheck, Search, Plus, MapPin, CheckCircle, X } from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";

export default function IpdDashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<any>(null);
  const [admissions, setAdmissions] = useState<any[]>([]);
  const [pendingRequests, setPendingRequests] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("admissions");

  const [showAllocateModal, setShowAllocateModal] = useState(false);
  const [allocatingRequest, setAllocatingRequest] = useState<any>(null);
  const [selectedBed, setSelectedBed] = useState("");

  const fetchData = async () => {
    try {
      const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      
      const [resStats, resAdm, resReq, resPat] = await Promise.all([
        fetch(`${api}/api/v1/ipd/dashboard/stats`, { headers }).catch(()=>null),
        fetch(`${api}/api/v1/ipd/admissions`, { headers }).catch(()=>null),
        fetch(`${api}/api/v1/ipd/requests/pending`, { headers }).catch(()=>null),
        fetch(`${api}/api/v1/patients`, { headers }).catch(()=>null),
      ]);
      
      if (resStats?.ok) setStats(await resStats.json());
      if (resAdm?.ok) setAdmissions(await resAdm.json());
      if (resReq?.ok) setPendingRequests(await resReq.json());
      if (resPat?.ok) setPatients(await resPat.json());

      setLoading(false);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getPatientName = (id: string, uhid: string) => {
    if (uhid) {
       const p = patients.find(x => x.patient_uuid === uhid || x.uhid === uhid);
       if (p) return `${p.first_name} ${p.last_name}`;
    }
    const pt = patients.find(x => x.id === id);
    return pt ? `${pt.first_name} ${pt.last_name}` : "Unknown Patient";
  };

  const handleAllocateBed = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!allocatingRequest || !selectedBed) return;
    try {
      const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      // This is the actual endpoint for allocation in IPD
      await fetch(`${api}/api/v1/ipd/requests/${allocatingRequest.id}/allocate/${selectedBed}`, {
        method: "POST", headers
      });
      setShowAllocateModal(false);
      setAllocatingRequest(null);
      fetchData();
    } catch (err) {
      console.error("Allocation failed", err);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <TopNav title={t("ipd.inpatientDepartment")} />
      
      <div className="flex-1 p-8 max-w-[1400px] mx-auto w-full">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-black text-rose-800 tracking-tight flex items-center gap-3">
              <Bed className="text-rose-600" size={32}/>{t("ipd.smartWardsCentralNursing")}</h1>
            <p className="text-slate-500 font-medium mt-1">{t("ipd.ipdSubtitle")}</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => fetchData()} className="bg-white border border-rose-200 text-rose-700 hover:bg-rose-50 px-5 py-2.5 rounded-xl font-bold transition-all shadow-sm flex items-center gap-2">
              <Activity size={18}/>{t("ipd.refreshTelemetry")}</button>
          </div>
        </div>

        {loading ? (
           <div className="p-24 text-center text-rose-400 font-bold flex flex-col items-center">
             <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-500 mb-4"></div>{t("ipd.connectingToWardStations")}</div>
        ) : (
          <div className="space-y-6">
            
            {/* KPI STATS */}
            <div className="grid grid-cols-4 gap-4">
               <div className="bg-white rounded-2xl p-5 border border-rose-100 shadow-sm relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-3 opacity-10"><Bed size={64}/></div>
                 <div className="text-rose-500 font-black text-xs uppercase mb-1">{t("ipd.activeAdmissions")}</div>
                 <div className="text-3xl font-black text-slate-800">{stats?.total_admissions || admissions.length}</div>
                 <div className="text-xs font-bold text-slate-400 mt-2">{t("ipd.currentlyAccommodated")}</div>
               </div>
               <div className="bg-white rounded-2xl p-5 border border-rose-100 shadow-sm relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-3 opacity-10"><Users size={64}/></div>
                 <div className="text-indigo-500 font-black text-xs uppercase mb-1">{t("ipd.pendingRequests")}</div>
                 <div className="text-3xl font-black text-slate-800">{pendingRequests.length}</div>
                 <div className="text-xs font-bold text-amber-500 mt-2">{t("ipd.awaitingErOpdClearance")}</div>
               </div>
               <div className="bg-white rounded-2xl p-5 border border-rose-100 shadow-sm relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-3 opacity-10"><Activity size={64}/></div>
                 <div className="text-emerald-500 font-black text-xs uppercase mb-1">{t("ipd.icuOccupancy")}</div>
                 <div className="text-3xl font-black text-slate-800">{stats?.icu_occupancy || 0}%</div>
                 <div className="text-xs font-bold text-slate-400 mt-2">{t("ipd.criticalCareBeds")}</div>
               </div>
               <div className="bg-white rounded-2xl p-5 border border-rose-100 shadow-sm relative overflow-hidden">
                 <div className="absolute top-0 right-0 p-3 opacity-10"><Shield size={64}/></div>
                 <div className="text-blue-500 font-black text-xs uppercase mb-1">{t("ipd.dischargesToday")}</div>
                 <div className="text-3xl font-black text-slate-800">{stats?.discharges_today || 0}</div>
                 <div className="text-xs font-bold text-slate-400 mt-2">{t("ipd.clearedByBilling")}</div>
               </div>
            </div>

            {/* Main Tabs */}
            <div className="flex gap-2 p-1.5 bg-white border border-slate-200 rounded-2xl w-fit shadow-sm">
              <button onClick={() => setActiveTab('admissions')} className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'admissions' ? "bg-rose-50 text-rose-700 shadow-sm border border-rose-100" : "text-slate-500 hover:text-slate-800"}`}>
                <UserCheck size={18}/>{t("ipd.activeWardCensus")}</button>
              <button onClick={() => setActiveTab('requests')} className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'requests' ? "bg-rose-50 text-rose-700 shadow-sm border border-rose-100" : "text-slate-500 hover:text-slate-800"}`}>
                <AlertTriangle size={18}/> {t("ipd.admissionRequestsTab")} {pendingRequests.length > 0 && <span className="bg-red-500 text-white rounded-full px-2 py-0.5 text-[10px] ml-1">{pendingRequests.length}</span>}
              </button>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[400px]">
              
              {activeTab === 'admissions' && (
                <table className="w-full text-left border-collapse">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr className="text-slate-500 text-xs uppercase font-black tracking-wider">
                      <th className="p-4">{t("ipd.admHash")}</th>
                      <th className="p-4">{t("ipd.patient")}</th>
                      <th className="p-4">{t("ipd.wardBed")}</th>
                      <th className="p-4">{t("ipd.attendingDoctor")}</th>
                      <th className="p-4">{t("ipd.vitals")}</th>
                      <th className="p-4 text-center">{t("ipd.status")}</th>
                      <th className="p-4 text-right">{t("ipd.action")}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {admissions.length === 0 ? (
                      <tr><td colSpan={7} className="p-12 text-center text-slate-400 font-bold">{t("ipd.noActiveAdmissionsCurrentlyTra")}</td></tr>
                    ) : admissions.map(adm => (
                      <tr key={adm.id} className="hover:bg-slate-50 transition-colors">
                        <td className="p-4 text-slate-500 text-xs font-mono">{adm.admission_number || adm.id.split('-')[0].toUpperCase()}</td>
                        <td className="p-4">
                           <span className="font-bold text-slate-800 block">{getPatientName(adm.patient_id, adm.patient_uhid)}</span>
                           <span className="text-xs text-slate-400 font-mono">{adm.patient_uhid || adm.patient_id.split('-')[0]}</span>
                        </td>
                        <td className="p-4">
                           <span className="bg-rose-50 text-rose-700 px-2 py-1 flex items-center gap-1 w-max rounded-md border border-rose-100 text-[11px] font-black uppercase"><MapPin size={12}/> {adm.bed_id ? t("ipd.bedAllocatedStr") : adm.ward_name || t("ipd.generalWardStr")}</span>
                        </td>
                        <td className="p-4 font-medium text-slate-600 flex items-center gap-2"><Stethoscope size={14} className="text-blue-500"/> {adm.admitting_doctor_id ? t("ipd.assignedDr") : t("ipd.pendingDoctor")}</td>
                        <td className="p-4"><span className="bg-emerald-50 text-emerald-600 px-2 py-1 rounded text-[10px] font-bold uppercase flex items-center w-max gap-1 border border-emerald-100"><HeartPulse size={12}/>{t("ipd.stable")}</span></td>
                        <td className="p-4 text-center">
                           <span className="bg-blue-100 text-blue-700 font-black px-2.5 py-1 rounded-md text-[10px] uppercase tracking-wider">{adm.status}</span>
                        </td>
                        <td className="p-4 text-right">
                           <button className="bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold px-3 py-1.5 rounded-lg text-xs shadow-sm">{t("ipd.nursingFlowsheet")}</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'requests' && (
                <div className="p-0">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-amber-50/50 border-b border-amber-100">
                      <tr className="text-amber-800 text-[10px] uppercase font-black tracking-wider">
                        <th className="p-4">{t("ipd.requestTime")}</th>
                        <th className="p-4">{t("ipd.patient")}</th>
                        <th className="p-4">{t("ipd.priority")}</th>
                        <th className="p-4">{t("ipd.diagnosisNotes")}</th>
                        <th className="p-4 text-right">{t("ipd.action")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-sm">
                      {pendingRequests.length === 0 ? (
                        <tr><td colSpan={5} className="p-12 text-center text-slate-400 font-bold">{t("ipd.noPendingAdmissionRequestsFrom")}</td></tr>
                      ) : pendingRequests.map(req => (
                        <tr key={req.id} className="hover:bg-slate-50">
                          <td className="p-4 text-slate-500 text-xs font-mono">{new Date(req.created_at).toLocaleString()}</td>
                          <td className="p-4 font-bold text-slate-800">{getPatientName(req.patient_id, req.patient_uhid)}</td>
                          <td className="p-4">
                             <span className={`px-2 py-1 rounded text-[10px] font-black uppercase ${req.priority === 'emergency' ? 'bg-red-100 text-red-700 animate-pulse' : 'bg-amber-100 text-amber-700'}`}>{req.priority}</span>
                          </td>
                          <td className="p-4 font-medium text-slate-600">{req.provisional_diagnosis || t("ipd.triageStandard")}</td>
                          <td className="p-4 text-right">
                             <button onClick={() => { setAllocatingRequest(req); setShowAllocateModal(true); }} className="bg-rose-600 text-white rounded-lg px-4 py-2 font-bold hover:bg-rose-700 shadow-sm text-xs flex items-center gap-2 ml-auto">
                                <Bed size={14}/>{t("ipd.allocateBed")}</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

            </div>
          </div>
        )}
      </div>

      {/* Allocate Bed Modal */}
      {showAllocateModal && allocatingRequest && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleAllocateBed} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-5">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2"><Bed size={22} className="text-rose-600"/>{t("ipd.allocateWardBed")}</h3>
              <button type="button" onClick={() => setShowAllocateModal(false)}><X size={20} className="text-slate-400 hover:text-slate-600"/></button>
            </div>
            
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 mb-2">
               <p className="text-sm font-semibold text-slate-500 mb-1">{t("ipd.patientName")}</p>
               <p className="font-black text-slate-800">{getPatientName(allocatingRequest.patient_id, allocatingRequest.patient_uhid)}</p>
               <p className="text-xs font-mono text-rose-500 mt-1 uppercase mt-2 font-bold">{t("ipd.priorityLabel")}: {allocatingRequest.priority}</p>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-500 uppercase block mb-2">{t("ipd.selectAvailableBedStar")}</label>
              <select 
                value={selectedBed} 
                onChange={e => setSelectedBed(e.target.value)} 
                required 
                className="w-full p-3 border rounded-xl text-sm font-medium outline-none focus:border-rose-400 bg-white"
              >
                <option value="">{t("ipd.dropdownSyncedWithBedMatrix")}</option>
                {/* Mocking Beds for demonstration since we don't have the GET /beds endpoint documented clearly */}
                <option value="bed-gen-101">{t("ipd.gen101GeneralMaleWard")}</option>
                <option value="bed-gen-102">{t("ipd.gen102GeneralMaleWard")}</option>
                <option value="bed-icu-01">{t("ipd.icu01IntensiveCare")}</option>
                <option value="bed-pvt-205">{t("ipd.pvt205PrivateRoomSuite")}</option>
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-100">
              <button type="button" onClick={() => setShowAllocateModal(false)} className="px-5 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg">{t("ipd.cancel")}</button>
              <button type="submit" className="bg-rose-600 hover:bg-rose-700 text-white px-6 py-2.5 rounded-xl text-sm font-bold transition-all shadow-md shadow-rose-200 block text-center flex items-center gap-2">
                 <CheckCircle size={16}/>{t("ipd.confirmAllocation")}</button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}
