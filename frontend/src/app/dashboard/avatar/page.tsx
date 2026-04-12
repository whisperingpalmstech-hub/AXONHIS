"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useTranslation } from "@/i18n";
import { avatarApi, type AvatarMessage as ApiMessage, type ChatResponse } from "@/lib/avatar-api";
import { AvatarVideo } from "@/components/avatar/AvatarVideo";
import { ChatPanel } from "@/components/avatar/ChatPanel";
import { VoiceMicButton, type MicState } from "@/components/avatar/VoiceMicButton";
import { WorkflowStatus } from "@/components/avatar/WorkflowStatus";
import { WorkflowPrompts } from "@/components/avatar/WorkflowPrompts";
import { AvatarLanguageSelector } from "@/components/avatar/AvatarLanguageSelector";
import Link from "next/link";

interface LocalMessage {
  id: string;
  role: string;
  content: string;
  created_at: string;
  intent?: string | null;
  workflow?: string | null;
}

export default function AvatarKioskPage() {
  const { locale, setLocale, t } = useTranslation();

  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [micState, setMicState] = useState<MicState>("idle");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentWorkflow, setCurrentWorkflow] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [textInput, setTextInput] = useState("");
  const [showChat, setShowChat] = useState(true);
  const [language, setLanguage] = useState(locale || "en");

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // ── Initialize Session ──────────────────────────────────────────────────
  useEffect(() => {
    let currentSessionId = sessionId;

    const initSession = async () => {
      try {
        const session = await avatarApi.createSession(language);
        setSessionId(session.id);
        currentSessionId = session.id;

        // Clear previous data for the new language session
        setMessages([]);
        setCurrentWorkflow(null);
        setWorkflowStatus(null);
        setError(null);

        // Load messages (including the greeting in the new language)
        const msgs = await avatarApi.getMessages(session.id);
        setMessages(msgs.map(m => ({
          id: m.id,
          role: m.role,
          content: m.content,
          created_at: m.created_at,
          intent: m.intent,
          workflow: m.workflow,
        })));

        // Play greeting TTS
        if (msgs.length > 0) {
          try {
            const tts = await avatarApi.textToSpeech(session.id, msgs[0].content, language);
            if (tts.audio_base64) {
              playAudio(tts.audio_base64);
            }
          } catch {
            // Silently fail TTS
          }
        }
      } catch (err: any) {
        setError(err.message || "Failed to start avatar session");
      }
    };

    initSession();

    // Cleanup when language changes or unmounts
    return () => {
      if (currentSessionId) {
        avatarApi.endSession(currentSessionId).catch(() => {});
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  // ── Audio Playback ──────────────────────────────────────────────────────
  const playAudio = useCallback((base64Audio: string) => {
    try {
      const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
      audioPlayerRef.current = audio;
      setIsSpeaking(true);
      setMicState("speaking");
      audio.play();
      audio.onended = () => {
        setIsSpeaking(false);
        setMicState("idle");
      };
      audio.onerror = () => {
        setIsSpeaking(false);
        setMicState("idle");
      };
    } catch {
      setIsSpeaking(false);
      setMicState("idle");
    }
  }, []);

  // ── Voice Recording ─────────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });

        // Convert to base64
        const reader = new FileReader();
        reader.onloadend = async () => {
          const base64 = (reader.result as string).split(",")[1];
          await processAudioInput(base64);
        };
        reader.readAsDataURL(blob);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setMicState("listening");
      setError(null);
    } catch (err: any) {
      setError("Microphone access denied. Please allow microphone permissions.");
      setMicState("idle");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setMicState("processing");
    }
  }, []);

  const handleMicPress = useCallback(() => {
    if (micState === "idle") {
      startRecording();
    } else if (micState === "listening") {
      stopRecording();
    }
  }, [micState, startRecording, stopRecording]);

  // ── Process Audio → Backend Pipeline ────────────────────────────────────
  const processAudioInput = async (audioBase64: string) => {
    if (!sessionId) return;

    setMicState("processing");
    try {
      const response = await avatarApi.converse(sessionId, audioBase64);

      // Add user message
      if (response.transcription) {
        setMessages(prev => [
          ...prev,
          {
            id: `user-${Date.now()}`,
            role: "user",
            content: response.transcription,
            created_at: new Date().toISOString(),
          },
        ]);
      }

      // Add assistant response
      setMessages(prev => [
        ...prev,
        {
          id: `asst-${Date.now()}`,
          role: "assistant",
          content: response.response_text,
          created_at: new Date().toISOString(),
          intent: response.intent,
          workflow: response.workflow,
        },
      ]);

      // Update workflow state
      if (response.workflow) setCurrentWorkflow(response.workflow);
      if (response.workflow_status) setWorkflowStatus(response.workflow_status);

      // Play TTS response
      if (response.audio_base64) {
        playAudio(response.audio_base64);
      } else {
        setMicState("idle");
      }
    } catch (err: any) {
      setError(err.message || "Communication error");
      setMicState("idle");
    }
  };

  // ── Text Chat Submission ────────────────────────────────────────────────
  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId || !textInput.trim()) return;

    const userText = textInput.trim();
    setTextInput("");

    // Optimistically add user message
    setMessages(prev => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: userText,
        created_at: new Date().toISOString(),
      },
    ]);

    setMicState("processing");
    try {
      const response = await avatarApi.chatText(sessionId, userText);

      setMessages(prev => [
        ...prev,
        {
          id: `asst-${Date.now()}`,
          role: "assistant",
          content: response.response_text,
          created_at: new Date().toISOString(),
          intent: response.intent,
          workflow: response.workflow,
        },
      ]);

      if (response.workflow) setCurrentWorkflow(response.workflow);
      if (response.workflow_status) setWorkflowStatus(response.workflow_status);

      if (response.audio_base64) {
        playAudio(response.audio_base64);
      } else {
        setMicState("idle");
      }
    } catch (err: any) {
      setError(err.message || "Chat error");
      setMicState("idle");
    }
  };

  // ── Workflow Quick Action ───────────────────────────────────────────────
  const handleWorkflowSelect = async (_key: string, prompt: string) => {
    if (!sessionId) return;

    setMessages(prev => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: prompt,
        created_at: new Date().toISOString(),
      },
    ]);

    setMicState("processing");
    try {
      const response = await avatarApi.chatText(sessionId, prompt);

      setMessages(prev => [
        ...prev,
        {
          id: `asst-${Date.now()}`,
          role: "assistant",
          content: response.response_text,
          created_at: new Date().toISOString(),
          intent: response.intent,
          workflow: response.workflow,
        },
      ]);

      if (response.workflow) setCurrentWorkflow(response.workflow);
      if (response.workflow_status) setWorkflowStatus(response.workflow_status);

      if (response.audio_base64) {
        playAudio(response.audio_base64);
      } else {
        setMicState("idle");
      }
    } catch (err: any) {
      setError(err.message);
      setMicState("idle");
    }
  };

  // ── Language Change ─────────────────────────────────────────────────────
  const handleLanguageChange = (code: string) => {
    setLanguage(code);
    setLocale(code);
    // Note: useEffect[language] will automatically recreate a fresh translated session.
  };

  return (
    <div className="avatar-kiosk" id="avatar-kiosk-page">
      {/* ── Full-screen Avatar Video ──────────────────────────── */}
      <AvatarVideo isSpeaking={isSpeaking} className="absolute inset-0 w-full h-full" />

      {/* ── Dark overlay ──────────────────────────────────────── */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-black/40 pointer-events-none z-[1]" />

      {/* ── Top Bar ───────────────────────────────────────────── */}
      <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-6 py-4">
        {/* Branding */}
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30 group-hover:scale-110 transition-transform">
            <span className="text-white text-sm font-bold">A</span>
          </div>
          <div>
            <span className="text-white font-bold text-sm">AXON</span>
            <span className="text-blue-400 font-bold text-sm">HIS</span>
            <p className="text-white/40 text-[9px] font-medium uppercase tracking-widest">{t("Virtual Avatar")}</p>
          </div>
        </Link>

        {/* Right Controls */}
        <div className="flex items-center gap-3">
          <AvatarLanguageSelector
            currentLanguage={language}
            onLanguageChange={handleLanguageChange}
          />

          <button
            onClick={() => setShowChat(!showChat)}
            className="p-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 transition-all"
            title="Toggle Chat"
          >
            <svg className="w-5 h-5 text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
          </button>

          <Link
            href="/dashboard"
            className="p-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 transition-all"
            title="Back to Dashboard"
          >
            <svg className="w-5 h-5 text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Link>
        </div>
      </div>

      {/* ── Chat Panel (left side) ────────────────────────────── */}
      {showChat && (
        <div className="absolute left-4 top-20 bottom-48 w-[380px] z-10">
          <ChatPanel messages={messages} isProcessing={micState === "processing"} />
        </div>
      )}

      {/* ── Workflow Status (right side) ──────────────────────── */}
      <div className="absolute right-4 top-20 z-10 w-[300px]">
        <WorkflowStatus workflow={currentWorkflow} status={workflowStatus} />
      </div>

      {/* ── Error Toast ───────────────────────────────────────── */}
      {error && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-30">
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/90 backdrop-blur-md text-white text-sm font-medium shadow-xl">
            <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-2 hover:text-white/80">✕</button>
          </div>
        </div>
      )}

      {/* ── Bottom Control Bar ─────────────────────────────────── */}
      <div className="absolute bottom-0 left-0 right-0 z-20">
        {/* Workflow Quick Actions */}
        <div className="px-6 pb-4">
          <WorkflowPrompts
            onSelect={handleWorkflowSelect}
            disabled={micState === "processing" || micState === "speaking"}
          />
        </div>

        {/* Mic + Text Input Bar */}
        <div className="bg-gradient-to-t from-black/90 via-black/70 to-transparent pt-6 pb-8 px-6">
          <div className="flex items-end justify-center gap-6 max-w-3xl mx-auto">
            {/* Text input */}
            <form onSubmit={handleTextSubmit} className="flex-1 max-w-xl">
              <div className="relative">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder={micState === "speaking" ? t("Avatar is speaking...") : t("Type your message...")}
                  disabled={micState === "processing" || micState === "speaking"}
                  className="
                    w-full px-5 py-3.5 pr-14 rounded-2xl
                    bg-white/10 backdrop-blur-md
                    border border-white/15 focus:border-blue-400/50
                    text-white placeholder-white/40 text-sm
                    focus:outline-none focus:ring-2 focus:ring-blue-500/30
                    transition-all duration-200
                    disabled:opacity-50
                  "
                />
                <button
                  type="submit"
                  disabled={!textInput.trim() || micState === "processing" || micState === "speaking"}
                  className="
                    absolute right-2 top-1/2 -translate-y-1/2
                    w-9 h-9 rounded-xl
                    bg-blue-500 hover:bg-blue-600
                    flex items-center justify-center
                    transition-all disabled:opacity-30
                  "
                >
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                  </svg>
                </button>
              </div>
            </form>

            {/* Mic Button */}
            <VoiceMicButton
              state={micState}
              onPress={handleMicPress}
              disabled={!sessionId}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
