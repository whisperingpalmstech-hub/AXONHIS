"use client";
import { useTranslation } from "@/i18n";

import React, { useEffect, useState, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Receipt, DollarSign, CreditCard, ArrowRightLeft, FileText, TrendingUp,
  Search, Eye, AlertTriangle, CheckCircle2, Clock, Wallet, Building2,
  X, ChevronDown, Zap, Shield, Activity, BarChart3
} from "lucide-react";
import { api } from "@/lib/api";

type Tab = "CHARGES" | "LEDGER" | "EVENTS" | "DEPOSITS" | "ESTIMATIONS";

export default function BillingDashboard() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<Tab>("CHARGES");
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [deposits, setDeposits] = useState<any[]>([]);
  const [estimates, setEstimates] = useState<any[]>([]);
  const [preAuths, setPreAuths] = useState<any[]>([]);
  const [creditNotes, setCreditNotes] = useState<any[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [ev, dep, est, pa, cn] = await Promise.all([
        api.get<any[]>("/integration/events").catch(() => []),
        api.get<any[]>("/billing-masters/deposits").catch(() => []),
        api.get<any[]>("/ipd-enhanced/estimates").catch(() => []),
        api.get<any[]>("/ipd-enhanced/pre-auth").catch(() => []),
        api.get<any[]>("/billing-masters/credit-debit-notes").catch(() => []),
      ]);
      setEvents(ev || []); setDeposits(dep || []); setEstimates(est || []);
      setPreAuths(pa || []); setCreditNotes(cn || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const getEventIcon = (type: string) => {
    const map: Record<string, React.ReactNode> = {
      er_to_ipd: <ArrowRightLeft size={14} className="text-blue-500"/>,
      order_to_bill: <Receipt size={14} className="text-emerald-500"/>,
      discharge_settle: <CheckCircle2 size={14} className="text-purple-500"/>,
      charge_posted: <DollarSign size={14} className="text-amber-500"/>,
    };
    return map[type] || <Activity size={14} className="text-slate-400"/>;
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <TopNav title="Billing & Finance" />
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
              <Wallet className="text-emerald-500" size={32}/>{t("billing.billingFinanceHub")}</h1>
            <p className="text-slate-500 font-medium mt-1">Charges • Ledger • Deposits • Pre-Auth • Cross-Module Events</p>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1"><Receipt size={12}/>{t("billing.deposits")}</div>
            <div className="text-3xl font-black text-emerald-600">{deposits.length}</div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1"><FileText size={12}/>{t("billing.estimates")}</div>
            <div className="text-3xl font-black text-blue-600">{estimates.length}</div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-amber-100 shadow-sm">
            <div className="text-[10px] font-bold text-amber-500 uppercase flex items-center gap-1"><Shield size={12}/>{t("billing.preAuth")}</div>
            <div className="text-3xl font-black text-amber-600">{preAuths.length}</div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-purple-100 shadow-sm">
            <div className="text-[10px] font-bold text-purple-500 uppercase flex items-center gap-1"><CreditCard size={12}/>{t("billing.creditNotes")}</div>
            <div className="text-3xl font-black text-purple-600">{creditNotes.length}</div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1"><ArrowRightLeft size={12}/>{t("billing.crossEvents")}</div>
            <div className="text-3xl font-black text-slate-700">{events.length}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1.5 p-1.5 bg-white/50 backdrop-blur border border-slate-200 rounded-2xl w-fit mb-6 shadow-sm">
          {[
            { id: "DEPOSITS", label: "Deposits", icon: <Wallet size={14}/> },
            { id: "ESTIMATIONS", label: "Estimates & Pre-Auth", icon: <FileText size={14}/> },
            { id: "EVENTS", label: "Cross-Module Events", icon: <ArrowRightLeft size={14}/> },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id as Tab)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === t.id ? "bg-white text-emerald-700 shadow-sm border border-slate-200/50" : "text-slate-500 hover:text-slate-700"
              }`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-400 font-medium">{t("billing.loadingFinancialData")}</div>
        ) : (
          <div>
            {/* DEPOSITS */}
            {activeTab === "DEPOSITS" && (
              <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                      <th className="p-4 font-bold">Receipt #</th><th className="p-4 font-bold">{t("billing.patient")}</th>
                      <th className="p-4 font-bold">{t("billing.amount")}</th><th className="p-4 font-bold">{t("billing.utilized")}</th>
                      <th className="p-4 font-bold">{t("billing.balance")}</th><th className="p-4 font-bold">{t("billing.status")}</th>
                      <th className="p-4 font-bold">{t("billing.date")}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {deposits.length === 0 ? (
                      <tr><td colSpan={7} className="p-8 text-center text-slate-400 font-medium">{t("billing.noDepositsRecordedYet")}</td></tr>
                    ) : deposits.map((d: any) => (
                      <tr key={d.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="p-4 font-mono text-xs font-bold text-slate-700">{d.receipt_number || d.id?.slice(0,8)}</td>
                        <td className="p-4 text-sm font-bold text-slate-800">{d.patient_name || '—'}</td>
                        <td className="p-4 text-sm font-bold text-emerald-700">₹{parseFloat(d.amount || 0).toLocaleString()}</td>
                        <td className="p-4 text-sm text-amber-600">₹{parseFloat(d.utilized_amount || 0).toLocaleString()}</td>
                        <td className="p-4 text-sm font-bold text-blue-700">₹{parseFloat(d.balance_amount || 0).toLocaleString()}</td>
                        <td className="p-4"><span className={`text-[10px] font-black uppercase px-2 py-1 rounded-md ${
                          d.status === 'active' ? 'bg-emerald-100 text-emerald-700' :
                          d.status === 'fully_utilized' ? 'bg-slate-100 text-slate-600' :
                          'bg-amber-100 text-amber-700'
                        }`}>{d.status || 'active'}</span></td>
                        <td className="p-4 text-xs text-slate-500">{d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* ESTIMATIONS & PRE-AUTH */}
            {activeTab === "ESTIMATIONS" && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2"><BarChart3 size={16}/>{t("billing.admissionEstimates")}</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {estimates.length === 0 ? (
                      <div className="col-span-2 p-8 text-center text-slate-400 border-2 border-dashed rounded-2xl font-medium">{t("billing.noEstimatesCreatedYet")}</div>
                    ) : estimates.map((e: any) => (
                      <div key={e.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <div className="font-black text-slate-800">{e.patient_name}</div>
                            <div className="text-xs text-slate-500">{e.bed_category || 'General'} • {e.expected_stay_days} days</div>
                          </div>
                          <span className={`text-[10px] font-black px-2 py-0.5 rounded-md ${
                            e.status === 'confirmed' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'
                          }`}>{e.status?.toUpperCase()}</span>
                        </div>
                        <div className="text-2xl font-black text-emerald-700">₹{parseFloat(e.total_estimated_cost || 0).toLocaleString()}</div>
                        <div className="flex gap-4 mt-2 text-xs text-slate-500">
                          <span>Deposit: ₹{parseFloat(e.deposit_required || 0).toLocaleString()}</span>
                          <span>Liability: ₹{parseFloat(e.patient_liability || 0).toLocaleString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2"><Shield size={16}/>{t("billing.insurancePreAuthorizations")}</h3>
                  <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                          <th className="p-4 font-bold">PA #</th><th className="p-4 font-bold">{t("billing.requested")}</th>
                          <th className="p-4 font-bold">{t("billing.approved")}</th><th className="p-4 font-bold">{t("billing.status")}</th>
                          <th className="p-4 font-bold">{t("billing.date")}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {preAuths.length === 0 ? (
                          <tr><td colSpan={5} className="p-8 text-center text-slate-400 font-medium">{t("billing.noPreAuthorizations")}</td></tr>
                        ) : preAuths.map((pa: any) => (
                          <tr key={pa.id} className="hover:bg-slate-50/50">
                            <td className="p-4 font-mono text-xs font-bold">{pa.pre_auth_number || '—'}</td>
                            <td className="p-4 text-sm font-bold text-slate-700">₹{parseFloat(pa.requested_amount || 0).toLocaleString()}</td>
                            <td className="p-4 text-sm font-bold text-emerald-700">{pa.approved_amount ? `₹${parseFloat(pa.approved_amount).toLocaleString()}` : '—'}</td>
                            <td className="p-4"><span className={`text-[10px] font-black uppercase px-2 py-1 rounded-md ${
                              pa.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                              pa.status === 'rejected' ? 'bg-red-100 text-red-700' :
                              'bg-amber-100 text-amber-700'
                            }`}>{pa.status}</span></td>
                            <td className="p-4 text-xs text-slate-500">{pa.requested_at ? new Date(pa.requested_at).toLocaleDateString() : '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* CROSS-MODULE EVENTS */}
            {activeTab === "EVENTS" && (
              <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100">
                  <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider flex items-center gap-2">
                    <ArrowRightLeft size={16}/>{t("billing.crossModuleIntegrationEvents")}</h3>
                  <p className="text-xs text-slate-500 mt-1">Audit trail: ER → IPD, Order → Bill, Discharge → Settlement</p>
                </div>
                <div className="divide-y divide-slate-100">
                  {events.length === 0 ? (
                    <div className="p-12 text-center text-slate-400">
                      <ArrowRightLeft size={32} className="mx-auto mb-2 opacity-50"/>
                      <p className="font-medium">No cross-module events yet. Events are logged when:</p>
                      <ul className="text-xs mt-2 space-y-1">
                        <li>• ER patient is transferred to IPD</li>
                        <li>• Clinical orders generate billing charges</li>
                        <li>• Discharge settlement completes</li>
                      </ul>
                    </div>
                  ) : events.map((ev: any) => (
                    <div key={ev.id} className="p-4 flex items-center gap-4 hover:bg-slate-50/50 transition-colors">
                      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                        {getEventIcon(ev.event_type)}
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-bold text-slate-800">{ev.event_type?.replace(/_/g, ' ')?.toUpperCase()}</div>
                        <div className="text-xs text-slate-500">{ev.source_module} → {ev.target_module}</div>
                      </div>
                      <span className={`text-[10px] font-black uppercase px-2 py-1 rounded-md ${
                        ev.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                        ev.status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-amber-100 text-amber-700'
                      }`}>{ev.status}</span>
                      <div className="text-xs text-slate-400">{new Date(ev.triggered_at).toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Module Connectivity Diagram */}
        <div className="mt-8 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider mb-4">{t("billing.moduleConnectivityMap")}</h3>
          <div className="grid grid-cols-5 gap-4">
            {[
              { name: "ER", color: "red", icon: <Zap size={20}/>, connections: ["Billing", "IPD"] },
              { name: "OPD", color: "blue", icon: <Activity size={20}/>, connections: ["Billing", "Lab", "Pharmacy"] },
              { name: "IPD", color: "indigo", icon: <Building2 size={20}/>, connections: ["Billing", "Lab", "Pharmacy", "ER"] },
              { name: "Lab/Rad", color: "purple", icon: <BarChart3 size={20}/>, connections: ["Billing", "OPD", "IPD"] },
              { name: "Pharmacy", color: "emerald", icon: <Receipt size={20}/>, connections: ["Billing", "OPD", "IPD"] },
            ].map(m => (
              <div key={m.name} className={`p-4 rounded-xl border-2 border-${m.color}-200 bg-${m.color}-50 text-center`}>
                <div className={`text-${m.color}-600 mx-auto w-fit mb-2`}>{m.icon}</div>
                <div className={`font-black text-${m.color}-800 text-sm mb-1`}>{m.name}</div>
                <div className="flex flex-wrap justify-center gap-1">
                  {m.connections.map(c => (
                    <span key={c} className={`text-[8px] font-bold bg-white text-${m.color}-600 px-1.5 py-0.5 rounded`}>→ {c}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
