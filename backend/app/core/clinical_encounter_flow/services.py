"""
Clinical Encounter Flow Services

Implements the complete AI-powered clinical consultation workflow:
1. Interactive questioning (one question at a time)
2. Examination phase transition
3. Management plan generation
4. Document generation from audio
5. Specialty and doctor-level prompt management
"""
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.core.ai.grok_client import grok_chat, grok_json
from app.core.clinical_encounter_flow.models import (
    ClinicalEncounterFlow,
    EncounterPhase,
    QuestionTurn,
    ExaminationGuidance,
    ManagementPlan,
    DoctorPromptOverride
)
from app.core.clinical_encounter_flow.schemas import (
    ClinicalEncounterFlowCreate,
    ClinicalEncounterFlowUpdate,
    QuestionTurnCreate,
    ManagementPlanCreate,
    ManagementPlanUpdate,
    DoctorPromptOverrideCreate,
    DoctorPromptOverrideUpdate
)

logger = logging.getLogger(__name__)


# ── Default Prompts ──────────────────────────────────────────────────────────

DEFAULT_QUESTIONING_PROMPT = """
You are an experienced clinical AI assistant conducting a patient consultation.
Your task is to ask ONE focused, clinically relevant question at a time to gather necessary information.

Rules:
- Ask ONLY ONE question per response
- Questions should be clear, concise, and patient-friendly
- Build on previous answers to deepen understanding
- When you have enough information, suggest moving to examination
- Consider the patient's chief complaint and medical context

Response format (JSON):
{
  "question": "Your single question here",
  "reasoning": "Brief explanation of why this question is important",
  "suggest_examination": true/false,
  "confidence": 0.0-1.0
}
"""

DEFAULT_EXAMINATION_PROMPT = """
You are an experienced clinical AI assistant providing examination guidance.
Based on the patient's complaint and questioning history, provide specific examination guidance.

Response format (JSON):
{
  "critical_examinations": [
    {
      "body_system": "e.g., Cardiovascular",
      "specific_areas": ["e.g., heart sounds", "blood pressure"],
      "priority": "HIGH/MEDIUM/LOW",
      "reasoning": "Why this examination is critical"
    }
  ],
  "red_flags": ["List of critical warning signs to look for"],
  "confidence": 0.0-1.0
}
"""

DEFAULT_MANAGEMENT_PLAN_PROMPT = """
You are an experienced clinical AI assistant generating a management plan.
Based on the complete consultation (complaint, questioning, examination), generate a comprehensive management plan.

Response format (JSON):
{
  "diagnoses": [
    {
      "diagnosis": "Diagnosis name",
      "confidence": 0.0-1.0,
      "reasoning": "Brief explanation"
    }
  ],
  "medications": [
    {
      "medication": "Drug name",
      "dosage": "e.g., 500mg",
      "frequency": "e.g., twice daily",
      "duration": "e.g., 7 days",
      "instructions": "Specific instructions"
    }
  ],
  "lab_orders": [
    {
      "test": "Test name",
      "urgency": "ROUTINE/URGENT/STAT",
      "reasoning": "Why this test is needed"
    }
  ],
  "imaging": [
    {
      "modality": "e.g., Chest X-ray",
      "indication": "Clinical indication",
      "urgency": "ROUTINE/URGENT/STAT"
    }
  ],
  "follow_up": ["Follow-up recommendations"],
  "confidence": 0.0-1.0
}
"""

DEFAULT_DOCUMENTATION_PROMPT = """
You are a clinical documentation assistant. Generate a formatted clinical document based on the consultation transcript.

Generate a professional, well-structured clinical document appropriate for the specified document type.
Include all relevant clinical information in a clear, organized format.
"""


# ── Clinical Encounter Flow Service ───────────────────────────────────────────

