"use client";
import React, { useEffect, useState } from "react";
import PatientSummaryPanel from "./PatientSummaryPanel";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const rpiwApi = {
  getWorkspaceConfig: async (roleCode: string) => {
    const res = await fetch(`${API}/api/v1/rpiw/workspace/${roleCode}`);
    return res.json();
  },
  getActivityLogs: async (roleCode?: string) => {
    const url = roleCode
      ? `${API}/api/v1/rpiw/activity-logs?role_code=${roleCode}&limit=20`
      : `${API}/api/v1/rpiw/activity-logs?limit=20`;
    const res = await fetch(url);
    return res.json();
  },
};

const ROLE_ICONS: Record<string, string> = {
  clipboard: "📋", pencil: "✏️", flask: "🧪", pill: "💊", chart: "📊",
  heart: "❤️", monitor: "🖥️", check: "✅", list: "📃", syringe: "💉",
  barcode: "🔲", truck: "🚚",
};

const ROLE_THEMES: Record<string, { bg: string; accent: string; gradient: string; label: string }> = {
  doctor: { bg: "bg-indigo-50", accent: "bg-indigo-600", gradient: "from-indigo-600 to-blue-500", label: "Doctor Workspace" },
  nurse: { bg: "bg-emerald-50", accent: "bg-emerald-600", gradient: "from-emerald-600 to-teal-500", label: "Nurse Workspace" },
  phlebotomist: { bg: "bg-amber-50", accent: "bg-amber-600", gradient: "from-amber-600 to-orange-500", label: "Phlebotomist Workspace" },
};

