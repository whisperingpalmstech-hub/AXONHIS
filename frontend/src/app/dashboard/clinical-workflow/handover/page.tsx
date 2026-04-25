"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

const statusColors: Record<string, { bg: string; text: string; border: string }> = {
  Stable: { bg: "bg-emerald-600", text: "text-emerald-100", border: "border-emerald-200" },
  Guarded: { bg: "bg-amber-500", text: "text-amber-100", border: "border-amber-200" },
  Deteriorating: { bg: "bg-red-600", text: "text-red-100", border: "border-red-200" },
  "Insufficient Data": { bg: "bg-slate-500", text: "text-slate-100", border: "border-slate-200" },
};
const trendIcons: Record<string, string> = { Improving: "📈", Declining: "📉", Stable: "➡️", Mixed: "🔀" };

// Demo patients with realistic 12h data
const DEMO_PATIENTS = [
  {
    id: "pt-001", name: "Raj Patel", bed: "ICU-3", age: "58", gender: "Male",
    diagnosis: "Sepsis secondary to UTI", status: "critical",
    vitals_12h: [
      { timestamp: "06:00", bp: "110/70", hr: "95", temp: "38.5", spo2: "94" },
      { timestamp: "09:00", bp: "95/55", hr: "112", temp: "39.2", spo2: "91" },
      { timestamp: "12:00", bp: "88/50", hr: "120", temp: "39.8", spo2: "88" },
    ],
    nurse_notes: [
      { timestamp: "07:00", note: "Patient febrile, started IV fluids" },
      { timestamp: "10:00", note: "Increasing tachycardia, notified doctor" },
      { timestamp: "11:30", note: "O2 started via NRB mask, urine output declining" },
    ],
    doctor_orders: [
      { timestamp: "07:30", order: "Blood cultures x2", status: "completed" },
      { timestamp: "10:15", order: "Noradrenaline infusion", status: "pending" },
      { timestamp: "11:00", order: "Repeat lactate in 2h", status: "pending" },
    ],
    medications_due: ["Meropenem 1g IV Q8H (due 14:00)", "Vasopressin drip titrate"],
  },
  {
    id: "pt-002", name: "Anita Sharma", bed: "Ward-7B", age: "42", gender: "Female",
    diagnosis: "Post laparoscopic cholecystectomy Day 1", status: "stable",
    vitals_12h: [
      { timestamp: "06:00", bp: "125/80", hr: "78", temp: "37.0", spo2: "98" },
      { timestamp: "12:00", bp: "120/75", hr: "72", temp: "36.8", spo2: "99" },
    ],
    nurse_notes: [
      { timestamp: "08:00", note: "Tolerating clear fluids, ambulated with assistance" },
      { timestamp: "11:00", note: "Pain well controlled with oral analgesia, drain output 30ml serous" },
    ],
    doctor_orders: [
      { timestamp: "08:00", order: "Advance diet as tolerated", status: "completed" },
      { timestamp: "09:00", order: "Remove drain if output <50ml", status: "pending" },
    ],
    medications_due: ["Paracetamol 1g PO (due 14:00)"],
  },
  {
    id: "pt-003", name: "Mohammed Khan", bed: "Ward-12A", age: "70", gender: "Male",
    diagnosis: "COPD exacerbation + Type 2 DM", status: "guarded",
    vitals_12h: [
      { timestamp: "06:00", bp: "140/90", hr: "88", temp: "37.5", spo2: "91" },
      { timestamp: "09:00", bp: "135/85", hr: "82", temp: "37.2", spo2: "93" },
      { timestamp: "12:00", bp: "130/80", hr: "78", temp: "37.0", spo2: "95" },
    ],
    nurse_notes: [
      { timestamp: "07:00", note: "Nebulization given, mild wheeze bilateral" },
      { timestamp: "10:00", note: "Breathing easier, less accessory muscle use" },
      { timestamp: "11:30", note: "New onset confusion — POCT glucose 42 mg/dL (HYPOGLYCEMIA)" },
    ],
    doctor_orders: [
      { timestamp: "07:00", order: "Nebulization Q4H", status: "completed" },
      { timestamp: "08:00", order: "ABG in AM", status: "pending" },
      { timestamp: "11:40", order: "D50 bolus stat for hypoglycemia", status: "pending" },
    ],
    medications_due: ["Insulin glargine (HOLD until glucose reviewed)", "Salbutamol neb (due 14:00)"],
  },
];

