"use client";
import React from "react";

interface WorkflowStep {
  label: string;
  status: "done" | "active" | "pending";
  onClick?: () => void;
}

interface WorkflowPipelineProps {
  steps: WorkflowStep[];
  title?: string;
  colorScheme?: "blue" | "emerald" | "violet" | "cyan" | "amber";
}

const COLORS = {
  blue: { bg: "from-blue-50 to-indigo-50", border: "border-blue-100", title: "text-blue-800", done: "bg-blue-500 border-blue-500", active: "bg-blue-500 border-blue-500 shadow-lg shadow-blue-500/30", line: "bg-blue-300" },
  emerald: { bg: "from-emerald-50 to-teal-50", border: "border-emerald-100", title: "text-emerald-800", done: "bg-emerald-500 border-emerald-500", active: "bg-emerald-500 border-emerald-500 shadow-lg shadow-emerald-500/30", line: "bg-emerald-300" },
  violet: { bg: "from-violet-50 to-purple-50", border: "border-violet-100", title: "text-violet-800", done: "bg-violet-500 border-violet-500", active: "bg-violet-500 border-violet-500 shadow-lg shadow-violet-500/30", line: "bg-violet-300" },
  cyan: { bg: "from-cyan-50 to-blue-50", border: "border-cyan-100", title: "text-cyan-800", done: "bg-cyan-500 border-cyan-500", active: "bg-cyan-500 border-cyan-500 shadow-lg shadow-cyan-500/30", line: "bg-cyan-300" },
  amber: { bg: "from-amber-50 to-orange-50", border: "border-amber-100", title: "text-amber-800", done: "bg-amber-500 border-amber-500", active: "bg-amber-500 border-amber-500 shadow-lg shadow-amber-500/30", line: "bg-amber-300" },
};

export function WorkflowPipeline({ steps, title, colorScheme = "blue" }: WorkflowPipelineProps) {
  const c = COLORS[colorScheme];

  return (
    <div className={`p-4 bg-gradient-to-r ${c.bg} rounded-xl border ${c.border}`}>
      {title && (
        <p className={`text-xs font-bold ${c.title} mb-3 uppercase tracking-wider`}>{title}</p>
      )}
      <div className="flex items-center gap-1 overflow-x-auto pb-2">
        {steps.map((step, i) => (
          <React.Fragment key={step.label}>
            <div
              className={`flex flex-col items-center min-w-[80px] ${step.onClick ? "cursor-pointer" : ""}`}
              onClick={step.onClick}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all duration-300 ${
                  step.status === "done"
                    ? `${c.done} text-white`
                    : step.status === "active"
                    ? `${c.active} text-white animate-pulse`
                    : "bg-white border-slate-300 text-slate-400"
                }`}
              >
                {step.status === "done" ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <p className={`text-[10px] mt-1 font-medium text-center ${
                step.status === "pending" ? "text-slate-400" : "text-slate-600"
              }`}>
                {step.label}
              </p>
            </div>
            {i < steps.length - 1 && (
              <div
                className={`h-0.5 flex-1 mx-1 transition-colors ${
                  step.status !== "pending" ? c.line : "bg-slate-200"
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
