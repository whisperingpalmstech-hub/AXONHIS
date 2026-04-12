import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import (
    RpiwAiContext, RpiwAiSuggestion, RpiwAiAlert, RpiwAiFeedback, RpiwAiActivityLog
)
from .schemas import AiContextCreate, AiFeedbackCreate

class RpiwAiService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _log_ai_activity(self, patient_uhid: str, user_id: str, role_code: str, event_type: str, reference_id: str = None, payload: dict = None):
        """Write to immutable AI Activity Log."""
        log = RpiwAiActivityLog(
            patient_uhid=patient_uhid,
            user_id=user_id,
            role_code=role_code,
            event_type=event_type,
            reference_id=reference_id,
            metadata_payload=payload
        )
        self.db.add(log)
        await self.db.flush()

    async def gather_context_and_generate(self, patient_uhid: str, user_id: str, role_code: str) -> dict:
        """
        1. Create an AI context snapshot for the user role.
        2. Detect clinical risks.
        3. Generate relevant suggestions.
        """
        # --- MOCK CONTEXT BUILDER ---
        # In a real app, this queries `rpiw_summary_vitals`, `rpiw_clinical_notes`, etc.
        # We simulate the gathered context for demonstration.
        context_data = {
            "patient_uhid": patient_uhid,
            "user_id": user_id,
            "role_code": role_code,
            "clinical_summary": "Patient presented with fever and hypotension. Admitted for observation.",
            "recent_vitals": {"bp": "90/60", "hr": 110, "temp": 38.9},
            "active_medications": [{"drug": "Paracetamol"}],
            "latest_labs": {"wbc": 18.5, "lactate": 2.1} # High WBC indicating infection
        }
        
        # 1. Save Context Map
        ctx = RpiwAiContext(**context_data)
        self.db.add(ctx)
        await self.db.flush()
        
        await self._log_ai_activity(patient_uhid, user_id, role_code, "ContextAnalyzed", str(ctx.id), {"timestamp": ctx.analyzed_at.isoformat()})

        generated_responses = {
            "alerts": [],
            "suggestions": []
        }

        # 2. Route to specific Agent logic based on role
        if role_code == "doctor":
            generated_responses = await self._doctor_agent(ctx)
        elif role_code == "nurse":
            generated_responses = await self._nurse_agent(ctx)
        elif role_code == "phlebotomist":
            generated_responses = await self._phlebotomist_agent(ctx)

        await self.db.commit()
        return generated_responses


    async def _doctor_agent(self, ctx: RpiwAiContext) -> dict:
        """AI Engine tailored to Physicians."""
        # Risk Detection (e.g. Sepsis profile from vitals & labs)
        alert = RpiwAiAlert(
            patient_uhid=ctx.patient_uhid,
            target_role="doctor",
            risk_category="AbnormalPattern",
            severity="High",
            message="Critical: Patient combination of hypotension (BP 90/60) and high WBC (18.5) strongly indicates systemic infection (Sepsis)."
        )
        self.db.add(alert)
        await self.db.flush()

        # Suggestion 1: Differential and Investigations
        sugg_1 = RpiwAiSuggestion(
            context_id=ctx.id,
            patient_uhid=ctx.patient_uhid,
            user_id=ctx.user_id,
            target_role="doctor",
            suggestion_type="OrderRecommendation",
            title="Suggested Investigations for Sepsis",
            content="Based on the vital trends and high WBC, consider ordering Blood Cultures and Procalcitonin immediately.",
            structured_data={
                "action_type": "order", 
                "payload": {"order_category": "laboratory", "item_code": "LAB-BC", "item_name": "Blood Culture", "priority": "STAT"}
            }
        )
        
        # Suggestion 2: Draft Clinical Note
        sugg_2 = RpiwAiSuggestion(
            context_id=ctx.id,
            patient_uhid=ctx.patient_uhid,
            user_id=ctx.user_id,
            target_role="doctor",
            suggestion_type="DraftNote",
            title="Draft Progress Note",
            content="Patient exhibits signs of sepsis (hypotensive, febrile, elevated WBC). Will initiate sepsis bundle.",
            structured_data={
                "action_type": "note", 
                "payload": {"note_type": "Progress", "content": "Patient exhibits signs of sepsis (hypotensive, febrile, elevated WBC). Will initiate sepsis bundle."}
            }
        )
        
        self.db.add_all([sugg_1, sugg_2])
        await self.db.flush()
        
        await self._log_ai_activity(ctx.patient_uhid, ctx.user_id, "doctor", "SuggestionsGenerated", str(ctx.id))
        
        return {"alerts": [alert], "suggestions": [sugg_1, sugg_2]}

    async def _nurse_agent(self, ctx: RpiwAiContext) -> dict:
        """AI Engine tailored to Nursing Staff."""
        alert = RpiwAiAlert(
            patient_uhid=ctx.patient_uhid,
            target_role="nurse",
            risk_category="AbnormalVitals",
            severity="High",
            message="Early Warning Score elevated. Blood pressure dropping persistently."
        )
        self.db.add(alert)
        await self.db.flush()

        sugg = RpiwAiSuggestion(
            context_id=ctx.id,
            patient_uhid=ctx.patient_uhid,
            user_id=ctx.user_id,
            target_role="nurse",
            suggestion_type="CareProtocol",
            title="Suggested Care Action",
            content="Repeat vitals and notify the attending doctor immediately.",
            structured_data={
                "action_type": "task",
                "payload": {"assigned_role": "nurse", "task_description": "Repeat vitals now", "priority": "STAT"}
            }
        )
        self.db.add(sugg)
        await self.db.flush()
        await self._log_ai_activity(ctx.patient_uhid, ctx.user_id, "nurse", "SuggestionsGenerated", str(ctx.id))
        return {"alerts": [alert], "suggestions": [sugg]}


    async def _phlebotomist_agent(self, ctx: RpiwAiContext) -> dict:
        """AI Engine tailored to Phlebotomists."""
        sugg = RpiwAiSuggestion(
            context_id=ctx.id,
            patient_uhid=ctx.patient_uhid,
            user_id=ctx.user_id,
            target_role="phlebotomist",
            suggestion_type="TaskPrioritization",
            title="Priority Sample Execution",
            content="STAT Blood Culture requested for this patient. Prioritize collection.",
            structured_data=None # Phlebotomists typically execute existing tasks, not create new ones from AI
        )
        self.db.add(sugg)
        await self.db.flush()
        await self._log_ai_activity(ctx.patient_uhid, ctx.user_id, "phlebotomist", "SuggestionsGenerated", str(ctx.id))
        return {"alerts": [], "suggestions": [sugg]}


    async def handle_suggestion_action(self, suggestion_id: str, action: str, user_id: str, role_code: str):
        """User Accepts/Rejects an AI suggestion."""
        query = select(RpiwAiSuggestion).where(RpiwAiSuggestion.id == suggestion_id)
        result = await self.db.execute(query)
        sugg = result.scalars().first()
        if not sugg:
            return None
        
        sugg.status = "Accepted" if action.lower() == "accept" else "Rejected"
        sugg.resolved_at = datetime.now(timezone.utc)
        
        await self._log_ai_activity(sugg.patient_uhid, user_id, role_code, f"Suggestion{sugg.status}", str(sugg.id))
        await self.db.commit()
        return sugg

    async def submit_feedback(self, suggestion_id: str, feedback: AiFeedbackCreate):
        """User provides manual rating on AI utility."""
        fb = RpiwAiFeedback(
            suggestion_id=suggestion_id,
            user_id=feedback.user_id,
            feedback_rating=feedback.feedback_rating,
            comments=feedback.comments
        )
        self.db.add(fb)
        await self.db.commit()
        return fb

    async def get_patient_ai_state(self, patient_uhid: str, role_code: str):
         """Fetch active (unresolved) suggestions and alerts for a role & patient."""
         s_query = select(RpiwAiSuggestion).where(
             RpiwAiSuggestion.patient_uhid == patient_uhid,
             RpiwAiSuggestion.target_role == role_code,
             RpiwAiSuggestion.status == "Pending"
         ).order_by(RpiwAiSuggestion.created_at.desc())
         s_res = await self.db.execute(s_query)
         suggestions = s_res.scalars().all()

         a_query = select(RpiwAiAlert).where(
             RpiwAiAlert.patient_uhid == patient_uhid,
             RpiwAiAlert.target_role == role_code,
             RpiwAiAlert.is_acknowledged == False
         ).order_by(RpiwAiAlert.detected_at.desc())
         a_res = await self.db.execute(a_query)
         alerts = a_res.scalars().all()

         return {"suggestions": suggestions, "alerts": alerts}
