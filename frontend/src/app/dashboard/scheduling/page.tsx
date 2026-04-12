"use client";
import React, { useState, useEffect } from "react";
import { useTranslation } from "@/i18n";
import {
  Calendar, Clock, User, Users, AlertTriangle, Check, X,
  Activity, BarChart3, Zap, Settings, Plus, ChevronDown,
  Monitor, ArrowRight, ArrowLeft, RefreshCw, Loader2, QrCode,
  Bell, Repeat, Shield, Brain, Eye, Stethoscope, Scan,
  TrendingUp, TrendingDown, Percent, Timer
} from "lucide-react";
import {
  schedulingApi,
  type DoctorCalendar,
  type CalendarSlot,
  type SlotBooking,
  type CyclicSchedule,
  type ModalityResource,
  type ModalitySlot,
  type SchedulingAnalytics,
  type AnalyticsSummary,
} from "@/lib/scheduling-api";
import { api } from "@/lib/api";

interface UserRecord { id: string; full_name: string; email: string; role?: string; }
interface PatientRecord { id: string; first_name: string; last_name: string; uhid?: string; }

/* ═══════════════════════════════════════════════════════════════════════════
   ENTERPRISE APPOINTMENT SCHEDULING
   ═══════════════════════════════════════════════════════════════════════════ */



const SLOT_COLORS: Record<string, string> = {
  available: "bg-emerald-100 text-emerald-800 border-emerald-300",
  booked: "bg-blue-100 text-blue-800 border-blue-300",
  blocked: "bg-slate-200 text-slate-600 border-slate-300",
  overbooked: "bg-amber-100 text-amber-800 border-amber-300",
};

const STATUS_BADGE: Record<string, string> = {
  confirmed: "bg-blue-100 text-blue-700",
  checked_in: "bg-purple-100 text-purple-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
  no_show: "bg-orange-100 text-orange-700",
};

const MODALITY_ICONS: Record<string, string> = {
  mri: "🧲", ct: "🔬", xray: "☢️", ultrasound: "📡",
};

