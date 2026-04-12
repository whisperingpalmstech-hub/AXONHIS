"""
Cross-Module Integration Services
====================================
Orchestrates multi-module workflows:
1. ChargePostingService — posts charges from ANY module to billing
2. PatientLedgerService — real-time financial summary 
3. ERToIPDTransferService — ER discharge → IPD admission
4. IntegrationEventService — audit trail for all cross-module ops
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CrossModuleEvent, ChargePosting, PatientLedger
from .schemas import ChargePostingCreate, ERToIPDTransferRequest


def _now(): return datetime.now(timezone.utc)


class ChargePostingService:
    """Post charges from any clinical module → centralized billing ledger."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def post_charge(self, data: ChargePostingCreate, posted_by: uuid.UUID, 
                          posted_by_name: str, org_id: uuid.UUID) -> ChargePosting:
        # Calculate pricing
        net = data.unit_price * data.quantity
        stat_surcharge = Decimal("0")
        if data.is_stat:
            stat_surcharge = net * Decimal("0.25")  # 25% STAT surcharge
            net += stat_surcharge
        
        # GST (5% for healthcare services)
        tax = net * Decimal("0.05")
        
        charge = ChargePosting(
            org_id=org_id,
            patient_id=data.patient_id,
            encounter_type=data.encounter_type,
            encounter_id=data.encounter_id,
            service_id=data.service_id,
            service_code=data.service_code,
            service_name=data.service_name,
            service_group=data.service_group,
            source_module=data.source_module,
            source_order_id=data.source_order_id,
            quantity=data.quantity,
            unit_price=data.unit_price,
            discount_amount=Decimal("0"),
            tax_amount=tax,
            net_amount=net + tax,
            is_stat=data.is_stat,
            stat_surcharge=stat_surcharge,
            posted_by=posted_by,
            posted_by_name=posted_by_name,
        )
        self.db.add(charge)
        
        # Update patient ledger
        await self._update_ledger(org_id, data.patient_id, data.encounter_type, 
                                   data.encounter_id, net + tax, tax)
        
        await self.db.commit()
        await self.db.refresh(charge)
        return charge

    async def get_charges(self, patient_id: uuid.UUID, encounter_id: uuid.UUID,
                          org_id: uuid.UUID) -> List[ChargePosting]:
        return list((await self.db.execute(
            select(ChargePosting).where(
                ChargePosting.org_id == org_id,
                ChargePosting.patient_id == patient_id,
                ChargePosting.encounter_id == encounter_id,
                ChargePosting.is_cancelled == False
            ).order_by(ChargePosting.posted_at.desc())
        )).scalars().all())

    async def get_unbilled_total(self, patient_id: uuid.UUID, encounter_id: uuid.UUID,
                                 org_id: uuid.UUID) -> Decimal:
        result = await self.db.execute(
            select(func.sum(ChargePosting.net_amount)).where(
                ChargePosting.org_id == org_id,
                ChargePosting.patient_id == patient_id,
                ChargePosting.encounter_id == encounter_id,
                ChargePosting.is_billed == False,
                ChargePosting.is_cancelled == False
            )
        )
        return result.scalar() or Decimal("0")

    async def cancel_charge(self, charge_id: uuid.UUID, reason: str, 
                            org_id: uuid.UUID) -> ChargePosting:
        charge = (await self.db.execute(
            select(ChargePosting).where(
                ChargePosting.id == charge_id, ChargePosting.org_id == org_id
            )
        )).scalars().first()
        if not charge:
            raise ValueError("Charge not found")
        charge.is_cancelled = True
        charge.cancelled_reason = reason
        await self.db.commit()
        await self.db.refresh(charge)
        return charge

    async def _update_ledger(self, org_id, patient_id, encounter_type, encounter_id,
                              charge_amount, tax_amount):
        ledger = (await self.db.execute(
            select(PatientLedger).where(
                PatientLedger.org_id == org_id,
                PatientLedger.patient_id == patient_id,
                PatientLedger.encounter_id == encounter_id
            )
        )).scalars().first()
        
        if not ledger:
            ledger = PatientLedger(
                org_id=org_id, patient_id=patient_id,
                encounter_type=encounter_type, encounter_id=encounter_id
            )
            self.db.add(ledger)
        
        ledger.total_charges = (ledger.total_charges or Decimal("0")) + charge_amount
        ledger.total_tax = (ledger.total_tax or Decimal("0")) + tax_amount
        ledger.outstanding_balance = (
            (ledger.total_charges or Decimal("0")) -
            (ledger.total_payments or Decimal("0")) -
            (ledger.total_deposits or Decimal("0")) -
            (ledger.total_insurance_covered or Decimal("0")) -
            (ledger.total_discounts or Decimal("0"))
        )
        ledger.last_updated = _now()


