"use client";
import { TopNav } from "@/components/ui/TopNav";

const STAT_CARDS = [
  { label: "Total Users", value: "12", color: "bg-[var(--accent-primary-light)] text-[var(--accent-primary)]", icon: "👥" },
  { label: "Active Sessions", value: "4", color: "bg-[var(--success-light)] text-[var(--success)]", icon: "🟢" },
  { label: "Audit Events Today", value: "156", color: "bg-[var(--warning-light)] text-[var(--warning)]", icon: "📋" },
  { label: "System Alerts", value: "0", color: "bg-[var(--info-light)] text-[var(--info)]", icon: "🔔" },
];

const RECENT_ACTIVITY = [
  { action: "User logged in", user: "Dr. Sharma", time: "2 min ago", type: "info" as const },
  { action: "Configuration updated", user: "Admin", time: "15 min ago", type: "warning" as const },
  { action: "New user registered", user: "Admin", time: "1 hour ago", type: "success" as const },
  { action: "Password changed", user: "Nurse Priya", time: "3 hours ago", type: "info" as const },
  { action: "Role assigned", user: "Admin", time: "5 hours ago", type: "info" as const },
];

export default function DashboardPage() {
  return (
    <div>
      <TopNav title="Dashboard" />

      <div className="p-6 space-y-6">
        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {STAT_CARDS.map((stat) => (
            <div key={stat.label} className="card card-body">
              <div className="flex items-center justify-between">
                <div>
                  <p className="stat-label">{stat.label}</p>
                  <p className="stat-value mt-1">{stat.value}</p>
                </div>
                <div className={`w-12 h-12 rounded-xl ${stat.color} flex items-center justify-center text-xl`}>
                  {stat.icon}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <div className="lg:col-span-2 card">
            <div className="card-header">
              <h3 className="font-semibold">Recent Activity</h3>
              <a href="/dashboard/audit" className="text-sm text-[var(--accent-primary)] hover:underline">
                View all →
              </a>
            </div>
            <div className="divide-y divide-[var(--border)]">
              {RECENT_ACTIVITY.map((item, i) => (
                <div key={i} className="px-6 py-3.5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      item.type === "success" ? "bg-[var(--success)]" :
                      item.type === "warning" ? "bg-[var(--warning)]" :
                      "bg-[var(--info)]"
                    }`} />
                    <div>
                      <p className="text-sm font-medium">{item.action}</p>
                      <p className="text-xs text-[var(--text-secondary)]">by {item.user}</p>
                    </div>
                  </div>
                  <span className="text-xs text-[var(--text-secondary)]">{item.time}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Info */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold">System Status</h3>
            </div>
            <div className="card-body space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">Database</span>
                <span className="badge-success">Connected</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">Redis Cache</span>
                <span className="badge-success">Connected</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">Worker</span>
                <span className="badge-success">Running</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">API Version</span>
                <span className="badge-neutral">v0.1.0</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">Environment</span>
                <span className="badge-info">Development</span>
              </div>

              <hr className="border-[var(--border)]" />

              <div>
                <p className="text-xs text-[var(--text-secondary)] mb-2">Phase 1 Modules</p>
                <div className="flex flex-wrap gap-1.5">
                  {["Auth", "RBAC", "Audit", "Events", "Files", "Config", "Notifications"].map((m) => (
                    <span key={m} className="badge-success text-[10px]">✓ {m}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
