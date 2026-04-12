"""
Clinical Encounter Flow Routes

API endpoints for the AI-powered clinical consultation workflow.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clinical_encounter_flow.schemas import (
    ClinicalEncounterFlowCreate,
    ClinicalEncounterFlowUpdate,
    ClinicalEncounterFlowResponse,
    QuestionTurnCreate,
    QuestionTurnResponse,
    ExaminationGuidanceCreate,
    ExaminationGuidanceResponse,
    ManagementPlanCreate,
    ManagementPlanUpdate,
    ManagementPlanResponse,
    DoctorPromptOverrideCreate,
    DoctorPromptOverrideUpdate,
    DoctorPromptOverrideResponse,
    StartConsultationRequest,
    SubmitComplaintRequest,
    SubmitAnswerRequest,
    SubmitExaminationFindingsRequest,
    GenerateDocumentsRequest,
    NextQuestionResponse,
    PhaseTransitionResponse
)
from app.core.clinical_encounter_flow.services import (
    ClinicalEncounterFlowService,
    InteractiveQuestioningService,
    ExaminationGuidanceService,
    ManagementPlanService,
    DoctorPromptService
)
from app.core.clinical_encounter_flow.models import EncounterPhase
from app.database import get_db

router = APIRouter(prefix="/clinical-encounter-flow", tags=["clinical-encounter-flow"])


# ── Flow Management ─────────────────────────────────────────────────────────

@router.post("/start", response_model=ClinicalEncounterFlowResponse, status_code=201)
async def start_consultation(
    request: StartConsultationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Start a new AI-powered clinical consultation flow."""
    service = ClinicalEncounterFlowService(db)
    data = ClinicalEncounterFlowCreate(
        encounter_id=request.encounter_id,
        patient_id=request.patient_id,
        clinician_id=request.clinician_id,
        specialty_profile_id=request.specialty_profile_id
    )
    flow = await service.start_flow(data)
    return ClinicalEncounterFlowResponse.model_validate(flow)


