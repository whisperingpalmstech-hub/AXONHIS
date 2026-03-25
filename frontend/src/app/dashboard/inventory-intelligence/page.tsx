"use client";

import React, { useState, useEffect } from "react";
import { 
  BarChart4, AlertTriangle, Clock, Layers, PackagePlus, ShieldAlert,
  Activity, ArrowRightLeft, FolderKanban, Search, Plus, CheckCircle 
} from "lucide-react";

// Formatter without external date libs
const formatDate = (dateString: string) => {
  const d = new Date(dateString);
  return d.toLocaleDateString("en-GB", { day: '2-digit', month: 'short', year: 'numeric' });
};

interface Alert {
  id: string;
  alert_type: string;
  message: string;
  store_id: string;
  alert_date: string;
  status: string;
}

interface Kit {
  id: string;
  kit_name: string;
  description: string;
  status?: string;
  kit_components: any[];
}

export default function InventoryIntelligenceWorkbench() {
  const [activeTab, setActiveTab] = useState("Alerts & Intelligence");
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [kits, setKits] = useState<Kit[]>([]);
  const [loading, setLoading] = useState(true);

  // New Kit Form State
  const [newKitName, setNewKitName] = useState("");
  const [newKitDesc, setNewKitDesc] = useState("");

  // Manage Kit Item State
  const [managingKit, setManagingKit] = useState<Kit | null>(null);
  const [tempDrug, setTempDrug] = useState("");
  const [tempQty, setTempQty] = useState("");

  const fetchIntelligenceData = async () => {
    setLoading(true);
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const [alRes, kitRes] = await Promise.all([
        fetch(`${u}/api/v1/pharmacy/inventory-intelligence/alerts`),
        fetch(`${u}/api/v1/pharmacy/inventory-intelligence/kits`)
      ]);
      if (alRes.ok) setAlerts(await alRes.json());
      if (kitRes.ok) setKits(await kitRes.json());
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchIntelligenceData();
  }, [activeTab]);

  const addKitComponent = async () => {
    if (!managingKit || !tempDrug || !tempQty) return alert("Select drug and quantity");
    
    // Copy the existing array
    const currentComponents = Array.isArray(managingKit.kit_components) ? [...managingKit.kit_components] : [];
    
    // Check for duplicate
    if(currentComponents.find(c => c.drug_id === tempDrug)) {
      return alert("Drug already added to this kit");
    }

    currentComponents.push({
      drug_id: tempDrug,
      quantity: parseFloat(tempQty)
    });

    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const rs = await fetch(`${u}/api/v1/pharmacy/inventory-intelligence/kits/${managingKit.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentComponents)
      });
      if (rs.ok) {
        setTempDrug("");
        setTempQty("");
        const updatedKit = await rs.json();
        setManagingKit(updatedKit); // update local modal context automatically!
        fetchIntelligenceData(); // refresh background dashboard list context 
      } else {
        alert("Failed to patch kit");
      }
    } catch (e) {
      alert("Error saving component");
    }
  };

  const removeKitComponent = async (drugName: string) => {
    if(!managingKit) return;
    const currentComponents = managingKit.kit_components.filter((c: any) => c.drug_id !== drugName);
    
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const rs = await fetch(`${u}/api/v1/pharmacy/inventory-intelligence/kits/${managingKit.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentComponents)
      });
      if (rs.ok) {
        const updatedKit = await rs.json();
        setManagingKit(updatedKit);
        fetchIntelligenceData();
      }
    } catch(e) {}
  };

  const triggerExpiryScan = async () => {
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      await fetch(`${u}/api/v1/pharmacy/inventory-intelligence/analysis/expiries`, { method: "POST" });
      alert("Deep scan for expiring/near-expiry and dead-stock triggered.");
      fetchIntelligenceData();
    } catch (e) {
      alert("Failed to run analyzer.");
    }
  };

  const createKit = async () => {
    if (!newKitName) return alert("Kit Name required");
    try {
      const u = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      const rs = await fetch(`${u}/api/v1/pharmacy/inventory-intelligence/kits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kit_name: newKitName,
          description: newKitDesc,
          kit_components: [] // Starting with empty config for demo mock
        })
      });
      if (rs.ok) {
        alert("Predefined Item Kit created successfully!");
        setNewKitName(""); setNewKitDesc("");
        fetchIntelligenceData();
      }
    } catch (e) {
      alert("Failed to create kit");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-6 font-sans relative">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-indigo-900/10">
          <div>
            <h1 className="text-3xl font-extrabold flex items-center gap-3 text-indigo-900">
              <BarChart4 className="w-8 h-8 text-indigo-600" />
              Inventory Intelligence Matrix
            </h1>
            <p className="text-slate-500 mt-2 font-medium">ABC / VED Analysis, Reorders, Kits & Expiry Controls</p>
          </div>
          <button 
            onClick={triggerExpiryScan}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg shadow-lg shadow-indigo-200 transition-all font-semibold"
          >
            <ShieldAlert className="w-5 h-5" /> Trigger Deep Scan
          </button>
        </div>

        {/* Tab Nav */}
        <div className="flex space-x-2 mb-8 bg-white shadow-sm p-1.5 rounded-xl border border-slate-200 w-fit">
          {["Alerts & Intelligence", "ABC/VED Strategy", "Item Kits Bundle", "Multi-Store Transfers"].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-all ${
                activeTab === tab 
                  ? "bg-indigo-50 text-indigo-700 shadow-sm border border-indigo-200" 
                  : "text-slate-500 hover:text-slate-700 hover:bg-slate-100/50"
              }`}
            >
              {tab === "Alerts & Intelligence" && <AlertTriangle className="w-4 h-4 inline mr-2" />}
              {tab === "ABC/VED Strategy" && <Activity className="w-4 h-4 inline mr-2" />}
              {tab === "Item Kits Bundle" && <PackagePlus className="w-4 h-4 inline mr-2" />}
              {tab === "Multi-Store Transfers" && <ArrowRightLeft className="w-4 h-4 inline mr-2" />}
              {tab}
            </button>
          ))}
        </div>

        {/* Dashboard Content */}
        
        {activeTab === "Alerts & Intelligence" && (
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 lg:col-span-4">
              <div className="bg-white border text-center p-8 rounded-2xl shadow-sm h-full flex flex-col justify-center border-rose-200">
                <AlertTriangle className="w-16 h-16 text-rose-500 mx-auto mb-4" />
                <h3 className="text-5xl font-black text-slate-800">{alerts.length}</h3>
                <p className="text-slate-500 font-medium uppercase tracking-wider mt-2">Active Risk Alerts</p>
                <div className="mt-8 flex gap-2 justify-center">
                  <span className="bg-amber-100 text-amber-700 font-bold px-3 py-1 rounded text-xs">Expiries</span>
                  <span className="bg-rose-100 text-rose-700 font-bold px-3 py-1 rounded text-xs">Reorders</span>
                </div>
              </div>
            </div>

            <div className="col-span-12 lg:col-span-8">
              <div className="bg-white border border-slate-200 rounded-2xl h-[500px] overflow-y-auto shadow-sm">
                <div className="sticky top-0 bg-slate-50 border-b border-slate-200 px-6 py-4 font-bold text-slate-700 flex items-center justify-between">
                  <span>Critical Action Queue</span>
                  <Search className="w-5 h-5 text-slate-400" />
                </div>
                
                {loading ? (
                  <div className="p-8 text-center text-indigo-500 font-medium animate-pulse">Scanning matrix...</div>
                ) : alerts.length === 0 ? (
                  <div className="p-16 text-center flex flex-col items-center">
                    <CheckCircle className="w-12 h-12 text-emerald-400 mb-4" />
                    <h4 className="text-xl font-bold text-slate-700">All Clear</h4>
                    <p className="text-slate-500 mt-2">No reorder deficits or near-expiry batches detected.</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {alerts.map(a => (
                      <div key={a.id} className="p-6 hover:bg-slate-50 transition-colors flex items-start gap-4">
                        <div className={`p-3 rounded-full ${a.alert_type === 'EXPIRY' ? 'bg-amber-100 text-amber-600' : 'bg-rose-100 text-rose-600'}`}>
                          {a.alert_type === 'EXPIRY' ? <Clock className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-bold text-slate-800 uppercase tracking-tight text-sm mb-1">{a.alert_type} ALERT <span className="opacity-50 mx-2">•</span> Store: {a.store_id}</h4>
                          <p className="text-slate-600 font-medium">{a.message}</p>
                          <div className="mt-2 text-xs text-slate-400 font-medium">Logged: {formatDate(a.alert_date)}</div>
                        </div>
                        <button className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-bold text-slate-600 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 transition-colors">
                          Resolve
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "Item Kits Bundle" && (
          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-12 lg:col-span-5 space-y-6">
              <div className="bg-white p-6 border border-slate-200 rounded-2xl shadow-sm">
                <h3 className="font-bold text-lg mb-4 text-indigo-900 border-b pb-3">Configure New Trauma/Procedure Kit</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-600 mb-2">Kit Nomenclature / Purpose</label>
                    <input type="text" value={newKitName} onChange={e => setNewKitName(e.target.value)}
                      className="w-full border-2 border-slate-200 p-3 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 outline-none text-slate-800 font-medium transition-all"
                      placeholder="e.g. Post-Op Hemorrhage Set" />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-600 mb-2">Clinical Guidelines</label>
                    <textarea value={newKitDesc} onChange={e => setNewKitDesc(e.target.value)}
                      className="w-full border-2 border-slate-200 p-3 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 outline-none h-28 text-slate-800 font-medium transition-all"
                      placeholder="Instructions for usage..." />
                  </div>
                  
                  <button onClick={createKit} className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white p-3 rounded-xl font-bold shadow-lg shadow-indigo-200/50 mt-4 transition-all">
                    <Plus className="w-5 h-5"/> Package Template Kit
                  </button>
                </div>
              </div>
            </div>

            <div className="col-span-12 lg:col-span-7">
              <div className="grid grid-cols-2 gap-4">
                {kits.length === 0 ? (
                  <div className="col-span-2 p-12 text-center border-2 border-dashed border-slate-300 rounded-2xl text-slate-500 font-medium bg-white/50">
                    No custom preset kits configured.
                  </div>
                ) : (
                  kits.map(k => (
                    <div key={k.id} className="bg-white border-2 border-slate-100 p-6 rounded-2xl shadow-sm relative overflow-hidden group hover:border-indigo-200 transition-colors">
                      <div className="absolute -right-6 -top-6 text-slate-50 opacity-50 group-hover:opacity-100 transition-opacity">
                        <FolderKanban className="w-32 h-32" />
                      </div>
                      <div className="relative z-10">
                        <div className="flex items-center gap-2 text-indigo-600 mb-3">
                          <PackagePlus className="w-5 h-5" />
                          <span className="text-xs font-bold uppercase tracking-widest px-2 py-0.5 bg-indigo-50 rounded-full">{k.status}</span>
                        </div>
                        <h4 className="text-xl font-bold text-slate-800 mb-2 leading-tight pr-8">{k.kit_name}</h4>
                        <p className="text-sm text-slate-500 font-medium min-h-[40px]">{k.description || "System configured combo kit for rapid dispensing."}</p>
                        <div className="mt-6 flex justify-between items-center">
                          <button 
                            onClick={() => setManagingKit(k)}
                            className="text-sm font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 group">
                            Manage Items <ArrowRightLeft className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                          </button>
                          <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-md">{k.kit_components?.length || 0} Drugs</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Dummy/Mock Data Panels for other sub-modules requested */}
        {activeTab === "ABC/VED Strategy" && (
           <div className="bg-gradient-to-br from-indigo-900 via-slate-800 to-indigo-950 p-12 rounded-3xl shadow-xl text-center border border-indigo-700 relative overflow-hidden">
             <Layers className="w-32 h-32 mx-auto text-indigo-500/20 absolute -bottom-10 -right-5 pointer-events-none" />
             <Activity className="w-16 h-16 text-indigo-400 mx-auto mb-6 opacity-90" />
             <h2 className="text-4xl font-extrabold text-white mb-4">Dead Stock & Value Matrix Analytics</h2>
             <p className="text-indigo-200 max-w-2xl mx-auto font-medium text-lg leading-relaxed">
               ABC (Value) and VED (Criticality) analysis runs as an automated background CRON. The machine learning model prevents Capital freeze by identifying "C-Desirable" dead inventory.
             </p>
             <button className="mt-8 bg-indigo-500 hover:bg-indigo-400 text-white font-bold py-3 px-8 rounded-xl shadow-lg shadow-indigo-500/30 transition-all border border-indigo-400">View Heatmap</button>
           </div>
        )}

        {activeTab === "Multi-Store Transfers" && (
          <div className="bg-white p-12 rounded-3xl shadow-sm text-center border-2 border-dashed border-slate-300">
             <ArrowRightLeft className="w-16 h-16 text-slate-300 mx-auto mb-4" />
             <h2 className="text-2xl font-bold text-slate-700">Cross-Hospital Batch Indent Submodule</h2>
             <p className="text-slate-500 mt-2 font-medium">Tracks massive stock loads seamlessly between the Central Hub, Ward Pharmacies, and ICU Depots.</p>
          </div>
        )}

      </div>

      {/* Item Management Modal Overlay */}
      {managingKit && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl border border-slate-200 overflow-hidden">
            <div className="bg-indigo-900 p-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FolderKanban className="text-indigo-400 w-8 h-8" />
                <h3 className="text-2xl font-black text-white">{managingKit.kit_name} Editor</h3>
              </div>
              <button onClick={() => setManagingKit(null)} className="text-indigo-200 hover:text-white font-bold">Close X</button>
            </div>
            
            <div className="p-8">
              <p className="text-slate-500 mb-6 font-medium">Add medications and pre-defined quantities to this kit. Upon prescription or emergency dispensing, these constituents are automatically mapped and deducted.</p>
              
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
                 <h4 className="font-bold text-slate-700 mb-3 text-sm tracking-wider uppercase">Search Formulary</h4>
                 <div className="flex gap-2">
                   <input type="text" placeholder="Start typing medication name..." 
                     value={tempDrug} onChange={e => setTempDrug(e.target.value)}
                     className="flex-1 p-3 border border-slate-200 rounded-lg outline-none focus:border-indigo-400"/>
                   <input type="number" placeholder="Qty" 
                     value={tempQty} onChange={e => setTempQty(e.target.value)}
                     className="w-24 p-3 border border-slate-200 rounded-lg outline-none focus:border-indigo-400" />
                   <button onClick={addKitComponent} className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-4 rounded-lg flex items-center gap-1 shadow-md shadow-emerald-200"><Plus className="w-5 h-5"/> Add</button>
                 </div>
              </div>

              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-left bg-white">
                  <thead className="bg-slate-100 text-slate-600 font-bold text-sm uppercase">
                    <tr>
                      <th className="p-4 py-3">Medication Composition</th>
                      <th className="p-4 py-3 text-center">Standard Qty</th>
                      <th className="p-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {managingKit.kit_components && managingKit.kit_components.length > 0 ? (
                      managingKit.kit_components.map((c, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          <td className="p-4 font-bold text-indigo-900">{c.drug_id}</td>
                          <td className="p-4 text-center font-bold">{c.quantity}</td>
                          <td className="p-4 text-right">
                            <button onClick={() => removeKitComponent(c.drug_id)} className="text-rose-500 font-bold hover:underline text-sm">Remove</button>
                          </td>
                        </tr>
                      ))
                    ) : (
                       <tr>
                         <td colSpan={3} className="p-8 text-center text-slate-400 font-medium">This kit configuration is currently empty. Add constituent drugs above.</td>
                       </tr>
                    )}
                  </tbody>
                </table>
              </div>
              
              <div className="mt-8 flex justify-end gap-3">
                 <button onClick={() => setManagingKit(null)} className="px-5 py-2.5 font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition-all">Done</button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
