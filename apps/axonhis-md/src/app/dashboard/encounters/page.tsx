"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function EncountersPage() {
  const router = useRouter();
  const [encounters, setEncounters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<any>(null);
  const [notes, setNotes] = useState<any[]>([]);
  const [diagnoses, setDiagnoses] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [meds, setMeds] = useState<any[]>([]);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [showDiagModal, setShowDiagModal] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [showRxModal, setShowRxModal] = useState(false);
  const [noteForm, setNoteForm] = useState<any>({ note_type: "HISTORY" });
  const [diagForm, setDiagForm] = useState<any>({ diagnosis_type: "PRIMARY", source_type: "CLINICIAN" });
  const [orderForm, setOrderForm] = useState<any>({ request_type: "LAB", priority: "ROUTINE" });
  const [rxForm, setRxForm] = useState<any>({ route: "ORAL" });
  
  // Clinical Encounter Flow
  const [flowId, setFlowId] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState<string>("COMPLAINT_CAPTURE");
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
  const [turnId, setTurnId] = useState<string | null>(null);
  const [turnNumber, setTurnNumber] = useState(0);
  const [shouldMoveToExam, setShouldMoveToExam] = useState(false);
  const [examinationGuidance, setExaminationGuidance] = useState<any>(null);
  const [managementPlan, setManagementPlan] = useState<any>(null);
  
  // Voice and AI features
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [aiQuestions, setAiQuestions] = useState<string[]>([]);
  const [showAiPanel, setShowAiPanel] = useState(true);
  const [encounterMode, setEncounterMode] = useState<"MANUAL" | "AI_GUIDED" | "AI_DRIVEN">("MANUAL");
  const [aiSuggestions, setAiSuggestions] = useState<any>({ diagnoses: [], tests: [], medications: [], advice: [] });
  
  // Examination findings
  const [examinationFindings, setExaminationFindings] = useState("");
  const [aiExamSuggestions, setAiExamSuggestions] = useState<string[]>([]);
  
  // Prompt configuration
  const [showPromptConfig, setShowPromptConfig] = useState(false);
  const [promptTemplate, setPromptTemplate] = useState("");
  
  // Document generation
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [documentTitle, setDocumentTitle] = useState("");
  const [documentContent, setDocumentContent] = useState("");
  
  // Encounter completion
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [shareWithEmail, setShareWithEmail] = useState("");
  
  // AI workflow automation
  const [isRunningAiWorkflow, setIsRunningAiWorkflow] = useState(false);
  const [aiWorkflowResults, setAiWorkflowResults] = useState<any>(null);
  const [workflowType, setWorkflowType] = useState<"FULL_AUTOMATION" | "QUESTIONING_ONLY" | "MANAGEMENT_ONLY">("FULL_AUTOMATION");

  const load = useCallback(async () => {
    try { const data = await apiFetch("/encounters"); setEncounters(data); } catch { setEncounters([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const loadDetails = async (enc: any) => {
    setSelected(enc);
    const eid = enc.encounter_id;
    try { setNotes(await apiFetch(`/encounters/${eid}/notes`)); } catch { setNotes([]); }
    try { setDiagnoses(await apiFetch(`/encounters/${eid}/diagnoses`)); } catch { setDiagnoses([]); }
    try { setOrders(await apiFetch(`/encounters/${eid}/service-requests`)); } catch { setOrders([]); }
    try { setMeds(await apiFetch(`/encounters/${eid}/medications`)); } catch { setMeds([]); }
  };

  // Voice capture using Web Audio API
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: any[] = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.wav');
        
        try {
          const response = await fetch(`${API}/api/v1/md/voice/transcribe`, {
            method: 'POST',
            headers: authHeaders(),
            body: formData
          });
          const data = await response.json();
          setTranscript(data.transcript);
          
          // Get AI suggestions based on transcript
          if (selected) {
            const params = new URLSearchParams({
              encounter_id: selected.encounter_id,
              transcript: data.transcript
            });
            const questionsRes = await fetch(`${API}/api/v1/md/ai/suggest-questions?${params}`, {
              method: 'POST',
              headers: authHeaders()
            });
            const questionsData = await questionsRes.json();
            setAiQuestions(questionsData.questions);
          }
        } catch (e) {
          console.error('Transcription failed:', e);
        }
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      
      // Store recorder to stop it later
      (window as any).mediaRecorder = mediaRecorder;
    } catch (e) {
      alert('Microphone access denied or not available');
    }
  };

  const stopRecording = () => {
    if ((window as any).mediaRecorder && (window as any).mediaRecorder.state !== 'inactive') {
      (window as any).mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const handleRecordingToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const getAiSuggestions = async () => {
    if (!selected) return;
    try {
      const params = new URLSearchParams({ encounter_id: selected.encounter_id });
      const response = await fetch(`${API}/api/v1/md/ai/suggest-management?${params}`, {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await response.json();
      setAiSuggestions(data);
    } catch (e) {
      console.error('Failed to get AI suggestions:', e);
    }
  };

  const getExamAiSuggestions = async () => {
    if (!selected || !examinationFindings) return;
    try {
      const params = new URLSearchParams({
        encounter_id: selected.encounter_id,
        findings: examinationFindings
      });
      const response = await fetch(`${API}/api/v1/md/ai/suggest-exam?${params}`, {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await response.json();
      setAiExamSuggestions(data.suggestions || []);
    } catch (e) {
      console.error('Failed to get exam AI suggestions:', e);
    }
  };

  const savePromptTemplate = async () => {
    if (!selected) return;
    try {
      const params = new URLSearchParams({
        encounter_id: selected.encounter_id,
        prompt_template: promptTemplate
      });
      await fetch(`${API}/api/v1/md/encounter-templates?${params}`, {
        method: 'POST',
        headers: authHeaders()
      });
      setShowPromptConfig(false);
      alert('Prompt template saved successfully');
    } catch (e) {
      alert('Error saving prompt template: ' + e);
    }
  };

  const generateDocument = async () => {
    if (!selected) return;
    try {
      const params = new URLSearchParams({ title: documentTitle });
      const response = await fetch(`${API}/api/v1/md/encounters/${selected.encounter_id}/generate-document?${params}`, {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await response.json();
      setDocumentContent(data.content);
      setShowDocumentModal(true);
    } catch (e) {
      alert('Error generating document: ' + e);
    }
  };

  const runAiWorkflow = async () => {
    if (!selected) return;
    setIsRunningAiWorkflow(true);
    try {
      const params = new URLSearchParams({
        workflow_type: workflowType,
        auto_execute: 'false'
      });
      const response = await fetch(`${API}/api/v1/md/encounters/${selected.encounter_id}/ai-workflow?${params}`, {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await response.json();
      setAiWorkflowResults(data);
      
      // Update UI with AI suggestions if available
      if (data.steps) {
        const questionsStep = data.steps.find((s: any) => s.step === 'generate_questions');
        if (questionsStep && questionsStep.success) {
          setAiQuestions(questionsStep.data.questions || []);
        }
        
        const mgmtStep = data.steps.find((s: any) => s.step === 'generate_management_plan');
        if (mgmtStep && mgmtStep.success) {
          setAiSuggestions(mgmtStep.data);
        }
      }
      
      // Reload encounter details to see any new data
      await loadDetails(selected);
    } catch (e) {
      alert('Error running AI workflow: ' + e);
    } finally {
      setIsRunningAiWorkflow(false);
    }
  };

  const completeEncounter = async () => {
    if (!selected) return;
    try {
      await apiPost(`/encounters/${selected.encounter_id}/complete`, {
        share_with_email: shareWithEmail
      });
      setShowCompletionModal(false);
      load();
      alert('Encounter completed successfully');
      setSelected(null);
    } catch (e) {
      alert('Error completing encounter: ' + e);
    }
  };

  // Clinical Encounter Flow Functions
  const startClinicalFlow = async () => {
    if (!selected) return;
    try {
      const response = await fetch(`${API}/api/v1/clinical-encounter-flow/start`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          encounter_id: selected.encounter_id,
          patient_id: selected.patient_id,
          clinician_id: selected.clinician_id
        })
      });
      const data = await response.json();
      setFlowId(data.flow_id);
      setCurrentPhase(data.current_phase);
      alert('Clinical encounter flow started');
    } catch (e) {
      alert('Error starting clinical flow: ' + e);
    }
  };

  const submitComplaint = async () => {
    if (!flowId || !transcript) return;
    try {
      const response = await fetch(`${API}/api/v1/clinical-encounter-flow/flow/${flowId}/complaint`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          flow_id: flowId,
          complaint_transcript: transcript,
          language: 'en'
        })
      });
      const data = await response.json();
      setCurrentPhase(data.current_phase);
      setTranscript('');
    } catch (e) {
      alert('Error submitting complaint: ' + e);
    }
  };

  const getNextQuestion = async () => {
    if (!flowId || !selected) return;
    try {
      const response = await fetch(`${API}/api/v1/clinical-encounter-flow/flow/${flowId}/next-question?encounter_id=${selected.encounter_id}`, {
        method: 'GET',
        headers: authHeaders()
      });
      const data = await response.json();
      setCurrentQuestion(data.question);
      setTurnId(data.turn_id);
      setTurnNumber(data.turn_number);
      setShouldMoveToExam(data.should_move_to_examination || false);
    } catch (e) {
      alert('Error getting next question: ' + e);
    }
  };

  const submitAnswer = async () => {
    if (!flowId || !transcript || !selected || !turnId) return;
    try {
      const response = await fetch(`${API}/api/v1/clinical-encounter-flow/flow/${flowId}/answer?turn_id=${turnId}`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          flow_id: flowId,
          encounter_id: selected.encounter_id,
          answer_transcript: transcript,
          language: 'en'
        })
      });
      const data = await response.json();
      setTranscript('');
      await getNextQuestion();
    } catch (e) {
      alert('Error submitting answer: ' + e);
    }
  };

  const generateExaminationGuidance = async () => {
    if (!flowId || !selected) return;
    try {
      const response = await fetch(`${API}/api/v1/clinical-encounter-flow/flow/${flowId}/examination/guidance?encounter_id=${selected.encounter_id}`, {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await response.json();
      setExaminationGuidance(data);
      setCurrentPhase('EXAMINATION');
    } catch (e) {
      alert('Error generating examination guidance: ' + e);
    }
  };

  const submitExaminationFindings = async () => {
    if (!flowId || !examinationFindings) return;
    try {
      const response = await fetch(`${API}/api/v1/clinical-encounter-flow/flow/${flowId}/examination/findings`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          flow_id: flowId,
          examination_transcript: examinationFindings,
          language: 'en'
        })
      });
      const data = await response.json();
      setExaminationGuidance(data);
    } catch (e) {
      alert('Error submitting examination findings: ' + e);
    }
  };

  const generateManagementPlan = async () => {
    if (!flowId || !selected) return;
    try {
      const response = await fetch(`${API}/api/v1/clinical-encounter-flow/flow/${flowId}/management-plan?encounter_id=${selected.encounter_id}`, {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await response.json();
      setManagementPlan(data);
      setCurrentPhase('MANAGEMENT_PLANNING');
    } catch (e) {
      alert('Error generating management plan: ' + e);
    }
  };

  const generateDocuments = async () => {
    if (!flowId || !selected) return;
    try {
      const response = await fetch(`${API}/api/v1/clinical-encounter-flow/flow/${flowId}/documents/generate`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          flow_id: flowId,
          encounter_id: selected.encounter_id,
          document_types: ['clinic_letter', 'prescription', 'lab_orders']
        })
      });
      const data = await response.json();
      setCurrentPhase('COMPLETED');
      alert('Documents generated successfully');
    } catch (e) {
      alert('Error generating documents: ' + e);
    }
  };

  const addNote = async () => {
    try { await apiPost("/notes", { ...noteForm, encounter_id: selected.encounter_id }); setShowNoteModal(false); setNoteForm({ note_type: "HISTORY" }); loadDetails(selected); } catch(e) { alert("Error: " + e); }
  };
  const addDiag = async () => {
    try { await apiPost("/diagnoses", { ...diagForm, encounter_id: selected.encounter_id }); setShowDiagModal(false); setDiagForm({ diagnosis_type: "PRIMARY", source_type: "CLINICIAN" }); loadDetails(selected); } catch(e) { alert("Error: " + e); }
  };
  const addOrder = async () => {
    try { await apiPost("/service-requests", { ...orderForm, encounter_id: selected.encounter_id }); setShowOrderModal(false); setOrderForm({ request_type: "LAB", priority: "ROUTINE" }); loadDetails(selected); } catch(e) { alert("Error: " + e); }
  };
  const addRx = async () => {
    try { await apiPost("/medications", { ...rxForm, encounter_id: selected.encounter_id }); setShowRxModal(false); setRxForm({ route: "ORAL" }); loadDetails(selected); } catch(e) { alert("Error: " + e); }
  };

  const statusColors: Record<string,string> = { OPEN: "badge-warning", IN_PROGRESS: "badge-warning", COMPLETED: "badge-success", CANCELLED: "badge-error" };
  const filtered = encounters.filter(e => !filter || e.encounter_status === filter);

  // Encounter workspace view
  if (selected) {
    return (<div><TopNav title="Encounter Workspace" />
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <button onClick={() => setSelected(null)} className="flex items-center gap-2 text-sm text-teal-600 hover:text-teal-800 transition">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/></svg>Back to Encounters</button>
          <button className="flex items-center gap-2 text-sm px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition" onClick={() => router.push(`/dashboard/billing?encounter_id=${selected.encounter_id}&patient_id=${selected.patient_id}&patient_name=${encodeURIComponent(selected.patient_name || "")}`)}>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>Create Invoice
          </button>
        </div>

        {/* Encounter Header */}
        <div className="bg-gradient-to-r from-teal-600 to-cyan-700 rounded-2xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">{selected.patient_name || "Patient"}</h2>
              <p className="text-teal-200 text-sm">Clinician: {selected.clinician_name || "—"} &bull; Mode: {selected.encounter_mode}</p>
              <p className="text-teal-100 text-xs mt-1">ID: {selected.encounter_id?.slice(0, 8)} &bull; Started: {selected.started_at ? new Date(selected.started_at).toLocaleString() : "—"}</p>
            </div>
            <div className="text-right">
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${selected.encounter_status === "OPEN" ? "bg-yellow-400 text-yellow-900" : selected.encounter_status === "COMPLETED" ? "bg-green-400 text-green-900" : "bg-slate-200 text-slate-700"}`}>{selected.encounter_status}</span>
              <p className="text-teal-200 text-xs mt-2">Chief Complaint: {selected.chief_complaint || "—"}</p>
            </div>
          </div>
        </div>

        {/* Encounter Mode Selector & Voice Interface */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm text-slate-700">Encounter Mode</h3>
            <div className="flex gap-2">
              <select
                value={encounterMode}
                onChange={(e) => setEncounterMode(e.target.value as any)}
                className="px-3 py-2 border rounded-md"
              >
                <option value="MANUAL">Manual Entry</option>
                <option value="AI_GUIDED">AI Guided</option>
                <option value="AI_DRIVEN">AI Driven</option>
              </select>
              <button
                onClick={runAiWorkflow}
                disabled={isRunningAiWorkflow || !selected}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isRunningAiWorkflow ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                    Running AI Workflow...
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    Run AI Workflow
                  </>
                )}
              </button>
              <select
                value={workflowType}
                onChange={(e) => setWorkflowType(e.target.value as any)}
                className="px-3 py-2 border rounded-md"
                disabled={isRunningAiWorkflow}
              >
                <option value="FULL_AUTOMATION">Full Automation</option>
                <option value="QUESTIONING_ONLY">Questioning Only</option>
                <option value="MANAGEMENT_ONLY">Management Only</option>
              </select>
            </div>
          </div>

          {/* Voice Recording Interface */}
          <div className="border-t border-slate-100 pt-4">
            <div className="flex items-center gap-4">
              <button
                onClick={handleRecordingToggle}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                  isRecording
                    ? "bg-red-500 text-white animate-pulse"
                    : "bg-teal-600 text-white hover:bg-teal-700"
                }`}
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isRecording ? "M6 18L18 6M6 6l12 12" : "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"} />
                </svg>
                {isRecording ? "Stop Recording" : "Start Voice Recording"}
              </button>
              {isRecording && <span className="text-xs text-red-500 font-semibold animate-pulse">Recording...</span>}
            </div>

            {/* Transcript Display */}
            {transcript && (
              <div className="mt-4 p-4 bg-slate-50 rounded-xl">
                <h4 className="font-semibold text-xs text-slate-700 mb-2">Transcript</h4>
                <p className="text-sm text-slate-600">{transcript}</p>
              </div>
            )}
          </div>

          {/* AI Panel Toggle */}
          <div className="border-t border-slate-100 pt-4 mt-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-slate-700">AI Assistant</h3>
              <div className="flex gap-2">
                <button onClick={getAiSuggestions} className="text-xs px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">Get AI Suggestions</button>
                <button onClick={() => setShowAiPanel(!showAiPanel)} className="text-xs text-teal-600 hover:text-teal-800">
                  {showAiPanel ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {/* AI Questions Panel */}
            {showAiPanel && (
              <div className="mt-4 space-y-4">
                <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-100">
                  <h4 className="font-semibold text-xs text-purple-800 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    Suggested Questions
                  </h4>
                  {aiQuestions?.length > 0 ? (
                    <ul className="space-y-2">
                      {aiQuestions.map((q, i) => (
                        <li key={i} className="text-xs text-slate-700 bg-white p-2 rounded-lg border border-purple-200">{q}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-500 italic">Start recording or enter patient information to see AI-suggested questions.</p>
                  )}
                </div>

                {/* AI Suggestions */}
                {aiSuggestions?.diagnoses?.length > 0 && (
                  <div className="p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-100">
                    <h4 className="font-semibold text-xs text-amber-800 mb-3">AI Suggested Diagnoses</h4>
                    <ul className="space-y-1">
                      {aiSuggestions.diagnoses.map((d: any, i: number) => (
                        <li key={i} className="text-xs text-slate-700 bg-white p-2 rounded-lg border border-amber-200 flex items-center justify-between">
                          <span>{d.name}</span>
                          <span className="text-xs text-amber-600 font-semibold">{(d.confidence * 100).toFixed(0)}%</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {aiSuggestions?.medications?.length > 0 && (
                  <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-100">
                    <h4 className="font-semibold text-xs text-green-800 mb-3">AI Suggested Medications</h4>
                    <ul className="space-y-1">
                      {aiSuggestions.medications.map((m: any, i: number) => (
                        <li key={i} className="text-xs text-slate-700 bg-white p-2 rounded-lg border border-green-200">
                          <strong>{m.name}</strong> - {m.dose}, {m.frequency}, {m.duration}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {aiSuggestions?.advice?.length > 0 && (
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-100">
                    <h4 className="font-semibold text-xs text-blue-800 mb-3">Patient Advice</h4>
                    <ul className="space-y-1">
                      {aiSuggestions.advice.map((a: string, i: number) => (
                        <li key={i} className="text-xs text-slate-700 bg-white p-2 rounded-lg border border-blue-200">{a}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Examination Findings Section */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm text-slate-700">Examination Findings</h3>
            <div className="flex gap-2">
              <button onClick={getExamAiSuggestions} className="text-xs px-3 py-1 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">Get AI Suggestions</button>
            </div>
          </div>
          <textarea
            value={examinationFindings}
            onChange={(e) => setExaminationFindings(e.target.value)}
            placeholder="Enter examination findings..."
            className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            rows={4}
          />
          {aiExamSuggestions?.length > 0 && (
            <div className="mt-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-100">
              <h4 className="font-semibold text-xs text-indigo-800 mb-3">AI Suggested Follow-ups</h4>
              <ul className="space-y-1">
                {aiExamSuggestions.map((s, i) => (
                  <li key={i} className="text-xs text-slate-700 bg-white p-2 rounded-lg border border-indigo-200">{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Clinical Encounter Flow */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm text-slate-700">AI-Powered Clinical Encounter Flow</h3>
            <span className={`text-xs px-3 py-1 rounded-full font-bold ${currentPhase === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'}`}>
              Phase: {currentPhase}
            </span>
          </div>
          
          {!flowId ? (
            <button onClick={startClinicalFlow} className="w-full text-sm px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl hover:from-purple-700 hover:to-indigo-700 transition font-semibold">
              Start AI-Powered Clinical Flow
            </button>
          ) : (
            <div className="space-y-3">
              {/* Manual Text Input (for when voice is not available) */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <p className="text-xs font-bold text-slate-700 mb-2">
                  {currentPhase === 'COMPLAINT_CAPTURE' ? 'Enter Patient Complaint (Type or Use Voice)' : 
                   currentPhase === 'INTERACTIVE_QUESTIONING' ? 'Enter Answer to Question (Type or Use Voice)' : 
                   'Enter Text (Type or Use Voice)'}
                </p>
                <textarea
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Type here or use voice recording above..."
                  className="w-full p-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  rows={3}
                />
              </div>

              {/* Complaint Capture */}
              {currentPhase === 'COMPLAINT_CAPTURE' && (
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
                  <p className="text-xs font-bold text-amber-800 mb-2">Step 1: Capture Patient Complaint</p>
                  <div className="flex gap-2">
                    <button onClick={submitComplaint} disabled={!transcript.trim()} className="text-xs px-3 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition disabled:opacity-50">
                      Submit Complaint
                    </button>
                  </div>
                </div>
              )}

              {/* Interactive Questioning */}
              {currentPhase === 'INTERACTIVE_QUESTIONING' && (
                <div className="p-4 bg-purple-50 rounded-xl border border-purple-200">
                  <p className="text-xs font-bold text-purple-800 mb-2">Step 2: Interactive Questioning (Turn {turnNumber})</p>
                  {currentQuestion && (
                    <div className="bg-white p-3 rounded-lg mb-2 border border-purple-200">
                      <p className="text-sm text-slate-700 font-semibold">{currentQuestion}</p>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <button onClick={getNextQuestion} className="text-xs px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
                      Get Next Question
                    </button>
                    <button onClick={submitAnswer} disabled={!transcript.trim() || !turnId} className="text-xs px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50">
                      Submit Answer
                    </button>
                  </div>
                  {shouldMoveToExam && (
                    <button onClick={generateExaminationGuidance} className="mt-2 text-xs px-3 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition w-full">
                      Move to Examination Phase
                    </button>
                  )}
                </div>
              )}

              {/* Examination */}
              {currentPhase === 'EXAMINATION' && (
                <div className="p-4 bg-teal-50 rounded-xl border border-teal-200">
                  <p className="text-xs font-bold text-teal-800 mb-2">Step 3: Examination</p>
                  {examinationGuidance && (
                    <div className="bg-white p-3 rounded-lg mb-2 border border-teal-200">
                      <p className="text-sm text-slate-700">{examinationGuidance.guidance}</p>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <button onClick={submitExaminationFindings} disabled={!examinationFindings.trim()} className="text-xs px-3 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition disabled:opacity-50">
                      Submit Findings
                    </button>
                    <button onClick={generateManagementPlan} className="text-xs px-3 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition">
                      Generate Management Plan
                    </button>
                  </div>
                </div>
              )}

              {/* Management Planning */}
              {currentPhase === 'MANAGEMENT_PLANNING' && (
                <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
                  <p className="text-xs font-bold text-emerald-800 mb-2">Step 4: Management Planning</p>
                  {managementPlan && (
                    <div className="space-y-3">
                      {/* Diagnoses */}
                      {managementPlan.suggested_diagnoses && managementPlan.suggested_diagnoses.length > 0 && (
                        <div className="bg-white p-3 rounded-lg border border-emerald-200">
                          <p className="text-xs font-bold text-slate-800 mb-2">Suggested Diagnoses</p>
                          {managementPlan.suggested_diagnoses.map((diag: any, idx: number) => (
                            <div key={idx} className="text-xs text-slate-700 mb-1">
                              <span className="font-semibold">{diag.code || diag.name || 'Unknown'}:</span> {diag.description || diag.reason || ''}
                            </div>
                          ))}
                        </div>
                      )}
                      {/* Medications */}
                      {managementPlan.suggested_medications && managementPlan.suggested_medications.length > 0 && (
                        <div className="bg-white p-3 rounded-lg border border-emerald-200">
                          <p className="text-xs font-bold text-slate-800 mb-2">Suggested Medications</p>
                          {managementPlan.suggested_medications.map((med: any, idx: number) => (
                            <div key={idx} className="text-xs text-slate-700 mb-1">
                              <span className="font-semibold">{med.name || 'Unknown'}:</span> {med.dosage || ''} {med.frequency || ''} {med.duration || ''}
                            </div>
                          ))}
                        </div>
                      )}
                      {/* Lab Orders */}
                      {managementPlan.suggested_lab_orders && managementPlan.suggested_lab_orders.length > 0 && (
                        <div className="bg-white p-3 rounded-lg border border-emerald-200">
                          <p className="text-xs font-bold text-slate-800 mb-2">Suggested Lab Orders</p>
                          {managementPlan.suggested_lab_orders.map((lab: any, idx: number) => (
                            <div key={idx} className="text-xs text-slate-700 mb-1">
                              <span className="font-semibold">{lab.name || 'Unknown'}:</span> {lab.reason || ''}
                            </div>
                          ))}
                        </div>
                      )}
                      {/* Imaging */}
                      {managementPlan.suggested_imaging && managementPlan.suggested_imaging.length > 0 && (
                        <div className="bg-white p-3 rounded-lg border border-emerald-200">
                          <p className="text-xs font-bold text-slate-800 mb-2">Suggested Imaging</p>
                          {managementPlan.suggested_imaging.map((img: any, idx: number) => (
                            <div key={idx} className="text-xs text-slate-700 mb-1">
                              <span className="font-semibold">{img.name || 'Unknown'}:</span> {img.reason || ''}
                            </div>
                          ))}
                        </div>
                      )}
                      {/* Procedures */}
                      {managementPlan.suggested_procedures && managementPlan.suggested_procedures.length > 0 && (
                        <div className="bg-white p-3 rounded-lg border border-emerald-200">
                          <p className="text-xs font-bold text-slate-800 mb-2">Suggested Procedures</p>
                          {managementPlan.suggested_procedures.map((proc: any, idx: number) => (
                            <div key={idx} className="text-xs text-slate-700 mb-1">
                              <span className="font-semibold">{proc.name || 'Unknown'}:</span> {proc.reason || ''}
                            </div>
                          ))}
                        </div>
                      )}
                      {/* Follow-up Recommendations */}
                      {managementPlan.follow_up_recommendations && managementPlan.follow_up_recommendations.length > 0 && (
                        <div className="bg-white p-3 rounded-lg border border-emerald-200">
                          <p className="text-xs font-bold text-slate-800 mb-2">Follow-up Recommendations</p>
                          {managementPlan.follow_up_recommendations.map((rec: string, idx: number) => (
                            <div key={idx} className="text-xs text-slate-700 mb-1">
                              • {rec}
                            </div>
                          ))}
                        </div>
                      )}
                      {/* Fallback to text if no structured data */}
                      {(!managementPlan.suggested_diagnoses || managementPlan.suggested_diagnoses.length === 0) &&
                       (!managementPlan.suggested_medications || managementPlan.suggested_medications.length === 0) && (
                        <div className="bg-white p-3 rounded-lg border border-emerald-200">
                          <p className="text-sm text-slate-700 whitespace-pre-wrap">{managementPlan.current_plan_text || managementPlan.original_plan_text || JSON.stringify(managementPlan.current_plan, null, 2)}</p>
                        </div>
                      )}
                    </div>
                  )}
                  <button onClick={generateDocuments} className="text-xs px-3 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition w-full">
                    Generate Documents
                  </button>
                </div>
              )}

              {/* Document Generation */}
              {currentPhase === 'DOCUMENT_GENERATION' && (
                <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
                  <p className="text-xs font-bold text-blue-800 mb-2">Step 5: Document Generation</p>
                  <button onClick={generateDocuments} className="text-xs px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition w-full">
                    Generate Clinical Documents
                  </button>
                </div>
              )}

              {/* Completed */}
              {currentPhase === 'COMPLETED' && (
                <div className="p-4 bg-green-50 rounded-xl border border-green-200">
                  <p className="text-xs font-bold text-green-800 mb-2">Clinical Flow Completed</p>
                  <p className="text-sm text-slate-700">All phases completed successfully.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h3 className="font-bold text-sm text-slate-700 mb-4">Quick Actions</h3>
          <div className="flex flex-wrap gap-3">
            <button onClick={() => setShowPromptConfig(true)} className="text-xs px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition">
              Configure Prompt Template
            </button>
            <button onClick={() => { setDocumentTitle("Clinical Summary"); generateDocument(); }} className="text-xs px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              Generate Clinical Summary
            </button>
            <button onClick={() => { setDocumentTitle("Discharge Note"); generateDocument(); }} className="text-xs px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              Generate Discharge Note
            </button>
            <button onClick={() => setShowCompletionModal(true)} className="text-xs px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
              Complete Encounter
            </button>
          </div>
        </div>

        {/* Tabbed Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Notes Section */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 bg-slate-50 border-b">
              <h3 className="font-bold text-sm text-slate-700 flex items-center gap-2"><svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>Clinical Notes ({notes.length})</h3>
              <button onClick={() => setShowNoteModal(true)} className="text-xs px-3 py-1 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition">+ Add Note</button>
            </div>
            <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
              {notes.length === 0 ? <p className="text-sm text-slate-400 text-center py-6">No notes yet. Add your first clinical note.</p> :
              notes.map((n: any) => (
                <div key={n.encounter_note_id} className="bg-slate-50 rounded-xl p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${n.note_type === "HISTORY" ? "bg-blue-100 text-blue-700" : n.note_type === "EXAM" ? "bg-green-100 text-green-700" : "bg-purple-100 text-purple-700"}`}>{n.note_type}</span>
                    <span className="text-[10px] text-slate-400">{n.authored_at ? new Date(n.authored_at).toLocaleString() : ""}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{n.narrative_text || JSON.stringify(n.structured_json)}</p>
                  <p className="text-[10px] text-slate-400 mt-1">By: {n.authored_by || "—"}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Diagnoses Section */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 bg-slate-50 border-b">
              <h3 className="font-bold text-sm text-slate-700 flex items-center gap-2"><svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>Diagnoses ({diagnoses.length})</h3>
              <button onClick={() => setShowDiagModal(true)} className="text-xs px-3 py-1 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition">+ Add Diagnosis</button>
            </div>
            <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
              {diagnoses.length === 0 ? <p className="text-sm text-slate-400 text-center py-6">No diagnoses yet.</p> :
              diagnoses.map((d: any) => (
                <div key={d.diagnosis_id} className="bg-slate-50 rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded mr-2 ${d.diagnosis_type === "PRIMARY" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>{d.diagnosis_type}</span>
                    <span className="font-semibold text-sm text-slate-800">{d.diagnosis_display}</span>
                    {d.diagnosis_code && <span className="text-xs text-slate-400 ml-2">[{d.diagnosis_code}]</span>}
                  </div>
                  <div className="text-right">
                    {d.probability_score && <span className="text-xs text-slate-500">{(d.probability_score * 100).toFixed(0)}%</span>}
                    <span className={`text-[10px] ml-2 px-2 py-0.5 rounded ${d.source_type === "AI_SUGGESTED" ? "bg-purple-100 text-purple-600" : "bg-slate-100 text-slate-500"}`}>{d.source_type}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Orders Section */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 bg-slate-50 border-b">
              <h3 className="font-bold text-sm text-slate-700 flex items-center gap-2"><svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>Clinical Orders ({orders.length})</h3>
              <button onClick={() => setShowOrderModal(true)} className="text-xs px-3 py-1 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition">+ New Order</button>
            </div>
            <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
              {orders.length === 0 ? <p className="text-sm text-slate-400 text-center py-6">No orders yet.</p> :
              orders.map((o: any) => (
                <div key={o.service_request_id} className="bg-slate-50 rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded mr-2 ${o.request_type === "LAB" ? "bg-blue-100 text-blue-700" : o.request_type === "IMAGING" ? "bg-violet-100 text-violet-700" : "bg-amber-100 text-amber-700"}`}>{o.request_type}</span>
                    <span className="font-semibold text-sm">{o.catalog_name}</span>
                    {o.catalog_code && <span className="text-xs text-slate-400 ml-2">[{o.catalog_code}]</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] px-2 py-0.5 rounded ${o.priority === "STAT" ? "bg-red-100 text-red-600 font-bold" : "bg-slate-100 text-slate-500"}`}>{o.priority}</span>
                    <span className="badge badge-info">{o.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Prescriptions Section */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 bg-slate-50 border-b">
              <h3 className="font-bold text-sm text-slate-700 flex items-center gap-2"><svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>Prescriptions ({meds.length})</h3>
              <button onClick={() => setShowRxModal(true)} className="text-xs px-3 py-1 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition">+ Prescribe</button>
            </div>
            <div className="p-4 space-y-3 max-h-80 overflow-y-auto">
              {meds.length === 0 ? <p className="text-sm text-slate-400 text-center py-6">No prescriptions yet.</p> :
              meds.map((m: any) => (
                <div key={m.medication_request_id} className="bg-slate-50 rounded-xl p-3">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-slate-800 flex items-center gap-2"><svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>{m.medication_name}</span>
                    <span className="text-[10px] text-slate-400">{m.medication_code || ""}</span>
                  </div>
                  <div className="flex gap-4 mt-1 text-xs text-slate-500">
                    <span>Route: {m.route || "—"}</span>
                    <span>Dose: {m.dose || "—"}</span>
                    <span>Freq: {m.frequency || "—"}</span>
                    <span>Duration: {m.duration || "—"}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Note Modal */}
        {showNoteModal && (<div className="modal-overlay" onClick={() => setShowNoteModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header"><h3 className="font-bold text-lg">Add Clinical Note</h3><button onClick={() => setShowNoteModal(false)} className="text-xl">&times;</button></div>
          <div className="modal-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">Note Type</label><select className="input-field" value={noteForm.note_type} onChange={e => setNoteForm({...noteForm, note_type: e.target.value})}><option value="HISTORY">History</option><option value="EXAM">Examination</option><option value="PROGRESS">Progress</option><option value="PROCEDURE">Procedure</option><option value="SUMMARY">Summary</option></select></div>
              <div><label className="input-label">Authored By</label><input className="input-field" value={noteForm.authored_by || ""} onChange={e => setNoteForm({...noteForm, authored_by: e.target.value})} /></div>
            </div>
            <div><label className="input-label">Narrative Text</label><textarea className="input-field" rows={4} value={noteForm.narrative_text || ""} onChange={e => setNoteForm({...noteForm, narrative_text: e.target.value})} /></div>
          </div>
          <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowNoteModal(false)}>Cancel</button><button className="btn-primary" onClick={addNote}>Save Note</button></div>
        </div></div>)}

        {/* Diagnosis Modal */}
        {showDiagModal && (<div className="modal-overlay" onClick={() => setShowDiagModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header"><h3 className="font-bold text-lg">Add Diagnosis</h3><button onClick={() => setShowDiagModal(false)} className="text-xl">&times;</button></div>
          <div className="modal-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">Type</label><select className="input-field" value={diagForm.diagnosis_type} onChange={e => setDiagForm({...diagForm, diagnosis_type: e.target.value})}><option value="PRIMARY">Primary</option><option value="SECONDARY">Secondary</option><option value="DIFFERENTIAL">Differential</option></select></div>
              <div><label className="input-label">ICD Code</label><input className="input-field" placeholder="e.g. I20.0" value={diagForm.diagnosis_code || ""} onChange={e => setDiagForm({...diagForm, diagnosis_code: e.target.value})} /></div>
            </div>
            <div><label className="input-label">Diagnosis *</label><input className="input-field" value={diagForm.diagnosis_display || ""} onChange={e => setDiagForm({...diagForm, diagnosis_display: e.target.value})} /></div>
          </div>
          <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowDiagModal(false)}>Cancel</button><button className="btn-primary" onClick={addDiag}>Save</button></div>
        </div></div>)}

        {/* Order Modal */}
        {showOrderModal && (<div className="modal-overlay" onClick={() => setShowOrderModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header"><h3 className="font-bold text-lg">New Clinical Order</h3><button onClick={() => setShowOrderModal(false)} className="text-xl">&times;</button></div>
          <div className="modal-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">Type</label><select className="input-field" value={orderForm.request_type} onChange={e => setOrderForm({...orderForm, request_type: e.target.value})}><option value="LAB">Lab</option><option value="IMAGING">Imaging</option><option value="PROCEDURE">Procedure</option><option value="REFERRAL">Referral</option></select></div>
              <div><label className="input-label">Priority</label><select className="input-field" value={orderForm.priority} onChange={e => setOrderForm({...orderForm, priority: e.target.value})}><option value="ROUTINE">Routine</option><option value="STAT">STAT</option><option value="URGENT">Urgent</option></select></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">Catalog Code</label><input className="input-field" value={orderForm.catalog_code || ""} onChange={e => setOrderForm({...orderForm, catalog_code: e.target.value})} /></div>
              <div><label className="input-label">Name *</label><input className="input-field" value={orderForm.catalog_name || ""} onChange={e => setOrderForm({...orderForm, catalog_name: e.target.value})} /></div>
            </div>
          </div>
          <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowOrderModal(false)}>Cancel</button><button className="btn-primary" onClick={addOrder}>Place Order</button></div>
        </div></div>)}

        {/* Prescription Modal */}
        {showRxModal && (<div className="modal-overlay" onClick={() => setShowRxModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header"><h3 className="font-bold text-lg">Prescribe Medication</h3><button onClick={() => setShowRxModal(false)} className="text-xl">&times;</button></div>
          <div className="modal-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><label className="input-label">Medication Name *</label><input className="input-field" value={rxForm.medication_name || ""} onChange={e => setRxForm({...rxForm, medication_name: e.target.value})} /></div>
              <div><label className="input-label">Code</label><input className="input-field" value={rxForm.medication_code || ""} onChange={e => setRxForm({...rxForm, medication_code: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div><label className="input-label">Route</label><select className="input-field" value={rxForm.route} onChange={e => setRxForm({...rxForm, route: e.target.value})}><option value="ORAL">Oral</option><option value="IV">IV</option><option value="IM">IM</option><option value="TOPICAL">Topical</option><option value="INHALED">Inhaled</option></select></div>
              <div><label className="input-label">Dose</label><input className="input-field" value={rxForm.dose || ""} onChange={e => setRxForm({...rxForm, dose: e.target.value})} /></div>
              <div><label className="input-label">Frequency</label><input className="input-field" placeholder="e.g. BID" value={rxForm.frequency || ""} onChange={e => setRxForm({...rxForm, frequency: e.target.value})} /></div>
              <div><label className="input-label">Duration</label><input className="input-field" placeholder="e.g. 7 days" value={rxForm.duration || ""} onChange={e => setRxForm({...rxForm, duration: e.target.value})} /></div>
            </div>
          </div>
          <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowRxModal(false)}>Cancel</button><button className="btn-primary" onClick={addRx}>Prescribe</button></div>
        </div></div>)}

        {/* Prompt Configuration Modal */}
        {showPromptConfig && (<div className="modal-overlay" onClick={() => setShowPromptConfig(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header"><h3 className="font-bold text-lg">Configure Prompt Template</h3><button onClick={() => setShowPromptConfig(false)} className="text-xl">&times;</button></div>
          <div className="modal-body space-y-4">
            <div><label className="input-label">AI Prompt Template</label><textarea className="input-field" rows={6} value={promptTemplate} onChange={e => setPromptTemplate(e.target.value)} placeholder="Enter custom prompt template for AI suggestions..." /></div>
            <p className="text-xs text-slate-500">This template will be used to generate AI-powered suggestions for this encounter type.</p>
          </div>
          <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowPromptConfig(false)}>Cancel</button><button className="btn-primary" onClick={savePromptTemplate}>Save Template</button></div>
        </div></div>)}

        {/* Document Generation Modal */}
        {showDocumentModal && (<div className="modal-overlay" onClick={() => setShowDocumentModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header"><h3 className="font-bold text-lg">{documentTitle}</h3><button onClick={() => setShowDocumentModal(false)} className="text-xl">&times;</button></div>
          <div className="modal-body space-y-4">
            <div><textarea className="input-field" rows={12} value={documentContent} onChange={e => setDocumentContent(e.target.value)} readOnly /></div>
          </div>
          <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowDocumentModal(false)}>Close</button><button className="btn-primary" onClick={() => { navigator.clipboard.writeText(documentContent); alert('Copied to clipboard'); }}>Copy to Clipboard</button></div>
        </div></div>)}

        {/* Encounter Completion Modal */}
        {showCompletionModal && (<div className="modal-overlay" onClick={() => setShowCompletionModal(false)}><div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header"><h3 className="font-bold text-lg">Complete Encounter</h3><button onClick={() => setShowCompletionModal(false)} className="text-xl">&times;</button></div>
          <div className="modal-body space-y-4">
            <div><label className="input-label">Share With (Email)</label><input className="input-field" type="email" value={shareWithEmail} onChange={e => setShareWithEmail(e.target.value)} placeholder="stakeholder@example.com" /></div>
            <p className="text-xs text-slate-500">Enter email address to share the encounter summary with stakeholders (optional).</p>
          </div>
          <div className="modal-footer"><button className="btn-secondary" onClick={() => setShowCompletionModal(false)}>Cancel</button><button className="btn-primary" onClick={completeEncounter}>Complete & Share</button></div>
        </div></div>)}
      </div></div>);
  }

  // Encounter list view
  return (<div><TopNav title="Encounter Workspace" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Clinical Encounters</h2><p className="text-sm text-slate-500">Unified encounter engine — {encounters.length} encounters</p></div>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["", "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"].map(s => (
          <button key={s} onClick={() => setFilter(s)} className={`px-4 py-2 rounded-full text-xs font-semibold transition-all ${filter === s ? "bg-teal-600 text-white shadow-md" : "bg-white border border-slate-200 text-slate-600 hover:border-teal-300"}`}>{s || "All"}</button>
        ))}
      </div>

      {loading ? <div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      filtered.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-teal-50 flex items-center justify-center text-teal-600">
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
          </div>
          <h3 className="text-lg font-bold text-slate-700">No Encounters</h3>
          <p className="text-sm text-slate-500 mt-1">Encounters are created when appointments are checked in</p>
        </div>
      ) :
      <div className="grid gap-4">
        {filtered.map(enc => (
          <div key={enc.encounter_id} className="bg-white rounded-2xl border border-slate-200 p-5 hover:shadow-lg hover:border-teal-300 transition-all cursor-pointer" onClick={() => loadDetails(enc)}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center text-white font-bold text-lg">{enc.patient_name?.charAt(0) || "E"}</div>
                <div>
                  <h3 className="font-bold text-slate-800">{enc.patient_name || "Patient"}</h3>
                  <p className="text-xs text-slate-500">{enc.encounter_mode} &bull; {enc.clinician_name || "—"} &bull; {enc.started_at ? new Date(enc.started_at).toLocaleString() : ""}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`badge ${statusColors[enc.encounter_status] || "badge-neutral"}`}>{enc.encounter_status}</span>
                <span className="text-xs px-3 py-1 bg-teal-50 text-teal-700 rounded-lg font-semibold hover:bg-teal-100">Open Workspace →</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="bg-slate-50 rounded-lg p-2"><span className="text-slate-400 block">Chief Complaint</span><span className="font-semibold">{enc.chief_complaint || "—"}</span></div>
              <div className="bg-slate-50 rounded-lg p-2"><span className="text-slate-400 block">Encounter ID</span><span className="font-mono">{enc.encounter_id?.slice(0,12)}</span></div>
              <div className="bg-slate-50 rounded-lg p-2"><span className="text-slate-400 block">Mode</span><span className="font-semibold">{enc.encounter_mode}</span></div>
            </div>
          </div>
        ))}
      </div>}
    </div></div>);
}
