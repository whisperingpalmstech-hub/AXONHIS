import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PatientGuardian(Base):
    __tablename__ = "patient_guardians"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_name = Column(String(150), nullable=False)
    relationship_type = Column("relationship", String(50), nullable=False) # e.g., parent, sibling
    phone_number = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)

    patient = relationship("Patient", back_populates="guardians")
