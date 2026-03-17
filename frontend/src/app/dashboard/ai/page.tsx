"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Brain, Mic, MicOff, Zap, AlertTriangle, CheckCircle2,
  ChevronRight, Loader2, RefreshCw, ShieldAlert, Activity,
  MessageSquare, FileText, ClipboardList, X, Check, Eye,
  BotMessageSquare, Stethoscope, FlaskConical, Pill, Clock,
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface EncounterOption {
  id: string;
  encounter_uuid: string;
  patient_id: string;
  encounter_type: string;
  status: string;
}

interface PatientSummary {
  id: string;
  encounter_id: string;
  narrative: string;
  primary_diagnosis: string | null;
  active_treatments: string[];
  recent_abnormal_labs: { test: string; value: string; flag: string }[];
  pending_tests: string[];
  clinical_trends: string[];
  risk_flags: string[];
  llm_model: string;
  generated_at: string;
  is_stale: boolean;
}

interface ClinicalInsight {
  id: string;
  insight_type: string;
  title: string;
  description: string;
  recommendation: string | null;
  confidence_score: number | null;
  is_acknowledged: boolean;
  created_at: string;
}

interface RiskAlert {
  id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  recommended_action: string | null;
  is_resolved: boolean;
  created_at: string;
}

interface VoiceCommand {
  id: string;
  raw_transcript: string;
  detected_language: string;
  translated_text: string | null;
  intent: string | null;
  suggested_orders: { order_type: string; name: string; note: string }[];
  confidence: number;
  status: string;
  created_at: string;
}

interface AgentTask {
  id: string;
  agent_type: string;
  draft_output: string | null;
  status: string;
  created_at: string;
}

// ─── Severity colours ─────────────────────────────────────────────────────────

const SEVERITY_STYLE: Record<string, string> = {
  CRITICAL: "bg-red-100 text-red-700 border-red-200",
  HIGH: "bg-orange-100 text-orange-700 border-orange-200",
  MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
  LOW: "bg-blue-100 text-blue-700 border-blue-200",
};

const INSIGHT_ICON: Record<string, React.ElementType> = {
  ABNORMAL_LAB: FlaskConical,
  DRUG_INTERACTION: Pill,
  RAPID_DETERIORATION: Activity,
  SEPSIS_RISK: ShieldAlert,
  DELAYED_RESULT: Clock,
  GENERAL: Brain,
};

// ─── Main AI Page ─────────────────────────────────────────────────────────────

