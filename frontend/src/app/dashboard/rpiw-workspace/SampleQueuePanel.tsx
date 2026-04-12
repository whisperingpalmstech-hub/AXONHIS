"use client";
import React, { useState } from "react";
import { Droplet, Info, User, FlaskConical, MapPin, Clock } from "lucide-react";

const SAMPLES = [
  { id: "S1", patient: "Jane Doe", uhid: "PX9283", test: "Complete Blood Count", container: "EDTA (Lavender)", status: "Pending", priority: "STAT" },
  { id: "S2", patient: "Jane Doe", uhid: "PX9283", test: "Kidney Function Test", container: "SST (Yellow)", status: "Pending", priority: "ROUTINE" },
  { id: "S3", patient: "Jane Doe", uhid: "PX9283", test: "HBA1C", container: "EDTA (Lavender)", status: "Collected", priority: "ROUTINE" }
];

export default function SampleQueuePanel({ patientUhid }: { patientUhid: string }) {
  const [samples, setSamples] = useState(SAMPLES);

  return (
    <div className="space-y-4">
      <div className="bg-blue-50/50 p-4 rounded-2xl border border-blue-100 mb-6 flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-200">
           <Droplet size={24} />
        </div>
        <div>
           <div className="text-sm font-black text-slate-800 tracking-tight">Pending Collections</div>
           <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{samples.filter(s => s.status === "Pending").length} samples remaining for current patient</div>
        </div>
      </div>

      <div className="space-y-4 max-h-80 overflow-y-auto pr-1 custom-scrollbar">
        {samples.map(s => (
          <div key={s.id} className={`p-4 rounded-xl border border-slate-200 transition-all ${
            s.status === "Collected" ? "bg-slate-50 border-slate-100" : "bg-white hover:border-blue-300"
          }`}>
             <div className="flex justify-between items-start mb-2">
                <div>
                   <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-black text-slate-800 tracking-tight">{s.test}</span>
                      {s.priority === "STAT" && (
                         <span className="bg-rose-100 text-rose-700 text-[9px] font-black px-1.5 py-0.5 rounded-md animate-pulse">STAT</span>
                      )}
                   </div>
                   <div className="flex gap-2 items-center text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                      <FlaskConical size={10} className="text-blue-500"/> {s.container}
                   </div>
                </div>
                {s.status === "Collected" ? (
                   <span className="bg-emerald-100 text-emerald-700 text-[9px] font-black px-2 py-1 rounded-md uppercase tracking-wider">DONE</span>
                ) : (
                   <button className="bg-blue-600 text-white text-[10px] font-black px-3 py-1.5 rounded-lg hover:bg-blue-700 shadow-md shadow-blue-100">COLLECT</button>
                )}
             </div>
             
             {s.status === "Pending" && (
                <div className="mt-3 flex gap-4 text-[9px] font-bold text-slate-400 border-t border-slate-50 pt-3">
                   <div className="flex items-center gap-1 uppercase tracking-widest"><Clock size={10}/> Ordered 22m ago</div>
                   <div className="flex items-center gap-1 uppercase tracking-widest"><Info size={10}/> Fasting Required</div>
                </div>
             )}
          </div>
        ))}
      </div>

      <div className="bg-slate-900 p-4 rounded-xl text-white flex items-center justify-between shadow-xl mt-6">
         <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">
               <User size={16}/>
            </div>
            <div>
               <div className="text-[10px] font-black uppercase text-slate-400">Sample Phlebotomist</div>
               <div className="text-xs font-bold font-mono">STAFF-PHL-001</div>
            </div>
         </div>
         <div className="flex items-center gap-2 text-[10px] font-black uppercase text-emerald-400 tracking-widest">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span> Terminal Ready
         </div>
      </div>
    </div>
  );
}
