"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "@/i18n";
import { LanguageSelector } from "./LanguageSelector";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

interface Patient {
  id: string;
  uhid?: string;
  first_name: string;
  last_name: string;
  phone?: string;
  date_of_birth?: string;
  gender?: string;
}

interface TopNavProps {
  title: string;
}

export function TopNav({ title }: TopNavProps) {
  const router = useRouter();
  const { t } = useTranslation();
  const [userName, setUserName] = useState("Admin");
  const [userRole, setUserRole] = useState("admin");
  const [showMenu, setShowMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Patient search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Patient[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const searchTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    fetch(`${API}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error("Unauthorized");
        return r.json();
      })
      .then((data) => {
        setUserName(data.full_name || data.email);
        // Extract primary role from roles array
        const roleNames = (data.roles || []).map((r: any) => (r.name || "").toLowerCase());
        const rolePriority = ["admin", "director", "doctor", "nurse", "pharmacist", "lab_technician", "front_desk"];
        let primaryRole = "admin";
        for (const rp of rolePriority) {
          if (roleNames.includes(rp)) { primaryRole = rp; break; }
        }
        setUserRole(primaryRole);
        localStorage.setItem("user", JSON.stringify({
          ...data,
          role: primaryRole,
          roleNames: roleNames,
        }));
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        router.push("/login");
      });
  }, [router]);

  // Click-outside handler for search
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearch(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Global patient search with debounce
  const searchPatients = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API}/api/v1/patients?search=${encodeURIComponent(query)}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data : data?.items || [];
        setSearchResults(list.slice(0, 8));
      }
    } catch (err) {
      console.error("Patient search error:", err);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchQuery(val);
    setShowSearch(true);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => searchPatients(val), 300);
  };

  const openPatientWorkspace = (patientId: string) => {
    setShowSearch(false);
    setSearchQuery("");
    router.push(`/dashboard/patients/${patientId}/workspace`);
  };

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

  const getAge = (dob: string | undefined) => {
    if (!dob) return "";
    const diff = Date.now() - new Date(dob).getTime();
    const age = Math.floor(diff / (365.25 * 24 * 60 * 60 * 1000));
    return `${age}y`;
  };

  return (
    <header className="topnav-enterprise" id="topnav">
      {/* Left: Page Title + Breadcrumb */}
      <div className="flex items-center gap-3 min-w-0">
        <h1 className="text-lg font-semibold text-slate-800 truncate">
          {t(title) !== title ? t(title) : title}
        </h1>
      </div>

      {/* Center: Global Patient Search */}
      <div ref={searchRef} className="topnav-search-wrapper">
        <div className="topnav-search-container">
          <svg
            className="topnav-search-icon"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            id="global-patient-search"
            type="text"
            placeholder={t("patients.searchPatients")}
            className="topnav-search-input"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={() => searchQuery.length >= 2 && setShowSearch(true)}
          />
          <kbd className="topnav-search-kbd">⌘K</kbd>
          {isSearching && (
            <svg className="topnav-search-spinner" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
        </div>

        {/* Search Results Dropdown */}
        {showSearch && (searchResults.length > 0 || searchQuery.length >= 2) && (
          <div className="topnav-search-results" id="search-results">
            {searchResults.length === 0 && !isSearching ? (
              <div className="px-4 py-8 text-center">
                <svg className="w-10 h-10 mx-auto text-slate-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
                </svg>
                <p className="text-sm text-slate-400">{t("common.noData")} &quot;{searchQuery}&quot;</p>
                <p className="text-xs text-slate-400 mt-1">{t("patients.searchPatients")}</p>
              </div>
            ) : (
              <div>
                <div className="px-3 py-2 border-b border-slate-100">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    {t("nav.patients")} ({searchResults.length})
                  </p>
                </div>
                {searchResults.map((patient) => (
                  <button
                    key={patient.id}
                    onClick={() => openPatientWorkspace(patient.id)}
                    className="topnav-search-result-item"
                  >
                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm shrink-0">
                      {(patient.first_name?.[0] || "").toUpperCase()}
                      {(patient.last_name?.[0] || "").toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <p className="text-sm font-semibold text-slate-800 truncate">
                        {patient.first_name} {patient.last_name}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {patient.uhid && (
                          <span className="text-[11px] font-mono text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                            {patient.uhid}
                          </span>
                        )}
                        {patient.gender && (
                          <span className="text-[11px] text-slate-400">
                            {patient.gender === "male" ? "♂" : patient.gender === "female" ? "♀" : "⚥"}{" "}
                            {getAge(patient.date_of_birth)}
                          </span>
                        )}
                        {patient.phone && (
                          <span className="text-[11px] text-slate-400">📞 {patient.phone}</span>
                        )}
                      </div>
                    </div>
                    <svg className="w-4 h-4 text-slate-300 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                    </svg>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Language Selector */}
        <LanguageSelector />
        {/* Notifications */}
        <button
          onClick={() => setShowNotifications(!showNotifications)}
          className="topnav-action-btn"
          id="notifications-btn"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
          </svg>
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-2.5 hover:opacity-90 transition-opacity pl-2 pr-3 py-1.5 rounded-xl hover:bg-slate-50"
            id="user-menu-btn"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
              {initials}
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-semibold text-slate-700 leading-tight">{userName}</p>
              <p className="text-[10px] text-slate-400 capitalize leading-tight">{t(`users.role${userRole.charAt(0).toUpperCase()}${userRole.slice(1)}`) || userRole.replace("_", " ")}</p>
            </div>
            <svg className="w-4 h-4 text-slate-400 hidden md:block" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          </button>

          {showMenu && (
            <div className="absolute right-0 top-12 w-56 bg-white rounded-xl shadow-xl border border-slate-200 py-1.5 z-50" id="user-dropdown">
              <div className="px-4 py-2.5 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-800">{userName}</p>
                <p className="text-xs text-slate-400 capitalize">{userRole.replace("_", " ")}</p>
              </div>
              <button
                onClick={() => { setShowMenu(false); router.push("/dashboard/settings"); }}
                className="w-full px-4 py-2.5 text-sm text-left hover:bg-slate-50 transition-colors text-slate-600 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {t("common.settings")}
              </button>
              <hr className="border-slate-100 my-1" />
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2.5 text-sm text-left text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                </svg>
                {t("common.logout")}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
