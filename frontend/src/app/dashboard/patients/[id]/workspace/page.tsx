"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

/* ── Types ────────────────────────────── */
interface Patient {
  id: string;
  uhid?: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  gender?: string;
  phone?: string;
  email?: string;
  blood_group?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  allergies?: string;
  medical_history?: string;
}

interface Encounter {
  id: string;
  encounter_type: string;
  status: string;
  created_at: string;
  chief_complaint?: string;
  department?: string;
}

interface Order {
  id: string;
  order_type: string;
  status: string;
  created_at: string;
  item_name?: string;
  priority?: string;
}

interface Task {
  id: string;
  title: string;
  status: string;
  priority?: string;
  created_at: string;
  assigned_to?: string;
}

interface Invoice {
  id: string;
  total_amount: number;
  status: string;
  created_at: string;
  invoice_number?: string;
}

const TABS = [
  { key: "summary", label: "Summary", icon: "📋" },
  { key: "encounters", label: "Encounters", icon: "🩺" },
  { key: "vitals", label: "Vitals", icon: "❤️" },
  { key: "diagnosis", label: "Diagnosis", icon: "🧠" },
  { key: "orders", label: "Orders", icon: "📝" },
  { key: "labs", label: "Labs", icon: "🔬" },
  { key: "medications", label: "Medications", icon: "💊" },
  { key: "tasks", label: "Tasks", icon: "✅" },
  { key: "billing", label: "Billing", icon: "💳" },
  { key: "notes", label: "Notes", icon: "📒" },
  { key: "history", label: "History", icon: "📁" },
] as const;

type TabKey = typeof TABS[number]["key"];

/* ── Utility ─────────────────────────── */
function getAge(dob: string | undefined): string {
  if (!dob) return "—";
  const diff = Date.now() - new Date(dob).getTime();
  return `${Math.floor(diff / (365.25 * 24 * 60 * 60 * 1000))}y`;
}

