"use client";

import React, { useState, useEffect } from "react";
import { ipdApi as api } from "@/lib/ipd-api";

export default function IpdBillingDashboard() {
  const [activeTab, setActiveTab] = useState<"active" | "settled">("active");
  const [bills, setBills] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Modal State for specific patient
  const [selectedBill, setSelectedBill] = useState<any>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [services, setServices] = useState<any[]>([]);
  const [deposits, setDeposits] = useState<any[]>([]);
  const [claims, setClaims] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [availableInsurances, setAvailableInsurances] = useState<any[]>([]);

  // Form states
  const [newService, setNewService] = useState({ category: "", name: "", qty: 1, price: 0 });
  const [newDeposit, setNewDeposit] = useState({ amount: 0, mode: "Cash", ref: "" });
  const [newClaim, setNewClaim] = useState({ provider: "", policy: "", preAuth: "", limit: 0, amount: 0 });
  const [newPay, setNewPay] = useState({ amount: 0, mode: "Card", ref: "" });

  useEffect(() => {
    fetchDashboard();
  }, [activeTab]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.getBillingDashboard();
      setBills(res as any);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const openBillDetail = async (admNo: string) => {
    try {
      const bRes = await api.getBillingMaster(admNo);
      setSelectedBill(bRes);
      const sRes = await api.getBillingServices(admNo);
      setServices(sRes as any);
      const dRes = await api.getBillingDeposits(admNo);
      setDeposits(dRes as any);
      const cRes = await api.getInsuranceClaims(admNo);
      setClaims(cRes as any);
      const pRes = await api.getPayments(admNo);
      setPayments(pRes as any);
      const iRes = await api.getAvailableInsurance(admNo);
      setAvailableInsurances(iRes as any);
      // Auto-populate form if available
      if (iRes && (iRes as any).length > 0) {
          const first = (iRes as any)[0];
          setNewClaim({ ...newClaim, provider: first.provider, policy: first.policy });
      } else {
          setNewClaim({ provider: "", policy: "", preAuth: "", limit: 0, amount: 0 });
      }
      setShowDetailModal(true);
    } catch (e) {
      console.error(e);
      alert("Error fetching billing details.");
    }
  };

  const handleRecalculate = async () => {
    if (!selectedBill) return;
    try {
      const res = await api.recalculateBill(selectedBill.admission_number);
      setSelectedBill(res);
      alert("Bill recalculated successfully!");
      fetchDashboard();
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddService = async () => {
    if (!selectedBill || !newService.category || !newService.name || newService.price <= 0) return;
    try {
      await api.addBillingService(selectedBill.admission_number, {
        service_category: newService.category,
        service_name: newService.name,
        quantity: newService.qty,
        unit_price: newService.price,
      });
      setNewService({ category: "", name: "", qty: 1, price: 0 });
      await openBillDetail(selectedBill.admission_number);
    } catch (e) {
      console.error(e);
      alert("Failed to add service.");
    }
  };

  const handleAddDeposit = async () => {
    if (!selectedBill || newDeposit.amount <= 0) return;
    try {
      await api.addDeposit(selectedBill.admission_number, {
        amount: newDeposit.amount,
        payment_mode: newDeposit.mode,
        reference_number: newDeposit.ref,
      });
      setNewDeposit({ amount: 0, mode: "Cash", ref: "" });
      await openBillDetail(selectedBill.admission_number);
    } catch (e) {
      console.error(e);
      alert("Failed to add deposit.");
    }
  };

  const handleAddClaim = async () => {
    if (!selectedBill || !newClaim.provider || !newClaim.policy) return;
    try {
      await api.addInsuranceClaim(selectedBill.admission_number, {
        insurance_provider: newClaim.provider,
        policy_number: newClaim.policy,
        pre_auth_number: newClaim.preAuth,
        coverage_limit: newClaim.limit,
        claimed_amount: newClaim.amount,
      });
      setNewClaim({ provider: "", policy: "", preAuth: "", limit: 0, amount: 0 });
      await openBillDetail(selectedBill.admission_number);
    } catch (e) {
      console.error(e);
      alert("Failed to add claim.");
    }
  };

  const handleProcessPayment = async () => {
    if (!selectedBill || newPay.amount <= 0) return;
    try {
      await api.addPayment(selectedBill.admission_number, {
        amount: newPay.amount,
        payment_mode: newPay.mode,
        reference_number: newPay.ref,
      });
      setNewPay({ amount: 0, mode: "Card", ref: "" });
      await openBillDetail(selectedBill.admission_number);
    } catch (e) {
      console.error(e);
      alert("Failed to process payment.");
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">IPD Billing & Settlement</h1>
          <p className="text-sm text-gray-500">Manage patient charges, deposits, insurance, and final settlements.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchDashboard}
            className="px-4 py-2 border rounded hover:bg-gray-50 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Data
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow mt-6">
        <ul className="flex border-b text-sm">
          <li
            className={`px-6 py-3 cursor-pointer ${activeTab === "active" ? "border-b-2 border-primary text-primary font-semibold" : "text-gray-500 hover:text-gray-700"}`}
            onClick={() => setActiveTab("active")}
          >
            Active Patients
          </li>
          <li
            className={`px-6 py-3 cursor-pointer ${activeTab === "settled" ? "border-b-2 border-primary text-primary font-semibold" : "text-gray-500 hover:text-gray-700"}`}
            onClick={() => setActiveTab("settled")}
          >
            Settled / Discharged
          </li>
        </ul>

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading billing data...</div>
        ) : bills.filter(b => activeTab === 'active' ? b.status !== 'Settled' : b.status === 'Settled').length === 0 ? (
          <div className="p-8 text-center text-gray-500">No billing records found for this tab.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="py-3 px-4">Adm No.</th>
                  <th className="py-3 px-4">Patient Name</th>
                  <th className="py-3 px-4 text-right">Charges</th>
                  <th className="py-3 px-4 text-right">Deposits</th>
                  <th className="py-3 px-4 text-right">Insurance</th>
                  <th className="py-3 px-4 text-right">Paid</th>
                  <th className="py-3 px-4 text-right">Balance</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {bills.filter(b => activeTab === 'active' ? b.status !== 'Settled' : b.status === 'Settled').map((b, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{b.admission_number}</td>
                    <td className="py-3 px-4">
                      {b.patient_name} <br />
                      <span className="text-xs text-gray-500">{b.patient_uhid} • {b.bed_code || 'No Bed'}</span>
                    </td>
                    <td className="py-3 px-4 text-right">₹{b.total_charges.toFixed(2)}</td>
                    <td className="py-3 px-4 text-right text-green-600">₹{b.total_deposits.toFixed(2)}</td>
                    <td className="py-3 px-4 text-right text-blue-600">₹{b.insurance_payable.toFixed(2)}</td>
                    <td className="py-3 px-4 text-right text-green-600">₹{b.total_paid.toFixed(2)}</td>
                    <td className="py-3 px-4 text-right font-bold text-red-600">₹{b.outstanding_balance.toFixed(2)}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs ${b.status === 'Settled' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                        {b.status || 'Active'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => openBillDetail(b.admission_number)}
                        className="text-primary hover:underline"
                      >
                        Manage Bill
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Bill Manage Modal */}
      {showDetailModal && selectedBill && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] flex flex-col shadow-xl">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h2 className="text-lg font-bold">Billing Details: {selectedBill.patient_name}</h2>
                <div className="text-sm text-gray-500">Adm No: {selectedBill.admission_number} | UHID: {selectedBill.patient_uhid}</div>
              </div>
              <button onClick={() => setShowDetailModal(false)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            <div className="p-4 flex-1 overflow-y-auto bg-gray-50 grid grid-cols-3 gap-6">
              {/* Left Column: Services & Insurance */}
              <div className="col-span-2 space-y-6">
                
                {/* Services Card */}
                <div className="bg-white p-4 rounded border shadow-sm">
                  <h3 className="font-semibold mb-4">Itemized Services & Charges</h3>
                  <div className="overflow-x-auto max-h-64 border rounded mb-4">
                    <table className="w-full text-sm text-left">
                      <thead className="bg-gray-100 sticky top-0">
                        <tr>
                          <th className="p-2">Date</th>
                          <th className="p-2">Category</th>
                          <th className="p-2">Service</th>
                          <th className="p-2 text-right">Qty</th>
                          <th className="p-2 text-right">Price</th>
                          <th className="p-2 text-right">Total</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {services.length === 0 ? (
                          <tr><td colSpan={6} className="p-4 text-center text-gray-400">No services billed yet.</td></tr>
                        ) : services.map((s, i) => (
                          <tr key={i}>
                            <td className="p-2 text-xs">{new Date(s.service_date).toLocaleDateString()}</td>
                            <td className="p-2">{s.service_category}</td>
                            <td className="p-2 truncate max-w-xs">{s.service_name}</td>
                            <td className="p-2 text-right">{s.quantity}</td>
                            <td className="p-2 text-right">₹{s.unit_price}</td>
                            <td className="p-2 text-right font-medium">₹{s.total_price}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="grid grid-cols-5 gap-2 items-end">
                    <div className="col-span-1">
                      <label className="text-xs text-gray-500 block">Category</label>
                      <select className="w-full border rounded p-1 text-sm" value={newService.category} onChange={e => setNewService({...newService, category: e.target.value})}>
                        <option value="">Select...</option>
                        <option>Consultation</option>
                        <option>Room & Nursing</option>
                        <option>Laboratory</option>
                        <option>Radiology</option>
                        <option>Pharmacy</option>
                        <option>Surgery/OT</option>
                        <option>Other</option>
                      </select>
                    </div>
                    <div className="col-span-2">
                       <label className="text-xs text-gray-500 block">Service Name</label>
                       <input type="text" className="w-full border rounded p-1 text-sm" value={newService.name} onChange={e => setNewService({...newService, name: e.target.value})} placeholder="Service Description"/>
                    </div>
                    <div>
                       <label className="text-xs text-gray-500 block">Qty</label>
                       <input type="number" min="1" className="w-full border rounded p-1 text-sm" value={newService.qty} onChange={e => setNewService({...newService, qty: parseInt(e.target.value) || 1})}/>
                    </div>
                    <div>
                       <label className="text-xs text-gray-500 block">Unit Price (₹)</label>
                       <input type="number" className="w-full border rounded p-1 text-sm" value={newService.price} onChange={e => setNewService({...newService, price: parseFloat(e.target.value) || 0})}/>
                    </div>
                  </div>
                  <div className="mt-3 text-right">
                    <button onClick={handleAddService} className="bg-primary text-white px-4 py-1.5 rounded text-sm hover:bg-primary/90">Add Service</button>
                  </div>
                </div>

                {/* Deposits Card */}
                <div className="bg-white p-4 rounded border shadow-sm">
                  <h3 className="font-semibold mb-4">Advance Deposits</h3>
                  <div className="overflow-x-auto max-h-48 border rounded mb-4">
                    <table className="w-full text-sm text-left">
                      <thead className="bg-gray-100 sticky top-0">
                        <tr>
                          <th className="p-2">Date</th>
                          <th className="p-2">Receipt</th>
                          <th className="p-2">Mode</th>
                          <th className="p-2">Reference</th>
                          <th className="p-2 text-right">Amount</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {deposits.length === 0 ? (
                          <tr><td colSpan={5} className="p-4 text-center text-gray-400">No deposits collected.</td></tr>
                        ) : deposits.map((d, i) => (
                          <tr key={i}>
                            <td className="p-2 text-xs">{new Date(d.deposit_date).toLocaleDateString()}</td>
                            <td className="p-2 text-xs text-gray-500">{d.receipt_number}</td>
                            <td className="p-2">{d.payment_mode}</td>
                            <td className="p-2">{d.reference_number || '-'}</td>
                            <td className="p-2 text-right font-medium text-green-600">₹{d.amount}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex gap-2 items-end">
                    <div className="w-1/4">
                       <label className="text-xs text-gray-500 block">Amount (₹)</label>
                       <input type="number" className="w-full border rounded p-1.5 text-sm" value={newDeposit.amount} onChange={e => setNewDeposit({...newDeposit, amount: parseFloat(e.target.value) || 0})}/>
                    </div>
                    <div className="w-1/4">
                       <label className="text-xs text-gray-500 block">Mode</label>
                       <select className="w-full border rounded p-1.5 text-sm" value={newDeposit.mode} onChange={e => setNewDeposit({...newDeposit, mode: e.target.value})}>
                          <option>Cash</option>
                          <option>Credit Card</option>
                          <option>Debit Card</option>
                          <option>UPI</option>
                          <option>Bank Transfer</option>
                       </select>
                    </div>
                    <div className="flex-1">
                       <label className="text-xs text-gray-500 block">Reference ID (Op)</label>
                       <input type="text" className="w-full border rounded p-1.5 text-sm" placeholder="Txn ID" value={newDeposit.ref} onChange={e => setNewDeposit({...newDeposit, ref: e.target.value})}/>
                    </div>
                    <button onClick={handleAddDeposit} className="bg-brand-secondary text-white px-4 py-1.5 rounded text-sm hover:opacity-90">Collect Deposit</button>
                  </div>
                </div>

                {/* Insurance Card */}
                <div className="bg-white p-4 rounded border shadow-sm">
                  <h3 className="font-semibold mb-4">Insurance & TPA Claims</h3>
                  <div className="overflow-x-auto border rounded mb-4">
                    <table className="w-full text-sm text-left">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="p-2">Provider</th>
                          <th className="p-2">Policy No</th>
                          <th className="p-2">PreAuth</th>
                          <th className="p-2 text-right">Limit</th>
                          <th className="p-2 text-right">Claimed</th>
                          <th className="p-2 text-right">Approved</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {claims.length === 0 ? (
                          <tr><td colSpan={6} className="p-4 text-center text-gray-400">No insurance claims filed.</td></tr>
                        ) : claims.map((c, i) => (
                          <tr key={i}>
                            <td className="p-2 font-medium">{c.insurance_provider}</td>
                            <td className="p-2 text-xs text-gray-500">{c.policy_number}</td>
                            <td className="p-2">{c.pre_auth_number || '-'}</td>
                            <td className="p-2 text-right">₹{c.coverage_limit}</td>
                            <td className="p-2 text-right text-yellow-600">₹{c.claimed_amount}</td>
                            <td className="p-2 text-right font-medium text-green-600">₹{c.approved_amount}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="grid grid-cols-6 gap-2 items-end mt-4">
                    {availableInsurances.length > 0 ? (
                        <div className="col-span-4">
                            <label className="text-xs text-gray-500 block">Select Registered Policy</label>
                            <select 
                                className="w-full border rounded p-1 text-sm bg-gray-50"
                                onChange={(e) => {
                                    const idx = e.target.selectedIndex;
                                    if(idx > 0) {
                                        const ins = availableInsurances[idx - 1];
                                        setNewClaim({...newClaim, provider: ins.provider, policy: ins.policy});
                                    }
                                }}
                            >
                                <option>-- Select Linked Policy --</option>
                                {availableInsurances.map((ins, idx) => (
                                    <option key={idx} value={ins.policy}>{ins.provider} (Pol: {ins.policy})</option>
                                ))}
                            </select>
                        </div>
                    ) : (
                        <>
                            <div className="col-span-2">
                                <label className="text-xs text-gray-500 block">Provider Name</label>
                                <input type="text" className="w-full border rounded p-1 text-sm" value={newClaim.provider} onChange={e => setNewClaim({...newClaim, provider: e.target.value})}/>
                            </div>
                            <div className="col-span-2">
                                <label className="text-xs text-gray-500 block">Policy No.</label>
                                <input type="text" className="w-full border rounded p-1 text-sm" value={newClaim.policy} onChange={e => setNewClaim({...newClaim, policy: e.target.value})}/>
                            </div>
                        </>
                    )}
                    <div>
                       <label className="text-xs text-gray-500 block">Pre-Auth</label>
                       <input type="text" className="w-full border rounded p-1 text-sm" value={newClaim.preAuth} onChange={e => setNewClaim({...newClaim, preAuth: e.target.value})}/>
                    </div>
                    <div>
                       <label className="text-xs text-gray-500 block">Claim Amt</label>
                       <input type="number" className="w-full border rounded p-1 text-sm" value={newClaim.amount} onChange={e => setNewClaim({...newClaim, amount: parseFloat(e.target.value) || 0})}/>
                    </div>
                  </div>
                  <div className="mt-3 text-right">
                    <button onClick={handleAddClaim} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700">File Claim</button>
                  </div>
                </div>

              </div>

              {/* Right Column: Calculations & Settlement */}
              <div className="flex flex-col gap-6">
                
                <div className="bg-white p-5 rounded border shadow-sm flex-1">
                  <div className="flex items-center justify-between mb-6 border-b pb-2">
                    <h3 className="font-bold text-lg">Bill Summary</h3>
                    <button onClick={handleRecalculate} className="text-xs bg-gray-100 px-2 py-1 rounded hover:bg-gray-200 text-gray-700">Recalculate</button>
                  </div>

                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Gross Total Charges:</span>
                      <span className="font-semibold">₹{selectedBill.total_charges.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Fixed Discount:</span>
                      <span className="text-red-500">- ₹{selectedBill.total_discount.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span className="font-medium">Net Amount:</span>
                      <span className="font-bold">₹{(selectedBill.total_charges - selectedBill.total_discount).toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between mt-4">
                      <span className="text-gray-500">Insurance Payable:</span>
                      <span className="text-blue-600 font-medium">- ₹{selectedBill.insurance_payable.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-700">Patient Payable:</span>
                      <span className="font-bold">₹{selectedBill.patient_payable.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between mt-4">
                      <span className="text-gray-500">Advance Deposits:</span>
                      <span className="text-green-600">- ₹{selectedBill.total_deposits.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Payments Received:</span>
                      <span className="text-green-600">- ₹{selectedBill.total_paid.toFixed(2)}</span>
                    </div>
                  </div>

                  <div className={`mt-6 p-4 rounded-lg flex items-center justify-between ${selectedBill.outstanding_balance > 0 ? 'bg-red-50 text-red-900 border border-red-200' : (selectedBill.outstanding_balance < 0 ? 'bg-yellow-50 text-yellow-900 border border-yellow-200' : 'bg-green-50 text-green-900 border border-green-200')}`}>
                    <div>
                      <div className="text-xs uppercase tracking-wider font-semibold opacity-80">
                        {selectedBill.outstanding_balance > 0 ? 'Outstanding Balance' : (selectedBill.outstanding_balance < 0 ? 'Refund Due' : 'Fully Settled')}
                      </div>
                      <div className="text-3xl font-black mt-1">₹{Math.abs(selectedBill.outstanding_balance).toFixed(2)}</div>
                    </div>
                  </div>

                  <div className="mt-8 border-t pt-6">
                    <h4 className="font-semibold mb-3 text-sm">Process Settlement</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">Payment Amount (₹)</label>
                        <input type="number" className="w-full border rounded p-2 text-sm bg-gray-50 font-bold text-gray-800" value={newPay.amount} onChange={e => setNewPay({...newPay, amount: parseFloat(e.target.value) || 0})}/>
                      </div>
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <label className="text-xs text-gray-500 block mb-1">Mode</label>
                          <select className="w-full border rounded p-2 text-sm" value={newPay.mode} onChange={e => setNewPay({...newPay, mode: e.target.value})}>
                            <option>Cash</option>
                            <option>Card</option>
                            <option>UPI</option>
                            <option>Online</option>
                          </select>
                        </div>
                        <div className="flex-1">
                          <label className="text-xs text-gray-500 block mb-1">Ref ID</label>
                          <input type="text" className="w-full border rounded p-2 text-sm" value={newPay.ref} onChange={e => setNewPay({...newPay, ref: e.target.value})}/>
                        </div>
                      </div>
                      <button onClick={handleProcessPayment} disabled={newPay.amount === 0} className={`w-full text-white py-2 rounded font-medium ${newPay.amount > 0 ? 'bg-green-600 hover:bg-green-700 shadow shadow-green-200' : 'bg-gray-300 cursor-not-allowed'}`}>
                        Process Payment
                      </button>
                    </div>

                    <div className="mt-6 flex gap-2">
                        <button 
                            onClick={() => window.open(`/dashboard/ipd-billing/print/${selectedBill.admission_number}`, '_blank')}
                            className="flex-1 border border-primary text-primary py-2 rounded text-sm hover:bg-primary/5"
                        >
                            Print Detail Bill
                        </button>
                        <button className="flex-1 border bg-gray-100 text-gray-700 py-2 rounded text-sm hover:bg-gray-200">Print Receipt</button>
                    </div>
                  </div>

                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
