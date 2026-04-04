"use client";

import React, { useState, useEffect } from "react";
import { procurementApi, Vendor, PurchaseRequest, PurchaseOrder, GRN } from "@/lib/procurement-api";
import { ShoppingCart, Truck, ShieldAlert, Package, CheckCircle2, Factory, ClipboardCheck, ArrowRight, PlusCircle } from "lucide-react";

export default function ProcurementDashboard() {
  const [activeTab, setActiveTab] = useState("PR");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [prs, setPrs] = useState<PurchaseRequest[]>([]);
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [grns, setGrns] = useState<GRN[]>([]);
  
  const [stores, setStores] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);

  // Modals state
  const [showPRModal, setShowPRModal] = useState(false);
  const [showPOModal, setShowPOModal] = useState<PurchaseRequest | null>(null);
  const [showGRNModal, setShowGRNModal] = useState<PurchaseOrder | null>(null);

  const fetchProcurementData = async () => {
    setLoading(true);
    setError("");
    try {
      if (activeTab === "PR") {
        setPrs(await procurementApi.getPRs());
        if (!stores.length) {
          setStores(await procurementApi.getStores());
          setItems(await procurementApi.getItems());
        }
      }
      if (activeTab === "VENDORS") setVendors(await procurementApi.getVendors());
      if (activeTab === "PO") {
        setPos(await procurementApi.getPOs());
        if (!vendors.length) setVendors(await procurementApi.getVendors());
      }
      if (activeTab === "GRN") setGrns(await procurementApi.getGRNs());
    } catch (e: any) {
      setError("Failed to fetch procurement data: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProcurementData();
  }, [activeTab]);

  const approvePR = async (id: string) => {
    try {
      await procurementApi.approvePR(id);
      setSuccess("Purchase Request successfully approved.");
      fetchProcurementData();
    } catch (e: any) { setError(e.message); }
  };

  const createPR = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await procurementApi.createPR({
        requesting_store_id: formData.get("requesting_store_id"),
        delivery_store_id: formData.get("delivery_store_id"),
        priority: formData.get("priority"),
        justification: formData.get("justification"),
        items: [{
          item_id: formData.get("item_id"),
          requested_qty: Number(formData.get("requested_qty"))
        }]
      });
      setSuccess("New Purchase Request Raised!");
      setShowPRModal(false);
      fetchProcurementData();
    } catch (e: any) { setError(e.message); }
  };

  const createPO = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if(!showPOModal) return;
    const formData = new FormData(e.currentTarget);
    try {
      await procurementApi.createPO({
        vendor_id: formData.get("vendor_id"),
        pr_id: showPOModal.id,
        delivery_date: new Date(Date.now() + 86400000 * 7).toISOString(), 
        items: showPOModal.items.map(i => ({
          item_id: i.item_id,
          ordered_qty: i.approved_qty,
          rate: Number(formData.get("rate")),
          tax_pct: Number(formData.get("tax_pct"))
        }))
      });
      setSuccess(`PO successfully dispatched to Vendor!`);
      setShowPOModal(null);
      setActiveTab("PO");
    } catch (e: any) { setError(e.message); }
  };

  const receiveGRN = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if(!showGRNModal) return;
    const formData = new FormData(e.currentTarget);
    try {
      await procurementApi.createGRN({
        po_id: showGRNModal.id,
        vendor_id: showGRNModal.vendor_id,
        store_id: formData.get("store_id"),
        invoice_number: formData.get("invoice_number"),
        items: showGRNModal.items.map(i => ({
          po_item_id: i.item_id, // technically it's po item id, simplified here
          item_id: i.item_id,
          received_qty: i.ordered_qty
        }))
      });
      setSuccess(`Goods Receipt Note created! Pending Physical Inspection.`);
      setShowGRNModal(null);
      setActiveTab("GRN");
    } catch (e: any) { setError(e.message); }
  };

  const inspectGRN = async (id: string, grn: GRN) => {
    try {
      const inspections: Record<string, any> = {};
      grn.items.forEach(i => {
        inspections[i.id] = { accepted_qty: i.received_qty, rejected_qty: 0, inspection_remarks: "All intact." };
      });
      await procurementApi.inspectGRN(id, inspections);
      setSuccess("GRN physically inspected. Inventory successfully restocked!");
      fetchProcurementData();
    } catch (e: any) { setError(e.message); }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans p-6 overflow-y-auto w-full max-w-7xl mx-auto">
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <ShoppingCart className="text-indigo-600" /> Enterprise Procurement System
          </h1>
          <p className="text-slate-500 font-bold text-xs uppercase tracking-wider mt-1">
            Procure-to-Pay Lifecycle Management
          </p>
        </div>
        <div className="flex bg-slate-100 p-1 rounded-xl shadow-inner border border-slate-200">
          {["PR", "PO", "GRN", "VENDORS"].map(tb => (
            <button
              key={tb}
              onClick={() => setActiveTab(tb)}
              className={`px-5 py-2.5 rounded-lg text-xs font-black transition-all ${
                activeTab === tb ? "bg-indigo-600 text-white shadow" : "text-slate-500 hover:text-indigo-600"
              }`}
            >
              {tb === "PR" && "Purchase Requests"}
              {tb === "PO" && "Purchase Orders"}
              {tb === "GRN" && "Goods Receipt (GRN)"}
              {tb === "VENDORS" && "Vendor Master"}
            </button>
          ))}
        </div>
      </div>

      {(error || success) && (
        <div className={`p-4 rounded-xl mb-6 shadow border font-bold text-sm flex gap-2 items-center ${error ? 'bg-rose-50 text-rose-800 border-rose-200' : 'bg-emerald-50 text-emerald-800 border-emerald-200'}`}>
          {error ? <ShieldAlert size={18} /> : <CheckCircle2 size={18} />}
          {error || success}
          <button onClick={() => { setError(""); setSuccess(""); }} className="ml-auto underline text-xs opacity-70">Dismiss</button>
        </div>
      )}

      {/* VENDOR TAB */}
      {activeTab === "VENDORS" && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 bg-slate-50 border-b relative"><h3 className="font-black text-slate-800 flex items-center gap-2"><Factory size={16}/> Registered Vendors</h3></div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {vendors.map(v => (
                <div key={v.id} className="border rounded-xl p-4 flex flex-col">
                  <span className="text-[10px] font-black uppercase text-indigo-500">{v.vendor_code}</span>
                  <h4 className="font-black text-slate-800 text-lg">{v.name}</h4>
                  <p className="text-xs text-slate-500 mb-2">Contact: {v.contact_person} | {v.phone}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* PURCHASE REQUEST TAB */}
      {activeTab === "PR" && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 bg-slate-50 border-b flex justify-between items-center">
            <h3 className="font-black text-slate-800">Departmental Purchase Requests</h3>
            <button onClick={() => setShowPRModal(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1 font-bold text-xs px-3 py-1.5 rounded shadow-sm">
              <PlusCircle size={14}/> Raise New PR
            </button>
          </div>
          <div className="p-6 space-y-4">
            {prs.map(pr => (
              <div key={pr.id} className="border border-slate-200 rounded-xl p-4 flex flex-col gap-4 bg-white hover:bg-slate-50 transition-all">
                <div className="flex justify-between items-center border-b pb-3">
                  <div>
                    <h4 className="font-black text-lg text-slate-800">{pr.pr_number}</h4>
                    <span className={`text-[10px] uppercase font-black px-2 py-0.5 rounded mt-1 inline-block ${pr.priority === 'URGENT'?'bg-rose-100 text-rose-700':'bg-slate-100 text-slate-600'}`}>{pr.priority} Priority</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded text-xs font-black uppercase ${pr.status==='APPROVED'?'bg-emerald-100 text-emerald-800':(pr.status==='PO_GENERATED'?'bg-indigo-100 text-indigo-800':'bg-amber-100 text-amber-800')}`}>{pr.status}</span>
                    {pr.status === "PENDING_APPROVAL" && (
                      <button onClick={()=>approvePR(pr.id)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-4 py-2 rounded-lg shadow-sm">APPROVE</button>
                    )}
                    {pr.status === "APPROVED" && (
                      <button onClick={()=>setShowPOModal(pr)} className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2 rounded-lg shadow-sm flex items-center gap-1">Generate PO <ArrowRight size={14}/></button>
                    )}
                  </div>
                </div>
                <div className="text-sm text-slate-600">
                  <span className="font-bold">Justification:</span> {pr.justification}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: CREATE PR */}
      {showPRModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex justify-center items-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden">
            <div className="p-4 border-b bg-slate-50"><h2 className="font-black text-lg">Raise Purchase Request (Indent)</h2></div>
            <form onSubmit={createPR} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Requesting Store</label>
                  <select name="requesting_store_id" required className="w-full border rounded-lg p-2 text-sm bg-slate-50"><option value="">Select Store...</option>{stores.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Delivery Store</label>
                  <select name="delivery_store_id" required className="w-full border rounded-lg p-2 text-sm bg-slate-50"><option value="">Select Store...</option>{stores.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Select Item</label>
                  <select name="item_id" required className="w-full border rounded-lg p-2 text-sm bg-slate-50"><option value="">Select AXONHIS Item...</option>{items.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}</select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Quantity</label>
                  <input type="number" name="requested_qty" required min="1" className="w-full border rounded-lg p-2 text-sm" placeholder="e.g. 500"/>
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-1">Priority</label>
                <select name="priority" className="w-full border rounded-lg p-2 text-sm bg-slate-50"><option value="NORMAL">Normal</option><option value="URGENT">Urgent Stock Depletion</option></select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-1">Justification</label>
                <textarea name="justification" required className="w-full border rounded-lg p-2 text-sm" rows={2} placeholder="Reason for purchase..."></textarea>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={()=>setShowPRModal(false)} className="px-4 py-2 font-bold text-sm text-slate-500 hover:bg-slate-100 rounded-lg">Cancel</button>
                <button type="submit" className="px-4 py-2 font-bold text-sm text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg">Submit Indent</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: GENERATE PO */}
      {showPOModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex justify-center items-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden">
            <div className="p-4 border-b bg-indigo-50"><h2 className="font-black text-lg text-indigo-900">Generate Purchase Order</h2></div>
            <form onSubmit={createPO} className="p-6 space-y-4">
              <p className="text-sm text-slate-600 font-bold mb-4">Sourcing for PR: <span className="text-indigo-600">{showPOModal.pr_number}</span></p>
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-1">Select Sourcing Vendor</label>
                <select name="vendor_id" required className="w-full border rounded-lg p-2 text-sm bg-slate-50">
                  <option value="">Select Authorized Vendor...</option>
                  {vendors.map(v => <option key={v.id} value={v.id}>{v.name} ({v.vendor_code})</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Negotiated Rate (Per Unit)</label>
                  <input type="number" step="0.01" name="rate" required className="w-full border rounded-lg p-2 text-sm" placeholder="e.g. 15.50"/>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Applicable GST/Tax %</label>
                  <input type="number" step="0.1" name="tax_pct" required className="w-full border rounded-lg p-2 text-sm" placeholder="e.g. 18.0"/>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={()=>setShowPOModal(null)} className="px-4 py-2 font-bold text-sm text-slate-500 hover:bg-slate-100 rounded-lg">Cancel</button>
                <button type="submit" className="px-4 py-2 font-bold text-sm text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center gap-1"><ArrowRight size={16}/> Dispatch PO</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PO TAB */}
      {activeTab === "PO" && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 bg-slate-50 border-b relative"><h3 className="font-black text-slate-800">Active Supply Orders (Sourcing)</h3></div>
          <div className="p-6 space-y-4">
            {pos.map(po => (
              <div key={po.id} className="border border-slate-200 rounded-xl p-4 flex flex-col gap-4 bg-slate-50">
                <div className="flex justify-between items-center border-b pb-3 border-slate-200">
                  <div>
                    <h4 className="font-black text-lg text-slate-800">{po.po_number}</h4>
                    <p className="text-xs text-slate-500 font-bold mt-1">Delivery ETA: {po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : 'TBD'}</p>
                  </div>
                  <div className="text-right flex items-center gap-4">
                    <div className="text-right">
                      <div className="font-black text-indigo-700 text-lg">${po.net_amount.toFixed(2)}</div>
                      <span className="text-[10px] font-black uppercase text-slate-400 border border-slate-200 px-2 py-0.5 rounded">{po.status}</span>
                    </div>
                    {po.status === "SENT" && (
                      <button onClick={()=>setShowGRNModal(po)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-4 py-2 rounded-lg shadow-sm flex items-center gap-1 ml-4"><Truck size={14}/> Receive Delivery</button>
                    )}
                  </div>
                </div>
                <div className="text-xs font-bold text-slate-500">
                  Supplier ID: {po.vendor_id} | Linked PR: {po.pr_id || 'N/A'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: RECEIVE GRN */}
      {showGRNModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex justify-center items-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden">
            <div className="p-4 border-b bg-emerald-50"><h2 className="font-black text-lg text-emerald-900 flex items-center gap-2"><Truck size={18}/> Inbound Delivery Manifest</h2></div>
            <form onSubmit={receiveGRN} className="p-6 space-y-4">
              <p className="text-sm text-slate-600 font-bold mb-4">Receiving delivery against: <span className="text-emerald-600">{showGRNModal.po_number}</span></p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Vendor Invoice / BOL #</label>
                  <input type="text" name="invoice_number" required className="w-full border rounded-lg p-2 text-sm font-mono uppercase" placeholder="INV-2026-XYZ"/>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Receiving Dock / Store</label>
                  <select name="store_id" required className="w-full border rounded-lg p-2 text-sm bg-slate-50">
                    {stores.length ? stores.map(s => <option key={s.id} value={s.id}>{s.name}</option>) : <option value={showGRNModal.vendor_id}>Default Receiving Dock</option>}
                  </select>
                </div>
              </div>
              <div className="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-3 rounded-lg font-bold">
                By submitting this form, you confirm physical goods have arrived at the dock. This will trigger the QA Physical Inspection protocol.
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={()=>setShowGRNModal(null)} className="px-4 py-2 font-bold text-sm text-slate-500 hover:bg-slate-100 rounded-lg">Cancel</button>
                <button type="submit" className="px-4 py-2 font-bold text-sm text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg flex items-center gap-1"><Package size={16}/> Lock Delivery</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* GRN TAB */}
      {activeTab === "GRN" && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 bg-slate-50 border-b relative"><h3 className="font-black text-slate-800 flex items-center gap-2"><ClipboardCheck size={16}/> Quality Assurance & Re-stocking (GRN)</h3></div>
          <div className="p-6 space-y-4">
            {grns.map(g => (
              <div key={g.id} className={`border rounded-xl p-4 ${g.status==='APPROVED'?'border-emerald-200 bg-emerald-50/30':'border-amber-200 bg-amber-50/30'}`}>
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="font-black text-slate-800">{g.grn_number}</h4>
                    <p className="text-xs font-bold text-slate-600 mt-1">Vendor Invoice: <span className="font-mono">{g.invoice_number}</span></p>
                  </div>
                  <div className="text-right flex items-center gap-4">
                     <span className={`px-3 py-1 rounded text-[10px] font-black uppercase ${g.status==='APPROVED'?'bg-emerald-100 text-emerald-800':'bg-amber-100 text-amber-800'}`}>{g.status.replace("_", " ")}</span>
                     {g.status === "INSPECTION_PENDING" && (
                       <button onClick={()=>inspectGRN(g.id, g)} className="ml-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2 rounded-lg shadow-sm flex items-center gap-1"><ClipboardCheck size={14}/> QA Pass & Add to Inventory</button>
                     )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
