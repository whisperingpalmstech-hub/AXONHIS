import { api } from "./api";

const BASE = "/kiosk";

export interface TokenQueue {
  id: string;
  token_number: number;
  token_display: string;
  department: string;
  doctor_id?: string;
  patient_uhid?: string;
  patient_name?: string;
  status: string;
  priority: boolean;
  generated_at: string;
  counter_name?: string;
}

export const kioskApi = {
  generateToken: (data: any) => api.post<TokenQueue>(`${BASE}/token`, data),
  getQueue: (status?: string) => api.get<TokenQueue[]>(`${BASE}/queue${status ? `?status=${status}` : ''}`),
  callPatient: (token_id: string, counter_id?: string) => api.post<any>(`${BASE}/call`, { token_id, counter_id }),
  updateStatus: (token_id: string, new_status: string) => api.put<TokenQueue>(`${BASE}/token/${token_id}/status`, { status: new_status }),
  checkIn: (identifier: string) => api.post<TokenQueue>(`${BASE}/check-in`, { identifier }),
  getDepartments: () => api.get<any[]>(`${BASE}/departments`),
  getDoctors: (department: string) => api.get<any[]>(`${BASE}/doctors?department=${department}`),
  bookAppointment: (data: any) => api.post<TokenQueue>(`${BASE}/appointments`, data),
};
