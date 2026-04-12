"use client";

import React, { useState } from "react";
import { Building2, Globe, ArrowRight, Activity, Cpu } from "lucide-react";
import { tenantsApi } from "@/lib/tenants-api";
import { useRouter } from "next/navigation";

export default function RegisterOrganization() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    setSuccessMsg("");
    const fd = new FormData(e.currentTarget);
    const org_code = fd.get("org_code") as string;
    const admin_password = fd.get("admin_password") as string;
    
    try {
      await tenantsApi.createOrganization({
        name: fd.get("name") as string,
        org_code: org_code,
        country: fd.get("country") as string,
        contact_email: fd.get("email") as string,
        default_language: fd.get("default_language") as string,
        global_settings: { voice_ai_enabled: true },
        admin_password: admin_password
      });
      
      setSuccessMsg(`Welcome to AxonHIS Edge Network! Your tenant was provisioned. Please login with admin@${org_code.toLowerCase()}.com | Password: ${admin_password}`);
      setTimeout(() => {
        router.push("/login");
      }, 7000);
    } catch (err: any) {
      setErrorMsg("Failed to provision tenant space. Please choose a different Tenant Namespace code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white rounded-3xl overflow-hidden shadow-2xl shadow-blue-900/10 flex">
        {/* LEFT BRANDING SIDE */}
        <div className="w-5/12 bg-blue-600 p-12 text-white flex flex-col justify-between hidden md:flex">
          <div>
            <div className="flex items-center gap-2 mb-8 w-max px-3 py-1.5 bg-blue-500/50 rounded-lg text-sm font-bold tracking-widest"><Cpu size={16}/> AXONHIS EDGE</div>
            <h1 className="text-4xl font-black tracking-tight leading-tight">Deploy your next-gen hospital today.</h1>
            <p className="mt-4 text-blue-100 font-medium">Provision an isolated, secure enterprise workspace. Your master configuration comes with AI Scribing and multi-facility capabilities out of the box.</p>
          </div>
          
          <div className="space-y-4 text-sm font-medium text-blue-200 border-t border-blue-500 pt-6">
            <div className="flex items-center gap-3"><Activity size={18} className="text-emerald-300"/> Tier-1 Data Partitioning</div>
            <div className="flex items-center gap-3"><Globe size={18} className="text-amber-300"/> Multilingual Patient Routing</div>
            <div className="flex items-center gap-3"><Building2 size={18} className="text-purple-300"/> Unlimited Distributed Sites</div>
          </div>
        </div>

        {/* RIGHT FORM SIDE */}
        <div className="flex-1 p-10 lg:p-12">
          <div className="mb-8">
            <h2 className="text-2xl font-black text-slate-800">Provision Tenant Workspace</h2>
            <p className="text-sm font-medium text-slate-500 mt-2">Enter your healthcare organization's details to instantly auto-generate your master administrative account and private sector boundary.</p>
          </div>

          {errorMsg && (
            <div className="mb-6 p-4 bg-red-50 text-red-600 font-bold text-sm rounded-xl border border-red-100">
              {errorMsg}
            </div>
          )}

          {successMsg ? (
            <div className="p-8 bg-emerald-50 rounded-2xl border border-emerald-100 text-center animate-in fade-in zoom-in">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4"><Activity size={32}/></div>
              <h3 className="text-xl font-black text-emerald-800 mb-2">Workspace Deployed!</h3>
              <p className="text-sm font-bold text-emerald-600 mb-6">{successMsg}</p>
              <button onClick={() => router.push("/login")} className="px-6 py-2.5 bg-emerald-600 text-white font-bold rounded-xl shadow-md">Redirecting to Vault...</button>
            </div>
          ) : (
            <form onSubmit={handleRegister} className="space-y-5">
                <div className="grid grid-cols-2 gap-5">
                    <div>
                        <label className="text-[10px] uppercase font-black tracking-widest text-slate-500">Legal Org Name</label>
                        <input name="name" required placeholder="Riverside Health" className="w-full mt-1.5 p-3 border border-slate-200 rounded-xl text-sm bg-slate-50 outline-none focus:border-blue-500 font-medium text-slate-800 transition-colors"/>
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-black tracking-widest text-slate-500">Tenant Namespace</label>
                        <input name="org_code" required placeholder="RIV-HLT" className="w-full mt-1.5 p-3 border border-slate-200 rounded-xl text-sm bg-slate-50 outline-none focus:border-blue-500 font-mono text-slate-800 uppercase transition-colors"/>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-5">
                    <div>
                        <label className="text-[10px] uppercase font-black tracking-widest text-slate-500">Operating Country</label>
                        <input name="country" required placeholder="United Kingdom" className="w-full mt-1.5 p-3 border border-slate-200 rounded-xl text-sm bg-slate-50 outline-none focus:border-blue-500 font-medium text-slate-800"/>
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-black tracking-widest text-slate-500">Base Language</label>
                        <select name="default_language" className="w-full mt-1.5 p-3 border border-slate-200 rounded-xl text-sm bg-slate-50 outline-none focus:border-blue-500 font-bold text-slate-800 cursor-pointer">
                            <option value="en">English (UK)</option>
                            <option value="es">Spanish (ES)</option>
                            <option value="hi">Hindi (IN)</option>
                            <option value="ar">Arabic (AE)</option>
                        </select>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-5">
                    <div>
                        <label className="text-[10px] uppercase font-black tracking-widest text-slate-500">IT Administrator Email (Recovery)</label>
                        <input name="email" type="email" required placeholder="it-director@riverside.local" className="w-full mt-1.5 p-3 border border-slate-200 rounded-xl text-sm bg-slate-50 outline-none focus:border-blue-500 font-medium text-slate-800"/>
                        <p className="text-xs text-slate-400 font-medium mt-2">Note: AxonHIS will automatically provision 'admin@{'{tenant-code}'}.com' linked to this sector.</p>
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-black tracking-widest text-slate-500">Master Vault Password</label>
                        <input name="admin_password" type="password" required minLength={8} placeholder="••••••••" className="w-full mt-1.5 p-3 border border-slate-200 rounded-xl text-sm bg-slate-50 outline-none focus:border-blue-500 font-medium text-slate-800 tracking-widest"/>
                        <p className="text-xs text-slate-400 font-medium mt-2">Create a secure password for your initial Tenant Admin credentials.</p>
                    </div>
                </div>

                <div className="pt-6 mt-6 border-t border-slate-100 flex items-center justify-between">
                    <button type="button" onClick={() => router.push("/login")} className="text-sm font-bold text-slate-500 hover:text-slate-800 transition-colors">← Back to Login</button>
                    <button type="submit" disabled={loading} className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-200 transition-all flex items-center gap-2">
                        {loading ? "Provisioning Engine..." : "Deploy Tenant "} 
                        {!loading && <ArrowRight size={18}/>}
                    </button>
                </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
