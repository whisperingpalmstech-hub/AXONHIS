"""
MCP Server for AxonHIS Clinical Tools

Provides MCP tools for clinical workflows including:
- Patient information retrieval
- Lab test ordering
- Medication prescribing
- Document generation
- Appointment scheduling
"""
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server for clinical tool operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Any]:
        """Register available MCP tools"""
        return {
            "get_patient_info": {
                "name": "get_patient_info",
                "description": "Retrieve patient information including demographics, medical history, and recent encounters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "Patient UUID"
                        }
                    },
                    "required": ["patient_id"]
                }
            },
            "get_encounter_info": {
                "name": "get_encounter_info",
                "description": "Retrieve encounter details including notes, diagnoses, medications, and orders",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "encounter_id": {
                            "type": "string",
                            "description": "Encounter UUID"
                        }
                    },
                    "required": ["encounter_id"]
                }
            },
            "order_lab_test": {
                "name": "order_lab_test",
                "description": "Order a laboratory test for a patient",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "encounter_id": {
                            "type": "string",
                            "description": "Encounter UUID"
                        },
                        "test_name": {
                            "type": "string",
                            "description": "Name of the lab test"
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority level (ROUTINE, URGENT, STAT)",
                            "enum": ["ROUTINE", "URGENT", "STAT"]
                        }
                    },
                    "required": ["encounter_id", "test_name"]
                }
            },
            "prescribe_medication": {
                "name": "prescribe_medication",
                "description": "Prescribe a medication for a patient",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "encounter_id": {
                            "type": "string",
                            "description": "Encounter UUID"
                        },
                        "medication_name": {
                            "type": "string",
                            "description": "Name of the medication"
                        },
                        "dose": {
                            "type": "string",
                            "description": "Dosage (e.g., '500mg')"
                        },
                        "frequency": {
                            "type": "string",
                            "description": "Frequency (e.g., 'Twice daily')"
                        },
                        "route": {
                            "type": "string",
                            "description": "Route of administration (ORAL, IV, IM, etc.)"
                        }
                    },
                    "required": ["encounter_id", "medication_name", "dose", "frequency"]
                }
            },
            "schedule_appointment": {
                "name": "schedule_appointment",
                "description": "Schedule a follow-up appointment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "Patient UUID"
                        },
                        "clinician_id": {
                            "type": "string",
                            "description": "Clinician UUID"
                        },
                        "appointment_type": {
                            "type": "string",
                            "description": "Type of appointment (NEW, FOLLOW_UP, EMERGENCY)"
                        },
                        "slot_start": {
                            "type": "string",
                            "description": "Start time in ISO format"
                        },
                        "slot_end": {
                            "type": "string",
                            "description": "End time in ISO format"
                        }
                    },
                    "required": ["patient_id", "clinician_id", "appointment_type", "slot_start", "slot_end"]
                }
            },
            "generate_clinical_note": {
                "name": "generate_clinical_note",
                "description": "Generate a clinical note based on encounter data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "encounter_id": {
                            "type": "string",
                            "description": "Encounter UUID"
                        },
                        "note_type": {
                            "type": "string",
                            "description": "Type of note (HISTORY, EXAM, PROGRESS, SUMMARY)"
                        }
                    },
                    "required": ["encounter_id", "note_type"]
                }
            }
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool with given arguments"""
        try:
            if tool_name not in self.tools:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }
            
            # Dispatch to appropriate handler
            handler = getattr(self, f"_handle_{tool_name}", None)
            if handler:
                return await handler(**arguments)
            else:
                return {
                    "success": False,
                    "error": f"Handler for tool '{tool_name}' not implemented"
                }
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_patient_info(self, patient_id: str) -> Dict[str, Any]:
        """Handle patient information retrieval"""
        try:
            from app.core.axonhis_md.models import MdPatient
            
            patient = await self.db.get(MdPatient, UUID(patient_id))
            if not patient:
                return {
                    "success": False,
                    "error": "Patient not found"
                }
            
            return {
                "success": True,
                "data": {
                    "patient_id": str(patient.patient_id),
                    "display_name": patient.display_name,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "mrn": patient.mrn,
                    "dob": patient.dob.isoformat() if patient.dob else None,
                    "sex": patient.sex,
                    "status": patient.status
                }
            }
        except Exception as e:
            logger.error(f"Error getting patient info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_encounter_info(self, encounter_id: str) -> Dict[str, Any]:
        """Handle encounter information retrieval"""
        try:
            from app.core.axonhis_md.models import MdEncounter, MdEncounterNote, MdDiagnosis
            
            enc = await self.db.get(MdEncounter, UUID(encounter_id))
            if not enc:
                return {
                    "success": False,
                    "error": "Encounter not found"
                }
            
            # Get notes
            notes_result = await self.db.execute(
                select(MdEncounterNote).where(MdEncounterNote.encounter_id == UUID(encounter_id))
            )
            notes = notes_result.scalars().all()
            
            # Get diagnoses
            diag_result = await self.db.execute(
                select(MdDiagnosis).where(MdDiagnosis.encounter_id == UUID(encounter_id))
            )
            diagnoses = diag_result.scalars().all()
            
            return {
                "success": True,
                "data": {
                    "encounter_id": str(enc.encounter_id),
                    "patient_id": str(enc.patient_id),
                    "chief_complaint": enc.chief_complaint,
                    "encounter_status": enc.encounter_status,
                    "started_at": enc.started_at.isoformat() if enc.started_at else None,
                    "notes": [
                        {
                            "note_type": n.note_type,
                            "narrative_text": n.narrative_text,
                            "structured_json": n.structured_json
                        } for n in notes
                    ],
                    "diagnoses": [
                        {
                            "diagnosis_display": d.diagnosis_display,
                            "diagnosis_code": d.diagnosis_code,
                            "probability_score": d.probability_score
                        } for d in diagnoses
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error getting encounter info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_order_lab_test(self, encounter_id: str, test_name: str, priority: str = "ROUTINE") -> Dict[str, Any]:
        """Handle lab test ordering"""
        try:
            from app.core.axonhis_md.models import MdServiceRequest
            
            order = MdServiceRequest(
                encounter_id=UUID(encounter_id),
                request_type="LAB",
                request_code=test_name,
                request_display=test_name,
                priority=priority,
                status="REQUESTED"
            )
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            
            return {
                "success": True,
                "data": {
                    "service_request_id": str(order.service_request_id),
                    "request_code": order.request_code,
                    "priority": order.priority,
                    "status": order.status
                }
            }
        except Exception as e:
            logger.error(f"Error ordering lab test: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_prescribe_medication(
        self, 
        encounter_id: str, 
        medication_name: str, 
        dose: str, 
        frequency: str,
        route: str = "ORAL"
    ) -> Dict[str, Any]:
        """Handle medication prescription"""
        try:
            from app.core.axonhis_md.models import MdMedicationRequest
            
            rx = MdMedicationRequest(
                encounter_id=UUID(encounter_id),
                medication_name=medication_name,
                dose=dose,
                frequency=frequency,
                route=route,
                status="PRESCRIBED"
            )
            self.db.add(rx)
            await self.db.commit()
            await self.db.refresh(rx)
            
            return {
                "success": True,
                "data": {
                    "medication_request_id": str(rx.medication_request_id),
                    "medication_name": rx.medication_name,
                    "dose": rx.dose,
                    "frequency": rx.frequency,
                    "route": rx.route,
                    "status": rx.status
                }
            }
        except Exception as e:
            logger.error(f"Error prescribing medication: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_schedule_appointment(
        self,
        patient_id: str,
        clinician_id: str,
        appointment_type: str,
        slot_start: str,
        slot_end: str
    ) -> Dict[str, Any]:
        """Handle appointment scheduling"""
        try:
            from app.core.axonhis_md.models import MdAppointment
            from datetime import datetime
            
            start_time = datetime.fromisoformat(slot_start)
            end_time = datetime.fromisoformat(slot_end)
            
            apt = MdAppointment(
                patient_id=UUID(patient_id),
                clinician_id=UUID(clinician_id),
                appointment_type=appointment_type,
                slot_start=start_time,
                slot_end=end_time,
                status="BOOKED"
            )
            self.db.add(apt)
            await self.db.commit()
            await self.db.refresh(apt)
            
            return {
                "success": True,
                "data": {
                    "appointment_id": str(apt.appointment_id),
                    "appointment_type": apt.appointment_type,
                    "slot_start": apt.slot_start.isoformat(),
                    "slot_end": apt.slot_end.isoformat(),
                    "status": apt.status
                }
            }
        except Exception as e:
            logger.error(f"Error scheduling appointment: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_generate_clinical_note(self, encounter_id: str, note_type: str) -> Dict[str, Any]:
        """Handle clinical note generation"""
        try:
            from app.core.axonhis_md.models import MdEncounterNote
            from app.core.ai.grok_client import grok_chat
            
            # Get encounter context
            enc_info = await self._handle_get_encounter_info(encounter_id)
            if not enc_info["success"]:
                return enc_info
            
            context = enc_info["data"]
            
            # Generate note using AI
            messages = [
                {
                    "role": "system",
                    "content": f"You are a clinical documentation assistant. Generate a professional {note_type} note based on the provided encounter information."
                },
                {
                    "role": "user",
                    "content": f"Generate a {note_type} note for this encounter:\n{json.dumps(context, default=str)}"
                }
            ]
            
            result = await grok_chat(messages, temperature=0.3, max_tokens=1024)
            
            # Save the note
            note = MdEncounterNote(
                encounter_id=UUID(encounter_id),
                note_type=note_type,
                narrative_text=result["content"],
                authored_by="AI_ASSISTANT"
            )
            self.db.add(note)
            await self.db.commit()
            await self.db.refresh(note)
            
            return {
                "success": True,
                "data": {
                    "encounter_note_id": str(note.encounter_note_id),
                    "note_type": note.note_type,
                    "narrative_text": note.narrative_text
                }
            }
        except Exception as e:
            logger.error(f"Error generating clinical note: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools"""
        return list(self.tools.values())
