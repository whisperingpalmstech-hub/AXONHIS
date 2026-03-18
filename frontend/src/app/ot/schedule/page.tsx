"use client";

import React, { useState, useEffect } from "react";
import { otApi } from "@/lib/ot-api";
import { OperatingRoom, SurgicalProcedure, SurgeryPriority } from "@/types/ot";
import { Calendar, Clock, Plus, Filter, Search, User, MapPin } from "lucide-react";

export default function SurgerySchedulePage() {
  const [rooms, setRooms] = useState<OperatingRoom[]>([]);
  const [procedures, setProcedures] = useState<SurgicalProcedure[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    patient_id: "",
    encounter_id: "",
    procedure_id: "",
    operating_room_id: "",
    scheduled_start_time: "",
    scheduled_end_time: "",
    priority: SurgeryPriority.ELECTIVE,
  });

  useEffect(() => {
    async function init() {
      try {
        const [roomData, procData] = await Promise.all([
          otApi.getRooms(),
          otApi.getProcedures(),
        ]);
        setRooms(roomData);
        setProcedures(procData);
      } catch (e) {
        console.error("Failed to load metadata", e);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await otApi.scheduleSurgery(formData);
      setIsModalOpen(false);
      alert("Surgery scheduled successfully!");
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
  };

  if (loading) return null;

  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Surgical Scheduling</h1>
            <p className="text-slate-500 font-medium">Orchestrate theater logistics and surgical teams</p>
          </div>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white font-bold rounded-xl shadow-xl shadow-indigo-100 hover:bg-indigo-700 transition-all hover:scale-[1.02]"
          >
            <Plus size={20} strokeWidth={3} />
            Schedule Procedure
          </button>
        </div>

        {/* Toolbar */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm mb-8 flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-[300px] relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="Search by Patient, ID or Surgeon..." 
              className="w-full pl-12 pr-4 py-3 bg-slate-50 border-transparent rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-3 border border-slate-200 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-50">
            <Filter size={18} />
            Filter
          </button>
          <button className="flex items-center gap-2 px-4 py-3 border border-slate-200 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-50">
            <Calendar size={18} />
            March 18, 2026
          </button>
        </div>

        {/* Empty State / Table Placeholder */}
        <div className="bg-white rounded-3xl border border-dashed border-slate-300 p-20 flex flex-col items-center text-center">
            <div className="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-600 mb-6">
                <Calendar size={40} />
            </div>
            <h2 className="text-xl font-bold text-slate-800 mb-2">No Surgeries Selected</h2>
            <p className="text-slate-500 max-w-sm mb-8">Select a date or use search to view scheduled surgical procedures and theater allocations.</p>
        </div>
      </div>

      {/* Schedule Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-xl rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="px-8 py-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h3 className="text-xl font-black text-slate-800">New Surgery Schedule</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                <Plus className="rotate-45" size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <FormField label="Patient UUID" icon={<User size={16} />}>
                  <input 
                    required
                    value={formData.patient_id}
                    onChange={(e) => setFormData({...formData, patient_id: e.target.value})}
                    className="w-full px-4 py-3 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" 
                  />
                </FormField>
                <FormField label="Encounter UUID" icon={<Activity size={16} />}>
                  <input 
                    required
                    value={formData.encounter_id}
                    onChange={(e) => setFormData({...formData, encounter_id: e.target.value})}
                    className="w-full px-4 py-3 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" 
                  />
                </FormField>
              </div>

              <FormField label="Procedure" icon={<Activity size={16} />}>
                <select 
                  required
                  value={formData.procedure_id}
                  onChange={(e) => setFormData({...formData, procedure_id: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none"
                >
                  <option value="">Select Procedure</option>
                  {procedures.map(p => <option key={p.id} value={p.id}>{p.procedure_name} ({p.procedure_code})</option>)}
                </select>
              </FormField>

              <FormField label="Operating Theater" icon={<MapPin size={16} />}>
                <select 
                  required
                  value={formData.operating_room_id}
                  onChange={(e) => setFormData({...formData, operating_room_id: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none"
                >
                  <option value="">Select Room</option>
                  {rooms.map(r => <option key={r.id} value={r.id}>{r.room_name} ({r.room_code})</option>)}
                </select>
              </FormField>

              <div className="grid grid-cols-2 gap-6">
                <FormField label="Start Time" icon={<Clock size={16} />}>
                  <input 
                    type="datetime-local" 
                    required
                    value={formData.scheduled_start_time}
                    onChange={(e) => setFormData({...formData, scheduled_start_time: e.target.value})}
                    className="w-full px-4 py-3 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" 
                  />
                </FormField>
                <FormField label="End Time" icon={<Clock size={16} />}>
                  <input 
                    type="datetime-local" 
                    required
                    value={formData.scheduled_end_time}
                    onChange={(e) => setFormData({...formData, scheduled_end_time: e.target.value})}
                    className="w-full px-4 py-3 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none" 
                  />
                </FormField>
              </div>

              <div className="pt-4">
                <button type="submit" className="w-full py-4 bg-indigo-600 text-white font-black rounded-2xl shadow-xl shadow-indigo-100 hover:bg-indigo-700 transition-all hover:scale-[1.01]">
                  Confirm Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const FormField = ({ label, icon, children }: any) => (
  <div className="space-y-2">
    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 ml-1">
      {icon} {label}
    </label>
    {children}
  </div>
);

const Activity = ({ size, className }: any) => (
    <svg 
      width={size || 24} 
      height={size || 24} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
