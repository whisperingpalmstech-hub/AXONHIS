/**
 * LIS Analyzer & Device Integration Engine – Frontend API Client
 */
import { api } from "./api";

export interface AnalyzerDevice {
  id: string; device_code: string; device_name: string; device_type: string;
  manufacturer?: string; model?: string; serial_number?: string;
  department: string; protocol: string; connection_string?: string;
  ip_address?: string; port?: number; status: string;
  last_communication?: string; last_maintenance?: string;
  test_code_mappings?: Record<string,string>; result_format_config?: Record<string,any>;
  is_active: boolean; created_at?: string;
}
export interface AnalyzerWorklistItem {
  id: string; device_id: string; sample_id: string; barcode: string;
  patient_id: string; patient_uhid?: string; patient_name?: string;
  order_id: string; test_code: string; test_name: string;
  analyzer_test_code?: string; priority: string; status: string;
  sent_at?: string; acknowledged_at?: string; completed_at?: string; created_at?: string;
}
export interface AnalyzerResult {
  id: string; device_id: string; worklist_id?: string;
  sample_id: string; barcode?: string; patient_id?: string;
  test_code: string; analyzer_test_code?: string;
  result_value?: string; result_numeric?: number;
  result_unit?: string; result_flag?: string;
  status: string; match_confidence?: number;
  is_qc_sample: boolean; verified_by?: string;
  verified_at?: string; received_at?: string; imported_at?: string;
}
export interface ReagentUsage {
  id: string; device_id: string; reagent_name: string; reagent_lot?: string;
  test_code: string; quantity_used: number; unit: string;
  current_stock?: number; reorder_level?: number;
  is_low_stock: boolean; recorded_at?: string;
}
export interface DeviceError {
  id: string; device_id: string; error_code?: string;
  error_type: string; severity: string; message: string;
  raw_data?: string; is_resolved: boolean;
  resolved_by?: string; resolved_at?: string; occurred_at?: string;
}
export interface DeviceAudit {
  id: string; device_id: string; action: string; direction: string;
  data_transmitted?: string; data_received?: string;
  status: string; error_message?: string;
  performed_by?: string; details?: any; performed_at?: string;
}
export interface AnalyzerDashStats {
  total_devices: number; online_devices: number; offline_devices: number;
  maintenance_devices: number; error_devices: number;
  pending_worklists: number; unverified_results: number;
  unresolved_errors: number; low_stock_reagents: number;
  department_status: Record<string,Record<string,number>>; results_today: number;
}

const BASE = "/analyzer-integration";

export const analyzerApi = {
  getDashboard: () => api.get<AnalyzerDashStats>(`${BASE}/dashboard`),

  // Devices
  registerDevice: (data: any) => api.post<AnalyzerDevice>(`${BASE}/devices`, data),
  listDevices: (params?: { department?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.department) q.set("department", params.department);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return api.get<AnalyzerDevice[]>(`${BASE}/devices${qs ? `?${qs}` : ""}`);
  },
  getDevice: (id: string) => api.get<AnalyzerDevice>(`${BASE}/devices/${id}`),
  updateDevice: (id: string, data: any) => api.put<AnalyzerDevice>(`${BASE}/devices/${id}`, data),
  updateDeviceStatus: (id: string, status: string, by?: string) => {
    const q = new URLSearchParams({ status });
    if (by) q.set("performed_by", by);
    return api.put<AnalyzerDevice>(`${BASE}/devices/${id}/status?${q.toString()}`, {});
  },

  // Worklists
  sendWorklist: (data: any) => api.post<AnalyzerWorklistItem>(`${BASE}/worklists`, data),
  listWorklists: (params?: { device_id?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.device_id) q.set("device_id", params.device_id);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return api.get<AnalyzerWorklistItem[]>(`${BASE}/worklists${qs ? `?${qs}` : ""}`);
  },

  // Results
  receiveResult: (data: any) => api.post<AnalyzerResult>(`${BASE}/results`, data),
  batchReceiveResults: (data: any) => api.post<AnalyzerResult[]>(`${BASE}/results/batch`, data),
  listResults: (params?: { device_id?: string; status?: string; unverified?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.device_id) q.set("device_id", params.device_id);
    if (params?.status) q.set("status", params.status);
    if (params?.unverified) q.set("unverified", "true");
    const qs = q.toString();
    return api.get<AnalyzerResult[]>(`${BASE}/results${qs ? `?${qs}` : ""}`);
  },
  verifyResult: (id: string, verified_by: string) =>
    api.put<AnalyzerResult>(`${BASE}/results/${id}/verify`, { verified_by }),
  importResult: (id: string) => api.put<any>(`${BASE}/results/${id}/import`, {}),

  // Reagents
  recordReagent: (data: any) => api.post<ReagentUsage>(`${BASE}/reagents`, data),
  listReagents: (params?: { device_id?: string; low_only?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.device_id) q.set("device_id", params.device_id);
    if (params?.low_only) q.set("low_only", "true");
    const qs = q.toString();
    return api.get<ReagentUsage[]>(`${BASE}/reagents${qs ? `?${qs}` : ""}`);
  },

  // Errors
  reportError: (data: any) => api.post<DeviceError>(`${BASE}/errors`, data),
  listErrors: (params?: { device_id?: string; unresolved?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.device_id) q.set("device_id", params.device_id);
    if (params?.unresolved) q.set("unresolved", "true");
    const qs = q.toString();
    return api.get<DeviceError[]>(`${BASE}/errors${qs ? `?${qs}` : ""}`);
  },
  resolveError: (id: string, resolved_by: string) =>
    api.put<any>(`${BASE}/errors/${id}/resolve`, { resolved_by }),

  // Audit
  getAudit: (params?: { device_id?: string; action?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.device_id) q.set("device_id", params.device_id);
    if (params?.action) q.set("action", params.action);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return api.get<DeviceAudit[]>(`${BASE}/audit${qs ? `?${qs}` : ""}`);
  },
};
