import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class Medication(Base):
    """Enhanced Drug Master Database - keeps original tablename for FK compatibility."""
    __tablename__ = "medications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_code = Column(String(50), nullable=False, unique=True, index=True)
    drug_name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=False)
    drug_class = Column(String(100), nullable=True)
    form = Column(String(50), nullable=True)
    strength = Column(String(50), nullable=True)
    pack_size = Column(String(50), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    schedule_category = Column(String(50), nullable=True)  # Schedule H, Schedule X, OTC
    global_code = Column(String(100), nullable=True)       # ATC code for global codification
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class PharmacyGenericMapping(Base):
    """Maps generic names to branded drug products for substitution."""
    __tablename__ = "pharmacy_generic_mapping"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generic_name = Column(String(200), nullable=False, index=True)
    drug_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False)
    brand_substitute_rank = Column(Numeric, default=1)

class PharmacyDrugInteraction(Base):
    """Records known drug-drug interactions for safety checks."""
    __tablename__ = "pharmacy_drug_interactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_a_generic = Column(String(200), nullable=False, index=True)
    drug_b_generic = Column(String(200), nullable=False, index=True)
    severity = Column(String(50), nullable=False)  # High, Moderate, Low
    interaction_effect = Column(Text, nullable=False)

class PharmacyDrugSchedule(Base):
    """Regulatory classification for controlled substance management."""
    __tablename__ = "pharmacy_drug_schedules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_name = Column(String(50), nullable=False, unique=True)
    requires_prescription = Column(Boolean, default=True)
    strict_narcotic = Column(Boolean, default=False)

class PharmacyDosageRule(Base):
    """Dosage calculation rules per drug per patient category."""
    __tablename__ = "pharmacy_dosage_rules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generic_name = Column(String(200), nullable=False, index=True)
    patient_category = Column(String(50), nullable=False)  # Adult, Pediatric, Geriatric
    dosage_per_kg = Column(Numeric, nullable=True)
    fixed_dosage = Column(String(100), nullable=True)

class PharmacyRolePermission(Base):
    """Pharmacy-specific RBAC roles and permissions."""
    __tablename__ = "pharmacy_role_permissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(100), nullable=False, unique=True)
    can_dispense = Column(Boolean, default=False)
    can_manage_inventory = Column(Boolean, default=False)
    can_manage_master = Column(Boolean, default=False)

class PharmacyDrugMasterAudit(Base):
    """Immutable audit trail for all drug master changes."""
    __tablename__ = "pharmacy_drug_master_audits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    modified_by = Column(String, nullable=False)
    modified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=False)
