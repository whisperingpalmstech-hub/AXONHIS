"use client";
import { useTranslation } from "@/i18n";

import React, { useEffect, useState } from "react";
import { Settings, Save, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const { t } = useTranslation();
  const [configs, setConfigs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API}/api/v1/config`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to fetch settings");
      const data = await res.json();
      setConfigs(data || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-in slide-in-from-right-4 duration-500">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            <Settings className="text-slate-700" size={32} />
            {t("settings.title")}
          </h1>
          <p className="mt-2 text-slate-500">{t("settings.subtitle")}</p>
        </div>
        <button onClick={fetchConfigs} className="bg-white border border-slate-200 text-slate-700 px-5 py-2.5 rounded-lg font-medium shadow-sm hover:bg-slate-50 transition-colors flex items-center gap-2">
          <RefreshCw size={18} />
          <span>{t("common.refresh")}</span>
        </button>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">{t("settings.loading")}</div>
        ) : error ? (
          <div className="p-12 text-center text-rose-500 bg-rose-50">{error}</div>
        ) : configs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">{t("settings.noConfigs")}</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {configs.map((c) => (
              <div key={c.key} className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50 transition-colors group">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-slate-900 tracking-wide">{c.key}</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">{c.category}</span>
                  </div>
                  <p className="text-sm text-slate-500 max-w-2xl">{c.description || t("settings.noDescription")}</p>
                  <p className="text-xs text-slate-400 mt-2">{t("settings.lastUpdated")}: {new Date(c.updated_at).toLocaleString()}</p>
                </div>
                <div className="flex-shrink-0 w-full sm:w-1/3">
                  <input
                    type="text"
                    defaultValue={c.value}
                    className="w-full bg-slate-100 text-slate-800 border-none rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 font-mono transition-shadow h-10"
                    placeholder={t("settings.valuePlaceholder")}
                  />
                </div>
                <div>
                  <button className="h-10 px-4 bg-white border border-slate-200 shadow-sm rounded-lg hover:bg-blue-50 text-slate-600 hover:text-blue-600 transition-colors font-medium text-sm flex items-center gap-2">
                    <Save size={16} />
                    {t("common.save")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
