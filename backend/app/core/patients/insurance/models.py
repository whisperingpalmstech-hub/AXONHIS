import uuid
from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PatientInsurance(Base):
    __tablename__ = "patient_insurance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    insurance_provider = Column(String(150), nullable=False)
    policy_number = Column(String(100), nullable=False, index=True)
    coverage_type = Column(String(100), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    patient = relationship("Patient", back_populates="insurance")
