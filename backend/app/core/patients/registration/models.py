"""
Enterprise Registration Models.

Tables:
  - registration_sessions      : AI-guided registration sessions
  - id_scan_records             : OCR ID scan results
  - face_embeddings             : Face recognition embeddings
  - patient_documents           : Uploaded documents (ID proof, medical docs, photos)
  - health_cards                : Digital health card records with QR
  - registration_notifications  : Notification dispatch log (SMS/Email/WhatsApp)
  - address_directory           : Pincode-to-address mapping cache
"""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class RegistrationStatus(str, PyEnum):
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class IDDocumentType(str, PyEnum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    AADHAAR = "aadhaar"
    DRIVING_LICENSE = "driving_license"
    OTHER = "other"


class NotificationChannel(str, PyEnum):
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class NotificationStatus(str, PyEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class DocumentCategory(str, PyEnum):
    ID_PROOF = "id_proof"
    MEDICAL_DOCUMENT = "medical_document"
    PATIENT_PHOTO = "patient_photo"
    INSURANCE_CARD = "insurance_card"
    OTHER = "other"


# ─────────────────────────────────────────────────────────────────────────────
# 1. AI-Assisted Registration Session
# ─────────────────────────────────────────────────────────────────────────────

class RegistrationSession(Base):
    """Tracks the AI-guided step-by-step registration flow."""
    __tablename__ = "registration_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(
        Enum(RegistrationStatus, name="registration_status_enum"),
        default=RegistrationStatus.IN_PROGRESS,
        nullable=False,
    )
    current_step = Column(Integer, default=1, nullable=False)  # 1-based step index
    total_steps = Column(Integer, default=6, nullable=False)
    collected_data = Column(JSON, default=dict, nullable=False)  # Partial form data
    ai_suggestions = Column(JSON, default=dict, nullable=False)  # AI-generated hints
    voice_language = Column(String(10), default="en", nullable=False)
    registration_method = Column(
        String(30), default="manual", nullable=False
    )  # manual | ai_guided | voice | id_scan | face_recognition
    initiated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. ID Scan Records (OCR)
# ─────────────────────────────────────────────────────────────────────────────

class IDScanRecord(Base):
    """Stores OCR extraction results from scanned identity documents."""
    __tablename__ = "id_scan_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("registration_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    document_type = Column(
        Enum(IDDocumentType, name="id_document_type_enum"),
        nullable=False,
    )
    file_path = Column(String(500), nullable=True)  # Path to uploaded scan image
    extracted_name = Column(String(200), nullable=True)
    extracted_dob = Column(String(20), nullable=True)
    extracted_gender = Column(String(20), nullable=True)
    extracted_id_number = Column(String(100), nullable=True)
    raw_ocr_text = Column(Text, nullable=True)
    extraction_confidence = Column(Float, default=0.0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Face Embeddings (Biometric Check-in)
# ─────────────────────────────────────────────────────────────────────────────

class FaceEmbedding(Base):
    """Stores face recognition vector embeddings for patient identification."""
    __tablename__ = "face_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    embedding_vector = Column(JSON, nullable=False)  # List[float] – 128/512-d vector
    photo_path = Column(String(500), nullable=True)  # reference photo
    quality_score = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 8. Health Card
# ─────────────────────────────────────────────────────────────────────────────

class HealthCard(Base):
    """Digital patient health card with QR code."""
    __tablename__ = "health_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uhid = Column(String(30), unique=True, index=True, nullable=False)  # UHID on card
    card_number = Column(String(30), unique=True, index=True, nullable=False)
    qr_code_data = Column(Text, nullable=False)  # Base64-encoded QR image
    qr_payload = Column(JSON, nullable=False)  # JSON payload encoded in QR
    issue_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 9. Patient Documents
# ─────────────────────────────────────────────────────────────────────────────

class RegistrationDocument(Base):
    """Uploaded documents linked to a patient (ID proof, medical records, photos)."""
    __tablename__ = "registration_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(
        Enum(DocumentCategory, name="document_category_enum"),
        nullable=False,
    )
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 10. Registration Notification Log
# ─────────────────────────────────────────────────────────────────────────────

class RegistrationNotification(Base):
    """Tracks SMS / Email / WhatsApp notifications sent during registration."""
    __tablename__ = "registration_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel = Column(
        Enum(NotificationChannel, name="reg_notification_channel_enum"),
        nullable=False,
    )
    recipient = Column(String(200), nullable=False)  # phone number or email address
    subject = Column(String(255), nullable=True)
    message_body = Column(Text, nullable=False)
    status = Column(
        Enum(NotificationStatus, name="reg_notification_status_enum"),
        default=NotificationStatus.QUEUED,
        nullable=False,
    )
    external_message_id = Column(String(200), nullable=True)  # Provider reference ID
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Address Directory (Pincode lookup cache)
# ─────────────────────────────────────────────────────────────────────────────

class AddressDirectory(Base):
    """Cached pincode-to-address mapping for auto-population."""
    __tablename__ = "address_directory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pincode = Column(String(10), index=True, nullable=False)
    area = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), default="India", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
