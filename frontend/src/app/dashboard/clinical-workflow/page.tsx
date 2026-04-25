"use client";
import React, { useState } from "react";
import { TopNav } from "@/components/ui/TopNav";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

const MODULES = [
  {
    name: "Clinical Navigator",
    desc: "Intake Intelligence — triage, differentials, routing",
    href: "/dashboard/clinical-workflow/navigator",
    icon: "🧭",
    color: "from-blue-500 to-cyan-500",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  {
    name: "Actionable Scribe",
    desc: "SOAP Notes + Auto-Order Generation",
    href: "/dashboard/clinical-workflow/scribe",
    icon: "📝",
    color: "from-violet-500 to-purple-500",
    bg: "bg-violet-50",
    border: "border-violet-200",
  },
  {
    name: "Safety Guardian",
    desc: "Drug interactions, allergies, compliance",
    href: "/dashboard/clinical-workflow/guardian",
    icon: "🛡️",
    color: "from-rose-500 to-red-500",
    bg: "bg-rose-50",
    border: "border-rose-200",
  },
  {
    name: "Handover Engine",
    desc: "SBAR shift summaries for continuity of care",
    href: "/dashboard/clinical-workflow/handover",
    icon: "🔄",
    color: "from-amber-500 to-orange-500",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  {
    name: "Patient Translator",
    desc: "Patient-friendly discharge instructions",
    href: "/dashboard/clinical-workflow/translator",
    icon: "💬",
    color: "from-emerald-500 to-green-500",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
  },
];

export default function ClinicalWorkflowPage() {
  const [status, setStatus] = useState<any>(null);
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const checkStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/clinical-workflow/status`);
      setStatus(await res.json());
    } catch (e) {
      setStatus({ error: "Failed to reach API" });
    }
    setLoading(false);
  };

  const runDemoPipeline = async () => {
    setDemoLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/clinical-workflow/pipeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient: {
            age: "45",
            gender: "Male",
            history: ["Type 2 Diabetes", "Hypertension"],
            allergies: ["Penicillin"],
            medications: ["Metformin 500mg", "Amlodipine 5mg"],
          },
          encounter: {
            narrative:
              "Patient presents with productive cough for 5 days, fever 101F, and shortness of breath. Crackles heard at left lung base.",
            vitals: [
              { name: "BP", value: "130/85" },
              { name: "HR", value: "95" },
              { name: "SpO2", value: "93%" },
              { name: "Temp", value: "38.3C" },
              { name: "RR", value: "22" },
            ],
          },
        }),
      });
      setPipelineResult(await res.json());
    } catch (e: any) {
      setPipelineResult({ error: e.message });
    }
    setDemoLoading(false);
  };

  return (
    <div>
      <TopNav title="Clinical AI Workflow Engine" />

      <div className="p-6 space-y-8">
        {/* Hero */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 text-white">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-blue-500/20 to-transparent rounded-full blur-3xl" />
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">🧠</span>
              <h1 className="text-2xl font-bold">Clinical Workflow Engine</h1>
              <span className="px-2 py-0.5 text-xs font-bold bg-blue-500/20 text-blue-300 rounded-full border border-blue-500/30">
                v1.0
              </span>
            </div>
            <p className="text-slate-400 text-sm max-w-2xl mt-2">
              5 AI-powered modules that automate clinical documentation, triage,
              safety validation, handover, and patient communication — powered by
              AnythingLLM.
            </p>
            <div className="flex gap-3 mt-5">
              <button
                onClick={checkStatus}
                disabled={loading}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-sm font-medium transition-all"
              >
                {loading ? "Checking..." : "⚡ Check Engine Status"}
              </button>
              <button
                onClick={runDemoPipeline}
                disabled={demoLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-all"
              >
                {demoLoading ? "Running Pipeline..." : "🚀 Run Demo Pipeline"}
              </button>
            </div>
          </div>
        </div>

        {/* Status */}
        {status && (
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${status.status === "operational" ? "bg-emerald-500" : "bg-red-500"}`} />
              Engine Status: {status.status || "unknown"}
            </h3>
            {status.modules && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {status.modules.map((m: any) => (
                  <div key={m.name} className="flex items-center gap-2 text-sm text-slate-600 bg-slate-50 rounded-lg px-3 py-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    {m.name}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Module Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {MODULES.map((mod) => (
            <Link
              key={mod.name}
              href={mod.href}
              className="group relative bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
            >
              <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${mod.color} opacity-0 group-hover:opacity-5 transition-opacity`} />
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-12 h-12 rounded-xl ${mod.bg} ${mod.border} border flex items-center justify-center text-2xl`}>
                    {mod.icon}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">{mod.name}</h3>
                  </div>
                </div>
                <p className="text-sm text-slate-500">{mod.desc}</p>
                <div className="mt-4 flex items-center text-xs text-slate-400 group-hover:text-blue-500 transition-colors">
                  Open module →
                </div>
              </div>
            </Link>
          ))}

          {/* Full Pipeline Card */}
          <div className="group relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-6 text-white cursor-pointer hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
            onClick={runDemoPipeline}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center text-2xl">
                ⚡
              </div>
              <div>
                <h3 className="font-bold">Full Pipeline</h3>
              </div>
            </div>
            <p className="text-sm text-slate-400">
              Run all 5 modules sequentially: Navigate → Scribe → Guard → Translate
            </p>
            <div className="mt-4 text-xs text-slate-500 group-hover:text-blue-400 transition-colors">
              {demoLoading ? "Processing..." : "Run pipeline →"}
            </div>
          </div>
        </div>

        {/* Pipeline Result */}
        {pipelineResult && (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
              <h3 className="font-bold text-slate-800">Pipeline Result</h3>
              <span className={`px-3 py-1 text-xs font-bold rounded-full ${
                pipelineResult.overall_status === "safe"
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-red-100 text-red-700"
              }`}>
                {pipelineResult.overall_status?.toUpperCase() || "UNKNOWN"}
              </span>
            </div>
            <div className="p-6 space-y-4">
              {/* Navigator Summary */}
              {pipelineResult.results?.navigator?.module_output && (
                <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                  <h4 className="font-semibold text-blue-800 text-sm mb-2">🧭 Navigator</h4>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div>
                      <span className="text-blue-500 text-xs">Triage</span>
                      <p className="font-bold text-blue-900">{pipelineResult.results.navigator.module_output.triage_level}</p>
                    </div>
                    <div>
                      <span className="text-blue-500 text-xs">Severity</span>
                      <p className="font-bold text-blue-900">{pipelineResult.results.navigator.module_output.severity_score}/10</p>
                    </div>
                    <div>
                      <span className="text-blue-500 text-xs">Impression</span>
                      <p className="font-bold text-blue-900 text-xs">{pipelineResult.results.navigator.module_output.primary_impression}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Scribe Summary */}
              {pipelineResult.results?.scribe?.module_output?.soap_note && (
                <div className="bg-violet-50 rounded-xl p-4 border border-violet-100">
                  <h4 className="font-semibold text-violet-800 text-sm mb-2">📝 Scribe — SOAP Note</h4>
                  <div className="text-sm text-violet-900 space-y-1">
                    <p><strong>Assessment:</strong> {pipelineResult.results.scribe.module_output.soap_note.assessment?.primary_diagnosis?.description || "N/A"}</p>
                    <p><strong>Plan:</strong> {pipelineResult.results.scribe.module_output.soap_note.plan?.summary || "N/A"}</p>
                  </div>
                </div>
              )}

              {/* Guardian Summary */}
              {pipelineResult.results?.guardian?.module_output && (
                <div className={`rounded-xl p-4 border ${
                  pipelineResult.results.guardian.module_output.overall_safety === "safe"
                    ? "bg-emerald-50 border-emerald-100"
                    : "bg-red-50 border-red-100"
                }`}>
                  <h4 className={`font-semibold text-sm mb-2 ${
                    pipelineResult.results.guardian.module_output.overall_safety === "safe"
                      ? "text-emerald-800"
                      : "text-red-800"
                  }`}>🛡️ Guardian — {pipelineResult.results.guardian.module_output.overall_safety?.toUpperCase()}</h4>
                  <p className="text-sm">{pipelineResult.results.guardian.module_output.guardian_summary}</p>
                </div>
              )}

              {/* Translator Summary */}
              {pipelineResult.results?.translator?.module_output?.patient_summary && (
                <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-100">
                  <h4 className="font-semibold text-emerald-800 text-sm mb-2">💬 Patient Translation</h4>
                  <div className="text-sm text-emerald-900 space-y-1">
                    <p><strong>What happened:</strong> {pipelineResult.results.translator.module_output.patient_summary.what_happened}</p>
                    <p><strong>What to do next:</strong> {pipelineResult.results.translator.module_output.patient_summary.what_to_do_next}</p>
                  </div>
                </div>
              )}

              {/* Safety Flags */}
              {pipelineResult.aggregate_safety_flags?.length > 0 && (
                <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                  <h4 className="font-semibold text-amber-800 text-sm mb-2">⚠️ Safety Flags</h4>
                  <ul className="text-sm text-amber-900 space-y-1">
                    {pipelineResult.aggregate_safety_flags.map((f: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Raw JSON Toggle */}
              <details className="text-sm">
                <summary className="cursor-pointer text-slate-500 hover:text-slate-700 font-medium">
                  View raw JSON response
                </summary>
                <pre className="mt-2 bg-slate-900 text-green-400 p-4 rounded-xl overflow-auto text-xs max-h-96">
                  {JSON.stringify(pipelineResult, null, 2)}
                </pre>
              </details>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
