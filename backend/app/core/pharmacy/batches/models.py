import uuid
from datetime import date
from sqlalchemy import Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class DrugBatch(Base):
    __tablename__ = "drug_batches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_number = Column(String(100), nullable=False)
    manufacture_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    quantity = Column(Numeric(12, 2), nullable=False, default=0.0)
