"use client";
import React, { useState, useEffect } from "react";
import { useTranslation } from "@/i18n";
import { TopNav } from "@/components/ui/TopNav";
import {
  avatarApi,
  type WorkflowConfig,
  type AvatarAnalytics,
  type ConversationLog,
} from "@/lib/avatar-api";

export default function AvatarAdminPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"workflows" | "analytics" | "logs">("workflows");
  const [workflows, setWorkflows] = useState<WorkflowConfig[]>([]);
  const [analytics, setAnalytics] = useState<AvatarAnalytics | null>(null);
  const [logs, setLogs] = useState<ConversationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [tab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === "workflows") {
        const data = await avatarApi.getWorkflowConfigs();
        setWorkflows(data);
      } else if (tab === "analytics") {
        const data = await avatarApi.getAnalytics();
        setAnalytics(data);
      } else if (tab === "logs") {
        const data = await avatarApi.getConversationLogs(50, 0);
        setLogs(data);
      }
    } catch (err) {
      console.error("Failed to load avatar admin data:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleWorkflow = async (config: WorkflowConfig) => {
    setSaving(config.id);
    try {
      const updated = await avatarApi.updateWorkflowConfig(config.id, {
        is_enabled: !config.is_enabled,
      });
      setWorkflows((prev) =>
        prev.map((w) => (w.id === updated.id ? updated : w))
      );
    } catch (err) {
      console.error("Failed to update workflow:", err);
    } finally {
      setSaving(null);
    }
  };

  return (
    <div>
      <TopNav title="Avatar Management Dashboard" />

      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">
              🤖 Virtual Avatar Administration
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Manage avatar workflows, monitor usage, and review conversation logs
            </p>
          </div>
          <a
            href="/dashboard/avatar"
            className="btn-primary flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
            Open Avatar Kiosk
          </a>
        </div>

        {/* Tabs */}
        <div className="tabs">
          {[
            { key: "workflows" as const, label: "Workflow Config", icon: "⚙️" },
            { key: "analytics" as const, label: "Usage Analytics", icon: "📊" },
            { key: "logs" as const, label: "Conversation Logs", icon: "💬" },
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setTab(item.key)}
              className={`tab ${tab === item.key ? "tab-active" : ""}`}
            >
              <span className="mr-1.5">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          </div>
        ) : (
          <>
            {/* ── Workflows Tab ────────────────────────────────── */}
            {tab === "workflows" && (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {workflows.map((wf) => (
                  <div
                    key={wf.id}
                    className={`card transition-all duration-200 ${
                      wf.is_enabled
                        ? "border-emerald-200 bg-emerald-50/30"
                        : "border-slate-200 bg-slate-50/30 opacity-70"
                    }`}
                  >
                    <div className="card-body">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{wf.icon || "⚙️"}</span>
                          <div>
                            <h3 className="font-bold text-slate-800 text-sm">
                              {wf.display_name}
                            </h3>
                            <p className="text-xs text-slate-500 mt-0.5">
                              {wf.description}
                            </p>
                          </div>
                        </div>

                        {/* Toggle */}
                        <button
                          onClick={() => toggleWorkflow(wf)}
                          disabled={saving === wf.id}
                          className={`
                            relative w-11 h-6 rounded-full transition-colors duration-200 shrink-0
                            ${wf.is_enabled ? "bg-emerald-500" : "bg-slate-300"}
                            ${saving === wf.id ? "opacity-50" : ""}
                          `}
                        >
                          <span
                            className={`
                              absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200
                              ${wf.is_enabled ? "left-[22px]" : "left-0.5"}
                            `}
                          />
                        </button>
                      </div>

                      <div className="mt-4 flex items-center gap-2">
                        <span
                          className={`badge ${
                            wf.is_enabled ? "badge-success" : "badge-neutral"
                          }`}
                        >
                          {wf.is_enabled ? "Active" : "Disabled"}
                        </span>
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider">
                          Key: {wf.workflow_key}
                        </span>
                      </div>

                      {wf.system_prompt_override && (
                        <div className="mt-3 p-2.5 rounded-lg bg-slate-100 border border-slate-200">
                          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                            Custom Prompt Override
                          </p>
                          <p className="text-xs text-slate-600 line-clamp-3">
                            {wf.system_prompt_override}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ── Analytics Tab ────────────────────────────────── */}
            {tab === "analytics" && analytics && (
              <div className="space-y-6">
                {/* KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { label: "Total Sessions", value: analytics.total_sessions, color: "bg-blue-50 border-blue-100", icon: "🗣️" },
                    { label: "Active Sessions", value: analytics.active_sessions, color: "bg-emerald-50 border-emerald-100", icon: "🟢" },
                    { label: "Total Messages", value: analytics.total_messages, color: "bg-violet-50 border-violet-100", icon: "💬" },
                    { label: "Avg Msgs/Session", value: analytics.avg_messages_per_session, color: "bg-amber-50 border-amber-100", icon: "📊" },
                  ].map((stat) => (
                    <div key={stat.label} className={`card ${stat.color} border`}>
                      <div className="card-body flex items-center gap-4">
                        <span className="text-3xl">{stat.icon}</span>
                        <div>
                          <p className="text-2xl font-extrabold text-slate-800">{stat.value}</p>
                          <p className="text-xs font-medium text-slate-500">{stat.label}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Top Workflows */}
                {analytics.top_workflows.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <h3 className="font-bold text-slate-800 flex items-center gap-2">
                        <span>🏆</span> Top Workflows
                      </h3>
                    </div>
                    <div className="card-body">
                      <div className="space-y-3">
                        {analytics.top_workflows.map((wf, i) => (
                          <div key={i} className="flex items-center gap-3">
                            <span className="text-sm font-bold text-slate-400 w-6">#{i + 1}</span>
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-medium text-slate-700 capitalize">
                                  {wf.workflow.replace(/_/g, " ")}
                                </span>
                                <span className="text-sm font-bold text-slate-800">{wf.count}</span>
                              </div>
                              <div className="w-full h-2 rounded-full bg-slate-100">
                                <div
                                  className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500"
                                  style={{
                                    width: `${(wf.count / Math.max(...analytics.top_workflows.map(w => w.count))) * 100}%`,
                                  }}
                                />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Language Distribution */}
                {analytics.language_distribution.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <h3 className="font-bold text-slate-800 flex items-center gap-2">
                        <span>🌐</span> Language Distribution
                      </h3>
                    </div>
                    <div className="card-body">
                      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
                        {analytics.language_distribution.map((lang) => (
                          <div key={lang.language} className="text-center p-3 rounded-xl bg-slate-50 border border-slate-100">
                            <p className="text-2xl font-extrabold text-slate-800">{lang.count}</p>
                            <p className="text-xs font-medium text-slate-500 uppercase mt-1">{lang.language}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── Logs Tab ─────────────────────────────────────── */}
            {tab === "logs" && (
              <div className="card">
                <div className="card-header">
                  <h3 className="font-bold text-slate-800">Recent Conversations</h3>
                  <span className="text-xs text-slate-500">{logs.length} sessions</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Session ID</th>
                        <th>Language</th>
                        <th>Status</th>
                        <th>Workflow</th>
                        <th>Messages</th>
                        <th>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr key={log.session_id}>
                          <td>
                            <span className="font-mono text-xs text-slate-600">
                              {log.session_id.slice(0, 8)}...
                            </span>
                          </td>
                          <td>
                            <span className="badge badge-info uppercase">{log.language}</span>
                          </td>
                          <td>
                            <span
                              className={`badge ${
                                log.status === "active"
                                  ? "badge-success"
                                  : log.status === "completed"
                                  ? "badge-neutral"
                                  : "badge-warning"
                              }`}
                            >
                              {log.status}
                            </span>
                          </td>
                          <td className="text-sm text-slate-600 capitalize">
                            {log.workflow?.replace(/_/g, " ") || "—"}
                          </td>
                          <td className="text-sm font-semibold text-slate-800">
                            {log.message_count}
                          </td>
                          <td className="text-xs text-slate-500">
                            {new Date(log.created_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                      {logs.length === 0 && (
                        <tr>
                          <td colSpan={6} className="text-center py-12 text-slate-400">
                            No conversation logs yet
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
