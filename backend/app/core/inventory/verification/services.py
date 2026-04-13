"""Physical Stock Verification Services for Inventory."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.core.inventory.verification.models import (
    VerificationSchedule, VerificationItem, Discrepancy, VerificationReport
)
from app.core.inventory.verification.schemas import (
    VerificationScheduleCreate, VerificationItemCreate, VerificationItemUpdate, DiscrepancyCreate
)


class VerificationService:
    """Service for physical stock verification operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_verification_schedule(self, schedule_data: VerificationScheduleCreate, created_by: str) -> VerificationSchedule:
        """Create a verification schedule."""
        # Generate schedule number
        result = await self.db.execute(select(func.max(VerificationSchedule.id)))
        max_id = result.scalar()
        schedule_number = f"VER-SCH-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        schedule = VerificationSchedule(
            **schedule_data.model_dump(),
            schedule_number=schedule_number,
            created_by=created_by
        )
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule
    
    async def add_verification_item(self, item_data: VerificationItemCreate) -> VerificationItem:
        """Add an item to a verification schedule."""
        item = VerificationItem(**item_data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def verify_item(self, item_id: str, update_data: VerificationItemUpdate, verified_by: str) -> VerificationItem:
        """Verify an item."""
        item = await self.db.get(VerificationItem, item_id)
        if not item:
            raise ValueError("Verification item not found")
        
        item.verified_quantity = update_data.verified_quantity
        item.variance = item.verified_quantity - item.expected_quantity
        item.variance_reason = update_data.variance_reason
        item.verified_by = verified_by
        item.verified_at = datetime.now(timezone.utc)
        
        # Determine status
        if item.variance == 0:
            item.status = "verified"
        else:
            item.status = "discrepancy"
        
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def create_discrepancy(self, discrepancy_data: DiscrepancyCreate) -> Discrepancy:
        """Create a discrepancy record."""
        variance = discrepancy_data.actual_quantity - discrepancy_data.expected_quantity
        
        discrepancy = Discrepancy(
            **discrepancy_data.model_dump(),
            variance=variance
        )
        self.db.add(discrepancy)
        await self.db.commit()
        await self.db.refresh(discrepancy)
        return discrepancy
    
    async def complete_verification(self, schedule_id: str) -> VerificationSchedule:
        """Complete a verification schedule."""
        schedule = await self.db.get(VerificationSchedule, schedule_id)
        if not schedule:
            raise ValueError("Verification schedule not found")
        
        schedule.status = "completed"
        schedule.completed_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(schedule)
        
        # Generate verification report
        await self.generate_verification_report(schedule_id, "system")
        
        return schedule
    
    async def generate_verification_report(self, schedule_id: str, generated_by: str) -> VerificationReport:
        """Generate a verification report."""
        # Generate report number
        result = await self.db.execute(select(func.max(VerificationReport.id)))
        max_id = result.scalar()
        report_number = f"VER-RPT-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        # Get verification items
        result = await self.db.execute(
            select(VerificationItem).where(VerificationItem.schedule_id == schedule_id)
        )
        items = result.scalars().all()
        
        total_items = len(items)
        verified_items = sum(1 for item in items if item.status == "verified")
        discrepancy_count = sum(1 for item in items if item.status == "discrepancy")
        total_variance = sum(item.variance or 0 for item in items if item.variance)
        total_variance_value = 0.0  # In real implementation, calculate from unit prices
        
        report = VerificationReport(
            report_number=report_number,
            schedule_id=schedule_id,
            generated_by=generated_by,
            total_items=total_items,
            verified_items=verified_items,
            discrepancy_count=discrepancy_count,
            total_variance=total_variance,
            total_variance_value=total_variance_value
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report
    
    async def get_discrepancies(self, schedule_id: str) -> List[Discrepancy]:
        """Get discrepancies for a verification schedule."""
        result = await self.db.execute(
            select(Discrepancy).join(
                VerificationItem, Discrepancy.verification_item_id == VerificationItem.id
            ).where(
                VerificationItem.schedule_id == schedule_id
            )
        )
        return result.scalars().all()
    
    async def resolve_discrepancy(self, discrepancy_id: str, resolved_by: str) -> Discrepancy:
        """Resolve a discrepancy."""
        discrepancy = await self.db.get(Discrepancy, discrepancy_id)
        if not discrepancy:
            raise ValueError("Discrepancy not found")
        
        discrepancy.resolution_status = "resolved"
        discrepancy.resolved_by = resolved_by
        discrepancy.resolved_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(discrepancy)
        return discrepancy
