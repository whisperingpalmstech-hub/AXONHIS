"use client";
import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { User, Phone, MapPin, Calendar, Activity, FileText, ArrowLeft, Shield } from "lucide-react";
import Link from "next/link";

export default function PatientProfilePage() {
  const params = useParams();
  const id = params.id as string;
  const [patient, setPatient] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/patients/${id}`, {
          headers: { "Authorization": `Bearer ${localStorage.getItem("access_token")}` }
        });
        if (res.ok) {
          const data = await res.json();
          setPatient(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [id]);

  if (loading) return <div className="p-8 text-[var(--text-secondary)]">Loading patient profile...</div>;
  if (!patient) return <div className="p-8 text-red-500">Patient not found</div>;

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <Link href="/dashboard/patients" className="inline-flex items-center text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
          <ArrowLeft size={16} className="mr-2" /> Back to Patients
        </Link>
        <Link href={`/dashboard/patients/${id}/billing`} className="btn-primary text-sm flex items-center gap-2">
          <FileText size={16} /> View Billing Summary
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left Column - Core Demographics */}
        <div className="md:col-span-1 space-y-6">
          <div className="card text-center p-8">
            <div className="w-24 h-24 rounded-full bg-[var(--accent-primary)]/10 flex items-center justify-center text-[var(--accent-primary)] font-bold text-3xl mx-auto mb-4">
              {patient.first_name[0]}{patient.last_name[0]}
            </div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">{patient.first_name} {patient.last_name}</h1>
            <p className="text-[var(--text-secondary)] mb-4">{patient.patient_uuid}</p>
            <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-semibold rounded-full capitalize">
              {patient.status}
            </span>
          </div>

          <div className="card">
            <div className="card-header border-b border-[var(--border)]"><h2 className="font-semibold text-[var(--text-primary)] flex items-center gap-2"><User size={18}/> Details</h2></div>
            <div className="card-body p-5 space-y-4 text-sm">
              <div className="flex justify-between border-b pb-2"><span className="text-[var(--text-secondary)]">DOB</span> <span className="font-medium">{patient.date_of_birth}</span></div>
              <div className="flex justify-between border-b pb-2"><span className="text-[var(--text-secondary)]">Gender</span> <span className="font-medium">{patient.gender}</span></div>
              <div className="flex justify-between border-b pb-2"><span className="text-[var(--text-secondary)]">Phone</span> <span className="font-medium">{patient.primary_phone || "N/A"}</span></div>
              <div className="flex justify-between"><span className="text-[var(--text-secondary)]">Email</span> <span className="font-medium text-blue-600">{patient.email || "N/A"}</span></div>
            </div>
          </div>
        </div>

        {/* Right Column - Related Records */}
        <div className="md:col-span-2 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="card">
              <div className="card-header border-b border-[var(--border)]"><h2 className="font-semibold flex items-center gap-2"><Shield size={18} className="text-[var(--accent-primary)]"/> Identifiers</h2></div>
              <div className="card-body p-4 text-sm space-y-3">
                {patient.identifiers.length === 0 ? <span className="text-[var(--text-secondary)]">No identifiers recorded</span> : 
                  patient.identifiers.map((idn: any, i: number) => (
                    <div key={i} className="flex justify-between items-center bg-[var(--bg-secondary)] p-3 rounded-md border border-[var(--border)]">
                      <span className="text-[var(--text-secondary)] capitalize">{idn.identifier_type.replace('_', ' ')}</span>
                      <strong className="font-bold tracking-widest">{idn.identifier_value}</strong>
                    </div>
                  ))
                }
              </div>
            </div>

            <div className="card">
              <div className="card-header border-b border-[var(--border)]"><h2 className="font-semibold flex items-center gap-2"><FileText size={18} className="text-emerald-500"/> Insurance</h2></div>
              <div className="card-body p-4 text-sm space-y-3">
                {patient.insurance.length === 0 ? <span className="text-[var(--text-secondary)]">No insurance records</span> : 
                  patient.insurance.map((ins: any, i: number) => (
                    <div key={i} className="bg-emerald-50 border border-emerald-100 p-3 rounded-md">
                      <div className="font-bold text-emerald-800 mb-1">{ins.insurance_provider}</div>
                      <div className="text-emerald-700 font-medium">Policy: {ins.policy_number}</div>
                    </div>
                  ))
                }
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header border-b border-[var(--border)] flex justify-between items-center">
              <h2 className="font-semibold flex items-center gap-2"><Activity size={18} className="text-purple-500" /> Clinical Consents</h2>
            </div>
            <div className="card-body p-0">
              <table className="w-full text-left text-sm">
                <thead><tr className="bg-[var(--bg-secondary)] text-[var(--text-secondary)]"><th className="p-4">Type</th><th className="p-4">Signed On</th></tr></thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {patient.consents.length === 0 && <tr><td colSpan={2} className="p-4 text-center text-[var(--text-secondary)]">No consent records found</td></tr>}
                  {patient.consents.map((con: any, i: number) => (
                    <tr key={i}>
                      <td className="p-4 font-medium capitalize">{con.consent_type.replace('_', ' ')}</td>
                      <td className="p-4 text-[var(--text-secondary)]">{new Date(con.signed_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="card">
            <div className="card-header border-b border-[var(--border)] flex justify-between items-center">
              <h2 className="font-semibold flex items-center gap-2"><Calendar size={18} className="text-blue-500" /> Appointments Timeline</h2>
            </div>
            <div className="card-body p-4 text-sm">
              {patient.appointments.length === 0 ? <div className="text-[var(--text-secondary)]">No appointment history.</div> : 
                <div className="space-y-4 border-l-2 border-slate-200 ml-3 pl-4">
                  {patient.appointments.map((apt: any, i: number) => (
                    <div key={i} className="relative">
                      <div className={`absolute -left-[23px] top-1 w-3 h-3 rounded-full ${apt.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'}`}></div>
                      <div className="font-bold text-[var(--text-primary)]">{apt.department}</div>
                      <div className="text-[var(--text-secondary)]">{new Date(apt.appointment_time).toLocaleString()}</div>
                      <div className="mt-1 inline-block px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-slate-100 text-slate-600">{apt.status}</div>
                    </div>
                  ))}
                </div>
              }
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
