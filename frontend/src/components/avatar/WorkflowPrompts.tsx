"use client";
import React from "react";
import { useTranslation } from "@/i18n";

interface WorkflowPromptsProps {
  onSelect: (workflow: string, prompt: string) => void;
  disabled?: boolean;
}

export function WorkflowPrompts({ onSelect, disabled = false }: WorkflowPromptsProps) {
  const { t } = useTranslation();

  const WORKFLOW_ACTIONS = [
    { key: "patient_registration", label: t("Register"), icon: "📋", prompt: t("I want to register as a new patient") },
    { key: "appointment_booking", label: t("Appointment"), icon: "📅", prompt: t("I want to book an appointment") },
    { key: "opd_triage", label: t("Symptoms"), icon: "🩺", prompt: t("I want to describe my symptoms before my visit") },
    { key: "billing_assistant", label: t("Billing"), icon: "💰", prompt: t("I want to check my bill") },
    { key: "lab_booking", label: t("Lab Test"), icon: "🧪", prompt: t("I want to schedule a lab test") },
    { key: "discharge_education", label: t("Discharge"), icon: "📄", prompt: t("I need my discharge instructions") },
    { key: "hospital_navigation", label: t("Directions"), icon: "🗺️", prompt: t("I need directions to a department") },
  ];

  return (
    <div className="workflow-prompts-glass">
      <div className="flex flex-wrap justify-center gap-2">
        {WORKFLOW_ACTIONS.map((action) => (
          <button
            key={action.key}
            onClick={() => onSelect(action.key, action.prompt)}
            disabled={disabled}
            className="
              group flex items-center gap-1.5 px-3 py-2 rounded-xl
              bg-white/10 hover:bg-white/20 backdrop-blur-sm
              border border-white/10 hover:border-white/30
              transition-all duration-200 ease-out
              hover:scale-105 active:scale-95
              disabled:opacity-40 disabled:cursor-not-allowed
            "
          >
            <span className="text-base group-hover:scale-110 transition-transform">{action.icon}</span>
            <span className="text-xs font-medium text-white/80 group-hover:text-white whitespace-nowrap">
              {action.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
