import { api } from "./api";

export interface DoctorWorklist {
  id: string;
  visit_id: string;
  patient_id: string;
  status: string;
  priority_indicator: string;
  queue_position: number;
}

export interface PatientTimelineNode {
  node_type: string;
  date: string;
  title: string;
  details: string;
}

export interface DoctorDeskApiType {
  // 1 Worklist
  getWorklist: (doctorId: string) => Promise<DoctorWorklist[]>;
  updateStatus: (wlId: string, status: string) => Promise<any>;
  seedPatient: (data: any) => Promise<any>;

  // 2 Timeline
  getTimeline: (patientId: string) => Promise<any>;

  // 3 Scribe
  saveNote: (data: any) => Promise<any>;
  transcribeVoice: (data: any) => Promise<any>;

  // 5 AI Suggest
  getAISuggestions: (symptoms: string) => Promise<any>;

  // 7 Orders
  placeOrder: (data: any) => Promise<any>;

  // 8 Prescriptions
  savePrescription: (data: any) => Promise<any>;
  parseVoicePrescription: (data: any) => Promise<any>;

  // 9 Summary
  generateSummary: (visitId: string, doctorId: string) => Promise<any>;

  // 10 Follow-up
  logFollowUp: (data: any) => Promise<any>;

  // Advanced EMR
  addComplaint: (data: any) => Promise<any>;
  getComplaints: (visitId: string) => Promise<any[]>;
  addMedicalHistory: (data: any) => Promise<any>;
  getMedicalHistory: (patientId: string) => Promise<any[]>;
  addExamination: (data: any) => Promise<any>;
  getExaminations: (visitId: string) => Promise<any[]>;
  addDiagnosis: (data: any) => Promise<any>;
  getDiagnoses: (visitId: string) => Promise<any[]>;
  addVitals: (data: any) => Promise<any>;
  getVitals: (visitId: string) => Promise<any[]>;
  getPrescriptions: (visitId: string) => Promise<any[]>;
  getOrders: (visitId: string) => Promise<any[]>;
}

export const doctorDeskApi: DoctorDeskApiType = {
  getWorklist: (doctorId) => api.get(`/doctor-desk/worklist/${doctorId}`),
  updateStatus: (wlId, status) => api.put(`/doctor-desk/worklist/${wlId}/status?status=${status}`),
  seedPatient: (data) => api.post(`/doctor-desk/worklist`, data),

  getTimeline: (patientId) => api.get(`/doctor-desk/timeline/${patientId}`),

  saveNote: (data) => api.post(`/doctor-desk/scribe`, data),
  transcribeVoice: (data) => api.post(`/doctor-desk/scribe/transcribe`, data),

  getAISuggestions: (symptoms) => api.post(`/doctor-desk/ai/suggestions`, {
    visit_id: "00000000-0000-0000-0000-000000000000",
    symptoms
  }),

  placeOrder: (data) => api.post(`/doctor-desk/orders`, data),

  savePrescription: (data) => api.post(`/doctor-desk/prescriptions`, data),
  parseVoicePrescription: (data) => api.post(`/doctor-desk/prescriptions/voice?visit_id=${data.visit_id}`, { doctor_id: data.doctor_id, voice_command_text: data.text }),

  generateSummary: (visitId, doctorId) => api.post(`/doctor-desk/summary/${visitId}?doctor_id=${doctorId}`, {}),

  logFollowUp: (data) => api.post(`/doctor-desk/follow-ups`, data),

  // ── Advanced EMR Subsystems ──────────────────────────────────────
  addComplaint: (data: any) => api.post(`/doctor-desk/advanced/complaints`, data),
  getComplaints: (visitId: string) => api.get(`/doctor-desk/advanced/complaints/${visitId}`),

  addMedicalHistory: (data: any) => api.post(`/doctor-desk/advanced/medical-history`, data),
  getMedicalHistory: (patientId: string) => api.get(`/doctor-desk/advanced/medical-history/${patientId}`),

  addExamination: (data: any) => api.post(`/doctor-desk/advanced/examinations`, data),
  getExaminations: (visitId: string) => api.get(`/doctor-desk/advanced/examinations/${visitId}`),

  addDiagnosis: (data: any) => api.post(`/doctor-desk/advanced/diagnoses`, data),
  getDiagnoses: (visitId: string) => api.get(`/doctor-desk/advanced/diagnoses/${visitId}`),

  addVitals: (data: any) => api.post(`/doctor-desk/advanced/vitals`, data),
  getVitals: (visitId: string) => api.get(`/doctor-desk/advanced/vitals/${visitId}`),

  getPrescriptions: (visitId: string) => api.get(`/doctor-desk/prescriptions?visit_id=${visitId}`),
  getOrders: (visitId: string) => api.get(`/doctor-desk/orders?visit_id=${visitId}`),
};
