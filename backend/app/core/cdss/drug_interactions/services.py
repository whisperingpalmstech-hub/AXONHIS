from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List
from .models import DrugInteraction
from ..engine.schemas import CDSSAlertCreate
import uuid

async def check_drug_interactions(db: AsyncSession, new_med_id: str, active_meds: List[str], patient_id: uuid.UUID, encounter_id: uuid.UUID) -> List[CDSSAlertCreate]:
    alerts = []

    if not active_meds:
        return alerts

    result = await db.execute(
        select(DrugInteraction).where(
            or_(
                and_(DrugInteraction.drug_a == new_med_id, DrugInteraction.drug_b.in_(active_meds)),
                and_(DrugInteraction.drug_b == new_med_id, DrugInteraction.drug_a.in_(active_meds))
            )
        )
    )
    interactions = result.scalars().all()

    for interaction in interactions:
        alert = CDSSAlertCreate(
            encounter_id=encounter_id,
            patient_id=patient_id,
            alert_type="interaction",
            severity=interaction.severity,
            message=interaction.interaction_description,
            recommended_action="Consider alternative medication or monitor closely." if interaction.severity != "contraindicated" else "DO NOT PRESCRIBE."
        )
        alerts.append(alert)

    return alerts
