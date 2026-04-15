"use client";
import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "@/i18n";
import { api } from "@/lib/api";
import { opdApi, type PreRegistration, type Deposit, type ConsentDocument, type ProFormaBill, type OPDAnalytics, type PatientJourney, type WaitlistEntry } from "@/lib/opd-api";
import { opdVisitsApi, type OpdVisit } from "@/lib/opd-visits-api";
import { schedulingApi } from "@/lib/scheduling-api";
import {
  Users, Calendar, ClipboardList, Stethoscope, CreditCard, FileText,
  BarChart3, Activity, Search, Plus, ArrowRight, CheckCircle2, Clock,
  AlertTriangle, RefreshCw, UserPlus, DollarSign, FileSignature,
  Smartphone, Brain, TrendingUp, Eye, ChevronRight, Shield,
  Building2, UserCheck, Wallet, Receipt, ArrowUpDown, Layers
} from "lucide-react";

type TabId = "appointments" | "registration" | "queue" | "billing" | "consents" | "analytics" | "journey";

interface PatientRecord { id: string; first_name: string; last_name: string; patient_uuid?: string; primary_phone?: string; }
interface DoctorRecord { id: string; full_name: string; email: string; }

export default function OPDCommandCenter() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabId>("appointments");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [doctors, setDoctors] = useState<DoctorRecord[]>([]);
  const [slotsMap, setSlotsMap] = useState<Record<string, any[]>>({});

  // Data states
  const [preRegs, setPreRegs] = useState<PreRegistration[]>([]);
  const [deposits, setDeposits] = useState<Deposit[]>([]);
  const [consents, setConsents] = useState<ConsentDocument[]>([]);
  const [visits, setVisits] = useState<OpdVisit[]>([]);
  const [waitlist, setWaitlist] = useState<WaitlistEntry[]>([]);
  const [analytics, setAnalytics] = useState<OPDAnalytics | null>(null);
  const [journey, setJourney] = useState<PatientJourney | null>(null);

  const [showPreRegForm, setShowPreRegForm] = useState(false);
  const [showDepositForm, setShowDepositForm] = useState(false);
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [showConsentForm, setShowConsentForm] = useState(false);
  const [showTemplateForm, setShowTemplateForm] = useState(false);
  const [preRegForm, setPreRegForm] = useState({ first_name: "", last_name: "", mobile_number: "", gender: "male", date_of_birth: "", email: "", preferred_department: "", payer_category: "self_pay" });
  const [depositForm, setDepositForm] = useState({ patient_id: "", deposit_amount: "", payment_mode: "cash" });
  const [consentForm, setConsentForm] = useState({ patient_id: "", consent_title: "", consent_body: "" });
  const [templateForm, setTemplateForm] = useState({ template_name: "", template_category: "Surgery", language: "en", template_body: "" });
  const [bookingForm, setBookingForm] = useState({ patient_id: "", doctor_id: "", department: "", preferred_date: new Date().toISOString().split("T")[0] });
  const [journeyVisitId, setJourneyVisitId] = useState("");

  useEffect(() => { loadBaseData(); }, []);

  useEffect(() => {
    if (activeTab === "appointments") loadWaitlist();
    else if (activeTab === "registration") loadPreRegistrations();
    else if (activeTab === "billing") loadDeposits();
    else if (activeTab === "consents") loadConsents();
    else if (activeTab === "queue" || activeTab === "journey") loadVisits();
    else if (activeTab === "analytics") loadAnalytics();
  }, [activeTab]);

  const loadBaseData = async () => {
    try {
      const [p, d, v, a] = await Promise.all([
        api.get<any>("/patients").catch(() => []),
        api.get<any>("/auth/users").catch(() => []),
        opdVisitsApi.listVisits().catch(() => []),
        opdApi.computeAnalytics(new Date().toISOString().split("T")[0]).catch(() => null)
      ]);
      setPatients(Array.isArray(p) ? p : p?.items || []);
      const docs = Array.isArray(d) ? d : d?.items || [];
      setDoctors(docs);
      setVisits(v || []);
      setAnalytics(a);

      const topDocs = docs.slice(0, 5);
      const slotPromises = topDocs.map((doc: any) => 
        schedulingApi.getDoctorSlots(doc.id, new Date().toISOString().split("T")[0])
          .then((res: any) => ({ id: doc.id, slots: res }))
          .catch(() => ({ id: doc.id, slots: [] }))
      );
      const resolvedSlots = await Promise.all(slotPromises);
      const sMap: Record<string, any[]> = {};
      resolvedSlots.forEach(rs => { sMap[rs.id] = rs.slots });
      setSlotsMap(sMap);
    } catch (e) { console.error(e); }
  };

  const loadPreRegistrations = async () => { setLoading(true); try { const r = await opdApi.listPreRegistrations(); setPreRegs(r || []); } catch {} setLoading(false); };
  const loadWaitlist = async () => { setLoading(true); try { const r = await opdApi.listWaitlist(undefined, "waiting"); setWaitlist(r || []); } catch {} setLoading(false); };
  const loadDeposits = async () => { setLoading(true); try { const r = await opdApi.listDeposits(); setDeposits(r || []); } catch {} setLoading(false); };
  const loadConsents = async () => { setLoading(true); try { const r = await opdApi.listConsentDocuments(); setConsents(r || []); } catch {} setLoading(false); };
  const loadVisits = async () => { setLoading(true); try { const r = await opdVisitsApi.listVisits(); setVisits(r || []); } catch {} setLoading(false); };
  const loadAnalytics = async () => { setLoading(true); try { const r = await opdApi.computeAnalytics(new Date().toISOString().split("T")[0]); setAnalytics(r); } catch {} setLoading(false); };

  const getPatientName = (id: string) => { const p = patients.find(x => x.id === id); return p ? `${p.first_name} ${p.last_name}` : id?.slice(0, 8) || "Unknown"; };
  const getDoctorName = (id?: string) => { if (!id) return "Unassigned"; const d = doctors.find(x => x.id === id); return d ? d.full_name : id.slice(0, 8); };

  const handlePreRegSubmit = async () => {
    setLoading(true); setError("");
    try {
      await opdApi.createPreRegistration(preRegForm);
      setSuccess("Pre-registration created successfully!");
      setShowPreRegForm(false);
      setPreRegForm({ first_name: "", last_name: "", mobile_number: "", gender: "male", date_of_birth: "", email: "", preferred_department: "", payer_category: "self_pay" });
      loadPreRegistrations();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleConvertPreReg = async (id: string) => {
    setLoading(true); setError("");
    try {
      await opdApi.convertToPatient(id, {});
      setSuccess("Patient registered with UHID successfully!");
      loadPreRegistrations();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleDepositSubmit = async () => {
    setLoading(true); setError("");
    try {
      await opdApi.createDeposit({ ...depositForm, deposit_amount: parseFloat(depositForm.deposit_amount) });
      setSuccess("Deposit collected successfully!");
      setShowDepositForm(false);
      setDepositForm({ patient_id: "", deposit_amount: "", payment_mode: "cash" });
      loadDeposits();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleConsentSubmit = async () => {
    setLoading(true); setError("");
    try {
      await opdApi.createConsentDocument(consentForm);
      setSuccess("Consent document created!");
      setShowConsentForm(false);
      setConsentForm({ patient_id: "", consent_title: "", consent_body: "" });
      loadConsents();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleTemplateSubmit = async () => {
    setLoading(true); setError("");
    try {
      await opdApi.createConsentTemplate(templateForm);
      setSuccess("Consent template created!");
      setShowTemplateForm(false);
      setTemplateForm({ template_name: "", template_category: "Surgery", language: "en", template_body: "" });
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleBookingSubmit = async () => {
    setLoading(true); setError("");
    try {
      await opdApi.addToWaitlist(bookingForm);
      setSuccess("Appointment booked successfully!");
      setShowBookingForm(false);
      setBookingForm({ patient_id: "", doctor_id: "", department: "", preferred_date: new Date().toISOString().split("T")[0] });
      loadWaitlist();
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const handleCheckInWaitlist = async (w: WaitlistEntry) => {
    setLoading(true); setError("");
    try {
      if (!w.patient_id || !w.doctor_id) throw new Error("Missing Patient or Doctor ID");
      await opdVisitsApi.createVisit({
        patient_id: w.patient_id,
        doctor_id: w.doctor_id,
        department: w.department || "Cardiology",
        visit_source: "appointment",
        visit_type: "doctor_consultation",
        appointment_id: w.id,
        priority_tag: "normal"
      });
      setSuccess("Patient checked in! They are now in the active Queue & Flow.");
      loadWaitlist();
    } catch (e: any) { 
      setError(e.response?.data?.detail?.[0]?.msg || e.message || "Failed to check in waitlist entry."); 
    }
    setLoading(false);
  };

  const handleCompleteVisit = async (visit_id: string) => {
    setLoading(true); setError("");
    try {
      await opdVisitsApi.updateVisit(visit_id, { status: "completed" });
      setSuccess("Visit successfully completed!");
      loadVisits();
    } catch (e: any) {
      setError(e.response?.data?.detail?.[0]?.msg || e.message || "Failed to complete visit.");
    }
    setLoading(false);
  };

  const handleLoadJourney = async () => {
    if (!journeyVisitId) return;
    setLoading(true); setError("");
    try { const j = await opdApi.getPatientJourney(journeyVisitId); setJourney(j); } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const clearMessages = () => { setError(""); setSuccess(""); };

  const tabs: { id: TabId; icon: any; label: string; color: string }[] = [
    { id: "appointments", icon: Calendar, label: "Appointments", color: "from-violet-500 to-purple-600" },
    { id: "registration", icon: UserPlus, label: "Registration", color: "from-blue-500 to-cyan-500" },
    { id: "queue", icon: Users, label: "Queue & Flow", color: "from-emerald-500 to-teal-500" },
    { id: "billing", icon: CreditCard, label: "Billing", color: "from-amber-500 to-orange-500" },
    { id: "consents", icon: FileSignature, label: "Consents", color: "from-indigo-500 to-blue-600" },
    { id: "analytics", icon: BarChart3, label: "Analytics", color: "from-fuchsia-500 to-purple-600" },
    { id: "journey", icon: Layers, label: "Journey", color: "from-slate-500 to-gray-600" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      {/* ── Header ── */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white px-8 py-6">
        <div className="max-w-[1600px] mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
                <Building2 size={22} />
              </div>
              OPD Command Center
            </h1>
            <p className="text-indigo-300 mt-1 text-sm">Enterprise Outpatient Department Management System</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="bg-white/10 backdrop-blur-sm px-4 py-2 rounded-lg text-sm">
              <span className="text-indigo-300">Today: </span>
              <span className="font-semibold">{new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Tab Navigation ── */}
      <div className="bg-white border-b sticky top-0 z-30 shadow-sm">
        <div className="max-w-[1600px] mx-auto px-8">
          <div className="flex gap-1 overflow-x-auto py-2">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id); clearMessages(); }}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? `bg-gradient-to-r ${tab.color} text-white shadow-md scale-[1.02]`
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="max-w-[1600px] mx-auto px-8 mt-4">
        {error && <div className="bg-red-50 text-red-700 p-4 rounded-xl flex items-center gap-2 mb-4 border border-red-200"><AlertTriangle size={18} />{error}<button onClick={clearMessages} className="ml-auto text-red-400 hover:text-red-600">✕</button></div>}
        {success && <div className="bg-emerald-50 text-emerald-700 p-4 rounded-xl flex items-center gap-2 mb-4 border border-emerald-200"><CheckCircle2 size={18} />{success}<button onClick={clearMessages} className="ml-auto text-emerald-400 hover:text-emerald-600">✕</button></div>}
      </div>

      {/* ── Content ── */}
      <div className="max-w-[1600px] mx-auto px-8 py-6">
        
        {/* ═════════ APPOINTMENTS TAB ═════════ */}
        {activeTab === "appointments" && (
          <div className="space-y-6">
            <div className="grid grid-cols-4 gap-4">
              {[
                { label: "Today's Appointments", value: analytics ? analytics.total_visits : waitlist.length, icon: Calendar, color: "from-violet-500 to-purple-600", sub: `${waitlist.length} pending in waitlist` },
                { label: "Walk-in Patients", value: visits.filter(v => v.visit_source === 'walk_in').length, icon: Users, color: "from-emerald-500 to-teal-500", sub: `${visits.filter(v => v.status === 'in_queue').length} in queue` },
                { label: "Teleconsultations", value: visits.filter(v => v.visit_source === 'teleconsultation' || v.visit_type === 'telemedicine').length, icon: Smartphone, color: "from-blue-500 to-cyan-500", sub: "Active virtually" },
                { label: "No-Show Prediction", value: analytics ? analytics.no_show_count : 0, icon: Brain, color: "from-amber-500 to-orange-500", sub: "AI flagged" },
              ].map((card, i) => (
                <div key={i} className={`bg-gradient-to-br ${card.color} text-white p-5 rounded-2xl shadow-lg`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-sm font-medium opacity-80">{card.label}</div>
                      <div className="text-4xl font-black mt-2">{card.value}</div>
                      <div className="text-xs opacity-70 mt-1">{card.sub}</div>
                    </div>
                    <card.icon size={28} className="opacity-50" />
                  </div>
                </div>
              ))}
            </div>

            {/* Doctor Schedule Grid */}
            <div className="bg-white rounded-2xl shadow-sm border p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold flex items-center gap-2"><Calendar className="text-violet-500" /> Doctor Schedule Grid</h2>
                <button onClick={() => setShowBookingForm(!showBookingForm)} className="bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 transition shadow-md">Book Appointment</button>
              </div>

              {showBookingForm && (
                <div className="bg-slate-50 border rounded-xl p-5 mb-6 shadow-inner">
                  <h3 className="font-bold text-slate-700 mb-3 flex items-center gap-2"><Plus size={16} className="text-violet-500" /> Book New Appointment</h3>
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-500 mb-1">Patient *</label>
                      <select className="w-full border rounded-lg px-3 py-2 text-sm outline-none bg-white" value={bookingForm.patient_id} onChange={e => setBookingForm({...bookingForm, patient_id: e.target.value})}>
                        <option value="">Select Patient...</option>
                        {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-500 mb-1">Doctor *</label>
                      <select className="w-full border rounded-lg px-3 py-2 text-sm outline-none bg-white" value={bookingForm.doctor_id} onChange={e => setBookingForm({...bookingForm, doctor_id: e.target.value})}>
                        <option value="">Select Doctor...</option>
                        {doctors.map(d => <option key={d.id} value={d.id}>{d.full_name}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-500 mb-1">Department</label>
                      <select className="w-full border rounded-lg px-3 py-2 text-sm outline-none bg-white" value={bookingForm.department} onChange={e => setBookingForm({...bookingForm, department: e.target.value})}>
                        <option value="">Select...</option>
                        <option value="Cardiology">Cardiology</option><option value="Orthopedics">Orthopedics</option><option value="General Medicine">General Medicine</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-500 mb-1">Date</label>
                      <input type="date" className="w-full border rounded-lg px-3 py-2 text-sm outline-none bg-white" value={bookingForm.preferred_date} onChange={e => setBookingForm({...bookingForm, preferred_date: e.target.value})} />
                    </div>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <button onClick={handleBookingSubmit} disabled={loading || !bookingForm.patient_id || !bookingForm.doctor_id} className="bg-violet-600 text-white px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50 shadow-md">Confirm Booking</button>
                    <button onClick={() => setShowBookingForm(false)} className="border bg-white px-5 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50">Cancel</button>
                  </div>
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-slate-50">
                      <th className="text-left py-3 px-4 font-semibold text-slate-600">Doctor</th>
                      {["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "14:00", "14:30", "15:00", "15:30", "16:00"].map(t => (
                        <th key={t} className="text-center py-3 px-2 font-medium text-slate-500 text-xs">{t}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(doctors.length > 0 ? doctors.slice(0, 5) : [{ id: "1", full_name: "Dr. Sample" }]).map((doc, i) => {
                      const slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "14:00", "14:30", "15:00", "15:30", "16:00"];
                      const docBookings = waitlist.filter(w => w.doctor_id === doc.id);
                      return (
                        <tr key={doc.id} className="border-b hover:bg-slate-50 transition-colors">
                          <td className="py-3 px-4 font-semibold text-slate-800">{doc.full_name}</td>
                          {slots.map((time, si) => {
                            const allDoctorSlots = slotsMap[doc.id] || [];
                            const slot = allDoctorSlots.find((s: any) => s.start_time && s.start_time.startsWith(time));
                            
                            let st = "—";
                            if (slot) {
                               st = "available";
                               if (slot.status === 'booked' || slot.current_bookings > 0) st = "booked";
                               if (slot.status === 'blocked') st = "blocked";
                               if (slot.current_bookings > slot.max_bookings) st = "overbooked";
                            }
                            
                            const colors: Record<string, string> = {
                              available: "bg-emerald-100 border-emerald-300 text-emerald-700",
                              booked: "bg-blue-100 border-blue-300 text-blue-700",
                              overbooked: "bg-amber-100 border-amber-300 text-amber-700",
                              blocked: "bg-slate-200 border-slate-300 text-slate-500",
                              "—": "bg-slate-50 border-slate-200 text-slate-400 text-opacity-50"
                            };
                            return (
                              <td key={si} className="py-2 px-1 text-center">
                                <div className={`px-1 py-1.5 rounded-lg border text-[10px] font-bold uppercase cursor-pointer hover:shadow-md transition-all ${colors[st]}`}>
                                  {st === "available" ? "●" : st === "booked" ? "■" : st === "overbooked" ? "▲" : st === "blocked" ? "X" : "—"}
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="flex gap-4 mt-4 text-xs">
                {[
                  { label: "Available", color: "bg-emerald-100 border-emerald-300 text-emerald-700" },
                  { label: "Booked", color: "bg-blue-100 border-blue-300 text-blue-700" },
                  { label: "Overbooked", color: "bg-amber-100 border-amber-300 text-amber-700" },
                  { label: "Blocked", color: "bg-slate-200 border-slate-300 text-slate-500" },
                ].map(l => (
                  <div key={l.label} className="flex items-center gap-1.5">
                    <div className={`w-4 h-4 rounded border ${l.color}`}></div>
                    <span className="text-slate-600">{l.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Upcoming Waitlist Appointments */}
            <div className="bg-white rounded-2xl shadow-sm border overflow-hidden mt-6">
              <div className="px-6 py-4 border-b bg-slate-50 flex items-center justify-between">
                <h3 className="font-bold text-slate-700 flex items-center gap-2"><ClipboardList size={18} className="text-violet-500" /> Upcoming Waitlist Appointments</h3>
                <span className="text-xs flex items-center font-semibold bg-violet-100 text-violet-700 px-3 py-1 rounded-full">{waitlist.length} Waiting</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-50 border-b">
                    <tr><th className="py-3 px-6 font-medium text-slate-500 border-none">Patient</th><th className="py-3 px-6 font-medium text-slate-500 border-none">Doctor</th><th className="py-3 px-6 font-medium text-slate-500 border-none">Department</th><th className="py-3 px-6 font-medium text-slate-500 border-none">Pref. Date</th><th className="py-3 px-6 font-medium text-slate-500 border-none">Status</th><th className="py-3 px-6 font-medium text-slate-500 border-none text-right">Action</th></tr>
                  </thead>
                  <tbody className="divide-y">
                    {waitlist.map(w => (
                      <tr key={w.id} className="hover:bg-slate-50">
                        <td className="py-3 px-6 font-semibold">{getPatientName(w.patient_id)}</td>
                        <td className="py-3 px-6">{getDoctorName(w.doctor_id)}</td>
                        <td className="py-3 px-6 text-slate-500">{w.department}</td>
                        <td className="py-3 px-6 text-slate-500">{new Date(w.preferred_date).toLocaleDateString()}</td>
                        <td className="py-3 px-6"><span className="bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full text-xs font-bold uppercase">{w.status}</span></td>
                        <td className="py-3 px-6 text-right">
                          <button onClick={() => handleCheckInWaitlist(w)} className="bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-emerald-200 transition">Check In</button>
                        </td>
                      </tr>
                    ))}
                    {waitlist.length === 0 && <tr><td colSpan={5} className="py-12 text-center text-slate-400">No waiting appointments on the waitlist</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

        {/* ═════════ REGISTRATION TAB ═════════ */}
        {activeTab === "registration" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2"><UserPlus className="text-blue-500" />Patient Registration & Pre-Registration</h2>
              <button onClick={() => setShowPreRegForm(!showPreRegForm)} className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 hover:shadow-lg transition-all"><Plus size={16} />New Pre-Registration</button>
            </div>

            {showPreRegForm && (
              <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-6">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><ClipboardList className="text-blue-500" />Pre-Registration Form</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">First Name *</label>
                    <input className="w-full border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-blue-400 outline-none" value={preRegForm.first_name} onChange={e => setPreRegForm({...preRegForm, first_name: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Last Name *</label>
                    <input className="w-full border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-blue-400 outline-none" value={preRegForm.last_name} onChange={e => setPreRegForm({...preRegForm, last_name: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Mobile Number *</label>
                    <input className="w-full border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-blue-400 outline-none" value={preRegForm.mobile_number} onChange={e => setPreRegForm({...preRegForm, mobile_number: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Gender</label>
                    <select className="w-full border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-blue-400 outline-none bg-white" value={preRegForm.gender} onChange={e => setPreRegForm({...preRegForm, gender: e.target.value})}>
                      <option value="male">Male</option><option value="female">Female</option><option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Date of Birth</label>
                    <input type="date" className="w-full border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-blue-400 outline-none" value={preRegForm.date_of_birth} onChange={e => setPreRegForm({...preRegForm, date_of_birth: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Email</label>
                    <input type="email" className="w-full border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-blue-400 outline-none" value={preRegForm.email} onChange={e => setPreRegForm({...preRegForm, email: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Department</label>
                    <select className="w-full border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-blue-400 outline-none bg-white" value={preRegForm.preferred_department} onChange={e => setPreRegForm({...preRegForm, preferred_department: e.target.value})}>
                      <option value="">Select...</option>
                      {["General Medicine", "Cardiology", "Orthopedics", "Neurology", "ENT", "Ophthalmology", "Dermatology", "Pediatrics", "Gynecology"].map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Payer Category</label>
                    <select className="w-full border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-blue-400 outline-none bg-white" value={preRegForm.payer_category} onChange={e => setPreRegForm({...preRegForm, payer_category: e.target.value})}>
                      <option value="self_pay">Self Pay (Cash)</option><option value="insurance">Insurance</option><option value="corporate">Corporate</option>
                    </select>
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button onClick={handlePreRegSubmit} disabled={loading || !preRegForm.first_name || !preRegForm.mobile_number} className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-6 py-2.5 rounded-xl font-medium disabled:opacity-40">
                    {loading ? "Creating..." : "Create Pre-Registration"}
                  </button>
                  <button onClick={() => setShowPreRegForm(false)} className="px-6 py-2.5 rounded-xl border text-slate-600 hover:bg-slate-50">Cancel</button>
                </div>
              </div>
            )}

            {/* Pre-Registration List */}
            <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
              <div className="px-6 py-4 border-b bg-slate-50 flex justify-between items-center">
                <h3 className="font-bold text-slate-700">Pre-Registration Records</h3>
                <button onClick={loadPreRegistrations} className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"><RefreshCw size={14} />Refresh</button>
              </div>
              <table className="w-full text-sm">
                <thead><tr className="border-b text-slate-500">
                  <th className="text-left py-3 px-4">Pre-Reg ID</th>
                  <th className="text-left py-3 px-4">Name</th>
                  <th className="text-left py-3 px-4">Mobile</th>
                  <th className="text-left py-3 px-4">Department</th>
                  <th className="text-left py-3 px-4">Payer</th>
                  <th className="text-left py-3 px-4">Duplicate</th>
                  <th className="text-left py-3 px-4">Status</th>
                  <th className="text-left py-3 px-4">Actions</th>
                </tr></thead>
                <tbody className="divide-y">
                  {preRegs.map(pr => (
                    <tr key={pr.id} className="hover:bg-blue-50/50 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-blue-600">{pr.pre_reg_id}</td>
                      <td className="py-3 px-4 font-semibold">{pr.first_name} {pr.last_name}</td>
                      <td className="py-3 px-4 text-slate-600">{pr.mobile_number}</td>
                      <td className="py-3 px-4">{pr.preferred_department || "—"}</td>
                      <td className="py-3 px-4"><span className="px-2 py-1 rounded-lg text-xs font-medium bg-slate-100">{pr.payer_category}</span></td>
                      <td className="py-3 px-4">
                        {pr.duplicate_score ? (
                          <span className={`px-2 py-1 rounded-lg text-xs font-bold ${pr.duplicate_score > 0.7 ? "bg-red-100 text-red-700" : pr.duplicate_score > 0.4 ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                            {(pr.duplicate_score * 100).toFixed(0)}%
                          </span>
                        ) : <span className="text-slate-400 text-xs">None</span>}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${pr.status === "converted" ? "bg-emerald-100 text-emerald-700" : pr.status === "pending" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600"}`}>
                          {pr.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {pr.status === "pending" && (
                          <button onClick={() => handleConvertPreReg(pr.id)} className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:shadow-md transition-all flex items-center gap-1">
                            <UserCheck size={12} />Generate UHID
                          </button>
                        )}
                        {pr.status === "converted" && <span className="text-emerald-600 font-mono text-xs font-bold">{pr.converted_uhid}</span>}
                      </td>
                    </tr>
                  ))}
                  {preRegs.length === 0 && <tr><td colSpan={8} className="text-center py-12 text-slate-400">No pre-registrations found. Click &quot;New Pre-Registration&quot; to start.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═════════ QUEUE TAB ═════════ */}
        {activeTab === "queue" && (
          <div className="space-y-6">
            <div className="grid grid-cols-4 gap-4">
              {[
                { label: "In Queue", value: visits.filter(v => v.status === "in_queue").length, color: "from-blue-500 to-indigo-500", icon: Users },
                { label: "With Nurse", value: visits.filter(v => v.status === "with_nurse").length, color: "from-rose-500 to-pink-500", icon: Activity },
                { label: "With Doctor", value: visits.filter(v => v.status === "with_doctor").length, color: "from-emerald-500 to-teal-500", icon: Stethoscope },
                { label: "Completed Today", value: visits.filter(v => v.status === "completed").length, color: "from-violet-500 to-purple-500", icon: CheckCircle2 },
              ].map((c, i) => (
                <div key={i} className={`bg-gradient-to-br ${c.color} text-white p-5 rounded-2xl shadow-lg`}>
                  <div className="flex justify-between"><div><div className="text-sm opacity-80">{c.label}</div><div className="text-4xl font-black mt-1">{c.value}</div></div><c.icon size={28} className="opacity-40" /></div>
                </div>
              ))}
            </div>

            <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
              <div className="px-6 py-4 border-b bg-slate-50 flex justify-between items-center">
                <h3 className="font-bold text-slate-700 flex items-center gap-2"><ArrowUpDown className="text-blue-500" />Live Patient Queue</h3>
                <button onClick={loadVisits} className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"><RefreshCw size={14} />Refresh</button>
              </div>
              <table className="w-full text-sm">
                <thead><tr className="border-b text-slate-500 bg-slate-50/50">
                  <th className="text-left py-3 px-4">Token</th>
                  <th className="text-left py-3 px-4">Visit ID</th>
                  <th className="text-left py-3 px-4">Patient</th>
                  <th className="text-left py-3 px-4">Department</th>
                  <th className="text-left py-3 px-4">Doctor</th>
                  <th className="text-left py-3 px-4">Priority</th>
                  <th className="text-left py-3 px-4">Status</th>
                  <th className="text-left py-3 px-4">Wait Time</th>
                  <th className="text-right py-3 px-4">Action</th>
                </tr></thead>
                <tbody className="divide-y">
                  {visits.map((v, i) => (
                    <tr key={v.id} className={`hover:bg-blue-50/30 transition-colors ${v.priority_tag === "emergency" ? "bg-red-50/30" : ""}`}>
                      <td className="py-3 px-4"><span className="bg-slate-800 text-white px-2.5 py-1 rounded-lg font-mono font-bold text-xs">{v.queue_token || `T${(i+1).toString().padStart(3,"0")}`}</span></td>
                      <td className="py-3 px-4 font-mono text-blue-600 text-xs">{v.visit_id}</td>
                      <td className="py-3 px-4 font-semibold">{getPatientName(v.patient_id)}</td>
                      <td className="py-3 px-4 text-slate-600">{v.department || v.specialty || "—"}</td>
                      <td className="py-3 px-4">{getDoctorName(v.doctor_id)}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                          v.priority_tag === "emergency" ? "bg-red-100 text-red-700 ring-1 ring-red-300" :
                          v.priority_tag === "priority" ? "bg-amber-100 text-amber-700" :
                          v.priority_tag === "vip" ? "bg-purple-100 text-purple-700" :
                          "bg-slate-100 text-slate-600"
                        }`}>{v.priority_tag.toUpperCase()}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${
                          v.status === "with_doctor" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                          v.status === "with_nurse" ? "bg-rose-50 text-rose-700 border-rose-200" :
                          v.status === "in_queue" ? "bg-blue-50 text-blue-700 border-blue-200" :
                          "bg-slate-50 text-slate-600 border-slate-200"
                        }`}>{v.status.replace(/_/g," ").toUpperCase()}</span>
                      </td>
                      <td className="py-3 px-4 font-medium flex items-center gap-1"><Clock size={12} className="text-slate-400" />{v.estimated_wait_min || Math.floor(Math.random()*30+5)} min</td>
                      <td className="py-3 px-4 text-right">
                        {v.status !== "completed" && (
                          <button onClick={() => handleCompleteVisit(v.id)} className="bg-emerald-100 text-emerald-700 hover:bg-emerald-200 px-3 py-1.5 rounded-lg text-xs font-bold transition shadow-sm">Complete Consult</button>
                        )}
                        {v.status === "completed" && <span className="text-xs font-bold text-slate-400">DONE</span>}
                      </td>
                    </tr>
                  ))}
                  {visits.length === 0 && <tr><td colSpan={9} className="text-center py-12 text-slate-400">Queue is empty</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═════════ BILLING TAB ═════════ */}
        {activeTab === "billing" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2"><CreditCard className="text-amber-500" />Billing & Financial Management</h2>
              <button onClick={() => setShowDepositForm(!showDepositForm)} className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 hover:shadow-lg transition-all"><Wallet size={16} />Collect Deposit</button>
            </div>

            {showDepositForm && (
              <div className="bg-white rounded-2xl shadow-lg border border-amber-100 p-6">
                <h3 className="text-lg font-bold mb-4">Collect Advance Deposit</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Patient *</label>
                    <select className="w-full border rounded-xl px-4 py-2.5 outline-none bg-white" value={depositForm.patient_id} onChange={e => setDepositForm({...depositForm, patient_id: e.target.value})}>
                      <option value="">Select Patient</option>
                      {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.patient_uuid})</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Amount (₹) *</label>
                    <input type="number" className="w-full border rounded-xl px-4 py-2.5 outline-none" value={depositForm.deposit_amount} onChange={e => setDepositForm({...depositForm, deposit_amount: e.target.value})} placeholder="0.00" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Payment Mode</label>
                    <select className="w-full border rounded-xl px-4 py-2.5 outline-none bg-white" value={depositForm.payment_mode} onChange={e => setDepositForm({...depositForm, payment_mode: e.target.value})}>
                      <option value="cash">Cash</option><option value="card">Credit/Debit Card</option><option value="upi">UPI</option><option value="bank_transfer">Bank Transfer</option>
                    </select>
                  </div>
                </div>
                <div className="flex gap-3 mt-4">
                  <button onClick={handleDepositSubmit} disabled={loading || !depositForm.patient_id || !depositForm.deposit_amount} className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-6 py-2.5 rounded-xl font-medium disabled:opacity-40">{loading ? "Processing..." : "Collect Deposit"}</button>
                  <button onClick={() => setShowDepositForm(false)} className="px-6 py-2.5 rounded-xl border text-slate-600">Cancel</button>
                </div>
              </div>
            )}

            {/* Deposits Table */}
            <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
              <div className="px-6 py-4 border-b bg-slate-50"><h3 className="font-bold text-slate-700 flex items-center gap-2"><Receipt className="text-amber-500" />Deposit Ledger</h3></div>
              <table className="w-full text-sm">
                <thead><tr className="border-b text-slate-500">
                  <th className="text-left py-3 px-4">Deposit #</th>
                  <th className="text-left py-3 px-4">Patient</th>
                  <th className="text-right py-3 px-4">Deposited</th>
                  <th className="text-right py-3 px-4">Consumed</th>
                  <th className="text-right py-3 px-4">Balance</th>
                  <th className="text-left py-3 px-4">Mode</th>
                  <th className="text-left py-3 px-4">Status</th>
                </tr></thead>
                <tbody className="divide-y">
                  {deposits.map(d => (
                    <tr key={d.id} className="hover:bg-amber-50/30">
                      <td className="py-3 px-4 font-mono text-amber-700 font-medium">{d.deposit_number}</td>
                      <td className="py-3 px-4 font-semibold">{getPatientName(d.patient_id)}</td>
                      <td className="py-3 px-4 text-right font-bold text-emerald-600">₹{Number(d.deposit_amount).toFixed(2)}</td>
                      <td className="py-3 px-4 text-right text-slate-600">₹{Number(d.consumed_amount).toFixed(2)}</td>
                      <td className="py-3 px-4 text-right font-bold text-blue-600">₹{Number(d.balance_amount).toFixed(2)}</td>
                      <td className="py-3 px-4"><span className="px-2 py-1 bg-slate-100 rounded-lg text-xs capitalize">{d.payment_mode}</span></td>
                      <td className="py-3 px-4"><span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        d.status === "active" ? "bg-emerald-100 text-emerald-700" :
                        d.status === "refunded" ? "bg-red-100 text-red-700" :
                        "bg-amber-100 text-amber-700"
                      }`}>{d.status.toUpperCase()}</span></td>
                    </tr>
                  ))}
                  {deposits.length === 0 && <tr><td colSpan={7} className="text-center py-12 text-slate-400">No deposits recorded</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═════════ CONSENTS TAB ═════════ */}
        {activeTab === "consents" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2"><FileSignature className="text-indigo-500" />Consent & Document Management</h2>
              <div className="flex gap-2">
                <button onClick={() => { setShowConsentForm(!showConsentForm); setShowTemplateForm(false); }} className="bg-gradient-to-r from-indigo-500 to-blue-600 text-white px-4 py-2.5 rounded-xl font-medium text-sm flex items-center gap-2"><Plus size={14} />New Consent</button>
                <button onClick={() => { setShowTemplateForm(!showTemplateForm); setShowConsentForm(false); }} className="border px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 flex items-center gap-2 hover:bg-slate-50"><Shield size={14} />Templates</button>
              </div>
            </div>

            {showConsentForm && (
              <div className="bg-white rounded-2xl shadow-lg border border-indigo-100 p-6">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-indigo-700">Create New Consent Document</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Patient *</label>
                    <select className="w-full border rounded-xl px-4 py-2.5 outline-none bg-white" value={consentForm.patient_id} onChange={e => setConsentForm({...consentForm, patient_id: e.target.value})}>
                      <option value="">Select Patient...</option>
                      {patients.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Consent Title *</label>
                    <input className="w-full border rounded-xl px-4 py-2.5 outline-none" placeholder="e.g. Minor Surgery Consent" value={consentForm.consent_title} onChange={e => setConsentForm({...consentForm, consent_title: e.target.value})} />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-slate-600 mb-1">Consent Body / Content *</label>
                    <textarea rows={4} className="w-full border rounded-xl px-4 py-2.5 outline-none" placeholder="I hereby consent to..." value={consentForm.consent_body} onChange={e => setConsentForm({...consentForm, consent_body: e.target.value})} />
                  </div>
                </div>
                <div className="flex gap-3 mt-4">
                  <button onClick={handleConsentSubmit} disabled={loading || !consentForm.patient_id || !consentForm.consent_title} className="bg-gradient-to-r from-indigo-500 to-blue-600 text-white px-6 py-2.5 rounded-xl font-medium disabled:opacity-40">{loading ? "Saving..." : "Save Consent"}</button>
                  <button onClick={() => setShowConsentForm(false)} className="px-6 py-2.5 rounded-xl border text-slate-600">Cancel</button>
                </div>
              </div>
            )}

            {showTemplateForm && (
              <div className="bg-white rounded-2xl shadow-lg border border-indigo-100 p-6">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-indigo-700">New Consent Template</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Template Name *</label>
                    <input className="w-full border rounded-xl px-4 py-2.5 outline-none" placeholder="e.g. Standard Procedure" value={templateForm.template_name} onChange={e => setTemplateForm({...templateForm, template_name: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-600 mb-1">Category</label>
                    <select className="w-full border rounded-xl px-4 py-2.5 outline-none bg-white" value={templateForm.template_category} onChange={e => setTemplateForm({...templateForm, template_category: e.target.value})}>
                      <option value="Surgery">Surgery</option><option value="Radiology">Radiology</option><option value="General">General</option>
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-slate-600 mb-1">Template Body *</label>
                    <textarea rows={4} className="w-full border rounded-xl px-4 py-2.5 outline-none" placeholder="Standard template wording..." value={templateForm.template_body} onChange={e => setTemplateForm({...templateForm, template_body: e.target.value})} />
                  </div>
                </div>
                <div className="flex gap-3 mt-4">
                  <button onClick={handleTemplateSubmit} disabled={loading || !templateForm.template_name || !templateForm.template_body} className="bg-gradient-to-r from-slate-700 to-slate-900 text-white px-6 py-2.5 rounded-xl font-medium disabled:opacity-40">{loading ? "Saving..." : "Create Template"}</button>
                  <button onClick={() => setShowTemplateForm(false)} className="px-6 py-2.5 rounded-xl border text-slate-600">Cancel</button>
                </div>
              </div>
            )}

            <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
              <div className="px-6 py-4 border-b bg-slate-50"><h3 className="font-bold text-slate-700">Consent Documents</h3></div>
              <table className="w-full text-sm">
                <thead><tr className="border-b text-slate-500">
                  <th className="text-left py-3 px-4">Consent #</th>
                  <th className="text-left py-3 px-4">Title</th>
                  <th className="text-left py-3 px-4">Patient</th>
                  <th className="text-left py-3 px-4">Status</th>
                  <th className="text-left py-3 px-4">Signed</th>
                  <th className="text-left py-3 px-4">Actions</th>
                </tr></thead>
                <tbody className="divide-y">
                  {consents.map(c => (
                    <tr key={c.id} className="hover:bg-indigo-50/30">
                      <td className="py-3 px-4 font-mono text-indigo-600">{c.consent_number}</td>
                      <td className="py-3 px-4 font-semibold">{c.consent_title}</td>
                      <td className="py-3 px-4">{getPatientName(c.patient_id)}</td>
                      <td className="py-3 px-4"><span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        c.status === "signed" ? "bg-emerald-100 text-emerald-700" :
                        c.status === "pending_signature" ? "bg-amber-100 text-amber-700" :
                        "bg-slate-100 text-slate-600"
                      }`}>{c.status.replace(/_/g," ").toUpperCase()}</span></td>
                      <td className="py-3 px-4">{c.signed_at ? new Date(c.signed_at).toLocaleDateString() : "—"}</td>
                      <td className="py-3 px-4 flex gap-1">
                        <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500"><Eye size={14} /></button>
                        <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500"><FileText size={14} /></button>
                      </td>
                    </tr>
                  ))}
                  {consents.length === 0 && <tr><td colSpan={6} className="text-center py-12 text-slate-400">No consent documents</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ═════════ ANALYTICS TAB ═════════ */}
        {activeTab === "analytics" && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2"><BarChart3 className="text-fuchsia-500" />OPD Analytics Dashboard</h2>
            
            {analytics ? (
              <>
                <div className="grid grid-cols-5 gap-4">
                  {[
                    { label: "Total Visits", value: analytics.total_visits, color: "from-violet-500 to-purple-600", icon: Users },
                    { label: "Completed", value: analytics.completed_visits, color: "from-emerald-500 to-teal-500", icon: CheckCircle2 },
                    { label: "No-Shows", value: analytics.no_show_count, color: "from-amber-500 to-orange-500", icon: AlertTriangle },
                    { label: "Avg Wait", value: `${(analytics.avg_wait_time_min || 0).toFixed(0)}m`, color: "from-blue-500 to-cyan-500", icon: Clock },
                    { label: "Revenue", value: `₹${(analytics.total_revenue || 0).toLocaleString()}`, color: "from-fuchsia-500 to-purple-500", icon: TrendingUp },
                  ].map((c, i) => (
                    <div key={i} className={`bg-gradient-to-br ${c.color} text-white p-5 rounded-2xl shadow-lg`}>
                      <div className="flex justify-between items-start">
                        <div><div className="text-sm opacity-80">{c.label}</div><div className="text-3xl font-black mt-1">{c.value}</div></div>
                        <c.icon size={24} className="opacity-40" />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-6">
                  {/* Hourly Distribution */}
                  <div className="bg-white rounded-2xl shadow-sm border p-6">
                    <h3 className="font-bold mb-4">Patient Flow (Hourly)</h3>
                    <div className="flex items-end gap-1 h-40">
                      {Object.entries(analytics.hourly_distribution || {}).sort().map(([hour, count]) => (
                        <div key={hour} className="flex flex-col items-center flex-1">
                          <div
                            className="bg-gradient-to-t from-violet-500 to-purple-400 rounded-t-lg w-full min-h-[4px] transition-all hover:opacity-80"
                            style={{ height: `${Math.max(((count as number) / Math.max(...Object.values(analytics.hourly_distribution || {1: 1}) as number[])) * 100, 5)}%` }}
                          />
                          <span className="text-[10px] text-slate-400 mt-1">{hour}h</span>
                        </div>
                      ))}
                      {Object.keys(analytics.hourly_distribution || {}).length === 0 && <div className="text-slate-400 text-sm w-full text-center">No data</div>}
                    </div>
                    {analytics.peak_hour && <div className="mt-3 text-sm text-slate-500">Peak hour: <span className="font-bold text-violet-600">{analytics.peak_hour}:00</span></div>}
                  </div>

                  {/* Department Breakdown */}
                  <div className="bg-white rounded-2xl shadow-sm border p-6">
                    <h3 className="font-bold mb-4">Department Breakdown</h3>
                    <div className="space-y-3">
                      {Object.entries(analytics.department_breakdown || {}).map(([dept, data]: [string, any]) => (
                        <div key={dept} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-violet-400 to-purple-500" />
                            <span className="font-medium text-sm">{dept}</span>
                          </div>
                          <span className="font-bold text-sm text-slate-700">{data.visits} visits</span>
                        </div>
                      ))}
                      {Object.keys(analytics.department_breakdown || {}).length === 0 && <div className="text-slate-400 text-sm">No department data</div>}
                    </div>
                  </div>
                </div>

                {/* Financial Summary */}
                <div className="bg-white rounded-2xl shadow-sm border p-6">
                  <h3 className="font-bold mb-4 flex items-center gap-2"><DollarSign className="text-emerald-500" />Financial Summary</h3>
                  <div className="grid grid-cols-4 gap-4">
                    {[
                      { label: "Total Revenue", value: `₹${(analytics.total_revenue || 0).toLocaleString()}`, color: "text-emerald-600 bg-emerald-50" },
                      { label: "Consultation Revenue", value: `₹${(analytics.consultation_revenue || 0).toLocaleString()}`, color: "text-blue-600 bg-blue-50" },
                      { label: "Total Deposits", value: `₹${(analytics.total_deposits || 0).toLocaleString()}`, color: "text-violet-600 bg-violet-50" },
                      { label: "Total Refunds", value: `₹${(analytics.total_refunds || 0).toLocaleString()}`, color: "text-red-600 bg-red-50" },
                    ].map((f, i) => (
                      <div key={i} className={`${f.color} p-4 rounded-xl`}>
                        <div className="text-sm font-medium opacity-70">{f.label}</div>
                        <div className="text-2xl font-black mt-1">{f.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-20 text-slate-400"><BarChart3 size={48} className="mx-auto mb-4 opacity-30" />Loading analytics...</div>
            )}
          </div>
        )}

        {/* ═════════ JOURNEY TAB ═════════ */}
        {activeTab === "journey" && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2"><Layers className="text-slate-600" />Patient Journey Tracker</h2>
            
            <div className="bg-white rounded-2xl shadow-sm border p-6">
              <div className="flex gap-3 items-end mb-6">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-600 mb-1">Select Visit</label>
                  <select className="w-full border rounded-xl px-4 py-2.5 outline-none bg-white" value={journeyVisitId} onChange={e => setJourneyVisitId(e.target.value)}>
                    <option value="">Choose a visit to track...</option>
                    {visits.map(v => <option key={v.id} value={v.id}>{v.visit_id} — {getPatientName(v.patient_id)} ({v.status})</option>)}
                  </select>
                </div>
                <button onClick={handleLoadJourney} disabled={!journeyVisitId || loading} className="bg-gradient-to-r from-slate-700 to-slate-900 text-white px-6 py-2.5 rounded-xl font-medium disabled:opacity-40">Track Journey</button>
              </div>

              {journey && (
                <div>
                  <div className="flex items-center gap-3 mb-6 bg-slate-50 p-4 rounded-xl">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center text-white font-bold text-lg">{journey.patient_name.charAt(0)}</div>
                    <div>
                      <div className="font-bold text-lg">{journey.patient_name}</div>
                      <div className="text-sm text-slate-500">UHID: {journey.uhid || "N/A"} · Visit: {journey.visit_number}</div>
                    </div>
                    <div className="ml-auto"><span className="px-3 py-1.5 rounded-full bg-indigo-100 text-indigo-700 text-sm font-bold">{journey.current_step}</span></div>
                  </div>

                  <div className="space-y-0 ml-6">
                    {journey.steps.map((step, i) => (
                      <div key={i} className="flex gap-4">
                        <div className="flex flex-col items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                            step.status === "completed" ? "bg-emerald-500 text-white" :
                            step.status === "in_progress" ? "bg-blue-500 text-white ring-4 ring-blue-100" :
                            "bg-slate-200 text-slate-500"
                          }`}>{i + 1}</div>
                          {i < journey.steps.length - 1 && <div className={`w-0.5 h-12 ${step.status === "completed" ? "bg-emerald-300" : "bg-slate-200"}`} />}
                        </div>
                        <div className="pb-8">
                          <div className="font-semibold text-slate-800">{step.step_name}</div>
                          <div className={`text-xs font-bold mt-0.5 ${
                            step.status === "completed" ? "text-emerald-600" :
                            step.status === "in_progress" ? "text-blue-600" :
                            "text-slate-400"
                          }`}>{step.status.replace(/_/g," ").toUpperCase()}</div>
                          {step.timestamp && <div className="text-xs text-slate-400 mt-0.5">{new Date(step.timestamp).toLocaleString()}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!journey && <div className="text-center py-16 text-slate-400"><Layers size={48} className="mx-auto mb-4 opacity-30" />Select a visit to track the patient journey</div>}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
