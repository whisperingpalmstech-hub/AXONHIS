"use client";
import { useTranslation } from "@/i18n";


import React, { useState, useEffect } from "react";
import { 
  Users, Activity, ClipboardList, Clock, 
  ArrowLeftRight, LogOut, Thermometer, Pill, 
  Search, Filter, CheckCircle2, AlertCircle,
  Menu, MoreVertical, Bed
} from "lucide-react";

export default function NursingWardView() {
  const { t } = useTranslation();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
  const [activeWardId, setActiveWardId] = useState<string | null>(null);
  const [wards, setWards] = useState<any[]>([]);
  const [beds, setBeds] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWards();
  }, []);

  const fetchWards = async () => {
    try {
      const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const res = await fetch(`${API_URL}/api/v1/wards/`, { headers });
      if (res.ok) {
        const data = await res.json();
        setWards(data);
        if (data.length > 0) setActiveWardId(data[0].id);
      }
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    if (activeWardId) fetchBeds();
  }, [activeWardId]);

  const fetchBeds = async () => {
    setLoading(true);
    try {
      const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const res = await fetch(`${API_URL}/api/v1/wards/beds`, { headers });
      if (res.ok) {
        const data = await res.json();
        // Filter by ward in real implementation
        setBeds(data);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-screen">
      {/* ── NURSING STATION HEADER ── */}
      <div className="flex items-center justify-between">
         <div className="flex items-center gap-4">
            <div className="p-3 bg-rose-600 text-white rounded-xl shadow-lg shadow-rose-200">
               <Activity size={24} />
            </div>
            <div>
               <h1 className="text-2xl font-bold text-slate-900">Nursing Station</h1>
               <div className="flex items-center gap-2">
                 <select 
                    value={activeWardId || ""} 
                    onChange={e => setActiveWardId(e.target.value)}
                    className="bg-transparent border-none text-sm font-semibold text-rose-600 focus:ring-0 p-0 cursor-pointer"
                 >
                    {wards.map(w => <option key={w.id} value={w.id}>{w.ward_name}</option>)}
                 </select>
                 <span className="text-slate-300">|</span>
                 <p className="text-slate-500 text-sm">Main Nursing Desk - Shift A</p>
               </div>
            </div>
         </div>
         <div className="flex items-center gap-3">
            <div className="hidden md:flex flex-col items-end mr-4">
               <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Active Patients</p>
               <p className="text-xl font-black text-slate-800">12 / 20</p>
            </div>
            <button className="p-2 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-rose-600 transition shadow-sm">
               <Menu size={20} />
            </button>
         </div>
      </div>

      {/* ── SUB-HEADER ACTIONS ── */}
      <div className="flex flex-wrap items-center gap-4 bg-white p-2 rounded-2xl border border-slate-200 shadow-sm">
         <div className="relative flex-1 min-w-[300px]">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input type="text" placeholder="Search by patient name, MRN, or bed..." className="w-full pl-10 pr-4 py-2 bg-slate-50 border-none rounded-xl text-sm focus:ring-2 focus:ring-rose-500" />
         </div>
         <div className="flex items-center gap-2">
            <button className="px-4 py-2 bg-rose-50 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-100 transition">Vitals Entry</button>
            <button className="px-4 py-2 bg-emerald-50 text-emerald-600 rounded-xl text-xs font-bold hover:bg-emerald-100 transition">Medication Pass</button>
            <button className="p-2 bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition"><MoreVertical size={18} /></button>
         </div>
      </div>

      {/* ── PATIENT GRID ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
         {beds.filter(b => b.status === "occupied").map((bed, idx) => (
           <div key={bed.id} className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition group">
              <div className="p-4 flex items-start justify-between">
                 <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center font-bold text-slate-500 group-hover:from-rose-500 group-hover:to-rose-600 group-hover:text-white transition-all duration-300">
                       {bed.bed_number}
                    </div>
                    <div>
                       <h3 className="font-bold text-slate-900">Patient Name #{idx+1}</h3>
                       <p className="text-xs text-slate-500 font-medium tracking-tight">MRN-9283-00{idx} • Male, 45y</p>
                    </div>
                 </div>
                 <div className="flex flex-col items-end">
                    <span className="text-[10px] font-black text-rose-500 bg-rose-50 px-2 py-0.5 rounded-full uppercase italic">Critical</span>
                    <p className="text-[10px] text-slate-400 mt-1">Admitted 2d ago</p>
                 </div>
              </div>

              {/* STATS / VITALS PREVIEW */}
              <div className="grid grid-cols-3 border-y border-slate-100">
                 <div className="p-3 border-r border-slate-100 flex flex-col items-center">
                    <Thermometer size={14} className="text-orange-500 mb-1" />
                    <span className="text-xs font-bold text-slate-700">38.2°C</span>
                    <span className="text-[9px] text-slate-400 uppercase">Temp</span>
                 </div>
                 <div className="p-3 border-r border-slate-100 flex flex-col items-center">
                    <Activity size={14} className="text-rose-500 mb-1" />
                    <span className="text-xs font-bold text-slate-700">110/72</span>
                    <span className="text-[9px] text-slate-400 uppercase">BP</span>
                 </div>
                 <div className="p-3 flex flex-col items-center">
                    <Clock size={14} className="text-blue-500 mb-1" />
                    <span className="text-xs font-bold text-slate-700">98%</span>
                    <span className="text-[9px] text-slate-400 uppercase">SPO2</span>
                 </div>
              </div>

              {/* PENDING TASKS */}
              <div className="p-4 space-y-3">
                 <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-widest">
                    <span>Pending Tasks</span>
                    <span className="text-rose-500">2 Overdue</span>
                 </div>
                 <div className="space-y-2">
                    <div className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg border border-slate-100 border-l-4 border-l-rose-500">
                       <Pill size={14} className="text-rose-500" />
                       <p className="text-xs font-medium text-slate-700 truncate flex-1">Paracetamol 500mg - Oral</p>
                       <span className="text-[10px] text-rose-600 font-bold whitespace-nowrap">08:00 AM</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg border border-slate-100 border-l-4 border-l-blue-500">
                       <ClipboardList size={14} className="text-blue-500" />
                       <p className="text-xs font-medium text-slate-700 truncate flex-1">Wound Dressing Change</p>
                       <span className="text-[10px] text-blue-600 font-bold whitespace-nowrap">10:30 AM</span>
                    </div>
                 </div>
              </div>

              {/* QUICK ACTIONS */}
              <div className="p-2 bg-slate-50 flex items-center gap-2">
                 <button className="flex-1 flex items-center justify-center gap-2 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition">
                    <ArrowLeftRight size={14} /> Transfer
                 </button>
                 <button className="flex-1 flex items-center justify-center gap-2 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition text-rose-600">
                    <LogOut size={14} /> Release
                 </button>
              </div>
           </div>
         ))}
      </div>
    </div>
  );
}
