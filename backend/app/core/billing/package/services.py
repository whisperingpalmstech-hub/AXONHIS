"""Package Management Services for Billing Module."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timezone

from app.core.billing.package.models import (
    PackageVersion, PackageInclusion, PackageExclusion,
    PackagePricing, PackageApproval, PackageProfit
)
from app.core.billing.package.schemas import (
    PackageCreate, PackageUpdate, PackageInclusionCreate,
    PackageExclusionCreate, PackagePricingCreate
)
from app.core.billing_masters.models import PackageMaster as Package


class PackageService:
    """Service for package management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_package(self, package_data: PackageCreate, created_by: str) -> Package:
        """Create a new package with inclusions, exclusions, and pricing."""
        # Create the package
        package = Package(
            name=package_data.name,
            description=package_data.description,
            package_type=package_data.package_type,
            base_price=package_data.base_price,
            validity_start_date=package_data.validity_start_date,
            validity_end_date=package_data.validity_end_date,
            is_active=package_data.is_active
        )
        self.db.add(package)
        await self.db.flush()
        
        # Create initial version
        version = PackageVersion(
            package_id=package.id,
            version_number=1,
            version_name="v1.0",
            changes_description="Initial version",
            created_by=created_by
        )
        self.db.add(version)
        
        # Add inclusions
        for inclusion_data in package_data.inclusions:
            inclusion = PackageInclusion(
                package_id=package.id,
                service_id=inclusion_data.service_id,
                service_name=inclusion_data.service_name,
                service_type=inclusion_data.service_type,
                quantity=inclusion_data.quantity,
                is_mandatory=inclusion_data.is_mandatory
            )
            self.db.add(inclusion)
        
        # Add exclusions
        for exclusion_data in package_data.exclusions:
            exclusion = PackageExclusion(
                package_id=package.id,
                service_id=exclusion_data.service_id,
                service_name=exclusion_data.service_name,
                service_type=exclusion_data.service_type,
                exclusion_reason=exclusion_data.exclusion_reason
            )
            self.db.add(exclusion)
        
        # Add pricing
        for pricing_data in package_data.pricing:
            pricing = PackagePricing(
                package_id=package.id,
                patient_category=pricing_data.patient_category,
                bed_type=pricing_data.bed_type,
                payment_entitlement=pricing_data.payment_entitlement,
                price=pricing_data.price,
                validity_start_date=pricing_data.validity_start_date,
                validity_end_date=pricing_data.validity_end_date,
                is_active=pricing_data.is_active
            )
            self.db.add(pricing)
        
        await self.db.commit()
        await self.db.refresh(package)
        return package
    
    async def update_package(
        self, package_id: str, package_data: PackageUpdate, updated_by: str
    ) -> Package:
        """Update a package (creates new version)."""
        package = await self.db.get(Package, package_id)
        if not package:
            raise ValueError(f"Package {package_id} not found")
        
        # Update package fields
        if package_data.name is not None:
            package.name = package_data.name
        if package_data.description is not None:
            package.description = package_data.description
        if package_data.validity_start_date is not None:
            package.validity_start_date = package_data.validity_start_date
        if package_data.validity_end_date is not None:
            package.validity_end_date = package_data.validity_end_date
        if package_data.is_active is not None:
            package.is_active = package_data.is_active
        
        # Get current version number
        result = await self.db.execute(
            select(func.max(PackageVersion.version_number)).where(
                PackageVersion.package_id == package_id
            )
        )
        current_version = result.scalar() or 0
        
        # Create new version
        version = PackageVersion(
            package_id=package.id,
            version_number=current_version + 1,
            version_name=package_data.version_name or f"v{current_version + 1}.0",
            changes_description=package_data.changes_description or "Package update",
            created_by=updated_by
        )
        self.db.add(version)
        
        # Update inclusions if provided
        if package_data.inclusions is not None:
            # Delete old inclusions
            await self.db.execute(
                select(PackageInclusion).where(PackageInclusion.package_id == package_id)
            )
            old_inclusions = (await self.db.execute(
                select(PackageInclusion).where(PackageInclusion.package_id == package_id)
            )).scalars().all()
            for old in old_inclusions:
                await self.db.delete(old)
            
            # Add new inclusions
            for inclusion_data in package_data.inclusions:
                inclusion = PackageInclusion(
                    package_id=package.id,
                    service_id=inclusion_data.service_id,
                    service_name=inclusion_data.service_name,
                    service_type=inclusion_data.service_type,
                    quantity=inclusion_data.quantity,
                    is_mandatory=inclusion_data.is_mandatory
                )
                self.db.add(inclusion)
        
        # Update exclusions if provided
        if package_data.exclusions is not None:
            # Delete old exclusions
            old_exclusions = (await self.db.execute(
                select(PackageExclusion).where(PackageExclusion.package_id == package_id)
            )).scalars().all()
            for old in old_exclusions:
                await self.db.delete(old)
            
            # Add new exclusions
            for exclusion_data in package_data.exclusions:
                exclusion = PackageExclusion(
                    package_id=package.id,
                    service_id=exclusion_data.service_id,
                    service_name=exclusion_data.service_name,
                    service_type=exclusion_data.service_type,
                    exclusion_reason=exclusion_data.exclusion_reason
                )
                self.db.add(exclusion)
        
        # Update pricing if provided
        if package_data.pricing is not None:
            # Delete old pricing
            old_pricing = (await self.db.execute(
                select(PackagePricing).where(PackagePricing.package_id == package_id)
            )).scalars().all()
            for old in old_pricing:
                await self.db.delete(old)
            
            # Add new pricing
            for pricing_data in package_data.pricing:
                pricing = PackagePricing(
                    package_id=package.id,
                    patient_category=pricing_data.patient_category,
                    bed_type=pricing_data.bed_type,
                    payment_entitlement=pricing_data.payment_entitlement,
                    price=pricing_data.price,
                    validity_start_date=pricing_data.validity_start_date,
                    validity_end_date=pricing_data.validity_end_date,
                    is_active=pricing_data.is_active
                )
                self.db.add(pricing)
        
        await self.db.commit()
        await self.db.refresh(package)
        return package
    
    async def add_package_inclusion(
        self, package_id: str, inclusion_data: PackageInclusionCreate
    ) -> PackageInclusion:
        """Add a service to package inclusions."""
        inclusion = PackageInclusion(
            package_id=package_id,
            service_id=inclusion_data.service_id,
            service_name=inclusion_data.service_name,
            service_type=inclusion_data.service_type,
            quantity=inclusion_data.quantity,
            is_mandatory=inclusion_data.is_mandatory
        )
        self.db.add(inclusion)
        await self.db.commit()
        await self.db.refresh(inclusion)
        return inclusion
    
    async def remove_package_inclusion(self, package_id: str, inclusion_id: str) -> bool:
        """Remove a service from package inclusions."""
        inclusion = await self.db.get(PackageInclusion, inclusion_id)
        if inclusion and inclusion.package_id == package_id:
            await self.db.delete(inclusion)
            await self.db.commit()
            return True
        return False
    
    async def add_package_exclusion(
        self, package_id: str, exclusion_data: PackageExclusionCreate
    ) -> PackageExclusion:
        """Add a service to package exclusions."""
        exclusion = PackageExclusion(
            package_id=package_id,
            service_id=exclusion_data.service_id,
            service_name=exclusion_data.service_name,
            service_type=exclusion_data.service_type,
            exclusion_reason=exclusion_data.exclusion_reason
        )
        self.db.add(exclusion)
        await self.db.commit()
        await self.db.refresh(exclusion)
        return exclusion
    
    async def remove_package_exclusion(self, package_id: str, exclusion_id: str) -> bool:
        """Remove a service from package exclusions."""
        exclusion = await self.db.get(PackageExclusion, exclusion_id)
        if exclusion and exclusion.package_id == package_id:
            await self.db.delete(exclusion)
            await self.db.commit()
            return True
        return False
    
    async def approve_forceful_inclusion(
        self, package_id: str, service_id: str, requested_by: str, reason: str
    ) -> PackageApproval:
        """Request approval for forceful service inclusion."""
        approval = PackageApproval(
            package_id=package_id,
            request_type="forceful_inclusion",
            service_id=service_id,
            service_name="",  # Will be filled by service lookup
            requested_by=requested_by,
            reason=reason,
            status="pending"
        )
        self.db.add(approval)
        await self.db.commit()
        await self.db.refresh(approval)
        return approval
    
    async def check_package_validity(self, package_id: str, date: datetime) -> bool:
        """Check if package is valid on a given date."""
        package = await self.db.get(Package, package_id)
        if not package:
            return False
        
        if not package.is_active:
            return False
        
        if package.validity_start_date and date < package.validity_start_date:
            return False
        
        if package.validity_end_date and date > package.validity_end_date:
            return False
        
        return True
    
    async def deactivate_package(self, package_id: str) -> bool:
        """Deactivate a package."""
        package = await self.db.get(Package, package_id)
        if package:
            package.is_active = False
            await self.db.commit()
            return True
        return False
    
    async def forceful_close_package(self, package_id: str) -> bool:
        """Forcefully close a package (no more services can be added)."""
        package = await self.db.get(Package, package_id)
        if package:
            package.is_active = False
            await self.db.commit()
            return True
        return False
    
    async def calculate_package_price(
        self, package_id: str, patient_category: str,
        bed_type: Optional[str] = None, payment_entitlement: Optional[str] = None
    ) -> float:
        """Calculate package price based on patient context."""
        # Get applicable pricing
        result = await self.db.execute(
            select(PackagePricing).where(
                PackagePricing.package_id == package_id,
                PackagePricing.patient_category == patient_category,
                PackagePricing.is_active == True
            )
        )
        pricings = result.scalars().all()
        
        # Filter by bed type and payment entitlement if provided
        applicable_pricing = None
        for pricing in pricings:
            bed_match = bed_type is None or pricing.bed_type == bed_type
            payment_match = payment_entitlement is None or pricing.payment_entitlement == payment_entitlement
            if bed_match and payment_match:
                applicable_pricing = pricing
                break
        
        if applicable_pricing:
            return float(applicable_pricing.price)
        
        # If no specific pricing found, use base price
        package = await self.db.get(Package, package_id)
        if package:
            return float(package.base_price)
        
        return 0.0
    
    async def get_package_profit(self, package_id: str, patient_id: str) -> Optional[PackageProfit]:
        """Get package profit for a specific patient."""
        result = await self.db.execute(
            select(PackageProfit).where(
                PackageProfit.package_id == package_id,
                PackageProfit.patient_id == patient_id
            ).order_by(PackageProfit.calculated_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def copy_package(self, package_id: str, new_name: str, created_by: str) -> Package:
        """Copy a package to create a new one."""
        original = await self.db.get(Package, package_id)
        if not original:
            raise ValueError(f"Package {package_id} not found")
        
        # Get original inclusions
        inclusions_result = await self.db.execute(
            select(PackageInclusion).where(PackageInclusion.package_id == package_id)
        )
        inclusions = inclusions_result.scalars().all()
        
        # Get original exclusions
        exclusions_result = await self.db.execute(
            select(PackageExclusion).where(PackageExclusion.package_id == package_id)
        )
        exclusions = exclusions_result.scalars().all()
        
        # Get original pricing
        pricing_result = await self.db.execute(
            select(PackagePricing).where(PackagePricing.package_id == package_id)
        )
        pricings = pricing_result.scalars().all()
        
        # Create new package
        new_package = Package(
            name=new_name,
            description=original.description,
            package_type=original.package_type,
            base_price=original.base_price,
            validity_start_date=original.validity_start_date,
            validity_end_date=original.validity_end_date,
            is_active=True
        )
        self.db.add(new_package)
        await self.db.flush()
        
        # Create initial version
        version = PackageVersion(
            package_id=new_package.id,
            version_number=1,
            version_name="v1.0",
            changes_description=f"Copied from package {package_id}",
            created_by=created_by
        )
        self.db.add(version)
        
        # Copy inclusions
        for inclusion in inclusions:
            new_inclusion = PackageInclusion(
                package_id=new_package.id,
                service_id=inclusion.service_id,
                service_name=inclusion.service_name,
                service_type=inclusion.service_type,
                quantity=inclusion.quantity,
                is_mandatory=inclusion.is_mandatory
            )
            self.db.add(new_inclusion)
        
        # Copy exclusions
        for exclusion in exclusions:
            new_exclusion = PackageExclusion(
                package_id=new_package.id,
                service_id=exclusion.service_id,
                service_name=exclusion.service_name,
                service_type=exclusion.service_type,
                exclusion_reason=exclusion.exclusion_reason
            )
            self.db.add(new_exclusion)
        
        # Copy pricing
        for pricing in pricings:
            new_pricing = PackagePricing(
                package_id=new_package.id,
                patient_category=pricing.patient_category,
                bed_type=pricing.bed_type,
                payment_entitlement=pricing.payment_entitlement,
                price=pricing.price,
                validity_start_date=pricing.validity_start_date,
                validity_end_date=pricing.validity_end_date,
                is_active=pricing.is_active
            )
            self.db.add(new_pricing)
        
        await self.db.commit()
        await self.db.refresh(new_package)
        return new_package
