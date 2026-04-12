import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base

class AbdmConsentArtefact(Base):
    __tablename__ = "abdm_consent_artefacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # ABDM specifics
    consent_id = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False) # GRANTED, REVOKED, EXPIRED, DENIED
    
    # Granular permissions
    purpose_of_request = Column(String(255), nullable=True)
    hi_types = Column(JSONB, nullable=True) # Health Information Types (e.g. ['Prescription', 'DiagnosticReport'])
    
    # Validity period
    permission_from = Column(DateTime(timezone=True), nullable=True)
    permission_to = Column(DateTime(timezone=True), nullable=True)
    data_erase_at = Column(DateTime(timezone=True), nullable=True)
    
    # Encrypted payload/artefact from ABDM Gateway
    encrypted_payload = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class HealthInformationExchangeLog(Base):
    __tablename__ = "abdm_hie_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    consent_id = Column(String(255), ForeignKey("abdm_consent_artefacts.consent_id", ondelete="SET NULL"), nullable=True, index=True)
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Pull / Push
    exchange_type = Column(String(50), nullable=False) # e.g., PUSH, PULL, NOTIFY
    request_payload = Column(JSONB, nullable=True)
    response_payload = Column(JSONB, nullable=True)
    
    status = Column(String(50), nullable=False) # SUCCESS, FAILED, TIMEOUT
    
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
