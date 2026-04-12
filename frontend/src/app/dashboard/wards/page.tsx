"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect } from "react";
import { 
  Bed, Building2, LayoutPanelLeft, Clock, ShieldCheck, 
  Plus, Users, Activity, Trash2, ArrowLeftRight, 
  CheckCircle2, AlertCircle, Search, Filter, 
  MapPin, ClipboardList, Info, Home
} from "lucide-react";

type BedStatus = "available" | "occupied" | "cleaning" | "maintenance";
type RoomType = "private" | "semi_private" | "general";

interface Ward {
  id: string;
  ward_code: string;
  ward_name: string;
  department: string;
  floor: string;
  capacity: number;
}

interface Room {
  id: string;
  ward_id: string;
  room_number: string;
  room_type: RoomType;
  capacity: number;
}

interface BedInfo {
  id: string;
  room_id: string;
  bed_code: string;
  bed_number: string;
  bed_type: string;
  status: BedStatus;
}

interface OccupancyStats {
  total: number;
  occupied: number;
  cleaning: number;
  available: number;
  occupancy_rate: number;
}

interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  patient_uuid: string;
}

interface Encounter {
  id: string;
  patient_id: string;
  encounter_type: string;
  encounter_uuid: string;
  status: string;
}

export default function WardManagement() {
  const { t } = useTranslation();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
  const [activeView, setActiveView] = useState<"dashboard" | "inventory">("dashboard");
  const [wards, setWards] = useState<Ward[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [beds, setBeds] = useState<BedInfo[]>([]);
  const [stats, setStats] = useState<OccupancyStats>({ total: 0, occupied: 0, cleaning: 0, available: 0, occupancy_rate: 0 });
  const [loading, setLoading] = useState(true);
  
  // Modals
  const [showWardModal, setShowWardModal] = useState(false);
  const [showRoomModal, setShowRoomModal] = useState(false);
  const [showBedModal, setShowBedModal] = useState(false);
  const [showBulkBedModal, setShowBulkBedModal] = useState(false);
  const [showWardDetailModal, setShowWardDetailModal] = useState<Ward | null>(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  
  // Forms
  const [wardForm, setWardForm] = useState({ ward_code: "", ward_name: "", department: "", floor: "", capacity: 0 });
  const [roomForm, setRoomForm] = useState({ ward_id: "", room_number: "", room_type: "general" as RoomType, capacity: 2 });
  const [bedForm, setBedForm] = useState({ room_id: "", bed_code: "", bed_number: "", bed_type: "standard" });
  const [bulkBedForm, setBulkBedForm] = useState({ room_id: "", prefix: "BED-", start_num: 1, count: 5 });
  const [selectedBed, setSelectedBed] = useState<BedInfo | null>(null);
  const [selectedWardRooms, setSelectedWardRooms] = useState<Room[]>([]);
  const [selectedWardForBulk, setSelectedWardForBulk] = useState("");
  const [currentActiveWardId, setCurrentActiveWardId] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [assignForm, setAssignForm] = useState({ patient_id: "", encounter_id: "", bed_id: "" });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const [wRes, bRes, sRes, pRes, eRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/wards/`, { headers }),
        fetch(`${API_URL}/api/v1/wards/beds`, { headers }),
        fetch(`${API_URL}/api/v1/wards/dashboard/occupancy`, { headers }),
        fetch(`${API_URL}/api/v1/patients/`, { headers }),
        fetch(`${API_URL}/api/v1/encounters/`, { headers })
      ]);
      
      if (wRes.ok) setWards(await wRes.json());
      if (bRes.ok) setBeds(await bRes.json());
      if (sRes.ok) setStats(await sRes.json());
      if (pRes.ok) setPatients(await pRes.json());
      if (eRes.ok) setEncounters(await eRes.json());
    } catch (err) {
      console.error("Failed to fetch ward data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWard = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/wards/`, {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(wardForm)
      });
      if (res.ok) {
        setShowWardModal(false);
        setWardForm({ ward_code: "", ward_name: "", department: "", floor: "", capacity: 0 });
        fetchData();
      }
    } catch (e) { alert(e); }
  };

  const fetchRooms = async (wardId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/wards/${wardId}/rooms`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("access_token")}` }
      });
      if (res.ok) setSelectedWardRooms(await res.json());
    } catch (e) { console.error(e); }
  };

  const handleCreateRoom = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/wards/rooms`, {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(roomForm)
      });
      if (res.ok) {
        setShowRoomModal(false);
        fetchRooms(roomForm.ward_id);
      }
    } catch (e) { alert(e); }
  };

  const handleCreateBed = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/wards/beds`, {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(bedForm)
      });
      if (res.ok) {
        setShowBedModal(false);
        fetchData();
      }
    } catch (e) { alert(e); }
  };

  const handleCreateBedsBulk = async () => {
    try {
      const bedsToCreate = Array.from({ length: bulkBedForm.count }, (_, i) => ({
        room_id: bulkBedForm.room_id,
        bed_code: `${bulkBedForm.prefix}${bulkBedForm.start_num + i}`,
        bed_number: `${bulkBedForm.start_num + i}`,
        bed_type: "standard",
        status: "available"
      }));

      const res = await fetch(`${API_URL}/api/v1/wards/beds/bulk`, {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(bedsToCreate)
      });
      if (res.ok) {
        setShowBulkBedModal(false);
        fetchData();
      }
    } catch (e) { alert(e); }
  };

  const handleAssignBed = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/wards/assign`, {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(assignForm)
      });
      if (res.ok) {
        setShowAssignModal(false);
        fetchData();
      } else {
        const err = await res.json();
        alert(err.detail || "Assignment failed");
      }
    } catch (e) { alert(e); }
  };

  const statusColors = {
    available: "bg-emerald-50 text-emerald-700 border-emerald-200",
    occupied: "bg-rose-50 text-rose-700 border-rose-200",
    cleaning: "bg-amber-50 text-amber-700 border-amber-200",
    maintenance: "bg-slate-50 text-slate-700 border-slate-200"
  };

  const statusIcons = {
    available: <CheckCircle2 size={16} />,
    occupied: <Activity size={16} />,
    cleaning: <Clock size={16} />,
    maintenance: <LayoutPanelLeft size={16} />
  };

  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-screen">
      {/* ── HEADER ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("wards.wardAndBedManagement") || "Ward & Bed Management"}</h1>
          <p className="text-slate-500 text-sm">{t("wards.monitorHospitalOccupancy") || "Monitor hospital occupancy and manage beds."}</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowWardModal(true)} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition shadow-sm font-medium">
            <Plus size={18} />{t("wards.newWard")}</button>
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition shadow-xs font-medium">
            <Filter size={18} />{t("wards.filters")}</button>
        </div>
      </div>

      {/* ── OCCUPANCY STATS ── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{t("wards.totalCapacity")}</p>
            <p className="text-2xl font-bold text-slate-900">{stats.total} <span className="text-sm font-normal text-slate-400 ml-1">{t("wards.beds")}</span></p>
          </div>
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <Building2 size={24} />
          </div>
        </div>
        <div className="p-5 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-between border-l-4 border-l-rose-500">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{t("wards.occupied")}</p>
            <p className="text-2xl font-bold text-rose-600">{stats.occupied}</p>
          </div>
          <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <Home size={24} />
          </div>
        </div>
        <div className="p-5 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-between border-l-4 border-l-amber-500">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{t("wards.cleaning")}</p>
            <p className="text-2xl font-bold text-amber-600">{stats.cleaning}</p>
          </div>
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <Clock size={24} />
          </div>
        </div>
        <div className="p-5 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-between border-l-4 border-l-emerald-500">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{t("wards.available")}</p>
            <p className="text-2xl font-bold text-emerald-600">{stats.available}</p>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle2 size={24} />
          </div>
        </div>
      </div>

      {/* ── NAVIGATION TABS ── */}
      <div className="flex border-b border-slate-200">
        <button onClick={() => setActiveView("dashboard")} className={`px-6 py-3 font-medium transition-all ${activeView === "dashboard" ? "text-indigo-600 border-b-2 border-indigo-600" : "text-slate-500 hover:text-slate-700"}`}>{t("wards.wardDashboard")}</button>
        <button onClick={() => setActiveView("inventory")} className={`px-6 py-3 font-medium transition-all ${activeView === "inventory" ? "text-indigo-600 border-b-2 border-indigo-600" : "text-slate-500 hover:text-slate-700"}`}>{t("wards.bedInventory")}</button>
      </div>

      {/* ── WARD GRID ── */}
      {activeView === "dashboard" ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {wards.length > 0 ? wards.map(ward => (
            <div key={ward.id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:border-indigo-300 transition-colors">
              <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
                    <MapPin size={18} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900">{ward.ward_name} <span className="text-xs text-slate-400 font-normal ml-1">({ward.ward_code})</span></h3>
                    <p className="text-xs text-slate-500">{ward.department} • Floor {ward.floor}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold bg-white border border-slate-200 px-2 py-1 rounded text-slate-600">
                    Cap: {ward.capacity}
                  </span>
                </div>
              </div>
              <div className="p-4">
                <div className="grid grid-cols-4 md:grid-cols-5 gap-3">
                  {beds.filter(b => true).map(bed => ( // Need to filter by ward/room properly later
                    <button key={bed.id} onClick={() => setSelectedBed(bed)} className={`flex flex-col items-center justify-center p-3 rounded-lg border transition-all ${statusColors[bed.status]} hover:scale-105 shadow-xs`}>
                      <Bed size={24} className="mb-1" />
                      <span className="text-[10px] font-bold uppercase">{bed.bed_number}</span>
                    </button>
                  ))}
                  <button 
                    onClick={() => {
                      setCurrentActiveWardId(ward.id);
                      setBedForm(prev => ({ ...prev, room_id: "" }));
                      setRoomForm(prev => ({ ...prev, ward_id: ward.id }));
                      fetchRooms(ward.id);
                      setShowBedModal(true);
                    }}
                    className="flex flex-col items-center justify-center p-3 rounded-lg border border-dashed border-slate-300 text-slate-400 hover:bg-slate-50 hover:border-indigo-300 hover:text-indigo-600 transition-all font-bold"
                  >
                    <Plus size={24} className="mb-1" />
                    <span className="text-[10px] uppercase">{t("wards.addBed")}</span>
                  </button>
                </div>
              </div>
              <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-4">
                   <div className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                      <span className="text-[10px] text-slate-500">12 Avail</span>
                   </div>
                   <div className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full bg-rose-500"></div>
                      <span className="text-[10px] text-slate-500">8 Occu</span>
                   </div>
                </div>
                <button 
                  onClick={() => setShowWardDetailModal(ward)}
                  className="text-xs font-semibold text-indigo-600 hover:underline"
                >
                  View details →
                </button>
              </div>
            </div>
          )) : (
            <div className="col-span-2 py-20 bg-white rounded-xl border border-dashed border-slate-300 flex flex-col items-center justify-center text-slate-400">
              <Building2 size={48} className="mb-4 opacity-20" />
              <p>{t("wards.noWardsDefinedYetStartByCreati")}</p>
              <button onClick={() => setShowWardModal(true)} className="mt-4 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg font-medium hover:bg-indigo-100 transition">
                + Create Ward
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
           <div className="p-4 border-b border-slate-200 flex items-center justify-between gap-4">
              <div className="relative flex-1 max-w-md">
                 <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                 <input type="text" placeholder="Search bed code or patient name..." className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <button 
                onClick={() => setShowBulkBedModal(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition shadow-sm"
              >{t("wards.addMultipleBeds")}</button>
           </div>
           <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
                  <th className="px-6 py-4 border-b border-slate-200">{t("wards.bedInfo")}</th>
                  <th className="px-6 py-4 border-b border-slate-200">{t("wards.status")}</th>
                  <th className="px-6 py-4 border-b border-slate-200">{t("wards.roomWard")}</th>
                  <th className="px-6 py-4 border-b border-slate-200">{t("wards.currentOccupant")}</th>
                  <th className="px-6 py-4 border-b border-slate-200">{t("wards.actions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {beds.map(bed => (
                  <tr key={bed.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                         <div className={`p-2 rounded-lg ${statusColors[bed.status]} opacity-80`}>
                            <Bed size={20} />
                         </div>
                         <div>
                            <p className="font-bold text-slate-900">{bed.bed_code}</p>
                            <p className="text-xs text-slate-500">{bed.bed_type} Bed</p>
                         </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${statusColors[bed.status]}`}>
                        {statusIcons[bed.status]}
                        <span className="capitalize">{bed.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-slate-700">Room {bed.room_id.substring(0,4)}</p>
                      <p className="text-xs text-slate-400">{t("wards.wardName")}</p>
                    </td>
                    <td className="px-6 py-4">
                      {bed.status === "occupied" ? (
                        <div className="flex items-center gap-2">
                           <div className="w-8 h-8 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-xs uppercase">{t("wards.jd")}</div>
                           <div>
                              <p className="text-sm font-bold text-slate-900">{t("wards.johnDoe")}</p>
                              <p className="text-[10px] text-slate-500 uppercase tracking-tighter italic">Enc: ENT-2938</p>
                           </div>
                        </div>
                      ) : (
                        <span className="text-slate-300 text-xs italic">{t("wards.unassigned")}</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <button 
                          onClick={() => {
                            setSelectedBed(bed);
                            setAssignForm({ ...assignForm, bed_id: bed.id });
                            setShowAssignModal(true);
                          }}
                          className="p-2 text-slate-400 hover:text-indigo-600 transition hover:bg-indigo-50 rounded-lg" 
                          title="Assign Patient"
                        >
                          <Plus size={18} />
                        </button>
                        <button className="p-2 text-slate-400 hover:text-slate-600 transition hover:bg-slate-100 rounded-lg">
                          <Info size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
           </table>
        </div>
      )}

      {/* ── CREATE WARD MODAL ── */}
      {showWardModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
           <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-indigo-600">
                 <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Building2 size={20} />{t("wards.defineNewHospitalWard")}</h2>
                 <button onClick={() => setShowWardModal(false)} className="text-white/80 hover:text-white transition">
                    <Trash2 size={20} />
                 </button>
              </div>
              <div className="p-6 space-y-4">
                 <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.wardCode")}</label>
                    <input value={wardForm.ward_code} onChange={e => setWardForm({...wardForm, ward_code: e.target.value})} type="text" placeholder="e.g. WARD-B1" className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium" />
                 </div>
                 <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.wardName")}</label>
                    <input value={wardForm.ward_name} onChange={e => setWardForm({...wardForm, ward_name: e.target.value})} type="text" placeholder="e.g. General Surgery" className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium" />
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.department")}</label>
                        <select value={wardForm.department} onChange={e => setWardForm({...wardForm, department: e.target.value})} className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium">
                            <option value="">{t("wards.selectDept")}</option>
                            <option value="Surgery">{t("wards.surgery")}</option>
                            <option value="Medicine">{t("wards.medicine")}</option>
                            <option value="ICU">{t("wards.icu")}</option>
                            <option value="Emergency">{t("wards.emergency")}</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.floor")}</label>
                        <input value={wardForm.floor} onChange={e => setWardForm({...wardForm, floor: e.target.value})} type="text" placeholder="e.g. 2nd Floor" className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium" />
                    </div>
                 </div>
              </div>
              <div className="p-6 bg-slate-50 border-t border-slate-100 flex gap-3">
                 <button onClick={() => setShowWardModal(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-slate-600 font-bold hover:bg-slate-100 transition">{t("wards.discard")}</button>
                 <button onClick={handleCreateWard} className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition shadow-lg shadow-indigo-200">{t("wards.saveWard")}</button>
              </div>
           </div>
        </div>
      )}

      {/* ── CREATE ROOM MODAL ── */}
      {showRoomModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
           <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-emerald-600 text-white">
                 <h2 className="text-lg font-bold">{t("wards.newRoomInWard")}</h2>
                 <button onClick={() => setShowRoomModal(false)} className="hover:opacity-80 transition"><Trash2 size={20} /></button>
              </div>
              <div className="p-6 space-y-4">
                 <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.roomNumber")}</label>
                    <input value={roomForm.room_number} onChange={e => setRoomForm({...roomForm, room_number: e.target.value})} type="text" placeholder="e.g. 101" className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium focus:ring-2 focus:ring-emerald-500" />
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.roomType")}</label>
                        <select value={roomForm.room_type} onChange={e => setRoomForm({...roomForm, room_type: e.target.value as RoomType})} className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium">
                            <option value="general">{t("wards.general")}</option>
                            <option value="semi_private">{t("wards.semiPrivate")}</option>
                            <option value="private">{t("wards.private")}</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.capacity")}</label>
                        <input value={roomForm.capacity} onChange={e => setRoomForm({...roomForm, capacity: parseInt(e.target.value)})} type="number" className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium" />
                    </div>
                 </div>
              </div>
              <div className="p-6 bg-slate-50 border-t border-slate-100 flex gap-3">
                 <button onClick={() => setShowRoomModal(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-slate-600 font-bold hover:bg-slate-100 transition">{t("wards.cancel")}</button>
                 <button onClick={handleCreateRoom} className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 transition">{t("wards.createRoom")}</button>
              </div>
           </div>
        </div>
      )}

      {/* ── CREATE BED MODAL ── */}
      {showBedModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-[55] flex items-center justify-center p-4">
           <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-indigo-600 text-white">
                 <h2 className="text-lg font-bold">{t("wards.addSingleBed")}</h2>
                 <button onClick={() => setShowBedModal(false)} className="hover:opacity-80 transition"><Trash2 size={20} /></button>
              </div>
              <div className="p-6 space-y-4">
                 <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.selectRoom")}</label>
                    <div className="flex gap-2">
                        <select value={bedForm.room_id} onChange={e => setBedForm({...bedForm, room_id: e.target.value})} className="flex-1 px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium focus:ring-2 focus:ring-indigo-500">
                            <option value="">{selectedWardRooms.length === 0 ? "-- No Rooms in Ward --" : "-- Choose Room --"}</option>
                            {selectedWardRooms.map(r => <option key={r.id} value={r.id}>Room {r.room_number}</option>)}
                        </select>
                        <button onClick={() => {
                          setShowRoomModal(true);
                        }} className="p-2 bg-indigo-50 text-indigo-600 rounded-xl hover:bg-indigo-100 transition shadow-sm" title="Create New Room First">
                          <Plus size={24} />
                        </button>
                    </div>
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.bedCode")}</label>
                        <input value={bedForm.bed_code} onChange={e => setBedForm({...bedForm, bed_code: e.target.value})} type="text" placeholder="B1-01" className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium focus:ring-2 focus:ring-indigo-500" />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.bedNumber")}</label>
                        <input value={bedForm.bed_number} onChange={e => setBedForm({...bedForm, bed_number: e.target.value})} type="text" placeholder="1" className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium focus:ring-2 focus:ring-indigo-500" />
                    </div>
                 </div>
              </div>
              <div className="p-6 bg-slate-50 border-t border-slate-100 flex gap-3">
                 <button onClick={() => setShowBedModal(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-slate-600 font-bold hover:bg-slate-100 transition">{t("wards.cancel")}</button>
                 <button onClick={handleCreateBed} className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition">{t("wards.addBed")}</button>
              </div>
           </div>
        </div>
      )}

      {/* ── BULK BED MODAL ── */}
      {showBulkBedModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-[55] flex items-center justify-center p-4">
           <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-indigo-700 text-white">
                 <h2 className="text-lg font-bold">{t("wards.addMultipleBeds")}</h2>
                 <button onClick={() => setShowBulkBedModal(false)} className="hover:opacity-80 transition"><Trash2 size={20} /></button>
              </div>
              <div className="p-6 space-y-4">
                 <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.selectWard")}</label>
                    <select 
                      value={selectedWardForBulk} 
                      onChange={e => {
                        setSelectedWardForBulk(e.target.value);
                        setBulkBedForm(prev => ({ ...prev, room_id: "" }));
                        fetchRooms(e.target.value);
                      }} 
                      className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium focus:ring-2 focus:ring-indigo-500 mb-4"
                    >
                        <option value="">-- Choose Ward --</option>
                        {wards.map(w => <option key={w.id} value={w.id}>{w.ward_name}</option>)}
                    </select>

                    <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.selectRoom")}</label>
                    <select 
                      value={bulkBedForm.room_id} 
                      onChange={e => setBulkBedForm({...bulkBedForm, room_id: e.target.value})} 
                      className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium focus:ring-2 focus:ring-indigo-500"
                    >
                        <option value="">{selectedWardRooms.length === 0 ? "-- No Rooms in Selected Ward --" : "-- Choose Room --"}</option>
                        {selectedWardRooms.map(r => <option key={r.id} value={r.id}>Room {r.room_number}</option>)}
                    </select>
                 </div>
                 <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-1">
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.prefix")}</label>
                        <input value={bulkBedForm.prefix} onChange={e => setBulkBedForm({...bulkBedForm, prefix: e.target.value})} type="text" className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium" />
                    </div>
                    <div className="col-span-1">
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">Start #</label>
                        <input value={bulkBedForm.start_num} onChange={e => setBulkBedForm({...bulkBedForm, start_num: parseInt(e.target.value)})} type="number" className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium" />
                    </div>
                    <div className="col-span-1">
                        <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.count")}</label>
                        <input value={bulkBedForm.count} onChange={e => setBulkBedForm({...bulkBedForm, count: parseInt(e.target.value)})} type="number" className="w-full px-4 py-2 border border-slate-200 rounded-xl outline-none font-medium" />
                    </div>
                 </div>
              </div>
              <div className="p-6 bg-slate-50 border-t border-slate-100 flex gap-3">
                 <button onClick={() => setShowBulkBedModal(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-slate-600 font-bold hover:bg-slate-100 transition">{t("wards.cancel")}</button>
                 <button onClick={handleCreateBedsBulk} className="flex-1 px-4 py-2 bg-indigo-700 text-white rounded-xl font-bold hover:bg-indigo-800 transition">Create {bulkBedForm.count} Beds</button>
              </div>
           </div>
        </div>
      )}

      {/* ── WARD DETAIL MODAL ── */}
      {showWardDetailModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
           <div className="bg-white rounded-2xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-white">
                 <div className="flex items-center gap-4">
                    <div className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl">
                       <MapPin size={24} />
                    </div>
                    <div>
                       <h2 className="text-xl font-bold text-slate-900">{showWardDetailModal.ward_name}</h2>
                       <p className="text-sm text-slate-500 font-medium">{showWardDetailModal.department} • {showWardDetailModal.floor} • Code: {showWardDetailModal.ward_code}</p>
                    </div>
                 </div>
                 <button onClick={() => setShowWardDetailModal(null)} className="p-2 bg-slate-100 text-slate-400 rounded-full hover:bg-slate-200 hover:text-slate-600 transition">
                    <LayoutPanelLeft size={20} />
                 </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 bg-slate-50">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="col-span-2 space-y-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                      <div className="flex items-center justify-between mb-6">
                        <h3 className="font-bold text-slate-900">{t("wards.roomsLayout")}</h3>
                        <button 
                          onClick={() => {
                            setRoomForm({...roomForm, ward_id: showWardDetailModal.id});
                            setShowRoomModal(true);
                          }}
                          className="text-xs font-bold text-indigo-600 flex items-center gap-1 hover:underline"
                        >
                          <Plus size={14} />{t("wards.addRoom")}</button>
                      </div>
                      <div className="space-y-4">
                         {/* This would show rooms if we had them fetched */}
                         <div className="p-4 bg-slate-50 rounded-xl border border-dashed border-slate-300 flex flex-col items-center py-10 text-slate-400">
                            <Home size={32} className="mb-2 opacity-20" />
                            <p className="text-sm">Click 'Add Room' to define room structure</p>
                         </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 text-center">
                       <div className="w-20 h-20 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 border-4 border-white shadow-sm font-black text-2xl tracking-tighter italic">
                          85%
                       </div>
                       <h3 className="font-bold text-slate-900">{t("wards.occupancyRate")}</h3>
                       <p className="text-xs text-slate-500 mt-1">17 / 20 Beds Occupied</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="p-4 bg-white border-t border-slate-100 flex justify-end">
                <button onClick={() => setShowWardDetailModal(null)} className="px-6 py-2 bg-slate-900 text-white rounded-xl font-bold hover:bg-black transition shadow-lg">{t("wards.closeView")}</button>
              </div>
           </div>
        </div>
      )}
      {/* ── ASSIGN BED MODAL ── */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
           <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-indigo-600 text-white">
                 <h2 className="text-lg font-bold flex items-center gap-2">
                    <Activity size={20} /> Assign Bed: {selectedBed?.bed_code}
                 </h2>
                 <button onClick={() => setShowAssignModal(false)} className="hover:opacity-80 transition"><Trash2 size={20} /></button>
              </div>
              <div className="p-6 space-y-4">
                 <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.selectPatient")}</label>
                    <select 
                      value={assignForm.patient_id} 
                      onChange={e => setAssignForm({...assignForm, patient_id: e.target.value, encounter_id: ""})} 
                      className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
                    >
                        <option value="">-- Choose Patient --</option>
                        {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.patient_uuid})</option>)}
                    </select>
                 </div>
                 <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase mb-1">{t("wards.selectEncounter")}</label>
                    <select 
                      value={assignForm.encounter_id} 
                      onChange={e => setAssignForm({...assignForm, encounter_id: e.target.value})} 
                      className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
                      disabled={!assignForm.patient_id}
                    >
                        <option value="">-- Choose Encounter --</option>
                        {encounters
                          .filter(e => e.patient_id === assignForm.patient_id)
                          .map(enc => <option key={enc.id} value={enc.id}>{enc.encounter_type} - {enc.status} ({enc.encounter_uuid.substring(0,8)})</option>)
                        }
                    </select>
                    {!assignForm.patient_id && <p className="text-[10px] text-rose-500 mt-1 italic">{t("wards.pleaseSelectAPatientFirstToSee")}</p>}
                 </div>
                 <p className="text-[10px] text-slate-400 italic bg-slate-50 p-2 rounded border border-slate-100 flex items-start gap-2">
                    <Activity size={14} className="shrink-0 mt-0.5" />{t("wards.bedsCanOnlyBeAssignedToPatient")}</p>
              </div>
              <div className="p-6 bg-slate-50 border-t border-slate-100 flex gap-3">
                 <button onClick={() => setShowAssignModal(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-slate-600 font-bold hover:bg-slate-100 transition">{t("wards.cancel")}</button>
                 <button onClick={handleAssignBed} className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition">{t("wards.confirmAssignment")}</button>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
