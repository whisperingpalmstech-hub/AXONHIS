"use client";
import React, { useState, useEffect } from "react";
import { TopNav } from "@/components/ui/TopNav";
import Link from "next/link";
import {
  Users, Activity, ClipboardList, AlertTriangle, Pill,
  TestTubes, Receipt, CheckCircle2, Clock, TrendingDown,
  ArrowRight, Loader2, ShieldAlert, Package, Stethoscope
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

interface DashboardStats {
  totalPatients: number;
  activeEncounters: number;
  pendingOrders: number;
  pendingTasks: number;
  lowStockAlerts: number;
  nearExpiryBatches: number;
  pendingPrescriptions: number;
  dispensedToday: number;
  pendingSamples: number;
  criticalLabResults: number;
  totalInvoices: number;
  pendingPayments: number;
  recentActivity: any[];
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalPatients: 0,
    activeEncounters: 0,
    pendingOrders: 0,
    pendingTasks: 0,
    lowStockAlerts: 0,
    nearExpiryBatches: 0,
    pendingPrescriptions: 0,
    dispensedToday: 0,
    pendingSamples: 0,
    criticalLabResults: 0,
    totalInvoices: 0,
    pendingPayments: 0,
    recentActivity: [],
  });
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    const fetchAllStats = async () => {
      const headers = authHeaders();
      try {
        // Fire all requests in parallel — gracefully handle failures
        const [
          patientsRes, encountersRes, tasksRes,
          prescriptionsRes, lowStockRes, nearExpiryRes,
          labStatsRes, invoicesRes, inventoryRes
        ] = await Promise.allSettled([
          fetch(`${API}/api/v1/patients`, { headers }),
          fetch(`${API}/api/v1/encounters/`, { headers }),
          fetch(`${API}/api/v1/tasks`, { headers }),
          fetch(`${API}/api/v1/pharmacy/prescriptions`, { headers }),
          fetch(`${API}/api/v1/pharmacy/inventory/low-stock`, { headers }),
          fetch(`${API}/api/v1/pharmacy/batches/near-expiry?days=60`, { headers }),
          fetch(`${API}/api/v1/lab/dashboard/stats`, { headers }),
          fetch(`${API}/api/v1/billing/invoices`, { headers }),
          fetch(`${API}/api/v1/pharmacy/inventory`, { headers }),
        ]);

        const getJson = async (r: PromiseSettledResult<Response>) => {
          if (r.status === "fulfilled" && r.value.ok) return r.value.json();
          return null;
        };

        const [patients, encounters, tasks, prescriptions, lowStock, nearExpiry, labStats, invoices, inventory] = await Promise.all([
          getJson(patientsRes),
          getJson(encountersRes),
          getJson(tasksRes),
          getJson(prescriptionsRes),
          getJson(lowStockRes),
          getJson(nearExpiryRes),
          getJson(labStatsRes),
          getJson(invoicesRes),
          getJson(inventoryRes),
        ]);

        const patientList = Array.isArray(patients) ? patients : (patients?.items || []);
        const encounterList = Array.isArray(encounters) ? encounters : [];
        const taskList = Array.isArray(tasks) ? tasks : [];
        const rxList = Array.isArray(prescriptions) ? prescriptions : [];
        const lowStockList = Array.isArray(lowStock) ? lowStock : [];
        const nearExpiryList = Array.isArray(nearExpiry) ? nearExpiry : [];
        const invoiceList = Array.isArray(invoices) ? invoices : [];

        const activeEncounters = encounterList.filter((e: any) => e.status === "in_progress" || e.status === "scheduled").length;
        const pendingTasks = taskList.filter((t: any) => t.status === "PENDING" || t.status === "ASSIGNED" || t.status === "IN_PROGRESS").length;
        const pendingRx = rxList.filter((r: any) => r.status === "pending" || r.status === "approved").length;
        const dispensedToday = rxList.filter((r: any) => r.status === "dispensed").length;
        const pendingPayments = invoiceList.filter((i: any) => i.status === "issued").length;

        setStats({
          totalPatients: patientList.length,
          activeEncounters,
          pendingOrders: 0, // orders are per-encounter, hard to count globally
          pendingTasks,
          lowStockAlerts: lowStockList.length,
          nearExpiryBatches: nearExpiryList.length,
          pendingPrescriptions: pendingRx,
          dispensedToday,
          pendingSamples: labStats?.pending_samples ?? 0,
          criticalLabResults: labStats?.critical_results ?? 0,
          totalInvoices: invoiceList.length,
          pendingPayments,
          recentActivity: [],
        });

        // Check health
        try {
          const healthRes = await fetch(`${API}/health`);
          if (healthRes.ok) setSystemStatus(await healthRes.json());
        } catch { /* ignore */ }

      } catch (error) {
        console.error("Failed to load dashboard stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAllStats();
  }, []);

  const STAT_CARDS = [
    {
      label: "Total Patients",
      value: stats.totalPatients,
      color: "bg-blue-50 border-blue-100",
      iconColor: "text-blue-600",
      icon: Users,
      href: "/dashboard/patients",
      sub: "Registered patients",
      subColor: "text-blue-500",
    },
    {
      label: "Active Encounters",
      value: stats.activeEncounters,
      color: "bg-emerald-50 border-emerald-100",
      iconColor: "text-emerald-600",
      icon: Stethoscope,
      href: "/dashboard/encounters",
      sub: "In progress & scheduled",
      subColor: "text-emerald-500",
    },
    {
      label: "Pending Tasks",
      value: stats.pendingTasks,
      color: "bg-amber-50 border-amber-100",
      iconColor: "text-amber-600",
      icon: ClipboardList,
      href: "/dashboard/tasks",
      sub: "Awaiting execution",
      subColor: "text-amber-500",
    },
    {
      label: "Low Stock Alerts",
      value: stats.lowStockAlerts,
      color: stats.lowStockAlerts > 0 ? "bg-rose-50 border-rose-100" : "bg-slate-50 border-slate-100",
      iconColor: stats.lowStockAlerts > 0 ? "text-rose-600" : "text-slate-400",
      icon: TrendingDown,
      href: "/dashboard/pharmacy/inventory",
      sub: "Items below threshold",
      subColor: stats.lowStockAlerts > 0 ? "text-rose-500" : "text-slate-400",
    },
    {
      label: "Pending Rx",
      value: stats.pendingPrescriptions,
      color: "bg-violet-50 border-violet-100",
      iconColor: "text-violet-600",
      icon: Pill,
      href: "/dashboard/pharmacy",
      sub: "Awaiting dispensing",
      subColor: "text-violet-500",
    },
    {
      label: "Near Expiry",
      value: stats.nearExpiryBatches,
      color: stats.nearExpiryBatches > 0 ? "bg-orange-50 border-orange-100" : "bg-slate-50 border-slate-100",
      iconColor: stats.nearExpiryBatches > 0 ? "text-orange-600" : "text-slate-400",
      icon: AlertTriangle,
      href: "/dashboard/pharmacy/inventory",
      sub: "Expiring in 60 days",
      subColor: stats.nearExpiryBatches > 0 ? "text-orange-500" : "text-slate-400",
    },
    {
      label: "Lab Samples",
      value: stats.pendingSamples,
      color: "bg-cyan-50 border-cyan-100",
      iconColor: "text-cyan-600",
      icon: TestTubes,
      href: "/dashboard/lab",
      sub: "Pending processing",
      subColor: "text-cyan-500",
    },
    {
      label: "Invoices",
      value: stats.totalInvoices,
      color: "bg-indigo-50 border-indigo-100",
      iconColor: "text-indigo-600",
      icon: Receipt,
      href: "/dashboard/billing",
      sub: `${stats.pendingPayments} pending payment`,
      subColor: "text-indigo-500",
    },
  ];

  const PHASE_MODULES = [
    { phase: "Phase 1", modules: ["Auth", "RBAC", "Audit", "Events", "Files", "Config", "Notifications"], status: "active" },
    { phase: "Phase 2", modules: ["Patient Registry", "Demographics", "Search"], status: "active" },
    { phase: "Phase 3", modules: ["Encounters", "Consultations", "Clinical Notes"], status: "active" },
    { phase: "Phase 4", modules: ["Order Engine", "Catalog", "Templates"], status: "active" },
    { phase: "Phase 5", modules: ["Task Queue", "Care Execution", "Workflows"], status: "active" },
    { phase: "Phase 6", modules: ["Lab Tests", "Samples", "Results", "Validation"], status: "active" },
    { phase: "Phase 7", modules: ["Medications", "Inventory", "Batches", "Prescriptions"], status: "active" },
    { phase: "Phase 8", modules: ["Billing", "Invoices", "Payments", "Insurance Claims"], status: "active" },
  ];

  if (loading) {
    return (
      <div>
        <TopNav title="Dashboard" />
        <div className="flex h-[80vh] items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-10 h-10 animate-spin text-[var(--accent-primary)]" />
            <p className="text-sm text-[var(--text-secondary)]">Loading dashboard data...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <TopNav title="Dashboard" />

      <div className="p-6 space-y-6">
        {/* KPI Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {STAT_CARDS.map((stat) => {
            const Icon = stat.icon;
            return (
              <Link key={stat.label} href={stat.href} className="block group">
                <div className={`card card-body border ${stat.color} hover:shadow-md transition-all duration-200 group-hover:scale-[1.01]`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="stat-label text-xs">{stat.label}</p>
                      <p className="stat-value mt-1 text-2xl font-bold">{stat.value}</p>
                    </div>
                    <div className={`w-12 h-12 rounded-xl ${stat.color} flex items-center justify-center`}>
                      <Icon className={`w-6 h-6 ${stat.iconColor}`} />
                    </div>
                  </div>
                  <p className={`text-xs mt-3 flex items-center gap-1 ${stat.subColor}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${stat.iconColor.replace("text-", "bg-")}`}></span>
                    {stat.sub}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Quick Navigation */}
          <div className="lg:col-span-2 card">
            <div className="card-header">
              <h3 className="font-semibold">Quick Navigation</h3>
            </div>
            <div className="divide-y divide-[var(--border)]">
              {[
                { label: "Patient Registry", desc: "Register & search patients", href: "/dashboard/patients", icon: Users, color: "text-blue-600", bg: "bg-blue-50" },
                { label: "Encounters", desc: "Manage clinical visits & consultations", href: "/dashboard/encounters", icon: Stethoscope, color: "text-emerald-600", bg: "bg-emerald-50" },
                { label: "Order Management", desc: "Lab tests, medications & procedures", href: "/dashboard/orders", icon: ClipboardList, color: "text-violet-600", bg: "bg-violet-50" },
                { label: "Task Queue", desc: "Clinical workflows & nursing tasks", href: "/dashboard/tasks", icon: Activity, color: "text-amber-600", bg: "bg-amber-50" },
                { label: "Laboratory", desc: "Test catalog, samples & results", href: "/dashboard/lab", icon: TestTubes, color: "text-cyan-600", bg: "bg-cyan-50" },
                { label: "Pharmacy", desc: "Inventory, prescriptions & dispensing", href: "/dashboard/pharmacy", icon: Pill, color: "text-rose-600", bg: "bg-rose-50" },
                { label: "Billing", desc: "Invoices, payments & insurance claims", href: "/dashboard/billing", icon: Receipt, color: "text-indigo-600", bg: "bg-indigo-50" },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <Link key={item.href} href={item.href} className="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors group">
                    <div className={`w-10 h-10 rounded-xl ${item.bg} flex items-center justify-center shrink-0`}>
                      <Icon className={`w-5 h-5 ${item.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-[var(--text-primary)]">{item.label}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{item.desc}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Link>
                );
              })}
            </div>
          </div>

          {/* System Status + Phase Modules */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold">System Status</h3>
            </div>
            <div className="card-body space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">Backend</span>
                <span className={systemStatus ? "badge-success" : "badge-error"}>
                  {systemStatus ? "Connected" : "Offline"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">API Version</span>
                <span className="badge-neutral">{systemStatus?.version || "—"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">Environment</span>
                <span className="badge-info">Development</span>
              </div>

              <hr className="border-[var(--border)]" />

              {/* Phase Modules Status */}
              <div className="space-y-3">
                <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Module Status</p>
                {PHASE_MODULES.map((phase) => (
                  <div key={phase.phase}>
                    <p className="text-xs text-[var(--text-secondary)] mb-1.5 font-medium">{phase.phase}</p>
                    <div className="flex flex-wrap gap-1">
                      {phase.modules.map((m) => (
                        <span key={m} className="badge-success text-[9px] !px-1.5 !py-0.5">✓ {m}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Critical Alerts Section */}
        {(stats.lowStockAlerts > 0 || stats.nearExpiryBatches > 0 || stats.criticalLabResults > 0) && (
          <div className="card border-amber-200 bg-amber-50/30">
            <div className="card-header !bg-amber-50/50">
              <h3 className="font-semibold flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-600" />
                Critical Alerts
              </h3>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {stats.lowStockAlerts > 0 && (
                  <Link href="/dashboard/pharmacy/inventory" className="flex items-center gap-3 p-3 bg-white rounded-lg border border-amber-200 hover:shadow-sm transition-shadow">
                    <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                      <TrendingDown className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-amber-800">{stats.lowStockAlerts} Low Stock</p>
                      <p className="text-xs text-amber-600">Items below reorder threshold</p>
                    </div>
                  </Link>
                )}
                {stats.nearExpiryBatches > 0 && (
                  <Link href="/dashboard/pharmacy/inventory" className="flex items-center gap-3 p-3 bg-white rounded-lg border border-orange-200 hover:shadow-sm transition-shadow">
                    <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                      <AlertTriangle className="w-5 h-5 text-orange-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-orange-800">{stats.nearExpiryBatches} Near Expiry</p>
                      <p className="text-xs text-orange-600">Drug batches expiring soon</p>
                    </div>
                  </Link>
                )}
                {stats.criticalLabResults > 0 && (
                  <Link href="/dashboard/lab" className="flex items-center gap-3 p-3 bg-white rounded-lg border border-rose-200 hover:shadow-sm transition-shadow">
                    <div className="w-10 h-10 rounded-lg bg-rose-100 flex items-center justify-center">
                      <ShieldAlert className="w-5 h-5 text-rose-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-rose-800">{stats.criticalLabResults} Critical Results</p>
                      <p className="text-xs text-rose-600">Lab results needing attention</p>
                    </div>
                  </Link>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