export default function EnterpriseSchedulingPage() {
  const { t } = useTranslation();
  const TABS = [
    { id: "calendar", label: t("scheduling.doctorCalendar"), icon: <Calendar size={16} /> },
    { id: "bookings", label: t("scheduling.bookings"), icon: <Clock size={16} /> },
    { id: "modalities", label: t("scheduling.modalityScheduling"), icon: <Scan size={16} /> },
    { id: "analytics", label: t("scheduling.analytics"), icon: <BarChart3 size={16} /> },
    { id: "config", label: t("scheduling.configuration"), icon: <Settings size={16} /> },
  ] as const;
  type TabId = typeof TABS[number]["id"];

  const [activeTab, setActiveTab] = useState<TabId>("calendar");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Calendar state
  const [calendars, setCalendars] = useState<DoctorCalendar[]>([]);
  const [selectedCalendar, setSelectedCalendar] = useState<DoctorCalendar | null>(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
  const [slots, setSlots] = useState<CalendarSlot[]>([]);
  const [cyclicSchedules, setCyclicSchedules] = useState<CyclicSchedule[]>([]);

  // Booking state
  const [bookings, setBookings] = useState<SlotBooking[]>([]);
  const [bookingFilter, setBookingFilter] = useState<"all" | "confirmed" | "completed" | "cancelled" | "no_show">("all");

  // Modality state
  const [modalityResources, setModalityResources] = useState<ModalityResource[]>([]);
  const [selectedModality, setSelectedModality] = useState<string>("mri");
  const [selectedResource, setSelectedResource] = useState<ModalityResource | null>(null);
  const [modalitySlots, setModalitySlots] = useState<ModalitySlot[]>([]);

  // Analytics state
  const [analyticsSummary, setAnalyticsSummary] = useState<AnalyticsSummary | null>(null);
  const [analyticsData, setAnalyticsData] = useState<SchedulingAnalytics[]>([]);

  // Modals
  const [showNewCalModal, setShowNewCalModal] = useState(false);
  const [showBookModal, setShowBookModal] = useState(false);
  const [showCyclicModal, setShowCyclicModal] = useState(false);
  const [showResourceModal, setShowResourceModal] = useState(false);
  const [showOverbookModal, setShowOverbookModal] = useState(false);
  const [showFollowUpModal, setShowFollowUpModal] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<CalendarSlot | null>(null);

  // Doctors & Patients from DB
  const [doctors, setDoctors] = useState<UserRecord[]>([]);
  const [patients, setPatients] = useState<PatientRecord[]>([]);

  // New calendar form
  const [newCal, setNewCal] = useState({ doctor_id: "", department: "", default_slot_duration_min: 15, max_patients_per_slot: 1, allow_teleconsultation: true, allow_overbooking: false, max_overbook_count: 2, buffer_between_slots_min: 5 });
  // New cyclic schedule form
  const [newCyclic, setNewCyclic] = useState({ day_of_week: "mon", start_time: "09:00", end_time: "17:00", slot_duration_min: 15, appointment_type: "in_person", max_patients_per_slot: 1, effective_from: new Date().toISOString().split("T")[0], effective_until: "" });
  // Booking form
  const [bookForm, setBookForm] = useState({ patient_id: "", department: "", appointment_type: "in_person", reason: "" });
  // New resource form
  const [newResource, setNewResource] = useState({ modality_type: "mri", name: "", location: "", slot_duration_min: 30, buffer_min: 10, operating_start: "08:00", operating_end: "20:00" });
  // Config forms
  const [newOverbook, setNewOverbook] = useState({ doctor_id: "", department: "", max_overbook_per_slot: 2, max_overbook_per_day: 10, priority_threshold: 3, allow_emergency_override: true });
  const [newFollowUp, setNewFollowUp] = useState({ department: "", diagnosis_code: "", follow_up_days: 14, max_follow_ups: 3, is_active: true });

  // ── Load data ──
  useEffect(() => { loadCalendars(); loadDoctorsAndPatients(); }, []);

  const loadDoctorsAndPatients = async () => {
    try {
      const u = await api.get<any>("/auth/users");
      const items = Array.isArray(u) ? u : (u?.items || []);
      setDoctors(items);
    } catch {}
    try {
      const p = await api.get<any>("/patients");
      const items = Array.isArray(p) ? p : (p?.items || []);
      setPatients(items);
    } catch {}
  };

  const getDoctorName = (id: string) => {
    const doc = doctors.find(d => d.id === id);
    return doc ? doc.full_name : id.slice(0, 8) + "...";
  };
  const getPatientName = (id: string) => {
    const pt = patients.find(p => p.id === id);
    return pt ? `${pt.first_name} ${pt.last_name}` : id.slice(0, 8) + "...";
  };
  useEffect(() => { if (activeTab === "bookings") loadBookings(); }, [activeTab, bookingFilter]);
  useEffect(() => { if (activeTab === "modalities") loadResources(); }, [activeTab, selectedModality]);
  useEffect(() => { if (activeTab === "analytics") loadAnalytics(); }, [activeTab]);
  useEffect(() => { if (selectedCalendar) loadSlots(); }, [selectedCalendar, selectedDate]);
  useEffect(() => { if (selectedResource) loadModalitySlots(); }, [selectedResource, selectedDate]);

  const loadCalendars = async () => {
    try { const cals = await schedulingApi.listCalendars(); setCalendars(cals); } catch {}
  };

  const loadSlots = async () => {
    if (!selectedCalendar) return;
    try { const s = await schedulingApi.getDoctorSlots(selectedCalendar.doctor_id, selectedDate); setSlots(s); } catch {}
  };

  const loadBookings = async () => {
    try {
      const params: any = {};
      if (bookingFilter !== "all") params.status = bookingFilter;
      const b = await schedulingApi.listBookings(params);
      setBookings(b);
    } catch {}
  };

  const loadResources = async () => {
    try { const r = await schedulingApi.listModalityResources(selectedModality); setModalityResources(r); } catch {}
  };

  const loadModalitySlots = async () => {
    if (!selectedResource) return;
    try { const s = await schedulingApi.getModalitySlots(selectedResource.id, selectedDate); setModalitySlots(s); } catch {}
  };

  const loadAnalytics = async () => {
    const today = new Date();
    const from = new Date(today); from.setDate(from.getDate() - 30);
    try {
      const summary = await schedulingApi.getAnalyticsSummary(from.toISOString().split("T")[0], today.toISOString().split("T")[0]);
      setAnalyticsSummary(summary);
      const data = await schedulingApi.getAnalytics(from.toISOString().split("T")[0], today.toISOString().split("T")[0]);
      setAnalyticsData(data);
    } catch {}
  };

  // ── Actions ──
  const createCalendar = async () => {
    setLoading(true);
    try {
      await schedulingApi.createCalendar(newCal);
      setShowNewCalModal(false);
      loadCalendars();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const createCyclicSchedule = async () => {
    if (!selectedCalendar) return;
    setLoading(true);
    try {
      await schedulingApi.createCyclicSchedule({
        ...newCyclic, calendar_id: selectedCalendar.id, doctor_id: selectedCalendar.doctor_id,
        effective_until: newCyclic.effective_until || null,
      });
      setShowCyclicModal(false);
      const schedules = await schedulingApi.listCyclicSchedules(selectedCalendar.id);
      setCyclicSchedules(schedules);
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const generateWeekSlots = async () => {
    if (!selectedCalendar) return;
    setLoading(true);
    try {
      const end = new Date(selectedDate); end.setDate(end.getDate() + 7);
      await schedulingApi.generateSlots({
        calendar_id: selectedCalendar.id, doctor_id: selectedCalendar.doctor_id,
        start_date: selectedDate, end_date: end.toISOString().split("T")[0],
      });
      loadSlots();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const bookSlot = async () => {
    if (!selectedSlot) return;
    setLoading(true);
    try {
      await schedulingApi.createBooking({
        slot_id: selectedSlot.id, doctor_id: selectedSlot.doctor_id,
        ...bookForm, booking_date: selectedSlot.slot_date,
      });
      setShowBookModal(false);
      setSelectedSlot(null);
      loadSlots();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const updateBookingStatus = async (bookingId: string, status: string) => {
    try { await schedulingApi.updateBooking(bookingId, { status }); loadBookings(); } catch (e: any) { setError(e.message); }
  };

  const toggleSlotBlock = async (slot: CalendarSlot) => {
    try {
      await schedulingApi.updateSlotStatus(slot.id, { status: slot.status === "blocked" ? "available" : "blocked" });
      loadSlots();
    } catch (e: any) { setError(e.message); }
  };

  const createResource = async () => {
    setLoading(true);
    try {
      await schedulingApi.createModalityResource(newResource);
      setShowResourceModal(false);
      loadResources();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const createOverbookingRule = async () => {
    setLoading(true);
    try {
      await schedulingApi.createOverbookingConfig(newOverbook);
      setShowOverbookModal(false);
      setError("");
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const createFollowUpRule = async () => {
    setLoading(true);
    try {
      await schedulingApi.createFollowUpRule(newFollowUp);
      setShowFollowUpModal(false);
      setError("");
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const generateResourceSlots = async () => {
    if (!selectedResource) return;
    setLoading(true);
    try {
      const end = new Date(selectedDate); end.setDate(end.getDate() + 7);
      await schedulingApi.generateModalitySlots({
        resource_id: selectedResource.id,
        start_date: selectedDate, end_date: end.toISOString().split("T")[0],
      });
      loadModalitySlots();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ── Date nav helpers ──
  const prevDay = () => { const d = new Date(selectedDate); d.setDate(d.getDate() - 1); setSelectedDate(d.toISOString().split("T")[0]); };
  const nextDay = () => { const d = new Date(selectedDate); d.setDate(d.getDate() + 1); setSelectedDate(d.toISOString().split("T")[0]); };
  const formatTime = (t: string) => t?.slice(0, 5);

  // ═══════════════════════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════════════════════
  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] flex items-center gap-3">
          <div className="bg-gradient-to-br from-indigo-500 to-violet-600 p-2.5 rounded-xl text-white shadow-lg">
            <Calendar size={24} />
          </div>
          {t("scheduling.title")}
        </h1>
        <p className="text-[var(--text-secondary)] mt-2 text-sm">
          {t("scheduling.subtitle")}
        </p>
      </div>

      {error && (
        <div className="p-3 mb-4 bg-red-50 text-red-600 rounded-xl text-sm font-medium border border-red-200 flex items-center gap-2">
          <AlertTriangle size={16} /> {error}
          <button onClick={() => setError("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-1 mb-6 bg-[var(--bg-secondary)] p-1 rounded-xl">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === tab.id
                ? "bg-white text-[var(--text-primary)] shadow-sm"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* ═════════ TAB: Doctor Calendar ═════════ */}
      {activeTab === "calendar" && (
        <div className="flex gap-6">
          {/* Sidebar: Calendar list */}
          <div className="w-72 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-[var(--text-secondary)]">{t("scheduling.doctorCalendarsTitle")}</h3>
              <button onClick={() => setShowNewCalModal(true)} className="text-[var(--accent-primary)] hover:bg-blue-50 p-1.5 rounded-lg">
                <Plus size={16} />
              </button>
            </div>
            {calendars.length === 0 ? (
              <p className="text-xs text-slate-400 p-4 text-center">{t("scheduling.noCalendars")}</p>
            ) : (
              calendars.map(cal => (
                <button key={cal.id} onClick={() => { setSelectedCalendar(cal); schedulingApi.listCyclicSchedules(cal.id).then(setCyclicSchedules).catch(() => {}); }}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    selectedCalendar?.id === cal.id
                      ? "border-indigo-300 bg-indigo-50 ring-2 ring-indigo-200"
                      : "border-[var(--border)] bg-white hover:border-indigo-200"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <User size={14} className="text-indigo-500" />
                    <span className="font-semibold text-sm truncate">{getDoctorName(cal.doctor_id)}</span>
                  </div>
                  <div className="text-xs text-slate-500">{cal.department}</div>
                  <div className="flex gap-2 mt-2">
                    {cal.allow_teleconsultation && <span className="text-[9px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">Teleconsult</span>}
                    {cal.allow_overbooking && <span className="text-[9px] bg-amber-50 text-amber-600 px-1.5 py-0.5 rounded">Overbook</span>}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Main: Slots view */}
          <div className="flex-1">
            {selectedCalendar ? (
              <>
                {/* Date navigation */}
                <div className="flex items-center gap-3 mb-4">
                  <button onClick={prevDay} className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-slate-200"><ArrowLeft size={16} /></button>
                  <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)}
                    className="input-field w-auto font-semibold" />
                  <button onClick={nextDay} className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-slate-200"><ArrowRight size={16} /></button>
                  <div className="flex-1" />
                  <button onClick={() => setShowCyclicModal(true)} className="btn-secondary text-xs flex items-center gap-1">
                    <Repeat size={14} /> Cyclic Schedule
                  </button>
                  <button onClick={generateWeekSlots} disabled={loading} className="btn-primary text-xs flex items-center gap-1">
                    {loading ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />} Generate 7-Day Slots
                  </button>
                </div>

                {/* Slot Grid */}
                {slots.length === 0 ? (
                  <div className="text-center py-16 text-slate-400">
                    <Calendar size={48} className="mx-auto mb-3 opacity-50" />
                    <p className="font-medium">No slots for this date</p>
                    <p className="text-xs mt-1">Create a cyclic schedule and generate slots</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-4 xl:grid-cols-6 gap-2">
                    {slots.map(slot => (
                      <div key={slot.id}
                        className={`p-3 rounded-xl border cursor-pointer transition-all hover:shadow-md ${SLOT_COLORS[slot.status] || SLOT_COLORS.available}`}
                        onClick={() => { if (slot.status === "available") { setSelectedSlot(slot); setShowBookModal(true); } }}
                      >
                        <div className="font-bold text-sm">{formatTime(slot.start_time)}</div>
                        <div className="text-[10px] opacity-70">{formatTime(slot.end_time)}</div>
                        <div className="mt-1 flex items-center justify-between">
                          <span className="text-[9px] font-semibold uppercase">{slot.status}</span>
                          <span className="text-[9px]">{slot.current_bookings}/{slot.max_bookings}</span>
                        </div>
                        {slot.appointment_type === "teleconsultation" && <Monitor size={10} className="mt-1 opacity-60" />}
                        {slot.is_emergency_override && <Zap size={10} className="mt-1 text-red-500" />}
                        <div className="mt-1 flex gap-1">
                          <button onClick={e => { e.stopPropagation(); toggleSlotBlock(slot); }}
                            className="text-[9px] underline opacity-60 hover:opacity-100">
                            {slot.status === "blocked" ? "Unblock" : "Block"}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Cyclic Schedules Summary */}
                {cyclicSchedules.length > 0 && (
                  <div className="mt-6 card">
                    <div className="card-header border-b border-[var(--border)] flex items-center gap-2 text-sm">
                      <Repeat size={16} className="text-indigo-500" /> Active Cyclic Schedules
                    </div>
                    <div className="card-body">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        {cyclicSchedules.map(cs => (
                          <div key={cs.id} className="bg-indigo-50 rounded-lg p-2.5 text-xs">
                            <div className="font-bold text-indigo-800 uppercase">{cs.day_of_week}</div>
                            <div className="text-indigo-600">{formatTime(cs.start_time)} – {formatTime(cs.end_time)}</div>
                            <div className="text-slate-500 mt-1">{cs.slot_duration_min}min · {cs.max_patients_per_slot}pt/slot</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-20 text-slate-400">
                <Stethoscope size={48} className="mx-auto mb-3 opacity-50" />
                <p className="font-medium">{t("scheduling.selectDoctor")}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═════════ TAB: Bookings ═════════ */}
      {activeTab === "bookings" && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            {["all", "confirmed", "completed", "cancelled", "no_show"].map(f => (
              <button key={f} onClick={() => setBookingFilter(f as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  bookingFilter === f ? "bg-indigo-500 text-white" : "bg-[var(--bg-secondary)] text-[var(--text-secondary)]"
                }`}
              >
                {f === "all" ? "All" : f.replace("_", " ").replace(/^\w/, c => c.toUpperCase())}
              </button>
            ))}
            <div className="flex-1" />
            <button onClick={loadBookings} className="btn-secondary text-xs flex items-center gap-1">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>

          {bookings.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <Clock size={48} className="mx-auto mb-3 opacity-50" />
              <p>No bookings found</p>
            </div>
          ) : (
            <div className="space-y-2">
              {bookings.map(b => (
                <div key={b.id} className="card p-4 flex items-center gap-4">
                  <div className="flex-1 grid grid-cols-5 gap-3 text-sm">
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase">Patient</div>
                      <div className="font-semibold">{getPatientName(b.patient_id)}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase">Date</div>
                      <div className="font-medium">{b.booking_date}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase">Department</div>
                      <div>{b.department}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase">Type</div>
                      <div className="capitalize">{b.appointment_type.replace("_", " ")}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase">Status</div>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${STATUS_BADGE[b.status] || "bg-slate-100"}`}>
                        {b.status.replace("_", " ").toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {b.status === "confirmed" && (
                      <>
                        <button onClick={() => updateBookingStatus(b.id, "checked_in")} className="text-[10px] bg-purple-100 text-purple-700 px-2 py-1 rounded-lg hover:bg-purple-200">Check In</button>
                        <button onClick={() => updateBookingStatus(b.id, "no_show")} className="text-[10px] bg-orange-100 text-orange-700 px-2 py-1 rounded-lg hover:bg-orange-200">No Show</button>
                      </>
                    )}
                    {b.status === "checked_in" && (
                      <button onClick={() => updateBookingStatus(b.id, "completed")} className="text-[10px] bg-green-100 text-green-700 px-2 py-1 rounded-lg hover:bg-green-200">Complete</button>
                    )}
                    {["confirmed", "checked_in"].includes(b.status) && (
                      <button onClick={() => updateBookingStatus(b.id, "cancelled")} className="text-[10px] bg-red-100 text-red-700 px-2 py-1 rounded-lg hover:bg-red-200">Cancel</button>
                    )}
                    {b.qr_code_data && (
                      <button className="text-[10px] bg-slate-100 text-slate-600 px-2 py-1 rounded-lg" title="QR Slip">
                        <QrCode size={12} />
                      </button>
                    )}
                    {b.is_follow_up && <span className="text-[9px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded">Follow-up</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ═════════ TAB: Modality Scheduling ═════════ */}
      {activeTab === "modalities" && (
        <div>
          {/* Modality type pills */}
          <div className="flex items-center gap-2 mb-4">
            {(["mri", "ct", "xray", "ultrasound"] as const).map(m => (
              <button key={m} onClick={() => { setSelectedModality(m); setSelectedResource(null); }}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all border ${
                  selectedModality === m
                    ? "bg-gradient-to-r from-indigo-500 to-violet-600 text-white border-transparent"
                    : "bg-white border-[var(--border)] text-[var(--text-secondary)] hover:border-indigo-300"
                }`}
              >
                <span>{MODALITY_ICONS[m]}</span> {m.toUpperCase()}
              </button>
            ))}
            <div className="flex-1" />
            <button onClick={() => setShowResourceModal(true)} className="btn-primary text-xs flex items-center gap-1">
              <Plus size={14} /> Add Equipment
            </button>
          </div>

          <div className="flex gap-6">
            {/* Resource list */}
            <div className="w-64 space-y-2">
              {modalityResources.length === 0 ? (
                <p className="text-xs text-slate-400 p-4 text-center">No {selectedModality.toUpperCase()} equipment registered.</p>
              ) : (
                modalityResources.map(r => (
                  <button key={r.id} onClick={() => setSelectedResource(r)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      selectedResource?.id === r.id ? "border-violet-300 bg-violet-50 ring-2 ring-violet-200" : "border-[var(--border)] bg-white"
                    }`}
                  >
                    <div className="font-semibold text-sm">{r.name}</div>
                    <div className="text-[10px] text-slate-500">{r.location || "No location"}</div>
                    <div className="text-[10px] text-slate-400 mt-1">{r.slot_duration_min}min slots · {r.max_slots_per_day}/day</div>
                  </button>
                ))
              )}
            </div>

            {/* Modality slots */}
            <div className="flex-1">
              {selectedResource ? (
                <>
                  <div className="flex items-center gap-3 mb-4">
                    <button onClick={prevDay} className="p-2 rounded-lg bg-[var(--bg-secondary)]"><ArrowLeft size={16} /></button>
                    <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} className="input-field w-auto" />
                    <button onClick={nextDay} className="p-2 rounded-lg bg-[var(--bg-secondary)]"><ArrowRight size={16} /></button>
                    <div className="flex-1" />
                    <button onClick={generateResourceSlots} disabled={loading} className="btn-primary text-xs flex items-center gap-1">
                      {loading ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />} Generate 7-Day Slots
                    </button>
                  </div>
                  <div className="grid grid-cols-4 xl:grid-cols-6 gap-2">
                    {modalitySlots.map(s => (
                      <div key={s.id} className={`p-3 rounded-xl border ${SLOT_COLORS[s.status] || SLOT_COLORS.available}`}>
                        <div className="font-bold text-sm">{formatTime(s.start_time)}</div>
                        <div className="text-[10px] opacity-70">{formatTime(s.end_time)}</div>
                        <div className="text-[9px] font-semibold uppercase mt-1">{s.status}</div>
                        {s.patient_id && <div className="text-[9px] mt-1 opacity-60">Patient: {s.patient_id.slice(0, 6)}...</div>}
                      </div>
                    ))}
                    {modalitySlots.length === 0 && (
                      <div className="col-span-full text-center py-12 text-slate-400">No slots generated yet</div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-20 text-slate-400">
                  <Scan size={48} className="mx-auto mb-3 opacity-50" />
                  <p>Select equipment to view schedule</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═════════ TAB: Analytics ═════════ */}
      {activeTab === "analytics" && (
        <div>
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: "Total Appointments", value: analyticsSummary?.total_appointments || 0, icon: <Calendar size={20} />, color: "from-blue-500 to-indigo-600" },
              { label: "No-Show Rate", value: `${analyticsSummary?.no_show_rate_pct?.toFixed(1) || 0}%`, icon: <TrendingDown size={20} />, color: "from-orange-500 to-red-600" },
              { label: "Doctor Utilization", value: `${analyticsSummary?.avg_doctor_utilization_pct?.toFixed(1) || 0}%`, icon: <Activity size={20} />, color: "from-emerald-500 to-teal-600" },
              { label: "Slot Utilization", value: `${analyticsSummary?.avg_slot_utilization_pct?.toFixed(1) || 0}%`, icon: <Percent size={20} />, color: "from-purple-500 to-pink-600" },
            ].map((c, i) => (
              <div key={i} className="card overflow-hidden">
                <div className={`bg-gradient-to-r ${c.color} p-3 text-white flex items-center gap-2`}>
                  {c.icon}
                  <span className="text-xs font-medium">{c.label}</span>
                </div>
                <div className="p-4">
                  <div className="text-2xl font-bold">{c.value}</div>
                  <div className="text-[10px] text-slate-400 mt-1">Last 30 days</div>
                </div>
              </div>
            ))}
          </div>

          {/* Breakdown */}
          {analyticsSummary && (
            <div className="grid grid-cols-2 gap-4">
              <div className="card p-4">
                <h3 className="font-bold text-sm mb-3 flex items-center gap-2"><BarChart3 size={16} className="text-indigo-500" /> Appointment Breakdown</h3>
                <div className="space-y-2">
                  {[
                    { label: "Completed", val: analyticsSummary.completed, color: "bg-green-400" },
                    { label: "Cancelled", val: analyticsSummary.cancelled, color: "bg-red-400" },
                    { label: "No Shows", val: analyticsSummary.no_shows, color: "bg-orange-400" },
                  ].map((r, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${r.color}`} />
                      <span className="text-sm flex-1">{r.label}</span>
                      <span className="font-bold text-sm">{r.val}</span>
                      <div className="w-24 bg-slate-100 rounded-full h-2">
                        <div className={`h-2 rounded-full ${r.color}`}
                          style={{ width: `${analyticsSummary.total_appointments ? (r.val / analyticsSummary.total_appointments) * 100 : 0}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card p-4">
                <h3 className="font-bold text-sm mb-3 flex items-center gap-2"><TrendingUp size={16} className="text-emerald-500" /> Daily Trends</h3>
                {analyticsData.length === 0 ? (
                  <p className="text-xs text-slate-400">No analytics data yet. Compute analytics first.</p>
                ) : (
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {analyticsData.slice(-10).map((a, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs py-1 border-b border-slate-50">
                        <span className="text-slate-500 w-20">{a.analytics_date}</span>
                        <span className="font-medium">{a.total_appointments} appts</span>
                        <span className="text-green-600">{a.slot_utilization_pct.toFixed(0)}% util</span>
                        <span className="text-orange-600">{a.no_show_rate_pct.toFixed(0)}% no-show</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═════════ TAB: Configuration ═════════ */}
      {activeTab === "config" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card p-4">
            <h3 className="font-bold text-sm mb-3 flex items-center gap-2"><Shield size={16} className="text-amber-500" /> Overbooking Rules</h3>
            <p className="text-xs text-slate-500 mb-3">Configure per-doctor or per-department overbooking limits.</p>
            <button onClick={() => setShowOverbookModal(true)} className="btn-primary text-xs flex items-center gap-1"><Plus size={14} /> Add Rule</button>
          </div>
          <div className="card p-4">
            <h3 className="font-bold text-sm mb-3 flex items-center gap-2"><Repeat size={16} className="text-indigo-500" /> Follow-Up Rules</h3>
            <p className="text-xs text-slate-500 mb-3">Set automated follow-up scheduling per department / diagnosis.</p>
            <button onClick={() => setShowFollowUpModal(true)} className="btn-primary text-xs flex items-center gap-1"><Plus size={14} /> Add Rule</button>
          </div>
          <div className="card p-4">
            <h3 className="font-bold text-sm mb-3 flex items-center gap-2"><Bell size={16} className="text-purple-500" /> Reminder Settings</h3>
            <p className="text-xs text-slate-500 mb-3">Configure appointment reminder channels, timing, and templates.</p>
            <div className="space-y-2">
              {["24h Before (SMS)", "2h Before (WhatsApp)", "Follow-up Reminder (Email)"].map((r, i) => (
                <div key={i} className="flex items-center gap-2 bg-purple-50 p-2 rounded-lg text-xs text-purple-700">
                  <Check size={12} /> {r}
                </div>
              ))}
            </div>
          </div>
          <div className="card p-4">
            <h3 className="font-bold text-sm mb-3 flex items-center gap-2"><Users size={16} className="text-emerald-500" /> Workload Balancing</h3>
            <p className="text-xs text-slate-500 mb-3">AI suggests the least-loaded doctor for new bookings.</p>
            <div className="bg-emerald-50 p-3 rounded-lg text-xs text-emerald-700 flex items-center gap-2">
              <Brain size={14} /> Auto-balance is enabled for all departments
            </div>
          </div>
        </div>
      )}

      {/* ═════════ MODAL: New Calendar ═════════ */}
      {showNewCalModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <h2 className="font-bold text-lg flex items-center gap-2"><Calendar size={18} /> New Doctor Calendar</h2>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2"><label className="input-label">Select Doctor *</label>
                <select className="input-field" value={newCal.doctor_id} onChange={e => setNewCal(p => ({ ...p, doctor_id: e.target.value }))}>
                  <option value="">-- Select a Doctor --</option>
                  {doctors.map(d => <option key={d.id} value={d.id}>{d.full_name} ({d.email})</option>)}
                </select>
              </div>
              <div className="col-span-2"><label className="input-label">Department *</label><input className="input-field" value={newCal.department} onChange={e => setNewCal(p => ({ ...p, department: e.target.value }))} placeholder="e.g. Cardiology, Orthopedics" /></div>
              <div><label className="input-label">Slot Duration (min)</label><input type="number" className="input-field" value={newCal.default_slot_duration_min} onChange={e => setNewCal(p => ({ ...p, default_slot_duration_min: +e.target.value }))} /></div>
              <div><label className="input-label">Max Patients/Slot</label><input type="number" className="input-field" value={newCal.max_patients_per_slot} onChange={e => setNewCal(p => ({ ...p, max_patients_per_slot: +e.target.value }))} /></div>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newCal.allow_teleconsultation} onChange={e => setNewCal(p => ({ ...p, allow_teleconsultation: e.target.checked }))} /> Teleconsultation</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newCal.allow_overbooking} onChange={e => setNewCal(p => ({ ...p, allow_overbooking: e.target.checked }))} /> Allow Overbooking</label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowNewCalModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={createCalendar} disabled={loading} className="btn-primary flex items-center gap-1">
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═════════ MODAL: Cyclic Schedule ═════════ */}
      {showCyclicModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <h2 className="font-bold text-lg flex items-center gap-2"><Repeat size={18} /> New Cyclic Schedule</h2>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="input-label">Day of Week</label>
                <select className="input-field" value={newCyclic.day_of_week} onChange={e => setNewCyclic(p => ({ ...p, day_of_week: e.target.value }))}>
                  {["mon","tue","wed","thu","fri","sat","sun"].map(d => <option key={d} value={d}>{d.toUpperCase()}</option>)}
                </select>
              </div>
              <div>
                <label className="input-label">Appointment Type</label>
                <select className="input-field" value={newCyclic.appointment_type} onChange={e => setNewCyclic(p => ({ ...p, appointment_type: e.target.value }))}>
                  <option value="in_person">In-Person</option>
                  <option value="teleconsultation">Teleconsultation</option>
                </select>
              </div>
              <div><label className="input-label">Start Time</label><input type="time" className="input-field" value={newCyclic.start_time} onChange={e => setNewCyclic(p => ({ ...p, start_time: e.target.value }))} /></div>
              <div><label className="input-label">End Time</label><input type="time" className="input-field" value={newCyclic.end_time} onChange={e => setNewCyclic(p => ({ ...p, end_time: e.target.value }))} /></div>
              <div><label className="input-label">Slot Duration (min)</label><input type="number" className="input-field" value={newCyclic.slot_duration_min} onChange={e => setNewCyclic(p => ({ ...p, slot_duration_min: +e.target.value }))} /></div>
              <div><label className="input-label">Patients/Slot</label><input type="number" className="input-field" value={newCyclic.max_patients_per_slot} onChange={e => setNewCyclic(p => ({ ...p, max_patients_per_slot: +e.target.value }))} /></div>
              <div><label className="input-label">Effective From</label><input type="date" className="input-field" value={newCyclic.effective_from} onChange={e => setNewCyclic(p => ({ ...p, effective_from: e.target.value }))} /></div>
              <div><label className="input-label">Effective Until</label><input type="date" className="input-field" value={newCyclic.effective_until} onChange={e => setNewCyclic(p => ({ ...p, effective_until: e.target.value }))} /></div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowCyclicModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={createCyclicSchedule} disabled={loading} className="btn-primary flex items-center gap-1">
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═════════ MODAL: Book Slot ═════════ */}
      {showBookModal && selectedSlot && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <h2 className="font-bold text-lg flex items-center gap-2"><Clock size={18} /> Book Appointment</h2>
            <div className="bg-indigo-50 rounded-lg p-3 text-sm">
              <div className="font-bold text-indigo-800">{selectedSlot.slot_date} · {formatTime(selectedSlot.start_time)} – {formatTime(selectedSlot.end_time)}</div>
            </div>
            <div className="space-y-3">
              <div><label className="input-label">Select Patient *</label>
                <select className="input-field" value={bookForm.patient_id} onChange={e => setBookForm(p => ({ ...p, patient_id: e.target.value }))}>
                  <option value="">-- Select a Patient --</option>
                  {patients.map(pt => <option key={pt.id} value={pt.id}>{pt.first_name} {pt.last_name}{pt.uhid ? ` (${pt.uhid})` : ""}</option>)}
                </select>
              </div>
              <div><label className="input-label">Department *</label><input className="input-field" value={bookForm.department} onChange={e => setBookForm(p => ({ ...p, department: e.target.value }))} placeholder="e.g. General Medicine" /></div>
              <div>
                <label className="input-label">Type</label>
                <select className="input-field" value={bookForm.appointment_type} onChange={e => setBookForm(p => ({ ...p, appointment_type: e.target.value }))}>
                  <option value="in_person">In-Person</option>
                  <option value="teleconsultation">Teleconsultation</option>
                  <option value="follow_up">Follow-Up</option>
                </select>
              </div>
              <div><label className="input-label">Reason</label><input className="input-field" value={bookForm.reason} onChange={e => setBookForm(p => ({ ...p, reason: e.target.value }))} /></div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => { setShowBookModal(false); setSelectedSlot(null); }} className="btn-secondary">Cancel</button>
              <button onClick={bookSlot} disabled={loading} className="btn-primary flex items-center gap-1">
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Book
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═════════ MODAL: New Modality Resource ═════════ */}
      {showResourceModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <h2 className="font-bold text-lg flex items-center gap-2"><Scan size={18} /> New Modality Equipment</h2>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="input-label">Modality Type</label>
                <select className="input-field" value={newResource.modality_type} onChange={e => setNewResource(p => ({ ...p, modality_type: e.target.value }))}>
                  <option value="mri">MRI</option><option value="ct">CT</option><option value="xray">X-Ray</option><option value="ultrasound">Ultrasound</option>
                </select>
              </div>
              <div><label className="input-label">Name *</label><input className="input-field" value={newResource.name} onChange={e => setNewResource(p => ({ ...p, name: e.target.value }))} /></div>
              <div><label className="input-label">Location</label><input className="input-field" value={newResource.location} onChange={e => setNewResource(p => ({ ...p, location: e.target.value }))} /></div>
              <div><label className="input-label">Slot Duration (min)</label><input type="number" className="input-field" value={newResource.slot_duration_min} onChange={e => setNewResource(p => ({ ...p, slot_duration_min: +e.target.value }))} /></div>
              <div><label className="input-label">Operating Start</label><input type="time" className="input-field" value={newResource.operating_start} onChange={e => setNewResource(p => ({ ...p, operating_start: e.target.value }))} /></div>
              <div><label className="input-label">Operating End</label><input type="time" className="input-field" value={newResource.operating_end} onChange={e => setNewResource(p => ({ ...p, operating_end: e.target.value }))} /></div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowResourceModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={createResource} disabled={loading} className="btn-primary flex items-center gap-1">
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═════════ MODAL: Overbooking Rule ═════════ */}
      {showOverbookModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <h2 className="font-bold text-lg flex items-center gap-2"><Shield size={18} /> New Overbooking Rule</h2>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2"><label className="input-label">Doctor (optional)</label>
                <select className="input-field" value={newOverbook.doctor_id} onChange={e => setNewOverbook(p => ({ ...p, doctor_id: e.target.value }))}>
                  <option value="">All doctors (department-wide)</option>
                  {doctors.map(d => <option key={d.id} value={d.id}>{d.full_name}</option>)}
                </select>
              </div>
              <div className="col-span-2"><label className="input-label">Department</label><input className="input-field" placeholder="e.g. Cardiology" value={newOverbook.department} onChange={e => setNewOverbook(p => ({ ...p, department: e.target.value }))} /></div>
              <div><label className="input-label">Max Overbook/Slot</label><input type="number" className="input-field" value={newOverbook.max_overbook_per_slot} onChange={e => setNewOverbook(p => ({ ...p, max_overbook_per_slot: +e.target.value }))} /></div>
              <div><label className="input-label">Max Overbook/Day</label><input type="number" className="input-field" value={newOverbook.max_overbook_per_day} onChange={e => setNewOverbook(p => ({ ...p, max_overbook_per_day: +e.target.value }))} /></div>
              <div><label className="input-label">Priority Threshold (1-5)</label><input type="number" min={1} max={5} className="input-field" value={newOverbook.priority_threshold} onChange={e => setNewOverbook(p => ({ ...p, priority_threshold: +e.target.value }))} /></div>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newOverbook.allow_emergency_override} onChange={e => setNewOverbook(p => ({ ...p, allow_emergency_override: e.target.checked }))} /> Emergency Override</label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowOverbookModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={createOverbookingRule} disabled={loading} className="btn-primary flex items-center gap-1">
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═════════ MODAL: Follow-Up Rule ═════════ */}
      {showFollowUpModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <h2 className="font-bold text-lg flex items-center gap-2"><Repeat size={18} /> New Follow-Up Rule</h2>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2"><label className="input-label">Department *</label><input className="input-field" placeholder="e.g. Orthopedics" value={newFollowUp.department} onChange={e => setNewFollowUp(p => ({ ...p, department: e.target.value }))} /></div>
              <div><label className="input-label">Diagnosis Code (ICD)</label><input className="input-field" placeholder="e.g. M17.1" value={newFollowUp.diagnosis_code} onChange={e => setNewFollowUp(p => ({ ...p, diagnosis_code: e.target.value }))} /></div>
              <div><label className="input-label">Follow-Up After (days)</label><input type="number" className="input-field" value={newFollowUp.follow_up_days} onChange={e => setNewFollowUp(p => ({ ...p, follow_up_days: +e.target.value }))} /></div>
              <div><label className="input-label">Max Follow-Ups</label><input type="number" className="input-field" value={newFollowUp.max_follow_ups} onChange={e => setNewFollowUp(p => ({ ...p, max_follow_ups: +e.target.value }))} /></div>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newFollowUp.is_active} onChange={e => setNewFollowUp(p => ({ ...p, is_active: e.target.checked }))} /> Active</label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowFollowUpModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={createFollowUpRule} disabled={loading} className="btn-primary flex items-center gap-1">
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
