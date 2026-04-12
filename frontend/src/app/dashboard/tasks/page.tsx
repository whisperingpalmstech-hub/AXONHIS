"use client";
import { useTranslation } from "@/i18n";
import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  ListOrdered, Activity, Pill, Syringe, Scan, Stethoscope, 
  CheckCircle2, XCircle, Clock, Check, FileText, ChevronRight,
  User, Play, Search, Filter, Loader2, ArrowRight, X
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

const TASK_TYPES = {
  COLLECT_SPECIMEN: { label: "Sample Collection", icon: Syringe, color: "#8B5CF6", bg: "#EDE9FE" },
  PROCESS_LAB_TEST: { label: "Lab Processing", icon: Activity, color: "#8B5CF6", bg: "#EDE9FE" },
  DISPENSE_MEDICATION: { label: "Dispense Med", icon: Pill, color: "#EC4899", bg: "#FCE7F3" },
  ADMINISTER_MEDICATION: { label: "Administer Med", icon: Pill, color: "#EC4899", bg: "#FCE7F3" },
  PERFORM_IMAGING: { label: "Imaging Prep", icon: Scan, color: "#0EA5E9", bg: "#E0F2FE" },
  PERFORM_PROCEDURE: { label: "Procedure Assist", icon: Stethoscope, color: "#F59E0B", bg: "#FEF3C7" },
  VITAL_MONITORING: { label: "Vitals", icon: Activity, color: "#10B981", bg: "#D1FAE5" },
  NURSING_ASSESSMENT: { label: "Nursing", icon: Stethoscope, color: "#10B981", bg: "#D1FAE5" },
  PREPARE_DISCHARGE: { label: "Discharge", icon: ArrowRight, color: "#64748B", bg: "#F1F5F9" },
  GENERIC: { label: "General Task", icon: FileText, color: "#64748B", bg: "#F1F5F9" },
};

const STATUS_MAP = {
  PENDING: { label: "Pending", color: "#64748B", bg: "#F1F5F9", icon: Clock },
  ASSIGNED: { label: "Assigned", color: "#F59E0B", bg: "#FEF3C7", icon: User },
  IN_PROGRESS: { label: "In Progress", color: "#3B82F6", bg: "#DBEAFE", icon: Loader2 },
  COMPLETED: { label: "Completed", color: "#10B981", bg: "#D1FAE5", icon: CheckCircle2 },
  CANCELLED: { label: "Cancelled", color: "#EF4444", bg: "#FEE2E2", icon: XCircle },
};

const PRIORITY_MAP = {
  ROUTINE: { label: "Routine", color: "#64748B" },
  URGENT: { label: "Urgent", color: "#F59E0B" },
  STAT: { label: "STAT", color: "#DC2626" },
};

function getHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export default function TasksPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"queue" | "my_tasks">("queue");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [completeNotes, setCompleteNotes] = useState("");
  const [actionLoading, setActionLoading] = useState<string|null>(null);

  const currentUserStr = typeof window !== "undefined" ? localStorage.getItem("user") : null;
  const currentUser = currentUserStr ? JSON.parse(currentUserStr) : null;

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const endpoint = activeTab === "my_tasks" ? "/api/v1/tasks/my-tasks" : "/api/v1/tasks";
      const res = await fetch(`${API}${endpoint}`, { headers: getHeaders() });
      if (res.ok) {
        setTasks(await res.json());
      }
    } catch { /* ignore */ }
    setLoading(false);
  }, [activeTab]);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  const handleAction = async (taskId: string, action: "assign" | "start" | "complete", data?: any) => {
    setActionLoading(taskId);
    try {
      const res = await fetch(`${API}/api/v1/tasks/${taskId}/${action}`, {
        method: "POST",
        headers: getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
      });
      if (res.ok) {
        if (action === "complete") {
          setShowCompleteModal(false);
          setCompleteNotes("");
          setSelectedTask(null);
        }
        loadTasks();
      } else {
        const e = await res.json();
        const errorMsg = typeof e.detail === 'string' ? e.detail : JSON.stringify(e.detail);
        alert(errorMsg || `Failed to ${action} task`);
      }
    } catch {
      alert("Network error");
    }
    setActionLoading(null);
  };

  const filteredTasks = useMemo(() => {
    return tasks.filter(t => {
      if (filterStatus && t.status !== filterStatus) return false;
      if (filterRole && t.assigned_to_role !== filterRole) return false;
      return true;
    });
  }, [tasks, filterStatus, filterRole]);

  return (
    <div className="flex-1 h-screen overflow-hidden flex flex-col bg-[var(--bg-secondary)] relative">
      <div className="flex z-10 p-6 md:p-8 justify-between items-start gap-4 flex-col sm:flex-row shadow-sm bg-[var(--bg-primary)] border-b border-[var(--border)]">
        <div>
          <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight">{t("tasks.taskCareExecution")}</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">{t("tasks.manageClinicalWorkflowsNursing")}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex p-1 bg-slate-100 rounded-lg">
            <button
              onClick={() => setActiveTab("queue")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${activeTab === "queue" ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >{t("tasks.taskQueue")}</button>
            <button
              onClick={() => setActiveTab("my_tasks")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${activeTab === "my_tasks" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >{t("tasks.myTasks")}</button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6 md:p-8 z-0">
        <div className="max-w-[1400px] mx-auto space-y-6">
          
          {/* Filters */}
          {activeTab === "queue" && (
            <div className="flex flex-wrap gap-4 items-center bg-white p-4 rounded-xl border border-[var(--border)] shadow-sm">
              <div className="flex-1 min-w-[200px] relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder={t("tasks.searchPlaceholder")}
                  className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm"
                />
              </div>
              <select
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                className="px-4 py-2 rounded-lg bg-slate-50 border border-slate-200 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="">{t("tasks.allStatuses")}</option>
                {Object.entries(STATUS_MAP).map(([k, v]) => (
                  <option key={k} value={k}>{t(`tasks.status_${k}`)}</option>
                ))}
              </select>
              <select
                value={filterRole}
                onChange={e => setFilterRole(e.target.value)}
                className="px-4 py-2 rounded-lg bg-slate-50 border border-slate-200 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="">{t("tasks.allRoles")}</option>
                <option value="nurse">{t("tasks.nurse")}</option>
                <option value="lab_tech">{t("tasks.labTech")}</option>
                <option value="radiology_tech">{t("tasks.radiologyTech")}</option>
                <option value="pharmacist">{t("tasks.pharmacist")}</option>
                <option value="doctor">{t("tasks.doctor")}</option>
              </select>
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-slate-400" /></div>
          ) : filteredTasks.length === 0 ? (
            <div className="bg-white rounded-2xl border border-[var(--border)] p-12 text-center shadow-sm">
              <div className="w-16 h-16 rounded-2xl bg-slate-50 flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-500" />
              </div>
              <h3 className="text-lg font-bold text-[var(--text-primary)]">{t("tasks.allCaughtUp")}</h3>
              <p className="text-[var(--text-secondary)] mt-1 max-w-sm mx-auto">
                {activeTab === "my_tasks" ? t("tasks.noActiveTasksAssigned") : t("tasks.noTasksFoundQueue")}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredTasks.map(task => {
                const typeInfo = TASK_TYPES[task.task_type as keyof typeof TASK_TYPES] || TASK_TYPES.GENERIC;
                const statusInfo = STATUS_MAP[task.status as keyof typeof STATUS_MAP];
                const prioInfo = PRIORITY_MAP[task.priority as keyof typeof PRIORITY_MAP];
                const TypeIcon = typeInfo.icon;
                const StatusIcon = statusInfo.icon;
                
                return (
                  <div key={task.id} className="bg-white rounded-2xl border border-[var(--border)] overflow-hidden shadow-sm hover:shadow-md transition-shadow group flex flex-col">
                    <div className="p-5 border-b border-slate-100 flex-1">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: typeInfo.bg, color: typeInfo.color }}>
                            <TypeIcon className="w-5 h-5" />
                          </div>
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: typeInfo.color }}>{t(`tasks.type_${task.task_type}`) || typeInfo.label}</p>
                            <p className="font-bold text-slate-900 mt-0.5 line-clamp-1" title={task.description}>{task.description}</p>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold" style={{ backgroundColor: statusInfo.bg, color: statusInfo.color }}>
                            <StatusIcon className="w-3.5 h-3.5" />
                            {t(`tasks.status_${task.status}`)}
                          </div>
                          {task.priority !== "ROUTINE" && (
                            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-red-50 text-red-600 border border-red-100">
                              {task.priority}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="space-y-3 mt-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">{t("tasks.patient")}:</span>
                          <span className="font-medium text-slate-900 truncate max-w-[150px]">{task.patient_id.slice(0,8)}...</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">{t("tasks.role")}:</span>
                          <span className="font-medium text-slate-900 capitalize">{task.assigned_to_role ? t(`tasks.${task.assigned_to_role.replace('_', '')}Role`) : t("tasks.anyRole")}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">{t("tasks.created")}:</span>
                          <span className="text-slate-700">{new Date(task.created_at).toLocaleString()}</span>
                        </div>
                        {task.due_at && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-500">{t("tasks.due")}:</span>
                            <span className={`font-medium ${new Date(task.due_at) < new Date() ? 'text-red-600' : 'text-slate-700'}`}>
                              {new Date(task.due_at).toLocaleString()}
                            </span>
                          </div>
                        )}
                        {task.schedule_interval && (
                          <div className="flex justify-between text-sm bg-slate-50 p-2 rounded border border-slate-100">
                            <span className="text-slate-500">{t("tasks.recurring")}:</span>
                            <span className="font-medium text-blue-600">{t("tasks.everyXMins").replace("{x}", task.schedule_interval.toString())}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Action Footer */}
                    <div className="bg-slate-50 p-4 border-t border-[var(--border)] flex gap-3 justify-end items-center">
                      {task.status === "PENDING" && (
                        <button
                          onClick={() => handleAction(task.id, "assign", { assigned_to_user_id: currentUser?.id })}
                          disabled={actionLoading === task.id}
                          className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-sm font-semibold hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
                        >
                          <User className="w-4 h-4" />{t("tasks.pickUpTask")}</button>
                      )}
                      
                      {task.status === "ASSIGNED" && (
                        <button
                          onClick={() => handleAction(task.id, "start")}
                          disabled={actionLoading === task.id}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
                        >
                          <Play className="w-4 h-4 fill-current" />{t("tasks.startTask")}</button>
                      )}

                      {task.status === "IN_PROGRESS" && (
                        <button
                          onClick={() => { setSelectedTask(task); setShowCompleteModal(true); }}
                          className="px-5 py-2 bg-green-600 text-white rounded-lg text-sm font-semibold hover:bg-green-700 transition-colors shadow-sm flex items-center gap-2 w-full justify-center"
                        >
                          <Check className="w-4 h-4" />{t("tasks.completeTask")}</button>
                      )}
                      
                      {['COMPLETED', 'CANCELLED'].includes(task.status) && (
                        <div className="text-sm font-medium text-slate-500 w-full text-center">
                          {task.status === 'COMPLETED' ? t("tasks.completedByUser") : t("tasks.cancelledStatusMsg")}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Complete Task Modal */}
      {showCompleteModal && selectedTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="text-xl font-bold text-slate-900">{t("tasks.completeTask")}</h2>
              <button onClick={() => { setShowCompleteModal(false); setSelectedTask(null); }} className="p-2 hover:bg-slate-200 rounded-full transition-colors">
                <X size={20} className="text-slate-500" />
              </button>
            </div>
            
            <div className="p-6 space-y-5">
              <div className="bg-blue-50 text-blue-800 p-4 rounded-xl border border-blue-100 flex gap-4 items-start">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shrink-0 shadow-sm">
                  {(() => {
                    const TI = TASK_TYPES[selectedTask.task_type as keyof typeof TASK_TYPES]?.icon || FileText;
                    return <TI className="w-5 h-5 text-blue-600" />;
                  })()}
                </div>
                <div>
                  <h4 className="font-bold">{selectedTask.description}</h4>
                  <p className="text-sm text-blue-600 mt-1 opacity-80">{t("tasks.logYourExecutionDetailsBelow")}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">{t("tasks.executionNotesOptional")}</label>
                <textarea
                  value={completeNotes}
                  onChange={e => setCompleteNotes(e.target.value)}
                  placeholder={t("tasks.executionNotesPlaceholder")}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none h-32"
                />
              </div>
            </div>

            <div className="p-6 bg-slate-50 border-t border-[var(--border)] flex justify-end gap-3">
              <button onClick={() => { setShowCompleteModal(false); setSelectedTask(null); }} className="px-5 py-2.5 font-semibold text-slate-600 hover:bg-slate-200 rounded-xl transition-colors">{t("tasks.cancel")}</button>
              <button
                onClick={() => handleAction(selectedTask.id, "complete", { notes: completeNotes, action: "standard_completion", metadata_json: {} })}
                disabled={actionLoading === selectedTask.id}
                className="px-6 py-2.5 font-bold text-white bg-green-600 hover:bg-green-700 rounded-xl shadow-sm transition-all flex items-center gap-2 disabled:opacity-50"
              >
                {actionLoading === selectedTask.id ? <Loader2 size={18} className="animate-spin" /> : <Check size={18} />}
                {t("tasks.confirmCompletion")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
