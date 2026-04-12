import { api } from "./api";

// --- Types ---
export interface HomeCollection { id: string; patient_name: string; patient_uhid: string; address: string; test_requested: string; preferred_collection_time: string; status: string; test_order_id?: string; created_at: string; }
export interface PhlebSchedule { id: string; request_id: string; collection_date: string; collection_time: string; assigned_phlebotomist: string; collection_location: string; status: string; }
export interface OutsourceLab { id: string; lab_name: string; contact_details: string; test_capabilities: string; is_active: boolean; }
export interface ExternalResult { id: string; outsource_lab_id: string; test_order_id: string; sample_id: string; patient_uhid: string; result_data: string; imported_at: string; is_validated: boolean; }
export interface QCRecord { id: string; test_name: string; equipment_id: string; qc_date: string; result_value: number; expected_value: number; is_passed: boolean; failure_alert_sent: boolean; remarks?: string; }
export interface EquipmentRecord { id: string; equipment_id: string; equipment_name: string; maintenance_schedule: string; last_calibration_date: string; next_maintenance_date: string; service_history: string; is_overdue: boolean; }

const BASE = "/extended";

export const extendedLabApi = {
  // Home Collections
  getHomeCollections: () => api.get<HomeCollection[]>(`${BASE}/home-collections`),
  createHomeCollection: (data: any) => api.post<HomeCollection>(`${BASE}/home-collections`, data),
  schedulePhlebotomist: (data: any) => api.post<PhlebSchedule>(`${BASE}/home-collections/schedule`, data),

  // Outsource Labs
  getOutsourceLabs: () => api.get<OutsourceLab[]>(`${BASE}/outsource-labs`),
  registerOutsourceLab: (data: any) => api.post<OutsourceLab>(`${BASE}/outsource-labs`, data),
  importExternalResult: (data: any) => api.post<ExternalResult>(`${BASE}/outsource-results`, data),

  // Quality Control
  getQCs: () => api.get<QCRecord[]>(`${BASE}/quality-controls`),
  recordQC: (data: any) => api.post<QCRecord>(`${BASE}/quality-controls`, data),

  // Equipment Maintenance
  getEquipment: () => api.get<EquipmentRecord[]>(`${BASE}/equipment-maintenance`),
  addEquipment: (data: any) => api.post<EquipmentRecord>(`${BASE}/equipment-maintenance`, data),
};
