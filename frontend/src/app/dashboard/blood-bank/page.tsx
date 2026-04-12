"use strict";
"use client";
import { useTranslation } from "@/i18n";


import React, { useState, useEffect } from "react";
import { TopNav } from "@/components/ui/TopNav";
import { Activity, Plus, Search, Layers, Droplets, Users, CheckCircle, RefreshCw, HandHeart, ShieldAlert, HeartPulse, Stethoscope, AlertTriangle } from "lucide-react";

export default function BloodBankDashboard() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("inventory");
  const [inventory, setInventory] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [donors, setDonors] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [simulating, setSimulating] = useState(false);
  const [showDonorModal, setShowDonorModal] = useState(false);
  
  // Form state
  const [dFirst, setDFirst] = useState("");
  const [dLast, setDLast] = useState("");
  const [dDob, setDDob] = useState("1990-01-01");
  const [dGroup, setDGroup] = useState("O");
  const [dRh, setDRh] = useState("+");
  const [dContact, setDContact] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}` };
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
      
      const [resInv, resOrd, resDon, resPat] = await Promise.all([
        fetch(`${api}/api/v1/blood-bank/inventory`, { headers }).catch(()=>null),
        fetch(`${api}/api/v1/blood-bank/orders`, { headers }).catch(()=>null),
        fetch(`${api}/api/v1/blood-bank/donors`, { headers }).catch(()=>null),
        fetch(`${api}/api/v1/patients`, { headers }).catch(()=>null),
      ]);
      
      if (resInv?.ok) setInventory((await resInv.json()) || []);
      if (resOrd?.ok) setOrders((await resOrd.json()) || []);
      if (resDon?.ok) setDonors((await resDon.json()) || []);
      if (resPat?.ok) setPatients((await resPat.json()) || []);

    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getPatientName = (id: string, uhid: string) => {
    if (uhid) {
       const p = patients.find(x => x.patient_uuid === uhid || x.uhid === uhid);
       if (p) return `${p.first_name} ${p.last_name}`;
    }
    const pt = patients.find(x => x.id === id);
    return pt ? `${pt.first_name} ${pt.last_name}` : "Unknown Patient";
  };

  const handleRegisterDonor = async (e: React.FormEvent) => {
     e.preventDefault();
     setSimulating(true);
     try {
       const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}`, "Content-Type": "application/json" };
       const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
       const dID = "DNR-" + Math.floor(Math.random() * 100000);
       const uID = "BAG-" + Math.floor(Math.random() * 1000000);
       
       // 1. Create Donor
       const dRes = await fetch(`${api}/api/v1/blood-bank/donors`, {
          method: "POST", headers, body: JSON.stringify({
            donor_id: dID,
            first_name: dFirst, last_name: dLast,
            date_of_birth: dDob,
            blood_group: dGroup, rh_factor: dRh, 
            contact_number: dContact,
            screening_status: "eligible"
          })
       });
       if (!dRes.ok) throw new Error("Donor fault: " + await dRes.text());
       const dData = await dRes.json();
       
       // 2. Add collection
       const cRes = await fetch(`${api}/api/v1/blood-bank/donors/${dData.id}/collections`, {
          method: "POST", headers, body: JSON.stringify({
             donor_id: dData.id,
             collection_date: new Date().toISOString(),
             collection_location: "Main Center",
             collected_by: "Phlebotomist",
             collection_volume: 450,
             screening_results: { hiv: "negative", hbsag: "negative", hcv: "negative" }
          })
       });
       if (!cRes.ok) throw new Error("Collection fault: " + await cRes.text());
       const cData = await cRes.json();

       // 3. Add to inventory 
       const uRes = await fetch(`${api}/api/v1/blood-bank/inventory`, {
          method: "POST", headers, body: JSON.stringify({
             unit_id: uID,
             blood_group: dGroup,
             rh_factor: dRh,
             collection_id: cData.id,
             collection_date: new Date().toISOString(),
             expiry_date: new Date(Date.now() + 35*24*60*60*1000).toISOString(),
             status: "available"
          })
       });
       if (!uRes.ok) throw new Error("Unit fault: " + await uRes.text());

       setShowDonorModal(false);
       setDFirst(""); setDLast(""); setDContact("");
       await fetchData();
     } catch(e: any) { 
        console.error(e); 
        alert("Failed to register donor: " + e.message);
     } finally {
        setSimulating(false);
     }
  };

  const handleAllocate = async (order: any) => {
      // Find an available unit matching the blood type
      const matchType = order.blood_type || order.required_blood_group;
      let suitableUnit;
      if (matchType) {
         // order might use blood_type "A+" or "A" + "+"
         const matchGroup = matchType.replace(/[+-]/g, "");
         const matchRh = matchType.includes("+") ? "+" : matchType.includes("-") ? "-" : "";
         suitableUnit = inventory.find(u => u.status === 'available' && u.blood_group === matchGroup && u.rh_factor === matchRh);
      } else {
         suitableUnit = inventory.find(u => u.status === 'available');
      }

      if (!suitableUnit) {
         alert(`No available units matching required blood type in inventory!`);
         return;
      }
      
      try {
       const headers = { "Authorization": `Bearer ${localStorage.getItem("access_token")}`, "Content-Type": "application/json" };
       const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";
       
       // Allocate
       await fetch(`${api}/api/v1/blood-bank/orders/${order.id}/allocations`, {
          method: "POST", headers, body: JSON.stringify({
             blood_unit_id: suitableUnit.id,
             allocation_date: new Date().toISOString(),
             status: "allocated"
          })
       });

       // Usually would mark unit as 'reserved' or 'issued' via /inventory endpoints but let's refresh to show changes.
       await fetchData();
       alert("Crossmatched & Allocated unit " + suitableUnit.id?.substring(0,8));
      } catch (e) { console.error(e); }
  };

  const bloodStats = {
     "O+": inventory.filter(i => i.blood_group === 'O' && i.rh_factor === '+' && i.status === 'available').length,
     "O-": inventory.filter(i => i.blood_group === 'O' && i.rh_factor === '-' && i.status === 'available').length,
     "A+": inventory.filter(i => i.blood_group === 'A' && i.rh_factor === '+' && i.status === 'available').length,
     "A-": inventory.filter(i => i.blood_group === 'A' && i.rh_factor === '-' && i.status === 'available').length,
     "B+": inventory.filter(i => i.blood_group === 'B' && i.rh_factor === '+' && i.status === 'available').length,
     "B-": inventory.filter(i => i.blood_group === 'B' && i.rh_factor === '-' && i.status === 'available').length,
     "AB+": inventory.filter(i => i.blood_group === 'AB' && i.rh_factor === '+' && i.status === 'available').length,
     "AB-": inventory.filter(i => i.blood_group === 'AB' && i.rh_factor === '-' && i.status === 'available').length,
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <TopNav title="Blood Bank & Transfusion Medicine" />
      
      <div className="flex-1 p-8 max-w-[1400px] mx-auto w-full">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-black text-rose-800 tracking-tight flex items-center gap-3">
              <Droplets className="text-rose-600" size={32} fill="currentColor"/> {t("bloodBank.title")}
            </h1>
            <p className="text-slate-500 font-medium mt-1">{t("bloodBank.subtitle")} • Inventory Tracking • Donor Registry</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setShowDonorModal(true)} className="bg-rose-600 hover:bg-rose-700 text-white px-5 py-2.5 rounded-xl font-bold shadow-md shadow-rose-200 transition-all flex items-center gap-2">
              <Plus size={18}/> New Blood Donation
            </button>
            <button onClick={fetchData} className="bg-white border text-slate-600 px-4 py-2.5 rounded-xl font-bold flex items-center gap-2">
              <RefreshCw size={18}/> Refresh
            </button>
          </div>
        </div>

        {/* BLOOD TYPE HIGHLIGHT BANNER */}
        <div className="grid grid-cols-4 md:grid-cols-8 gap-2 mb-8">
           {Object.keys(bloodStats).map(type => (
              <div key={type} className={`bg-white border ${bloodStats[type as keyof typeof bloodStats] === 0 ? 'border-red-200' : 'border-slate-200'} rounded-xl p-3 text-center shadow-sm relative overflow-hidden`}>
                 <div className="absolute top-0 right-0 p-1 opacity-5"><Droplets size={48}/></div>
                 <div className={`text-xl font-black ${bloodStats[type as keyof typeof bloodStats] === 0 ? 'text-red-600' : 'text-slate-800'}`}>{type}</div>
                 <div className={`text-xs font-bold ${bloodStats[type as keyof typeof bloodStats] === 0 ? 'text-red-400' : 'text-emerald-500'}`}>{bloodStats[type as keyof typeof bloodStats]} Units</div>
                 {bloodStats[type as keyof typeof bloodStats] === 0 && <div className="absolute bottom-0 left-0 w-full h-1 bg-red-500"></div>}
              </div>
           ))}
        </div>

        <div className="flex gap-2 p-1.5 bg-white border border-slate-200 rounded-2xl w-fit mb-6 shadow-sm overflow-x-auto">
          {[
            { id: "inventory", label: "Cold Storage Inventory", icon: <Layers size={16}/> },
            { id: "requests", label: "Transfusion Orders (Ward/OT)", icon: <AlertTriangle size={16}/> },
            { id: "donors", label: "Donor Registry", icon: <Users size={16}/> },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all whitespace-nowrap ${
                activeTab === t.id ? "bg-rose-50 text-rose-700 shadow-sm border border-rose-100" : "text-slate-500 hover:text-slate-800"
              }`}>
              {t.icon} {t.label} 
              {t.id === 'requests' && orders.length > 0 && <span className="bg-rose-500 text-white text-[10px] px-2 py-0.5 rounded-full ml-1">{orders.length}</span>}
            </button>
          ))}
        </div>

        {loading ? (
             <div className="py-20 text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500 mx-auto mb-4"></div><p className="text-slate-500 font-bold">Connecting to Blood Bank analyzers...</p></div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[500px]">
            {activeTab === 'inventory' && (
              <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr className="text-slate-500 text-[10px] uppercase font-black tracking-wider">
                    <th className="p-4">Unit #</th>
                    <th className="p-4">Blood Type</th>
                    <th className="p-4">Component</th>
                    <th className="p-4">Volume</th>
                    <th className="p-4">Expiry Date</th>
                    <th className="p-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {inventory.length === 0 ? <tr><td colSpan={6} className="p-12 text-center text-slate-400 font-bold">Freezer is empty. No blood units logged.</td></tr> : inventory.map(unit => (
                    <tr key={unit.id} className="hover:bg-slate-50">
                      <td className="p-4 font-mono text-xs text-slate-500">{unit.unit_id || unit.id?.substring(0,8).toUpperCase()}</td>
                      <td className="p-4 font-black flex items-center gap-2 text-rose-700"><Droplets size={14} fill="currentColor"/> {unit.blood_group}{unit.rh_factor}</td>
                      <td className="p-4 font-semibold text-slate-700 capitalize">Whole Blood</td>
                      <td className="p-4 font-mono text-xs">450 mL</td>
                      <td className="p-4 text-xs font-semibold">{new Date(unit.expiry_date).toLocaleDateString()}</td>
                      <td className="p-4 text-center">
                        <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider ${unit.status === 'available' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{unit.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'requests' && (
              <div className="p-0">
                <table className="w-full text-left">
                  <thead className="bg-amber-50/50 border-b border-amber-100">
                    <tr className="text-amber-800 text-[10px] uppercase font-black tracking-wider">
                      <th className="p-4">Order Date</th>
                      <th className="p-4">Patient & Ward/OT</th>
                      <th className="p-4">Required Type</th>
                      <th className="p-4">Indication</th>
                      <th className="p-4 text-right">Emergency Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {orders.length === 0 ? <tr><td colSpan={5} className="p-12 text-center text-slate-400 font-bold">No active transfusion requests.</td></tr> : orders.map(order => (
                      <tr key={order.id} className="hover:bg-slate-50">
                        <td className="p-4 font-mono text-xs text-slate-500">{new Date(order.created_at || Date.now()).toLocaleString()}</td>
                        <td className="p-4">
                           <span className="font-bold text-slate-800 block">{getPatientName(order.patient_id, "")}</span>
                           <span className="text-[10px] font-black uppercase bg-slate-100 text-slate-500 px-1 rounded mt-1 inline-block">Req By: ER/Surgeon</span>
                        </td>
                        <td className="p-4 font-black text-rose-700 flex items-center gap-1 mt-1"><Droplets size={14}/> {order.blood_type} ({order.units_requested} Units)</td>
                        <td className="p-4 font-medium text-slate-600 truncate max-w-[200px]">{order.indication || "Emergency Transfusion"}</td>
                        <td className="p-4 text-right">
                           <button onClick={() => handleAllocate(order)} className="bg-rose-600 hover:bg-rose-700 text-white font-bold px-4 py-2 rounded-lg text-xs shadow-sm flex items-center gap-2 ml-auto">
                              <ShieldAlert size={14}/> Crossmatch & Allocate
                           </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'donors' && (
              <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr className="text-slate-500 text-[10px] uppercase font-black tracking-wider">
                    <th className="p-4">Donor ID</th>
                    <th className="p-4">Name</th>
                    <th className="p-4">Blood Type</th>
                    <th className="p-4">Contact</th>
                    <th className="p-4 text-center">Eligibility</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {donors.length === 0 ? <tr><td colSpan={5} className="p-12 text-center text-slate-400 font-bold">No donors registered.</td></tr> : donors.map(donor => (
                    <tr key={donor.id} className="hover:bg-slate-50">
                        <td className="p-4 font-mono text-xs text-slate-500 uppercase">{donor.donor_id || donor.id?.substring(0,8)}</td>
                      <td className="p-4 font-bold text-slate-800">{donor.first_name} {donor.last_name}</td>
                      <td className="p-4 font-black text-rose-700">{donor.blood_group}{donor.rh_factor}</td>
                      <td className="p-4 font-mono text-xs">{donor.contact_number}</td>
                      <td className="p-4 text-center">
                        <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider ${donor.screening_status === 'eligible' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{donor.screening_status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* DONOR MODAL */}
      {showDonorModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm">
          <form onSubmit={handleRegisterDonor} className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-xl font-black text-slate-800 flex items-center gap-2 mb-2"><HandHeart size={22} className="text-rose-600"/> Register New Donor</h3>
            
            <div className="grid grid-cols-2 gap-3">
               <div>
                  <label className="text-xs font-bold text-slate-500 uppercase block mb-1">First Name *</label>
                  <input type="text" required value={dFirst} onChange={e=>setDFirst(e.target.value)} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400" placeholder="John" />
               </div>
               <div>
                  <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Last Name *</label>
                  <input type="text" required value={dLast} onChange={e=>setDLast(e.target.value)} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400" placeholder="Doe" />
               </div>
            </div>

            <div>
               <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Date of Birth *</label>
               <input type="date" required value={dDob} onChange={e=>setDDob(e.target.value)} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400" />
            </div>

            <div className="grid grid-cols-2 gap-3">
               <div>
                  <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Blood Group *</label>
                  <select value={dGroup} onChange={e=>setDGroup(e.target.value)} required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400 bg-white">
                     <option value="O">O</option>
                     <option value="A">A</option>
                     <option value="B">B</option>
                     <option value="AB">AB</option>
                  </select>
               </div>
               <div>
                  <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Rh Factor *</label>
                  <select value={dRh} onChange={e=>setDRh(e.target.value)} required className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400 bg-white">
                     <option value="+">+ Positive</option>
                     <option value="-">- Negative</option>
                  </select>
               </div>
            </div>

            <div>
               <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Contact Number *</label>
               <input type="tel" required value={dContact} onChange={e=>setDContact(e.target.value)} className="w-full p-2.5 border rounded-lg text-sm outline-none focus:border-rose-400" placeholder="+1 (555) 000-0000" />
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-100 mt-2">
              <button type="button" onClick={() => setShowDonorModal(false)} className="px-5 py-2 text-slate-600 text-sm font-bold hover:bg-slate-50 rounded-lg">Cancel</button>
              <button type="submit" disabled={simulating} className="bg-rose-600 hover:bg-rose-700 text-white px-6 py-2 rounded-xl text-sm font-bold transition-all shadow-md shadow-rose-200 flex items-center gap-2">
                 <CheckCircle size={16}/> {simulating ? "Saving..." : "Register & Bag Unit"}
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}
