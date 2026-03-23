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
};
