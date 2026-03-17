"use client";
import React, { useState, useEffect } from "react";
import {
  Receipt, DollarSign, FileText, CheckCircle2, Clock, AlertCircle,
  Plus, X, TrendingUp, ShieldCheck, CreditCard, Search, Eye,
  Building2, ArrowRight, Loader2, BarChart3, Wallet, BadgeDollarSign,
  Activity, Users, Stethoscope, ChevronDown
} from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

type TabKey = "overview" | "invoices" | "payments" | "claims" | "services";

export default function BillingDashboard() {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [loading, setLoading] = useState(true);

  // Data states
  const [invoices, setInvoices] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [claims, setClaims] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [encounters, setEncounters] = useState<any[]>([]);
  const [providers, setProviders] = useState<any[]>([]);
  const [billingServices, setBillingServices] = useState<any[]>([]);
  const [entries, setEntries] = useState<any[]>([]);

  // Modal states
  const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [showInvoiceDetail, setShowInvoiceDetail] = useState<any>(null);

  // Form states
  const [invoiceForm, setInvoiceForm] = useState({ patient_id: "", encounter_id: "" });
  const [paymentForm, setPaymentForm] = useState({ invoice_id: "", payment_method: "cash", amount: "" });
  const [claimForm, setClaimForm] = useState({ invoice_id: "", provider_id: "", claim_amount: "" });

  // Search
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    const headers = authHeaders();
    try {
      const [invRes, payRes, claimRes, patRes, encRes, provRes, svcRes, entRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/billing/invoices`, { headers }),
        fetch(`${API_URL}/api/v1/billing/payments`, { headers }),
        fetch(`${API_URL}/api/v1/billing/insurance/claims`, { headers }),
        fetch(`${API_URL}/api/v1/patients`, { headers }),
        fetch(`${API_URL}/api/v1/encounters`, { headers }),
        fetch(`${API_URL}/api/v1/billing/insurance/providers`, { headers }),
        fetch(`${API_URL}/api/v1/billing/services`, { headers }),
        fetch(`${API_URL}/api/v1/billing/entries`, { headers }),
      ]);
      if (invRes.ok) setInvoices(await invRes.json());
      if (payRes.ok) setPayments(await payRes.json());
      if (claimRes.ok) setClaims(await claimRes.json());
      if (patRes.ok) {
        const pData = await patRes.json();
        // Handle both list and {items: [...]} format
        setPatients(Array.isArray(pData) ? pData : (pData.items || []));
      }
      if (encRes.ok) setEncounters(await encRes.json());
      if (provRes.ok) setProviders(await provRes.json());
      if (svcRes.ok) setBillingServices(await svcRes.json());
      if (entRes.ok) setEntries(await entRes.json());
    } catch (err) {
      console.error("Failed to load billing data:", err);
    } finally {
      setLoading(false);
    }
  };

  // Helpers
  const getPatientName = (pid: string) => {
    const p = patients.find((pt: any) => pt.id === pid);
    if (!p) return pid?.substring(0, 8) + "...";
    return `${p.first_name} ${p.last_name}`;
  };
  const getPatientMRN = (pid: string) => {
    const p = patients.find((pt: any) => pt.id === pid);
    return p?.patient_uuid || p?.mrn || "—";
  };

  // KPI metrics
  const totalRevenue = payments.reduce((acc: number, p: any) => acc + parseFloat(p.amount || 0), 0);
  const pendingAmount = invoices.filter((i: any) => i.status === "issued").reduce((acc: number, i: any) => acc + parseFloat(i.total_amount || 0), 0);
  const paidInvoices = invoices.filter((i: any) => i.status === "paid").length;
  const activeClaims = claims.filter((c: any) => c.status !== "approved" && c.status !== "rejected").length;

  // Filtered encounters for selected patient
  const patientEncounters = encounters.filter((e: any) => e.patient_id === invoiceForm.patient_id);

  // Invoice entries lookup
  const getInvoiceEntries = (invId: string) => entries.filter((e: any) => e.encounter_id === showInvoiceDetail?.encounter_id && e.patient_id === showInvoiceDetail?.patient_id);

  // Invoice search
  const filteredInvoices = invoices.filter((i: any) => {
    if (!searchTerm) return true;
    const pName = getPatientName(i.patient_id).toLowerCase();
    return pName.includes(searchTerm.toLowerCase()) || i.invoice_number?.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const handleCreateInvoice = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/billing/invoice`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(invoiceForm)
      });
      if (res.ok) {
        setShowInvoiceModal(false);
        setInvoiceForm({ patient_id: "", encounter_id: "" });
        fetchData();
      } else {
        const err = await res.json();
        alert(err.detail ? JSON.stringify(err.detail) : "Error generating invoice");
      }
    } catch (e: any) { alert(e.message); }
  };

  const handleRecordPayment = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/billing/payment`, {
        method: "POST", headers: authHeaders(),
        body: JSON.stringify({ ...paymentForm, amount: parseFloat(paymentForm.amount) })
      });
      if (res.ok) {
        setShowPaymentModal(false);
        setPaymentForm({ invoice_id: "", payment_method: "cash", amount: "" });
        fetchData();
      } else {
        const err = await res.json();
        alert(err.detail ? JSON.stringify(err.detail) : "Error recording payment");
      }
    } catch (e: any) { alert(e.message); }
  };

  const handleSubmitClaim = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/billing/insurance/claim`, {
        method: "POST", headers: authHeaders(),
        body: JSON.stringify({ ...claimForm, claim_amount: parseFloat(claimForm.claim_amount) })
      });
      if (res.ok) {
        setShowClaimModal(false);
        setClaimForm({ invoice_id: "", provider_id: "", claim_amount: "" });
        fetchData();
      } else {
        const err = await res.json();
        alert(err.detail ? JSON.stringify(err.detail) : "Error submitting claim");
      }
    } catch (e: any) { alert(e.message); }
  };

  const TABS: { key: TabKey; label: string; icon: any; count?: number }[] = [
    { key: "overview", label: "Dashboard", icon: BarChart3 },
    { key: "invoices", label: "Invoices", icon: Receipt, count: invoices.length },
    { key: "payments", label: "Payments", icon: Wallet, count: payments.length },
    { key: "claims", label: "Insurance Claims", icon: ShieldCheck, count: claims.length },
    { key: "services", label: "Service Catalog", icon: Stethoscope, count: billingServices.length },
  ];

  return (
    <div className="flex flex-col h-full">
      <TopNav title="Billing & Revenue Cycle Management" />

      <div className="p-6 space-y-6">
        {/* Tab Navigation */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button key={tab.key}
                onClick={() => { setActiveTab(tab.key); setSearchTerm(""); }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
                  isActive
                    ? "bg-white text-[var(--accent-primary)] shadow-sm border border-[var(--border)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-slate-50"
                }`}>
                <Icon size={16} />
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="text-[10px] font-bold rounded-full px-1.5 py-0.5 min-w-[18px] text-center bg-slate-200 text-slate-600">{tab.count}</span>
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
            {activeTab === "overview" && (
              <div className="space-y-6">
                {/* KPI Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                  {[
                    { label: "Total Invoices", value: invoices.length, icon: Receipt, cBg: "bg-blue-50", cIcon: "text-blue-600", cBorder: "border-blue-100" },
                    { label: "Revenue Collected", value: `$${totalRevenue.toFixed(2)}`, icon: TrendingUp, cBg: "bg-emerald-50", cIcon: "text-emerald-600", cBorder: "border-emerald-100" },
                    { label: "Pending Dues", value: `$${pendingAmount.toFixed(2)}`, icon: Clock, cBg: "bg-amber-50", cIcon: "text-amber-600", cBorder: "border-amber-100" },
                    { label: "Paid Invoices", value: paidInvoices, icon: CheckCircle2, cBg: "bg-green-50", cIcon: "text-green-600", cBorder: "border-green-100" },
                    { label: "Active Claims", value: activeClaims, icon: ShieldCheck, cBg: "bg-violet-50", cIcon: "text-violet-600", cBorder: "border-violet-100" },
                    { label: "Patients Billed", value: new Set(invoices.map((i: any) => i.patient_id)).size, icon: Users, cBg: "bg-rose-50", cIcon: "text-rose-600", cBorder: "border-rose-100" },
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

                {/* Quick Actions + Recent */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Quick Actions */}
                  <div className="card">
                    <div className="card-header"><h3 className="font-semibold text-sm">Quick Actions</h3></div>
                    <div className="divide-y divide-[var(--border)]">
                      {[
                        { label: "Generate Invoice", desc: "Create invoice from encounter", icon: Receipt, color: "text-blue-600", bg: "bg-blue-50", action: () => { setShowInvoiceModal(true); setActiveTab("invoices"); } },
                        { label: "Record Payment", desc: "Log a payment against an invoice", icon: DollarSign, color: "text-emerald-600", bg: "bg-emerald-50", action: () => { setShowPaymentModal(true); setActiveTab("payments"); } },
                        { label: "Submit Claim", desc: "File an insurance claim", icon: ShieldCheck, color: "text-violet-600", bg: "bg-violet-50", action: () => { setShowClaimModal(true); setActiveTab("claims"); } },
                      ].map((a, i) => {
                        const Icon = a.icon;
                        return (
                          <button key={i} onClick={a.action}
                            className="w-full flex items-center gap-3 px-5 py-3.5 hover:bg-slate-50 transition-colors text-left">
                            <div className={`w-9 h-9 rounded-lg ${a.bg} flex items-center justify-center`}>
                              <Icon size={18} className={a.color} />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-[var(--text-primary)]">{a.label}</p>
                              <p className="text-xs text-[var(--text-secondary)]">{a.desc}</p>
                            </div>
                            <ArrowRight size={14} className="text-slate-400" />
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Recent Invoices */}
                  <div className="lg:col-span-2 card">
                    <div className="card-header">
                      <h3 className="font-semibold text-sm">Recent Invoices</h3>
                      <button onClick={() => setActiveTab("invoices")} className="text-xs text-[var(--accent-primary)] hover:underline">
                        View all &rarr;
                      </button>
                    </div>
                    {invoices.length > 0 ? (
                      <div className="divide-y divide-[var(--border)]">
                        {invoices.slice(0, 5).map((inv: any) => (
                          <div key={inv.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-slate-50 transition-colors">
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
                                <Receipt size={18} className="text-blue-600" />
                              </div>
                              <div>
                                <p className="text-sm font-semibold text-[var(--text-primary)]">{inv.invoice_number}</p>
                                <p className="text-xs text-[var(--text-secondary)]">{getPatientName(inv.patient_id)}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-bold">${parseFloat(inv.total_amount).toFixed(2)}</p>
                              <span className={`badge text-[10px] ${inv.status === 'paid' ? 'badge-success' : inv.status === 'issued' ? 'badge-warning' : 'badge-neutral'}`}>
                                {inv.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="card-body text-center text-[var(--text-secondary)]">
                        <Receipt size={36} className="mx-auto mb-2 opacity-30" />
                        <p className="text-sm">No invoices yet. Generate one from an encounter.</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ═══ INVOICES TAB ═══ */}
            {activeTab === "invoices" && (
              <div className="space-y-5">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="relative flex-1 max-w-sm">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                    <input value={searchTerm} onChange={(e: any) => setSearchTerm(e.target.value)}
                      placeholder="Search invoices by patient or number…" className="input-field pl-9" />
                  </div>
                  <button onClick={() => setShowInvoiceModal(true)} className="btn-primary">
                    <Plus size={16} /> Generate Invoice
                  </button>
                </div>

                {filteredInvoices.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filteredInvoices.map((inv: any) => (
                      <div key={inv.id} className="card card-body !p-5 hover:shadow-md transition-shadow flex flex-col justify-between">
                        <div>
                          <div className="flex items-start justify-between mb-4">
                            <div>
                              <code className="text-xs font-bold text-[var(--accent-primary)] bg-[var(--accent-primary-light)] px-2 py-1 rounded inline-block mb-2">
                                {inv.invoice_number}
                              </code>
                              <p className="text-base font-semibold text-[var(--text-primary)]">{getPatientName(inv.patient_id)}</p>
                              <p className="text-xs text-[var(--text-secondary)]">MRN: {getPatientMRN(inv.patient_id)}</p>
                            </div>
                            <span className={`badge ${inv.status === 'paid' ? 'badge-success' : inv.status === 'issued' ? 'badge-warning' : inv.status === 'cancelled' ? 'badge-error' : 'badge-neutral'}`}>
                              {inv.status}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 gap-x-4 gap-y-3 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs mb-4">
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Total Amount</span>
                              <span className="font-bold text-lg text-[var(--text-primary)]">${parseFloat(inv.total_amount).toFixed(2)}</span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Generated</span>
                              <span className="font-medium text-slate-700">{new Date(inv.generated_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>

                        <button onClick={() => setShowInvoiceDetail(inv)}
                          className="btn-secondary btn-sm w-full flex items-center justify-center gap-2">
                          <Eye size={14} /> View Details
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <Receipt size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">No invoices found. Generate one by selecting a patient and encounter.</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ PAYMENTS TAB ═══ */}
            {activeTab === "payments" && (
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold flex items-center gap-2"><Wallet size={18} className="text-emerald-600" /> Payment History</h3>
                  <button onClick={() => setShowPaymentModal(true)} className="btn-primary">
                    <DollarSign size={16} /> Record Payment
                  </button>
                </div>

                {payments.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {payments.map((p: any) => {
                      const inv = invoices.find((i: any) => i.id === p.invoice_id);
                      return (
                        <div key={p.id} className="card card-body !p-5 hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${p.payment_status === 'completed' ? 'bg-emerald-50' : 'bg-amber-50'}`}>
                                <CreditCard size={20} className={p.payment_status === 'completed' ? 'text-emerald-600' : 'text-amber-600'} />
                              </div>
                              <div>
                                <p className="text-lg font-bold text-[var(--text-primary)]">${parseFloat(p.amount).toFixed(2)}</p>
                                <p className="text-xs text-[var(--text-secondary)] capitalize">{p.payment_method}</p>
                              </div>
                            </div>
                            <span className={`badge ${p.payment_status === 'completed' ? 'badge-success' : p.payment_status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                              {p.payment_status}
                            </span>
                          </div>
                          <div className="space-y-2 text-xs">
                            <div className="flex justify-between">
                              <span className="text-slate-500">Invoice</span>
                              <span className="font-medium text-[var(--accent-primary)]">{inv?.invoice_number || "—"}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Patient</span>
                              <span className="font-medium">{inv ? getPatientName(inv.patient_id) : "—"}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Time</span>
                              <span className="font-medium">{new Date(p.payment_time).toLocaleString()}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <DollarSign size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">No payments recorded yet.</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ CLAIMS TAB ═══ */}
            {activeTab === "claims" && (
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold flex items-center gap-2"><ShieldCheck size={18} className="text-violet-600" /> Insurance Claims</h3>
                  <button onClick={() => setShowClaimModal(true)} className="btn-primary">
                    <FileText size={16} /> Submit Claim
                  </button>
                </div>

                {claims.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {claims.map((c: any) => {
                      const inv = invoices.find((i: any) => i.id === c.invoice_id);
                      const prov = providers.find((pr: any) => pr.id === c.provider_id);
                      return (
                        <div key={c.id} className="card card-body !p-5 hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${c.status === 'approved' ? 'bg-emerald-50' : c.status === 'rejected' ? 'bg-red-50' : 'bg-violet-50'}`}>
                                <Building2 size={20} className={c.status === 'approved' ? 'text-emerald-600' : c.status === 'rejected' ? 'text-red-600' : 'text-violet-600'} />
                              </div>
                              <div>
                                <p className="text-lg font-bold text-[var(--text-primary)]">${parseFloat(c.claim_amount).toFixed(2)}</p>
                                <p className="text-xs text-[var(--text-secondary)]">{prov?.provider_name || "Unknown Provider"}</p>
                              </div>
                            </div>
                            <span className={`badge ${c.status === 'approved' ? 'badge-success' : c.status === 'rejected' ? 'badge-error' : 'badge-warning'}`}>
                              {c.status}
                            </span>
                          </div>
                          <div className="space-y-2 text-xs">
                            <div className="flex justify-between">
                              <span className="text-slate-500">Invoice</span>
                              <span className="font-medium text-[var(--accent-primary)]">{inv?.invoice_number || "—"}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Submitted</span>
                              <span className="font-medium">{new Date(c.submitted_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <ShieldCheck size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">No insurance claims filed yet.</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ SERVICE CATALOG TAB ═══ */}
            {activeTab === "services" && (
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold flex items-center gap-2"><Stethoscope size={18} className="text-blue-600" /> Service Catalog ({billingServices.length})</h3>
                </div>
                {billingServices.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {billingServices.map((svc: any) => (
                      <div key={svc.id} className="card card-body !p-5 hover:shadow-md transition-shadow">
                        <div className="flex items-start gap-3 mb-3">
                          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center flex-shrink-0">
                            <Stethoscope size={20} className="text-blue-600" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-base font-semibold text-[var(--text-primary)] truncate">{svc.service_name}</p>
                            <code className="text-xs font-bold text-[var(--accent-primary)] bg-[var(--accent-primary-light)] px-1.5 py-0.5 rounded border border-blue-200">
                              {svc.service_code}
                            </code>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2 p-2 bg-slate-50 rounded-lg text-xs">
                          <div><span className="text-[10px] uppercase font-semibold text-slate-400">Category</span><br/><span className="font-medium capitalize">{svc.service_category || "—"}</span></div>
                          <div><span className="text-[10px] uppercase font-semibold text-slate-400">Department</span><br/><span className="font-medium capitalize">{svc.department || "—"}</span></div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card card-body text-center py-16">
                    <Stethoscope size={40} className="mx-auto mb-3 text-slate-300" />
                    <p className="text-[var(--text-secondary)]">No billing services configured.</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* ═══ GENERATE INVOICE MODAL ═══ */}
      {showInvoiceModal && (
        <div className="modal-overlay" onClick={() => setShowInvoiceModal(false)}>
          <div className="modal-content" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2"><Receipt size={18} className="text-[var(--accent-primary)]" /> Generate Invoice</h3>
              <button onClick={() => setShowInvoiceModal(false)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="input-label">Select Patient <span className="text-red-500">*</span></label>
                <select className="input-field" value={invoiceForm.patient_id}
                  onChange={(e: any) => setInvoiceForm({ patient_id: e.target.value, encounter_id: "" })}>
                  <option value="">-- Choose Patient ({patients.length} available) --</option>
                  {patients.map((p: any) => (
                    <option key={p.id} value={p.id}>
                      {p.first_name} {p.last_name} — {p.patient_uuid || p.mrn || "No MRN"}
                    </option>
                  ))}
                </select>
                {patients.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1 flex items-center gap-1"><AlertCircle size={12}/> No patients found. Register patients first.</p>
                )}
              </div>
              <div>
                <label className="input-label">Select Encounter <span className="text-red-500">*</span></label>
                <select className="input-field" value={invoiceForm.encounter_id}
                  onChange={(e: any) => setInvoiceForm((prev: any) => ({ ...prev, encounter_id: e.target.value }))}
                  disabled={!invoiceForm.patient_id}>
                  <option value="">-- Choose Encounter ({patientEncounters.length} for this patient) --</option>
                  {patientEncounters.map((enc: any) => (
                    <option key={enc.id} value={enc.id}>
                      {enc.encounter_type} — {enc.department || "General"} — {new Date(enc.start_time || enc.created_at).toLocaleDateString()} ({enc.status})
                    </option>
                  ))}
                </select>
                {invoiceForm.patient_id && patientEncounters.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1 flex items-center gap-1"><AlertCircle size={12}/> No encounters found for this patient.</p>
                )}
              </div>
              {invoiceForm.patient_id && invoiceForm.encounter_id && (
                <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                  <p className="text-xs text-emerald-700 font-medium flex items-center gap-1"><CheckCircle2 size={14}/> Ready to generate invoice. The system will consolidate all pending billing entries for this encounter.</p>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowInvoiceModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleCreateInvoice} className="btn-primary" disabled={!invoiceForm.patient_id || !invoiceForm.encounter_id}>
                <Receipt size={16} /> Generate Invoice
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ RECORD PAYMENT MODAL ═══ */}
      {showPaymentModal && (
        <div className="modal-overlay" onClick={() => setShowPaymentModal(false)}>
          <div className="modal-content" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2"><DollarSign size={18} className="text-emerald-600" /> Record Payment</h3>
              <button onClick={() => setShowPaymentModal(false)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="input-label">Select Invoice <span className="text-red-500">*</span></label>
                <select className="input-field" value={paymentForm.invoice_id}
                  onChange={(e: any) => {
                    const inv = invoices.find((i: any) => i.id === e.target.value);
                    setPaymentForm((prev: any) => ({
                      ...prev,
                      invoice_id: e.target.value,
                      amount: inv ? parseFloat(inv.total_amount).toFixed(2) : ""
                    }));
                  }}>
                  <option value="">-- Choose Invoice --</option>
                  {invoices.filter((i: any) => i.status !== 'paid').map((inv: any) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.invoice_number} — {getPatientName(inv.patient_id)} — ${parseFloat(inv.total_amount).toFixed(2)} ({inv.status})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="input-label">Payment Method <span className="text-red-500">*</span></label>
                <select className="input-field" value={paymentForm.payment_method}
                  onChange={(e: any) => setPaymentForm((prev: any) => ({ ...prev, payment_method: e.target.value }))}>
                  <option value="cash">💵 Cash</option>
                  <option value="card">💳 Card</option>
                  <option value="online">🌐 Online</option>
                  <option value="insurance">🏥 Insurance</option>
                </select>
              </div>
              <div>
                <label className="input-label">Amount <span className="text-red-500">*</span></label>
                <input className="input-field" type="number" step="0.01" placeholder="0.00" value={paymentForm.amount}
                  onChange={(e: any) => setPaymentForm((prev: any) => ({ ...prev, amount: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowPaymentModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleRecordPayment} className="btn bg-[var(--success)] text-white hover:bg-green-700 focus:ring-green-400">
                <CheckCircle2 size={16} /> Confirm Payment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ SUBMIT CLAIM MODAL ═══ */}
      {showClaimModal && (
        <div className="modal-overlay" onClick={() => setShowClaimModal(false)}>
          <div className="modal-content" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2"><ShieldCheck size={18} className="text-violet-600" /> Submit Insurance Claim</h3>
              <button onClick={() => setShowClaimModal(false)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="input-label">Select Invoice <span className="text-red-500">*</span></label>
                <select className="input-field" value={claimForm.invoice_id}
                  onChange={(e: any) => {
                    const inv = invoices.find((i: any) => i.id === e.target.value);
                    setClaimForm((prev: any) => ({
                      ...prev,
                      invoice_id: e.target.value,
                      claim_amount: inv ? parseFloat(inv.total_amount).toFixed(2) : ""
                    }));
                  }}>
                  <option value="">-- Choose Invoice --</option>
                  {invoices.map((inv: any) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.invoice_number} — {getPatientName(inv.patient_id)} — ${parseFloat(inv.total_amount).toFixed(2)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="input-label">Insurance Provider <span className="text-red-500">*</span></label>
                <select className="input-field" value={claimForm.provider_id}
                  onChange={(e: any) => setClaimForm((prev: any) => ({ ...prev, provider_id: e.target.value }))}>
                  <option value="">-- Choose Provider ({providers.length} registered) --</option>
                  {providers.map((prov: any) => (
                    <option key={prov.id} value={prov.id}>{prov.provider_name}</option>
                  ))}
                </select>
                {providers.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1 flex items-center gap-1"><AlertCircle size={12}/> No insurance providers registered.</p>
                )}
              </div>
              <div>
                <label className="input-label">Claim Amount <span className="text-red-500">*</span></label>
                <input className="input-field" type="number" step="0.01" placeholder="0.00" value={claimForm.claim_amount}
                  onChange={(e: any) => setClaimForm((prev: any) => ({ ...prev, claim_amount: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowClaimModal(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleSubmitClaim} className="btn bg-violet-600 text-white hover:bg-violet-700">
                <FileText size={16} /> Submit Claim
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ INVOICE DETAIL MODAL ═══ */}
      {showInvoiceDetail && (
        <div className="modal-overlay" onClick={() => setShowInvoiceDetail(null)}>
          <div className="modal-content !max-w-2xl" onClick={(e: any) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold flex items-center gap-2">
                <Receipt size={18} className="text-[var(--accent-primary)]" />
                Invoice: {showInvoiceDetail.invoice_number}
              </h3>
              <button onClick={() => setShowInvoiceDetail(null)} className="btn-ghost p-1 rounded"><X size={18} /></button>
            </div>
            <div className="modal-body space-y-5">
              {/* Patient Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                  <p className="text-[10px] uppercase font-semibold text-slate-400 mb-1">Patient</p>
                  <p className="text-sm font-bold text-[var(--text-primary)]">{getPatientName(showInvoiceDetail.patient_id)}</p>
                  <p className="text-xs text-[var(--text-secondary)]">MRN: {getPatientMRN(showInvoiceDetail.patient_id)}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                  <p className="text-[10px] uppercase font-semibold text-slate-400 mb-1">Invoice Details</p>
                  <p className="text-sm font-bold text-[var(--text-primary)]">{showInvoiceDetail.invoice_number}</p>
                  <p className="text-xs text-[var(--text-secondary)]">Generated: {new Date(showInvoiceDetail.generated_at).toLocaleString()}</p>
                </div>
              </div>

              {/* Billing Entries */}
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2"><Activity size={14} className="text-blue-500"/>Services Billed</h4>
                {(() => {
                  const invEntries = entries.filter((e: any) => e.encounter_id === showInvoiceDetail.encounter_id && e.patient_id === showInvoiceDetail.patient_id);
                  return invEntries.length > 0 ? (
                    <table className="data-table">
                      <thead><tr><th>Service</th><th>Qty</th><th>Unit Price</th><th>Total</th><th>Status</th></tr></thead>
                      <tbody>
                        {invEntries.map((entry: any) => {
                          const svc = billingServices.find((s: any) => s.id === entry.service_id);
                          return (
                            <tr key={entry.id}>
                              <td className="font-medium">{svc?.service_name || entry.service_id?.substring(0, 8)}</td>
                              <td>{entry.quantity}</td>
                              <td>${parseFloat(entry.unit_price).toFixed(2)}</td>
                              <td className="font-semibold">${parseFloat(entry.total_price).toFixed(2)}</td>
                              <td><span className={`badge ${entry.status === 'charged' ? 'badge-success' : 'badge-neutral'}`}>{entry.status}</span></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  ) : (
                    <p className="text-xs text-slate-500 p-3 bg-slate-50 rounded-lg">No billing entries found for this encounter.</p>
                  );
                })()}
              </div>

              {/* Total Summary */}
              <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-slate-600">Total Payable</span>
                  <span className="text-2xl font-bold text-[var(--accent-primary)]">${parseFloat(showInvoiceDetail.total_amount).toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-slate-500">Status</span>
                  <span className={`badge ${showInvoiceDetail.status === 'paid' ? 'badge-success' : showInvoiceDetail.status === 'issued' ? 'badge-warning' : 'badge-neutral'}`}>
                    {showInvoiceDetail.status}
                  </span>
                </div>
              </div>

              {/* Payments made against this invoice */}
              {(() => {
                const invPayments = payments.filter((p: any) => p.invoice_id === showInvoiceDetail.id);
                return invPayments.length > 0 ? (
                  <div>
                    <h4 className="text-sm font-semibold mb-2 flex items-center gap-2"><CreditCard size={14} className="text-emerald-500"/>Payments Received</h4>
                    <div className="space-y-2">
                      {invPayments.map((p: any) => (
                        <div key={p.id} className="flex items-center justify-between p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                          <div>
                            <p className="text-sm font-semibold text-emerald-700">${parseFloat(p.amount).toFixed(2)}</p>
                            <p className="text-xs text-emerald-600 capitalize">{p.payment_method} • {new Date(p.payment_time).toLocaleString()}</p>
                          </div>
                          <span className={`badge ${p.payment_status === 'completed' ? 'badge-success' : 'badge-warning'}`}>{p.payment_status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null;
              })()}
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowInvoiceDetail(null)} className="btn-secondary">Close</button>
              {showInvoiceDetail.status !== 'paid' && (
                <button onClick={() => {
                  setPaymentForm({ invoice_id: showInvoiceDetail.id, payment_method: "cash", amount: parseFloat(showInvoiceDetail.total_amount).toFixed(2) });
                  setShowInvoiceDetail(null);
                  setShowPaymentModal(true);
                }} className="btn bg-[var(--success)] text-white hover:bg-green-700">
                  <DollarSign size={16} /> Record Payment
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
