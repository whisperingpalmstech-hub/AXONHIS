/**
 * LIS Central Receiving & Specimen Tracking Engine – Frontend API Client
 */
import { api } from "./api";

export interface CRReceipt {
  id: string; sample_id: string; barcode: string; order_id: string; order_number: string;
  patient_id: string; patient_name?: string; patient_uhid?: string;
  test_code: string; test_name: string; sample_type: string; container_type?: string;
  collection_time?: string; collection_location?: string; priority: string;
  transport_batch_id?: string; received_by: string; received_at?: string;
  status: string; current_location: string; notes?: string;
}
export interface CRVerification {
  id: string; receipt_id: string; sample_type_correct: boolean; container_correct: boolean;
  volume_adequate: boolean; labeling_correct: boolean; transport_ok: boolean;
  hemolyzed: boolean; clotted: boolean; overall_result: string;
  verified_by: string; verified_at?: string; remarks?: string;
}
export interface CRRejection {
  id: string; receipt_id: string; rejection_reason: string; rejection_details?: string;
  rejected_by: string; rejected_at?: string; recollection_requested: boolean;
  notification_sent: boolean; notification_targets?: any;
}
export interface CRRouting {
  id: string; receipt_id: string; target_department: string; routed_by: string;
  routed_at?: string; received_at_dept?: string; received_by_dept?: string;
  status: string; notes?: string;
}
export interface CRStorage {
  id: string; receipt_id: string; storage_location: string; storage_temperature: string;
  max_duration_hours: number; stored_at?: string; stored_by: string;
  retrieved_at?: string; retrieved_by?: string; is_active: boolean; alert_sent: boolean;
}
export interface CRCustodyEntry {
  id: string; receipt_id: string; sample_id: string; stage: string;
  location: string; responsible_staff: string; timestamp?: string; notes?: string;
}
export interface CRAlert {
  id: string; alert_type: string; severity: string; sample_id?: string;
  order_number?: string; patient_name?: string; message: string;
  status: string; acknowledged_by?: string; acknowledged_at?: string; created_at?: string;
}
export interface CRAuditEntry {
  id: string; entity_type: string; entity_id: string; action: string;
  performed_by?: string; details?: any; performed_at?: string;
}
export interface CRDashboardStats {
  received_today: number; pending_verification: number; accepted: number;
  rejected: number; routed: number; stored: number; active_alerts: number;
  department_distribution: Record<string, number>;
}

export const crApi = {
  getDashboard: () => api.get<CRDashboardStats>("/central-receiving/dashboard"),
  registerSample: (data: { barcode: string; received_by: string; notes?: string }) =>
    api.post<CRReceipt>("/central-receiving/receive", data),
  listReceipts: (params?: { status?: string; priority?: string }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.priority) q.set("priority", params.priority);
    const qs = q.toString();
    return api.get<CRReceipt[]>(`/central-receiving/receipts${qs ? `?${qs}` : ""}`);
  },
  getReceipt: (id: string) => api.get<CRReceipt>(`/central-receiving/receipts/${id}`),
  getReceiptByBarcode: (barcode: string) => api.get<CRReceipt>(`/central-receiving/receipts/barcode/${barcode}`),
  verifySample: (data: {
    receipt_id: string; sample_type_correct?: boolean; container_correct?: boolean;
    volume_adequate?: boolean; labeling_correct?: boolean; transport_ok?: boolean;
    hemolyzed?: boolean; clotted?: boolean; verified_by: string; remarks?: string;
  }) => api.post<CRVerification>("/central-receiving/verify", data),
  rejectSample: (data: {
    receipt_id: string; rejection_reason: string; rejection_details?: string;
    rejected_by: string; recollection_requested?: boolean;
  }) => api.post<CRRejection>("/central-receiving/reject", data),
  listRejections: () => api.get<CRRejection[]>("/central-receiving/rejections"),
  routeSample: (data: { receipt_id: string; target_department?: string; routed_by: string; notes?: string }) =>
    api.post<CRRouting>("/central-receiving/route", data),
  receiveAtDept: (routingId: string, receivedBy: string) =>
    api.put<CRRouting>(`/central-receiving/routing/${routingId}/receive`, { received_by_dept: receivedBy }),
  listRoutings: (department?: string) => {
    const qs = department ? `?department=${department}` : "";
    return api.get<CRRouting[]>(`/central-receiving/routings${qs}`);
  },
  storeSample: (data: {
    receipt_id: string; storage_location: string; storage_temperature?: string;
    max_duration_hours?: number; stored_by: string;
  }) => api.post<CRStorage>("/central-receiving/store", data),
  retrieveSample: (storageId: string, retrievedBy: string) =>
    api.put<CRStorage>(`/central-receiving/storage/${storageId}/retrieve`, { retrieved_by: retrievedBy }),
  listActiveStorage: () => api.get<CRStorage[]>("/central-receiving/storage"),
  getChainOfCustody: (receiptId: string) => api.get<CRCustodyEntry[]>(`/central-receiving/chain-of-custody/${receiptId}`),
  listAlerts: (status?: string) => {
    const qs = status ? `?status=${status}` : "";
    return api.get<CRAlert[]>(`/central-receiving/alerts${qs}`);
  },
  acknowledgeAlert: (alertId: string, by: string) =>
    api.put<CRAlert>(`/central-receiving/alerts/${alertId}/acknowledge`, { acknowledged_by: by }),
  resolveAlert: (alertId: string) => api.put<CRAlert>(`/central-receiving/alerts/${alertId}/resolve`),
  getAuditTrail: (entityType?: string, entityId?: string, limit?: number) => {
    const q = new URLSearchParams();
    if (entityType) q.set("entity_type", entityType);
    if (entityId) q.set("entity_id", entityId);
    if (limit) q.set("limit", String(limit));
    const qs = q.toString();
    return api.get<CRAuditEntry[]>(`/central-receiving/audit${qs ? `?${qs}` : ""}`);
  },
};
