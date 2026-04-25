"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function ScribePage() {
  const [doctorInput, setDoctorInput] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("Male");
  const [history, setHistory] = useState("");
  const [allergies, setAllergies] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!doctorInput.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/clinical-workflow/scribe`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient: { age, gender, history: history ? history.split(",").map(s=>s.trim()) : [], allergies: allergies ? allergies.split(",").map(s=>s.trim()) : [] },
          encounter: { doctor_input: doctorInput },
        }),
      });
      setResult(await res.json());
    } catch (e: any) { setResult({ error: e.message }); }
    setLoading(false);
  };

  const soap = result?.module_output?.soap_note;
  const orders = result?.module_output?.suggested_orders;

  return (
    <div>
      <TopNav title="Actionable Scribe — SOAP + Orders" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-violet-50 to-purple-50">
              <h3 className="font-bold text-slate-800">📝 Doctor&apos;s Findings</h3>
              <p className="text-xs text-slate-500 mt-1">Enter clinical findings — AI generates SOAP + orders</p>
            </div>
            <div className="p-6 space-y-4">
              <textarea value={doctorInput} onChange={(e) => setDoctorInput(e.target.value)} rows={5}
                placeholder="e.g. Patient presents with productive cough x5 days, fever 101F, crackles left base. Suspect community-acquired pneumonia..."
                className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-violet-500 outline-none" />
              <div className="grid grid-cols-2 gap-3">
                <input value={age} onChange={(e) => setAge(e.target.value)} placeholder="Age" className="border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500" />
                <select value={gender} onChange={(e) => setGender(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500">
                  <option>Male</option><option>Female</option><option>Other</option>
                </select>
              </div>
              <input value={history} onChange={(e) => setHistory(e.target.value)} placeholder="Medical History (comma-separated)"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500" />
              <input value={allergies} onChange={(e) => setAllergies(e.target.value)} placeholder="Allergies (comma-separated)"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-500" />
              <button onClick={handleSubmit} disabled={loading || !doctorInput.trim()}
                className="w-full py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all">
                {loading ? "🔄 Generating..." : "📝 Generate SOAP + Orders"}
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {!result && <div className="bg-slate-50 rounded-2xl border p-12 text-center"><span className="text-4xl">📝</span><p className="text-slate-500 mt-3 text-sm">Enter findings to generate SOAP notes and orders</p></div>}
            {loading && <div className="bg-white rounded-2xl border p-12 text-center animate-pulse"><span className="text-4xl">⏳</span><p className="text-slate-500 mt-3 text-sm">AI Scribe working...</p></div>}

            {soap && (
              <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                <div className="px-5 py-3 bg-violet-50 border-b border-violet-100 font-bold text-violet-800 text-sm">SOAP Note</div>
                <div className="p-5 space-y-3 text-sm">
                  <div><span className="font-bold text-blue-700">S:</span> <span className="text-slate-700">{soap.subjective?.chief_complaint || soap.subjective?.hpi || "N/A"}</span></div>
                  <div><span className="font-bold text-green-700">O:</span> <span className="text-slate-700">{JSON.stringify(soap.objective?.physical_exam || soap.objective?.observations || "N/A")}</span></div>
                  <div><span className="font-bold text-amber-700">A:</span> <span className="text-slate-700">{soap.assessment?.primary_diagnosis?.description || "N/A"} ({soap.assessment?.primary_diagnosis?.icd10 || ""})</span></div>
                  <div><span className="font-bold text-red-700">P:</span> <span className="text-slate-700">{soap.plan?.summary || "N/A"}</span></div>
                </div>
              </div>
            )}

            {orders && (
              <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                <div className="px-5 py-3 bg-cyan-50 border-b border-cyan-100 font-bold text-cyan-800 text-sm">Suggested Orders</div>
                <div className="p-5 space-y-3">
                  {orders.medications?.length > 0 && (
                    <div><p className="text-xs font-bold text-violet-600 mb-1">💊 Medications</p>
                      {orders.medications.map((m: any, i: number) => (<p key={i} className="text-xs text-slate-700 py-0.5">• {m.drug} {m.dose} {m.route} {m.frequency} × {m.duration}</p>))}
                    </div>
                  )}
                  {orders.lab_tests?.length > 0 && (
                    <div><p className="text-xs font-bold text-cyan-600 mb-1">🔬 Labs</p>
                      {orders.lab_tests.map((l: any, i: number) => (<p key={i} className="text-xs text-slate-700 py-0.5">• {l.test} ({l.priority})</p>))}
                    </div>
                  )}
                  {orders.imaging?.length > 0 && (
                    <div><p className="text-xs font-bold text-amber-600 mb-1">📷 Imaging</p>
                      {orders.imaging.map((img: any, i: number) => (<p key={i} className="text-xs text-slate-700 py-0.5">• {img.study} ({img.priority})</p>))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {result?.module_output?.icd10_codes?.length > 0 && (
              <div className="bg-slate-50 rounded-xl p-4 border"><p className="text-xs font-bold text-slate-600 mb-1">ICD-10 Codes</p>
                {result.module_output.icd10_codes.map((c: any, i: number) => (<p key={i} className="text-xs text-slate-700">• {c.code} — {c.description}</p>))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
