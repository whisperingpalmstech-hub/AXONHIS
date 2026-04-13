"""Multi-stage Billing Services for Billing Module."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timezone

from app.core.billing.stages.models import (
    BillStage, BillStageTransition, PartialPayment, BillHold,
    RefundRequest, CreditNote, DebitNote
)
from app.core.billing.stages.schemas import (
    PartialPaymentCreate, BillHoldCreate, RefundRequestCreate,
    CreditNoteCreate, DebitNoteCreate
)


class BillingStagesService:
    """Service for multi-stage billing operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_interim_bill(self, bill_id: str, created_by: str) -> BillStage:
        """Create an interim bill stage."""
        stage = BillStage(
            bill_id=bill_id,
            stage_type="interim",
            created_by=created_by
        )
        self.db.add(stage)
        
        # Record transition
        transition = BillStageTransition(
            bill_id=bill_id,
            to_stage="interim",
            reason="Interim bill generated",
            transitioned_by=created_by
        )
        self.db.add(transition)
        
        await self.db.commit()
        await self.db.refresh(stage)
        return stage
    
    async def create_intermediate_bill(self, bill_id: str, created_by: str) -> BillStage:
        """Create an intermediate bill stage."""
        # Get current stage
        result = await self.db.execute(
            select(BillStage).where(
                BillStage.bill_id == bill_id,
                BillStage.is_active == True
            )
        )
        current_stage = result.scalar_one_or_none()
        
        stage = BillStage(
            bill_id=bill_id,
            stage_type="intermediate",
            previous_stage_id=current_stage.id if current_stage else None,
            created_by=created_by
        )
        self.db.add(stage)
        
        # Deactivate previous stage
        if current_stage:
            current_stage.is_active = False
        
        # Record transition
        transition = BillStageTransition(
            bill_id=bill_id,
            from_stage=current_stage.stage_type if current_stage else None,
            to_stage="intermediate",
            reason="Intermediate bill generated",
            transitioned_by=created_by
        )
        self.db.add(transition)
        
        await self.db.commit()
        await self.db.refresh(stage)
        return stage
    
    async def create_final_bill(self, bill_id: str, created_by: str) -> BillStage:
        """Create a final bill stage."""
        # Get current stage
        result = await self.db.execute(
            select(BillStage).where(
                BillStage.bill_id == bill_id,
                BillStage.is_active == True
            )
        )
        current_stage = result.scalar_one_or_none()
        
        stage = BillStage(
            bill_id=bill_id,
            stage_type="final",
            previous_stage_id=current_stage.id if current_stage else None,
            created_by=created_by
        )
        self.db.add(stage)
        
        # Deactivate previous stage
        if current_stage:
            current_stage.is_active = False
        
        # Record transition
        transition = BillStageTransition(
            bill_id=bill_id,
            from_stage=current_stage.stage_type if current_stage else None,
            to_stage="final",
            reason="Final bill generated",
            transitioned_by=created_by
        )
        self.db.add(transition)
        
        await self.db.commit()
        await self.db.refresh(stage)
        return stage
    
    async def process_partial_payment(
        self, bill_id: str, payment_data: PartialPaymentCreate, received_by: str
    ) -> PartialPayment:
        """Process a partial payment on a bill."""
        payment = PartialPayment(
            bill_id=bill_id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            payment_reference=payment_data.payment_reference,
            reason=payment_data.reason,
            received_by=received_by
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment
    
    async def set_bill_on_hold(
        self, bill_id: str, hold_data: BillHoldCreate, placed_by: str
    ) -> BillHold:
        """Set a bill on hold."""
        hold = BillHold(
            bill_id=bill_id,
            hold_reason=hold_data.hold_reason,
            hold_type=hold_data.hold_type,
            placed_by=placed_by
        )
        self.db.add(hold)
        await self.db.commit()
        await self.db.refresh(hold)
        return hold
    
    async def release_bill_hold(self, bill_id: str, released_by: str) -> bool:
        """Release a bill from hold."""
        result = await self.db.execute(
            select(BillHold).where(
                BillHold.bill_id == bill_id,
                BillHold.is_active == True
            )
        )
        hold = result.scalar_one_or_none()
        
        if hold:
            hold.is_active = False
            hold.released_at = datetime.now(timezone.utc)
            hold.released_by = released_by
            await self.db.commit()
            return True
        return False
    
    async def process_refund(
        self, bill_id: str, refund_data: RefundRequestCreate, requested_by: str
    ) -> RefundRequest:
        """Process a refund request."""
        refund = RefundRequest(
            bill_id=bill_id,
            refund_amount=refund_data.refund_amount,
            refund_method=refund_data.refund_method,
            reason=refund_data.reason,
            requested_by=requested_by
        )
        self.db.add(refund)
        await self.db.commit()
        await self.db.refresh(refund)
        return refund
    
    async def create_credit_note(
        self, bill_id: Optional[str], credit_data: CreditNoteCreate, requested_by: str
    ) -> CreditNote:
        """Create a credit note."""
        # Generate note number
        result = await self.db.execute(
            select(func.max(CreditNote.id))
        )
        max_id = result.scalar()
        note_number = f"CN-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        credit_note = CreditNote(
            bill_id=bill_id,
            note_number=note_number,
            amount=credit_data.amount,
            reason=credit_data.reason,
            requested_by=requested_by
        )
        self.db.add(credit_note)
        await self.db.commit()
        await self.db.refresh(credit_note)
        return credit_note
    
    async def create_debit_note(
        self, bill_id: Optional[str], debit_data: DebitNoteCreate, requested_by: str
    ) -> DebitNote:
        """Create a debit note."""
        # Generate note number
        result = await self.db.execute(
            select(func.max(DebitNote.id))
        )
        max_id = result.scalar()
        note_number = f"DN-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        debit_note = DebitNote(
            bill_id=bill_id,
            note_number=note_number,
            amount=debit_data.amount,
            reason=debit_data.reason,
            requested_by=requested_by
        )
        self.db.add(debit_note)
        await self.db.commit()
        await self.db.refresh(debit_note)
        return debit_note
    
    async def cancel_bill(self, bill_id: str, cancelled_by: str) -> bool:
        """Cancel a bill."""
        # Set bill on hold with cancellation type
        hold = BillHold(
            bill_id=bill_id,
            hold_reason="Bill cancelled",
            hold_type="cancellation",
            placed_by=cancelled_by
        )
        self.db.add(hold)
        
        # Record transition
        result = await self.db.execute(
            select(BillStage).where(
                BillStage.bill_id == bill_id,
                BillStage.is_active == True
            )
        )
        current_stage = result.scalar_one_or_none()
        
        transition = BillStageTransition(
            bill_id=bill_id,
            from_stage=current_stage.stage_type if current_stage else None,
            to_stage="cancelled",
            reason="Bill cancelled",
            transitioned_by=cancelled_by
        )
        self.db.add(transition)
        
        await self.db.commit()
        return True
    
    async def change_bill_stage(
        self, bill_id: str, to_stage: str, reason: str, changed_by: str
    ) -> BillStage:
        """Change bill stage manually."""
        # Get current stage
        result = await self.db.execute(
            select(BillStage).where(
                BillStage.bill_id == bill_id,
                BillStage.is_active == True
            )
        )
        current_stage = result.scalar_one_or_none()
        
        # Create new stage
        stage = BillStage(
            bill_id=bill_id,
            stage_type=to_stage,
            previous_stage_id=current_stage.id if current_stage else None,
            created_by=changed_by
        )
        self.db.add(stage)
        
        # Deactivate previous stage
        if current_stage:
            current_stage.is_active = False
        
        # Record transition
        transition = BillStageTransition(
            bill_id=bill_id,
            from_stage=current_stage.stage_type if current_stage else None,
            to_stage=to_stage,
            reason=reason,
            transitioned_by=changed_by
        )
        self.db.add(transition)
        
        await self.db.commit()
        await self.db.refresh(stage)
        return stage