export default function AIPage() {
  const [encounterId, setEncounterId] = useState("");
  const [encounters, setEncounters] = useState<EncounterOption[]>([]);
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [insights, setInsights] = useState<ClinicalInsight[]>([]);
  const [riskAlerts, setRiskAlerts] = useState<RiskAlert[]>([]);
  const [voiceCommands, setVoiceCommands] = useState<VoiceCommand[]>([]);
  const [agentTasks, setAgentTasks] = useState<AgentTask[]>([]);

  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [loadingRisks, setLoadingRisks] = useState(false);
  const [loadingVoice, setLoadingVoice] = useState(false);
  const [loadingAgent, setLoadingAgent] = useState(false);

  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [voiceLang, setVoiceLang] = useState("en");
  const [pendingCommand, setPendingCommand] = useState<VoiceCommand | null>(null);

  const [agentType, setAgentType] = useState("discharge_summary");
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);
  const [editDraftContent, setEditDraftContent] = useState("");

  const [activeTab, setActiveTab] = useState<"summary" | "insights" | "risks" | "voice" | "agents">("summary");
  const recognitionRef = useRef<any>(null);

  // ── Voice Recording ──────────────────────────────────────────────────────

  const startRecording = useCallback(() => {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      alert("Speech recognition is not supported in this browser. Please use Chrome.");
      return;
    }
    const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognitionAPI() as any;
    recognition.lang = voiceLang === "hi" ? "hi-IN" : voiceLang === "mr" ? "mr-IN" : "en-US";
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onresult = (event: any) => {
      const t = Array.from(event.results as any[])
        .map((r: any) => r[0].transcript)
        .join("");
      setTranscript(t);
    };
    recognition.onerror = () => setIsRecording(false);
    recognition.onend = () => setIsRecording(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
    setTranscript("");
  }, [voiceLang]);

  const stopRecording = useCallback(() => {
    recognitionRef.current?.stop();
    setIsRecording(false);
  }, []);

  // ── API Calls ─────────────────────────────────────────────────────────────

  const fetchSummary = async (forceRefresh = false) => {
    if (!encounterId.trim()) return;
    setLoadingSummary(true);
    try {
      const url = `${API}/api/v1/ai/summarize-patient${forceRefresh ? "?force_refresh=true" : ""}`;
      const res = await fetch(url, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ encounter_id: encounterId }),
      });
      if (res.ok) setSummary(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchInsights = async (generate = false) => {
    if (!encounterId.trim()) return;
    setLoadingInsights(true);
    try {
      if (generate) {
        const res = await fetch(`${API}/api/v1/ai/clinical-insights/generate`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ encounter_id: encounterId }),
        });
        if (res.ok) setInsights(await res.json());
      } else {
        const res = await fetch(`${API}/api/v1/ai/clinical-insights/${encounterId}`, {
          headers: authHeaders(),
        });
        if (res.ok) setInsights(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingInsights(false);
    }
  };

  const fetchRiskAlerts = async (analyze = false) => {
    if (!encounterId.trim()) return;
    setLoadingRisks(true);
    try {
      if (analyze) {
        const res = await fetch(`${API}/api/v1/ai/risk-alerts/analyze`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ encounter_id: encounterId }),
        });
        if (res.ok) setRiskAlerts(await res.json());
      } else {
        const res = await fetch(`${API}/api/v1/ai/risk-alerts?encounter_id=${encounterId}`, {
          headers: authHeaders(),
        });
        if (res.ok) setRiskAlerts(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingRisks(false);
    }
  };

  const submitVoiceCommand = async () => {
    if (!transcript.trim()) return;
    setLoadingVoice(true);
    try {
      const res = await fetch(`${API}/api/v1/ai/voice-command`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          transcript,
          language: voiceLang,
          encounter_id: encounterId || undefined,
        }),
      });
      if (res.ok) {
        const cmd: VoiceCommand = await res.json();
        setPendingCommand(cmd);
        setVoiceCommands((prev) => [cmd, ...prev]);
        setTranscript("");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingVoice(false);
    }
  };

  const confirmCommand = async (id: string) => {
    try {
      const res = await fetch(`${API}/api/v1/ai/voice-command/${id}/confirm`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        const updated: VoiceCommand = await res.json();
        setVoiceCommands((prev) => prev.map((c) => (c.id === id ? updated : c)));
        if (pendingCommand?.id === id) setPendingCommand(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const acknowledgeInsight = async (id: string) => {
    try {
      const res = await fetch(`${API}/api/v1/ai/clinical-insights/${id}/acknowledge`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        const updated: ClinicalInsight = await res.json();
        setInsights((prev) => prev.map((i) => (i.id === id ? updated : i)));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const resolveAlert = async (id: string) => {
    try {
      const res = await fetch(`${API}/api/v1/ai/risk-alerts/${id}/resolve`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        setRiskAlerts((prev) => prev.filter((a) => a.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createAgentTask = async () => {
    setLoadingAgent(true);
    try {
      const res = await fetch(`${API}/api/v1/ai/agents/task`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          agent_type: agentType,
          encounter_id: encounterId || undefined,
          task_input: {},
        }),
      });
      if (res.ok) {
        const task: AgentTask = await res.json();
        setAgentTasks((prev) => [task, ...prev]);
        setSelectedTask(task);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAgent(false);
    }
  };

  const approveAgentTask = async (id: string) => {
    try {
      const res = await fetch(`${API}/api/v1/ai/agents/task/${id}/approve`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ draft_output: editDraftContent || undefined }),
      });
      if (res.ok) {
        const updated: AgentTask = await res.json();
        setAgentTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
        if (selectedTask?.id === id) {
          setSelectedTask(updated);
          setEditDraftContent(updated.draft_output || "");
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Load data on mount
  useEffect(() => {
    fetch(`${API}/api/v1/encounters`, { headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : []))
      .then(setEncounters)
      .catch((e) => console.error("Failed to load encounters", e));

    fetch(`${API}/api/v1/ai/voice-commands`, { headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : []))
      .then(setVoiceCommands)
      .catch(() => {});
    fetch(`${API}/api/v1/ai/agents/tasks`, { headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : []))
      .then(setAgentTasks)
      .catch(() => {});
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────

  const TABS = [
    { id: "summary", label: "AI Summary", icon: Brain },
    { id: "insights", label: "Insights", icon: Zap },
    { id: "risks", label: "Risk Alerts", icon: ShieldAlert },
    { id: "voice", label: "Voice", icon: Mic },
    { id: "agents", label: "AI Agents", icon: BotMessageSquare },
  ] as const;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <TopNav title="AI Intelligence Platform" />

      <div className="p-6 space-y-6 max-w-7xl mx-auto">

        {/* Header Banner */}
        <div className="rounded-2xl bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600 p-6 text-white shadow-xl">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">AXONHIS AI Platform</h1>
              <p className="text-violet-200 text-sm mt-0.5">
                Phase 9 — Powered by Llama-3.3-70b-versatile via Grok API
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2 bg-white/10 backdrop-blur rounded-xl px-4 py-2">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-sm font-medium">AI Active</span>
            </div>
          </div>

          {/* Encounter ID input */}
          <div className="mt-5 flex gap-3">
            <select
              id="encounter-id-input"
              value={encounterId}
              onChange={(e) => setEncounterId(e.target.value)}
              className="flex-1 bg-white/10 backdrop-blur border border-white/20 rounded-xl px-4 py-2.5 text-white placeholder-violet-200 text-sm focus:outline-none focus:border-white/60 appearance-none drop-shadow-sm"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%23fff' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E")`,
                backgroundPosition: `right 16px center`,
                backgroundRepeat: `no-repeat`,
                backgroundSize: `20px 20px`,
              }}
            >
              <option value="" className="text-slate-800">-- Select Encounter --</option>
              {encounters.map(enc => (
                <option key={enc.id} value={enc.id} className="text-slate-800">
                  {enc.encounter_type} - {enc.status} (UUID: {enc.encounter_uuid.substring(0,8)})
                </option>
              ))}
            </select>
            <button
              id="load-ai-context-btn"
              onClick={() => { fetchSummary(); fetchInsights(); fetchRiskAlerts(); }}
              disabled={!encounterId.trim()}
              className="px-5 py-2.5 bg-white text-violet-700 font-semibold rounded-xl text-sm hover:bg-violet-50 transition-colors disabled:opacity-40"
            >
              Load Context
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-1 bg-[var(--bg-secondary)] p-1 rounded-xl border border-[var(--border)]">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              id={`ai-tab-${id}`}
              onClick={() => setActiveTab(id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === id
                  ? "bg-violet-600 text-white shadow-sm"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-primary)]"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>

        {/* ── Tab: AI Summary ── */}
        {activeTab === "summary" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Brain className="w-5 h-5 text-violet-600" /> Live Patient Summary
              </h2>
              <div className="flex gap-2">
                <button
                  id="generate-summary-btn"
                  onClick={() => fetchSummary(false)}
                  disabled={!encounterId || loadingSummary}
                  className="btn-outline text-sm flex items-center gap-1.5 disabled:opacity-40"
                >
                  {loadingSummary ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
                  Generate
                </button>
                <button
                  id="refresh-summary-btn"
                  onClick={() => fetchSummary(true)}
                  disabled={!encounterId || loadingSummary}
                  className="btn-outline text-sm flex items-center gap-1.5 disabled:opacity-40"
                >
                  <RefreshCw className="w-4 h-4" /> Force Refresh
                </button>
              </div>
            </div>

            {loadingSummary ? (
              <AiLoading text="Generating clinical summary with Llama-3.3-70b..." />
            ) : summary ? (
              <div className="space-y-4">
                {/* Narrative card */}
                <div className="card border-l-4 border-violet-500">
                  <div className="card-header flex justify-between items-center">
                    <span className="font-semibold text-sm">Clinical Narrative</span>
                    <span className="text-xs text-[var(--text-secondary)]">
                      {summary.llm_model} · {new Date(summary.generated_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="card-body">
                    <p className="text-sm leading-relaxed text-[var(--text-primary)]">
                      {summary.narrative}
                    </p>
                    {summary.primary_diagnosis && (
                      <div className="mt-3 flex items-center gap-2 p-3 bg-violet-50 rounded-lg border border-violet-100">
                        <Stethoscope className="w-4 h-4 text-violet-600 shrink-0" />
                        <div>
                          <p className="text-xs font-semibold text-violet-700">Primary Diagnosis</p>
                          <p className="text-sm text-violet-900">{summary.primary_diagnosis}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* 4-column grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                  <SummaryListCard
                    title="Active Treatments"
                    icon={<Pill className="w-4 h-4 text-emerald-600" />}
                    items={summary.active_treatments}
                    emptyText="No active treatments"
                    color="emerald"
                  />
                  <SummaryListCard
                    title="Abnormal Labs"
                    icon={<FlaskConical className="w-4 h-4 text-rose-600" />}
                    items={summary.recent_abnormal_labs.map((l) => `${l.test}: ${l.value} [${l.flag}]`)}
                    emptyText="No abnormal results"
                    color="rose"
                    highlight
                  />
                  <SummaryListCard
                    title="Pending Tests"
                    icon={<Clock className="w-4 h-4 text-amber-600" />}
                    items={summary.pending_tests}
                    emptyText="No pending tests"
                    color="amber"
                  />
                  <SummaryListCard
                    title="Risk Flags"
                    icon={<AlertTriangle className="w-4 h-4 text-red-600" />}
                    items={summary.risk_flags}
                    emptyText="No risk flags"
                    color="red"
                    highlight={summary.risk_flags.length > 0}
                  />
                </div>

                {summary.clinical_trends.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <span className="font-semibold text-sm flex items-center gap-2">
                        <Activity className="w-4 h-4 text-cyan-600" /> Clinical Trends
                      </span>
                    </div>
                    <div className="card-body flex flex-wrap gap-2">
                      {summary.clinical_trends.map((t, i) => (
                        <span key={i} className="bg-cyan-50 text-cyan-700 border border-cyan-100 text-xs px-3 py-1 rounded-full">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <EmptyState
                icon={<Brain className="w-10 h-10 text-violet-300" />}
                title="No summary loaded"
                desc="Enter an encounter UUID above and click Generate to create a Grok-powered clinical summary."
              />
            )}
          </div>
        )}

        {/* ── Tab: Clinical Insights ── */}
        {activeTab === "insights" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-500" /> Clinical Insights
              </h2>
              <div className="flex gap-2">
                <button
                  id="fetch-insights-btn"
                  onClick={() => fetchInsights(false)}
                  disabled={!encounterId || loadingInsights}
                  className="btn-outline text-sm flex items-center gap-1.5 disabled:opacity-40"
                >
                  <Eye className="w-4 h-4" /> Load Existing
                </button>
                <button
                  id="generate-insights-btn"
                  onClick={() => fetchInsights(true)}
                  disabled={!encounterId || loadingInsights}
                  className="btn text-sm flex items-center gap-1.5 disabled:opacity-40"
                >
                  {loadingInsights ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                  Generate Insights
                </button>
              </div>
            </div>

            {loadingInsights ? (
              <AiLoading text="Analyzing clinical patterns with Llama-3.3-70b..." />
            ) : insights.length > 0 ? (
              <div className="space-y-3">
                {insights.map((ins) => {
                  const Icon = INSIGHT_ICON[ins.insight_type] || Brain;
                  return (
                    <div
                      key={ins.id}
                      className={`card border-l-4 ${ins.is_acknowledged ? "opacity-60 border-slate-200" : "border-amber-500"}`}
                    >
                      <div className="card-body">
                        <div className="flex items-start gap-3">
                          <div className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
                            <Icon className="w-5 h-5 text-amber-600" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="font-semibold text-sm">{ins.title}</h3>
                              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                                {ins.insight_type.replace(/_/g, " ")}
                              </span>
                              {ins.confidence_score && (
                                <span className="text-xs text-[var(--text-secondary)]">
                                  {Math.round(ins.confidence_score * 100)}% confidence
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-[var(--text-secondary)] mt-1">{ins.description}</p>
                            {ins.recommendation && (
                              <div className="mt-2 flex items-start gap-2 p-2 bg-blue-50 rounded-lg">
                                <ChevronRight className="w-3 h-3 text-blue-600 mt-0.5 shrink-0" />
                                <p className="text-xs text-blue-700">{ins.recommendation}</p>
                              </div>
                            )}
                          </div>
                          {!ins.is_acknowledged && (
                            <button
                              id={`ack-insight-${ins.id}`}
                              onClick={() => acknowledgeInsight(ins.id)}
                              className="btn-outline text-xs flex items-center gap-1 shrink-0"
                            >
                              <CheckCircle2 className="w-3 h-3" /> Acknowledge
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                icon={<Zap className="w-10 h-10 text-amber-300" />}
                title="No insights yet"
                desc="Generate AI insights to detect abnormal lab patterns, drug interactions, and deterioration signals."
              />
            )}
          </div>
        )}

        {/* ── Tab: Risk Alerts ── */}
        {activeTab === "risks" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-red-500" /> Risk Alerts
              </h2>
              <div className="flex gap-2">
                <button
                  id="fetch-risks-btn"
                  onClick={() => fetchRiskAlerts(false)}
                  disabled={!encounterId || loadingRisks}
                  className="btn-outline text-sm flex items-center gap-1.5 disabled:opacity-40"
                >
                  <Eye className="w-4 h-4" /> Load Alerts
                </button>
                <button
                  id="analyze-risks-btn"
                  onClick={() => fetchRiskAlerts(true)}
                  disabled={!encounterId || loadingRisks}
                  className="btn text-sm flex items-center gap-1.5 disabled:opacity-40 !bg-red-600 !text-white hover:!bg-red-700"
                >
                  {loadingRisks ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldAlert className="w-4 h-4" />}
                  Run Risk Analysis
                </button>
              </div>
            </div>

            {loadingRisks ? (
              <AiLoading text="Running risk analysis — checking sepsis, drug safety, critical labs..." />
            ) : riskAlerts.length > 0 ? (
              <div className="space-y-3">
                {riskAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`card border ${SEVERITY_STYLE[alert.severity] || "border-slate-200"} border-l-4`}
                  >
                    <div className="card-body">
                      <div className="flex items-start gap-3">
                        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${SEVERITY_STYLE[alert.severity]}`}>
                          <AlertTriangle className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-sm">{alert.title}</h3>
                            <span className={`text-xs px-2 py-0.5 rounded-full border ${SEVERITY_STYLE[alert.severity]}`}>
                              {alert.severity}
                            </span>
                            <span className="text-xs text-[var(--text-secondary)]">
                              {alert.category.replace(/_/g, " ")}
                            </span>
                          </div>
                          <p className="text-xs text-[var(--text-secondary)] mt-1">{alert.description}</p>
                          {alert.recommended_action && (
                            <div className="mt-2 p-2 bg-white/60 rounded-lg border">
                              <p className="text-xs font-medium">Recommended Action:</p>
                              <p className="text-xs text-[var(--text-secondary)]">{alert.recommended_action}</p>
                            </div>
                          )}
                        </div>
                        <button
                          id={`resolve-alert-${alert.id}`}
                          onClick={() => resolveAlert(alert.id)}
                          className="btn-outline text-xs flex items-center gap-1 shrink-0"
                        >
                          <Check className="w-3 h-3" /> Resolve
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<ShieldAlert className="w-10 h-10 text-red-200" />}
                title="No active risk alerts"
                desc="Run risk analysis to detect sepsis risk, drug-allergy conflicts, and critical lab abnormalities."
              />
            )}
          </div>
        )}

        {/* ── Tab: Voice Commands ── */}
        {activeTab === "voice" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Mic className="w-5 h-5 text-blue-500" /> Multilingual Voice Control
            </h2>

            {/* Voice input panel */}
            <div className="card border-2 border-blue-100 bg-blue-50/30">
              <div className="card-body space-y-4">
                <div className="flex items-center gap-4">
                  <div className="flex gap-2">
                    {(["en", "hi", "mr"] as const).map((lang) => (
                      <button
                        key={lang}
                        id={`voice-lang-${lang}`}
                        onClick={() => setVoiceLang(lang)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                          voiceLang === lang
                            ? "bg-blue-600 text-white border-blue-600"
                            : "bg-white text-slate-600 border-slate-200 hover:border-blue-300"
                        }`}
                      >
                        {lang === "en" ? "🇺🇸 English" : lang === "hi" ? "🇮🇳 Hindi" : "🇮🇳 Marathi"}
                      </button>
                    ))}
                  </div>
                  <span className="text-xs text-[var(--text-secondary)]">Select input language</span>
                </div>

                {/* Mic button */}
                <div className="flex flex-col items-center py-4 gap-4">
                  <button
                    id="voice-record-btn"
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`w-20 h-20 rounded-full flex items-center justify-center shadow-lg transition-all ${
                      isRecording
                        ? "bg-red-500 hover:bg-red-600 animate-pulse ring-4 ring-red-200"
                        : "bg-blue-600 hover:bg-blue-700 hover:scale-105"
                    }`}
                  >
                    {isRecording ? (
                      <MicOff className="w-8 h-8 text-white" />
                    ) : (
                      <Mic className="w-8 h-8 text-white" />
                    )}
                  </button>
                  <p className="text-xs text-[var(--text-secondary)]">
                    {isRecording ? "Recording… click to stop" : "Click to start speaking"}
                  </p>
                </div>

                {/* Transcript preview */}
                <div className="relative">
                  <textarea
                    id="voice-transcript-preview"
                    rows={3}
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    placeholder='Transcript will appear here… or type manually, e.g. "Order CBC and CRP"'
                    className="w-full px-4 py-3 border border-[var(--border)] rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white"
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    id="submit-voice-command-btn"
                    onClick={submitVoiceCommand}
                    disabled={!transcript.trim() || loadingVoice}
                    className="btn flex items-center gap-2 disabled:opacity-40"
                  >
                    {loadingVoice ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4" />}
                    Parse Command
                  </button>
                  <button onClick={() => setTranscript("")} className="btn-outline text-sm">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Pending command confirmation */}
            {pendingCommand && (
              <div className="card border-2 border-amber-300 bg-amber-50/30">
                <div className="card-header !bg-amber-50/50">
                  <h3 className="font-semibold text-sm flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Confirm Voice Command
                  </h3>
                </div>
                <div className="card-body space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-500">Transcript:</span>
                    <span className="text-sm">"{pendingCommand.raw_transcript}"</span>
                  </div>
                  {pendingCommand.translated_text && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-slate-500">Translated:</span>
                      <span className="text-sm">"{pendingCommand.translated_text}"</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-500">Intent:</span>
                    <span className="badge-info">{pendingCommand.intent || "unknown"}</span>
                    <span className="text-xs text-slate-400">
                      {Math.round(pendingCommand.confidence * 100)}% confidence
                    </span>
                  </div>
                  {pendingCommand.suggested_orders.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-slate-500 mb-2">Suggested Orders:</p>
                      <div className="space-y-1.5">
                        {pendingCommand.suggested_orders.map((o, i) => (
                          <div key={i} className="flex items-center gap-2 p-2 bg-white rounded-lg border">
                            <span className="badge-neutral text-xs">{o.order_type}</span>
                            <span className="text-sm font-medium">{o.name}</span>
                            {o.note && <span className="text-xs text-slate-400">— {o.note}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <p className="text-xs text-amber-700 bg-amber-100 p-2 rounded-lg">
                    ⚠️ Doctor confirmation required before any action is executed.
                  </p>
                  <div className="flex gap-2 pt-1">
                    <button
                      id={`confirm-cmd-${pendingCommand.id}`}
                      onClick={() => confirmCommand(pendingCommand.id)}
                      className="btn flex items-center gap-2 !bg-emerald-600 hover:!bg-emerald-700"
                    >
                      <Check className="w-4 h-4" /> Confirm & Proceed
                    </button>
                    <button
                      onClick={() => setPendingCommand(null)}
                      className="btn-outline text-sm flex items-center gap-1.5"
                    >
                      <X className="w-4 h-4" /> Dismiss
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Voice command history */}
            {voiceCommands.length > 0 && (
              <div className="card">
                <div className="card-header">
                  <h3 className="font-semibold text-sm">Command History</h3>
                </div>
                <div className="divide-y divide-[var(--border)]">
                  {voiceCommands.slice(0, 10).map((cmd) => (
                    <div key={cmd.id} className="px-4 py-3 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                        <Mic className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">"{cmd.raw_transcript}"</p>
                        <p className="text-xs text-[var(--text-secondary)]">
                          {cmd.intent || "unknown"} · {cmd.detected_language.toUpperCase()} ·{" "}
                          {new Date(cmd.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          cmd.status === "CONFIRMED"
                            ? "bg-green-100 text-green-700"
                            : cmd.status === "PENDING"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {cmd.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Tab: AI Agents ── */}
        {activeTab === "agents" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <BotMessageSquare className="w-5 h-5 text-indigo-500" /> AI Agent Orchestration
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Create agent task */}
              <div className="card">
                <div className="card-header">
                  <h3 className="font-semibold text-sm">Create Agent Task</h3>
                </div>
                <div className="card-body space-y-4">
                  <div>
                    <label className="form-label">Agent Type</label>
                    <select
                      id="agent-type-select"
                      value={agentType}
                      onChange={(e) => setAgentType(e.target.value)}
                      className="input w-full"
                    >
                      <option value="discharge_summary">Discharge Summary</option>
                      <option value="documentation_draft">Documentation Draft</option>
                      <option value="clinical_data_summary">Clinical Data Summary</option>
                      <option value="workflow_reminder">Workflow Reminders</option>
                    </select>
                  </div>
                  <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-700">
                    ⚠️ AI agents generate DRAFTS only. Clinician must review and approve before use.
                  </div>
                  <button
                    id="create-agent-task-btn"
                    onClick={createAgentTask}
                    disabled={loadingAgent}
                    className="btn w-full flex items-center justify-center gap-2 disabled:opacity-40"
                  >
                    {loadingAgent ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <BotMessageSquare className="w-4 h-4" />
                    )}
                    {loadingAgent ? "Generating Draft…" : "Start Agent"}
                  </button>
                </div>
              </div>

              {/* Task list */}
              <div className="card lg:col-span-2">
                <div className="card-header">
                  <h3 className="font-semibold text-sm">Agent Tasks</h3>
                </div>
                {agentTasks.length > 0 ? (
                  <div className="divide-y divide-[var(--border)]">
                    {agentTasks.slice(0, 8).map((task) => (
                      <div
                        key={task.id}
                        className="px-4 py-3 hover:bg-[var(--bg-secondary)] cursor-pointer transition-colors"
                        onClick={() => {
                          setSelectedTask(task);
                          setEditDraftContent(task.draft_output || "");
                        }}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">
                            <FileText className="w-5 h-5 text-indigo-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold capitalize">
                              {task.agent_type.replace(/_/g, " ")}
                            </p>
                            <p className="text-xs text-[var(--text-secondary)]">
                              {new Date(task.created_at).toLocaleString()}
                            </p>
                          </div>
                          <span
                            className={`text-xs px-2 py-1 rounded-full font-medium ${
                              task.status === "APPROVED"
                                ? "bg-green-100 text-green-700"
                                : task.status === "AWAITING_APPROVAL"
                                ? "bg-amber-100 text-amber-700"
                                : task.status === "FAILED"
                                ? "bg-red-100 text-red-700"
                                : "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {task.status.replace(/_/g, " ")}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card-body">
                    <EmptyState
                      icon={<ClipboardList className="w-8 h-8 text-indigo-200" />}
                      title="No agent tasks"
                      desc="Create an agent task to generate clinical drafts."
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Task detail / approval */}
            {selectedTask && (
              <div className="card border-2 border-indigo-200">
                <div className="card-header flex justify-between items-center">
                  <h3 className="font-semibold text-sm">
                    {selectedTask.agent_type.replace(/_/g, " ").toUpperCase()} — Draft Output
                  </h3>
                  <button onClick={() => setSelectedTask(null)}>
                    <X className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
                <div className="card-body space-y-4">
                  {selectedTask.status === "AWAITING_APPROVAL" ? (
                    <textarea
                      value={editDraftContent}
                      onChange={(e) => setEditDraftContent(e.target.value)}
                      className="w-full bg-white rounded-xl p-4 border border-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-400 font-mono text-xs leading-relaxed max-h-[400px] overflow-y-auto resize-y min-h-[250px] shadow-inner"
                      placeholder="Draft appears here. Edit before approving..."
                    />
                  ) : (
                    <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 font-mono text-xs leading-relaxed whitespace-pre-wrap max-h-[400px] overflow-y-auto">
                      {selectedTask.draft_output || "Draft is being generated…"}
                    </div>
                  )}
                  {selectedTask.status === "AWAITING_APPROVAL" && (
                    <div className="flex items-center gap-3">
                      <div className="flex-1 p-3 bg-amber-50 rounded-xl text-xs text-amber-700 border border-amber-200">
                        This is an AI-generated draft. Review carefully before approving.
                      </div>
                      <button
                        id={`approve-task-${selectedTask.id}`}
                        onClick={() => approveAgentTask(selectedTask.id)}
                        className="btn flex items-center gap-2 !bg-emerald-600 hover:!bg-emerald-700 shrink-0"
                      >
                        <Check className="w-4 h-4" /> Approve Draft
                      </button>
                    </div>
                  )}
                  {selectedTask.status === "APPROVED" && (
                    <div className="flex items-center gap-2 p-3 bg-green-50 rounded-xl border border-green-200">
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                      <span className="text-xs text-green-700 font-medium">Approved by clinician</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Shared sub-components ────────────────────────────────────────────────────

function SummaryListCard({
  title, icon, items, emptyText, color, highlight = false,
}: {
  title: string;
  icon: React.ReactNode;
  items: string[];
  emptyText: string;
  color: string;
  highlight?: boolean;
}) {
  const colorMap: Record<string, string> = {
    emerald: "bg-emerald-50 border-emerald-100",
    rose: "bg-rose-50 border-rose-100",
    amber: "bg-amber-50 border-amber-100",
    red: "bg-red-50 border-red-100",
  };
  return (
    <div className={`card border ${highlight && items.length > 0 ? "border-red-200" : "border-[var(--border)]"}`}>
      <div className="card-header">
        <span className="text-xs font-semibold flex items-center gap-1.5">
          {icon} {title}
        </span>
      </div>
      <div className="card-body">
        {items.length > 0 ? (
          <ul className="space-y-1.5">
            {items.map((item, i) => (
              <li key={i} className={`text-xs px-2 py-1 rounded-md ${colorMap[color] || "bg-slate-50"}`}>
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-[var(--text-secondary)] italic">{emptyText}</p>
        )}
      </div>
    </div>
  );
}

function AiLoading({ text }: { text: string }) {
  return (
    <div className="card border border-violet-100 bg-violet-50/30">
      <div className="card-body flex flex-col items-center gap-4 py-10">
        <div className="relative">
          <Brain className="w-10 h-10 text-violet-400" />
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-violet-600 rounded-full animate-bounce" />
        </div>
        <p className="text-sm text-violet-700 text-center">{text}</p>
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-violet-500 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function EmptyState({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="card">
      <div className="card-body flex flex-col items-center gap-3 py-12 text-center">
        {icon}
        <p className="text-sm font-semibold text-[var(--text-secondary)]">{title}</p>
        <p className="text-xs text-[var(--text-secondary)] max-w-80">{desc}</p>
      </div>
    </div>
  );
}