class ClinicalEncounterFlowService:
    """Main orchestrator for the clinical encounter flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_flow(self, data: ClinicalEncounterFlowCreate) -> ClinicalEncounterFlow:
        """Initialize a new clinical encounter flow or return existing one."""
        # Check if flow already exists for this encounter
        existing_flow = await self.get_flow_by_encounter(data.encounter_id)
        if existing_flow:
            logger.info(f"Flow already exists for encounter {data.encounter_id}, returning existing flow")
            return existing_flow
        
        # Create new flow
        flow = ClinicalEncounterFlow(
            encounter_id=data.encounter_id,
            patient_id=data.patient_id,
            clinician_id=data.clinician_id,
            specialty_profile_id=data.specialty_profile_id,
            current_phase=EncounterPhase.COMPLAINT_CAPTURE,
            phase_history=[{
                "phase": EncounterPhase.COMPLAINT_CAPTURE,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "Flow initialized"
            }]
        )
        self.db.add(flow)
        await self.db.commit()
        await self.db.refresh(flow)
        return flow

    async def get_flow(self, flow_id: uuid.UUID) -> Optional[ClinicalEncounterFlow]:
        """Get a clinical encounter flow by ID."""
        result = await self.db.execute(
            select(ClinicalEncounterFlow).where(ClinicalEncounterFlow.flow_id == flow_id)
        )
        return result.scalar_one_or_none()

    async def get_flow_by_encounter(self, encounter_id: uuid.UUID) -> Optional[ClinicalEncounterFlow]:
        """Get a clinical encounter flow by encounter ID."""
        result = await self.db.execute(
            select(ClinicalEncounterFlow).where(ClinicalEncounterFlow.encounter_id == encounter_id)
        )
        return result.scalar_one_or_none()

    async def update_flow(self, flow_id: uuid.UUID, data: ClinicalEncounterFlowUpdate) -> Optional[ClinicalEncounterFlow]:
        """Update a clinical encounter flow."""
        flow = await self.get_flow(flow_id)
        if not flow:
            return None

        # Track phase transition
        if data.current_phase and data.current_phase != flow.current_phase:
            flow.phase_history.append({
                "phase": data.current_phase,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "Phase transition"
            })
            flow.current_phase = data.current_phase

        # Update other fields
        if data.chief_complaint_transcript is not None:
            flow.chief_complaint_transcript = data.chief_complaint_transcript
        if data.chief_complaint_language is not None:
            flow.chief_complaint_language = data.chief_complaint_language
        if data.chief_complaint_analyzed is not None:
            flow.chief_complaint_analyzed = data.chief_complaint_analyzed
        if data.adequate_questions_reached is not None:
            flow.adequate_questions_reached = data.adequate_questions_reached
        if data.examination_findings_transcript is not None:
            flow.examination_findings_transcript = data.examination_findings_transcript
        if data.management_plan_accepted is not None:
            flow.management_plan_accepted = data.management_plan_accepted
        if data.selected_document_types is not None:
            flow.selected_document_types = data.selected_document_types

        await self.db.commit()
        await self.db.refresh(flow)
        return flow

    async def transition_phase(self, flow_id: uuid.UUID, new_phase: EncounterPhase, reason: str) -> Optional[ClinicalEncounterFlow]:
        """Transition the flow to a new phase."""
        flow = await self.get_flow(flow_id)
        if not flow:
            return None

        flow.phase_history.append({
            "phase": new_phase,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        })
        flow.current_phase = new_phase

        if new_phase == EncounterPhase.COMPLETED:
            flow.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(flow)
        return flow


# ── Interactive Questioning Service ──────────────────────────────────────────

class InteractiveQuestioningService:
    """Manages the interactive questioning phase - one question at a time."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_next_question(
        self,
        flow_id: uuid.UUID,
        encounter_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Generate the next question using AI.
        Returns a single question for the doctor to ask the patient.
        """
        flow_service = ClinicalEncounterFlowService(self.db)
        flow = await flow_service.get_flow(flow_id)
        
        if not flow:
            raise ValueError("Flow not found")

        # Get prompt (doctor override > specialty > default)
        prompt = await self._get_prompt(flow, "questioning")
        
        # Build context from previous turns
        context = await self._build_questioning_context(flow, encounter_id)
        
        # Generate question using AI
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Patient context:\n{json.dumps(context, indent=2, default=str)}"}
        ]
        
        try:
            response = await grok_json(messages, max_tokens=300)
            question = response.get("question", "Can you tell me more about your symptoms?")
            suggest_examination = response.get("suggest_examination", False)
            confidence = response.get("confidence", 0.7)
        except Exception as e:
            logger.error(f"Failed to generate question: {e}")
            question = "Can you tell me more about your symptoms?"
            suggest_examination = False
            confidence = 0.5

        # Create question turn record
        turn_number = flow.question_count + 1
        turn = QuestionTurn(
            flow_id=flow_id,
            encounter_id=encounter_id,
            turn_number=turn_number,
            llm_question=question,
            question_context=context,
            prompt_used=prompt[:500],  # Store truncated prompt
            confidence_score=int(confidence * 100),
            is_complete=False
        )
        self.db.add(turn)

        # Update flow
        flow.question_count = turn_number
        if suggest_examination:
            flow.adequate_questions_reached = True

        await self.db.commit()
        await self.db.refresh(turn)

        # Suggest next action
        suggested_action = "CONTINUE_QUESTIONING"
        if suggest_examination:
            suggested_action = "MOVE_TO_EXAMINATION"

        return {
            "question": question,
            "turn_id": str(turn.turn_id),
            "turn_number": turn_number,
            "suggested_next_action": suggested_action,
            "should_move_to_examination": suggest_examination,
            "confidence": confidence
        }

    async def submit_answer(
        self,
        flow_id: uuid.UUID,
        turn_id: uuid.UUID,
        answer_transcript: str,
        language: str = "en"
    ) -> QuestionTurn:
        """Submit the patient's answer to a question."""
        result = await self.db.execute(
            select(QuestionTurn).where(QuestionTurn.turn_id == turn_id)
        )
        turn = result.scalar_one_or_none()
        
        if not turn:
            raise ValueError("Question turn not found")

        turn.response_transcript = answer_transcript
        turn.response_language = language
        turn.is_complete = True

        # Analyze the answer
        try:
            analysis = await self._analyze_answer(turn.llm_question, answer_transcript)
            turn.response_analysis = analysis
        except Exception as e:
            logger.error(f"Failed to analyze answer: {e}")
            turn.response_analysis = {"error": str(e)}

        await self.db.commit()
        await self.db.refresh(turn)
        return turn

    async def _get_prompt(self, flow: ClinicalEncounterFlow, prompt_type: str) -> str:
        """Get the appropriate prompt (doctor override > specialty > default)."""
        # Check for doctor override
        result = await self.db.execute(
            select(DoctorPromptOverride).where(
                and_(
                    DoctorPromptOverride.clinician_id == flow.clinician_id,
                    DoctorPromptOverride.is_active == True
                )
            )
        )
        doctor_override = result.scalar_one_or_none()

        if doctor_override:
            if prompt_type == "questioning" and doctor_override.questioning_prompt:
                return self._apply_style(doctor_override.questioning_prompt, doctor_override.question_style)
            elif prompt_type == "examination" and doctor_override.examination_prompt:
                return self._apply_style(doctor_override.examination_prompt, doctor_override.examination_style)
            elif prompt_type == "management_plan" and doctor_override.management_plan_prompt:
                return self._apply_style(doctor_override.management_plan_prompt, doctor_override.management_style)
            elif prompt_type == "documentation" and doctor_override.documentation_prompt:
                return doctor_override.documentation_prompt

        # Check for specialty prompt
        if flow.specialty_profile_id:
            from app.core.prompt_mappings.models import MdPromptMapping
            result = await self.db.execute(
                select(MdPromptMapping).where(
                    and_(
                        MdPromptMapping.specialty_profile_id == flow.specialty_profile_id,
                        MdPromptMapping.prompt_category == prompt_type.upper(),
                        MdPromptMapping.is_active == True
                    )
                )
            )
            specialty_prompt = result.scalar_one_or_none()
            if specialty_prompt:
                return specialty_prompt.prompt_template

        # Return default
        if prompt_type == "questioning":
            return DEFAULT_QUESTIONING_PROMPT
        elif prompt_type == "examination":
            return DEFAULT_EXAMINATION_PROMPT
        elif prompt_type == "management_plan":
            return DEFAULT_MANAGEMENT_PLAN_PROMPT
        elif prompt_type == "documentation":
            return DEFAULT_DOCUMENTATION_PROMPT
        return DEFAULT_QUESTIONING_PROMPT

    def _apply_style(self, prompt: str, style: Optional[str]) -> str:
        """Apply style modifications to prompt."""
        if not style:
            return prompt
        
        style_instructions = {
            "CONCISE": " Keep responses brief and to the point.",
            "DETAILED": " Provide comprehensive, detailed responses.",
            "FRIENDLY": " Use a warm, patient-friendly tone.",
            "PROFESSIONAL": " Maintain a strictly professional clinical tone."
        }
        
        instruction = style_instructions.get(style, "")
        return prompt + instruction

    async def _build_questioning_context(self, flow: ClinicalEncounterFlow, encounter_id: uuid.UUID) -> Dict[str, Any]:
        """Build context for question generation."""
        # Get previous question turns
        result = await self.db.execute(
            select(QuestionTurn).where(
                and_(
                    QuestionTurn.flow_id == flow.flow_id,
                    QuestionTurn.is_complete == True
                )
            ).order_by(QuestionTurn.turn_number)
        )
        previous_turns = result.scalars().all()

        conversation_history = []
        for turn in previous_turns:
            conversation_history.append({
                "question": turn.llm_question,
                "answer": turn.response_transcript,
                "analysis": turn.response_analysis
            })

        return {
            "chief_complaint": flow.chief_complaint_transcript,
            "question_count": flow.question_count,
            "conversation_history": conversation_history,
            "language": flow.chief_complaint_language or "en"
        }

    async def _analyze_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """Analyze the patient's answer using AI."""
        messages = [
            {
                "role": "system",
                "content": "Analyze the patient's answer and extract key clinical information. Respond with JSON: {\"key_findings\": [], \"follow_up_needed\": true/false, \"concerns\": []}"
            },
            {
                "role": "user",
                "content": f"Question: {question}\nAnswer: {answer}"
            }
        ]
        
        try:
            response = await grok_json(messages, max_tokens=200)
            return response
        except Exception as e:
            logger.error(f"Failed to analyze answer: {e}")
            return {"key_findings": [], "follow_up_needed": True, "concerns": []}


