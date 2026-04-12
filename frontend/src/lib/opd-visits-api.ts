/**
 * OPD Visit Intelligence Engine — API Client
 */
import { api } from "./api";

// Types
export interface OpdVisit {
  id: string; visit_id: string; encounter_id: string; patient_id: string;
  patient_uhid?: string; visit_date_time: string; visit_type: string;
  visit_source: string; status: string; specialty?: string;
  doctor_id?: string; department?: string; clinic_location?: string;
  referral_type?: string; referral_source?: string;
  payment_entitlement?: string; priority_tag: string;
  is_follow_up: boolean; parent_visit_id?: string;
  appointment_id?: string; queue_token?: string;
  estimated_wait_min?: number; created_at: string;
}

export interface VisitComplaint {
  id: string; visit_id: string; raw_complaint_text?: string;
  input_mode: string; language: string;
  structured_symptoms: string[]; medical_keywords: string[];
  icpc_codes: { code: string; label: string }[];
  icd_suggestions: any[]; severity_score?: number;
  ai_confidence?: number; created_at: string;
}

export interface VisitClassification {
  id: string; visit_id: string; category: string;
  classification_reason?: string; triggered_rules: string[];
  complaint_severity?: number; vitals_abnormal: boolean;
  has_chronic_disease: boolean; age_risk: boolean;
  vitals_snapshot?: any; is_override: boolean; classified_at: string;
}

export interface DoctorRecommendation {
  id: string; visit_id: string; recommended_specialty?: string;
  recommended_doctors: any[]; selection_mode: string;
  selected_doctor_id?: string; created_at: string;
}

export interface ContextSnapshot {
  id: string; visit_id: string; patient_id: string;
  previous_diagnoses: any[]; previous_prescriptions: any[];
  allergies: any[]; chronic_conditions: any[];
  last_visit_notes?: string; last_visit_date?: string;
  recent_lab_reports: any[]; recent_radiology_reports: any[];
  active_medications: any[]; context_summary?: string;
  risk_flags: string[]; aggregated_at: string;
}

export interface QuestionnaireTemplate {
  id: string; specialty: string; title: string;
  description?: string; questions: any[];
  is_active: boolean; created_at: string;
}

export interface VisitDashboardSummary {
  period_start: string; period_end: string;
  total_visits: number; completed: number; cancelled: number;
  no_shows: number; emergency_count: number; priority_count: number;
  routine_count: number; top_specialties: any[]; top_complaints: any[];
  avg_wait_time_min?: number;
}

// API
export const opdVisitsApi = {
  // Visits
  createVisit: (data: any) => api.post<OpdVisit>("/opd-visits/visits", data),
  listVisits: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return api.get<OpdVisit[]>(`/opd-visits/visits${qs}`);
  },
  getVisit: (id: string) => api.get<OpdVisit>(`/opd-visits/visits/${id}`),
  updateVisit: (id: string, data: any) => api.put<OpdVisit>(`/opd-visits/visits/${id}`, data),
  getDoctorQueue: (doctorId: string) => api.get<OpdVisit[]>(`/opd-visits/visits/queue/${doctorId}`),

  // Complaints
  captureComplaint: (data: any) => api.post<VisitComplaint>("/opd-visits/complaints", data),
  getComplaints: (visitId: string) => api.get<VisitComplaint[]>(`/opd-visits/complaints/${visitId}`),

  // Classification
  classifyVisit: (data: any) => api.post<VisitClassification>("/opd-visits/classification", data),
  getClassification: (visitId: string) => api.get<VisitClassification>(`/opd-visits/classification/${visitId}`),
  overrideClassification: (visitId: string, data: any) =>
    api.put<VisitClassification>(`/opd-visits/classification/${visitId}/override`, data),

  // Doctor Recommendation
  recommendDoctor: (visitId: string) => api.post<DoctorRecommendation>(`/opd-visits/recommendations/${visitId}`),
  selectDoctor: (visitId: string, data: any) =>
    api.put<DoctorRecommendation>(`/opd-visits/recommendations/${visitId}/select`, data),

  // Questionnaires
  createTemplate: (data: any) => api.post<QuestionnaireTemplate>("/opd-visits/questionnaires/templates", data),
  listTemplates: (specialty?: string) => {
    const qs = specialty ? `?specialty=${encodeURIComponent(specialty)}` : "";
    return api.get<QuestionnaireTemplate[]>(`/opd-visits/questionnaires/templates${qs}`);
  },
  submitResponse: (data: any) => api.post<any>("/opd-visits/questionnaires/responses", data),
  getResponses: (visitId: string) => api.get<any[]>(`/opd-visits/questionnaires/responses/${visitId}`),

  // Context
  aggregateContext: (visitId: string) => api.post<ContextSnapshot>(`/opd-visits/context/${visitId}/aggregate`),
  getContext: (visitId: string) => api.get<ContextSnapshot>(`/opd-visits/context/${visitId}`),

  // Multi-Visit Rules
  createRule: (data: any) => api.post<any>("/opd-visits/multi-visit-rules", data),
  listRules: () => api.get<any[]>("/opd-visits/multi-visit-rules"),
  checkMultiVisit: (visitId: string) => api.get<any>(`/opd-visits/multi-visit-check/${visitId}`),

  // Analytics
  computeAnalytics: (forDate: string, department?: string) => {
    const qs = department ? `&department=${encodeURIComponent(department)}` : "";
    return api.post<any>(`/opd-visits/analytics/compute?for_date=${forDate}${qs}`);
  },
  getSummary: (from: string, to: string) =>
    api.get<VisitDashboardSummary>(`/opd-visits/analytics/summary?from_date=${from}&to_date=${to}`),
};
