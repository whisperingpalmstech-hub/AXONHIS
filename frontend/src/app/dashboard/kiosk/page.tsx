"use client";

import React, { useState, useEffect } from "react";
import { Users, Mic, UserX, Clock, Volume2, MonitorPlay } from "lucide-react";
import { kioskApi, TokenQueue } from "@/lib/kiosk-api";

export default function QueueDashboard() {
  const [tokens, setTokens] = useState<TokenQueue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  const fetchQueue = async () => {
    setLoading(true);
    try {
      setTokens(await kioskApi.getQueue());
    } catch(e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCall = async (tokenId: string) => {
    try {
      const res = await kioskApi.callPatient(tokenId);
      if ('speechSynthesis' in window) {
        const msg = new SpeechSynthesisUtterance(res.announcement);
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
      }
      fetchQueue();
    } catch(e: any) { alert(e.message); }
  };

  const handleComplete = async (tokenId: string) => {
    try {
      await kioskApi.updateStatus(tokenId, "Completed");
      fetchQueue();
    } catch(e: any) { alert(e.message); }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans p-6 overflow-y-auto w-full max-w-7xl mx-auto">
      
      {/* Header Glass Panel */}
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <MonitorPlay className="text-indigo-600" /> Queue Analytics & Signage
          </h1>
          <p className="text-slate-500 font-bold text-xs uppercase tracking-wider mt-1">
            Clinic Queue Flow & Global Wayfinding Announcer
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex flex-col items-end px-4 py-2">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Broadcasting to</span>
            <span className="text-emerald-600 font-bold text-sm flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div> Local Terminals
            </span>
          </div>
        </div>
      </div>

      {/* Vital Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[
          { label: "Total Waiting", value: tokens.filter(t => t.status === "Pending").length, icon: Users, color: "text-slate-500" },
          { label: "Calling Now", value: tokens.filter(t => t.status === "Calling").length, icon: Mic, color: "text-indigo-600" },
          { label: "Avg Wait Time", value: "11m", icon: Clock, color: "text-amber-500" },
          { label: "No Show", value: tokens.filter(t => t.status === "No Show").length, icon: UserX, color: "text-rose-500" }
        ].map((metric, idx) => (
          <div key={idx} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <div className={`flex items-center gap-2 font-bold text-xs uppercase tracking-wider mb-2 ${metric.color}`}>
              <metric.icon size={16} /> {metric.label}
            </div>
            <div className={`text-4xl font-black ${metric.color}`}>{metric.value}</div>
          </div>
        ))}
      </div>

      {/* Live Queue Grid */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-slate-50 p-4 grid grid-cols-12 font-bold text-slate-500 text-xs uppercase tracking-wider border-b border-slate-200">
          <div className="col-span-2">Token #</div>
          <div className="col-span-3">Patient</div>
          <div className="col-span-2">Department</div>
          <div className="col-span-2">Wait Time</div>
          <div className="col-span-3 text-right">Queue Actions</div>
        </div>
        
        <div className="divide-y divide-slate-100">
          {tokens.map(t => {
            const waitMins = Math.max(0, Math.floor((new Date().getTime() - new Date(t.generated_at).getTime()) / 60000));
            const isCalling = t.status === 'Calling';
            
            return (
              <div key={t.id} className="grid grid-cols-12 items-center p-4 hover:bg-slate-50 transition-colors">
                <div className="col-span-2 flex flex-col items-start">
                  <span className={`text-xl font-black ${t.priority ? 'text-rose-600' : 'text-slate-800'}`}>
                    {t.token_display}
                  </span>
                  {t.priority && <span className="bg-rose-100 text-rose-700 font-bold px-1 rounded text-[9px] uppercase tracking-widest mt-1">ER Override</span>}
                </div>
                
                <div className="col-span-3">
                  <div className="font-bold text-sm text-slate-800">{t.patient_name || 'Anonymous Walk-In'}</div>
                  {t.patient_uhid && <div className="text-xs text-slate-500 mt-0.5">{t.patient_uhid}</div>}
                </div>
                
                <div className="col-span-2 text-slate-600 font-medium text-sm">
                  {t.department}
                </div>
                
                <div className="col-span-2 text-sm text-slate-600">
                  {waitMins} mins
                </div>
                
                <div className="col-span-3 flex justify-end items-center gap-3">
                  <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-widest
                    ${isCalling ? 'bg-indigo-100 text-indigo-700' 
                    : t.status === 'Pending' ? 'bg-amber-100 text-amber-700' 
                    : 'bg-slate-100 text-slate-500'}`}>{t.status}
                  </span>
                  
                  {(t.status === "Pending" || t.status === "Calling") && (
                    <button onClick={() => handleCall(t.id)} title="Call Patient to Counter" className={`p-2 rounded-lg ${isCalling ? 'bg-indigo-50 text-indigo-400 hover:bg-indigo-100' : 'bg-indigo-600 text-white hover:bg-indigo-700'} transition-colors`}>
                      <Mic size={16} />
                    </button>
                  )}
                  {t.status === "Calling" && (
                    <button onClick={() => handleComplete(t.id)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] uppercase tracking-widest px-3 py-2 rounded-lg transition-colors">
                      In Console
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
