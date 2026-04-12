from typing import List, Optional
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.cssd.models import (
    InstrumentSet, SterilizationCycle, CycleSetLink, CSSDDispatch,
    CycleStatus, InstrumentCondition
)
from app.core.cssd.schemas import (
    InstrumentSetCreate, SterilizationCycleCreate,
    SterilizationCycleStatusUpdate, CSSDDispatchCreate, CSSDDispatchReturn
)


class CSSDService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Instrument Sets ────────────────────────────────────
    async def create_instrument_set(self, data: InstrumentSetCreate, org_id: uuid.UUID) -> InstrumentSet:
        instrument = InstrumentSet(**data.model_dump(), org_id=org_id)
        self.db.add(instrument)
        await self.db.commit()
        await self.db.refresh(instrument)
        return instrument

    async def get_instrument_sets(self, org_id: uuid.UUID) -> List[InstrumentSet]:
        result = await self.db.execute(
            select(InstrumentSet).where(InstrumentSet.org_id == org_id).order_by(InstrumentSet.name)
        )
        return list(result.scalars().all())

    # ─── Sterilization Cycles ───────────────────────────────
    async def create_cycle(self, data: SterilizationCycleCreate, operator_id: uuid.UUID, org_id: uuid.UUID) -> SterilizationCycle:
        cycle = SterilizationCycle(
            cycle_number=data.cycle_number,
            machine_id=data.machine_id,
            method=data.method,
            temperature_celsius=data.temperature_celsius,
            pressure_psi=data.pressure_psi,
            exposure_minutes=data.exposure_minutes,
            notes=data.notes,
            operator_id=operator_id,
            status=CycleStatus.loading,
            start_time=datetime.utcnow(),
            org_id=org_id
        )
        self.db.add(cycle)
        await self.db.flush()  # Get cycle.id

        # Link instrument sets to this cycle
        for set_id in data.set_ids:
            link = CycleSetLink(cycle_id=cycle.id, set_id=set_id, org_id=org_id)
            self.db.add(link)

        await self.db.commit()
        await self.db.refresh(cycle)
        return cycle

    async def get_cycles(self, org_id: uuid.UUID) -> List[SterilizationCycle]:
        result = await self.db.execute(
            select(SterilizationCycle)
            .where(SterilizationCycle.org_id == org_id)
            .order_by(SterilizationCycle.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_cycle_status(self, cycle_id: uuid.UUID, data: SterilizationCycleStatusUpdate, org_id: uuid.UUID) -> SterilizationCycle:
        result = await self.db.execute(
            select(SterilizationCycle).where(
                SterilizationCycle.id == cycle_id,
                SterilizationCycle.org_id == org_id
            )
        )
        cycle = result.scalar_one_or_none()
        if not cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")

        cycle.status = data.status
        if data.bi_result:
            cycle.bi_result = data.bi_result
        if data.ci_result:
            cycle.ci_result = data.ci_result
        if data.end_time:
            cycle.end_time = data.end_time

        await self.db.commit()
        await self.db.refresh(cycle)
        return cycle

    # ─── Dispatches ─────────────────────────────────────────
    async def dispatch_set(self, data: CSSDDispatchCreate, user_id: uuid.UUID, org_id: uuid.UUID) -> CSSDDispatch:
        dispatch = CSSDDispatch(
            set_id=data.set_id,
            cycle_id=data.cycle_id,
            destination_department=data.destination_department,
            dispatched_by=user_id,
            org_id=org_id
        )
        self.db.add(dispatch)
        await self.db.commit()
        await self.db.refresh(dispatch)
        return dispatch

    async def get_dispatches(self, org_id: uuid.UUID) -> List[CSSDDispatch]:
        result = await self.db.execute(
            select(CSSDDispatch)
            .where(CSSDDispatch.org_id == org_id)
            .order_by(CSSDDispatch.dispatched_at.desc())
        )
        return list(result.scalars().all())

    async def return_dispatch(self, dispatch_id: uuid.UUID, data: CSSDDispatchReturn, org_id: uuid.UUID) -> CSSDDispatch:
        result = await self.db.execute(
            select(CSSDDispatch).where(CSSDDispatch.id == dispatch_id, CSSDDispatch.org_id == org_id)
        )
        dispatch = result.scalar_one_or_none()
        if not dispatch:
            raise HTTPException(status_code=404, detail="Dispatch not found")

        dispatch.returned_at = datetime.utcnow()
        dispatch.return_condition = data.return_condition
        if data.notes:
            dispatch.notes = data.notes

        # Update set condition
        set_result = await self.db.execute(
            select(InstrumentSet).where(InstrumentSet.id == dispatch.set_id)
        )
        instrument_set = set_result.scalar_one_or_none()
        if instrument_set:
            instrument_set.condition = data.return_condition

        await self.db.commit()
        await self.db.refresh(dispatch)
        return dispatch

    # ─── Dashboard Stats ────────────────────────────────────
    async def get_stats(self, org_id: uuid.UUID) -> dict:
        sets_result = await self.db.execute(
            select(InstrumentSet).where(InstrumentSet.org_id == org_id, InstrumentSet.is_active == True)
        )
        sets = list(sets_result.scalars().all())

        cycles_result = await self.db.execute(
            select(SterilizationCycle).where(SterilizationCycle.org_id == org_id)
        )
        cycles = list(cycles_result.scalars().all())

        dispatches_result = await self.db.execute(
            select(CSSDDispatch).where(CSSDDispatch.org_id == org_id, CSSDDispatch.returned_at == None)
        )
        pending_returns = list(dispatches_result.scalars().all())

        active_cycles = [c for c in cycles if c.status in (CycleStatus.loading, CycleStatus.in_progress)]
        completed_cycles = [c for c in cycles if c.status == CycleStatus.completed or c.status == CycleStatus.released]

        return {
            "total_sets": len(sets),
            "serviceable_sets": len([s for s in sets if s.condition == InstrumentCondition.serviceable]),
            "active_cycles": len(active_cycles),
            "completed_today": len([c for c in completed_cycles if c.end_time and c.end_time.date() == datetime.utcnow().date()]),
            "pending_returns": len(pending_returns),
            "damaged_sets": len([s for s in sets if s.condition == InstrumentCondition.damaged]),
        }
