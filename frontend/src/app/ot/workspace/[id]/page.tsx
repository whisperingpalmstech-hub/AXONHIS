"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { otApi } from '@/lib/ot-api';
import { SurgerySchedule, SurgeryStatus } from '@/types/ot';
import { Play, Square, Pause, User, Building, BriefcaseMedical, Clock, ArrowLeft, FileText, Plus } from 'lucide-react';

export default function OTWorkspacePage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const id = params.id;
  
  const [schedule, setSchedule] = useState<SurgerySchedule | null>(null);
  const [notes, setNotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New Note Form State
  const [noteContent, setNoteContent] = useState('');
  const [noteType, setNoteType] = useState('operative_note');
  const [savingNote, setSavingNote] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [scheduleData, notesData] = await Promise.all([
          otApi.getSchedule(id),
          otApi.getNotes(id).catch(() => []) // Handle case where notes don't exist yet gracefully
        ]);
        setSchedule(scheduleData);
        setNotes(notesData || []);
      } catch (err) {
        console.error("Failed to load workspace data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const updateStatus = async (newStatus: SurgeryStatus) => {
    if (!schedule) return;
    try {
      const updated = await otApi.updateSchedule(schedule.id, { status: newStatus });
      setSchedule({ ...schedule, status: updated.status });
    } catch (err) {
      alert("Failed to update status");
    }
  };

  const handleCreateNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteContent.trim()) return;
    
    setSavingNote(true);
    try {
      const newNote = await otApi.createNote({
        schedule_id: id,
        note_type: noteType,
        content: noteContent
      });
      setNotes([newNote, ...notes]);
      setNoteContent('');
    } catch (err) {
      alert("Failed to save note. Please try again.");
    } finally {
      setSavingNote(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500 font-medium">Loading Workspace...</div>;
  }

  if (!schedule) {
    return <div className="p-12 text-center text-rose-500 font-bold">Surgery Schedule not found.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push('/ot')} className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-500">
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-3xl font-black text-slate-900">Surgery Workspace</h1>
            <p className="text-slate-500 font-medium mt-1">Operational control and documentation</p>
          </div>
        </div>
        <div className="bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-200">
          <span className="text-xs uppercase tracking-wider font-bold text-slate-400 mr-2">Status:</span>
          <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-widest ${
            schedule.status === SurgeryStatus.IN_PROGRESS ? 'bg-indigo-100 text-indigo-700' :
            schedule.status === SurgeryStatus.COMPLETED ? 'bg-emerald-100 text-emerald-700' :
            'bg-slate-100 text-slate-700'
          }`}>
            {schedule.status}
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Info Card */}
        <div className="bg-white shadow-sm border border-slate-200 rounded-2xl overflow-hidden p-6 space-y-6 lg:h-fit">
          <h2 className="font-bold text-lg text-slate-800 border-b border-slate-100 pb-3">Surgery Details</h2>
          
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <User className="text-slate-400 mt-0.5" size={18} />
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Patient</p>
                <p className="font-semibold text-slate-800 break-all text-sm mt-0.5">{schedule.patient_id}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <BriefcaseMedical className="text-slate-400 mt-0.5" size={18} />
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Procedure</p>
                <p className="font-semibold text-slate-800 break-all text-sm mt-0.5">{schedule.procedure_id}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Building className="text-slate-400 mt-0.5" size={18} />
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Operating Room</p>
                <p className="font-semibold text-slate-800 break-all text-sm mt-0.5">{schedule.operating_room_id}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Clock className="text-slate-400 mt-0.5" size={18} />
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Scheduled Time</p>
                <p className="font-semibold text-slate-800 text-sm mt-0.5">
                  {new Date(schedule.scheduled_start_time).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Live Controls & Notes */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="bg-gradient-to-br from-slate-900 to-indigo-950 rounded-2xl p-8 shadow-lg text-white">
            <h2 className="font-bold text-xl mb-6">Workflow Controls</h2>
            
            <div className="flex items-center gap-4">
              <button 
                onClick={() => updateStatus(SurgeryStatus.PREPARING)}
                disabled={schedule.status === SurgeryStatus.COMPLETED}
                className="flex-1 bg-white/10 hover:bg-white/20 transition-all py-4 rounded-xl flex flex-col items-center justify-center gap-2 disabled:opacity-50"
              >
                <Square className="text-amber-400" size={24} />
                <span className="font-semibold text-sm">Preparing</span>
              </button>
              
              <button 
                onClick={() => updateStatus(SurgeryStatus.IN_PROGRESS)}
                disabled={schedule.status === SurgeryStatus.COMPLETED}
                className="flex-1 bg-indigo-600 hover:bg-indigo-500 transition-all py-4 rounded-xl flex flex-col items-center justify-center gap-2 shadow-lg shadow-indigo-500/30 disabled:opacity-50"
              >
                <Play className="text-white" size={24} />
                <span className="font-semibold text-sm">Start Surgery</span>
              </button>
              
              <button 
                onClick={() => updateStatus(SurgeryStatus.COMPLETED)}
                disabled={schedule.status === SurgeryStatus.COMPLETED}
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 transition-all py-4 rounded-xl flex flex-col items-center justify-center gap-2 shadow-lg shadow-emerald-500/30 disabled:opacity-50"
              >
                <Pause className="text-white fill-current" size={24} />
                <span className="font-semibold text-sm">Complete</span>
              </button>
            </div>
          </div>

          <div className="bg-white shadow-sm border border-slate-200 rounded-2xl overflow-hidden p-8">
            <h3 className="font-bold text-slate-800 text-lg mb-4 flex items-center gap-2">
              <FileText className="text-indigo-500" size={20} />
              Surgical Documentation
            </h3>
            
            <form onSubmit={handleCreateNote} className="mb-8 space-y-4 border border-slate-200 p-5 rounded-xl bg-slate-50/50">
              <div className="flex gap-4">
                <select 
                  value={noteType}
                  onChange={e => setNoteType(e.target.value)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm bg-white outline-none focus:border-indigo-500 font-medium text-slate-700"
                >
                  <option value="operative_note">Operative Note</option>
                  <option value="procedure_summary">Procedure Summary</option>
                  <option value="complication_note">Complication Note</option>
                </select>
              </div>
              <textarea 
                required
                value={noteContent}
                onChange={e => setNoteContent(e.target.value)}
                placeholder="Write your surgical notes, findings, and documentation here..."
                className="w-full h-32 px-4 py-3 border border-slate-200 rounded-lg text-sm bg-white outline-none focus:border-indigo-500 resize-none font-mono"
              />
              <div className="flex justify-end">
                <button 
                  type="submit" 
                  disabled={savingNote || !noteContent.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 flex items-center gap-2 shadow-sm"
                >
                  <Plus size={16} />
                  {savingNote ? 'Saving...' : 'Save Record'}
                </button>
              </div>
            </form>

            <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-2">Previous Records ({notes.length})</h4>
              {notes.length === 0 ? (
                <p className="text-slate-400 text-center py-6 border border-dashed border-slate-200 rounded-xl">No documentation recorded yet.</p>
              ) : (
                <div className="space-y-3">
                  {notes.map(note => (
                    <div key={note.id} className="p-4 rounded-xl border border-slate-100 bg-white shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded border ${
                          note.note_type === 'complication_note' ? 'bg-rose-50 border-rose-100 text-rose-600' :
                          note.note_type === 'procedure_summary' ? 'bg-blue-50 border-blue-100 text-blue-600' :
                          'bg-indigo-50 border-indigo-100 text-indigo-600'
                        }`}>
                          {note.note_type.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-slate-400 font-medium">{new Date(note.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-sm text-slate-700 font-mono whitespace-pre-wrap">{note.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}