# ── Examination Guidance Service ─────────────────────────────────────────────

class ExaminationGuidanceService:
    """Manages the examination phase with AI-generated guidance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_guidance(self, flow_id: uuid.UUID, encounter_id: uuid.UUID) -> ExaminationGuidance:
        """Generate examination guidance using AI."""
        flow_service = ClinicalEncounterFlowService(self.db)
        flow = await flow_service.get_flow(flow_id)
        
        if not flow:
            raise ValueError("Flow not found")

        # Get prompt
        questioning_service = InteractiveQuestioningService(self.db)
        prompt = await questioning_service._get_prompt(flow, "examination")

        # Build context
        context = await self._build_examination_context(flow, encounter_id)

        # Generate guidance
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Clinical context:\n{json.dumps(context, indent=2, default=str)}"}
        ]

        try:
            response = await grok_json(messages, max_tokens=800)
        except Exception as e:
            logger.error(f"Failed to generate examination guidance: {e}")
            response = {
                "critical_examinations": [{"body_system": "General", "priority": "MEDIUM"}],
                "red_flags": [],
                "confidence": 0.5
            }

        guidance = ExaminationGuidance(
            flow_id=flow_id,
            encounter_id=encounter_id,
            critical_examinations=response.get("critical_examinations", []),
            examination_priorities=response.get("examination_priorities", []),
            specific_findings_to_look_for=response.get("specific_findings_to_look_for", []),
            red_flags=response.get("red_flags", []),
            prompt_used=prompt[:500],
            confidence_score=int(response.get("confidence", 0.7) * 100)
        )
        self.db.add(guidance)

        # Update flow
        flow.examination_guidance_shown = True

        await self.db.commit()
        await self.db.refresh(guidance)
        return guidance

    async def submit_examination_findings(
        self,
        flow_id: uuid.UUID,
        transcript: str,
        language: str = "en"
    ) -> ExaminationGuidance:
        """Submit examination findings and analyze them."""
        result = await self.db.execute(
            select(ExaminationGuidance).where(ExaminationGuidance.flow_id == flow_id)
        )
        guidance = result.scalar_one_or_none()
        
        if not guidance:
            raise ValueError("Examination guidance not found")

        guidance.examination_findings_transcript = transcript

        # Analyze findings
        try:
            structured_findings = await self._analyze_examination_findings(transcript)
            guidance.structured_findings = structured_findings
            guidance.examination_findings_analyzed = True
        except Exception as e:
            logger.error(f"Failed to analyze examination findings: {e}")

        await self.db.commit()
        await self.db.refresh(guidance)
        return guidance

    async def _build_examination_context(self, flow: ClinicalEncounterFlow, encounter_id: uuid.UUID) -> Dict[str, Any]:
        """Build context for examination guidance."""
        questioning_service = InteractiveQuestioningService(self.db)
        
        # Get conversation history
        result = await self.db.execute(
            select(QuestionTurn).where(
                and_(
                    QuestionTurn.flow_id == flow.flow_id,
                    QuestionTurn.is_complete == True
                )
            ).order_by(QuestionTurn.turn_number)
        )
        previous_turns = result.scalars().all()

        conversation_summary = []
        for turn in previous_turns:
            conversation_summary.append(f"Q: {turn.llm_question}\nA: {turn.response_transcript}")

        return {
            "chief_complaint": flow.chief_complaint_transcript,
            "conversation_summary": "\n\n".join(conversation_summary),
            "question_count": flow.question_count
        }

    async def _analyze_examination_findings(self, transcript: str) -> Dict[str, Any]:
        """Analyze examination findings using AI."""
        messages = [
            {
                "role": "system",
                "content": "Extract structured examination findings from the transcript. Respond with JSON: {\"body_systems\": {}, \"abnormal_findings\": [], \"normal_findings\": []}"
            },
            {
                "role": "user",
                "content": f"Examination findings:\n{transcript}"
            }
        ]
        
        try:
            response = await grok_json(messages, max_tokens=500)
            return response
        except Exception as e:
            logger.error(f"Failed to analyze examination findings: {e}")
            return {"body_systems": {}, "abnormal_findings": [], "normal_findings": []}


# ── Management Plan Service ─────────────────────────────────────────────────

class ManagementPlanService:
    """Manages the management plan generation and editing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_plan(self, flow_id: uuid.UUID, encounter_id: uuid.UUID) -> ManagementPlan:
        """Generate a management plan using AI."""
        flow_service = ClinicalEncounterFlowService(self.db)
        flow = await flow_service.get_flow(flow_id)
        
        if not flow:
            raise ValueError("Flow not found")

        # Get prompt
        questioning_service = InteractiveQuestioningService(self.db)
        prompt = await questioning_service._get_prompt(flow, "management_plan")

        # Build context
        context = await self._build_management_context(flow, encounter_id)

        # Generate plan
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Complete clinical context:\n{json.dumps(context, indent=2, default=str)}"}
        ]

        try:
            response = await grok_json(messages, max_tokens=1500)
        except Exception as e:
            logger.error(f"Failed to generate management plan: {e}")
            response = {
                "diagnoses": [],
                "medications": [],
                "lab_orders": [],
                "imaging": [],
                "follow_up": [],
                "confidence": 0.5
            }

        plan = ManagementPlan(
            flow_id=flow_id,
            encounter_id=encounter_id,
            original_plan=response,
            original_plan_text=json.dumps(response, indent=2),
            current_plan=response,
            current_plan_text=json.dumps(response, indent=2),
            suggested_diagnoses=response.get("diagnoses", []),
            suggested_medications=response.get("medications", []),
            suggested_lab_orders=response.get("lab_orders", []),
            suggested_imaging=response.get("imaging", []),
            suggested_procedures=response.get("procedures", []),
            follow_up_recommendations=response.get("follow_up", []),
            prompt_used=prompt[:500],
            confidence_score=int(response.get("confidence", 0.7) * 100)
        )
        self.db.add(plan)

        # Update flow
        flow.management_plan_generated = True

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def update_plan(self, plan_id: uuid.UUID, data: ManagementPlanUpdate) -> Optional[ManagementPlan]:
        """Update the management plan (doctor modifications)."""
        result = await self.db.execute(
            select(ManagementPlan).where(ManagementPlan.plan_id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None

        if data.current_plan is not None:
            plan.current_plan = data.current_plan
        if data.current_plan_text is not None:
            plan.current_plan_text = data.current_plan_text
        if data.is_accepted is not None:
            plan.is_accepted = data.is_accepted
        if data.is_modified is not None:
            plan.is_modified = data.is_modified
        if data.modification_notes is not None:
            plan.modification_notes = data.modification_notes

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def _build_management_context(self, flow: ClinicalEncounterFlow, encounter_id: uuid.UUID) -> Dict[str, Any]:
        """Build complete context for management plan generation."""
        # Get all conversation
        result = await self.db.execute(
            select(QuestionTurn).where(
                QuestionTurn.flow_id == flow.flow_id
            ).order_by(QuestionTurn.turn_number)
        )
        question_turns = result.scalars().all()

        conversation = []
        for turn in question_turns:
            conversation.append({
                "question": turn.llm_question,
                "answer": turn.response_transcript
            })

        # Get examination findings
        exam_result = await self.db.execute(
            select(ExaminationGuidance).where(ExaminationGuidance.flow_id == flow.flow_id)
        )
        exam_guidance = exam_result.scalar_one_or_none()

        return {
            "chief_complaint": flow.chief_complaint_transcript,
            "questioning_history": conversation,
            "examination_findings": exam_guidance.structured_findings if exam_guidance else {},
            "examination_transcript": exam_guidance.examination_findings_transcript if exam_guidance else None
        }


# ── Doctor Prompt Service ───────────────────────────────────────────────────

class DoctorPromptService:
    """Manages doctor-level prompt overrides."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_override(self, data: DoctorPromptOverrideCreate) -> DoctorPromptOverride:
        """Create a doctor prompt override."""
        override = DoctorPromptOverride(**data.model_dump())
        self.db.add(override)
        await self.db.commit()
        await self.db.refresh(override)
        return override

    async def get_override(self, clinician_id: uuid.UUID) -> Optional[DoctorPromptOverride]:
        """Get a doctor's prompt override."""
        result = await self.db.execute(
            select(DoctorPromptOverride).where(
                and_(
                    DoctorPromptOverride.clinician_id == clinician_id,
                    DoctorPromptOverride.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_override(self, override_id: uuid.UUID, data: DoctorPromptOverrideUpdate) -> Optional[DoctorPromptOverride]:
        """Update a doctor prompt override."""
        result = await self.db.execute(
            select(DoctorPromptOverride).where(DoctorPromptOverride.override_id == override_id)
        )
        override = result.scalar_one_or_none()
        
        if not override:
            return None

        if data.questioning_prompt is not None:
            override.questioning_prompt = data.questioning_prompt
        if data.examination_prompt is not None:
            override.examination_prompt = data.examination_prompt
        if data.management_plan_prompt is not None:
            override.management_plan_prompt = data.management_plan_prompt
        if data.documentation_prompt is not None:
            override.documentation_prompt = data.documentation_prompt
        if data.prompt_variables is not None:
            override.prompt_variables = data.prompt_variables
        if data.question_style is not None:
            override.question_style = data.question_style
        if data.examination_style is not None:
            override.examination_style = data.examination_style
        if data.management_style is not None:
            override.management_style = data.management_style
        if data.is_active is not None:
            override.is_active = data.is_active

        await self.db.commit()
        await self.db.refresh(override)
        return override
