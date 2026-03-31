"use client";
import React, { useState, useEffect } from "react";
import { 
  Pill, AlertCircle, Clock, CheckCircle2, Search, ArrowRight,
  Package, AlertTriangle, TrendingDown, ClipboardList, ShieldAlert
} from "lucide-react";
import Link from "next/link";
import { WorkflowPipeline } from "@/components/ui/WorkflowPipeline";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function PharmacyDashboardPage() {
  const [prescriptions, setPrescriptions] = useState<any[]>([]);
  const [lowStock, setLowStock] = useState<any[]>([]);
  const [nearExpiry, setNearExpiry] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const headers = {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        };

        const [rxRes, stockRes, expiryRes] = await Promise.all([
          fetch(`${API}/api/v1/pharmacy/prescriptions`, { headers }),
          fetch(`${API}/api/v1/pharmacy/inventory/low-stock`, { headers }),
          fetch(`${API}/api/v1/pharmacy/batches/near-expiry?days=60`, { headers })
        ]);

        if (rxRes.ok) {
          const rxData = await rxRes.json();
          setPrescriptions(rxData);
        }
        if (stockRes.ok) {
          const stockData = await stockRes.json();
          setLowStock(stockData);
        }
        if (expiryRes.ok) {
          const expiryData = await expiryRes.json();
          setNearExpiry(expiryData);
        }
      } catch (error) {
        console.error("Failed to fetch pharmacy data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const pendingRx = prescriptions.filter(r => r.status === "pending" || r.status === "approved");

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--accent-primary)]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Pharmacy Dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">Real-time overview of dispensary operations and inventory.</p>
        </div>
        <div className="flex gap-4">
          <Link
            href="/dashboard/pharmacy/inventory"
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:border-slate-300 hover:bg-slate-50 transition-colors shadow-sm text-sm font-medium"
          >
            <Package className="w-4 h-4" />
            Manage Inventory
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
        <WorkflowPipeline 
          title="Pharmacy Dispensing Pipeline" 
          colorScheme="violet"
          steps={[
            { label: "Prescription Received", status: "done" },
            { label: "Pharmacist Verification", status: "active" },
            { label: "Stock Allocation", status: "pending" },
            { label: "Medication Dispensing", status: "pending" },
            { label: "Inventory Deduction", status: "pending" },
            { label: "Billing Entry", status: "pending" }
          ]} 
        />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Pending Prescriptions</p>
              <h3 className="text-3xl font-bold text-slate-800">{pendingRx.length}</h3>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
              <ClipboardList className="w-5 h-5 text-blue-500" />
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-4 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            Awaiting dispensing
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Low Stock Alerts</p>
              <h3 className="text-3xl font-bold text-amber-600">{lowStock.length}</h3>
            </div>
            <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center">
              <TrendingDown className="w-5 h-5 text-amber-500" />
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-4 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            Items below threshold
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Near Expiry</p>
              <h3 className="text-3xl font-bold text-rose-600">{nearExpiry.length}</h3>
            </div>
            <div className="w-10 h-10 rounded-full bg-rose-50 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-rose-500" />
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-4 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            Expiring in 60 days
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Dispensed Today</p>
              <h3 className="text-3xl font-bold text-emerald-600">
                {prescriptions.filter(r => r.status === "dispensed").length}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-4 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Completed processes
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Prescriptions List */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
          <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <ClipboardList className="w-5 h-5 text-slate-400" />
              Pending Prescriptions
            </h2>
          </div>
          
          <div className="p-0 flex-1">
            {pendingRx.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                <CheckCircle2 className="w-12 h-12 mb-3 text-emerald-100" />
                <p>No pending prescriptions</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {pendingRx.map((rx) => (
                  <div key={rx.id} className="p-5 hover:bg-slate-50 transition-colors flex justify-between items-center group">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-slate-800">Prescription #{rx.id.split("-")[0]}</span>
                        <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 text-xs font-medium border border-blue-100">
                          {rx.status}
                        </span>
                      </div>
                      <p className="text-sm text-slate-500">{rx.items.length} items to dispense</p>
                      <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(rx.prescription_time).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <Link 
                        href={`/dashboard/pharmacy/prescriptions/${rx.id}`}
                        className="p-2 text-slate-400 bg-white border border-slate-200 rounded-lg group-hover:border-[var(--accent-primary)] group-hover:text-[var(--accent-primary)] transition-all flex items-center shadow-sm"
                      >
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Alerts / Stock Issues */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
          <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-slate-400" />
              Critical Inventory Alerts
            </h2>
          </div>
          
          <div className="p-0 flex-1">
            {lowStock.length === 0 && nearExpiry.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                <ShieldAlert className="w-12 h-12 mb-3 text-slate-100" />
                <p>No inventory alerts</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {/* Low Stock Items */}
                {lowStock.map((item) => (
                  <div key={`low-${item.id}`} className="p-5 flex gap-4 hover:bg-slate-50 transition-colors">
                    <div className="mt-1">
                      <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center border border-amber-100">
                        <TrendingDown className="w-4 h-4 text-amber-500" />
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-slate-800 flex items-center gap-2">
                        Low Stock Alert
                        <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 text-[10px] font-bold uppercase tracking-wider border border-amber-200">
                          Critical
                        </span>
                      </p>
                      <p className="text-sm text-slate-600 mt-1">
                        Drug ID <span className="font-mono text-xs">{item.drug_id.split("-")[0]}</span> has dropped below the threshold.
                      </p>
                      <div className="flex items-center gap-4 mt-2">
                        <div className="flex items-center gap-1.5 min-w-[120px]">
                          <span className="text-xs text-slate-400">Available:</span>
                          <span className="text-sm font-semibold text-amber-600">{item.quantity_available}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs text-slate-400">Threshold:</span>
                          <span className="text-sm font-medium text-slate-700">{item.reorder_threshold}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Near Expiry Items */}
                {nearExpiry.map((batch) => (
                  <div key={`exp-${batch.id}`} className="p-5 flex gap-4 hover:bg-slate-50 transition-colors">
                    <div className="mt-1">
                      <div className="w-8 h-8 rounded-full bg-rose-50 flex items-center justify-center border border-rose-100">
                        <AlertTriangle className="w-4 h-4 text-rose-500" />
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-slate-800 flex items-center gap-2">
                        Near Expiry Warning
                        <span className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 text-[10px] font-bold uppercase tracking-wider border border-rose-200">
                          Warning
                        </span>
                      </p>
                      <p className="text-sm text-slate-600 mt-1">
                        Batch <span className="font-mono text-xs font-semibold">{batch.batch_number}</span> is nearing its expiration date.
                      </p>
                      <div className="flex items-center gap-4 mt-2">
                        <div className="flex items-center gap-1.5 min-w-[120px]">
                          <span className="text-xs text-slate-400">Expires:</span>
                          <span className="text-sm font-semibold text-rose-600">{new Date(batch.expiry_date).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs text-slate-400">Quantity Affected:</span>
                          <span className="text-sm font-medium text-slate-700">{batch.quantity}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
