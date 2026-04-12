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
  getQueue: (status?: string) => api.get<TokenQueue[]>(`${BASE}/queue${status ? `?status=${status}` : ''}`),
  generateToken: (data: any) => api.post<TokenQueue>(`${BASE}/token`, data),
  callPatient: (token_id: string) => api.post<any>(`${BASE}/call`, { token_id }),
  
  checkIn: (identifier: string) => api.post<TokenQueue>(`${BASE}/check-in`, { identifier }),
  bookAppointment: (data: any) => api.post<TokenQueue>(`${BASE}/appointments`, data),
  
  updateStatus: (id: string, status: string) => api.put<TokenQueue>(`${BASE}/token/${id}/status`, { status }),

  getDepartments: () => api.get<any[]>(`${BASE}/departments`),
  getDoctors: (department_name?: string) => api.get<any[]>(`${BASE}/doctors${department_name ? `?department=${department_name}` : ''}`),
};
