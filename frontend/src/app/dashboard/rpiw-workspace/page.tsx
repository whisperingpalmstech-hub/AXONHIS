"use client";
import React, { useEffect, useState } from "react";
import { useTranslation } from "@/i18n";
import PatientSummaryPanel from "./PatientSummaryPanel";
import ClinicalActionPanel from "./ClinicalActionPanel";
import AiAssistantPanel from "./AiAssistantPanel";
import VitalsRecordingPanel from "./VitalsRecordingPanel";
import MedicationAdminPanel from "./MedicationAdminPanel";
import TaskListPanel from "./TaskListPanel";
import PatientMonitorPanel from "./PatientMonitorPanel";
import SampleQueuePanel from "./SampleQueuePanel";
import BarcodeScannerPanel from "./BarcodeScannerPanel";
import CollectionStatusPanel from "./CollectionStatusPanel";

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
  const { t } = useTranslation();
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
    setLoading(false);
  };

  const themeConfig: Record<string, { bg: string; accent: string; gradient: string }> = {
    doctor: { bg: "bg-indigo-50", accent: "bg-indigo-600", gradient: "from-indigo-600 to-blue-500" },
    nurse: { bg: "bg-emerald-50", accent: "bg-emerald-600", gradient: "from-emerald-600 to-teal-500" },
    phlebotomist: { bg: "bg-amber-50", accent: "bg-amber-600", gradient: "from-amber-600 to-orange-500" },
  };

  const theme = themeConfig[selectedRole] || themeConfig.doctor;
  const tWorkspaceLabel = t(`rpiw.${selectedRole}Workspace`); // Dynamic translation
  
  const workflows = config?.workflows || [];
  const components = config?.components || [];
  const permissions = config?.permissions || [];

  return (
    <div className={`min-h-screen ${theme.bg} transition-colors duration-500`}>
      {/* Top Bar */}
      <div className={`bg-gradient-to-r ${theme.gradient} text-white px-6 py-4 shadow-lg`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{tWorkspaceLabel}</h1>
            <p className="text-white/70 text-sm mt-0.5">{t("rpiw.subtitle")}</p>
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
                <div className="flex justify-between"><span className="text-gray-500">{t("rpiw.userId")}</span><span className="font-mono">STAFF-{selectedRole.toUpperCase().slice(0, 3)}-001</span></div>
                <div className="flex justify-between"><span className="text-gray-500">{t("rpiw.department")}</span><span>{t("rpiw.generalMedicine")}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">{t("rpiw.activeSession")}</span><span className="text-green-600 font-semibold">● {t("rpiw.online")}</span></div>
              </div>
            </div>

            {/* Workflow Navigation */}
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">{t("rpiw.workflowsTitle")}</h3>
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
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">{t("rpiw.permissionsTitle")}</h3>
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
                  {workflows.find((w: any) => w.workflow_key === activeWorkflow)?.workflow_label || t("rpiw.workflow")}
                </h2>
                <p className="text-sm text-gray-500 mb-6">{t("rpiw.activeWorkflowSubtitle")}</p>

                {/* Simulated workflow content */}
                {activeWorkflow === "patient_summary" || activeWorkflow === "review_summary" ? (
                  <div className="mt-4">
                    <PatientSummaryPanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : activeWorkflow === "actions" ? (
                  <div className="mt-4">
                    <ClinicalActionPanel patientUhid="UHID-TEST-001" userRole={selectedRole} />
                  </div>
                ) : activeWorkflow === "ai_assistant" || activeWorkflow === "ai_suggestions_panel" ? (
                  <div className="mt-4">
                    <AiAssistantPanel patientUhid="UHID-TEST-001" userRole={selectedRole} />
                  </div>
                ) : activeWorkflow === "record_vitals" || activeWorkflow === "vitals_recording_panel" ? (
                  <div className="mt-4">
                    <VitalsRecordingPanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : activeWorkflow === "administer_meds" || activeWorkflow === "medication_admin_panel" ? (
                  <div className="mt-4">
                    <MedicationAdminPanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : activeWorkflow === "monitor_patient" || activeWorkflow === "patient_monitor_panel" ? (
                  <div className="mt-4">
                    <PatientMonitorPanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : activeWorkflow === "execute_tasks" || activeWorkflow === "task_list_panel" ? (
                  <div className="mt-4">
                    <TaskListPanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : activeWorkflow === "view_pending" || activeWorkflow === "sample_queue_panel" ? (
                  <div className="mt-4">
                    <SampleQueuePanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : activeWorkflow === "scan_barcode" || activeWorkflow === "barcode_scanner_panel" ? (
                  <div className="mt-4">
                    <BarcodeScannerPanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : activeWorkflow === "transport_status" || activeWorkflow === "collection_status_panel" ? (
                  <div className="mt-4">
                    <CollectionStatusPanel patientUhid="UHID-TEST-001" />
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center text-slate-400">
                    <div className="text-4xl mb-3">
                      {ROLE_ICONS[workflows.find((w: any) => w.workflow_key === activeWorkflow)?.icon] || "📌"}
                    </div>
                    <p className="text-gray-600 font-medium">
                      {workflows.find((w: any) => w.workflow_key === activeWorkflow)?.workflow_label}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-1 uppercase tracking-widest">
                       {t("rpiw.route")}: {workflows.find((w: any) => w.workflow_key === activeWorkflow)?.route_path}
                    </p>
                    <p className="text-xs text-slate-400 mt-4 italic font-medium">
                      {t("rpiw.linkedPanelInfo").replace("{role}", selectedRole)}
                      <br />{t("rpiw.syncInfo")}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm border p-8 text-center">
                <div className="text-5xl mb-4">🏥</div>
                <h2 className="text-lg font-bold text-gray-800">{t("rpiw.welcomeTo")} {tWorkspaceLabel}</h2>
                <p className="text-sm text-gray-500 mt-1">{t("rpiw.selectWorkflowToStart")}</p>
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
                  
                  {/* Phase 23 - Real Component Linking */}
                  <div className="mt-2">
                    {comp.component_key === "patient_summary_panel" ? (
                      <PatientSummaryPanel patientUhid="UHID-TEST-001" />
                    ) : comp.component_key === "clinical_action_panel" ? (
                      <ClinicalActionPanel patientUhid="UHID-TEST-001" userRole={selectedRole} />
                    ) : comp.component_key === "ai_suggestions_panel" ? (
                      <AiAssistantPanel patientUhid="UHID-TEST-001" userRole={selectedRole} />
                    ) : comp.component_key === "vitals_recording_panel" ? (
                      <VitalsRecordingPanel patientUhid="UHID-TEST-001" />
                    ) : comp.component_key === "medication_admin_panel" ? (
                      <MedicationAdminPanel patientUhid="UHID-TEST-001" />
                    ) : comp.component_key === "task_list_panel" ? (
                      <TaskListPanel patientUhid="UHID-TEST-001" />
                    ) : comp.component_key === "patient_monitor_panel" ? (
                      <PatientMonitorPanel patientUhid="UHID-TEST-001" />
                    ) : comp.component_key === "sample_queue_panel" ? (
                      <SampleQueuePanel patientUhid="UHID-TEST-001" />
                    ) : comp.component_key === "barcode_scanner_panel" ? (
                      <BarcodeScannerPanel patientUhid="UHID-TEST-001" />
                    ) : comp.component_key === "collection_status_panel" ? (
                      <CollectionStatusPanel patientUhid="UHID-TEST-001" />
                    ) : (
                      <div className="border border-dashed border-gray-200 rounded-lg p-4 text-center text-xs text-gray-400">
                        <p>Dynamic component: <code className="bg-gray-100 px-1 rounded">{comp.component_key}</code></p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Activity Feed */}
          <div className="col-span-3 space-y-5">
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">{t("rpiw.recentActivity")}</h3>
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
                <p className="text-xs text-gray-400 italic">{t("rpiw.noActivityRecord")}</p>
              )}
            </div>

            {/* Quick Stats */}
            <div className="bg-white rounded-2xl shadow-sm border p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">{t("rpiw.sessionStats")}</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{t("rpiw.workflowsAvailable")}</span>
                  <span className="text-sm font-bold">{workflows.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{t("rpiw.activePermissions")}</span>
                  <span className="text-sm font-bold">{permissions.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{t("rpiw.uiComponents")}</span>
                  <span className="text-sm font-bold">{components.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{t("rpiw.activityLogs")}</span>
                  <span className="text-sm font-bold">{logs.length}</span>
                </div>
              </div>
            </div>

            {/* Access Control Info */}
            <div className={`rounded-2xl p-5 bg-gradient-to-br ${theme.gradient} text-white`}>
              <h3 className="text-xs font-bold uppercase tracking-wider mb-2 text-white/70">{t("rpiw.rbacStatus")}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-white/20 rounded flex items-center justify-center text-xs">🔒</span>
                  <span>{t("rpiw.accessControlActive")}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-white/20 rounded flex items-center justify-center text-xs">📝</span>
                  <span>{t("rpiw.auditLoggingEnabled")}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-white/20 rounded flex items-center justify-center text-xs">🔐</span>
                  <span>{t("rpiw.encryptedSession")}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
