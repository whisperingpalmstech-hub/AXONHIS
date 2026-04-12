"use client";
import React, { useState, useEffect } from "react";
import { TopNav } from "@/components/TopNav";
import { apiFetch, apiPost } from "@/lib/api";

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [facilities, setFacilities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState<"org" | "fac" | null>(null);
  const [form, setForm] = useState<any>({});
  const [activeTab, setActiveTab] = useState<"orgs" | "facs">("orgs");

  const load = async () => {
    try {
      const [o, f] = await Promise.all([
        apiFetch("/organizations"),
        apiFetch("/facilities"),
      ]);
      setOrgs(o);
      setFacilities(f);
    } catch {
      setOrgs([]);
      setFacilities([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreateOrg = async () => {
    try {
      await apiPost("/organizations", {
        code: form.code,
        name: form.name,
        organization_type: form.organization_type || "CLINIC",
      });
      setShowModal(null);
      setForm({});
      load();
    } catch (e: any) {
      alert("Error: " + e.message);
    }
  };

  const handleCreateFac = async () => {
    try {
      await apiPost("/facilities", {
        organization_id: form.organization_id,
        code: form.code,
        name: form.name,
        facility_type: form.facility_type || "CLINIC",
        timezone: form.timezone || "Asia/Dubai",
      });
      setShowModal(null);
      setForm({});
      load();
    } catch (e: any) {
      alert("Error: " + e.message);
    }
  };

  const items = activeTab === "orgs" ? orgs : facilities;

  return (
    <div>
      <TopNav title="Organizations & Facilities" />
      <div className="p-8 space-y-6">
        {/* Tabs */}
        <div className="flex items-center gap-1 bg-slate-100 rounded-xl p-1 w-fit">
          <button onClick={() => setActiveTab("orgs")} className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all ${activeTab === "orgs" ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
            Organizations ({orgs.length})
          </button>
          <button onClick={() => setActiveTab("facs")} className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all ${activeTab === "facs" ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
            Facilities ({facilities.length})
          </button>
        </div>

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              {activeTab === "orgs" ? "Organization Registry" : "Facility Registry"}
            </h2>
            <p className="text-sm text-slate-500 mt-0.5">{items.length} records</p>
          </div>
          <button onClick={() => setShowModal(activeTab === "orgs" ? "org" : "fac")} className="btn-primary">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            {activeTab === "orgs" ? "Add Organization" : "Add Facility"}
          </button>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-3">
            <div className="spinner"></div>
            <p className="text-sm text-slate-400">Loading...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🏥</div>
            <h3>No {activeTab === "orgs" ? "Organizations" : "Facilities"} Yet</h3>
            <p>Create your first one to get started</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Name</th>
                  <th>Type / Category</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item: any, i: number) => (
                  <tr key={item.organization_id || item.facility_id}>
                    <td className="text-xs text-slate-400 font-mono">{i + 1}</td>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                          {item.name?.charAt(0)?.toUpperCase() || "O"}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-800">{item.name}</div>
                          <div className="text-[11px] text-slate-400 font-mono">{item.code}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-info">{item.organization_type || item.facility_type}</span>
                    </td>
                    <td>
                      <span className={`badge badge-dot ${item.status === "ACTIVE" ? "badge-success" : "badge-neutral"}`}>
                        {item.status}
                      </span>
                    </td>
                    <td className="text-xs text-slate-400">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Create Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-lg">🏥</div>
                  <h3 className="font-bold text-lg">{showModal === "org" ? "Create Organization" : "Create Facility"}</h3>
                </div>
                <button onClick={() => setShowModal(null)}>&times;</button>
              </div>
              <div className="modal-body space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">Code *</label>
                    <input className="input-field" placeholder="e.g. CLINIC-001" value={form.code || ""} onChange={(e) => setForm({ ...form, code: e.target.value })} />
                  </div>
                  <div>
                    <label className="input-label">Name *</label>
                    <input className="input-field" placeholder="Organization name" value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                  </div>
                </div>
                {showModal === "org" ? (
                  <div>
                    <label className="input-label">Type</label>
                    <select className="input-field" value={form.organization_type || "CLINIC"} onChange={(e) => setForm({ ...form, organization_type: e.target.value })}>
                      <option value="CLINIC">Clinic</option>
                      <option value="HOSPITAL">Hospital</option>
                      <option value="NETWORK">Network</option>
                    </select>
                  </div>
                ) : (
                  <>
                    <div>
                      <label className="input-label">Organization *</label>
                      <select className="input-field" value={form.organization_id || ""} onChange={(e) => setForm({ ...form, organization_id: e.target.value })}>
                        <option value="">Select organization...</option>
                        {orgs.map((o) => (
                          <option key={o.organization_id} value={o.organization_id}>{o.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="input-label">Facility Type</label>
                        <select className="input-field" value={form.facility_type || "CLINIC"} onChange={(e) => setForm({ ...form, facility_type: e.target.value })}>
                          <option value="CLINIC">Clinic</option>
                          <option value="HOSPITAL">Hospital</option>
                          <option value="HEALTH_ATM">Health ATM</option>
                        </select>
                      </div>
                      <div>
                        <label className="input-label">Timezone</label>
                        <input className="input-field" placeholder="Asia/Dubai" value={form.timezone || ""} onChange={(e) => setForm({ ...form, timezone: e.target.value })} />
                      </div>
                    </div>
                  </>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn-secondary" onClick={() => setShowModal(null)}>Cancel</button>
                <button className="btn-primary" onClick={showModal === "org" ? handleCreateOrg : handleCreateFac}>Create</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
