import { api } from "./api";

export interface ReportReleaseOut {
  id: string;
  report_id: string;
  released_by_name: string;
  distribution_channels: string[];
  recipients: string[];
  released_at: string;
}

export interface ReportVersionOut {
  id: string;
  version_number: number;
  changes_made: any;
  amended_by_name: string;
  amended_at: string;
  previous_snapshot: any;
}

export interface ReportAuditLogOut {
  id: string;
  action_type: string;
  actor_name: string;
  details?: any;
  timestamp: string;
}

export interface LabReportOut {
  id: string;
  sample_id: string;
  test_order_id: string;
  patient_uhid: string;
  patient_name: string;
  visit_id?: string;
  department?: string;
  test_details: any;
  result_values: any;
  reference_ranges?: any;
  abnormal_flags?: any;
  interpretative_comments?: string;
  is_signed: boolean;
  signed_by_name?: string;
  signed_by_designation?: string;
  signed_at?: string;
  status: string;
  current_version: number;
  created_at: string;
  updated_at: string;

  releases: ReportReleaseOut[];
  versions: ReportVersionOut[];
  audit_logs: ReportAuditLogOut[];
}

export interface SignReportRequest {
  signer_id: string;
  signer_name: string;
  signer_designation: string;
}

export interface ReleaseReportRequest {
  releaser_id: string;
  releaser_name: string;
  channels: string[];
  recipients: string[];
}

export interface BulkReleaseRequest {
  report_ids: string[];
  releaser_id: string;
  releaser_name: string;
  channels: string[];
}

export interface AmendReportRequest {
  amender_id: string;
  amender_name: string;
  changes_made: any;
  reason: string;
  new_result_values: any;
  new_comments?: string;
}

const BASE = "/reports";

export const reportingApi = {
  getReports: (params?: { status?: string; department?: string; patient_uhid?: string }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.department) q.set("department", params.department);
    if (params?.patient_uhid) q.set("patient_uhid", params.patient_uhid);
    const qs = q.toString();
    return api.get<LabReportOut[]>(`${BASE}${qs ? `?${qs}` : ""}`);
  },

  getReport: (id: string) => api.get<LabReportOut>(`${BASE}/${id}`),

  signReport: (id: string, req: SignReportRequest) => 
    api.put<LabReportOut>(`${BASE}/${id}/sign`, req),

  releaseReport: (id: string, req: ReleaseReportRequest) => 
    api.put<LabReportOut>(`${BASE}/${id}/release`, req),

  bulkRelease: (req: BulkReleaseRequest) => 
    api.post<any>(`${BASE}/bulk-release`, req),

  amendReport: (id: string, req: AmendReportRequest) => 
    api.put<LabReportOut>(`${BASE}/${id}/amend`, req),
};
