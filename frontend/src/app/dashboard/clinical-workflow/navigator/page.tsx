"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function NavigatorPage() {
  const [narrative, setNarrative] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("Male");
  const [history, setHistory] = useState("");
  const [allergies, setAllergies] = useState("");
  const [medications, setMedications] = useState("");
  const [vitals, setVitals] = useState({ bp: "", hr: "", spo2: "", temp: "", rr: "" });
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!narrative.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/clinical-workflow/navigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient: {
            age, gender,
            history: history ? history.split(",").map(s => s.trim()) : [],
            allergies: allergies ? allergies.split(",").map(s => s.trim()) : [],
            medications: medications ? medications.split(",").map(s => s.trim()) : [],
          },
          encounter: {
            narrative,
            vitals: Object.entries(vitals)
              .filter(([_, v]) => v)
              .map(([k, v]) => ({ name: k.toUpperCase(), value: v })),
          },
        }),
      });
      setResult(await res.json());
    } catch (e: any) {
      setResult({ error: e.message });
    }
    setLoading(false);
  };

  const triageColors: Record<string, string> = {
    "ESI-1": "bg-red-600", "ESI-2": "bg-orange-500", "ESI-3": "bg-yellow-500",
    "ESI-4": "bg-green-500", "ESI-5": "bg-blue-500",
  };

  const nav = result?.module_output || {};

  return (
    <div>
      <TopNav title="Clinical Navigator — Intake Intelligence" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-blue-50 to-cyan-50">
              <h3 className="font-bold text-slate-800">🧭 Patient Intake</h3>
              <p className="text-xs text-slate-500 mt-1">Enter presenting complaint and patient data</p>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Presenting Complaint *</label>
                <textarea value={narrative} onChange={(e) => setNarrative(e.target.value)} rows={3}
                  placeholder="e.g. Crushing chest pain radiating to left arm for 30 minutes..."
                  className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Age</label>
                  <input value={age} onChange={(e) => setAge(e.target.value)} placeholder="45"
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Gender</label>
                  <select value={gender} onChange={(e) => setGender(e.target.value)}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500">
                    <option>Male</option><option>Female</option><option>Other</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Medical History (comma-separated)</label>
                <input value={history} onChange={(e) => setHistory(e.target.value)} placeholder="Type 2 Diabetes, Hypertension"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Allergies (comma-separated)</label>
                <input value={allergies} onChange={(e) => setAllergies(e.target.value)} placeholder="Penicillin, Sulfa"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Current Medications (comma-separated)</label>
                <input value={medications} onChange={(e) => setMedications(e.target.value)} placeholder="Metformin 500mg, Amlodipine 5mg"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              {/* Vitals Grid */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-2">Vitals</label>
                <div className="grid grid-cols-5 gap-2">
                  {(["bp", "hr", "spo2", "temp", "rr"] as const).map((v) => (
                    <div key={v}>
                      <label className="block text-[10px] text-slate-400 mb-0.5 uppercase">{v}</label>
                      <input value={vitals[v]} onChange={(e) => setVitals({ ...vitals, [v]: e.target.value })}
                        placeholder={v === "bp" ? "120/80" : v === "hr" ? "80" : v === "spo2" ? "98%" : v === "temp" ? "37C" : "16"}
                        className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-xs outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                  ))}
                </div>
              </div>
              <button onClick={handleSubmit} disabled={loading || !narrative.trim()}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all">
                {loading ? "🔄 Analyzing..." : "🧭 Run Clinical Navigator"}
              </button>
            </div>
          </div>

          {/* Result Panel */}
          <div className="space-y-4">
            {!result && !loading && (
              <div className="bg-slate-50 rounded-2xl border border-slate-200 p-12 text-center">
                <span className="text-4xl">🧭</span>
                <p className="text-slate-500 mt-3 text-sm">Enter patient data and run the Navigator to see AI triage results</p>
              </div>
            )}

            {loading && (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center animate-pulse">
                <span className="text-4xl">⏳</span>
                <p className="text-slate-500 mt-3 text-sm">AI is analyzing clinical data...</p>
              </div>
            )}

            {result && nav.triage_level && (
              <>
                {/* Triage Badge */}
                <div className={`rounded-2xl p-6 text-white ${triageColors[nav.triage_level] || "bg-slate-600"}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-white/70 text-xs font-medium">TRIAGE LEVEL</p>
                      <p className="text-3xl font-black mt-1">{nav.triage_level}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-white/70 text-xs font-medium">SEVERITY</p>
                      <p className="text-3xl font-black mt-1">{nav.severity_score}/10</p>
                    </div>
                  </div>
                  <p className="mt-3 text-sm text-white/80">{nav.primary_impression}</p>
                </div>

                {/* Red Flags */}
                {nav.red_flags?.length > 0 && (
                  <div className="bg-red-50 rounded-xl p-4 border border-red-200">
                    <h4 className="font-semibold text-red-800 text-sm mb-2">🚨 Red Flags</h4>
                    <ul className="space-y-1">
                      {nav.red_flags.map((f: string, i: number) => (
                        <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 shrink-0" />{f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Differentials */}
                {nav.differential_diagnoses?.length > 0 && (
                  <div className="bg-white rounded-xl p-4 border border-slate-200">
                    <h4 className="font-semibold text-slate-800 text-sm mb-3">📋 Differential Diagnoses</h4>
                    <div className="space-y-2">
                      {nav.differential_diagnoses.map((d: any, i: number) => (
                        <div key={i} className="flex items-center gap-3 p-2 bg-slate-50 rounded-lg">
                          <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-700">
                            {Math.round((d.probability || 0) * 100)}%
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-slate-800">{d.diagnosis}</p>
                            <p className="text-xs text-slate-500">{d.icd10} — {d.reasoning}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Routing */}
                {nav.recommended_routing && (
                  <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                    <h4 className="font-semibold text-blue-800 text-sm mb-2">🏥 Recommended Routing</h4>
                    <div className="grid grid-cols-3 gap-3 text-sm">
                      <div><span className="text-blue-500 text-xs">Department</span><p className="font-bold text-blue-900">{nav.recommended_routing.department}</p></div>
                      <div><span className="text-blue-500 text-xs">Urgency</span><p className="font-bold text-blue-900 capitalize">{nav.recommended_routing.urgency}</p></div>
                      <div><span className="text-blue-500 text-xs">Specialist</span><p className="font-bold text-blue-900">{nav.recommended_routing.specialist}</p></div>
                    </div>
                  </div>
                )}

                {/* Workup */}
                {nav.recommended_workup && (
                  <div className="bg-white rounded-xl p-4 border border-slate-200">
                    <h4 className="font-semibold text-slate-800 text-sm mb-3">🔬 Recommended Workup</h4>
                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <p className="text-xs font-semibold text-violet-600 mb-1">Labs</p>
                        {nav.recommended_workup.labs?.map((l: string, i: number) => (
                          <p key={i} className="text-xs text-slate-700 py-0.5">• {l}</p>
                        ))}
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-cyan-600 mb-1">Imaging</p>
                        {nav.recommended_workup.imaging?.map((l: string, i: number) => (
                          <p key={i} className="text-xs text-slate-700 py-0.5">• {l}</p>
                        ))}
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-amber-600 mb-1">Procedures</p>
                        {nav.recommended_workup.procedures?.map((l: string, i: number) => (
                          <p key={i} className="text-xs text-slate-700 py-0.5">• {l}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Validation */}
                {result.validation && (
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <h4 className="font-semibold text-slate-700 text-xs mb-2">✅ Validation</h4>
                    <p className="text-xs text-slate-500">Schema: {result.validation.schema_valid ? "✅ Valid" : "❌ Invalid"}</p>
                    {result.validation.safety_flags?.length > 0 && (
                      <div className="mt-2">
                        {result.validation.safety_flags.map((f: string, i: number) => (
                          <p key={i} className="text-xs text-amber-600">⚠️ {f}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Clinical Summary */}
                {nav.clinical_summary && (
                  <div className="bg-slate-800 rounded-xl p-4 text-white">
                    <h4 className="font-semibold text-sm mb-1">📄 Clinical Summary</h4>
                    <p className="text-sm text-slate-300">{nav.clinical_summary}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
