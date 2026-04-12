import { api } from "./api";

export interface TestOrderItem {
  test_code: string;
  test_name: string;
  sample_type: string;
  priority: string;
  price: number;
  panel_id?: string;
  collection_location?: string;
  notes?: string;
}

export interface TestOrderCreate {
  patient_id: string;
  visit_id?: string;
  encounter_id?: string;
  ordering_doctor?: string;
  department_source: string;
  order_source: string;
  priority: string;
  clinical_indication?: string;
  provisional_diagnosis?: string;
  symptoms?: string;
  medication_history?: string;
  items: TestOrderItem[];
}

export interface TestOrderItemOut extends TestOrderItem {
  id: string;
  order_id: string;
  status: string;
  barcode?: string;
  created_at: string;
}

export interface TestOrderOut {
  id: string;
  order_number: string;
  patient_id: string;
  visit_id?: string;
  encounter_id?: string;
  ordering_doctor?: string;
  department_source: string;
  order_source: string;
  priority: string;
  status: string;
  clinical_indication?: string;
  provisional_diagnosis?: string;
  insurance_validated: boolean;
  created_at: string;
  confirmed_at?: string;
  completed_at?: string;
  items: TestOrderItemOut[];
}

export interface PanelOut {
  id: string;
  panel_code: string;
  panel_name: string;
  description?: string;
  category?: string;
  total_price: number;
  is_active: boolean;
  panel_items: { id: string; test_code: string; test_name: string; sample_type: string; price: number }[];
}

export interface PhlebotomyItem {
  order_id: string;
  order_number: string;
  patient_id: string;
  patient_name?: string;
  test_name: string;
  test_code: string;
  sample_type: string;
  priority: string;
  collection_location?: string;
  barcode?: string;
}

export const lisApi = {
  // Order CRUD
  createOrder: (data: TestOrderCreate) =>
    api.post<TestOrderOut>("/lis-orders/orders", data),
  getOrder: (orderId: string) =>
    api.get<TestOrderOut>(`/lis-orders/orders/${orderId}`),
  getPatientOrders: (patientId: string) =>
    api.get<TestOrderOut[]>(`/lis-orders/orders/patient/${patientId}`),

  // Order operations
  addItems: (orderId: string, items: TestOrderItem[]) =>
    api.post<TestOrderOut>(`/lis-orders/orders/${orderId}/items`, { items }),
  addPanel: (orderId: string, panelId: string) =>
    api.post<TestOrderOut>(`/lis-orders/orders/${orderId}/panel`, { panel_id: panelId }),
  confirmOrder: (orderId: string) =>
    api.post<TestOrderOut>(`/lis-orders/orders/${orderId}/confirm`),
  cancelOrder: (orderId: string, reason: string) =>
    api.post<TestOrderOut>(`/lis-orders/orders/${orderId}/cancel`, { reason }),

  // Prescription scan
  scanPrescription: (text: string) =>
    api.post<{ detected_tests: string[]; ocr_text: string; confidence: number }>(
      `/lis-orders/prescription-scan?text=${encodeURIComponent(text)}`
    ),

  // Panels
  listPanels: () => api.get<PanelOut[]>("/lis-orders/panels"),
  getPanel: (panelId: string) => api.get<PanelOut>(`/lis-orders/panels/${panelId}`),
  createPanel: (data: any) => api.post<PanelOut>("/lis-orders/panels", data),

  // Phlebotomy worklist
  getPhlebotomyWorklist: () => api.get<PhlebotomyItem[]>("/lis-orders/phlebotomy-worklist"),
};
