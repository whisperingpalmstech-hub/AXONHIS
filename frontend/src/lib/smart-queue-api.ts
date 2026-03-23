/**
 * OPD Smart Queue & Flow Orchestration Engine — API Client
 */
import { api } from "./api";

export interface QueueMaster {
  id: string;
  doctor_id?: string;
  department?: string;
  queue_date: string;
  room_number?: string;
  room_status: string;
  status_reason?: string;
  current_length: number;
  avg_consult_time_min: number;
}

export interface QueuePosition {
  id: string;
  queue_id: string;
  visit_id: string;
  patient_id: string;
  status: string;
  priority_level: string;
  calculated_priority_score: number;
  position_number?: number;
  estimated_wait_time_min?: number;
  estimated_call_time?: string;
  missed_calls_count: number;
  joined_at: string;
}

export interface ActivePatientDisplay {
  position_number: number;
  patient_id: string;
  patient_uhid?: string;
  patient_name?: string;
  priority_level: string;
  status: string;
}

export interface DigitalSignageDisplay {
  room_number: string;
  doctor_name: string;
  department: string;
  current_patient?: ActivePatientDisplay;
  next_patients: ActivePatientDisplay[];
  queue_length: number;
  avg_wait_time_min: number;
}

export interface CrowdPredictionSnapshot {
  id: string;
  prediction_date: string;
  department?: string;
  predicted_peak_start?: string;
  predicted_peak_end?: string;
  predicted_inflow_count: number;
  confidence_score: number;
  factors_used: string[];
}

export const smartQueueApi = {
  // Master
  createQueue: (data: any) => api.post<QueueMaster>("/smart-queue/master", data),
  
  // Positions
  addToQueue: (data: any) => api.post<QueuePosition>("/smart-queue/positions", data),
  forceReorder: (queueId: string) => api.put<any>(`/smart-queue/positions/${queueId}/reorder`),
  
  // Dashboard & Signage
  getDigitalSignage: (queueId: string) => api.get<DigitalSignageDisplay>(`/smart-queue/dashboard/${queueId}/signage`),
  
  // Routing
  getRoutingRecommendation: (department: string) => 
    api.get<any>(`/smart-queue/routing/recommendation?department=${encodeURIComponent(department)}`),
    
  // Recovery
  markMissed: (posId: string) => api.post<any>(`/smart-queue/positions/${posId}/mark-missed`),
  
  // Wayfinding
  getWayfinding: (roomNumber: string) => api.get<any>(`/smart-queue/wayfinding/${roomNumber}`),
  
  // AI Prediction
  generateCrowdPrediction: (department: string) => 
    api.post<CrowdPredictionSnapshot>(`/smart-queue/analytics/crowd-prediction?dept=${encodeURIComponent(department)}`),
};
