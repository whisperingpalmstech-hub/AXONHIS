from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class MdPromptMapping(Base):
    """
    Prompt mapping model for specialty UI.
    Maps AI prompts to UI elements and workflows.
    """
    __tablename__ = "md_prompt_mapping"

    mapping_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialty_profile_id = Column(UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=False, index=True)
    prompt_category = Column(String(50), nullable=False, index=True)  # QUESTIONING, MANAGEMENT_PLAN, DOCUMENTATION, etc.
    ui_element = Column(String(255), nullable=False)  # Button, field, section, etc.
    ui_location = Column(String(255), nullable=False)  # Page, modal, sidebar, etc.
    prompt_template = Column(Text, nullable=False)
    prompt_variables = Column(JSONB, nullable=False, default=[])  # Variables to substitute
    trigger_condition = Column(JSONB, nullable=False, default={})  # When to show prompt
    output_mapping = Column(JSONB, nullable=False, default={})  # Map output to fields
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    specialty_profile = relationship("MdSpecialtyProfile", backref="prompt_mappings")

    __table_args__ = (
        Index('idx_prompt_specialty_category', 'specialty_profile_id', 'prompt_category'),
        Index('idx_prompt_ui_location', 'ui_location'),
    )


class MdPromptVariable(Base):
    """
    Prompt variable model for reusable prompt variables.
    """
    __tablename__ = "md_prompt_variable"

    variable_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variable_name = Column(String(100), unique=True, nullable=False)
    variable_type = Column(String(50), nullable=False)  # PATIENT_DATA, ENCOUNTER_DATA, SYSTEM, etc.
    description = Column(Text, nullable=True)
    default_value = Column(String(500), nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    validation_regex = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MdPromptExecution(Base):
    """
    Prompt execution tracking model.
    Tracks prompt executions and results.
    """
    __tablename__ = "md_prompt_execution"

    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mapping_id = Column(UUID(as_uuid=True), ForeignKey("md_prompt_mapping.mapping_id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    input_data = Column(JSONB, nullable=False, default={})
    prompt_text = Column(Text, nullable=False)
    ai_response = Column(JSONB, nullable=False, default={})
    execution_time_ms = Column(Integer, nullable=True)
    status = Column(String(30), nullable=False)  # SUCCESS, ERROR, TIMEOUT
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    mapping = relationship("MdPromptMapping", backref="executions")

    __table_args__ = (
        Index('idx_prompt_execution_encounter', 'encounter_id', 'created_at'),
        Index('idx_prompt_execution_user', 'user_id', 'created_at'),
    )
