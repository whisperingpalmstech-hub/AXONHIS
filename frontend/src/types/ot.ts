export enum OperatingRoomStatus {
  AVAILABLE = "available",
  OCCUPIED = "occupied",
  CLEANING = "cleaning",
  MAINTENANCE = "maintenance"
}

export interface OperatingRoom {
  id: string;
  room_code: string;
  room_name: string;
  department: string;
  equipment_profile?: any;
  status: OperatingRoomStatus;
}

export enum SurgeryPriority {
  ELECTIVE = "elective",
  URGENT = "urgent",
  EMERGENCY = "emergency"
}

export enum SurgeryStatus {
  SCHEDULED = "scheduled",
  PREPARING = "preparing",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  CANCELLED = "cancelled"
}

export interface SurgicalProcedure {
  id: string;
  procedure_code: string;
  procedure_name: string;
  specialty: string;
  expected_duration: number;
}

export interface SurgerySchedule {
  id: string;
  patient_id: string;
  encounter_id: string;
  procedure_id: string;
  operating_room_id: string;
  scheduled_start_time: string;
  scheduled_end_time: string;
  priority: SurgeryPriority;
  status: SurgeryStatus;
  scheduled_by?: string;
  created_at: string;
  
  // Relations (optional for summary view)
  procedure?: SurgicalProcedure;
  room?: OperatingRoom;
  patient?: any;
}

export enum AnesthesiaType {
  GENERAL = "general",
  REGIONAL = "regional",
  LOCAL = "local",
  SEDATION = "sedation"
}

export interface AnesthesiaRecord {
  id: string;
  schedule_id: string;
  anesthesia_type: AnesthesiaType;
  anesthesia_start_time: string;
  anesthesia_end_time?: string;
  anesthesiologist_id: string;
  notes?: string;
}

export enum SurgeryEventType {
  PATIENT_IN_ROOM = "patient_in_room",
  ANESTHESIA_STARTED = "anesthesia_started",
  INCISION_MADE = "incision_made",
  PROCEDURE_COMPLETED = "procedure_completed",
  PATIENT_OUT_ROOM = "patient_out_room"
}

export interface SurgeryEvent {
  id: string;
  schedule_id: string;
  event_type: SurgeryEventType;
  event_time: string;
  recorded_by: string;
}

export interface OTDashboardSummary {
  today_count: number;
  today_surgeries?: SurgerySchedule[];
  room_usage: { id: string; code: string; name: string; status: string }[];
  upcoming: SurgerySchedule[];
  delayed: SurgerySchedule[];
  emergency: SurgerySchedule[];
}
