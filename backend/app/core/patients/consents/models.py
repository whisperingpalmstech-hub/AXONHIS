import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PatientConsent(Base):
    __tablename__ = "patient_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(100), nullable=False) # treatment_consent, data_sharing_consent, etc.
    consent_text = Column(Text, nullable=False)
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    signature_file_id = Column(UUID(as_uuid=True), nullable=True) # Could refer to a file/storage backend table

    patient = relationship("Patient", back_populates="consents")
