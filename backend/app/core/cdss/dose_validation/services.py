from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from .models import DrugDosageGuideline
from ..engine.schemas import CDSSAlertCreate
import uuid

async def validate_drug_dose(db: AsyncSession, new_med_id: str, dose: float, patient_weight: Optional[float], patient_age: Optional[float], patient_id: uuid.UUID, encounter_id: uuid.UUID) -> List[CDSSAlertCreate]:
    alerts = []

    if dose is None:
        return alerts

    result = await db.execute(
        select(DrugDosageGuideline).where(DrugDosageGuideline.drug_id == new_med_id)
    )
    guidelines = result.scalars().all()

    if not guidelines:
        return alerts

    for guideline in guidelines:
        is_pediatric = patient_age and patient_age < 18
        if guideline.age_group == "pediatric" and not is_pediatric:
            continue
        if guideline.age_group == "adult" and is_pediatric:
            continue

        if dose < guideline.min_dose:
            alerts.append(CDSSAlertCreate(
                encounter_id=encounter_id,
                patient_id=patient_id,
                alert_type="dosage",
                severity="warning",
                message=f"Prescribed dose ({dose}) is below the recommended minimum ({guideline.min_dose})",
                recommended_action="Consider increasing dosage for efficacy."
            ))
        elif dose > guideline.max_dose:
            alerts.append(CDSSAlertCreate(
                encounter_id=encounter_id,
                patient_id=patient_id,
                alert_type="dosage",
                severity="warning",
                message=f"Prescribed dose ({dose}) exceeds the recommended maximum ({guideline.max_dose})",
                recommended_action="Reduce dosage to prevent toxicity."
            ))

    return alerts
