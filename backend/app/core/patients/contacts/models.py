import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PatientContact(Base):
    __tablename__ = "patient_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_type = Column(String(50), nullable=False) # e.g. phone, email, address
    contact_value = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    patient = relationship("Patient", back_populates="contacts")
