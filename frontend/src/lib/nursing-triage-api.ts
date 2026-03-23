/**
 * OPD Nursing Clinical Triage Engine — API Client
 */
import { api } from "./api";

export interface NursingWorklist {
  id: string;
  visit_id: string;
  patient_id: string;
  assigned_nurse_id?: string;
  triage_status: string;
  priority_level: string;
  called_at?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface NursingVitals {
  id: string;
  visit_id: string;
  patient_id: string;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  heart_rate?: number;
  respiratory_rate?: number;
  temperature_celsius?: number;
  oxygen_saturation_spo2?: number;
  height_cm?: number;
  weight_kg?: number;
  bmi?: number;
  blood_glucose?: number;
  pain_score?: number;
  gcs_score?: number;
  is_manual_entry: boolean;
  recorded_at: string;
}

export interface NursingAssessment {
  id: string;
  visit_id: string;
  patient_id: string;
  template_used?: string;
  chief_complaint?: string;
  allergy_information?: string;
  past_medical_history?: string;
  medication_history?: string;
  family_history?: string;
  social_history?: string;
  nursing_observations?: string;
  recorded_at: string;
}

export interface NursingTemplateOut {
  id: string;
  name: string;
  specialty?: string;
  fields: { name: string; type: string }[];
  is_active: boolean;
}

export const nursingTriageApi = {
  // Worklist Dashboard
  getWorklist: () => api.get<NursingWorklist[]>("/nursing-triage/worklist"),
  addWorklist: (data: any) => api.post<NursingWorklist>("/nursing-triage/worklist", data),
  updateStatus: (wlId: string, status: string) => api.put<any>(`/nursing-triage/worklist/${wlId}/status?status=${encodeURIComponent(status)}`),
  
  // Vitals & Alert Engine
  recordVitals: (data: any) => api.post<NursingVitals>("/nursing-triage/vitals", data),
  
  // Clinical Templates & Assessments
  getTemplates: () => api.get<NursingTemplateOut[]>("/nursing-triage/templates"),
  recordAssessment: (data: any) => api.post<NursingAssessment>("/nursing-triage/assessments", data),
  
  // Documents
  uploadDocument: (data: any) => api.post<any>("/nursing-triage/documents", data),
  
  // Doctor Desk View 
  getDoctorContext: (visitId: string) => api.get<any>(`/nursing-triage/doctor-context/${visitId}`),
};
