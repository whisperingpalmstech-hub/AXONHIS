"use client";
import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost, apiPut } from "@/lib/api";

export default function Page() {
  const searchParams = useSearchParams();
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showBillModal, setShowBillModal] = useState(false);
  const [form, setForm] = useState<any>({ invoice_type: "PROFESSIONAL", status: "PENDING" });
  const [selectedInvoice, setSelectedInvoice] = useState<any>(null);
  const [encounters, setEncounters] = useState<any[]>([]);
  const [payers, setPayers] = useState<any[]>([]);
  const [coverageList, setCoverageList] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [invData, encData, payerData] = await Promise.all([
        apiFetch("/billing/invoices"),
        apiFetch("/encounters"),
        apiFetch("/payers")
      ]);
      setInvoices(invData);
      setEncounters(encData);
      setPayers(payerData);
    } catch { setInvoices([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  // Load URL params and pre-fill form
  useEffect(() => {
    const encounterId = searchParams.get("encounter_id");
    const patientId = searchParams.get("patient_id");
    const patientName = searchParams.get("patient_name");

    if (encounterId || patientId) {
      setForm(prev => ({
        ...prev,
        encounter_id: encounterId || prev.encounter_id,
        patient_id: patientId || prev.patient_id,
        patient_name: patientName || prev.patient_name
      }));
      setShowModal(true);

      // Fetch patient coverage if patient_id is available
      if (patientId) {
        apiFetch(`/coverage?patient_id=${patientId}`).then(setCoverageList).catch(() => setCoverageList([]));
      }
    }
  }, [searchParams]);

  const handleCreateInvoice = async () => {
    if (!form.patient_id) {
      alert("Patient is required");
      return;
    }
    setSaving(true);
    try {
      const lineItems = [
        {
          description: "Consultation Fee",
          quantity: 1,
          unit_price: parseFloat(form.total_amount || 100),
          line_amount: parseFloat(form.total_amount || 100)
        }
      ];

      await apiPost("/billing/invoices", {
        patient_id: form.patient_id,
        encounter_id: form.encounter_id,
        coverage_id: form.coverage_id,
        currency_code: "USD",
        due_date: form.due_date || undefined,
        line_items: lineItems
      });
      setShowModal(false);
      setForm({ invoice_type: "PROFESSIONAL", status: "PENDING" });
      setCoverageList([]);
      load();
    } catch (e: any) { alert("Error creating invoice: " + e.message); }
    finally { setSaving(false); }
  };

  const handleUpdateStatus = async (invoice: any, newStatus: string) => {
    try {
      await apiFetch(`/billing/invoices/${invoice.billing_invoice_id}/status?status=${newStatus}`, { method: "PATCH" });
      load();
    } catch (e: any) { alert("Error updating status: " + e.message); }
  };

  const handleGenerateBill = (invoice: any) => {
    setSelectedInvoice(invoice);
    setShowBillModal(true);
  };

  const handlePrintBill = () => {
    window.print();
  };

  const statusColors: Record<string,string> = { PENDING: "badge-warning", PAID: "badge-success", OVERDUE: "badge-error", CANCELLED: "badge-neutral" };

  return (<div><TopNav title="Billing & Invoices" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Billing & Invoices</h2><p className="text-sm text-slate-500">{invoices.length} records</p></div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Create Invoice</button>
      </div>

      {loading ? <div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      invoices.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-slate-50 flex items-center justify-center text-4xl">\ud83d\udcb0</div>
          <h3 className="text-lg font-bold text-slate-700">No Invoices</h3>
          <p className="text-sm text-slate-500 mt-1">Create invoices from encounters to get started</p>
        </div>
      ) :
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm overflow-x-auto">
        <table className="data-table min-w-full"><thead><tr><th>#</th><th>Invoice Number</th><th>Patient</th><th>Type</th><th>Amount</th><th>Status</th><th>Due Date</th><th>Actions</th></tr></thead>
          <tbody>{invoices.map((item: any, i: number) => (
            <tr key={item.billing_invoice_id || i} className="hover:bg-teal-50/30">
              <td className="text-xs text-slate-400 font-mono">{i + 1}</td>
              <td className="font-semibold text-slate-800">{item.invoice_number || "—"}</td>
              <td className="text-sm text-slate-600">{item.patient_name || "—"}</td>
              <td><span className="badge badge-info">{item.invoice_type || "—"}</span></td>
              <td className="font-semibold text-slate-800">${item.total_amount ? item.total_amount.toFixed(2) : "0.00"}</td>
              <td><span className={`badge ${statusColors[item.status] || "badge-neutral"}`}>{item.status || "—"}</span></td>
              <td className="text-xs text-slate-500">{item.due_date ? new Date(item.due_date).toLocaleDateString() : "—"}</td>
              <td className="flex gap-1">
                <button className="btn-secondary text-xs py-1 px-2" onClick={() => handleGenerateBill(item)}>View</button>
                {item.status === "PENDING" && (
                  <button className="btn-primary text-xs py-1 px-2 bg-green-600 hover:bg-green-700" onClick={() => handleUpdateStatus(item, "PAID")}>Mark Paid</button>
                )}
                {item.status === "PENDING" && (
                  <button className="btn-secondary text-xs py-1 px-2 bg-red-600 text-white hover:bg-red-700" onClick={() => handleUpdateStatus(item, "CANCELLED")}>Cancel</button>
                )}
              </td>
            </tr>))}</tbody></table>
      </div>}

      {/* Create Invoice Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Create New Invoice</h3>
            </div>
            <div className="modal-body space-y-4">
              {form.patient_name && (
                <div className="bg-teal-50 rounded-lg p-3">
                  <p className="text-sm font-medium text-teal-800">Patient: {form.patient_name}</p>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Encounter</label>
                <select className="input-field" value={form.encounter_id || ""} onChange={e => setForm({...form, encounter_id: e.target.value})}>
                  <option value="">Select Encounter</option>
                  {encounters.map((e: any) => (
                    <option key={e.encounter_id} value={e.encounter_id}>
                      {e.patient_name || e.encounter_id.split('-')[0]} - {new Date(e.started_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>
              {coverageList.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Insurance Coverage</label>
                  <select className="input-field" value={form.coverage_id || ""} onChange={e => setForm({...form, coverage_id: e.target.value})}>
                    <option value="">No Insurance (Self Pay)</option>
                    {coverageList.map((c: any) => (
                      <option key={c.coverage_id} value={c.coverage_id}>
                        {c.payer_name || "Insurance"} - {c.policy_number || "No Policy"}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Total Amount ($)</label>
                  <input type="number" className="input-field" value={form.total_amount || ""} onChange={e => setForm({...form, total_amount: e.target.value})} placeholder="100.00" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Invoice Type</label>
                  <select className="input-field" value={form.invoice_type || "PROFESSIONAL"} onChange={e => setForm({...form, invoice_type: e.target.value})}>
                    <option value="PROFESSIONAL">Professional</option>
                    <option value="PHARMACY">Pharmacy</option>
                    <option value="DIAGNOSTIC">Diagnostic</option>
                    <option value="PROCEDURAL">Procedural</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Due Date</label>
                <input type="date" className="input-field" value={form.due_date || ""} onChange={e => setForm({...form, due_date: e.target.value})} />
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={saving}>Cancel</button>
              <button type="button" className="btn-primary" onClick={handleCreateInvoice} disabled={saving}>{saving ? "Creating..." : "Create Invoice"}</button>
            </div>
          </div>
        </div>
      )}

      {/* Bill Preview Modal */}
      {showBillModal && selectedInvoice && (
        <div className="modal-overlay" onClick={() => setShowBillModal(false)}>
          <div className="modal-content max-w-3xl" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Invoice Bill - {selectedInvoice.invoice_number}</h3>
              <button onClick={() => setShowBillModal(false)} className="text-xl">&times;</button>
            </div>
            <div className="modal-body space-y-4">
              <div className="bg-slate-50 rounded-xl p-6">
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <h4 className="font-bold text-slate-800 mb-2">Bill To</h4>
                    <p className="text-sm text-slate-600">{selectedInvoice.patient_name || "Patient"}</p>
                    <p className="text-xs text-slate-500">Invoice: {selectedInvoice.invoice_number}</p>
                  </div>
                  <div className="text-right">
                    <h4 className="font-bold text-slate-800 mb-2">Amount Due</h4>
                    <p className="text-3xl font-bold text-teal-600">${selectedInvoice.total_amount ? selectedInvoice.total_amount.toFixed(2) : "0.00"}</p>
                    <p className="text-xs text-slate-500">Due: {selectedInvoice.due_date ? new Date(selectedInvoice.due_date).toLocaleDateString() : "—"}</p>
                  </div>
                </div>
                <div className="border-t border-slate-200 pt-4">
                  <h4 className="font-bold text-slate-800 mb-3">Bill Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-slate-600">Doctor Fees</span><span className="font-semibold">${(selectedInvoice.total_amount * 0.4).toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-600">Medications / Tablets</span><span className="font-semibold">${(selectedInvoice.total_amount * 0.3).toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-600">Lab Tests / Diagnostics</span><span className="font-semibold">${(selectedInvoice.total_amount * 0.2).toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-600">Procedures</span><span className="font-semibold">${(selectedInvoice.total_amount * 0.1).toFixed(2)}</span></div>
                    <div className="flex justify-between border-t border-slate-200 pt-2 mt-2"><span className="font-bold text-slate-800">Total</span><span className="font-bold text-teal-600">${selectedInvoice.total_amount ? selectedInvoice.total_amount.toFixed(2) : "0.00"}</span></div>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowBillModal(false)}>Close</button>
              <button type="button" className="btn-primary" onClick={handlePrintBill}>Print Bill</button>
            </div>
          </div>
        </div>
      )}
    </div></div>);
}
