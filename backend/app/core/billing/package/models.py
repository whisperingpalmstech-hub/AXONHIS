"""Package Management Models for Billing Module."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class PackageVersion(Base):
    """Package version tracking."""
    __tablename__ = "billing_package_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(50), nullable=False)
    changes_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class PackageInclusion(Base):
    """Services included in a package."""
    __tablename__ = "billing_package_inclusions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), nullable=False)
    service_name = Column(String(200), nullable=False)
    service_type = Column(String(50), nullable=False)  # 'hospital_service', 'lab', 'radiology', 'pharmacy'
    quantity = Column(Integer, nullable=False, default=1)
    is_mandatory = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PackageExclusion(Base):
    """Services excluded from a package."""
    __tablename__ = "billing_package_exclusions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), nullable=False)
    service_name = Column(String(200), nullable=False)
    service_type = Column(String(50), nullable=False)
    exclusion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PackagePricing(Base):
    """Package pricing by patient category, bed type, payment entitlement."""
    __tablename__ = "billing_package_pricing"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_category = Column(String(50), nullable=False)  # 'national', 'foreign', 'bpl', 'employee', 'nok_employee'
    bed_type = Column(String(50), nullable=True)  # 'general', 'private', 'semi_private', 'icu'
    payment_entitlement = Column(String(50), nullable=True)  # 'self', 'insurance', 'corporate', 'stat'
    price = Column(Numeric(12, 2), nullable=False)
    validity_start_date = Column(DateTime(timezone=True), nullable=True)
    validity_end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PackageApproval(Base):
    """Approval workflow for forceful inclusion/exclusion."""
    __tablename__ = "billing_package_approvals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False)  # 'forceful_inclusion', 'forceful_exclusion'
    service_id = Column(UUID(as_uuid=True), nullable=False)
    service_name = Column(String(200), nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'rejected'
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PackageProfit(Base):
    """Package profit calculation tracking."""
    __tablename__ = "billing_package_profits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    package_cost = Column(Numeric(12, 2), nullable=False)
    package_price = Column(Numeric(12, 2), nullable=False)
    profit = Column(Numeric(12, 2), nullable=False)
    profit_percentage = Column(Numeric(5, 2), nullable=False)
    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
