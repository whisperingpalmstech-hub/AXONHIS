"use client";
import React, { useEffect, useState } from "react";
import { Activity, Thermometer, Wind, Heart, TrendingUp, TrendingDown, Minus } from "lucide-react";

const VITAL_TRENDS = {
  temp: [37.2, 37.1, 37.0, 37.2, 37.3, 37.2],
  pulse: [82, 85, 88, 86, 84, 82],
  spo2: [98, 97, 98, 99, 98, 98]
};

export default function PatientMonitorPanel({ patientUhid }: { patientUhid: string }) {
  const [currentVitals, setCurrentVitals] = useState({ temp: 37.2, pulse: 82, spo2: 98 });
  const [trends, setTrends] = useState({ temp: "STABLE", pulse: "STABLE", spo2: "STABLE" });

  useEffect(() => {
    // Simulated real-time update
    const interval = setInterval(() => {
      setCurrentVitals(prev => ({
        temp: +(prev.temp + (Math.random() * 0.2 - 0.1)).toFixed(1),
        pulse: Math.floor(prev.pulse + (Math.random() * 4 - 2)),
        spo2: Math.min(100, Math.max(95, prev.spo2 + (Math.random() * 2 - 1)))
      }));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-6">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 rounded-2xl bg-orange-50 flex items-center justify-center text-orange-500 mb-2 border border-orange-100 shadow-sm">
            <Thermometer size={24} />
          </div>
          <span className="text-xl font-black text-slate-800 tracking-tight">{currentVitals.temp}°C</span>
          <span className={`text-[9px] font-black uppercase tracking-wider flex items-center gap-0.5 mt-1 ${
             currentVitals.temp > 37.5 ? "text-rose-500" : "text-slate-400"
          }`}>
             {currentVitals.temp > 37.5 ? <TrendingUp size={10}/> : <Minus size={10}/>} Stable
          </span>
        </div>

        <div className="flex flex-col items-center">
          <div className="w-16 h-16 rounded-2xl bg-rose-50 flex items-center justify-center text-rose-500 mb-2 border border-rose-100 shadow-sm relative overflow-hidden">
             <div className="absolute inset-0 bg-rose-400/10 animate-pulse"></div>
             <Heart size={24} className="relative z-10" />
          </div>
          <span className="text-xl font-black text-slate-800 tracking-tight">{currentVitals.pulse} bpm</span>
          <span className="text-[9px] font-black uppercase tracking-wider text-slate-400 flex items-center gap-0.5 mt-1">
             <TrendingUp size={10}/> Normal Range
          </span>
        </div>

        <div className="flex flex-col items-center">
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-500 mb-2 border border-emerald-100 shadow-sm">
            <Wind size={24} />
          </div>
          <span className="text-xl font-black text-slate-800 tracking-tight">{currentVitals.spo2}%</span>
          <span className="text-[9px] font-black uppercase tracking-wider text-emerald-600 flex items-center gap-0.5 mt-1">
             <CheckCircle2 size={10} className="inline"/> Optimal
          </span>
        </div>
      </div>

      <div className="bg-slate-900 rounded-xl p-4 overflow-hidden relative border-2 border-slate-800 shadow-xl">
        <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-2">
           <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
             <Activity size={14} className="text-emerald-400 animate-pulse"/> Live EKG Monitor (Simulated)
           </span>
           <span className="text-[10px] font-bold text-slate-600 tracking-tight uppercase">Connected: Bed 102 (ICU)</span>
        </div>
        <div className="h-24 w-full flex items-center justify-center relative">
          <svg className="w-full h-full text-emerald-400 overflow-visible" viewBox="0 0 400 100">
             <path 
               d="M0 50 L20 50 L25 40 L30 60 L35 50 L50 50 L55 30 L60 80 L65 50 L80 50 L85 45 L90 55 L95 50 L110 50 L115 20 L120 90 L125 50 L140 50 L145 45 L150 55 L155 50 L170 50 L175 40 L180 60 L185 50 L200 50 L205 30 L210 80 L215 50 L230 50 L235 45 L240 55 L245 50 L260 50 L265 20 L270 90 L275 50 L290 50 L295 45 L300 55 L305 50 L320 50 L325 40 L330 60 L335 50 L350 50 L355 30 L360 80 L365 50 L380 50 L385 45 L390 55 L400 50" 
               fill="none" 
               stroke="currentColor" 
               strokeWidth="2" 
               className="ekg-line"
             />
          </svg>
          <style jsx>{`
            .ekg-line {
              stroke-dasharray: 1000;
              stroke-dashoffset: 1000;
              animation: draw 2s linear infinite;
            }
            @keyframes draw {
               from { stroke-dashoffset: 1000; }
               to { stroke-dashoffset: 0; }
            }
          `}</style>
        </div>
        <div className="flex justify-between items-center mt-3 text-[9px] font-bold text-slate-600 uppercase tracking-widest">
           <span>Pulse: {currentVitals.pulse} bpm</span>
           <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 bg-rose-500 rounded-full animate-ping"></span> Recording Live Feed</span>
        </div>
      </div>
    </div>
  );
}

function CheckCircle2({ size, className }: { size: number, className?: string }) {
  return (
    <svg 
      width={size} height={size} viewBox="0 0 24 24" fill="none" 
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}
    >
      <circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>
    </svg>
  );
}
