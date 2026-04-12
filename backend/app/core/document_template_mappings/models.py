from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class MdDocumentTemplateMapping(Base):
    """
    Document template mapping model.
    Maps document templates to document types and specialties.
    """
    __tablename__ = "md_document_template_mapping"

    mapping_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(255), nullable=False)
    template_code = Column(String(100), unique=True, nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)  # CLINICAL_NOTE, DISCHARGE_SUMMARY, etc.
    specialty_profile_id = Column(UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=True, index=True)
    template_content = Column(Text, nullable=False)
    template_variables = Column(JSONB, nullable=False, default=[])  # Variables in template
    output_format = Column(String(20), nullable=False)  # PDF, DOCX, HTML, etc.
    meta_data = Column(JSONB, nullable=False, default={})
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    specialty_profile = relationship("MdSpecialtyProfile", backref="document_templates")

    __table_args__ = (
        Index('idx_doc_template_type', 'document_type'),
        Index('idx_doc_template_specialty', 'specialty_profile_id', 'document_type'),
    )
