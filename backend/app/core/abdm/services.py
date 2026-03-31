import uuid
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.abdm.models import AbdmConsentArtefact, HealthInformationExchangeLog
from app.core.patients.patients.models import Patient
from app.core.abdm.encryption import encrypt_data, decrypt_data
from app.core.audit.models import AuditLog

class AbdmService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def link_abha(self, patient_id: uuid.UUID, abha_number: str, abha_address: str, org_id: uuid.UUID, user_id: uuid.UUID):
        """Link an ABHA number to a patient with proper encryption."""
        patient = (await self.db.execute(select(Patient).where(Patient.id == patient_id))).scalar_one_or_none()
        if not patient:
            raise ValueError("Patient not found")

        # Encrypt sensitive ABDM Data
        patient.abha_number_encrypted = encrypt_data(abha_number)
        patient.abha_address_encrypted = encrypt_data(abha_address)
        patient.abha_linked = True
        
        # HIPAA compliant audit log
        audit = AuditLog(
            user_id=user_id,
            org_id=org_id,
            action="UPDATE",
            resource_type="Patient",
            resource_id=str(patient_id),
            before_state={"abha_linked": False},
            after_state={"abha_linked": True, "abha_address": "****"}, # Masked
            note="Linked ABHA account to patient profile"
        )
        self.db.add(audit)
        await self.db.flush()

    async def generate_consent_artefact(self, patient_id: uuid.UUID, org_id: uuid.UUID, hi_types: list[str], purpose: str):
        """Mock creation of consent artefact from Consent Manager"""
        consent_id = f"CONSENT-{str(uuid.uuid4())[:8].upper()}"
        
        artefact = AbdmConsentArtefact(
            patient_id=patient_id,
            org_id=org_id,
            consent_id=consent_id,
            status="GRANTED",
            purpose_of_request=purpose,
            hi_types=hi_types,
            permission_from=datetime.datetime.now(datetime.timezone.utc),
            permission_to=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        )
        self.db.add(artefact)
        
        # Log this creation
        audit = AuditLog(
            user_id=None, # System/Patient
            org_id=org_id,
            action="CREATE",
            resource_type="AbdmConsentArtefact",
            resource_id=consent_id,
            note=f"Consent granted for {purpose}"
        )
        self.db.add(audit)
        
        await self.db.flush()
        return artefact

    async def log_exchange(self, transaction_id: str, consent_id: str, patient_id: uuid.UUID, org_id: uuid.UUID, type: str, status: str, request_payload: dict, response_payload: dict | None = None, doctor_id: uuid.UUID | None = None):
        """Log FHIR standard health information exchange."""
        log_entry = HealthInformationExchangeLog(
            transaction_id=transaction_id,
            consent_id=consent_id,
            patient_id=patient_id,
            org_id=org_id,
            doctor_id=doctor_id,
            exchange_type=type,
            status=status,
            request_payload=request_payload,
            response_payload=response_payload
        )
        self.db.add(log_entry)
        
        # Audit log for the data access
        audit = AuditLog(
            user_id=doctor_id,
            org_id=org_id,
            action="READ" if type == "PULL" else "EXPORT",
            resource_type="HealthInformationExchange",
            resource_id=transaction_id,
            note=f"Processed HIE-CM request: {status}"
        )
        self.db.add(audit)
        
        await self.db.flush()
        return log_entry
