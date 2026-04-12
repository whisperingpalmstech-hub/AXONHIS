"use client";
import { useTranslation } from "@/i18n";


import React, { useEffect, useState } from "react";
import { ipdApi as api } from "@/lib/ipd-api";
import { useParams } from "next/navigation";

export default function IpdBillingPrint() {
  const { t } = useTranslation();
  const params = useParams();
  const admNo = params.admNo as string;

  const [bill, setBill] = useState<any>(null);
  const [services, setServices] = useState<any[]>([]);
  const [deposits, setDeposits] = useState<any[]>([]);
  const [claims, setClaims] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (admNo) {
      fetchBillDetails();
    }
  }, [admNo]);

  const fetchBillDetails = async () => {
    try {
      const bRes = await api.getBillingMaster(admNo);
      setBill(bRes);
      const sRes = await api.getBillingServices(admNo);
      setServices(sRes as any);
      const dRes = await api.getBillingDeposits(admNo);
      setDeposits(dRes as any);
      const cRes = await api.getInsuranceClaims(admNo);
      setClaims(cRes as any);
      const pRes = await api.getPayments(admNo);
      setPayments(pRes as any);
      
      setLoading(false);
      // Wait for React to render the DOM, then trigger print dialog
      setTimeout(() => {
          window.print();
      }, 500);
    } catch (e) {
      console.error(e);
      alert("Error loading bill data for printing.");
    }
  };

  if (loading) return <div className="p-10">Generating Print View...</div>;
  if (!bill) return <div className="p-10 text-red-500">Bill not found.</div>;

  return (
    <div className="bg-white text-black max-w-[210mm] mx-auto p-8 text-sm" id="print-area">
      <style dangerouslySetInnerHTML={{__html: `
        @media print {
            body { background-color: white !important; }
            #sidebar, #navbar, nav, header { display: none !important; }
            #print-area { width: 100% !important; max-width: none !important; margin: 0; padding: 0;}
            .page-break { page-break-after: always; }
        }
      `}} />

      {/* Header Section */}
      <div className="flex justify-between items-start border-b-2 border-black pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold uppercase tracking-wider">AXONHIS HOSPITAL</h1>
          <p className="text-xs text-gray-700">123 Healthway Drive, Medical City</p>
          <p className="text-xs text-gray-700">Phone: +1 800-555-0199 | GSTIN: 29AABBCCDD1Z</p>
        </div>
        <div className="text-right">
          <h2 className="text-xl font-bold">INPATIENT FINAL BILL</h2>
          <p className="text-xs font-mono mt-1">Date: {new Date().toLocaleDateString()}</p>
          <p className="text-xs font-mono font-bold">Status: {bill.status.toUpperCase()}</p>
        </div>
      </div>

      {/* Patient Details */}
      <div className="grid grid-cols-2 gap-4 mb-8 border p-4 rounded text-xs">
        <div>
          <p><span className="font-semibold inline-block w-24">Patient Name:</span> <span className="uppercase font-bold">{bill.patient_name}</span></p>
          <p><span className="font-semibold inline-block w-24">UHID:</span> {bill.patient_uhid}</p>
          <p><span className="font-semibold inline-block w-24">Admission No:</span> {bill.admission_number}</p>
        </div>
        <div>
          <p><span className="font-semibold inline-block w-24">Ward:</span> {bill.ward_name || '-'}</p>
          <p><span className="font-semibold inline-block w-24">Bed Code:</span> {bill.bed_code || '-'}</p>
          <p><span className="font-semibold inline-block w-24">Billed On:</span> {new Date(bill.created_at).toLocaleString()}</p>
        </div>
      </div>

      {/* Itemized Services */}
      <h3 className="font-semibold mb-2 uppercase text-xs border-b border-gray-300 pb-1">Statement of Charges</h3>
      <table className="w-full mb-8 text-xs border-collapse">
        <thead className="bg-gray-100 border-b border-t">
          <tr>
            <th className="py-2 text-left w-24">Date</th>
            <th className="py-2 text-left">Category</th>
            <th className="py-2 text-left">Description</th>
            <th className="py-2 text-right">Qty</th>
            <th className="py-2 text-right">Rate</th>
            <th className="py-2 text-right">Total (₹)</th>
          </tr>
        </thead>
        <tbody>
          {services.map((s, i) => (
            <tr key={i} className="border-b border-gray-100 border-dashed">
              <td className="py-2 align-top">{new Date(s.service_date).toLocaleDateString()}</td>
              <td className="py-2 align-top">{s.service_category}</td>
              <td className="py-2 align-top">{s.service_name}</td>
              <td className="py-2 align-top text-right">{s.quantity}</td>
              <td className="py-2 align-top text-right">{s.unit_price.toFixed(2)}</td>
              <td className="py-2 align-top text-right font-semibold">{s.total_price.toFixed(2)}</td>
            </tr>
          ))}
          {services.length === 0 && (
            <tr><td colSpan={6} className="py-4 text-center italic">No services billed.</td></tr>
          )}
        </tbody>
        <tfoot>
          <tr className="border-t border-black font-bold">
            <td colSpan={5} className="py-2 text-right">Gross Total:</td>
            <td className="py-2 text-right">₹ {bill.total_charges.toFixed(2)}</td>
          </tr>
        </tfoot>
      </table>

      {/* Financial Transactions: Deposits, Insurance, Payments */}
      <div className="grid grid-cols-2 gap-8 mb-8">
          <div>
              <h3 className="font-semibold mb-2 uppercase text-xs border-b border-gray-300 pb-1">Advance Deposits</h3>
              {deposits.length > 0 ? (
                  <table className="w-full text-xs">
                      <tbody>
                          {deposits.map((d, i) => (
                              <tr key={i} className="border-b border-gray-100 border-dashed">
                                  <td className="py-1">{new Date(d.deposit_date).toLocaleDateString()}</td>
                                  <td className="py-1">{d.payment_mode} ({d.receipt_number})</td>
                                  <td className="py-1 text-right">₹{d.amount.toFixed(2)}</td>
                              </tr>
                          ))}
                      </tbody>
                  </table>
              ) : <p className="text-xs italic py-1">No advance deposits collected.</p>}

              <h3 className="font-semibold mt-4 mb-2 uppercase text-xs border-b border-gray-300 pb-1">Insurance Adjustments</h3>
              {claims.length > 0 ? (
                  <table className="w-full text-xs">
                      <tbody>
                          {claims.map((c, i) => (
                              <tr key={i} className="border-b border-gray-100 border-dashed">
                                  <td className="py-1">{c.insurance_provider}</td>
                                  <td className="py-1 text-right text-green-700">₹{c.approved_amount.toFixed(2)}</td>
                              </tr>
                          ))}
                      </tbody>
                  </table>
              ) : <p className="text-xs italic py-1">No insurance claims registered.</p>}
          </div>

          <div>
              <h3 className="font-semibold mb-2 uppercase text-xs border-b border-gray-300 pb-1">Final Settlement Summary</h3>
              <table className="w-full text-sm">
                <tbody>
                  <tr>
                    <td className="py-1 text-gray-700">Gross Total</td>
                    <td className="py-1 text-right">₹ {bill.total_charges.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-1 text-gray-700">Less: Discount</td>
                    <td className="py-1 text-right text-red-600">- ₹ {bill.total_discount.toFixed(2)}</td>
                  </tr>
                  <tr className="border-t font-semibold">
                    <td className="py-1">Net Payable Amount</td>
                    <td className="py-1 text-right">₹ {(bill.total_charges - bill.total_discount).toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-1 text-gray-700">Less: Insurance Coverage</td>
                    <td className="py-1 text-right text-green-700">- ₹ {bill.insurance_payable.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-1 text-gray-700">Patient Share Payable</td>
                    <td className="py-1 text-right">₹ {bill.patient_payable.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-1 text-gray-700">Less: Advance Paid</td>
                    <td className="py-1 text-right">- ₹ {bill.total_deposits.toFixed(2)}</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-1 text-gray-700">Less: Payments Received</td>
                    <td className="py-1 text-right">- ₹ {bill.total_paid.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="py-3 font-bold text-base uppercase">Final Balance</td>
                    <td className="py-3 text-right font-bold text-base">₹ {bill.outstanding_balance.toFixed(2)}</td>
                  </tr>
                </tbody>
              </table>
          </div>
      </div>

      <div className="mt-16 pt-8 border-t border-gray-300 flex justify-between px-10">
          <div className="text-center">
              <div className="w-40 border-b border-black mb-2"></div>
              <p className="text-xs font-semibold">Prepared By</p>
          </div>
          <div className="text-center">
              <div className="w-40 border-b border-black mb-2"></div>
              <p className="text-xs font-semibold">Patient / Attendee Signature</p>
          </div>
      </div>

      <div className="mt-8 text-center text-[10px] text-gray-500 italic">
        This is a computer-generated invoice and requires no physical seal. Please retain this copy for your records.
      </div>
    </div>
  );
}
