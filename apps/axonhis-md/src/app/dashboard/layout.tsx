"use client";
import React, { useState, createContext, useContext } from "react";
import { Sidebar } from "@/components/Sidebar";

const SidebarContext = createContext<{
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}>({
  sidebarOpen: false,
  setSidebarOpen: () => {},
});

export function useSidebar() {
  return useContext(SidebarContext);
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <SidebarContext.Provider value={{ sidebarOpen, setSidebarOpen }}>
      <div className="min-h-screen" style={{ background: "var(--bg)" }}>
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="main-content">{children}</main>
      </div>
    </SidebarContext.Provider>
  );
}
