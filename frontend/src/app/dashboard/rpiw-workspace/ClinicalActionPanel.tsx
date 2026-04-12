"use client";
import React, { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ClinicalActionPanel({ 
  patientUhid, 
  userRole = "doctor" 
}: { 
  patientUhid: string, 
  userRole?: string 
}) {
  const [activeTab, setActiveTab] = useState("note");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success'|'error', text: string} | null>(null);

  // Form States
  const [noteForm, setNoteForm] = useState({ note_type: "Progress", content: "" });
  const [orderForm, setOrderForm] = useState({ order_category: "laboratory", item_code: "", item_name: "", priority: "Routine" });
  const [rxForm, setRxForm] = useState({ drug_name: "", dosage: "", frequency: "Once daily", route: "Oral", duration_days: 3, instructions: "" });
  const [taskForm, setTaskForm] = useState({ assigned_role: "nurse", task_description: "", priority: "Routine" });
  const [voiceInput, setVoiceInput] = useState("");

  const handleActionSubmit = async (endpoint: string, payload: any) => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`${API}/api/v1/rpiw-actions/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_uhid: patientUhid,
          created_by_user_id: `UID-${userRole.toUpperCase()}-001`,
          created_by_role: userRole,
          ...payload
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Submission failed");
      
      setMessage({ type: 'success', text: `Action completed! Status: ${data.status}` });
      // Clear forms
      setNoteForm({ note_type: "Progress", content: "" });
      setOrderForm({ order_category: "laboratory", item_code: "", item_name: "", priority: "Routine" });
      setRxForm({ drug_name: "", dosage: "", frequency: "Once daily", route: "Oral", duration_days: 3, instructions: "" });
      setTaskForm({ assigned_role: "nurse", task_description: "", priority: "Routine" });
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    }
    setLoading(false);
  };

  const handleVoiceProcess = async () => {
    if (!voiceInput.trim()) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(`${API}/api/v1/rpiw-actions/voice-parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_uhid: patientUhid,
          created_by_user_id: `UID-${userRole.toUpperCase()}-001`,
          created_by_role: userRole,
          transcript: voiceInput
        })
      });
      const data = await res.json();
      if (data.actions_extracted.length > 0) {
        setMessage({ type: 'success', text: `Voice parsed successfully. Extracted ${data.actions_extracted.length} actions.` });
      } else {
        setMessage({ type: 'error', text: "Voice parsed but no actionable context found." });
      }
    } catch (e) {
      setMessage({ type: 'error', text: "Voice processing failed." });
    }
    setLoading(false);
  };

  const tabs = [
    { id: "note", label: "Add Note", icon: "📝" },
    { id: "order", label: "Order Test", icon: "🔬" },
    { id: "prescription", label: "Prescribe Drug", icon: "💊", lock: userRole !== 'doctor' },
    { id: "task", label: "Assign Task", icon: "📋" },
    { id: "voice", label: "Voice Action", icon: "🎙️" },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
      <div className="bg-gradient-to-r from-gray-800 to-gray-700 p-4 flex gap-2 overflow-x-auto">
        {tabs.map(t => (
          <button 
            key={t.id} 
            onClick={() => !t.lock && setActiveTab(t.id)}
            disabled={t.lock}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
              t.lock ? 'opacity-50 cursor-not-allowed bg-gray-600/50 text-gray-400' :
              activeTab === t.id ? 'bg-white text-gray-900 shadow' : 'bg-gray-700/50 hover:bg-gray-600 text-gray-200'
            }`}
          >
            <span>{t.icon}</span> {t.label} {t.lock && <span className="ml-1 text-[10px]">🔒</span>}
          </button>
        ))}
      </div>

      <div className="p-6">
        {message && (
          <div className={`p-4 rounded-xl text-sm font-medium mb-6 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
             {message.type === 'success' ? '✅' : '⚠️'} {message.text}
          </div>
        )}

        {/* Note Form */}
        {activeTab === "note" && (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Note Type</label>
              <select className="w-full border p-2 rounded-lg text-sm" value={noteForm.note_type} onChange={e => setNoteForm({...noteForm, note_type: e.target.value})}>
                <option>Progress</option><option>Nursing</option><option>Procedure</option><option>Discharge</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Content</label>
              <textarea rows={4} className="w-full border p-2 rounded-lg text-sm" placeholder="Enter clinical note details..." value={noteForm.content} onChange={e => setNoteForm({...noteForm, content: e.target.value})}></textarea>
            </div>
            <button onClick={() => handleActionSubmit('notes', noteForm)} disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-xl transition-colors">
              {loading ? 'Saving...' : 'Save Clinical Note'}
            </button>
          </div>
        )}

        {/* Order Form */}
        {activeTab === "order" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Category</label>
                <select className="w-full border p-2 rounded-lg text-sm" value={orderForm.order_category} onChange={e => setOrderForm({...orderForm, order_category: e.target.value})}>
                  <option value="laboratory">Laboratory / LIS</option><option value="radiology">Radiology / RIS</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Priority</label>
                <select className="w-full border p-2 rounded-lg text-sm" value={orderForm.priority} onChange={e => setOrderForm({...orderForm, priority: e.target.value})}>
                  <option>Routine</option><option>Urgent</option><option>STAT</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
               <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Item Code</label>
                <input type="text" className="w-full border p-2 rounded-lg text-sm" placeholder="e.g. LAB-001" value={orderForm.item_code} onChange={e => setOrderForm({...orderForm, item_code: e.target.value})} />
              </div>
              <div>
                 <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Item Name</label>
                 <input type="text" className="w-full border p-2 rounded-lg text-sm" placeholder="e.g. Complete Blood Count" value={orderForm.item_name} onChange={e => setOrderForm({...orderForm, item_name: e.target.value})} />
              </div>
            </div>
            <button onClick={() => handleActionSubmit('orders', orderForm)} disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-xl transition-colors">
              {loading ? 'Processing...' : 'Place Order'}
            </button>
          </div>
        )}

        {/* Rx Form */}
        {activeTab === "prescription" && (
          <div className="space-y-4">
             <div>
                 <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Drug Name</label>
                 <input type="text" className="w-full border p-2 rounded-lg text-sm" placeholder="e.g. Paracetamol / Penicillin (Triggers allergy check)" value={rxForm.drug_name} onChange={e => setRxForm({...rxForm, drug_name: e.target.value})} />
             </div>
             <div className="grid grid-cols-2 gap-4">
                 <div>
                     <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Dosage</label>
                     <input type="text" className="w-full border p-2 rounded-lg text-sm" placeholder="e.g. 500mg" value={rxForm.dosage} onChange={e => setRxForm({...rxForm, dosage: e.target.value})} />
                 </div>
                 <div>
                     <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Route</label>
                     <select className="w-full border p-2 rounded-lg text-sm" value={rxForm.route} onChange={e => setRxForm({...rxForm, route: e.target.value})}>
                         <option>Oral</option><option>IV</option><option>IM</option><option>Topical</option>
                     </select>
                 </div>
             </div>
             <div className="grid grid-cols-2 gap-4">
                 <div>
                     <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Frequency</label>
                     <select className="w-full border p-2 rounded-lg text-sm" value={rxForm.frequency} onChange={e => setRxForm({...rxForm, frequency: e.target.value})}>
                         <option>Once daily</option><option>Twice daily</option><option>Thrice daily</option><option>As needed</option>
                     </select>
                 </div>
                 <div>
                     <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Duration (Days)</label>
                     <input type="number" min="1" className="w-full border p-2 rounded-lg text-sm" value={rxForm.duration_days} onChange={e => setRxForm({...rxForm, duration_days: parseInt(e.target.value)})} />
                 </div>
             </div>
            <button onClick={() => handleActionSubmit('prescriptions', rxForm)} disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded-xl transition-colors">
              {loading ? 'Validating...' : 'Validate & Prescribe'}
            </button>
          </div>
        )}

        {/* Task Form */}
        {activeTab === "task" && (
           <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
               <div>
                 <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Assign To Role</label>
                 <select className="w-full border p-2 rounded-lg text-sm" value={taskForm.assigned_role} onChange={e => setTaskForm({...taskForm, assigned_role: e.target.value})}>
                  <option value="nurse">Nurse</option><option value="phlebotomist">Phlebotomist</option>
                 </select>
               </div>
               <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Priority</label>
                  <select className="w-full border p-2 rounded-lg text-sm" value={taskForm.priority} onChange={e => setTaskForm({...taskForm, priority: e.target.value})}>
                    <option>Routine</option><option>High</option>
                  </select>
               </div>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Task Description</label>
              <textarea rows={3} className="w-full border p-2 rounded-lg text-sm" placeholder="e.g. Monitor blood pressure every 2 hours" value={taskForm.task_description} onChange={e => setTaskForm({...taskForm, task_description: e.target.value})}></textarea>
            </div>
            <button onClick={() => handleActionSubmit('tasks', taskForm)} disabled={loading} className="w-full bg-amber-500 hover:bg-amber-600 text-white font-bold py-2 px-4 rounded-xl transition-colors">
              {loading ? 'Assigning...' : 'Assign Staff Task'}
            </button>
          </div>
        )}

        {/* Voice Form */}
         {activeTab === "voice" && (
           <div className="space-y-4 text-center">
             <div className="bg-gray-50 border p-8 rounded-xl">
               <div className="text-5xl mb-4">🎙️</div>
               <p className="font-bold text-gray-800 mb-2">Voice-to-Structured Action Processor</p>
               <p className="text-xs text-gray-500 mb-6">Type a simulated transcript below (e.g. "Order CBC and start IV ceftriaxone 1g")</p>
               
               <textarea rows={3} className="w-full border shadow-inner p-4 rounded-xl text-sm" 
                 placeholder="Waiting for voice transcript..." 
                 value={voiceInput} 
                 onChange={e => setVoiceInput(e.target.value)}></textarea>
             </div>
             
             <button onClick={handleVoiceProcess} disabled={loading} className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-xl transition-colors flex justify-center items-center gap-2">
              {loading ? <div className="animate-spin w-4 h-4 border-2 border-white/20 border-t-white rounded-full"></div> : null}
              {loading ? 'Processing NLP...' : 'Extract Clinical Actions from Transcript'}
            </button>
           </div>
         )}
      </div>
    </div>
  );
}
