/**
 * Enterprise Patient Registration API Client.
 *
 * Covers all 10 OPD FRD features:
 *  1. AI-Assisted Registration
 *  2. Voice-Enabled Registration
 *  3. ID Scan (OCR)
 *  4. Face Recognition Check-in
 *  5. AI Duplicate Detection
 *  6. Address Auto-Population
 *  7. UHID Generation
 *  8. Health Card Generation
 *  9. Document Upload
 * 10. Notification Engine
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
const PREFIX = "/api/v1/registration";

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function jsonRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${PREFIX}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

async function formRequest<T>(path: string, formData: FormData): Promise<T> {
  const url = `${API_BASE}${PREFIX}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface AIRegistrationSession {
  id: string;
  status: string;
  current_step: number;
  total_steps: number;
  collected_data: Record<string, string>;
  ai_suggestions: Record<string, any>;
  next_question: string | null;
  registration_method: string;
  patient_id: string | null;
  created_at: string;
}

export interface VoiceRegistrationResult {
  intent: string;
  confidence: number;
  translated_text: string | null;
  parsed_data: Record<string, any>;
  action_taken: string | null;
  patient_id: string | null;
}

export interface IDScanResult {
  id: string;
  document_type: string;
  extracted_name: string | null;
  extracted_dob: string | null;
  extracted_gender: string | null;
  extracted_id_number: string | null;
  extraction_confidence: number;
  is_verified: boolean;
  created_at: string;
}

export interface FaceCheckInResult {
  matched: boolean;
  patient_id: string | null;
  patient_name: string | null;
  uhid: string | null;
  confidence: number;
  message: string;
}

export interface DuplicateMatch {
  patient_id: string;
  patient_uuid: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  primary_phone: string | null;
  confidence_score: number;
  match_reasons: string[];
}

export interface DuplicateCheckResult {
  has_duplicates: boolean;
  matches: DuplicateMatch[];
  ai_recommendation: string;
}

export interface AddressLookupResult {
  pincode: string;
  area: string | null;
  city: string | null;
  state: string | null;
  country: string;
  source: string;
}

export interface HealthCardResult {
  id: string;
  patient_id: string;
  uhid: string;
  card_number: string;
  qr_code_data: string;
  issue_date: string;
  is_active: boolean;
}

export interface PatientDocumentResult {
  id: string;
  patient_id: string;
  category: string;
  file_name: string;
  original_name: string;
  file_type: string;
  file_size: number;
  description: string | null;
  created_at: string;
}

export interface NotificationResult {
  notifications_sent: number;
  details: Array<{
    id: string;
    channel: string;
    recipient: string;
    status: string;
    sent_at: string | null;
  }>;
}

// ─────────────────────────────────────────────────────────────────────────────
// API Functions
// ─────────────────────────────────────────────────────────────────────────────

export const registrationApi = {
  // Feature 1: AI-Assisted Registration
  aiStart: (language = "en") =>
    jsonRequest<AIRegistrationSession>("/ai/start", {
      method: "POST",
      body: JSON.stringify({ language }),
    }),

  aiStep: (session_id: string, field_name: string, field_value: string) =>
    jsonRequest<AIRegistrationSession>("/ai/step", {
      method: "POST",
      body: JSON.stringify({ session_id, field_name, field_value }),
    }),

  aiComplete: (session_id: string) =>
    jsonRequest<AIRegistrationSession>("/ai/complete", {
      method: "POST",
      body: JSON.stringify({ session_id }),
    }),

  // Feature 2: Voice-Enabled Registration
  voiceCommand: (transcript: string, language = "en") =>
    jsonRequest<VoiceRegistrationResult>("/voice/command", {
      method: "POST",
      body: JSON.stringify({ transcript, language }),
    }),

  // Feature 3: ID Scan (OCR)
  idScanExtract: (file: File, documentType: string, sessionId?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("document_type", documentType);
    if (sessionId) fd.append("session_id", sessionId);
    return formRequest<IDScanResult>("/id-scan/extract", fd);
  },

  idScanVerify: (scanId: string) =>
    jsonRequest<IDScanResult>(`/id-scan/${scanId}/verify`, { method: "POST" }),

  // Feature 4: Face Recognition
  faceEnroll: (patientId: string, photo: File) => {
    const fd = new FormData();
    fd.append("patient_id", patientId);
    fd.append("photo", photo);
    return formRequest<any>("/face/enroll", fd);
  },

  faceCheckIn: (photo: File) => {
    const fd = new FormData();
    fd.append("photo", photo);
    return formRequest<FaceCheckInResult>("/face/check-in", fd);
  },

  // Feature 5: AI Duplicate Detection
  checkDuplicates: (data: {
    first_name: string;
    last_name: string;
    date_of_birth: string;
    mobile?: string;
    email?: string;
    address?: string;
  }) =>
    jsonRequest<DuplicateCheckResult>("/duplicates/check", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Feature 6: Address Auto-Population
  addressLookup: (pincode: string) =>
    jsonRequest<AddressLookupResult>(`/address/lookup?pincode=${pincode}`),

  // Feature 7: UHID Generation
  generateUHID: (patientId: string) =>
    jsonRequest<{ patient_id: string; uhid: string; generated_at: string }>(
      `/uhid/generate?patient_id=${patientId}`,
      { method: "POST" }
    ),

  // Feature 8: Health Card
  generateHealthCard: (patientId: string) =>
    jsonRequest<HealthCardResult>(
      `/health-card/generate?patient_id=${patientId}`,
      { method: "POST" }
    ),

  getHealthCard: (patientId: string) =>
    jsonRequest<HealthCardResult>(`/health-card/${patientId}`),

  // Feature 9: Document Upload
  uploadDocument: (patientId: string, category: string, file: File, description?: string) => {
    const fd = new FormData();
    fd.append("patient_id", patientId);
    fd.append("category", category);
    fd.append("file", file);
    if (description) fd.append("description", description);
    return formRequest<PatientDocumentResult>("/documents/upload", fd);
  },

  listDocuments: (patientId: string, category?: string) => {
    let path = `/documents/${patientId}`;
    if (category) path += `?category=${category}`;
    return jsonRequest<PatientDocumentResult[]>(path);
  },

  // Feature 10: Notification Engine
  sendNotifications: (patientId: string, channels: string[] = ["sms", "email"]) =>
    jsonRequest<NotificationResult>(
      `/notifications/send?patient_id=${patientId}&channels=${channels.join(",")}`,
      { method: "POST" }
    ),

  getNotificationLog: (patientId: string) =>
    jsonRequest<any[]>(`/notifications/${patientId}`),
};
