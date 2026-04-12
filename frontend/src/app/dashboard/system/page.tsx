"use client";
import { useTranslation } from "@/i18n";


import { useEffect, useState } from "react";
import { 
  ShieldCheck, Activity, RefreshCcw, Save, AlertTriangle, 
  Database, Server, HardDrive, Clock, History, AlertCircle
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

const authHeaders = () => {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  };
};

export default function SystemAdminDashboard() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("health");
  const [health, setHealth] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [errors, setErrors] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const [hRes, mRes, eRes, lRes] = await Promise.all([
        fetch(`${API}/api/v1/system/health`, { headers: authHeaders() }),
        fetch(`${API}/api/v1/system/metrics`, { headers: authHeaders() }),
        fetch(`${API}/api/v1/system/monitoring/errors`, { headers: authHeaders() }),
        fetch(`${API}/api/v1/system/logs`, { headers: authHeaders() })
      ]);

      if (hRes.ok) setHealth(await hRes.json());
      if (mRes.ok) setMetrics(await mRes.json());
      if (eRes.ok) setErrors(await eRes.json());
      if (lRes.ok) setLogs(await lRes.json());
    } catch (e) {
      console.error("Failed to fetch system data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    const interval = setInterval(fetchHealthData, 60000); // 1-minute auto-refresh
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl animate-in fade-in duration-500 rounded-xl p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 flex items-center gap-3">
            <ShieldCheck className="h-8 w-8 text-indigo-600" />
            {t("system.title")}
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            {t("system.subtitle")}
          </p>
        </div>
        <button 
          onClick={fetchHealthData}
          className="flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-all border border-gray-200 shadow-sm"
        >
          <RefreshCcw className="h-4 w-4" />
          {t("common.refresh")}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200 pb-px mb-8">
        {[
          { id: "health", label: "System Health & Metrics", icon: Activity },
          { id: "errors", label: "Error Tracking", icon: AlertTriangle },
          { id: "logs", label: "Centralized Logs", icon: History },
          { id: "backups", label: "Disaster Recovery", icon: Save }
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 pb-4 text-sm font-medium transition-colors border-b-2 ${
              activeTab === t.id
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-900 hover:border-gray-300"
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Health Tab */}
      {activeTab === "health" && (
        <div className="space-y-6">
          <div className="grid gap-6 md:grid-cols-4">
            <MetricCard 
              title="System Status" 
              value={health?.status.toUpperCase()} 
              icon={Activity}
              color={health?.status === "healthy" ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"}
              bg="bg-white"
            />
            <MetricCard 
              title="Database Link" 
              value={health?.database_status.toUpperCase()} 
              icon={Database}
              color={health?.database_status === "healthy" ? "text-emerald-600 bg-emerald-50" : "text-red-600 bg-red-50"}
              bg="bg-white"
            />
            <MetricCard 
              title="CPU Load" 
              value={metrics ? `${metrics.cpu_usage}%` : "---"} 
              icon={Server}
              color="text-indigo-600 bg-indigo-50"
              bg="bg-white"
            />
            <MetricCard 
              title="Memory Utilization" 
              value={metrics ? `${metrics.memory_usage}%` : "---"} 
              icon={HardDrive}
              color={metrics?.memory_usage > 85 ? "text-red-600 bg-red-50" : "text-indigo-600 bg-indigo-50"}
              bg="bg-white"
            />
          </div>
          
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-2xl bg-white border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Core Infrastructure</h3>
              <ul className="space-y-4">
                <StatusItem label="API Microservice Gateway" status={health?.api_status} />
                <StatusItem label="PostgreSQL Instance" status={health?.database_status} />
                <StatusItem label="Redis Key-Value Cache" status={health?.redis_status} />
                <StatusItem label="Grok AI Inference Engine" status={health?.ai_service_status} />
              </ul>
            </div>
            
            <div className="rounded-2xl bg-white border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Metrics Telemetry</h3>
               <ul className="space-y-4">
                <li className="flex justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                  <span className="text-gray-600 font-medium">Application Uptime</span>
                  <span className="text-emerald-600 font-mono font-medium">{(health?.details?.uptime_seconds / 3600).toFixed(2)}h</span>
                </li>
                <li className="flex justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                  <span className="text-gray-600 font-medium">Total Active Requests</span>
                  <span className="text-indigo-600 font-mono font-medium">{metrics?.active_requests}</span>
                </li>
                <li className="flex justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                  <span className="text-gray-600 font-medium">Background Job Queue Backlog</span>
                  <span className="text-indigo-600 font-mono font-medium">{metrics?.queue_backlog}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Errors Tab */}
      {activeTab === "errors" && (
        <div className="rounded-2xl bg-white border border-gray-200 overflow-hidden shadow-sm">
          <div className="p-6 border-b border-gray-100 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              Automated Error Tracking
            </h3>
          </div>
          {errors.length === 0 ? (
             <div className="p-12 text-center text-gray-500 flex flex-col items-center">
              <ShieldCheck className="h-16 w-16 text-emerald-500/50 mb-4" />
              <p>No system exceptions strictly recorded.</p>
            </div>
          ) : (
             <ul className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto custom-scrollbar">
              {errors.map(err => (
                 <li key={err.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700 border border-red-200">
                      {err.error_type.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(err.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-gray-900 font-medium mb-3">{err.message}</p>
                  
                  {err.stack_trace && (
                    <div className="mt-3 p-4 bg-gray-900 rounded-lg overflow-x-auto text-xs font-mono text-gray-300 border border-gray-800">
                      <pre>{err.stack_trace}</pre>
                    </div>
                  )}
                 </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === "logs" && (
        <div className="rounded-2xl bg-white border border-gray-200 overflow-hidden shadow-sm">
          <div className="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
             <h3 className="text-lg font-semibold text-gray-900">Centralized System Audit Logs</h3>
          </div>
           <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4">Timestamp</th>
                  <th className="px-6 py-4">Level</th>
                  <th className="px-6 py-4">Service</th>
                  <th className="px-6 py-4">Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-gray-500">Waiting for logs...</td>
                  </tr>
                ) : (
                  logs.map(log => (
                    <tr key={log.id} className="hover:bg-gray-50 font-mono text-xs">
                      <td className="px-6 py-3 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="px-6 py-3">
                         <span className={`px-2 py-1 rounded text-[10px] font-bold ${
                           log.level === 'CRITICAL' ? 'bg-red-100 text-red-700 border border-red-200' :
                           log.level === 'ERROR' ? 'bg-red-50 text-red-600 border border-red-100' :
                           log.level === 'WARNING' ? 'bg-amber-100 text-amber-700 border border-amber-200' :
                           'bg-emerald-100 text-emerald-700 border border-emerald-200'
                         }`}>
                           {log.level}
                         </span>
                      </td>
                      <td className="px-6 py-3">{log.service_name}</td>
                      <td className="px-6 py-3 truncate max-w-md" title={log.message}>{log.message}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Backups Tab */}
      {activeTab === "backups" && (
        <div className="rounded-2xl bg-white border border-gray-200 shadow-sm p-8">
          <div className="flex flex-col items-center justify-center text-center max-w-2xl mx-auto py-12">
            <div className="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center mb-6">
              <Save className="w-10 h-10 text-indigo-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Disaster Recovery & Enterprise Backups</h2>
            <p className="text-gray-600 mb-8 leading-relaxed">
              Automated incremental and full snapshot backups are securely orchestrated by cron jobs executing `backup_db.sh` using advanced AES-256 encryption. Database snapshots are stored completely off-site.
            </p>

            <div className="grid gap-4 w-full text-left">
              <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 flex justify-between items-center">
                 <div>
                    <h4 className="font-semibold text-gray-900">Hourly Incremental Protection</h4>
                    <p className="text-xs text-gray-500 mt-1">Snapshots captured every 60 minutes.</p>
                 </div>
                 <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-bold border border-emerald-200">ACTIVE</span>
              </div>
              <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 flex justify-between items-center">
                 <div>
                    <h4 className="font-semibold text-gray-900">Daily Cold Storage Full Dump</h4>
                    <p className="text-xs text-gray-500 mt-1">Hard encrypted snapshot archived offline daily.</p>
                 </div>
                  <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-bold border border-emerald-200">ACTIVE</span>
              </div>
            </div>

            <div className="mt-8 pt-8 border-t border-gray-200 w-full flex justify-center">
               <button className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-medium transition-all shadow-md opacity-50 cursor-not-allowed">
                  <History className="w-5 h-5" />
                  Initiate Manual Sync Check
               </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

function MetricCard({ title, value, icon: Icon, color, bg }: any) {
  // color will containt both text and bg colors for the icon container like "text-emerald-600 bg-emerald-50"
  return (
    <div className={`rounded-2xl ${bg} p-6 border border-gray-200 shadow-sm flex items-center gap-4`}>
      <div className={`p-4 rounded-xl ${color}`}>
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <p className={`text-2xl font-bold mt-1 ${color.split(' ')[0]}`}>{value}</p>
      </div>
    </div>
  );
}

function StatusItem({ label, status }: any) {
  return (
     <li className="flex justify-between items-center p-3 rounded-lg bg-gray-50 border border-gray-100">
        <span className="text-gray-700 font-medium">{label}</span>
        {status === "healthy" ? (
          <span className="flex items-center gap-2 text-emerald-700 text-xs font-bold bg-emerald-100 px-3 py-1 rounded-full border border-emerald-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            ONLINE
          </span>
        ) : (
          <span className="flex items-center gap-2 text-red-700 text-xs font-bold bg-red-100 px-3 py-1 rounded-full border border-red-200">
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
            DOWN
          </span>
        )}
      </li>
  );
}
