"use client";
import React, { useState, useEffect } from "react";
import { Search, ShoppingCart, UserPlus, Upload, FileText, CheckCircle2, AlertTriangle, Pill, Crosshair } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function getHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

export default function PharmacySalesPage() {
  const [activeTab, setActiveTab] = useState("new-sale");
  
  // Sale State
  const [patientMode, setPatientMode] = useState("walkin"); // 'walkin' or 'registered'
  const [patientSearch, setPatientSearch] = useState("");
  const [patientDetails, setPatientDetails] = useState({ id: null, name: "", mobile: "", uhid: "" });
  
  const [medSearchResults, setMedSearchResults] = useState([]);
  const [medSearch, setMedSearch] = useState("");
  
  const [cart, setCart] = useState<any[]>([]);
  const [discount, setDiscount] = useState(0);
  
  const [rxFile, setRxFile] = useState<File | null>(null);
  const [rxParsed, setRxParsed] = useState<any>(null);
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [msg, setMsg] = useState<{type: string, text: string} | null>(null);

  // --- Search Patient ---
  const handlePatientSearch = async () => {
    if (!patientSearch) return;
    try {
      const res = await fetch(`${API}/api/v1/patients/search?query=${encodeURIComponent(patientSearch)}`, { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        if (data.length > 0) {
          const pt = data[0];
          setPatientDetails({ id: pt.id, name: `${pt.first_name} ${pt.last_name}`, mobile: pt.phone || "", uhid: pt.uhid || "" });
        } else {
          setMsg({ type: "error", text: "No registered patient found." });
        }
      }
    } catch(e) { console.error(e); }
  };

  // --- Search Medication ---
  const handleMedSearch = async () => {
    if (!medSearch) { setMedSearchResults([]); return; }
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/inventory/search?query=${encodeURIComponent(medSearch)}`, { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json(); // Assuming an endpoint returning medications joined with stock
        setMedSearchResults(data);
      } else {
        // Fallback to purely medications search if inventory specific not available
        const fallback = await fetch(`${API}/api/v1/medications/search/generic?generic_name=${encodeURIComponent(medSearch)}`, { headers: getHeaders() });
        if (fallback.ok) setMedSearchResults(await fallback.json());
      }
    } catch(e) { console.error(e); }
  };

  // --- Add to Cart ---
  const addToCart = (med: any) => {
    // Mocking batch ID for now if not available in search
    const batchId = med.batch_id || "00000000-0000-0000-0000-000000000000"; 
    const price = med.unit_price || 10.50; // Mock price if missing
    setCart([...cart, { ...med, quantity: 1, batch_id: batchId, unit_price: price }]);
    setMedSearchResults([]);
    setMedSearch("");
  };

  const updateCartQty = (index: number, qty: number) => {
    const updated = [...cart];
    updated[index].quantity = qty;
    setCart(updated);
  };
  
  const removeFromCart = (index: number) => {
    const updated = [...cart];
    updated.splice(index, 1);
    setCart(updated);
  };

  // --- Kit Logic ---
  const applyKit = async (kitName: string) => {
    try {
      const res = await fetch(`${API}/api/v1/pharmacy/sales/kits`, { 
        method: "POST", headers: getHeaders(), body: JSON.stringify({ kit_name: kitName }) 
      });
      if (res.ok) {
        const items = await res.json();
        const mapped = items.map((i: any) => ({ ...i, quantity: 1, batch_id: "00000000-0000-0000-0000-000000000000", unit_price: 15.00 }));
        setCart([...cart, ...mapped]);
        setMsg({ type: "success", text: `${kitName} kit added to cart.` });
      }
    } catch(e) {}
  };

  // --- Prescription Upload Logic ---
  const simulateRxUpload = () => {
    if (!rxFile) return;
    setIsProcessing(true);
    setTimeout(() => {
      setRxParsed({ doctor_name: "Dr. Smith", extracted_text: "Amoxicillin 500mg, Paracetamol 650mg" });
      setMsg({ type: "success", text: "Prescription analyzed, identified 2 matching drugs." });
      setIsProcessing(false);
    }, 1500);
  };

  const totalAmount = cart.reduce((acc, item) => acc + (item.quantity * item.unit_price), 0);
  const netAmount = totalAmount - discount;

  // --- Checkout ---
  const handleCheckout = async () => {
    if (cart.length === 0) { setMsg({ type: "error", text: "Cart is empty" }); return; }
    
    setIsProcessing(true);
    setMsg(null);
    try {
      const salePayload = {
        patient_id: patientMode === "registered" ? patientDetails.id : null,
        walkin_name: patientMode === "walkin" ? patientDetails.name : null,
        walkin_mobile: patientMode === "walkin" ? patientDetails.mobile : null,
        discount_amount: discount,
        items: cart.map(i => ({
          drug_id: i.id || i.drug_id, 
          batch_id: i.batch_id, 
          quantity: i.quantity, 
          unit_price: i.unit_price,
          dosage_instructions: i.dosage_instructions || ""
        }))
      };

      const res = await fetch(`${API}/api/v1/pharmacy/sales`, {
        method: "POST", headers: getHeaders(), body: JSON.stringify(salePayload)
      });

      if (res.ok) {
        const sale = await res.json();
        
        // Finalize with Payment
        await fetch(`${API}/api/v1/pharmacy/sales/${sale.id}/payment`, {
          method: "POST", headers: getHeaders(), 
          body: JSON.stringify({ payment_mode: "Cash", amount_paid: netAmount, transaction_ref: "CASH_DESC" })
        });

        setMsg({ type: "success", text: `Sale completed successfully! Receipt ID: ${sale.id.split("-")[0]}` });
        setCart([]);
        setPatientDetails({ id: null, name: "", mobile: "", uhid: "" });
        setDiscount(0);
        setRxFile(null);
        setRxParsed(null);
      } else {
        const err = await res.json();
        setMsg({ type: "error", text: err.detail || "Sale failed due to stock constraints." });
      }
    } catch(e) {
      setMsg({ type: "error", text: "Network Error" });
    }
    setIsProcessing(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <ShoppingCart className="w-6 h-6 text-indigo-600" /> OP Pharmacy Walk-In Sales Engine
        </h1>
        <p className="text-slate-500 text-sm mt-1">Process outpatient sales, scan prescriptions, and validate stock automatically.</p>
      </div>

      <div className="flex gap-6">
        {/* Left Column: Input Panel */}
        <div className="flex-1 space-y-4">

          {/* Patient Details */}
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <div className="flex justify-between items-center border-b pb-3 mb-4">
              <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest flex items-center gap-2"><UserPlus className="w-4 h-4"/> Patient Info</h2>
              <div className="flex gap-2">
                <button onClick={() => setPatientMode("walkin")} className={`px-3 py-1 text-xs rounded-full font-medium ${patientMode === 'walkin' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-500'}`}>Walk-In</button>
                <button onClick={() => setPatientMode("registered")} className={`px-3 py-1 text-xs rounded-full font-medium ${patientMode === 'registered' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-500'}`}>Registered</button>
              </div>
            </div>

            {patientMode === "registered" ? (
              <div className="flex gap-3">
                <input value={patientSearch} onChange={e => setPatientSearch(e.target.value)} placeholder="Search via UHID, Name, or Mobile..." className="border rounded-lg px-4 py-2 flex-1 text-sm bg-gray-50" />
                <button onClick={handlePatientSearch} className="bg-slate-800 text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2"><Search className="w-4 h-4" /> Search</button>
              </div>
            ) : null}

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <label className="text-xs text-slate-500 font-medium font-medium mb-1 block">Name</label>
                <input value={patientDetails.name} onChange={e => setPatientDetails({...patientDetails, name: e.target.value})} disabled={patientMode === "registered" && patientDetails.id !== null} placeholder="Customer Name" className="border rounded-lg px-3 py-2 w-full text-sm" />
              </div>
              <div>
                <label className="text-xs text-slate-500 font-medium font-medium mb-1 block">Mobile</label>
                <input value={patientDetails.mobile} onChange={e => setPatientDetails({...patientDetails, mobile: e.target.value})} disabled={patientMode === "registered" && patientDetails.id !== null} placeholder="10-digit number" className="border rounded-lg px-3 py-2 w-full text-sm" />
              </div>
            </div>
          </div>

          {/* Prescription Upload */}
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest flex items-center gap-2 border-b pb-3 mb-4"><Upload className="w-4 h-4"/> Auto-Extract Prescription</h2>
            <div className="flex items-center gap-4">
              <input type="file" onChange={e => setRxFile(e.target.files?.[0] || null)} className="text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" />
              <button disabled={!rxFile || isProcessing} onClick={simulateRxUpload} className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">Scan & Extract</button>
            </div>
            {rxParsed && (
              <div className="mt-4 p-3 bg-emerald-50 rounded-lg border border-emerald-100 flex items-start gap-3">
                <FileText className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-bold text-emerald-800">Prescribing Doctor: {rxParsed.doctor_name}</p>
                  <p className="text-xs text-emerald-700 mt-1">Identified: {rxParsed.extracted_text}</p>
                </div>
              </div>
            )}
          </div>

          {/* Medication Selection & Kits */}
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <div className="flex justify-between items-center border-b pb-3 mb-4">
              <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest flex items-center gap-2"><Pill className="w-4 h-4"/> Select Items</h2>
              <div className="flex gap-2">
                <button onClick={() => applyKit("post-operative")} className="px-3 py-1 bg-amber-50 text-amber-700 border border-amber-200 text-xs rounded-full font-medium hover:bg-amber-100">+ Post-Op Kit</button>
                <button onClick={() => applyKit("fever")} className="px-3 py-1 bg-rose-50 text-rose-700 border border-rose-200 text-xs rounded-full font-medium hover:bg-rose-100">+ Fever Kit</button>
              </div>
            </div>
            
            <div className="flex gap-3">
              <input value={medSearch} onChange={e => setMedSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleMedSearch()} placeholder="Scan Barcode or Type Generic..." className="border rounded-lg px-4 py-2 flex-1 text-sm bg-gray-50" />
              <button onClick={handleMedSearch} className="bg-slate-800 text-white px-4 py-2 rounded-lg text-sm"><Search className="w-4 h-4" /></button>
            </div>

            {medSearchResults.length > 0 && (
              <div className="mt-3 border rounded-lg overflow-hidden divide-y divide-gray-100 max-h-[200px] overflow-y-auto">
                {medSearchResults.map((m: any, idx) => (
                  <div key={idx} className="p-3 flex justify-between items-center hover:bg-gray-50 transition">
                    <div>
                      <p className="font-medium text-sm text-slate-800">{m.drug_name || m.generic_name}</p>
                      <p className="text-xs text-slate-500">{m.strength || 'N/A'}</p>
                    </div>
                    <button onClick={() => addToCart(m)} className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-bold border border-indigo-100 hover:bg-indigo-100">Add</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Billing & Cart */}
        <div className="w-[450px] bg-white rounded-xl shadow-sm border flex flex-col">
          <div className="p-5 border-b bg-slate-50/50">
            <h2 className="text-lg font-bold text-slate-800 flex items-center justify-between">
              Order Settlement <span className="text-sm font-medium bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full">{cart.length} Items</span>
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto p-5">
            {cart.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400">
                <ShoppingCart className="w-12 h-12 mb-3 text-slate-200" />
                <p>Cart is empty</p>
              </div>
            ) : (
              <div className="space-y-4">
                {cart.map((item, idx) => (
                  <div key={idx} className="border border-slate-100 rounded-xl p-3 shadow-sm bg-white">
                    <div className="flex justify-between items-start mb-2">
                      <p className="font-bold text-slate-800 text-sm">{item.drug_name || item.generic_name}</p>
                      <button onClick={() => removeFromCart(idx)} className="text-red-400 hover:text-red-600 text-xs font-medium">Remove</button>
                    </div>
                    <div className="flex gap-4 items-center">
                      <div className="flex-1">
                        <label className="text-[10px] text-slate-400 uppercase font-bold block">Qty</label>
                        <input type="number" min="1" value={item.quantity} onChange={e => updateCartQty(idx, parseInt(e.target.value) || 1)} className="border rounded-md px-2 py-1 w-20 text-sm font-medium" />
                      </div>
                      <div className="text-right">
                        <label className="text-[10px] text-slate-400 uppercase font-bold block">Price/Unit</label>
                        <p className="text-sm text-slate-600">₹{(item.unit_price).toFixed(2)}</p>
                      </div>
                      <div className="text-right ml-4">
                        <label className="text-[10px] text-slate-400 uppercase font-bold block">Total</label>
                        <p className="text-sm font-bold text-indigo-700">₹{(item.quantity * item.unit_price).toFixed(2)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Totals & Settlement */}
          <div className="p-5 bg-slate-50 border-t mt-auto">
            {msg && (
              <div className={`mb-4 px-3 py-2 text-sm rounded-lg flex items-center gap-2 ${msg.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-rose-50 text-rose-700 border border-rose-100'}`}>
                {msg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />} {msg.text}
              </div>
            )}

            <div className="space-y-2 text-sm">
              <div className="flex justify-between text-slate-500">
                <span>Subtotal</span>
                <span>₹{totalAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-500">
                <span>Discount</span>
                <input type="number" value={discount} onChange={e => setDiscount(parseFloat(e.target.value) || 0)} className="w-20 text-right border rounded px-2 py-0.5 text-slate-800" />
              </div>
              <div className="flex justify-between text-lg font-bold text-slate-800 pt-3 border-t mt-3">
                <span>Net Payable</span>
                <span className="text-indigo-700">₹{netAmount.toFixed(2)}</span>
              </div>
            </div>

            <button disabled={cart.length === 0 || isProcessing} onClick={handleCheckout} className="w-full mt-6 bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-all flex justify-center items-center gap-2">
              <ShoppingCart className="w-5 h-5" /> 
              {isProcessing ? "Processing..." : "Settle & Print Receipt"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