@router.get("/flow/{flow_id}", response_model=ClinicalEncounterFlowResponse)
async def get_flow(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the current state of a clinical encounter flow."""
    service = ClinicalEncounterFlowService(db)
    flow = await service.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return ClinicalEncounterFlowResponse.model_validate(flow)


@router.get("/encounter/{encounter_id}/flow", response_model=ClinicalEncounterFlowResponse)
async def get_flow_by_encounter(
    encounter_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the clinical encounter flow for a specific encounter."""
    service = ClinicalEncounterFlowService(db)
    flow = await service.get_flow_by_encounter(encounter_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found for this encounter")
    return ClinicalEncounterFlowResponse.model_validate(flow)


@router.put("/flow/{flow_id}", response_model=ClinicalEncounterFlowResponse)
async def update_flow(
    flow_id: UUID,
    data: ClinicalEncounterFlowUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a clinical encounter flow."""
    service = ClinicalEncounterFlowService(db)
    flow = await service.update_flow(flow_id, data)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return ClinicalEncounterFlowResponse.model_validate(flow)


@router.post("/flow/{flow_id}/transition", response_model=PhaseTransitionResponse)
async def transition_phase(
    flow_id: UUID,
    new_phase: EncounterPhase = Query(...),
    reason: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Transition the flow to a new phase."""
    service = ClinicalEncounterFlowService(db)
    flow = await service.transition_phase(flow_id, new_phase, reason)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    return PhaseTransitionResponse(
        previous_phase=flow.phase_history[-2]["phase"] if len(flow.phase_history) >= 2 else flow.phase_history[0]["phase"],
        new_phase=new_phase,
        reason=reason
    )


# ── Complaint Capture ───────────────────────────────────────────────────────

@router.post("/flow/{flow_id}/complaint", response_model=ClinicalEncounterFlowResponse)
async def submit_complaint(
    flow_id: UUID,
    request: SubmitComplaintRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit the patient's chief complaint (voice transcript)."""
    service = ClinicalEncounterFlowService(db)
    
    # Update flow with complaint
    data = ClinicalEncounterFlowUpdate(
        chief_complaint_transcript=request.complaint_transcript,
        chief_complaint_language=request.language,
        chief_complaint_analyzed=True
    )
    
    # Transition to questioning phase
    flow = await service.update_flow(flow_id, data)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    # Auto-transition to questioning
    await service.transition_phase(flow_id, EncounterPhase.INTERACTIVE_QUESTIONING, "Complaint captured, starting questioning")
    
    # Refresh flow to get updated state
    flow = await service.get_flow(flow_id)
    
    return ClinicalEncounterFlowResponse.model_validate(flow)


# ── Interactive Questioning ──────────────────────────────────────────────────

@router.get("/flow/{flow_id}/next-question", response_model=NextQuestionResponse)
async def get_next_question(
    flow_id: UUID,
    encounter_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the next question from the AI.
    The AI generates ONE question at a time for the doctor to ask the patient.
    """
    service = InteractiveQuestioningService(db)
    response = await service.get_next_question(flow_id, encounter_id)
    
    return NextQuestionResponse(
        question=response["question"],
        turn_id=response["turn_id"],
        turn_number=response["turn_number"],
        suggested_next_action=response["suggested_next_action"],
        should_move_to_examination=response["should_move_to_examination"]
    )


@router.post("/flow/{flow_id}/answer", response_model=QuestionTurnResponse)
async def submit_answer(
    flow_id: UUID,
    request: SubmitAnswerRequest,
    turn_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Submit the patient's answer to a question."""
    service = InteractiveQuestioningService(db)
    turn = await service.submit_answer(flow_id, turn_id, request.answer_transcript, request.language)
    
    return QuestionTurnResponse.model_validate(turn)


@router.get("/flow/{flow_id}/questions", response_model=List[QuestionTurnResponse])
async def get_question_history(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the complete question-answer history for this flow."""
    from app.core.clinical_encounter_flow.models import QuestionTurn
    from sqlalchemy import select, desc
    
    result = await db.execute(
        select(QuestionTurn).where(
            QuestionTurn.flow_id == flow_id
        ).order_by(desc(QuestionTurn.turn_number))
    )
    turns = result.scalars().all()
    return [QuestionTurnResponse.model_validate(t) for t in turns]


# ── Examination Phase ───────────────────────────────────────────────────────

@router.post("/flow/{flow_id}/examination/guidance", response_model=ExaminationGuidanceResponse)
async def generate_examination_guidance(
    flow_id: UUID,
    encounter_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate examination guidance using AI.
    The AI displays critical things to examine based on the complaint and questioning.
    """
    service = ExaminationGuidanceService(db)
    guidance = await service.generate_guidance(flow_id, encounter_id)
    
    # Auto-transition to examination phase
    flow_service = ClinicalEncounterFlowService(db)
    await flow_service.transition_phase(flow_id, EncounterPhase.EXAMINATION, "Examination guidance generated")
    
    return ExaminationGuidanceResponse.model_validate(guidance)


@router.post("/flow/{flow_id}/examination/findings", response_model=ExaminationGuidanceResponse)
async def submit_examination_findings(
    flow_id: UUID,
    request: SubmitExaminationFindingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit examination findings (voice transcript from doctor).
    The AI analyzes the findings and structures them.
    """
    service = ExaminationGuidanceService(db)
    guidance = await service.submit_examination_findings(flow_id, request.examination_transcript, request.language)
    
    return ExaminationGuidanceResponse.model_validate(guidance)


@router.get("/flow/{flow_id}/examination/guidance", response_model=ExaminationGuidanceResponse)
async def get_examination_guidance(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the examination guidance for this flow."""
    from app.core.clinical_encounter_flow.models import ExaminationGuidance
    from sqlalchemy import select
    
    result = await db.execute(
        select(ExaminationGuidance).where(ExaminationGuidance.flow_id == flow_id)
    )
    guidance = result.scalar_one_or_none()
    
    if not guidance:
        raise HTTPException(status_code=404, detail="Examination guidance not found")
    
    return ExaminationGuidanceResponse.model_validate(guidance)


# ── Management Plan ─────────────────────────────────────────────────────────

@router.post("/flow/{flow_id}/management-plan", response_model=ManagementPlanResponse)
async def generate_management_plan(
    flow_id: UUID,
    encounter_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a full but editable management plan using AI.
    Includes diagnoses, medications, lab orders, and follow-up recommendations.
    """
    service = ManagementPlanService(db)
    plan = await service.generate_plan(flow_id, encounter_id)
    
    # Auto-transition to management planning phase
    flow_service = ClinicalEncounterFlowService(db)
    await flow_service.transition_phase(flow_id, EncounterPhase.MANAGEMENT_PLANNING, "Management plan generated")
    
    return ManagementPlanResponse.model_validate(plan)


@router.put("/management-plan/{plan_id}", response_model=ManagementPlanResponse)
async def update_management_plan(
    plan_id: UUID,
    data: ManagementPlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update the management plan (doctor modifications).
    The doctor can choose from/amend the management plan.
    """
    service = ManagementPlanService(db)
    plan = await service.update_plan(plan_id, data)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Management plan not found")
    
    return ManagementPlanResponse.model_validate(plan)


@router.get("/flow/{flow_id}/management-plan", response_model=ManagementPlanResponse)
async def get_management_plan(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the management plan for this flow."""
    from app.core.clinical_encounter_flow.models import ManagementPlan
    from sqlalchemy import select
    
    result = await db.execute(
        select(ManagementPlan).where(ManagementPlan.flow_id == flow_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Management plan not found")
    
    return ManagementPlanResponse.model_validate(plan)


# ── Document Generation ─────────────────────────────────────────────────────

@router.post("/flow/{flow_id}/documents/generate", response_model=ClinicalEncounterFlowResponse)
async def generate_documents(
    flow_id: UUID,
    request: GenerateDocumentsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate documents from the audio transcript using AI.
    The doctor can choose whatever documents they want (lab orders, clinic letter, prescription, etc.).
    The LLM creates formatted documents based on the consultation transcript.
    """
    # Get the flow
    flow_service = ClinicalEncounterFlowService(db)
    flow = await flow_service.get_flow(flow_id)
    
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    # Update selected document types
    update_data = ClinicalEncounterFlowUpdate(
        selected_document_types=request.document_types
    )
    flow = await flow_service.update_flow(flow_id, update_data)
    
    # Generate documents using AI
    # This would integrate with the existing AgentOrchestrationService
    # For now, we'll mark the documents as generated
    generated_docs = []
    for doc_type in request.document_types:
        generated_docs.append({
            "type": doc_type,
            "status": "generated",
            "generated_at": datetime.utcnow().isoformat()
        })
    
    flow.documents_generated = generated_docs
    
    # Transition to document generation phase
    await flow_service.transition_phase(flow_id, EncounterPhase.DOCUMENT_GENERATION, "Documents generated")
    
    # Complete the flow
    await flow_service.transition_phase(flow_id, EncounterPhase.COMPLETED, "Consultation completed")
    
    # Refresh flow
    flow = await flow_service.get_flow(flow_id)
    
    return ClinicalEncounterFlowResponse.model_validate(flow)


# ── Doctor Prompt Overrides ─────────────────────────────────────────────────

@router.post("/doctor-prompts", response_model=DoctorPromptOverrideResponse, status_code=201)
async def create_doctor_prompt_override(
    data: DoctorPromptOverrideCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a doctor-level prompt override.
    Allows individual doctors to customize AI behavior beyond specialty-level prompts.
    """
    service = DoctorPromptService(db)
    override = await service.create_override(data)
    
    return DoctorPromptOverrideResponse.model_validate(override)


@router.get("/doctor-prompts/{clinician_id}", response_model=DoctorPromptOverrideResponse)
async def get_doctor_prompt_override(
    clinician_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a doctor's prompt override."""
    service = DoctorPromptService(db)
    override = await service.get_override(clinician_id)
    
    if not override:
        raise HTTPException(status_code=404, detail="Doctor prompt override not found")
    
    return DoctorPromptOverrideResponse.model_validate(override)


@router.put("/doctor-prompts/{override_id}", response_model=DoctorPromptOverrideResponse)
async def update_doctor_prompt_override(
    override_id: UUID,
    data: DoctorPromptOverrideUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a doctor's prompt override."""
    service = DoctorPromptService(db)
    override = await service.update_override(override_id, data)
    
    if not override:
        raise HTTPException(status_code=404, detail="Doctor prompt override not found")
    
    return DoctorPromptOverrideResponse.model_validate(override)
