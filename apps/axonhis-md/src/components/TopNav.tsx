"use client";
import React from "react";
import { useSidebar } from "@/app/dashboard/layout";

export function TopNav({ title, subtitle }: { title: string; subtitle?: string }) {
  const { setSidebarOpen } = useSidebar();
  
  return (
    <header className="topnav">
      <div className="flex items-center gap-3">
        <button 
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden w-10 h-10 flex items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:border-teal-500 hover:text-teal-500 transition-colors"
          aria-label="Toggle menu"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <div>
          <div className="topnav-title">{title}</div>
          {subtitle && <div className="topnav-subtitle">{subtitle}</div>}
        </div>
      </div>
      <div className="topnav-right">
        <div className="topnav-version hidden sm:block">AxonHIS MD v1.0</div>
        <div className="topnav-avatar">A</div>
      </div>
    </header>
  );
}
