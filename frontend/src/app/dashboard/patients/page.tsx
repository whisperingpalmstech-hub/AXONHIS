"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Search, Plus, User, Calendar, Phone } from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { useTranslation } from "@/i18n";

interface Patient {
  id: string;
  patient_uuid: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  primary_phone: string;
  status: string;
}

export default function PatientsPage() {
  const [search, setSearch] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();

  useEffect(() => {
    const fetchPatients = async () => {
      setLoading(true);
      try {
        const url = search.length > 1 
          ? `/api/v1/patients/search?query=${encodeURIComponent(search)}` 
          : '/api/v1/patients';
          
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}${url}`, {
          headers: {
            "Authorization": `Bearer ${localStorage.getItem("access_token")}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          setPatients(data);
        }
      } catch (err) {
        console.error("Failed to fetch patients", err);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(() => fetchPatients(), 300);
    return () => clearTimeout(debounce);
  }, [search]);

  return (
    <div>
      <TopNav title={t("patients.title")} />
      <div className="p-8 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-700">
              {t("patients.title")}
            </h1>
            <p className="text-[var(--text-secondary)] mt-1">{t("patients.manageRecords")}</p>
          </div>
          <Link href="/dashboard/patients/registration" className="btn-primary flex items-center gap-2 shadow-lg shadow-blue-500/20">
            <Plus size={20} />
            <span>{t("patients.registerNew")}</span>
          </Link>
        </div>

      <div className="card">
        <div className="card-body">
          <div className="relative mb-6">
            <Search className="absolute left-3 top-3 text-[var(--text-secondary)]" size={20} />
            <input 
              type="text"
              placeholder="Search by name, phone, or patient ID..."
              className="input-field pl-10"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {loading ? (
            <div className="py-8 text-center text-[var(--text-secondary)]">Loading...</div>
          ) : patients.length === 0 ? (
            <div className="py-8 text-center text-[var(--text-secondary)]">No patients found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--text-secondary)] text-sm">
                    <th className="pb-3 font-medium">Patient Details</th>
                    <th className="pb-3 font-medium">Patient ID</th>
                    <th className="pb-3 font-medium">Phone Number</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {patients.map(p => (
                    <tr key={p.id} className="group hover:bg-[var(--bg-secondary)] transition-colors">
                      <td className="py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-[var(--accent-primary)]/10 flex items-center justify-center text-[var(--accent-primary)] font-semibold">
                            {p.first_name[0]}{p.last_name[0]}
                          </div>
                          <div>
                            <div className="font-semibold text-[var(--text-primary)]">{p.first_name} {p.last_name}</div>
                            <div className="text-xs text-[var(--text-secondary)] flex items-center gap-1 mt-1">
                              <Calendar size={12} /> {p.date_of_birth} 
                              <span className="mx-1">•</span> <User size={12} /> {p.gender}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 text-sm font-medium text-[var(--text-secondary)]">{p.patient_uuid}</td>
                      <td className="py-4">
                        <div className="text-sm text-[var(--text-secondary)] flex items-center gap-2">
                          <Phone size={14} /> {p.primary_phone || "N/A"}
                        </div>
                      </td>
                      <td className="py-4">
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          {p.status}
                        </span>
                      </td>
                      <td className="py-4 text-right">
                        <Link href={`/dashboard/patients/${p.id}`} className="text-sm font-medium text-[var(--accent-primary)] hover:underline">
                          View details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
    </div>
  );
}
