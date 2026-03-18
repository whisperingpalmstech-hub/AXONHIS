"use client";
import { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Droplets, Heart, Users, TestTubes, Activity, AlertTriangle, CheckCircle2,
  Clock, Search, Plus, BarChart3, Loader2, X, ShieldCheck, Syringe,
  Thermometer, Package, RefreshCw, ArrowRight
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}

const BLOOD_GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"];
const BG_COLORS: Record<string, string> = {
  "O-": "bg-red-100 text-red-700 border-red-200", "O+": "bg-red-50 text-red-600 border-red-100",
  "A-": "bg-blue-100 text-blue-700 border-blue-200", "A+": "bg-blue-50 text-blue-600 border-blue-100",
  "B-": "bg-emerald-100 text-emerald-700 border-emerald-200", "B+": "bg-emerald-50 text-emerald-600 border-emerald-100",
  "AB-": "bg-violet-100 text-violet-700 border-violet-200", "AB+": "bg-violet-50 text-violet-600 border-violet-100",
};

type TabKey = "dashboard" | "donors" | "inventory" | "crossmatch" | "orders" | "transfusions" | "reactions";

export default function BloodBankPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [loading, setLoading] = useState(true);
  const [donors, setDonors] = useState<any[]>([]);
  const [units, setUnits] = useState<any[]>([]);
  const [components, setComponents] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [crossmatches, setCrossmatches] = useState<any[]>([]);
  const [transfusions, setTransfusions] = useState<any[]>([]);
  const [reactions, setReactions] = useState<any[]>([]);
  const [storageUnits, setStorageUnits] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [showAddDonor, setShowAddDonor] = useState(false);
  const [showAddCrossmatch, setShowAddCrossmatch] = useState(false);
  const [showAddReaction, setShowAddReaction] = useState(false);
  const [showAddTransfusion, setShowAddTransfusion] = useState(false);

  const [newDonor, setNewDonor] = useState({
    donor_id: "", first_name: "", last_name: "", date_of_birth: "",
    blood_group: "O", rh_factor: "+", contact_number: "",
  });
  const [newCrossmatch, setNewCrossmatch] = useState({
    patient_id: "", blood_unit_id: "", patient_blood_group: "", unit_blood_group: "",
  });
  const [newReaction, setNewReaction] = useState({
    transfusion_id: "", reaction_type: "allergic", reaction_severity: "mild",
    symptoms: "", reported_by: "",
  });
  const [newTransfusion, setNewTransfusion] = useState({
    patient_id: "", blood_unit_id: "", administered_by: "",
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const h = authHeaders();
      const [dRes, uRes, cRes, oRes, xRes, tRes, rRes, sRes, pRes] = await Promise.all([
        fetch(`${API}/api/v1/blood-bank/donors`, { headers: h }),
        fetch(`${API}/api/v1/blood-bank/inventory`, { headers: h }),
        fetch(`${API}/api/v1/blood-bank/components`, { headers: h }),
        fetch(`${API}/api/v1/blood-bank/orders`, { headers: h }),
        fetch(`${API}/api/v1/blood-bank/crossmatch`, { headers: h }),
        fetch(`${API}/api/v1/blood-bank/transfusion`, { headers: h }),
        fetch(`${API}/api/v1/blood-bank/reaction`, { headers: h }),
        fetch(`${API}/api/v1/blood-bank/storage-units`, { headers: h }),
        fetch(`${API}/api/v1/patients`, { headers: h }),
      ]);
      if (dRes.ok) setDonors(await dRes.json());
      if (uRes.ok) setUnits(await uRes.json());
      if (cRes.ok) setComponents(await cRes.json());
      if (oRes.ok) setOrders(await oRes.json());
      if (xRes.ok) setCrossmatches(await xRes.json());
      if (tRes.ok) setTransfusions(await tRes.json());
      if (rRes.ok) setReactions(await rRes.json());
      if (sRes.ok) setStorageUnits(await sRes.json());
      if (pRes.ok) { const pData = await pRes.json(); setPatients(Array.isArray(pData) ? pData : pData.items || []); }
    } catch (e) { console.error("Failed to load blood bank data:", e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAddDonor = async () => {
    try {
      const res = await fetch(`${API}/api/v1/blood-bank/donors`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(newDonor),
      });
      if (res.ok) { setShowAddDonor(false); loadData(); }
      else { const err = await res.json(); alert(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)); }
    } catch { alert("Failed to add donor"); }
  };

  const handleAddCrossmatch = async () => {
    if (!newCrossmatch.patient_id || !newCrossmatch.blood_unit_id) {
      alert("Please select both a Patient and a Blood Unit.");
      return;
    }
    try {
      const res = await fetch(`${API}/api/v1/blood-bank/crossmatch`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(newCrossmatch),
      });
      if (res.ok) { setShowAddCrossmatch(false); loadData(); }
      else { const err = await res.json(); alert(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)); }
    } catch { alert("Failed to create crossmatch"); }
  };

  const handleAddReaction = async () => {
    if (!newReaction.transfusion_id) {
      alert("Please select a Transfusion record.");
      return;
    }
    try {
      const res = await fetch(`${API}/api/v1/blood-bank/reaction`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(newReaction),
      });
      if (res.ok) { setShowAddReaction(false); loadData(); setNewReaction({ transfusion_id: "", reaction_type: "allergic", reaction_severity: "mild", symptoms: "", reported_by: "" }); }
      else { const err = await res.json(); alert(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)); }
    } catch { alert("Failed to report reaction"); }
  };

  const handleAddTransfusion = async () => {
    if (!newTransfusion.patient_id || !newTransfusion.blood_unit_id || !newTransfusion.administered_by) {
      alert("Please fill in all required fields (Patient, Unit, Administered By).");
      return;
    }
    try {
      const res = await fetch(`${API}/api/v1/blood-bank/transfusion`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(newTransfusion),
      });
      if (res.ok) { setShowAddTransfusion(false); loadData(); setNewTransfusion({ patient_id: "", blood_unit_id: "", administered_by: "" }); }
      else { const err = await res.json(); alert(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)); }
    } catch { alert("Failed to start transfusion"); }
  };

  // Inventory grouping by blood group
  const inventoryByGroup = BLOOD_GROUPS.map(bg => ({
    group: bg,
    available: units.filter((u: any) => `${u.blood_group}${u.rh_factor}` === bg && u.status === "available").length,
    reserved: units.filter((u: any) => `${u.blood_group}${u.rh_factor}` === bg && u.status === "reserved").length,
    total: units.filter((u: any) => `${u.blood_group}${u.rh_factor}` === bg).length,
  }));

  const nearExpiryUnits = units.filter((u: any) => {
    if (u.status !== "available") return false;
    const exp = new Date(u.expiry_date);
    const diff = (exp.getTime() - Date.now()) / (1000 * 60 * 60 * 24);
    return diff <= 7 && diff > 0;
  });

  const expiredUnits = units.filter((u: any) => u.status === "expired");
  const pendingCrossmatches = crossmatches.filter((c: any) => c.compatibility_result === "pending");
  const pendingOrders = orders.filter((o: any) => o.order_status === "pending");
  const activeTransfusions = transfusions.filter((t: any) => t.transfusion_status === "in_progress");

  const TABS: { key: TabKey; label: string; icon: any; count?: number }[] = [
    { key: "dashboard", label: "Dashboard", icon: BarChart3 },
    { key: "donors", label: "Donors", icon: Users, count: donors.length },
    { key: "inventory", label: "Inventory", icon: Package, count: units.length },
    { key: "crossmatch", label: "Crossmatch", icon: ShieldCheck, count: pendingCrossmatches.length },
    { key: "orders", label: "Orders", icon: Syringe, count: pendingOrders.length },
    { key: "transfusions", label: "Transfusions", icon: Activity, count: activeTransfusions.length },
    { key: "reactions", label: "Reactions", icon: AlertTriangle, count: reactions.length },
  ];

  return (
    <div>
      <TopNav title="Blood Bank & Transfusion Management" />
      <div className="p-6 space-y-6">
        {/* Tab Navigation */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl overflow-x-auto">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key}
                onClick={() => { setActiveTab(tab.key); setSearchTerm(""); }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-1 justify-center whitespace-nowrap ${
                  isActive
                    ? "bg-white text-red-600 shadow-sm border border-red-100"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-slate-50"
                }`}>
                <Icon size={16} />
                <span className="hidden md:inline">{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span className={`text-[10px] font-bold rounded-full px-1.5 py-0.5 min-w-[18px] text-center ${
                    tab.key === "crossmatch" || tab.key === "reactions" ? "bg-red-100 text-red-700" : "bg-slate-200 text-slate-600"
                  }`}>{tab.count}</span>
                )}
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 size={28} className="animate-spin text-red-500" />
          </div>
        ) : (
          <>
            {/* ═══ DASHBOARD TAB ═══ */}
            {activeTab === "dashboard" && (
              <div className="space-y-6">
                {/* Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                  {[
                    { label: "Total Donors", value: donors.length, icon: Users, cBg: "bg-blue-50", cIcon: "text-blue-600", cBorder: "border-blue-100" },
                    { label: "Available Units", value: units.filter((u: any) => u.status === "available").length, icon: Droplets, cBg: "bg-emerald-50", cIcon: "text-emerald-600", cBorder: "border-emerald-100" },
                    { label: "Pending Crossmatch", value: pendingCrossmatches.length, icon: ShieldCheck, cBg: "bg-amber-50", cIcon: "text-amber-600", cBorder: "border-amber-100" },
                    { label: "Active Transfusions", value: activeTransfusions.length, icon: Activity, cBg: "bg-cyan-50", cIcon: "text-cyan-600", cBorder: "border-cyan-100" },
                    { label: "Near Expiry", value: nearExpiryUnits.length, icon: Clock, cBg: "bg-orange-50", cIcon: "text-orange-600", cBorder: "border-orange-100" },
                    { label: "Reactions", value: reactions.length, icon: AlertTriangle, cBg: "bg-red-50", cIcon: "text-red-600", cBorder: "border-red-100" },
                  ].map((c, i) => {
                    const Icon = c.icon;
                    return (
                      <div key={i} className={`card card-body !p-4 ${c.cBorder}`}>
                        <div className="flex items-center justify-between mb-3">
                          <div className={`w-10 h-10 rounded-xl ${c.cBg} flex items-center justify-center`}>
                            <Icon size={20} className={c.cIcon} />
                          </div>
                        </div>
                        <p className="stat-value !text-2xl">{c.value}</p>
                        <p className="stat-label !text-xs !mt-0.5">{c.label}</p>
                      </div>
                    );
                  })}
                </div>

                {/* Blood Inventory Grid */}
                <div className="card">
                  <div className="card-header">
                    <h3 className="font-semibold text-sm flex items-center gap-2"><Droplets size={16} className="text-red-500" /> Blood Inventory by Group</h3>
                    <button onClick={() => setActiveTab("inventory")} className="text-xs text-red-500 hover:underline">View all &rarr;</button>
                  </div>
                  <div className="p-5 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
                    {inventoryByGroup.map(g => (
                      <div key={g.group} className={`rounded-xl border-2 p-4 text-center ${BG_COLORS[g.group] || "bg-slate-50 border-slate-200"}`}>
                        <p className="text-2xl font-bold">{g.group}</p>
                        <p className="text-3xl font-black mt-1">{g.available}</p>
                        <p className="text-[10px] uppercase font-semibold mt-1 opacity-70">Available</p>
                        {g.reserved > 0 && <p className="text-[10px] mt-1 opacity-60">{g.reserved} reserved</p>}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Alerts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Near Expiry */}
                  <div className="card">
                    <div className="card-header"><h3 className="font-semibold text-sm flex items-center gap-2"><Clock size={16} className="text-orange-500" /> Near Expiry Units</h3></div>
                    {nearExpiryUnits.length > 0 ? (
                      <div className="divide-y divide-[var(--border)]">
                        {nearExpiryUnits.slice(0, 5).map((u: any) => (
                          <div key={u.id} className="px-5 py-3 flex items-center justify-between">
                            <div>
                              <code className="text-xs font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded">{u.unit_id}</code>
                              <span className="text-xs ml-2 text-slate-500">{u.blood_group}{u.rh_factor}</span>
                            </div>
                            <span className="text-xs text-orange-600 font-medium">Exp: {new Date(u.expiry_date).toLocaleDateString()}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="card-body text-center text-[var(--text-secondary)]">
                        <CheckCircle2 size={32} className="mx-auto mb-2 text-emerald-300" />
                        <p className="text-sm">No units near expiry</p>
                      </div>
                    )}
                  </div>

                  {/* Pending Orders */}
                  <div className="card">
                    <div className="card-header"><h3 className="font-semibold text-sm flex items-center gap-2"><Syringe size={16} className="text-blue-500" /> Pending Transfusion Orders</h3></div>
                    {pendingOrders.length > 0 ? (
                      <div className="divide-y divide-[var(--border)]">
                        {pendingOrders.slice(0, 5).map((o: any) => (
                          <div key={o.id} className="px-5 py-3 flex items-center justify-between">
                            <div className="text-sm">
                              <span className={`badge ${o.priority === "stat" ? "badge-error" : o.priority === "urgent" ? "badge-warning" : "badge-neutral"}`}>
                                {o.priority}
                              </span>
                              <span className="ml-2 text-slate-600">{o.units_requested} unit(s)</span>
                            </div>
                            <span className="text-xs text-slate-400">{new Date(o.created_at).toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="card-body text-center text-[var(--text-secondary)]">
                        <CheckCircle2 size={32} className="mx-auto mb-2 text-emerald-300" />
                        <p className="text-sm">No pending orders</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ═══ DONORS TAB ═══ */}
            {activeTab === "donors" && (
              <div className="space-y-5">
                <div className="flex items-center justify-between gap-3">
                  <div className="relative flex-1 max-w-sm">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                    <input value={searchTerm} onChange={(e: any) => setSearchTerm(e.target.value)}
                      placeholder="Search donors…" className="input-field pl-9" />
                  </div>
                  <button onClick={() => setShowAddDonor(true)} className="btn-primary"><Plus size={16} /> Add Donor</button>
                </div>
                {donors.filter((d: any) => !searchTerm || d.first_name.toLowerCase().includes(searchTerm.toLowerCase()) || d.donor_id.toLowerCase().includes(searchTerm.toLowerCase())).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {donors.filter((d: any) => !searchTerm || d.first_name.toLowerCase().includes(searchTerm.toLowerCase()) || d.donor_id.toLowerCase().includes(searchTerm.toLowerCase())).map((d: any) => (
                      <div key={d.id} className="card card-body !p-5 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <p className="font-semibold text-base">{d.first_name} {d.last_name}</p>
                            <code className="text-xs text-red-600 bg-red-50 px-2 py-0.5 rounded">{d.donor_id}</code>
                          </div>
                          <span className={`text-lg font-bold px-3 py-1 rounded-lg border ${BG_COLORS[`${d.blood_group}${d.rh_factor}`] || "bg-slate-50"}`}>
                            {d.blood_group}{d.rh_factor}
                          </span>
                        </div>
                        <div className="space-y-1 text-xs text-slate-500">
                          <p>DOB: {d.date_of_birth} · Phone: {d.contact_number}</p>
                          <p>Status: <span className={`font-medium ${d.screening_status === "eligible" ? "text-emerald-600" : "text-orange-600"}`}>{d.screening_status}</span></p>
                          {d.last_donation_date && <p>Last donation: {d.last_donation_date}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <Users size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">No donors found. Click "Add Donor" to register one.</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ INVENTORY TAB ═══ */}
            {activeTab === "inventory" && (
              <div className="space-y-5">
                <div className="flex items-center gap-2">
                  <Droplets size={18} className="text-red-500" />
                  <h3 className="font-semibold">Blood Unit Inventory ({units.length} total)</h3>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 mb-4">
                  {inventoryByGroup.map(g => (
                    <div key={g.group} className={`rounded-xl border-2 p-3 text-center ${BG_COLORS[g.group]}`}>
                      <p className="text-xl font-bold">{g.group}</p>
                      <p className="text-2xl font-black mt-1">{g.available}</p>
                      <p className="text-[10px] uppercase font-semibold opacity-70">avail</p>
                    </div>
                  ))}
                </div>
                {units.length > 0 ? (
                  <div className="overflow-x-auto card">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 text-xs text-slate-500 uppercase">
                        <tr><th className="px-4 py-3 text-left">Unit ID</th><th className="px-4 py-3">Group</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Expiry</th></tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--border)]">
                        {units.map((u: any) => (
                          <tr key={u.id} className="hover:bg-slate-50">
                            <td className="px-4 py-3 font-mono text-xs font-bold text-red-600">{u.unit_id}</td>
                            <td className="px-4 py-3 text-center"><span className={`px-2 py-0.5 rounded text-xs font-bold border ${BG_COLORS[`${u.blood_group}${u.rh_factor}`]}`}>{u.blood_group}{u.rh_factor}</span></td>
                            <td className="px-4 py-3 text-center"><span className={`badge ${u.status === "available" ? "badge-success" : u.status === "reserved" ? "badge-warning" : u.status === "expired" ? "badge-error" : "badge-neutral"}`}>{u.status}</span></td>
                            <td className="px-4 py-3 text-center text-xs text-slate-500">{new Date(u.expiry_date).toLocaleDateString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="card card-body text-center py-16"><Droplets size={40} className="mx-auto mb-3 text-slate-300" /><p className="text-[var(--text-secondary)]">No blood units in inventory.</p></div>
                )}
              </div>
            )}

            {/* ═══ CROSSMATCH TAB ═══ */}
            {activeTab === "crossmatch" && (
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold flex items-center gap-2"><ShieldCheck size={18} className="text-violet-500" /> Compatibility Tests</h3>
                  <button onClick={() => setShowAddCrossmatch(true)} className="btn-primary"><Plus size={16} /> New Crossmatch</button>
                </div>
                {crossmatches.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {crossmatches.map((c: any) => (
                      <div key={c.id} className={`card card-body !p-5 ${c.compatibility_result === "incompatible" ? "border-red-200 bg-red-50/30" : c.compatibility_result === "compatible" ? "border-emerald-200 bg-emerald-50/30" : ""}`}>
                        <div className="flex items-center justify-between mb-3">
                          <span className={`badge ${c.compatibility_result === "compatible" ? "badge-success" : c.compatibility_result === "incompatible" ? "badge-error" : "badge-warning"}`}>{c.compatibility_result}</span>
                          {c.tested_by && <span className="text-xs text-slate-400">by {c.tested_by}</span>}
                        </div>
                        <div className="text-center my-3"><span className="text-lg font-bold">{c.patient_blood_group}</span><span className="mx-2 text-slate-400">←</span><span className="text-lg font-bold">{c.unit_blood_group}</span></div>
                        <p className="text-xs text-slate-400 text-center">{c.tested_at ? new Date(c.tested_at).toLocaleString() : "Pending"}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16"><ShieldCheck size={40} className="mx-auto mb-3 text-slate-300" /><p className="text-[var(--text-secondary)]">No crossmatch tests yet.</p></div>
                )}
              </div>
            )}

            {/* ═══ ORDERS TAB ═══ */}
            {activeTab === "orders" && (
              <div className="space-y-5">
                <h3 className="font-semibold flex items-center gap-2"><Syringe size={18} className="text-blue-500" /> Transfusion Orders ({orders.length})</h3>
                {orders.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {orders.map((o: any) => (
                      <div key={o.id} className="card card-body !p-5">
                        <div className="flex justify-between mb-2">
                          <span className={`badge ${o.priority === "stat" ? "badge-error" : o.priority === "urgent" ? "badge-warning" : "badge-neutral"}`}>{o.priority}</span>
                          <span className={`badge ${o.order_status === "pending" ? "badge-warning" : o.order_status === "completed" ? "badge-success" : "badge-neutral"}`}>{o.order_status}</span>
                        </div>
                        <p className="text-sm text-slate-600">Units: <strong>{o.units_requested}</strong></p>
                        <p className="text-xs text-slate-400 mt-1">{new Date(o.created_at).toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16"><Syringe size={40} className="mx-auto mb-3 text-slate-300" /><p className="text-[var(--text-secondary)]">No transfusion orders.</p></div>
                )}
              </div>
            )}

            {/* ═══ TRANSFUSIONS TAB ═══ */}
            {activeTab === "transfusions" && (
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold flex items-center gap-2"><Activity size={18} className="text-cyan-500" /> Transfusion Records ({transfusions.length})</h3>
                  <button onClick={() => setShowAddTransfusion(true)} className="btn-primary"><Plus size={16} /> Start Transfusion</button>
                </div>
                {transfusions.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {transfusions.map((t: any) => (
                      <div key={t.id} className="card card-body !p-5">
                        <div className="flex justify-between mb-2">
                          <span className={`badge ${t.transfusion_status === "in_progress" ? "badge-info animate-pulse" : t.transfusion_status === "completed" ? "badge-success" : "badge-error"}`}>{t.transfusion_status}</span>
                        </div>
                        <p className="text-sm">Administered by: <strong>{t.administered_by}</strong></p>
                        <p className="text-xs text-slate-400 mt-1">Started: {new Date(t.transfusion_start_time).toLocaleString()}</p>
                        {t.transfusion_end_time && <p className="text-xs text-slate-400">Ended: {new Date(t.transfusion_end_time).toLocaleString()}</p>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16"><Activity size={40} className="mx-auto mb-3 text-slate-300" /><p className="text-[var(--text-secondary)]">No transfusion records.</p></div>
                )}
              </div>
            )}

            {/* ═══ REACTIONS TAB ═══ */}
            {activeTab === "reactions" && (
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold flex items-center gap-2"><AlertTriangle size={18} className="text-red-500" /> Transfusion Reactions ({reactions.length})</h3>
                  <button onClick={() => setShowAddReaction(true)} className="btn-primary bg-red-600 hover:bg-red-700"><Plus size={16} /> Report Reaction</button>
                </div>
                {reactions.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {reactions.map((r: any) => (
                      <div key={r.id} className={`card card-body !p-5 ${r.reaction_severity === "severe" || r.reaction_severity === "life_threatening" ? "border-red-200 bg-red-50/30" : ""}`}>
                        <div className="flex justify-between mb-2">
                          <span className="badge badge-error capitalize">{r.reaction_type}</span>
                          <span className={`badge ${r.reaction_severity === "mild" ? "badge-warning" : r.reaction_severity === "moderate" ? "badge-info" : "badge-error"} capitalize`}>{r.reaction_severity}</span>
                        </div>
                        {r.symptoms && <p className="text-sm text-slate-600 mt-2">{r.symptoms}</p>}
                        <p className="text-xs text-slate-400 mt-2">Reported by: {r.reported_by} · {new Date(r.reported_at).toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16"><CheckCircle2 size={40} className="mx-auto mb-3 text-emerald-300" /><p className="text-[var(--text-secondary)]">No reactions reported.</p></div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* ═══ ADD DONOR MODAL ═══ */}
      {showAddDonor && (
        <div className="modal-overlay" onClick={() => setShowAddDonor(false)}>
          <div className="modal-content" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2"><Users size={18} className="text-red-500" /> Register Donor</h3>
              <button onClick={() => setShowAddDonor(false)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><label className="input-label">Donor ID</label><input className="input-field" placeholder="DN-001" value={newDonor.donor_id} onChange={(e: any) => setNewDonor(p => ({ ...p, donor_id: e.target.value }))} /></div>
                <div><label className="input-label">First Name</label><input className="input-field" value={newDonor.first_name} onChange={(e: any) => setNewDonor(p => ({ ...p, first_name: e.target.value }))} /></div>
                <div><label className="input-label">Last Name</label><input className="input-field" value={newDonor.last_name} onChange={(e: any) => setNewDonor(p => ({ ...p, last_name: e.target.value }))} /></div>
                <div><label className="input-label">Date of Birth</label><input className="input-field" type="date" value={newDonor.date_of_birth} onChange={(e: any) => setNewDonor(p => ({ ...p, date_of_birth: e.target.value }))} /></div>
                <div><label className="input-label">Blood Group</label>
                  <select className="input-field" value={newDonor.blood_group} onChange={(e: any) => setNewDonor(p => ({ ...p, blood_group: e.target.value }))}>
                    {["O", "A", "B", "AB"].map(g => <option key={g} value={g}>{g}</option>)}
                  </select>
                </div>
                <div><label className="input-label">Rh Factor</label>
                  <select className="input-field" value={newDonor.rh_factor} onChange={(e: any) => setNewDonor(p => ({ ...p, rh_factor: e.target.value }))}>
                    <option value="+">Positive (+)</option><option value="-">Negative (-)</option>
                  </select>
                </div>
                <div className="col-span-2"><label className="input-label">Contact Number</label><input className="input-field" value={newDonor.contact_number} onChange={(e: any) => setNewDonor(p => ({ ...p, contact_number: e.target.value }))} /></div>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddDonor(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleAddDonor} className="btn-primary"><Plus size={16} /> Register</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ ADD CROSSMATCH MODAL ═══ */}
      {showAddCrossmatch && (
        <div className="modal-overlay" onClick={() => setShowAddCrossmatch(false)}>
          <div className="modal-content" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2"><ShieldCheck size={18} className="text-violet-500" /> New Crossmatch Test</h3>
              <button onClick={() => setShowAddCrossmatch(false)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="input-label">Select Patient <span className="text-red-500">*</span></label>
                  <select className="input-field" value={newCrossmatch.patient_id} onChange={(e: any) => {
                    const pat = patients.find((p: any) => p.id === e.target.value);
                    const bg = pat?.blood_group && pat.blood_group !== "UNKNOWN" ? pat.blood_group : "";
                    setNewCrossmatch(prev => ({
                      ...prev,
                      patient_id: e.target.value,
                      patient_blood_group: bg || prev.patient_blood_group,
                    }));
                  }}>
                    <option value="">-- Choose Patient --</option>
                    {patients.map((p: any) => {
                      const bg = p.blood_group && p.blood_group !== "UNKNOWN" ? p.blood_group : "Not Set";
                      return (
                        <option key={p.id} value={p.id}>
                          {p.mrn} — {p.first_name} {p.last_name} [Blood: {bg}]
                        </option>
                      );
                    })}
                  </select>
                  {newCrossmatch.patient_id && (() => {
                    const pat = patients.find((p: any) => p.id === newCrossmatch.patient_id);
                    if (!pat) return null;
                    const bg = pat.blood_group && pat.blood_group !== "UNKNOWN" ? pat.blood_group : null;
                    return (
                      <div className="mt-2 p-2 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-600">
                        <strong>{pat.first_name} {pat.last_name}</strong> · MRN: {pat.mrn} · Blood Group: <span className={bg ? "font-bold text-red-600" : "text-orange-500"}>{bg || "Not recorded — select below"}</span>
                      </div>
                    );
                  })()}
                </div>
                <div>
                  <label className="input-label">Select Blood Unit <span className="text-red-500">*</span></label>
                  <select className="input-field" value={newCrossmatch.blood_unit_id} onChange={(e: any) => {
                    const unit = units.find((u: any) => u.id === e.target.value);
                    setNewCrossmatch(prev => ({
                      ...prev,
                      blood_unit_id: e.target.value,
                      unit_blood_group: unit ? `${unit.blood_group}${unit.rh_factor}` : prev.unit_blood_group,
                    }));
                  }}>
                    <option value="">{units.length === 0 ? "No blood units in inventory" : "-- Choose Blood Unit --"}</option>
                    {units.map((u: any) => (
                      <option key={u.id} value={u.id}>
                        {u.unit_id} — {u.blood_group}{u.rh_factor} ({u.status})
                      </option>
                    ))}
                  </select>
                  {units.length === 0 && (
                    <p className="text-xs text-orange-500 mt-1">⚠ No blood units found. Add units in the Inventory tab first.</p>
                  )}
                </div>
                <div><label className="input-label">Patient Blood Group</label><select className="input-field" value={newCrossmatch.patient_blood_group} onChange={(e: any) => setNewCrossmatch(p => ({ ...p, patient_blood_group: e.target.value }))}><option value="">Select</option>{BLOOD_GROUPS.map(g => <option key={g} value={g}>{g}</option>)}</select></div>
                <div><label className="input-label">Unit Blood Group</label><select className="input-field" value={newCrossmatch.unit_blood_group} onChange={(e: any) => setNewCrossmatch(p => ({ ...p, unit_blood_group: e.target.value }))}><option value="">Select</option>{BLOOD_GROUPS.map(g => <option key={g} value={g}>{g}</option>)}</select></div>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddCrossmatch(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleAddCrossmatch} className="btn-primary"><Plus size={16} /> Run Crossmatch</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ ADD REACTION MODAL ═══ */}
      {showAddReaction && (
        <div className="modal-overlay" onClick={() => setShowAddReaction(false)}>
          <div className="modal-content" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2"><AlertTriangle size={18} className="text-red-500" /> Report Reaction</h3>
              <button onClick={() => setShowAddReaction(false)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="input-label">Select Transfusion <span className="text-red-500">*</span></label>
                <select className="input-field" value={newReaction.transfusion_id} onChange={(e: any) => setNewReaction(p => ({ ...p, transfusion_id: e.target.value }))}>
                  <option value="">{transfusions.length === 0 ? "No transfusions found" : "-- Choose Transfusion --"}</option>
                  {transfusions.map((t: any) => {
                    const pat = patients.find(p => p.id === t.patient_id);
                    const pName = pat ? `${pat.first_name} ${pat.last_name}` : "Unknown Patient";
                    return (
                      <option key={t.id} value={t.id}>
                        {pName} — {new Date(t.transfusion_start_time).toLocaleDateString()} ({t.transfusion_status})
                      </option>
                    );
                  })}
                </select>
                {transfusions.length === 0 && (
                  <p className="text-xs text-orange-500 mt-1">⚠ No transfusion records found in the system. Start one in the Transfusions tab.</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="input-label">Reaction Type</label>
                  <select className="input-field" value={newReaction.reaction_type} onChange={(e: any) => setNewReaction(p => ({ ...p, reaction_type: e.target.value }))}>
                    {["allergic", "febrile", "hemolytic", "anaphylactic"].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div><label className="input-label">Severity</label>
                  <select className="input-field" value={newReaction.reaction_severity} onChange={(e: any) => setNewReaction(p => ({ ...p, reaction_severity: e.target.value }))}>
                    {["mild", "moderate", "severe", "life_threatening"].map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div><label className="input-label">Symptoms</label><textarea className="input-field min-h-[80px]" value={newReaction.symptoms} onChange={(e: any) => setNewReaction(p => ({ ...p, symptoms: e.target.value }))} /></div>
              <div><label className="input-label">Reported By</label><input className="input-field" value={newReaction.reported_by} onChange={(e: any) => setNewReaction(p => ({ ...p, reported_by: e.target.value }))} /></div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddReaction(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleAddReaction} className="btn-primary bg-red-600 hover:bg-red-700"><AlertTriangle size={16} /> Report</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ START TRANSFUSION MODAL ═══ */}
      {showAddTransfusion && (
        <div className="modal-overlay" onClick={() => setShowAddTransfusion(false)}>
          <div className="modal-content" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2"><Activity size={18} className="text-cyan-500" /> Start Transfusion</h3>
              <button onClick={() => setShowAddTransfusion(false)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="input-label">Select Patient <span className="text-red-500">*</span></label>
                <select className="input-field" value={newTransfusion.patient_id} onChange={(e: any) => setNewTransfusion(p => ({ ...p, patient_id: e.target.value }))}>
                  <option value="">-- Choose Patient --</option>
                  {patients.map((p: any) => (
                    <option key={p.id} value={p.id}>{p.mrn} — {p.first_name} {p.last_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="input-label">Select Blood Unit <span className="text-red-500">*</span></label>
                <select className="input-field" value={newTransfusion.blood_unit_id} onChange={(e: any) => setNewTransfusion(p => ({ ...p, blood_unit_id: e.target.value }))}>
                  <option value="">-- Choose Unit --</option>
                  {units.map((u: any) => (
                    <option key={u.id} value={u.id}>{u.unit_id} — {u.blood_group}{u.rh_factor} ({u.status})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="input-label">Administered By <span className="text-red-500">*</span></label>
                <input className="input-field" placeholder="Nurse/Doctor Name" value={newTransfusion.administered_by} onChange={(e: any) => setNewTransfusion(p => ({ ...p, administered_by: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddTransfusion(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleAddTransfusion} className="btn-primary"><Plus size={16} /> Start</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
