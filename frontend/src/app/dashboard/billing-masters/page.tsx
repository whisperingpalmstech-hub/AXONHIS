"use client";
import { useTranslation } from "@/i18n";


import React, { useEffect, useState, useCallback } from "react";
import { TopNav } from "@/components/ui/TopNav";
import {
  Receipt, DollarSign, Layers, Package, CreditCard, Percent, Building2,
  Shield, Plus, Search, Settings, ChevronDown, X, Check, Tag, Wallet,
  FileText, BarChart3, Coins, Heart, Zap
} from "lucide-react";
import { api } from "@/lib/api";

type Tab = "SERVICE_GROUPS" | "SERVICES" | "TARIFFS" | "PACKAGES" | "DEPOSITS" | "INSURANCE" | "CONFIG";

export default function BillingMastersDashboard() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<Tab>("SERVICE_GROUPS");
  const [loading, setLoading] = useState(false);

  // Data states
  const [serviceGroups, setServiceGroups] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [tariffPlans, setTariffPlans] = useState<any[]>([]);
  const [packages, setPackages] = useState<any[]>([]);
  const [patientCategories, setPatientCategories] = useState<any[]>([]);
  const [paymentModes, setPaymentModes] = useState<any[]>([]);
  const [taxGroups, setTaxGroups] = useState<any[]>([]);
  const [currencies, setCurrencies] = useState<any[]>([]);
  const [insuranceProviders, setInsuranceProviders] = useState<any[]>([]);
  const [corporateContracts, setCorporateContracts] = useState<any[]>([]);
  const [discountReasons, setDiscountReasons] = useState<any[]>([]);

  // Modals
  const [showServiceGroupModal, setShowServiceGroupModal] = useState(false);
  const [showServiceModal, setShowServiceModal] = useState(false);
  const [showTariffModal, setShowTariffModal] = useState(false);
  const [showPackageModal, setShowPackageModal] = useState(false);
  const [showInsuranceModal, setShowInsuranceModal] = useState(false);
  const [showCorporateModal, setShowCorporateModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [sg, sv, tp, pk, pc, pm, tg, cur, ip, cc, dr] = await Promise.all([
        api.get<any[]>("/billing-masters/service-groups").catch(() => []),
        api.get<any[]>("/billing-masters/services").catch(() => []),
        api.get<any[]>("/billing-masters/tariff-plans").catch(() => []),
        api.get<any[]>("/billing-masters/packages").catch(() => []),
        api.get<any[]>("/billing-masters/patient-categories").catch(() => []),
        api.get<any[]>("/billing-masters/payment-modes").catch(() => []),
        api.get<any[]>("/billing-masters/tax-groups").catch(() => []),
        api.get<any[]>("/billing-masters/currencies").catch(() => []),
        api.get<any[]>("/billing-masters/insurance-providers").catch(() => []),
        api.get<any[]>("/billing-masters/corporate-contracts").catch(() => []),
        api.get<any[]>("/billing-masters/discount-reasons").catch(() => []),
      ]);
      setServiceGroups(sg || []); setServices(sv || []); setTariffPlans(tp || []);
      setPackages(pk || []); setPatientCategories(pc || []); setPaymentModes(pm || []);
      setTaxGroups(tg || []); setCurrencies(cur || []); setInsuranceProviders(ip || []);
      setCorporateContracts(cc || []); setDiscountReasons(dr || []);
    } catch (err) { console.error(err); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSeed = async () => {
    try {
      await api.post("/billing-masters/seed", {});
      alert("Billing masters seeded! Refreshing...");
      fetchData();
    } catch { alert("Seed failed"); }
  };

  const handleCreateServiceGroup = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/billing-masters/service-groups", {
        code: fd.get("code"), name: fd.get("name"), description: fd.get("description"),
        display_order: parseInt(fd.get("display_order") as string || "0"),
        is_pharmacy: fd.get("is_pharmacy") === "on", is_lab: fd.get("is_lab") === "on",
        is_radiology: fd.get("is_radiology") === "on", is_procedure: fd.get("is_procedure") === "on",
        is_consultation: fd.get("is_consultation") === "on", is_bed_charge: fd.get("is_bed_charge") === "on",
      });
      setShowServiceGroupModal(false); fetchData();
    } catch { alert("Failed to create service group"); }
  };

  const handleCreateService = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/billing-masters/services", {
        service_group_id: fd.get("service_group_id"), code: fd.get("code"), name: fd.get("name"),
        base_price: parseFloat(fd.get("base_price") as string || "0"),
        is_variable_pricing: fd.get("is_variable_pricing") === "on",
        is_stat_applicable: fd.get("is_stat_applicable") === "on",
        stat_percentage: parseFloat(fd.get("stat_percentage") as string || "0"),
        department: fd.get("department"),
      });
      setShowServiceModal(false); fetchData();
    } catch { alert("Failed to create service"); }
  };

  const handleCreateInsurance = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/billing-masters/insurance-providers", {
        code: fd.get("code"), name: fd.get("name"), tpa_name: fd.get("tpa_name"),
        contact_person: fd.get("contact_person"), phone: fd.get("phone"), email: fd.get("email"),
        payment_terms_days: parseInt(fd.get("payment_terms_days") as string || "30"),
      });
      setShowInsuranceModal(false); fetchData();
    } catch { alert("Failed"); }
  };

  const handleCreateCorporate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/billing-masters/corporate-contracts", {
        code: fd.get("code"), company_name: fd.get("company_name"),
        contact_person: fd.get("contact_person"), phone: fd.get("phone"), email: fd.get("email"),
        credit_limit: parseFloat(fd.get("credit_limit") as string || "0"),
        payment_terms_days: parseInt(fd.get("payment_terms_days") as string || "30"),
      });
      setShowCorporateModal(false); fetchData();
    } catch { alert("Failed"); }
  };

  const handleCreateTariffPlan = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/billing-masters/tariff-plans", {
        code: fd.get("code"), name: fd.get("name"), description: fd.get("description"),
        bed_category: fd.get("bed_category") || null,
        is_default: fd.get("is_default") === "on",
      });
      setShowTariffModal(false); fetchData();
    } catch { alert("Failed to create tariff plan"); }
  };

  const handleCreatePackage = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.post("/billing-masters/packages", {
        code: fd.get("code"), name: fd.get("name"), 
        package_type: fd.get("package_type"),
        package_amount: parseFloat(fd.get("package_amount") as string || "0"),
        bed_category: fd.get("bed_category") || null,
        included_stay_days: fd.get("included_stay_days") ? parseInt(fd.get("included_stay_days") as string) : null,
      });
      setShowPackageModal(false); fetchData();
    } catch { alert("Failed to create package"); }
  };

  const getGroupIcon = (g: any) => {
    if (g.is_pharmacy) return <Coins size={16} className="text-emerald-500"/>;
    if (g.is_lab) return <BarChart3 size={16} className="text-blue-500"/>;
    if (g.is_radiology) return <Zap size={16} className="text-purple-500"/>;
    if (g.is_consultation) return <Heart size={16} className="text-rose-500"/>;
    if (g.is_bed_charge) return <Building2 size={16} className="text-amber-500"/>;
    if (g.is_procedure) return <FileText size={16} className="text-indigo-500"/>;
    return <Tag size={16} className="text-slate-400"/>;
  };

  const filteredServices = services.filter(s =>
    `${s.name} ${s.code}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <TopNav title={t("billingMasters.title")} />
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
              <Receipt className="text-emerald-500" size={32}/> Billing Configuration
            </h1>
            <p className="text-slate-500 font-medium mt-1">Service Masters • Tariffs • Packages • Insurance • Tax Configuration</p>
          </div>
          <div className="flex gap-3">
            <button onClick={handleSeed} className="flex items-center gap-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 px-4 py-2.5 rounded-xl font-bold transition-all text-sm border border-emerald-200">
              <Zap size={16}/> Seed Defaults
            </button>
            <button onClick={() => {
              if (activeTab === "SERVICE_GROUPS") setShowServiceGroupModal(true);
              else if (activeTab === "SERVICES") setShowServiceModal(true);
              else if (activeTab === "INSURANCE") setShowInsuranceModal(true);
              else if (activeTab === "TARIFFS") setShowTariffModal(true);
              else if (activeTab === "PACKAGES") setShowPackageModal(true);
            }} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-xl font-bold transition-all shadow-md shadow-emerald-200">
              <Plus size={18}/> Add New
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-6 gap-3 mb-6">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase">Groups</div>
            <div className="text-2xl font-black text-slate-800">{serviceGroups.length}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase">Services</div>
            <div className="text-2xl font-black text-blue-600">{services.length}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase">Tariff Plans</div>
            <div className="text-2xl font-black text-purple-600">{tariffPlans.length}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase">Packages</div>
            <div className="text-2xl font-black text-amber-600">{packages.length}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase">Insurers</div>
            <div className="text-2xl font-black text-rose-600">{insuranceProviders.length}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-[10px] font-bold text-slate-500 uppercase">Corporates</div>
            <div className="text-2xl font-black text-emerald-600">{corporateContracts.length}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1.5 p-1.5 bg-white/50 backdrop-blur border border-slate-200 rounded-2xl w-fit mb-6 shadow-sm overflow-x-auto">
          {[
            { id: "SERVICE_GROUPS", label: "Service Groups", icon: <Layers size={14}/> },
            { id: "SERVICES", label: "Service Master", icon: <Receipt size={14}/> },
            { id: "TARIFFS", label: "Tariff Plans", icon: <DollarSign size={14}/> },
            { id: "PACKAGES", label: "Packages", icon: <Package size={14}/> },
            { id: "INSURANCE", label: "Insurance & Corp", icon: <Shield size={14}/> },
            { id: "CONFIG", label: "Tax / Payment / Discount", icon: <Settings size={14}/> },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id as Tab)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === t.id ? "bg-white text-emerald-700 shadow-sm border border-slate-200/50" : "text-slate-500 hover:text-slate-700"
              }`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-400 font-medium">Loading billing configuration...</div>
        ) : (
          <div>
            {/* SERVICE GROUPS */}
            {activeTab === "SERVICE_GROUPS" && (
              <div className="grid grid-cols-3 gap-4">
                {serviceGroups.length === 0 ? (
                  <div className="col-span-3 p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400">
                    <Layers size={32} className="mx-auto mb-2 opacity-50"/>
                    <p className="font-medium">No service groups. Click "Seed Defaults" to populate.</p>
                  </div>
                ) : serviceGroups.map(g => (
                  <div key={g.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2">
                        {getGroupIcon(g)}
                        <div>
                          <div className="font-black text-slate-800 text-sm">{g.name}</div>
                          <div className="text-[10px] text-slate-400 font-mono">{g.code}</div>
                        </div>
                      </div>
                      <span className={`text-[10px] font-black px-2 py-0.5 rounded-md ${g.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                        {g.is_active ? 'ACTIVE' : 'INACTIVE'}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {g.is_pharmacy && <span className="text-[9px] bg-emerald-50 text-emerald-600 px-1.5 py-0.5 rounded font-bold">PHARMA</span>}
                      {g.is_lab && <span className="text-[9px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded font-bold">LAB</span>}
                      {g.is_radiology && <span className="text-[9px] bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded font-bold">RADIOLOGY</span>}
                      {g.is_consultation && <span className="text-[9px] bg-rose-50 text-rose-600 px-1.5 py-0.5 rounded font-bold">CONSULT</span>}
                      {g.is_bed_charge && <span className="text-[9px] bg-amber-50 text-amber-600 px-1.5 py-0.5 rounded font-bold">BED</span>}
                      {g.is_procedure && <span className="text-[9px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded font-bold">PROCEDURE</span>}
                      {g.is_nursing && <span className="text-[9px] bg-pink-50 text-pink-600 px-1.5 py-0.5 rounded font-bold">NURSING</span>}
                      {g.is_ot && <span className="text-[9px] bg-orange-50 text-orange-600 px-1.5 py-0.5 rounded font-bold">OT</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* SERVICES */}
            {activeTab === "SERVICES" && (
              <div>
                <div className="mb-4 relative">
                  <Search size={16} className="absolute left-3 top-3 text-slate-400"/>
                  <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="Search services..."
                    className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:border-emerald-400 outline-none"/>
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                        <th className="p-3 font-bold">Code</th><th className="p-3 font-bold">Service Name</th>
                        <th className="p-3 font-bold">Base Price</th><th className="p-3 font-bold">Variable</th>
                        <th className="p-3 font-bold">STAT</th><th className="p-3 font-bold">Dept</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredServices.length === 0 ? (
                        <tr><td colSpan={6} className="p-8 text-center text-slate-400 font-medium">No services configured</td></tr>
                      ) : filteredServices.map(s => (
                        <tr key={s.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="p-3 font-mono text-xs font-bold text-slate-600">{s.code}</td>
                          <td className="p-3 text-sm font-bold text-slate-800">{s.name}</td>
                          <td className="p-3 text-sm font-bold text-emerald-700">₹{parseFloat(s.base_price).toLocaleString()}</td>
                          <td className="p-3">{s.is_variable_pricing ? <Check size={14} className="text-emerald-500"/> : <X size={14} className="text-slate-300"/>}</td>
                          <td className="p-3">{s.is_stat_applicable ? <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-bold">{s.stat_percentage}%</span> : <span className="text-slate-300 text-xs">—</span>}</td>
                          <td className="p-3 text-xs text-slate-500">{s.department || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TARIFF PLANS */}
            {activeTab === "TARIFFS" && (
              <div className="grid grid-cols-2 gap-4">
                {tariffPlans.length === 0 ? (
                  <div className="col-span-2 p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400">
                    <DollarSign size={32} className="mx-auto mb-2 opacity-50"/>
                    <p className="font-medium">No tariff plans configured yet.</p>
                  </div>
                ) : tariffPlans.map(tp => (
                  <div key={tp.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-black text-slate-800">{tp.name}</div>
                        <div className="text-xs text-slate-400 font-mono">{tp.code}</div>
                      </div>
                      {tp.is_default && <span className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-md font-bold">DEFAULT</span>}
                    </div>
                    <div className="text-xs text-slate-500 mt-2">{tp.description || 'No description'}</div>
                    {tp.bed_category && <div className="text-xs text-amber-600 font-bold mt-1">Bed: {tp.bed_category}</div>}
                  </div>
                ))}
              </div>
            )}

            {/* PACKAGES */}
            {activeTab === "PACKAGES" && (
              <div className="grid grid-cols-3 gap-4">
                {packages.length === 0 ? (
                  <div className="col-span-3 p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400">
                    <Package size={32} className="mx-auto mb-2 opacity-50"/>
                    <p className="font-medium">No packages. Create OPD/IPD/Daycare packages to get started.</p>
                  </div>
                ) : packages.map(p => (
                  <div key={p.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-black text-slate-800">{p.name}</div>
                        <div className="text-xs text-slate-400 font-mono">{p.code}</div>
                      </div>
                      <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md ${
                        p.package_type === 'ipd' ? 'bg-blue-100 text-blue-700' :
                        p.package_type === 'opd' ? 'bg-emerald-100 text-emerald-700' :
                        'bg-amber-100 text-amber-700'
                      }`}>{p.package_type}</span>
                    </div>
                    <div className="text-2xl font-black text-emerald-700 mt-2">₹{parseFloat(p.package_amount).toLocaleString()}</div>
                    {p.bed_category && <div className="text-xs text-slate-500 mt-1">Bed: {p.bed_category}</div>}
                    {p.included_stay_days && <div className="text-xs text-slate-500">Stay: {p.included_stay_days} days</div>}
                  </div>
                ))}
              </div>
            )}

            {/* INSURANCE & CORPORATE */}
            {activeTab === "INSURANCE" && (
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider">Insurance Providers</h3>
                    <button onClick={() => setShowInsuranceModal(true)} className="text-xs font-bold bg-rose-50 text-rose-700 px-3 py-1.5 rounded-lg hover:bg-rose-100"><Plus size={12} className="inline mr-1"/>Add Insurer</button>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    {insuranceProviders.map(ip => (
                      <div key={ip.id} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                        <div className="font-bold text-slate-800 text-sm">{ip.name}</div>
                        <div className="text-xs text-slate-400 font-mono mb-2">{ip.code}</div>
                        {ip.tpa_name && <div className="text-xs text-slate-500">TPA: {ip.tpa_name}</div>}
                        <div className="text-xs text-slate-500">Payment Terms: {ip.payment_terms_days} days</div>
                      </div>
                    ))}
                    {insuranceProviders.length === 0 && <div className="col-span-3 text-center text-slate-400 p-8 border-2 border-dashed rounded-2xl">No insurance providers</div>}
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider">Corporate Contracts</h3>
                    <button onClick={() => setShowCorporateModal(true)} className="text-xs font-bold bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-100"><Plus size={12} className="inline mr-1"/>Add Corporate</button>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    {corporateContracts.map(cc => (
                      <div key={cc.id} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                        <div className="font-bold text-slate-800 text-sm">{cc.company_name}</div>
                        <div className="text-xs text-slate-400 font-mono mb-2">{cc.code}</div>
                        {cc.credit_limit && <div className="text-xs text-emerald-600 font-bold">Limit: ₹{parseFloat(cc.credit_limit).toLocaleString()}</div>}
                        <div className="text-xs text-slate-500">Terms: {cc.payment_terms_days} days</div>
                      </div>
                    ))}
                    {corporateContracts.length === 0 && <div className="col-span-3 text-center text-slate-400 p-8 border-2 border-dashed rounded-2xl">No corporate contracts</div>}
                  </div>
                </div>
              </div>
            )}

            {/* CONFIG TAB */}
            {activeTab === "CONFIG" && (
              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-6">
                  {/* Patient Categories */}
                  <div>
                    <h3 className="text-xs font-black text-slate-600 uppercase mb-3">Patient Categories</h3>
                    <div className="space-y-2">
                      {patientCategories.map(c => (
                        <div key={c.id} className="bg-white p-3 rounded-xl border border-slate-200 flex justify-between items-center">
                          <div><span className="text-sm font-bold text-slate-700">{c.name}</span><span className="text-[10px] text-slate-400 ml-2 font-mono">{c.code}</span></div>
                          {c.is_default && <span className="text-[9px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded font-bold">DEFAULT</span>}
                        </div>
                      ))}
                      {patientCategories.length === 0 && <div className="text-xs text-slate-400 text-center p-4 border border-dashed rounded-xl">No categories. Seed defaults to populate.</div>}
                    </div>
                  </div>
                  {/* Payment Modes */}
                  <div>
                    <h3 className="text-xs font-black text-slate-600 uppercase mb-3">Payment Modes</h3>
                    <div className="space-y-2">
                      {paymentModes.map(m => (
                        <div key={m.id} className="bg-white p-3 rounded-xl border border-slate-200 flex justify-between items-center">
                          <div><Wallet size={14} className="inline mr-2 text-slate-400"/><span className="text-sm font-bold text-slate-700">{m.name}</span></div>
                          <div className="flex gap-1">
                            {m.requires_reference && <span className="text-[9px] bg-amber-50 text-amber-600 px-1 py-0.5 rounded font-bold">REF</span>}
                            {m.requires_bank_details && <span className="text-[9px] bg-blue-50 text-blue-600 px-1 py-0.5 rounded font-bold">BANK</span>}
                          </div>
                        </div>
                      ))}
                      {paymentModes.length === 0 && <div className="text-xs text-slate-400 text-center p-4 border border-dashed rounded-xl">No payment modes</div>}
                    </div>
                  </div>
                  {/* Tax Groups */}
                  <div>
                    <h3 className="text-xs font-black text-slate-600 uppercase mb-3">Tax Groups (GST)</h3>
                    <div className="space-y-2">
                      {taxGroups.map(t => (
                        <div key={t.id} className="bg-white p-3 rounded-xl border border-slate-200">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-bold text-slate-700">{t.name}</span>
                            <span className="text-sm font-black text-emerald-700">{t.total_percentage}%</span>
                          </div>
                          <div className="text-[10px] text-slate-400 mt-1">CGST: {t.cgst_percentage}% | SGST: {t.sgst_percentage}% | IGST: {t.igst_percentage}%</div>
                        </div>
                      ))}
                      {taxGroups.length === 0 && <div className="text-xs text-slate-400 text-center p-4 border border-dashed rounded-xl">No tax groups</div>}
                    </div>
                  </div>
                </div>
                {/* Discount Reasons */}
                <div>
                  <h3 className="text-xs font-black text-slate-600 uppercase mb-3">Discount Reasons</h3>
                  <div className="flex flex-wrap gap-2">
                    {discountReasons.map(r => (
                      <span key={r.id} className="bg-white px-3 py-1.5 rounded-lg border border-slate-200 text-sm font-medium text-slate-700">
                        <Percent size={12} className="inline mr-1 text-slate-400"/>{r.name}
                      </span>
                    ))}
                    {discountReasons.length === 0 && <span className="text-xs text-slate-400">No discount reasons configured</span>}
                  </div>
                </div>
                {/* Currencies */}
                <div>
                  <h3 className="text-xs font-black text-slate-600 uppercase mb-3">Currencies</h3>
                  <div className="flex gap-3">
                    {currencies.map(c => (
                      <div key={c.id} className="bg-white p-3 rounded-xl border border-slate-200 min-w-[120px]">
                        <div className="text-lg font-black text-slate-800">{c.symbol}</div>
                        <div className="text-xs font-bold text-slate-600">{c.name} ({c.code})</div>
                        {c.is_default && <span className="text-[9px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-bold">DEFAULT</span>}
                      </div>
                    ))}
                    {currencies.length === 0 && <span className="text-xs text-slate-400">No currencies</span>}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* MODALS */}
      {showServiceGroupModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateServiceGroup} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Layers size={20} className="text-emerald-500"/> New Service Group</h3>
              <button type="button" onClick={() => setShowServiceGroupModal(false)}><X size={20} className="text-slate-400"/></button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Code *</label><input name="code" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-emerald-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Name *</label><input name="name" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-emerald-400"/></div>
            </div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">Description</label><input name="description" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-emerald-400"/></div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">Display Order</label><input name="display_order" type="number" defaultValue="0" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-emerald-400"/></div>
            <div className="flex flex-wrap gap-3">
              {["is_pharmacy","is_lab","is_radiology","is_procedure","is_consultation","is_bed_charge"].map(f => (
                <label key={f} className="flex items-center gap-1.5 text-xs font-bold text-slate-600"><input type="checkbox" name={f} className="rounded"/>{f.replace('is_','').replace('_',' ')}</label>
              ))}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowServiceGroupModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">Create</button>
            </div>
          </form>
        </div>
      )}

      {showServiceModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateService} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Receipt size={20} className="text-blue-500"/> New Service</h3>
              <button type="button" onClick={() => setShowServiceModal(false)}><X size={20} className="text-slate-400"/></button>
            </div>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">Service Group *</label>
              <select name="service_group_id" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-400">
                <option value="">— Select —</option>
                {serviceGroups.map(g => <option key={g.id} value={g.id}>{g.name} ({g.code})</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Code *</label><input name="code" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Name *</label><input name="name" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Base Price (₹) *</label><input name="base_price" type="number" step="0.01" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">STAT Surcharge %</label><input name="stat_percentage" type="number" step="0.1" defaultValue="0" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-400"/></div>
            </div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">Department</label><input name="department" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-blue-400"/></div>
            <div className="flex gap-4">
              <label className="flex items-center gap-1.5 text-xs font-bold text-slate-600"><input type="checkbox" name="is_variable_pricing" className="rounded"/>Variable Pricing</label>
              <label className="flex items-center gap-1.5 text-xs font-bold text-slate-600"><input type="checkbox" name="is_stat_applicable" className="rounded"/>STAT Applicable</label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowServiceModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">Create Service</button>
            </div>
          </form>
        </div>
      )}

      {showInsuranceModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateInsurance} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Shield size={20} className="text-rose-500"/> New Insurance Provider</h3>
              <button type="button" onClick={() => setShowInsuranceModal(false)}><X size={20} className="text-slate-400"/></button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Code *</label><input name="code" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Name *</label><input name="name" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">TPA Name</label><input name="tpa_name" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Contact Person</label><input name="contact_person" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Phone</label><input name="phone" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Email</label><input name="email" type="email" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Payment Terms (days)</label><input name="payment_terms_days" type="number" defaultValue="30" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400"/></div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowInsuranceModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button type="submit" className="bg-rose-600 hover:bg-rose-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">Add Provider</button>
            </div>
          </form>
        </div>
      )}

      {showCorporateModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateCorporate} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Building2 size={20} className="text-indigo-500"/> New Corporate Contract</h3>
              <button type="button" onClick={() => setShowCorporateModal(false)}><X size={20} className="text-slate-400"/></button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Code *</label><input name="code" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-indigo-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Company Name *</label><input name="company_name" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-indigo-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Contact Person</label><input name="contact_person" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-indigo-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Phone</label><input name="phone" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-indigo-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Email</label><input name="email" type="email" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-indigo-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Credit Limit (₹)</label><input name="credit_limit" type="number" step="0.01" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-indigo-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Payment Terms (days)</label><input name="payment_terms_days" type="number" defaultValue="30" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-indigo-400"/></div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowCorporateModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">Add Corporate</button>
            </div>
          </form>
        </div>
      )}

      {showTariffModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreateTariffPlan} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><DollarSign size={20} className="text-purple-500"/> New Tariff Plan</h3>
              <button type="button" onClick={() => setShowTariffModal(false)}><X size={20} className="text-slate-400"/></button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Code *</label><input name="code" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Name *</label><input name="name" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400"/></div>
            </div>
            <div><label className="text-[10px] font-bold text-slate-500 uppercase">Description</label><input name="description" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400"/></div>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">Bed Category (Optional)</label>
              <select name="bed_category" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-purple-400 text-slate-700">
                <option value="">Any</option>
                <option value="General Ward">General Ward</option>
                <option value="Semi-Private">Semi-Private</option>
                <option value="Private">Private</option>
                <option value="ICU">ICU</option>
              </select>
            </div>
            <label className="flex items-center gap-1.5 text-xs font-bold text-slate-600"><input type="checkbox" name="is_default" className="rounded"/>Set as Default Tariff</label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowTariffModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button type="submit" className="bg-purple-600 hover:bg-purple-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">Create Tariff</button>
            </div>
          </form>
        </div>
      )}

      {showPackageModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleCreatePackage} className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Package size={20} className="text-amber-500"/> New Package</h3>
              <button type="button" onClick={() => setShowPackageModal(false)}><X size={20} className="text-slate-400"/></button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Code *</label><input name="code" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Name *</label><input name="name" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Package Type *</label>
                <select name="package_type" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-amber-400 text-slate-700">
                  <option value="opd">OPD / Health Checkup</option>
                  <option value="ipd">IPD / Admission</option>
                  <option value="daycare">Daycare</option>
                </select>
              </div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Total Amount (₹) *</label><input name="package_amount" type="number" step="0.01" required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Bed Category (IPD)</label>
                <select name="bed_category" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-amber-400 text-slate-700">
                  <option value="">Not Applicable</option>
                  <option value="General Ward">General Ward</option>
                  <option value="Semi-Private">Semi-Private</option>
                  <option value="Private">Private</option>
                  <option value="ICU">ICU</option>
                </select>
              </div>
              <div><label className="text-[10px] font-bold text-slate-500 uppercase">Stay Days Included</label><input name="included_stay_days" type="number" className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-amber-400"/></div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowPackageModal(false)} className="px-4 py-2 text-slate-600 text-sm font-bold">Cancel</button>
              <button type="submit" className="bg-amber-600 hover:bg-amber-700 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors">Create Package</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
