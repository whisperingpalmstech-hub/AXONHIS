import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class RadiologyTemplate(Base):
    __tablename__ = "radiology_templates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    modality: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    body_part: Mapped[str | None] = mapped_column(String(100))
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class RadiologyReport(Base):
    __tablename__ = "radiology_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("imaging_studies.id", ondelete="CASCADE"), nullable=False, index=True)
    report_text: Mapped[str] = mapped_column(Text, nullable=False)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft") # draft, provisional, validation_pending, final, amended

    # Relationships
    study: Mapped["ImagingStudy"] = relationship("ImagingStudy", lazy="joined")
    validations: Mapped[list["RadiologyValidation"]] = relationship("RadiologyValidation", back_populates="report", cascade="all, delete-orphan")
    amendments: Mapped[list["RadiologyAmendmentLog"]] = relationship("RadiologyAmendmentLog", back_populates="report", cascade="all, delete-orphan")

class RadiologyValidation(Base):
    __tablename__ = "radiology_validations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("radiology_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    validated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    electronic_signature: Mapped[str] = mapped_column(String(255), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text)
    
    report: Mapped["RadiologyReport"] = relationship("RadiologyReport", back_populates="validations")

class RadiologyAmendmentLog(Base):
    __tablename__ = "radiology_amendment_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("radiology_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    amended_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    amended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    previous_report_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    report: Mapped["RadiologyReport"] = relationship("RadiologyReport", back_populates="amendments")
