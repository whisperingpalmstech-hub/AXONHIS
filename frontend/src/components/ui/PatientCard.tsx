"use client";
import React from "react";
import Link from "next/link";

interface PatientCardProps {
  id: string;
  firstName: string;
  lastName: string;
  uhid?: string;
  gender?: string;
  age?: string;
  phone?: string;
  status?: string;
  bedNumber?: string;
  ward?: string;
  compact?: boolean;
}

function statusBadge(status: string | undefined) {
  if (!status) return null;
  const s = status.toLowerCase();
  const colors =
    s === "admitted" || s === "active" || s === "in_progress"
      ? "bg-emerald-100 text-emerald-700"
      : s === "discharged" || s === "completed"
      ? "bg-slate-100 text-slate-600"
      : s === "critical"
      ? "bg-red-100 text-red-700"
      : "bg-amber-100 text-amber-700";
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${colors}`}>
      {status.replace("_", " ")}
    </span>
  );
}

export function PatientCard({
  id, firstName, lastName, uhid, gender, age, phone, status, bedNumber, ward, compact = false,
}: PatientCardProps) {
  const initials = `${(firstName?.[0] || "").toUpperCase()}${(lastName?.[0] || "").toUpperCase()}`;

  if (compact) {
    return (
      <Link
        href={`/dashboard/patients/${id}/workspace`}
        className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-blue-50/60 transition-colors cursor-pointer border border-transparent hover:border-blue-100"
      >
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-[11px] font-bold shadow-sm shrink-0">
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-800 truncate">{firstName} {lastName}</p>
          <div className="flex items-center gap-2 mt-0.5">
            {uhid && <span className="text-[10px] font-mono text-blue-600">{uhid}</span>}
            {age && <span className="text-[10px] text-slate-400">{gender === "male" ? "♂" : "♀"} {age}</span>}
          </div>
        </div>
        {status && statusBadge(status)}
      </Link>
    );
  }

  return (
    <Link
      href={`/dashboard/patients/${id}/workspace`}
      className="block bg-white rounded-xl border border-slate-200 hover:shadow-md hover:border-blue-200 transition-all duration-200 group overflow-hidden"
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm font-bold shadow-sm shrink-0 group-hover:scale-105 transition-transform">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-slate-800 truncate">{firstName} {lastName}</p>
            <div className="flex items-center gap-2 mt-1">
              {uhid && (
                <span className="text-[10px] font-mono text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                  {uhid}
                </span>
              )}
              {gender && (
                <span className="text-[10px] text-slate-400">
                  {gender === "male" ? "♂" : "♀"} {age || ""}
                </span>
              )}
            </div>
          </div>
          {status && statusBadge(status)}
        </div>

        {(phone || bedNumber || ward) && (
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-3 text-[11px] text-slate-400">
            {phone && <span>📞 {phone}</span>}
            {ward && <span>🏥 {ward}</span>}
            {bedNumber && <span>🛏️ Bed {bedNumber}</span>}
          </div>
        )}
      </div>
    </Link>
  );
}
