"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "@/i18n";
import { LanguageSelector } from "@/components/ui/LanguageSelector";

/* ─── Role-based visibility map ──────────────────────── */
type UserRole = "admin" | "doctor" | "nurse" | "pharmacist" | "lab_technician" | "front_desk" | "director" | "all";

interface NavChild {
  label: string;
  href: string;
  badge?: string;
  roles?: UserRole[];
}

interface NavGroup {
  section: string;
  icon: React.ReactNode;
  roles?: UserRole[];
  children: NavChild[];
  href?: string; // direct link (no children)
}

/* ─── SVG Icon helpers (inline for zero deps) ───── */
const Icon = {
  dashboard: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
    </svg>
  ),
  patients: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
    </svg>
  ),
  clinical: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  opd: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
    </svg>
  ),
  ipd: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z" />
    </svg>
  ),
  diagnostics: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  ),
  pharmacy: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  ),
  er: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
    </svg>
  ),
  finance: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18v-.008zm-12 0h.008v.008H6v-.008z" />
    </svg>
  ),
  admin: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
    </svg>
  ),
  analytics: (
    <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  ),
  chevron: (
    <svg className="w-4 h-4 transition-transform duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
    </svg>
  ),
};

/* ─── Full Navigation Structure ──────────────────── */
const NAV_GROUPS: NavGroup[] = [
  {
    section: "Dashboard",
    icon: Icon.dashboard,
    href: "/dashboard",
    children: [],
  },
  {
    section: "Patients",
    icon: Icon.patients,
    children: [
      { label: "Patient Registry", href: "/dashboard/patients" },
      { label: "Encounters", href: "/dashboard/encounters" },
      { label: "Scheduling", href: "/dashboard/scheduling" },
    ],
  },
  {
    section: "Clinical Workspace",
    icon: Icon.clinical,
    roles: ["doctor", "nurse", "admin", "director"],
    children: [
      { label: "RPIW Workspace", href: "/dashboard/rpiw-workspace", badge: "RPIW" },
      { label: "Tasks", href: "/dashboard/tasks" },
      { label: "Orders", href: "/dashboard/orders" },
      { label: "Doctor Desk", href: "/dashboard/doctor-desk", badge: "EMR", roles: ["doctor", "admin"] },
    ],
  },
  {
    section: "Outpatient (OPD)",
    icon: Icon.opd,
    roles: ["doctor", "nurse", "front_desk", "admin", "director"],
    children: [
      { label: "OPD Command Center", href: "/dashboard/opd", badge: "NEW" },
      { label: "OPD Visits", href: "/dashboard/opd-visits", badge: "AI" },
      { label: "Smart Queue", href: "/dashboard/smart-queue" },
      { label: "Nursing Triage", href: "/dashboard/nursing-triage", roles: ["nurse", "doctor", "admin"] },
    ],
  },
  {
    section: "Emergency (ER)",
    icon: Icon.er,
    roles: ["doctor", "nurse", "front_desk", "admin", "director"],
    children: [
      { label: "Command Center", href: "/dashboard/er", badge: "ER" },
      { label: "Operating Theatre", href: "/dashboard/ot", badge: "OT" },
    ],
  },
  {
    section: "Inpatient (IPD)",
    icon: Icon.ipd,
    roles: ["doctor", "nurse", "front_desk", "admin", "director"],
    children: [
      { label: "Admissions", href: "/dashboard/ipd", badge: "IPD" },
      { label: "Ward Board", href: "/dashboard/wards" },
      { label: "Nursing Station", href: "/dashboard/nursing-ipd", roles: ["nurse", "admin"] },
      { label: "Nursing Vitals", href: "/dashboard/nursing-vitals", roles: ["nurse", "admin"] },
      { label: "Doctor Rounds", href: "/dashboard/ipd-doctor-desk", badge: "IPD", roles: ["doctor", "admin"] },
      { label: "Orders", href: "/dashboard/ipd-orders" },
      { label: "Bed Transfers", href: "/dashboard/ipd-transfers" },
      { label: "IPD Billing", href: "/dashboard/ipd-billing" },
      { label: "Consent Forms", href: "/dashboard/ipd-consent", roles: ["doctor", "nurse", "admin"] },
      { label: "Diet Management", href: "/dashboard/ipd-diet", roles: ["doctor", "nurse", "admin"] },
      { label: "Visitor & MLC", href: "/dashboard/visitor-mlc" },
      { label: "Smart Discharge", href: "/dashboard/ipd-discharge" },
    ],
  },
  {
    section: "Diagnostics",
    icon: Icon.diagnostics,
    roles: ["doctor", "nurse", "lab_technician", "admin", "director"],
    children: [
      { label: "LIS Orders", href: "/dashboard/lis-orders", badge: "LIS" },
      { label: "Phlebotomy", href: "/dashboard/phlebotomy", roles: ["lab_technician", "nurse", "admin"] },
      { label: "Sample Receiving", href: "/dashboard/central-receiving", roles: ["lab_technician", "admin"] },
      { label: "Lab Processing", href: "/dashboard/lab-processing", badge: "WORKFLOW", roles: ["lab_technician", "admin"] },
      { label: "Analyzer Hub", href: "/dashboard/analyzer-integration", badge: "HL7", roles: ["lab_technician", "admin"] },
      { label: "Validation Desk", href: "/dashboard/result-validation", roles: ["lab_technician", "doctor", "admin"] },
      { label: "Report Handover", href: "/dashboard/reporting-release", roles: ["lab_technician", "admin"] },
      { label: "Laboratory", href: "/dashboard/lab" },
      { label: "Advanced Diagnostics", href: "/dashboard/advanced-lab" },
      { label: "Extended Lab Services", href: "/dashboard/extended-lab" },
      { label: "Radiology", href: "/dashboard/radiology" },
      { label: "Blood Bank", href: "/dashboard/blood-bank" },
    ],
  },
  {
    section: "Pharmacy",
    icon: Icon.pharmacy,
    roles: ["pharmacist", "doctor", "nurse", "admin", "director"],
    children: [
      { label: "Rx Worklist", href: "/dashboard/rx-worklist", badge: "OP", roles: ["pharmacist", "admin"] },
      { label: "Walk-in Sales", href: "/dashboard/pharmacy-sales", roles: ["pharmacist", "admin"] },
      { label: "IP Medication Issue", href: "/dashboard/ip-pharmacy-issues", roles: ["pharmacist", "nurse", "admin"] },
      { label: "Returns", href: "/dashboard/sales-returns", roles: ["pharmacist", "admin"] },
      { label: "IP Returns", href: "/dashboard/ip-pharmacy-returns", roles: ["pharmacist", "admin"] },
      { label: "Narcotics Vault", href: "/dashboard/narcotics-workbench", badge: "Rx-X", roles: ["pharmacist", "admin"] },
      { label: "Inventory Intelligence", href: "/dashboard/inventory-intelligence", roles: ["pharmacist", "admin"] },
      { label: "Pharmacy Core", href: "/dashboard/pharmacy-core", roles: ["pharmacist", "admin"] },
      { label: "Pharmacy", href: "/dashboard/pharmacy" },
      { label: "Billing & Compliance", href: "/dashboard/pharmacy-billing", roles: ["pharmacist", "admin"] },
    ],
  },
  {
    section: "Hospital Operations",
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
    ),
    roles: ["admin", "director", "nurse"],
    children: [
      { label: "Linen & Laundry", href: "/dashboard/linen", badge: "OPS" },
      { label: "CSSD", href: "/dashboard/cssd", badge: "STERILE" },
    ],
  },
  {
    section: "Finance & Billing",
    icon: Icon.finance,
    roles: ["admin", "front_desk", "director"],
    children: [
      { label: "Billing Hub", href: "/dashboard/billing", badge: "HUB" },
      { label: "Billing Masters", href: "/dashboard/billing-masters", badge: "CONFIG" },
      { label: "RCM Billing", href: "/dashboard/rcm-billing", badge: "FINANCE" },
    ],
  },
  {
    section: "Administration",
    icon: Icon.admin,
    roles: ["admin", "front_desk", "director"],
    children: [
      { label: "Organizations (SaaS)", href: "/dashboard/administration/organizations", badge: "MASTER" },
      { label: "Users", href: "/dashboard/users", roles: ["admin", "director"] },
      { label: "System Settings", href: "/dashboard/settings", roles: ["admin"] },
      { label: "Core System", href: "/dashboard/system", roles: ["admin"] },
      { label: "Audit Logs", href: "/dashboard/audit", roles: ["admin", "director"] },
      { label: "Notifications", href: "/dashboard/notifications" },
      { label: "Language Management", href: "/dashboard/admin/languages", badge: "i18n", roles: ["admin"] },
      { label: "Communication", href: "/communication" },
    ],
  },
  {
    section: "Analytics & AI",
    icon: Icon.analytics,
    roles: ["admin", "director", "doctor"],
    children: [
      { label: "BI Intelligence", href: "/dashboard/bi-intelligence", badge: "ANALYTICS" },
      { label: "Analytics", href: "/dashboard/analytics" },
      { label: "AI Platform", href: "/dashboard/ai", badge: "NEW" },
    ],
  },
  {
    section: "Virtual Avatar",
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
      </svg>
    ),
    children: [
      { label: "Avatar Kiosk", href: "/dashboard/avatar", badge: "AI" },
      { label: "Avatar Admin", href: "/dashboard/avatar-admin", badge: "CONFIG", roles: ["admin" as UserRole] },
    ],
  },
  {
    section: "Operating Theatre",
    icon: (
      <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
    href: "/ot",
    roles: ["doctor", "nurse", "admin", "director"],
    children: [],
  },
];

