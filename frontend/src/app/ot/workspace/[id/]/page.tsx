"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { otApi } from "@/lib/ot-api";
import { SurgerySchedule, SurgeryEvent, SurgeryEventType, SurgeryStatus } from "@/types/ot";
import { 
  Activity, 
  Clock, 
  User, 
  MapPin, 
  CheckCircle2, 
  Play, 
  RotateCcw, 
  FileText,
  AlertTriangle
} from "lucide-react";

export default function SurgeryWorkspace() {
  const { id } = useParams();
  const [surgery, setSurgery] = useState<SurgerySchedule | null>(null);
  const [events, setEvents] = useState<SurgeryEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!id) return;
      try {
        const [data, eventData] = await Promise.all([
          otApi.getSchedule(id as string),
          otApi.getEvents(id as string)
        ]);
        setSurgery(data);
        setEvents(eventData);
      } catch (e) {
        console.error("Failed to load surgery", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const handleRecordEvent = async (type: SurgeryEventType) => {
    try {
      await otApi.recordEvent({
        schedule_id: id,
        event_type: type,
        event_time: new Date().toISOString(),
      });
      // Refresh
      const [data, eventData] = await Promise.all([
        otApi.getSchedule(id as string),
        otApi.getEvents(id as string)
      ]);
      setSurgery(data);
      setEvents(eventData);
    } catch (e: any) {
      alert(`Error recording event: ${e.message}`);
    }
  };

  if (loading || !surgery) return null;

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      {/* HUD Header */}
      <div className="p-6 bg-slate-800/50 border-b border-slate-700 flex justify-between items-center backdrop-blur-md">
        <div className="flex items-center gap-6">
          <div className="flex flex-col">
            <span className="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em] mb-1">Operating Theater HUD</span>
            <h1 className="text-xl font-black flex items-center gap-2">
              <span className="p-1.5 bg-indigo-500 rounded text-white"><Activity size={18} /></span>
              {surgery.procedure?.procedure_name}
            </h1>
          </div>
          <div className="h-10 w-px bg-slate-700" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Theater Room</span>
            <span className="font-bold text-indigo-400">{surgery.room?.room_code}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Elapsed Time</span>
            <span className="text-2xl font-mono font-black text-emerald-400">01:24:45</span>
          </div>
          <button className="px-6 py-3 bg-rose-600 rounded-xl font-bold flex items-center gap-2 hover:bg-rose-700 shadow-xl shadow-rose-900/20">
            <AlertTriangle size={18} />
            EMERGENCY CALL
          </button>
        </div>
      </div>

      {/* Main Control Panel */}
      <div className="flex-1 overflow-hidden flex">
        {/* Left: Workflow Controls */}
        <div className="w-1/3 p-8 bg-slate-900 border-r border-slate-800 space-y-8 overflow-y-auto">
          <section className="space-y-4">
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">Intraoperative Workflow</h3>
            <div className="grid grid-cols-1 gap-4">
                <WorkflowButton 
                    label="Patient in Room" 
                    active={surgery.status !== SurgeryStatus.SCHEDULED}
                    completed={events.some(e => e.event_type === SurgeryEventType.PATIENT_IN_ROOM)}
                    onClick={() => handleRecordEvent(SurgeryEventType.PATIENT_IN_ROOM)}
                />
                <WorkflowButton 
                    label="Anesthesia Started" 
                    active={surgery.status === SurgeryStatus.PREPARING}
                    completed={events.some(e => e.event_type === SurgeryEventType.ANESTHESIA_STARTED)}
                    onClick={() => handleRecordEvent(SurgeryEventType.ANESTHESIA_STARTED)}
                />
                <WorkflowButton 
                    label="Incision Made" 
                    active={surgery.status === SurgeryStatus.PREPARING}
                    completed={events.some(e => e.event_type === SurgeryEventType.INCISION_MADE)}
                    onClick={() => handleRecordEvent(SurgeryEventType.INCISION_MADE)}
                />
                <WorkflowButton 
                    label="Procedure Completed" 
                    active={surgery.status === SurgeryStatus.IN_PROGRESS}
                    completed={events.some(e => e.event_type === SurgeryEventType.PROCEDURE_COMPLETED)}
                    onClick={() => handleRecordEvent(SurgeryEventType.PROCEDURE_COMPLETED)}
                />
                <WorkflowButton 
                    label="Patient Out Room" 
                    active={surgery.status === SurgeryStatus.COMPLETED}
                    completed={events.some(e => e.event_type === SurgeryEventType.PATIENT_OUT_ROOM)}
                    onClick={() => handleRecordEvent(SurgeryEventType.PATIENT_OUT_ROOM)}
                />
            </div>
          </section>

          <section className="space-y-4">
            <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              <QuickActionButton icon={<FileText size={16} />} label="Add Note" />
              <QuickActionButton icon={<RotateCcw size={16} />} label="Update Time" />
            </div>
          </section>
        </div>

        {/* Right: Monitoring & Logs */}
        <div className="flex-1 flex flex-col bg-black/20">
          <div className="flex-1 p-8 overflow-y-auto">
            <div className="max-w-3xl mx-auto space-y-8">
                {/* Event Log */}
                <div className="space-y-6">
                    <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">Live Event Log</h3>
                    <div className="space-y-4 relative">
                        <div className="absolute left-4 top-2 bottom-2 w-px bg-slate-800" />
                        {events.map((event, i) => (
                            <div key={event.id} className="relative pl-10 flex items-center gap-4 group">
                                <div className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-indigo-500 border-4 border-slate-900 group-last:bg-emerald-500 group-last:ring-4 group-last:ring-emerald-500/20" />
                                <span className="text-xs font-mono text-slate-500 uppercase">
                                    {new Date(event.event_time).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className="text-sm font-bold text-slate-200 uppercase tracking-tight">{event.event_type.replace(/_/g, ' ')}</span>
                            </div>
                        ))}
                        {events.length === 0 && <p className="text-slate-600 text-sm pl-10">Waiting for procedure start...</p>}
                    </div>
                </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const WorkflowButton = ({ label, active, completed, onClick }: any) => (
  <button 
    onClick={onClick}
    disabled={completed || !active}
    className={`p-6 rounded-2xl border transition-all flex items-center justify-between group ${
      completed ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
      active ? 'bg-slate-800 border-slate-700 border-b-4 border-b-indigo-500 hover:bg-slate-750 hover:scale-[1.02] text-white' :
      'bg-slate-900/50 border-slate-800 text-slate-600 grayscale opacity-50 cursor-not-allowed'
    }`}
  >
    <div className="flex items-center gap-4">
        {completed ? <CheckCircle2 size={24} /> : <Play size={24} className={active ? 'text-indigo-400 animate-pulse' : ''} />}
        <span className="font-black text-lg uppercase tracking-tight">{label}</span>
    </div>
    {completed && <span className="text-[10px] font-black uppercase tracking-widest opacity-50">Logged</span>}
  </button>
);

const QuickActionButton = ({ icon, label }: any) => (
  <button className="flex items-center gap-2 px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-xs font-bold uppercase tracking-widest text-slate-300 hover:bg-slate-700 transition-colors">
    {icon} {label}
  </button>
);
