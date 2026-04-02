/**
 * AXONHIS Complete OPD Module — API Client
 * Covers all unified OPD endpoints: pre-registration, deposits, consents, 
 * pro-forma billing, kiosk, waitlist, AI scheduling, analytics, journey.
 */
import { api } from "./api";

// ═══ Types ═══════════════════════════════════════════════════════════════════

export interface PreRegistration {
  id: string; pre_reg_id: string;
  first_name: string; last_name: string;
  gender?: string; date_of_birth?: string;
  mobile_number: string; email?: string;
  status: string; converted_patient_id?: string;
  converted_uhid?: string; duplicate_score?: number;
  potential_duplicate_id?: string;
  payer_category?: string; preferred_department?: string;
  created_at: string;
}

export interface Deposit {
  id: string; deposit_number: string;
  patient_id: string; visit_id?: string;
  deposit_amount: number; consumed_amount: number;
  balance_amount: number; refunded_amount: number;
  payment_mode: string; transaction_reference?: string;
  status: string; collected_at: string; created_at: string;
}

export interface ConsentTemplate {
  id: string; template_name: string;
  template_category: string; template_body: string;
  language: string; version: number;
  is_active: boolean; created_at: string;
}

export interface ConsentDocument {
  id: string; consent_number: string;
  patient_id: string; visit_id?: string;
  template_id?: string; consent_title: string;
  consent_body: string; status: string;
  signature_data?: string; signed_by_name?: string;
  signed_at?: string; witness_name?: string;
  pdf_url?: string; emailed_to?: string;
  scanned_document_url?: string; created_at: string;
}

export interface ProFormaBill {
  id: string; proforma_number: string;
  patient_id: string; items: any[];
  subtotal: number; tax_amount: number;
  discount_amount: number; estimated_total: number;
  valid_until?: string; notes?: string;
  converted_to_bill_id?: string; generated_at: string;
}

export interface KioskCheckin {
  id: string; kiosk_id?: string;
  verification_method: string; patient_id?: string;
  visit_id?: string; status: string;
  token_number?: string; started_at: string;
  completed_at?: string; error_message?: string;
}

export interface WaitlistEntry {
  id: string; patient_id: string;
  doctor_id: string; department: string;
  preferred_date: string; status: string;
  offered_slot_id?: string; created_at: string;
}

export interface AISchedulingPrediction {
  id: string; booking_id?: string;
  patient_id: string; doctor_id: string;
  appointment_date: string; no_show_probability: number;
  prediction_factors: any[]; recommendation?: string;
  recommendation_applied: boolean; predicted_at: string;
}

export interface OPDAnalytics {
  analytics_date: string;
  total_appointments: number; total_walkins: number;
  total_checkins: number; total_visits: number;
  completed_visits: number; cancelled_visits: number;
  no_show_count: number; avg_wait_time_min?: number;
  max_wait_time_min?: number;
  avg_consultation_duration_min?: number;
  doctor_utilization: Record<string, any>;
  total_revenue: number; consultation_revenue: number;
  diagnostic_revenue: number; pharmacy_revenue: number;
  total_deposits: number; total_refunds: number;
  department_breakdown: Record<string, any>;
  peak_hour?: string;
  hourly_distribution: Record<string, number>;
}

export interface PatientJourneyStep {
  step_name: string;
  status: string; // pending, in_progress, completed, skipped
  timestamp?: string;
  details?: Record<string, any>;
}

export interface PatientJourney {
  patient_id: string; visit_id: string;
  visit_number: string; patient_name: string;
  uhid?: string; steps: PatientJourneyStep[];
  current_step: string; overall_status: string;
}

// ═══ API Methods ═════════════════════════════════════════════════════════════

