from datetime import datetime, timezone
import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import (
    RpiwAction, RpiwClinicalNote, RpiwOrder,
    RpiwPrescription, RpiwTask, RpiwActionLog
)

class RPIWActionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _create_root_action(self, action_type: str, data: dict) -> RpiwAction:
        """Create the central action registry entry."""
        action = RpiwAction(
            patient_uhid=data["patient_uhid"],
            admission_number=data.get("admission_number"),
            visit_id=data.get("visit_id"),
            action_type=action_type,
            status="Initiated",
            created_by_user_id=data["created_by_user_id"],
            created_by_role=data["created_by_role"],
            validation_status="Pending"
        )
        self.db.add(action)
        await self.db.flush()
        
        # Log the initiation
        await self._log_action(action.id, "Created", data["created_by_user_id"], data["created_by_role"], {"action_type": action_type})
        return action

    async def _log_action(self, action_id: str, event_type: str, user_id: str, role_code: str, details: dict = None):
        """Write to immutable action audit log."""
        log = RpiwActionLog(
            action_id=action_id,
            event_type=event_type,
            user_id=user_id,
            role_code=role_code,
            event_details=details
        )
        self.db.add(log)
        await self.db.flush()

    async def _validate_action(self, action: RpiwAction, child_payload: dict, action_type: str):
        """Simulate safety/billing checks."""
        # E.g., if a drug is prescribed, check known allergies. (Mocked here, normally calls CDSS subsystem)
        if action_type == "prescription":
            if "penicillin" in child_payload.get("drug_name", "").lower():
                action.validation_status = "Failed"
                action.validation_remarks = "Allergy conflict detected: Patient allergic to Penicillin."
                action.status = "Failed"
                await self._log_action(action.id, "ValidationFailed", action.created_by_user_id, action.created_by_role, {"reason": action.validation_remarks})
                return False
        
        # By default pass validation
        action.validation_status = "Passed"
        await self._log_action(action.id, "Validated", action.created_by_user_id, action.created_by_role)
        return True

    # ─── Public Action Methods ──────────────────────────────────

    async def add_clinical_note(self, data: dict):
        """Add a progress or nursing note."""
        action = await self._create_root_action("note", data)
        if await self._validate_action(action, data, "note"):
            note = RpiwClinicalNote(
                action_id=action.id,
                note_type=data["note_type"],
                content=data["content"]
            )
            self.db.add(note)
            action.status = "Completed"
            action.executed_at = datetime.now(timezone.utc)
            await self._log_action(action.id, "Executed", action.created_by_user_id, action.created_by_role)
        return action

    async def order_investigation(self, data: dict):
        """Create LIS or RIS order."""
        action = await self._create_root_action("order", data)
        if await self._validate_action(action, data, "order"):
            order = RpiwOrder(
                action_id=action.id,
                order_category=data["order_category"],
                item_code=data["item_code"],
                item_name=data["item_name"],
                priority=data.get("priority", "Routine"),
                routed_to_module="LIS" if data["order_category"] == "laboratory" else "RIS"
            )
            self.db.add(order)
            action.status = "Routed"
            action.executed_at = datetime.now(timezone.utc)
            await self._log_action(action.id, "Routed", action.created_by_user_id, action.created_by_role, {"destination": order.routed_to_module})
        return action

    async def prescribe_medication(self, data: dict):
        """Prescribe a medication."""
        action = await self._create_root_action("prescription", data)
        if await self._validate_action(action, data, "prescription"):
            med = RpiwPrescription(
                action_id=action.id,
                drug_name=data["drug_name"],
                dosage=data["dosage"],
                frequency=data["frequency"],
                route=data["route"],
                duration_days=data["duration_days"],
                instructions=data.get("instructions"),
                routed_to_pharmacy=True
            )
            self.db.add(med)
            action.status = "Routed"
            action.executed_at = datetime.now(timezone.utc)
            await self._log_action(action.id, "Routed", action.created_by_user_id, action.created_by_role, {"destination": "Pharmacy"})
        return action

    async def assign_task(self, data: dict):
        """Create a task for staff execution."""
        action = await self._create_root_action("task", data)
        if await self._validate_action(action, data, "task"):
            task = RpiwTask(
                action_id=action.id,
                assigned_role=data["assigned_role"],
                assigned_user_id=data.get("assigned_user_id"),
                task_description=data["task_description"],
                priority=data.get("priority", "Routine"),
                due_at=data.get("due_at")
            )
            self.db.add(task)
            action.status = "Routed"
            action.executed_at = datetime.now(timezone.utc)
            await self._log_action(action.id, "Routed", action.created_by_user_id, action.created_by_role, {"assigned_role": task.assigned_role})
        return action


    # ─── NLP Voice-to-Structured Processor (Mock Representation) ────────────────

    async def process_voice_command(self, transcript: str):
        """Parse raw text to structured clinical actions."""
        # Simple Regex parser simulating NLP behavior
        actions_extracted = []
        transcript_lower = transcript.lower()

        # Match Lab Orders (e.g., "Order CBC")
        if "order cbc" in transcript_lower or "complete blood count" in transcript_lower:
            actions_extracted.append({
                "action_type": "order",
                "parsed_data": {
                    "order_category": "laboratory",
                    "item_code": "LAB-001",
                    "item_name": "Complete Blood Count (CBC)",
                    "priority": "STAT" if "stat" in transcript_lower or "urgent" in transcript_lower else "Routine"
                }
            })
            
        # Match Medication (e.g., "start IV ceftriaxone 1g")
        if "ceftriaxone" in transcript_lower:
            actions_extracted.append({
                "action_type": "prescription",
                "parsed_data": {
                    "drug_name": "Ceftriaxone",
                    "dosage": "1g",
                    "frequency": "Once daily",
                    "route": "IV",
                    "duration_days": 3
                }
            })
            
        # Match task (e.g., "check vitals every 2 hours")
        if "check vitals" in transcript_lower:
            actions_extracted.append({
                "action_type": "task",
                "parsed_data": {
                    "assigned_role": "nurse",
                    "task_description": "Check vitals every 2 hours",
                    "priority": "High"
                }
            })

        return {
            "actions_extracted": actions_extracted,
            "raw_transcript": transcript
        }
