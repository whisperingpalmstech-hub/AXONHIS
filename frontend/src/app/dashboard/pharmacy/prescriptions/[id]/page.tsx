"use client";
import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  Pill, AlertCircle, Clock, CheckCircle2, Search, ArrowRight,
  Package, AlertTriangle, TrendingDown, ClipboardList, ShieldAlert,
  ArrowLeft, Check, X, Info
} from "lucide-react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function DispensePrescriptionPage() {
  const router = useRouter();
  const params = useParams();
  const rxId = params.id as string;
  
  const [prescription, setPrescription] = useState<any>(null);
  const [patient, setPatient] = useState<any>(null);
  const [medications, setMedications] = useState<any[]>([]);
  const [drugInteractions, setDrugInteractions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dispensing, setDispensing] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const headers = {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        };

        // 1. Fetch Prescription
        const rxRes = await fetch(`${API}/api/v1/pharmacy/prescriptions/${rxId}`, { headers });
        if (!rxRes.ok) throw new Error("Rx not found");
        const rxData = await rxRes.json();
        setPrescription(rxData);

        // 2. Fetch Patient Data (Phase 2 core module)
        const patRes = await fetch(`${API}/api/v1/patients/${rxData.patient_id}`, { headers });
        if (patRes.ok) {
          const patData = await patRes.json();
          setPatient(patData);
        }

        // 3. Fetch Drug Dictionary
        const medRes = await fetch(`${API}/api/v1/pharmacy/medications`, { headers });
        if (medRes.ok) {
          const medData = await medRes.json();
          setMedications(medData);
        }

        // 4. Fetch Full CDSS Safety Checks
        const activeMeds = rxData.items.map((i: any) => i.drug_id);
        const cdssAlerts: any[] = [];
        
        for (const item of rxData.items) {
          try {
            const cdssRes = await fetch(`${API}/api/v1/cdss/check-medication`, {
              method: "POST",
              headers,
              body: JSON.stringify({
                patient_context: {
                  patient_id: rxData.patient_id,
                  encounter_id: rxData.encounter_id,
                  weight_kg: 70, // mocked for demo 
                  age_years: 30, // mocked
                  kidney_function_egfr: 90,
                  allergies: ["penicillin"], // mocked allergy
                  active_medications: activeMeds.filter((id: string) => id !== item.drug_id), // check against others on this Rx
                  diagnoses: ["hypertension"] // mocked diagnosis
                },
                new_medication_id: item.drug_id,
                dose: parseFloat(item.dosage) || 500
              })
            });
            if (cdssRes.ok) {
              const resData = await cdssRes.json();
              if (resData.alerts?.length > 0) {
                cdssAlerts.push(...resData.alerts);
              }
            }
          } catch (e) {
            console.error(e);
          }
        }
        // Deduplicate alerts by message
        const uniqueAlerts = cdssAlerts.filter((v, i, a) => a.findIndex(t => (t.message === v.message)) === i);
        setDrugInteractions(uniqueAlerts);

      } catch (error) {
        console.error("Failed to fetch rx data", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [rxId]);

  const handleDispense = async () => {
    try {
      setDispensing(true);
      const token = localStorage.getItem("access_token");
      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };

      const res = await fetch(`${API}/api/v1/pharmacy/dispense`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          prescription_id: rxId,
          status: "dispensed"
        })
      });

      if (res.ok) {
        router.push("/dashboard/pharmacy");
      } else {
        alert("Failed to dispense prescription");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setDispensing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--accent-primary)]"></div>
      </div>
    );
  }

  if (!prescription) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-slate-500">
        <AlertCircle className="w-16 h-16 text-slate-300 mb-4" />
        <h2 className="text-xl font-bold">Prescription Not Found</h2>
        <button onClick={() => router.back()} className="mt-4 px-4 py-2 border rounded-lg hover:bg-slate-50">Go Back</button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <button 
        onClick={() => router.back()} 
        className="flex items-center gap-2 text-slate-500 hover:text-[var(--accent-primary)] transition-colors text-sm font-medium"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
            Dispense Prescription
            <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wide border ${
              prescription.status === 'dispensed' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-blue-50 text-blue-700 border-blue-200'
            }`}>
              {prescription.status}
            </span>
          </h1>
          <p className="text-slate-500 text-sm mt-1 font-mono">RX-{prescription.id.split("-")[0].toUpperCase()}</p>
        </div>
      </div>

      {drugInteractions.length > 0 && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 flex items-start gap-4 shadow-sm">
          <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
            <ShieldAlert className="w-6 h-6 text-rose-600" />
          </div>
          <div>
            <h3 className="font-semibold text-rose-800">CDSS Safety Alerts!</h3>
            <p className="text-sm text-rose-600 mt-1">The CDSS Engine has detected clinical warnings for this prescription.</p>
            <ul className="mt-3 space-y-2">
              {drugInteractions.map((inter: any, idx) => (
                <li key={idx} className="text-sm flex gap-3 items-start text-rose-800 px-4 py-3 bg-white/70 border border-rose-100 rounded-lg">
                  <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-rose-500" />
                  <div>
                    <strong className="uppercase bg-rose-100 text-rose-700 px-2 flex-inline rounded text-[10px] tracking-wider mb-1 block w-max">
                      {inter.alert_type} ({inter.severity})
                    </strong>
                    <span>{inter.message}</span>
                    {inter.recommended_action && (
                      <p className="text-xs mt-1.5 font-medium text-rose-600 border-t border-rose-100 pt-1.5">
                        <span className="font-bold">Action Required: </span>{inter.recommended_action}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          {/* Drug List */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="bg-slate-50/80 px-5 py-4 border-b border-slate-200 flex items-center justify-between">
              <h2 className="font-semibold text-slate-800 flex items-center gap-2">
                <Pill className="w-5 h-5 text-slate-400" />
                Prescribed Medications
              </h2>
              <span className="text-xs font-medium text-slate-500">{prescription.items.length} items</span>
            </div>
            
            <div className="divide-y divide-slate-100">
              {prescription.items.map((item: any) => {
                const med = medications.find(m => m.id === item.drug_id);
                return (
                  <div key={item.id} className="p-5 flex gap-4">
                    <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center border border-blue-100 shrink-0">
                      <Pill className="w-5 h-5 text-blue-500" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-800 text-lg">
                        {med ? med.drug_name : <span className="font-mono text-xs">{item.drug_id}</span>}
                      </h3>
                      {med && <p className="text-sm text-slate-500">{med.generic_name} • {med.form}</p>}
                      
                      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
                        <div>
                          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Dosage</p>
                          <p className="font-medium text-slate-700">{item.dosage}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Frequency</p>
                          <p className="font-medium text-slate-700">{item.frequency}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Duration</p>
                          <p className="font-medium text-slate-700">{item.duration}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Instructions</p>
                          <p className="font-medium text-slate-700">{item.instructions || "As directed"}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Patient Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">Patient Details</h3>
            {patient ? (
              <div>
                <p className="font-bold text-lg text-slate-800">{patient.first_name} {patient.last_name}</p>
                <div className="mt-3 space-y-2 text-sm text-slate-600">
                  <p className="flex justify-between">
                    <span className="text-slate-400">MRN:</span>
                    <span className="font-mono font-medium">{patient.patient_uuid}</span>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-slate-400">DOB:</span>
                    <span>{patient.date_of_birth}</span>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-slate-400">Gender:</span>
                    <span className="capitalize">{patient.gender}</span>
                  </p>
                </div>
              </div>
            ) : (
              <div className="h-10 bg-slate-100 animate-pulse rounded"></div>
            )}
          </div>

          {/* Action Box */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">Workflow Actions</h3>
            
            {prescription.status === "dispensed" ? (
              <div className="bg-emerald-50 text-emerald-700 p-4 rounded-lg flex items-center justify-center gap-2 border border-emerald-200">
                <CheckCircle2 className="w-5 h-5" />
                <span className="font-medium">Already Dispensed</span>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-slate-500 mb-4 bg-blue-50 p-3 rounded-lg border border-blue-100 flex gap-2">
                  <Info className="w-4 h-4 shrink-0 text-blue-500" />
                  Verify patient identity and scan medication barcode before confirming. Inventory will sync automatically.
                </p>
                <button 
                  onClick={handleDispense}
                  disabled={dispensing}
                  className="w-full flex justify-center items-center gap-2 py-3 px-4 bg-[var(--accent-primary)] hover:bg-emerald-600 text-white font-medium rounded-lg transition-all shadow-sm disabled:opacity-50"
                >
                  {dispensing ? (
                    <span className="flex gap-2 items-center"><div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div> Dispensing...</span>
                  ) : (
                    <><Check className="w-5 h-5" /> Confirm Dispense</>
                  )}
                </button>
                <button 
                  className="w-full flex justify-center items-center gap-2 py-3 px-4 bg-white border border-slate-200 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 text-slate-600 font-medium rounded-lg transition-all shadow-sm"
                >
                  <X className="w-5 h-5" /> Cancel / Reject
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
