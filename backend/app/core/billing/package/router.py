"""Package Management Router for Billing Module."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.core.billing.package.schemas import (
    PackageCreate, PackageUpdate, PackageResponse, PackageWithDetailsResponse,
    PackageInclusionV2Create, PackageExclusionCreate, PackageApprovalRequest, PackageApprovalResponse
)
from app.core.billing.package.services import PackageService

router = APIRouter()


@router.post("/packages", response_model=PackageResponse)
async def create_package(
    package_data: PackageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new package with inclusions, exclusions, and pricing."""
    service = PackageService(db)
    return await service.create_package(package_data, "system")


@router.get("/packages", response_model=List[PackageResponse])
async def list_packages(
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all packages."""
    from app.core.billing.package.models import Package
    from sqlalchemy import select
    
    query = select(Package).where(Package.is_active == is_active)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/packages/{package_id}", response_model=PackageWithDetailsResponse)
async def get_package(
    package_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get package details with inclusions, exclusions, and pricing."""
    from app.core.billing.package.models import Package, PackageInclusionV2, PackageExclusion, PackagePricing
    from sqlalchemy import select
    
    # Get package
    package = await db.get(Package, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Get inclusions
    inclusions_result = await db.execute(
        select(PackageInclusionV2).where(PackageInclusionV2.package_id == package_id)
    )
    inclusions = inclusions_result.scalars().all()
    
    # Get exclusions
    exclusions_result = await db.execute(
        select(PackageExclusion).where(PackageExclusion.package_id == package_id)
    )
    exclusions = exclusions_result.scalars().all()
    
    # Get pricing
    pricing_result = await db.execute(
        select(PackagePricing).where(PackagePricing.package_id == package_id)
    )
    pricings = pricing_result.scalars().all()
    
    # Get current version
    from sqlalchemy import func
    version_result = await db.execute(
        select(func.max(PackagePricing.version_number)).where(
            PackagePricing.package_id == package_id
        )
    )
    current_version = version_result.scalar()
    
    return PackageWithDetailsResponse(
        id=str(package.id),
        name=package.name,
        description=package.description,
        package_type=package.package_type,
        base_price=float(package.base_price),
        validity_start_date=package.validity_start_date,
        validity_end_date=package.validity_end_date,
        is_active=package.is_active,
        created_at=package.created_at,
        updated_at=package.updated_at,
        inclusions=inclusions,
        exclusions=exclusions,
        pricing=pricings,
        current_version=current_version
    )


@router.put("/packages/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: str,
    package_data: PackageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a package (creates new version)."""
    service = PackageService(db)
    return await service.update_package(package_id, package_data, "system")


@router.post("/packages/{package_id}/inclusions")
async def add_package_inclusion(
    package_id: str,
    inclusion_data: PackageInclusionV2Create,
    db: AsyncSession = Depends(get_db)
):
    """Add a service to package inclusions."""
    service = PackageService(db)
    return await service.add_package_inclusion(package_id, inclusion_data)


@router.delete("/packages/{package_id}/inclusions/{inclusion_id}")
async def remove_package_inclusion(
    package_id: str,
    inclusion_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a service from package inclusions."""
    service = PackageService(db)
    success = await service.remove_package_inclusion(package_id, inclusion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Inclusion not found")
    return {"success": True}


@router.post("/packages/{package_id}/exclusions")
async def add_package_exclusion(
    package_id: str,
    exclusion_data: PackageExclusionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a service to package exclusions."""
    service = PackageService(db)
    return await service.add_package_exclusion(package_id, exclusion_data)


@router.delete("/packages/{package_id}/exclusions/{exclusion_id}")
async def remove_package_exclusion(
    package_id: str,
    exclusion_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a service from package exclusions."""
    service = PackageService(db)
    success = await service.remove_package_exclusion(package_id, exclusion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exclusion not found")
    return {"success": True}


@router.post("/packages/{package_id}/approve-inclusion", response_model=PackageApprovalResponse)
async def approve_forceful_inclusion(
    package_id: str,
    approval_data: PackageApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request approval for forceful service inclusion."""
    service = PackageService(db)
    return await service.approve_forceful_inclusion(
        package_id,
        approval_data.service_id,
        "system",
        approval_data.reason
    )


@router.post("/packages/{package_id}/deactivate")
async def deactivate_package(package_id: str, db: AsyncSession = Depends(get_db)):
    """Deactivate a package."""
    service = PackageService(db)
    success = await service.deactivate_package(package_id)
    if not success:
        raise HTTPException(status_code=404, detail="Package not found")
    return {"success": True}


@router.post("/packages/{package_id}/close")
async def forceful_close_package(package_id: str, db: AsyncSession = Depends(get_db)):
    """Forcefully close a package."""
    service = PackageService(db)
    success = await service.forceful_close_package(package_id)
    if not success:
        raise HTTPException(status_code=404, detail="Package not found")
    return {"success": True}


@router.get("/packages/{package_id}/profit")
async def get_package_profit(
    package_id: str,
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get package profit for a specific patient."""
    service = PackageService(db)
    profit = await service.get_package_profit(package_id, patient_id)
    if not profit:
        raise HTTPException(status_code=404, detail="Profit record not found")
    return profit


@router.post("/packages/{package_id}/copy")
async def copy_package(
    package_id: str,
    new_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Copy a package to create a new one."""
    service = PackageService(db)
    return await service.copy_package(package_id, new_name, "system")
