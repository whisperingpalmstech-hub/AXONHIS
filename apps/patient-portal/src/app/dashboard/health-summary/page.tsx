"use client";
import React, { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function HealthSummaryPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/v1/portal/health-summary/demo`)
      .then((r) => r.json())
      .then((d) => { setData(d.data || d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center">
      <div className="text-center animate-pulse">
        <span className="text-5xl">💊</span>
        <p className="text-slate-500 mt-3">Loading your health summary...</p>
      </div>
    </div>
  );

  const ps = data?.patient_summary || {};
  const meds = data?.medications_explained || [];
  const warnings = data?.warning_signs || [];
  const care = data?.care_instructions || [];
  const faq = data?.faq || [];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <span className="text-2xl">🏥</span>
          <div>
            <h1 className="font-bold text-slate-800 text-lg">My Health Summary</h1>
            <p className="text-xs text-slate-500">AXONHIS Patient Portal — Powered by AI</p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto p-6 space-y-6">
        {/* Patient Summary */}
        {ps.title && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="bg-gradient-to-r from-blue-500 to-cyan-500 px-6 py-5 text-white">
              <h2 className="text-xl font-bold">{ps.title}</h2>
            </div>
            <div className="p-6 space-y-4">
              {ps.what_happened && (
                <div className="flex gap-3">
                  <span className="text-2xl">📋</span>
                  <div><p className="font-semibold text-slate-700 text-sm">What happened</p><p className="text-slate-600 text-sm mt-1">{ps.what_happened}</p></div>
                </div>
              )}
              {ps.what_we_found && (
                <div className="flex gap-3">
                  <span className="text-2xl">🔍</span>
                  <div><p className="font-semibold text-slate-700 text-sm">What we found</p><p className="text-slate-600 text-sm mt-1">{ps.what_we_found}</p></div>
                </div>
              )}
              {ps.what_it_means && (
                <div className="flex gap-3">
                  <span className="text-2xl">💡</span>
                  <div><p className="font-semibold text-slate-700 text-sm">What it means</p><p className="text-slate-600 text-sm mt-1">{ps.what_it_means}</p></div>
                </div>
              )}
              {ps.what_to_do_next && (
                <div className="flex gap-3 bg-blue-50 rounded-xl p-4">
                  <span className="text-2xl">✅</span>
                  <div><p className="font-semibold text-blue-700 text-sm">What to do next</p><p className="text-blue-600 text-sm mt-1">{ps.what_to_do_next}</p></div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Medications */}
        {meds.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b bg-violet-50">
              <h3 className="font-bold text-violet-800 flex items-center gap-2"><span>💊</span> Your Medicines</h3>
            </div>
            <div className="p-6 space-y-4">
              {meds.map((m: any, i: number) => (
                <div key={i} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <h4 className="font-bold text-slate-800 text-lg">{m.medicine_name}</h4>
                  <p className="text-sm text-slate-600 mt-1">{m.what_its_for}</p>
                  <div className="mt-3 bg-blue-50 rounded-lg p-3">
                    <p className="text-sm text-blue-800 font-medium">📌 How to take: {m.how_to_take}</p>
                  </div>
                  {m.common_side_effects?.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-semibold text-slate-500">Possible side effects:</p>
                      <p className="text-sm text-slate-600">{m.common_side_effects.join(", ")}</p>
                    </div>
                  )}
                  {m.important_warnings?.length > 0 && (
                    <div className="mt-2">
                      {m.important_warnings.map((w: string, j: number) => (
                        <p key={j} className="text-sm text-amber-600 font-medium">⚠️ {w}</p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Warning Signs */}
        {warnings.length > 0 && (
          <div className="bg-red-50 rounded-2xl border border-red-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-red-200 bg-red-100">
              <h3 className="font-bold text-red-800 flex items-center gap-2"><span>🚨</span> When to Get Help</h3>
            </div>
            <div className="p-6 space-y-3">
              {warnings.map((w: any, i: number) => (
                <div key={i} className="flex items-start gap-3">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full shrink-0 ${
                    w.action === "go_to_er" ? "bg-red-200 text-red-800" :
                    w.action === "call_doctor" ? "bg-amber-200 text-amber-800" :
                    "bg-blue-200 text-blue-800"
                  }`}>
                    {w.action === "go_to_er" ? "🏥 GO TO ER" : w.action === "call_doctor" ? "📞 CALL DOCTOR" : "👁️ WATCH"}
                  </span>
                  <p className="text-sm text-red-800">{w.symptom}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Care Instructions */}
        {care.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b bg-emerald-50">
              <h3 className="font-bold text-emerald-800 flex items-center gap-2"><span>📋</span> Care Instructions</h3>
            </div>
            <div className="p-6 space-y-2">
              {care.map((c: any, i: number) => (
                <div key={i} className={`flex items-start gap-3 p-3 rounded-xl ${
                  c.priority === "must_do" ? "bg-red-50 border border-red-100" :
                  c.priority === "should_do" ? "bg-amber-50 border border-amber-100" :
                  "bg-slate-50 border border-slate-100"
                }`}>
                  <span className="text-xl">
                    {c.icon === "pill" ? "💊" : c.icon === "food" ? "🍎" : c.icon === "activity" ? "🏃" :
                     c.icon === "bandage" ? "🩹" : c.icon === "calendar" ? "📅" : "⚠️"}
                  </span>
                  <div>
                    <p className="text-sm text-slate-700">{c.instruction}</p>
                    {c.priority === "must_do" && <span className="text-xs text-red-600 font-bold">Important!</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* FAQ */}
        {faq.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b bg-blue-50">
              <h3 className="font-bold text-blue-800 flex items-center gap-2"><span>❓</span> Common Questions</h3>
            </div>
            <div className="p-6 space-y-4">
              {faq.map((f: any, i: number) => (
                <div key={i}>
                  <p className="font-semibold text-slate-800">{f.question}</p>
                  <p className="text-sm text-slate-600 mt-1">{f.answer}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center py-6 text-xs text-slate-400">
          <p>Generated by AXONHIS Clinical AI Engine</p>
          <p>If you have questions, please contact your healthcare provider</p>
        </div>
      </div>
    </div>
  );
}
