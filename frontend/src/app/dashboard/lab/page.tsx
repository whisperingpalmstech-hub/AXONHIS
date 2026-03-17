"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/ui/TopNav";
import {
  FlaskConical, TestTubes, Microscope, Activity, AlertTriangle, CheckCircle2,
  Clock, Search, Plus, BarChart3, FileText, ArrowRight, Loader2,
  Pipette, Beaker, ShieldCheck, X, TrendingUp, RefreshCw, Filter
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

const CATEGORIES = [
  { key: "hematology", label: "Hematology", icon: Pipette, color: "text-red-600", bg: "bg-red-50", border: "border-red-100" },
  { key: "biochemistry", label: "Biochemistry", icon: Beaker, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-100" },
  { key: "microbiology", label: "Microbiology", icon: Microscope, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-100" },
  { key: "immunology", label: "Immunology", icon: ShieldCheck, color: "text-violet-600", bg: "bg-violet-50", border: "border-violet-100" },
];

const SAMPLE_STATUS: Record<string, { badge: string; label: string }> = {
  COLLECTED: { badge: "badge-info", label: "Collected" },
  IN_TRANSIT: { badge: "badge-warning", label: "In Transit" },
  RECEIVED_IN_LAB: { badge: "badge-neutral", label: "Received" },
  PROCESSING: { badge: "badge-info", label: "Processing" },
  COMPLETED: { badge: "badge-success", label: "Completed" },
  REJECTED: { badge: "badge-error", label: "Rejected" },
};

const FLAG_STYLES: Record<string, { badge: string; label: string }> = {
  NORMAL: { badge: "badge-success", label: "Normal" },
  HIGH: { badge: "badge-warning", label: "High" },
  LOW: { badge: "badge-info", label: "Low" },
  CRITICAL_HIGH: { badge: "badge-error", label: "Critical High" },
  CRITICAL_LOW: { badge: "badge-error", label: "Critical Low" },
};

type TabKey = "dashboard" | "catalog" | "samples" | "results" | "validation";

export default function LabPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [tests, setTests] = useState<any[]>([]);
  const [samples, setSamples] = useState<any[]>([]);
  const [pendingValidation, setPendingValidation] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [sampleStatusFilter, setSampleStatusFilter] = useState("");
  const [showAddTest, setShowAddTest] = useState(false);
  const [showResultModal, setShowResultModal] = useState<any>(null);
  const [resultForm, setResultForm] = useState({
    test_id: "", value: "", numeric_value: "", notes: "", unit: "", reference_range: ""
  });

  const [newTest, setNewTest] = useState({
    code: "", name: "", category: "hematology", sample_type: "blood",
    unit: "", normal_range_low: "", normal_range_high: "",
    reference_range: "", critical_low: "", critical_high: "", price: "0",
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const headers = authHeaders();
      const [statsRes, testsRes, samplesRes, pendingRes] = await Promise.all([
        fetch(`${API}/api/v1/lab/dashboard/stats`, { headers }),
        fetch(`${API}/api/v1/lab/tests`, { headers }),
        fetch(`${API}/api/v1/lab/samples`, { headers }),
        fetch(`${API}/api/v1/lab/results/pending-validation`, { headers }),
      ]);
      if (statsRes.ok) setStats(await statsRes.json());
      if (testsRes.ok) setTests(await testsRes.json());
      if (samplesRes.ok) setSamples(await samplesRes.json());
      if (pendingRes.ok) setPendingValidation(await pendingRes.json());
    } catch (e) { console.error("Failed to load lab data:", e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAddTest = async () => {
    try {
      const body: any = { ...newTest };
      ["normal_range_low","normal_range_high","critical_low","critical_high"].forEach(k => {
        if (body[k]) body[k] = parseFloat(body[k]); else delete body[k];
      });
      body.price = parseFloat(body.price) || 0;
      const res = await fetch(`${API}/api/v1/lab/tests`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(body),
      });
      if (res.ok) {
        setShowAddTest(false);
        setNewTest({ code: "", name: "", category: "hematology", sample_type: "blood",
          unit: "", normal_range_low: "", normal_range_high: "",
          reference_range: "", critical_low: "", critical_high: "", price: "0" });
        loadData();
      } else {
        const err = await res.json();
        alert(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
      }
    } catch { alert("Failed to create test"); }
  };

  const handleValidate = async (resultId: string, status: string) => {
    try {
      const res = await fetch(`${API}/api/v1/lab/validate`, {
        method: "POST", headers: authHeaders(),
        body: JSON.stringify({ result_id: resultId, validation_status: status }),
      });
      if (res.ok) loadData();
      else { const err = await res.json(); alert(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)); }
    } catch { alert("Validation failed"); }
  };

  const handleSubmitResult = async () => {
    if (!showResultModal || !resultForm.test_id || !resultForm.value) {
      alert("Please select a test and enter a value");
      return;
    }
    setLoading(true);
    try {
      // Fetch lab order to get patient_id and actual order_id
      const labOrderRes = await fetch(`${API}/api/v1/lab/orders/${showResultModal.lab_order_id}`, { headers: authHeaders() });
      if (!labOrderRes.ok) throw new Error("Could not fetch Lab Order details");
      const labOrder = await labOrderRes.json();

      const body = {
        sample_id: showResultModal.id,
        test_id: resultForm.test_id,
        order_id: labOrder.order_id,
        patient_id: labOrder.patient_id,
        value: resultForm.value,
        numeric_value: parseFloat(resultForm.numeric_value) || null,
        unit: resultForm.unit || undefined,
        reference_range: resultForm.reference_range || undefined,
        notes: resultForm.notes || undefined,
      };

      const res = await fetch(`${API}/api/v1/lab/results`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(body)
      });
      if (res.ok) {
        setShowResultModal(null);
        setResultForm({ test_id: "", value: "", numeric_value: "", notes: "", unit: "", reference_range: "" });
        loadData();
      } else {
        const err = await res.json();
        alert(err.detail ? JSON.stringify(err.detail) : "Failed to enter result");
      }
    } catch (e: any) {
      alert(e.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleReceiveSample = async (sampleId: string) => {
    const res = await fetch(`${API}/api/v1/lab/samples/${sampleId}/receive`, { method: "POST", headers: authHeaders() });
    if (res.ok) loadData();
  };

  const handleProcessSample = async (sampleId: string) => {
    const res = await fetch(`${API}/api/v1/lab/samples/${sampleId}/process`, { method: "POST", headers: authHeaders() });
    if (res.ok) loadData();
  };

  const filteredTests = tests.filter((t: any) => {
    const matchSearch = !searchTerm || t.name.toLowerCase().includes(searchTerm.toLowerCase()) || t.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchCategory = !categoryFilter || t.category === categoryFilter;
    return matchSearch && matchCategory;
  });

  const filteredSamples = samples.filter((s: any) => {
    const matchSearch = !searchTerm || s.sample_barcode.toLowerCase().includes(searchTerm.toLowerCase());
    const matchStatus = !sampleStatusFilter || s.status === sampleStatusFilter;
    return matchSearch && matchStatus;
  });

  const TABS: { key: TabKey; label: string; icon: any; count?: number }[] = [
    { key: "dashboard", label: "Dashboard", icon: BarChart3 },
    { key: "catalog", label: "Test Catalog", icon: FlaskConical, count: tests.length },
    { key: "samples", label: "Samples", icon: TestTubes, count: samples.length },
    { key: "results", label: "Results", icon: FileText },
    { key: "validation", label: "Validation", icon: ShieldCheck, count: pendingValidation.length },
  ];

  return (
    <div>
      <TopNav title="Laboratory Information System" />

      <div className="p-6 space-y-6">
        {/* Tab Navigation */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key}
                onClick={() => { setActiveTab(tab.key); setSearchTerm(""); setCategoryFilter(""); setSampleStatusFilter(""); }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
                  isActive
                    ? "bg-white text-[var(--accent-primary)] shadow-sm border border-[var(--border)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-slate-50"
                }`}>
                <Icon size={16} />
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span className={`text-[10px] font-bold rounded-full px-1.5 py-0.5 min-w-[18px] text-center ${
                    tab.key === "validation" ? "bg-red-100 text-red-700" : "bg-slate-200 text-slate-600"
                  }`}>{tab.count}</span>
                )}
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 size={28} className="animate-spin text-[var(--accent-primary)]" />
          </div>
        ) : (
          <>
            {/* ═══ DASHBOARD TAB ═══ */}
            {activeTab === "dashboard" && (
              <div className="space-y-6">
                {/* Stat Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                  {[
                    { label: "Pending Samples", value: stats?.pending_samples ?? 0, icon: Clock, cBg: "bg-amber-50", cIcon: "text-amber-600", cBorder: "border-amber-100" },
                    { label: "Processing", value: stats?.processing_samples ?? 0, icon: Activity, cBg: "bg-cyan-50", cIcon: "text-cyan-600", cBorder: "border-cyan-100" },
                    { label: "Completed Today", value: stats?.completed_today ?? 0, icon: CheckCircle2, cBg: "bg-emerald-50", cIcon: "text-emerald-600", cBorder: "border-emerald-100" },
                    { label: "Critical Results", value: stats?.critical_results ?? 0, icon: AlertTriangle, cBg: "bg-red-50", cIcon: "text-red-600", cBorder: "border-red-100" },
                    { label: "Pending Validation", value: stats?.pending_validation ?? 0, icon: ShieldCheck, cBg: "bg-violet-50", cIcon: "text-violet-600", cBorder: "border-violet-100" },
                    { label: "Test Catalog", value: stats?.total_tests_catalog ?? 0, icon: FlaskConical, cBg: "bg-blue-50", cIcon: "text-blue-600", cBorder: "border-blue-100" },
                  ].map((c, i) => {
                    const Icon = c.icon;
                    return (
                      <div key={i} className={`card card-body !p-4 ${c.cBorder}`}>
                        <div className="flex items-center justify-between mb-3">
                          <div className={`w-10 h-10 rounded-xl ${c.cBg} flex items-center justify-center`}>
                            <Icon size={20} className={c.cIcon} />
                          </div>
                          {c.label === "Critical Results" && c.value > 0 && (
                            <span className="badge-error text-[10px] animate-pulse">ALERT</span>
                          )}
                        </div>
                        <p className="stat-value !text-2xl">{c.value}</p>
                        <p className="stat-label !text-xs !mt-0.5">{c.label}</p>
                      </div>
                    );
                  })}
                </div>

                {/* Two-column: Categories + Recent Samples */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Test Categories */}
                  <div className="card">
                    <div className="card-header">
                      <h3 className="font-semibold text-sm">Test Categories</h3>
                      <button onClick={() => setActiveTab("catalog")} className="text-xs text-[var(--accent-primary)] hover:underline">
                        View all &rarr;
                      </button>
                    </div>
                    <div className="divide-y divide-[var(--border)]">
                      {CATEGORIES.map(cat => {
                        const Icon = cat.icon;
                        const count = tests.filter((t: any) => t.category === cat.key).length;
                        return (
                          <button key={cat.key}
                            onClick={() => { setActiveTab("catalog"); setCategoryFilter(cat.key); }}
                            className="w-full flex items-center gap-3 px-5 py-3.5 hover:bg-slate-50 transition-colors text-left">
                            <div className={`w-9 h-9 rounded-lg ${cat.bg} flex items-center justify-center`}>
                              <Icon size={18} className={cat.color} />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-[var(--text-primary)]">{cat.label}</p>
                              <p className="text-xs text-[var(--text-secondary)]">{count} tests</p>
                            </div>
                            <ArrowRight size={14} className="text-slate-400" />
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Recent Samples */}
                  <div className="lg:col-span-2 card">
                    <div className="card-header">
                      <h3 className="font-semibold text-sm">Recent Samples</h3>
                      <button onClick={() => setActiveTab("samples")} className="text-xs text-[var(--accent-primary)] hover:underline">
                        View all &rarr;
                      </button>
                    </div>
                    {samples.length > 0 ? (
                      <div className="space-y-3">
                        {samples.slice(0, 5).map((s: any) => {
                          const st = SAMPLE_STATUS[s.status] || SAMPLE_STATUS.COLLECTED;
                          return (
                            <div key={s.id} className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex items-center justify-between">
                              <div className="flex flex-col">
                                <code className="text-xs font-semibold text-[var(--accent-primary)] bg-[var(--accent-primary-light)] px-2 py-0.5 rounded w-max mb-1">
                                  {s.sample_barcode}
                                </code>
                                <span className="text-xs capitalize text-slate-600 font-medium">{s.sample_type} &middot; {new Date(s.collection_time).toLocaleString()}</span>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className={st.badge}>{st.label}</span>
                                {s.status === "COLLECTED" && (
                                  <button onClick={() => handleReceiveSample(s.id)} className="btn-secondary btn-sm">Receive</button>
                                )}
                                {s.status === "RECEIVED_IN_LAB" && (
                                  <button onClick={() => handleProcessSample(s.id)} className="btn-primary btn-sm">Process</button>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="card-body text-center text-[var(--text-secondary)]">
                        <TestTubes size={36} className="mx-auto mb-2 opacity-30" />
                        <p className="text-sm">No samples yet. Samples are created when lab orders are collected.</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ═══ TEST CATALOG TAB ═══ */}
            {activeTab === "catalog" && (
              <div className="space-y-5">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex gap-2 flex-1 w-full sm:w-auto">
                    <div className="relative flex-1 max-w-sm">
                      <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                      <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                        placeholder="Search by name or code…" className="input-field pl-9" />
                    </div>
                    <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)} className="input-field w-auto">
                      <option value="">All Categories</option>
                      {CATEGORIES.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
                    </select>
                  </div>
                  <button onClick={() => setShowAddTest(true)} className="btn-primary">
                    <Plus size={16} /> Add Test
                  </button>
                </div>

                {filteredTests.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filteredTests.map((test: any) => {
                      const cat = CATEGORIES.find(c => c.key === test.category);
                      const CatIcon = cat?.icon || FlaskConical;
                      return (
                        <div key={test.id} className={`card card-body !p-5 hover:shadow-md transition-shadow ${cat?.border || "border-slate-200"} flex flex-col justify-between`}>
                          <div className="flex items-start gap-3 mb-4">
                            <div className={`w-12 h-12 rounded-xl border ${cat?.bg || "bg-slate-50"} ${cat?.border || "border-slate-100"} flex items-center justify-center flex-shrink-0`}>
                              <CatIcon size={24} className={cat?.color || "text-slate-600"} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-base font-semibold text-[var(--text-primary)] truncate">{test.name}</p>
                              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                                <code className="text-xs font-semibold text-[var(--accent-primary)] bg-[var(--accent-primary-light)] px-1.5 py-0.5 rounded border border-blue-200">
                                  {test.code}
                                </code>
                                <span className="badge badge-neutral bg-slate-100 text-slate-600 capitalize">{test.sample_type}</span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-x-4 gap-y-3 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Reference Range</span>
                              <span className="font-medium text-slate-700">{test.reference_range || "—"}</span>
                            </div>
                            
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Normal Limits</span>
                              <span className="font-medium text-slate-700">
                                {(test.normal_range_low == null && test.normal_range_high == null) ? "—" : 
                                 `${test.normal_range_low ?? ""} - ${test.normal_range_high ?? ""} ${test.unit || ""}`}
                              </span>
                            </div>

                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Critical Limits</span>
                              {(test.critical_low != null || test.critical_high != null) ? (
                                <span className="font-medium text-red-600 flex items-center gap-1">
                                  <AlertTriangle size={12} className="shrink-0" />
                                  {test.critical_low ?? "—"} / {test.critical_high ?? "—"} {test.unit || ""}
                                </span>
                              ) : (
                                <span className="font-medium text-slate-700">—</span>
                              )}
                            </div>
                            
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Price</span>
                              <span className="font-medium text-[var(--accent-primary)]">
                                {test.price ? `$${test.price}` : "—"}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <FlaskConical size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">No tests found. Click &quot;Add Test&quot; to create your first lab test.</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ SAMPLES TAB ═══ */}
            {activeTab === "samples" && (
              <div className="space-y-5">
                <div className="flex gap-2">
                  <div className="relative flex-1 max-w-sm">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                    <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                      placeholder="Search by barcode…" className="input-field pl-9" />
                  </div>
                  <select value={sampleStatusFilter} onChange={e => setSampleStatusFilter(e.target.value)} className="input-field w-auto">
                    <option value="">All Statuses</option>
                    {Object.entries(SAMPLE_STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                  </select>
                </div>

                {filteredSamples.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredSamples.map((s: any) => {
                      const st = SAMPLE_STATUS[s.status] || SAMPLE_STATUS.COLLECTED;
                      return (
                        <div key={s.id} className="card card-body !p-5 hover:shadow-md transition-shadow">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <code className="text-[10px] font-bold text-[var(--accent-primary)] bg-[var(--accent-primary-light)] px-2 py-1 rounded inline-block mb-2">
                                {s.sample_barcode}
                              </code>
                              <div className="flex items-center gap-2">
                                <TestTubes size={16} className="text-slate-400" />
                                <span className="text-base font-semibold capitalize text-slate-800">{s.sample_type}</span>
                              </div>
                            </div>
                            <span className={st.badge}>{st.label}</span>
                          </div>

                          <div className="space-y-2 mb-5">
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-slate-500 flex items-center gap-1"><Clock size={12} /> Collected</span>
                              <span className="font-medium text-slate-700">{new Date(s.collection_time).toLocaleString()}</span>
                            </div>
                            {s.received_at && (
                              <div className="flex justify-between items-center text-xs">
                                <span className="text-slate-500 flex items-center gap-1"><Activity size={12} /> Received</span>
                                <span className="font-medium text-slate-700">{new Date(s.received_at).toLocaleString()}</span>
                              </div>
                            )}
                          </div>

                          <div className="flex gap-2 w-full mt-auto">
                            {s.status === "COLLECTED" && <button onClick={() => handleReceiveSample(s.id)} className="btn-secondary btn-sm flex-1">Receive</button>}
                            {s.status === "RECEIVED_IN_LAB" && <button onClick={() => handleProcessSample(s.id)} className="btn-primary btn-sm flex-1">Process In Analyzer</button>}
                            {s.status === "PROCESSING" && <button onClick={() => setShowResultModal(s)} className="btn bg-violet-600 text-white hover:bg-violet-700 btn-sm flex-1"><Plus size={14}/> Enter Result</button>}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <TestTubes size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">No samples found.</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ RESULTS TAB ═══ */}
            {activeTab === "results" && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <FileText size={18} className="text-[var(--accent-primary)]" />
                  <h3 className="font-semibold">All Lab Results</h3>
                </div>
                {pendingValidation.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {pendingValidation.map((r: any) => {
                      const flag = FLAG_STYLES[r.result_flag] || FLAG_STYLES.NORMAL;
                      return (
                        <div key={r.id} className={`card card-body !p-5 ${r.is_critical ? "border-red-200 bg-red-50/50" : ""}`}>
                          <div className="flex flex-col gap-2">
                            <div className="flex items-start justify-between">
                              <span className={`${flag.badge} ${r.is_critical ? "animate-pulse" : ""}`}>
                                {r.is_critical && <AlertTriangle size={10} className="mr-1 inline" />}
                                {flag.label}
                              </span>
                              <span className="badge-neutral text-[10px]">{r.status}</span>
                            </div>
                            <div className="text-center my-4">
                              <span className="text-3xl font-bold text-slate-800">{r.value}</span>
                              <span className="text-sm text-slate-500 ml-1">{r.unit || ""}</span>
                            </div>
                            <div className="bg-slate-50 rounded p-2 text-xs border border-slate-100 flex flex-col gap-1">
                              <div className="flex justify-between text-slate-600">
                                <span>Reference:</span>
                                <span className="font-medium">{r.reference_range || "—"}</span>
                              </div>
                              <div className="flex justify-between text-slate-400">
                                <span>Entered:</span>
                                <span>{new Date(r.entered_at).toLocaleDateString()}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <FileText size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">No results yet. Results appear after entering values for processed samples.</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ VALIDATION TAB ═══ */}
            {activeTab === "validation" && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <ShieldCheck size={18} className="text-[var(--accent-primary)]" />
                  <h3 className="font-semibold">Pending Validation ({pendingValidation.length})</h3>
                </div>

                {pendingValidation.length > 0 ? (
                  <div className="space-y-3">
                    {pendingValidation.map((r: any) => {
                      const flag = FLAG_STYLES[r.result_flag] || FLAG_STYLES.NORMAL;
                      return (
                        <div key={r.id} className={`card card-body !p-5 ${r.is_critical ? "border-red-200 bg-red-50/50" : ""}`}>
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                            <div>
                              <div className="flex items-center gap-3 mb-2">
                                <span className="text-xl font-bold text-[var(--text-primary)]">{r.value}</span>
                                <span className="text-sm text-[var(--text-secondary)]">{r.unit || ""}</span>
                                <span className={`${flag.badge} ${r.is_critical ? "animate-pulse" : ""}`}>
                                  {r.is_critical && <AlertTriangle size={10} className="mr-1 inline" />}
                                  {flag.label}
                                </span>
                              </div>
                              <p className="text-xs text-[var(--text-secondary)]">
                                Reference: {r.reference_range || "—"} &middot; Entered: {new Date(r.entered_at).toLocaleString()}
                              </p>
                            </div>
                            <div className="flex gap-2 flex-shrink-0">
                              <button onClick={() => handleValidate(r.id, "VALIDATED")}
                                className="btn bg-[var(--success)] text-white hover:bg-green-700 focus:ring-green-400 btn-sm">
                                <CheckCircle2 size={14} /> Validate
                              </button>
                              <button onClick={() => handleValidate(r.id, "REJECTED")} className="btn-danger btn-sm">
                                <X size={14} /> Reject
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <CheckCircle2 size={40} className="mx-auto mb-3 text-emerald-300" />
                    <p className="font-medium text-[var(--text-primary)]">All results validated!</p>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">No pending validations at this time.</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* ═══ ADD TEST MODAL ═══ */}
      {showAddTest && (
        <div className="modal-overlay" onClick={() => setShowAddTest(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2">
                <FlaskConical size={18} className="text-[var(--accent-primary)]" />
                Add Lab Test
              </h3>
              <button onClick={() => setShowAddTest(false)} className="btn-ghost p-1 rounded">
                <X size={18} />
              </button>
            </div>
            <div className="modal-body space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="input-label">Test Code</label>
                  <input className="input-field" placeholder="e.g. CBC" value={newTest.code}
                    onChange={e => setNewTest(p => ({ ...p, code: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">Test Name</label>
                  <input className="input-field" placeholder="Complete Blood Count" value={newTest.name}
                    onChange={e => setNewTest(p => ({ ...p, name: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">Category</label>
                  <select className="input-field" value={newTest.category}
                    onChange={e => setNewTest(p => ({ ...p, category: e.target.value }))}>
                    {CATEGORIES.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="input-label">Sample Type</label>
                  <select className="input-field" value={newTest.sample_type}
                    onChange={e => setNewTest(p => ({ ...p, sample_type: e.target.value }))}>
                    {["blood","urine","serum","plasma","csf","stool","sputum","swab"].map(s => (
                      <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="input-label">Unit</label>
                  <input className="input-field" placeholder="e.g. g/dL" value={newTest.unit}
                    onChange={e => setNewTest(p => ({ ...p, unit: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">Reference Range</label>
                  <input className="input-field" placeholder="e.g. 12-16 g/dL" value={newTest.reference_range}
                    onChange={e => setNewTest(p => ({ ...p, reference_range: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">Normal Low</label>
                  <input className="input-field" type="number" step="any" placeholder="12" value={newTest.normal_range_low}
                    onChange={e => setNewTest(p => ({ ...p, normal_range_low: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">Normal High</label>
                  <input className="input-field" type="number" step="any" placeholder="16" value={newTest.normal_range_high}
                    onChange={e => setNewTest(p => ({ ...p, normal_range_high: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">Critical Low</label>
                  <input className="input-field" type="number" step="any" placeholder="5" value={newTest.critical_low}
                    onChange={e => setNewTest(p => ({ ...p, critical_low: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">Critical High</label>
                  <input className="input-field" type="number" step="any" placeholder="20" value={newTest.critical_high}
                    onChange={e => setNewTest(p => ({ ...p, critical_high: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">Price</label>
                  <input className="input-field" type="number" step="any" placeholder="0" value={newTest.price}
                    onChange={e => setNewTest(p => ({ ...p, price: e.target.value }))} />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddTest(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleAddTest} className="btn-primary">
                <Plus size={16} /> Create Test
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ ENTER RESULT MODAL ═══ */}
      {showResultModal && (
        <div className="modal-overlay" onClick={() => setShowResultModal(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2">
                <FileText size={18} className="text-[var(--accent-primary)]" />
                Enter Lab Result
              </h3>
              <button onClick={() => setShowResultModal(null)} className="btn-ghost p-1 rounded">
                <X size={18} />
              </button>
            </div>
            <div className="modal-body space-y-4">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 flex justify-between items-center mb-4 text-sm">
                <div>
                  <span className="text-slate-500 block text-xs">Sample Barcode</span>
                  <span className="font-semibold text-slate-800">{showResultModal.sample_barcode}</span>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 block text-xs">Type</span>
                  <span className="font-medium capitalize text-slate-800">{showResultModal.sample_type}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="input-label">Select Test <span className="text-red-500">*</span></label>
                  <select className="input-field" value={resultForm.test_id} onChange={e => {
                    const test = tests.find(t => t.id === e.target.value);
                    setResultForm(p => ({ 
                      ...p, 
                      test_id: e.target.value,
                      unit: test?.unit || "",
                      reference_range: test?.reference_range || ""
                    }));
                  }}>
                    <option value="">-- Choose Test --</option>
                    {tests.filter(t => t.sample_type === showResultModal.sample_type).map((t: any) => (
                      <option key={t.id} value={t.id}>{t.name} ({t.code})</option>
                    ))}
                  </select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">Result Value (Text) <span className="text-red-500">*</span></label>
                    <input className="input-field" placeholder="e.g. 14.5 or Positive" value={resultForm.value}
                      onChange={e => setResultForm(p => ({ ...p, value: e.target.value }))} />
                  </div>
                  <div>
                    <label className="input-label">Numeric Value (Optional)</label>
                    <input className="input-field" type="number" step="any" placeholder="For triggers" value={resultForm.numeric_value}
                      onChange={e => setResultForm(p => ({ ...p, numeric_value: e.target.value }))} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">Unit</label>
                    <input className="input-field" placeholder="e.g. g/dL" value={resultForm.unit}
                      onChange={e => setResultForm(p => ({ ...p, unit: e.target.value }))} />
                  </div>
                  <div>
                    <label className="input-label">Reference Range</label>
                    <input className="input-field" placeholder="e.g. 12-16" value={resultForm.reference_range}
                      onChange={e => setResultForm(p => ({ ...p, reference_range: e.target.value }))} />
                  </div>
                </div>

                <div>
                  <label className="input-label">Notes / Remarks</label>
                  <textarea className="input-field min-h-[80px]" placeholder="Add any clinical remarks..." value={resultForm.notes}
                    onChange={e => setResultForm(p => ({ ...p, notes: e.target.value }))}></textarea>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowResultModal(null)} className="btn-secondary">Cancel</button>
              <button onClick={handleSubmitResult} className="btn bg-[var(--success)] text-white hover:bg-green-700">
                <CheckCircle2 size={16} /> Submit Result
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
