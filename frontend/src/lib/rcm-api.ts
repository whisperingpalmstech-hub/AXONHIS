import { api } from "./api";

export interface TariffQuery {
  service_name: string;
  patient_category: string;
  doctor_grade?: string;
  insurance_plan?: string;
}

export interface BillingService {
  service_name: string;
  department?: string;
  sub_department?: string;
  quantity: number;
}

export const rcmApi = {
  // 1 Pre-Consult Billing Preview
  getCostEstimate: (query: TariffQuery) => api.post(`/rcm-billing/preview`, query),

  // 10 Analytics
  getDailyRevenue: () => api.get(`/rcm-billing/analytics/daily-revenue`),

  // Bill Workflows
  initializeBill: (data: any) => api.post(`/rcm-billing/master?authorized_user_id=11111111-1111-1111-1111-111111111111`, data),
  getBillInfo: (visitId: string, patientId?: string) => 
    api.get(`/rcm-billing/master/${visitId}${patientId ? `?patient_id=${patientId}` : ''}`),
  
  // Appends
  addService: (billId: string, svc: any) => api.post(`/rcm-billing/master/${billId}/services`, svc),
  applyDiscount: (billId: string, disc: any) => api.post(`/rcm-billing/master/${billId}/discounts?admin_id=11111111-1111-1111-1111-111111111111`, disc),
  
  // Terminal Payments
  collectPayment: (billId: string, pmt: any) => api.post(`/rcm-billing/master/${billId}/payments?cashier_id=11111111-1111-1111-1111-111111111111`, pmt),
  issueRefund: (billId: string, ref: any) => api.post(`/rcm-billing/master/${billId}/refunds?auth_id=11111111-1111-1111-1111-111111111111`, ref),
};
