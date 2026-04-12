"use client";
import React, { useState } from "react";
import { Activity, Thermometer, Wind, Heart } from "lucide-react";

export default function VitalsRecordingPanel({ patientUhid }: { patientUhid: string }) {
  const [vitals, setVitals] = useState({
    temp: "37.2",
    pulse: "82",
    bp_sys: "120",
    bp_dia: "80",
    spo2: "98",
    resp: "18"
  });

  const [saving, setSaving] = useState(false);

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => setSaving(false), 1000);
  };

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div className="flex items-center gap-2 mb-2">
            <Thermometer size={16} className="text-orange-500" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Temperature</span>
          </div>
          <div className="flex items-baseline gap-1">
            <input 
              type="text" 
              value={vitals.temp} 
              onChange={e => setVitals({...vitals, temp: e.target.value})}
              className="text-2xl font-black bg-transparent w-16 outline-none text-slate-800"
            />
            <span className="text-xs text-slate-400 font-bold">°C</span>
          </div>
        </div>

        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div className="flex items-center gap-2 mb-2">
            <Heart size={16} className="text-rose-500" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Pulse Rate</span>
          </div>
          <div className="flex items-baseline gap-1">
            <input 
              type="text" 
              value={vitals.pulse} 
              onChange={e => setVitals({...vitals, pulse: e.target.value})}
              className="text-2xl font-black bg-transparent w-16 outline-none text-slate-800"
            />
            <span className="text-xs text-slate-400 font-bold">bpm</span>
          </div>
        </div>

        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 col-span-2">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={16} className="text-blue-500" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Blood Pressure</span>
          </div>
          <div className="flex items-center gap-3">
            <input 
              type="text" 
              value={vitals.bp_sys} 
              onChange={e => setVitals({...vitals, bp_sys: e.target.value})}
              className="text-2xl font-black bg-transparent w-14 text-center outline-none text-slate-800"
            />
            <span className="text-xl text-slate-300 font-black">/</span>
            <input 
              type="text" 
              value={vitals.bp_dia} 
              onChange={e => setVitals({...vitals, bp_dia: e.target.value})}
              className="text-2xl font-black bg-transparent w-14 text-center outline-none text-slate-800"
            />
            <span className="text-xs text-slate-400 font-bold ml-2">mmHg</span>
          </div>
        </div>

        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div className="flex items-center gap-2 mb-2">
            <Wind size={16} className="text-emerald-500" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">SpO2</span>
          </div>
          <div className="flex items-baseline gap-1">
            <input 
              type="text" 
              value={vitals.spo2} 
              onChange={e => setVitals({...vitals, spo2: e.target.value})}
              className="text-2xl font-black bg-transparent w-14 outline-none text-slate-800"
            />
            <span className="text-xs text-slate-400 font-bold">%</span>
          </div>
        </div>

        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={16} className="text-purple-500" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Resp Rate</span>
          </div>
          <div className="flex items-baseline gap-1">
            <input 
              type="text" 
              value={vitals.resp} 
              onChange={e => setVitals({...vitals, resp: e.target.value})}
              className="text-2xl font-black bg-transparent w-14 outline-none text-slate-800"
            />
            <span className="text-xs text-slate-400 font-bold">/min</span>
          </div>
        </div>
      </div>

      <button 
        onClick={handleSave}
        disabled={saving}
        className={`w-full py-3 rounded-xl font-bold text-sm transition-all shadow-sm ${
          saving ? "bg-slate-100 text-slate-400 cursor-not-allowed" : "bg-blue-600 text-white hover:bg-blue-700 active:scale-[0.98] shadow-blue-100"
        }`}
      >
        {saving ? "🔄 Recording Vitals..." : "📥 Save Vital Readings"}
      </button>

      <p className="text-[10px] text-center text-slate-400 italic">Connected to AxonHIS IoT Monitoring Gateway (Simulated)</p>
    </div>
  );
}
