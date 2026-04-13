"""Expiry Management Router for Inventory."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.core.inventory.expiry.schemas import (
    ExpiryAlertCreate, ExpiryReportRequest, ReturnToSupplierCreate, DiscountSaleCreate
)
from app.core.inventory.expiry.services import ExpiryService

router = APIRouter()


@router.post("/expiry-alerts")
async def create_expiry_alert(
    alert_data: ExpiryAlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create an expiry alert configuration."""
    service = ExpiryService(db)
    return await service.create_expiry_alert(alert_data)


@router.get("/expiry-status")
async def check_expiry_status(db: AsyncSession = Depends(get_db)):
    """Check expiry status of all batches."""
    service = ExpiryService(db)
    return await service.check_expiry_status()


@router.post("/expiry-reports")
async def generate_expiry_report(
    report_data: ExpiryReportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate an expiry report."""
    service = ExpiryService(db)
    return await service.generate_expiry_report(report_data, "system")


@router.post("/return-to-supplier")
async def return_to_supplier(
    return_data: ReturnToSupplierCreate,
    db: AsyncSession = Depends(get_db)
):
    """Process return to supplier."""
    service = ExpiryService(db)
    return await service.return_to_supplier(return_data, "system")


@router.post("/discount-sales")
async def create_discount_sale(
    discount_data: DiscountSaleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a discount sale for expiring item."""
    service = ExpiryService(db)
    return await service.create_discount_sale(discount_data, "system")


@router.get("/near-expiry")
async def get_near_expiry_items(
    days_threshold: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get items nearing expiry within threshold days."""
    service = ExpiryService(db)
    return await service.get_near_expiry_items(days_threshold)


@router.get("/expired")
async def get_expired_items(db: AsyncSession = Depends(get_db)):
    """Get expired items."""
    service = ExpiryService(db)
    return await service.get_expired_items()
