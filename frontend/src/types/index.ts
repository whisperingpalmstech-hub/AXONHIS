/**
 * Shared TypeScript types for the AXONHIS frontend.
 */

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export type UserRole =
  | "DOCTOR"
  | "NURSE"
  | "LAB_TECH"
  | "PHARMACIST"
  | "ADMIN"
  | "BILLING";

export interface Patient {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  gender: string;
  phone: string | null;
  blood_group: string;
  allergies: string | null;
}

export interface Encounter {
  id: string;
  patient_id: string;
  encounter_type: "OPD" | "IPD" | "ER";
  status: "ACTIVE" | "DISCHARGED" | "TRANSFERRED" | "CANCELLED";
  doctor_id: string | null;
  chief_complaint: string | null;
  ward: string | null;
  room: string | null;
  bed: string | null;
  admitted_at: string;
  discharged_at: string | null;
}

export interface Order {
  id: string;
  encounter_id: string;
  patient_id: string;
  order_type: OrderType;
  status: OrderStatus;
  priority: "STAT" | "URGENT" | "ROUTINE";
  items: OrderItem[];
  created_at: string;
}

export type OrderType =
  | "LAB_ORDER"
  | "RADIOLOGY_ORDER"
  | "MEDICATION_ORDER"
  | "PROCEDURE_ORDER"
  | "NURSING_TASK"
  | "ADMISSION_ORDER"
  | "DISCHARGE_ORDER";

export type OrderStatus =
  | "DRAFT"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED";

export interface OrderItem {
  id: string;
  item_type: string;
  item_name: string;
  quantity: number;
  dose: string | null;
  frequency: string | null;
  route: string | null;
  unit_price: number;
}

export interface TimelineEvent {
  id: string;
  type: string;
  summary: string;
  occurred_at: string;
  payload: Record<string, unknown>;
}

export interface BillingEntry {
  id: string;
  encounter_id: string;
  order_id: string;
  description: string;
  amount: number;
  status: "ACTIVE" | "REVERSED";
}

export interface AISummary {
  encounter_id: string;
  narrative: string;
  active_problems: string[];
  active_medications: string[];
  risk_alerts: string[];
}
