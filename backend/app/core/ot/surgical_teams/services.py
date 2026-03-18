import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import SurgicalTeam
from .schemas import SurgicalTeamCreate, SurgicalTeamUpdate


class SurgicalTeamService:
    @staticmethod
    async def assign_team(db: AsyncSession, team_in: SurgicalTeamCreate) -> SurgicalTeam:
        team = SurgicalTeam(**team_in.model_dump())
        db.add(team)
        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def update_team(db: AsyncSession, schedule_id: uuid.UUID, team_in: SurgicalTeamUpdate) -> SurgicalTeam | None:
        stmt = select(SurgicalTeam).where(SurgicalTeam.schedule_id == schedule_id)
        result = await db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            return None
        
        update_data = team_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)
        
        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def get_team(db: AsyncSession, schedule_id: uuid.UUID) -> SurgicalTeam | None:
        stmt = select(SurgicalTeam).where(SurgicalTeam.schedule_id == schedule_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
