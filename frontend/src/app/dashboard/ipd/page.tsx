"use client";
import { useTranslation } from "@/i18n";
import React, { useState, useEffect, useCallback } from "react";
import {
  Bed, Users, Activity, HeartPulse, Stethoscope, ArrowRight, Shield,
  AlertTriangle, UserCheck, Search, Plus, MapPin, CheckCircle, X,
  BarChart3, Clock, LogOut, FileText, DollarSign, TrendingUp, RefreshCw,
  Filter, ChevronDown, Eye, Building2, Layers, LayoutGrid
} from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { ipdApi } from "@/lib/ipd-api";

const API = () => process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
const headers = () => ({
  "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
  "Content-Type": "application/json",
});

// --- Reusable Components ---
function StatCard({ icon: Icon, label, value, color, sub }: any) {
  const colors: Record<string, string> = {
    rose: "text-rose-500 bg-rose-50 border-rose-100",
    indigo: "text-indigo-500 bg-indigo-50 border-indigo-100",
    emerald: "text-emerald-500 bg-emerald-50 border-emerald-100",
    blue: "text-blue-500 bg-blue-50 border-blue-100",
    amber: "text-amber-500 bg-amber-50 border-amber-100",
    violet: "text-violet-500 bg-violet-50 border-violet-100",
  };
  const c = colors[color] || colors.rose;
  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm relative overflow-hidden hover:shadow-md transition-shadow group">
      <div className="absolute top-0 right-0 p-3 opacity-[0.06] group-hover:opacity-[0.1] transition-opacity"><Icon size={72}/></div>
      <div className={`font-black text-xs uppercase mb-1.5 tracking-wider ${c.split(" ")[0]}`}>{label}</div>
      <div className="text-3xl font-black text-slate-800">{value}</div>
      {sub && <div className="text-[11px] font-bold text-slate-400 mt-2">{sub}</div>}
    </div>
  );
}

function TabButton({ label, active, onClick, icon: Icon, badge }: any) {
  return (
    <button onClick={onClick}
      className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all whitespace-nowrap ${
        active ? "bg-rose-50 text-rose-700 shadow-sm border border-rose-100" : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
      }`}>
      {Icon && <Icon size={16}/>}
      {label}
      {badge !== undefined && badge > 0 && (
        <span className="bg-red-500 text-white rounded-full px-2 py-0.5 text-[10px] ml-1 font-black">{badge}</span>
      )}
    </button>
  );
}

function BedStatusDot({ status }: { status: string }) {
  const map: Record<string, string> = {
    available: "bg-emerald-500", occupied: "bg-rose-500",
    cleaning: "bg-amber-400", maintenance: "bg-slate-400", reserved: "bg-blue-400",
  };
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${map[status] || "bg-slate-300"}`}/>;
}

function Badge({ text, type = "default" }: { text: string; type?: string }) {
  const map: Record<string, string> = {
    success: "bg-emerald-50 text-emerald-700 border-emerald-100",
    danger: "bg-red-50 text-red-700 border-red-100",
    warning: "bg-amber-50 text-amber-700 border-amber-100",
    info: "bg-blue-50 text-blue-700 border-blue-100",
    default: "bg-slate-100 text-slate-700 border-slate-200",
    purple: "bg-violet-50 text-violet-700 border-violet-100",
  };
  return <span className={`px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border ${map[type] || map.default}`}>{text}</span>;
}

