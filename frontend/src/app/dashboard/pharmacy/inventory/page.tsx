"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect } from "react";
import { 
  Pill, AlertCircle, Clock, CheckCircle2, Search, ArrowRight,
  Package, AlertTriangle, TrendingDown, ClipboardList, ShieldAlert,
  ArrowLeft, Plus, Edit2, Archive, X
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function PharmacyInventoryPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [medications, setMedications] = useState<any[]>([]);
  const [inventory, setInventory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Modals
  const [showAddMedModal, setShowAddMedModal] = useState(false);
  const [showBatchesModal, setShowBatchesModal] = useState(false);
  const [showEditInvModal, setShowEditInvModal] = useState(false);
  
  // Selected Data
  const [selectedMed, setSelectedMed] = useState<any>(null);
  const [invExists, setInvExists] = useState(false);
  
  // Forms
  const [invForm, setInvForm] = useState({ quantity_available: 0, reorder_threshold: 10, reason: "Initial Setup" });
  
  const [batches, setBatches] = useState<any[]>([]);
  const [showAddBatch, setShowAddBatch] = useState(false);
  const [newBatch, setNewBatch] = useState({ drug_id: "", batch_number: "", manufacture_date: "", expiry_date: "", quantity: 0 });
  
  // New Medication Form
  const [newMed, setNewMed] = useState({
    drug_code: "",
    drug_name: "",
    generic_name: "",
    drug_class: "",
    form: "Tablet",
    strength: "",
    manufacturer: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchInventoryData = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };

      const [medsRes, invRes] = await Promise.all([
        fetch(`${API}/api/v1/pharmacy/medications`, { headers }),
        fetch(`${API}/api/v1/pharmacy/inventory`, { headers })
      ]);

      if (medsRes.ok) {
        const medsData = await medsRes.json();
        setMedications(medsData);
      }
      if (invRes.ok) {
        const invData = await invRes.json();
        setInventory(invData);
      }
    } catch (error) {
      console.error("Failed to fetch inventory data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventoryData();
  }, []);

  const handleAddMedication = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API}/api/v1/pharmacy/medications`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newMed)
      });
      if (res.ok) {
        setShowAddMedModal(false);
        setNewMed({
          drug_code: "",
          drug_name: "",
          generic_name: "",
          drug_class: "",
          form: "Tablet",
          strength: "",
          manufacturer: ""
        });
        fetchInventoryData(); // Refresh list after adding
      } else {
        alert("Failed to create medication. Please check the drug code.");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditInvClick = (med: any) => {
    const inv = getInventoryForMed(med.id);
    setSelectedMed(med);
    if (inv) {
      setInvExists(true);
      setInvForm({
        quantity_available: inv.quantity_available,
        reorder_threshold: inv.reorder_threshold, // Note: update API might only accept quantity and reason
        reason: "Stock Adjustment"
      });
    } else {
      setInvExists(false);
      setInvForm({ quantity_available: 0, reorder_threshold: 10, reason: "Initial Setup" });
    }
    setShowEditInvModal(true);
  };

  const handleSaveInventory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMed) return;
    try {
      setSubmitting(true);
      const token = localStorage.getItem("access_token");
      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };

      if (invExists) {
        // Update
        const res = await fetch(`${API}/api/v1/pharmacy/inventory/${selectedMed.id}/update`, {
          method: "POST",
          headers,
          body: JSON.stringify({ 
            quantity_available: parseFloat(invForm.quantity_available.toString()), 
            reason: invForm.reason 
          })
        });
        if (!res.ok) throw new Error("Failed to update inventory.");
      } else {
        // Create
        const res = await fetch(`${API}/api/v1/pharmacy/inventory`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            drug_id: selectedMed.id,
            quantity_available: parseFloat(invForm.quantity_available.toString()),
            reorder_threshold: parseFloat(invForm.reorder_threshold.toString())
          })
        });
        if (!res.ok) throw new Error("Failed to create inventory setup.");
      }

      setShowEditInvModal(false);
      fetchInventoryData();
    } catch (error) {
      console.error(error);
      alert("Error saving inventory.");
    } finally {
      setSubmitting(false);
    }
  };

  const loadBatches = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API}/api/v1/pharmacy/batches`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setBatches(await res.json());
      }
    } catch (error) {
      console.error(error);
    }
  };

  const handleOpenBatches = () => {
    setShowBatchesModal(true);
    setShowAddBatch(false);
    loadBatches();
  };

  const handleSaveBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const token = localStorage.getItem("access_token");
      const payload = {
        ...newBatch,
        quantity: parseFloat(newBatch.quantity.toString())
      };
      
      const res = await fetch(`${API}/api/v1/pharmacy/batches`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setNewBatch({ drug_id: "", batch_number: "", manufacture_date: "", expiry_date: "", quantity: 0 });
        setShowAddBatch(false);
        loadBatches(); // Refresh batches list
      } else {
        alert("Failed to save batch.");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  const getInventoryForMed = (medId: string) => {
    return inventory.find(i => i.drug_id === medId);
  };

  const filteredMeds = medications.filter(m => 
    m.drug_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    m.drug_code.toLowerCase().includes(searchTerm.toLowerCase()) || 
    m.generic_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Area */}
      <div>
        <button 
          onClick={() => router.back()} 
          className="flex items-center gap-2 text-slate-500 hover:text-[var(--accent-primary)] transition-colors text-sm font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Pharmacy Inventory</h1>
            <p className="text-slate-500 text-sm mt-1">Manage stock levels, reorder thresholds, and catalog items.</p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={handleOpenBatches}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:border-[var(--accent-primary)] hover:text-[var(--accent-primary)] transition-colors shadow-sm font-medium"
            >
              <Archive className="w-4 h-4" />
              Drug Batches
            </button>
            <button 
              onClick={() => setShowAddMedModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:bg-slate-800 transition-colors shadow-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              Add Medication
            </button>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        
        {/* Toolbar */}
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/50">
          <div className="relative max-w-md w-full">
            <Search className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search medications by name, generic, or code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-transparent transition-all shadow-sm"
            />
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-600 font-medium">
            <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-md border border-slate-200 shadow-sm">
              <Pill className="w-4 h-4 text-slate-400" />
              Total Catalog: {medications.length}
            </div>
            <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-md border border-slate-200 shadow-sm">
              <TrendingDown className="w-4 h-4 text-amber-500" />
              Low Stock: {inventory.filter(i => i.quantity_available <= i.reorder_threshold).length}
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--accent-primary)]"></div>
          </div>
        ) : (
          /* Data Table */
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Drug Info</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Form / Class</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Manufacturer</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Stock Status</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredMeds.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                      <Package className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                      <p className="text-lg font-medium text-slate-700">No medications found.</p>
                      <p className="text-sm mt-1">Try a different search term or add a new entry.</p>
                    </td>
                  </tr>
                ) : (
                  filteredMeds.map((med) => {
                    const inv = getInventoryForMed(med.id);
                    const isLowStock = inv ? (inv.quantity_available <= inv.reorder_threshold) : true;
                    
                    return (
                      <tr key={med.id} className="hover:bg-slate-50/80 transition-colors group">
                        <td className="px-6 py-5">
                          <div className="flex items-start gap-3">
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 border ${isLowStock ? 'bg-amber-50 border-amber-100' : 'bg-blue-50 border-blue-100'}`}>
                              <Pill className={`w-5 h-5 ${isLowStock ? 'text-amber-500' : 'text-blue-500'}`} />
                            </div>
                            <div>
                              <p className="font-semibold text-slate-800">{med.drug_name}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs font-medium text-slate-500 px-1.5 py-0.5 bg-slate-100 rounded border border-slate-200">
                                  {med.drug_code}
                                </span>
                                <span className="text-xs text-slate-500">{med.generic_name}</span>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-5">
                          <p className="text-sm font-medium text-slate-700">{med.form} {med.strength && <span className="text-slate-400">({med.strength})</span>}</p>
                          <p className="text-xs text-slate-500 mt-1">{med.drug_class}</p>
                        </td>
                        <td className="px-6 py-5">
                          <p className="text-sm text-slate-600">{med.manufacturer || "N/A"}</p>
                        </td>
                        <td className="px-6 py-5">
                          {inv ? (
                            <div className="flex flex-col gap-1.5">
                              <div className="flex items-center gap-2">
                                <span className={`text-lg font-bold ${isLowStock ? 'text-amber-600' : 'text-emerald-600'}`}>
                                  {inv.quantity_available}
                                </span>
                                {isLowStock && (
                                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                                )}
                              </div>
                              <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                                <div 
                                  className={`h-1.5 rounded-full ${isLowStock ? 'bg-amber-500' : 'bg-emerald-500'}`} 
                                  style={{ width: `${Math.min((inv.quantity_available / (inv.reorder_threshold * 3)) * 100, 100)}%` }}
                                ></div>
                              </div>
                              <span className="text-xs text-slate-400">Reorder Threshold: {inv.reorder_threshold}</span>
                            </div>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded-md bg-slate-100 text-slate-500 text-xs font-medium border border-slate-200">
                              No setup
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-5 text-right">
                          <button 
                            onClick={() => handleEditInvClick(med)}
                            className="p-2 text-slate-400 hover:text-[var(--accent-primary)] hover:bg-slate-100 rounded-lg transition-colors border border-transparent hover:border-slate-200"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Medication Modal */}
      {showAddMedModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden border border-slate-200 flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-5 border-b border-slate-100 bg-slate-50/80 shrink-0">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Pill className="w-5 h-5 text-[var(--accent-primary)]" />
                Add New Medication
              </h2>
              <button onClick={() => setShowAddMedModal(false)} className="text-slate-400 hover:text-slate-600 outline-none">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddMedication} className="flex-1 overflow-y-auto p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-slate-700 mb-1">Drug Name *</label>
                  <input required type="text" value={newMed.drug_name} onChange={e => setNewMed({...newMed, drug_name: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" placeholder="e.g. Paracetamol 500mg" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Drug Code *</label>
                  <input required type="text" value={newMed.drug_code} onChange={e => setNewMed({...newMed, drug_code: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" placeholder="e.g. MED-001" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Generic Name *</label>
                  <input required type="text" value={newMed.generic_name} onChange={e => setNewMed({...newMed, generic_name: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" placeholder="e.g. Acetaminophen" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Drug Class</label>
                  <input type="text" value={newMed.drug_class} onChange={e => setNewMed({...newMed, drug_class: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" placeholder="e.g. Analgesic" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Form</label>
                  <select value={newMed.form} onChange={e => setNewMed({...newMed, form: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]">
                    <option value="Tablet">Tablet</option>
                    <option value="Capsule">Capsule</option>
                    <option value="Syrup">Syrup</option>
                    <option value="Injection">Injection</option>
                    <option value="Ointment">Ointment</option>
                    <option value="Drops">Drops</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Strength</label>
                  <input type="text" value={newMed.strength} onChange={e => setNewMed({...newMed, strength: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" placeholder="e.g. 500mg" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Manufacturer</label>
                  <input type="text" value={newMed.manufacturer} onChange={e => setNewMed({...newMed, manufacturer: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" placeholder="e.g. PharmaCorp" />
                </div>
              </div>
              <div className="pt-5 mt-2 flex justify-end gap-3 border-t border-slate-100">
                <button type="button" onClick={() => setShowAddMedModal(false)} className="px-4 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors">Cancel</button>
                <button type="submit" disabled={submitting} className="px-4 py-2 bg-[var(--accent-primary)] rounded-lg text-white hover:bg-slate-800 transition-colors disabled:opacity-50">
                  {submitting ? "Saving..." : "Save Medication"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inventory Edit Modal */}
      {showEditInvModal && selectedMed && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200 flex flex-col">
            <div className="flex justify-between items-center p-5 border-b border-slate-100 bg-slate-50/80 shrink-0">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Edit2 className="w-5 h-5 text-[var(--accent-primary)]" />
                {invExists ? "Update Stock Level" : "Setup Inventory"}
              </h2>
              <button onClick={() => setShowEditInvModal(false)} className="text-slate-400 hover:text-slate-600 outline-none">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 bg-blue-50/50 border-b border-blue-100">
              <p className="font-semibold text-slate-800">{selectedMed.drug_name}</p>
              <p className="text-sm text-slate-500">{selectedMed.drug_code} • {selectedMed.form}</p>
            </div>
            <form onSubmit={handleSaveInventory} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Quantity Available *</label>
                <input required type="number" step="0.01" value={invForm.quantity_available} onChange={e => setInvForm({...invForm, quantity_available: Number(e.target.value)})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" />
              </div>
              {!invExists && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Reorder Threshold *</label>
                  <input required type="number" step="0.01" value={invForm.reorder_threshold} onChange={e => setInvForm({...invForm, reorder_threshold: Number(e.target.value)})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" />
                  <p className="text-xs text-slate-400 mt-1">Alert triggers when stock drops below this number.</p>
                </div>
              )}
              {invExists && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Reason for update</label>
                  <input required type="text" value={invForm.reason} onChange={e => setInvForm({...invForm, reason: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" />
                  <p className="text-xs text-slate-400 mt-1">Logged for auditing purposes.</p>
                </div>
              )}
              
              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setShowEditInvModal(false)} className="px-4 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors">Cancel</button>
                <button type="submit" disabled={submitting} className="px-4 py-2 bg-[var(--accent-primary)] rounded-lg text-white hover:bg-slate-800 transition-colors disabled:opacity-50">
                  {submitting ? "Saving..." : "Save Stock"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Drug Batches Modal */}
      {showBatchesModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl overflow-hidden border border-slate-200 flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-5 border-b border-slate-100 bg-slate-50/80 shrink-0">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Archive className="w-5 h-5 text-[var(--accent-primary)]" />
                Drug Batches Ledger
              </h2>
              <div className="flex gap-2">
                {!showAddBatch && (
                  <button onClick={() => setShowAddBatch(true)} className="flex items-center gap-1 px-3 py-1.5 bg-[var(--accent-primary)] text-white rounded text-sm font-medium hover:bg-slate-800 transition-colors">
                    <Plus className="w-4 h-4" /> Add Batch
                  </button>
                )}
                <button onClick={() => setShowBatchesModal(false)} className="p-1.5 text-slate-400 hover:text-slate-600 outline-none ml-2">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <div className="overflow-y-auto bg-slate-50 flex-1">
              {showAddBatch ? (
                <div className="p-6 bg-white border-b border-slate-200">
                  <h3 className="font-semibold text-slate-800 mb-4">Register New Batch</h3>
                  <form onSubmit={handleSaveBatch} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="sm:col-span-2">
                        <label className="block text-sm font-medium text-slate-700 mb-1">Medication *</label>
                        <select required value={newBatch.drug_id} onChange={e => setNewBatch({...newBatch, drug_id: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] bg-white">
                          <option value="">Select an Item...</option>
                          {medications.map(m => (
                            <option key={m.id} value={m.id}>{m.drug_name} ({m.drug_code})</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Batch / Lot Number *</label>
                        <input required type="text" value={newBatch.batch_number} onChange={e => setNewBatch({...newBatch, batch_number: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" placeholder="e.g. LOT-12345" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Quantity Received *</label>
                        <input required type="number" step="0.01" value={newBatch.quantity} onChange={e => setNewBatch({...newBatch, quantity: Number(e.target.value)})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Manufacture Date *</label>
                        <input required type="date" value={newBatch.manufacture_date} onChange={e => setNewBatch({...newBatch, manufacture_date: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Expiry Date *</label>
                        <input required type="date" value={newBatch.expiry_date} onChange={e => setNewBatch({...newBatch, expiry_date: e.target.value})} className="w-full p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]" />
                      </div>
                    </div>
                    <div className="pt-2 flex justify-end gap-3">
                      <button type="button" onClick={() => setShowAddBatch(false)} className="px-4 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors">Cancel</button>
                      <button type="submit" disabled={submitting} className="px-4 py-2 bg-[var(--accent-primary)] rounded-lg text-white hover:bg-slate-800 transition-colors disabled:opacity-50">
                        {submitting ? "Processing..." : "Register Batch"}
                      </button>
                    </div>
                  </form>
                </div>
              ) : null}

              <div className="p-0">
                {batches.length === 0 ? (
                  <div className="p-12 text-center flex flex-col items-center">
                    <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                      <Archive className="w-8 h-8 text-slate-300" />
                    </div>
                    <h3 className="font-semibold text-slate-700">No Batches Registered</h3>
                    <p className="text-slate-500 text-sm mt-1 mb-4 max-w-sm">There are currently no active medication batches listed. Please add a batch to begin tracing expirations.</p>
                  </div>
                ) : (
                  <table className="w-full text-left bg-white">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        <th className="px-6 py-4 rounded-tl-lg">Batch / Lot</th>
                        <th className="px-6 py-4">Medication</th>
                        <th className="px-6 py-4">MFG Date</th>
                        <th className="px-6 py-4">Expiry Date</th>
                        <th className="px-6 py-4 text-right">Quantity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {batches.map(v => {
                        const med = medications.find(m => m.id === v.drug_id);
                        const isExpired = new Date(v.expiry_date) < new Date();
                        const isNearExpiry = !isExpired && (new Date(v.expiry_date).getTime() - new Date().getTime()) < (60 * 24 * 60 * 60 * 1000);
                        return (
                          <tr key={v.id} className="hover:bg-slate-50/50">
                            <td className="px-6 py-4">
                              <span className="font-mono text-sm font-semibold text-slate-700">{v.batch_number}</span>
                            </td>
                            <td className="px-6 py-4">
                              <span className="font-medium text-slate-800">{med?.drug_name || v.drug_id.split('-')[0]}</span>
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-600">
                              {new Date(v.manufacture_date).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <span className={`text-sm font-medium ${isExpired ? 'text-rose-600' : isNearExpiry ? 'text-amber-600' : 'text-slate-600'}`}>
                                  {new Date(v.expiry_date).toLocaleDateString()}
                                </span>
                                {isExpired && <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-700">EXPIRED</span>}
                                {isNearExpiry && <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-700">SOON</span>}
                              </div>
                            </td>
                            <td className="px-6 py-4 text-right font-medium text-slate-700">
                              {v.quantity}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