class PatientLedgerService:
    """Real-time patient financial summary."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ledger(self, patient_id: uuid.UUID, encounter_id: uuid.UUID,
                         org_id: uuid.UUID) -> Optional[PatientLedger]:
        return (await self.db.execute(
            select(PatientLedger).where(
                PatientLedger.org_id == org_id,
                PatientLedger.patient_id == patient_id,
                PatientLedger.encounter_id == encounter_id
            )
        )).scalars().first()

    async def record_payment(self, patient_id: uuid.UUID, encounter_id: uuid.UUID,
                             amount: Decimal, org_id: uuid.UUID) -> PatientLedger:
        ledger = await self.get_ledger(patient_id, encounter_id, org_id)
        if not ledger:
            raise ValueError("Ledger not found for this encounter")
        ledger.total_payments = (ledger.total_payments or Decimal("0")) + amount
        ledger.outstanding_balance = (
            (ledger.total_charges or Decimal("0")) -
            (ledger.total_payments or Decimal("0")) -
            (ledger.total_deposits or Decimal("0")) -
            (ledger.total_insurance_covered or Decimal("0")) -
            (ledger.total_discounts or Decimal("0"))
        )
        ledger.last_updated = _now()
        await self.db.commit()
        await self.db.refresh(ledger)
        return ledger

    async def record_deposit(self, patient_id: uuid.UUID, encounter_id: uuid.UUID,
                             amount: Decimal, org_id: uuid.UUID) -> PatientLedger:
        ledger = await self.get_ledger(patient_id, encounter_id, org_id)
        if not ledger:
            raise ValueError("Ledger not found")
        ledger.total_deposits = (ledger.total_deposits or Decimal("0")) + amount
        ledger.outstanding_balance = (
            (ledger.total_charges or Decimal("0")) -
            (ledger.total_payments or Decimal("0")) -
            (ledger.total_deposits or Decimal("0")) -
            (ledger.total_insurance_covered or Decimal("0")) -
            (ledger.total_discounts or Decimal("0"))
        )
        ledger.last_updated = _now()
        await self.db.commit()
        await self.db.refresh(ledger)
        return ledger


class ERToIPDTransferService:
    """Orchestrates ER → IPD admission transfer."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def transfer(self, data: ERToIPDTransferRequest, transferred_by: uuid.UUID,
                       org_id: uuid.UUID) -> dict:
        from app.core.er.models import EREncounter
        
        # Get ER encounter
        enc = (await self.db.execute(
            select(EREncounter).where(
                EREncounter.id == data.er_encounter_id, EREncounter.org_id == org_id
            )
        )).scalars().first()
        if not enc:
            raise ValueError("ER encounter not found")
        
        # Update ER encounter
        enc.status = "transferred_to_ipd"
        enc.disposition = "admit_ipd"
        enc.disposition_department = data.department
        enc.discharge_time = _now()
        
        # Log cross-module event
        event = CrossModuleEvent(
            org_id=org_id,
            event_type="er_to_ipd",
            source_module="er",
            target_module="ipd",
            source_id=data.er_encounter_id,
            patient_id=enc.patient_id,
            payload={
                "patient_name": enc.patient_name,
                "department": data.department,
                "bed_category": data.bed_category,
                "er_number": enc.er_number,
                "triage_priority": enc.priority,
            },
            status="completed",
            triggered_by=transferred_by,
        )
        self.db.add(event)
        await self.db.commit()
        
        return {
            "status": "transferred",
            "er_number": enc.er_number,
            "patient_name": enc.patient_name,
            "target_department": data.department,
            "transfer_time": _now().isoformat(),
        }


class IntegrationEventService:
    """Audit trail for all cross-module operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(self, event_type: str, source_module: str, target_module: str,
                        source_id: uuid.UUID, target_id: uuid.UUID, org_id: uuid.UUID,
                        triggered_by: uuid.UUID, patient_id: uuid.UUID = None,
                        payload: dict = None) -> CrossModuleEvent:
        event = CrossModuleEvent(
            org_id=org_id, event_type=event_type, source_module=source_module,
            target_module=target_module, source_id=source_id, target_id=target_id,
            patient_id=patient_id, payload=payload, triggered_by=triggered_by,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_events(self, org_id: uuid.UUID, source_module: str = None,
                         limit: int = 50) -> List[CrossModuleEvent]:
        stmt = select(CrossModuleEvent).where(CrossModuleEvent.org_id == org_id)
        if source_module:
            stmt = stmt.where(CrossModuleEvent.source_module == source_module)
        return list((await self.db.execute(
            stmt.order_by(CrossModuleEvent.triggered_at.desc()).limit(limit)
        )).scalars().all())
