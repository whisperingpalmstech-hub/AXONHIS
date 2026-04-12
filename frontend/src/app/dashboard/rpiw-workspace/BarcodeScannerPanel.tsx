"use client";
import React, { useState } from "react";
import { Maximize, Barcode, CheckCircle2, AlertCircle, Scan } from "lucide-react";

export default function BarcodeScannerPanel({ patientUhid }: { patientUhid: string }) {
  const [scanning, setScanning] = useState(false);
  const [scannedData, setScannedData] = useState<string | null>(null);

  const startScan = () => {
    setScanning(true);
    setScannedData(null);
    setTimeout(() => {
      setScanning(false);
      setScannedData(`SMPL-${Math.floor(100000 + Math.random() * 900000)}`);
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 rounded-2xl p-8 overflow-hidden relative border-4 border-slate-700 shadow-2xl flex flex-col items-center justify-center min-h-[160px]">
        {scanning ? (
          <div className="absolute inset-x-8 top-1/2 h-1 bg-emerald-500 animate-scan shadow-[0_0_15px_#10b981]"></div>
        ) : null}
        
        {scannedData ? (
          <div className="text-center animate-bounce-in">
             <div className="w-16 h-16 rounded-full bg-emerald-500 flex items-center justify-center text-white mx-auto mb-4 border-4 border-emerald-400">
                <CheckCircle2 size={32}/>
             </div>
             <div className="text-emerald-400 font-black text-xl tracking-widest uppercase">{scannedData}</div>
             <div className="text-slate-500 text-[10px] font-bold mt-2 uppercase tracking-widest">Valid Barcode Logged</div>
          </div>
        ) : scanning ? (
          <div className="flex flex-col items-center gap-4">
             <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 flex items-center justify-center text-emerald-500 animate-pulse border-2 border-emerald-500/30">
                <Scan size={32} />
             </div>
             <div className="text-emerald-500 font-black text-sm tracking-widest uppercase">Targeting Specimen...</div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 text-center cursor-pointer group" onClick={startScan}>
             <div className="w-20 h-20 rounded-full bg-slate-800 flex items-center justify-center text-slate-500 group-hover:text-blue-500/80 transition-all border-4 border-slate-700 group-hover:border-blue-500/20">
                <Barcode size={40} />
             </div>
             <div>
                <div className="text-slate-400 font-black text-sm tracking-widest uppercase group-hover:text-blue-400 transition-colors">Point Camera at Vial</div>
                <div className="text-slate-600 text-[10px] font-bold mt-1 uppercase tracking-widest">Click to Simulate Scan</div>
             </div>
          </div>
        )}
      </div>

      {scannedData && (
        <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100 flex items-center justify-between">
           <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500 flex items-center justify-center text-white shadow-lg">
                 <Maximize size={20}/>
              </div>
              <div>
                 <div className="text-sm font-black text-slate-800 tracking-tight">Label Match OK</div>
                 <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Patient UHID Verified</div>
              </div>
           </div>
           <button onClick={() => setScannedData(null)} className="text-[10px] font-black text-emerald-600 uppercase tracking-widest hover:text-emerald-700">Clear</button>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
         <button className="bg-slate-100 p-3 rounded-lg text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 transition-all flex items-center justify-center gap-2">
            <AlertCircle size={14}/> Invalid Read
         </button>
         <button className="bg-slate-100 p-3 rounded-lg text-[10px] font-black text-slate-500 uppercase tracking-widest hover:bg-slate-200 transition-all flex items-center justify-center gap-2">
            <Scan size={14}/> Manual ID
         </button>
      </div>

      <style jsx>{`
        @keyframes scan {
          0% { top: 30px; opacity: 0; }
          40% { opacity: 1; }
          60% { opacity: 1; }
          100% { top: 130px; opacity: 0; }
        }
        .animate-scan {
          animation: scan 1.5s linear infinite;
        }
        @keyframes bounce-in {
          0% { transform: scale(0.5); opacity: 0; }
          70% { transform: scale(1.1); }
          100% { transform: scale(1); opacity: 1; }
        }
        .animate-bounce-in {
          animation: bounce-in 0.4s cubic-bezier(.34,1.56,.64,1);
        }
      `}</style>
    </div>
  );
}
