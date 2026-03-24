"use client";

import React, { useState, useEffect } from "react";
import { ipdApi } from "@/lib/ipd-api";

export default function IpdTransfersPage() {
  const [activeTab, setActiveTab] = useState<"requests" | "new_request">("requests");
  const [transfers, setTransfers] = useState<any[]>([]);
  const [admissions, setAdmissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // New Request Form State
  const [admNo, setAdmNo] = useState("");
  const [currentWard, setCurrentWard] = useState("Ward A");
  const [currentBed, setCurrentBed] = useState("101");
  const [reqWard, setReqWard] = useState("");
  const [reqBedCat, setReqBedCat] = useState("General");
  const [transferType, setTransferType] = useState("Ward-to-Ward");
  const [priority, setPriority] = useState("Routine");
  const [reason, setReason] = useState("");
  
  // ISBAR State
  const [sit, setSit] = useState("");
  const [bg, setBg] = useState("");
  const [asmnt, setAsmnt] = useState("");
  const [rec, setRec] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [transfersRes, admissionsRes] = await Promise.all([
        ipdApi.getTransferRequests(),
        ipdApi.getAdmissions()
      ]);
      setTransfers((transfersRes as any).data || transfersRes);
      setAdmissions((admissionsRes as any).data || admissionsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAdmissionSelect = (selectedAdmNo: string) => {
    setAdmNo(selectedAdmNo);
    const adm = admissions.find((a) => a.admission_number === selectedAdmNo);
    if (adm) {
      setCurrentWard(adm.ward_id || "");
      setCurrentBed(adm.bed_number || "");
    } else {
      setCurrentWard("");
      setCurrentBed("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!admNo) return alert("Admission Number is required");
    try {
      await ipdApi.createTransferRequest(admNo, {
        current_ward: currentWard,
        current_bed: currentBed,
        requested_ward: reqWard,
        requested_bed_category: reqBedCat,
        reason: reason,
        transfer_type: transferType,
        priority: priority,
        handover: {
          situation: sit,
          background: bg,
          assessment: asmnt,
          recommendation: rec
        }
      });
      alert("Transfer request submitted successfully!");
      setActiveTab("requests");
      fetchData();
    } catch (err) {
      console.error(err);
      alert("Error submitting request.");
    }
  };

  const handleApprove = async (id: string) => {
    const bed = prompt("Enter approved bed number:");
    if (!bed) return;
    try {
      await ipdApi.approveTransfer(id, { approved_bed: bed, remarks: "Approved by manager" });
      fetchData();
    } catch (err) {
      console.error(err);
      alert("Failed to approve");
    }
  };

  const handleReject = async (id: string) => {
    const rmk = prompt("Enter rejection reason:");
    if (!rmk) return;
    try {
      await ipdApi.rejectTransfer(id, rmk);
      fetchData();
    } catch (err) {
      console.error(err);
      alert("Failed to reject");
    }
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
            Bed Transfer & Patient Movement
          </h1>
          <p className="text-gray-500 text-sm mt-1">Manage hospital ward transfers and ICU movements</p>
        </div>
        <div className="flex space-x-2 bg-indigo-50/50 p-1 rounded-xl border border-indigo-100">
          <button
            onClick={() => setActiveTab("requests")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === "requests" ? "bg-white text-indigo-700 shadow-sm" : "text-gray-600 hover:text-indigo-600"
            }`}
          >
            Transfer Worklist
          </button>
          <button
            onClick={() => setActiveTab("new_request")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === "new_request" ? "bg-white text-indigo-700 shadow-sm" : "text-gray-600 hover:text-indigo-600"
            }`}
          >
            New Request
          </button>
        </div>
      </div>

      {activeTab === "requests" ? (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex-1 flex flex-col">
          <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
            <h2 className="text-sm font-semibold text-gray-700 flex items-center">
              <svg className="w-4 h-4 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              Active Transfer Requests
            </h2>
            <button onClick={fetchData} className="text-indigo-600 hover:text-indigo-700 text-sm font-medium flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600">
              <thead className="bg-gray-50 text-gray-700 border-b border-gray-100">
                <tr>
                  <th className="px-4 py-3 font-semibold">Patient & Adm No</th>
                  <th className="px-4 py-3 font-semibold">Current Bed</th>
                  <th className="px-4 py-3 font-semibold">Target Ward</th>
                  <th className="px-4 py-3 font-semibold">Transfer Type</th>
                  <th className="px-4 py-3 font-semibold">Priority</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {transfers.length === 0 ? (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No transfer requests found.</td></tr>
                ) : transfers.map((t) => (
                  <tr key={t.id} className="hover:bg-indigo-50/30 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{t.patient_uhid}</div>
                      <div className="text-xs text-gray-500">{t.admission_number}</div>
                    </td>
                    <td className="px-4 py-3">{t.current_ward} / {t.current_bed}</td>
                    <td className="px-4 py-3 font-medium text-indigo-700">{t.requested_ward} <span className="text-xs font-normal text-gray-500">({t.requested_bed_category})</span></td>
                    <td className="px-4 py-3">{t.transfer_type}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${t.priority === 'Emergency' ? 'bg-red-100 text-red-700' : t.priority === 'Urgent' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                        {t.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${t.status === 'Pending' ? 'bg-blue-100 text-blue-700' : t.status === 'Approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-700'}`}>
                        {t.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {t.status === "Pending" && (
                        <div className="flex space-x-2">
                          <button onClick={() => handleApprove(t.id)} className="px-3 py-1 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 rounded-md text-xs font-medium transition-colors">Approve</button>
                          <button onClick={() => handleReject(t.id)} className="px-3 py-1 bg-red-50 text-red-600 hover:bg-red-100 rounded-md text-xs font-medium transition-colors">Reject</button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex-1 overflow-y-auto">
          <div className="p-6">
            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Patient Details */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mr-3 text-sm">1</span>
                  Patient & Transfer Details
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pl-11">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Admission Number *</label>
                    <select value={admNo} onChange={(e) => handleAdmissionSelect(e.target.value)} required className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all bg-white">
                      <option value="">Select Action</option>
                      {admissions.map(adm => (
                        <option key={adm.admission_number} value={adm.admission_number}>
                          {adm.admission_number} ({adm.patient_uhid})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Priority</label>
                    <select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all bg-white">
                      <option>Routine</option>
                      <option>Urgent</option>
                      <option>Emergency</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Transfer Type</label>
                    <select value={transferType} onChange={(e) => setTransferType(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all bg-white">
                      <option>Ward-to-Ward</option>
                      <option>Bed-to-Bed</option>
                      <option>ICU Transfer</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Reason for Transfer</label>
                    <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} required className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="E.g. Condition deterioration" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Current Ward</label>
                    <input type="text" value={currentWard} onChange={(e) => setCurrentWard(e.target.value)} required className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-gray-50" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Current Bed</label>
                    <input type="text" value={currentBed} onChange={(e) => setCurrentBed(e.target.value)} required className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-gray-50" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Requested Ward *</label>
                    <input type="text" value={reqWard} onChange={(e) => setReqWard(e.target.value)} required className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="E.g. ICU" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Bed Category</label>
                    <select value={reqBedCat} onChange={(e) => setReqBedCat(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white">
                      <option>General</option>
                      <option>Semi-Private</option>
                      <option>Private</option>
                      <option>ICU</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* ISBAR Handover */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mr-3 text-sm">2</span>
                  Clinical Handover (ISBAR)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-11">
                  <div className="space-y-4 border border-emerald-100 bg-emerald-50/30 p-4 rounded-xl">
                    <div className="flex items-start">
                      <div className="w-8 h-8 rounded bg-emerald-100 text-emerald-700 font-bold flex items-center justify-center mr-3 shrink-0">S</div>
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-700 mb-1">Situation</label>
                        <p className="text-xs text-gray-500 mb-2">What is the problem/reason for transfer?</p>
                        <textarea value={sit} onChange={(e) => setSit(e.target.value)} required rows={2} className="w-full px-3 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none resize-none" placeholder="E.g. Patient requires ICU monitoring..."></textarea>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <div className="w-8 h-8 rounded bg-emerald-100 text-emerald-700 font-bold flex items-center justify-center mr-3 shrink-0">B</div>
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-700 mb-1">Background</label>
                        <p className="text-xs text-gray-500 mb-2">Brief clinical history related to the situation.</p>
                        <textarea value={bg} onChange={(e) => setBg(e.target.value)} required rows={2} className="w-full px-3 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none resize-none" placeholder="E.g. Post-operative complications..."></textarea>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4 border border-indigo-100 bg-indigo-50/30 p-4 rounded-xl">
                    <div className="flex items-start">
                      <div className="w-8 h-8 rounded bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center mr-3 shrink-0">A</div>
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-700 mb-1">Assessment</label>
                        <p className="text-xs text-gray-500 mb-2">Current clinical status, recent vitals, concerns.</p>
                        <textarea value={asmnt} onChange={(e) => setAsmnt(e.target.value)} required rows={2} className="w-full px-3 py-2 border border-indigo-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none resize-none" placeholder="E.g. BP unstable, SpO2 dropping..."></textarea>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <div className="w-8 h-8 rounded bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center mr-3 shrink-0">R</div>
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-700 mb-1">Recommendation</label>
                        <p className="text-xs text-gray-500 mb-2">What action needs to be taken by the receiving team?</p>
                        <textarea value={rec} onChange={(e) => setRec(e.target.value)} required rows={2} className="w-full px-3 py-2 border border-indigo-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none resize-none" placeholder="E.g. Immediate ICU care and ventilator support..."></textarea>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pl-11 pt-4 border-t border-gray-100">
                <button type="submit" className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors shadow-sm shadow-indigo-200 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Submit Transfer Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
