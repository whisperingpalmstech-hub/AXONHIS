"""
AXONHIS Virtual Avatar – Core Services.

Components:
  SpeechService         – Google Cloud STT / TTS
  ConversationService   – Grok LLM intent detection & response generation
  WorkflowOrchestrator  – Dispatches to AXONHIS APIs
  AvatarSessionService  – Session & message CRUD + analytics
"""
from __future__ import annotations

import base64
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.avatar.models import AvatarMessage, AvatarSession, AvatarWorkflowConfig

logger = logging.getLogger("avatar")

# ─── Language → Google Cloud voice mapping ────────────────────────────────────
LANGUAGE_VOICE_MAP: dict[str, dict[str, str]] = {
    "en": {"code": "en-US", "voice": "en-US-Studio-O", "gender": "FEMALE"},
    "hi": {"code": "hi-IN", "voice": "hi-IN-Wavenet-A", "gender": "FEMALE"},
    "mr": {"code": "mr-IN", "voice": "mr-IN-Wavenet-A", "gender": "FEMALE"},
    "es": {"code": "es-ES", "voice": "es-ES-Wavenet-C", "gender": "FEMALE"},
    "de": {"code": "de-DE", "voice": "de-DE-Wavenet-C", "gender": "FEMALE"},
    "fr": {"code": "fr-FR", "voice": "fr-FR-Wavenet-C", "gender": "FEMALE"},
    "ar": {"code": "ar-XA", "voice": "ar-XA-Wavenet-A", "gender": "FEMALE"},
    "zh": {"code": "cmn-CN", "voice": "cmn-CN-Wavenet-A", "gender": "FEMALE"},
    "ja": {"code": "ja-JP", "voice": "ja-JP-Wavenet-B", "gender": "FEMALE"},
    "pt": {"code": "pt-BR", "voice": "pt-BR-Wavenet-A", "gender": "FEMALE"},
    "ru": {"code": "ru-RU", "voice": "ru-RU-Wavenet-C", "gender": "FEMALE"},
}

