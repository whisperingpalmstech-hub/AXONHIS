"use client";

import React, { useState, useEffect } from 'react';
import { otApi } from '@/lib/ot-api';
import { OperatingRoom, SurgicalProcedure } from '@/types/ot';
import { Plus, Save, Building, BriefcaseMedical } from 'lucide-react';

export default function OTSettingsPage() {
  const [rooms, setRooms] = useState<OperatingRoom[]>([]);
  const [procedures, setProcedures] = useState<SurgicalProcedure[]>([]);
  
  const [newRoom, setNewRoom] = useState({
    room_code: '',
    room_name: '',
    department: '',
    status: 'available'
  });

  const [newProcedure, setNewProcedure] = useState({
    procedure_code: '',
    procedure_name: '',
    specialty: '',
    expected_duration: 60,
    billing_code: ''
  });

  const loadData = async () => {
    try {
      const [_rooms, _procs] = await Promise.all([
        otApi.getRooms(),
        otApi.getProcedures()
      ]);
      setRooms(_rooms);
      setProcedures(_procs);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await otApi.createRoom({
        ...newRoom,
        equipment_profile: {}
      });
      setNewRoom({ room_code: '', room_name: '', department: '', status: 'available' });
      loadData();
    } catch (e: any) {
      alert(typeof e.message === 'string' ? e.message : JSON.stringify(e));
    }
  };

  const handleCreateProcedure = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await otApi.createProcedure({
        ...newProcedure
      });
      setNewProcedure({ procedure_code: '', procedure_name: '', specialty: '', expected_duration: 60, billing_code: '' });
      loadData();
    } catch (e: any) {
      alert(typeof e.message === 'string' ? e.message : JSON.stringify(e));
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-black text-slate-900">OT Administration</h1>
        <p className="text-slate-500 mt-1">Configure reference data for the Operating Theatre module</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Operating Rooms Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center gap-3 bg-slate-50">
            <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg"><Building size={20} /></div>
            <h2 className="text-lg font-bold text-slate-800">Operating Rooms</h2>
          </div>
          
          <div className="p-5">
            <form onSubmit={handleCreateRoom} className="space-y-4 mb-8 p-4 bg-slate-50 rounded-xl border border-slate-100">
              <h3 className="text-sm font-semibold text-slate-600 mb-3 flex items-center gap-2"><Plus size={16}/> Add New Room</h3>
              <div className="grid grid-cols-2 gap-4">
                <input required placeholder="Room Code (e.g. OR-1)" value={newRoom.room_code} onChange={e => setNewRoom({...newRoom, room_code: e.target.value})} className="px-3 py-2 text-sm border border-slate-200 rounded-lg" />
                <input required placeholder="Room Name" value={newRoom.room_name} onChange={e => setNewRoom({...newRoom, room_name: e.target.value})} className="px-3 py-2 text-sm border border-slate-200 rounded-lg" />
                <input required placeholder="Department" value={newRoom.department} onChange={e => setNewRoom({...newRoom, department: e.target.value})} className="px-3 py-2 text-sm border border-slate-200 rounded-lg" />
                <button type="submit" className="bg-indigo-600 text-white font-medium rounded-lg text-sm flex items-center justify-center gap-2 hover:bg-indigo-700">
                  <Save size={16} /> Save Room
                </button>
              </div>
            </form>

            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-600 mb-3">Existing Rooms ({rooms.length})</h3>
              {rooms.map(r => (
                <div key={r.id} className="p-3 border border-slate-100 rounded-lg flex justify-between items-center bg-white hover:border-indigo-100 transition-colors">
                  <div>
                    <span className="font-bold text-slate-800 text-sm">{r.room_code}</span>
                    <span className="text-slate-500 text-xs ml-2">{r.room_name}</span>
                  </div>
                  <span className="text-xs px-2 py-1 bg-green-50 text-green-700 rounded-full font-medium">{r.status}</span>
                </div>
              ))}
              {rooms.length === 0 && <p className="text-sm text-slate-400">No operating rooms configured.</p>}
            </div>
          </div>
        </div>

        {/* Procedures Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center gap-3 bg-slate-50">
            <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg"><BriefcaseMedical size={20} /></div>
            <h2 className="text-lg font-bold text-slate-800">Surgical Procedures</h2>
          </div>
          
          <div className="p-5">
            <form onSubmit={handleCreateProcedure} className="space-y-4 mb-8 p-4 bg-slate-50 rounded-xl border border-slate-100">
              <h3 className="text-sm font-semibold text-slate-600 mb-3 flex items-center gap-2"><Plus size={16}/> Add New Procedure</h3>
              <div className="grid grid-cols-2 gap-4">
                <input required placeholder="Code (e.g. CABG-01)" value={newProcedure.procedure_code} onChange={e => setNewProcedure({...newProcedure, procedure_code: e.target.value})} className="px-3 py-2 text-sm border border-slate-200 rounded-lg" />
                <input required placeholder="Procedure Name" value={newProcedure.procedure_name} onChange={e => setNewProcedure({...newProcedure, procedure_name: e.target.value})} className="px-3 py-2 text-sm border border-slate-200 rounded-lg" />
                <input required placeholder="Specialty" value={newProcedure.specialty} onChange={e => setNewProcedure({...newProcedure, specialty: e.target.value})} className="px-3 py-2 text-sm border border-slate-200 rounded-lg" />
                <input required placeholder="Billing Code" value={newProcedure.billing_code} onChange={e => setNewProcedure({...newProcedure, billing_code: e.target.value})} className="px-3 py-2 text-sm border border-slate-200 rounded-lg" />
                <div className="flex gap-2 col-span-2">
                  <input type="number" required placeholder="Duration (min)" value={newProcedure.expected_duration} onChange={e => setNewProcedure({...newProcedure, expected_duration: parseInt(e.target.value)})} className="px-3 py-2 text-sm border border-slate-200 rounded-lg w-1/2" />
                  <button type="submit" className="bg-emerald-600 text-white font-medium rounded-lg text-sm flex-1 flex items-center justify-center gap-2 hover:bg-emerald-700">
                    <Save size={16} /> Save
                  </button>
                </div>
              </div>
            </form>

            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-600 mb-3">Existing Procedures ({procedures.length})</h3>
              {procedures.map(p => (
                <div key={p.id} className="p-3 border border-slate-100 rounded-lg flex justify-between items-center bg-white hover:border-emerald-100 transition-colors">
                  <div>
                    <span className="font-bold text-slate-800 text-sm">{p.procedure_code}</span>
                    <span className="text-slate-500 text-xs ml-2">{p.procedure_name}</span>
                  </div>
                  <span className="text-xs text-slate-400">{p.expected_duration}m</span>
                </div>
              ))}
              {procedures.length === 0 && <p className="text-sm text-slate-400">No surgical procedures configured.</p>}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
