"""Expiry Management Services for Inventory."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from app.core.inventory.expiry.models import (
    ExpiryAlert, ExpiryTracking, ExpiryReport, ReturnToSupplier, DiscountSale
)
from app.core.inventory.expiry.schemas import (
    ExpiryAlertCreate, ExpiryReportRequest, ReturnToSupplierCreate, DiscountSaleCreate
)


class ExpiryService:
    """Service for expiry management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_expiry_alert(self, alert_data: ExpiryAlertCreate) -> ExpiryAlert:
        """Create an expiry alert configuration."""
        alert = ExpiryAlert(**alert_data.model_dump())
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert
    
    async def check_expiry_status(self) -> List[Dict[str, Any]]:
        """Check expiry status of all batches."""
        # Get active alerts
        result = await self.db.execute(
            select(ExpiryAlert).where(ExpiryAlert.is_active == True)
        )
        alerts = result.scalars().all()
        
        expiring_items = []
        now = datetime.now(timezone.utc)
        
        # Get batch records with expiry dates
        from app.core.inventory.models import BatchRecord
        result = await self.db.execute(
            select(BatchRecord).where(
                BatchRecord.expiry_date.isnot(None)
            )
        )
        batches = result.scalars().all()
        
        for batch in batches:
            days_to_expiry = (batch.expiry_date - now).days
            
            # Determine status based on alerts
            status = "active"
            alert_type = None
            for alert in alerts:
                if days_to_expiry <= alert.threshold_days:
                    status = "near_expiry" if days_to_expiry > 0 else "expired"
                    alert_type = alert.alert_type
                    break
            
            if status in ["near_expiry", "expired"]:
                expiring_items.append({
                    "batch_id": str(batch.id),
                    "item_id": str(batch.item_id),
                    "expiry_date": batch.expiry_date,
                    "days_to_expiry": days_to_expiry,
                    "status": status,
                    "alert_type": alert_type
                })
        
        return expiring_items
    
    async def generate_expiry_report(self, report_data: ExpiryReportRequest, generated_by: str) -> ExpiryReport:
        """Generate an expiry report."""
        # Generate report number
        result = await self.db.execute(select(func.max(ExpiryReport.id)))
        max_id = result.scalar()
        report_number = f"EXP-RPT-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        # Get expiring items
        expiring_items = await self.check_expiry_status()
        
        # Calculate totals
        total_items = len(expiring_items)
        near_expiry_count = sum(1 for item in expiring_items if item["status"] == "near_expiry")
        expired_count = sum(1 for item in expiring_items if item["status"] == "expired")
        
        # Calculate values (simplified - in real implementation would fetch actual values)
        total_value = 0.0
        expiry_value = 0.0
        
        report = ExpiryReport(
            report_number=report_number,
            **report_data.model_dump(),
            generated_by=generated_by,
            total_items=total_items,
            near_expiry_count=near_expiry_count,
            expired_count=expired_count,
            total_value=total_value,
            expiry_value=expiry_value
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report
    
    async def return_to_supplier(self, return_data: ReturnToSupplierCreate, requested_by: str) -> ReturnToSupplier:
        """Process return to supplier."""
        # Generate return number
        result = await self.db.execute(select(func.max(ReturnToSupplier.id)))
        max_id = result.scalar()
        return_number = f"RTS-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        return_request = ReturnToSupplier(
            **return_data.model_dump(),
            return_number=return_number,
            requested_by=requested_by
        )
        self.db.add(return_request)
        await self.db.commit()
        await self.db.refresh(return_request)
        return return_request
    
    async def create_discount_sale(self, discount_data: DiscountSaleCreate, created_by: str) -> DiscountSale:
        """Create a discount sale for expiring item."""
        discounted_price = discount_data.original_price * (1 - discount_data.discount_percentage / 100)
        
        discount_sale = DiscountSale(
            **discount_data.model_dump(),
            discounted_price=discounted_price,
            created_by=created_by
        )
        self.db.add(discount_sale)
        await self.db.commit()
        await self.db.refresh(discount_sale)
        return discount_sale
    
    async def get_near_expiry_items(self, days_threshold: int = 30) -> List[Dict[str, Any]]:
        """Get items nearing expiry within threshold days."""
        now = datetime.now(timezone.utc)
        threshold_date = now + timedelta(days=days_threshold)
        
        from app.core.inventory.models import BatchRecord
        result = await self.db.execute(
            select(BatchRecord).where(
                BatchRecord.expiry_date.isnot(None),
                BatchRecord.expiry_date <= threshold_date,
                BatchRecord.expiry_date > now
            )
        )
        batches = result.scalars().all()
        
        near_expiry = []
        for batch in batches:
            days_to_expiry = (batch.expiry_date - now).days
            near_expiry.append({
                "batch_id": str(batch.id),
                "item_id": str(batch.item_id),
                "expiry_date": batch.expiry_date,
                "days_to_expiry": days_to_expiry
            })
        
        return near_expiry
    
    async def get_expired_items(self) -> List[Dict[str, Any]]:
        """Get expired items."""
        now = datetime.now(timezone.utc)
        
        from app.core.inventory.models import BatchRecord
        result = await self.db.execute(
            select(BatchRecord).where(
                BatchRecord.expiry_date.isnot(None),
                BatchRecord.expiry_date < now
            )
        )
        batches = result.scalars().all()
        
        expired = []
        for batch in batches:
            days_expired = (now - batch.expiry_date).days
            expired.append({
                "batch_id": str(batch.id),
                "item_id": str(batch.item_id),
                "expiry_date": batch.expiry_date,
                "days_expired": days_expired
            })
        
        return expired
