"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  UserPlus, AlertTriangle, Check, ArrowRight, ArrowLeft,
  Droplets, Activity, Weight, Heart, FileText, Phone, Mail, Shield,
  Mic, MicOff, Camera, CreditCard, Upload, Bell, MapPin, ScanLine,
  Sparkles, Globe, QrCode, Send, X, ChevronDown, Loader2, Brain,
  Eye, Fingerprint, Zap
} from "lucide-react";
import {
  registrationApi,
  type AIRegistrationSession,
  type VoiceRegistrationResult,
  type IDScanResult,
  type FaceCheckInResult,
  type DuplicateCheckResult,
  type AddressLookupResult,
  type HealthCardResult,
} from "@/lib/registration-api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

/* ═══════════════════════════════════════════════════════════════════════════
   ENTERPRISE PATIENT REGISTRATION – 10 OPD FRD FEATURES
   ═══════════════════════════════════════════════════════════════════════════ */

export default function EnterpriseRegistrationPage() {
  const router = useRouter();

  // ── Core form state ──
  const [formData, setFormData] = useState({
    first_name: "", last_name: "", date_of_birth: "", gender: "",
    primary_phone: "", email: "",
    blood_group: "", weight_kg: "", height_cm: "",
    allergies: "", chronic_conditions: "", current_medications: "",
    chief_complaint: "", family_history: "",
    identifier_type: "national_id", identifier_value: "",
    insurance_provider: "", policy_number: "",
    emergency_contact_name: "", emergency_contact_phone: "",
    consent_type: "treatment_consent",
    address_line: "", pincode: "", area: "", city: "", state: "", country: "India",
    reason_for_visit: "",
  });

  // ── UI state ──
  const [activeStep, setActiveStep] = useState(1);
  const [activeMode, setActiveMode] = useState<"manual" | "ai" | "voice" | "id_scan" | "face">("manual");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [createdPatientId, setCreatedPatientId] = useState<string | null>(null);

  // ── Feature 1: AI Registration ──
  const [aiSession, setAiSession] = useState<AIRegistrationSession | null>(null);
  const [aiAnswer, setAiAnswer] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  // ── Feature 2: Voice Registration ──
  const [isListening, setIsListening] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [voiceResult, setVoiceResult] = useState<VoiceRegistrationResult | null>(null);
  const [voiceLanguage, setVoiceLanguage] = useState("en");

  // ── Feature 3: ID Scan ──
  const [idScanResult, setIdScanResult] = useState<IDScanResult | null>(null);
  const [idDocType, setIdDocType] = useState("aadhaar");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Feature 4: Face Recognition ──
  const [faceResult, setFaceResult] = useState<FaceCheckInResult | null>(null);
  const faceInputRef = useRef<HTMLInputElement>(null);

  // ── Feature 5: Duplicate Detection ──
  const [duplicateResult, setDuplicateResult] = useState<DuplicateCheckResult | null>(null);

  // ── Feature 6: Address Auto-Population ──
  const [addressLoading, setAddressLoading] = useState(false);

  // ── Feature 8: Health Card ──
  const [healthCard, setHealthCard] = useState<HealthCardResult | null>(null);

  // ── Feature 9: Document Upload ──
  const [uploadedDocs, setUploadedDocs] = useState<any[]>([]);
  const docInputRef = useRef<HTMLInputElement>(null);

  // ── Feature 10: Notification ──
  const [notifChannels, setNotifChannels] = useState({ sms: true, email: true, whatsapp: false });
  const [notifSent, setNotifSent] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // Feature 5: Auto Duplicate Detection
  // ═══════════════════════════════════════════════════════════════════════════
  useEffect(() => {
    if (formData.first_name.length > 2 && formData.last_name.length > 2 && formData.date_of_birth) {
      const timer = setTimeout(async () => {
        try {
          const result = await registrationApi.checkDuplicates({
            first_name: formData.first_name,
            last_name: formData.last_name,
            date_of_birth: formData.date_of_birth,
            mobile: formData.primary_phone || undefined,
            email: formData.email || undefined,
            address: formData.address_line || undefined,
          });
          setDuplicateResult(result);
        } catch { setDuplicateResult(null); }
      }, 900);
      return () => clearTimeout(timer);
    } else { setDuplicateResult(null); }
  }, [formData.first_name, formData.last_name, formData.date_of_birth, formData.primary_phone]);

  // ═══════════════════════════════════════════════════════════════════════════
  // Feature 6: Address auto-population on pincode change
  // ═══════════════════════════════════════════════════════════════════════════
  useEffect(() => {
    if (formData.pincode.length >= 5) {
      const timer = setTimeout(async () => {
        setAddressLoading(true);
        try {
          const result = await registrationApi.addressLookup(formData.pincode);
          setFormData(prev => ({
            ...prev,
            area: result.area || prev.area,
            city: result.city || prev.city,
            state: result.state || prev.state,
            country: result.country || prev.country,
          }));
        } catch {}
        setAddressLoading(false);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [formData.pincode]);

  // ═══════════════════════════════════════════════════════════════════════════
  // Feature 1: AI-Assisted Registration
  // ═══════════════════════════════════════════════════════════════════════════
  const startAISession = async () => {
    setAiLoading(true);
    try {
      const session = await registrationApi.aiStart(voiceLanguage);
      setAiSession(session);
      setActiveMode("ai");
    } catch (e: any) { setError(e.message); }
    setAiLoading(false);
  };

  const submitAIStep = async () => {
    if (!aiSession || !aiAnswer.trim()) return;
    setAiLoading(true);
    const fieldMap = ["name", "dob", "gender", "mobile", "email", "reason_for_visit"];
    const fieldName = fieldMap[aiSession.current_step - 1] || "unknown";
    try {
      const result = await registrationApi.aiStep(aiSession.id, fieldName, aiAnswer.trim());
      setAiSession(result);
      setAiAnswer("");
      // Auto-populate form
      if (fieldName === "name") {
        const parts = aiAnswer.trim().split(/\s+/);
        setFormData(p => ({ ...p, first_name: parts[0] || "", last_name: parts.slice(1).join(" ") || "" }));
      } else if (fieldName === "dob") setFormData(p => ({ ...p, date_of_birth: aiAnswer.trim() }));
      else if (fieldName === "gender") setFormData(p => ({ ...p, gender: aiAnswer.trim() }));
      else if (fieldName === "mobile") setFormData(p => ({ ...p, primary_phone: aiAnswer.trim() }));
      else if (fieldName === "email") setFormData(p => ({ ...p, email: aiAnswer.trim() }));
      else if (fieldName === "reason_for_visit") setFormData(p => ({ ...p, reason_for_visit: aiAnswer.trim() }));
    } catch (e: any) { setError(e.message); }
    setAiLoading(false);
  };

  const completeAISession = async () => {
    if (!aiSession) return;
    setAiLoading(true);
    try {
      const result = await registrationApi.aiComplete(aiSession.id);
      setAiSession(result);
      if (result.patient_id) {
        setCreatedPatientId(result.patient_id);
        setSuccess(true);
      }
    } catch (e: any) { setError(e.message); }
    setAiLoading(false);
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // Feature 2: Voice Registration
  // ═══════════════════════════════════════════════════════════════════════════
  const startVoice = () => {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      setError("Voice recognition not supported in this browser.");
      return;
    }
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    const recog = new SpeechRecognition();
    recog.lang = voiceLanguage === "hi" ? "hi-IN" : voiceLanguage === "mr" ? "mr-IN" : "en-US";
    recog.continuous = false;
    recog.interimResults = false;
    recog.onresult = async (event: any) => {
      const text = event.results[0][0].transcript;
      setVoiceTranscript(text);
      setIsListening(false);
      try {
        const result = await registrationApi.voiceCommand(text, voiceLanguage);
        setVoiceResult(result);
      } catch (e: any) { setError(e.message); }
    };
    recog.onerror = () => setIsListening(false);
    recog.onend = () => setIsListening(false);
    setIsListening(true);
    recog.start();
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // Feature 3: ID Scan
  // ═══════════════════════════════════════════════════════════════════════════
  const handleIDScan = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    try {
      const result = await registrationApi.idScanExtract(file, idDocType);
      setIdScanResult(result);
      // Auto-fill form from extracted data
      if (result.extracted_name) {
        const parts = result.extracted_name.split(/\s+/);
        setFormData(p => ({ ...p, first_name: parts[0] || p.first_name, last_name: parts.slice(1).join(" ") || p.last_name }));
      }
      if (result.extracted_dob) setFormData(p => ({ ...p, date_of_birth: result.extracted_dob! }));
      if (result.extracted_gender) setFormData(p => ({ ...p, gender: result.extracted_gender! }));
      if (result.extracted_id_number) setFormData(p => ({ ...p, identifier_value: result.extracted_id_number! }));
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // Feature 4: Face Check-In
  // ═══════════════════════════════════════════════════════════════════════════
  const handleFaceCheckIn = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    try {
      const result = await registrationApi.faceCheckIn(file);
      setFaceResult(result);
      if (result.matched && result.patient_id) {
        setTimeout(() => router.push(`/dashboard/patients/${result.patient_id}`), 2000);
      }
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // Main form submit (manual mode)
  // ═══════════════════════════════════════════════════════════════════════════
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const patientRes = await fetch(`${API}/api/v1/patients/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("access_token")}` },
        body: JSON.stringify({
          first_name: formData.first_name, last_name: formData.last_name,
          date_of_birth: formData.date_of_birth, gender: formData.gender,
          primary_phone: formData.primary_phone || undefined,
          email: formData.email || undefined,
        }),
      });
      if (!patientRes.ok) {
        const err = await patientRes.json();
        throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
      }
      const patient = await patientRes.json();
      setCreatedPatientId(patient.id);

      // Parallel: identifiers, insurance, consent, UHID, health card, notifications
      const promises: Promise<any>[] = [];
      if (formData.identifier_value) {
        promises.push(fetch(`${API}/api/v1/patients/${patient.id}/identifiers/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("access_token")}` },
          body: JSON.stringify({ identifier_type: formData.identifier_type, identifier_value: formData.identifier_value }),
        }));
      }
      if (formData.insurance_provider) {
        promises.push(fetch(`${API}/api/v1/patients/${patient.id}/insurance/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("access_token")}` },
          body: JSON.stringify({ insurance_provider: formData.insurance_provider, policy_number: formData.policy_number || null }),
        }));
      }
      // Generate UHID
      promises.push(registrationApi.generateUHID(patient.id).catch(() => {}));
      // Generate Health Card
      promises.push(
        registrationApi.generateHealthCard(patient.id).then(card => setHealthCard(card)).catch(() => {})
      );
      // Send Notifications
      const channels = Object.entries(notifChannels).filter(([, v]) => v).map(([k]) => k);
      if (channels.length > 0) {
        promises.push(registrationApi.sendNotifications(patient.id, channels).then(() => setNotifSent(true)).catch(() => {}));
      }
      await Promise.allSettled(promises);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally { setLoading(false); }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // Feature 9: Document Upload (post-registration)
  // ═══════════════════════════════════════════════════════════════════════════
  const handleDocUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !createdPatientId) return;
    try {
      const doc = await registrationApi.uploadDocument(createdPatientId, "id_proof", file, "Uploaded during registration");
      setUploadedDocs(prev => [...prev, doc]);
    } catch (e: any) { setError(e.message); }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // Registration mode selector buttons
  // ═══════════════════════════════════════════════════════════════════════════
  const modes = [
    { id: "manual" as const, label: "Manual", icon: <UserPlus size={16} />, desc: "Step-by-step form" },
    { id: "ai" as const, label: "AI Guided", icon: <Brain size={16} />, desc: "AI asks questions" },
    { id: "voice" as const, label: "Voice", icon: <Mic size={16} />, desc: "Voice commands" },
    { id: "id_scan" as const, label: "ID Scan", icon: <ScanLine size={16} />, desc: "OCR document scan" },
    { id: "face" as const, label: "Face Check-in", icon: <Fingerprint size={16} />, desc: "Biometric" },
  ];

  const steps = [
    { num: 1, label: "Demographics", icon: <UserPlus size={16} /> },
    { num: 2, label: "Medical & Address", icon: <Heart size={16} /> },
    { num: 3, label: "Identity & Insurance", icon: <Shield size={16} /> },
    { num: 4, label: "Notifications", icon: <Bell size={16} /> },
  ];

  // ═══════════════════════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════════════════════
  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] flex items-center gap-3">
          <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2.5 rounded-xl text-white shadow-lg">
            <UserPlus size={24} />
          </div>
          Enterprise Patient Registration
        </h1>
        <p className="text-[var(--text-secondary)] mt-2 text-sm">
          AI-powered smart registration with OCR, voice commands, face recognition, and duplicate detection.
        </p>
      </div>

      {/* Registration Mode Selector */}
      <div className="flex flex-wrap gap-2 mb-6">
        {modes.map(m => (
          <button
            key={m.id}
            onClick={() => { setActiveMode(m.id); if (m.id === "ai" && !aiSession) startAISession(); }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all border ${
              activeMode === m.id
                ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white border-transparent shadow-lg shadow-blue-500/25"
                : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-slate-100 hover:border-blue-300"
            }`}
          >
            {m.icon} {m.label}
            <span className={`text-[10px] font-normal ${activeMode === m.id ? "text-blue-100" : "text-slate-400"}`}>
              {m.desc}
            </span>
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 mb-4 bg-red-50 text-red-600 rounded-xl text-sm font-medium border border-red-200 flex items-center gap-2">
          <AlertTriangle size={16} /> {error}
          <button onClick={() => setError("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}

      {/* Success State */}
      {success && (
        <div className="p-6 mb-6 bg-gradient-to-r from-green-50 to-emerald-50 text-green-800 rounded-2xl border border-green-200 shadow-lg shadow-green-500/10">
          <div className="flex items-center gap-4 mb-4">
            <div className="bg-green-100 p-3 rounded-full"><Check size={28} className="text-green-600" /></div>
            <div>
              <h3 className="font-bold text-xl">Registration Successful!</h3>
              <p className="text-sm text-green-600">Patient record created with UHID. Health card generated.</p>
            </div>
          </div>
          {/* Post-registration actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
            {/* Health Card */}
            {healthCard && (
              <div className="bg-white rounded-xl p-4 border border-green-200">
                <div className="flex items-center gap-2 mb-2 text-sm font-bold text-green-800">
                  <QrCode size={16} /> Health Card Ready
                </div>
                <p className="text-xs text-green-600 mb-1">UHID: <strong>{healthCard.uhid}</strong></p>
                <p className="text-xs text-green-600">Card: <strong>{healthCard.card_number}</strong></p>
                {healthCard.qr_code_data && (
                  <img src={`data:image/png;base64,${healthCard.qr_code_data}`} alt="QR" className="w-24 h-24 mt-2 mx-auto" />
                )}
              </div>
            )}
            {/* Document Upload */}
            <div className="bg-white rounded-xl p-4 border border-green-200">
              <div className="flex items-center gap-2 mb-2 text-sm font-bold text-green-800">
                <Upload size={16} /> Upload Documents
              </div>
              <input ref={docInputRef} type="file" className="hidden" accept="image/*,.pdf" onChange={handleDocUpload} />
              <button onClick={() => docInputRef.current?.click()} className="btn-secondary text-xs w-full">
                Upload ID / Medical Doc
              </button>
              {uploadedDocs.map(d => (
                <p key={d.id} className="text-[10px] text-green-600 mt-1">✓ {d.original_name}</p>
              ))}
            </div>
            {/* Notifications */}
            <div className="bg-white rounded-xl p-4 border border-green-200">
              <div className="flex items-center gap-2 mb-2 text-sm font-bold text-green-800">
                <Bell size={16} /> Notifications
              </div>
              {notifSent ? (
                <p className="text-xs text-green-600">✓ Confirmation sent via selected channels</p>
              ) : (
                <p className="text-xs text-slate-500">Notifications will be sent on registration</p>
              )}
            </div>
          </div>
          <button
            onClick={() => createdPatientId && router.push(`/dashboard/patients/${createdPatientId}`)}
            className="btn-primary mt-4 flex items-center gap-2"
          >
            View Patient Profile <ArrowRight size={16} />
          </button>
        </div>
      )}

      <div className="flex flex-col xl:flex-row gap-6">
        {/* ── Main Content Area ── */}
        <div className="flex-1">
          {/* ═════════ AI GUIDED MODE ═════════ */}
          {activeMode === "ai" && (
            <div className="card overflow-hidden">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 text-white flex items-center gap-3">
                <Brain size={22} />
                <div>
                  <h2 className="font-bold text-lg">AI-Guided Registration</h2>
                  <p className="text-blue-100 text-xs">The AI assistant will guide you through each question</p>
                </div>
                {aiSession && (
                  <span className="ml-auto bg-white/20 px-3 py-1 rounded-full text-xs font-semibold">
                    Step {aiSession.current_step} / {aiSession.total_steps}
                  </span>
                )}
              </div>
              <div className="p-6">
                {aiSession ? (
                  <div className="space-y-4">
                    {/* Progress bar */}
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all"
                        style={{ width: `${(aiSession.current_step / aiSession.total_steps) * 100}%` }}
                      />
                    </div>
                    {/* Collected data */}
                    {Object.keys(aiSession.collected_data).length > 0 && (
                      <div className="bg-slate-50 rounded-xl p-3 space-y-1">
                        {Object.entries(aiSession.collected_data).map(([k, v]) => (
                          <div key={k} className="flex items-center gap-2 text-sm">
                            <Check size={14} className="text-green-500" />
                            <span className="text-slate-500 capitalize">{k.replace(/_/g, " ")}:</span>
                            <strong>{v}</strong>
                          </div>
                        ))}
                      </div>
                    )}
                    {/* Current question */}
                    {aiSession.next_question ? (
                      <>
                        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                          <p className="text-blue-800 font-medium flex items-center gap-2">
                            <Sparkles size={16} className="text-purple-500" />
                            {aiSession.next_question}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <input
                            value={aiAnswer}
                            onChange={e => setAiAnswer(e.target.value)}
                            onKeyDown={e => e.key === "Enter" && submitAIStep()}
                            className="input-field flex-1"
                            placeholder="Type your answer..."
                            autoFocus
                          />
                          <button onClick={submitAIStep} disabled={aiLoading} className="btn-primary flex items-center gap-2">
                            {aiLoading ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
                            Next
                          </button>
                        </div>
                      </>
                    ) : aiSession.status === "pending_review" ? (
                      <div className="text-center space-y-3">
                        <p className="text-green-700 font-semibold">✅ All questions answered! Review and complete registration.</p>
                        <button onClick={completeAISession} disabled={aiLoading} className="btn-primary mx-auto flex items-center gap-2">
                          {aiLoading ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
                          Complete Registration
                        </button>
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Brain size={48} className="text-purple-300 mx-auto mb-4" />
                    <p className="text-slate-500 mb-4">Click "AI Guided" mode to start the AI-assisted registration flow</p>
                    <button onClick={startAISession} disabled={aiLoading} className="btn-primary flex items-center gap-2 mx-auto">
                      {aiLoading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                      Start AI Registration
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ═════════ VOICE MODE ═════════ */}
          {activeMode === "voice" && (
            <div className="card overflow-hidden">
              <div className="bg-gradient-to-r from-emerald-500 to-teal-600 p-4 text-white flex items-center gap-3">
                <Mic size={22} />
                <div>
                  <h2 className="font-bold text-lg">Voice-Enabled Registration</h2>
                  <p className="text-emerald-100 text-xs">Speak commands: &quot;Register new patient&quot;, &quot;Search by mobile&quot;</p>
                </div>
              </div>
              <div className="p-6 space-y-4">
                {/* Language selector */}
                <div className="flex items-center gap-3">
                  <Globe size={16} className="text-slate-500" />
                  <select value={voiceLanguage} onChange={e => setVoiceLanguage(e.target.value)} className="input-field w-auto">
                    <option value="en">English</option>
                    <option value="hi">हिन्दी (Hindi)</option>
                    <option value="mr">मराठी (Marathi)</option>
                  </select>
                </div>
                {/* Mic button */}
                <div className="flex flex-col items-center py-6">
                  <button
                    onClick={startVoice}
                    disabled={isListening}
                    className={`w-24 h-24 rounded-full flex items-center justify-center transition-all ${
                      isListening
                        ? "bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/30"
                        : "bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-500/20"
                    }`}
                  >
                    {isListening ? <MicOff size={36} /> : <Mic size={36} />}
                  </button>
                  <p className="mt-3 text-sm text-slate-500">
                    {isListening ? "Listening..." : "Tap to speak"}
                  </p>
                </div>
                {voiceTranscript && (
                  <div className="bg-slate-50 rounded-xl p-4 border">
                    <p className="text-sm text-slate-500 mb-1">Transcript:</p>
                    <p className="font-medium">&quot;{voiceTranscript}&quot;</p>
                  </div>
                )}
                {voiceResult && (
                  <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
                    <p className="font-semibold text-emerald-800">Intent: <span className="capitalize">{voiceResult.intent.replace(/_/g, " ")}</span></p>
                    <p className="text-sm text-emerald-600 mt-1">Confidence: {(voiceResult.confidence * 100).toFixed(0)}%</p>
                    {voiceResult.action_taken && <p className="text-sm text-slate-600 mt-1">{voiceResult.action_taken}</p>}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ═════════ ID SCAN MODE ═════════ */}
          {activeMode === "id_scan" && (
            <div className="card overflow-hidden">
              <div className="bg-gradient-to-r from-amber-500 to-orange-600 p-4 text-white flex items-center gap-3">
                <ScanLine size={22} />
                <div>
                  <h2 className="font-bold text-lg">ID Scan Registration (OCR)</h2>
                  <p className="text-amber-100 text-xs">Upload an ID document → AI extracts name, DOB, gender, ID number</p>
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex items-center gap-3">
                  <label className="input-label mb-0">Document Type:</label>
                  <select value={idDocType} onChange={e => setIdDocType(e.target.value)} className="input-field w-auto">
                    <option value="aadhaar">Aadhaar Card</option>
                    <option value="passport">Passport</option>
                    <option value="national_id">National ID</option>
                    <option value="driving_license">Driving License</option>
                  </select>
                </div>
                <input ref={fileInputRef} type="file" className="hidden" accept="image/*" onChange={handleIDScan} />
                <button onClick={() => fileInputRef.current?.click()} disabled={loading} className="w-full border-2 border-dashed border-amber-300 rounded-xl py-12 flex flex-col items-center gap-3 hover:bg-amber-50 transition-colors">
                  {loading ? <Loader2 size={40} className="text-amber-500 animate-spin" /> : <ScanLine size={40} className="text-amber-400" />}
                  <span className="text-slate-600 font-medium">{loading ? "Scanning..." : "Click to upload ID document"}</span>
                  <span className="text-xs text-slate-400">Supports: JPG, PNG, PDF</span>
                </button>
                {idScanResult && (
                  <div className="bg-amber-50 rounded-xl p-4 border border-amber-200 space-y-2">
                    <h3 className="font-bold text-amber-800 flex items-center gap-2"><Check size={16} /> Extraction Results</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div><span className="text-slate-500">Name:</span> <strong>{idScanResult.extracted_name || "—"}</strong></div>
                      <div><span className="text-slate-500">DOB:</span> <strong>{idScanResult.extracted_dob || "—"}</strong></div>
                      <div><span className="text-slate-500">Gender:</span> <strong>{idScanResult.extracted_gender || "—"}</strong></div>
                      <div><span className="text-slate-500">ID Number:</span> <strong>{idScanResult.extracted_id_number || "—"}</strong></div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-amber-600">
                      <Zap size={12} /> Confidence: {(idScanResult.extraction_confidence * 100).toFixed(0)}%
                    </div>
                    <button onClick={() => setActiveMode("manual")} className="btn-primary text-sm mt-2 flex items-center gap-2">
                      Continue with Form <ArrowRight size={14} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ═════════ FACE RECOGNITION MODE ═════════ */}
          {activeMode === "face" && (
            <div className="card overflow-hidden">
              <div className="bg-gradient-to-r from-pink-500 to-rose-600 p-4 text-white flex items-center gap-3">
                <Fingerprint size={22} />
                <div>
                  <h2 className="font-bold text-lg">Face Recognition Check-in</h2>
                  <p className="text-pink-100 text-xs">Identify a returning patient by face photo</p>
                </div>
              </div>
              <div className="p-6 space-y-4">
                <input ref={faceInputRef} type="file" className="hidden" accept="image/*" capture="user" onChange={handleFaceCheckIn} />
                <button onClick={() => faceInputRef.current?.click()} disabled={loading} className="w-full border-2 border-dashed border-pink-300 rounded-xl py-12 flex flex-col items-center gap-3 hover:bg-pink-50 transition-colors">
                  {loading ? <Loader2 size={40} className="text-pink-500 animate-spin" /> : <Camera size={40} className="text-pink-400" />}
                  <span className="text-slate-600 font-medium">{loading ? "Identifying..." : "Take/Upload Face Photo"}</span>
                </button>
                {faceResult && (
                  <div className={`rounded-xl p-4 border ${faceResult.matched ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
                    {faceResult.matched ? (
                      <>
                        <h3 className="font-bold text-green-800 flex items-center gap-2"><Check size={16} /> Patient Identified!</h3>
                        <p className="text-sm mt-1">Name: <strong>{faceResult.patient_name}</strong></p>
                        <p className="text-sm">UHID: <strong>{faceResult.uhid}</strong></p>
                        <p className="text-xs text-green-600 mt-1">Confidence: {(faceResult.confidence * 100).toFixed(1)}%</p>
                        <p className="text-xs text-green-600 mt-2">Redirecting to patient profile...</p>
                      </>
                    ) : (
                      <>
                        <h3 className="font-bold text-red-800 flex items-center gap-2"><X size={16} /> No Match Found</h3>
                        <p className="text-sm text-red-600 mt-1">{faceResult.message}</p>
                        <button onClick={() => setActiveMode("manual")} className="btn-primary text-sm mt-3">
                          Register Manually
                        </button>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ═════════ MANUAL FORM MODE ═════════ */}
          {activeMode === "manual" && !success && (
            <>
              {/* Step Indicator */}
              <div className="flex items-center gap-0 mb-6">
                {steps.map((step, idx) => (
                  <React.Fragment key={step.num}>
                    <button
                      onClick={() => setActiveStep(step.num)}
                      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-semibold text-sm transition-all ${
                        activeStep === step.num
                          ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md"
                          : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-slate-200"
                      }`}
                    >
                      {step.icon} {step.label}
                    </button>
                    {idx < steps.length - 1 && <div className="flex-1 h-0.5 bg-slate-200 mx-1" />}
                  </React.Fragment>
                ))}
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* ── STEP 1: Demographics ── */}
                {activeStep === 1 && (
                  <div className="card">
                    <div className="card-header border-b border-[var(--border)] flex items-center gap-2">
                      <UserPlus size={18} className="text-[var(--accent-primary)]" />
                      <h2 className="text-lg font-semibold">Patient Demographics</h2>
                    </div>
                    <div className="card-body grid grid-cols-2 gap-4">
                      <div><label className="input-label">First Name *</label><input name="first_name" className="input-field" required value={formData.first_name} onChange={handleChange} /></div>
                      <div><label className="input-label">Last Name *</label><input name="last_name" className="input-field" required value={formData.last_name} onChange={handleChange} /></div>
                      <div><label className="input-label">Date of Birth *</label><input type="date" name="date_of_birth" className="input-field" required value={formData.date_of_birth} onChange={handleChange} /></div>
                      <div>
                        <label className="input-label">Gender *</label>
                        <select name="gender" className="input-field" value={formData.gender} onChange={handleChange} required>
                          <option value="">Select gender</option>
                          <option value="Male">Male</option>
                          <option value="Female">Female</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                      <div><label className="input-label flex items-center gap-1"><Phone size={13} /> Phone *</label><input type="tel" name="primary_phone" className="input-field" value={formData.primary_phone} onChange={handleChange} placeholder="+91 98765 43210" /></div>
                      <div><label className="input-label flex items-center gap-1"><Mail size={13} /> Email</label><input type="email" name="email" className="input-field" value={formData.email} onChange={handleChange} placeholder="patient@example.com" /></div>
                      <div><label className="input-label">Emergency Contact</label><input name="emergency_contact_name" className="input-field" value={formData.emergency_contact_name} onChange={handleChange} /></div>
                      <div><label className="input-label">Emergency Phone</label><input type="tel" name="emergency_contact_phone" className="input-field" value={formData.emergency_contact_phone} onChange={handleChange} /></div>
                    </div>
                    <div className="card-body border-t border-[var(--border)] flex justify-end">
                      <button type="button" onClick={() => setActiveStep(2)} className="btn-primary flex items-center gap-2">Next <ArrowRight size={16} /></button>
                    </div>
                  </div>
                )}

                {/* ── STEP 2: Medical & Address ── */}
                {activeStep === 2 && (
                  <div className="space-y-6">
                    <div className="card">
                      <div className="card-header border-b border-[var(--border)] flex items-center gap-2">
                        <Heart size={18} className="text-rose-500" />
                        <h2 className="text-lg font-semibold">Medical Information</h2>
                      </div>
                      <div className="card-body grid grid-cols-2 gap-4">
                        <div>
                          <label className="input-label">Blood Group</label>
                          <select name="blood_group" className="input-field" value={formData.blood_group} onChange={handleChange}>
                            <option value="">Unknown</option>
                            {["A+","A-","B+","B-","AB+","AB-","O+","O-"].map(b => <option key={b} value={b}>{b}</option>)}
                          </select>
                        </div>
                        <div><label className="input-label">Weight (kg)</label><input type="number" step="0.1" name="weight_kg" className="input-field" value={formData.weight_kg} onChange={handleChange} /></div>
                        <div><label className="input-label">Height (cm)</label><input type="number" name="height_cm" className="input-field" value={formData.height_cm} onChange={handleChange} /></div>
                        <div><label className="input-label">Allergies</label><input name="allergies" className="input-field" value={formData.allergies} onChange={handleChange} placeholder="Penicillin, Sulfa..." /></div>
                        <div className="col-span-2"><label className="input-label">Chief Complaint</label><textarea name="chief_complaint" className="input-field min-h-[70px] resize-none" value={formData.chief_complaint} onChange={handleChange} /></div>
                        <div className="col-span-2"><label className="input-label">Reason for Visit</label><input name="reason_for_visit" className="input-field" value={formData.reason_for_visit} onChange={handleChange} placeholder="Routine checkup, Follow-up..." /></div>
                      </div>
                    </div>
                    {/* Address with auto-fill */}
                    <div className="card">
                      <div className="card-header border-b border-[var(--border)] flex items-center gap-2">
                        <MapPin size={18} className="text-blue-500" />
                        <h2 className="text-lg font-semibold">Address (Auto-Fill by Pincode)</h2>
                        {addressLoading && <Loader2 size={14} className="animate-spin text-blue-500" />}
                      </div>
                      <div className="card-body grid grid-cols-2 gap-4">
                        <div className="col-span-2"><label className="input-label">Address Line</label><input name="address_line" className="input-field" value={formData.address_line} onChange={handleChange} /></div>
                        <div>
                          <label className="input-label flex items-center gap-1"><Zap size={12} className="text-amber-500" /> Pincode (auto-fill)</label>
                          <input name="pincode" className="input-field" value={formData.pincode} onChange={handleChange} placeholder="Enter 6-digit pincode" maxLength={10} />
                        </div>
                        <div><label className="input-label">Area</label><input name="area" className="input-field bg-slate-50" value={formData.area} onChange={handleChange} /></div>
                        <div><label className="input-label">City</label><input name="city" className="input-field bg-slate-50" value={formData.city} onChange={handleChange} /></div>
                        <div><label className="input-label">State</label><input name="state" className="input-field bg-slate-50" value={formData.state} onChange={handleChange} /></div>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <button type="button" onClick={() => setActiveStep(1)} className="btn-secondary flex items-center gap-2"><ArrowLeft size={16} /> Back</button>
                      <button type="button" onClick={() => setActiveStep(3)} className="btn-primary flex items-center gap-2">Next <ArrowRight size={16} /></button>
                    </div>
                  </div>
                )}

                {/* ── STEP 3: Identity & Insurance ── */}
                {activeStep === 3 && (
                  <div className="space-y-6">
                    <div className="card">
                      <div className="card-header border-b border-[var(--border)] flex items-center gap-2"><Shield size={18} className="text-[var(--accent-primary)]" /><h2 className="text-lg font-semibold">Identity Verification</h2></div>
                      <div className="card-body grid grid-cols-2 gap-4">
                        <div>
                          <label className="input-label">ID Type</label>
                          <select name="identifier_type" className="input-field" value={formData.identifier_type} onChange={handleChange}>
                            <option value="national_id">Aadhaar</option><option value="passport">Passport</option><option value="driving_license">Driving License</option>
                          </select>
                        </div>
                        <div><label className="input-label">Document Number</label><input name="identifier_value" className="input-field" value={formData.identifier_value} onChange={handleChange} /></div>
                      </div>
                    </div>
                    <div className="card">
                      <div className="card-header border-b border-[var(--border)]"><h2 className="text-lg font-semibold">Insurance</h2></div>
                      <div className="card-body grid grid-cols-2 gap-4">
                        <div><label className="input-label">Provider</label><input name="insurance_provider" className="input-field" value={formData.insurance_provider} onChange={handleChange} /></div>
                        <div><label className="input-label">Policy Number</label><input name="policy_number" className="input-field" value={formData.policy_number} onChange={handleChange} /></div>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <button type="button" onClick={() => setActiveStep(2)} className="btn-secondary flex items-center gap-2"><ArrowLeft size={16} /> Back</button>
                      <button type="button" onClick={() => setActiveStep(4)} className="btn-primary flex items-center gap-2">Next <ArrowRight size={16} /></button>
                    </div>
                  </div>
                )}

                {/* ── STEP 4: Notifications & Submit ── */}
                {activeStep === 4 && (
                  <div className="space-y-6">
                    <div className="card">
                      <div className="card-header border-b border-[var(--border)] flex items-center gap-2"><Bell size={18} className="text-purple-500" /><h2 className="text-lg font-semibold">Registration Notifications</h2></div>
                      <div className="card-body space-y-3">
                        <p className="text-sm text-slate-500">Send registration confirmation via:</p>
                        {[
                          { key: "sms", label: "SMS", icon: <Phone size={14} /> },
                          { key: "email", label: "Email", icon: <Mail size={14} /> },
                          { key: "whatsapp", label: "WhatsApp", icon: <Send size={14} /> },
                        ].map(ch => (
                          <label key={ch.key} className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border)] hover:bg-slate-50 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={(notifChannels as any)[ch.key]}
                              onChange={e => setNotifChannels(p => ({ ...p, [ch.key]: e.target.checked }))}
                              className="w-4 h-4 accent-purple-600"
                            />
                            {ch.icon}
                            <span className="font-medium text-sm">{ch.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <button type="button" onClick={() => setActiveStep(3)} className="btn-secondary flex items-center gap-2"><ArrowLeft size={16} /> Back</button>
                      <button
                        type="submit"
                        className="btn-primary flex items-center gap-2 px-8"
                        disabled={loading || success || (duplicateResult?.matches?.some(d => d.confidence_score > 80) ?? false)}
                      >
                        {loading ? <Loader2 size={18} className="animate-spin" /> : <Check size={18} />}
                        {loading ? "Processing..." : "Complete Registration"}
                      </button>
                    </div>
                  </div>
                )}
              </form>
            </>
          )}
        </div>

        {/* ── Sidebar: Duplicate Detection + Medical Summary ── */}
        {(activeMode === "manual" || activeMode === "ai") && !success && (
          <div className="w-full xl:w-[360px]">
            <div className="sticky top-6 space-y-4">
              {/* AI Duplicate Detection Panel */}
              <div className={`card overflow-hidden transition-all duration-300 ${
                duplicateResult?.has_duplicates
                  ? "border-amber-300 ring-4 ring-amber-500/10 shadow-lg shadow-amber-500/10"
                  : ""
              }`}>
                <div className={`p-4 font-bold flex items-center gap-2 text-sm ${
                  duplicateResult?.has_duplicates
                    ? "bg-amber-100 text-amber-900 border-b border-amber-200"
                    : "bg-[var(--bg-secondary)] text-[var(--text-secondary)]"
                }`}>
                  <AlertTriangle size={18} className={duplicateResult?.has_duplicates ? "text-amber-500 animate-pulse" : ""} />
                  AI Duplicate Detection
                </div>
                <div className="p-4">
                  {!duplicateResult || !duplicateResult.has_duplicates ? (
                    <p className="text-sm text-[var(--text-secondary)]">No duplicates detected. Fill demographics to trigger AI matching.</p>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-sm font-medium text-amber-800">{duplicateResult.ai_recommendation}</p>
                      {duplicateResult.matches.slice(0, 3).map((m, i) => (
                        <div key={i} className="bg-white border border-amber-200 rounded-lg p-3 text-sm shadow-sm">
                          <div className="flex justify-between items-start mb-1">
                            <strong>{m.first_name} {m.last_name}</strong>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${m.confidence_score >= 70 ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>
                              {m.confidence_score}%
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 space-y-0.5">
                            <div>DOB: {m.date_of_birth}</div>
                            <div>Phone: {m.primary_phone || "N/A"}</div>
                            <div>UHID: {m.patient_uuid}</div>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {m.match_reasons.map((r, ri) => (
                                <span key={ri} className="bg-amber-50 text-amber-700 text-[9px] px-1.5 py-0.5 rounded">{r}</span>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Medical Summary */}
              {(formData.blood_group || formData.allergies || formData.chief_complaint) && (
                <div className="card overflow-hidden">
                  <div className="p-3 font-bold bg-blue-50 text-blue-800 border-b border-blue-100 text-sm flex items-center gap-2">
                    <Heart size={14} /> Medical Summary
                  </div>
                  <div className="p-3 space-y-1.5 text-xs">
                    {formData.blood_group && <div className="flex items-center gap-2"><Droplets size={11} className="text-red-500" /> Blood: <strong>{formData.blood_group}</strong></div>}
                    {formData.allergies && <div className="flex items-center gap-2"><AlertTriangle size={11} className="text-amber-500" /> Allergies: <strong className="text-red-700">{formData.allergies}</strong></div>}
                    {formData.chief_complaint && <div className="flex items-center gap-2"><FileText size={11} className="text-blue-500" /> Complaint: <span>{formData.chief_complaint.slice(0, 60)}...</span></div>}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