/* ─── Helpers ─────────────────────────────────────── */
function getUserRole(): UserRole {
  if (typeof window === "undefined") return "admin";
  try {
    const userData = localStorage.getItem("user");
    if (userData) {
      const user = JSON.parse(userData);
      return (user.role || "admin").toLowerCase() as UserRole;
    }
  } catch { /* fallback */ }
  return "admin";
}

function isItemVisible(item: { roles?: UserRole[] }, userRole: UserRole): boolean {
  if (!item.roles || item.roles.length === 0) return true;
  if (userRole === "admin" || userRole === "director") return true;
  return item.roles.includes(userRole);
}

/* ─── Sidebar Component ──────────────────────────── */
// Label → i18n key mapping for sidebar navigation
const LABEL_I18N_MAP: Record<string, string> = {
  "Dashboard": "nav.dashboard", "Patients": "nav.patients", "Patient Management": "nav.patients", "Patient Registry": "nav.patientRegistry",
  "Encounters": "nav.encounters", "Scheduling": "nav.scheduling", "Clinical Workspace": "nav.clinicalOps",
  "Doctor Desk": "nav.doctorDesk", "Outpatient (OPD)": "nav.opdVisits", "OPD Visits": "nav.opdVisits",
  "Smart Queue": "nav.smartQueue", "Nursing Triage": "nav.nursingTriage",
  "Emergency (ER)": "nav.emergencyRoom", "Command Center": "nav.emergencyRoom",
  "Operating Theatre": "nav.operationTheater",
  "Inpatient (IPD)": "nav.ipdManagement", "Admissions": "nav.ipdAdmissions",
  "Ward Board": "nav.wardsAndBeds", "Nursing Station": "nav.ipdNursing",
  "Nursing Vitals": "nav.ipdNursing", "Doctor Rounds": "nav.ipdDoctorDesk",
  "IPD Billing": "nav.ipdBilling", "Bed Transfers": "nav.ipdTransfers",
  "Smart Discharge": "nav.ipdDischarge",
  "Consent Forms": "nav.ipdConsent", "Diet Management": "nav.ipdDiet",
  "Diagnostics": "nav.laboratory", "LIS Orders": "nav.lisOrders",
  "Lab Processing": "nav.labProcessing", "Validation Desk": "nav.resultValidation",
  "Laboratory": "nav.laboratory", "Radiology": "nav.radiology", "Blood Bank": "nav.bloodBank",
  "Pharmacy": "nav.pharmacy", "Pharmacy Core": "nav.pharmacyCore",
  "Walk-in Sales": "nav.pharmacySales", "Billing & Compliance": "nav.pharmacyBilling",
  "Finance & Billing": "nav.billing", "Billing Hub": "nav.billing",
  "Billing Masters": "nav.billingMasters", "RCM Billing": "nav.rcmBilling",
  "Administration": "nav.administration", "Users": "nav.users",
  "Hospital Operations": "nav.hospitalOps", "Linen & Laundry": "nav.linenLaundry", "CSSD": "nav.cssd",
  "System Settings": "nav.systemSettings", "Audit Logs": "nav.audit",
  "Notifications": "common.notifications",
  "Analytics & AI": "nav.analytics", "Analytics": "nav.analytics",
  "Language Management": "admin.languageManagement",

  "RPIW Workspace": "nav.rpiwWorkspace",
  "Tasks": "nav.tasks",
  "Orders": "nav.clinicalOrders",
  "Visitor & MLC": "nav.visitorMlc",
  "Sample Receiving": "nav.sampleReceiving",
  "Analyzer Hub": "nav.analyzerHub",
  "Report Handover": "nav.reportHandover",
  "Advanced Diagnostics": "nav.advancedDiagnostics",
  "Extended Lab Services": "nav.extendedLab",
  "Rx Worklist": "nav.rxWorklist",
  "IP Medication Issue": "nav.ipMedicationIssue",
  "Returns": "nav.pharmacyReturns",
  "IP Returns": "nav.ipPharmacyReturns",
  "Narcotics Vault": "nav.narcoticsVault",
  "Inventory Intelligence": "nav.inventoryIntelligence",
  "Organizations (SaaS)": "nav.organizations",
  "Core System": "nav.coreSystem",
  "Communication": "nav.communication",
  "BI Intelligence": "nav.biIntelligence",
  "AI Platform": "nav.aiPlatform",
  "Virtual Avatar": "nav.virtualAvatar",
  "Avatar Kiosk": "nav.avatarKiosk",
  "Avatar Admin": "nav.avatarAdmin",
};

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [userRole, setUserRole] = useState<UserRole>("admin");
  const [collapsed, setCollapsed] = useState(false);

  // Translate a label using the mapping, fallback to original English
  const tLabel = (label: string) => {
    const key = LABEL_I18N_MAP[label];
    if (key) {
      const translated = t(key);
      return translated !== key ? translated : label;
    }
    return label;
  };

  // Determine role on mount
  useEffect(() => {
    setUserRole(getUserRole());
  }, []);

  // Auto-expand the section containing the current route
  useEffect(() => {
    NAV_GROUPS.forEach((group) => {
      const isChildActive = group.children.some((child) =>
        pathname === child.href || pathname.startsWith(child.href + "/")
      );
      const isDirectActive = group.href && (pathname === group.href || pathname.startsWith(group.href + "/"));
      if (isChildActive || isDirectActive) {
        setExpandedSections((prev) => new Set([...prev, group.section]));
      }
    });
  }, [pathname]);

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) next.delete(section);
      else next.add(section);
      return next;
    });
  };

  return (
    <aside
      className={`sidebar-enterprise ${collapsed ? "sidebar-collapsed" : ""}`}
      id="main-sidebar"
    >
      {/* ─── Brand ─── */}
      <div className="sidebar-brand-enterprise">
        <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
          <span className="text-white text-base font-bold">A</span>
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <span className="text-white font-bold text-[15px] tracking-tight">AXON</span>
            <span className="text-blue-400 font-bold text-[15px]">HIS</span>
            <p className="text-slate-500 text-[10px] font-medium tracking-wider uppercase">Enterprise Clinical</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto text-slate-500 hover:text-slate-300 transition-colors p-1 rounded-lg hover:bg-slate-700/50"
          aria-label="Toggle sidebar"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {collapsed ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            )}
          </svg>
        </button>
      </div>

      {/* ─── Role Badge & Language ─── */}
      {!collapsed && (
        <div className="px-4 pb-2 flex flex-col gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-700/50 border border-slate-600/30">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              {t(`roles.${userRole}`) || userRole.replace("_", " ")}
            </span>
          </div>
          <div className="flex justify-between items-center px-1">
            <span className="text-[10px] text-slate-500 font-medium">{t("nav.languageLabel") || "LANGUAGE"}</span>
            <LanguageSelector />
          </div>
        </div>
      )}
      {collapsed && (
        <div className="px-2 pb-2 flex justify-center">
            <LanguageSelector />
        </div>
      )}

      {/* ─── Navigation ─── */}
      <nav className="sidebar-nav-enterprise">
        {NAV_GROUPS.filter((group) => isItemVisible(group, userRole)).map((group) => {
          const isExpanded = expandedSections.has(group.section);

          // Direct link group (no children)
          if (group.href && group.children.length === 0) {
            const isActive = pathname === group.href || pathname.startsWith(group.href + "/");
            return (
              <div key={group.section} className="mb-0.5">
                <Link
                  href={group.href}
                  className={`sidebar-group-header ${isActive ? "sidebar-group-active" : ""}`}
                  title={collapsed ? tLabel(group.section) : undefined}
                >
                  <span className="sidebar-group-icon">{group.icon}</span>
                  {!collapsed && <span className="sidebar-group-label">{tLabel(group.section)}</span>}
                </Link>
              </div>
            );
          }

          // Collapsible group
          const visibleChildren = group.children.filter((child) => isItemVisible(child, userRole));
          if (visibleChildren.length === 0) return null;

          const hasActiveChild = visibleChildren.some(
            (child) => pathname === child.href || pathname.startsWith(child.href + "/")
          );

          return (
            <div key={group.section} className="mb-0.5">
              <button
                onClick={() => toggleSection(group.section)}
                className={`sidebar-group-header w-full ${hasActiveChild ? "sidebar-group-active" : ""}`}
                title={collapsed ? tLabel(group.section) : undefined}
              >
                <span className="sidebar-group-icon">{group.icon}</span>
                {!collapsed && (
                  <>
                    <span className="sidebar-group-label">{tLabel(group.section)}</span>
                    <span className={`ml-auto transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}>
                      {Icon.chevron}
                    </span>
                  </>
                )}
              </button>

              {/* Child items — animated expand/collapse */}
              {!collapsed && isExpanded && (
                <div className="sidebar-children">
                  {visibleChildren.map((child) => {
                    const isActive = pathname === child.href || pathname.startsWith(child.href + "/");
                    return (
                      <Link
                        key={child.href}
                        href={child.href}
                        className={`sidebar-child-link ${isActive ? "sidebar-child-active" : ""}`}
                      >
                        <span className={`sidebar-child-dot ${isActive ? "bg-blue-400" : "bg-slate-600"}`}></span>
                        <span className="flex-1 truncate">{tLabel(child.label)}</span>
                        {child.badge && (
                          <span className="sidebar-badge">{child.badge}</span>
                        )}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* ─── Footer ─── */}
      <div className="sidebar-footer-enterprise border-t border-slate-800/50 mt-auto pt-4 flex flex-col gap-4">
        {!collapsed ? (
          <>
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span className="text-[11px] text-slate-500">{tLabel("System Online") || "System Online"}</span>
              </div>
              <p className="text-[10px] text-slate-600">v1.0.0 — Enterprise Clinical Platform</p>
            </div>
          </>
        ) : (
          <div className="flex flex-col gap-4 items-center">
            <span className="w-2 h-2 rounded-full bg-emerald-400 block"></span>
          </div>
        )}
      </div>
    </aside>
  );
}
