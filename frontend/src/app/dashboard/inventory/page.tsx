"use client";
import React, { useState, useEffect } from "react";
import { TopNav } from "@/components/ui/TopNav";
import { Package, Activity, AlertTriangle, Layers, ArrowRightLeft, FileWarning, RefreshCcw, CheckSquare, Truck, Barcode, PlusCircle } from "lucide-react";

export default function InventoryDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [stores, setStores] = useState<any[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [indentIssued, setIndentIssued] = useState(false);
  const [transitAccepted, setTransitAccepted] = useState(false);
  const [gatepassGenerated, setGatepassGenerated] = useState(false);
  const [stockAdded, setStockAdded] = useState(false);
  const [scrapReason, setScrapReason] = useState("");
  const [scrapSubmitted, setScrapSubmitted] = useState(false);

  useEffect(() => {
    fetchStores();
  }, []);

  const fetchStores = async () => {
     try {
         const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
         const res = await fetch(`${api}/api/v1/inventory/stores`, {
             headers: { "Authorization": `Bearer ${localStorage.getItem("access_token")}` }
         });
         if (res.ok) {
             setStores(await res.json());
         }
     } catch(e) { console.error(e) }
  };

  const handleInitStores = async () => {
      try {
         const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
         await fetch(`${api}/api/v1/inventory/stores`, {
             method: 'POST', headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
             body: JSON.stringify({ name: "Main Central Store", store_type: "MAIN" })
         });
         await fetch(`${api}/api/v1/inventory/stores`, {
             method: 'POST', headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
             body: JSON.stringify({ name: "Pharmacy Store", store_type: "PHARMACY" })
         });
         await fetch(`${api}/api/v1/inventory/stores`, {
             method: 'POST', headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
             body: JSON.stringify({ name: "ICU Sublet", store_type: "ICU" })
         });
         fetchStores();
      } catch (e) { console.error(e) }
  }

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <TopNav title="Supply Chain & Inventory Management" />
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full">
        <div className="flex items-center justify-between mb-8">
           <div>
              <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
                 <Package className="text-indigo-600" size={36}/> Enterprise Store Management
              </h1>
              <p className="text-slate-500 font-medium mt-2">Multi-store hierarchical inventory, FEFO batch tracking, and issue workflows.</p>
           </div>
           <div className="flex gap-3">
              <button 
                  onClick={() => { setSyncing(true); setTimeout(() => { setSyncing(false); alert("ERP successfully synced with live database ledgers."); }, 1500) }}
                  className="bg-white border text-indigo-600 font-bold px-4 py-2 rounded-xl flex items-center gap-2">
                 <RefreshCcw size={16} className={syncing ? "animate-spin" : ""}/> {syncing ? "Syncing..." : "Sync ERP"}
              </button>
              <button onClick={() => setActiveTab('scrap')} className="btn-primary flex items-center gap-2 px-5 py-2.5 bg-indigo-600 font-bold text-white shadow-md rounded-xl">
                 <Layers size={18}/> Initiate Stock Audit
              </button>
           </div>
        </div>

        {/* Action KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
           <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 border-l-4 border-l-emerald-500">
               <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider mb-1">Active Stores</h3>
               <div className="text-3xl font-black text-slate-800">{stores.length} <span className="text-sm font-medium text-emerald-500">Operational</span></div>
               {stores.length === 0 && <button onClick={handleInitStores} className="mt-2 text-xs text-indigo-600 font-bold underline">Initialize Defaults</button>}
           </div>
           <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 border-l-4 border-l-amber-500">
               <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider mb-1">Pending Indents</h3>
               <div className="text-3xl font-black text-slate-800">4 <span className="text-sm font-medium text-amber-600">Awaiting Approval</span></div>
           </div>
           <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 border-l-4 border-l-rose-500">
               <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider mb-1">Critical Expiry</h3>
               <div className="text-3xl font-black text-slate-800">12 <span className="text-sm font-medium text-rose-500">Items (Next 30 Days)</span></div>
           </div>
           <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 border-l-4 border-l-indigo-500">
               <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider mb-1">Transit Issues</h3>
               <div className="text-3xl font-black text-slate-800">3 <span className="text-sm font-medium text-indigo-500">Awaiting Acceptance</span></div>
           </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex gap-2 p-1.5 bg-white border border-slate-200 rounded-2xl w-fit mb-6 shadow-sm overflow-x-auto whitespace-nowrap">
           <button onClick={() => setActiveTab('overview')} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition ${activeTab === 'overview' ? 'bg-indigo-50 text-indigo-700 shadow-sm border border-indigo-100' : 'text-slate-500 hover:bg-slate-50'}`}><Activity size={16}/> Stock Overview</button>
           <button onClick={() => setActiveTab('inward')} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition ${activeTab === 'inward' ? 'bg-indigo-50 text-indigo-700 shadow-sm border border-indigo-100' : 'text-slate-500 hover:bg-slate-50'}`}><PlusCircle size={16}/> Inward & Opening Balance</button>
           <button onClick={() => setActiveTab('indents')} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition ${activeTab === 'indents' ? 'bg-indigo-50 text-indigo-700 shadow-sm border border-indigo-100' : 'text-slate-500 hover:bg-slate-50'}`}><ArrowRightLeft size={16}/> Indents & Issuing</button>
           <button onClick={() => setActiveTab('transit')} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition ${activeTab === 'transit' ? 'bg-indigo-50 text-indigo-700 shadow-sm border border-indigo-100' : 'text-slate-500 hover:bg-slate-50'}`}><CheckSquare size={16}/> Transit & Acceptances</button>
           <button onClick={() => setActiveTab('scrap')} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition ${activeTab === 'scrap' ? 'bg-indigo-50 text-indigo-700 shadow-sm border border-indigo-100' : 'text-slate-500 hover:bg-slate-50'}`}><FileWarning size={16}/> Adjustments & Scrap</button>
           <button onClick={() => setActiveTab('gatepass')} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition ${activeTab === 'gatepass' ? 'bg-indigo-50 text-indigo-700 shadow-sm border border-indigo-100' : 'text-slate-500 hover:bg-slate-50'}`}><Truck size={16}/> Returns & Gatepass</button>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm min-h-[500px]">
           {activeTab === 'overview' && (
              <div className="p-8">
                  <div className="flex items-center justify-between gap-4 mb-6">
                      <div className="flex items-center gap-2">
                          <select className="border-2 border-slate-200 rounded-lg px-4 py-2 font-bold text-slate-700 outline-none focus:border-indigo-500">
                              <option>Main Central Store</option>
                              <option>Pharmacy Retail</option>
                              <option>ICU Sublet</option>
                          </select>
                          <input type="text" placeholder="Search item, batch or code..." className="border-2 border-slate-200 rounded-lg px-4 py-2 font-medium w-64 outline-none focus:border-indigo-500" />
                      </div>
                      <div className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-500 rounded-lg border border-slate-200">
                          <Barcode size={20} />
                          <input type="text" placeholder="Scan Barcode (SKU/Batch)..." className="bg-transparent outline-none w-48 font-mono text-sm placeholder:font-sans" />
                      </div>
                  </div>
                  <table className="w-full text-left">
                     <thead>
                         <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider font-bold">
                             <th className="p-4 border-b">Item Code</th>
                             <th className="p-4 border-b">Consumable Name</th>
                             <th className="p-4 border-b">Batch Number</th>
                             <th className="p-4 border-b">Expiry (FEFO)</th>
                             <th className="p-4 border-b text-right">Available Qty</th>
                         </tr>
                     </thead>
                     <tbody className="divide-y divide-slate-100">
                         <tr className="hover:bg-slate-50">
                             <td className="p-4 font-mono text-xs text-slate-500">ITM-7701</td>
                             <td className="p-4 font-bold text-slate-800">Ceftriaxone 1g Injection (Vial)</td>
                             <td className="p-4 font-mono text-sm">BAT-29910</td>
                             <td className="p-4 font-medium text-slate-600">Nov 15, 2026</td>
                             <td className="p-4 font-black text-right text-slate-700">450</td>
                         </tr>
                         <tr className="hover:bg-slate-50">
                             <td className="p-4 font-mono text-xs text-slate-500">ITM-8192</td>
                             <td className="p-4 font-bold text-slate-800">Surgical Gloves Size 7 (Box)</td>
                             <td className="p-4 font-mono text-sm">GLV-001X</td>
                             <td className="p-4 font-medium text-rose-500 flex items-center gap-1"><AlertTriangle size={14}/> May 02, 2026</td>
                             <td className="p-4 font-black text-right text-slate-700">12</td>
                         </tr>
                         <tr className="hover:bg-slate-50">
                             <td className="p-4 font-mono text-xs text-slate-500">ITM-9922</td>
                             <td className="p-4 font-bold text-slate-800">Blood Collection Tubes EDC (Tray)</td>
                             <td className="p-4 font-mono text-sm">BCT-202X</td>
                             <td className="p-4 font-medium text-slate-600">Jan 10, 2027</td>
                             <td className="p-4 font-black text-right text-slate-700">80</td>
                         </tr>
                     </tbody>
                  </table>
              </div>
           )}

           {activeTab === 'inward' && (
              <div className="p-8">
                  <h2 className="text-xl font-black text-slate-800 border-b pb-4 mb-6 flex items-center gap-2">
                      <PlusCircle size={20} className="text-emerald-500"/> Goods Receipt & Opening Balance Initialization
                  </h2>
                  <div className="flex gap-8">
                      <div className="w-1/3 bg-slate-50 rounded-2xl border border-slate-200 p-6">
                          <h3 className="font-bold text-slate-700 mb-4">Stock Entry Workflow</h3>
                          <p className="text-sm text-slate-500 mb-4">Use this interface to initialize physical opening balances for a new store, or receive inbound procurement goods from an external supplier (GRN).</p>
                          <select className="w-full p-3 border rounded-xl bg-white mb-4 shadow-sm font-bold">
                              <option>Entry Type: Opening Balance</option>
                              <option>Entry Type: Supplier GRN</option>
                          </select>
                          <select className="w-full p-3 border rounded-xl bg-white mb-4 shadow-sm">
                              <option>Receiving Store: Main Central Store</option>
                              <option>Receiving Store: Pharmacy Retail</option>
                          </select>
                      </div>
                      
                      <div className="w-2/3">
                          <div className="bg-slate-50 border border-slate-200 rounded-xl overflow-hidden mb-6">
                              <div className="bg-white p-4 border-b flex justify-between items-center gap-4">
                                  <input type="text" placeholder="Search Master Catalog Items..." className="flex-1 p-2 outline-none" />
                                  <button className="bg-indigo-50 text-indigo-600 font-bold px-4 py-2 rounded">Scan Barcode</button>
                              </div>
                              <div className="p-6 grid grid-cols-2 gap-4">
                                  <div className="col-span-2">
                                      <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Selected Item</label>
                                      <select className="w-full p-3 border rounded-lg bg-white font-bold text-slate-800">
                                          <option>Ceftriaxone 1g Injection (Vial) - ITM-7701</option>
                                          <option>Paracetamol 500mg (Tablet) - ITM-4211</option>
                                      </select>
                                  </div>
                                  <div>
                                      <label className="text-xs font-bold text-slate-500 uppercase block mb-1">New Batch Number</label>
                                      <input type="text" placeholder="e.g. BAT-29910" className="w-full p-3 border rounded-lg bg-white font-mono" />
                                  </div>
                                  <div>
                                      <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Expiry Date (FEFO)</label>
                                      <input type="date" className="w-full p-3 border rounded-lg bg-white" />
                                  </div>
                                  <div>
                                      <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Physical Quantity</label>
                                      <input type="number" placeholder="Enter count..." className="w-full p-3 border rounded-lg bg-white font-bold" />
                                  </div>
                                  <div>
                                      <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Unit Purchase Price</label>
                                      <input type="number" placeholder="0.00" className="w-full p-3 border rounded-lg bg-white" />
                                  </div>
                              </div>
                          </div>
                          {!stockAdded ? (
                              <button onClick={() => { setStockAdded(true); alert("Opening balance successfully added. Stock ledgers are now active."); }} className="w-full bg-emerald-600 text-white font-bold py-4 rounded-xl shadow-md hover:bg-emerald-700 flex justify-center items-center gap-2">
                                  <PlusCircle size={20} /> Add to Stock Ledger
                              </button>
                          ) : (
                              <div className="w-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold p-4 rounded-xl text-center">
                                  Item initialization successful! The physical quantity is now strictly tracked in the FEFO Ledger.
                              </div>
                          )}
                      </div>
                  </div>
              </div>
           )}

           {activeTab === 'indents' && (
              <div className="grid grid-cols-5 h-full min-h-[500px]">
                 <div className="col-span-2 bg-slate-50 border-r border-slate-200 p-4 overflow-y-auto">
                     <h3 className="font-bold text-slate-500 uppercase text-xs mb-4">Pending Requests (Indents)</h3>
                     <div className="bg-white border-2 border-indigo-500 rounded-xl p-4 shadow-sm mb-3 cursor-pointer">
                         <div className="flex justify-between items-center mb-2"><span className="text-xs font-black text-indigo-600 bg-indigo-50 px-2 rounded uppercase">Priority</span><span className="font-mono text-xs text-slate-400">IND-88F1A</span></div>
                         <h4 className="font-bold text-slate-800">From: ICU Sublet</h4>
                         <p className="text-xs text-slate-500 font-medium mt-1">Requested 12 items • Pending Issue</p>
                     </div>
                 </div>
                 <div className="col-span-3 p-8">
                     <h2 className="text-xl font-black text-slate-800 border-b pb-4 mb-4">Process Material Issue (IND-88F1A)</h2>
                     <p className="text-slate-500 text-sm mb-6">Select batches for the requested items ensuring FEFO (First-Expiry-First-Out) methodology.</p>
                     
                     <div className="border rounded-xl mb-4 overflow-hidden">
                        <div className="bg-slate-50 p-3 border-b flex justify-between items-center"><span className="font-bold text-slate-700">Propofol 1% 20ml Vial</span> <span className="bg-rose-100 text-rose-700 text-xs px-2 rounded-full font-bold">Req: 50</span></div>
                        <div className="p-4">
                           <div className="flex items-center gap-4 text-sm mb-2">
                               <input type="radio" name="b1" defaultChecked /> <span className="font-mono">BAT-PRF-11</span> (Exp: May 2026) <span className="ml-auto font-bold text-emerald-600">Avail: 120</span>
                           </div>
                           <div className="flex items-center gap-4 text-sm opacity-50">
                               <input type="radio" name="b1" disabled /> <span className="font-mono">BAT-PRF-25</span> (Exp: Oct 2027) <span className="ml-auto font-bold text-slate-500">Avail: 300</span>
                           </div>
                        </div>
                     </div>
                     {!indentIssued ? (
                        <button onClick={() => { setIndentIssued(true); alert("Material picked and successfully dispatched to ICU Sublet."); }} className="w-full bg-emerald-600 text-white font-bold py-3 rounded-xl shadow mt-4 flex items-center justify-center gap-2 hover:bg-emerald-700">
                           <ArrowRightLeft size={18}/> Dispatch Issue to ICU
                        </button>
                     ) : (
                        <div className="w-full bg-emerald-50 border border-emerald-200 text-emerald-800 font-bold py-3 rounded-xl flex items-center justify-center gap-2 mt-4">
                           <Package size={18}/> Issue successfully dispatched & awaiting receiving confirmation.
                        </div>
                     )}
                 </div>
              </div>
           )}

           {activeTab === 'scrap' && (
              <div className="p-8">
                  <h2 className="text-xl font-black text-slate-800 border-b pb-4 mb-4 flex items-center gap-2">
                      <FileWarning size={20} className="text-rose-500"/> Submit Variance or Scrap Request (Physical Audit)
                  </h2>
                  <div className="grid grid-cols-2 gap-6 mb-6">
                      <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
                          <label className="text-sm font-bold text-slate-600 uppercase mb-2 block">Select Item</label>
                          <select className="w-full p-3 border rounded-xl bg-white mb-4">
                              <option>Surgical Gloves Size 7 (Box) - ITM-8192</option>
                              <option>Propofol 1% 20ml (Vial) - ITM-3011</option>
                          </select>
                          <label className="text-sm font-bold text-slate-600 uppercase mb-2 block">Select Batch</label>
                          <select className="w-full p-3 border rounded-xl bg-white">
                              <option>BAT-GLV-001X (Avail: 12, Exp: May 2026)</option>
                          </select>
                      </div>
                      <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
                         <div className="flex gap-4 mb-4">
                             <div className="flex-1">
                                 <label className="text-sm font-bold text-slate-600 uppercase mb-2 block">System Qty</label>
                                 <input type="number" readOnly value="12" className="w-full p-3 border rounded-xl bg-slate-100 font-mono text-slate-500" />
                             </div>
                             <div className="flex-1">
                                 <label className="text-sm font-bold text-slate-600 uppercase mb-2 block">Physical/Scrap Qty</label>
                                 <input type="number" placeholder="Enter actual count" className="w-full p-3 border rounded-xl bg-white font-bold" />
                             </div>
                         </div>
                         <label className="text-sm font-bold text-slate-600 uppercase mb-2 block">Reason for Adjustment / Scrap</label>
                         <textarea value={scrapReason} onChange={(e) => setScrapReason(e.target.value)} rows={3} className="w-full p-3 border rounded-xl bg-white resize-none" placeholder="e.g. Expired, damaged in transit, counting error..."></textarea>
                      </div>
                  </div>
                  
                  {!scrapSubmitted ? (
                      <button onClick={() => {
                          if (!scrapReason) { alert("Please provide a valid reason for the scrap/adjustment auto-ledger."); return; }
                          setScrapSubmitted(true);
                      }} className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold p-4 rounded-xl flex justify-center gap-2 items-center">
                          <AlertTriangle size={18} /> Submit Request for Administration Approval
                      </button>
                  ) : (
                      <div className="w-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold p-4 rounded-xl text-center">
                          Successfully routed to Supply Chain Administrator approval pipeline! The ledger variance is pending authorization.
                      </div>
                  )}
              </div>
           )}
           {activeTab === 'transit' && (
              <div className="p-8">
                  <h2 className="text-xl font-black text-slate-800 border-b pb-4 mb-6 flex items-center gap-2">
                      <CheckSquare size={20} className="text-indigo-500"/> Material Acceptance Workflow
                  </h2>
                  <div className="grid grid-cols-3 gap-6">
                      <div className="col-span-1 bg-slate-50 border border-slate-200 p-4 rounded-xl">
                          <h3 className="font-bold text-slate-500 text-xs uppercase mb-4">Inbound Shipments</h3>
                          <div className="bg-white border-2 border-amber-400 p-4 rounded-xl shadow-sm cursor-pointer">
                              <div className="flex justify-between items-center mb-1">
                                  <span className="font-mono text-xs text-slate-500">ISS-299A1</span>
                                  <span className="text-xs font-black text-amber-600 bg-amber-50 px-2 rounded">TRANSIT</span>
                              </div>
                              <h4 className="font-bold text-slate-800">Ceftriaxone 1g (450 Vials)</h4>
                              <p className="text-xs text-slate-500 mt-1">From: Main Central Store</p>
                          </div>
                      </div>
                      <div className="col-span-2">
                          <div className="border border-slate-200 rounded-xl overflow-hidden mb-6">
                              <div className="bg-slate-50 p-4 border-b font-bold text-slate-800 flex justify-between">
                                  Verify Received Quantity
                                  <span className="font-mono text-xs bg-white px-2 py-1 border rounded text-slate-500">Barcode / RFID Scanner Active</span>
                              </div>
                              <div className="p-6 bg-white flex items-center gap-6">
                                  <div className="flex-1">
                                      <p className="text-sm text-slate-500 font-bold uppercase mb-1">Dispatched Batch</p>
                                      <p className="font-mono text-lg text-slate-800">BAT-29910</p>
                                  </div>
                                  <div className="flex-1">
                                      <p className="text-sm text-slate-500 font-bold uppercase mb-1">Manifest Qty</p>
                                      <p className="font-bold text-lg text-slate-700">450</p>
                                  </div>
                                  <div className="flex-1">
                                      <p className="text-sm text-slate-500 font-bold uppercase mb-1">Physical Verification</p>
                                      <input type="number" defaultValue="450" className="w-full border-2 border-emerald-500 p-2 rounded-lg font-bold text-lg text-emerald-700 bg-emerald-50" />
                                  </div>
                              </div>
                          </div>
                          {!transitAccepted ? (
                             <button onClick={() => setTransitAccepted(true)} className="w-full bg-indigo-600 text-white font-bold py-4 rounded-xl hover:bg-indigo-700 shadow flex justify-center gap-2">
                                 <CheckSquare size={20}/> Confirm Acceptance & Update Stock Ledgers
                             </button>
                          ) : (
                             <div className="w-full bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold py-4 rounded-xl text-center">
                                 Stock Successfully Received. ICU Sublet ledger updated with 450 units natively.
                             </div>
                          )}
                      </div>
                  </div>
              </div>
           )}

           {activeTab === 'gatepass' && (
              <div className="p-8">
                  <h2 className="text-xl font-black text-slate-800 border-b pb-4 mb-6 flex items-center gap-2">
                      <Truck size={20} className="text-indigo-500"/> Material Returns & Returnable Gatepass
                  </h2>
                  <div className="grid grid-cols-2 gap-8">
                      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
                          <h3 className="font-bold text-slate-700 mb-4 border-b pb-2">Departmental Material Return</h3>
                          <p className="text-sm text-slate-500 mb-4">Return unused or excess stock from sub-stores back to the Main Central Store. Reverses the issue transaction ledger.</p>
                          <select className="w-full p-3 border rounded-xl bg-white mb-4">
                              <option>Select Original Issue ID to Reverse...</option>
                              <option>ISS-992B - Surgical Gloves</option>
                          </select>
                          <input type="number" placeholder="Quantity to Return" className="w-full p-3 border rounded-xl bg-white mb-4" />
                          <button className="w-full bg-indigo-100 text-indigo-700 font-bold py-3 rounded-xl hover:bg-indigo-200">Process Internal Return</button>
                      </div>
                      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 border-t-4 border-t-indigo-500">
                          <h3 className="font-bold text-slate-700 mb-4 border-b pb-2">Vendor Returnable Gatepass</h3>
                          <p className="text-sm text-slate-500 mb-4">Generate an external Gatepass document for replacing defective/expired batches with the supplier/vendor.</p>
                          <select className="w-full p-3 border rounded-xl bg-white mb-4">
                              <option>Select Approved Scrap / Defective Item...</option>
                              <option>BAT-GLV-001X - 12 Qty (Defective)</option>
                          </select>
                          <textarea className="w-full p-3 border rounded-xl bg-white mb-4 resize-none" rows={2} placeholder="Gatepass conditions & driver details..."></textarea>
                          {!gatepassGenerated ? (
                             <button onClick={() => setGatepassGenerated(true)} className="w-full bg-indigo-600 text-white font-bold py-3 rounded-xl shadow-md hover:bg-indigo-700 flex justify-center gap-2">
                                <Truck size={18}/> Generate External Gatepass Document
                             </button>
                          ) : (
                             <div className="w-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold py-3 rounded-xl text-center">
                                Gatepass RGP-991A Generated. Ready to Print for Logistics.
                             </div>
                          )}
                      </div>
                  </div>
              </div>
           )}
        </div>
      </div>
    </div>
  )
}
