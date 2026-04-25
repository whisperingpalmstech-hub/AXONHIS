"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function GuardianPage() {
  const [allergies, setAllergies] = useState("Penicillin");
  const [medications, setMedications] = useState("Metformin 500mg");
  const [history, setHistory] = useState("Type 2 Diabetes, CKD Stage 3");
  const [age, setAge] = useState("65");
  const [newOrders, setNewOrders] = useState('[\n  {"drug": "Amoxicillin", "dose": "500mg", "route": "PO", "frequency": "TID", "duration": "7 days"},\n  {"drug": "Metformin", "dose": "1000mg", "route": "PO", "frequency": "BID", "duration": "ongoing"}\n]');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      let parsedMeds = [];
      try { parsedMeds = JSON.parse(newOrders); } catch { parsedMeds = []; }
      const res = await fetch(`${API}/api/v1/clinical-workflow/guard`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient: { age, gender: "Male", allergies: allergies.split(",").map(s=>s.trim()), medications: medications.split(",").map(s=>s.trim()), history: history.split(",").map(s=>s.trim()) },
          proposed_orders: { medications: parsedMeds },
        }),
      });
      setResult(await res.json());
    } catch (e: any) { setResult({ error: e.message }); }
    setLoading(false);
  };

  const g = result?.module_output || {};

  return (
    <div>
      <TopNav title="Safety Guardian — Compliance Validation" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-rose-50 to-red-50">
              <h3 className="font-bold text-slate-800">🛡️ Safety Check</h3>
              <p className="text-xs text-slate-500 mt-1">Validate orders against patient safety profile</p>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs font-semibold text-slate-600 mb-1">Age</label>
                  <input value={age} onChange={e=>setAge(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500" /></div>
                <div><label className="block text-xs font-semibold text-slate-600 mb-1">Allergies</label>
                  <input value={allergies} onChange={e=>setAllergies(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500" /></div>
              </div>
              <div><label className="block text-xs font-semibold text-slate-600 mb-1">Current Medications</label>
                <input value={medications} onChange={e=>setMedications(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500" /></div>
              <div><label className="block text-xs font-semibold text-slate-600 mb-1">Medical History</label>
                <input value={history} onChange={e=>setHistory(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500" /></div>
              <div><label className="block text-xs font-semibold text-slate-600 mb-1">Proposed Orders (JSON)</label>
                <textarea value={newOrders} onChange={e=>setNewOrders(e.target.value)} rows={6} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-xs font-mono focus:ring-2 focus:ring-rose-500 outline-none" /></div>
              <button onClick={handleSubmit} disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-rose-600 to-red-600 text-white rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all">
                {loading ? "🔄 Validating..." : "🛡️ Run Safety Guardian"}
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {!result && <div className="bg-slate-50 rounded-2xl border p-12 text-center"><span className="text-4xl">🛡️</span><p className="text-slate-500 mt-3 text-sm">Submit orders for safety validation</p></div>}
            {loading && <div className="bg-white rounded-2xl border p-12 text-center animate-pulse"><span className="text-4xl">⏳</span><p className="text-slate-500 mt-3 text-sm">Checking safety...</p></div>}
            {g.overall_safety && (
              <>
                <div className={`rounded-2xl p-6 text-white ${g.overall_safety === "safe" ? "bg-emerald-600" : g.overall_safety === "caution" ? "bg-amber-500" : "bg-red-600"}`}>
                  <p className="text-white/70 text-xs">OVERALL SAFETY</p>
                  <p className="text-3xl font-black mt-1">{g.overall_safety.toUpperCase()}</p>
                  <p className="text-sm text-white/80 mt-2">{g.guardian_summary}</p>
                </div>
                {g.allergy_alerts?.length > 0 && (
                  <div className="bg-red-50 rounded-xl p-4 border border-red-200">
                    <h4 className="font-semibold text-red-800 text-sm mb-2">🚨 Allergy Alerts</h4>
                    {g.allergy_alerts.map((a: any, i: number) => (
                      <div key={i} className="text-sm text-red-700 py-1 border-b border-red-100 last:border-0">
                        <p className="font-bold">{a.proposed_drug} ↔ {a.allergen}</p>
                        <p className="text-xs">{a.recommendation}</p>
                      </div>
                    ))}
                  </div>
                )}
                {g.drug_interactions?.length > 0 && (
                  <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                    <h4 className="font-semibold text-amber-800 text-sm mb-2">⚠️ Drug Interactions</h4>
                    {g.drug_interactions.map((d: any, i: number) => (
                      <div key={i} className="text-sm text-amber-700 py-1"><p className="font-bold">{d.drug_a} + {d.drug_b} ({d.interaction_type})</p><p className="text-xs">{d.description}</p></div>
                    ))}
                  </div>
                )}
                <details className="text-sm"><summary className="cursor-pointer text-slate-500 font-medium">View raw JSON</summary>
                  <pre className="mt-2 bg-slate-900 text-green-400 p-4 rounded-xl overflow-auto text-xs max-h-96">{JSON.stringify(result, null, 2)}</pre>
                </details>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
