from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from .models import DrugClass
from ..engine.schemas import CDSSAlertCreate
import uuid

async def detect_duplicate_therapy(db: AsyncSession, new_med_id: str, active_meds: List[str], patient_id: uuid.UUID, encounter_id: uuid.UUID) -> List[CDSSAlertCreate]:
    alerts = []

    if not active_meds:
        return alerts

    result = await db.execute(
        select(DrugClass).where(DrugClass.drug_id == new_med_id)
    )
    new_med_class_entry = result.scalar_one_or_none()

    if not new_med_class_entry:
        return alerts

    new_med_therapeutic_group = new_med_class_entry.therapeutic_group

    result = await db.execute(
        select(DrugClass).where(DrugClass.drug_id.in_(active_meds))
    )
    active_meds_classes = result.scalars().all()

    for amc in active_meds_classes:
        if amc.therapeutic_group == new_med_therapeutic_group:
            alerts.append(CDSSAlertCreate(
                encounter_id=encounter_id,
                patient_id=patient_id,
                alert_type="duplicate",
                severity="warning",
                message=f"Duplicate therapy detected. Both new medication and active medication belong to {new_med_therapeutic_group}.",
                recommended_action="Consider discontinuing one of the overlapping medications."
            ))
            break

    return alerts
