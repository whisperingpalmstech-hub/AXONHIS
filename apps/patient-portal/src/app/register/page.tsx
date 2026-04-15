"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, Mail, Lock, UserRound, ArrowLeft, Search } from "lucide-react";
import { portalApi } from "@/lib/portal-api";

export default function PatientRegister() {
  const router = useRouter();
  const [step, setStep] = useState(1); // 1: Search, 2: Account Details
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [patientId, setPatientId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await portalApi.searchPatient(email);
      if (result.patient_id) {
        setPatientId(result.patient_id);
        setStep(2);
      } else {
        const errDetail = typeof result.detail === 'string' ? result.detail : (Array.isArray(result.detail) ? result.detail[0].msg : "Patient not found in HIS. Please contact the hospital.");
        setError(errDetail);
      }
    } catch (err) {
      setError("Search failed. Please ensure you are entering a valid email or ID registered at the hospital.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setError("");

    try {
      const result = await portalApi.register({ 
        email, 
        password, 
        patient_id: patientId,
        phone_number: null // Optional
      });
      
      if (result.id) {
        setSuccess("Account created successfully! Redirecting to login...");
        setTimeout(() => router.push("/login"), 2000);
      } else {
        const errDetail = typeof result.detail === 'string' ? result.detail : (Array.isArray(result.detail) ? result.detail[0].msg : "Registration failed.");
        setError(errDetail);
      }
    } catch (err) {
      setError("Registration failed. Account might already exist.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-50 p-4">
      <div className="bg-white p-10 rounded-3xl shadow-xl w-full max-w-md border border-slate-100">
        <button 
          onClick={() => step === 1 ? router.push("/login") : setStep(1)}
          className="flex items-center gap-2 text-slate-400 hover:text-indigo-600 mb-6 transition-colors font-medium text-sm"
        >
          <ArrowLeft size={16} /> Back
        </button>

        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center text-white mb-4 shadow-md">
             <span className="text-3xl font-bold">A</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900">Create Account</h1>
          <p className="text-slate-500 mt-2 font-medium text-center">
            {step === 1 ? "First, find your records in our system" : "Now, set up your portal login details"}
          </p>
        </div>

        <div className="min-h-[4rem] mb-2">
          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm font-semibold flex items-center gap-2 border border-red-100">
              <span className="w-2 h-2 rounded-full bg-red-600"></span>
              {error}
            </div>
          )}

          {success && (
            <div className="bg-emerald-50 text-emerald-600 p-4 rounded-xl text-sm font-semibold flex items-center gap-2 border border-emerald-100">
              <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
              {success}
            </div>
          )}
        </div>

        {step === 1 ? (
          <form key="search-form" onSubmit={handleSearch} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5">Registered Email or Patient ID</label>
              <div className="relative">
                <Search className="absolute left-3.5 top-3.5 text-slate-400" size={20} />
                <input
                  type="text"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 outline-none transition-all font-medium"
                  placeholder="e.g. patient@email.com or PID123"
                />
              </div>
              <p className="text-[10px] text-slate-400 mt-2 italic px-1">
                Note: Use the email you provided during hospital registration.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-md disabled:opacity-70 transition-all flex justify-center items-center gap-2"
            >
              {loading ? <Activity className="animate-spin" size={20} /> : "Find My Records"}
            </button>
          </form>
        ) : (
          <form key="registration-form" onSubmit={handleRegister} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5">Create Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 text-slate-400" size={20} />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 outline-none transition-all font-medium"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 text-slate-400" size={20} />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 outline-none transition-all font-medium"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-md disabled:opacity-70 transition-all flex justify-center items-center gap-2"
            >
              {loading ? <Activity className="animate-spin" size={20} /> : "Complete Registration"}
            </button>
          </form>
        )}

        <p className="text-center text-slate-500 text-sm mt-8 font-medium">
          Already have an account? <button onClick={() => router.push("/login")} className="text-indigo-600 font-bold hover:underline">Log in</button>
        </p>
      </div>
    </div>
  );
}
