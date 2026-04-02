"use client";

import React, { useState, useEffect } from "react";
import { useTranslation } from "@/i18n";
import { 
  Building2, 
  Sparkles, 
  AlertTriangle, 
  RefreshCw,
  Plus,
  Loader2,
  X
} from "lucide-react";


interface LinenCategory {
  id: string;
  name: string;
  description: string;
  expected_lifespan_washes: number;
}

interface LedgerEntry {
  id: string;
  category: LinenCategory;
  department_id: string;
  clean_quantity: number;
  dirty_quantity: number;
  in_wash_quantity: number;
}

interface LaundryBatch {
  id: string;
  batch_number: string;
  status: string;
  total_weight_kg: number;
  start_time: string;
}

interface LinenTransaction {
  id: string;
  transaction_type: string;
  quantity: number;
  source_department: string;
  destination_department: string;
  transaction_date: string;
}

export default function LinenDashboard() {
  const { t } = useTranslation();
  
  const [activeTab, setActiveTab] = useState<"inventory" | "transactions" | "laundry">("inventory");
  const [loading, setLoading] = useState(true);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [categories, setCategories] = useState<LinenCategory[]>([]);
  const [batches, setBatches] = useState<LaundryBatch[]>([]);
  const [showTransactionModal, setShowTransactionModal] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [txType, setTxType] = useState<"ISSUE_TO_WARD" | "COLLECT_FROM_WARD">("ISSUE_TO_WARD");

  // Transaction form states
  const [formCategory, setFormCategory] = useState("");
  const [formQty, setFormQty] = useState("");
  const [formDept, setFormDept] = useState("ICU Ward");

  // Category form states
  const [catName, setCatName] = useState("");
  const [catDesc, setCatDesc] = useState("");
  const [catLifespan, setCatLifespan] = useState("100");

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
      
      const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const ledgerRes = await fetch(`${API}/api/v1/linen/ledger`, { headers });
      if (ledgerRes.ok) {
        setLedger(await ledgerRes.json());
      }
      
      const catRes = await fetch(`${API}/api/v1/linen/categories`, { headers });
      if (catRes.ok) {
        setCategories(await catRes.json());
      }

      const batchRes = await fetch(`${API}/api/v1/linen/batches`, { headers });
      if (batchRes.ok) {
        setBatches(await batchRes.json());
      }
    } catch (e) {
      console.error("Failed to fetch linen data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // In production we would poll this or use websockets
    const interval = setInterval(fetchData, 30000); 
    return () => clearInterval(interval);
  }, []);

  const handleTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      if (!token) return;

      const payload = {
        transaction_type: txType,
        category_id: formCategory,
        quantity: parseInt(formQty),
        source_department: txType === "ISSUE_TO_WARD" ? "LAUNDRY-MAIN" : formDept,
        destination_department: txType === "ISSUE_TO_WARD" ? formDept : "LAUNDRY-DIRTY",
        notes: "Logged via Dashboard"
      };

      const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const res = await fetch(`${API}/api/v1/linen/transactions`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setShowTransactionModal(false);
        setFormQty("");
        fetchData(); // Refresh ledger
      } else {
        const err = await res.json();
        alert("Transaction Failed: " + (err.detail || "Unknown Error"));
      }
    } catch (error) {
      console.error(error);
      alert("Error committing transaction");
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      if (!token) return;

      const payload = {
        name: catName,
        description: catDesc,
        expected_lifespan_washes: parseInt(catLifespan),
        is_active: true
      };

      const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const res = await fetch(`${API}/api/v1/linen/categories`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setShowCategoryModal(false);
        setCatName("");
        setCatDesc("");
        setCatLifespan("100");
        fetchData(); // Refresh Categories
      } else {
        const err = await res.json();
        alert("Failed to create category: " + (err.detail || "Unknown Error"));
      }
    } catch (error) {
      console.error(error);
      alert("Error creating category");
    }
  };

  const totalClean = ledger.reduce((acc, curr) => acc + curr.clean_quantity, 0);
  const totalDirty = ledger.reduce((acc, curr) => acc + curr.dirty_quantity, 0);
  const totalWash = ledger.reduce((acc, curr) => acc + curr.in_wash_quantity, 0);

  return (
    <div className="space-y-6">
      {/* Header section with gradient and glow */}
      <div className="relative bg-slate-900 border border-slate-700/50 rounded-2xl p-6 overflow-hidden shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-teal-500/10 opacity-50" />
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
              <Sparkles className="w-8 h-8 text-blue-400" />
              {t("Linen & Laundry Control Center")}
            </h1>
            <p className="mt-2 text-sm text-slate-400">
              {t("Monitor clean inventory, track dirty collections, and manage wash cycles in real-time.")}
            </p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={() => setShowCategoryModal(true)}
              className="px-4 py-2 bg-slate-800 text-slate-300 border border-slate-700 rounded-xl text-sm font-semibold hover:bg-slate-700 hover:text-white transition-all flex items-center gap-2">
              <Plus className="w-4 h-4" />
              {t("New Category")}
            </button>
            <button 
              onClick={() => { setTxType("ISSUE_TO_WARD"); setShowTransactionModal(true); }}
              className="px-4 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-sm font-semibold hover:bg-blue-500/20 transition-all flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              {t("Distribute Clean Linen")}
            </button>
            <button 
               onClick={() => { setTxType("COLLECT_FROM_WARD"); setShowTransactionModal(true); }}
               className="px-4 py-2 bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-xl text-sm font-semibold shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 hover:-translate-y-0.5 transition-all">
              {t("Collect Dirty Linen")}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 p-1 bg-slate-900/50 border border-slate-800 rounded-xl w-fit">
        {["inventory", "transactions", "laundry"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab 
                ? "bg-slate-800 text-white shadow-sm border border-slate-700" 
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
            }`}
          >
            {t(tab.charAt(0).toUpperCase() + tab.slice(1))}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        
        {/* Sidebar Summary */}
        <div className="md:col-span-1 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">
              {t("Hospital Status")}
            </h3>
            {loading ? (
              <div className="flex justify-center p-4"><Loader2 className="w-6 h-6 animate-spin text-slate-500" /></div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    {t("Clean Ready")}
                  </span>
                  <span className="font-mono text-emerald-400 font-bold">{totalClean}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-500 hover:animate-pulse"></span>
                    {t("Dirty/Collected")}
                  </span>
                  <span className="font-mono text-amber-400 font-bold">{totalDirty}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    {t("In Wash Cycle")}
                  </span>
                  <span className="font-mono text-blue-400 font-bold">{totalWash}</span>
                </div>
                
                {/* Dynamic alert if any clean stock goes below 10 */}
                {ledger.filter(l => l.clean_quantity < 10).length > 0 && (
                  <div className="pt-4 border-t border-slate-800">
                    <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-3 flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-xs font-semibold text-rose-400 block mb-1">Low Stock Alert</span>
                        <span className="text-[11px] text-rose-300/80 leading-tight block">
                          Some wards are crucially low on clean linen.
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Data Table */}
        <div className="md:col-span-3">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden min-h-[400px]">
            <div className="p-5 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
              <h2 className="text-base font-semibold text-white">
                {activeTab === "inventory" ? t("Live Inventory Ledger") : 
                 activeTab === "transactions" ? t("Recent Movement Logs") : 
                 t("Active Laundry Batches")}
              </h2>
            </div>
            
            {loading ? (
                <div className="flex items-center justify-center p-20">
                    <Loader2 className="w-8 h-8 animate-spin text-slate-500" />
                </div>
            ) : activeTab === "inventory" ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-800/30 border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400">
                      <th className="px-5 py-4 font-medium">{t("Department")}</th>
                      <th className="px-5 py-4 font-medium">{t("Category")}</th>
                      <th className="px-5 py-4 font-medium text-right">{t("Clean (Ready)")}</th>
                      <th className="px-5 py-4 font-medium text-right">{t("Dirty (Collected)")}</th>
                      <th className="px-5 py-4 font-medium text-right">{t("In Wash")}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {ledger.length === 0 ? (
                        <tr><td colSpan={5} className="text-center py-10 text-slate-500 text-sm">No inventory records found.</td></tr>
                    ) : ledger.map((row) => (
                      <tr key={row.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-5 py-3.5 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-slate-500" />
                            <span className="text-sm font-medium text-slate-200">{row.department_id}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3.5 whitespace-nowrap text-sm text-slate-400">
                          {row.category?.name || "Unknown"}
                        </td>
                        <td className="px-5 py-3.5 whitespace-nowrap text-right">
                          <span className="inline-flex items-center justify-center px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 font-mono text-sm font-medium">
                            {row.clean_quantity}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 whitespace-nowrap text-right">
                          <span className={`inline-flex items-center justify-center px-2 py-1 rounded font-mono text-sm font-medium ${row.dirty_quantity > 0 ? "bg-amber-500/10 text-amber-400" : "text-slate-500"}`}>
                            {row.dirty_quantity}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 whitespace-nowrap text-right">
                          <span className={`inline-flex items-center justify-center px-2 py-1 rounded font-mono text-sm font-medium ${row.in_wash_quantity > 0 ? "bg-blue-500/10 text-blue-400" : "text-slate-500"}`}>
                            {row.in_wash_quantity}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : activeTab === "laundry" ? (
                <div className="p-8">
                     {batches.length === 0 ? (
                        <div className="text-center py-10 text-slate-500 text-sm">No active laundry batches today.</div>
                    ) : (
                        <div className="space-y-4">
                            {batches.map(b => (
                                <div key={b.id} className="flex justify-between items-center p-4 bg-slate-800/30 rounded-lg border border-slate-700">
                                    <div>
                                        <div className="font-semibold text-white">Batch #{b.batch_number}</div>
                                        <div className="text-xs text-slate-400 mt-1">{new Date(b.start_time).toLocaleString()} - {b.total_weight_kg} kg</div>
                                    </div>
                                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 uppercase tracking-wider">{b.status}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-sm">
                {t("No recent transactions fetched.")}
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Transaction Modal */}
      {showTransactionModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
                <div className="flex items-center justify-between p-5 border-b border-slate-800">
                    <h3 className="font-bold text-white">
                        {txType === "ISSUE_TO_WARD" ? t("Issue Clean Linen to Ward") : t("Collect Dirty Linen from Ward")}
                    </h3>
                    <button onClick={() => setShowTransactionModal(false)} className="text-slate-400 hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <form onSubmit={handleTransaction} className="p-5 space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">{t("Ward / Department")}</label>
                        <select 
                            value={formDept} 
                            onChange={(e) => setFormDept(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                        >
                            <option value="ICU Ward">ICU Ward</option>
                            <option value="Emergency Room">Emergency Room</option>
                            <option value="Surgical Ward">Surgical Ward</option>
                            <option value="Maternity Ward">Maternity Ward</option>
                            <option value="General Ward A">General Ward A</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">{t("Linen Category")}</label>
                        <select 
                            value={formCategory} 
                            onChange={(e) => setFormCategory(e.target.value)}
                            required
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                        >
                            <option value="">-- {t("Select Category")} --</option>
                            {categories.map(c => <option key={c.id} value={c.id}>{t(c.name)}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">{t("Quantity")}</label>
                        <input 
                            type="number" 
                            min="1" 
                            required
                            value={formQty}
                            onChange={(e) => setFormQty(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                            placeholder={t("Enter amount...")}
                        />
                    </div>
                    <div className="pt-4 flex justify-end gap-3">
                        <button type="button" onClick={() => setShowTransactionModal(false)} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">
                            {t("Cancel")}
                        </button>
                        <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-blue-500/30 transition-all">
                            {t("Confirm Transaction")}
                        </button>
                    </div>
                </form>
            </div>
        </div>
      )}

      {/* Category Modal */}
      {showCategoryModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
                <div className="flex items-center justify-between p-5 border-b border-slate-800">
                    <h3 className="font-bold text-white">
                        {t("Create Linen Category")}
                    </h3>
                    <button onClick={() => setShowCategoryModal(false)} className="text-slate-400 hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <form onSubmit={handleCreateCategory} className="p-5 space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">{t("Category Name")}</label>
                        <input 
                            type="text" 
                            required
                            value={catName}
                            onChange={(e) => setCatName(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                            placeholder="e.g. Standard Bed Sheet"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">{t("Description")}</label>
                        <input 
                            type="text" 
                            value={catDesc}
                            onChange={(e) => setCatDesc(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                            placeholder="e.g. White Cotton Blend..."
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">{t("Expected Lifespan (Washes)")}</label>
                        <input 
                            type="number" 
                            min="1" 
                            required
                            value={catLifespan}
                            onChange={(e) => setCatLifespan(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                            placeholder="100"
                        />
                    </div>
                    <div className="pt-4 flex justify-end gap-3">
                        <button type="button" onClick={() => setShowCategoryModal(false)} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">
                            {t("Cancel")}
                        </button>
                        <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-blue-500/30 transition-all">
                            {t("Save Category")}
                        </button>
                    </div>
                </form>
            </div>
        </div>
      )}

    </div>
  );
}