export default function RpiwWorkspacePage() {
  const [selectedRole, setSelectedRole] = useState("doctor");
  const [config, setConfig] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeWorkflow, setActiveWorkflow] = useState<string | null>(null);

  useEffect(() => { loadWorkspace(selectedRole); }, [selectedRole]);

  const loadWorkspace = async (role: string) => {
    setLoading(true);
    setActiveWorkflow(null);
    try {
      const cfg = await rpiwApi.getWorkspaceConfig(role);
      setConfig(cfg);
      const l = await rpiwApi.getActivityLogs(role);
      setLogs(l || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const theme = ROLE_THEMES[selectedRole] || ROLE_THEMES.doctor;
  const workflows = config?.workflows || [];
  const components = config?.components || [];
  const permissions = config?.permissions || [];

  return (
    <div className={`min-h-screen ${theme.bg} transition-colors duration-500`}>
      {/* Top Bar */}
      <div className={`bg-gradient-to-r ${theme.gradient} text-white px-6 py-4 shadow-lg`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{theme.label}</h1>
            <p className="text-white/70 text-sm mt-0.5">Role-Based Patient Interaction Workspace (RPIW)</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Role Switcher */}
            {(["doctor", "nurse", "phlebotomist"] as const).map((r) => (
              <button key={r} onClick={() => setSelectedRole(r)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  selectedRole === r
                    ? "bg-white text-gray-900 shadow-lg scale-105"
                    : "bg-white/20 hover:bg-white/30 text-white"
                }`}>
                {r === "doctor" ? "🩺" : r === "nurse" ? "💉" : "🧪"} {r.charAt(0).toUpperCase() + r.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin w-8 h-8 border-4 border-gray-300 border-t-blue-600 rounded-full" />
        </div>
      ) : (
        <div className="p-6 grid grid-cols-12 gap-6">
          {/* Left: Navigation & Workflows */}
          <div className="col-span-3 space-y-5">
            {/* Session Context Card */}
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${theme.gradient} flex items-center justify-center text-white text-xl`}>
                  {selectedRole === "doctor" ? "🩺" : selectedRole === "nurse" ? "💉" : "🧪"}
                </div>
                <div>
                  <div className="font-bold text-sm capitalize">{selectedRole}</div>
                  <div className="text-xs text-gray-500">General Medicine</div>
                </div>
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between"><span className="text-gray-500">User ID</span><span className="font-mono">STAFF-{selectedRole.toUpperCase().slice(0, 3)}-001</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Department</span><span>General Medicine</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Active Session</span><span className="text-green-600 font-semibold">● Online</span></div>
              </div>
            </div>

            {/* Workflow Navigation */}
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Workflows</h3>
              <div className="space-y-1">
                {workflows.map((wf: any) => (
                  <button key={wf.workflow_key} onClick={() => setActiveWorkflow(wf.workflow_key)}
                    className={`w-full text-left px-4 py-3 rounded-xl text-sm flex items-center gap-3 transition-all duration-200 ${
                      activeWorkflow === wf.workflow_key
                        ? `bg-gradient-to-r ${theme.gradient} text-white shadow-md`
                        : "hover:bg-gray-50 text-gray-700"
                    }`}>
                    <span className="text-lg">{ROLE_ICONS[wf.icon] || "📌"}</span>
                    <span className="font-medium">{wf.workflow_label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Permissions Summary */}
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Permissions</h3>
              <div className="space-y-2">
                {permissions.map((p: any) => (
                  <div key={p.permission_key} className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${p.can_create || p.can_update ? 'bg-green-500' : 'bg-gray-300'}`} />
                    <span className="text-xs text-gray-600">{p.permission_label}</span>
                    <div className="flex gap-1 ml-auto">
                      {p.can_create && <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-mono">C</span>}
                      {p.can_read && <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-mono">R</span>}
                      {p.can_update && <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-mono">U</span>}
                      {p.can_delete && <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-mono">D</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Center: Dynamic Component Area */}
          <div className="col-span-6 space-y-5">
            {/* Active Workflow Display */}
            {activeWorkflow ? (
              <div className={`bg-white rounded-2xl shadow-sm border p-6 relative overflow-hidden`}>
                <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${theme.gradient}`} />
                <h2 className="text-lg font-bold mb-1">
                  {workflows.find((w: any) => w.workflow_key === activeWorkflow)?.workflow_label || "Workflow"}
                </h2>
                <p className="text-sm text-gray-500 mb-6">Active clinical workflow panel</p>

                {/* Simulated workflow content */}
                {activeWorkflow === "patient_summary" ? (
                  <div className="mt-4">
                    <PatientSummaryPanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
                    <div className="text-4xl mb-3">
                      {ROLE_ICONS[workflows.find((w: any) => w.workflow_key === activeWorkflow)?.icon] || "📌"}
                    </div>
                    <p className="text-gray-600 font-medium">
                      {workflows.find((w: any) => w.workflow_key === activeWorkflow)?.workflow_label}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      Route: {workflows.find((w: any) => w.workflow_key === activeWorkflow)?.route_path}
                    </p>
                    <p className="text-xs text-gray-400 mt-4 italic">
                      This workspace panel will be dynamically loaded based on the selected workflow.
                      <br />Connect with existing AxonHIS modules (OPD, IPD, LIS, EHR).
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm border p-8 text-center">
                <div className="text-5xl mb-4">🏥</div>
                <h2 className="text-lg font-bold text-gray-800">Welcome to {theme.label}</h2>
                <p className="text-sm text-gray-500 mt-1">Select a workflow from the left panel to get started</p>
              </div>
            )}

            {/* Dynamic Component Panels */}
            <div className="grid grid-cols-2 gap-4">
              {components.map((comp: any) => (
                <div key={comp.component_key}
                  className={`bg-white rounded-2xl shadow-sm border p-5 transition-all hover:shadow-md hover:-translate-y-0.5 ${
                    comp.component_type === "widget" ? "col-span-2" : ""
                  }`}>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-sm text-gray-800">{comp.component_label}</h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wide ${
                      comp.component_type === "panel" ? "bg-blue-50 text-blue-600" :
                      comp.component_type === "widget" ? "bg-purple-50 text-purple-600" :
                      "bg-amber-50 text-amber-600"
                    }`}>{comp.component_type}</span>
                  </div>
                  <div className="border border-dashed border-gray-200 rounded-lg p-4 text-center text-xs text-gray-400">
                    <p>Dynamic component: <code className="bg-gray-100 px-1 rounded">{comp.component_key}</code></p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Activity Feed */}
          <div className="col-span-3 space-y-5">
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Recent Activity</h3>
              {logs.length > 0 ? (
                <div className="space-y-3 max-h-[50vh] overflow-y-auto">
                  {logs.map((log: any) => (
                    <div key={log.id} className="flex gap-3 items-start">
                      <div className="w-2 h-2 rounded-full bg-blue-400 mt-2 flex-shrink-0" />
                      <div>
                        <p className="text-xs font-medium text-gray-700">{log.action_label || log.action}</p>
                        <p className="text-[10px] text-gray-400">{new Date(log.performed_at).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-400 italic">No activity recorded yet. Actions performed in the workspace will appear here.</p>
              )}
            </div>

            {/* Quick Stats */}
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Session Stats</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Workflows Available</span>
                  <span className="text-sm font-bold">{workflows.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Active Permissions</span>
                  <span className="text-sm font-bold">{permissions.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">UI Components</span>
                  <span className="text-sm font-bold">{components.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Activity Logs</span>
                  <span className="text-sm font-bold">{logs.length}</span>
                </div>
              </div>
            </div>

            {/* Access Control Info */}
            <div className={`rounded-2xl p-5 bg-gradient-to-br ${theme.gradient} text-white`}>
              <h3 className="text-xs font-bold uppercase tracking-wider mb-2 text-white/70">RBAC Status</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-white/20 rounded flex items-center justify-center text-xs">🔒</span>
                  <span>Access Control Active</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-white/20 rounded flex items-center justify-center text-xs">📝</span>
                  <span>Audit Logging Enabled</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-white/20 rounded flex items-center justify-center text-xs">🔐</span>
                  <span>Encrypted Session</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
