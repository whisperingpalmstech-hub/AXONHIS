import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import SurgicalProcedure
from .schemas import SurgicalProcedureCreate, SurgicalProcedureUpdate


class SurgicalProcedureService:
    @staticmethod
    async def create_procedure(db: AsyncSession, procedure_in: SurgicalProcedureCreate) -> SurgicalProcedure:
        procedure = SurgicalProcedure(**procedure_in.model_dump())
        db.add(procedure)
        await db.commit()
        await db.refresh(procedure)
        return procedure

    @staticmethod
    async def get_procedure(db: AsyncSession, procedure_id: uuid.UUID) -> SurgicalProcedure | None:
        return await db.get(SurgicalProcedure, procedure_id)

    @staticmethod
    async def get_all_procedures(db: AsyncSession) -> list[SurgicalProcedure]:
        result = await db.execute(select(SurgicalProcedure))
        return list(result.scalars().all())

    @staticmethod
    async def update_procedure(db: AsyncSession, procedure_id: uuid.UUID, procedure_in: SurgicalProcedureUpdate) -> SurgicalProcedure | None:
        procedure = await db.get(SurgicalProcedure, procedure_id)
        if not procedure:
            return None
        
        update_data = procedure_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(procedure, field, value)
        
        await db.commit()
        await db.refresh(procedure)
        return procedure

    @staticmethod
    async def delete_procedure(db: AsyncSession, procedure_id: uuid.UUID) -> bool:
        procedure = await db.get(SurgicalProcedure, procedure_id)
        if not procedure:
            return False
        await db.delete(procedure)
        await db.commit()
        return True
