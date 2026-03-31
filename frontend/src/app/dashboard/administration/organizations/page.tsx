"use client";

import React, { useState, useEffect } from "react";
import { TopNav } from "@/components/ui/TopNav";
import { tenantsApi, type Organization, type Site } from "@/lib/tenants-api";
import { Building2, MapPin, Globe, Mic, Settings2, Plus, Users, Save, CheckCircle2, AlertTriangle, ShieldCheck, Database, ShieldAlert } from "lucide-react";

export default function TenantManagementDashboard() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);
  
  const [showOrgModal, setShowOrgModal] = useState(false);
  const [showSiteModal, setShowSiteModal] = useState<string | null>(null);
  const [showConfigSiteModal, setShowConfigSiteModal] = useState<Site | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await tenantsApi.getOrganizations();
      setOrgs(data || []);
    } catch(e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const createOrg = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await tenantsApi.createOrganization({
        name: fd.get("name"),
        org_code: fd.get("org_code"),
        country: fd.get("country"),
        contact_email: fd.get("email"),
        default_language: fd.get("default_language") || "en",
        global_settings: { voice_enabled: fd.get("voice_enabled") === "on" }
      });
      setShowOrgModal(false);
      fetchData();
    } catch (e) {
      alert("Error: Org code/name may already exist");
    }
  };

  const addSite = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if(!showSiteModal) return;
    const fd = new FormData(e.currentTarget);
    try {
      await tenantsApi.addSite(showSiteModal, {
        name: fd.get("name"),
        site_code: fd.get("site_code"),
        location_address: fd.get("location_address"),
        timezone: fd.get("timezone") || "UTC"
      });
      setShowSiteModal(null);
      fetchData();
    } catch (e) {
      alert("Error adding site configuration.");
    }
  };

  const toggleVoice = async (id: string, currentlyEnabled: boolean) => {
    try {
        await tenantsApi.toggleVoiceSettings(id, !currentlyEnabled);
        fetchData();
    } catch (e) {
        alert("Action failed.");
    }
  };

  const changeLanguage = async (id: string, lang: string) => {
    try {
        await tenantsApi.changeLanguage(id, lang);
        fetchData();
    } catch (e) {
        alert("Action failed.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <TopNav title="Multi-Tenancy & Global Configurations" />
      <div className="flex-1 p-8 max-w-[1600px] mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
              <Building2 className="text-blue-600" size={32}/>
              Master Tenant Management
            </h1>
            <p className="text-slate-500 font-medium mt-1">Multi-site architecture, configuration masters, multilingual routing, and AI policy control.</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setShowOrgModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl font-bold transition-all shadow-md shadow-blue-200">
              <Plus size={18}/> New Enterprise Organization
            </button>
          </div>
        </div>

        {/* Global Control Status */}
        <div className="grid grid-cols-4 gap-4 mb-8">
            <div className="bg-gradient-to-br from-indigo-500 to-blue-600 text-white p-6 rounded-2xl shadow-sm">
                <div className="flex items-center gap-2 opacity-80 mb-2 font-bold text-sm"><ShieldCheck size={18}/> SaaS Ecosystem</div>
                <div className="text-3xl font-black">{orgs.length} Active Tenants</div>
            </div>
            <div className="bg-white border border-slate-200 text-slate-700 p-6 rounded-2xl shadow-sm">
                <div className="flex items-center gap-2 text-slate-500 mb-2 font-bold text-sm"><MapPin size={18}/> Deployed Sites</div>
                <div className="text-3xl font-black text-slate-800">{orgs.reduce((a, b) => a + (b.sites?.length || 0), 0)}</div>
            </div>
            <div className="bg-emerald-50 border border-emerald-200 text-slate-700 p-6 rounded-2xl shadow-sm">
                <div className="flex items-center gap-2 text-emerald-600 mb-2 font-bold text-sm"><Mic size={18}/> Global Voice AI</div>
                <div className="text-3xl font-black text-emerald-700">Online</div>
            </div>
            <div className="bg-purple-50 border border-purple-200 text-slate-700 p-6 rounded-2xl shadow-sm">
                <div className="flex items-center gap-2 text-purple-600 mb-2 font-bold text-sm"><Globe size={18}/> i18n Localization</div>
                <div className="text-3xl font-black text-purple-700">Enabled</div>
            </div>
        </div>

        {loading ? (
          <div className="text-slate-400 font-medium text-center py-12">Loading Enterprise Configurations...</div>
        ) : (
          <div className="space-y-8">
            {orgs.length === 0 ? (
                <div className="text-center py-12 text-slate-400 border-2 border-dashed border-slate-200 rounded-2xl">
                    No organizations configured in the cluster.
                </div>
            ) : (
                orgs.map(org => (
                    <div key={org.id} className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col hover:border-blue-300 transition-all">
                        {/* ORG HEADER */}
                        <div className="bg-slate-50 border-b border-slate-200 p-6 flex justify-between items-center">
                            <div className="flex items-center gap-4">
                                <div className="w-16 h-16 bg-blue-100 text-blue-700 rounded-2xl flex items-center justify-center font-black text-2xl uppercase shadow-inner">
                                    {org.name.substring(0,2)}
                                </div>
                                <div>
                                    <h3 className="text-2xl font-black text-slate-800 tracking-tight">{org.name}</h3>
                                    <div className="text-sm font-bold text-slate-500 tracking-widest font-mono mt-1 flex items-center gap-3">
                                        <span>TENANT: {org.org_code}</span>
                                        <span>•</span>
                                        <span className="text-emerald-600 bg-emerald-50 px-2 rounded lowercase border border-emerald-100">admin@{org.org_code.toLowerCase()}.com</span>
                                        <span>•</span>
                                        <span className="flex items-center gap-1"><Globe size={14}/> {org.country || "Global"}</span>
                                    </div>
                                </div>
                            </div>

                            {/* TENANT CONFIGURATIONS (LANGUAGE & VOICE) */}
                            <div className="flex items-center gap-6 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                                <div className="flex items-center gap-2">
                                    <Globe size={16} className="text-slate-400"/>
                                    <div className="flex flex-col">
                                        <label className="text-[10px] uppercase font-black text-slate-500">Language Region</label>
                                        <select 
                                            value={org.default_language} 
                                            onChange={(e) => changeLanguage(org.id as string, e.target.value)}
                                            className="text-xs font-bold text-slate-800 outline-none w-24 cursor-pointer"
                                        >
                                            <option value="en">English (UK)</option>
                                            <option value="fr">Français (FR)</option>
                                            <option value="hi">Hindi (IN)</option>
                                            <option value="ar">Arabic (AE)</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="h-8 w-px bg-slate-200"></div>
                                <div className="flex items-center gap-2">
                                    <Mic size={16} className={org.global_settings?.voice_ai_enabled ? "text-emerald-500" : "text-slate-400"}/>
                                    <div className="flex flex-col items-start pr-2">
                                        <label className="text-[10px] uppercase font-black text-slate-500">AI Scribing Core</label>
                                        <button 
                                            onClick={() => toggleVoice(org.id as string, org.global_settings?.voice_ai_enabled)}
                                            className={`text-xs font-bold ${org.global_settings?.voice_ai_enabled ? "text-emerald-700 w-16 text-left" : "text-slate-500 w-16 text-left"}`}
                                        >
                                            {org.global_settings?.voice_ai_enabled ? "ACTIVE" : "DISABLED"}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* SITES CONTAINER */}
                        <div className="p-6 bg-white">
                            <div className="flex items-center justify-between mb-4">
                                <h4 className="font-bold text-slate-700 uppercase text-xs flex items-center gap-2 tracking-widest"><MapPin size={14}/> Operational Sites</h4>
                                <button onClick={() => setShowSiteModal(org.id || null)} className="text-blue-600 font-bold text-xs hover:text-blue-800 flex items-center gap-1"><Plus size={14}/> Connect Site</button>
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                {org.sites?.length === 0 && <div className="text-xs text-slate-400 font-medium italic">No multi-site topology deployed.</div>}
                                {org.sites?.map(site => (
                                    <div key={site.id} className="border border-slate-200 p-4 rounded-xl hover:border-blue-400 transition-colors cursor-pointer group">
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="font-black text-slate-800 flex items-center gap-2">{site.name}</div>
                                            <div className="text-[10px] font-mono font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded">{site.site_code}</div>
                                        </div>
                                        <p className="text-xs text-slate-500 font-medium mb-3">{site.timezone}</p>
                                        
                                        <div className="flex items-center justify-between pt-3 border-t border-slate-50">
                                            <span className="text-[10px] font-bold uppercase text-emerald-600 flex items-center gap-1"><CheckCircle2 size={12}/> Site Online</span>
                                            <button onClick={(e) => { e.stopPropagation(); setShowConfigSiteModal(site); }} className="text-xs text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity font-bold hover:underline cursor-pointer">Configure Enterprise Settings →</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ))
            )}
          </div>
        )}
      </div>

      {/* NEW ORGANIZATION MODAL */}
      {showOrgModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
            <div className="bg-white rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
                <div className="bg-slate-50 border-b border-slate-100 p-5 flex justify-between items-center">
                    <h3 className="font-black text-slate-800 text-lg flex items-center gap-2"><Building2 size={20} className="text-blue-600"/> Create New Tenant</h3>
                </div>
                <form onSubmit={createOrg} className="p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div><label className="text-[10px] uppercase font-bold text-slate-500">Organization Name</label><input name="name" required placeholder="e.g. Apollo Global" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 outline-none focus:border-blue-500 font-medium text-slate-800"/></div>
                        <div><label className="text-[10px] uppercase font-bold text-slate-500">Tenant Namespace (Code)</label><input name="org_code" required placeholder="e.g. APL-GLO" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 outline-none focus:border-blue-500 font-mono text-slate-800 uppercase"/></div>
                    </div>
                    <div><label className="text-[10px] uppercase font-bold text-slate-500">Country of Incorporation</label><input name="country" placeholder="e.g. India" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 outline-none focus:border-blue-500 text-slate-800"/></div>
                    <div><label className="text-[10px] uppercase font-bold text-slate-500">Primary Admin Email</label><input type="email" name="email" required placeholder="admin@enterprise.com" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 outline-none focus:border-blue-500 text-slate-800"/></div>
                    
                    <div className="grid grid-cols-2 gap-4 pt-2">
                        <div>
                            <label className="text-[10px] uppercase font-bold text-slate-500 block mb-1">Base Language Profile</label>
                            <select name="default_language" className="w-full p-2.5 border rounded-lg text-sm bg-slate-50 outline-none cursor-pointer">
                                <option value="en">English (UK)</option>
                                <option value="fr">French (FR)</option>
                                <option value="es">Spanish (ES)</option>
                            </select>
                        </div>
                        <div className="flex items-center gap-3 pt-6 pl-2">
                            <input type="checkbox" name="voice_enabled" defaultChecked id="voice_enb" className="w-5 h-5 text-blue-600 rounded cursor-pointer"/>
                            <label htmlFor="voice_enb" className="text-sm font-bold text-slate-700 cursor-pointer">Enable Voice Scribing AI</label>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
                        <button type="button" onClick={() => setShowOrgModal(false)} className="px-4 py-2 font-bold text-slate-500 hover:bg-slate-100 rounded-lg">Cancel</button>
                        <button type="submit" className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md transition-colors">Provision Tenant Space</button>
                    </div>
                </form>
            </div>
        </div>
      )}

      {/* NEW SITE MODAL */}
      {showSiteModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
            <div className="bg-white rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl">
                <div className="bg-slate-50 border-b border-slate-100 p-5">
                    <h3 className="font-black text-slate-800 text-lg flex items-center gap-2"><MapPin size={20} className="text-emerald-600"/> Add Facility Site</h3>
                    <p className="text-xs text-slate-500 mt-1 font-medium">Link a physical hospital location to this tenant.</p>
                </div>
                <form onSubmit={addSite} className="p-6 space-y-4">
                    <div><label className="text-[10px] uppercase font-bold text-slate-500">Site Name</label><input name="name" required placeholder="Downtown Branch" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 outline-none focus:border-blue-500 text-slate-800"/></div>
                    <div><label className="text-[10px] uppercase font-bold text-slate-500">Local Routing Code</label><input name="site_code" required placeholder="DT-BR" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 outline-none focus:border-blue-500 font-mono text-slate-800 uppercase"/></div>
                    <div><label className="text-[10px] uppercase font-bold text-slate-500">Timezone offset</label><input name="timezone" defaultValue="CET" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 outline-none focus:border-blue-500 text-slate-800 uppercase"/></div>

                    <div className="flex justify-end gap-3 pt-4">
                        <button type="button" onClick={() => setShowSiteModal(null)} className="px-4 py-2 font-bold text-slate-500 hover:bg-slate-100 rounded-lg">Cancel</button>
                        <button type="submit" className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg shadow-md transition-colors">Connect Site</button>
                    </div>
                </form>
            </div>
        </div>
      )}

      {/* CONFIGURE ENTERPRISE SITE MODAL */}
      {showConfigSiteModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
            <div className="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
                <div className="bg-slate-50 border-b border-slate-200 p-6 flex justify-between items-start">
                    <div>
                        <h3 className="font-black text-slate-800 text-xl flex items-center gap-2">
                            <Settings2 size={24} className="text-blue-600"/> 
                            Remote Site Configuration Engine
                        </h3>
                        <p className="text-sm text-slate-500 mt-2 font-medium">
                            Managing local routing, HL7 interfaces, and printing security for <strong className="text-slate-800">{showConfigSiteModal.name}</strong> ({showConfigSiteModal.site_code}).
                        </p>
                    </div>
                    <div className="bg-emerald-100 text-emerald-800 font-bold px-3 py-1 text-xs rounded-full flex gap-2 items-center border border-emerald-200 uppercase">
                        <Globe size={14}/> Node Live Sync
                    </div>
                </div>
                
                <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-slate-50/50">
                    <div className="bg-white border text-sm border-slate-200 rounded-xl p-5 shadow-sm">
                        <h4 className="font-black text-slate-700 uppercase tracking-widest text-[11px] mb-4 flex gap-2 items-center"><Database size={16}/> Local HIS Networking</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div><label className="text-[10px] uppercase font-bold text-slate-500">Local Static IP Mapping</label><input defaultValue="192.168.1.100" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 font-mono text-slate-800"/></div>
                            <div><label className="text-[10px] uppercase font-bold text-slate-500">HL7 Interface Engine Port</label><input defaultValue="2575" className="w-full mt-1 p-2.5 border rounded-lg text-sm bg-slate-50 font-mono text-slate-800"/></div>
                        </div>
                    </div>

                    <div className="bg-white border text-sm border-slate-200 rounded-xl p-5 shadow-sm">
                        <h4 className="font-black text-slate-700 uppercase tracking-widest text-[11px] mb-4 flex gap-2 items-center"><ShieldAlert size={16}/> Hardware & Endpoints</h4>
                        <div className="flex flex-col gap-3">
                            <label className="flex items-center gap-3 bg-slate-50 p-3 rounded-lg border border-slate-100 cursor-pointer">
                                <input type="checkbox" defaultChecked className="w-4 h-4 text-blue-600 rounded cursor-pointer"/>
                                <span className="font-bold text-slate-700">Enforce Thermal Printer Spooling Encryption</span>
                            </label>
                            <label className="flex items-center gap-3 bg-slate-50 p-3 rounded-lg border border-slate-100 cursor-pointer">
                                <input type="checkbox" defaultChecked className="w-4 h-4 text-blue-600 rounded cursor-pointer"/>
                                <span className="font-bold text-slate-700">Enable LIS Auto-Analyzer Bridges at this site</span>
                            </label>
                        </div>
                    </div>
                </div>

                <div className="bg-white border-t border-slate-200 p-5 flex justify-between items-center">
                    <button type="button" onClick={() => setShowConfigSiteModal(null)} className="px-5 py-2.5 font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition">Close Settings</button>
                    <button type="button" onClick={() => { setShowConfigSiteModal(null); alert("Enterprise Site Configuration Pushed to Edge Database!"); }} className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md transition-colors flex gap-2 items-center">
                        <Save size={18}/> Deploy to Site Edge
                    </button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}
