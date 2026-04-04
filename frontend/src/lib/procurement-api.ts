import { api } from "./api";

const BASE = "/procurement";

export interface Vendor {
  id: string;
  vendor_code: string;
  name: string;
  contact_person: string;
  email: string;
  phone: string;
  address: string;
  tax_id: string;
  payment_terms: string;
  rating: number;
  is_active: boolean;
}

export interface PRItem {
  item_id: string;
  requested_qty: number;
  approved_qty?: number;
}

export interface PurchaseRequest {
  id: string;
  pr_number: string;
  requesting_store_id: string;
  delivery_store_id: string;
  priority: string;
  status: string;
  justification: string;
  created_at: string;
  items: PRItem[];
}

export interface POItem {
  item_id: string;
  ordered_qty: number;
  rate: number;
  tax_pct: number;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  vendor_id: string;
  total_amount: number;
  status: string;
  delivery_date: string;
  created_at: string;
  items: POItem[];
}

export interface GRNItem {
  id: string;
  po_item_id: string;
  item_id: string;
  received_qty: number;
  accepted_qty: number;
  rejected_qty: number;
  batch_number: string;
  inspection_remarks?: string;
}

export interface GRN {
  id: string;
  grn_number: string;
  po_id: string;
  vendor_id: string;
  store_id: string;
  invoice_number?: string;
  challan_number?: string;
  status: string;
  received_at: string;
  items: GRNItem[];
}

export const procurementApi = {
  getStores: () => api.get<any[]>(`${BASE}/utils/stores`),
  getItems: () => api.get<any[]>(`${BASE}/utils/items`),

  getVendors: () => api.get<Vendor[]>(`${BASE}/vendors`),
  createVendor: (data: Partial<Vendor>) => api.post<Vendor>(`${BASE}/vendors`, data),
  
  getPRs: () => api.get<PurchaseRequest[]>(`${BASE}/requests`),
  createPR: (data: any) => api.post<PurchaseRequest>(`${BASE}/requests`, data),
  approvePR: (pr_id: string) => api.post<PurchaseRequest>(`${BASE}/requests/${pr_id}/approve`),
  
  getPOs: () => api.get<PurchaseOrder[]>(`${BASE}/orders`),
  createPO: (data: any) => api.post<PurchaseOrder>(`${BASE}/orders`, data),
  
  getGRNs: () => api.get<GRN[]>(`${BASE}/grn`),
  createGRN: (data: any) => api.post<GRN>(`${BASE}/grn`, data),
  inspectGRN: (grn_id: string, inspections: any) => api.post<GRN>(`${BASE}/grn/${grn_id}/inspect`, inspections),
};
