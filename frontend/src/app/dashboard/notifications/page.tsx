"use client";
import { useTranslation } from "@/i18n";

import React, { useEffect, useState } from "react";
import { Bell, CheckCircle, Info, AlertTriangle } from "lucide-react";

export default function NotificationsPage() {
  const { t } = useTranslation();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API}/api/v1/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to fetch notifications");
      const data = await res.json();
      setNotifications(data.items || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const markRead = async (id: string) => {
    try {
      const token = localStorage.getItem("access_token");
      await fetch(`${API}/api/v1/notifications/${id}/read`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  const markAllRead = async () => {
    try {
      const token = localStorage.getItem("access_token");
      await fetch(`${API}/api/v1/notifications/read-all`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  const getIcon = (type: string) => {
    if (type.includes("alert")) return <AlertTriangle className="text-rose-500" size={24} />;
    if (type.includes("success")) return <CheckCircle className="text-emerald-500" size={24} />;
    return <Info className="text-blue-500" size={24} />;
  };

  return (
    <div className="p-8 max-w-5xl mx-auto animate-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            <Bell className="text-slate-700" size={32} />
             {t("notifications.title")}
          </h1>
          <p className="mt-2 text-slate-500">{t("notifications.subtitle")}</p>
        </div>
        <button 
          onClick={markAllRead} 
          className="bg-slate-900 text-white px-5 py-2.5 rounded-lg shadow-md font-medium hover:bg-slate-800 transition-colors text-sm"
        >
          {t("notifications.markAllRead")}
        </button>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm rounded-2xl overflow-hidden min-h-[400px]">
        {loading ? (
          <div className="p-12 text-center text-slate-500">{t("notifications.loading")}</div>
        ) : error ? (
          <div className="p-12 text-center text-rose-500 bg-rose-50 m-4 rounded-xl border border-rose-200">{error}</div>
        ) : notifications.length === 0 ? (
          <div className="p-20 text-center flex flex-col items-center">
            <CheckCircle className="text-emerald-400 mb-6" size={64} />
            <p className="text-2xl font-bold text-slate-900">{t("notifications.noNotifications")}</p>
            <p className="text-slate-500 mt-2">{t("common.noData")}</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {notifications.map((n) => (
              <div key={n.id} className={`p-6 flex gap-4 items-start transition-colors ${!n.read_at ? 'bg-blue-50/50' : 'bg-white hover:bg-slate-50'}`}>
                <div className="flex-shrink-0 mt-1">
                  {getIcon(n.notification_type)}
                </div>
                <div className="flex-1">
                  <h3 className={`text-base tracking-wide ${!n.read_at ? 'font-bold text-slate-900' : 'font-medium text-slate-700'}`}>
                    {n.title}
                  </h3>
                  <p className="text-slate-600 mt-1 text-sm leading-relaxed">{n.message}</p>
                  <p className="text-xs text-slate-400 mt-3 font-mono">
                    {new Date(n.created_at).toLocaleString()} 
                    {n.read_at && ` • Read: ${new Date(n.read_at).toLocaleString()}`}
                  </p>
                </div>
                {!n.read_at && (
                  <button onClick={() => markRead(n.id)} className="flex-shrink-0 text-sm font-bold text-blue-600 hover:text-blue-800 bg-blue-100 px-3 py-1.5 rounded-lg transition-colors">
                    {t("notifications.markAsRead")}
                  </button>
                )}
              </div>
             ))}
          </div>
        )}
      </div>
    </div>
  );
}
