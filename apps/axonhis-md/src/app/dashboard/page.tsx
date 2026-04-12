"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { TopNav } from "@/components/TopNav";
import { apiFetch } from "@/lib/api";

const modules = [
  { href: "/dashboard/organizations", icon: "🏥", name: "Organizations", desc: "Multi-org hierarchy & facility management", color: "from-blue-500 to-indigo-600" },
  { href: "/dashboard/specialties", icon: "⭐", name: "Specialty Profiles", desc: "Experience packs & AI config per specialty", color: "from-amber-500 to-orange-600" },
  { href: "/dashboard/clinicians", icon: "👨‍⚕️", name: "Clinician Registry", desc: "Doctor, nurse & technician management", color: "from-teal-500 to-emerald-600" },
  { href: "/dashboard/patients", icon: "👥", name: "Patient Management", desc: "Registration, identifiers & consent", color: "from-rose-500 to-pink-600" },
  { href: "/dashboard/channels", icon: "📡", name: "Care Channels", desc: "Clinic, teleconsult, Health ATM & hybrid", color: "from-violet-500 to-purple-600" },
  { href: "/dashboard/appointments", icon: "📅", name: "Appointments", desc: "Multi-mode scheduling engine", color: "from-sky-500 to-blue-600" },
  { href: "/dashboard/encounters", icon: "📋", name: "Encounter Workspace", desc: "Unified encounter engine", color: "from-emerald-500 to-teal-600" },
  { href: "/dashboard/orders", icon: "🧪", name: "Clinical Orders", desc: "Lab, imaging & referral orders", color: "from-cyan-500 to-teal-600" },
  { href: "/dashboard/prescriptions", icon: "💊", name: "Prescriptions", desc: "Medication orders & formulary", color: "from-red-500 to-rose-600" },
  { href: "/dashboard/devices", icon: "🔬", name: "Device Hub", desc: "Medical device integration", color: "from-indigo-500 to-violet-600" },
  { href: "/dashboard/documents", icon: "📄", name: "Documents", desc: "Clinical documents & records", color: "from-slate-500 to-gray-600" },
  { href: "/dashboard/sharing", icon: "🔗", name: "Patient Sharing", desc: "QR code & secure link sharing", color: "from-green-500 to-emerald-600" },
  { href: "/dashboard/coverage", icon: "🛡️", name: "Coverage & Payers", desc: "Insurance & coverage management", color: "from-blue-600 to-indigo-700" },
  { href: "/dashboard/billing", icon: "💳", name: "Billing", desc: "Invoices & payment processing", color: "from-amber-600 to-yellow-600" },
  { href: "/dashboard/integration", icon: "⚡", name: "Integration Hub", desc: "HL7, FHIR & system events", color: "from-purple-600 to-violet-700" },
  { href: "/dashboard/audit", icon: "🕐", name: "Audit Trail", desc: "Complete activity logging", color: "from-gray-600 to-slate-700" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    apiFetch("/dashboard/stats").then(setStats).catch(() => {});
  }, []);

  const kpis = stats ? [
    { label: "Organizations", value: stats.total_organizations, icon: "🏥", color: "teal" },
    { label: "Facilities", value: stats.total_facilities, icon: "🏢", color: "blue" },
    { label: "Clinicians", value: stats.total_clinicians, icon: "👨‍⚕️", color: "violet" },
    { label: "Patients", value: stats.total_patients, icon: "👥", color: "rose" },
    { label: "Appointments", value: stats.total_appointments, icon: "📅", color: "amber" },
    { label: "Today", value: stats.appointments_today, icon: "📌", color: "emerald" },
    { label: "Open Encounters", value: stats.open_encounters, icon: "📋", color: "teal" },
    { label: "Specialties", value: stats.total_specialties, icon: "⭐", color: "amber" },
  ] : [];

  return (<div><TopNav title="AxonHIS MD Dashboard" subtitle="Unified Clinical Practice Platform" />
    <div className="p-6 lg:p-8 space-y-8">

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-600 via-teal-700 to-cyan-800 p-8 text-white">
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/3"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/4"></div>
        <div className="relative z-10">
          <h1 className="text-3xl font-extrabold tracking-tight">AxonHIS MD</h1>
          <p className="text-teal-200 mt-2 text-sm max-w-xl">Unified Clinical Practice & Health ATM Platform — powering multi-specialty clinical workflows across all care channels.</p>
          <div className="flex gap-3 mt-5">
            {["In-Person", "Teleconsult", "Health ATM", "Hybrid"].map(m => (
              <span key={m} className="px-4 py-1.5 rounded-full bg-white/10 backdrop-blur text-xs font-semibold border border-white/20">{m}</span>
            ))}
          </div>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-4">
        {kpis.map(k => (
          <div key={k.label} className={`stat-card ${k.color}`}>
            <div className={`stat-icon ${k.color}`}>{k.icon}</div>
            <div className="stat-value">{k.value ?? "—"}</div>
            <div className="stat-label">{k.label}</div>
          </div>
        ))}
      </div>

      {/* Module Grid */}
      <div>
        <h2 className="text-lg font-bold text-slate-800 mb-4">Platform Modules</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {modules.map(m => (
            <Link key={m.href} href={m.href}>
              <div className="card card-interactive p-5 group cursor-pointer h-full">
                <div className={`h-1.5 -mx-5 -mt-5 mb-4 rounded-t-2xl bg-gradient-to-r ${m.color}`}></div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{m.icon}</span>
                  <h3 className="font-bold text-sm text-slate-800 group-hover:text-teal-700 transition">{m.name}</h3>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">{m.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div></div>);
}
