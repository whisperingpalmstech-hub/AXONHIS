/**
 * AXONHIS Virtual Avatar API Client.
 *
 * Covers: Sessions, Speech, Conversation, Workflows, Admin
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
const PREFIX = "/api/v1/avatar";

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return { ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${PREFIX}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...opts.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

// ── Types ───────────────────────────────────────────────────────────────────

export interface AvatarSession {
  id: string;
  user_id: string;
  language: string;
  status: string;
  patient_id: string | null;
  current_workflow: string | null;
  workflow_step: number;
  created_at: string;
  updated_at: string;
}

export interface AvatarMessage {
  id: string;
  session_id: string;
  role: string;
  content: string;
  intent: string | null;
  workflow: string | null;
  entities: string | null;
  created_at: string;
}

export interface ConverseResponse {
  transcription: string;
  response_text: string;
  audio_base64: string | null;
  intent: string | null;
  workflow: string | null;
  workflow_status: Record<string, any> | null;
  entities: Record<string, any> | null;
}

export interface ChatResponse {
  response_text: string;
  audio_base64: string | null;
  intent: string | null;
  workflow: string | null;
  workflow_status: Record<string, any> | null;
  entities: Record<string, any> | null;
}

export interface STTResponse {
  transcription: string;
  language: string;
  confidence: number;
}

export interface TTSResponse {
  audio_base64: string;
  language: string;
}

export interface WorkflowConfig {
  id: string;
  workflow_key: string;
  display_name: string;
  description: string | null;
  is_enabled: boolean;
  icon: string | null;
  system_prompt_override: string | null;
  supported_languages: string | null;
  display_order: number;
}

export interface AvatarAnalytics {
  total_sessions: number;
  active_sessions: number;
  total_messages: number;
  avg_messages_per_session: number;
  top_workflows: { workflow: string; count: number }[];
  language_distribution: { language: string; count: number }[];
  daily_sessions: { date: string; count: number }[];
}

export interface ConversationLog {
  session_id: string;
  language: string;
  status: string;
  workflow: string | null;
  created_at: string;
  message_count: number;
}

// ── API ─────────────────────────────────────────────────────────────────────

export const avatarApi = {
  // Session Management
  createSession: (language = "en") =>
    req<AvatarSession>("/sessions", { method: "POST", body: JSON.stringify({ language }) }),

  endSession: (sessionId: string) =>
    req<void>(`/sessions/${sessionId}`, { method: "DELETE" }),

  // Full Conversation Pipeline (STT → LLM → Workflow → TTS)
  converse: (sessionId: string, audioBase64: string) =>
    req<ConverseResponse>(`/sessions/${sessionId}/converse`, {
      method: "POST",
      body: JSON.stringify({ audio_base64: audioBase64 }),
    }),

  // Text-only Chat
  chatText: (sessionId: string, text: string) =>
    req<ChatResponse>(`/sessions/${sessionId}/chat`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  // Standalone Speech Services
  speechToText: (sessionId: string, audioBase64: string) =>
    req<STTResponse>(`/sessions/${sessionId}/speech-to-text`, {
      method: "POST",
      body: JSON.stringify({ audio_base64: audioBase64 }),
    }),

  textToSpeech: (sessionId: string, text: string, language = "en") =>
    req<TTSResponse>(`/sessions/${sessionId}/text-to-speech`, {
      method: "POST",
      body: JSON.stringify({ text, language }),
    }),

  // Message History
  getMessages: (sessionId: string) =>
    req<AvatarMessage[]>(`/sessions/${sessionId}/messages`),

  // Admin Endpoints
  getWorkflowConfigs: () =>
    req<WorkflowConfig[]>("/admin/workflows"),

  updateWorkflowConfig: (configId: string, data: Partial<WorkflowConfig>) =>
    req<WorkflowConfig>(`/admin/workflows/${configId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getAnalytics: () =>
    req<AvatarAnalytics>("/admin/analytics"),

  getConversationLogs: (limit = 50, offset = 0) =>
    req<ConversationLog[]>(`/admin/logs?limit=${limit}&offset=${offset}`),
};
