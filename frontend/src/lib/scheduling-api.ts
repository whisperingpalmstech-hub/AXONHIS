/**
 * Enterprise Scheduling API Client
 * Covers: Doctor calendars, slots, bookings, overbooking, cyclic schedules,
 *         modality scheduling, reminders, follow-ups, workload, analytics
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
const PREFIX = "/api/v1/scheduling";

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return { ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${PREFIX}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...opts.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

// ── Types ───────────────────────────────────────────────────────────────────

export interface DoctorCalendar {
  id: string; doctor_id: string; department: string;
  default_slot_duration_min: number; max_patients_per_slot: number;
  allow_teleconsultation: boolean; allow_overbooking: boolean;
  max_overbook_count: number; buffer_between_slots_min: number;
  is_active: boolean; created_at: string;
}

export interface CalendarSlot {
  id: string; calendar_id: string; doctor_id: string;
  slot_date: string; start_time: string; end_time: string;
  status: string; appointment_type: string;
  current_bookings: number; max_bookings: number;
  is_emergency_override: boolean; notes: string | null;
  created_at: string;
}

export interface SlotBooking {
  id: string; slot_id: string; patient_id: string; doctor_id: string;
  department: string; booking_date: string; appointment_type: string;
  status: string; reason: string | null; qr_code_data: string | null;
  check_in_time: string | null; completion_time: string | null;
  is_follow_up: boolean; parent_booking_id: string | null;
  created_at: string;
}

export interface OverbookingConfig {
  id: string; doctor_id: string | null; department: string | null;
  max_overbook_per_slot: number; max_overbook_per_day: number;
  priority_threshold: number; allow_emergency_override: boolean;
  is_active: boolean; created_at: string;
}

export interface CyclicSchedule {
  id: string; calendar_id: string; doctor_id: string;
  day_of_week: string; start_time: string; end_time: string;
  slot_duration_min: number; appointment_type: string;
  max_patients_per_slot: number; is_active: boolean;
  effective_from: string; effective_until: string | null;
}

export interface ModalityResource {
  id: string; modality_type: string; name: string;
  location: string | null; department: string;
  is_active: boolean; max_slots_per_day: number;
  slot_duration_min: number; buffer_min: number;
  operating_start: string; operating_end: string;
  created_at: string;
}

export interface ModalitySlot {
  id: string; resource_id: string; slot_date: string;
  start_time: string; end_time: string; status: string;
  patient_id: string | null; imaging_order_id: string | null;
  technician_id: string | null; notes: string | null;
  created_at: string;
}

export interface SchedulingAnalytics {
  id: string; analytics_date: string; doctor_id: string | null;
  department: string | null;
  total_slots: number; booked_slots: number; available_slots: number;
  blocked_slots: number; overbooked_slots: number;
  total_appointments: number; completed_appointments: number;
  cancelled_appointments: number; no_show_count: number;
  slot_utilization_pct: number; doctor_utilization_pct: number;
  no_show_rate_pct: number; avg_wait_time_min: number | null;
  modality_type: string | null; computed_at: string;
}

export interface AnalyticsSummary {
  period_start: string; period_end: string;
  total_appointments: number; completed: number;
  cancelled: number; no_shows: number;
  no_show_rate_pct: number; avg_slot_utilization_pct: number;
  avg_doctor_utilization_pct: number;
}

// ── API ─────────────────────────────────────────────────────────────────────

export const schedulingApi = {
  // Doctor Calendars
  createCalendar: (data: any) => req<DoctorCalendar>("/calendars", { method: "POST", body: JSON.stringify(data) }),
  listCalendars: (department?: string) => req<DoctorCalendar[]>(`/calendars${department ? `?department=${department}` : ""}`),
  getCalendar: (id: string) => req<DoctorCalendar>(`/calendars/${id}`),
  getDoctorCalendar: (doctorId: string) => req<DoctorCalendar>(`/calendars/doctor/${doctorId}`),
  updateCalendar: (id: string, data: any) => req<DoctorCalendar>(`/calendars/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  // Slots
  createSlot: (data: any) => req<CalendarSlot>("/slots", { method: "POST", body: JSON.stringify(data) }),
  generateSlots: (data: any) => req<CalendarSlot[]>("/slots/generate", { method: "POST", body: JSON.stringify(data) }),
  getDoctorSlots: (doctorId: string, slotDate: string, status?: string) =>
    req<CalendarSlot[]>(`/slots/doctor/${doctorId}?slot_date=${slotDate}${status ? `&status=${status}` : ""}`),
  getAvailableSlots: (doctorId: string, from: string, to: string) =>
    req<CalendarSlot[]>(`/slots/available/${doctorId}?from_date=${from}&to_date=${to}`),
  updateSlotStatus: (slotId: string, data: { status: string; notes?: string }) =>
    req<CalendarSlot>(`/slots/${slotId}/status`, { method: "PUT", body: JSON.stringify(data) }),

  // Bookings
  createBooking: (data: any) => req<SlotBooking>("/bookings", { method: "POST", body: JSON.stringify(data) }),
  emergencyOverride: (data: any) => req<SlotBooking>("/bookings/emergency", { method: "POST", body: JSON.stringify(data) }),
  getBooking: (id: string) => req<SlotBooking>(`/bookings/${id}`),
  updateBooking: (id: string, data: any) => req<SlotBooking>(`/bookings/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  listBookings: (params: { doctor_id?: string; patient_id?: string; from_date?: string; to_date?: string; status?: string }) => {
    const qs = Object.entries(params).filter(([, v]) => v).map(([k, v]) => `${k}=${v}`).join("&");
    return req<SlotBooking[]>(`/bookings${qs ? `?${qs}` : ""}`);
  },

  // Overbooking
  createOverbookingConfig: (data: any) => req<OverbookingConfig>("/overbooking", { method: "POST", body: JSON.stringify(data) }),
  listOverbookingConfigs: () => req<OverbookingConfig[]>("/overbooking"),

  // Cyclic Schedules
  createCyclicSchedule: (data: any) => req<CyclicSchedule>("/cyclic-schedules", { method: "POST", body: JSON.stringify(data) }),
  listCyclicSchedules: (calendarId: string) => req<CyclicSchedule[]>(`/cyclic-schedules/${calendarId}`),
  deactivateCyclicSchedule: (id: string) => req<void>(`/cyclic-schedules/${id}`, { method: "DELETE" }),

  // Modality
  createModalityResource: (data: any) => req<ModalityResource>("/modalities/resources", { method: "POST", body: JSON.stringify(data) }),
  listModalityResources: (type?: string) => req<ModalityResource[]>(`/modalities/resources${type ? `?modality_type=${type}` : ""}`),
  generateModalitySlots: (data: any) => req<ModalitySlot[]>("/modalities/slots/generate", { method: "POST", body: JSON.stringify(data) }),
  getModalitySlots: (resourceId: string, slotDate: string) =>
    req<ModalitySlot[]>(`/modalities/slots/${resourceId}?slot_date=${slotDate}`),
  bookModalitySlot: (data: any) => req<ModalitySlot>("/modalities/slots/book", { method: "POST", body: JSON.stringify(data) }),

  // Reminders
  createReminder: (data: any) => req<any>("/reminders", { method: "POST", body: JSON.stringify(data) }),
  listReminders: (bookingId: string) => req<any[]>(`/reminders/${bookingId}`),

  // Follow-ups
  createFollowUpRule: (data: any) => req<any>("/follow-up-rules", { method: "POST", body: JSON.stringify(data) }),
  listFollowUpRules: (department?: string) => req<any[]>(`/follow-up-rules${department ? `?department=${department}` : ""}`),
  scheduleFollowUp: (bookingId: string, department: string) =>
    req<SlotBooking>(`/follow-up/${bookingId}/schedule?department=${department}`, { method: "POST" }),

  // Workload
  getWorkload: (department: string, targetDate: string) =>
    req<any[]>(`/workload/${department}?target_date=${targetDate}`),
  suggestDoctor: (department: string, targetDate: string) =>
    req<{ suggested_doctor_id: string }>(`/workload/${department}/suggest-doctor?target_date=${targetDate}`),

  // Analytics
  computeAnalytics: (targetDate: string, doctorId?: string) =>
    req<SchedulingAnalytics>(`/analytics/compute?target_date=${targetDate}${doctorId ? `&doctor_id=${doctorId}` : ""}`, { method: "POST" }),
  getAnalytics: (from: string, to: string, doctorId?: string) =>
    req<SchedulingAnalytics[]>(`/analytics?from_date=${from}&to_date=${to}${doctorId ? `&doctor_id=${doctorId}` : ""}`),
  getAnalyticsSummary: (from: string, to: string) =>
    req<AnalyticsSummary>(`/analytics/summary?from_date=${from}&to_date=${to}`),
};
