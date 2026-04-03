"use client";
import { useTranslation } from "@/i18n";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TopNav } from "@/components/ui/TopNav";
import {
  FlaskConical, TestTubes, Microscope, Activity, AlertTriangle, CheckCircle2,
  Clock, Search, Plus, BarChart3, FileText, ArrowRight, Loader2,
  Pipette, Beaker, ShieldCheck, X, TrendingUp, RefreshCw, Filter
} from "lucide-react";
import { WorkflowPipeline } from "@/components/ui/WorkflowPipeline";

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
  const { t } = useTranslation();
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
  const [multiResultForm, setMultiResultForm] = useState<any[]>([
    { id: Date.now(), test_id: "", value: "", numeric_value: "", notes: "", unit: "", reference_range: "" }
  ]);

  const [newTest, setNewTest] = useState({
    code: "", name: "", category: "hematology", sample_type: "blood",
    unit: "", normal_range_low: "", normal_range_high: "",
    reference_range: "", critical_low: "", critical_high: "", price: "0",
    is_calculated: false, calculation_formula: ""
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
      if (!body.is_calculated) {
          body.calculation_formula = null;
      }
      const res = await fetch(`${API}/api/v1/lab/tests`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(body),
      });
      if (res.ok) {
        setShowAddTest(false);
        setNewTest({ code: "", name: "", category: "hematology", sample_type: "blood",
          unit: "", normal_range_low: "", normal_range_high: "",
          reference_range: "", critical_low: "", critical_high: "", price: "0",
          is_calculated: false, calculation_formula: "" });
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
    // Validate we have at least one completely filled test
    const validResults = multiResultForm.filter((r: any) => r.test_id && r.value !== "");
    if (validResults.length === 0) {
      alert("Please select at least one test and enter a value.");
      return;
    }
    setLoading(true);
    try {
      const labOrderRes = await fetch(`${API}/api/v1/lab/orders/${showResultModal.lab_order_id}`, { headers: authHeaders() });
      if (!labOrderRes.ok) throw new Error("Could not fetch Lab Order details");
      const labOrder = await labOrderRes.json();

      // Submit each valid result concurrently
      const promises = validResults.map((rf: any) => {
          const body = {
            sample_id: showResultModal.id,
            test_id: rf.test_id,
            order_id: labOrder.order_id,
            patient_id: labOrder.patient_id,
            value: rf.value,
            numeric_value: parseFloat(rf.numeric_value) || null,
            unit: rf.unit || undefined,
            reference_range: rf.reference_range || undefined,
            notes: rf.notes || undefined,
          };
          return fetch(`${API}/api/v1/lab/results`, {
            method: "POST", headers: authHeaders(), body: JSON.stringify(body)
          }).then(async r => {
              if(!r.ok) {
                  const e = await r.json();
                  throw new Error(e.detail || "Batch result entry failed");
              }
              return r;
          });
      });

      await Promise.all(promises);
      setShowResultModal(null);
      setMultiResultForm([{ id: Date.now(), test_id: "", value: "", numeric_value: "", notes: "", unit: "", reference_range: "" }]);
      loadData();
    } catch (e: any) {
      alert(e.message || "An error occurred during consolidated entry");
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
      <div className="p-6 pb-0">
        <WorkflowPipeline 
          title="Lab Pipeline" 
          colorScheme="cyan"
          steps={[
            { label: "Order Created", status: "done" },
            { label: "Phlebotomy", status: "done" },
            { label: "Processing", status: "active" },
            { label: "Analyzer", status: "pending" },
            { label: "Validation", status: "pending" },
            { label: "Report", status: "pending" }
          ]} 
        />
      </div>
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
                            <span className="badge-error text-[10px] animate-pulse">{t("lab.alert")}</span>
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
                      <h3 className="font-semibold text-sm">{t("lab.testCategories")}</h3>
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
                      <h3 className="font-semibold text-sm">{t("lab.recentSamples")}</h3>
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
                                  <button onClick={() => handleReceiveSample(s.id)} className="btn-secondary btn-sm">{t("lab.receive")}</button>
                                )}
                                {s.status === "RECEIVED_IN_LAB" && (
                                  <button onClick={() => handleProcessSample(s.id)} className="btn-primary btn-sm">{t("lab.process")}</button>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="card-body text-center text-[var(--text-secondary)]">
                        <TestTubes size={36} className="mx-auto mb-2 opacity-30" />
                        <p className="text-sm">{t("lab.noSamplesYetSamplesAreCreatedW")}</p>
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
                      <input value={searchTerm} onChange={(e: any) => setSearchTerm(e.target.value)}
                        placeholder="Search by name or code…" className="input-field pl-9" />
                    </div>
                    <select value={categoryFilter} onChange={(e: any) => setCategoryFilter(e.target.value)} className="input-field w-auto">
                      <option value="">{t("lab.allCategories")}</option>
                      {CATEGORIES.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
                    </select>
                  </div>
                  <button onClick={() => setShowAddTest(true)} className="btn-primary">
                    <Plus size={16} />{t("lab.addTest")}</button>
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
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">{t("lab.referenceRange")}</span>
                              <span className="font-medium text-slate-700">{test.reference_range || "—"}</span>
                            </div>
                            
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">{t("lab.normalLimits")}</span>
                              <span className="font-medium text-slate-700">
                                {(test.normal_range_low == null && test.normal_range_high == null) ? "—" : 
                                 `${test.normal_range_low ?? ""} - ${test.normal_range_high ?? ""} ${test.unit || ""}`}
                              </span>
                            </div>

                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">{t("lab.criticalLimits")}</span>
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
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">{t("lab.price")}</span>
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
                    <input value={searchTerm} onChange={(e: any) => setSearchTerm(e.target.value)}
                      placeholder="Search by barcode…" className="input-field pl-9" />
                  </div>
                  <select value={sampleStatusFilter} onChange={(e: any) => setSampleStatusFilter(e.target.value)} className="input-field w-auto">
                    <option value="">{t("lab.allStatuses")}</option>
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
                              <span className="text-slate-500 flex items-center gap-1"><Clock size={12} />{t("lab.collected")}</span>
                              <span className="font-medium text-slate-700">{new Date(s.collection_time).toLocaleString()}</span>
                            </div>
                            {s.received_at && (
                              <div className="flex justify-between items-center text-xs">
                                <span className="text-slate-500 flex items-center gap-1"><Activity size={12} />{t("lab.received")}</span>
                                <span className="font-medium text-slate-700">{new Date(s.received_at).toLocaleString()}</span>
                              </div>
                            )}
                          </div>

                          <div className="flex gap-2 w-full mt-auto">
                            {s.status === "COLLECTED" && <button onClick={() => handleReceiveSample(s.id)} className="btn-secondary btn-sm flex-1">{t("lab.receive")}</button>}
                            {s.status === "RECEIVED_IN_LAB" && <button onClick={() => handleProcessSample(s.id)} className="btn-primary btn-sm flex-1">{t("lab.processInAnalyzer")}</button>}
                            {s.status === "PROCESSING" && <button onClick={() => setShowResultModal(s)} className="btn bg-violet-600 text-white hover:bg-violet-700 btn-sm flex-1"><Plus size={14}/>{t("lab.enterResult")}</button>}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <TestTubes size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">{t("lab.noSamplesFound")}</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ RESULTS TAB ═══ */}
            {activeTab === "results" && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <FileText size={18} className="text-[var(--accent-primary)]" />
                  <h3 className="font-semibold">{t("lab.allLabResults")}</h3>
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
                    <p className="text-[var(--text-secondary)]">{t("lab.noResultsYetResultsAppearAfter")}</p>
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
                                <CheckCircle2 size={14} />{t("lab.validate")}</button>
                              <button onClick={() => handleValidate(r.id, "REJECTED")} className="btn-danger btn-sm">
                                <X size={14} />{t("lab.reject")}</button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <CheckCircle2 size={40} className="mx-auto mb-3 text-emerald-300" />
                    <p className="font-medium text-[var(--text-primary)]">{t("lab.allResultsValidated")}</p>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">{t("lab.noPendingValidationsAtThisTime")}</p>
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
          <div className="modal-content" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2">
                <FlaskConical size={18} className="text-[var(--accent-primary)]" />{t("lab.addLabTest")}</h3>
              <button onClick={() => setShowAddTest(false)} className="btn-ghost p-1 rounded">
                <X size={18} />
              </button>
            </div>
            <div className="modal-body space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="input-label">{t("lab.testCode")}</label>
                  <input className="input-field" placeholder="e.g. CBC" value={newTest.code}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, code: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">{t("lab.testName")}</label>
                  <input className="input-field" placeholder="Complete Blood Count" value={newTest.name}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, name: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">{t("lab.category")}</label>
                  <select className="input-field" value={newTest.category}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, category: e.target.value }))}>
                    {CATEGORIES.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="input-label">{t("lab.sampleType")}</label>
                  <select className="input-field" value={newTest.sample_type}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, sample_type: e.target.value }))}>
                    {["blood","urine","serum","plasma","csf","stool","sputum","swab"].map(s => (
                      <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="input-label">{t("lab.unit")}</label>
                  <input className="input-field" placeholder="e.g. g/dL" value={newTest.unit}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, unit: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">{t("lab.referenceRange")}</label>
                  <input className="input-field" placeholder="e.g. 12-16 g/dL" value={newTest.reference_range}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, reference_range: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">{t("lab.normalLow")}</label>
                  <input className="input-field" type="number" step="any" placeholder="12" value={newTest.normal_range_low}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, normal_range_low: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">{t("lab.normalHigh")}</label>
                  <input className="input-field" type="number" step="any" placeholder="16" value={newTest.normal_range_high}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, normal_range_high: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">{t("lab.criticalLow")}</label>
                  <input className="input-field" type="number" step="any" placeholder="5" value={newTest.critical_low}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, critical_low: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">{t("lab.criticalHigh")}</label>
                  <input className="input-field" type="number" step="any" placeholder="20" value={newTest.critical_high}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, critical_high: e.target.value }))} />
                </div>
                <div>
                  <label className="input-label">{t("lab.price")}</label>
                  <input className="input-field" type="number" step="any" placeholder="0" value={newTest.price}
                    onChange={(e: any) => setNewTest((p: any) => ({ ...p, price: e.target.value }))} />
                </div>
              </div>
              
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 mt-4 space-y-3">
                 <div className="flex items-center gap-2">
                    <input type="checkbox" id="is_calc" checked={newTest.is_calculated} 
                       onChange={e => setNewTest(p => ({...p, is_calculated: e.target.checked}))} 
                       className="w-4 h-4 text-[var(--accent-primary)] border-gray-300 rounded focus:ring-[var(--accent-primary)]" 
                    />
                    <label htmlFor="is_calc" className="text-sm font-semibold text-slate-700">Calculated Test Parameter (Formula Engine)</label>
                 </div>
                 {newTest.is_calculated && (
                    <div>
                        <label className="input-label text-xs">Dynamic Calculation Formula (Use test codes as variables)</label>
                        <input className="input-field font-mono text-sm" placeholder="e.g. TC - HDL - (TG / 5)" value={newTest.calculation_formula}
                          onChange={(e: any) => setNewTest((p: any) => ({ ...p, calculation_formula: e.target.value }))} />
                        <p className="text-[10px] text-slate-500 mt-1">Example: For LDL calculation, enter <code className="bg-slate-200 px-1 rounded">TC - HDL - (TG / 5)</code> where variables are valid <b>Test Codes</b>.</p>
                    </div>
                 )}
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowAddTest(false)} className="btn-secondary">{t("lab.cancel")}</button>
              <button onClick={handleAddTest} className="btn-primary">
                <Plus size={16} />{t("lab.createTest")}</button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ CONSOLIDATED RESULT MODAL ═══ */}
      {showResultModal && (
        <div className="modal-overlay" onClick={() => setShowResultModal(null)}>
          <div className="modal-content max-w-4xl" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2">
                <FileText size={18} className="text-[var(--accent-primary)]" /> Consolidated Result Entry
              </h3>
              <button onClick={() => setShowResultModal(null)} className="btn-ghost p-1 rounded">
                <X size={18} />
              </button>
            </div>
            <div className="modal-body space-y-4 max-h-[70vh] overflow-y-auto">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 flex justify-between items-center mb-2 text-sm sticky top-0 z-10">
                <div>
                  <span className="text-slate-500 block text-xs">Sample Barcode</span>
                  <span className="font-semibold text-slate-800 tracking-wide">{showResultModal.sample_barcode}</span>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 block text-xs">Biomaterial / Group</span>
                  <span className="font-medium capitalize text-slate-800">{showResultModal.sample_type}</span>
                </div>
              </div>

              {/* Dynamic Rows */}
              <div className="space-y-4 pt-2">
                  <div className="hidden md:grid grid-cols-12 gap-3 px-3 text-[10px] uppercase font-bold text-slate-400">
                      <div className="col-span-3">Test Parameter <span className="text-red-500">*</span></div>
                      <div className="col-span-2">Qualitative Value <span className="text-red-500">*</span></div>
                      <div className="col-span-2">Numeric / Unit</div>
                      <div className="col-span-2">Reference Bounds</div>
                      <div className="col-span-2">Clinical Notes</div>
                      <div className="col-span-1"></div>
                  </div>
                  
                  {multiResultForm.map((row: any, rIdx: number) => (
                      <div key={row.id} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-start bg-white p-3 md:p-0 rounded-lg md:rounded-none border border-slate-100 md:border-0 shadow-sm md:shadow-none relative">
                          <div className="col-span-1 md:col-span-3">
                              <label className="md:hidden text-[10px] font-bold text-slate-400 block mb-1">Test Parameter</label>
                              <select className="input-field !text-sm !py-1.5" value={row.test_id} onChange={(e: any) => {
                                const test = tests.find((t: any) => t.id === e.target.value);
                                const updated = [...multiResultForm];
                                updated[rIdx] = { 
                                  ...updated[rIdx], 
                                  test_id: e.target.value,
                                  unit: test?.unit || "",
                                  reference_range: test?.reference_range || ""
                                };
                                setMultiResultForm(updated);
                              }}>
                                <option value="">-- Choose Test --</option>
                                {tests.filter((t: any) => t.sample_type === showResultModal.sample_type).map((t: any) => (
                                  <option key={t.id} value={t.id}>{t.name} ({t.code})</option>
                                ))}
                              </select>
                          </div>
                          
                          <div className="col-span-1 md:col-span-2">
                              <label className="md:hidden text-[10px] font-bold text-slate-400 block mb-1">Qualitative Value</label>
                              <input className="input-field !text-sm !py-1.5" placeholder="e.g. Positive" value={row.value}
                                onChange={(e: any) => {
                                    const u = [...multiResultForm];
                                    u[rIdx].value = e.target.value;
                                    setMultiResultForm(u);
                                }} />
                          </div>

                          <div className="col-span-1 md:col-span-2 flex gap-1">
                              <div className="flex-1">
                                  <label className="md:hidden text-[10px] font-bold text-slate-400 block mb-1">Numeric</label>
                                  <input className="input-field !text-sm !py-1.5" type="number" step="any" placeholder="14.5" value={row.numeric_value}
                                    onChange={(e: any) => {
                                        const u = [...multiResultForm];
                                        u[rIdx].numeric_value = e.target.value;
                                        setMultiResultForm(u);
                                    }} />
                              </div>
                              <div className="w-16">
                                  <label className="md:hidden text-[10px] font-bold text-slate-400 block mb-1">Unit</label>
                                  <input className="input-field !text-sm !py-1.5 !px-1.5 bg-slate-50" placeholder="g/dL" value={row.unit}
                                    onChange={(e: any) => {
                                        const u = [...multiResultForm];
                                        u[rIdx].unit = e.target.value;
                                        setMultiResultForm(u);
                                    }} />
                              </div>
                          </div>

                          <div className="col-span-1 md:col-span-2">
                              <label className="md:hidden text-[10px] font-bold text-slate-400 block mb-1">Reference</label>
                              <input className="input-field !text-sm !py-1.5 bg-slate-50" placeholder="12.0 - 15.0" value={row.reference_range}
                                onChange={(e: any) => {
                                    const u = [...multiResultForm];
                                    u[rIdx].reference_range = e.target.value;
                                    setMultiResultForm(u);
                                }} />
                          </div>

                          <div className="col-span-1 md:col-span-2">
                              <label className="md:hidden text-[10px] font-bold text-slate-400 block mb-1">Notes</label>
                              <input className="input-field !text-sm !py-1.5" placeholder="Remarks..." value={row.notes}
                                onChange={(e: any) => {
                                    const u = [...multiResultForm];
                                    u[rIdx].notes = e.target.value;
                                    setMultiResultForm(u);
                                }} />
                          </div>
                          
                          <div className="col-span-1 md:col-span-1 flex items-center justify-end md:justify-center md:h-full mt-2 md:mt-0">
                              <button onClick={() => {
                                  if(multiResultForm.length > 1) {
                                      setMultiResultForm(multiResultForm.filter((_, i) => i !== rIdx));
                                  }
                              }} disabled={multiResultForm.length === 1} className="p-1.5 text-red-400 hover:bg-red-50 hover:text-red-600 rounded disabled:opacity-30 transition">
                                  <X size={16} />
                              </button>
                          </div>
                      </div>
                  ))}
              </div>
              
              <button onClick={() => setMultiResultForm([...multiResultForm, { id: Date.now(), test_id: "", value: "", numeric_value: "", notes: "", unit: "", reference_range: "" }])} className="btn-secondary btn-sm mt-2 text-xs flex items-center gap-1">
                  <Plus size={14} /> Add Additional Test Result
              </button>
            </div>
            <div className="modal-footer justify-between bg-slate-50/50">
               <span className="text-[10px] text-slate-400">Consolidated Batched Commit</span>
               <div className="flex gap-2">
                  <button onClick={() => setShowResultModal(null)} className="btn-secondary">Cancel</button>
                  <button onClick={handleSubmitResult} className="btn bg-[var(--accent-primary)] text-white hover:bg-indigo-700 shadow flex items-center gap-1.5">
                    <CheckCircle2 size={16} /> Finalize Consolidated Entry
                  </button>
               </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
