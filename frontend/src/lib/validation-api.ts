import { api } from "./api";

export interface ValidationRecord {
  id: string;
  worklist_id: string;
  stage_name: string;
  validator_name: string;
  action: string;
  corrections_made?: any;
  remarks?: string;
  timestamp: string;
}

export interface ValidationFlag {
  id: string;
  flag_type: string;
  reference_range?: string;
  recorded_value?: string;
  alert_message?: string;
  notified_to?: string[];
  created_at: string;
}

export interface ValidationRejection {
  id: string;
  worklist_id: string;
  rejected_by_name: string;
  rejection_reason: string;
  action_taken?: string;
  timestamp: string;
}

export interface ValidationWorklist {
  id: string;
  sample_id: string;
  patient_name: string;
  patient_uhid: string;
  test_order_id: string;
  test_code: string;
  test_name: string;
  department: string;
  result_value?: string;
  result_unit?: string;
  priority_level: string;
  validation_stage: string;
  is_critical_alert: boolean;
  analyzer_device_id?: string;
  created_at: string;
  updated_at: string;
  records: ValidationRecord[];
  flags: ValidationFlag[];
  rejections: ValidationRejection[];
}

export interface ApproveResultRequest {
  validator_id: string;
  validator_name: string;
  stage_name: string;
  remarks?: string;
}

export interface CorrectResultRequest {
  validator_id: string;
  validator_name: string;
  stage_name: string;
  new_value: string;
  remarks?: string;
}

export interface RejectResultRequest {
  validator_id: string;
  validator_name: string;
  rejection_reason: string;
  action_taken: string;
}

export interface ValidationPerformance {
  total_validated: number;
  total_rejected: number;
  critical_alerts: number;
  avg_turnaround_time_mins: number;
  workload_distribution: Record<string, number>;
}

const BASE = "/validation";

export const validationApi = {
  getWorklists: (params?: { department?: string; stage?: string; priority?: string; test_type?: string }) => {
    const q = new URLSearchParams();
    if (params?.department) q.set("department", params.department);
    if (params?.stage) q.set("stage", params.stage);
    if (params?.priority) q.set("priority", params.priority);
    if (params?.test_type) q.set("test_type", params.test_type);
    const qs = q.toString();
    return api.get<ValidationWorklist[]>(`${BASE}/worklist${qs ? `?${qs}` : ""}`);
  },

  getItem: (id: string) => api.get<ValidationWorklist>(`${BASE}/worklist/${id}`),

  approve: (id: string, req: ApproveResultRequest) => 
    api.put<ValidationWorklist>(`${BASE}/worklist/${id}/approve`, req),
    
  batchApprove: (worklist_ids: string[], validator_id: string, validator_name: string, stage_name: string) => 
    api.put<any>(`${BASE}/worklist/batch/approve`, { worklist_ids, validator_id, validator_name, stage_name }),

  correct: (id: string, req: CorrectResultRequest) => 
    api.put<ValidationWorklist>(`${BASE}/worklist/${id}/correct`, req),

  reject: (id: string, req: RejectResultRequest) => 
    api.put<ValidationWorklist>(`${BASE}/worklist/${id}/reject`, req),

  flagCritical: (id: string, value: string, ref: string, message: string) => 
    api.post<any>(`${BASE}/worklist/${id}/flag-critical?value=${encodeURIComponent(value)}&ref=${encodeURIComponent(ref)}&message=${encodeURIComponent(message)}`, {}),

  getMetrics: () => api.get<ValidationPerformance>(`${BASE}/metrics`)
};
