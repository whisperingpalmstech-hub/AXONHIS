"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { UserPlus, AlertTriangle, Check, ArrowRight } from "lucide-react";

export default function RegistrationPage() {
  const router = useRouter();
  
  // Registration State
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "",
    gender: "",
    primary_phone: "",
    email: "",
    identifier_type: "national_id",
    identifier_value: "",
    insurance_provider: "",
    policy_number: "",
    consent_type: "treatment_consent"
  });

  const [duplicates, setDuplicates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  // Duplicate Check logic
  useEffect(() => {
    if (formData.first_name.length > 2 && formData.last_name.length > 2 && formData.date_of_birth) {
      const checkDups = async () => {
        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/patients/detect-duplicates`, {
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
      // 1. Create Patient
      const patientRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/patients/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
        body: JSON.stringify({
          first_name: formData.first_name,
          last_name: formData.last_name,
          date_of_birth: formData.date_of_birth,
          gender: formData.gender,
          primary_phone: formData.primary_phone,
          email: formData.email
        })
      });

      if (!patientRes.ok) throw new Error("Failed to create patient");
      const patient = await patientRes.json();

      // 2. Add Identity, Insurance, Consent concurrently
      await Promise.all([
        formData.identifier_value && fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/patients/${patient.id}/identifiers/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
          body: JSON.stringify({ identifier_type: formData.identifier_type, identifier_value: formData.identifier_value })
        }),
        formData.insurance_provider && fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/patients/${patient.id}/insurance/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
          body: JSON.stringify({ insurance_provider: formData.insurance_provider, policy_number: formData.policy_number })
        }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/patients/${patient.id}/consents/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("access_token")}` },
          body: JSON.stringify({ consent_type: formData.consent_type, consent_text: "Standard registration consent signed dynamically." })
        })
      ]);

      setSuccess(true);
      setTimeout(() => router.push(`/dashboard/patients/${patient.id}`), 2000);
      
    } catch (err: any) {
      setError(err.message || "An error occurred during registration");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] flex items-center gap-3">
          <UserPlus className="text-[var(--accent-primary)]" /> Patient Registration
        </h1>
        <p className="text-[var(--text-secondary)] mt-2">Register a new patient securely with duplicate detection.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Main Form Area */}
        <form onSubmit={handleSubmit} className="flex-1 space-y-6">
          {error && <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm font-medium border border-red-200">{error}</div>}
          
          {success && (
            <div className="p-6 bg-green-50 text-green-700 rounded-xl border border-green-200 flex items-center gap-4 animate-in fade-in slide-in-from-top-4">
              <div className="bg-green-100 p-3 rounded-full"><Check size={24} /></div>
              <div>
                <h3 className="font-bold text-lg">Registration Successful!</h3>
                <p className="text-sm">Patient identity established. Redirecting to profile...</p>
              </div>
            </div>
          )}

          <div className="card">
            <div className="card-header border-b border-[var(--border)]"><h2 className="text-lg font-semibold">Step 1: Patient Demographics</h2></div>
            <div className="card-body grid grid-cols-2 gap-4">
              <div>
                <label className="input-label">First Name</label>
                <input name="first_name" className="input-field" required value={formData.first_name} onChange={handleChange} />
              </div>
              <div>
                <label className="input-label">Last Name</label>
                <input name="last_name" className="input-field" required value={formData.last_name} onChange={handleChange} />
              </div>
              <div className="relative">
                <label className="input-label">Date of Birth</label>
                <input 
                  type="date" 
                  name="date_of_birth" 
                  className="input-field [color-scheme:light]" 
                  required 
                  value={formData.date_of_birth} 
                  onChange={handleChange} 
                />
              </div>
              <div>
                <label className="input-label">Gender</label>
                <select name="gender" className="input-field" value={formData.gender} onChange={handleChange} required>
                  <option value="">Select gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="input-label">Phone Number</label>
                <input type="text" name="primary_phone" className="input-field" value={formData.primary_phone} onChange={handleChange} />
              </div>
              <div>
                <label className="input-label">Email Address</label>
                <input type="email" name="email" className="input-field" value={formData.email} onChange={handleChange} placeholder="name@example.com" />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header border-b border-[var(--border)]"><h2 className="text-lg font-semibold">Step 2: Identity Verification</h2></div>
            <div className="card-body grid grid-cols-2 gap-4">
              <div>
                <label className="input-label">Identity Type</label>
                <select name="identifier_type" className="input-field" value={formData.identifier_type} onChange={handleChange}>
                  <option value="national_id">National ID</option>
                  <option value="passport">Passport</option>
                  <option value="driver_license">Driver License</option>
                </select>
              </div>
              <div>
                <label className="input-label">Document Number</label>
                <input type="text" name="identifier_value" className="input-field" value={formData.identifier_value} onChange={handleChange} />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header border-b border-[var(--border)]"><h2 className="text-lg font-semibold">Step 3: Insurance & Consent</h2></div>
            <div className="card-body grid grid-cols-2 gap-4">
              <div>
                <label className="input-label">Insurance Provider</label>
                <input type="text" name="insurance_provider" className="input-field" value={formData.insurance_provider} onChange={handleChange} />
              </div>
              <div>
                <label className="input-label">Policy Number</label>
                <input type="text" name="policy_number" className="input-field" value={formData.policy_number} onChange={handleChange} />
              </div>
              
              <div className="col-span-2 pt-4">
                <label className="input-label mb-2 flex items-center gap-2"><Check size={16} className="text-[var(--accent-primary)]"/> Consent Verification</label>
                <div className="bg-[var(--bg-secondary)] p-4 rounded-lg text-sm text-[var(--text-secondary)]">
                  The patient has signed the generic medical treatment consent forms and authorized data collection.
                </div>
              </div>
            </div>
          </div>

          <button 
            type="submit" 
            className="btn-primary w-full flex items-center justify-center gap-2" 
            disabled={loading || success || duplicates.some(d => d.confidence_score > 60)}
          >
            {loading ? "Processing Registration..." : "Complete Registration"} <ArrowRight size={18} />
          </button>
        </form>

        {/* Duplicate Area Panel */}
        <div className="w-full lg:w-[350px]">
          <div className="sticky top-6">
            <div className={`card overflow-hidden transition-all duration-300 ${duplicates.length > 0 ? "border-amber-300 ring-4 ring-amber-500/10 shadow-lg shadow-amber-500/10" : ""}`}>
              <div className={`p-4 font-bold flex items-center gap-2 ${duplicates.length > 0 ? "bg-amber-100 text-amber-900 border-b border-amber-200" : "bg-[var(--bg-secondary)] text-[var(--text-secondary)]"}`}>
                <AlertTriangle size={20} className={duplicates.length > 0 ? "text-amber-500 animate-pulse" : ""} />
                Duplicate Detection Engine
              </div>
              <div className="p-4 bg-[var(--bg-primary)]">
                {duplicates.length === 0 ? (
                  <p className="text-sm text-[var(--text-secondary)]">No potential duplicate records found. Fill the demographics to trigger fuzzy matching.</p>
                ) : (
                  <div className="space-y-4">
                    <p className="text-sm font-medium text-amber-800">Warning: High similarity records detected in the Master Index.</p>
                    
                    <div className="space-y-3">
                      {duplicates.slice(0, 3).map((dup, i) => (
                        <div key={i} className="bg-white border text-sm border-amber-200 rounded-lg p-3 shadow-sm">
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-bold">{dup.patient.first_name} {dup.patient.last_name}</span>
                            <span className="bg-amber-100 text-amber-800 text-[10px] px-2 py-0.5 rounded-full font-bold">
                              {dup.confidence_score}% Match
                            </span>
                          </div>
                          <div className="text-[var(--text-secondary)] text-xs grid grid-cols-1 gap-1">
                            <div>DOB: {dup.patient.date_of_birth}</div>
                            <div>Phone: {dup.patient.primary_phone || "N/A"}</div>
                            <div>ID: {dup.patient.patient_uuid}</div>
                          </div>
                        </div>
                      ))}
                    </div>

                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
