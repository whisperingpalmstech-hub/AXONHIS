"use client";
import React, { useEffect, useState } from "react";
import { Activity, ShieldAlert, Clock, Database } from "lucide-react";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API}/api/v1/audit`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to fetch audit logs");
      const data = await res.json();
      setLogs(data.items || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-in fade-in duration-500 rounded-xl">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            <Activity className="text-emerald-600" size={32} />
            System Audit Logs
          </h1>
          <p className="mt-2 text-slate-500 max-w-2xl">Read-only event stream tracking all hospital administrative and clinical actions for compliance.</p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center">
            <Clock className="animate-spin text-slate-300 mb-4" size={32} />
            Loading immutable system logs...
          </div>
        ) : error ? (
          <div className="p-12 text-center text-rose-500 bg-rose-50 border border-rose-200 m-4 rounded-xl">{error}</div>
        ) : logs.length === 0 ? (
          <div className="p-20 text-center flex flex-col items-center">
              <Database className="text-slate-300 mb-4" size={48} />
              <p className="text-slate-500 text-lg">No audit events found.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 font-semibold">Timestamp</th>
                  <th className="px-6 py-4 font-semibold">Action</th>
                  <th className="px-6 py-4 font-semibold">Resource</th>
                  <th className="px-6 py-4 font-semibold">Actor ID</th>
                  <th className="px-6 py-4 font-semibold">Client IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((L) => (
                  <tr key={L.id} className="hover:bg-slate-50 transition-colors font-mono text-xs">
                    <td className="px-6 py-4 text-slate-500">
                      {new Date(L.occurred_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-bold text-emerald-700 bg-emerald-100 px-2 py-1 rounded-md">{L.action.toUpperCase()}</span>
                    </td>
                    <td className="px-6 py-4 text-slate-700 font-semibold tracking-wide">
                      {L.resource_type} <span className="text-slate-400 font-normal ml-1">({L.resource_id.split('-')[0]})</span>
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {L.user_id ? L.user_id.split('-')[0] : 'SYSTEM'}
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {L.client_ip || 'Internal'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
