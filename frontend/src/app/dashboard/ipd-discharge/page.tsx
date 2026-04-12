"use client";
import { useTranslation } from "@/i18n";


import React, { useState, useEffect } from "react";
import { ipdApi } from "@/lib/ipd-api";

export default function IpdDischargePage() {
  const { t } = useTranslation();
  const [admissions, setAdmissions] = useState<any[]>([]);
  const [selectedAdmNo, setSelectedAdmNo] = useState("");
  const [stateData, setStateData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [pendingOrders, setPendingOrders] = useState<any[]>([]);

  useEffect(() => {
    fetchAdmissions();
  }, []);

  const fetchAdmissions = async () => {
    try {
      const res: any = await ipdApi.getAdmissions();
      setAdmissions(res.data || res);
    } catch (err) {
      console.error(err);
    }
  };

  const loadDischargeState = async (admNo: string) => {
    if (!admNo) {
      setStateData(null);
      return;
    }
    setLoading(true);
    try {
      const res: any = await ipdApi.getDischargeState(admNo);
      setStateData(res.data || res);
      const ordersRes: any = await ipdApi.checkPendingOrders(admNo);
      setPendingOrders(ordersRes.data || ordersRes);
    } catch (err) {
      console.error(err);
      alert("Error loading discharge state from API.");
    } finally {
      setLoading(false);
    }
  };

  const handleAdmissionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedAdmNo(val);
    loadDischargeState(val);
  };

  const handlePlanChange = async (date: string) => {
    try {
      await ipdApi.updateDischargePlan(selectedAdmNo, { planned_discharge_date: date });
      loadDischargeState(selectedAdmNo);
    } catch (err) {
      console.error(err);
    }
  };

  const handleChecklistToggle = async (field: string, val: boolean) => {
    try {
      await ipdApi.updateDischargeChecklist(selectedAdmNo, { [field]: val });
      loadDischargeState(selectedAdmNo);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateSummary = async () => {
    try {
      await ipdApi.generateDischargeSummary(selectedAdmNo);
      loadDischargeState(selectedAdmNo);
    } catch (err) {
      console.error(err);
      alert("Error generating summary.");
    }
  };

  const handleSaveSummary = async (field: string, val: string) => {
    try {
      await ipdApi.updateDischargeSummary(selectedAdmNo, { [field]: val });
      loadDischargeState(selectedAdmNo);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFinalize = async () => {
    if (!selectedAdmNo) {
      alert("Please select an admission first.");
      return;
    }
    setFinalizing(true);
    try {
      console.log("Finalizing discharge for:", selectedAdmNo);
      const response = await ipdApi.finalizeDischarge(selectedAdmNo);
      console.log("Discharge finalize response:", response);
      alert("Discharge completed successfully.");
      setStateData(null);
      setSelectedAdmNo("");
      setPendingOrders([]);
      fetchAdmissions(); // refresh
    } catch (err: any) {
      console.error("Error finalizing discharge:", err);
      const errorMsg = err.response?.data?.detail || err.message || "Failed to finalize discharge.";
      alert("Error: " + errorMsg);
    } finally {
      setFinalizing(false);
    }
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-teal-600 to-emerald-600">
            {t("ipdDischarge.title")}
          </h1>
          <p className="text-gray-500 text-sm mt-1">{t("ipdDischarge.subtitle")}</p>
        </div>
        
        <div className="w-1/3">
          <label className="block text-xs font-semibold text-gray-600 mb-1 uppercase tracking-wider">{t("ipdDischarge.selectAdmission")}</label>
          <select 
            value={selectedAdmNo} 
            onChange={handleAdmissionChange}
            className="w-full px-4 py-2 border border-emerald-200 rounded-xl focus:ring-2 focus:ring-emerald-500 bg-white shadow-sm"
          >
            <option value="">-- {t("ipdDischarge.selectAdmission")} --</option>
            {admissions.map(a => (
              <option key={a.admission_number} value={a.admission_number}>
                {a.admission_number} ({a.patient_uhid})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div className="text-center p-8 text-emerald-600 animate-pulse">{t("ipdDischarge.loadingDischarge")}</div>}

      {!loading && stateData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 overflow-y-auto pb-4">
          
          {/* Left Column: Plan & Checklist */}
          <div className="space-y-6">
            <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 bg-emerald-50 rounded-bl-2xl">
                <span className="text-xs font-bold text-emerald-700">{stateData.plan.status}</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 text-emerald-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                {t("ipdDischarge.dischargePlan")}
              </h3>
              <div className="space-y-3">
                <label className="block text-xs text-gray-500">{t("ipdDischarge.plannedDate")}</label>
                <input 
                  type="datetime-local" 
                  value={stateData.plan.planned_discharge_date ? stateData.plan.planned_discharge_date.slice(0, 16) : ''}
                  onChange={(e) => handlePlanChange(new Date(e.target.value).toISOString())}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-emerald-500" 
                />
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 text-emerald-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                {t("ipdDischarge.checklist")}
              </h3>
              <div className="space-y-3">
                {[
                  { key: 'doctor_approval', label: 'Doctor Clinical Clearance' },
                  { key: 'nursing_clearance', label: 'Nursing Sign-off' },
                  { key: 'medications_reconciled', label: 'Medication Reconciliation' },
                  { key: 'final_investigations_checked', label: 'Final Labs/Imaging Checked' },
                  { key: 'patient_counseling', label: 'Patient Counseling Completed' },
                  { key: 'billing_clearance', label: 'Billing / Finance Clearance' },
                ].map(item => (
                  <label key={item.key} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors">
                    <input 
                      type="checkbox" 
                      checked={stateData.checklist[item.key]}
                      onChange={(e) => handleChecklistToggle(item.key, e.target.checked)}
                      className="w-5 h-5 rounded text-emerald-600 focus:ring-emerald-500 border-gray-300"
                    />
                    <span className="text-sm font-medium text-gray-700">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className={`p-5 rounded-2xl border shadow-sm ${pendingOrders.length > 0 ? 'bg-red-50 border-red-100' : 'bg-green-50 border-green-100'}`}>
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center">
                <svg className={`w-5 h-5 mr-2 ${pendingOrders.length > 0 ? 'text-red-500' : 'text-green-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  {pendingOrders.length > 0 ? (
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  ) : (
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  )}
                </svg>
                {t("ipdDischarge.pendingOrders")}
              </h3>
              {pendingOrders.length > 0 ? (
                <ul className="text-sm text-red-700 list-disc pl-5 mt-2">
                  {pendingOrders.map((o: any) => <li key={o.id}>{o.order_type} - {o.status}</li>)}
                </ul>
              ) : (
                <p className="text-sm text-green-700">{t("ipdDischarge.noPendingOrders")}</p>
              )}
            </div>
          </div>

          {/* Right Column: Discharge Summary */}
          <div className="md:col-span-2 space-y-4 flex flex-col h-full pl-2">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm flex-1 flex flex-col overflow-hidden">
              <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <svg className="w-5 h-5 text-indigo-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                  {t("ipdDischarge.dischargeSummary")}
                  {stateData.summary.status === 'Draft' ? (
                    <span className="ml-3 px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">Draft</span>
                  ) : (
                    <span className="ml-3 px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs rounded-full">Finalized</span>
                  )}
                </h3>
                <button 
                  onClick={handleGenerateSummary}
                  className="px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 text-xs font-semibold rounded-lg flex items-center transition-colors"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                  Auto-Generate
                </button>
              </div>
              
              <div className="p-6 overflow-y-auto flex-1 space-y-5">
                {[
                  { key: 'admission_diagnosis', label: 'Admission Diagnosis' },
                  { key: 'hospital_course', label: 'Hospital Course & Treatment' },
                  { key: 'procedures_performed', label: 'Procedures Performed' },
                  { key: 'medications_prescribed', label: 'Discharge Medications' },
                  { key: 'follow_up_instructions', label: 'Follow Up & Discharge Instructions' }
                ].map(field => (
                  <div key={field.key}>
                    <label className="block text-xs font-bold text-gray-700 mb-1 uppercase tracking-wide">{field.label}</label>
                    <textarea 
                      rows={3}
                      value={stateData.summary[field.key] || ''}
                      onChange={(e) => handleSaveSummary(field.key, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Final Action Bar */}
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-md flex justify-between items-center mt-auto">
               <div className="text-sm text-gray-500">
                  {t("ipdDischarge.checklist")}
               </div>
               <button
                  onClick={handleFinalize}
                  disabled={finalizing}
                  className="px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold rounded-xl transition-all shadow-lg hover:shadow-xl flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
               >
                  {finalizing ? (
                    <>
                      <svg className="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Processing...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      {t("ipdDischarge.completeDischarge")}
                    </>
                  )}
               </button>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !selectedAdmNo && (
        <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-gray-200 rounded-2xl bg-gray-50">
          <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m3-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
          <p className="text-gray-500 font-medium text-lg">{t("ipdDischarge.selectAdmission")}</p>
        </div>
      )}
    </div>
  );
}
