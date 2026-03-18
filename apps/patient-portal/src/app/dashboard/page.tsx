"use client";

import React, { useState, useEffect } from 'react';
import { 
  Calendar, FileText, Activity, CreditCard, 
  Video, LogOut, Bell, User 
} from 'lucide-react';
import { portalApi } from '@/lib/portal-api';

export default function PatientDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    appointments: [],
    records: [],
    prescriptions: [],
    stats: {
      nextAppointment: 'No upcoming',
      newReports: 0,
      billingDue: '$0.00'
    }
  });

  const PATIENT_ID = "47b82a31-0bcb-4df1-9317-e20954e6e870"; // For testing with a real patient from clinical DB

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [apts, labs, rx] = await Promise.all([
          portalApi.getMyAppointments(PATIENT_ID),
          portalApi.getLabResults(PATIENT_ID),
          portalApi.getPrescriptions(PATIENT_ID)
        ]);

        setData({
          appointments: apts.slice(0, 3) || [],
          records: labs.slice(0, 3) || [],
          prescriptions: rx.slice(0, 3) || [],
          stats: {
            nextAppointment: apts[0]?.appointment_time ? new Date(apts[0].appointment_time).toLocaleString() : 'No upcoming',
            newReports: labs.length,
            billingDue: '$120.00' // Placeholder for billing
          }
        });
      } catch (err) {
        console.error("Failed to load portal data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {/* SIDEBAR */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-slate-200 p-6 flex flex-col">
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-xl">
            A
          </div>
          <span className="text-xl font-bold tracking-tight">Patient Portal</span>
        </div>

        <nav className="flex-1 space-y-2">
          {[
            { id: 'overview', label: 'Dashboard', icon: Activity },
            { id: 'appointments', label: 'Appointments', icon: Calendar },
            { id: 'records', label: 'Medical Records', icon: FileText },
            { id: 'telemed', label: 'Telemedicine', icon: Video },
            { id: 'billing', label: 'Billing & Payments', icon: CreditCard },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                activeTab === item.id 
                  ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-sm' 
                  : 'text-slate-500 hover:bg-slate-100'
              }`}
            >
              <item.icon size={20} />
              {item.label}
            </button>
          ))}
        </nav>

        <button className="mt-auto flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-xl transition-all">
          <LogOut size={20} />
          Sign Out
        </button>
      </aside>

      {/* MAIN CONTENT */}
      <main className="ml-64 p-10 max-w-7xl">
        <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Welcome, Arjun Sharma</h1>
            <p className="text-slate-500 mt-1">Managing your health at AxonHIS</p>
          </div>
          <div className="flex gap-4">
            <button className="p-3 bg-white border border-slate-200 rounded-xl hover:shadow-md transition-shadow relative">
              <Bell size={20} className="text-slate-600" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
            </button>
            <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
              <div className="text-right">
                <p className="text-sm font-bold">Arjun Sharma</p>
                <p className="text-[10px] text-indigo-600 font-mono uppercase font-bold">Patient ID: AX9902</p>
              </div>
              <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700">
                <User size={20} />
              </div>
            </div>
          </div>
        </header>

        {activeTab === 'overview' && (
          <div className="space-y-8 animate-in fade-in duration-500">
            {/* STATS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                { label: 'Next Appointment', value: data.stats.nextAppointment, icon: Calendar, color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: 'Total Records', value: `${data.stats.newReports} Items`, icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                { label: 'Billing Due', value: data.stats.billingDue, icon: CreditCard, color: 'text-amber-600', bg: 'bg-amber-50' },
                { label: 'Prescriptions', value: `${data.prescriptions.length} Active`, icon: Activity, color: 'text-purple-600', bg: 'bg-purple-50' },
              ].map((stat, i) => (
                <div key={i} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className={`w-10 h-10 ${stat.bg} ${stat.color} rounded-lg flex items-center justify-center mb-4`}>
                    <stat.icon size={20} />
                  </div>
                  <p className="text-sm text-slate-500 font-medium">{stat.label}</p>
                  <p className="text-lg font-extrabold mt-1">{stat.value}</p>
                </div>
              ))}
            </div>

            {/* UPCOMING APPOINTMENTS & RECENT REPORTS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                  <h3 className="font-bold text-lg">Upcoming Appointments</h3>
                  <button className="text-indigo-600 text-sm font-semibold hover:underline">Book New</button>
                </div>
                <div className="divide-y divide-slate-50">
                  {data.appointments.length > 0 ? data.appointments.map((apt: any, i) => (
                    <div key={i} className="p-6 hover:bg-slate-50 transition-colors flex justify-between items-center group">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center text-slate-400 group-hover:bg-white transition-colors">
                          <User size={24} />
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{apt.doctor?.first_name ? `Dr. ${apt.doctor.first_name} ${apt.doctor.last_name}` : apt.department}</p>
                          <p className="text-xs text-slate-500">{apt.department} • {apt.appointment_type || 'In-Person'}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-slate-700">{new Date(apt.appointment_time).toLocaleString()}</p>
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase bg-slate-100 text-slate-500">
                          {apt.status}
                        </span>
                      </div>
                    </div>
                  )) : (
                    <div className="p-10 text-center text-slate-400">No upcoming appointments</div>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100">
                  <h3 className="font-bold text-lg">Recent Medical Records</h3>
                </div>
                <div className="p-6 space-y-4">
                  {data.records.length > 0 ? data.records.map((record: any, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100 group cursor-pointer hover:border-indigo-300 transition-all">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white border border-slate-200 rounded-xl flex items-center justify-center text-indigo-600 shadow-sm group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                          <FileText size={18} />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-slate-900">{record.value} Result</p>
                          <p className="text-[10px] text-slate-500 uppercase font-bold">Lab Report • {new Date(record.entered_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <button className="text-indigo-600 text-xs font-bold bg-white px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">View</button>
                    </div>
                  )) : (
                    <div className="p-10 text-center text-slate-400">No recent medical records</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab !== 'overview' && (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-slate-200 border-dashed">
             <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center text-slate-300 mb-4">
               <Activity size={32} />
             </div>
             <h3 className="font-bold text-xl">{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Module</h3>
             <p className="text-slate-500 mt-2">Connecting to secure medical backend...</p>
          </div>
        )}
      </main>
    </div>
  );
}
