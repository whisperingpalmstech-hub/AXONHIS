from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from .models import DrugContraindication
from ..engine.schemas import CDSSAlertCreate
import uuid

async def check_contraindications(db: AsyncSession, new_med_id: str, diagnoses: List[str], patient_id: uuid.UUID, encounter_id: uuid.UUID) -> List[CDSSAlertCreate]:
    alerts = []

    if not diagnoses:
        return alerts

    result = await db.execute(
        select(DrugContraindication).where(
            DrugContraindication.drug_id == new_med_id,
            DrugContraindication.contraindicated_condition.in_(diagnoses)
        )
    )
    contraindications = result.scalars().all()

    for contraindication in contraindications:
        alert = CDSSAlertCreate(
            encounter_id=encounter_id,
            patient_id=patient_id,
            alert_type="contraindication",
            severity="critical",
            message=f"Drug contraindicated due to patient's diagnosis of {contraindication.contraindicated_condition}. {contraindication.risk_description}",
            recommended_action="DO NOT PRESCRIBE."
        )
        alerts.append(alert)

    return alerts
