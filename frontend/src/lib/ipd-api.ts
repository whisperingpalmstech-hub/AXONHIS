import { api } from './api';

export interface DashboardStats {
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  housekeeping_beds: number;
  reserved_beds: number;
  pending_requests: number;
}

export interface IpdAdmissionRequest {
  id: string;
  request_id: string;
  patient_name: string;
  patient_uhid: string;
  gender: string;
  date_of_birth: string;
  mobile_number: string;
  admitting_doctor: string;
  treating_doctor: string;
  specialty: string;
  reason_for_admission: string;
  admission_category: string;
  admission_source: string;
  preferred_bed_category: string;
  expected_admission_date: string;
  status: string;
  created_at: string;
}

export interface IpdBedStatus {
  current_status: string;
  patient_uhid?: string;
  admission_number?: string;
  updated_at: string;
}

export interface IpdBedMaster {
  id: string;
  bed_code: string;
  room_id: string;
  bed_number: string;
  bed_type: string;
  status: string;
}

export interface IpdAdmissionRecord {
  id: string;
  admission_number: string;
  patient_uhid: string;
  bed_uuid: string;
  admitting_doctor: string;
  admission_time: string;
  status: string;
}

export const ipdApi = {
  getDashboardStats: () => api.get<DashboardStats>('/ipd/dashboard/stats'),
  getAdmissions: () => api.get<IpdAdmissionRecord[]>('/ipd/admissions'),
  createAdmissionRequest: (data: any) => api.post<IpdAdmissionRequest>('/ipd/requests', data),
  getPendingRequests: () => api.get<IpdAdmissionRequest[]>('/ipd/requests/pending'),
  updateRequestStatus: (reqId: string, status: string) => api.put<IpdAdmissionRequest>(`/ipd/requests/${reqId}/status?new_status=${status}`),
  
  // Use core Wards module for Bed Management
  getAllBeds: () => api.get<IpdBedMaster[]>('/wards/beds'),
  markBedCleaned: (bedId: string) => api.post(`/wards/cleaning/complete?bed_id=${bedId}&user_id=ipd-admin`),
  
  allocateBed: (reqId: string, bedId: string) => api.post<IpdAdmissionRecord>(`/ipd/requests/${reqId}/allocate/${bedId}`),

  // --- Phase 14: Smart Admission ---
  generateCostEstimate: (reqId: string, data: any) => api.post<any>(`/ipd/requests/${reqId}/estimate`, data),
  getChecklist: (admNo: string) => api.get<any>(`/ipd/admissions/${admNo}/checklist`),
  updateChecklist: (admNo: string, data: any) => api.put<any>(`/ipd/admissions/${admNo}/checklist`, data),
  saveInsurance: (admNo: string, data: any) => api.post<any>(`/ipd/admissions/${admNo}/insurance`, data),
  getProjectedBill: (admNo: string) => api.get<any>(`/ipd/admissions/${admNo}/bill`),
  collectDeposit: (admNo: string, data: any) => api.post<any>(`/ipd/admissions/${admNo}/deposit`, data),
  requestTransport: (admNo: string, data: any) => api.post<any>(`/ipd/admissions/${admNo}/transport`, data),

  // --- Phase 15: Nursing Coversheet & Patient Acceptance ---
  getNursingWorklist: () => api.get<any[]>('/ipd/nursing/worklist'),
  acceptPatient: (data: any) => api.post<any>('/ipd/nursing/coversheets', data),
  addNursingNote: (admNo: string, data: any) => api.post<any>(`/ipd/nursing/notes?admission_number=${admNo}`, data),
  assignNursingCare: (admNo: string, data: any) => api.post<any>(`/ipd/nursing/assignments?admission_number=${admNo}`, data),

  // --- Phase 16: Nursing Assessment & Vitals Monitoring ---
  recordVitals: (admNo: string, data: any) => api.post<any>(`/ipd/vitals/${admNo}`, data),
  getVitalsHistory: (admNo: string) => api.get<any[]>(`/ipd/vitals/${admNo}`),
  saveNursingAssessment: (admNo: string, data: any) => api.post<any>(`/ipd/assessments/${admNo}`, data),
  getNursingAssessment: (admNo: string) => api.get<any>(`/ipd/assessments/${admNo}`),
  addRiskAssessment: (admNo: string, data: any) => api.post<any>(`/ipd/risks/${admNo}`, data),
  getRiskAssessments: (admNo: string) => api.get<any[]>(`/ipd/risks/${admNo}`),
  addPainScore: (admNo: string, data: any) => api.post<any>(`/ipd/pain/${admNo}`, data),
  addNutritionAssessment: (admNo: string, data: any) => api.post<any>(`/ipd/nutrition/${admNo}`, data),
  addObservation: (admNo: string, data: any) => api.post<any>(`/ipd/observations/${admNo}`, data),
  getObservations: (admNo: string) => api.get<any[]>(`/ipd/observations/${admNo}`),

  // --- Phase 17: Doctor Coversheet & Clinical Documentation ---
  getDoctorWorklist: () => api.get<any[]>('/ipd/doctor/worklist'),
  getDoctorCoversheet: (admNo: string) => api.get<any>(`/ipd/doctor/coversheet/${admNo}`),
  updateDoctorCoversheet: (admNo: string, data: any) => api.put<any>(`/ipd/doctor/coversheet/${admNo}`, data),
  
  getDiagnoses: (admNo: string) => api.get<any[]>(`/ipd/doctor/diagnoses/${admNo}`),
  addDiagnosis: (admNo: string, data: any) => api.post<any>(`/ipd/doctor/diagnoses/${admNo}`, data),
  
  getTreatmentPlans: (admNo: string) => api.get<any[]>(`/ipd/doctor/treatment-plans/${admNo}`),
  addTreatmentPlan: (admNo: string, data: any) => api.post<any>(`/ipd/doctor/treatment-plans/${admNo}`, data),
  
  getProgressNotes: (admNo: string) => api.get<any[]>(`/ipd/doctor/progress-notes/${admNo}`),
  addProgressNote: (admNo: string, data: any) => api.post<any>(`/ipd/doctor/progress-notes/${admNo}`, data),
  
  getClinicalProcedures: (admNo: string) => api.get<any[]>(`/ipd/doctor/clinical-procedures/${admNo}`),
  addClinicalProcedure: (admNo: string, data: any) => api.post<any>(`/ipd/doctor/clinical-procedures/${admNo}`, data),
  
  getConsultationRequests: (admNo: string) => api.get<any[]>(`/ipd/doctor/consultation-requests/${admNo}`),
  addConsultationRequest: (admNo: string, data: any) => api.post<any>(`/ipd/doctor/consultation-requests/${admNo}`, data),

  // --- Phase 18: IPD Clinical Orders Management Engine ---
  createLabOrder: (admNo: string, data: any) => api.post<any>(`/ipd/orders/lab/${admNo}`, data),
  createRadiologyOrder: (admNo: string, data: any) => api.post<any>(`/ipd/orders/radiology/${admNo}`, data),
  createMedicationOrder: (admNo: string, data: any) => api.post<any>(`/ipd/orders/medication/${admNo}`, data),
  createProcedureOrder: (admNo: string, data: any) => api.post<any>(`/ipd/orders/procedure/${admNo}`, data),
  getPatientOrders: (admNo: string) => api.get<any[]>(`/ipd/orders/${admNo}`),
  getOrderDetail: (orderId: string) => api.get<any>(`/ipd/orders/detail/${orderId}`),
  updateOrderStatus: (orderId: string, data: any) => api.put<any>(`/ipd/orders/status/${orderId}`, data),
  getNursingExecutionWorklist: () => api.get<any[]>('/ipd/orders-nursing/execution-worklist'),

  // --- Phase 19: IPD Bed Transfer & Patient Movement Engine ---
  createTransferRequest: (admNo: string, data: any) => api.post<any>(`/ipd/transfers/${admNo}`, data),
  getTransferRequests: (ward?: string) => api.get<any[]>(`/ipd/transfers/list${ward ? `?ward=${ward}` : ''}`),
  getTransferDetail: (reqId: string) => api.get<any>(`/ipd/transfers/detail/${reqId}`),
  approveTransfer: (reqId: string, data: any) => api.put<any>(`/ipd/transfers/${reqId}/approve`, data),
  rejectTransfer: (reqId: string, remarks: string) => api.put<any>(`/ipd/transfers/${reqId}/reject?remarks=${remarks}`, {}),
  
  // --- Phase 20: IPD Smart Discharge Planning Engine ---
  getDischargeState: (admNo: string) => api.get<any>(`/ipd/discharge/${admNo}`),
  updateDischargePlan: (admNo: string, data: any) => api.put<any>(`/ipd/discharge/${admNo}/plan`, data),
  updateDischargeChecklist: (admNo: string, data: any) => api.put<any>(`/ipd/discharge/${admNo}/checklist`, data),
  generateDischargeSummary: (admNo: string) => api.post<any>(`/ipd/discharge/${admNo}/summary/generate`, {}),
  updateDischargeSummary: (admNo: string, data: any) => api.put<any>(`/ipd/discharge/${admNo}/summary`, data),
  checkPendingOrders: (admNo: string) => api.get<any[]>(`/ipd/discharge/${admNo}/pending-orders`),
  finalizeDischarge: (admNo: string) => api.post<any>(`/ipd/discharge/${admNo}/finalize`, {}),

  // --- Phase 21: IPD Billing Engine ---
  getBillingDashboard: () => api.get<any[]>('/ipd/billing/dashboard'),
  getBillingMaster: (admNo: string) => api.get<any>(`/ipd/billing/${admNo}`),
  recalculateBill: (admNo: string) => api.post<any>(`/ipd/billing/${admNo}/recalculate`, {}),
  getBillingServices: (admNo: string) => api.get<any[]>(`/ipd/billing/${admNo}/services`),
  addBillingService: (admNo: string, data: any) => api.post<any>(`/ipd/billing/${admNo}/services`, data),
  getBillingDeposits: (admNo: string) => api.get<any[]>(`/ipd/billing/${admNo}/deposits`),
  addDeposit: (admNo: string, data: any) => api.post<any>(`/ipd/billing/${admNo}/deposits`, data),
  getInsuranceClaims: (admNo: string) => api.get<any[]>(`/ipd/billing/${admNo}/insurance`),
  addInsuranceClaim: (admNo: string, data: any) => api.post<any>(`/ipd/billing/${admNo}/insurance`, data),
  approveInsuranceClaim: (claimId: string, data: any) => api.post<any>(`/ipd/billing/insurance/${claimId}/approve`, data),
  getAvailableInsurance: (admNo: string) => api.get<any[]>(`/ipd/billing/${admNo}/available-insurance`),
  getPayments: (admNo: string) => api.get<any[]>(`/ipd/billing/${admNo}/payments`),
  addPayment: (admNo: string, data: any) => api.post<any>(`/ipd/billing/${admNo}/payments`, data),

  // Phase 22: Visitor Management & MLC
  registerVisitor: (data: any) => api.post<any>('/ipd/visitors', data),
  getVisitors: (admNo: string) => api.get<any[]>(`/ipd/visitors/${admNo}`),
  generateVisitorPass: (data: any) => api.post<any>('/ipd/visitor-passes', data),
  getVisitorPasses: (admNo: string) => api.get<any[]>(`/ipd/visitor-passes/${admNo}`),
  logVisitorEntry: (data: any) => api.post<any>('/ipd/visitor-logs/entry', data),
  logVisitorExit: (logId: string) => api.put<any>(`/ipd/visitor-logs/${logId}/exit`, {}),
  getVisitorLogs: (passNo: string) => api.get<any[]>(`/ipd/visitor-logs/${passNo}`),
  registerMlcCase: (data: any) => api.post<any>('/ipd/mlc', data),
  getAllMlcCases: () => api.get<any[]>('/ipd/mlc'),
  getMlcCase: (admNo: string) => api.get<any>(`/ipd/mlc/${admNo}`),
  updateMlcCase: (admNo: string, data: any) => api.put<any>(`/ipd/mlc/${admNo}`, data),
  addMlcDocument: (data: any) => api.post<any>('/ipd/mlc-documents', data),
  getMlcDocuments: (mlcId: string) => api.get<any[]>(`/ipd/mlc-documents/${mlcId}`),
  getSecurityNotifications: (filter?: string) => api.get<any[]>(`/ipd/security-notifications${filter ? `?read_filter=${filter}` : ''}`),
  markNotificationRead: (id: string) => api.put<any>(`/ipd/security-notifications/${id}/read`, {}),
  
  // Consent Management
  getConsentTemplates: (type?: string) => api.get<any[]>(`/ipd/consent-templates${type ? `?consent_type=${type}` : ''}`),
  createConsentTemplate: (data: any) => api.post<any>('/ipd/consent-templates', data),
};
