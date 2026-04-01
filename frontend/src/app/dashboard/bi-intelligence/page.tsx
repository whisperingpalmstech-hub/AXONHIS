"use client";
import { useTranslation } from "@/i18n";


import React, { useEffect, useState } from "react";
import { 
    BarChart3, 
    LineChart, 
    PieChart, 
    Activity, 
    Users, 
    Clock, 
    TrendingUp, 
    Stethoscope, 
    DollarSign,
    Target,
    Download,
    BrainCircuit,
    AlertTriangle
} from "lucide-react";
import { biApi } from "../../../lib/bi-api";

export default function HospitalIntelligencePage() {
  const { t } = useTranslation();
    const [realTimeStats, setRealTimeStats] = useState<any>(null);
    const [finances, setFinances] = useState<any[]>([]);
    const [productivity, setProductivity] = useState<any[]>([]);
    const [clinical, setClinical] = useState<any[]>([]);
    const [predictions, setPredictions] = useState<any[]>([]);
    const [management, setManagement] = useState<any>(null);

    const [activeTab, setActiveTab] = useState("OPERATIONAL");

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const today = new Date().toISOString().split('T')[0];
            const [
                statsRes, 
                finRes, 
                prodRes, 
                clinRes, 
                predRes, 
                mgmtRes
            ] = await Promise.all([
                biApi.getRealTimeDashboard(),
                biApi.getFinancialAnalytics(),
                biApi.getDoctorProductivity(),
                biApi.getClinicalStatistics(),
                biApi.getCrowdForecasting(today),
                biApi.getManagementIntelligence()
            ]);

            setRealTimeStats(statsRes);
            setFinances(finRes);
            setProductivity(prodRes);
            setClinical(clinRes);
            setPredictions(predRes);
            setManagement(mgmtRes);
        } catch (error) {
            console.error("Failed to load analytics engine", error);
        }
    };

    const handleExport = async (format: string) => {
        try {
            const req = {
                report_type: activeTab,
                format: format,
                date_range_start: new Date().toISOString().split('T')[0],
                date_range_end: new Date().toISOString().split('T')[0],
            };
            const response = await biApi.generateExportReport(req);
            alert(`Report Generated: ${response.message}\nLink: ${response.file_url}`);
        } catch (error) {
            alert("Export generation failed.");
        }
    };

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto text-[var(--text-primary)]">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <BrainCircuit className="text-[var(--accent-primary)]" size={32} />
                        {t("biIntelligence.title")} & Analytics Engine
                    </h1>
                    <p className="text-[var(--text-secondary)] mt-2 font-medium">
                        Real-Time Operational Cockpit & Predictive Forecasting
                    </p>
                </div>
                
                <div className="flex gap-2">
                    <button onClick={() => handleExport("PDF")} className="btn btn-outline flex items-center gap-2">
                        <Download size={16} /> Export PDF
                    </button>
                    <button onClick={() => handleExport("Excel")} className="btn btn-outline flex items-center gap-2">
                        <Download size={16} /> Export Excel
                    </button>
                </div>
            </header>

            {/* Top Stat Cards - Always Visible Real-time Operations */}
            <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-5 gap-4">
                <div className="bg-[var(--bg-card)] rounded-2xl p-5 border border-[var(--border)] shadow-sm flex flex-col justify-between relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10"><Users size={48} /></div>
                    <span className="text-sm font-semibold flex items-center gap-2 text-slate-400">
                        <Users size={16} className="text-blue-400"/> Patients Registered
                    </span>
                    <span className="text-3xl font-black mt-4">{realTimeStats?.total_patients_registered_today || 0}</span>
                </div>

                <div className="bg-[var(--bg-card)] rounded-2xl p-5 border border-[var(--border)] shadow-sm flex flex-col justify-between relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10"><Activity size={48} /></div>
                    <span className="text-sm font-semibold flex items-center gap-2 text-slate-400">
                        <Activity size={16} className="text-indigo-400"/> Active OPD Visits
                    </span>
                    <span className="text-3xl font-black mt-4">{realTimeStats?.total_opd_visits_today || 0}</span>
                </div>

                <div className="bg-[var(--bg-card)] rounded-2xl p-5 border border-[var(--border)] shadow-sm flex flex-col justify-between relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10"><Clock size={48} /></div>
                    <span className="text-sm font-semibold flex items-center gap-2 text-slate-400">
                        <Clock size={16} className="text-orange-400"/> Currently Waiting
                    </span>
                    <span className="text-3xl font-black mt-4">{realTimeStats?.patients_waiting || 0}</span>
                </div>

                <div className="bg-[var(--bg-card)] rounded-2xl p-5 border border-[var(--border)] shadow-sm flex flex-col justify-between relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10"><TrendingUp size={48} /></div>
                    <span className="text-sm font-semibold flex items-center gap-2 text-slate-400">
                        <TrendingUp size={16} className="text-red-400"/> Avg Wait Time
                    </span>
                    <span className="text-3xl font-black mt-4">{realTimeStats?.avg_waiting_time_mins || 0} <span className="text-sm font-normal text-slate-400">mins</span></span>
                </div>
                
                <div className="bg-[var(--bg-card)] rounded-2xl p-5 border border-[var(--border)] shadow-sm flex flex-col justify-between relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10"><Stethoscope size={48} /></div>
                    <span className="text-sm font-semibold flex items-center gap-2 text-slate-400">
                        <Stethoscope size={16} className="text-green-400"/> In Consultation
                    </span>
                    <span className="text-3xl font-black mt-4 text-green-500">{realTimeStats?.patients_in_consultation || 0}</span>
                </div>
            </div>

            {/* Tabbed Intelligent Workspace */}
            <div className="bg-[var(--bg-card)] rounded-xl border border-[var(--border)] overflow-hidden">
                <div className="flex border-b border-[var(--border)] px-4 pt-4 gap-4 overflow-x-auto">
                    {[
                        { id: "OPERATIONAL", label: "Predictive Flow", icon: BarChart3 },
                        { id: "PRODUCTIVITY", label: "Doctor Analytics", icon: Users },
                        { id: "FINANCIAL", label: "Revenue Matrix", icon: DollarSign },
                        { id: "CLINICAL", label: "Clinical Intelligence", icon: Activity },
                        { id: "MANAGEMENT", label: "Management Dashboard", icon: Target },
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-4 py-3 font-semibold transition-colors border-b-2
                                ${activeTab === tab.id ? 'border-[var(--accent-primary)] text-[var(--accent-primary)]' : 'border-transparent hover:text-white text-slate-400'}
                            `}
                        >
                            <tab.icon size={18} /> {tab.label}
                        </button>
                    ))}
                </div>

                <div className="p-6 space-y-6">
                    {/* Predictive Flow Tab */}
                    {activeTab === "OPERATIONAL" && (
                        <div>
                            <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><BrainCircuit size={20}/> AI Crowd Forecasting</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {(predictions || []).map((pred, i) => (
                                    <div key={i} className={`p-5 rounded-xl border flex flex-col gap-2 ${pred?.is_anomaly_alert ? 'bg-red-900/10 border-red-500/30' : 'bg-slate-800/30 border-[var(--border)]'}`}>
                                        <div className="flex justify-between items-center">
                                            <span className="font-bold text-lg">{pred?.department}</span>
                                            {pred?.is_anomaly_alert && <span className="flex items-center gap-1 text-xs bg-red-500/20 text-red-500 px-2 py-1 rounded-full"><AlertTriangle size={12}/> High Volume Alert</span>}
                                        </div>
                                        <div className="text-slate-400 text-sm">Predicted Footfall</div>
                                        <div className="text-3xl font-black">{pred?.predicted_footfall} <span className="text-sm font-normal text-slate-500 text-xs">patients</span></div>
                                        <div className="bg-[var(--bg-surface)] p-3 rounded-lg mt-2 flex items-center gap-3">
                                            <Clock size={16} className="text-[var(--accent-primary)]"/>
                                            <span className="text-sm font-medium">Expected Peak: <span className="text-white">{pred?.peak_hours_expected}</span></span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Productivity Tab */}
                    {activeTab === "PRODUCTIVITY" && (
                        <div>
                            <h3 className="text-xl font-bold mb-4">Doctor Workload Distribution</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="border-b border-[var(--border)] text-slate-400 text-sm">
                                            <th className="py-3 px-4 font-semibold">Doctor Name</th>
                                            <th className="py-3 px-4 font-semibold">Department</th>
                                            <th className="py-3 px-4 font-semibold text-right">Patients Seen</th>
                                            <th className="py-3 px-4 font-semibold text-right">Avg Consult Time</th>
                                            <th className="py-3 px-4 font-semibold text-right">Revenue Generated</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[var(--border)]">
                                        {(productivity || []).map((doc, i) => (
                                            <tr key={i} className="hover:bg-slate-800/20 transition-colors">
                                                <td className="py-3 px-4 font-semibold">{doc?.doctor_name}</td>
                                                <td className="py-3 px-4 text-slate-400">{doc?.department}</td>
                                                <td className="py-3 px-4 text-right text-lg">{doc?.patients_seen}</td>
                                                <td className="py-3 px-4 text-right font-mono">{doc?.avg_consult_time_mins} min</td>
                                                <td className="py-3 px-4 text-right text-green-400 font-mono">₹{doc?.revenue_generated?.toLocaleString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Financial Tab */}
                    {activeTab === "FINANCIAL" && (
                        <div>
                            <h3 className="text-xl font-bold mb-4">Departmental Revenue Matrix</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {(finances || []).map((fin, i) => (
                                    <div key={i} className="bg-gradient-to-br from-slate-800 to-slate-900 border border-[var(--border)] rounded-xl p-5">
                                        <div className="text-slate-400 font-semibold mb-2">{fin?.department}</div>
                                        <div className="text-3xl font-bold text-[var(--accent-primary)]">
                                            ₹{fin?.net_revenue?.toLocaleString()}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Clinical Tab */}
                    {activeTab === "CLINICAL" && (
                        <div>
                            <h3 className="text-xl font-bold mb-4">Top Diagnostic Code Analysis</h3>
                            <div className="flex flex-col gap-3">
                                {(clinical || []).map((clin, i) => (
                                    <div key={i} className="bg-[var(--bg-surface)] p-4 rounded-xl border border-[var(--border)] flex justify-between items-center">
                                        <span className="font-semibold text-[var(--text-primary)]">{clin?.disease_name}</span>
                                        <div className="flex items-center gap-3">
                                            <span className="text-slate-400 text-sm">Incidence</span>
                                            <span className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full font-bold">{clin?.incidence_count}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Management Tab */}
                    {activeTab === "MANAGEMENT" && management && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="border border-[var(--border)] p-6 rounded-xl bg-slate-800/20">
                                <h4 className="font-bold text-lg mb-4 flex items-center gap-2"><PieChart size={18}/> Referral Sources</h4>
                                <div className="space-y-4">
                                    {Object.entries(management.referral_sources).map(([source, pct]: any) => (
                                        <div key={source}>
                                            <div className="flex justify-between mb-1 text-sm font-medium">
                                                <span>{source}</span>
                                                <span>{pct}%</span>
                                            </div>
                                            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                                <div className="h-full bg-[var(--accent-primary)]" style={{ width: `${pct}%` }}></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            
                            <div className="border border-[var(--border)] p-6 rounded-xl bg-slate-800/20 flex flex-col justify-center items-center text-center">
                                <Target size={48} className="text-emerald-400 mb-4 opacity-70"/>
                                <div className="text-sm font-bold text-slate-400 uppercase tracking-widest">Patient Retention Rate</div>
                                <div className="text-6xl font-black text-emerald-400 mt-2">{management.retention_rate_pct}%</div>
                                <div className="text-sm text-slate-400 mt-2">Overall cohort returning within 12 months</div>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}