// --- Main Component ---
export default function IpdDashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<any>(null);
  const [admissions, setAdmissions] = useState<any[]>([]);
  const [pendingRequests, setPendingRequests] = useState<any[]>([]);
  const [bedGrid, setBedGrid] = useState<any[]>([]);
  const [dischargedPatients, setDischargedPatients] = useState<any[]>([]);
  const [pendingDischarges, setPendingDischarges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("census");

  // Filters
  const [wardFilter, setWardFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals
  const [showAllocateModal, setShowAllocateModal] = useState(false);
  const [allocatingRequest, setAllocatingRequest] = useState<any>(null);
  const [selectedBed, setSelectedBed] = useState("");
  const [availableBeds, setAvailableBeds] = useState<any[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const h = headers();
      const api = API();
      const [resStats, resAdm, resReq, resBeds, resDischarged, resPendDis] = await Promise.all([
        fetch(`${api}/api/v1/ipd/dashboard/stats-extended`, { headers: h }).catch(() => null),
        fetch(`${api}/api/v1/ipd/admissions`, { headers: h }).catch(() => null),
        fetch(`${api}/api/v1/ipd/requests/pending`, { headers: h }).catch(() => null),
        fetch(`${api}/api/v1/ipd/bed-grid`, { headers: h }).catch(() => null),
        fetch(`${api}/api/v1/ipd/discharged-patients`, { headers: h }).catch(() => null),
        fetch(`${api}/api/v1/ipd/pending-discharges`, { headers: h }).catch(() => null),
      ]);
      if (resStats?.ok) setStats(await resStats.json());
      if (resAdm?.ok) setAdmissions(await resAdm.json());
      if (resReq?.ok) setPendingRequests(await resReq.json());
      if (resBeds?.ok) setBedGrid(await resBeds.json());
      if (resDischarged?.ok) setDischargedPatients(await resDischarged.json());
      if (resPendDis?.ok) setPendingDischarges(await resPendDis.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Filter available beds for modal
  useEffect(() => {
    setAvailableBeds(bedGrid.filter(b => b.status === "available"));
  }, [bedGrid]);

  const handleAllocateBed = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!allocatingRequest || !selectedBed) return;
    
    const fallbackAdm = {
      id: Date.now().toString(),
      admission_number: `IPD-ADM-2026-${Math.floor(Math.random() * 899999 + 100000)}`,
      patient_uhid: allocatingRequest.patient_uhid,
      bed_uuid: selectedBed,
      status: "ADMITTED"
    };

    try {
      await ipdApi.allocateBed(allocatingRequest.id, selectedBed);
      fetchData();
      alert("Bed allocated successfully");
    } catch (err: any) { 
      console.error(err);
      alert("Allocation failed.");
    } finally {
      setShowAllocateModal(false);
      setAllocatingRequest(null);
      setSelectedBed("");
    }
  };

  // Group beds by ward for the grid
  const bedsByWard = bedGrid.reduce((acc: Record<string, any[]>, bed) => {
    const key = bed.ward_name || "Unknown";
    if (!acc[key]) acc[key] = [];
    acc[key].push(bed);
    return acc;
  }, {});

  // Filter helpers
  const filteredAdmissions = admissions.filter(a => {
    if (wardFilter && a.ward_id !== wardFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (a.admission_number || "").toLowerCase().includes(q)
        || (a.patient_uhid || "").toLowerCase().includes(q);
    }
    return true;
  });

  const uniqueWards = [...new Set(bedGrid.map(b => b.ward_name).filter(Boolean))];

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <TopNav title={t("ipd.inpatientDepartment")} />

      <div className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8 max-w-[1600px] mx-auto w-full space-y-6">

          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl lg:text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
                <div className="p-2 bg-rose-100 rounded-xl"><Bed className="text-rose-600" size={24}/></div>
                {t("ipd.smartWardsCentralNursing")}
              </h1>
              <p className="text-slate-500 font-medium mt-1 text-sm">{t("ipd.ipdSubtitle")}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={fetchData}
                className="bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 px-4 py-2.5 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center gap-2">
                <RefreshCw size={16} className={loading ? "animate-spin" : ""}/> Refresh
              </button>
            </div>
          </div>

          {loading ? (
            <div className="p-24 text-center text-rose-400 font-bold flex flex-col items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-500 mb-4"></div>
              {t("ipd.connectingToWardStations")}
            </div>
          ) : (
            <>
              {/* Extended KPI Stats — 6 cards */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                <StatCard icon={Bed} label="Total Beds" value={stats?.total_beds || bedGrid.length} color="rose"
                  sub={`${stats?.occupancy_rate || 0}% Occupancy`}/>
                <StatCard icon={Activity} label="Occupied" value={stats?.occupied_beds || bedGrid.filter(b=>b.status==="occupied").length} color="indigo"
                  sub="Currently In Use"/>
                <StatCard icon={CheckCircle} label="Available" value={stats?.available_beds || bedGrid.filter(b=>b.status==="available").length} color="emerald"
                  sub="Ready for Admission"/>
                <StatCard icon={Users} label="Pending Requests" value={stats?.pending_requests || pendingRequests.length} color="amber"
                  sub="Awaiting Bed Allocation"/>
                <StatCard icon={LogOut} label="Pending Discharge" value={stats?.pending_discharges || pendingDischarges.length} color="violet"
                  sub="Clearance Required"/>
                <StatCard icon={TrendingUp} label="Discharged Today" value={stats?.discharges_today || 0} color="blue"
                  sub={`Avg LOS: ${stats?.avg_length_of_stay || '—'} days`}/>
              </div>

              {/* Occupancy Progress Bar */}
              <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Bed Occupancy Overview</span>
                  <span className="text-sm font-bold text-slate-700">{stats?.occupancy_rate || 0}%</span>
                </div>
                <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex">
                  <div className="h-full bg-rose-500 transition-all rounded-l-full" style={{ width: `${((stats?.occupied_beds || 0) / Math.max(stats?.total_beds || 1, 1)) * 100}%` }}/>
                  <div className="h-full bg-amber-400 transition-all" style={{ width: `${((stats?.housekeeping_beds || 0) / Math.max(stats?.total_beds || 1, 1)) * 100}%` }}/>
                  <div className="h-full bg-blue-400 transition-all" style={{ width: `${((stats?.reserved_beds || 0) / Math.max(stats?.total_beds || 1, 1)) * 100}%` }}/>
                  <div className="h-full bg-slate-300 transition-all" style={{ width: `${((stats?.maintenance_beds || 0) / Math.max(stats?.total_beds || 1, 1)) * 100}%` }}/>
                </div>
                <div className="flex gap-5 mt-2.5 flex-wrap">
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"/> Occupied ({stats?.occupied_beds || 0})</div>
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"/> Available ({stats?.available_beds || 0})</div>
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500"><span className="w-2.5 h-2.5 rounded-full bg-amber-400"/> Housekeeping ({stats?.housekeeping_beds || 0})</div>
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500"><span className="w-2.5 h-2.5 rounded-full bg-blue-400"/> Reserved ({stats?.reserved_beds || 0})</div>
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500"><span className="w-2.5 h-2.5 rounded-full bg-slate-300"/> Maintenance ({stats?.maintenance_beds || 0})</div>
                </div>
              </div>

              {/* Tab Navigation */}
              <div className="flex gap-1.5 p-1.5 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-x-auto">
                <TabButton label="Active Census" active={activeTab==="census"} onClick={()=>setActiveTab("census")} icon={UserCheck} badge={admissions.length}/>
                <TabButton label="Bed Grid" active={activeTab==="beds"} onClick={()=>setActiveTab("beds")} icon={LayoutGrid}/>
                <TabButton label="Admission Requests" active={activeTab==="requests"} onClick={()=>setActiveTab("requests")} icon={AlertTriangle} badge={pendingRequests.length}/>
                <TabButton label="Pending Discharge" active={activeTab==="pendingDis"} onClick={()=>setActiveTab("pendingDis")} icon={Clock} badge={pendingDischarges.length}/>
                <TabButton label="Discharged" active={activeTab==="discharged"} onClick={()=>setActiveTab("discharged")} icon={LogOut}/>
              </div>

              {/* Filter Bar */}
              {(activeTab === "census" || activeTab === "beds") && (
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="relative flex-1 min-w-[200px] max-w-md">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/>
                    <input type="text" placeholder="Search by Admission #, UHID, or Patient..."
                      value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:border-rose-300 bg-white"/>
                  </div>
                  <select value={wardFilter} onChange={e => setWardFilter(e.target.value)}
                    className="px-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:border-rose-300 bg-white min-w-[160px]">
                    <option value="">All Wards</option>
                    {uniqueWards.map(w => <option key={w} value={w}>{w}</option>)}
                  </select>
                  {activeTab === "beds" && (
                    <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
                      className="px-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:border-rose-300 bg-white min-w-[160px]">
                      <option value="">All Statuses</option>
                      <option value="available">Available</option>
                      <option value="occupied">Occupied</option>
                      <option value="cleaning">Housekeeping</option>
                      <option value="maintenance">Maintenance</option>
                    </select>
                  )}
                </div>
              )}

              {/* Content Area */}
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[400px]">

                {/* === Active Census Tab === */}
                {activeTab === "census" && (
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr className="text-slate-500 text-[10px] uppercase font-black tracking-wider">
                        <th className="p-4">Admission #</th>
                        <th className="p-4">Patient (UHID)</th>
                        <th className="p-4">Ward / Bed</th>
                        <th className="p-4">Doctor</th>
                        <th className="p-4">Admitted</th>
                        <th className="p-4 text-center">Status</th>
                        <th className="p-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {filteredAdmissions.length === 0 ? (
                        <tr><td colSpan={7} className="p-16 text-center text-slate-400 font-bold">
                          <div className="flex flex-col items-center gap-2">
                            <Bed size={40} className="text-slate-200"/>
                            <span>No active admissions found</span>
                          </div>
                        </td></tr>
                      ) : filteredAdmissions.map(adm => (
                        <tr key={adm.id || adm.admission_number} className="hover:bg-slate-50/50 transition-colors">
                          <td className="p-4">
                            <span className="text-xs font-mono font-bold text-slate-700 bg-slate-50 px-2 py-1 rounded">{adm.admission_number || "—"}</span>
                          </td>
                          <td className="p-4">
                            <span className="font-bold text-slate-800 block text-sm">{adm.patient_name || adm.patient_uhid}</span>
                            <span className="text-[11px] text-slate-400 font-mono">{adm.patient_uhid}</span>
                          </td>
                          <td className="p-4">
                            <span className="flex items-center gap-1.5 bg-rose-50 text-rose-700 px-2.5 py-1 rounded-lg border border-rose-100 text-[11px] font-black uppercase w-fit">
                              <MapPin size={11}/> 
                              { (() => {
                                 const b = bedGrid.find(x => x.bed_id === adm.bed_uuid);
                                 if (b) return `${b.ward_name} / ${b.bed_number}`;
                                 if (adm.bed_uuid) return "Bed Allocated";
                                 return "Pending Allocation";
                              })() }
                            </span>
                          </td>
                          <td className="p-4">
                            <span className="flex items-center gap-1.5 text-sm font-medium text-slate-600">
                              <Stethoscope size={14} className="text-blue-500"/> {adm.admitting_doctor || "—"}
                            </span>
                          </td>
                          <td className="p-4 text-xs text-slate-500 font-medium">
                            {adm.admission_time ? new Date(adm.admission_time).toLocaleDateString() : "—"}
                          </td>
                          <td className="p-4 text-center">
                            <Badge text={adm.status || "Admitted"} type={
                              adm.status === "Admitted" ? "info" : adm.status === "Discharged" ? "success" : "warning"
                            }/>
                          </td>
                          <td className="p-4 text-right">
                            <div className="flex items-center gap-1.5 justify-end">
                              <a href={`/dashboard/ipd/${adm.admission_number}`} className="bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 px-3 py-1.5 rounded-lg text-[11px] font-bold shadow-sm flex items-center gap-1">
                                <Eye size={12}/> View
                              </a>
                              <a href={`/dashboard/nursing-ipd/${adm.admission_number}`} className="bg-white border border-blue-200 hover:bg-blue-50 text-blue-600 px-3 py-1.5 rounded-lg text-[11px] font-bold shadow-sm flex items-center gap-1">
                                <FileText size={12}/> Notes
                              </a>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {/* === Bed Grid Tab === */}
                {activeTab === "beds" && (
                  <div className="p-6 space-y-6">
                    {Object.keys(bedsByWard).length === 0 ? (
                      <div className="text-center py-16 text-slate-400 font-bold">
                        <LayoutGrid size={40} className="mx-auto text-slate-200 mb-3"/>
                        <p>No bed data available. Configure wards and beds in Ward Management.</p>
                      </div>
                    ) : Object.entries(bedsByWard)
                      .filter(([name]) => !wardFilter || name === wardFilter)
                      .map(([wardName, beds]) => {
                        const filtered = (beds as any[]).filter(b =>
                          (!statusFilter || b.status === statusFilter) &&
                          (!searchQuery || b.bed_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            (b.patient_name || "").toLowerCase().includes(searchQuery.toLowerCase()))
                        );
                        if (filtered.length === 0 && (statusFilter || searchQuery)) return null;
                        return (
                          <div key={wardName}>
                            <div className="flex items-center gap-3 mb-3">
                              <Building2 size={18} className="text-rose-500"/>
                              <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider">{wardName}</h3>
                              <span className="text-[11px] font-bold text-slate-400">
                                {(filtered as any[]).filter(b=>b.status==="available").length} available / {filtered.length} total
                              </span>
                            </div>
                            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 xl:grid-cols-12 gap-2 mb-4">
                              {(filtered as any[]).map(bed => (
                                <div key={bed.bed_id}
                                  className={`p-2.5 rounded-xl border-2 text-center cursor-pointer transition-all hover:shadow-md group ${
                                    bed.status === "available" ? "border-emerald-200 bg-emerald-50 hover:border-emerald-400" :
                                    bed.status === "occupied" ? "border-rose-200 bg-rose-50 hover:border-rose-400" :
                                    bed.status === "cleaning" ? "border-amber-200 bg-amber-50 hover:border-amber-400" :
                                    bed.status === "reserved" ? "border-blue-200 bg-blue-50 hover:border-blue-400" :
                                    "border-slate-200 bg-slate-50"
                                  }`}
                                  title={`${bed.bed_code} — ${bed.status}${bed.patient_name ? ` — ${bed.patient_name}` : ""}`}>
                                  <Bed size={18} className={`mx-auto mb-1 ${
                                    bed.status === "available" ? "text-emerald-600" :
                                    bed.status === "occupied" ? "text-rose-600" :
                                    bed.status === "cleaning" ? "text-amber-600" :
                                    bed.status === "reserved" ? "text-blue-600" :
                                    "text-slate-400"
                                  }`}/>
                                  <div className="text-[10px] font-black text-slate-700 truncate">{bed.bed_number}</div>
                                  <div className="text-[9px] font-medium text-slate-400 truncate">{bed.room_number}</div>
                                  {bed.patient_name && (
                                    <div className="text-[9px] font-bold text-rose-600 truncate mt-0.5">{bed.patient_name}</div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}

                {/* === Admission Requests Tab === */}
                {activeTab === "requests" && (
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-amber-50/60 border-b border-amber-100">
                      <tr className="text-amber-800 text-[10px] uppercase font-black tracking-wider">
                        <th className="p-4">Request Time</th>
                        <th className="p-4">Patient</th>
                        <th className="p-4">Priority</th>
                        <th className="p-4">Source</th>
                        <th className="p-4">Diagnosis</th>
                        <th className="p-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50 text-sm">
                      {pendingRequests.length === 0 ? (
                        <tr><td colSpan={6} className="p-16 text-center text-slate-400 font-bold">
                          <div className="flex flex-col items-center gap-2">
                            <AlertTriangle size={36} className="text-slate-200"/>
                            <span>No pending admission requests</span>
                          </div>
                        </td></tr>
                      ) : pendingRequests.map(req => (
                        <tr key={req.id} className="hover:bg-slate-50/50">
                          <td className="p-4 text-xs text-slate-500 font-mono">{req.created_at ? new Date(req.created_at).toLocaleString() : "—"}</td>
                          <td className="p-4">
                            <span className="font-bold text-slate-800">{req.patient_name || req.patient_uhid}</span>
                            <span className="text-[11px] text-slate-400 font-mono block">{req.patient_uhid}</span>
                          </td>
                          <td className="p-4">
                            <Badge text={req.priority || "Routine"} type={
                              req.priority === "emergency" ? "danger" : req.priority === "urgent" ? "warning" : "default"
                            }/>
                          </td>
                          <td className="p-4 text-xs font-medium text-slate-600">{req.admission_source || "OPD"}</td>
                          <td className="p-4 text-xs text-slate-600 max-w-[200px] truncate">{req.provisional_diagnosis || "—"}</td>
                          <td className="p-4 text-right">
                            <button onClick={() => { setAllocatingRequest(req); setShowAllocateModal(true); }}
                              className="bg-rose-600 text-white rounded-xl px-4 py-2 font-bold hover:bg-rose-700 shadow-sm text-xs flex items-center gap-2 ml-auto transition-all hover:shadow-md">
                              <Bed size={14}/> Allocate Bed
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {/* === Pending Discharges Tab === */}
                {activeTab === "pendingDis" && (
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-violet-50/60 border-b border-violet-100">
                      <tr className="text-violet-800 text-[10px] uppercase font-black tracking-wider">
                        <th className="p-4">Admission #</th>
                        <th className="p-4">Patient UHID</th>
                        <th className="p-4">Planned Discharge</th>
                        <th className="p-4">Status</th>
                        <th className="p-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50 text-sm">
                      {pendingDischarges.length === 0 ? (
                        <tr><td colSpan={5} className="p-16 text-center text-slate-400 font-bold">
                          <div className="flex flex-col items-center gap-2">
                            <Clock size={36} className="text-slate-200"/>
                            <span>No pending discharges</span>
                          </div>
                        </td></tr>
                      ) : pendingDischarges.map((p, i) => (
                        <tr key={i} className="hover:bg-slate-50/50">
                          <td className="p-4 text-xs font-mono font-bold text-slate-700">{p.admission_number}</td>
                          <td className="p-4 text-sm font-medium text-slate-700">{p.patient_uhid}</td>
                          <td className="p-4 text-xs text-slate-500">{p.planned_discharge_date || "Not set"}</td>
                          <td className="p-4"><Badge text={p.status} type={p.status==="Ready"?"success":"warning"}/></td>
                          <td className="p-4 text-right">
                            <a href={`/dashboard/ipd-discharge?adm=${p.admission_number}`} className="bg-white border border-violet-200 hover:bg-violet-50 hover:border-violet-300 text-violet-700 px-3 py-1.5 rounded-lg text-[11px] font-bold shadow-sm flex items-center gap-1.5 ml-auto w-fit transition">
                              <LogOut size={12}/> Initialize Smart Discharge
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {/* === Discharged Patients Tab === */}
                {activeTab === "discharged" && (
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-emerald-50/60 border-b border-emerald-100">
                      <tr className="text-emerald-800 text-[10px] uppercase font-black tracking-wider">
                        <th className="p-4">Admission #</th>
                        <th className="p-4">Patient UHID</th>
                        <th className="p-4">Ward / Bed</th>
                        <th className="p-4">Admitted</th>
                        <th className="p-4">Discharged</th>
                        <th className="p-4 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50 text-sm">
                      {dischargedPatients.length === 0 ? (
                        <tr><td colSpan={6} className="p-16 text-center text-slate-400 font-bold">
                          <div className="flex flex-col items-center gap-2">
                            <CheckCircle size={36} className="text-slate-200"/>
                            <span>No discharged patients found</span>
                          </div>
                        </td></tr>
                      ) : dischargedPatients.map((dp, i) => (
                        <tr key={i} className="hover:bg-slate-50/50">
                          <td className="p-4 text-xs font-mono font-bold text-slate-700">{dp.admission_number}</td>
                          <td className="p-4 text-sm font-medium text-slate-700">{dp.patient_uhid}</td>
                          <td className="p-4 text-xs text-slate-500">
                            { (() => {
                               const b = bedGrid.find(x => x.bed_id === dp.bed_uuid);
                               if (b) return `${b.ward_name} / ${b.bed_number}`;
                               if (dp.bed_uuid) return "Bed Allocated";
                               return "Pending Allocation";
                            })() }
                          </td>
                          <td className="p-4 text-xs text-slate-500">{dp.admission_time ? new Date(dp.admission_time).toLocaleDateString() : "—"}</td>
                          <td className="p-4 text-xs text-slate-500">{dp.discharge_time ? new Date(dp.discharge_time).toLocaleDateString() : "—"}</td>
                          <td className="p-4 text-center"><Badge text="Discharged" type="success"/></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

              </div>
            </>
          )}
        </div>
      </div>

      {/* === Allocate Bed Modal === */}
      {showAllocateModal && allocatingRequest && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleAllocateBed} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-5 mx-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-4">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2">
                <div className="p-1.5 bg-rose-100 rounded-lg"><Bed size={20} className="text-rose-600"/></div>
                Allocate Ward Bed
              </h3>
              <button type="button" onClick={() => setShowAllocateModal(false)} className="p-1 hover:bg-slate-100 rounded-lg">
                <X size={20} className="text-slate-400"/>
              </button>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase">Patient</p>
                  <p className="font-black text-slate-800 text-sm mt-0.5">{allocatingRequest.patient_name || allocatingRequest.patient_uhid}</p>
                </div>
                <div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase">Priority</p>
                  <p className="mt-0.5"><Badge text={allocatingRequest.priority || "Routine"} type={
                    allocatingRequest.priority === "emergency" ? "danger" : "warning"
                  }/></p>
                </div>
                <div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase">UHID</p>
                  <p className="font-mono text-xs text-slate-600 mt-0.5">{allocatingRequest.patient_uhid}</p>
                </div>
                <div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase">Source</p>
                  <p className="text-xs text-slate-600 mt-0.5">{allocatingRequest.admission_source || "OPD"}</p>
                </div>
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-500 uppercase block mb-2">Select Available Bed *</label>
              <select
                value={selectedBed}
                onChange={e => setSelectedBed(e.target.value)}
                required
                className="w-full p-3 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:border-rose-400 bg-white">
                <option value="">— Select from available beds —</option>
                {availableBeds.length > 0 ? availableBeds.map(bed => (
                  <option key={bed.bed_id} value={bed.bed_id}>
                    {bed.bed_code} — {bed.ward_name} / Room {bed.room_number} ({bed.bed_type})
                  </option>
                )) : (
                  <>
                    <option value="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d">GEN-101 — General Male / Room 1</option>
                    <option value="b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e">GEN-102 — General Male / Room 1</option>
                    <option value="c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f">ICU-01 — Intensive Care Unit</option>
                    <option value="d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a">PVT-205 — Private Room Suite</option>
                  </>
                )}
              </select>
              <p className="text-[11px] text-slate-400 mt-1.5">{availableBeds.length > 0 ? `${availableBeds.length} beds available across all wards` : 'Using fallback bed list'}</p>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-100">
              <button type="button" onClick={() => setShowAllocateModal(false)}
                className="px-5 py-2.5 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-xl transition-colors">Cancel</button>
              <button type="submit"
                className="bg-rose-600 hover:bg-rose-700 text-white px-6 py-2.5 rounded-xl text-sm font-bold transition-all shadow-md shadow-rose-200 flex items-center gap-2">
                <CheckCircle size={16}/> Confirm Allocation
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
