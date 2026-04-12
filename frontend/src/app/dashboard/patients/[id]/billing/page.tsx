"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Receipt, DollarSign, FileText, ArrowLeft, Activity, ShieldCheck, AlertCircle, TrendingUp, CreditCard } from "lucide-react";
import Link from "next/link";
import { TopNav } from "@/components/ui/TopNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export default function PatientBillingPage() {
  const { t } = useTranslation();
  const params = useParams();
  const id = params.id as string;
  const [patient, setPatient] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [entries, setEntries] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    setLoading(true);
    const headers = authHeaders();
    try {
      const pRes = await fetch(`${API_URL}/api/v1/patients/${id}`, { headers });
      if (pRes.ok) setPatient(await pRes.json());

      const [invRes, payRes, entRes, svcRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/billing/invoices`, { headers }),
        fetch(`${API_URL}/api/v1/billing/payments`, { headers }),
        fetch(`${API_URL}/api/v1/billing/entries/patient/${id}`, { headers }),
        fetch(`${API_URL}/api/v1/billing/services`, { headers }),
      ]);

      if (invRes.ok) {
        const _invoices = await invRes.json();
        setInvoices(_invoices.filter((i: any) => i.patient_id === id));
      }
      if (payRes.ok) setPayments(await payRes.json());
      if (entRes.ok) setEntries(await entRes.json());
      if (svcRes.ok) setServices(await svcRes.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="flex flex-col h-full bg-slate-50/50">
      <TopNav title={`Loading Patient Billing...`} />
      <div className="flex-1 flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--accent-primary)]"></div></div>
    </div>
  );
  
  if (!patient) return (
    <div className="flex flex-col h-full bg-slate-50/50">
      <TopNav title={`Patient Not Found`} />
      <div className="p-8 text-center text-rose-500">The requested patient could not be found or you lack permission.</div>
    </div>
  );

  const totalBilled = invoices.reduce((sum, inv) => sum + parseFloat(inv.total_amount), 0);
  const patientInvoicesIds = new Set(invoices.map((i: any) => i.id));
  const patientPayments = payments.filter((p: any) => patientInvoicesIds.has(p.invoice_id));
  const totalPaid = patientPayments.reduce((sum, p: any) => sum + parseFloat(p.amount), 0);
  const balanceDue = Math.max(0, totalBilled - totalPaid);
  const insuranceCoverage = 0.00; // Phase 7 Insurance link

  return (
    <div className="flex flex-col h-full bg-slate-50/50">
      <TopNav title={`Billing Summary: ${patient.first_name} ${patient.last_name}`} />
      
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        <div className="flex items-center justify-between">
          <Link href={`/dashboard/patients/${id}`} className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-[var(--accent-primary)] transition-colors bg-white px-3 py-1.5 rounded-lg border border-slate-200 hover:border-[var(--accent-primary-light)]">
            <ArrowLeft size={16} className="mr-2" /> Back to Patient Profile
          </Link>
          <div className="text-xs bg-slate-200 text-slate-600 px-3 py-1 rounded-full font-bold">
            MRN: {patient.patient_uuid || patient.mrn || "N/A"}
          </div>
        </div>
        
        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card card-body flex flex-row items-center gap-4 !p-5 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 border border-blue-100"><Receipt size={24} /></div>
            <div>
              <p className="text-sm text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[10px]">Total Billed</p>
              <h3 className="text-2xl font-bold text-[var(--text-primary)]">${totalBilled.toFixed(2)}</h3>
            </div>
          </div>
          <div className="card card-body flex flex-row items-center gap-4 !p-5 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 border border-emerald-100"><ShieldCheck size={24} /></div>
            <div>
              <p className="text-sm text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[10px]">Insurance Covered</p>
              <h3 className="text-2xl font-bold text-[var(--text-primary)]">${insuranceCoverage.toFixed(2)}</h3>
            </div>
          </div>
          <div className="card card-body flex flex-row items-center gap-4 !p-5 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-green-50 flex items-center justify-center text-green-600 border border-green-100"><TrendingUp size={24} /></div>
            <div>
              <p className="text-sm text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[10px]">Payments Made</p>
              <h3 className="text-2xl font-bold text-[var(--text-primary)]">${totalPaid.toFixed(2)}</h3>
            </div>
          </div>
          <div className={`card card-body flex flex-row items-center gap-4 !p-5 transition-shadow shadow-sm ${balanceDue > 0 ? "border-rose-200 bg-rose-50" : "border-slate-200"}`}>
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${balanceDue > 0 ? "bg-rose-100 text-rose-600" : "bg-slate-100 text-slate-400"} border ${balanceDue > 0 ? "border-rose-200" : "border-slate-200"}`}><AlertCircle size={24} /></div>
            <div>
              <p className={`text-sm font-semibold mb-0.5 uppercase tracking-wider text-[10px] ${balanceDue > 0 ? "text-rose-600" : "text-slate-500"}`}>Balance Due</p>
              <h3 className={`text-2xl font-bold ${balanceDue > 0 ? "text-rose-600" : "text-[var(--text-primary)]"}`}>${balanceDue.toFixed(2)}</h3>
            </div>
          </div>
        </div>

        {/* Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card overflow-hidden flex flex-col h-full">
            <div className="card-header border-b border-slate-100 bg-white">
              <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2"><Activity size={18} className="text-blue-500" /> Services Charged</h2>
            </div>
            <div className="flex-1 overflow-auto bg-white">
              {entries.length > 0 ? (
                <table className="data-table w-full">
                  <thead className="bg-slate-50 sticky top-0"><tr><th>Date</th><th>Service</th><th>Qty</th><th>Total</th><th>Status</th></tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {entries.map((e: any) => {
                      const svcName = services.find((s: any) => s.id === e.service_id)?.service_name || e.service_id?.substring(0,8);
                      return (
                        <tr key={e.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="text-xs text-slate-500">{new Date(e.created_at).toLocaleDateString()}</td>
                          <td className="text-sm font-medium text-[var(--text-primary)]">{svcName}</td>
                          <td className="text-xs text-slate-600">{e.quantity}</td>
                          <td className="font-semibold text-slate-800">${parseFloat(e.total_price).toFixed(2)}</td>
                          <td><span className={`badge ${e.status === 'charged' ? 'badge-success' : 'badge-neutral'}`}>{e.status}</span></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : <div className="p-12 flex flex-col items-center justify-center text-center text-slate-500"><Activity size={32} className="mb-3 text-slate-300"/><p>No billing entries found.</p></div>}
            </div>
          </div>
          
          <div className="space-y-6">
            <div className="card overflow-hidden">
              <div className="card-header border-b border-slate-100 bg-white">
                <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2"><Receipt size={18} className="text-purple-500" /> Patient Invoices</h2>
              </div>
              <div className="bg-white">
                {invoices.length > 0 ? (
                  <div className="divide-y divide-slate-100">
                    {invoices.map((i: any) => (
                      <div key={i.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                        <div>
                          <p className="font-semibold text-[var(--accent-primary)] text-sm">{i.invoice_number}</p>
                          <p className="text-[10px] text-slate-400 uppercase tracking-widest mt-0.5">{new Date(i.generated_at).toLocaleDateString()}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-[var(--text-primary)]">${parseFloat(i.total_amount).toFixed(2)}</p>
                          <span className={`badge mt-1 ${i.status === 'paid' ? 'badge-success' : i.status === 'issued' ? 'badge-warning' : 'badge-neutral'}`}>{i.status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : <div className="p-8 flex flex-col items-center justify-center text-center text-slate-500"><Receipt size={32} className="mb-3 text-slate-300"/><p>No invoices generated yet.</p></div>}
              </div>
            </div>

            <div className="card overflow-hidden">
              <div className="card-header border-b border-slate-100 bg-white">
                <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2"><CreditCard size={18} className="text-emerald-500" /> Payment History</h2>
              </div>
              <div className="bg-white">
                {patientPayments.length > 0 ? (
                  <div className="divide-y divide-slate-100">
                    {patientPayments.map((p: any) => (
                      <div key={p.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                        <div>
                          <p className="font-semibold text-emerald-600 text-sm flex items-center gap-2 capitalize">
                            {p.payment_method}
                          </p>
                          <p className="text-[10px] text-slate-400 uppercase tracking-widest mt-0.5">{new Date(p.payment_time).toLocaleString()}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-[var(--text-primary)]">${parseFloat(p.amount).toFixed(2)}</p>
                          <span className={`badge mt-1 ${p.payment_status === 'completed' ? 'badge-success' : 'badge-neutral'}`}>{p.payment_status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : <div className="p-8 flex flex-col items-center justify-center text-center text-slate-500"><DollarSign size={32} className="mb-3 text-slate-300"/><p>No payments recorded yet.</p></div>}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

