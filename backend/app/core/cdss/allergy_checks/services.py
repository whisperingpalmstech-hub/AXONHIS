from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from .models import DrugAllergyMapping
from ..engine.schemas import CDSSAlertCreate
import uuid

async def check_allergy_conflicts(db: AsyncSession, new_med_class: str, patient_allergies: List[str], patient_id: uuid.UUID, encounter_id: uuid.UUID) -> List[CDSSAlertCreate]:
    alerts = []

    if not patient_allergies or not new_med_class:
        return alerts

    result = await db.execute(
        select(DrugAllergyMapping).where(
            DrugAllergyMapping.allergy_type.in_(patient_allergies),
            DrugAllergyMapping.drug_class == new_med_class
        )
    )
    mappings = result.scalars().all()

    for mapping in mappings:
        severity = "critical" if mapping.reaction_risk.lower() in ["severe", "anaphylaxis"] else "warning"
        alert = CDSSAlertCreate(
            encounter_id=encounter_id,
            patient_id=patient_id,
            alert_type="allergy",
            severity=severity,
            message=f"Patient has a documented {mapping.allergy_type} allergy which conflicts with {new_med_class} class. Risk level: {mapping.reaction_risk}",
            recommended_action="DO NOT PRESCRIBE." if severity == "critical" else "Monitor closely for allergic reaction"
        )
        alerts.append(alert)

    return alerts
