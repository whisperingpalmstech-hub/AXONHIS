"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Activity, Users, Bed, DollarSign, TrendingUp,
  AlertTriangle, Stethoscope, Pill, ShieldAlert, CheckCircle2,
  Calendar, FileText, BarChart, Download
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export default function AnalyticsDashboard() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("executive");
  const [data, setData] = useState<any>({
    executive: null,
    clinical: null,
    financial: null,
    operational: null,
    predictions: null,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      const headers = authHeaders();
      try {
        const [execRes, clinRes, finRes, opRes, predRes] = await Promise.allSettled([
          fetch(`${API}/api/v1/analytics/dashboards/executive`, { headers }),
          fetch(`${API}/api/v1/analytics/clinical-metrics`, { headers }),
          fetch(`${API}/api/v1/analytics/financial-metrics`, { headers }),
          fetch(`${API}/api/v1/analytics/operational-metrics`, { headers }),
          fetch(`${API}/api/v1/analytics/predictions`, { headers }),
        ]);

        const getJson = async (r: PromiseSettledResult<Response>) => {
          if (r.status === "fulfilled" && r.value.ok) return r.value.json();
          return null;
        };

        const [executive, clinical, financial, operational, predictions] = await Promise.all([
          getJson(execRes),
          getJson(clinRes),
          getJson(finRes),
          getJson(opRes),
          getJson(predRes),
        ]);

        setData({
          executive,
          clinical,
          financial,
          operational,
          predictions
        });
      } catch (e) {
        console.error("Failed to load analytics: ", e);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  const TABS = [
    { id: "executive", label: "Executive" },
    { id: "clinical", label: "Clinical" },
    { id: "financial", label: "Financial" },
    { id: "operational", label: "Operations" },
  ];

  const renderTabContent = () => {
    if (loading) {
      return (
        <div className="flex h-64 items-center justify-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      );
    }

    switch (activeTab) {
      case "executive":
        return <ExecutiveDashboard data={data.executive} predictions={data.predictions} />;
      case "clinical":
        return <ClinicalDashboard data={data.clinical} />;
      case "financial":
        return <FinancialDashboard data={data.financial} />;
      case "operational":
        return <OperationsDashboard data={data.operational} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-50 min-h-screen">
      <TopNav title={t("analytics.title")} />
      <div className="p-8 max-w-7xl mx-auto w-full">
        {/* Header section with tabs */}
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">{t("analytics.title")}</h1>
            <p className="mt-2 text-sm text-slate-500 max-w-2xl">
              {t("analytics.subtitle")}
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex items-center gap-4">
            <div className="bg-white p-1 rounded-xl shadow-sm border border-slate-200 inline-flex">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-5 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                    activeTab === tab.id
                      ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            
            {activeTab !== "executive" && (
              <button
                onClick={() => {
                  window.location.href = `${API}/api/v1/analytics/reports/export?report_type=${activeTab}&days=30`;
                }}
                className="inline-flex items-center gap-2 bg-white border border-slate-200 text-slate-700 px-4 py-2.5 rounded-xl hover:bg-slate-50 hover:text-blue-600 transition-colors shadow-sm font-medium text-sm"
              >
                <Download size={18} />
                Export CSV
              </button>
            )}
          </div>
        </div>

        {/* Dynamic Content */}
        <div className="transition-all duration-500">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color, bg, subtext }: any) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-lg transition-shadow duration-300 relative overflow-hidden group">
      <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${color}`}>
        <Icon size={80} className="transform translate-x-4 -translate-y-4" />
      </div>
      <div className="flex items-center gap-4 mb-4 relative z-10">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${bg}`}>
          <Icon className={color} size={24} />
        </div>
        <h3 className="text-slate-600 font-medium">{title}</h3>
      </div>
      <div className="relative z-10">
        <p className="text-3xl font-bold text-slate-900">{value !== undefined ? value : '--'}</p>
        {subtext && <p className="text-sm text-slate-500 mt-2">{subtext}</p>}
      </div>
    </div>
  );
}

function ExecutiveDashboard({ data, predictions }: { data: any, predictions: any }) {
  const d = data || {};
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Daily Admissions" value={d.daily_admissions} icon={Users} color="text-blue-600" bg="bg-blue-100" subtext="In the last 24 hours" />
        <StatCard title="Daily Revenue" value={`$${(d.daily_revenue || 0).toLocaleString()}`} icon={DollarSign} color="text-emerald-600" bg="bg-emerald-100" subtext="Collected today" />
        <StatCard title="Bed Occupancy" value={`${(d.bed_occupancy_rate || 0).toFixed(1)}%`} icon={Bed} color="text-purple-600" bg="bg-purple-100" subtext="Current utilization" />
        <StatCard title="Critical Alerts" value={d.critical_alerts_count} icon={AlertTriangle} color="text-rose-600" bg="bg-rose-100" subtext="Require immediate attention" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core metrics visual proxy */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <BarChart className="text-indigo-600" size={20} />
              Hospital Performance Overview
            </h3>
          </div>
          <div className="h-64 flex flex-col items-center justify-center bg-slate-50 rounded-xl border border-dashed border-slate-300">
            <TrendingUp size={48} className="text-slate-300 mb-4" />
            <p className="text-slate-500">Performance graph integration pending.</p>
          </div>
        </div>

        {/* Predictions */}
        <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-2xl shadow-lg border border-indigo-800 p-6 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 -m-8 mix-blend-overlay opacity-30">
            <Activity size={120} />
          </div>
          <h3 className="text-lg font-bold flex items-center gap-2 mb-6">
            <Activity size={20} className="text-indigo-400" />
            AI Predictive Insights
          </h3>
          <div className="space-y-4 relative z-10">
            {d.predictions && d.predictions.length > 0 ? d.predictions.map((p: any, i: number) => {
              const confidence = p.confidence_score ? p.confidence_score * 100 : 90; // Fallback to 90%
              return (
              <div key={i} className="bg-white/10 backdrop-blur-sm border border-white/20 p-4 rounded-xl hover:bg-white/20 transition-colors">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-indigo-200 text-sm font-medium uppercase tracking-wider">{p.prediction_type.replace('_', ' ')}</span>
                  <span className="text-xs bg-indigo-500/30 text-indigo-200 px-2 py-1 rounded-md">{new Date(p.target_date).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between items-end">
                  <span className="text-2xl font-bold text-white">{p.predicted_value.toFixed(1)}</span>
                  <span className="text-sm text-indigo-300">Conf: {confidence.toFixed(0)}%</span>
                </div>
              </div>
            )}) : (
              <p className="text-indigo-200/70 text-center py-8">No active predictions available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ClinicalDashboard({ data }: { data: any }) {
  const latest = data && data.length > 0 ? data[0] : {};
  return (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Avg Length of Stay" value={`${(latest.average_los_hours || 0).toFixed(1)} hrs`} icon={Clock} color="text-teal-600" bg="bg-teal-100" />
        <StatCard title="Readmission Rate" value={`${(latest.readmission_rate || 0).toFixed(1)}%`} icon={TrendingUp} color="text-orange-600" bg="bg-orange-100" />
        <StatCard title="Admissions Today" value={latest.admissions_count} icon={Stethoscope} color="text-indigo-600" bg="bg-indigo-100" />
        <StatCard title="Critical Alerts" value={latest.critical_alerts_count} icon={ShieldAlert} color="text-rose-600" bg="bg-rose-100" />
      </div>
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Historical Clinical Metrics</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium rounded-l-lg">Date</th>
                <th className="px-4 py-3 font-medium">Admissions</th>
                <th className="px-4 py-3 font-medium">Avg LOS</th>
                <th className="px-4 py-3 font-medium">Readmission Rate</th>
                <th className="px-4 py-3 font-medium rounded-r-lg">Critical Alerts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data && data.length > 0 ? data.map((d: any, i: number) => (
                <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-4 py-3 text-slate-900 font-medium">{new Date(d.date).toLocaleDateString()}</td>
                  <td className="px-4 py-3">{d.admissions_count}</td>
                  <td className="px-4 py-3">{d.average_los_hours.toFixed(1)}h</td>
                  <td className="px-4 py-3">{d.readmission_rate.toFixed(1)}%</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${d.critical_alerts_count > 10 ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-700'}`}>
                      {d.critical_alerts_count}
                    </span>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-slate-500">No clinical metric data available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function FinancialDashboard({ data }: { data: any }) {
  const latest = data && data.length > 0 ? data[0] : {};
  return (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Daily Revenue" value={`$${(latest.daily_revenue || 0).toLocaleString()}`} icon={DollarSign} color="text-emerald-600" bg="bg-emerald-100" />
        <StatCard title="Outstanding Invoices" value={`$${(latest.outstanding_invoices_amount || 0).toLocaleString()}`} icon={FileText} color="text-amber-600" bg="bg-amber-100" />
        <StatCard title="Completed Claims" value={latest.claims_completed} icon={CheckCircle2} color="text-blue-600" bg="bg-blue-100" />
        <StatCard title="Rejected Claims" value={latest.claims_rejected} icon={AlertTriangle} color="text-rose-600" bg="bg-rose-100" />
      </div>
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Daily Financial Snapshot</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium rounded-l-lg">Date</th>
                <th className="px-4 py-3 font-medium">Revenue</th>
                <th className="px-4 py-3 font-medium">Outstanding</th>
                <th className="px-4 py-3 font-medium">Completed Claims</th>
                <th className="px-4 py-3 font-medium rounded-r-lg">Rejected Claims</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data && data.length > 0 ? data.map((d: any, i: number) => (
                <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-4 py-3 text-slate-900 font-medium">{new Date(d.date).toLocaleDateString()}</td>
                  <td className="px-4 py-3 font-medium text-emerald-600">${d.daily_revenue.toLocaleString()}</td>
                  <td className="px-4 py-3 text-slate-600">${d.outstanding_invoices_amount.toLocaleString()}</td>
                  <td className="px-4 py-3">{d.claims_completed}</td>
                  <td className="px-4 py-3 text-rose-600">{d.claims_rejected}</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-slate-500">No financial data available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function OperationsDashboard({ data }: { data: any }) {
  const latest = data && data.length > 0 ? data[0] : {};
  return (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Bed Occupancy" value={`${(latest.bed_occupancy_rate || 0).toFixed(1)}%`} icon={Bed} color="text-purple-600" bg="bg-purple-100" />
        <StatCard title="Staff On Duty" value={latest.staff_on_duty} icon={Users} color="text-blue-600" bg="bg-blue-100" />
        <StatCard title="Patient Throughput" value={latest.patient_throughput} icon={Activity} color="text-emerald-600" bg="bg-emerald-100" />
        <StatCard title="Avg Wait Time" value={`${(latest.avg_wait_time_minutes || 0).toFixed(0)} min`} icon={Calendar} color="text-amber-600" bg="bg-amber-100" />
      </div>
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Operational Efficiency Trends</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium rounded-l-lg">Date</th>
                <th className="px-4 py-3 font-medium">Occupancy Rate</th>
                <th className="px-4 py-3 font-medium">Staff On Duty</th>
                <th className="px-4 py-3 font-medium">Throughput</th>
                <th className="px-4 py-3 font-medium rounded-r-lg">Avg Wait Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data && data.length > 0 ? data.map((d: any, i: number) => (
                <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-4 py-3 text-slate-900 font-medium">{new Date(d.date ? d.date : d.metric_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div className={`h-full ${(d.bed_occupancy_rate || 0) > 85 ? 'bg-rose-500' : 'bg-purple-500'}`} style={{ width: `${d.bed_occupancy_rate || 0}%` }}></div>
                      </div>
                      <span>{(d.bed_occupancy_rate || 0).toFixed(1)}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">{d.staff_on_duty || 0}</td>
                  <td className="px-4 py-3">{d.patient_throughput || 0}</td>
                  <td className="px-4 py-3">{(d.avg_wait_time_minutes || 0).toFixed(0)}m</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-slate-500">No operational data available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Ensure the use of 'lucide-react' icons Clock instead of Calendar in stat cards where applicable.
function Clock({ size, className }: any) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="10"></circle>
      <polyline points="12 6 12 12 16 14"></polyline>
    </svg>
  );
}
