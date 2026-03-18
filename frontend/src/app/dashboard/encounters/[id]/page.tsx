"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, Search, Plus, User, Calendar, Phone, MapPin, 
  Droplets, Activity, Thermometer, Wind, Save, 
  Clock, CheckCircle, FileText, Pill, FlaskConical, 
  Eye, Stethoscope, ChevronRight, Loader2, MessageSquare, 
  Mic, MicOff, Languages, Send, ShieldAlert, 
  AlertTriangle, X, Info, HeartPulse, Weight, ImagePlus,
  FileSignature
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

// ─── Types ──────────────────────────────────────────────────────────
interface VitalsData {
  heart_rate: string;
  blood_pressure: string;
  temperature: string;
  oxygen_saturation: string;
  respiratory_rate: string;
  weight_kg: string;
  height_cm: string;
}

interface LabOrder {
  test_name: string;
  urgency: string;
  notes: string;
}

interface MedOrder {
  medication_name: string;
  dosage: string;
  frequency: string;
  route: string;
  notes: string;
}

interface ImagingOrder {
  modality: string;
  body_part: string;
  clinical_indication: string;
  urgency: string;
}

// ─── Speech Recognition with Translation ───────────────────────────
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export default function DoctorWorkspace() {
  const { id } = useParams();
  const router = useRouter();

  const [encounter, setEncounter] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("notes");
  const [bedInfo, setBedInfo] = useState<any>(null);

  // Voice / dictation
  const [isRecording, setIsRecording] = useState(false);
  const [voiceText, setVoiceText] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [rawTranscript, setRawTranscript] = useState("");
  const recognitionRef = useRef<any>(null);

  // Vitals state
  const [vitals, setVitals] = useState<VitalsData>({
    heart_rate: "",
    blood_pressure: "",
    temperature: "",
    oxygen_saturation: "",
    respiratory_rate: "",
    weight_kg: "",
    height_cm: "",
  });
  const [savingVitals, setSavingVitals] = useState(false);
  const [vitalsSaved, setVitalsSaved] = useState(false);

  // Lab Orders state
  const [labOrders, setLabOrders] = useState<LabOrder[]>([]);
  const [newLab, setNewLab] = useState<LabOrder>({ test_name: "", urgency: "routine", notes: "" });
  const [savingLab, setSavingLab] = useState(false);

  // Medication Orders state
  const [medOrders, setMedOrders] = useState<MedOrder[]>([]);
  const [newMed, setNewMed] = useState<MedOrder>({ medication_name: "", dosage: "", frequency: "", route: "oral", notes: "" });
  const [savingMed, setSavingMed] = useState(false);
  const [cdssAlerts, setCdssAlerts] = useState<any[]>([]);
  const [isCheckingSafety, setIsCheckingSafety] = useState(false);

  // Imaging Orders state
  const [imagingOrders, setImagingOrders] = useState<ImagingOrder[]>([]);
  const [newImaging, setNewImaging] = useState<ImagingOrder>({ modality: "X-Ray", body_part: "", clinical_indication: "", urgency: "routine" });
  const [savingImaging, setSavingImaging] = useState(false);

  // Close encounter modal
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [closingEncounter, setClosingEncounter] = useState(false);

  const authHeaders = () => ({
    "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
    "Content-Type": "application/json",
  });

  // ─── Fetch Encounter ──────────────────────────────────────────────
  useEffect(() => {
    const fetchWorkspace = async () => {
      try {
        const res = await fetch(`${API}/api/v1/encounters/${id}`, {
          headers: authHeaders()
        });
        if (res.ok) {
          const data = await res.json();
          setEncounter(data);
        }
      } catch (err) {
        console.error("Failed to load workspace", err);
      } finally {
        setLoading(false);
      }
    };
    const fetchBedAssignment = async () => {
      try {
        const res = await fetch(`${API}/api/v1/wards/beds`, { headers: authHeaders() });
        if (res.ok) {
           const beds = await res.json();
           // Find bed assigned to this encounter
           const assignedBed = beds.find((b: any) => b.status === "occupied"); // Simplified for now, should ideally be an endpoint taking encounter_id
           setBedInfo(assignedBed);
        }
      } catch (e) { console.error(e); }
    };

    if (id) {
      fetchWorkspace();
      fetchBedAssignment();
    }
  }, [id]);

  // ─── Voice Recording with Web Speech API ─────────────────────────
  const startRecording = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support speech recognition. Please use Chrome or Edge.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;

    // Accept any language spoken by user
    recognition.lang = "";  // empty = use browser default, auto-detects
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let finalTranscript = "";

    recognition.onresult = (event: any) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += t + " ";
        } else {
          interim += t;
        }
      }
      setRawTranscript(finalTranscript + interim);
      setVoiceText(finalTranscript + interim); // Show live transcript first
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      if (event.error === "not-allowed") {
        alert("Microphone permission denied. Please allow microphone access.");
      }
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
      // After recording ends, translate to English if needed
      if (finalTranscript.trim()) {
        translateToEnglish(finalTranscript.trim());
      }
    };

    recognition.start();
    setIsRecording(true);
    setVoiceText("");
    setRawTranscript("");
  }, []);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsRecording(false);
  }, []);

  const toggleVoiceRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Translate any language text to English using MyMemory free translation API
  const translateToEnglish = async (text: string) => {
    if (!text) return;
    setIsTranslating(true);
    try {
      // Detect if it's already English using heuristic; if so skip translation
      const englishWordPattern = /^[a-zA-Z0-9\s.,!?'"()-]+$/;
      if (englishWordPattern.test(text)) {
        setVoiceText(text);
        setIsTranslating(false);
        return;
      }

      // Using MyMemory free translation API (no key needed for basic use)
      const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=autodetect|en-US`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.responseStatus === 200 && data.responseData?.translatedText) {
        const translated = data.responseData.translatedText;
        setVoiceText(translated);
      } else {
        // Fallback: keep raw transcript
        setVoiceText(text);
      }
    } catch (err) {
      console.error("Translation failed:", err);
      setVoiceText(text); // Keep original on error
    } finally {
      setIsTranslating(false);
    }
  };

  // ─── Save Note ────────────────────────────────────────────────────
  const saveNote = async () => {
    if (!voiceText) return;
    try {
      await fetch(`${API}/api/v1/encounters/${id}/notes/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          note_type: "doctor_note",
          content: voiceText
        })
      });
      setVoiceText("");
      setRawTranscript("");
      window.location.reload();
    } catch (err) {
      console.error(err);
    }
  };

  // ─── Save Vitals as a Note ────────────────────────────────────────
  const saveVitals = async () => {
    if (!vitals.heart_rate && !vitals.blood_pressure && !vitals.temperature) {
      alert("Please fill at least one vital sign.");
      return;
    }
    setSavingVitals(true);
    try {
      const content = `VITALS RECORDED:\n• Heart Rate: ${vitals.heart_rate || "N/A"} bpm\n• Blood Pressure: ${vitals.blood_pressure || "N/A"}\n• Temperature: ${vitals.temperature || "N/A"} °F\n• O2 Saturation: ${vitals.oxygen_saturation || "N/A"} %\n• Respiratory Rate: ${vitals.respiratory_rate || "N/A"} breaths/min\n• Weight: ${vitals.weight_kg || "N/A"} kg\n• Height: ${vitals.height_cm || "N/A"} cm`;

      await fetch(`${API}/api/v1/encounters/${id}/notes/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ note_type: "vitals_record", content })
      });
      setVitalsSaved(true);
      setTimeout(() => setVitalsSaved(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSavingVitals(false);
    }
  };

  // ─── Save Lab Order ───────────────────────────────────────────────
  const saveLabOrder = async () => {
    if (!newLab.test_name) { alert("Enter test name."); return; }
    setSavingLab(true);
    try {
      const content = `LAB ORDER:\nTest: ${newLab.test_name}\nUrgency: ${newLab.urgency}\nNotes: ${newLab.notes || "None"}`;
      await fetch(`${API}/api/v1/encounters/${id}/notes/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ note_type: "lab_order", content })
      });
      setLabOrders(prev => [...prev, { ...newLab }]);
      setNewLab({ test_name: "", urgency: "routine", notes: "" });
    } catch (err) {
      console.error(err);
    } finally {
      setSavingLab(false);
    }
  };

  // ─── Save Med Order ───────────────────────────────────────────────
  const saveMedOrder = async () => {
    if (!newMed.medication_name || !newMed.dosage) { alert("Fill medication name and dosage."); return; }
    
    setIsCheckingSafety(true);
    setCdssAlerts([]);
    
    try {
      // 1. Run CDSS Smart Check
      const doseVal = parseFloat(newMed.dosage.replace(/[^\d.]/g, ''));
      const safetyRes = await fetch(`${API}/api/v1/cdss/engine/check-medication-smart?medication_id=${encodeURIComponent(newMed.medication_name)}&encounter_id=${id}&patient_id=${encounter.patient_id}${!isNaN(doseVal) ? `&dose=${doseVal}` : ''}`, {
        method: "POST",
        headers: authHeaders(),
      });
      
      const safetyData = await safetyRes.json();
      
      if (safetyData.alerts && safetyData.alerts.length > 0) {
        setCdssAlerts(safetyData.alerts);
        if (safetyData.status === "blocked") {
          setIsCheckingSafety(false);
          return; // Stop execution
        }
      }

      setSavingMed(true);
      const content = `MEDICATION ORDER:\nMedicine: ${newMed.medication_name}\nDosage: ${newMed.dosage}\nFrequency: ${newMed.frequency}\nRoute: ${newMed.route}\nNotes: ${newMed.notes || "None"}\nCDSS Status: ${safetyData.status}`;
      
      await fetch(`${API}/api/v1/encounters/${id}/notes/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ note_type: "medication_order", content })
      });
      
      setMedOrders(prev => [...prev, { ...newMed }]);
      setNewMed({ medication_name: "", dosage: "", frequency: "", route: "oral", notes: "" });
    } catch (err) {
      console.error(err);
    } finally {
      setSavingMed(false);
      setIsCheckingSafety(false);
    }
  };

  // ─── Save Imaging Order ───────────────────────────────────────────
  const saveImagingOrder = async () => {
    if (!newImaging.body_part || !newImaging.clinical_indication) { alert("Fill body part and clinical indication."); return; }
    setSavingImaging(true);
    try {
      // 1. Create a core Order first
      const orderRes = await fetch(`${API}/api/v1/orders/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          encounter_id: id,
          patient_id: encounter.patient_id,
          order_type: "RADIOLOGY_ORDER",
          priority: newImaging.urgency.toUpperCase(),
          items: [{
            item_type: "radiology_test",
            item_name: `${newImaging.modality}: ${newImaging.body_part}`,
            quantity: 1,
            unit_price: 100.0 // Default price for phase 11
          }]
        })
      });
      const coreOrder = await orderRes.json();

      // 2. Create the Radiology specific order
      await fetch(`${API}/api/v1/radiology/order`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          order_id: coreOrder.id,
          encounter_id: id,
          patient_id: encounter.patient_id,
          requested_modality: newImaging.modality,
          requested_study: `${newImaging.modality} ${newImaging.body_part}`,
          priority: newImaging.urgency
        })
      });

      // 3. (Optional) Still save a note for clinical visibility
      const content = `IMAGING ORDERED: ${newImaging.modality} ${newImaging.body_part}\nIndication: ${newImaging.clinical_indication}\nUrgency: ${newImaging.urgency}`;
      await fetch(`${API}/api/v1/encounters/${id}/notes/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ note_type: "imaging_order", content })
      });

      setImagingOrders(prev => [...prev, { ...newImaging }]);
      setNewImaging({ modality: "X-Ray", body_part: "", clinical_indication: "", urgency: "routine" });
    } catch (err) {
      console.error(err);
    } finally {
      setSavingImaging(false);
    }
  };

  // ─── Close Encounter ──────────────────────────────────────────────
  const closeEncounter = async () => {
    setClosingEncounter(true);
    try {
      const res = await fetch(`${API}/api/v1/encounters/${id}`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify({ status: "completed" })
      });
      if (res.ok) {
        router.push("/dashboard/encounters");
      } else {
        const error = await res.json();
        alert(`Failed to close: ${error.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error(err);
      alert("Network error while closing encounter.");
    } finally {
      setClosingEncounter(false);
      setShowCloseModal(false);
    }
  };

  // ─── Render ───────────────────────────────────────────────────────
  if (loading) return <div className="p-8 text-center flex items-center gap-3 justify-center text-lg"><Loader2 className="animate-spin text-blue-500" size={24}/>Loading Doctor Workspace...</div>;
  if (!encounter) return <div className="p-8 text-center text-red-500">Encounter not found</div>;

  const patientLabel = encounter.patient_id
    ? String(encounter.patient_id).split("-")[0].toUpperCase()
    : "??";

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-primary)] overflow-hidden">

      {/* ─── Close Encounter Confirmation Modal ─── */}
      {showCloseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-red-100 p-3 rounded-full"><CheckCircle className="text-red-500" size={24}/></div>
              <h2 className="text-xl font-bold text-slate-800">Close This Encounter?</h2>
            </div>
            <p className="text-slate-600 mb-6 text-sm">This will mark the encounter as <strong>completed</strong> and lock the workspace. Make sure all notes, vitals, and orders are saved before closing.</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowCloseModal(false)}
                className="px-5 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={closeEncounter}
                disabled={closingEncounter}
                className="px-5 py-2 rounded-lg bg-red-500 text-white font-bold hover:bg-red-600 transition-colors flex items-center gap-2 disabled:opacity-60"
              >
                {closingEncounter ? <><Loader2 size={16} className="animate-spin"/>Closing...</> : <><CheckCircle size={16}/>Yes, Close Encounter</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Header ─── */}
      <header className="bg-white border-b border-[var(--border)] p-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-4">
          <div className="bg-blue-100 text-blue-800 p-2 rounded-lg font-bold text-xl px-4 tracking-wider">
            {encounter.encounter_type}
          </div>
          <div>
            <h1 className="text-xl font-bold">Consultation Workspace</h1>
            <p className="text-sm text-[var(--text-secondary)]">ID: {encounter.encounter_uuid}</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary py-3 px-6 text-base flex items-center gap-2">
            <Clock size={18}/> {encounter.status}
          </button>
          <button
            onClick={() => setShowCloseModal(true)}
            className="btn-primary py-3 px-6 text-base flex items-center gap-2 bg-red-500 hover:bg-red-600 border-red-500"
          >
            <CheckCircle size={18}/> Close Encounter
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* ─── Left Column: Data & Input ─── */}
        <div className="flex-1 flex flex-col p-4 overflow-y-auto space-y-4">

          {/* Patient Summary */}
          <div className="bg-white rounded-xl shadow-sm border border-[var(--border)] p-5 flex gap-6 items-center">
            <div className="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center text-2xl font-bold text-slate-500">
              AX
            </div>
            <div className="flex-1 grid grid-cols-5 gap-4">
              <div><p className="text-xs text-[var(--text-secondary)]">Patient ID</p><p className="font-semibold">{patientLabel}</p></div>
              <div><p className="text-xs text-[var(--text-secondary)]">Age / Gender</p><p className="font-semibold">34 Y / Male</p></div>
              <div><p className="text-xs text-[var(--text-secondary)]">Department</p><p className="font-semibold">{encounter.department}</p></div>
              <div>
                <p className="text-xs text-[var(--text-secondary)]">Imaging Summary</p>
                <div className="flex flex-col gap-0.5 mt-0.5">
                   <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded w-fit">2 Pending Scans</span>
                   <span className="text-[9px] text-slate-500 italic">Latest: CT Chest (Completed)</span>
                </div>
              </div>
              <div>
                <p className="text-xs text-[var(--text-secondary)]">Alerts</p>
                <div className="flex gap-1 mt-1">
                  <span className="badge-error bg-red-100 text-red-800 font-bold px-2 py-0.5 rounded text-xs flex items-center gap-1">
                    <AlertTriangle size={12}/> Penicillin
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Clinical Data Tabs */}
          <div className="bg-white rounded-xl shadow-sm border border-[var(--border)] flex-1 flex flex-col overflow-hidden">
            <div className="flex border-b border-[var(--border)] bg-gray-50/50">
              {[
                { key: 'vitals', label: 'Vitals', icon: <HeartPulse size={14}/> },
                { key: 'labs', label: 'Labs', icon: <FlaskConical size={14}/> },
                { key: 'medications', label: 'Medications', icon: <Pill size={14}/> },
                { key: 'imaging', label: 'Imaging', icon: <ImagePlus size={14}/> },
                { key: 'notes', label: 'Notes', icon: <FileText size={14}/> },
              ].map(tab => (
                <button
                  key={tab.key}
                  className={`flex-1 py-4 text-sm font-semibold capitalize border-b-2 transition-colors flex items-center justify-center gap-1.5 ${activeTab === tab.key ? 'border-[var(--accent-primary)] text-[var(--accent-primary)] bg-white' : 'border-transparent text-[var(--text-secondary)] hover:bg-gray-100'}`}
                  onClick={() => setActiveTab(tab.key)}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>

            <div className="p-6 flex-1 overflow-y-auto bg-slate-50/30">

              {/* ─── VITALS TAB ─── */}
              {activeTab === 'vitals' && (
                <div className="space-y-5">
                  <div className="flex justify-between items-center">
                    <h3 className="font-bold text-lg flex items-center gap-2"><Activity size={18} className="text-rose-500"/> Record Vitals</h3>
                    {vitalsSaved && <span className="text-green-600 text-sm font-semibold flex items-center gap-1"><CheckCircle size={14}/> Vitals Saved!</span>}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">

                    <div className="bg-white p-4 rounded-xl border border-rose-100 shadow-sm">
                      <label className="text-xs text-slate-500 font-semibold flex items-center gap-1 mb-2"><HeartPulse size={13} className="text-rose-500"/> Heart Rate (bpm)</label>
                      <input
                        type="number" placeholder="e.g. 82"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-rose-300"
                        value={vitals.heart_rate}
                        onChange={e => setVitals(v => ({ ...v, heart_rate: e.target.value }))}
                      />
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-amber-100 shadow-sm">
                      <label className="text-xs text-slate-500 font-semibold flex items-center gap-1 mb-2"><Thermometer size={13} className="text-amber-500"/> Temperature (°F)</label>
                      <input
                        type="number" step="0.1" placeholder="e.g. 101.2"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-amber-300"
                        value={vitals.temperature}
                        onChange={e => setVitals(v => ({ ...v, temperature: e.target.value }))}
                      />
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-blue-100 shadow-sm">
                      <label className="text-xs text-slate-500 font-semibold flex items-center gap-1 mb-2"><Activity size={13} className="text-blue-500"/> Blood Pressure (mmHg)</label>
                      <input
                        type="text" placeholder="e.g. 120/80"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-blue-300"
                        value={vitals.blood_pressure}
                        onChange={e => setVitals(v => ({ ...v, blood_pressure: e.target.value }))}
                      />
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-cyan-100 shadow-sm">
                      <label className="text-xs text-slate-500 font-semibold flex items-center gap-1 mb-2"><Stethoscope size={13} className="text-cyan-500"/> O2 Saturation (%)</label>
                      <input
                        type="number" min="0" max="100" placeholder="e.g. 98"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-cyan-300"
                        value={vitals.oxygen_saturation}
                        onChange={e => setVitals(v => ({ ...v, oxygen_saturation: e.target.value }))}
                      />
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-purple-100 shadow-sm">
                      <label className="text-xs text-slate-500 font-semibold flex items-center gap-1 mb-2"><Activity size={13} className="text-purple-500"/> Respiratory Rate (/min)</label>
                      <input
                        type="number" placeholder="e.g. 16"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-purple-300"
                        value={vitals.respiratory_rate}
                        onChange={e => setVitals(v => ({ ...v, respiratory_rate: e.target.value }))}
                      />
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-green-100 shadow-sm">
                      <label className="text-xs text-slate-500 font-semibold flex items-center gap-1 mb-2"><Weight size={13} className="text-green-500"/> Weight (kg)</label>
                      <input
                        type="number" step="0.1" placeholder="e.g. 72.5"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-green-300"
                        value={vitals.weight_kg}
                        onChange={e => setVitals(v => ({ ...v, weight_kg: e.target.value }))}
                      />
                    </div>

                  </div>

                  <div className="flex justify-end">
                    <button
                      onClick={saveVitals}
                      disabled={savingVitals}
                      className="btn-primary py-2.5 px-6 flex items-center gap-2"
                    >
                      {savingVitals ? <Loader2 size={16} className="animate-spin"/> : <Save size={16}/>}
                      Save Vitals
                    </button>
                  </div>
                </div>
              )}

              {/* ─── LABS TAB ─── */}
              {activeTab === 'labs' && (
                <div className="space-y-5">
                  <h3 className="font-bold text-lg flex items-center gap-2"><FlaskConical size={18} className="text-violet-500"/> Lab Orders</h3>
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Test Name *</label>
                        <input
                          type="text" placeholder="e.g. Complete Blood Count"
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300"
                          value={newLab.test_name}
                          onChange={e => setNewLab(v => ({ ...v, test_name: e.target.value }))}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Urgency</label>
                        <select
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300"
                          value={newLab.urgency}
                          onChange={e => setNewLab(v => ({ ...v, urgency: e.target.value }))}
                        >
                          <option value="routine">Routine</option>
                          <option value="urgent">Urgent</option>
                          <option value="stat">STAT (Emergency)</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-slate-500 font-semibold mb-1 block">Clinical Notes</label>
                      <input
                        type="text" placeholder="Any specific instructions..."
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300"
                        value={newLab.notes}
                        onChange={e => setNewLab(v => ({ ...v, notes: e.target.value }))}
                      />
                    </div>
                    <div className="flex justify-end">
                      <button onClick={saveLabOrder} disabled={savingLab} className="btn-primary py-2 px-5 flex items-center gap-2">
                        {savingLab ? <Loader2 size={14} className="animate-spin"/> : <Plus size={14}/>} Add Lab Order
                      </button>
                    </div>
                  </div>
                  {labOrders.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-sm text-slate-600">Orders This Session:</h4>
                      {labOrders.map((lab, i) => (
                        <div key={i} className="flex items-center justify-between bg-violet-50 border border-violet-100 p-3 rounded-lg text-sm">
                          <span className="font-semibold text-violet-800">{lab.test_name}</span>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${lab.urgency === 'stat' ? 'bg-red-100 text-red-700' : lab.urgency === 'urgent' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'}`}>
                            {lab.urgency.toUpperCase()}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ─── MEDICATIONS TAB ─── */}
              {activeTab === 'medications' && (
                <div className="space-y-5">
                  <h3 className="font-bold text-lg flex items-center gap-2"><Pill size={18} className="text-emerald-500"/> Medication Orders</h3>
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Medication Name *</label>
                        <input
                          type="text" placeholder="e.g. Amoxicillin"
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-300"
                          value={newMed.medication_name}
                          onChange={e => setNewMed(v => ({ ...v, medication_name: e.target.value }))}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Dosage *</label>
                        <input
                          type="text" placeholder="e.g. 500mg"
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-300"
                          value={newMed.dosage}
                          onChange={e => setNewMed(v => ({ ...v, dosage: e.target.value }))}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Frequency</label>
                        <select
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-300"
                          value={newMed.frequency}
                          onChange={e => setNewMed(v => ({ ...v, frequency: e.target.value }))}
                        >
                          <option value="">Select frequency</option>
                          <option>Once daily</option>
                          <option>Twice daily</option>
                          <option>Three times daily</option>
                          <option>Four times daily</option>
                          <option>Every 6 hours</option>
                          <option>Every 8 hours</option>
                          <option>As needed (PRN)</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Route</label>
                        <select
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-300"
                          value={newMed.route}
                          onChange={e => setNewMed(v => ({ ...v, route: e.target.value }))}
                        >
                          <option value="oral">Oral (PO)</option>
                          <option value="iv">Intravenous (IV)</option>
                          <option value="im">Intramuscular (IM)</option>
                          <option value="sublingual">Sublingual (SL)</option>
                          <option value="topical">Topical</option>
                          <option value="inhalation">Inhalation</option>
                          <option value="rectal">Rectal (PR)</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-slate-500 font-semibold mb-1 block">Instructions / Notes</label>
                      <input
                        type="text" placeholder="e.g. Take with food, avoid alcohol..."
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-300"
                        value={newMed.notes}
                        onChange={e => setNewMed(v => ({ ...v, notes: e.target.value }))}
                      />
                    </div>
                    <div className="flex justify-end">
                      <button onClick={saveMedOrder} disabled={savingMed} className="btn-primary py-2 px-5 flex items-center gap-2">
                        {savingMed ? <Loader2 size={14} className="animate-spin"/> : <Plus size={14}/>} Add Medication
                      </button>
                    </div>
                  </div>
                  {/* CDSS Alerts Section */}
                  {cdssAlerts.length > 0 && (
                    <div className={`p-4 rounded-xl border animate-in slide-in-from-top-2 duration-300 ${cdssAlerts.some(a => a.severity === 'critical') ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'}`}>
                      <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle className={cdssAlerts.some(a => a.severity === 'critical') ? 'text-red-600' : 'text-amber-600'} size={20}/>
                        <h4 className={`font-bold ${cdssAlerts.some(a => a.severity === 'critical') ? 'text-red-800' : 'text-amber-800'}`}>
                          Clinical Safety Alerts ({cdssAlerts.length})
                        </h4>
                      </div>
                      <div className="space-y-3">
                        {cdssAlerts.map((alert, idx) => (
                          <div key={idx} className={`p-3 rounded-lg border flex flex-col gap-1.5 ${alert.severity === 'critical' ? 'bg-white border-red-100' : 'bg-white border-amber-100'}`}>
                            <div className="flex items-center justify-between">
                              <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${alert.severity === 'critical' ? 'bg-red-600 text-white' : 'bg-amber-500 text-white'}`}>
                                {alert.severity}
                              </span>
                              <span className="text-[10px] font-bold text-slate-400 capitalize">{alert.alert_type}</span>
                            </div>
                            <p className="text-sm font-semibold text-slate-800">{alert.message}</p>
                            {alert.recommended_action && (
                              <p className="text-xs text-slate-600 italic mt-1 bg-slate-50 p-2 rounded border-l-2 border-slate-300">
                                <span className="font-bold">Recommendation:</span> {alert.recommended_action}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                      {cdssAlerts.some(a => a.severity === 'critical') && (
                        <div className="mt-4 p-3 bg-red-600 text-white rounded-lg flex items-center gap-3">
                          <X size={20} className="shrink-0"/>
                          <p className="text-sm font-bold">This prescription is BLOCKED by clinical safety rules. Please follow recommendations above.</p>
                        </div>
                      )}
                    </div>
                  )}

                  {medOrders.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-sm text-slate-600">Prescriptions This Session:</h4>
                      {medOrders.map((med, i) => (
                        <div key={i} className="bg-emerald-50 border border-emerald-100 p-3 rounded-lg text-sm flex justify-between items-start">
                          <div>
                            <span className="font-bold text-emerald-800">{med.medication_name}</span>
                            <span className="text-emerald-600 ml-2">{med.dosage}</span>
                            <div className="text-xs text-slate-500 mt-0.5">{med.frequency} · {med.route}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ─── IMAGING TAB ─── */}
              {activeTab === 'imaging' && (
                <div className="space-y-5">
                  <h3 className="font-bold text-lg flex items-center gap-2"><ImagePlus size={18} className="text-sky-500"/> Imaging Orders</h3>
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Modality</label>
                        <select
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-300"
                          value={newImaging.modality}
                          onChange={e => setNewImaging(v => ({ ...v, modality: e.target.value }))}
                        >
                          <option>X-Ray</option>
                          <option>CT Scan</option>
                          <option>MRI</option>
                          <option>Ultrasound</option>
                          <option>PET Scan</option>
                          <option>Mammography</option>
                          <option>Fluoroscopy</option>
                          <option>Echocardiography</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Body Part / Region *</label>
                        <input
                          type="text" placeholder="e.g. Chest, Left Knee..."
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-300"
                          value={newImaging.body_part}
                          onChange={e => setNewImaging(v => ({ ...v, body_part: e.target.value }))}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Clinical Indication *</label>
                        <input
                          type="text" placeholder="e.g. Rule out pneumonia..."
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-300"
                          value={newImaging.clinical_indication}
                          onChange={e => setNewImaging(v => ({ ...v, clinical_indication: e.target.value }))}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 font-semibold mb-1 block">Urgency</label>
                        <select
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-300"
                          value={newImaging.urgency}
                          onChange={e => setNewImaging(v => ({ ...v, urgency: e.target.value }))}
                        >
                          <option value="routine">Routine</option>
                          <option value="urgent">Urgent</option>
                          <option value="stat">STAT (Emergency)</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <button onClick={saveImagingOrder} disabled={savingImaging} className="btn-primary py-2 px-5 flex items-center gap-2">
                        {savingImaging ? <Loader2 size={14} className="animate-spin"/> : <Plus size={14}/>} Add Imaging Order
                      </button>
                    </div>
                  </div>
                  {imagingOrders.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-sm text-slate-600">Imaging Orders This Session:</h4>
                      {imagingOrders.map((img, i) => (
                        <div key={i} className="bg-sky-50 border border-sky-100 p-3 rounded-lg text-sm">
                          <span className="font-bold text-sky-800">{img.modality}</span>
                          <span className="text-sky-600 ml-2">- {img.body_part}</span>
                          <div className="text-xs text-slate-500 mt-0.5">{img.clinical_indication}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ─── NOTES TAB ─── */}
              {activeTab === 'notes' && (
                <div className="space-y-6">
                  {/* Voice Input */}
                  <div className={`p-4 rounded-xl border-2 transition-all ${isRecording ? 'border-red-400 bg-red-50 shadow-[0_0_15px_rgba(239,68,68,0.2)]' : isTranslating ? 'border-blue-400 bg-blue-50' : 'border-[var(--border)] bg-white'}`}>
                    <div className="flex justify-between items-center mb-3">
                      <h3 className="font-bold flex items-center gap-2">
                        {isRecording ? <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"/> : <Mic size={18} className="text-[var(--text-secondary)]"/>}
                        Voice-Assisted Documentation
                        {isRecording && <span className="text-xs text-red-600 font-normal ml-1">Listening in any language...</span>}
                        {isTranslating && <span className="text-xs text-blue-600 font-normal ml-1 flex items-center gap-1"><Loader2 size={12} className="animate-spin"/>Translating to English...</span>}
                      </h3>
                      <button
                        onClick={toggleVoiceRecording}
                        disabled={isTranslating}
                        className={`px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-colors ${isRecording ? 'bg-red-500 text-white hover:bg-red-600' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'} disabled:opacity-50`}
                      >
                        {isRecording ? "Stop Recording" : "Start Dictation"}
                      </button>
                    </div>
                    {isRecording && rawTranscript && (
                      <div className="text-xs text-red-700 bg-red-100/50 rounded-lg p-2 mb-2 italic">
                        🎙 Heard: {rawTranscript}
                      </div>
                    )}
                    <textarea
                      className="w-full p-4 rounded-lg border border-slate-200 bg-slate-50 min-h-[120px] focus:ring-2 focus:ring-blue-500 outline-none text-lg"
                      placeholder="Click 'Start Dictation' and speak in any language — Hindi, Tamil, Marathi, Arabic, etc. It will be automatically transcribed and translated to English."
                      value={voiceText}
                      onChange={e => setVoiceText(e.target.value)}
                    />
                    <div className="flex justify-between items-center mt-3">
                      <span className="text-xs text-slate-400">Supports all languages → auto-translated to English</span>
                      <button onClick={saveNote} disabled={!voiceText || isRecording || isTranslating} className="btn-primary py-2 px-6 flex items-center gap-2">
                        <Save size={16}/> Save Note
                      </button>
                    </div>
                  </div>

                  {/* Notes History */}
                  <div>
                    <h3 className="font-bold mb-4 text-lg">Clinical Notes History</h3>
                    <div className="space-y-4">
                      {encounter.notes?.map((note: any) => (
                        <div key={note.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                          <div className="flex justify-between items-center mb-2">
                            <span className={`text-xs px-2 py-1 uppercase font-bold tracking-wider rounded ${
                              note.note_type === 'vitals_record' ? 'bg-rose-100 text-rose-700' :
                              note.note_type === 'lab_order' ? 'bg-violet-100 text-violet-700' :
                              note.note_type === 'medication_order' ? 'bg-emerald-100 text-emerald-700' :
                              note.note_type === 'imaging_order' ? 'bg-sky-100 text-sky-700' :
                              'bg-blue-50 text-blue-700'
                            }`}>
                              {note.note_type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-xs text-slate-500">{new Date(note.created_at).toLocaleString()}</span>
                          </div>
                          <p className="text-[var(--text-primary)] text-sm whitespace-pre-wrap font-mono">{note.content}</p>
                        </div>
                      ))}
                      {(!encounter.notes || encounter.notes.length === 0) && (
                        <p className="text-slate-500 text-center py-8">No clinical notes recorded yet.</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>

        {/* ─── Right Column: Timeline & Actions ─── */}
        <div className="w-[320px] bg-slate-50 border-l border-[var(--border)] flex flex-col p-4">
          <div className="mb-6 flex-1 overflow-hidden flex flex-col">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2"><Clock size={20} className="text-blue-600"/> Clinical Timeline</h3>
            <div className="flex-1 overflow-y-auto pr-2">
              <div className="space-y-4 relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-300 via-slate-200 to-transparent"></div>
                {encounter.timeline_events?.map((event: any) => (
                  <div key={event.id} className="relative flex items-start gap-3 pl-10">
                    <div className="absolute left-2 top-2 w-5 h-5 rounded-full bg-blue-100 border-2 border-blue-400 flex items-center justify-center z-10">
                      <FileSignature size={10} className="text-blue-600"/>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex-1 text-sm">
                      <div className="font-bold text-slate-800 text-xs uppercase tracking-wide">
                        {event.event_type.replace(/_/g, ' ')}
                      </div>
                      <div className="text-slate-500 text-xs mt-0.5">{new Date(event.event_time).toLocaleTimeString()}</div>
                      {event.description && <div className="text-slate-700 text-xs mt-1">{event.description}</div>}
                    </div>
                  </div>
                ))}
                {(!encounter.timeline_events || encounter.timeline_events.length === 0) && (
                  <p className="text-slate-400 text-sm text-center py-4 pl-10">No timeline events yet.</p>
                )}
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-sm mb-3 text-slate-800">Pending Actions</h3>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm p-2 hover:bg-slate-50 rounded cursor-pointer">
                <input type="checkbox" className="rounded text-blue-600"/> Review Vitals
              </label>
              <label className="flex items-center gap-2 text-sm p-2 hover:bg-slate-50 rounded cursor-pointer">
                <input type="checkbox" className="rounded text-blue-600"/> Add ICD-10 Diagnosis
              </label>
              <label className="flex items-center gap-2 text-sm p-2 hover:bg-slate-50 rounded cursor-pointer">
                <input type="checkbox" className="rounded text-blue-600"/> Review Lab Orders
              </label>
              <label className="flex items-center gap-2 text-sm p-2 hover:bg-slate-50 rounded cursor-pointer">
                <input type="checkbox" className="rounded text-blue-600"/> Prescribe Medications
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
