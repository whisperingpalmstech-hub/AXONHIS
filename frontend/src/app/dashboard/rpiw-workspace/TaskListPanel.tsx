"use client";
import React, { useState } from "react";
import { ListChecks, AlertTriangle, Clock, MapPin, UserCheck, Stethoscope } from "lucide-react";

export default function TaskListPanel({ patientUhid }: { patientUhid: string }) {
  const [tasks, setTasks] = useState([
    { id: 101, title: "Wound Dressing Change", category: "NURSING", priority: "HIGH", due: "10:30", status: "PENDING" },
    { id: 102, title: "Collect Blood Sample for CBC", category: "SAMPLE", priority: "ROUTINE", due: "14:00", status: "PENDING" },
    { id: 103, title: "Update Care Plan Note", category: "DOCUMENTATION", priority: "LOW", due: "18:00", status: "PENDING" },
    { id: 104, title: "Patient Transfer to OT", category: "LOGISTICS", priority: "CRITICAL", due: "ASAP", status: "PENDING" }
  ]);

  const toggleTask = (id: number) => {
    setTasks(tasks.map(t => t.id === id ? { ...t, status: t.status === "DONE" ? "PENDING" : "DONE" } : t));
  };

  return (
    <div className="space-y-4">
      {tasks.map(t => (
        <div key={t.id} className={`group p-4 rounded-xl border border-slate-200 hover:shadow-md transition-all ${
          t.status === "DONE" ? "bg-slate-50 border-slate-100 opacity-60" : 
          t.priority === "CRITICAL" ? "bg-rose-50 border-rose-100" : "bg-white"
        }`}>
          <div className="flex items-start gap-4">
            <div 
              onClick={() => toggleTask(t.id)}
              className={`w-6 h-6 rounded-md border-2 transition-all flex items-center justify-center cursor-pointer ${
                t.status === "DONE" ? "bg-emerald-500 border-emerald-500 text-white" : 
                t.priority === "CRITICAL" ? "border-rose-400 bg-white" : "border-slate-300 bg-white hover:border-blue-500"
              }`}
            >
              <UserCheck size={14} className={t.status === "DONE" ? "opacity-100" : "opacity-0"} />
            </div>

            <div className="flex-1">
              <div className="flex justify-between items-start">
                <div className="flex flex-col">
                  <span className={`text-sm font-black text-slate-800 tracking-tight ${t.status === "DONE" ? "line-through" : ""}`}>{t.title}</span>
                  <div className="flex gap-2 items-center text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">
                    <span className="flex items-center gap-1"><Stethoscope size={10} className="text-blue-500"/> {t.category}</span>
                    <span className="flex items-center gap-1"><Clock size={10} className="text-blue-500"/> {t.due}</span>
                  </div>
                </div>
                {t.priority === "CRITICAL" && t.status !== "DONE" && (
                   <span className="bg-rose-100 text-rose-700 text-[9px] font-black px-1.5 py-0.5 rounded-md uppercase tracking-wider flex items-center gap-1 animate-pulse">
                     <AlertTriangle size={10}/> STAT
                   </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
      <div className="flex items-center justify-center pt-2">
        <button className="text-[10px] font-black text-blue-600 uppercase tracking-widest hover:text-blue-700 transition-all flex items-center gap-1">
          <ListChecks size={14}/> View Full List
        </button>
      </div>
    </div>
  );
}
