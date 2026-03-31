"use client";
import React, { useState } from "react";
import { Package, Truck, Check, MapPin, ClipboardList, Info } from "lucide-react";

export default function CollectionStatusPanel({ patientUhid }: { patientUhid: string }) {
  const [transportStatus, setTransportStatus] = useState("In Transit");

  return (
    <div className="space-y-6">
      <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
         <div className="flex border-l-2 border-slate-200 ml-6 pl-8 space-y-8 flex-col relative">
            <div className="relative">
               <div className="absolute -left-[41px] top-1 w-6 h-6 rounded-full bg-emerald-500 border-4 border-white shadow-md flex items-center justify-center text-white">
                  <Check size={12}/>
               </div>
               <div className="flex flex-col">
                  <span className="text-sm font-black text-slate-800 tracking-tight">Vial 9029 Collected</span>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">10:42 AM - Phlebotomist A</span>
               </div>
            </div>

            <div className="relative">
               <div className="absolute -left-[41px] top-1 w-6 h-6 rounded-full bg-blue-600 border-4 border-white shadow-md flex items-center justify-center text-white animate-pulse">
                  <Truck size={12}/>
               </div>
               <div className="flex flex-col">
                  <span className="text-sm font-black text-slate-800 tracking-tight">Transport Initiated</span>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">11:05 AM - Courier Box #04</span>
                  <div className="bg-blue-50 text-blue-700 text-[10px] font-black p-2 mt-2 rounded-lg border border-blue-100 flex items-center gap-2">
                     <MapPin size={12}/> EN ROUTE TO CENTRAL LAB
                  </div>
               </div>
            </div>

            <div className="relative opacity-40">
               <div className="absolute -left-[41px] top-1 w-6 h-6 rounded-full bg-slate-300 border-4 border-white shadow-md flex items-center justify-center text-white">
                  <Package size={12}/>
               </div>
               <div className="flex flex-col">
                  <span className="text-sm font-black text-slate-800 tracking-tight">Received at Lab</span>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1 pr-1">EXPECTED 11:45 AM</span>
               </div>
            </div>
         </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
         <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="text-[10px] font-black text-slate-400 mb-1 uppercase tracking-widest">Courier ID</div>
            <div className="text-sm font-black text-slate-800 tracking-tight">AXON-C-992</div>
         </div>
         <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="text-[10px] font-black text-slate-400 mb-1 uppercase tracking-widest">Box Temp</div>
            <div className="text-sm font-black text-slate-800 tracking-tight">4.2°C</div>
         </div>
      </div>

      <div className="flex gap-2">
         <button className="flex-1 bg-slate-100 p-3 rounded-xl text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 transition-all flex items-center justify-center gap-2">
            <ClipboardList size={14}/> Manifest
         </button>
         <button className="flex-1 bg-slate-100 p-3 rounded-xl text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 transition-all flex items-center justify-center gap-2">
            <Info size={14}/> Support
         </button>
      </div>
    </div>
  );
}
