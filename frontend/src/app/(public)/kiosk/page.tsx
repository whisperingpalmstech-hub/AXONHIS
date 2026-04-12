"use client";

import React, { useState, useEffect } from "react";
import { User, CalendarPlus, CheckCircle2, QrCode, ChevronLeft, ArrowRight, Scan, Volume2 } from "lucide-react";
import { kioskApi, TokenQueue } from "@/lib/kiosk-api";

export default function KioskSelfService() {
  const [view, setView] = useState<"home" | "token_print" | "new_appointment" | "check_in">("home");
  const [loading, setLoading] = useState(false);
  const [currentToken, setCurrentToken] = useState<TokenQueue | null>(null);
  const [error, setError] = useState("");

  const [departments, setDepartments] = useState<any[]>([]);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [selectedDept, setSelectedDept] = useState<any>(null);
  const [selectedDoc, setSelectedDoc] = useState<any>(null);

  useEffect(() => {
    if (view === "new_appointment") {
      kioskApi.getDepartments().then(setDepartments).catch(e => setError(e.message));
    }
  }, [view]);

  useEffect(() => {
    if (selectedDept) {
      setLoading(true);
      kioskApi.getDoctors(selectedDept.name).then(setDoctors).finally(() => setLoading(false));
    }
  }, [selectedDept]);

  const handlePrintToken = async () => {
    setLoading(true);
    try {
      const data = await kioskApi.generateToken({ department: "General OPD", priority: false });
      setCurrentToken(data);
      setTimeout(() => setView("home"), 5000);
    } catch (e: any) { setError(e.message); } 
    finally { setLoading(false); }
  };

  const handleCheckIn = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    try {
      const data = await kioskApi.checkIn(formData.get("identifier") as string);
      setCurrentToken(data);
      setTimeout(() => setView("home"), 5000);
    } catch (e: any) { setError(e.message); } 
    finally { setLoading(false); }
  };

  const handleBookAppointment = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    try {
      const data = await kioskApi.bookAppointment({
        department: selectedDept.name,
        doctor_id: selectedDoc.id,
        patient_name: formData.get("patient_name") as string,
        mobile: formData.get("mobile") as string,
        date: new Date().toISOString().split('T')[0],
        time_slot: "IMMEDIATE"
      });
      setCurrentToken(data);
      setTimeout(() => {
        setView("home");
        setSelectedDept(null);
        setSelectedDoc(null);
      }, 5000);
    } catch (e: any) { setError(e.message); } 
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center font-sans relative select-none">
      <div className="w-full max-w-5xl flex flex-col items-center">
        
        {view !== "home" && !currentToken && (
          <button onClick={() => { setView("home"); setSelectedDept(null); setSelectedDoc(null); }} 
            className="absolute top-12 left-12 bg-white text-slate-800 rounded-lg p-3 border border-slate-200 shadow-sm flex items-center justify-center hover:bg-slate-50">
            <ChevronLeft size={24} /> Back
          </button>
        )}

        <div className="mb-12 text-center">
          <Scan size={64} className="text-indigo-600 mx-auto mb-4" />
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">
            Welcome to <span className="text-indigo-600">AXONHIS</span> Self-Service
          </h1>
          <p className="text-lg text-slate-500 font-medium mt-2">
            Please select an option below to begin.
          </p>
        </div>

        {error && <div className="w-full max-w-2xl bg-rose-50 text-rose-800 border border-rose-200 p-4 rounded-xl mb-8 font-bold text-center">{error}</div>}

        {currentToken && (
          <div className="w-full max-w-2xl bg-white border border-slate-200 rounded-3xl p-12 flex flex-col items-center shadow-lg animate-in fade-in zoom-in-95">
            <CheckCircle2 size={80} className="text-emerald-500 mb-6" />
            <h2 className="text-3xl font-black text-slate-800 mb-8">You are in the Queue</h2>
            
            <div className="text-7xl font-black text-indigo-700 mb-8 py-8 px-16 bg-slate-50 border border-slate-200 rounded-2xl shadow-inner font-mono tracking-tighter">
              {currentToken.token_display}
            </div>
            
            <p className="text-xl text-slate-600 font-bold mb-4 text-center">Please take your printed ticket below.</p>
            <p className="text-slate-500 font-medium flex items-center gap-2 bg-slate-100 px-4 py-2 rounded-lg">
              <Volume2 size={20} className="text-indigo-600" /> Wait in the designated area for your number
            </p>
          </div>
        )}

        {!currentToken && view === "home" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl px-4">
            <button onClick={() => { setView("token_print"); handlePrintToken(); }} className="bg-white border border-slate-200 p-10 rounded-3xl flex flex-col items-center justify-center gap-6 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all group">
              <div className="bg-indigo-50 p-6 rounded-2xl group-hover:bg-indigo-600 transition-colors">
                <QrCode size={64} className="text-indigo-600 group-hover:text-white transition-colors" />
              </div>
              <span className="text-2xl font-black text-slate-800 text-center leading-tight">Token<br/>Print</span>
            </button>
            
            <button onClick={() => setView("new_appointment")} className="bg-white border border-slate-200 p-10 rounded-3xl flex flex-col items-center justify-center gap-6 shadow-sm hover:shadow-md hover:border-emerald-300 transition-all group">
              <div className="bg-emerald-50 p-6 rounded-2xl group-hover:bg-emerald-600 transition-colors">
                <CalendarPlus size={64} className="text-emerald-600 group-hover:text-white transition-colors" />
              </div>
              <span className="text-2xl font-black text-slate-800 text-center leading-tight">New<br/>Walk-In</span>
            </button>
            
            <button onClick={() => setView("check_in")} className="bg-white border border-slate-200 p-10 rounded-3xl flex flex-col items-center justify-center gap-6 shadow-sm hover:shadow-md hover:border-rose-300 transition-all group">
              <div className="bg-rose-50 p-6 rounded-2xl group-hover:bg-rose-600 transition-colors">
                <User size={64} className="text-rose-600 group-hover:text-white transition-colors" />
              </div>
              <span className="text-2xl font-black text-slate-800 text-center leading-tight">Express<br/>Check-In</span>
            </button>
          </div>
        )}

        {!currentToken && view === "new_appointment" && (
          <div className="w-full max-w-3xl bg-white border border-slate-200 p-8 rounded-2xl shadow-sm">
            {!selectedDept && (
              <>
                <h2 className="text-2xl font-black text-slate-800 mb-6 flex items-center gap-3"><CalendarPlus className="text-indigo-600"/> Select Department</h2>
                <div className="grid grid-cols-2 gap-4">
                  {departments.map(d => (
                    <button key={d.id} onClick={() => setSelectedDept(d)} className="bg-slate-50 hover:bg-slate-100 border border-slate-200 p-6 rounded-xl font-bold text-xl text-slate-700 transition-all flex justify-between items-center group">
                      {d.name} 
                      <ArrowRight className="text-slate-400 group-hover:text-indigo-600" />
                    </button>
                  ))}
                </div>
              </>
            )}

            {selectedDept && !selectedDoc && (
              <>
                <h2 className="text-2xl font-black text-slate-800 mb-6 flex items-center gap-3"><User className="text-emerald-600"/> Select Doctor</h2>
                <div className="flex flex-col gap-4">
                  {loading && <div className="text-center p-8 text-slate-500 font-bold">Loading...</div>}
                  {doctors.map(doc => (
                    <button key={doc.id} onClick={() => setSelectedDoc(doc)} className="bg-slate-50 hover:bg-slate-100 border border-slate-200 p-6 rounded-xl flex justify-between items-center group transition-all text-left">
                      <div>
                        <div className="font-bold text-xl text-slate-800 mb-1">{doc.name}</div>
                        <div className="text-emerald-600 font-bold uppercase tracking-wider text-xs">{doc.department}</div>
                      </div>
                      <ArrowRight className="text-slate-400 group-hover:text-emerald-600" />
                    </button>
                  ))}
                </div>
              </>
            )}

            {selectedDept && selectedDoc && (
               <form onSubmit={handleBookAppointment} className="flex flex-col gap-5 w-full max-w-2xl mx-auto">
                 <div className="mb-4">
                   <h2 className="text-2xl font-black text-slate-800 mb-1">Patient Details</h2>
                   <p className="text-slate-500">Booking with <span className="font-bold text-slate-700">{selectedDoc.name}</span></p>
                 </div>
                 
                 <input type="text" name="patient_name" required className="bg-white border-2 border-slate-200 focus:border-indigo-600 outline-none p-4 text-lg text-slate-800 font-bold rounded-xl" placeholder="Patient Full Name"/>
                 <input type="tel" name="mobile" required className="bg-white border-2 border-slate-200 focus:border-indigo-600 outline-none p-4 text-lg text-slate-800 font-bold rounded-xl" placeholder="Mobile Number"/>
                 
                 <button disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xl p-4 rounded-xl mt-4 transition-colors">
                   {loading ? "Processing..." : "Confirm Booking"}
                 </button>
               </form>
            )}
          </div>
        )}

        {!currentToken && view === "check_in" && (
          <div className="w-full max-w-xl bg-white border border-slate-200 p-8 rounded-2xl shadow-sm">
            <h2 className="text-2xl font-black text-slate-800 mb-4 flex items-center gap-3"><QrCode className="text-rose-600"/> Scan Identifier</h2>
            <p className="text-slate-500 mb-8 font-medium">Please enter your UHID or scan your Appointment QR Code.</p>
            <form onSubmit={handleCheckIn} className="flex flex-col gap-4">
              <input type="text" name="identifier" autoFocus className="w-full bg-slate-50 border-2 border-slate-200 focus:border-rose-600 outline-none p-6 text-2xl text-slate-800 font-bold rounded-xl text-center placeholder:text-slate-300 font-mono" placeholder="ID / PHONE"/>
              <button disabled={loading} className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold text-xl p-4 rounded-xl transition-colors">
                {loading ? "Verifying..." : "Check In"}
              </button>
            </form>
          </div>
        )}
      </div>

    </div>
  );
}
