import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class DICOMMetadata(Base):
    __tablename__ = "dicom_metadata"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_uid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    series_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    image_count: Mapped[int] = mapped_column(Integer, default=1)
    file_location: Mapped[str | None] = mapped_column(String(512), nullable=True) # PACS reference
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
