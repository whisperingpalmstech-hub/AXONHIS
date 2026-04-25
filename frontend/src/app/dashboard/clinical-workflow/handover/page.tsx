"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function HandoverPage() {
  const [department, setDepartment] = useState("General Ward");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/clinical-workflow/handover`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          department,
          patients: [
            { id: "P001", name: "Ahmed Khan", bed: "W2-B3", age: "62", gender: "Male", diagnosis: "Community-acquired pneumonia", status: "improving", vitals: [{ name: "BP", value: "130/80" }, { name: "SpO2", value: "95%" }, { name: "Temp", value: "37.8C" }], pending_orders: ["CBC follow-up", "CXR repeat"], medications_due: ["Azithromycin 500mg at 20:00"], notes: ["Patient tolerating oral intake"] },
            { id: "P002", name: "Fatima Ali", bed: "W2-B5", age: "45", gender: "Female", diagnosis: "Post-op appendectomy Day 2", status: "stable", vitals: [{ name: "BP", value: "120/75" }, { name: "HR", value: "78" }], pending_orders: ["Drain removal tomorrow"], medications_due: ["Paracetamol 1g PRN"], notes: ["Ambulating well, tolerating diet"] },
            { id: "P003", name: "Raj Patel", bed: "W2-B7", age: "78", gender: "Male", diagnosis: "Acute exacerbation COPD", status: "critical", vitals: [{ name: "BP", value: "100/60" }, { name: "SpO2", value: "88%" }, { name: "HR", value: "112" }], pending_orders: ["ABG stat", "Pulmonology consult"], medications_due: ["Salbutamol nebulization Q4H", "IV Methylprednisolone"], notes: ["Worsening dyspnea, may need ICU transfer"] },
          ],
          shift_info: { shift_type: "Evening", start: "14:00", end: "22:00", outgoing_staff: "Dr. Sarah Miller, RN James", incoming_staff: "Dr. Amit Singh, RN Priya" },
        }),
      });
      setResult(await res.json());
    } catch (e: any) { setResult({ error: e.message }); }
    setLoading(false);
  };

  const ho = result?.module_output || {};

  return (
    <div>
      <TopNav title="Handover Engine — Shift Summary" />
      <div className="p-6 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block text-xs font-semibold text-slate-600 mb-1">Department</label>
              <select value={department} onChange={e => setDepartment(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm w-full outline-none focus:ring-2 focus:ring-amber-500">
                <option>General Ward</option><option>ICU</option><option>Emergency</option><option>Surgical Ward</option><option>Pediatrics</option>
              </select>
            </div>
            <button onClick={handleSubmit} disabled={loading}
              className="px-6 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all mt-5">
              {loading ? "🔄 Generating..." : "🔄 Generate Handover"}
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2">Demo: 3 sample patients (1 critical) will be used for handover generation</p>
        </div>

        {loading && <div className="bg-white rounded-2xl border p-12 text-center animate-pulse"><span className="text-4xl">⏳</span><p className="text-slate-500 mt-3 text-sm">Generating SBAR handover...</p></div>}

        {ho.patient_handovers?.length > 0 && (
          <div className="space-y-4">
            {ho.handover_summary && (
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl border border-amber-200 p-5">
                <h3 className="font-bold text-amber-800">📋 Shift Handover — {ho.handover_summary.department || department}</h3>
                <div className="grid grid-cols-4 gap-4 mt-3 text-sm">
                  <div><span className="text-amber-500 text-xs">Total Patients</span><p className="font-bold text-amber-900">{ho.handover_summary.total_patients}</p></div>
                  <div><span className="text-red-500 text-xs">Critical</span><p className="font-bold text-red-700">{ho.handover_summary.critical_patients}</p></div>
                  <div><span className="text-blue-500 text-xs">New Admissions</span><p className="font-bold text-blue-700">{ho.handover_summary.new_admissions}</p></div>
                  <div><span className="text-green-500 text-xs">Pending Discharges</span><p className="font-bold text-green-700">{ho.handover_summary.pending_discharges}</p></div>
                </div>
              </div>
            )}

            {ho.patient_handovers.map((p: any, i: number) => (
              <div key={i} className={`bg-white rounded-2xl border overflow-hidden ${p.acuity === "critical" ? "border-red-300 ring-1 ring-red-200" : "border-slate-200"}`}>
                <div className={`px-5 py-3 flex items-center justify-between ${p.acuity === "critical" ? "bg-red-50" : p.acuity === "high" ? "bg-amber-50" : "bg-slate-50"}`}>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${p.acuity === "critical" ? "bg-red-100 text-red-700" : p.acuity === "high" ? "bg-amber-100 text-amber-700" : "bg-green-100 text-green-700"}`}>{p.acuity?.toUpperCase()}</span>
                    <span className="font-bold text-slate-800 text-sm">{p.patient_name}</span>
                    <span className="text-xs text-slate-500">Bed {p.bed}</span>
                  </div>
                  {p.escalation_needed && <span className="text-xs font-bold text-red-600 animate-pulse">🚨 ESCALATION NEEDED</span>}
                </div>
                <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div><span className="font-bold text-blue-700">S — Situation:</span><p className="text-slate-700 mt-0.5">{p.situation}</p></div>
                  <div><span className="font-bold text-green-700">B — Background:</span><p className="text-slate-700 mt-0.5">{p.background}</p></div>
                  <div><span className="font-bold text-amber-700">A — Assessment:</span><p className="text-slate-700 mt-0.5">{p.assessment}</p></div>
                  <div><span className="font-bold text-red-700">R — Recommendation:</span><p className="text-slate-700 mt-0.5">{p.recommendation}</p></div>
                </div>
                {p.pending_actions?.length > 0 && (
                  <div className="px-5 pb-4"><p className="text-xs font-bold text-slate-600 mb-1">Pending Actions:</p>
                    {p.pending_actions.map((a: string, j: number) => <span key={j} className="inline-block text-xs bg-slate-100 text-slate-700 rounded-full px-2 py-0.5 mr-1 mb-1">• {a}</span>)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
