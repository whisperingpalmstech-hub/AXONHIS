/**
 * LIS Laboratory Processing & Result Entry Engine – Frontend API Client
 * 
 * Covers all 10 Core Components:
 * 1. Laboratory Processing Worklist
 * 2. Result Entry Interface
 * 3. Analyzer Result Import System
 * 4. Abnormal Value Detection (auto by backend)
 * 5. Delta Check Engine (auto by backend)
 * 6. Result Comment System
 * 7. Batch Result Processing
 * 8. Quality Control Integration
 * 9. Result Status Workflow
 * 10. Result Entry Audit Logs
 */
import { api } from "./api";

export interface WorklistItem {
  id: string; cr_receipt_id?: string; sample_id: string; barcode: string;
  order_id: string; order_number: string; patient_id: string;
  patient_name?: string; patient_uhid?: string;
  test_code: string; test_name: string; sample_type: string;
  department: string; priority: string; receipt_time?: string;
  assigned_technician?: string; status: string;
  started_at?: string; completed_at?: string; created_at?: string;
}
export interface ResultFlag {
  id: string; result_id: string; flag_type: string;
  reference_low?: number; reference_high?: number;
  result_value?: number; is_critical: boolean;
  message?: string; created_at?: string;
}
export interface DeltaCheck {
  id: string; result_id: string; patient_id: string; test_code: string;
  current_value: number; previous_value: number; previous_date?: string;
  delta_absolute: number; delta_percent: number;
  threshold_percent: number; is_significant: boolean;
  message?: string; created_at?: string;
}
export interface ResultComment {
  id: string; result_id: string; comment_type: string;
  comment_text: string; is_template: boolean;
  added_by: string; added_at?: string;
}
export interface ResultEntry {
  id: string; worklist_id: string; sample_id: string; order_id: string;
  patient_id: string; test_code: string; test_name: string;
  result_type: string; result_value?: string; result_numeric?: number;
  result_unit?: string; reference_low?: number; reference_high?: number;
  result_source: string; analyzer_id?: string;
  entered_by: string; entered_at?: string;
  is_reviewed: boolean; reviewed_by?: string; reviewed_at?: string;
  status: string;
  flags: ResultFlag[];
  delta?: DeltaCheck;
  comments: ResultComment[];
}
export interface QCResult {
  id: string; department: string; test_code: string; test_name: string;
  qc_lot_number: string; qc_level: string;
  expected_value: number; expected_sd: number; actual_value: number;
  status: string; analyzer_id?: string;
  performed_by: string; performed_at?: string; remarks?: string;
}
export interface AuditEntry {
  id: string; entity_type: string; entity_id: string; action: string;
  performed_by?: string; details?: any; performed_at?: string;
}
export interface ProcessingStats {
  total_pending: number; in_progress: number; results_entered: number;
  awaiting_validation: number; critical_flags: number;
  delta_alerts: number; qc_failures: number;
  department_counts: Record<string, number>;
}

export const procApi = {
  getDashboard: () => api.get<ProcessingStats>("/lab-processing/dashboard"),

  // 1. Worklist
  listWorklist: (params?: { department?: string; status?: string; priority?: string }) => {
    const q = new URLSearchParams();
    if (params?.department) q.set("department", params.department);
    if (params?.status) q.set("status", params.status);
    if (params?.priority) q.set("priority", params.priority);
    const qs = q.toString();
    return api.get<WorklistItem[]>(`/lab-processing/worklist${qs ? `?${qs}` : ""}`);
  },
  getWorklistItem: (id: string) => api.get<WorklistItem>(`/lab-processing/worklist/${id}`),
  assignTechnician: (id: string, technician: string) =>
    api.put<WorklistItem>(`/lab-processing/worklist/${id}/assign`, { technician }),
  startProcessing: (id: string, technician: string) =>
    api.put<WorklistItem>(`/lab-processing/worklist/${id}/start`, { technician }),

  // 2. Result Entry
  enterResult: (data: {
    worklist_id: string; result_type?: string;
    result_value?: string; result_numeric?: number; result_unit?: string;
    result_source?: string; analyzer_id?: string;
    entered_by: string; comments?: string;
  }) => api.post<ResultEntry>("/lab-processing/results", data),

  // 7. Batch Result Processing
  batchEnterResults: (data: {
    items: Array<{
      worklist_id: string; result_type?: string;
      result_value?: string; result_numeric?: number;
      result_unit?: string; comments?: string;
    }>;
    result_source?: string; entered_by: string;
  }) => api.post<ResultEntry[]>("/lab-processing/results/batch", data),

  // 9. Result Status Workflow
  listResults: (params?: { patient_id?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.patient_id) q.set("patient_id", params.patient_id);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return api.get<ResultEntry[]>(`/lab-processing/results${qs ? `?${qs}` : ""}`);
  },
  getResult: (id: string) => api.get<ResultEntry>(`/lab-processing/results/${id}`),
  reviewResult: (id: string, reviewed_by: string, remarks?: string) =>
    api.put<ResultEntry>(`/lab-processing/results/${id}/review`, { reviewed_by, remarks }),
  validateResult: (id: string, validated_by: string, remarks?: string) =>
    api.put<ResultEntry>(`/lab-processing/results/${id}/validate`, { validated_by, remarks }),
  releaseResult: (id: string, released_by: string, remarks?: string) =>
    api.put<ResultEntry>(`/lab-processing/results/${id}/release`, { released_by, remarks }),
  rejectResult: (id: string, rejected_by: string, reason: string) =>
    api.put<ResultEntry>(`/lab-processing/results/${id}/reject`, { rejected_by, reason }),

  // 8. Quality Control
  recordQC: (data: {
    department: string; test_code: string; test_name: string;
    qc_lot_number: string; qc_level?: string;
    expected_value: number; expected_sd?: number; actual_value: number;
    analyzer_id?: string; performed_by: string; remarks?: string;
  }) => api.post<QCResult>("/lab-processing/qc", data),
  listQC: (params?: { department?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.department) q.set("department", params.department);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return api.get<QCResult[]>(`/lab-processing/qc${qs ? `?${qs}` : ""}`);
  },

  // 6. Comments
  addComment: (data: { result_id: string; comment_type?: string; comment_text: string; added_by: string }) =>
    api.post<ResultComment>("/lab-processing/comments", data),
  getComments: (resultId: string) => api.get<ResultComment[]>(`/lab-processing/comments/${resultId}`),
  getCommentLibrary: (department: string) => api.get<string[]>(`/lab-processing/comments/library/${department}`),

  // 10. Audit Trail
  getAuditTrail: (entityType?: string, entityId?: string, limit?: number) => {
    const q = new URLSearchParams();
    if (entityType) q.set("entity_type", entityType);
    if (entityId) q.set("entity_id", entityId);
    if (limit) q.set("limit", String(limit));
    const qs = q.toString();
    return api.get<AuditEntry[]>(`/lab-processing/audit${qs ? `?${qs}` : ""}`);
  },
};
