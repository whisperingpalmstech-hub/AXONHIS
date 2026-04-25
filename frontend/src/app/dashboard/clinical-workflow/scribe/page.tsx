"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

const catColors: Record<string, { bg: string; text: string; border: string }> = {
  Lab: { bg: "bg-cyan-50", text: "text-cyan-700", border: "border-cyan-200" },
  Imaging: { bg: "bg-violet-50", text: "text-violet-700", border: "border-violet-200" },
  Medication: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  Monitoring: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  Procedure: { bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200" },
};
const catIcons: Record<string, string> = {
  Lab: "🔬", Imaging: "📷", Medication: "💊", Monitoring: "📊", Procedure: "🔧",
};

export default function ScribePage() {
  const [doctorInput, setDoctorInput] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("Male");
  const [history, setHistory] = useState("");
  const [allergies, setAllergies] = useState("");
  const [medications, setMedications] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  const handleSubmit = async () => {
    if (!doctorInput.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/clinical-workflow/scribe`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient: {
            age, gender,
            history: history ? history.split(",").map(s => s.trim()) : [],
            allergies: allergies ? allergies.split(",").map(s => s.trim()) : [],
            medications: medications ? medications.split(",").map(s => s.trim()) : [],
          },
          encounter: { doctor_input: doctorInput },
        }),
      });
      const data = await res.json();
      setResult(data);
      // Initialize checkbox state from AI
      const items = data?.module_output?.items || [];
      const checks: Record<string, boolean> = {};
      items.forEach((it: any) => { checks[it.id] = it.selected; });
      setCheckedItems(checks);
    } catch (e: any) { setResult({ error: e.message }); }
    setLoading(false);
  };

  const toggleItem = (id: string) => {
    setCheckedItems(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const out = result?.module_output || {};
  const items = out.items || [];
  const soap = out.draft_soap || {};
  const categories = [...new Set(items.map((i: any) => i.category))];

  return (
    <div>
      <TopNav title="Actionable Scribe — Smart Order Engine" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-violet-50 to-purple-50">
              <h3 className="font-bold text-slate-800">📝 Doctor&apos;s Narration</h3>
              <p className="text-xs text-slate-500 mt-1">Enter findings — AI builds order set + SOAP note</p>
            </div>
            <div className="p-6 space-y-4">
              <textarea value={doctorInput} onChange={(e) => setDoctorInput(e.target.value)} rows={5}
                placeholder="e.g. Patient has productive cough x5 days, fever 101F, crackles left base. Suspect community-acquired pneumonia. Start empiric antibiotics. Order CXR and CBC..."
                className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-violet-500 outline-none" />
              <div className="grid grid-cols-2 gap-3">
                <input value={age} onChange={e => setAge(e.target.value)} placeholder="Age"
                  className="border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500" />
                <select value={gender} onChange={e => setGender(e.target.value)}
                  className="border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500">
                  <option>Male</option><option>Female</option><option>Other</option>
                </select>
              </div>
              <input value={history} onChange={e => setHistory(e.target.value)} placeholder="Medical History (comma-separated)"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500" />
              <input value={allergies} onChange={e => setAllergies(e.target.value)} placeholder="Allergies (comma-separated)"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500" />
              <input value={medications} onChange={e => setMedications(e.target.value)} placeholder="Current Medications (comma-separated)"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500" />
              <button onClick={handleSubmit} disabled={loading || !doctorInput.trim()}
                className="w-full py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all">
                {loading ? "🔄 Building Orders..." : "📝 Generate Orders + SOAP"}
              </button>
            </div>
          </div>

          {/* Output */}
          <div className="space-y-4">
            {!result && <div className="bg-slate-50 rounded-2xl border p-12 text-center"><span className="text-4xl">📝</span><p className="text-slate-500 mt-3 text-sm">Enter doctor narration to generate smart order set</p></div>}
            {loading && <div className="bg-white rounded-2xl border p-12 text-center animate-pulse"><span className="text-4xl">⏳</span><p className="text-slate-500 mt-3 text-sm">AI Scribe building orders...</p></div>}

            {out.order_set_name && (
              <>
                {/* Protocol Header */}
                <div className="flex items-center gap-3">
                  <div className={`rounded-xl px-4 py-2 text-sm font-bold ${
                    out.priority_level === "Emergency" ? "bg-red-100 text-red-800" :
                    out.priority_level === "Urgent" ? "bg-amber-100 text-amber-800" :
                    "bg-green-100 text-green-800"
                  }`}>
                    {out.priority_level}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-sm">{out.order_set_name}</h3>
                    <p className="text-xs text-slate-500">{items.filter((i: any) => checkedItems[i.id]).length}/{items.length} items selected</p>
                  </div>
                </div>

                {/* Smart Order Set — Checkbox UI */}
                {categories.map((cat: string) => (
                  <div key={cat} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                    <div className={`px-5 py-3 border-b flex items-center gap-2 ${catColors[cat]?.bg || "bg-slate-50"} ${catColors[cat]?.border || ""}`}>
                      <span>{catIcons[cat] || "📋"}</span>
                      <h4 className={`font-bold text-sm ${catColors[cat]?.text || "text-slate-700"}`}>{cat}</h4>
                      <span className="text-xs text-slate-400 ml-auto">
                        {items.filter((i: any) => i.category === cat && checkedItems[i.id]).length}/
                        {items.filter((i: any) => i.category === cat).length}
                      </span>
                    </div>
                    <div className="p-3 space-y-1">
                      {items.filter((i: any) => i.category === cat).map((item: any) => (
                        <label key={item.id} className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                          checkedItems[item.id] ? "bg-blue-50 border border-blue-200" : "bg-slate-50 border border-transparent hover:border-slate-200"
                        }`}>
                          <input type="checkbox" checked={checkedItems[item.id] || false}
                            onChange={() => toggleItem(item.id)}
                            className="mt-1 w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-slate-800">{item.label}</span>
                              {item.priority === "stat" && <span className="text-[10px] font-bold bg-red-100 text-red-700 rounded px-1.5 py-0.5">STAT</span>}
                              {item.priority === "prn" && <span className="text-[10px] font-bold bg-amber-100 text-amber-700 rounded px-1.5 py-0.5">PRN</span>}
                            </div>
                            {item.dose && <p className="text-xs text-blue-600 mt-0.5">{item.dose}</p>}
                            <p className="text-xs text-slate-500 mt-0.5">{item.reason}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}

                {/* SOAP Note */}
                {soap.subjective && (
                  <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                    <div className="px-5 py-3 bg-slate-800 text-white font-bold text-sm">📄 SOAP Note</div>
                    <div className="p-5 space-y-3 text-sm">
                      <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                        <span className="font-bold text-blue-700">S — Subjective</span>
                        <p className="text-slate-700 mt-1">{soap.subjective}</p>
                      </div>
                      <div className="p-3 bg-green-50 rounded-lg border border-green-100">
                        <span className="font-bold text-green-700">O — Objective</span>
                        <p className="text-slate-700 mt-1">{soap.objective}</p>
                      </div>
                      <div className="p-3 bg-amber-50 rounded-lg border border-amber-100">
                        <span className="font-bold text-amber-700">A — Assessment</span>
                        <p className="text-slate-700 mt-1">{soap.assessment}</p>
                      </div>
                      <div className="p-3 bg-red-50 rounded-lg border border-red-100">
                        <span className="font-bold text-red-700">P — Plan</span>
                        <p className="text-slate-700 mt-1">{soap.plan}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* ICD-10 Codes */}
                {out.icd10_codes?.length > 0 && (
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <h4 className="text-xs font-bold text-slate-600 mb-2">ICD-10 Codes</h4>
                    {out.icd10_codes.map((c: any, i: number) => (
                      <p key={i} className="text-xs text-slate-700">
                        <span className="font-mono font-bold">{c.code}</span> — {c.description}
                        {c.type === "primary" && <span className="ml-1 text-blue-600 font-bold">(Primary)</span>}
                      </p>
                    ))}
                  </div>
                )}

                {/* Alerts */}
                {out.clinical_alerts?.length > 0 && (
                  <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                    <h4 className="font-semibold text-amber-800 text-sm mb-2">⚠️ Clinical Alerts</h4>
                    {out.clinical_alerts.map((a: string, i: number) => (<p key={i} className="text-sm text-amber-700">⚡ {a}</p>))}
                  </div>
                )}

                {/* Validation */}
                {result.validation && (
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <h4 className="font-semibold text-slate-700 text-xs mb-2">✅ Validation</h4>
                    <p className="text-xs text-slate-500">Schema: {result.validation.schema_valid ? "✅ Valid" : "❌ Invalid"}</p>
                    {result.validation.safety_flags?.map((f: string, i: number) => (<p key={i} className="text-xs text-red-600">🚨 {f}</p>))}
                    {result.validation.logic_issues?.map((f: string, i: number) => (<p key={i} className="text-xs text-amber-600">⚠️ {f}</p>))}
                  </div>
                )}

                <details className="text-sm">
                  <summary className="cursor-pointer text-slate-500 font-medium">View raw JSON</summary>
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
