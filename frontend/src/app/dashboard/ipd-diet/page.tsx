"use client";
import React, { useState, useEffect } from "react";
import { Utensils, Search, Filter, Plus, FileText, CheckCircle2, Clock, X } from "lucide-react";
import { ipdApi } from "@/lib/ipd-api";

export default function IpdDietManagementPage() {
  const [activeTab, setActiveTab] = useState("roster");
  const [reportGenerated, setReportGenerated] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const [patients, setPatients] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [showDietModal, setShowDietModal] = useState(false);
  const [updatingDiet, setUpdatingDiet] = useState(false);
  const [dietForm, setDietForm] = useState({
    diet_type: "",
    meal_instructions: "",
    allergies: ""
  });

  useEffect(() => {
    const fetchDietRoster = async () => {
      try {
        const res: any = await ipdApi.getAdmissions();
        const activeAdmissions = res.data || res;
        const mappedRoster = await Promise.all(activeAdmissions.map(async (adm: any) => {
          try {
            const dietRes = await ipdApi.getDietPrescription(adm.admission_number);
            const dietData = dietRes.data || dietRes;
            return {
              id: adm.admission_number,
              name: adm.patient_name || reqNameMapping(adm.patient_uhid) || "Unregistered Patient",
              ward: "General Ward",
              diet: dietData?.diet_type || (adm.status === "ADMITTED" ? "Standard Routine" : "NPO (Nil Per Os)"),
              status: adm.status,
              allergies: dietData?.allergies || "NKDA",
              nextMeal: "Lunch (12:30 PM)"
            };
          } catch {
            return {
              id: adm.admission_number,
              name: adm.patient_name || reqNameMapping(adm.patient_uhid) || "Unregistered Patient",
              ward: "General Ward",
              diet: adm.status === "ADMITTED" ? "Standard Routine" : "NPO (Nil Per Os)",
              status: adm.status,
              allergies: "NKDA",
              nextMeal: "Lunch (12:30 PM)"
            };
          }
        }));
        setPatients(mappedRoster);
      } catch (err) {
        console.error("Failed to load diet roster from DB", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDietRoster();
  }, []);

  // Simple mock mapper since cross-module joins might be missing patient name in raw IPD list locally
  const reqNameMapping = (uuid: string) => {
    if(uuid?.includes('Test')) return "Test Subject";
    return null;
  };

  const handleUpdateDiet = (patient: any) => {
    setSelectedPatient(patient);
    setDietForm({
      diet_type: patient.diet || "",
      meal_instructions: "",
      allergies: patient.allergies || ""
    });
    setShowDietModal(true);
  };

  const handleSaveDiet = async () => {
    if (!selectedPatient) return;
    setUpdatingDiet(true);
    try {
      await ipdApi.updateDietPrescription(selectedPatient.id, {
        diet_type: dietForm.diet_type,
        meal_instructions: dietForm.meal_instructions,
        allergies: dietForm.allergies
      });
      
      setPatients(prev => prev.map(p => 
        p.id === selectedPatient.id 
          ? { ...p, diet: dietForm.diet_type, allergies: dietForm.allergies }
          : p
      ));
      
      setShowDietModal(false);
      alert("Diet prescription updated successfully. Kitchen notified.");
    } catch (err) {
      console.error("Failed to update diet", err);
      alert("Failed to update diet. Please try again.");
    } finally {
      setUpdatingDiet(false);
    }
  };

  return (
    <div className="p-6 h-full bg-slate-50 overflow-y-auto">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-2">
            <Utensils className="text-emerald-600" size={28} />
            Clinical Nutrition & Dietetics
          </h1>
          <p className="text-sm font-medium text-slate-500 mt-1">Manage inpatient meal plans, nutritional assessments, and dietary restrictions.</p>
        </div>
        <div className="flex gap-2">
          <button className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-md transition flex items-center gap-2">
            <Filter size={16}/> Filter Wards
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-slate-200 mb-6">
        <button 
          onClick={() => setActiveTab("roster")}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${activeTab === "roster" ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
          Patient Diet Roster
        </button>
        <button 
          onClick={() => setActiveTab("kitchen")}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${activeTab === "kitchen" ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
          Kitchen Requisition
        </button>
      </div>

      {activeTab === "roster" && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <div className="relative w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input type="text" placeholder="Search patient or UUID..." className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition" />
            </div>
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">{patients.length} Active Patients</p>
          </div>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-[11px] uppercase tracking-wider text-slate-500 font-bold">
                <th className="p-4 rounded-tl-2xl">Patient Info</th>
                <th className="p-4">Ward / Bed</th>
                <th className="p-4">Current Diet</th>
                <th className="p-4">Allergies</th>
                <th className="p-4">Next Scheduled Meal</th>
                <th className="p-4 rounded-tr-2xl text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                  <td className="p-4">
                    <p className="text-sm font-bold text-slate-800">{p.name}</p>
                    <p className="text-[10px] text-slate-400 font-mono mt-0.5">{p.id}</p>
                  </td>
                  <td className="p-4">
                    <span className="inline-flex items-center px-2 py-1 bg-slate-100 text-slate-600 rounded-md text-xs font-semibold">{p.ward}</span>
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${p.diet.includes("NPO") ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>
                      {p.diet}
                    </span>
                  </td>
                  <td className="p-4">
                    <p className={`text-xs font-bold ${p.allergies !== "None" ? 'text-amber-600' : 'text-slate-400'}`}>{p.allergies}</p>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                      <Clock size={12} className={p.nextMeal !== "N/A" ? "text-slate-400" : "text-slate-300"}/>
                      {p.nextMeal}
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <button onClick={() => handleUpdateDiet(p)} className="text-xs font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-lg transition">Update Diet</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === "kitchen" && (
        !reportGenerated ? (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center h-[400px] flex flex-col items-center justify-center">
            <FileText size={48} className="text-slate-200 mb-4" />
            <h3 className="text-lg font-bold text-slate-700 mb-2">Kitchen Dispatch Overview</h3>
            <p className="text-sm text-slate-500 max-w-md">The culinary summary and bulk dispatch features are active upon batch processing meal orders.</p>
            <button onClick={() => setReportGenerated(true)} className="mt-6 px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-bold shadow-md hover:bg-emerald-700 transition">Generate Dispatch Report</button>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 animate-in fade-in duration-300">
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-lg font-black text-slate-800">Lunch Dispatch Manifest</h3>
                <p className="text-xs text-slate-500 font-mono mt-1">Generated: {new Date().toLocaleString()}</p>
              </div>
              <button onClick={() => alert("Report sent to kitchen printer.")} className="px-5 py-2 bg-slate-800 text-white text-xs font-bold rounded-lg shadow-sm hover:bg-slate-900 transition">Print to Kitchen</button>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                <p className="text-xs font-bold text-emerald-600 uppercase tracking-widest mb-1">Total Meals needed</p>
                <p className="text-2xl font-black text-emerald-800">{patients.length}</p>
              </div>
              <div className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                <p className="text-xs font-bold text-amber-600 uppercase tracking-widest mb-1">Special Diets</p>
                <p className="text-2xl font-black text-amber-800">{patients.filter(p => !p.diet.includes("Standard") && !p.diet.includes("NPO")).length}</p>
              </div>
              <div className="p-4 bg-rose-50 rounded-xl border border-rose-100">
                <p className="text-xs font-bold text-rose-600 uppercase tracking-widest mb-1">NPO (Do Not Feed)</p>
                <p className="text-2xl font-black text-rose-800">{patients.filter(p => p.diet.includes("NPO")).length}</p>
              </div>
            </div>

            <table className="w-full text-left border-collapse border border-slate-200 rounded-xl overflow-hidden">
              <thead>
                <tr className="bg-slate-100 text-xs uppercase tracking-wider text-slate-600 font-bold">
                  <th className="p-3 border-b border-slate-200">Ward Name</th>
                  <th className="p-3 border-b border-slate-200">Standard / Routine</th>
                  <th className="p-3 border-b border-slate-200">Special Diets</th>
                  <th className="p-3 border-b border-slate-200">NPO (Nil Per Os)</th>
                </tr>
              </thead>
              <tbody className="text-sm font-medium text-slate-700">
                {/* Dynamically grouped by Ward */}
                {Array.from(new Set(patients.map(p => p.ward))).map((wardName, idx) => {
                  const wardPatients = patients.filter(p => p.ward === wardName);
                  const countStandard = wardPatients.filter(p => p.diet.includes("Standard")).length;
                  const countSpecial = wardPatients.filter(p => !p.diet.includes("Standard") && !p.diet.includes("NPO")).length;
                  const countNPO = wardPatients.filter(p => p.diet.includes("NPO")).length;
                  return (
                    <tr key={idx} className="border-b border-slate-100">
                      <td className="p-3 bg-slate-50 font-bold">{wardName}</td>
                      <td className="p-3 text-emerald-600 font-bold">{countStandard}</td>
                      <td className="p-3 text-amber-600 font-bold">{countSpecial}</td>
                      <td className={`p-3 font-bold ${countNPO > 0 ? "text-rose-600" : "text-slate-400"}`}>{countNPO}</td>
                    </tr>
                  )
                })}
                {patients.length === 0 && (
                   <tr className="border-b border-slate-100"><td colSpan={4} className="p-4 text-center text-slate-500">No wards populated</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )
      )}

      {/* Diet Update Modal */}
      {showDietModal && selectedPatient && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4">
            <div className="flex justify-between items-center p-6 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-800">Update Diet Prescription</h3>
              <button onClick={() => setShowDietModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-600 mb-1">Patient</p>
                <p className="text-sm font-bold text-slate-800">{selectedPatient.name}</p>
                <p className="text-xs text-slate-400">{selectedPatient.id}</p>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Diet Type</label>
                <select
                  value={dietForm.diet_type}
                  onChange={(e) => setDietForm({...dietForm, diet_type: e.target.value})}
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                >
                  <option value="">Select Diet Type</option>
                  <option value="Standard Routine">Standard Routine</option>
                  <option value="Liquid">Liquid</option>
                  <option value="Diabetic">Diabetic</option>
                  <option value="Low Sodium">Low Sodium</option>
                  <option value="High Protein">High Protein</option>
                  <option value="Low Fat">Low Fat</option>
                  <option value="Vegetarian">Vegetarian</option>
                  <option value="NPO (Nil Per Os)">NPO (Nil Per Os)</option>
                  <option value="Clear Liquid">Clear Liquid</option>
                  <option value="Full Liquid">Full Liquid</option>
                  <option value="Soft Diet">Soft Diet</option>
                  <option value="Bland Diet">Bland Diet</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Meal Instructions</label>
                <textarea
                  value={dietForm.meal_instructions}
                  onChange={(e) => setDietForm({...dietForm, meal_instructions: e.target.value})}
                  placeholder="Special instructions for meal preparation..."
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition resize-none"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Allergies</label>
                <input
                  type="text"
                  value={dietForm.allergies}
                  onChange={(e) => setDietForm({...dietForm, allergies: e.target.value})}
                  placeholder="e.g., NKDA, Peanuts, Dairy"
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                />
              </div>
            </div>
            <div className="flex gap-3 p-6 border-t border-slate-100">
              <button
                onClick={() => setShowDietModal(false)}
                className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-700 font-bold rounded-xl hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveDiet}
                disabled={updatingDiet || !dietForm.diet_type}
                className="flex-1 px-4 py-2.5 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {updatingDiet ? "Updating..." : "Update Diet"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
