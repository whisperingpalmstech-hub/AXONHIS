"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "@/i18n";
import {
  UserPlus, AlertTriangle, Check, ArrowRight, ArrowLeft,
  Droplets, Activity, Weight, Heart, FileText, Phone, Mail, Shield,
  Mic, MicOff, Camera, CreditCard, Upload, Bell, MapPin, ScanLine,
  Sparkles, Globe, QrCode, Send, X, ChevronDown, Loader2, Brain,
  Eye, Fingerprint, Zap, Edit, UserCheck, Calendar
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
  const { t } = useTranslation();

  // ── Fix: Patch DOM methods to prevent browser-extension-induced React crashes ──
  useEffect(() => {
    const origRemoveChild = Node.prototype.removeChild;
    // @ts-ignore
    Node.prototype.removeChild = function <T extends Node>(child: T): T {
      if (child.parentNode !== this) {
        console.warn("[DOM Patch] removeChild: node is not a child — suppressed");
        return child;
      }
      return origRemoveChild.call(this, child) as T;
    };

    const origInsertBefore = Node.prototype.insertBefore;
    // @ts-ignore
    Node.prototype.insertBefore = function <T extends Node>(newNode: T, refNode: Node | null): T {
      if (refNode && refNode.parentNode !== this) {
        console.warn("[DOM Patch] insertBefore: ref node is not a child — suppressed");
        return newNode;
      }
      return origInsertBefore.call(this, newNode, refNode) as T;
    };

    return () => {
      Node.prototype.removeChild = origRemoveChild;
      Node.prototype.insertBefore = origInsertBefore;
    };
  }, []);

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
    address_line: "", pincode: "", area: "", city: "", state: "", country: t("patients.countryDefault"),
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
  const [facePhotoFile, setFacePhotoFile] = useState<File | null>(null);
  const [facePhotoPreview, setFacePhotoPreview] = useState<string | null>(null);
  const faceEnrollRef = useRef<HTMLInputElement>(null);

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
    const { name, value } = e.target;
    // Validate DOB: no future dates
    if (name === "date_of_birth" && value) {
      const selected = new Date(value);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (selected > today) {
        setError("Date of birth cannot be in the future.");
        return;
      }
    }
    // Validate emergency phone: only digits, max 10
    if (name === "emergency_contact_phone") {
      setFormData(prev => ({ ...prev, [name]: value.replace(/\D/g, '').substring(0, 10) }));
      return;
    }
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Today's date for max DOB constraint
  const todayStr = new Date().toISOString().split('T')[0];

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

  // ── AI Input Focus Fix ──
  const aiInputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (activeMode === "ai" && aiSession && aiInputRef.current) {
      aiInputRef.current.focus();
    }
  }, [aiSession?.current_step, activeMode]);

  const submitAIStep = async () => {
    if (!aiSession || !aiAnswer.trim()) return;
    const fieldMap = ["name", "dob", "gender", "mobile", "email", "reason_for_visit"];
    const fieldName = fieldMap[aiSession.current_step - 1] || "unknown";

    // Validate name: must have at least 2 characters
    if (fieldName === "name" && aiAnswer.trim().length < 2) {
      setError("Please enter at least a first name (minimum 2 characters).");
      return;
    }

    // Validate DOB: no future dates
    if (fieldName === "dob" && aiAnswer.trim().toLowerCase() !== "skip") {
      const dobDate = new Date(aiAnswer.trim());
      if (isNaN(dobDate.getTime())) {
        setError("Please enter a valid date (YYYY-MM-DD format).");
        return;
      }
      if (dobDate > new Date()) {
        setError("Date of birth cannot be in the future.");
        return;
      }
    }

    if (fieldName === "mobile" && aiAnswer.trim().toLowerCase() !== "skip") {
      const numericAnswer = aiAnswer.replace(/\D/g, '');
      if (numericAnswer.length !== 10) {
        setError("Please enter exactly 10 digits for the phone number.");
        return;
      }
    }

    // Validate email format
    if (fieldName === "email" && aiAnswer.trim().toLowerCase() !== "skip") {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(aiAnswer.trim())) {
        setError("Please enter a valid email address.");
        return;
      }
    }

    setAiLoading(true);
    setError("");
    try {
      const result = await registrationApi.aiStep(aiSession.id, fieldName, aiAnswer.trim());
      setAiSession(result);

      // Auto-populate form
      if (fieldName === "name") {
        const parts = aiAnswer.trim().split(/\s+/);
        const firstName = parts[0] || "";
        const lastName = parts.slice(1).join(" ") || firstName;
        setFormData(p => ({ ...p, first_name: firstName, last_name: lastName }));
      } else if (fieldName === "dob") {
        setFormData(p => ({ ...p, date_of_birth: aiAnswer.trim() }));
      } else if (fieldName === "gender") {
        setFormData(p => ({ ...p, gender: aiAnswer.trim() }));
      } else if (fieldName === "mobile") {
        setFormData(p => ({ ...p, primary_phone: aiAnswer.trim() }));
      } else if (fieldName === "email") {
        setFormData(p => ({ ...p, email: aiAnswer.trim() }));
      } else if (fieldName === "reason_for_visit") {
        setFormData(p => ({ ...p, reason_for_visit: aiAnswer.trim() }));
      }

      setAiAnswer("");
    } catch (e: any) {
      setError(e.message);
    }
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
  // Handle face photo for enrollment during registration
  const handleFaceEnroll = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFacePhotoFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setFacePhotoPreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // ── Strict Validations ──
    if (!formData.first_name.trim() || formData.first_name.trim().length < 2) {
      setError("First name must be at least 2 characters."); return;
    }
    if (!formData.last_name.trim() || formData.last_name.trim().length < 2) {
      setError("Last name must be at least 2 characters."); return;
    }
    if (!formData.date_of_birth) {
      setError("Date of birth is required."); return;
    }
    const dobDate = new Date(formData.date_of_birth);
    if (dobDate > new Date()) {
      setError("Date of birth cannot be in the future."); return;
    }
    if (dobDate.getFullYear() < 1900) {
      setError("Date of birth year must be 1900 or later."); return;
    }
    if (!formData.gender) {
      setError("Gender is required."); return;
    }
    if (!formData.primary_phone || formData.primary_phone.length !== 10) {
      setError("Phone number must be exactly 10 digits."); return;
    }
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError("Please enter a valid email address."); return;
    }
    if (formData.emergency_contact_phone && formData.emergency_contact_phone.length > 0 && formData.emergency_contact_phone.length !== 10) {
      setError("Emergency contact phone must be exactly 10 digits."); return;
    }

    // ── Strict Duplicate Blocking ──
    if (duplicateResult?.has_duplicates && duplicateResult.matches.some(m => m.confidence_score >= 90)) {
      setError("A patient with the same name and date of birth already exists. Duplicate registration is not allowed.");
      return;
    }
    if (duplicateResult?.has_duplicates && !window.confirm("A similar patient record was found. Are you absolutely sure this is a new patient?")) {
      return;
    }
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
      // Enroll face photo if captured
      if (facePhotoFile) {
        promises.push(registrationApi.faceEnroll(patient.id, facePhotoFile).catch(() => {}));
      }
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
    { id: "manual" as const, label: t("patients.modeManual"), icon: <UserPlus size={16} />, desc: t("patients.modeManualDesc") },
    { id: "ai" as const, label: t("patients.modeAI"), icon: <Brain size={16} />, desc: t("patients.modeAIDesc") },
    { id: "voice" as const, label: t("patients.modeVoice"), icon: <Mic size={16} />, desc: t("patients.modeVoiceDesc") },
    { id: "id_scan" as const, label: t("patients.modeIDScan"), icon: <ScanLine size={16} />, desc: t("patients.modeIDScanDesc") },
    { id: "face" as const, label: t("patients.modeFace"), icon: <Fingerprint size={16} />, desc: t("patients.modeFaceDesc") },
  ];

  const steps = [
    { num: 1, label: t("patients.demographics"), icon: <UserPlus size={16} /> },
    { num: 2, label: t("patients.medicalInfo"), icon: <Heart size={16} /> },
    { num: 3, label: t("patients.identityVerification"), icon: <Shield size={16} /> },
    { num: 4, label: t("patients.consentNotification"), icon: <Bell size={16} /> },
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
          {t("patients.registration")}
        </h1>
        <p className="text-[var(--text-secondary)] mt-2 text-sm">
          {t("patients.registrationSub")}
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
                  <QrCode size={16} /> {t("patients.healthCardReady")}
                </div>
                <p className="text-xs text-green-600 mb-1">{t("patients.uhid")}: <strong>{healthCard.uhid}</strong></p>
                <p className="text-xs text-green-600">{t("patients.cardNumber")}: <strong>{healthCard.card_number}</strong></p>
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
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => createdPatientId && router.push(`/dashboard/patients/${createdPatientId}`)}
              className="btn-secondary flex items-center gap-2"
            >
              <ArrowLeft size={16} /> View Patient Profile
            </button>
            <button
              onClick={() => createdPatientId && router.push(`/dashboard/scheduling?patient_id=${createdPatientId}`)}
              className="btn-primary flex items-center gap-2"
            >
              <Calendar size={16} /> Book Appointment <ArrowRight size={16} />
            </button>
          </div>
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
                  <div className="space-y-6" translate="no">
                    {/* 1. Progress Bar (Always Present) */}
                    <div className="px-1">
                      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-full transition-all duration-700 ease-out"
                          style={{ width: `${(aiSession.current_step / aiSession.total_steps) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* 2. Collected Data Area (Stable Container) */}
                    <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 min-h-[40px]">
                      {Object.keys(aiSession.collected_data).length === 0 ? (
                        <p className="text-xs text-slate-400 italic">Information will appear here as you answer...</p>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {Object.entries(aiSession.collected_data).map(([k, v]) => (
                            <div key={`cdata-${k}`} className="flex items-center gap-2 bg-white p-2 rounded-lg border border-slate-100 text-sm shadow-sm group">
                              <div className="w-5 h-5 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-500 flex-shrink-0">
                                <Check size={12} />
                              </div>
                              <div className="truncate flex-1">
                                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-bold">{k.replace(/_/g, " ")}</span>
                                <span className="font-semibold text-slate-700">{String(v)}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* 3. Main Action Area */}
                    <div className="relative min-h-[160px]">
                      {aiSession.next_question ? (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                          <div className="bg-white border-2 border-indigo-50 rounded-2xl p-6 shadow-sm">
                            <h3 className="text-indigo-900 font-bold text-lg flex items-center gap-3">
                              <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600"><Sparkles size={20} /></div>
                              {aiSession.next_question}
                            </h3>
                          </div>

                          <div className="flex flex-col md:flex-row gap-3">
                            <input
                              ref={aiInputRef}
                              key={`ai-input-${aiSession.current_step}`}
                              value={aiAnswer}
                              onChange={e => setAiAnswer(e.target.value)}
                              onKeyDown={e => e.key === "Enter" && submitAIStep()}
                              className="input-field flex-1 py-4 px-6 text-lg"
                              placeholder="Type your answer..."
                              autoComplete="off"
                            />
                            <div className="flex gap-2">
                              <button onClick={() => { setAiAnswer("skip"); submitAIStep(); }} type="button" disabled={aiLoading} className="btn-secondary px-6">
                                Skip
                              </button>
                              <button
                                onClick={submitAIStep}
                                type="button"
                                disabled={aiLoading}
                                className="btn-primary px-8 flex items-center gap-2"
                              >
                                {aiLoading ? <Loader2 size={20} className="animate-spin" /> : <ArrowRight size={20} />}
                                Next
                              </button>
                            </div>
                          </div>

                          <button
                            onClick={() => setAiSession(prev => prev ? { ...prev, current_step: Math.max(1, prev.current_step - 1) } : prev)}
                            type="button"
                            disabled={aiLoading || aiSession.current_step <= 1}
                            className={`text-slate-400 hover:text-indigo-600 text-sm font-bold flex items-center gap-2 transition-colors ${aiSession.current_step <= 1 ? "invisible" : "visible"}`}
                          >
                            <ArrowLeft size={16} /> Go back
                          </button>
                        </div>
                      ) : aiSession.status === "pending_review" ? (
                        <div className="bg-indigo-900 text-white rounded-3xl p-10 text-center shadow-2xl animate-in zoom-in-95">
                          <Check size={40} className="mx-auto mb-4" />
                          <h2 className="text-2xl font-black mb-2">Information Complete</h2>
                          <button onClick={completeAISession} disabled={aiLoading} className="w-full py-4 bg-white text-indigo-900 rounded-2xl font-black text-lg mt-6 shadow-xl flex items-center justify-center gap-3">
                            {aiLoading ? <Loader2 size={24} className="animate-spin text-indigo-600" /> : <UserCheck size={24} />}
                            COMPLETE REGISTRATION
                          </button>
                        </div>
                      ) : null}
                    </div>
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
                      <h2 className="text-lg font-semibold">{t("patients.demographics")}</h2>
                    </div>
                    <div className="card-body grid grid-cols-2 gap-4">
                      <div><label className="input-label">{t("patients.firstName")} *</label><input name="first_name" className="input-field" required minLength={2} value={formData.first_name} onChange={handleChange} placeholder="Min 2 characters" /></div>
                      <div><label className="input-label">{t("patients.lastName")} *</label><input name="last_name" className="input-field" required minLength={2} value={formData.last_name} onChange={handleChange} placeholder="Min 2 characters" /></div>
                      <div>
                        <label className="input-label">{t("patients.dateOfBirth")} *</label>
                        <input type="date" name="date_of_birth" className="input-field" required value={formData.date_of_birth} onChange={handleChange} max={todayStr} min="1900-01-01" />
                        {formData.date_of_birth && new Date(formData.date_of_birth) > new Date() && (
                          <p className="text-red-500 text-xs mt-1">⚠ Date of birth cannot be in the future</p>
                        )}
                      </div>
                      <div>
                        <label className="input-label">{t("patients.gender")} *</label>
                        <select name="gender" className="input-field" value={formData.gender} onChange={handleChange} required>
                          <option value="">{t("patients.selectGender")}</option>
                          <option value="Male">{t("patients.male")}</option>
                          <option value="Female">{t("patients.female")}</option>
                          <option value="Other">{t("patients.other")}</option>
                        </select>
                      </div>
                      <div>
                        <label className="input-label flex items-center gap-1"><Phone size={13} /> {t("patients.phone")} *</label>
                        <input type="tel" pattern="^[0-9]{10}$" title="Enter exactly 10 digits for the phone number" name="primary_phone" className="input-field" required value={formData.primary_phone} onChange={(e) => setFormData({...formData, primary_phone: e.target.value.replace(/\D/g, '').substring(0, 10)})} placeholder="9876543210" minLength={10} maxLength={10} />
                        {formData.primary_phone && formData.primary_phone.length > 0 && formData.primary_phone.length < 10 && (
                          <p className="text-amber-500 text-xs mt-1">{formData.primary_phone.length}/10 digits entered</p>
                        )}
                      </div>
                      <div><label className="input-label flex items-center gap-1"><Mail size={13} /> {t("patients.email")}</label><input type="email" name="email" className="input-field" value={formData.email} onChange={handleChange} placeholder="patient@example.com" /></div>
                      <div><label className="input-label">{t("patients.emergencyContact")}</label><input name="emergency_contact_name" className="input-field" value={formData.emergency_contact_name} onChange={handleChange} /></div>
                      <div>
                        <label className="input-label">{t("patients.emergencyPhone")}</label>
                        <input type="tel" pattern="^[0-9]{10}$" title="Enter exactly 10 digits" name="emergency_contact_phone" className="input-field" value={formData.emergency_contact_phone} onChange={handleChange} maxLength={10} placeholder="10-digit number" />
                        {formData.emergency_contact_phone && formData.emergency_contact_phone.length > 0 && formData.emergency_contact_phone.length < 10 && (
                          <p className="text-amber-500 text-xs mt-1">{formData.emergency_contact_phone.length}/10 digits</p>
                        )}
                      </div>
                      {/* Face Photo Capture for Registration */}
                      <div className="col-span-2">
                        <label className="input-label flex items-center gap-1"><Camera size={13} /> Face Photo (for future check-in)</label>
                        <input ref={faceEnrollRef} type="file" className="hidden" accept="image/*" capture="user" onChange={handleFaceEnroll} />
                        <div className="flex items-center gap-3">
                          <button type="button" onClick={() => faceEnrollRef.current?.click()} className="btn-secondary text-sm flex items-center gap-2 py-2">
                            <Camera size={14} /> {facePhotoPreview ? "Change Photo" : "Capture Face Photo"}
                          </button>
                          {facePhotoPreview && (
                            <div className="flex items-center gap-2">
                              <img src={facePhotoPreview} alt="Face" className="w-12 h-12 rounded-full object-cover border-2 border-green-400" />
                              <span className="text-xs text-green-600 flex items-center gap-1"><Check size={12} /> Photo captured</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="card-body border-t border-[var(--border)] flex justify-end gap-3">
                      <button type="submit" className="btn-secondary flex items-center gap-2 border-green-200 text-green-700 hover:bg-green-50"><Check size={16} /> Register Now</button>
                      <button type="button" onClick={() => setActiveStep(2)} className="btn-primary flex items-center gap-2">{t("common.next")} <ArrowRight size={16} /></button>
                    </div>
                  </div>
                )}

                {/* ── STEP 2: Medical & Address ── */}
                {activeStep === 2 && (
                  <div className="space-y-6">
                    <div className="card">
                      <div className="card-header border-b border-[var(--border)] flex items-center gap-2">
                        <Heart size={18} className="text-rose-500" />
                        <h2 className="text-lg font-semibold">{t("patients.medicalInfo")}</h2>
                      </div>
                      <div className="card-body grid grid-cols-2 gap-4">
                        <div>
                          <label className="input-label">{t("patients.bloodGroup")}</label>
                          <select name="blood_group" className="input-field" value={formData.blood_group} onChange={handleChange}>
                            <option value="">Unknown</option>
                            {["A+","A-","B+","B-","AB+","AB-","O+","O-"].map(b => <option key={b} value={b}>{b}</option>)}
                          </select>
                        </div>
                        <div><label className="input-label">Weight (kg)</label><input type="number" step="0.1" name="weight_kg" className="input-field" value={formData.weight_kg} onChange={handleChange} /></div>
                        <div><label className="input-label">Height (cm)</label><input type="number" name="height_cm" className="input-field" value={formData.height_cm} onChange={handleChange} /></div>
                        <div><label className="input-label">{t("patients.allergies")}</label><input name="allergies" className="input-field" value={formData.allergies} onChange={handleChange} placeholder="Penicillin, Sulfa..." /></div>
                        <div className="col-span-2"><label className="input-label">{t("patients.chiefComplaint")}</label><textarea name="chief_complaint" className="input-field min-h-[70px] resize-none" value={formData.chief_complaint} onChange={handleChange} /></div>
                        <div className="col-span-2"><label className="input-label">{t("patients.reasonForVisit")}</label><input name="reason_for_visit" className="input-field" value={formData.reason_for_visit} onChange={handleChange} placeholder="Routine checkup, Follow-up..." /></div>
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
                        <div className="col-span-2"><label className="input-label">{t("patients.address")}</label><input name="address_line" className="input-field" value={formData.address_line} onChange={handleChange} /></div>
                        <div>
                          <label className="input-label flex items-center gap-1"><Zap size={12} className="text-amber-500" /> Pincode (auto-fill)</label>
                          <input name="pincode" className="input-field" value={formData.pincode} onChange={handleChange} placeholder="Enter 6-digit pincode" maxLength={10} />
                        </div>
                        <div><label className="input-label">{t("patients.area")}</label><input name="area" className="input-field bg-slate-50" value={formData.area} onChange={handleChange} /></div>
                        <div><label className="input-label">{t("patients.city")}</label><input name="city" className="input-field bg-slate-50" value={formData.city} onChange={handleChange} /></div>
                        <div><label className="input-label">{t("patients.state")}</label><input name="state" className="input-field bg-slate-50" value={formData.state} onChange={handleChange} /></div>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <button type="button" onClick={() => setActiveStep(1)} className="btn-secondary flex items-center gap-2"><ArrowLeft size={16} /> {t("common.back")}</button>
                      <div className="flex gap-3">
                        <button type="submit" className="btn-secondary flex items-center gap-2 border-green-200 text-green-700 hover:bg-green-50"><Check size={16} /> Register Now</button>
                        <button type="button" onClick={() => setActiveStep(3)} className="btn-primary flex items-center gap-2">{t("common.next")} <ArrowRight size={16} /></button>
                      </div>
                    </div>
                  </div>
                )}

                {/* ── STEP 3: Identity & Insurance ── */}
                {activeStep === 3 && (
                  <div className="space-y-6">
                    <div className="card">
                      <div className="card-header border-b border-[var(--border)] flex items-center gap-2"><Shield size={18} className="text-[var(--accent-primary)]" /><h2 className="text-lg font-semibold">{t("patients.identityVerification")}</h2></div>
                      <div className="card-body grid grid-cols-2 gap-4">
                        <div>
                          <label className="input-label">{t("patients.idType")}</label>
                          <select name="identifier_type" className="input-field" value={formData.identifier_type} onChange={handleChange}>
                            <option value="national_id">Aadhaar</option><option value="passport">Passport</option><option value="driving_license">Driving License</option>
                          </select>
                        </div>
                        <div><label className="input-label">{t("patients.idNumber")}</label><input name="identifier_value" className="input-field" value={formData.identifier_value} onChange={handleChange} /></div>
                      </div>
                    </div>
                    <div className="card">
                      <div className="card-header border-b border-[var(--border)]"><h2 className="text-lg font-semibold">{t("patients.insurance")}</h2></div>
                      <div className="card-body grid grid-cols-2 gap-4">
                        <div><label className="input-label">Provider</label><input name="insurance_provider" className="input-field" value={formData.insurance_provider} onChange={handleChange} /></div>
                        <div><label className="input-label">{t("patients.policyNumber")}</label><input name="policy_number" className="input-field" value={formData.policy_number} onChange={handleChange} /></div>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <button type="button" onClick={() => setActiveStep(2)} className="btn-secondary flex items-center gap-2"><ArrowLeft size={16} /> {t("common.back")}</button>
                      <button type="button" onClick={() => setActiveStep(4)} className="btn-primary flex items-center gap-2">{t("common.next")} <ArrowRight size={16} /></button>
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
                      <button type="button" onClick={() => setActiveStep(3)} className="btn-secondary flex items-center gap-2"><ArrowLeft size={16} /> {t("common.back")}</button>
                      <button
                        type="submit"
                        className="btn-primary flex items-center gap-2 px-8"
                        disabled={loading || success || (duplicateResult?.matches?.some(d => d.confidence_score >= 90) ?? false)}
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
                      {duplicateResult.matches.slice(0, 3).map((m) => (
                        <div key={m.patient_id} className="bg-white border border-amber-200 rounded-lg p-3 text-sm shadow-sm">
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
