"use client";
import { Sidebar } from "@/components/ui/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div
        className="flex-1 transition-all duration-300"
        style={{ marginLeft: "var(--sidebar-width)" }}
      >
        {children}
      </div>
    </div>
  );
}
