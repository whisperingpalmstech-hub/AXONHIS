"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface TopNavProps {
  title: string;
}

export function TopNav({ title }: TopNavProps) {
  const router = useRouter();
  const [userName, setUserName] = useState("Admin");
  const [showMenu, setShowMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // Fetch user profile on mount
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error("Unauthorized");
        return r.json();
      })
      .then((data) => {
        setUserName(data.full_name || data.email);
        localStorage.setItem("user", JSON.stringify(data));
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        router.push("/login");
      });
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="topnav">
      <div>
        <h1 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="hidden md:block relative">
          <input
            type="text"
            placeholder="Search..."
            className="input-field w-64 pl-9 py-2 text-sm"
          />
          <svg
            className="absolute left-3 top-2.5 w-4 h-4 text-[var(--text-secondary)]"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>

        {/* Notifications */}
        <button
          onClick={() => setShowNotifications(!showNotifications)}
          className="relative btn-ghost p-2 rounded-lg"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
          </svg>
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[var(--error)] text-white text-[10px] font-bold rounded-full flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <div className="avatar">{initials}</div>
            <span className="text-sm font-medium text-[var(--text-primary)] hidden md:block">
              {userName}
            </span>
          </button>

          {showMenu && (
            <div className="absolute right-0 top-11 w-48 card shadow-lg py-1 z-50">
              <button
                onClick={() => router.push("/dashboard/profile")}
                className="w-full px-4 py-2.5 text-sm text-left hover:bg-slate-50 transition-colors"
              >
                My Profile
              </button>
              <button
                onClick={() => router.push("/dashboard/settings")}
                className="w-full px-4 py-2.5 text-sm text-left hover:bg-slate-50 transition-colors"
              >
                Settings
              </button>
              <hr className="border-[var(--border)] my-1" />
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2.5 text-sm text-left text-[var(--error)] hover:bg-[var(--error-light)] transition-colors"
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
