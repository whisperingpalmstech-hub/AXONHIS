"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  UserPlus, AlertTriangle, Check, ArrowRight,
  Droplets, Activity, Weight, Heart, FileText, Phone, Mail, Shield
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

export default function RegistrationPage() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    // Demographics
    first_name: "",
    last_name: "",
    date_of_birth: "",
    gender: "",
    primary_phone: "",
    email: "",

    // Medical Info
    blood_group: "",
    weight_kg: "",
    height_cm: "",
    allergies: "",
    chronic_conditions: "",
    current_medications: "",
    chief_complaint: "",
    family_history: "",

    // Identity
    identifier_type: "national_id",
    identifier_value: "",

    // Insurance
    insurance_provider: "",
    policy_number: "",

    // Emergency Contact
    emergency_contact_name: "",
    emergency_contact_phone: "",

    consent_type: "treatment_consent",
  });

  const [duplicates, setDuplicates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [activeStep, setActiveStep] = useState(1);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  // Duplicate Check
  useEffect(() => {
    if (formData.first_name.length > 2 && formData.last_name.length > 2 && formData.date_of_birth) {
      const checkDups = async () => {
        try {
          const res = await fetch(`${API}/api/v1/patients/detect-duplicates`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({
              first_name: formData.first_name,
              last_name: formData.last_name,
              date_of_birth: formData.date_of_birth,
              phone: formData.primary_phone
            })
          });
          if (res.ok) {
            const data = await res.json();
            setDuplicates(data);
          }
        } catch (err) {
          console.error(err);
        }
      };
      const to = setTimeout(checkDups, 800);
      return () => clearTimeout(to);
    } else {
      setDuplicates([]);
    }
  }, [formData.first_name, formData.last_name, formData.date_of_birth, formData.primary_phone]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // 1. Create Patient (core demographics + medical)
      const patientPayload: any = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        date_of_birth: formData.date_of_birth,
        gender: formData.gender,
        primary_phone: formData.primary_phone || undefined,
        email: formData.email || undefined,
      };

      const patientRes = await fetch(`${API}/api/v1/patients/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("access_token")}`
        },
        body: JSON.stringify(patientPayload)
      });

      if (!patientRes.ok) {
        const err = await patientRes.json();
        throw new Error(err.detail || "Failed to create patient");
      }
      const patient = await patientRes.json();

      // Build medical info note
      const medNote = [
        formData.blood_group && `Blood Group: ${formData.blood_group}`,
        formData.weight_kg && `Weight: ${formData.weight_kg} kg`,
        formData.height_cm && `Height: ${formData.height_cm} cm`,
        formData.allergies && `Allergies: ${formData.allergies}`,
        formData.chronic_conditions && `Chronic Conditions: ${formData.chronic_conditions}`,
        formData.current_medications && `Current Medications: ${formData.current_medications}`,
        formData.chief_complaint && `Chief Complaint: ${formData.chief_complaint}`,
        formData.family_history && `Family History: ${formData.family_history}`,
        formData.emergency_contact_name && `Emergency Contact: ${formData.emergency_contact_name} (${formData.emergency_contact_phone || "N/A"})`,
      ].filter(Boolean).join("\n");

      // 2. Add related records concurrently
      const promises: Promise<any>[] = [];

      // Identifier
      if (formData.identifier_value) {
        promises.push(fetch(`${API}/api/v1/patients/${patient.id}/identifiers/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
          body: JSON.stringify({ identifier_type: formData.identifier_type, identifier_value: formData.identifier_value })
        }));
      }

      // Insurance
      if (formData.insurance_provider) {
        promises.push(fetch(`${API}/api/v1/patients/${patient.id}/insurance/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
          body: JSON.stringify({ insurance_provider: formData.insurance_provider, policy_number: formData.policy_number || "" })
        }));
      }

      // Consent
      promises.push(fetch(`${API}/api/v1/patients/${patient.id}/consents/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
        body: JSON.stringify({ consent_type: formData.consent_type, consent_text: "Standard registration consent signed during admission." })
      }));

      await Promise.allSettled(promises);

      setSuccess(true);
      setTimeout(() => router.push(`/dashboard/patients/${patient.id}`), 2000);

    } catch (err: any) {
      setError(err.message || "An error occurred during registration");
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { num: 1, label: "Demographics", icon: <UserPlus size={16}/> },
    { num: 2, label: "Medical Info", icon: <Heart size={16}/> },
    { num: 3, label: "Identity & Insurance", icon: <Shield size={16}/> },
  ];

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] flex items-center gap-3">
          <UserPlus className="text-[var(--accent-primary)]"/> Patient Registration
        </h1>
        <p className="text-[var(--text-secondary)] mt-2">Register a new patient with complete medical profile and duplicate detection.</p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center gap-0 mb-8">
        {steps.map((step, idx) => (
          <React.Fragment key={step.num}>
            <button
              onClick={() => setActiveStep(step.num)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-semibold text-sm transition-all ${activeStep === step.num ? 'bg-[var(--accent-primary)] text-white shadow-md' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-slate-200'}`}
            >
              {step.icon} Step {step.num}: {step.label}
            </button>
            {idx < steps.length - 1 && <div className="flex-1 h-0.5 bg-slate-200 mx-2"/>}
          </React.Fragment>
        ))}
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <form onSubmit={handleSubmit} className="flex-1 space-y-6">
          {error && <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm font-medium border border-red-200">{error}</div>}

          {success && (
            <div className="p-6 bg-green-50 text-green-700 rounded-xl border border-green-200 flex items-center gap-4">
              <div className="bg-green-100 p-3 rounded-full"><Check size={24}/></div>
              <div>
                <h3 className="font-bold text-lg">Registration Successful!</h3>
                <p className="text-sm">Patient identity established. Redirecting to profile...</p>
              </div>
            </div>
          )}

          {/* ─── STEP 1: Demographics ─── */}
          {activeStep === 1 && (
            <div className="card">
              <div className="card-header border-b border-[var(--border)] flex items-center gap-2">
                <UserPlus size={18} className="text-[var(--accent-primary)]"/>
                <h2 className="text-lg font-semibold">Patient Demographics</h2>
              </div>
              <div className="card-body grid grid-cols-2 gap-4">
                <div>
                  <label className="input-label">First Name *</label>
                  <input name="first_name" className="input-field" required value={formData.first_name} onChange={handleChange}/>
                </div>
                <div>
                  <label className="input-label">Last Name *</label>
                  <input name="last_name" className="input-field" required value={formData.last_name} onChange={handleChange}/>
                </div>
                <div>
                  <label className="input-label">Date of Birth *</label>
                  <input type="date" name="date_of_birth" className="input-field [color-scheme:light]" required value={formData.date_of_birth} onChange={handleChange}/>
                </div>
                <div>
                  <label className="input-label">Gender *</label>
                  <select name="gender" className="input-field" value={formData.gender} onChange={handleChange} required>
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="input-label flex items-center gap-1"><Phone size={13}/> Phone Number</label>
                  <input type="tel" name="primary_phone" className="input-field" value={formData.primary_phone} onChange={handleChange} placeholder="+91 98765 43210"/>
                </div>
                <div>
                  <label className="input-label flex items-center gap-1"><Mail size={13}/> Email Address</label>
                  <input type="email" name="email" className="input-field" value={formData.email} onChange={handleChange} placeholder="patient@example.com"/>
                </div>
                <div>
                  <label className="input-label">Emergency Contact Name</label>
                  <input name="emergency_contact_name" className="input-field" value={formData.emergency_contact_name} onChange={handleChange} placeholder="Guardian / Relative name"/>
                </div>
                <div>
                  <label className="input-label">Emergency Contact Phone</label>
                  <input type="tel" name="emergency_contact_phone" className="input-field" value={formData.emergency_contact_phone} onChange={handleChange} placeholder="+91 98765 43210"/>
                </div>
              </div>
              <div className="card-body border-t border-[var(--border)] flex justify-end">
                <button type="button" onClick={() => setActiveStep(2)} className="btn-primary flex items-center gap-2">
                  Next: Medical Info <ArrowRight size={16}/>
                </button>
              </div>
            </div>
          )}

          {/* ─── STEP 2: Medical Info ─── */}
          {activeStep === 2 && (
            <div className="card">
              <div className="card-header border-b border-[var(--border)] flex items-center gap-2">
                <Heart size={18} className="text-rose-500"/>
                <h2 className="text-lg font-semibold">Medical Information</h2>
              </div>
              <div className="card-body grid grid-cols-2 gap-4">
                <div>
                  <label className="input-label flex items-center gap-1"><Droplets size={13} className="text-red-500"/> Blood Group</label>
                  <select name="blood_group" className="input-field" value={formData.blood_group} onChange={handleChange}>
                    <option value="">Unknown / Not tested</option>
                    <option value="A+">A Positive (A+)</option>
                    <option value="A-">A Negative (A-)</option>
                    <option value="B+">B Positive (B+)</option>
                    <option value="B-">B Negative (B-)</option>
                    <option value="AB+">AB Positive (AB+)</option>
                    <option value="AB-">AB Negative (AB-)</option>
                    <option value="O+">O Positive (O+)</option>
                    <option value="O-">O Negative (O-)</option>
                  </select>
                </div>
                <div>
                  <label className="input-label flex items-center gap-1"><Weight size={13} className="text-green-600"/> Weight (kg)</label>
                  <input type="number" step="0.1" name="weight_kg" className="input-field" value={formData.weight_kg} onChange={handleChange} placeholder="e.g. 72.5"/>
                </div>
                <div>
                  <label className="input-label flex items-center gap-1"><Activity size={13} className="text-purple-500"/> Height (cm)</label>
                  <input type="number" name="height_cm" className="input-field" value={formData.height_cm} onChange={handleChange} placeholder="e.g. 175"/>
                </div>
                <div className="col-span-2">
                  <label className="input-label flex items-center gap-1"><AlertTriangle size={13} className="text-amber-500"/> Known Allergies</label>
                  <input type="text" name="allergies" className="input-field" value={formData.allergies} onChange={handleChange} placeholder="e.g. Penicillin, Sulfa drugs, Shellfish..."/>
                </div>
                <div className="col-span-2">
                  <label className="input-label flex items-center gap-1"><FileText size={13} className="text-blue-600"/> Chief Complaint / Presenting Symptoms</label>
                  <textarea
                    name="chief_complaint"
                    className="input-field min-h-[80px] resize-none"
                    value={formData.chief_complaint}
                    onChange={handleChange}
                    placeholder="e.g. Fever for 3 days, cough, shortness of breath..."
                  />
                </div>
                <div className="col-span-2">
                  <label className="input-label">Chronic Conditions / Past Medical History</label>
                  <textarea
                    name="chronic_conditions"
                    className="input-field min-h-[70px] resize-none"
                    value={formData.chronic_conditions}
                    onChange={handleChange}
                    placeholder="e.g. Diabetes Type 2, Hypertension, Asthma..."
                  />
                </div>
                <div className="col-span-2">
                  <label className="input-label">Current Medications</label>
                  <textarea
                    name="current_medications"
                    className="input-field min-h-[70px] resize-none"
                    value={formData.current_medications}
                    onChange={handleChange}
                    placeholder="e.g. Metformin 500mg, Amlodipine 5mg..."
                  />
                </div>
                <div className="col-span-2">
                  <label className="input-label">Family Medical History</label>
                  <input name="family_history" className="input-field" value={formData.family_history} onChange={handleChange} placeholder="e.g. Father: Diabetes, Mother: Hypertension"/>
                </div>
              </div>
              <div className="card-body border-t border-[var(--border)] flex justify-between">
                <button type="button" onClick={() => setActiveStep(1)} className="btn-secondary flex items-center gap-2">Back</button>
                <button type="button" onClick={() => setActiveStep(3)} className="btn-primary flex items-center gap-2">
                  Next: Identity & Insurance <ArrowRight size={16}/>
                </button>
              </div>
            </div>
          )}

          {/* ─── STEP 3: Identity & Insurance ─── */}
          {activeStep === 3 && (
            <>
              <div className="card">
                <div className="card-header border-b border-[var(--border)] flex items-center gap-2">
                  <Shield size={18} className="text-[var(--accent-primary)]"/>
                  <h2 className="text-lg font-semibold">Identity Verification</h2>
                </div>
                <div className="card-body grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">Identity Type</label>
                    <select name="identifier_type" className="input-field" value={formData.identifier_type} onChange={handleChange}>
                      <option value="national_id">National ID (Aadhaar)</option>
                      <option value="passport">Passport</option>
                      <option value="driver_license">Driver License</option>
                      <option value="voter_id">Voter ID</option>
                      <option value="pan_card">PAN Card</option>
                    </select>
                  </div>
                  <div>
                    <label className="input-label">Document Number</label>
                    <input type="text" name="identifier_value" className="input-field" value={formData.identifier_value} onChange={handleChange} placeholder="Enter document number"/>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header border-b border-[var(--border)]">
                  <h2 className="text-lg font-semibold">Insurance & Consent</h2>
                </div>
                <div className="card-body grid grid-cols-2 gap-4">
                  <div>
                    <label className="input-label">Insurance Provider</label>
                    <input type="text" name="insurance_provider" className="input-field" value={formData.insurance_provider} onChange={handleChange} placeholder="e.g. Star Health, HDFC Ergo"/>
                  </div>
                  <div>
                    <label className="input-label">Policy Number</label>
                    <input type="text" name="policy_number" className="input-field" value={formData.policy_number} onChange={handleChange} placeholder="e.g. POL-123456789"/>
                  </div>
                  <div className="col-span-2 pt-2">
                    <label className="input-label mb-2 flex items-center gap-2"><Check size={16} className="text-[var(--accent-primary)]"/> Consent Verification</label>
                    <div className="bg-[var(--bg-secondary)] p-4 rounded-lg text-sm text-[var(--text-secondary)] border border-[var(--border)]">
                      The patient has reviewed and signed the generic medical treatment consent forms. Data collection is authorized as per hospital policy.
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <button type="button" onClick={() => setActiveStep(2)} className="btn-secondary flex items-center gap-2">Back</button>
                <button
                  type="submit"
                  className="btn-primary flex items-center gap-2 px-8"
                  disabled={loading || success || duplicates.some(d => d.confidence_score > 60)}
                >
                  {loading ? "Processing..." : "Complete Registration"} <ArrowRight size={18}/>
                </button>
              </div>
            </>
          )}
        </form>

        {/* Duplicate Detection Panel */}
        <div className="w-full lg:w-[350px]">
          <div className="sticky top-6">
            <div className={`card overflow-hidden transition-all duration-300 ${duplicates.length > 0 ? "border-amber-300 ring-4 ring-amber-500/10 shadow-lg shadow-amber-500/10" : ""}`}>
              <div className={`p-4 font-bold flex items-center gap-2 ${duplicates.length > 0 ? "bg-amber-100 text-amber-900 border-b border-amber-200" : "bg-[var(--bg-secondary)] text-[var(--text-secondary)]"}`}>
                <AlertTriangle size={20} className={duplicates.length > 0 ? "text-amber-500 animate-pulse" : ""}/>
                Duplicate Detection Engine
              </div>
              <div className="p-4 bg-[var(--bg-primary)]">
                {duplicates.length === 0 ? (
                  <p className="text-sm text-[var(--text-secondary)]">No duplicates detected. Fill demographics to trigger fuzzy matching.</p>
                ) : (
                  <div className="space-y-4">
                    <p className="text-sm font-medium text-amber-800">⚠ High-similarity records found in Master Patient Index.</p>
                    <div className="space-y-3">
                      {duplicates.slice(0, 3).map((dup, i) => (
                        <div key={i} className="bg-white border border-amber-200 rounded-lg p-3 text-sm shadow-sm">
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-bold">{dup.patient.first_name} {dup.patient.last_name}</span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${dup.confidence_score >= 70 ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>
                              {dup.confidence_score}% Match
                            </span>
                          </div>
                          <div className="text-[var(--text-secondary)] text-xs grid gap-1">
                            <div>DOB: {dup.patient.date_of_birth}</div>
                            <div>Phone: {dup.patient.primary_phone || "N/A"}</div>
                            <div>ID: {dup.patient.patient_uuid}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                    {duplicates.some(d => d.confidence_score > 60) && (
                      <p className="text-xs text-red-600 font-semibold">⛔ Submit blocked. Resolve duplicates first or verify this is a new patient.</p>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Medical Info Summary (shown after step 2 filled) */}
            {(formData.blood_group || formData.allergies || formData.chief_complaint) && (
              <div className="card mt-4 overflow-hidden">
                <div className="p-4 font-bold bg-blue-50 text-blue-800 border-b border-blue-100 text-sm flex items-center gap-2">
                  <Heart size={16}/> Medical Summary
                </div>
                <div className="p-4 space-y-2 text-xs bg-white">
                  {formData.blood_group && <div className="flex items-center gap-2"><Droplets size={12} className="text-red-500"/><span className="text-slate-600">Blood Group:</span> <strong>{formData.blood_group}</strong></div>}
                  {formData.weight_kg && <div className="flex items-center gap-2"><Weight size={12} className="text-green-500"/><span className="text-slate-600">Weight:</span> <strong>{formData.weight_kg} kg</strong></div>}
                  {formData.allergies && <div className="flex items-start gap-2"><AlertTriangle size={12} className="text-amber-500 mt-0.5"/><span className="text-slate-600">Allergies:</span> <strong className="text-red-700">{formData.allergies}</strong></div>}
                  {formData.chief_complaint && <div className="flex items-start gap-2"><FileText size={12} className="text-blue-500 mt-0.5"/><span className="text-slate-600">Complaint:</span> <span className="text-slate-800">{formData.chief_complaint.slice(0, 80)}...</span></div>}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
