"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

const sevColors: Record<string, {bg: string; text: string; border: string}> = {
  High: {bg: "bg-red-50", text: "text-red-800", border: "border-red-200"},
  Medium: {bg: "bg-amber-50", text: "text-amber-800", border: "border-amber-200"},
  Low: {bg: "bg-blue-50", text: "text-blue-800", border: "border-blue-200"},
};
const typeIcons: Record<string, string> = {
  Allergy: "🚨", Interaction: "💊", Duplicate: "🔁", Contraindication: "⛔", Logic: "🧠", Fraud: "🔍",
};

export default function GuardianPage() {
  const [allergies, setAllergies] = useState("Penicillin, Sulfa");
  const [medications, setMedications] = useState("Metformin 500mg, Warfarin 5mg");
  const [history, setHistory] = useState("Type 2 Diabetes, CKD Stage 3, Atrial Fibrillation");
  const [age, setAge] = useState("65");
  const [gender, setGender] = useState("Male");
  const [newOrders, setNewOrders] = useState('{\n  "medications": [\n    {"drug": "Amoxicillin", "dose": "500mg", "route": "PO", "frequency": "TID"},\n    {"drug": "Ibuprofen", "dose": "400mg", "route": "PO", "frequency": "TID"},\n    {"drug": "Metformin", "dose": "1000mg", "route": "PO", "frequency": "BID"}\n  ],\n  "labs": ["CBC", "BMP", "INR"],\n  "imaging": ["CT Abdomen with Contrast"]\n}');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      let parsedOrders = {};
      try { parsedOrders = JSON.parse(newOrders); } catch { parsedOrders = { medications: [] }; }
      const res = await fetch(`${API}/api/v1/clinical-workflow/guard`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient: { age, gender, allergies: allergies.split(",").map(s=>s.trim()), medications: medications.split(",").map(s=>s.trim()), history: history.split(",").map(s=>s.trim()) },
          proposed_orders: parsedOrders,
        }),
      });
      setResult(await res.json());
    } catch (e: any) { setResult({ error: e.message }); }
    setLoading(false);
  };

  const g = result?.module_output || {};
  const alerts = g.alerts || [];
  const audit = g.audit_summary || {};

  return (
    <div>
      <TopNav title="Safety Guardian — 6-Step Audit Engine" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-rose-50 to-red-50">
              <h3 className="font-bold text-slate-800">🛡️ Safety Audit</h3>
              <p className="text-xs text-slate-500 mt-1">6-step check: Allergy → Interactions → Duplicates → Contraindications → Logic → Fraud</p>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs font-semibold text-slate-600 mb-1">Age</label>
                  <input value={age} onChange={e=>setAge(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500" /></div>
                <div><label className="block text-xs font-semibold text-slate-600 mb-1">Gender</label>
                  <select value={gender} onChange={e=>setGender(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500"><option>Male</option><option>Female</option></select></div>
              </div>
              <div><label className="block text-xs font-semibold text-slate-600 mb-1">🚨 Known Allergies</label>
                <input value={allergies} onChange={e=>setAllergies(e.target.value)} className="w-full border border-rose-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500 bg-rose-50" /></div>
              <div><label className="block text-xs font-semibold text-slate-600 mb-1">💊 Current Medications</label>
                <input value={medications} onChange={e=>setMedications(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500" /></div>
              <div><label className="block text-xs font-semibold text-slate-600 mb-1">📋 Medical History</label>
                <input value={history} onChange={e=>setHistory(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-rose-500" /></div>
              <div><label className="block text-xs font-semibold text-slate-600 mb-1">📦 Proposed Orders (JSON)</label>
                <textarea value={newOrders} onChange={e=>setNewOrders(e.target.value)} rows={8} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-xs font-mono focus:ring-2 focus:ring-rose-500 outline-none" /></div>
              <button onClick={handleSubmit} disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-rose-600 to-red-600 text-white rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all">
                {loading ? "🔄 Running 6-Step Safety Audit..." : "🛡️ Run Guardian Safety Engine"}
              </button>
            </div>
          </div>

          {/* Result Panel */}
          <div className="space-y-4">
            {!result && <div className="bg-slate-50 rounded-2xl border p-12 text-center"><span className="text-4xl">🛡️</span><p className="text-slate-500 mt-3 text-sm">Submit orders for 6-step safety validation</p><p className="text-xs text-slate-400 mt-1">Allergy • Interaction • Duplicate • Contraindication • Logic • Fraud</p></div>}
            {loading && <div className="bg-white rounded-2xl border p-12 text-center animate-pulse"><span className="text-4xl">⏳</span><p className="text-slate-500 mt-3 text-sm">Running safety checks...</p></div>}

            {g.overall_safety && (
              <>
                {/* Overall Status Banner */}
                <div className={`rounded-2xl p-6 text-white ${g.overall_safety === "safe" ? "bg-emerald-600" : g.overall_safety === "caution" ? "bg-amber-500" : "bg-red-600"}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-white/70 text-xs font-bold">OVERALL SAFETY STATUS</p>
                      <p className="text-3xl font-black mt-1">{g.overall_safety.toUpperCase()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-white/70 text-xs">Issues</p>
                      <p className="text-3xl font-black">{audit.issues_detected || 0}</p>
                    </div>
                  </div>
                  <p className="text-sm text-white/80 mt-3">{g.guardian_summary}</p>
                </div>

                {/* Audit Summary */}
                <div className="grid grid-cols-4 gap-2">
                  <div className="bg-slate-800 rounded-xl p-3 text-center text-white"><p className="text-[10px] text-slate-400">CHECKED</p><p className="text-lg font-black">{audit.total_orders_checked || 0}</p></div>
                  <div className="bg-red-100 rounded-xl p-3 text-center"><p className="text-[10px] text-red-500 font-bold">HIGH</p><p className="text-lg font-black text-red-800">{audit.high_risk_count || 0}</p></div>
                  <div className="bg-amber-100 rounded-xl p-3 text-center"><p className="text-[10px] text-amber-500 font-bold">MEDIUM</p><p className="text-lg font-black text-amber-800">{audit.medium_risk_count || 0}</p></div>
                  <div className="bg-emerald-100 rounded-xl p-3 text-center"><p className="text-[10px] text-emerald-500 font-bold">SAFE</p><p className="text-lg font-black text-emerald-800">{audit.orders_safe || 0}</p></div>
                </div>

                {/* Allergy Alerts */}
                {g.allergy_alerts?.length > 0 && (
                  <div className="bg-red-50 rounded-xl p-4 border-2 border-red-300">
                    <h4 className="font-bold text-red-800 text-sm mb-3 flex items-center gap-2">🚨 Allergy Alerts — CRITICAL</h4>
                    {g.allergy_alerts.map((a: any, i: number) => (
                      <div key={i} className="bg-white rounded-lg p-3 border border-red-200 mb-2">
                        <div className="flex items-center gap-2"><span className="text-red-600 font-black text-sm">{a.proposed_drug}</span><span className="text-slate-400">↔</span><span className="text-red-600 font-black text-sm">{a.allergen}</span></div>
                        {a.cross_reactivity_class && <p className="text-xs text-red-500 mt-1">Cross-reactivity: {a.cross_reactivity_class}</p>}
                        <p className="text-sm text-red-700 mt-1 bg-red-50 rounded px-2 py-1">✅ {a.recommendation}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Drug Interactions */}
                {g.drug_interactions?.length > 0 && (
                  <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                    <h4 className="font-bold text-amber-800 text-sm mb-3 flex items-center gap-2">💊 Drug-Drug Interactions</h4>
                    {g.drug_interactions.map((d: any, i: number) => (
                      <div key={i} className="bg-white rounded-lg p-3 border border-amber-100 mb-2">
                        <div className="flex items-center gap-2"><span className="font-bold text-sm">{d.drug_a}</span><span className="text-amber-500">+</span><span className="font-bold text-sm">{d.drug_b}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${d.interaction_type === "major" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>{d.interaction_type}</span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">{d.description}</p>
                        <p className="text-xs text-amber-700 mt-1 font-medium">→ {d.recommendation}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Contraindications */}
                {g.contraindications?.length > 0 && (
                  <div className="bg-rose-50 rounded-xl p-4 border border-rose-200">
                    <h4 className="font-bold text-rose-800 text-sm mb-3">⛔ Contraindications</h4>
                    {g.contraindications.map((c: any, i: number) => (
                      <div key={i} className="bg-white rounded-lg p-3 border border-rose-100 mb-2">
                        <p className="font-bold text-sm text-rose-800">{c.order} ↔ {c.condition}</p>
                        <p className="text-xs text-slate-600 mt-1">{c.risk}</p>
                        <p className="text-xs text-rose-700 mt-1 font-medium">→ {c.recommendation}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Logic Gaps */}
                {g.logic_gaps?.length > 0 && (
                  <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-200">
                    <h4 className="font-bold text-indigo-800 text-sm mb-3">🧠 Clinical Logic Gaps</h4>
                    {g.logic_gaps.map((l: any, i: number) => (
                      <div key={i} className="text-sm text-indigo-800 py-1"><span className="font-bold">{l.finding}</span> — Missing: {l.missing_order}<p className="text-xs text-indigo-600">→ {l.recommendation}</p></div>
                    ))}
                  </div>
                )}

                {/* Duplicate Flags */}
                {g.duplicate_flags?.length > 0 && (
                  <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                    <h4 className="font-bold text-blue-800 text-sm mb-2">🔁 Duplicate / Timing Flags</h4>
                    {g.duplicate_flags.map((d: any, i: number) => (
                      <p key={i} className="text-sm text-blue-700 py-0.5">• {d.order}: {d.reason}</p>
                    ))}
                  </div>
                )}

                {/* Fraud Flags */}
                {g.fraud_flags?.length > 0 && (
                  <div className="bg-slate-100 rounded-xl p-4 border border-slate-300">
                    <h4 className="font-bold text-slate-800 text-sm mb-2">🔍 Billing / Fraud Flags</h4>
                    {g.fraud_flags.map((f: any, i: number) => (
                      <p key={i} className="text-sm text-slate-700 py-0.5">• {f.pattern} → {f.recommendation}</p>
                    ))}
                  </div>
                )}

                {/* All Alerts (unified view) */}
                {alerts.length > 0 && (
                  <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                    <div className="px-4 py-3 bg-slate-800 text-white font-bold text-sm">📋 All Alerts ({alerts.length})</div>
                    <div className="p-3 space-y-2">
                      {alerts.map((a: any, i: number) => (
                        <div key={i} className={`rounded-lg p-3 border flex items-start gap-3 ${sevColors[a.severity]?.bg || "bg-slate-50"} ${sevColors[a.severity]?.border || "border-slate-200"}`}>
                          <span className="text-lg shrink-0">{typeIcons[a.type] || "⚠️"}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className={`text-xs font-bold ${sevColors[a.severity]?.text || "text-slate-700"}`}>{a.severity}</span>
                              <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-bold">{a.type}</span>
                              {a.override_required && <span className="text-[10px] bg-red-200 text-red-800 px-1.5 py-0.5 rounded font-bold">OVERRIDE REQUIRED</span>}
                            </div>
                            <p className="text-sm text-slate-800 mt-1 font-medium">{a.message}</p>
                            <p className="text-xs text-slate-600 mt-0.5">→ {a.action}</p>
                            {a.alternative && <p className="text-xs text-emerald-700 mt-0.5 font-medium">Alternative: {a.alternative}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
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
