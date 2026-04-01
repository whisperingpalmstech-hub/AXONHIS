"use client";
import { useTranslation } from "@/i18n";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { User, Phone, MapPin, Calendar, Activity, FileText, ArrowLeft, Shield, AlertTriangle, Pill, Stethoscope, Bed, DollarSign, Clock } from "lucide-react";
import Link from "next/link";

export default function PatientProfilePage() {
  const { t } = useTranslation();
  const params = useParams();
  const id = params.id as string;
  const router = useRouter();
  
  const [patient, setPatient] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  const [billing, setBilling] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState("timeline");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAllData = async () => {
      setLoading(true);
      try {
        const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
        
        // 1. Core Profile
        const resProfile = await fetch(`${apiUrl}/api/v1/patients/${id}`, { headers });
        if (resProfile.ok) setPatient(await resProfile.json());
        
        // 2. Doctor Desk Timeline (Clinical footprint)
        const resTimeline = await fetch(`${apiUrl}/api/v1/doctor-desk/timeline/${id}`, { headers });
        if (resTimeline.ok) {
           const tData = await resTimeline.json();
           setTimeline(tData);
        }

        // 3. Billing Entries (Financial footprint)
        const resBilling = await fetch(`${apiUrl}/api/v1/billing/entries/patient/${id}`, { headers });
        if (resBilling.ok) {
           setBilling(await resBilling.json());
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAllData();
  }, [id]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen space-y-4">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--accent-primary)]"></div>
      <p className="text-[var(--text-secondary)]">Assembling Patient 360° View...</p>
    </div>
  );
  if (!patient) return <div className="p-8 text-red-500 text-center font-bold text-xl">Patient not found in central registry</div>;

  return (
    <div className="p-4 md:p-8 space-y-6 max-w-[1400px] mx-auto pb-24">
      {/* HEADER ROW */}
      <div className="flex justify-between items-center mb-6">
        <Link href="/dashboard/patients" className="inline-flex items-center text-sm font-medium text-[var(--accent-primary)] hover:underline">
          <ArrowLeft size={16} className="mr-2" /> Back to Registry
        </Link>
        <div className="flex gap-3">
          <button className="btn-secondary flex items-center gap-2"><Bed size={16}/> Allocate Bed</button>
          <Link href={`/dashboard/rcm-billing`} className="btn-primary flex items-center gap-2">
            <DollarSign size={16} /> Settlement Desk
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* LEFT COMPONENT - DEMOGRAPHICS & VITALS */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card text-center p-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-600"></div>
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-100 to-blue-50 flex items-center justify-center text-indigo-700 font-bold text-2xl mx-auto mb-4 border border-indigo-200 shadow-sm">
              {patient.first_name[0]}{patient.last_name[0]}
            </div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">{patient.first_name} {patient.last_name}</h1>
            <p className="text-sm font-mono text-[var(--text-secondary)] mb-3 bg-slate-100 dark:bg-slate-800 py-1 rounded-md">{patient.patient_uuid}</p>
            <div className="flex justify-center gap-2 mb-4">
               <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full uppercase tracking-wider">
                 {patient.status}
               </span>
               <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded-full flex items-center gap-1">
                 <User size={12}/> {patient.gender}
               </span>
            </div>
          </div>

          <div className="card">
            <div className="card-header border-b border-[var(--border)]"><h2 className="font-semibold text-sm flex items-center gap-2"><User size={16} className="text-blue-500"/> Details</h2></div>
            <div className="card-body p-4 space-y-3 text-sm">
              <div className="flex justify-between items-center"><span className="text-[var(--text-secondary)]">DOB</span> <span className="font-medium">{patient.date_of_birth}</span></div>
              <div className="flex justify-between items-center"><span className="text-[var(--text-secondary)]">Phone</span> <span className="font-medium">{patient.primary_phone || "N/A"}</span></div>
              <div className="flex justify-between items-center"><span className="text-[var(--text-secondary)]">Email</span> <span className="font-medium text-blue-600 truncate max-w-[150px]">{patient.email || "None"}</span></div>
            </div>
          </div>

          <div className="card">
            <div className="card-header border-b border-[var(--border)] bg-rose-50 dark:bg-rose-900/10"><h2 className="font-semibold text-sm flex items-center gap-2 text-rose-600"><AlertTriangle size={16}/> Clinical Flags & Allergies</h2></div>
            <div className="card-body p-4 text-sm space-y-2">
               {(!timeline || !timeline.diagnoses || timeline.diagnoses.length === 0) ? (
                  <span className="text-slate-400 italic">No flags recorded</span>
               ) : (
                  timeline.diagnoses.slice(0, 3).map((d: any, i: number) => (
                    <div key={i} className="flex gap-2 items-start bg-rose-50 dark:bg-rose-900/20 text-rose-700 p-2 rounded text-xs font-medium">
                      <AlertTriangle size={14} className="mt-0.5 shrink-0"/> {d.condition_name}
                    </div>
                  ))
               )}
            </div>
          </div>
        </div>

        {/* RIGHT COMPONENT - TABS & 360 VIEW */}
        <div className="lg:col-span-3 space-y-6">
          {/* TABS Navigation */}
          <div className="flex border-b border-[var(--border)] gap-8">
            <button onClick={() => setActiveTab('timeline')} className={`pb-3 text-sm font-semibold transition-colors flex items-center gap-2 ${activeTab === 'timeline' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}>
              <Clock size={16}/> Clinical Timeline
            </button>
            <button onClick={() => setActiveTab('clinical')} className={`pb-3 text-sm font-semibold transition-colors flex items-center gap-2 ${activeTab === 'clinical' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}>
              <Stethoscope size={16}/> Encounters & Prescriptions
            </button>
            <button onClick={() => setActiveTab('billing')} className={`pb-3 text-sm font-semibold transition-colors flex items-center gap-2 ${activeTab === 'billing' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}>
              <DollarSign size={16}/> Financial Ledger
            </button>
          </div>

          {/* TAB CONTENTS */}
          {activeTab === 'timeline' && (
            <div className="card shadow-sm border border-[var(--border)]">
              <div className="card-header border-b border-[var(--border)] bg-[var(--bg-secondary)] flex justify-between items-center">
                <h2 className="font-bold flex items-center gap-2 text-indigo-700"><Activity size={18} /> Central Medical History</h2>
                <div className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded font-mono">Aggregated via EMR</div>
              </div>
              <div className="card-body p-6">
                {!timeline ? <div className="text-center text-slate-500 py-10">No clinical timeline available</div> : (
                   <div className="relative border-l-2 border-slate-200 ml-4 space-y-8 pb-4">
                     
                     {/* Encounters */}
                     {timeline.encounters?.map((enc: any, i: number) => (
                       <div key={i} className="relative pl-6">
                         <div className="absolute w-4 h-4 bg-blue-500 rounded-full -left-[9px] top-1 border-4 border-white dark:border-slate-900 shadow-sm"></div>
                         <div className="mb-1 text-xs text-slate-500 font-medium">Encounter Initiated • {new Date().toLocaleDateString()}</div>
                         <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                           <h4 className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                             <Stethoscope size={16} className="text-blue-500"/> {enc.department || "OPD"} Visit
                           </h4>
                           <p className="text-sm mt-2 text-slate-600 dark:text-slate-400">Chief Complaint: {enc.chief_complaint || "Routine checkup"}</p>
                           <p className="text-sm mt-1 text-slate-600 dark:text-slate-400">Status: <span className="font-mono text-xs bg-slate-200 dark:bg-slate-700 px-1 rounded">{enc.status}</span></p>
                         </div>
                       </div>
                     ))}

                     {/* Prescriptions */}
                     {timeline.prescriptions?.map((rx: any, i: number) => (
                       <div key={i} className="relative pl-6">
                         <div className="absolute w-4 h-4 bg-emerald-500 rounded-full -left-[9px] top-1 border-4 border-white dark:border-slate-900 shadow-sm"></div>
                         <div className="mb-1 text-xs text-slate-500 font-medium">Medication Prescribed • {new Date(rx.created_at).toLocaleDateString()}</div>
                         <div className="bg-emerald-50 dark:bg-emerald-900/10 p-3 rounded-lg border border-emerald-100 dark:border-emerald-800/30 flex items-center gap-3">
                           <div className="bg-emerald-100 text-emerald-600 p-2 rounded-md"><Pill size={18}/></div>
                           <div>
                             <div className="font-bold text-emerald-900 dark:text-emerald-100">{rx.medicine_name}</div>
                             <div className="text-xs text-emerald-700 dark:text-emerald-400">{rx.dosage} • {rx.frequency} • {rx.duration}</div>
                           </div>
                         </div>
                       </div>
                     ))}
                     
                     {/* Diagnostic Orders */}
                     {timeline.diagnostic_orders?.map((lab: any, i: number) => (
                       <div key={i} className="relative pl-6">
                         <div className="absolute w-4 h-4 bg-purple-500 rounded-full -left-[9px] top-1 border-4 border-white dark:border-slate-900 shadow-sm"></div>
                         <div className="mb-1 text-xs text-slate-500 font-medium">Diagnostic Ordered • {new Date(lab.created_at).toLocaleDateString()}</div>
                         <div className="bg-purple-50 dark:bg-purple-900/10 p-3 rounded-lg border border-purple-100 dark:border-purple-800/30 flex items-center gap-3">
                           <div className="bg-purple-100 text-purple-600 p-2 rounded-md"><Activity size={18}/></div>
                           <div>
                             <div className="font-bold text-purple-900 dark:text-purple-100">{lab.test_name}</div>
                             <div className="text-xs text-purple-700 dark:text-purple-400 uppercase tracking-wide">{lab.test_type} • {lab.status}</div>
                           </div>
                         </div>
                       </div>
                     ))}

                     {timeline.encounters?.length === 0 && timeline.prescriptions?.length === 0 && (
                       <div className="text-center text-slate-500 py-4 italic text-sm">Patient history is completely empty.</div>
                     )}
                   </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'billing' && (
            <div className="card shadow-sm border border-[var(--border)]">
              <div className="card-header border-b border-[var(--border)] bg-[var(--bg-secondary)] flex justify-between items-center">
                <h2 className="font-bold flex items-center gap-2 text-emerald-700"><DollarSign size={18} /> Financial Ledger</h2>
              </div>
              <div className="card-body p-0">
                {billing.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 flex flex-col items-center">
                    <DollarSign size={32} className="mb-3 opacity-20"/>
                    <p>No financial charges exist for this patient.</p>
                  </div>
                ) : (
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="bg-slate-50 text-slate-600 uppercase text-[10px] tracking-wider border-b">
                        <th className="p-4 font-bold">Date</th>
                        <th className="p-4 font-bold">Service / Item</th>
                        <th className="p-4 font-bold">Module</th>
                        <th className="p-4 font-bold text-right">Amount</th>
                        <th className="p-4 font-bold text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {billing.map((b: any, i: number) => (
                        <tr key={i} className="hover:bg-slate-50 transition-colors">
                          <td className="p-4 text-slate-500 whitespace-nowrap">{new Date(b.created_at).toLocaleDateString()}</td>
                          <td className="p-4 font-semibold text-slate-800">{b.item_name}</td>
                          <td className="p-4 text-xs font-mono text-slate-500 uppercase">{b.service_department}</td>
                          <td className="p-4 text-right font-bold text-slate-800">${b.total_amount?.toFixed(2)}</td>
                          <td className="p-4 text-center">
                             {b.status === 'BILLED' || b.status === 'PAID' ? 
                               <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-xs font-bold uppercase">PAID</span> :
                               <span className="bg-amber-100 text-amber-700 px-2 py-1 rounded text-xs font-bold uppercase">UNBILLED</span>
                             }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'clinical' && (
             <div className="card text-center p-12 text-slate-500 shadow-sm">
                <Stethoscope size={48} className="mx-auto mb-4 opacity-20 text-indigo-500"/>
                <h3 className="text-lg font-bold text-slate-700 mb-2">Detailed Clinical Encounter Viewer</h3>
                <p className="max-w-md mx-auto text-sm">The detailed encounter and vitals timeline graph is synced with the Central Timeline tab. Visit Doctor Desk to add new clinical notes.</p>
                <Link href="/dashboard/doctor-desk" className="btn-primary mt-6 inline-flex">Go to Doctor Desk</Link>
             </div>
          )}

        </div>
      </div>
    </div>
  );
}