# ─── Default system prompt for the avatar LLM ────────────────────────────────
AVATAR_SYSTEM_PROMPT = """You are Dr. AXON, a friendly, professional AI healthcare assistant avatar at a hospital kiosk.
You help patients and visitors with hospital services. You speak naturally, concisely, and warmly.

You can help with these workflows:
1. **patient_registration** – Register new patients (collect name, age, gender, phone, ID, address, emergency contact)
2. **appointment_booking** – Book OPD appointments (ask department/doctor, show available slots, confirm booking)
3. **opd_triage** – Collect pre-visit symptom info (chief complaint, duration, pain score, allergies, medical history)
4. **billing_assistant** – Show billing details, explain charges, guide through payment
5. **lab_booking** – Schedule lab tests, provide preparation instructions
6. **discharge_education** – Explain discharge summary, medications, diet, follow-up appointments
7. **hospital_navigation** – Give directions to departments, facilities, rooms

RULES:
- Always respond in the user's language.
- Be concise. Keep responses under 3 sentences unless explaining something detailed.
- When you detect the user wants a specific workflow, respond with a JSON block at the END of your message:
  ```json
  {"intent": "workflow_name", "entities": {"key": "value"}, "step": "current_step"}
  ```
- Extract entities naturally from conversation (patient name, phone, department, symptoms, etc.)
- If the user's request is unclear, ask a clarifying question.
- Always be empathetic, especially when discussing health concerns.
- For greetings, warmly welcome and ask how you can help today.
- Never provide medical diagnoses or treatment advice. Only collect information and route to workflows.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Speech Service — Google Cloud STT / TTS
# ═══════════════════════════════════════════════════════════════════════════════


class SpeechService:
    """Wraps Google Cloud Speech-to-Text and Text-to-Speech REST APIs."""

    def __init__(self):
        self._credentials_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
            "project-03342299-7d3e-4148-af4-7af3c52ca278.json",
        )
        self._token: str | None = None
        self._token_expiry: datetime | None = None

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token from service account credentials."""
        if self._token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._token

        import json as _json
        import time

        from jose import jwt as jose_jwt

        with open(self._credentials_path) as f:
            creds = _json.load(f)

        now = int(time.time())
        payload = {
            "iss": creds["client_email"],
            "sub": creds["client_email"],
            "aud": creds["token_uri"],
            "iat": now,
            "exp": now + 3600,
            "scope": "https://www.googleapis.com/auth/cloud-platform",
        }

        signed_jwt = jose_jwt.encode(payload, creds["private_key"], algorithm="RS256")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                creds["token_uri"],
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": signed_jwt,
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

        self._token = token_data["access_token"]
        self._token_expiry = datetime.utcnow() + timedelta(seconds=3500)
        return self._token  # type: ignore[return-value]

    async def speech_to_text(self, audio_base64: str, language: str = "en") -> dict[str, Any]:
        """Convert audio to text using Google Cloud Speech-to-Text."""
        lang_config = LANGUAGE_VOICE_MAP.get(language, LANGUAGE_VOICE_MAP["en"])
        token = await self._get_access_token()

        request_body = {
            "config": {
                "encoding": "WEBM_OPUS",
                "sampleRateHertz": 48000,
                "languageCode": lang_config["code"],
                "enableAutomaticPunctuation": True,
                "model": "latest_long",
                "alternativeLanguageCodes": ["en-US", "hi-IN"],
            },
            "audio": {"content": audio_base64},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://speech.googleapis.com/v1/speech:recognize",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        if not results:
            return {"transcription": "", "confidence": 0.0, "language": language}

        best = results[0]["alternatives"][0]
        return {
            "transcription": best.get("transcript", ""),
            "confidence": best.get("confidence", 0.0),
            "language": language,
        }

    async def text_to_speech(self, text: str, language: str = "en") -> str:
        """Convert text to speech using Google Cloud TTS. Returns base64 audio."""
        lang_config = LANGUAGE_VOICE_MAP.get(language, LANGUAGE_VOICE_MAP["en"])
        token = await self._get_access_token()

        request_body = {
            "input": {"text": text},
            "voice": {
                "languageCode": lang_config["code"],
                "name": lang_config["voice"],
                "ssmlGender": lang_config["gender"],
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 0.95,
                "pitch": 0.0,
                "effectsProfileId": ["large-home-entertainment-class-device"],
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://texttospeech.googleapis.com/v1/text:synthesize",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("audioContent", "")


# ═══════════════════════════════════════════════════════════════════════════════
# Conversation Service — Grok / Groq LLM
# ═══════════════════════════════════════════════════════════════════════════════


class ConversationService:
    """Manages Grok LLM interactions for intent detection and response generation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = settings.grok_api_key
        self.model = settings.grok_model
        self.base_url = settings.grok_base_url

    async def _get_conversation_history(self, session_id: uuid.UUID, limit: int = 20) -> list[dict]:
        """Get recent messages for context."""
        result = await self.db.execute(
            select(AvatarMessage)
            .where(AvatarMessage.session_id == session_id)
            .order_by(AvatarMessage.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        messages.reverse()
        return [{"role": m.role, "content": m.content} for m in messages]

    async def _get_session(self, session_id: uuid.UUID) -> AvatarSession | None:
        result = await self.db.execute(
            select(AvatarSession).where(AvatarSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def process_message(
        self,
        session_id: uuid.UUID,
        user_text: str,
        language: str = "en",
    ) -> dict[str, Any]:
        """Send user text to Grok LLM and get structured response."""
        session = await self._get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        history = await self._get_conversation_history(session_id)

        # Build system prompt with workflow context
        system_prompt = AVATAR_SYSTEM_PROMPT
        if session.current_workflow and session.workflow_data:
            system_prompt += f"\n\nCurrent active workflow: {session.current_workflow}"
            system_prompt += f"\nWorkflow state: {session.workflow_data}"
            system_prompt += "\nContinue this workflow. Ask for the next required field."

        if language != "en":
            lang_name = {
                "hi": "Hindi", "mr": "Marathi", "es": "Spanish", "de": "German",
                "fr": "French", "ar": "Arabic", "zh": "Chinese", "ja": "Japanese",
                "pt": "Portuguese", "ru": "Russian",
            }.get(language, "English")
            system_prompt += f"\n\nIMPORTANT: The user is speaking in {lang_name}. Respond in {lang_name}."

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})

        # Call Grok / Groq
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        response_text = data["choices"][0]["message"]["content"]

        # Parse intent / entities from response
        intent = None
        entities = {}
        workflow = None

        try:
            # Look for JSON block in response
            if "```json" in response_text:
                json_start = response_text.index("```json") + 7
                json_end = response_text.index("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                parsed = json.loads(json_str)
                intent = parsed.get("intent")
                entities = parsed.get("entities", {})
                workflow = intent
                # Remove JSON block from displayed text
                response_text = (
                    response_text[:response_text.index("```json")]
                    + response_text[json_end + 3:]
                ).strip()
            elif '{"intent"' in response_text:
                # Try inline JSON
                json_start = response_text.index('{"intent"')
                json_str = response_text[json_start:]
                # Find the closing brace
                brace_count = 0
                end_idx = 0
                for i, c in enumerate(json_str):
                    if c == "{":
                        brace_count += 1
                    elif c == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                if end_idx > 0:
                    parsed = json.loads(json_str[:end_idx])
                    intent = parsed.get("intent")
                    entities = parsed.get("entities", {})
                    workflow = intent
                    response_text = response_text[:json_start].strip()
        except (json.JSONDecodeError, ValueError):
            pass  # No parseable intent block

        return {
            "response_text": response_text,
            "intent": intent,
            "entities": entities,
            "workflow": workflow,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Workflow Orchestrator — Routes intents to AXONHIS APIs
# ═══════════════════════════════════════════════════════════════════════════════


class WorkflowOrchestrator:
    """Dispatches detected intents to the appropriate AXONHIS backend services."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(
        self,
        session: AvatarSession,
        intent: str | None,
        entities: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute workflow step based on intent and entities."""
        if not intent:
            return {"status": "no_workflow", "message": "General conversation"}

        handlers = {
            "patient_registration": self._handle_registration,
            "appointment_booking": self._handle_appointment,
            "opd_triage": self._handle_triage,
            "billing_assistant": self._handle_billing,
            "lab_booking": self._handle_lab,
            "discharge_education": self._handle_discharge,
            "hospital_navigation": self._handle_navigation,
        }

        handler = handlers.get(intent)
        if not handler:
            return {"status": "unknown_workflow", "message": f"Unknown workflow: {intent}"}

        try:
            result = await handler(session, entities)
            # Update session workflow state
            session.current_workflow = intent
            session.workflow_step = (session.workflow_step or 0) + 1
            session.workflow_data = json.dumps(
                {**(json.loads(session.workflow_data) if session.workflow_data else {}), **entities}
            )
            await self.db.commit()
            return result
        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _handle_registration(
        self, session: AvatarSession, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """Patient registration workflow."""
        collected = json.loads(session.workflow_data) if session.workflow_data else {}
        collected.update(entities)

        required_fields = ["first_name", "last_name", "age", "gender", "mobile"]
        missing = [f for f in required_fields if f not in collected]

        if missing:
            return {
                "status": "collecting",
                "workflow": "patient_registration",
                "collected": collected,
                "missing_fields": missing,
                "message": f"Still need: {', '.join(missing)}",
            }

        # Check for duplicates via existing patient query
        try:
            dup_check = await self.db.execute(
                text(
                    "SELECT id, first_name, last_name FROM patients "
                    "WHERE LOWER(first_name) = LOWER(:fn) AND LOWER(last_name) = LOWER(:ln) "
                    "LIMIT 1"
                ),
                {"fn": collected["first_name"], "ln": collected["last_name"]},
            )
            existing = dup_check.first()
            if existing:
                return {
                    "status": "duplicate_found",
                    "workflow": "patient_registration",
                    "existing_patient_id": str(existing[0]),
                    "message": f"Patient {existing[1]} {existing[2]} already exists.",
                }
        except Exception:
            pass

        # Create patient via direct DB insert (mirrors registration service)
        try:
            patient_id = uuid.uuid4()
            patient_uuid = f"AVTR-{str(patient_id)[:8].upper()}"
            
            # Fetch user's org_id to ensure tenant isolation works and patient shows up in UI
            user_res = await self.db.execute(
                text("SELECT org_id FROM users WHERE id = :uid"), 
                {"uid": session.user_id}
            )
            org_id = user_res.scalar()

            await self.db.execute(
                text(
                    "INSERT INTO patients (id, patient_uuid, first_name, last_name, date_of_birth, gender, primary_phone, status, org_id) "
                    "VALUES (:id, :puuid, :fn, :ln, :dob, :gender, :phone, 'active', :org_id)"
                ),
                {
                    "id": str(patient_id),
                    "puuid": patient_uuid,
                    "fn": collected["first_name"],
                    "ln": collected["last_name"],
                    "dob": collected.get("date_of_birth", "2000-01-01"),
                    "gender": collected.get("gender", "other"),
                    "phone": collected.get("mobile", ""),
                    "org_id": str(org_id) if org_id else None,
                },
            )
            await self.db.commit()

            session.patient_id = patient_id
            return {
                "status": "completed",
                "workflow": "patient_registration",
                "patient_id": str(patient_id),
                "message": f"Patient {collected['first_name']} {collected['last_name']} registered successfully!",
            }
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {
                "status": "error",
                "workflow": "patient_registration",
                "message": f"Registration failed: {e}",
            }

    async def _handle_appointment(
        self, session: AvatarSession, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """Appointment booking workflow."""
        collected = json.loads(session.workflow_data) if session.workflow_data else {}
        collected.update(entities)

        if "department" not in collected:
            # Get available departments
            try:
                result = await self.db.execute(
                    text("SELECT DISTINCT department FROM doctor_calendars WHERE is_active = true")
                )
                departments = [r[0] for r in result.fetchall()]
                return {
                    "status": "collecting",
                    "workflow": "appointment_booking",
                    "available_departments": departments,
                    "message": "Please select a department.",
                }
            except Exception:
                return {
                    "status": "collecting",
                    "workflow": "appointment_booking",
                    "missing_fields": ["department"],
                    "message": "Which department would you like to visit?",
                }

        if "slot_date" not in collected:
            return {
                "status": "collecting",
                "workflow": "appointment_booking",
                "collected": collected,
                "missing_fields": ["slot_date"],
                "message": "What date would you like to book for?",
            }

        # Try to find available slots
        try:
            result = await self.db.execute(
                text(
                    "SELECT cs.id, cs.start_time, cs.end_time, cs.doctor_id "
                    "FROM calendar_slots cs "
                    "JOIN doctor_calendars dc ON cs.calendar_id = dc.id "
                    "WHERE dc.department = :dept AND cs.slot_date = :sdate "
                    "AND cs.status = 'available' "
                    "ORDER BY cs.start_time LIMIT 5"
                ),
                {"dept": collected["department"], "sdate": collected["slot_date"]},
            )
            slots = [
                {"id": str(r[0]), "start": str(r[1]), "end": str(r[2]), "doctor_id": str(r[3])}
                for r in result.fetchall()
            ]
            if slots:
                return {
                    "status": "slots_available",
                    "workflow": "appointment_booking",
                    "available_slots": slots,
                    "message": f"Found {len(slots)} available slots.",
                }
            return {
                "status": "no_slots",
                "workflow": "appointment_booking",
                "message": "No available slots found for this date. Try another date?",
            }
        except Exception as e:
            return {
                "status": "info",
                "workflow": "appointment_booking",
                "collected": collected,
                "message": f"Appointment system query: {collected['department']} on {collected['slot_date']}",
            }

    async def _handle_triage(
        self, session: AvatarSession, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """OPD pre-triage data collection."""
        collected = json.loads(session.workflow_data) if session.workflow_data else {}
        collected.update(entities)

        required = ["chief_complaint"]
        optional = ["duration", "pain_score", "allergies", "medical_history", "medications"]
        missing = [f for f in required if f not in collected]

        if missing:
            return {
                "status": "collecting",
                "workflow": "opd_triage",
                "collected": collected,
                "missing_fields": missing,
                "message": f"Please describe your main concern/complaint.",
            }

        return {
            "status": "completed",
            "workflow": "opd_triage",
            "triage_data": collected,
            "message": "Triage information collected. A nurse will review this before your consultation.",
        }

    async def _handle_billing(
        self, session: AvatarSession, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """Billing assistant workflow."""
        patient_id = entities.get("patient_id") or (str(session.patient_id) if session.patient_id else None)

        if not patient_id:
            return {
                "status": "collecting",
                "workflow": "billing_assistant",
                "missing_fields": ["patient_id"],
                "message": "Please provide your patient ID or UHID to look up billing details.",
            }

        try:
            result = await self.db.execute(
                text(
                    "SELECT id, total_amount, paid_amount, status FROM invoices "
                    "WHERE patient_id = :pid ORDER BY created_at DESC LIMIT 5"
                ),
                {"pid": patient_id},
            )
            invoices = [
                {"id": str(r[0]), "total": float(r[1]), "paid": float(r[2]), "status": r[3]}
                for r in result.fetchall()
            ]
            return {
                "status": "info",
                "workflow": "billing_assistant",
                "invoices": invoices,
                "message": f"Found {len(invoices)} billing records.",
            }
        except Exception:
            return {
                "status": "info",
                "workflow": "billing_assistant",
                "message": "Billing information is being retrieved. Please visit the billing counter for payment.",
            }

    async def _handle_lab(
        self, session: AvatarSession, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """Lab booking workflow."""
        collected = json.loads(session.workflow_data) if session.workflow_data else {}
        collected.update(entities)

        if "test_name" not in collected:
            try:
                result = await self.db.execute(
                    text("SELECT id, name, category FROM lab_tests WHERE is_active = true LIMIT 20")
                )
                tests = [{"id": str(r[0]), "name": r[1], "category": r[2]} for r in result.fetchall()]
                return {
                    "status": "collecting",
                    "workflow": "lab_booking",
                    "available_tests": tests,
                    "message": "Which lab test would you like to schedule?",
                }
            except Exception:
                return {
                    "status": "collecting",
                    "workflow": "lab_booking",
                    "missing_fields": ["test_name"],
                    "message": "Which lab test would you like to schedule? Common tests include CBC, Blood Sugar, Lipid Profile, Thyroid Panel.",
                }

        return {
            "status": "info",
            "workflow": "lab_booking",
            "collected": collected,
            "message": f"Lab test '{collected['test_name']}' noted. Please visit the sample collection center. Remember to fast for 8-12 hours if it's a fasting test.",
        }

    async def _handle_discharge(
        self, session: AvatarSession, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """Discharge education workflow."""
        patient_id = entities.get("patient_id") or (str(session.patient_id) if session.patient_id else None)

        if not patient_id:
            return {
                "status": "collecting",
                "workflow": "discharge_education",
                "missing_fields": ["patient_id"],
                "message": "Please provide your patient ID to access discharge instructions.",
            }

        return {
            "status": "info",
            "workflow": "discharge_education",
            "message": "Your discharge summary includes medication instructions, dietary guidelines, and follow-up appointments. Would you like me to explain any specific section?",
        }

    async def _handle_navigation(
        self, session: AvatarSession, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """Hospital navigation workflow."""
        location = entities.get("destination") or entities.get("department") or entities.get("location")

        navigation_map = {
            "emergency": "Ground Floor, West Wing - Follow the RED signs",
            "er": "Ground Floor, West Wing - Follow the RED signs",
            "opd": "Ground Floor, Main Building - Follow the BLUE signs",
            "pharmacy": "Ground Floor, Near Main Entrance - Counter 1-4",
            "laboratory": "1st Floor, East Wing - Take elevator to Level 1",
            "lab": "1st Floor, East Wing - Take elevator to Level 1",
            "radiology": "1st Floor, West Wing - Near the elevator",
            "billing": "Ground Floor, Main Reception Area",
            "cafeteria": "2nd Floor, Central Building",
            "icu": "3rd Floor, North Wing - Restricted access",
            "ot": "3rd Floor, South Wing - Restricted access",
            "wards": "2nd-4th Floor, Main Building",
            "parking": "Basement Level B1 and B2",
            "reception": "Ground Floor, Main Entrance",
        }

        if not location:
            return {
                "status": "collecting",
                "workflow": "hospital_navigation",
                "available_locations": list(navigation_map.keys()),
                "message": "Where would you like to go? I can give you directions to any department.",
            }

        direction = None
        for key, val in navigation_map.items():
            if key in location.lower():
                direction = val
                break

        if direction:
            return {
                "status": "completed",
                "workflow": "hospital_navigation",
                "destination": location,
                "directions": direction,
                "message": f"To reach {location}: {direction}",
            }

        return {
            "status": "info",
            "workflow": "hospital_navigation",
            "message": f"Directions for '{location}': Please ask at the main reception desk for specific room numbers.",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Avatar Session Service — Session CRUD + Analytics
# ═══════════════════════════════════════════════════════════════════════════════


class AvatarSessionService:
    """Manages avatar session lifecycle, messages, and analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: uuid.UUID, language: str = "en") -> AvatarSession:
        session = AvatarSession(user_id=user_id, language=language)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: uuid.UUID) -> AvatarSession | None:
        result = await self.db.execute(
            select(AvatarSession).where(AvatarSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def end_session(self, session_id: uuid.UUID) -> None:
        await self.db.execute(
            update(AvatarSession)
            .where(AvatarSession.id == session_id)
            .values(status="completed")
        )
        await self.db.commit()

    async def add_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        intent: str | None = None,
        workflow: str | None = None,
        entities: dict | None = None,
    ) -> AvatarMessage:
        msg = AvatarMessage(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            workflow=workflow,
            entities=json.dumps(entities) if entities else None,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_messages(self, session_id: uuid.UUID) -> list[AvatarMessage]:
        result = await self.db.execute(
            select(AvatarMessage)
            .where(AvatarMessage.session_id == session_id)
            .order_by(AvatarMessage.created_at)
        )
        return list(result.scalars().all())

    async def get_analytics(self) -> dict[str, Any]:
        """Generate avatar usage analytics."""
        # Total sessions
        total_r = await self.db.execute(select(func.count(AvatarSession.id)))
        total_sessions = total_r.scalar() or 0

        # Active sessions
        active_r = await self.db.execute(
            select(func.count(AvatarSession.id)).where(AvatarSession.status == "active")
        )
        active_sessions = active_r.scalar() or 0

        # Total messages
        msg_r = await self.db.execute(select(func.count(AvatarMessage.id)))
        total_messages = msg_r.scalar() or 0

        # Average messages per session
        avg_msgs = total_messages / max(total_sessions, 1)

        # Top workflows
        wf_r = await self.db.execute(
            text(
                "SELECT current_workflow, COUNT(*) as cnt FROM avatar_sessions "
                "WHERE current_workflow IS NOT NULL "
                "GROUP BY current_workflow ORDER BY cnt DESC LIMIT 10"
            )
        )
        top_workflows = [{"workflow": r[0], "count": r[1]} for r in wf_r.fetchall()]

        # Language distribution
        lang_r = await self.db.execute(
            text(
                "SELECT language, COUNT(*) as cnt FROM avatar_sessions "
                "GROUP BY language ORDER BY cnt DESC"
            )
        )
        language_dist = [{"language": r[0], "count": r[1]} for r in lang_r.fetchall()]

        # Daily sessions (last 30 days)
        daily_r = await self.db.execute(
            text(
                "SELECT DATE(created_at) as day, COUNT(*) as cnt FROM avatar_sessions "
                "WHERE created_at > NOW() - INTERVAL '30 days' "
                "GROUP BY DATE(created_at) ORDER BY day"
            )
        )
        daily = [{"date": str(r[0]), "count": r[1]} for r in daily_r.fetchall()]

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "avg_messages_per_session": round(avg_msgs, 1),
            "top_workflows": top_workflows,
            "language_distribution": language_dist,
            "daily_sessions": daily,
        }

    # ── Workflow Config CRUD ──────────────────────────────────────────────────

    async def get_workflow_configs(self) -> list[AvatarWorkflowConfig]:
        result = await self.db.execute(
            select(AvatarWorkflowConfig).order_by(AvatarWorkflowConfig.display_order)
        )
        configs = list(result.scalars().all())

        # Seed default configs if empty
        if not configs:
            defaults = [
                ("patient_registration", "Patient Registration", "Register new patients", "📋", 1),
                ("appointment_booking", "Appointment Booking", "Book OPD appointments", "📅", 2),
                ("opd_triage", "OPD Pre-Triage", "Collect pre-visit symptoms", "🩺", 3),
                ("billing_assistant", "Billing Assistant", "View and explain charges", "💰", 4),
                ("lab_booking", "Lab Booking", "Schedule laboratory tests", "🧪", 5),
                ("discharge_education", "Discharge Education", "Explain discharge instructions", "📄", 6),
                ("hospital_navigation", "Hospital Navigation", "Directions and floor map", "🗺️", 7),
            ]
            for key, name, desc, icon, order in defaults:
                cfg = AvatarWorkflowConfig(
                    workflow_key=key, display_name=name, description=desc,
                    icon=icon, display_order=order, is_enabled=True,
                )
                self.db.add(cfg)
            await self.db.commit()
            return await self.get_workflow_configs()

        return configs

    async def update_workflow_config(
        self, config_id: uuid.UUID, updates: dict[str, Any]
    ) -> AvatarWorkflowConfig | None:
        result = await self.db.execute(
            select(AvatarWorkflowConfig).where(AvatarWorkflowConfig.id == config_id)
        )
        cfg = result.scalar_one_or_none()
        if not cfg:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(cfg, key):
                setattr(cfg, key, value)

        await self.db.commit()
        await self.db.refresh(cfg)
        return cfg

    async def get_conversation_logs(
        self, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get conversation logs for admin review."""
        result = await self.db.execute(
            text(
                "SELECT s.id, s.language, s.status, s.current_workflow, s.created_at, "
                "COUNT(m.id) as message_count "
                "FROM avatar_sessions s "
                "LEFT JOIN avatar_messages m ON m.session_id = s.id "
                "GROUP BY s.id, s.language, s.status, s.current_workflow, s.created_at "
                "ORDER BY s.created_at DESC "
                "LIMIT :lim OFFSET :off"
            ),
            {"lim": limit, "off": offset},
        )
        return [
            {
                "session_id": str(r[0]),
                "language": r[1],
                "status": r[2],
                "workflow": r[3],
                "created_at": str(r[4]),
                "message_count": r[5],
            }
            for r in result.fetchall()
        ]
