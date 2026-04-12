import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class OrganizationEntity(Base):
    """
    Master Multi-Tenant Organization. Represents the top-level hospital group.
    """
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    org_code = Column(String(50), nullable=False, unique=True, index=True)
    country = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Multilingual / Localization Overrides
    default_language = Column(String(10), default="en") # en, fr, ar, hi
    
    # ABDM M1: Health Facility Registry
    abdm_hfr_id = Column(String(100), nullable=True, unique=True, index=True)
    abdm_facility_name = Column(String(255), nullable=True)
    abdm_integration_active = Column(Boolean, default=False)
    
    # Global Settings (JSON payload for voice configs, currency, timezone etc)
    global_settings = Column(JSONB, nullable=True, default={})
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    sites = relationship("FacilitySite", back_populates="organization", cascade="all, delete-orphan")


class FacilitySite(Base):
    """
    Child entity of Organization. A single organization can manage multiple distributed physical sites (clinics/hospitals).
    """
    __tablename__ = "facility_sites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    site_code = Column(String(50), nullable=False, unique=True, index=True)
    location_address = Column(String(500), nullable=True)
    timezone = Column(String(100), default="UTC")
    is_active = Column(Boolean, default=True)
    
    # Specific feature flags (Voice AI enabled, Local Language Configs)
    site_settings = Column(JSONB, nullable=True, default={})
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    organization = relationship("OrganizationEntity", back_populates="sites")
