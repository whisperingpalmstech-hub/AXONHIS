"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

export default function Page() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try { const data = await apiFetch("/integration/events"); setItems(data); } catch { setItems([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  return (<div><TopNav title="Integration Events" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Integration Events</h2><p className="text-sm text-slate-500">{items.length} records</p></div>
      </div>

      {loading ? <div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      items.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-slate-50 flex items-center justify-center text-4xl">\ud83d\udd0c</div>
          <h3 className="text-lg font-bold text-slate-700">No Integration Events</h3>
          <p className="text-sm text-slate-500 mt-1">Records will appear here once created</p>
        </div>
      ) :
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <table className="data-table"><thead><tr><th>#</th><th>Name / Identifier</th><th>Type / Category</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>{items.map((item: any, i: number) => (
            <tr key={item.integration_event_id || i} className="hover:bg-teal-50/30">
              <td className="text-xs text-slate-400 font-mono">{i + 1}</td>
              <td className="font-semibold text-slate-800">{item.event_type || item.code || item.display_name || "—"}</td>
              <td><span className="badge badge-info">{item.device_class || item.channel_type || item.payer_type || item.sensitivity_level || item.event_type || item.action_type || item.invoice_status || "—"}</span></td>
              <td><span className={`badge ${(item.status === "ACTIVE" || item.active_flag !== false) ? "badge-success" : item.event_status === "DELIVERED" || item.action_status === "SUCCESS" ? "badge-success" : item.event_status === "FAILED" || item.action_status === "FAILURE" ? "badge-error" : "badge-neutral"}`}>{item.status || (item.active_flag !== false ? "Active" : "Inactive") || item.event_status || item.action_status || "Active"}</span></td>
              <td className="text-xs text-slate-500">{item.created_at ? new Date(item.created_at).toLocaleDateString() : item.event_time ? new Date(item.event_time).toLocaleDateString() : "—"}</td>
            </tr>))}</tbody></table>
      </div>}
    </div></div>);
}