export const opdApi = {
  // ── Pre-Registration ──
  createPreRegistration: (data: any) => api.post<PreRegistration>("/opd/pre-registration", data),
  listPreRegistrations: (status?: string) => {
    const qs = status ? `?status=${status}` : "";
    return api.get<PreRegistration[]>(`/opd/pre-registration${qs}`);
  },
  getPreRegistration: (id: string) => api.get<PreRegistration>(`/opd/pre-registration/${id}`),
  convertToPatient: (id: string, data: any) => api.post<PreRegistration>(`/opd/pre-registration/${id}/convert`, data),

  // ── Deposits ──
  createDeposit: (data: any) => api.post<Deposit>("/opd/deposits", data),
  listDeposits: (patientId?: string, status?: string) => {
    const params = new URLSearchParams();
    if (patientId) params.set("patient_id", patientId);
    if (status) params.set("status", status);
    const qs = params.toString() ? `?${params}` : "";
    return api.get<Deposit[]>(`/opd/deposits${qs}`);
  },
  consumeDeposit: (id: string, data: any) => api.post<Deposit>(`/opd/deposits/${id}/consume`, data),
  refundDeposit: (id: string, data: any) => api.post<Deposit>(`/opd/deposits/${id}/refund`, data),

  // ── Consent Templates ──
  createConsentTemplate: (data: any) => api.post<ConsentTemplate>("/opd/consent-templates", data),
  listConsentTemplates: (category?: string) => {
    const qs = category ? `?category=${category}` : "";
    return api.get<ConsentTemplate[]>(`/opd/consent-templates${qs}`);
  },

  // ── Consent Documents ──
  createConsentDocument: (data: any) => api.post<ConsentDocument>("/opd/consent-documents", data),
  listConsentDocuments: (patientId?: string, visitId?: string) => {
    const params = new URLSearchParams();
    if (patientId) params.set("patient_id", patientId);
    if (visitId) params.set("visit_id", visitId);
    const qs = params.toString() ? `?${params}` : "";
    return api.get<ConsentDocument[]>(`/opd/consent-documents${qs}`);
  },
  signConsentDocument: (id: string, data: any) => api.post<ConsentDocument>(`/opd/consent-documents/${id}/sign`, data),
  emailConsentDocument: (id: string, data: any) => api.post<ConsentDocument>(`/opd/consent-documents/${id}/email`, data),
  uploadScannedConsent: (id: string, data: any) => api.post<ConsentDocument>(`/opd/consent-documents/${id}/upload-scan`, data),

  // ── Pro-Forma Billing ──
  createProFormaBill: (data: any) => api.post<ProFormaBill>("/opd/proforma-bills", data),
  listProFormaBills: (patientId?: string) => {
    const qs = patientId ? `?patient_id=${patientId}` : "";
    return api.get<ProFormaBill[]>(`/opd/proforma-bills${qs}`);
  },

  // ── Kiosk Check-in ──
  kioskCheckin: (data: any) => api.post<KioskCheckin>("/opd/kiosk-checkin", data),

  // ── Waitlist ──
  addToWaitlist: (data: any) => api.post<WaitlistEntry>("/opd/waitlist", data),
  listWaitlist: (doctorId?: string, status?: string) => {
    const params = new URLSearchParams();
    if (doctorId) params.set("doctor_id", doctorId);
    if (status) params.set("status", status);
    const qs = params.toString() ? `?${params}` : "";
    return api.get<WaitlistEntry[]>(`/opd/waitlist${qs}`);
  },

  // ── AI Scheduling ──
  predictNoShow: (patientId: string, doctorId: string, appointmentDate: string) =>
    api.post<AISchedulingPrediction>(`/opd/ai-scheduling/predict?patient_id=${patientId}&doctor_id=${doctorId}&appointment_date=${appointmentDate}`),

  // ── Bill Cancellation ──
  cancelBill: (billId: string, data: any) => api.post<any>(`/opd/bills/${billId}/cancel`, data),

  // ── Analytics ──
  computeAnalytics: (forDate?: string) => {
    const qs = forDate ? `?for_date=${forDate}` : "";
    return api.post<OPDAnalytics>(`/opd/analytics/compute${qs}`);
  },

  // ── Patient Journey ──
  getPatientJourney: (visitId: string) => api.get<PatientJourney>(`/opd/journey/${visitId}`),
};