function formatDate(d: string | undefined): string {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

function statusColor(status: string): string {
  const s = status.toLowerCase();
  if (["completed", "paid", "done", "dispensed", "active", "in_progress"].includes(s))
    return "bg-emerald-100 text-emerald-700";
  if (["pending", "issued", "scheduled", "assigned"].includes(s))
    return "bg-amber-100 text-amber-700";
  if (["cancelled", "rejected", "failed"].includes(s))
    return "bg-red-100 text-red-700";
  return "bg-slate-100 text-slate-600";
}

/* ══════════════════════════════════════════════════════════════════
   PATIENT WORKSPACE PAGE
   ══════════════════════════════════════════════════════════════════ */
export default function PatientWorkspacePage() {
  const { t } = useTranslation();
  const params = useParams();
  const router = useRouter();
  const patientId = params.id as string;

  const [patient, setPatient] = useState<Patient | null>(null);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [prescriptions, setPrescriptions] = useState<any[]>([]);
  const [labResults, setLabResults] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<TabKey>("summary");
  const [loading, setLoading] = useState(true);

  const loadPatientData = useCallback(async () => {
    const headers = authHeaders();
    setLoading(true);
    try {
      // Fetch patient info
      const patRes = await fetch(`${API}/api/v1/patients/${patientId}`, { headers });
      if (patRes.ok) {
        const patData = await patRes.json();
        setPatient(patData);
      }

      // Fetch related data in parallel
      const [encRes, taskRes, invoiceRes, rxRes] = await Promise.allSettled([
        fetch(`${API}/api/v1/encounters/?patient_id=${patientId}`, { headers }),
        fetch(`${API}/api/v1/tasks?patient_id=${patientId}`, { headers }),
        fetch(`${API}/api/v1/billing/invoices?patient_id=${patientId}`, { headers }),
        fetch(`${API}/api/v1/pharmacy/prescriptions?patient_id=${patientId}`, { headers }),
      ]);

      const getJson = async (r: PromiseSettledResult<Response>) => {
        if (r.status === "fulfilled" && r.value.ok) return r.value.json();
        return null;
      };

      const [encData, taskData, invoiceData, rxData] = await Promise.all([
        getJson(encRes), getJson(taskRes), getJson(invoiceRes), getJson(rxRes),
      ]);

      setEncounters(Array.isArray(encData) ? encData : []);
      setTasks(Array.isArray(taskData) ? taskData : []);
      setInvoices(Array.isArray(invoiceData) ? invoiceData : []);
      setPrescriptions(Array.isArray(rxData) ? rxData : []);
    } catch (err) {
      console.error("Failed to load patient data:", err);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    if (patientId) loadPatientData();
  }, [patientId, loadPatientData]);

  if (loading) {
    return (
      <div>
        <TopNav title="Patient Workspace" />
        <div className="flex h-[80vh] items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-3 border-blue-200 border-t-blue-500 rounded-full animate-spin"></div>
            <p className="text-sm text-slate-400">Loading patient workspace...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div>
        <TopNav title="Patient Workspace" />
        <div className="flex h-[80vh] items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-slate-700">Patient not found</p>
            <p className="text-sm text-slate-400 mt-1">The patient record may have been removed.</p>
            <button onClick={() => router.push("/dashboard/patients")} className="btn-primary mt-4">
              Go to Patient Registry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const activeEncounters = encounters.filter((e) => e.status === "in_progress" || e.status === "scheduled");
  const pendingTasks = tasks.filter((t) => ["PENDING", "ASSIGNED", "IN_PROGRESS"].includes(t.status));
  const pendingBills = invoices.filter((i) => i.status === "issued");

  return (
    <div>
      <TopNav title="Patient Workspace" />

      <div className="p-6">
        {/* ── Patient Header ── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-6">
          <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 px-6 py-5">
            <div className="flex items-start gap-5">
              {/* Avatar */}
              <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-white text-xl font-bold shadow-lg border border-white/20 shrink-0">
                {(patient.first_name?.[0] || "").toUpperCase()}
                {(patient.last_name?.[0] || "").toUpperCase()}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-bold text-white">
                  {patient.first_name} {patient.last_name}
                </h2>
                <div className="flex flex-wrap items-center gap-3 mt-1.5">
                  {patient.uhid && (
                    <span className="text-xs font-mono bg-white/15 text-white/90 px-2 py-0.5 rounded-md">
                      UHID: {patient.uhid}
                    </span>
                  )}
                  <span className="text-xs text-white/70">
                    {patient.gender === "male" ? "♂ Male" : patient.gender === "female" ? "♀ Female" : "⚥ Other"} • {getAge(patient.date_of_birth)} • DOB: {formatDate(patient.date_of_birth)}
                  </span>
                  {patient.blood_group && (
                    <span className="text-xs bg-red-500/30 text-white/90 px-1.5 py-0.5 rounded-md font-bold">
                      🩸 {patient.blood_group}
                    </span>
                  )}
                </div>
                {patient.phone && (
                  <p className="text-xs text-white/60 mt-1">📞 {patient.phone} {patient.email ? `• ✉ ${patient.email}` : ""}</p>
                )}
              </div>

              {/* Quick Stats */}
              <div className="flex gap-4 shrink-0">
                <div className="text-center bg-white/10 backdrop-blur-sm rounded-xl px-4 py-2.5 border border-white/10 min-w-[80px]">
                  <p className="text-xl font-bold text-white">{activeEncounters.length}</p>
                  <p className="text-[10px] text-white/60 mt-0.5">Active Visits</p>
                </div>
                <div className="text-center bg-white/10 backdrop-blur-sm rounded-xl px-4 py-2.5 border border-white/10 min-w-[80px]">
                  <p className="text-xl font-bold text-white">{pendingTasks.length}</p>
                  <p className="text-[10px] text-white/60 mt-0.5">Pending Tasks</p>
                </div>
                <div className="text-center bg-white/10 backdrop-blur-sm rounded-xl px-4 py-2.5 border border-white/10 min-w-[80px]">
                  <p className="text-xl font-bold text-white">{pendingBills.length}</p>
                  <p className="text-[10px] text-white/60 mt-0.5">Open Bills</p>
                </div>
              </div>
            </div>
          </div>

          {/* ── Quick Actions Bar ── */}
          <div className="px-6 py-3 bg-slate-50/80 border-t border-slate-200/50 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-400 mr-2">ACTIONS:</span>
            {[
              { label: "New Encounter", icon: "🩺", href: `/dashboard/encounters?patient_id=${patientId}` },
              { label: "Order Tests", icon: "🔬", href: `/dashboard/lis-orders?patient_id=${patientId}` },
              { label: "Prescribe", icon: "💊", href: `/dashboard/pharmacy?patient_id=${patientId}` },
              { label: "Assign Task", icon: "✅", href: `/dashboard/tasks?patient_id=${patientId}` },
              { label: "Create Bill", icon: "💳", href: `/dashboard/patients/${patientId}/billing` },
              { label: "View OPD", icon: "⚡", href: `/dashboard/opd-visits?patient_id=${patientId}` },
              { label: "Admit (IPD)", icon: "🏥", href: `/dashboard/ipd?patient_id=${patientId}` },
            ].map((action) => (
              <Link
                key={action.label}
                href={action.href}
                className="workspace-action-btn text-xs border-slate-200 text-slate-600 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200"
              >
                <span>{action.icon}</span>
                {action.label}
              </Link>
            ))}
          </div>
        </div>

        {/* ── Alerts ── */}
        {patient.allergies && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
            <span className="text-lg">⚠️</span>
            <div>
              <p className="text-xs font-bold text-red-800">ALLERGY ALERT</p>
              <p className="text-sm text-red-700">{patient.allergies}</p>
            </div>
          </div>
        )}

        {/* ── Tab Navigation ── */}
        <div className="flex items-center gap-1 mb-6 bg-white rounded-xl border border-slate-200 p-1.5 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`workspace-tab whitespace-nowrap ${activeTab === tab.key ? "workspace-tab-active" : ""}`}
            >
              <span className="mr-1.5">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── Tab Content ── */}
        <div className="min-h-[400px]">
          {/* SUMMARY TAB */}
          {activeTab === "summary" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Patient Details */}
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center text-sm">👤</span>
                  Patient Details
                </h3>
                <dl className="space-y-3 text-sm">
                  {[
                    ["Full Name", `${patient.first_name} ${patient.last_name}`],
                    ["Gender", patient.gender || "—"],
                    ["Date of Birth", formatDate(patient.date_of_birth)],
                    ["Age", getAge(patient.date_of_birth)],
                    ["Phone", patient.phone || "—"],
                    ["Email", patient.email || "—"],
                    ["Blood Group", patient.blood_group || "—"],
                    ["Address", patient.address || "—"],
                    ["Emergency Contact", patient.emergency_contact_name || "—"],
                    ["Emergency Phone", patient.emergency_contact_phone || "—"],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between">
                      <dt className="text-slate-400 font-medium">{label}</dt>
                      <dd className="text-slate-700 font-medium text-right max-w-[60%] truncate">{value}</dd>
                    </div>
                  ))}
                </dl>
              </div>

              {/* Recent Encounters */}
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center text-sm">🩺</span>
                  Recent Encounters
                </h3>
                {encounters.length === 0 ? (
                  <p className="text-sm text-slate-400 text-center py-8">No encounters yet</p>
                ) : (
                  <div className="space-y-2">
                    {encounters.slice(0, 5).map((enc) => (
                      <Link
                        key={enc.id}
                        href={`/dashboard/encounters/${enc.id}`}
                        className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-slate-50 transition-colors"
                      >
                        <div className={`w-2 h-2 rounded-full ${enc.status === "in_progress" ? "bg-emerald-500 animate-pulse" : enc.status === "completed" ? "bg-slate-300" : "bg-amber-500"}`}></div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-slate-700 truncate">
                            {enc.encounter_type} {enc.chief_complaint ? `— ${enc.chief_complaint}` : ""}
                          </p>
                          <p className="text-[11px] text-slate-400">{formatDate(enc.created_at)}</p>
                        </div>
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusColor(enc.status)}`}>
                          {enc.status.replace("_", " ")}
                        </span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              {/* Pending Items */}
              <div className="space-y-4">
                {/* Pending Tasks */}
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                  <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <span className="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center text-sm">✅</span>
                    Pending Tasks ({pendingTasks.length})
                  </h3>
                  {pendingTasks.length === 0 ? (
                    <p className="text-sm text-slate-400 text-center py-4">All clear!</p>
                  ) : (
                    <div className="space-y-2">
                      {pendingTasks.slice(0, 4).map((task) => (
                        <div key={task.id} className="flex items-center gap-2 p-2 rounded-lg bg-amber-50/50 border border-amber-100">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                          <p className="text-xs text-slate-700 flex-1 truncate">{task.title}</p>
                          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${statusColor(task.status)}`}>
                            {task.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Medications */}
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                  <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <span className="w-7 h-7 rounded-lg bg-violet-50 flex items-center justify-center text-sm">💊</span>
                    Current Medications ({prescriptions.length})
                  </h3>
                  {prescriptions.length === 0 ? (
                    <p className="text-sm text-slate-400 text-center py-4">No active prescriptions</p>
                  ) : (
                    <div className="space-y-2">
                      {prescriptions.slice(0, 4).map((rx: any) => (
                        <div key={rx.id} className="flex items-center gap-2 p-2 rounded-lg bg-violet-50/50 border border-violet-100">
                          <span className="text-sm">💊</span>
                          <p className="text-xs text-slate-700 flex-1 truncate">{rx.drug_name || rx.medication || "Prescription"}</p>
                          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${statusColor(rx.status || "pending")}`}>
                            {rx.status || "pending"}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ENCOUNTERS TAB */}
          {activeTab === "encounters" && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-slate-800">All Encounters</h3>
                <Link href={`/dashboard/encounters?patient_id=${patientId}`} className="btn-primary btn-sm">
                  + New Encounter
                </Link>
              </div>
              {encounters.length === 0 ? (
                <div className="px-5 py-12 text-center text-slate-400">No encounters found</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type</th>
                      <th>Chief Complaint</th>
                      <th>Department</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {encounters.map((enc) => (
                      <tr key={enc.id}>
                        <td className="text-xs text-slate-500">{formatDate(enc.created_at)}</td>
                        <td className="font-medium text-slate-700">{enc.encounter_type}</td>
                        <td className="text-slate-600">{enc.chief_complaint || "—"}</td>
                        <td className="text-slate-500">{enc.department || "—"}</td>
                        <td>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusColor(enc.status)}`}>
                            {enc.status.replace("_", " ")}
                          </span>
                        </td>
                        <td>
                          <Link href={`/dashboard/encounters/${enc.id}`} className="text-blue-600 text-xs hover:underline">
                            View →
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* ORDERS TAB */}
          {activeTab === "orders" && (
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-800">Orders</h3>
                <Link href={`/dashboard/orders?patient_id=${patientId}`} className="btn-primary btn-sm">
                  + New Order
                </Link>
              </div>
              <p className="text-sm text-slate-400 text-center py-8">
                Orders are managed through encounters. Select an encounter to view or create orders.
              </p>
              {encounters.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                  {encounters.slice(0, 6).map((enc) => (
                    <Link
                      key={enc.id}
                      href={`/dashboard/encounters/${enc.id}`}
                      className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
                    >
                      <span className={`w-2 h-2 rounded-full ${enc.status === "in_progress" ? "bg-emerald-500" : "bg-slate-300"}`}></span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-slate-700 truncate">{enc.encounter_type}</p>
                        <p className="text-xs text-slate-400">{formatDate(enc.created_at)}</p>
                      </div>
                      <span className="text-xs text-blue-600">View Orders →</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* VITALS TAB */}
          {activeTab === "vitals" && (
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-800">Clinical Vitals</h3>
                <Link href={`/dashboard/nursing-vitals?patient_id=${patientId}`} className="btn-primary btn-sm">
                  + Record Vitals
                </Link>
              </div>
              <p className="text-sm text-slate-400 text-center py-8">
                Vitals are recorded by nursing staff across OPD and IPD modules.
              </p>
            </div>
          )}

          {/* DIAGNOSIS TAB */}
          {activeTab === "diagnosis" && (
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="font-semibold text-slate-800">Clinical Diagnosis</h3>
              <p className="text-sm text-slate-400 text-center py-8">
                Diagnoses are documented by physicians during encounters.
              </p>
            </div>
          )}

          {/* LABS TAB */}
          {activeTab === "labs" && (
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-800">Lab Results</h3>
                <Link href={`/dashboard/lis-orders?patient_id=${patientId}`} className="btn-primary btn-sm">
                  + Order Lab Test
                </Link>
              </div>
              {/* LIS Pipeline Visualization */}
              <div className="mb-6 p-4 bg-gradient-to-r from-cyan-50 to-blue-50 rounded-xl border border-cyan-100">
                <p className="text-xs font-bold text-cyan-800 mb-3">LAB WORKFLOW PIPELINE</p>
                <div className="flex items-center gap-1 overflow-x-auto pb-2">
                  {["Order", "Phlebotomy", "Receiving", "Processing", "Analyzer", "Validation", "Report"].map((step, i) => (
                    <React.Fragment key={step}>
                      <div className="flex flex-col items-center min-w-[80px]">
                        <div className={`workflow-step-circle ${i === 0 ? "workflow-step-done" : "workflow-step-pending"}`}>
                          {i + 1}
                        </div>
                        <p className="text-[10px] text-slate-500 mt-1 font-medium text-center">{step}</p>
                      </div>
                      {i < 6 && (
                        <div className={`workflow-connector ${i === 0 ? "bg-emerald-300" : "bg-slate-200"}`}></div>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
              <p className="text-sm text-slate-400 text-center py-4">
                Lab results are linked through encounters and LIS orders.
              </p>
            </div>
          )}

          {/* MEDICATIONS TAB */}
          {activeTab === "medications" && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-slate-800">Medications & Prescriptions</h3>
                <Link href={`/dashboard/pharmacy?patient_id=${patientId}`} className="btn-primary btn-sm">
                  + New Prescription
                </Link>
              </div>
              {/* Pharmacy Workflow */}
              <div className="p-4 bg-gradient-to-r from-violet-50 to-purple-50 border-b border-violet-100">
                <p className="text-xs font-bold text-violet-800 mb-3">PHARMACY WORKFLOW</p>
                <div className="flex items-center gap-1 overflow-x-auto pb-2">
                  {["Prescription", "Verification", "Dispensing", "Nursing Accept", "Returns", "Billing"].map((step, i) => (
                    <React.Fragment key={step}>
                      <div className="flex flex-col items-center min-w-[80px]">
                        <div className={`workflow-step-circle ${i <= 0 ? "workflow-step-done" : "workflow-step-pending"}`}>
                          {i + 1}
                        </div>
                        <p className="text-[10px] text-slate-500 mt-1 font-medium text-center">{step}</p>
                      </div>
                      {i < 5 && (
                        <div className={`workflow-connector ${i < 0 ? "bg-emerald-300" : "bg-slate-200"}`}></div>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
              {prescriptions.length === 0 ? (
                <div className="px-5 py-12 text-center text-slate-400">No prescriptions found</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Medication</th>
                      <th>Status</th>
                      <th>Date</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {prescriptions.map((rx: any) => (
                      <tr key={rx.id}>
                        <td className="font-medium text-slate-700">{rx.drug_name || rx.medication || "Prescription"}</td>
                        <td>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusColor(rx.status || "pending")}`}>
                            {rx.status || "pending"}
                          </span>
                        </td>
                        <td className="text-xs text-slate-500">{formatDate(rx.created_at)}</td>
                        <td>
                          {rx.id && (
                            <Link href={`/dashboard/pharmacy/prescriptions/${rx.id}`} className="text-blue-600 text-xs hover:underline">
                              View →
                            </Link>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* TASKS TAB */}
          {activeTab === "tasks" && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-slate-800">Tasks & Workflows</h3>
                <Link href={`/dashboard/tasks?patient_id=${patientId}`} className="btn-primary btn-sm">
                  + Assign Task
                </Link>
              </div>
              {tasks.length === 0 ? (
                <div className="px-5 py-12 text-center text-slate-400">No tasks assigned</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Task</th>
                      <th>Status</th>
                      <th>Priority</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasks.map((task) => (
                      <tr key={task.id}>
                        <td className="font-medium text-slate-700">{task.title}</td>
                        <td>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusColor(task.status)}`}>
                            {task.status}
                          </span>
                        </td>
                        <td className="text-xs text-slate-500">{task.priority || "Normal"}</td>
                        <td className="text-xs text-slate-500">{formatDate(task.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* BILLING TAB */}
          {activeTab === "billing" && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="font-semibold text-slate-800">Billing & Invoices</h3>
                <Link href={`/dashboard/patients/${patientId}/billing`} className="btn-primary btn-sm">
                  + Create Invoice
                </Link>
              </div>
              {invoices.length === 0 ? (
                <div className="px-5 py-12 text-center text-slate-400">No invoices found</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Invoice #</th>
                      <th>Amount</th>
                      <th>Status</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoices.map((inv) => (
                      <tr key={inv.id}>
                        <td className="font-medium text-slate-700 font-mono text-xs">{inv.invoice_number || inv.id.slice(0, 8)}</td>
                        <td className="font-bold text-slate-800">₹{inv.total_amount?.toLocaleString("en-IN") || "0"}</td>
                        <td>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusColor(inv.status)}`}>
                            {inv.status}
                          </span>
                        </td>
                        <td className="text-xs text-slate-500">{formatDate(inv.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* NOTES TAB */}
          {activeTab === "notes" && (
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="font-semibold text-slate-800 mb-4">Clinical Notes</h3>
              <p className="text-sm text-slate-400 text-center py-8">
                Clinical notes are available within each encounter. Select an encounter to view notes.
              </p>
              {encounters.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {encounters.slice(0, 6).map((enc) => (
                    <Link
                      key={enc.id}
                      href={`/dashboard/encounters/${enc.id}`}
                      className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
                    >
                      <span className="text-lg">📝</span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-slate-700 truncate">{enc.encounter_type} — {formatDate(enc.created_at)}</p>
                        <p className="text-xs text-slate-400">{enc.chief_complaint || "No chief complaint"}</p>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* HISTORY TAB */}
          {activeTab === "history" && (
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="font-semibold text-slate-800 mb-4">Patient History</h3>
              {patient.medical_history ? (
                <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <p className="text-sm text-slate-700 whitespace-pre-wrap">{patient.medical_history}</p>
                </div>
              ) : (
                <p className="text-sm text-slate-400 text-center py-4">No medical history recorded</p>
              )}

              {/* Timeline */}
              <h4 className="font-semibold text-slate-700 mt-6 mb-3">Visit Timeline</h4>
              {encounters.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">No visit history</p>
              ) : (
                <div className="relative pl-6 border-l-2 border-slate-200 space-y-4">
                  {encounters.map((enc) => (
                    <div key={enc.id} className="relative">
                      <div className="absolute -left-[25px] w-3 h-3 rounded-full bg-white border-2 border-blue-500"></div>
                      <Link href={`/dashboard/encounters/${enc.id}`} className="block p-3 rounded-lg hover:bg-slate-50 transition-colors">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-slate-700">{enc.encounter_type}</p>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusColor(enc.status)}`}>
                            {enc.status.replace("_", " ")}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{formatDate(enc.created_at)}</p>
                        {enc.chief_complaint && <p className="text-xs text-slate-500 mt-1">{enc.chief_complaint}</p>}
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
