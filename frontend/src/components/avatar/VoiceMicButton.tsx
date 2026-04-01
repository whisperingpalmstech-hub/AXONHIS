"use client";
import React from "react";
import { useTranslation } from "@/i18n";

export type MicState = "idle" | "listening" | "processing" | "speaking";

interface VoiceMicButtonProps {
  state: MicState;
  onPress: () => void;
  onRelease?: () => void;
  disabled?: boolean;
}

export function VoiceMicButton({ state, onPress, onRelease, disabled = false }: VoiceMicButtonProps) {
  const { t } = useTranslation();

  const stateConfig = {
    idle: {
      bg: "bg-gradient-to-br from-blue-500 to-blue-600",
      ring: "",
      label: t("Tap to speak"),
      icon: <MicIcon />,
    },
    listening: {
      bg: "bg-gradient-to-br from-red-500 to-rose-600",
      ring: "ring-animate",
      label: t("Listening..."),
      icon: <MicActiveIcon />,
    },
    processing: {
      bg: "bg-gradient-to-br from-amber-500 to-orange-600",
      ring: "",
      label: t("Processing..."),
      icon: <SpinnerIcon />,
    },
    speaking: {
      bg: "bg-gradient-to-br from-emerald-500 to-teal-600",
      ring: "speak-animate",
      label: t("Speaking..."),
      icon: <SpeakerIcon />,
    },
  };

  const config = stateConfig[state];

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onClick={onPress}
        disabled={disabled || state === "processing" || state === "speaking"}
        className={`
          relative w-[72px] h-[72px] rounded-full ${config.bg}
          shadow-2xl shadow-blue-500/30
          flex items-center justify-center
          transition-all duration-300 ease-out
          hover:scale-110 active:scale-95
          disabled:opacity-50 disabled:cursor-not-allowed
          ${config.ring}
        `}
        aria-label={config.label}
      >
        {/* Pulse rings for listening */}
        {state === "listening" && (
          <>
            <span className="absolute inset-0 rounded-full bg-red-500/30 animate-ping" />
            <span className="absolute -inset-2 rounded-full border-2 border-red-400/40 animate-pulse" />
            <span className="absolute -inset-4 rounded-full border border-red-400/20 animate-pulse" style={{ animationDelay: "300ms" }} />
          </>
        )}

        {/* Speaker wave animation */}
        {state === "speaking" && (
          <>
            <span className="absolute -inset-2 rounded-full border-2 border-emerald-400/40 animate-pulse" />
            <span className="absolute -inset-4 rounded-full border border-emerald-400/20 animate-pulse" style={{ animationDelay: "200ms" }} />
          </>
        )}

        <span className="relative z-10 text-white">{config.icon}</span>
      </button>

      <span className="text-xs font-medium text-white/60 uppercase tracking-wider">
        {config.label}
      </span>
    </div>
  );
}

function MicIcon() {
  return (
    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8" />
    </svg>
  );
}

function MicActiveIcon() {
  return (
    <svg className="w-7 h-7 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
      <path d="M19 10v2a7 7 0 01-14 0v-2h2v2a5 5 0 0010 0v-2h2zM11 19.93V23h2v-3.07A8.98 8.98 0 0020 12h-2a7 7 0 01-14 0H2a8.98 8.98 0 009 7.93z" />
    </svg>
  );
}

function SpinnerIcon() {
  return (
    <svg className="w-7 h-7 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );
}

function SpeakerIcon() {
  return (
    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072M18.364 5.636a9 9 0 010 12.728M11 5L6 9H2v6h4l5 4V5z" />
    </svg>
  );
}
