"use client";
import React, { useState } from "react";
import { Pill, CheckCircle2, Clock, MapPin, AlertCircle } from "lucide-react";

const INITIAL_MEDS = [
  { id: 1, name: "Ceftriaxone 1g", dosage: "1g", route: "IV", frequency: "BD", next_due: "14:00", scheduled_at: "14:00", status: "Due" },
  { id: 2, name: "Paracetamol 500mg", dosage: "500mg", route: "Oral", frequency: "TID", next_due: "18:00", scheduled_at: "18:00", status: "Planned" },
  { id: 3, name: "Metoprolol 25mg", dosage: "25mg", route: "Oral", frequency: "OD", next_due: "Tomorrow 08:00", scheduled_at: "08:00", status: "Planned" }
];

export default function MedicationAdminPanel({ patientUhid }: { patientUhid: string }) {
  const [meds, setMeds] = useState(INITIAL_MEDS);
  const [administering, setAdministering] = useState<number | null>(null);

  const administer = (id: number) => {
    setAdministering(id);
    setTimeout(() => {
      setMeds(meds.map(m => m.id === id ? { ...m, status: "Administered" } : m));
      setAdministering(null);
    }, 1200);
  };

  return (
    <div className="space-y-4">
      {meds.map(m => (
        <div key={m.id} className={`p-4 rounded-xl border border-slate-200 transition-all ${
          m.status === "Administered" ? "bg-emerald-50 border-emerald-100" : 
          m.status === "Due" ? "bg-amber-50 border-amber-100" : "bg-white"
        }`}>
          <div className="flex justify-between items-start mb-2">
            <div>
               <div className="flex items-center gap-2 mb-1">
                 <Pill size={16} className={m.status === "Administered" ? "text-emerald-500" : "text-blue-500"} />
                 <span className="text-sm font-black text-slate-800 tracking-tight">{m.name}</span>
               </div>
               <div className="flex gap-3 text-[10px] items-center text-slate-500 font-bold uppercase tracking-wider">
                 <span className="bg-white/80 p-1 rounded-md border border-slate-200">{m.dosage}</span>
                 <span className="bg-white/80 p-1 rounded-md border border-slate-200">{m.route}</span>
                 <span className="text-blue-600">Every {m.frequency}</span>
               </div>
            </div>
            {m.status === "Administered" ? (
              <span className="bg-emerald-100 text-emerald-700 text-[10px] font-black px-2 py-1 rounded-md uppercase tracking-widest flex items-center gap-1">
                <CheckCircle2 size={12}/> OK
              </span>
            ) : m.status === "Due" ? (
              <span className="bg-amber-100 text-amber-700 text-[10px] font-black px-2 py-1 rounded-md uppercase tracking-widest flex items-center gap-1 animate-pulse">
                <AlertCircle size={12}/> DUE NOW
              </span>
            ) : (
              <span className="bg-slate-100 text-slate-500 text-[10px] font-black px-2 py-1 rounded-md uppercase tracking-widest flex items-center gap-1">
                <Clock size={12}/> {m.next_due}
              </span>
            )}
          </div>
          
          {m.status !== "Administered" && (
            <button 
              onClick={() => administer(m.id)}
              disabled={administering !== null}
              className={`w-full mt-3 py-2 rounded-lg font-bold text-xs transition-all flex items-center justify-center gap-2 ${
                m.status === "Due" ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md shadow-blue-100" : "bg-slate-100 text-slate-500 hover:bg-slate-200"
              }`}
            >
              {administering === m.id ? (
                <>🔄 Confirming Barcode & Admin...</>
              ) : (
                <>💉 Mark as Administered</>
              )}
            </button>
          )}
        </div>
      ))}
      <div className="flex items-center justify-between text-[10px] text-slate-400 font-medium px-1">
        <span>Prescribed by: Dr. Axon</span>
        <span className="flex items-center gap-1 italic"><MapPin size={10}/> Pharmacy Verified ✅</span>
      </div>
    </div>
  );
}
