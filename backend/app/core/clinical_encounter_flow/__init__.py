"""
Clinical Encounter Flow Service - AI-Powered Interactive Clinical Consultation

Implements the complete clinical encounter workflow:
1. Patient complaint capture via voice
2. LLM-driven interactive questioning (one question at a time)
3. Transition to examination phase with AI suggestions
4. Management plan generation and editing
5. Document generation from audio transcript
6. Specialty and doctor-level prompt management
"""

from .models import (
    ClinicalEncounterFlow,
    EncounterPhase,
    QuestionTurn,
    ExaminationGuidance,
    ManagementPlan,
    DoctorPromptOverride
)
from .schemas import (
    ClinicalEncounterFlowCreate,
    ClinicalEncounterFlowUpdate,
    QuestionTurnCreate,
    QuestionTurnResponse,
    ExaminationGuidanceCreate,
    ManagementPlanCreate,
    ManagementPlanUpdate,
    DoctorPromptOverrideCreate,
    DoctorPromptOverrideResponse
)
from .services import (
    ClinicalEncounterFlowService,
    InteractiveQuestioningService,
    ExaminationGuidanceService,
    ManagementPlanService,
    DoctorPromptService
)

__all__ = [
    "ClinicalEncounterFlow",
    "EncounterPhase",
    "QuestionTurn",
    "ExaminationGuidance",
    "ManagementPlan",
    "DoctorPromptOverride",
    "ClinicalEncounterFlowCreate",
    "ClinicalEncounterFlowUpdate",
    "QuestionTurnCreate",
    "QuestionTurnResponse",
    "ExaminationGuidanceCreate",
    "ManagementPlanCreate",
    "ManagementPlanUpdate",
    "DoctorPromptOverrideCreate",
    "DoctorPromptOverrideResponse",
    "ClinicalEncounterFlowService",
    "InteractiveQuestioningService",
    "ExaminationGuidanceService",
    "ManagementPlanService",
    "DoctorPromptService"
]
