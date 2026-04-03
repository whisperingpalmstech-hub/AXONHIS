"use client";
import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Activity, HeartPulse, Droplets, Thermometer, ChevronLeft } from "lucide-react";

export default function IpdNursingNotesPage() {
  const params = useParams();
  const router = useRouter();
  const [newNote, setNewNote] = useState("");
  const [notes, setNotes] = useState([
    { title: "Night Shift Review", time: "06:00 AM", text: "Patient slept well. Complained of mild pain at 2 AM, administered PRN pain med.", user: "Nurse Alice" },
    { title: "Evening Shift Update", time: "Yesterday, 08:30 PM", text: "IV fluids running at 100ml/hr. No sign of respiratory distress.", user: "Nurse Bob" }
  ]);

  const handleRecordVitals = () => {
    const hr = prompt("Enter new Heart Rate (bpm):");
    const bp = prompt("Enter new Blood Pressure (sys/dia):");
    if (hr || bp) alert("Vitals recorded successfully to flowsheet!");
  };

  const handleSaveNote = () => {
    if (!newNote.trim()) return;
    setNotes([
      { title: "Progress Note Update", time: "Just now", text: newNote, user: "Current Nurse" },
      ...notes
    ]);
    setNewNote("");
  };
  
  return (
    <div className="p-6 h-full bg-slate-50 overflow-y-auto">
      {/* HEADER */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition shadow-sm">
            <ChevronLeft size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-black text-slate-800 tracking-tight">Nursing Flowsheet & Vitals</h1>
            <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">{params.id}</p>
          </div>
        </div>
        <button onClick={handleRecordVitals} className="px-5 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl shadow-md transition">+ Record Vitals</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* VITALS TRENDING */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-sm font-black text-slate-800 mb-6 flex items-center gap-2 uppercase tracking-wide border-b border-slate-100 pb-2">
              <Activity className="text-rose-500" size={18}/> Vitals Trending (Last 24h)
            </h2>
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="p-4 bg-rose-50/50 border border-rose-100 rounded-xl">
                 <p className="text-xs font-bold text-rose-800 mb-1 flex items-center gap-1"><HeartPulse size={12}/> Heart Rate</p>
                 <p className="text-2xl font-black text-rose-600">84 <span className="text-sm font-bold opacity-50">bpm</span></p>
              </div>
              <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-xl">
                 <p className="text-xs font-bold text-blue-800 mb-1 flex items-center gap-1"><Activity size={12}/> Blood Pressure</p>
                 <p className="text-2xl font-black text-blue-600">120/80</p>
              </div>
              <div className="p-4 bg-amber-50/50 border border-amber-100 rounded-xl">
                 <p className="text-xs font-bold text-amber-800 mb-1 flex items-center gap-1"><Thermometer size={12}/> Temperature</p>
                 <p className="text-2xl font-black text-amber-600">98.6 <span className="text-sm font-bold opacity-50">°F</span></p>
              </div>
              <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-xl">
                 <p className="text-xs font-bold text-emerald-800 mb-1 flex items-center gap-1"><Droplets size={12}/> SpO2</p>
                 <p className="text-2xl font-black text-emerald-600">98 <span className="text-sm font-bold opacity-50">%</span></p>
              </div>
            </div>
            
            <div className="h-48 flex items-end gap-2 pt-4">
               {/* Mock Graph Bars */}
               {[72, 75, 78, 80, 84, 82, 85, 88].map((val, i) => (
                 <div key={i} className="flex-1 bg-slate-100 rounded-t-md relative group hover:bg-slate-200 transition">
                    <div className="absolute bottom-0 w-full bg-rose-400 rounded-t-md transition-all" style={{ height: `${val}%` }}/>
                 </div>
               ))}
            </div>
            <div className="flex justify-between mt-2 text-[10px] font-bold text-slate-400">
              <span>00:00</span>
              <span>04:00</span>
              <span>08:00</span>
              <span>12:00</span>
              <span>16:00</span>
              <span>20:00</span>
              <span>Now</span>
            </div>
          </div>
        </div>

        {/* NURSING PROGRESS NOTES */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm h-full flex flex-col">
            <h2 className="text-sm font-black text-slate-800 mb-4 flex items-center gap-2 uppercase tracking-wide border-b border-slate-100 pb-2">
               Progress Notes
            </h2>
            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {notes.map((note, idx) => (
                <div key={idx} className="p-4 bg-slate-50 border border-slate-100 rounded-xl">
                  <div className="flex justify-between mb-2">
                    <span className="text-xs font-bold text-slate-700">{note.title}</span>
                    <span className="text-[10px] font-bold text-slate-400">{note.time}</span>
                  </div>
                  <p className="text-sm text-slate-600 mb-2">{note.text}</p>
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                    <div className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-[10px] font-bold">RN</div>
                    {note.user}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100">
              <textarea 
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Enter new nursing note..." 
                className="w-full text-sm p-3 border border-slate-200 rounded-xl resize-none focus:border-indigo-400 outline-none" 
                rows={3}
              />
              <button onClick={handleSaveNote} className="w-full mt-2 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-md transition text-sm">Save Note</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
