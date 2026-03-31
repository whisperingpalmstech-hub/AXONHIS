"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { otApi } from '@/lib/ot-api';
import { OTDashboardSummary, SurgeryStatus, SurgeryPriority, OperatingRoom, SurgicalProcedure } from '@/types/ot';
import { 
  Activity, 
  Calendar, 
  Clock, 
  AlertCircle, 
  Play, 
  CheckCircle2, 
  Plus,
  X,
  User,
  MapPin
} from 'lucide-react';
import { WorkflowPipeline } from "@/components/ui/WorkflowPipeline";

const OTDashboard = () => {
  const router = useRouter();
  const [summary, setSummary] = useState<OTDashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [rooms, setRooms] = useState<OperatingRoom[]>([]);
  const [procedures, setProcedures] = useState<SurgicalProcedure[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [encounters, setEncounters] = useState<any[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    patient_id: "",
    encounter_id: "",
    procedure_id: "",
    operating_room_id: "",
    scheduled_start_time: "",
    scheduled_end_time: "",
    priority: SurgeryPriority.ELECTIVE,
  });

  const fetchDashboard = async () => {
    try {
      const data = await otApi.getDashboardSummary();
      setSummary(data);
    } catch (error) {
      console.error("Failed to fetch OT summary:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const openScheduleModal = async () => {
    try {
      const { api } = await import('@/lib/api');
      const [roomData, procData, patientData, encounterData] = await Promise.all([
        otApi.getRooms(),
        otApi.getProcedures(),
        api.get<any[]>('/patients/'),
        api.get<any[]>('/encounters/'),
      ]);
      setRooms(roomData);
      setProcedures(procData);
      setPatients(patientData);
      setEncounters(encounterData);
    } catch (e) {
      console.error("Failed to load metadata", e);
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await otApi.scheduleSurgery(formData);
      setIsModalOpen(false);
      setFormData({
        patient_id: "", encounter_id: "", procedure_id: "",
        operating_room_id: "", scheduled_start_time: "", scheduled_end_time: "",
        priority: SurgeryPriority.ELECTIVE,
      });
      await fetchDashboard();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case SurgeryStatus.SCHEDULED: return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case SurgeryStatus.PREPARING: return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case SurgeryStatus.IN_PROGRESS: return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
      case SurgeryStatus.COMPLETED: return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
      default: return 'bg-slate-500/10 text-slate-500 border-slate-500/20';
    }
  };

  const getRoomStatusStyle = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'occupied': return 'bg-amber-500 text-white border-amber-600';
      case 'cleaning': return 'bg-blue-500 text-white border-blue-600';
      case 'maintenance': return 'bg-rose-500 text-white border-rose-600';
      default: return 'bg-emerald-500 text-white border-emerald-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-slate-50/50 min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-700">
            Operating Theatre Command Center
          </h1>
          <p className="text-slate-500 text-sm mt-1">Real-time OT utilization and surgical workflows</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => router.push('/ot/settings')}
            className="flex items-center gap-2 px-4 py-2 bg-white text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50 transition-all shadow-sm cursor-pointer"
          >
            <Activity size={18} />
            <span>Admin</span>
          </button>
          <button 
            onClick={openScheduleModal}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200 cursor-pointer"
          >
            <Plus size={18} />
            <span>Schedule Surgery</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-2">
        <WorkflowPipeline 
          title="Operating Theatre Pipeline" 
          colorScheme="amber"
          steps={[
            { label: "Surgery Request", status: "done" },
            { label: "OT Scheduling", status: "active" },
            { label: "Pre-op Checklist", status: "pending" },
            { label: "Blood Request", status: "pending" },
            { label: "Surgery Execution", status: "pending" },
            { label: "Post-op & Recovery", status: "pending" }
          ]} 
        />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon={<Calendar className="text-blue-500" />}
          label="Today's Surgeries"
          value={summary?.today_count || 0}
          trend="+2 vs yesterday"
        />
        <StatCard 
          icon={<Activity className="text-emerald-500" />}
          label="Active Rooms"
          value={summary?.room_usage?.filter(r => r.status === 'occupied').length || 0}
          subValue={`across ${summary?.room_usage?.length || 0} theaters`}
        />
        <StatCard 
          icon={<Clock className="text-amber-500" />}
          label="Upcoming Cases"
          value={summary?.upcoming?.length || 0}
          subValue="Next 4 hours"
        />
        <StatCard 
          icon={<AlertCircle className="text-rose-500" />}
          label="Emergency Cases"
          value={summary?.emergency?.length || 0}
          trend={summary?.emergency?.length ? "Critical" : "Clear"}
          critical={!!summary?.emergency?.length}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming List */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-semibold text-slate-800">Surgery Schedule</h3>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Next 10 Cases</span>
          </div>
          <div className="divide-y divide-slate-50">
            {(summary?.today_surgeries || []).length === 0 && (
              <div className="p-12 text-center text-slate-400">
                <Calendar size={32} className="mx-auto mb-3 opacity-50" />
                <p className="font-medium">No surgeries scheduled</p>
                <p className="text-sm mt-1">Click &quot;Schedule Surgery&quot; to book a procedure</p>
              </div>
            )}
            {(summary?.today_surgeries || [])
              .map((surgery: any) => (
              <div key={surgery.id} className="p-6 hover:bg-slate-50/50 transition-colors group cursor-pointer"
                onClick={() => router.push(`/ot/workspace/${surgery.id}`)}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(surgery.status)}`}>
                        {surgery.status?.replace('_', ' ')}
                      </span>
                      <span className="text-sm font-semibold text-slate-900">
                        {surgery.procedure?.procedure_name || `Procedure ${surgery.procedure_id?.slice(0, 8)}`}
                      </span>
                    </div>
                    <div className="text-sm text-slate-500 flex items-center gap-3">
                      <span className="flex items-center gap-1.5"><Clock size={14} /> {new Date(surgery.scheduled_start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      <span className="flex items-center gap-1.5"><MapPin size={14} /> Room: {surgery.operating_room?.room_code || 'TBD'}</span>
                    </div>
                  </div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 hover:bg-white rounded-lg border border-slate-200 shadow-sm transition-all text-slate-700">
                      <Play size={16} />
                    </button>
                    <button className="p-2 hover:bg-white rounded-lg border border-slate-200 shadow-sm transition-all text-slate-700">
                      <CheckCircle2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* OT Status Right Panel */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="font-semibold text-slate-800 mb-4">Theater Status</h3>
            <div className="space-y-4">
              {(summary?.room_usage || []).length === 0 && (
                <p className="text-sm text-slate-400 text-center py-4">No rooms configured</p>
              )}
              {summary?.room_usage?.map((room) => (
                <div key={room.id} className="p-4 rounded-lg border border-slate-100 bg-slate-50/50">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-sm text-slate-700">{room.code}</span>
                    <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full border ${getRoomStatusStyle(room.status)}`}>
                      {room.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 font-medium truncate">{room.name}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Schedule Surgery Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-xl rounded-3xl shadow-2xl overflow-hidden">
            <div className="px-8 py-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <h3 className="text-xl font-black text-slate-800">New Surgery Schedule</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors cursor-pointer">
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 ml-1">
                    <User size={14} /> Patient
                  </label>
                  <select 
                    required
                    value={formData.patient_id}
                    onChange={(e) => setFormData({...formData, patient_id: e.target.value})}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm"
                  >
                    <option value="">Select Patient</option>
                    {patients.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.first_name} {p.last_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 ml-1">
                    <Activity size={14} /> Encounter
                  </label>
                  <select 
                    required
                    value={formData.encounter_id}
                    onChange={(e) => setFormData({...formData, encounter_id: e.target.value})}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm"
                  >
                    <option value="">Select Encounter</option>
                    {encounters
                      .filter(e => !formData.patient_id || e.patient_id === formData.patient_id)
                      .map(e => (
                      <option key={e.id} value={e.id}>
                        {e.encounter_type} - {new Date(e.created_at || Date.now()).toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 ml-1">
                  <Activity size={14} /> Procedure
                </label>
                <select 
                  required
                  value={formData.procedure_id}
                  onChange={(e) => setFormData({...formData, procedure_id: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm"
                >
                  <option value="">Select Procedure</option>
                  {procedures.map(p => <option key={p.id} value={p.id}>{p.procedure_name} ({p.procedure_code})</option>)}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 ml-1">
                  <MapPin size={14} /> Operating Theater
                </label>
                <select 
                  required
                  value={formData.operating_room_id}
                  onChange={(e) => setFormData({...formData, operating_room_id: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm"
                >
                  <option value="">Select Room</option>
                  {rooms.map(r => <option key={r.id} value={r.id}>{r.room_name} ({r.room_code})</option>)}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 ml-1">
                    <Clock size={14} /> Start Time
                  </label>
                  <input 
                    type="datetime-local" 
                    required
                    value={formData.scheduled_start_time}
                    onChange={(e) => setFormData({...formData, scheduled_start_time: e.target.value})}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm" 
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 ml-1">
                    <Clock size={14} /> End Time
                  </label>
                  <input 
                    type="datetime-local" 
                    required
                    value={formData.scheduled_end_time}
                    onChange={(e) => setFormData({...formData, scheduled_end_time: e.target.value})}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none text-sm" 
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider ml-1">Priority</label>
                <div className="flex gap-3">
                  {Object.values(SurgeryPriority).map(p => (
                    <button 
                      key={p} type="button"
                      onClick={() => setFormData({...formData, priority: p})}
                      className={`flex-1 py-3 rounded-xl text-xs font-bold uppercase tracking-wider border transition-all cursor-pointer ${
                        formData.priority === p 
                          ? p === SurgeryPriority.EMERGENCY 
                            ? 'bg-rose-500 text-white border-rose-600' 
                            : p === SurgeryPriority.URGENT 
                              ? 'bg-amber-500 text-white border-amber-600'
                              : 'bg-indigo-500 text-white border-indigo-600'
                          : 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-4">
                <button 
                  type="submit" 
                  disabled={submitting}
                  className="w-full py-4 bg-indigo-600 text-white font-black rounded-2xl shadow-xl shadow-indigo-100 hover:bg-indigo-700 transition-all hover:scale-[1.01] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? "Scheduling..." : "Confirm Schedule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const StatCard = ({ icon, label, value, trend, subValue, critical }: any) => (
  <div className={`p-6 bg-white rounded-xl border ${critical ? 'border-rose-100 shadow-rose-50/50' : 'border-slate-200'} shadow-sm relative overflow-hidden`}>
    {critical && <div className="absolute top-0 right-0 p-2 bg-rose-500/10 text-rose-500"><AlertCircle size={16} /></div>}
    <div className="flex items-start justify-between mb-4">
      <div className="p-3 bg-slate-50 rounded-lg">{icon}</div>
      {trend && <span className={`text-[10px] font-bold ${critical ? 'text-rose-600' : 'text-emerald-600'}`}>{trend}</span>}
    </div>
    <div className="space-y-1">
      <p className="text-3xl font-bold text-slate-900">{value}</p>
      <p className="text-sm font-medium text-slate-500">{label}</p>
      {subValue && <p className="text-[10px] text-slate-400 font-medium">{subValue}</p>}
    </div>
  </div>
);

export default OTDashboard;
