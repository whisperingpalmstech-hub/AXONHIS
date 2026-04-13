"""Stock Movement Analytics Services for Inventory."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.core.inventory.movement.models import (
    StockTransfer, StockTransferItem, MovementReport, TransferApproval
)
from app.core.inventory.movement.schemas import (
    StockTransferCreate, StockTransferItemCreate, TransferApprovalCreate,
    MovementReportRequest
)


class MovementService:
    """Service for stock movement analytics operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_stock_transfer(self, transfer_data: StockTransferCreate, requested_by: str) -> StockTransfer:
        """Create a stock transfer request."""
        # Generate transfer number
        result = await self.db.execute(select(func.max(StockTransfer.id)))
        max_id = result.scalar()
        transfer_number = f"TRF-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        transfer = StockTransfer(
            **transfer_data.model_dump(),
            transfer_number=transfer_number,
            requested_by=requested_by
        )
        self.db.add(transfer)
        await self.db.commit()
        await self.db.refresh(transfer)
        return transfer
    
    async def add_transfer_item(self, transfer_id: str, item_data: StockTransferItemCreate) -> StockTransferItem:
        """Add an item to a transfer."""
        item = StockTransferItem(
            transfer_id=transfer_id,
            **item_data.model_dump()
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def approve_transfer(self, transfer_id: str, approval_data: TransferApprovalCreate, approver_id: str) -> TransferApproval:
        """Approve a transfer."""
        approval = TransferApproval(
            transfer_id=transfer_id,
            approver_id=approver_id,
            **approval_data.model_dump()
        )
        self.db.add(approval)
        
        # Update transfer status if all approvals are done
        transfer = await self.db.get(StockTransfer, transfer_id)
        if transfer:
            transfer.status = "approved"
            transfer.approved_by = approver_id
            transfer.approved_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(approval)
        return approval
    
    async def execute_transfer(self, transfer_id: str) -> StockTransfer:
        """Execute a transfer (ship items)."""
        transfer = await self.db.get(StockTransfer, transfer_id)
        if not transfer or transfer.status != "approved":
            raise ValueError("Transfer not found or not approved")
        
        transfer.status = "in_transit"
        transfer.shipped_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(transfer)
        return transfer
    
    async def receive_transfer(self, transfer_id: str, received_by: str) -> StockTransfer:
        """Receive a transfer."""
        transfer = await self.db.get(StockTransfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")
        
        transfer.status = "received"
        transfer.received_at = datetime.now(timezone.utc)
        transfer.received_by = received_by
        
        # Update stock ledger for each item
        result = await self.db.execute(
            select(StockTransferItem).where(StockTransferItem.transfer_id == transfer_id)
        )
        items = result.scalars().all()
        
        for item in items:
            # Create movement report
            report = MovementReport(
                report_type="inter_store",
                from_store_id=transfer.from_store_id,
                to_store_id=transfer.to_store_id,
                item_id=item.item_id,
                batch_record_id=item.batch_record_id,
                quantity=item.received_quantity,
                movement_date=datetime.now(timezone.utc),
                reference_type="transfer",
                reference_id=transfer.transfer_number
            )
            self.db.add(report)
        
        await self.db.commit()
        await self.db.refresh(transfer)
        return transfer
    
    async def track_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Track transfer status."""
        transfer = await self.db.get(StockTransfer, transfer_id)
        if not transfer:
            raise ValueError("Transfer not found")
        
        # Get items
        result = await self.db.execute(
            select(StockTransferItem).where(StockTransferItem.transfer_id == transfer_id)
        )
        items = result.scalars().all()
        
        return {
            "transfer_id": str(transfer.id),
            "transfer_number": transfer.transfer_number,
            "status": transfer.status,
            "from_store_id": str(transfer.from_store_id),
            "to_store_id": str(transfer.to_store_id),
            "items": [
                {
                    "item_id": str(item.item_id),
                    "requested_quantity": float(item.requested_quantity),
                    "approved_quantity": float(item.approved_quantity) if item.approved_quantity else 0,
                    "shipped_quantity": float(item.shipped_quantity),
                    "received_quantity": float(item.received_quantity),
                    "variance": float(item.variance) if item.variance else 0
                }
                for item in items
            ]
        }
    
    async def generate_movement_report(self, report_data: MovementReportRequest) -> List[MovementReport]:
        """Generate a movement report."""
        query = select(MovementReport)
        
        if report_data.from_store_id:
            query = query.where(MovementReport.from_store_id == report_data.from_store_id)
        if report_data.to_store_id:
            query = query.where(MovementReport.to_store_id == report_data.to_store_id)
        if report_data.item_id:
            query = query.where(MovementReport.item_id == report_data.item_id)
        if report_data.from_date:
            query = query.where(MovementReport.movement_date >= report_data.from_date)
        if report_data.to_date:
            query = query.where(MovementReport.movement_date <= report_data.to_date)
        if report_data.report_type:
            query = query.where(MovementReport.report_type == report_data.report_type)
        
        query = query.order_by(MovementReport.movement_date.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_store_movement_analytics(self, store_id: str) -> Dict[str, Any]:
        """Get movement analytics for a store."""
        # Get receipts
        receipts_result = await self.db.execute(
            select(func.sum(MovementReport.quantity)).where(
                MovementReport.to_store_id == store_id,
                MovementReport.report_type.in_(["receipt", "inter_store"])
            )
        )
        total_receipts = receipts_result.scalar() or 0
        
        # Get issues
        issues_result = await self.db.execute(
            select(func.sum(MovementReport.quantity)).where(
                MovementReport.from_store_id == store_id,
                MovementReport.report_type.in_(["issue", "inter_store"])
            )
        )
        total_issues = issues_result.scalar() or 0
        
        # Get consumption
        consumption_result = await self.db.execute(
            select(func.sum(MovementReport.quantity)).where(
                MovementReport.from_store_id == store_id,
                MovementReport.report_type == "consumption"
            )
        )
        total_consumption = consumption_result.scalar() or 0
        
        return {
            "store_id": store_id,
            "total_receipts": float(total_receipts),
            "total_issues": float(total_issues),
            "total_consumption": float(total_consumption),
            "net_change": float(total_receipts - total_issues - total_consumption)
        }
    
    async def get_item_movement_history(self, item_id: str) -> List[MovementReport]:
        """Get movement history for an item."""
        result = await self.db.execute(
            select(MovementReport).where(
                MovementReport.item_id == item_id
            ).order_by(MovementReport.movement_date.desc())
        )
        return result.scalars().all()
