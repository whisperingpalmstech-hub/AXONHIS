"use client";

import React, { useState, useEffect } from "react";
import { 
  Package, 
  Activity, 
  AlertTriangle, 
  Layers, 
  ArrowRightLeft, 
  FileWarning, 
  RefreshCcw, 
  CheckSquare, 
  Truck, 
  Barcode, 
  PlusCircle,
  Building2,
  Calendar,
  Search,
  ChevronRight,
  ClipboardList,
  AlertCircle
} from "lucide-react";
import { TopNav } from "@/components/ui/TopNav";
import { api } from "@/lib/api";

type Store = {
  id: string;
  name: string;
  store_type: string;
  is_active: boolean;
};

type StockLevel = {
  name: string;
  item_code: string;
  category: string;
  uom: string;
  total_quantity: number;
};

type ExpiryAlert = {
  item_name: string;
  batch_number: string;
  expiry_date: string;
  quantity: number;
};

export default function InventoryDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [stores, setStores] = useState<Store[]>([]);
  const [stockLevels, setStockLevels] = useState<StockLevel[]>([]);
  const [expiryAlerts, setExpiryAlerts] = useState<ExpiryAlert[]>([]);
  const [indents, setIndents] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);
  const [selectedIndent, setSelectedIndent] = useState<any>(null);
  const [selectedIssue, setSelectedIssue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Inward Form State
  const [inwardForm, setInwardForm] = useState({
    store_id: "",
    item_name: "Master Item",
    item_code: "MASTER-" + Math.floor(Math.random()*1000),
    category: "General",
    uom: "Units",
    batch_number: "BAT-" + Math.floor(Math.random()*1000),
    expiry_date: "",
    quantity: 0,
    price: 0
  });

  const [items, setItems] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [indentModalOpen, setIndentModalOpen] = useState(false);
  const [newIndent, setNewIndent] = useState({
    requesting_store_id: "",
    issuing_store_id: "",
    item_id: "",
    quantity: 0,
    justification: ""
  });

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [storesData, stockData, expiryData, indentsData, itemsData, issuesData, analyticsData] = await Promise.all([
        api.get<Store[]>('/inventory/stores'),
        api.get<StockLevel[]>('/inventory/stock-levels'),
        api.get<ExpiryAlert[]>('/inventory/expiry-alerts'),
        api.get<any[]>('/inventory/indents'),
        api.get<any[]>('/inventory/items'),
        api.get<any[]>('/inventory/issues'),
        api.get<any>('/inventory/analytics').catch(() => null)
      ]);
      setStores(Array.isArray(storesData) ? storesData : []);
      setStockLevels(Array.isArray(stockData) ? stockData : []);
      setExpiryAlerts(Array.isArray(expiryData) ? expiryData : []);
      setIndents(Array.isArray(indentsData) ? indentsData : []);
      setItems(Array.isArray(itemsData) ? itemsData : []);
      setIssues(Array.isArray(issuesData) ? issuesData : []);
      if (analyticsData) {
        setAnalytics(analyticsData);
        const realValue = analyticsData.abc_analysis.reduce((acc: number, curr: any) => acc + curr.value, 0);
        setTotalInventoryValue(realValue);
      } else {
        const value = (Array.isArray(stockData) ? stockData : []).reduce((acc: number, curr: any) => acc + (curr.total_quantity * 150), 0); // Mock fallback
        setTotalInventoryValue(value);
      }
    } catch (err) {
      console.error('Failed to fetch inventory data:', err);
    } finally {
      setLoading(false);
    }
  };

  const [totalInventoryValue, setTotalInventoryValue] = useState(0);
  const [ledgerHistory, setLedgerHistory] = useState<any[]>([]);
  const [ledgerModalOpen, setLedgerModalOpen] = useState(false);
  const [selectedLedgerItem, setSelectedLedgerItem] = useState<any>(null);

  const handleFetchLedgerHistory = async (item: any) => {
    try {
      setLoading(true);
      // We need the item.id. In stockLevels, the backend returns 'id' directly.
      const itemId = item.id || items.find(i => i.item_code === item.item_code)?.id;
      
      if (!itemId) {
        console.warn("Could not find ID for item:", item);
        alert("System syncing... please wait a moment and try again.");
        return;
      }
      
      const history = await api.get<any[]>(`/inventory/ledger-history/${itemId}`);
      setLedgerHistory(history);
      setSelectedLedgerItem(item); // Just use 'item' (from stockLevels) which has name and code
      setLedgerModalOpen(true);
    } catch (err) {
      console.error('Failed to fetch ledger history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedStores = async () => {
    try {
      alert("Initializing system stores... Please wait.");
      await api.post('/inventory/stores', { name: "Main Central Store", store_type: "MAIN" });
      await api.post('/inventory/stores', { name: "Pharmacy Retail", store_type: "PHARMACY" });
      await api.post('/inventory/stores', { name: "ICU Sublet", store_type: "WARD" });
      alert("System Initialized Successfully! Stores are now online.");
      fetchInitialData();
    } catch (err) {
      console.error('Failed to seed stores:', err);
      alert("Failed to initialize stores: " + err);
    }
  };

  const handleCreateIndentSubmit = async () => {
    try {
      if (!newIndent.requesting_store_id || !newIndent.issuing_store_id || !newIndent.item_id) {
        alert("Please fill all required fields");
        return;
      }
      setLoading(true);
      const res: any = await api.post('/inventory/indents', {
        requesting_store_id: newIndent.requesting_store_id,
        issuing_store_id: newIndent.issuing_store_id,
        justification: newIndent.justification || "Urgent Stock Gap fulfillment",
        items: [
          { item_id: newIndent.item_id, requested_quantity: Number(newIndent.quantity) }
        ]
      });
      alert("Indent Request Generated: " + res.indent_number);
      setIndentModalOpen(false);
      fetchInitialData();
    } catch (err) {
      console.error('Failed to create indent:', err);
      alert("Error creating indent: " + err);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteIssue = async () => {
    if (!selectedIndent) return;
    try {
      setLoading(true);
      const res: any = await api.post('/inventory/issues', {
        indent_id: selectedIndent.id,
        issuing_store_id: selectedIndent.issuing_store_id,
        receiving_store_id: selectedIndent.requesting_store_id,
        items: selectedIndent.items.map((itm: any) => ({
          item_id: itm.item_id,
          batch_record_id: "7701da52-16e0-47de-99c5-671c266a2b8e", // Demo placeholder; in prod selected by user
          issued_quantity: itm.requested_quantity
        }))
      });
      alert("Material Issue Generated: " + res.issue_number);
      setSelectedIndent(null);
      fetchInitialData();
    } catch (err) {
      console.error('Failed to issue material:', err);
      alert("Failed to issue: Check if stock exists in issuing store.");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveIndent = async (indentId: string) => {
    try {
      setLoading(true);
      await api.post(`/inventory/indents/${indentId}/approve`, {});
      alert("Indent Request Approved for fulfilment processing.");
      fetchInitialData();
    } catch (err) {
      console.error('Failed to approve indent:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePostStock = async () => {
    try {
      if (!inwardForm.store_id || inwardForm.quantity <= 0) {
        alert("Please fill all required fields (Store, Qty > 0)");
        return;
      }
      setLoading(true);
      
      const item: any = await api.post('/inventory/items', {
        name: inwardForm.item_name,
        item_code: inwardForm.item_code,
        category: inwardForm.category,
        uom: inwardForm.uom
      });
      
      await api.post('/inventory/opening-balance', {
        store_id: inwardForm.store_id,
        item_id: item.id,
        batch_number: inwardForm.batch_number,
        expiry_date: inwardForm.expiry_date || new Date(Date.now() + 365*24*60*60*1000).toISOString(),
        quantity: Number(inwardForm.quantity),
        purchase_price: Number(inwardForm.price)
      });
      
      alert("Stock Posted Successfully! Inventory levels updated.");
      setActiveTab('overview');
      fetchInitialData();
    } catch (err) {
      console.error('Failed to post stock:', err);
      alert("Error posting stock: " + err);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptTransit = async (issueId: string) => {
    try {
      setLoading(true);
      await api.post(`/inventory/issues/${issueId}/accept`, {});
      alert("Material Accepted! Stock levels in receiving store updated successfully.");
      setSelectedIssue(null);
      fetchInitialData();
    } catch (err) {
      console.error('Failed to accept transit:', err);
      alert("Failed to accept transit: " + err);
    } finally {
      setLoading(false);
    }
  };

  const [adjustmentForm, setAdjustmentForm] = useState({
    item_code: "",
    physical_qty: 0,
    reason: ""
  });

  const handleAdjustmentSubmit = async () => {
    try {
      if (!adjustmentForm.item_code || adjustmentForm.physical_qty < 0) {
        alert("Please select an item and enter physical quantity");
        return;
      }
      setLoading(true);
      
      const actualItem = items.find(i => i.item_code === adjustmentForm.item_code);
      if (!actualItem) {
        alert("Item not found in master catalog");
        return;
      }

      await api.post('/inventory/adjustments', {
        item_id: actualItem.id,
        store_id: stores[0]?.id, // Assuming main store for now, typically user's store
        physical_quantity: adjustmentForm.physical_qty,
        reason: adjustmentForm.reason || "Physical Adjustment Routine"
      });

      alert(`Stock Adjustment Logged: Physical count of ${adjustmentForm.item_code} adjusted to ${adjustmentForm.physical_qty}.`);
      fetchInitialData();
      setActiveTab('overview');
    } catch (err) {
      console.error('Adjustment failed:', err);
      alert("Adjustment failed to sync with the backend. Check network or logs.");
    } finally {
      setLoading(false);
    }
  };

  const filteredStock = stockLevels.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.item_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 font-sans antialiased text-slate-900">
      <TopNav title="Supply Chain Intelligence" />
      
      <div className="p-8 max-w-[1600px] mx-auto w-full space-y-8">
        
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-1">
            <h1 className="text-4xl font-black text-slate-900 tracking-tight flex items-center gap-4">
              <div className="bg-blue-600 p-2.5 rounded-2xl shadow-lg shadow-blue-200">
                <Package className="text-white w-8 h-8" />
              </div>
              INVENTORY CENTRAL
            </h1>
            <p className="text-slate-500 font-bold uppercase text-[10px] tracking-[0.2em] ml-1">
              Enterprise Resource Planning & Supply Chain Management
            </p>
          </div>
          
          <div className="flex items-center gap-3 relative z-50">
            <button 
              onClick={() => fetchInitialData()}
              disabled={loading}
              className="group flex items-center gap-2 px-6 py-3 bg-white border border-slate-200 text-slate-600 rounded-2xl font-black uppercase text-[10px] tracking-widest hover:bg-slate-50 transition-all shadow-sm active:scale-95 disabled:opacity-50"
            >
              <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Sync ERP
            </button>
            <button 
              onClick={() => setActiveTab('inward')}
              className="flex items-center gap-2 px-8 py-3 bg-slate-900 text-white rounded-2xl font-black uppercase text-[10px] tracking-widest shadow-xl transition-all hover:bg-slate-800 active:scale-95"
            >
              <PlusCircle className="w-4 h-4" />
              New Inward
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { label: "Stock Value", value: `₹${totalInventoryValue.toLocaleString()}`, status: "Current Assets", color: "emerald", icon: <Layers /> },
            { label: "Critical Stock", value: stockLevels.filter(s => s.total_quantity < 50).length, status: "Reorder Required", color: "rose", icon: <AlertTriangle /> },
            { label: "Near Expiry", value: expiryAlerts.length, status: "Next 90 Days", color: "amber", icon: <Calendar /> },
            { label: "Total Items", value: items.length, status: "In Catalog", color: "indigo", icon: <ClipboardList /> },
          ].map((kpi, i) => (
            <div key={i} className="bg-white p-6 rounded-[2.5rem] shadow-sm border border-slate-200 group hover:border-blue-200 transition-all">
              <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-2xl bg-${kpi.color}-50 text-${kpi.color}-600 group-hover:bg-blue-600 group-hover:text-white transition-all`}>
                  {React.cloneElement(kpi.icon as any, { size: 20 })}
                </div>
                <ChevronRight className="w-4 h-4 text-slate-300" />
              </div>
              <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{kpi.label}</h3>
              <div className="text-3xl font-black text-slate-900">{kpi.value}</div>
              <p className="text-[10px] font-bold mt-1 uppercase text-slate-400">{kpi.status}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-12 gap-8">
          <div className="col-span-12 lg:col-span-2 space-y-2">
            {[
              { id: "overview", label: "Stock Ledger", icon: <Layers /> },
              { id: "analytics", label: "Smart Analytics", icon: <Activity /> },
              { id: "inward", label: "Goods Receipt", icon: <PlusCircle /> },
              { id: "indents", label: "Store Indents", icon: <ArrowRightLeft /> },
              { id: "transit", label: "Transit Accept", icon: <CheckSquare /> },
              { id: "scrap", label: "Adjustments", icon: <FileWarning /> },
              { id: "gatepass", label: "Gatepass", icon: <Truck /> },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-5 py-4 rounded-[1.25rem] text-sm font-black uppercase tracking-wider transition-all ${
                  activeTab === tab.id 
                  ? "bg-blue-600 text-white shadow-lg" 
                  : "text-slate-500 hover:bg-white hover:text-blue-600"
                }`}
              >
                {React.cloneElement(tab.icon as any, { size: 18 })}
                {tab.label}
              </button>
            ))}
            
            {stores.length === 0 && (
              <div className="mt-8 p-6 bg-blue-50 rounded-[2.5rem] border border-blue-100">
                <p className="text-[10px] font-bold text-blue-700 uppercase leading-relaxed mb-3">No stores configured.</p>
                <button onClick={handleSeedStores} className="w-full py-2 bg-blue-600 text-white text-[10px] font-black uppercase rounded-xl">Init System</button>
              </div>
            )}
          </div>

          <div className="col-span-12 lg:col-span-10">
            <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden min-h-[600px]">
              
              {activeTab === 'overview' && (
                <div className="flex flex-col h-full">
                  <div className="p-8 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50/50">
                    <div>
                      <h2 className="text-2xl font-black text-slate-800 uppercase tracking-tight">Stock Inventory Ledger</h2>
                      <p className="text-slate-500 text-xs font-medium">Real-time batch-level visibility</p>
                    </div>
                    <div className="flex items-center gap-2 bg-white border border-slate-200 px-4 py-2.5 rounded-2xl shadow-sm">
                      <Search className="w-4 h-4 text-slate-400" />
                      <input 
                        type="text" 
                        placeholder="Search Stock..." 
                        className="bg-transparent outline-none text-xs font-bold w-48"
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50/30 text-slate-400 text-[10px] font-black uppercase tracking-widest">
                          <th className="px-8 py-5 border-b">Item Detail</th>
                          <th className="px-8 py-5 border-b">Category</th>
                          <th className="px-8 py-5 border-b text-center">UOM</th>
                          <th className="px-8 py-5 border-b text-right">Qty</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {loading ? (
                          <tr><td colSpan={4} className="px-8 py-32 text-center text-slate-400 font-bold uppercase tracking-widest">Loading...</td></tr>
                        ) : filteredStock.length === 0 ? (
                          <tr><td colSpan={4} className="px-8 py-32 text-center text-slate-400 font-bold uppercase tracking-widest">No records found</td></tr>
                        ) : filteredStock.map((item, idx) => (
                          <tr key={idx} onClick={() => handleFetchLedgerHistory(item)} className="group hover:bg-slate-50/80 transition-all cursor-pointer">
                            <td className="px-8 py-5">
                              <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-black text-slate-800 uppercase">{item.name}</span>
                                  <ChevronRight size={12} className="text-slate-300 group-hover:text-blue-500 transform group-hover:translate-x-1 transition-all" />
                                </div>
                                <span className="text-[10px] font-mono font-bold text-slate-400">{item.item_code}</span>
                              </div>
                            </td>
                            <td className="px-8 py-5"><span className="text-[10px] font-black uppercase text-slate-500 bg-slate-100 px-2 py-1 rounded">{item.category}</span></td>
                            <td className="px-8 py-5 text-center text-[10px] font-bold text-slate-400 uppercase">{item.uom}</td>
                            <td className="px-8 py-5 text-right font-black text-slate-800 text-lg">{item.total_quantity.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeTab === 'inward' && (
                <div className="p-8 space-y-8">
                  <h2 className="text-2xl font-black text-slate-800 uppercase tracking-tight">Inward Stock Receipt</h2>
                  <div className="bg-slate-50 border border-slate-200 p-8 rounded-[2.5rem] max-w-2xl space-y-4">
                     <div className="space-y-1.5">
                       <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Receiving Store</label>
                       <select value={inwardForm.store_id} onChange={e => setInwardForm({...inwardForm, store_id: e.target.value})} className="w-full bg-white border border-slate-200 rounded-xl p-3 text-sm font-bold">
                          <option value="">Select Store...</option>
                          {stores.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                       </select>
                     </div>
                     <div className="space-y-1.5">
                       <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Item SKU / Name</label>
                       <input value={inwardForm.item_name} onChange={e => setInwardForm({...inwardForm, item_name: e.target.value})} className="w-full bg-white border border-slate-200 rounded-xl p-3 text-sm font-bold" />
                     </div>
                     <div className="grid grid-cols-2 gap-4">
                       <div className="space-y-1.5"><label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Batch</label><input value={inwardForm.batch_number} onChange={e => setInwardForm({...inwardForm, batch_number: e.target.value})} className="w-full bg-white border border-slate-200 rounded-xl p-3 text-sm font-bold" /></div>
                       <div className="space-y-1.5"><label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Expiry</label><input type="date" value={inwardForm.expiry_date} onChange={e => setInwardForm({...inwardForm, expiry_date: e.target.value})} className="w-full bg-white border border-slate-200 rounded-xl p-3 text-sm font-bold" /></div>
                     </div>
                     <div className="grid grid-cols-2 gap-4">
                       <div className="space-y-1.5"><label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Qty</label><input type="number" value={inwardForm.quantity} onChange={e => setInwardForm({...inwardForm, quantity: Number(e.target.value)})} className="w-full bg-white border border-slate-200 rounded-xl p-3 text-sm font-bold" /></div>
                       <div className="space-y-1.5"><label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Price</label><input type="number" value={inwardForm.price} onChange={e => setInwardForm({...inwardForm, price: Number(e.target.value)})} className="w-full bg-white border border-slate-200 rounded-xl p-3 text-sm font-bold" /></div>
                     </div>
                     <button onClick={handlePostStock} disabled={loading} className="w-full py-4 bg-blue-600 text-white font-black uppercase text-[10px] tracking-widest rounded-2xl shadow-xl hover:bg-blue-700 active:scale-95 disabled:opacity-50">Post Stock</button>
                  </div>
                </div>
              )}

              {activeTab === 'indents' && (
                <div className="grid grid-cols-12 h-full min-h-[600px]">
                  <div className="col-span-12 lg:col-span-4 border-r border-slate-100 bg-slate-50/30 overflow-y-auto">
                    <div className="p-6 border-b flex justify-between items-center bg-white/50 sticky top-0 backdrop-blur-md z-10">
                       <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Pending Requests</h3>
                       <button onClick={() => setIndentModalOpen(true)} className="flex items-center gap-1.5 px-3 py-1 bg-blue-600 text-white text-[10px] font-black rounded-lg shadow-md uppercase hover:bg-blue-700 transition-all"><PlusCircle size={10} /> New Request</button>
                    </div>
                    <div className="p-4 space-y-3">
                      {indents.length === 0 && <p className="text-center text-[10px] py-20 text-slate-300 font-bold uppercase tracking-widest">No pending indents</p>}
                      {indents.map((ind: any) => (
                        <div key={ind.id} onClick={() => setSelectedIndent(ind)} className={`p-5 rounded-3xl border transition-all cursor-pointer ${selectedIndent?.id === ind.id ? "bg-white border-blue-500 shadow-xl" : "bg-white border-slate-200 hover:border-blue-200"}`}>
                           <div className="flex justify-between items-start mb-2"><span className="text-[10px] font-black text-blue-600 bg-blue-50 px-2 py-1 rounded uppercase">{ind.status}</span><span className="text-[10px] font-mono font-bold text-slate-400">{ind.indent_number}</span></div>
                           <h4 className="text-sm font-black text-slate-800 uppercase">{ind.requesting_store?.name}</h4>
                           <p className="text-[10px] text-slate-400 font-bold mt-1 uppercase">To: {ind.issuing_store?.name}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="col-span-12 lg:col-span-8 p-10 flex flex-col items-center justify-center bg-white">
                    {selectedIndent ? (
                      <div className="w-full text-left space-y-8 max-w-2xl">
                        <div className="p-8 bg-slate-900 text-white rounded-[3rem] shadow-2xl space-y-4">
                           <div className="flex justify-between items-center">
                             <div className="bg-white/10 p-4 rounded-3xl"><ArrowRightLeft className="w-8 h-8 text-blue-400" /></div>
                             <div className="text-right"><span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Ref Number</span><p className="text-xl font-black">{selectedIndent.indent_number}</p></div>
                           </div>
                           <div className="flex items-center gap-4 py-4 border-t border-white/10">
                             <div className="flex-1 text-center"><p className="text-[10px] text-blue-400 uppercase font-black tracking-widest">Requesting</p><p className="font-bold text-sm uppercase">{selectedIndent.requesting_store?.name}</p></div>
                             <div className="w-px h-8 bg-white/20"></div>
                             <div className="flex-1 text-center"><p className="text-[10px] text-blue-400 uppercase font-black tracking-widest">Issuing Store</p><p className="font-bold text-sm uppercase">{selectedIndent.issuing_store?.name}</p></div>
                           </div>
                        </div>
                        <div className="space-y-4">
                           <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Requested Items</h3>
                           {selectedIndent.items?.map((itm: any) => (
                              <div key={itm.id} className="bg-slate-50 border border-slate-200 rounded-[2rem] p-6 flex justify-between items-center group hover:bg-white hover:border-blue-300 transition-all">
                                 <div><span className="text-sm font-black text-slate-800 uppercase">{itm.item?.name || 'Item Detail'}</span><p className="text-[10px] font-mono text-slate-400 uppercase mt-1">{itm.item?.item_code || 'ITM-CODE'}</p></div>
                                 <div className="text-right bg-white px-6 py-3 rounded-2xl border border-slate-100"><span className="text-[10px] font-black text-blue-600 uppercase">Qty</span><p className="text-2xl font-black text-slate-900 leading-none">{itm.requested_quantity}</p></div>
                              </div>
                           ))}
                        </div>
                        {selectedIndent.status === 'DRAFT' && (
                          <div className="flex gap-4">
                            <button 
                              onClick={() => handleApproveIndent(selectedIndent.id)}
                              disabled={loading}
                              className="flex-1 py-6 bg-amber-600 text-white font-black uppercase text-xs tracking-[0.2em] rounded-[1.5rem] shadow-2xl hover:bg-amber-700 transition-all active:scale-95"
                            >
                              Approve Request
                            </button>
                          </div>
                        )}
                        {selectedIndent.status === 'APPROVED' && (
                          <button 
                            onClick={handleCompleteIssue}
                            disabled={loading}
                            className="w-full py-6 bg-blue-600 text-white font-black uppercase text-xs tracking-[0.2em] rounded-[1.5rem] shadow-2xl shadow-blue-200 hover:bg-blue-700 transition-all active:scale-95 disabled:opacity-50"
                          >
                            Generate Material Issue
                          </button>
                        )}
                        {['ISSUED', 'RECEIVED'].includes(selectedIndent.status) && (
                          <div className={`p-6 ${selectedIndent.status === 'RECEIVED' ? 'bg-blue-50 border-blue-100' : 'bg-emerald-50 border-emerald-100'} rounded-3xl flex items-center gap-4`}>
                             <CheckSquare className={selectedIndent.status === 'RECEIVED' ? 'text-blue-600 w-8 h-8' : 'text-emerald-600 w-8 h-8'} />
                             <div><p className={`${selectedIndent.status === 'RECEIVED' ? 'text-blue-900' : 'text-emerald-900'} font-black uppercase text-xs`}>{selectedIndent.status === 'RECEIVED' ? 'Receipt Confirmed' : 'Stock Issued'}</p><p className={`${selectedIndent.status === 'RECEIVED' ? 'text-blue-600' : 'text-emerald-600'} text-[10px] font-bold`}>{selectedIndent.status === 'RECEIVED' ? 'Transaction lifecycle completed successfully' : 'Waiting for receiving store acceptance'}</p></div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-4 opacity-30 text-center"><ArrowRightLeft size={80} className="text-slate-300 mx-auto" /><p className="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px]">Select an indent to begin processing</p></div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'transit' && (
                 <div className="grid grid-cols-12 h-full min-h-[600px]">
                   <div className="col-span-12 lg:col-span-4 border-r border-slate-100 bg-slate-50/30 overflow-y-auto">
                      <div className="p-6 border-b bg-white/50 sticky top-0 backdrop-blur-md z-10 text-center">
                         <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">In-Transit Shipments</h3>
                      </div>
                      <div className="p-4 space-y-3">
                        {issues.filter(iss => iss.status === 'PENDING_ACCEPTANCE').length === 0 && (
                          <p className="text-center text-[10px] py-20 text-slate-300 font-bold uppercase tracking-widest leading-loose">No pending deliveries found</p>
                        )}
                        {issues.filter(iss => iss.status === 'PENDING_ACCEPTANCE').map((iss: any) => (
                          <div key={iss.id} onClick={() => setSelectedIssue(iss)} className={`p-6 rounded-[2rem] border transition-all cursor-pointer ${selectedIssue?.id === iss.id ? "bg-white border-blue-500 shadow-xl" : "bg-white border-slate-200 hover:border-blue-200"}`}>
                             <div className="flex justify-between items-start mb-2"><span className="text-[10px] font-black text-amber-600 bg-amber-50 px-2 py-1 rounded uppercase">Transit</span><span className="text-[10px] font-mono font-bold text-slate-400">{iss.issue_number}</span></div>
                             <h4 className="text-sm font-black text-slate-800 uppercase">Delivery to {iss.receiving_store?.name}</h4>
                             <p className="text-[10px] text-slate-400 font-bold mt-1 uppercase">From: {iss.issuing_store?.name}</p>
                          </div>
                        ))}
                      </div>
                   </div>
                   <div className="col-span-12 lg:col-span-8 p-12 flex flex-col items-center justify-center bg-white">
                      {selectedIssue ? (
                        <div className="w-full max-w-2xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                           <div className="text-center space-y-2">
                             <div className="bg-blue-50 w-20 h-20 rounded-[2rem] flex items-center justify-center mx-auto mb-4 border border-blue-100"><Truck className="w-10 h-10 text-blue-600" /></div>
                             <h2 className="text-3xl font-black text-slate-900 uppercase tracking-tight">Confirm Receipt</h2>
                             <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">Package: {selectedIssue.issue_number}</p>
                           </div>
                           <div className="grid grid-cols-2 gap-4">
                              <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100"><p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Origin</p><p className="font-bold text-slate-800 uppercase">{selectedIssue.issuing_store?.name}</p></div>
                              <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100"><p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Destination</p><p className="font-bold text-slate-800 uppercase">{selectedIssue.receiving_store?.name}</p></div>
                           </div>
                           <div className="bg-slate-50 rounded-[2.5rem] p-8 border border-slate-100 space-y-6">
                              <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Contents</h3>
                              <div className="space-y-3">
                                 {selectedIssue.items?.map((itm: any) => (
                                   <div key={itm.id} className="flex justify-between items-center bg-white p-4 rounded-2xl border border-slate-100">
                                      <span className="text-sm font-bold text-slate-700 uppercase">{itm.item?.name || 'Item'}</span>
                                      <span className="text-lg font-black text-blue-600">{itm.issued_quantity}</span>
                                   </div>
                                 ))}
                              </div>
                           </div>
                           <button onClick={() => handleAcceptTransit(selectedIssue.id)} disabled={loading} className="w-full py-6 bg-slate-900 text-white font-black uppercase text-xs tracking-[0.2em] rounded-[1.5rem] shadow-2xl transition-all hover:bg-slate-800 active:scale-95 disabled:opacity-50">Accept & Post to Store</button>
                        </div>
                      ) : (
                        <div className="space-y-4 opacity-30 text-center"><Truck size={80} className="text-slate-300 mx-auto" /><p className="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px]">Awaiting physical confirmation</p></div>
                      )}
                   </div>
                 </div>
               )}

               {activeTab === 'scrap' && (
                 <div className="p-8 space-y-8 animate-in fade-in duration-500">
                    <div className="flex justify-between items-center">
                      <div>
                        <h2 className="text-2xl font-black text-slate-800 uppercase tracking-tight">Stock Adjustments</h2>
                        <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1">Record physical count discrepancies</p>
                      </div>
                      <AlertCircle className="text-amber-500 w-8 h-8" />
                    </div>
                    <div className="bg-amber-50 border border-amber-100 p-8 rounded-[2.5rem] max-w-2xl space-y-6">
                       <div className="space-y-1.5">
                         <label className="text-[10px] font-black text-amber-700 uppercase tracking-widest">Select Item to Adjust</label>
                         <select 
                           value={adjustmentForm.item_code}
                           onChange={e => setAdjustmentForm({...adjustmentForm, item_code: e.target.value})}
                           className="w-full bg-white border border-amber-200 rounded-xl p-4 text-sm font-bold"
                         >
                            <option value="">Select Item...</option>
                            {stockLevels.map((s,i) => <option key={i} value={s.item_code}>{s.name} ({s.item_code}) - Current: {s.total_quantity}</option>)}
                         </select>
                       </div>
                       <div className="grid grid-cols-2 gap-6">
                         <div className="space-y-1.5 align-top">
                           <label className="text-[10px] font-black text-amber-700 uppercase tracking-widest ml-1">Physical Qty</label>
                           <input 
                              type="number" 
                              value={adjustmentForm.physical_qty}
                              onChange={e => setAdjustmentForm({...adjustmentForm, physical_qty: Number(e.target.value)})}
                              className="w-full bg-white border border-amber-200 rounded-xl p-4 text-sm font-bold" 
                              placeholder="0.00" 
                           />
                         </div>
                         <div className="space-y-1.5">
                            <label className="text-[10px] font-black text-amber-700 uppercase tracking-widest ml-1">Adjustment Reason</label>
                            <input 
                               value={adjustmentForm.reason}
                               onChange={e => setAdjustmentForm({...adjustmentForm, reason: e.target.value})}
                               className="w-full bg-white border border-amber-200 rounded-xl p-4 text-sm font-bold" 
                               placeholder="Drying / Damage / Loss" 
                            />
                         </div>
                       </div>
                       <button 
                         onClick={handleAdjustmentSubmit}
                         disabled={loading}
                         className="w-full py-5 bg-amber-600 text-white font-black uppercase text-xs tracking-widest rounded-2xl shadow-xl hover:bg-amber-700 active:scale-95 transition-all disabled:opacity-50"
                       >
                         Submit Adjustment Request
                       </button>
                    </div>
                 </div>
               )}

               {activeTab === 'gatepass' && (
                 <div className="p-8 space-y-8 animate-in fade-in duration-500 h-full">
                    <h2 className="text-2xl font-black text-slate-800 uppercase tracking-tight">Logistics & Gatepass</h2>
                    <div className="space-y-4 max-w-4xl">
                       {issues.filter(iss => ['ISSUED'].includes(iss.status)).map((iss: any) => (
                         <div key={iss.id} className="bg-white border border-slate-200 p-8 rounded-[3rem] flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm hover:shadow-md transition-all">
                            <div className="flex items-center gap-6">
                               <div className="bg-slate-900 text-white p-5 rounded-[2rem]"><Barcode size={32} /></div>
                               <div>
                                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Security Clearance Pass</p>
                                  <h4 className="text-xl font-black text-slate-900 uppercase">{iss.issue_number}</h4>
                                  <p className="text-xs font-bold text-slate-500 uppercase mt-1">Destination: {iss.receiving_store?.name}</p>
                               </div>
                            </div>
                            <div className="flex gap-3">
                               <button className="px-6 py-3 bg-slate-50 text-slate-600 rounded-2xl font-black uppercase text-[10px] tracking-widest border border-slate-200 hover:bg-white transition-all">Print Pass</button>
                               <button 
                                  onClick={() => {
                                      alert(`Gatepass ${iss.issue_number} VERIFIED. Transport departure authorized.`);
                                      setIssues(issues.map((i: any) => i.id === iss.id ? { ...i, status: 'DISPATCHED' } : i));
                                  }} 
                                  className="px-6 py-3 bg-blue-600 text-white rounded-2xl font-black uppercase text-[10px] tracking-widest shadow-lg hover:bg-blue-700 transition-all"
                               >
                                  Gate Cleared
                               </button>
                            </div>
                         </div>
                       ))}
                       {issues.filter(iss => ['ISSUED'].includes(iss.status)).length === 0 && (
                          <div className="p-20 text-center space-y-4 opacity-50"><Truck size={48} className="mx-auto text-slate-400" /><p className="text-[10px] font-black uppercase tracking-widest">No outbound shipments ready for gatepass</p></div>
                       )}
                    </div>
                 </div>
               )}
               
               {activeTab === 'analytics' && (
                  <div className="flex flex-col h-full bg-slate-50/50 rounded-[2.5rem] mt-6 animate-in fade-in border border-slate-200 overflow-hidden">
                    <div className="p-8 border-b border-slate-100 bg-white">
                        <h2 className="text-2xl font-black text-slate-800 uppercase tracking-tight flex items-center gap-3">
                            <div className="bg-indigo-100 text-indigo-600 p-2 rounded-xl"><Activity size={20} /></div>
                            Smart Analytics Matrix
                        </h2>
                        <p className="text-slate-500 text-xs font-medium mt-1">AI-driven actionable insights for supply chain optimization</p>
                    </div>
                    
                    {!analytics ? (
                       <div className="p-32 text-center"><RefreshCcw className="w-12 h-12 mx-auto text-blue-200 animate-spin" /><p className="text-slate-400 font-bold uppercase mt-4 text-[10px] tracking-widest">Crunching data...</p></div>
                    ) : (
                       <div className="p-8 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                          
                          {/* ABC Analysis */}
                          <div className="bg-white rounded-[2rem] border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
                             <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest mb-6 flex items-center gap-2"><Activity className="w-4 h-4 text-indigo-500" /> Value Matrix (ABC)</h3>
                             <div className="space-y-3">
                                {analytics.abc_analysis?.slice(0, 5).map((item: any) => (
                                   <div key={item.item_id} className="flex justify-between items-center p-4 bg-slate-50 rounded-[1.5rem] border border-slate-100 group hover:border-indigo-200 transition-all">
                                      <div className="max-w-[70%]">
                                         <p className="text-xs font-black text-slate-800 uppercase truncate" title={item.name}>{item.name}</p>
                                         <p className="text-[10px] font-bold text-slate-400 mt-0.5"><span className="text-indigo-600 font-black">CLASS {item.abc_class}</span> • {item.percentage}% Portfolio</p>
                                      </div>
                                      <p className="text-sm font-black text-indigo-600 font-mono">₹{item.value.toLocaleString()}</p>
                                   </div>
                                ))}
                             </div>
                          </div>

                          {/* Reorder Alerts */}
                          <div className="bg-white rounded-[2rem] border border-rose-100 p-6 shadow-sm hover:shadow-md transition-all">
                             <h3 className="text-xs font-black text-rose-900 uppercase tracking-widest mb-6 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-rose-500" /> Reorder Engine Action</h3>
                             <div className="space-y-3">
                                {analytics.reorder_alerts?.length === 0 ? (
                                   <div className="p-10 text-center"><p className="text-xs font-black text-slate-300 uppercase">Stock levels optimal</p></div>
                                ) : analytics.reorder_alerts?.map((item: any) => (
                                   <div key={item.item_id} className="flex flex-col gap-3 p-4 bg-rose-50 rounded-[1.5rem] border border-rose-100">
                                      <div className="flex justify-between items-start">
                                         <p className="text-xs font-black text-rose-900 uppercase pr-2 leading-tight">{item.name}</p>
                                         <p className="text-[10px] font-black bg-rose-600 text-white px-2.5 py-1 rounded-xl whitespace-nowrap">{item.current_qty} left</p>
                                      </div>
                                   </div>
                                ))}
                             </div>
                          </div>

                          {/* Dead Stock */}
                          <div className="bg-white rounded-[2rem] border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
                             <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest mb-6 flex items-center gap-2"><FileWarning className="w-4 h-4 text-slate-500" /> Dead Stock (&gt;90 Days)</h3>
                             <div className="space-y-3">
                                {analytics.dead_stock?.length === 0 ? (
                                   <div className="p-10 text-center"><p className="text-xs font-black text-slate-300 uppercase">No dead stock detected</p></div>
                                ) : analytics.dead_stock?.map((item: any) => (
                                   <div key={item.item_id} className="flex justify-between items-center p-4 bg-slate-50 rounded-[1.5rem] border border-slate-100 group hover:border-amber-200 transition-all">
                                      <div className="max-w-[60%]">
                                         <p className="text-xs font-black text-slate-800 uppercase truncate" title={item.name}>{item.name}</p>
                                         <p className="text-[10px] font-black text-amber-600 mt-0.5">{item.days_inactive} Days Idle</p>
                                      </div>
                                      <div className="text-right">
                                         <p className="text-sm font-black text-slate-900 font-mono">Qty: {item.quantity}</p>
                                         <p className="text-[10px] font-black text-slate-400 font-mono mt-0.5">₹{item.value.toLocaleString()}</p>
                                      </div>
                                   </div>
                                ))}
                             </div>
                          </div>

                       </div>
                    )}
                  </div>
                )}

               {!['overview', 'analytics', 'inward', 'indents', 'transit', 'scrap', 'gatepass'].includes(activeTab) && (
                 <div className="flex flex-col items-center justify-center h-full text-center p-8 space-y-4">
                    <RefreshCcw className="w-12 h-12 text-blue-200 animate-spin" />
                    <h3 className="text-xl font-black text-slate-800 uppercase tracking-tight">{activeTab} workflow pending</h3>
                 </div>
               )}

            </div>
          </div>
        </div>
      </div>

      {indentModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-[3rem] shadow-2xl w-full max-w-xl overflow-hidden animate-in fade-in zoom-in duration-300">
             <div className="p-8 bg-blue-600 text-white flex justify-between items-center">
                <div className="flex items-center gap-4">
                   <div className="bg-white/20 p-3 rounded-2xl"><PlusCircle /></div>
                   <h2 className="text-xl font-black uppercase tracking-tight">New Stock Request</h2>
                </div>
                <button onClick={() => setIndentModalOpen(false)} className="text-white/60 hover:text-white">✕</button>
             </div>
             <div className="p-10 space-y-6">
                <div className="grid grid-cols-2 gap-6">
                   <div className="space-y-1.5 align-top">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Requesting Dept</label>
                      <select value={newIndent.requesting_store_id} onChange={e => setNewIndent({...newIndent, requesting_store_id: e.target.value})} className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-bold">
                         <option value="">Select Dept...</option>
                         {stores.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                      </select>
                   </div>
                   <div className="space-y-1.5">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Issuing Store</label>
                      <select value={newIndent.issuing_store_id} onChange={e => setNewIndent({...newIndent, issuing_store_id: e.target.value})} className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-bold">
                         <option value="">Select Store...</option>
                         {stores.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                      </select>
                   </div>
                </div>
                <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Requested Item</label>
                    <select value={newIndent.item_id} onChange={e => setNewIndent({...newIndent, item_id: e.target.value})} className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-bold">
                        <option value="">Search Item...</option>
                        {items.map(it => <option key={it.id} value={it.id}>{it.name} ({it.item_code})</option>)}
                    </select>
                </div>
                <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Desired Quantity</label>
                    <input type="number" value={newIndent.quantity} onChange={e => setNewIndent({...newIndent, quantity: Number(e.target.value)})} className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-bold" placeholder="0.00" />
                </div>
                <button onClick={handleCreateIndentSubmit} disabled={loading} className="w-full py-5 bg-blue-600 text-white font-black uppercase text-xs tracking-[0.2em] rounded-2xl shadow-xl hover:bg-blue-700 transition-all active:scale-95 disabled:opacity-50">Submit Internal Indent</button>
             </div>
          </div>
        </div>
      )}
      {ledgerModalOpen && selectedLedgerItem && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
           <div className="bg-white rounded-[3rem] shadow-2xl w-full max-w-4xl overflow-hidden animate-in fade-in zoom-in duration-300 h-[80vh] flex flex-col">
              <div className="p-8 bg-slate-900 text-white flex justify-between items-center">
                 <div className="flex items-center gap-4">
                    <div className="bg-blue-600 p-3 rounded-2xl shadow-lg ring-4 ring-blue-600/20"><Activity /></div>
                    <div>
                       <h2 className="text-xl font-black uppercase tracking-tight">Perpetual Stock Ledger</h2>
                       <p className="text-blue-400 text-[10px] font-black uppercase tracking-widest">{selectedLedgerItem.name} — {selectedLedgerItem.item_code}</p>
                    </div>
                 </div>
                 <button onClick={() => setLedgerModalOpen(false)} className="bg-white/10 hover:bg-white/20 p-2 rounded-xl transition-all">✕</button>
              </div>
              <div className="flex-1 overflow-y-auto p-8">
                 <table className="w-full text-sm">
                    <thead>
                       <tr className="text-[10px] font-black text-slate-400 uppercase tracking-widest border-b">
                          <th className="px-4 py-4">Ref Number</th>
                          <th className="px-4 py-4">Date</th>
                          <th className="px-4 py-4">Transaction Type</th>
                          <th className="px-4 py-4 text-right">In</th>
                          <th className="px-4 py-4 text-right">Out</th>
                          <th className="px-4 py-4 text-right">Running Bal</th>
                       </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                       {ledgerHistory.length === 0 ? (
                         <tr><td colSpan={6} className="py-20 text-center text-slate-300 font-bold uppercase tracking-widest">No history available</td></tr>
                       ) : ledgerHistory.map((log: any, i) => (
                         <tr key={i} className="hover:bg-slate-50 transition-all">
                            <td className="px-4 py-5 font-mono text-[10px] font-bold text-slate-400">{log.reference_id || 'TRX-DEFAULT'}</td>
                            <td className="px-4 py-5 font-bold text-slate-600">{new Date(log.transaction_date).toLocaleDateString()}</td>
                            <td className="px-4 py-5">
                               <span className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase ${
                                 log.transaction_type === 'OPB' ? 'bg-indigo-50 text-indigo-600' :
                                 log.transaction_type === 'ISS' ? 'bg-amber-50 text-amber-600' :
                                 'bg-emerald-50 text-emerald-600'
                               }`}>
                                 {log.transaction_type}
                               </span>
                            </td>
                            <td className="px-4 py-5 text-right font-black text-emerald-600">{log.quantity_change > 0 ? `+${log.quantity_change}` : '-'}</td>
                            <td className="px-4 py-5 text-right font-black text-rose-600">{log.quantity_change < 0 ? log.quantity_change : '-'}</td>
                            <td className="px-4 py-5 text-right font-black text-slate-900">{log.closing_balance}</td>
                         </tr>
                       ))}
                    </tbody>
                 </table>
              </div>
              <div className="p-8 bg-slate-50 border-t flex justify-between items-center">
                 <div className="flex gap-8">
                    <div><p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Method</p><p className="font-bold text-slate-900">FIFO / FEFO</p></div>
                    <div><p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Unit Price</p><p className="font-bold text-slate-900">₹150.00</p></div>
                 </div>
                 <button onClick={() => setLedgerModalOpen(false)} className="px-10 py-4 bg-slate-900 text-white rounded-2xl font-black uppercase text-xs tracking-widest shadow-xl active:scale-95 transition-all">Close History</button>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
