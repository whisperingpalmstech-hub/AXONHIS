import { api } from "./api";
import { 
  OperatingRoom, 
  SurgicalProcedure, 
  SurgerySchedule, 
  AnesthesiaRecord, 
  SurgeryEvent, 
  OTDashboardSummary 
} from "../types/ot";

export const otApi = {
  // Operating Rooms
  getRooms: () => api.get<OperatingRoom[]>("/ot/rooms/"),
  getRoom: (id: string) => api.get<OperatingRoom>(`/ot/rooms/${id}`),
  createRoom: (data: any) => api.post<OperatingRoom>("/ot/rooms/", data),

  // Procedures
  getProcedures: () => api.get<SurgicalProcedure[]>("/ot/procedures/"),
  getProcedure: (id: string) => api.get<SurgicalProcedure>(`/ot/procedures/${id}`),
  createProcedure: (data: any) => api.post<SurgicalProcedure>("/ot/procedures/", data),

  // Schedule
  getSchedules: () => api.get<SurgerySchedule[]>("/ot/schedule/"),
  getSchedule: (id: string) => api.get<SurgerySchedule>(`/ot/schedule/${id}`),
  scheduleSurgery: (data: any) => api.post<SurgerySchedule>("/ot/schedule/", data),
  updateSchedule: (id: string, data: any) => api.put<SurgerySchedule>(`/ot/schedule/${id}`, data),
  cancelSurgery: (id: string) => api.delete(`/ot/schedule/${id}`),

  // Team
  getTeam: (scheduleId: string) => api.get<any>(`/ot/team/${scheduleId}`),
  assignTeam: (data: any) => api.post<any>("/ot/team/", data),

  // Anesthesia
  getAnesthesiaRecord: (scheduleId: string) => api.get<AnesthesiaRecord>(`/ot/anesthesia/${scheduleId}`),
  createAnesthesiaRecord: (data: any) => api.post<AnesthesiaRecord>("/ot/anesthesia/", data),

  // Events
  getEvents: (scheduleId: string) => api.get<SurgeryEvent[]>(`/ot/event/${scheduleId}`),
  recordEvent: (data: any) => api.post<SurgeryEvent>("/ot/event/", data),

  // Dashboard
  getDashboardSummary: () => api.get<OTDashboardSummary>("/ot/dashboard/"),

  // Notes
  getNotes: (scheduleId: string) => api.get<any[]>(`/ot/note/${scheduleId}`),
  createNote: (data: any) => api.post<any>("/ot/note/", data),
};
