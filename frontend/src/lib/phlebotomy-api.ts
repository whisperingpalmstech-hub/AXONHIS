/**
 * LIS Phlebotomy & Sample Collection Engine – Frontend API Client
 */
import { api } from "./api";

// ── Interfaces ────────────────────────────────────────────────────────────

export interface WorklistItem {
  id: string;
  order_id: string;
  order_item_id: string;
  order_number: string;
  patient_id: string;
  patient_name?: string;
  patient_uhid?: string;
  visit_id?: string;
  test_code: string;
  test_name: string;
  sample_type: string;
  barcode?: string;
  priority: string;
  collection_location: string;
  status: string;
  consent_required: boolean;
  consent_uploaded: boolean;
  assigned_collector?: string;
  scheduled_time?: string;
  is_repeat: boolean;
  created_at?: string;
}

export interface SampleCollectionRecord {
  id: string;
  worklist_id: string;
  sample_id: string;
  order_id: string;
  patient_id: string;
  patient_uhid?: string;
  barcode: string;
  test_code: string;
  test_name: string;
  sample_type: string;
  container_type: string;
  collection_location: string;
  collector_name: string;
  collected_at?: string;
  status: string;
  identity_verified: boolean;
  identity_method?: string;
  notes?: string;
  quantity_ml?: number;
}

export interface ConsentDoc {
  id: string;
  worklist_id: string;
  patient_id: string;
  test_code: string;
  document_type: string;
  file_name: string;
  file_url: string;
  file_format: string;
  uploaded_by?: string;
  uploaded_at?: string;
  verified: boolean;
}

export interface RepeatSchedule {
  id: string;
  order_id: string;
  patient_id: string;
  test_code: string;
  test_name: string;
  total_samples: number;
  collected_count: number;
  interval_minutes: number;
  schedule_config?: any;
  is_complete: boolean;
  started_at?: string;
  created_at?: string;
}

export interface TransportBatch {
  id: string;
  batch_id: string;
  sample_ids: string[];
  sample_count: number;
  transport_personnel: string;
  transport_method: string;
  dispatch_time?: string;
  received_time?: string;
  received_by?: string;
  status: string;
  notes?: string;
}

export interface BarcodeLabel {
  barcode: string;
  sample_id: string;
  patient_uhid?: string;
  order_number: string;
  test_name: string;
  sample_type: string;
  collected_at: string;
}

export interface AuditEntry {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  performed_by?: string;
  details?: any;
  performed_at?: string;
}

// ── API Functions ─────────────────────────────────────────────────────────

export const phlebotomyApi = {
  // Worklist
  getWorklist: (params?: { location?: string; priority?: string; status?: string; collector?: string }) => {
    const q = new URLSearchParams();
    if (params?.location) q.set("location", params.location);
    if (params?.priority) q.set("priority", params.priority);
    if (params?.status) q.set("status", params.status);
    if (params?.collector) q.set("collector", params.collector);
    const qs = q.toString();
    return api.get<WorklistItem[]>(`/phlebotomy/worklist${qs ? `?${qs}` : ""}`);
  },

  getWorklistItem: (id: string) => api.get<WorklistItem>(`/phlebotomy/worklist/${id}`),

  assignCollector: (id: string, collector: string) =>
    api.put<WorklistItem>(`/phlebotomy/worklist/${id}/assign?collector=${encodeURIComponent(collector)}`),

  // Patient Verification
  verifyPatient: (data: { worklist_id: string; verification_method: string; verified_by: string }) =>
    api.post<{ verified: boolean; patient_name: string; patient_uhid?: string; date_of_birth?: string; gender?: string; photo_url?: string }>("/phlebotomy/verify-patient", data),

  // Sample Collection
  collectSample: (data: {
    worklist_id: string;
    collector_name: string;
    collector_id?: string;
    container_type?: string;
    collection_location?: string;
    identity_verified?: boolean;
    identity_method?: string;
    notes?: string;
    quantity_ml?: number;
  }) => api.post<SampleCollectionRecord>("/phlebotomy/collect", data),

  listSamples: (patientId?: string) => {
    const qs = patientId ? `?patient_id=${patientId}` : "";
    return api.get<SampleCollectionRecord[]>(`/phlebotomy/samples${qs}`);
  },

  getSample: (sampleId: string) => api.get<SampleCollectionRecord>(`/phlebotomy/samples/${sampleId}`),

  updateSampleStatus: (sampleId: string, data: { status: string; updated_by?: string; notes?: string }) =>
    api.put<SampleCollectionRecord>(`/phlebotomy/samples/${sampleId}/status`, data),

  getBarcodeLabel: (sampleId: string) => api.get<BarcodeLabel>(`/phlebotomy/samples/${sampleId}/barcode`),

  // Consent
  uploadConsent: (data: { worklist_id: string; file_name: string; file_url: string; file_format?: string; uploaded_by?: string }) =>
    api.post<ConsentDoc>("/phlebotomy/consent", data),

  getConsentDocs: (worklistId: string) => api.get<ConsentDoc[]>(`/phlebotomy/consent/${worklistId}`),

  // Repeat Schedule
  createRepeatSchedule: (data: { order_id: string; patient_id: string; test_code: string; test_name: string; total_samples?: number; interval_minutes?: number }) =>
    api.post<RepeatSchedule>("/phlebotomy/repeat-schedule", data),

  listActiveSchedules: (patientId?: string) => {
    const qs = patientId ? `?patient_id=${patientId}` : "";
    return api.get<RepeatSchedule[]>(`/phlebotomy/repeat-schedule${qs}`);
  },

  markRepeatCollected: (scheduleId: string) =>
    api.put<RepeatSchedule>(`/phlebotomy/repeat-schedule/${scheduleId}/collected`),

  // Transport
  createTransportBatch: (data: { sample_ids: string[]; transport_personnel: string; transport_method?: string; notes?: string }) =>
    api.post<TransportBatch>("/phlebotomy/transport", data),

  receiveTransportBatch: (batchId: string, receivedBy: string) =>
    api.put<TransportBatch>(`/phlebotomy/transport/${batchId}/receive`, { received_by: receivedBy }),

  listTransportBatches: (status?: string) => {
    const qs = status ? `?status=${status}` : "";
    return api.get<TransportBatch[]>(`/phlebotomy/transport${qs}`);
  },

  // Audit
  getAuditTrail: (entityType?: string, entityId?: string, limit?: number) => {
    const q = new URLSearchParams();
    if (entityType) q.set("entity_type", entityType);
    if (entityId) q.set("entity_id", entityId);
    if (limit) q.set("limit", String(limit));
    const qs = q.toString();
    return api.get<AuditEntry[]>(`/phlebotomy/audit${qs ? `?${qs}` : ""}`);
  },
};
