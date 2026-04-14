"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, Mail, Lock, UserRound } from "lucide-react";
import { portalApi } from "@/lib/portal-api";

export default function PatientLogin() {
  const router = useRouter();
  const [email, setEmail] = useState("soham123@gmail.com");
  const [password, setPassword] = useState("Patient@123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await portalApi.login(email, password);
      
      if (response.access_token) {
        localStorage.setItem("patient_token", response.access_token);
        // Extract patient_id from token (format: patient_token_<account_id>)
        // Use the profile API to get the real patient_id
        try {
          const tokenParts = response.access_token.split("patient_token_");
          const accountId = tokenParts.length > 1 ? tokenParts[1] : "";
          if (accountId) {
            const profile = await portalApi.getPatientInfo(accountId);
            if (profile && profile.patient_id) {
              localStorage.setItem("patient_id", String(profile.patient_id));
            } else {
              localStorage.setItem("patient_id", "6e65086b-f072-4161-a7af-49806b6439ac");
            }
          } else {
            localStorage.setItem("patient_id", "6e65086b-f072-4161-a7af-49806b6439ac");
          }
        } catch {
          localStorage.setItem("patient_id", "6e65086b-f072-4161-a7af-49806b6439ac");
        }
        router.push("/dashboard");
      } else {
        setError(response.detail || "Invalid email or password. Please try again.");
      }
    } catch (err: any) {
      setError("Connection error. Please ensure the portal backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-50">
      <div className="bg-white p-10 rounded-3xl shadow-xl w-full max-w-md border border-slate-100">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center text-white mb-4 shadow-md">
             <span className="text-3xl font-bold">A</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900">Patient Portal</h1>
          <p className="text-slate-500 mt-2 font-medium">Log in to manage your health</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm font-semibold mb-6 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-600"></span>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3.5 text-slate-400" size={20} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 outline-none transition-all font-medium"
                placeholder="patient@example.com"
              />
            </div>
          </div>

          <div>
             <div className="flex justify-between items-center mb-1.5">
               <label className="block text-sm font-bold text-slate-700">Password</label>
               <a href="#" className="text-xs font-bold text-indigo-600 hover:text-indigo-800">Forgot?</a>
             </div>
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

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-md disabled:opacity-70 transition-all flex justify-center items-center gap-2"
          >
            {loading ? <Activity className="animate-spin" size={20} /> : "Sign In to Portal"}
          </button>
        </form>

        <p className="text-center text-slate-500 text-sm mt-8 font-medium">
          Don't have an account? <button onClick={() => router.push("/register")} className="text-indigo-600 font-bold hover:underline">Register here</button>
        </p>
      </div>
    </div>
  );
}