export default function HandoverPage() {
  const [department, setDepartment] = useState("General Ward + ICU");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/clinical-workflow/handover`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          department,
          patients: DEMO_PATIENTS,
          shift_info: { shift_type: "day", outgoing_staff: "Dr. Mehra (Night)", incoming_staff: "Dr. Singh (Day)", start: "07:00", end: "19:00" },
        }),
      });
      setResult(await res.json());
    } catch (e: any) { setResult({ error: e.message }); }
    setLoading(false);
  };

  const ho = result?.module_output || {};
  const patients = ho.patients || (ho.status_summary ? [ho] : []);

  return (
    <div>
      <TopNav title="Handover Engine — Shift Summary Intelligence" />
      <div className="p-6 space-y-6">
        {/* Controls */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-600 mb-1">Department</label>
              <input value={department} onChange={e => setDepartment(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-500" />
            </div>
            <div className="text-center">
              <p className="text-xs text-slate-500">Patients</p>
              <p className="text-2xl font-black text-slate-800">{DEMO_PATIENTS.length}</p>
            </div>
            <button onClick={handleSubmit} disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-orange-600 to-amber-600 text-white rounded-xl font-bold text-sm hover:opacity-90 disabled:opacity-50 transition-all">
              {loading ? "🔄 Generating Handover..." : "🔄 Generate Shift Handover"}
            </button>
          </div>
          <p className="text-[10px] text-slate-400 mt-2">Day shift: Dr. Mehra (Night) → Dr. Singh (Day) • 3 patients with 12h vitals, nurse notes, and doctor orders</p>
        </div>

        {loading && <div className="bg-white rounded-2xl border p-12 text-center animate-pulse"><span className="text-4xl">⏳</span><p className="text-slate-500 mt-3 text-sm">AI analyzing 12h patient data...</p><p className="text-slate-400 text-xs">Trend analysis → Event extraction → Change detection → Task extraction</p></div>}

        {/* Department Summary */}
        {ho.shift_summary && (
          <div className="bg-slate-800 rounded-2xl p-5 text-white">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-slate-400 text-xs font-bold">SHIFT SUMMARY — {ho.department || department}</p>
                <p className="text-sm mt-1">{ho.shift_summary}</p>
              </div>
              <div className="text-right">
                <p className="text-slate-400 text-xs">Critical</p>
                <p className="text-2xl font-black text-red-400">{ho.critical_count || 0}</p>
              </div>
            </div>
          </div>
        )}

        {/* Patient Cards */}
        <div className="space-y-4">
          {patients.map((pt: any, i: number) => {
            const sc = statusColors[pt.status_summary] || statusColors["Insufficient Data"];
            const trend = pt.vitals_trend || {};
            return (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                {/* Patient Header */}
                <div className={`${sc.bg} px-5 py-3 flex items-center justify-between`}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center text-white font-black text-sm">
                      {pt.handover_priority || i + 1}
                    </div>
                    <div>
                      <h3 className="text-white font-bold text-sm">{pt.patient_name || `Patient ${i + 1}`}</h3>
                      <p className="text-white/70 text-xs">{pt.bed || "—"} • {pt.status_summary}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="bg-white/20 px-3 py-1 rounded-full text-white text-xs font-bold">{pt.status_summary}</span>
                  </div>
                </div>

                <div className="p-5 space-y-3">
                  {/* One-liner */}
                  {pt.one_liner && (
                    <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                      <p className="text-sm text-slate-800 font-medium">{pt.one_liner}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Critical Changes */}
                    {pt.critical_changes?.length > 0 && (
                      <div className="bg-red-50 rounded-xl p-4 border border-red-200">
                        <h4 className="font-bold text-red-800 text-xs mb-2">🔴 Critical Changes</h4>
                        {pt.critical_changes.map((c: string, j: number) => (
                          <p key={j} className="text-sm text-red-700 py-0.5 flex items-start gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 shrink-0" />{c}
                          </p>
                        ))}
                      </div>
                    )}

                    {/* Pending Tasks */}
                    {pt.pending_tasks?.length > 0 && (
                      <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                        <h4 className="font-bold text-amber-800 text-xs mb-2">📋 Pending Tasks</h4>
                        {pt.pending_tasks.map((t: string, j: number) => (
                          <div key={j} className="flex items-start gap-2 py-0.5">
                            <input type="checkbox" className="mt-1 w-3.5 h-3.5 rounded border-amber-300" />
                            <p className="text-sm text-amber-800">{t}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Vitals Trend */}
                  {trend.direction && (
                    <div className="flex items-center gap-3 bg-slate-50 rounded-lg p-3 border border-slate-200">
                      <span className="text-2xl">{trendIcons[trend.direction] || "➡️"}</span>
                      <div>
                        <p className="text-xs font-bold text-slate-600">Vitals: {trend.direction}</p>
                        <p className="text-xs text-slate-500">{trend.details}</p>
                      </div>
                      {trend.latest_vitals && (
                        <div className="ml-auto flex gap-3 text-[10px] text-slate-600">
                          {trend.latest_vitals.bp && <span>BP: <b>{trend.latest_vitals.bp}</b></span>}
                          {trend.latest_vitals.hr && <span>HR: <b>{trend.latest_vitals.hr}</b></span>}
                          {trend.latest_vitals.spo2 && <span>SpO₂: <b>{trend.latest_vitals.spo2}</b></span>}
                          {trend.latest_vitals.temp && <span>Temp: <b>{trend.latest_vitals.temp}</b></span>}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Attention Flags */}
                  {pt.attention_flags?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {pt.attention_flags.map((f: string, j: number) => (
                        <span key={j} className="text-[10px] bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">⚠️ {f}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {result && (
          <details className="text-sm"><summary className="cursor-pointer text-slate-500 font-medium">View raw JSON</summary>
            <pre className="mt-2 bg-slate-900 text-green-400 p-4 rounded-xl overflow-auto text-xs max-h-96">{JSON.stringify(result, null, 2)}</pre>
          </details>
        )}
      </div>
    </div>
  );
}
