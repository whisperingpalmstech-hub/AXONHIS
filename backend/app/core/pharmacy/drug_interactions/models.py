import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class DrugInteraction(Base):
    __tablename__ = "drug_interactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_a_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_b_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)  # minor, moderate, major, contraindicated
    description = Column(String, nullable=True)
