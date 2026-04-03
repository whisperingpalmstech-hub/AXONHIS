"use client";
import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { User, HeartPulse, Activity, FileText, Pill, Clock, ChevronLeft } from "lucide-react";

export default function IpdPatientViewPage() {
  const params = useParams();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("timeline");
  const [orders, setOrders] = useState([
    { id: 1, name: "Chest X-Ray PA View", dept: "Radiology" },
    { id: 2, name: "Serum Creatinine", dept: "Laboratory" }
  ]);

  const handleNewOrder = () => {
    const orderName = prompt("Enter new order name (e.g. CBC, MRI):");
    if (orderName) setOrders([...orders, { id: Date.now(), name: orderName, dept: "Clinical" }]);
  };
  
  return (
    <div className="p-6 h-full bg-slate-50 overflow-y-auto">
      {/* HEADER */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition shadow-sm">
            <ChevronLeft size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-black text-slate-800 tracking-tight">Patient Overview</h1>
            <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">{params.id}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <span className="px-3 py-1.5 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-lg text-xs font-bold uppercase">Admitted</span>
          <span className="px-3 py-1.5 bg-blue-50 text-blue-600 border border-blue-100 rounded-lg text-xs font-bold uppercase">General Ward</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* LEFT COLUMN - Patient Card */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-blue-500 to-indigo-500"/>
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-black text-2xl border-4 border-white shadow-sm ring-1 ring-slate-100">
                JD
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-800">John Doe</h2>
                <p className="text-xs font-medium text-slate-500 uppercase">UHID: AX-102934</p>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-xs text-slate-500">DOB / Age</span>
                <span className="text-xs font-bold text-slate-700">14 May 1985 (39y)</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-xs text-slate-500">Gender</span>
                <span className="text-xs font-bold text-slate-700">Male</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-xs text-slate-500">Blood Group</span>
                <span className="text-xs font-bold text-rose-600 flex items-center gap-1"><HeartPulse size={12}/> O+</span>
              </div>
              <div className="flex justify-between pb-1">
                <span className="text-xs text-slate-500">Attending</span>
                <span className="text-xs font-bold text-slate-700">Dr. Sarah Smith</span>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-2xl p-6 shadow-md text-white">
            <h3 className="text-sm font-bold opacity-80 uppercase tracking-widest mb-4 flex items-center gap-2"><Activity size={16}/> Vitals Snapshot</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs opacity-60">Heart Rate</p>
                <p className="text-xl font-black text-rose-400">84 <span className="text-xs font-normal opacity-50">bpm</span></p>
              </div>
              <div>
                <p className="text-xs opacity-60">Blood Pressure</p>
                <p className="text-xl font-black text-blue-300">120/80</p>
              </div>
              <div>
                <p className="text-xs opacity-60">Temperature</p>
                <p className="text-xl font-black text-amber-400">98.6 <span className="text-xs font-normal opacity-50">°F</span></p>
              </div>
              <div>
                <p className="text-xs opacity-60">SpO2</p>
                <p className="text-xl font-black text-emerald-400">98 <span className="text-xs font-normal opacity-50">%</span></p>
              </div>
            </div>
            <button onClick={() => router.push(`/dashboard/nursing-ipd/${params.id}`)} className="w-full mt-6 py-2 bg-white/10 hover:bg-white/20 transition rounded-xl text-xs font-bold">View Full Flowsheet</button>
          </div>
        </div>

        {/* MIDDLE COLUMN - Clinical Timeline */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm h-[600px] flex flex-col">
            <div className="flex border-b border-slate-100">
              <button onClick={() => setActiveTab('timeline')} className={`flex-1 py-4 text-sm font-bold transition-all relative ${activeTab === 'timeline' ? 'text-indigo-600' : 'text-slate-500'}`}>
                Clinical Timeline
                {activeTab === 'timeline' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-indigo-600"/>}
              </button>
              <button onClick={() => setActiveTab('notes')} className={`flex-1 py-4 text-sm font-bold transition-all relative ${activeTab === 'notes' ? 'text-indigo-600' : 'text-slate-500'}`}>
                Doctor Notes
                {activeTab === 'notes' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-indigo-600"/>}
              </button>
            </div>
            
            <div className="flex-1 p-6 overflow-y-auto w-full max-w-full">
              {activeTab === 'timeline' ? (
                <div className="relative border-l-2 border-slate-100 pl-6 ml-4 space-y-8">
                  <div className="relative">
                    <div className="absolute -left-[35px] top-0 w-8 h-8 rounded-full bg-blue-100 border-4 border-white flex items-center justify-center"><Activity size={14} className="text-blue-600"/></div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <div className="flex justify-between items-center mb-1">
                        <h4 className="font-bold text-sm text-slate-800">Morning Rounds completed</h4>
                        <span className="text-xs text-slate-400">Today, 08:30 AM</span>
                      </div>
                      <p className="text-xs text-slate-600">Patient is stable. Continue current IV antibiotics.</p>
                    </div>
                  </div>
                  <div className="relative">
                    <div className="absolute -left-[35px] top-0 w-8 h-8 rounded-full bg-emerald-100 border-4 border-white flex items-center justify-center"><Pill size={14} className="text-emerald-600"/></div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <div className="flex justify-between items-center mb-1">
                        <h4 className="font-bold text-sm text-slate-800">Medication Administered</h4>
                        <span className="text-xs text-slate-400">Yesterday, 10:00 PM</span>
                      </div>
                      <p className="text-xs text-slate-600">Paracetamol 500mg given orally.</p>
                    </div>
                  </div>
                  <div className="relative">
                    <div className="absolute -left-[35px] top-0 w-8 h-8 rounded-full bg-amber-100 border-4 border-white flex items-center justify-center"><FileText size={14} className="text-amber-600"/></div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <div className="flex justify-between items-center mb-1">
                        <h4 className="font-bold text-sm text-slate-800">CBC Result Published</h4>
                        <span className="text-xs text-slate-400">Yesterday, 02:15 PM</span>
                      </div>
                      <p className="text-xs text-slate-600">Results within normal limits. Hemoglobin 14.2 g/dL.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 bg-yellow-50/50 border border-yellow-100 rounded-xl">
                     <p className="text-xs font-bold text-yellow-800 mb-2">Admission Note • Dr. Sarah Smith</p>
                     <p className="text-sm text-slate-700 italic">"Patient presents with mild respiratory distress. Initiated oxygen therapy. Monitoring closely."</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN - Interventions & Orders */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
             <h3 className="text-sm font-black text-slate-800 mb-4 border-b border-slate-100 pb-2 flex items-center justify-between">
                Active Orders
                <span className="bg-rose-100 text-rose-600 text-[10px] px-2 py-0.5 rounded-full">{orders.length} Pending</span>
             </h3>
             <ul className="space-y-3">
                {orders.map(o => (
                  <li key={o.id} className="flex gap-3 justify-between items-center border border-slate-100 p-3 rounded-xl bg-slate-50/50 hover:bg-slate-50 transition cursor-pointer">
                    <div>
                      <p className="text-xs font-bold text-slate-700">{o.name}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{o.dept}</p>
                    </div>
                    <Clock size={14} className="text-amber-500 animate-pulse"/>
                  </li>
                ))}
             </ul>
             <button onClick={handleNewOrder} className="w-full mt-4 py-2 border border-dashed border-indigo-200 text-indigo-600 rounded-xl text-xs font-bold hover:bg-indigo-50 transition">+ New Order</button>
          </div>
        </div>

      </div>
    </div>
  );
}
