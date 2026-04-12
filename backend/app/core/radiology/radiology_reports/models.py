import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class RadiologyReport(Base):
    __tablename__ = "radiology_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("imaging_studies.id", ondelete="CASCADE"), nullable=False, index=True)
    report_text: Mapped[str] = mapped_column(Text, nullable=False)
    reported_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, final, amended

    # Relationships
    study: Mapped["ImagingStudy"] = relationship("ImagingStudy", lazy="joined")
