"use client";
import React, { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PatientSummaryPanel({ patientUhid }: { patientUhid: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API}/api/v1/rpiw-summary/${patientUhid}`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (e) {
        console.error("Failed to fetch summary:", e);
      }
      setLoading(false);
    };
    if (patientUhid) fetchSummary();
  }, [patientUhid]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin w-8 h-8 border-4 border-gray-300 border-t-indigo-600 rounded-full" />
      </div>
    );
  }

  if (!data || !data.summary) {
    return <div className="p-8 text-center text-gray-500">No summary data found for {patientUhid}</div>;
  }

  const { summary, alerts, vitals, medications, tasks } = data;

  return (
    <div className="space-y-6">
      <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100 flex gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-blue-800 uppercase tracking-wide">Chief Issue</p>
            {/* ABDM Milestone 2 - ABHA Connection Status */}
            <span className="bg-indigo-100 text-indigo-700 text-[9px] px-1.5 py-0.5 rounded font-bold border border-indigo-200">
              ABHA: {summary?.is_abha_linked ? "LINKED ✅" : "NOT LINKED ⚠️"}
            </span>
          </div>
          <p className="text-gray-800 font-medium text-lg mt-1">{summary.chief_issue || "Not recorded"}</p>
        </div>
        <div className="flex-1 border-l border-blue-200 pl-4">
          <p className="text-sm font-semibold text-blue-800 uppercase tracking-wide">Primary Diagnosis</p>
          <p className="text-gray-800 font-medium text-lg mt-1">{summary.primary_diagnosis || "Not recorded"}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Vitals */}
        <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50 px-4 py-3 border-b flex justify-between items-center">
            <h3 className="font-bold text-gray-700 flex items-center gap-2"><span>📈</span> Latest Vitals</h3>
          </div>
          <div className="p-4 grid grid-cols-2 gap-4">
            {vitals.slice(0, 4).map((v: any) => (
              <div key={v.id} className="bg-gray-50 rounded-lg p-3 border">
                <p className="text-xs text-gray-500 uppercase font-medium">{v.vital_sign}</p>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className={`text-xl font-bold ${v.is_abnormal ? "text-red-600" : "text-gray-900"}`}>{v.value}</span>
                  <span className="text-xs text-gray-500 font-medium">{v.unit}</span>
                </div>
                <p className="text-[10px] text-gray-400 mt-2">{new Date(v.recorded_at).toLocaleTimeString()}</p>
              </div>
            ))}
            {vitals.length === 0 && <p className="text-sm text-gray-400 col-span-2">No vitals recorded.</p>}
          </div>
        </div>

        {/* Alerts */}
        <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
          <div className="bg-red-50 px-4 py-3 border-b border-red-100 flex justify-between items-center">
            <h3 className="font-bold text-red-800 flex items-center gap-2"><span>⚠️</span> Critical Alerts</h3>
            <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-0.5 rounded-full">{alerts.length}</span>
          </div>
          <div className="p-0">
            {alerts.length > 0 ? (
               <ul className="divide-y divide-red-50">
                {alerts.map((a: any) => (
                  <li key={a.id} className="p-3 bg-red-50/30 flex items-start gap-3">
                    <span className="mt-0.5 text-red-500">🚨</span>
                    <div>
                      <p className="text-sm font-semibold text-red-800">{a.message}</p>
                      <p className="text-xs text-red-600/70 mt-0.5">{a.alert_type.replace("_", " ")}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-6 text-center text-sm text-gray-400">No active alerts.</div>
            )}
          </div>
        </div>

        {/* Medications */}
        <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
          <div className="bg-emerald-50 px-4 py-3 border-b border-emerald-100 flex justify-between items-center">
            <h3 className="font-bold text-emerald-800 flex items-center gap-2"><span>💊</span> Active Medications</h3>
          </div>
          <div className="p-0">
            {medications.length > 0 ? (
               <ul className="divide-y">
                {medications.map((m: any) => (
                  <li key={m.id} className="p-3 flex justify-between items-center hover:bg-gray-50">
                    <div>
                      <p className="text-sm font-bold text-gray-800">{m.drug_name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{m.dosage} • {m.route}</p>
                    </div>
                    <div className="text-right">
                      <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">{m.frequency}</span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-6 text-center text-sm text-gray-400">No active medications.</div>
            )}
          </div>
        </div>

        {/* Tasks */}
        <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
          <div className="bg-amber-50 px-4 py-3 border-b border-amber-100 flex justify-between items-center">
            <h3 className="font-bold text-amber-800 flex items-center gap-2"><span>📋</span> Pending Tasks</h3>
            <span className="bg-amber-100 text-amber-800 text-xs font-bold px-2 py-0.5 rounded-full">
              {tasks.filter((t:any) => t.status !== 'Completed').length}
            </span>
          </div>
          <div className="p-0">
            {tasks.length > 0 ? (
               <ul className="divide-y">
                {tasks.map((t: any) => (
                  <li key={t.id} className="p-3 flex items-start gap-3 hover:bg-gray-50">
                    <input type="checkbox" checked={t.status === "Completed"} readOnly className="mt-1 flex-shrink-0 text-amber-600 focus:ring-amber-500 rounded border-gray-300" />
                    <div className={t.status === "Completed" ? "opacity-50" : ""}>
                      <p className="text-sm font-medium text-gray-800">{t.description}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{t.task_category.replace("_", " ")}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-6 text-center text-sm text-gray-400">No pending tasks.</div>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex items-center justify-between text-xs text-gray-400 border-t pt-4">
        <span>Last Updated: {new Date(summary.last_updated_at).toLocaleString()}</span>
        <button className="flex items-center gap-1 hover:text-indigo-600 transition-colors">
          <span>🔄</span> Refresh
        </button>
      </div>
    </div>
  );
}
