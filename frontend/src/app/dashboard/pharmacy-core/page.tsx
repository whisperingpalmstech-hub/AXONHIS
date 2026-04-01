"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function getHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

/* ─── Drug Master Tab ─────────────────────────────────────────────────── */
function DrugMasterTab() {
  const [drugs, setDrugs] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ drug_code: "", drug_name: "", generic_name: "", drug_class: "", form: "", strength: "", pack_size: "", manufacturer: "", schedule_category: "", global_code: "" });
  const [msg, setMsg] = useState<{type: string, text: string} | null>(null);

  const fetchDrugs = async () => {
    const res = await fetch(`${API}/api/v1/medications`, { headers: getHeaders() });
    if (res.ok) setDrugs(await res.json());
  };
  useEffect(() => { fetchDrugs(); }, []);

  const addDrug = async () => {
    setMsg(null);
    const body: any = {};
    for (const [k, v] of Object.entries(form)) { if (v) body[k] = v; }
    const res = await fetch(`${API}/api/v1/medications`, { method: "POST", headers: getHeaders(), body: JSON.stringify(body) });
    if (res.ok) { setMsg({ type: "success", text: "Drug added." }); setShowAdd(false); fetchDrugs(); setForm({ drug_code: "", drug_name: "", generic_name: "", drug_class: "", form: "", strength: "", pack_size: "", manufacturer: "", schedule_category: "", global_code: "" }); }
    else { const d = await res.json(); setMsg({ type: "error", text: d.detail || "Failed" }); }
  };

  const filtered = drugs.filter(d => d.drug_name?.toLowerCase().includes(search.toLowerCase()) || d.generic_name?.toLowerCase().includes(search.toLowerCase()) || d.drug_code?.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name, generic, or code..." className="border rounded-lg px-4 py-2 w-80 text-sm" />
        <button onClick={() => setShowAdd(!showAdd)} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">+ Add Drug</button>
      </div>
      {msg && <div className={`p-3 rounded-lg text-sm mb-4 ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>{msg.text}</div>}
      {showAdd && (
        <div className="bg-gray-50 border rounded-xl p-5 mb-6 grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(form).map(([k, v]) => (
            <div key={k}>
              <label className="text-xs text-gray-500 font-medium block mb-1">{k.replace(/_/g, ' ').toUpperCase()}</label>
              <input value={v} onChange={e => setForm({ ...form, [k]: e.target.value })} className="border rounded-lg px-3 py-2 w-full text-sm" />
            </div>
          ))}
          <div className="col-span-full flex gap-2 mt-2">
            <button onClick={addDrug} className="bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm font-medium">Save</button>
            <button onClick={() => setShowAdd(false)} className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg text-sm">Cancel</button>
          </div>
        </div>
      )}
      <div className="bg-white border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-left">Code</th><th className="px-4 py-3 text-left">Drug Name</th><th className="px-4 py-3 text-left">Generic</th>
              <th className="px-4 py-3 text-left">Form</th><th className="px-4 py-3 text-left">Strength</th><th className="px-4 py-3 text-left">Schedule</th>
              <th className="px-4 py-3 text-left">Manufacturer</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-12 text-center text-gray-400">No drugs in master database.</td></tr>
            ) : filtered.map(d => (
              <tr key={d.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs">{d.drug_code}</td>
                <td className="px-4 py-3 font-medium">{d.drug_name}</td>
                <td className="px-4 py-3 text-gray-600">{d.generic_name}</td>
                <td className="px-4 py-3">{d.form || '-'}</td>
                <td className="px-4 py-3">{d.strength || '-'}</td>
                <td className="px-4 py-3"><span className="px-2 py-0.5 bg-purple-50 text-purple-700 text-xs rounded-full">{d.schedule_category || 'OTC'}</span></td>
                <td className="px-4 py-3 text-gray-500">{d.manufacturer || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ─── Generic Mapping Tab ──────────────────────────────────────────────── */
function GenericMappingTab() {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const searchSubstitutes = async () => {
    if (!search) return;
    setLoading(true);
    const res = await fetch(`${API}/api/v1/pharmacy/generic-mappings/substitutes?generic_name=${encodeURIComponent(search)}`, { headers: getHeaders() });
    if (res.ok) setResults(await res.json());
    setLoading(false);
  };

  return (
    <div>
      <div className="bg-gradient-to-r from-teal-50 to-cyan-50 border rounded-xl p-6 mb-6">
        <h3 className="font-bold text-teal-900 mb-2">🔄 Generic ↔ Brand Substitution Search</h3>
        <p className="text-sm text-teal-700 mb-4">Find all branded products mapped to a generic name</p>
        <div className="flex gap-3">
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="e.g. Paracetamol" className="border rounded-lg px-4 py-2 flex-1 text-sm" />
          <button onClick={searchSubstitutes} className="bg-teal-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-teal-700">Search</button>
        </div>
      </div>
      {loading ? <p className="text-sm text-gray-400">Searching...</p> : results.length > 0 ? (
        <div className="space-y-3">
          {results.map((r, i) => (
            <div key={i} className="bg-white border rounded-xl p-4 flex justify-between items-center">
              <div>
                <p className="font-medium text-gray-800">{r.brand}</p>
                <p className="text-xs text-gray-500">Generic: {r.generic_name} | Strength: {r.strength || 'N/A'}</p>
              </div>
              <span className="px-2 py-1 bg-teal-50 text-teal-700 text-xs rounded-full font-medium">Rank #{r.mapping_id?.split('-')[0]}</span>
            </div>
          ))}
        </div>
      ) : search ? <p className="text-sm text-gray-400 text-center py-8">No brand substitutes found for "{search}".</p> : null}
    </div>
  );
}

/* ─── Drug Interaction Checker Tab ─────────────────────────────────────── */
function InteractionCheckerTab() {
  const [generics, setGenerics] = useState("");
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const checkInteractions = async () => {
    if (!generics) return;
    setLoading(true);
    const list = generics.split(",").map(g => g.trim()).filter(Boolean);
    const res = await fetch(`${API}/api/v1/pharmacy/drug-interactions/check`, { method: "POST", headers: getHeaders(), body: JSON.stringify({ active_generics: list }) });
    if (res.ok) setResult(await res.json());
    setLoading(false);
  };

  return (
    <div>
      <div className="bg-gradient-to-r from-red-50 to-orange-50 border rounded-xl p-6 mb-6">
        <h3 className="font-bold text-red-900 mb-2">⚠️ Drug-Drug Interaction Checker</h3>
        <p className="text-sm text-red-700 mb-4">Enter comma-separated generic names to check for known interactions</p>
        <div className="flex gap-3">
          <input value={generics} onChange={e => setGenerics(e.target.value)} placeholder="e.g. Warfarin, Aspirin, Ibuprofen" className="border rounded-lg px-4 py-2 flex-1 text-sm" />
          <button onClick={checkInteractions} className="bg-red-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-red-700">Check</button>
        </div>
      </div>
      {loading ? <p className="text-sm text-gray-400">Checking...</p> : result ? (
        result.has_interactions ? (
          <div className="space-y-3">
            {result.interactions.map((ix: any, i: number) => (
              <div key={i} className="bg-white border-l-4 border-red-500 rounded-xl p-4">
                <div className="flex justify-between items-start mb-2">
                  <p className="font-bold text-red-800">{ix.drug_a_generic} ↔ {ix.drug_b_generic}</p>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${ix.severity === 'High' ? 'bg-red-100 text-red-700' : ix.severity === 'Moderate' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>{ix.severity}</span>
                </div>
                <p className="text-sm text-gray-600">{ix.interaction_effect}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
            <p className="text-green-700 font-medium">✅ No known interactions found between these medications.</p>
          </div>
        )
      ) : null}
    </div>
  );
}

/* ─── Dosage Calculator Tab ────────────────────────────────────────────── */
function DosageCalcTab() {
  const [form, setForm] = useState({ generic_name: "", patient_category: "Adult", weight_kg: "" });
  const [result, setResult] = useState<any | null>(null);

  const calculate = async () => {
    const body: any = { generic_name: form.generic_name, patient_category: form.patient_category };
    if (form.weight_kg) body.weight_kg = parseFloat(form.weight_kg);
    const res = await fetch(`${API}/api/v1/pharmacy/dosage-calculator`, { method: "POST", headers: getHeaders(), body: JSON.stringify(body) });
    if (res.ok) setResult(await res.json());
  };

  return (
    <div>
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border rounded-xl p-6 mb-6">
        <h3 className="font-bold text-blue-900 mb-2">💊 Dosage Calculator Engine</h3>
        <p className="text-sm text-blue-700 mb-4">Calculate recommended dosage based on patient category and weight</p>
        <div className="grid grid-cols-3 gap-3">
          <input value={form.generic_name} onChange={e => setForm({ ...form, generic_name: e.target.value })} placeholder="Generic Name (e.g. Amoxicillin)" className="border rounded-lg px-4 py-2 text-sm" />
          <select value={form.patient_category} onChange={e => setForm({ ...form, patient_category: e.target.value })} className="border rounded-lg px-4 py-2 text-sm">
            <option>Adult</option><option>Pediatric</option><option>Geriatric</option>
          </select>
          <input value={form.weight_kg} onChange={e => setForm({ ...form, weight_kg: e.target.value })} placeholder="Weight (kg)" type="number" className="border rounded-lg px-4 py-2 text-sm" />
        </div>
        <button onClick={calculate} className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">Calculate Dosage</button>
      </div>
      {result && (
        <div className="bg-white border rounded-xl p-6 text-center">
          <p className="text-xs text-gray-500 uppercase mb-1">Recommended Dosage</p>
          <p className="text-2xl font-bold text-blue-800">{result.calculated_dosage}</p>
          <p className="text-sm text-gray-500 mt-2">{result.generic_name} — {result.patient_category}</p>
        </div>
      )}
    </div>
  );
}

/* ─── Drug Schedules Tab ───────────────────────────────────────────────── */
function SchedulesTab() {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ schedule_name: "", requires_prescription: true, strict_narcotic: false });

  const fetchSchedules = async () => {
    const res = await fetch(`${API}/api/v1/pharmacy/drug-schedules`, { headers: getHeaders() });
    if (res.ok) setSchedules(await res.json());
  };
  useEffect(() => { fetchSchedules(); }, []);

  const addSchedule = async () => {
    const res = await fetch(`${API}/api/v1/pharmacy/drug-schedules`, { method: "POST", headers: getHeaders(), body: JSON.stringify(form) });
    if (res.ok) { fetchSchedules(); setShowAdd(false); setForm({ schedule_name: "", requires_prescription: true, strict_narcotic: false }); }
  };

  return (
    <div>
      <div className="flex justify-between items.center mb-4">
        <p className="text-sm text-gray-500">Regulatory drug schedule classifications</p>
        <button onClick={() => setShowAdd(!showAdd)} className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700">+ Add Schedule</button>
      </div>
      {showAdd && (
        <div className="bg-gray-50 border rounded-xl p-5 mb-4 flex gap-4 items-end">
          <div className="flex-1"><label className="text-xs text-gray-500 block mb-1">Schedule Name</label><input value={form.schedule_name} onChange={e => setForm({...form, schedule_name: e.target.value})} className="border rounded-lg px-3 py-2 w-full text-sm" /></div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.requires_prescription} onChange={e => setForm({...form, requires_prescription: e.target.checked})} /> Rx Required</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.strict_narcotic} onChange={e => setForm({...form, strict_narcotic: e.target.checked})} /> Narcotic</label>
          <button onClick={addSchedule} className="bg-purple-600 text-white px-6 py-2 rounded-lg text-sm">Save</button>
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {schedules.map(s => (
          <div key={s.id} className="bg-white border rounded-xl p-4 text-center">
            <p className="font-bold text-lg text-gray-800">{s.schedule_name}</p>
            <div className="flex gap-3 justify-center mt-3">
              <span className={`px-2 py-0.5 rounded-full text-xs ${s.requires_prescription ? 'bg-amber-50 text-amber-700' : 'bg-green-50 text-green-700'}`}>{s.requires_prescription ? 'Rx Required' : 'OTC'}</span>
              {s.strict_narcotic && <span className="px-2 py-0.5 bg-red-50 text-red-700 rounded-full text-xs">Narcotic</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Pharmacy Roles Tab ───────────────────────────────────────────────── */
function RolesTab() {
  const [roles, setRoles] = useState<any[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ role_name: "", can_dispense: false, can_manage_inventory: false, can_manage_master: false });

  const fetchRoles = async () => {
    const res = await fetch(`${API}/api/v1/pharmacy/roles`, { headers: getHeaders() });
    if (res.ok) setRoles(await res.json());
  };
  useEffect(() => { fetchRoles(); }, []);

  const addRole = async () => {
    const res = await fetch(`${API}/api/v1/pharmacy/roles`, { method: "POST", headers: getHeaders(), body: JSON.stringify(form) });
    if (res.ok) { fetchRoles(); setShowAdd(false); }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-gray-500">Pharmacy-specific RBAC roles and permissions</p>
        <button onClick={() => setShowAdd(!showAdd)} className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700">+ Add Role</button>
      </div>
      {showAdd && (
        <div className="bg-gray-50 border rounded-xl p-5 mb-4 flex gap-4 items-end">
          <div className="flex-1"><label className="text-xs text-gray-500 block mb-1">Role Name</label><input value={form.role_name} onChange={e => setForm({...form, role_name: e.target.value})} className="border rounded-lg px-3 py-2 w-full text-sm" /></div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.can_dispense} onChange={e => setForm({...form, can_dispense: e.target.checked})} /> Dispense</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.can_manage_inventory} onChange={e => setForm({...form, can_manage_inventory: e.target.checked})} /> Inventory</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.can_manage_master} onChange={e => setForm({...form, can_manage_master: e.target.checked})} /> Master</label>
          <button onClick={addRole} className="bg-emerald-600 text-white px-6 py-2 rounded-lg text-sm">Save</button>
        </div>
      )}
      <div className="bg-white border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
            <tr><th className="px-4 py-3 text-left">Role</th><th className="px-4 py-3 text-center">Dispense</th><th className="px-4 py-3 text-center">Inventory</th><th className="px-4 py-3 text-center">Master Data</th></tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {roles.map(r => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{r.role_name}</td>
                <td className="px-4 py-3 text-center">{r.can_dispense ? '✅' : '❌'}</td>
                <td className="px-4 py-3 text-center">{r.can_manage_inventory ? '✅' : '❌'}</td>
                <td className="px-4 py-3 text-center">{r.can_manage_master ? '✅' : '❌'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ─── Main Page ────────────────────────────────────────────────────────── */
const TABS = [
  { key: "master", label: "Drug Master", icon: "💊" },
  { key: "generic", label: "Generic ↔ Brand", icon: "🔄" },
  { key: "interactions", label: "Interaction Checker", icon: "⚠️" },
  { key: "dosage", label: "Dosage Calculator", icon: "🧮" },
  { key: "schedules", label: "Drug Schedules", icon: "📋" },
  { key: "roles", label: "Pharmacy Roles", icon: "🔐" },
];

export default function PharmacyCoreInfraPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("master");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">{t("pharmacyCore.title")} Infrastructure</h1>
        <p className="text-slate-500 text-sm mt-1">Drug Master, Interactions, Dosage Rules, Schedules & Role Management</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 overflow-x-auto">
        {TABS.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${activeTab === t.key ? 'bg-white shadow-sm text-indigo-700' : 'text-gray-500 hover:text-gray-700'}`}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-2xl shadow-sm border p-6">
        {activeTab === "master" && <DrugMasterTab />}
        {activeTab === "generic" && <GenericMappingTab />}
        {activeTab === "interactions" && <InteractionCheckerTab />}
        {activeTab === "dosage" && <DosageCalcTab />}
        {activeTab === "schedules" && <SchedulesTab />}
        {activeTab === "roles" && <RolesTab />}
      </div>
    </div>
  );
}
