"use client";
import React from "react";

interface WorkflowStatusProps {
  workflow: string | null;
  status: Record<string, any> | null;
}

const WORKFLOW_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  patient_registration: { label: "Patient Registration", icon: "📋", color: "from-blue-500/20 to-blue-600/10" },
  appointment_booking: { label: "Appointment Booking", icon: "📅", color: "from-violet-500/20 to-violet-600/10" },
  opd_triage: { label: "OPD Pre-Triage", icon: "🩺", color: "from-emerald-500/20 to-emerald-600/10" },
  billing_assistant: { label: "Billing Assistant", icon: "💰", color: "from-amber-500/20 to-amber-600/10" },
  lab_booking: { label: "Lab Booking", icon: "🧪", color: "from-cyan-500/20 to-cyan-600/10" },
  discharge_education: { label: "Discharge Education", icon: "📄", color: "from-rose-500/20 to-rose-600/10" },
  hospital_navigation: { label: "Hospital Navigation", icon: "🗺️", color: "from-indigo-500/20 to-indigo-600/10" },
};

export function WorkflowStatus({ workflow, status }: WorkflowStatusProps) {
  if (!workflow) return null;

  const config = WORKFLOW_LABELS[workflow] || {
    label: workflow.replace(/_/g, " "),
    icon: "⚙️",
    color: "from-slate-500/20 to-slate-600/10",
  };

  const statusText = status?.status || "active";
  const statusColor =
    statusText === "completed" ? "text-emerald-400" :
    statusText === "error" ? "text-red-400" :
    statusText === "collecting" ? "text-amber-400" :
    "text-blue-400";

  return (
    <div className={`workflow-status-glass bg-gradient-to-r ${config.color}`}>
      <div className="flex items-center gap-3">
        <span className="text-xl">{config.icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold text-white/90 truncate">{config.label}</p>
          <p className={`text-[10px] font-medium uppercase tracking-wider ${statusColor}`}>
            {statusText === "collecting" ? "⏳ In Progress" :
             statusText === "completed" ? "✅ Completed" :
             statusText === "error" ? "❌ Error" :
             statusText === "slots_available" ? "📋 Slots Found" :
             statusText === "duplicate_found" ? "⚠️ Duplicate Found" :
             `● ${statusText}`}
          </p>
        </div>
      </div>

      {/* Display collected fields if available */}
      {status?.collected && Object.keys(status.collected).length > 0 && (
        <div className="mt-2 pt-2 border-t border-white/10">
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(status.collected).map(([key, val]) => (
              <span key={key} className="px-2 py-0.5 rounded-full bg-white/10 text-[10px] text-white/70">
                {key}: <span className="text-white/90">{String(val)}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Missing fields indicator */}
      {status?.missing_fields && status.missing_fields.length > 0 && (
        <div className="mt-2 pt-2 border-t border-white/10">
          <p className="text-[10px] text-amber-400/80">
            Still needed: {status.missing_fields.join(", ")}
          </p>
        </div>
      )}
    </div>
  );
}
