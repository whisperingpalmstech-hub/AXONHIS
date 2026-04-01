"use client";
import React, { useRef, useEffect } from "react";
import { useTranslation } from "@/i18n";

interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
  intent?: string | null;
  workflow?: string | null;
}

interface ChatPanelProps {
  messages: Message[];
  isProcessing?: boolean;
}

export function ChatPanel({ messages, isProcessing = false }: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-panel-glass">
      <div className="chat-panel-header">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold text-white/80 uppercase tracking-wider">
            {t("Live Conversation")}
          </span>
        </div>
        <span className="text-[10px] text-white/40">
          {t("{count} messages", { count: messages.length })}
        </span>
      </div>

      <div className="chat-panel-messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message ${msg.role === "user" ? "chat-message-user" : "chat-message-assistant"}`}
          >
            <div className="flex items-start gap-2">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                  msg.role === "user"
                    ? "bg-blue-500/80 text-white"
                    : "bg-emerald-500/80 text-white"
                }`}
              >
                {msg.role === "user" ? "U" : "A"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] leading-relaxed text-white/90 break-words">
                  {msg.content}
                </p>
                {msg.workflow && (
                  <span className="inline-block mt-1.5 px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-[10px] font-medium">
                    {msg.workflow.replace(/_/g, " ")}
                  </span>
                )}
                <span className="block mt-1 text-[10px] text-white/30">
                  {new Date(msg.created_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="chat-message chat-message-assistant">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-emerald-500/80 flex items-center justify-center">
                <div className="w-3 h-3 border-2 border-white/60 border-t-transparent rounded-full animate-spin" />
              </div>
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
