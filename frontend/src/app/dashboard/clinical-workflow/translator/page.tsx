"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function TranslatorPage() {
  const [clinicalNote, setClinicalNote] = useState("Patient diagnosed with community-acquired pneumonia (CAP). CXR shows left lower lobe infiltrate. Started on Azithromycin 500mg PO daily x5 days and Amoxicillin-Clavulanate 875/125mg PO BID x7 days. Follow-up CXR in 4-6 weeks. Return precautions: worsening dyspnea, high fever >39C, hemoptysis, chest pain.");
  const [patientName, setPatientName] = useState("Mrs. Sharma");
  const [age, setAge] = useState("55");
  const [readingLevel, setReadingLevel] = useState("grade_5");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!clinicalNote.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/clinical-workflow/translate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clinical_content: { clinical_note: clinicalNote },
          patient: { name: patientName, age },
          reading_level: readingLevel,
        }),
      });
      setResult(await res.json());
    } catch (e: any) { setResult({ error: e.message }); }
    setLoading(false);
  };

  const t = result?.module_output || {};

  return (
    <div>
      <TopNav title="Patient Translator — Human-Friendly Output" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-emerald-50 to-green-50">
              <h3 className="font-bold text-slate-800">💬 Clinical Content</h3>
              <p className="text-xs text-slate-500 mt-1">Paste clinical notes — AI translates to patient-friendly language</p>
            </div>
            <div className="p-6 space-y-4">
              <textarea value={clinicalNote} onChange={(e) => setClinicalNote(e.target.value)} rows={6}
                placeholder="Paste discharge summary, clinical note, or SOAP note here..."
                className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none" />
              <div className="grid grid-cols-3 gap-3">
                <div><label className="block text-xs font-semibold text-slate-600 mb-1">Patient Name</label>
                  <input value={patientName} onChange={e=>setPatientName(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500" /></div>
                <div><label className="block text-xs font-semibold text-slate-600 mb-1">Age</label>
                  <input value={age} onChange={e=>setAge(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500" /></div>
                <div><label className="block text-xs font-semibold text-slate-600 mb-1">Reading Level</label>
                  <select value={readingLevel} onChange={e=>setReadingLevel(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500">
                    <option value="grade_5">Simple (Grade 5)</option><option value="grade_8">Standard (Grade 8)</option><option value="grade_12">Advanced</option>
                  </select></div>
              </div>
              <button onClick={handleSubmit} disabled={loading || !clinicalNote.trim()}
                className="w-full py-3 bg-gradient-to-r from-emerald-600 to-green-600 text-white rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all">
                {loading ? "🔄 Translating..." : "💬 Translate for Patient"}
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {!result && <div className="bg-slate-50 rounded-2xl border p-12 text-center"><span className="text-4xl">💬</span><p className="text-slate-500 mt-3 text-sm">Paste clinical content and translate for patients</p></div>}
            {loading && <div className="bg-white rounded-2xl border p-12 text-center animate-pulse"><span className="text-4xl">⏳</span><p className="text-slate-500 mt-3 text-sm">Translating to plain language...</p></div>}

            {t.patient_summary && (
              <>
                <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-2xl border border-emerald-200 p-6">
                  <h3 className="font-bold text-emerald-800 text-lg mb-3">{t.patient_summary.title || "Your Health Summary"}</h3>
                  <div className="space-y-3 text-sm text-emerald-900">
                    {t.patient_summary.what_happened && <div><p className="font-semibold text-emerald-700 text-xs">What happened</p><p>{t.patient_summary.what_happened}</p></div>}
                    {t.patient_summary.what_we_found && <div><p className="font-semibold text-emerald-700 text-xs">What we found</p><p>{t.patient_summary.what_we_found}</p></div>}
                    {t.patient_summary.what_it_means && <div><p className="font-semibold text-emerald-700 text-xs">What it means</p><p>{t.patient_summary.what_it_means}</p></div>}
                    {t.patient_summary.what_to_do_next && <div><p className="font-semibold text-emerald-700 text-xs">What to do next</p><p>{t.patient_summary.what_to_do_next}</p></div>}
                  </div>
                </div>

                {t.medications_explained?.length > 0 && (
                  <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                    <div className="px-5 py-3 bg-violet-50 border-b font-bold text-violet-800 text-sm">💊 Your Medicines</div>
                    <div className="p-5 space-y-3">
                      {t.medications_explained.map((m: any, i: number) => (
                        <div key={i} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                          <p className="font-bold text-slate-800">{m.medicine_name}</p>
                          <p className="text-sm text-slate-600 mt-1">{m.what_its_for}</p>
                          <p className="text-sm text-blue-700 mt-1">📌 {m.how_to_take}</p>
                          {m.important_warnings?.length > 0 && (
                            <div className="mt-2">{m.important_warnings.map((w: string, j: number) => <p key={j} className="text-xs text-amber-600">⚠️ {w}</p>)}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {t.warning_signs?.length > 0 && (
                  <div className="bg-red-50 rounded-2xl border border-red-200 p-5">
                    <h4 className="font-bold text-red-800 text-sm mb-3">🚨 When to Get Help</h4>
                    <div className="space-y-2">
                      {t.warning_signs.map((w: any, i: number) => (
                        <div key={i} className="flex items-start gap-3 text-sm">
                          <span className={`px-2 py-0.5 text-xs font-bold rounded-full shrink-0 ${w.action === "go_to_er" ? "bg-red-200 text-red-800" : w.action === "call_doctor" ? "bg-amber-200 text-amber-800" : "bg-blue-200 text-blue-800"}`}>
                            {w.action === "go_to_er" ? "ER" : w.action === "call_doctor" ? "CALL" : "WATCH"}
                          </span>
                          <p className="text-slate-700">{w.symptom}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {t.care_instructions?.length > 0 && (
                  <div className="bg-white rounded-2xl border border-slate-200 p-5">
                    <h4 className="font-bold text-slate-800 text-sm mb-3">📋 Care Instructions</h4>
                    <div className="space-y-2">
                      {t.care_instructions.map((c: any, i: number) => (
                        <div key={i} className={`flex items-start gap-3 text-sm p-2 rounded-lg ${c.priority === "must_do" ? "bg-red-50" : c.priority === "should_do" ? "bg-amber-50" : "bg-slate-50"}`}>
                          <span className="text-lg">{c.icon === "pill" ? "💊" : c.icon === "food" ? "🍎" : c.icon === "activity" ? "🏃" : c.icon === "bandage" ? "🩹" : c.icon === "calendar" ? "📅" : "⚠️"}</span>
                          <p className="text-slate-700">{c.instruction}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {t.faq?.length > 0 && (
                  <div className="bg-blue-50 rounded-2xl border border-blue-200 p-5">
                    <h4 className="font-bold text-blue-800 text-sm mb-3">❓ Common Questions</h4>
                    {t.faq.map((f: any, i: number) => (
                      <div key={i} className="mb-3 last:mb-0"><p className="font-semibold text-blue-900 text-sm">{f.question}</p><p className="text-sm text-blue-700 mt-0.5">{f.answer}</p></div>
                    ))}
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
