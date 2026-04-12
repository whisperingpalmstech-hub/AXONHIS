from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..engine.schemas import CDSSAlertCreate, PatientContext

async def check_clinical_risks(db: AsyncSession, context: PatientContext, medication_id: str) -> List[CDSSAlertCreate]:
    alerts = []
    
    # 1. Geriatric Risk (Beer's Criteria basic check)
    if context.age_years and context.age_years >= 65:
        high_risk_geriatric = ["Diazepam", "Amitriptyline", "Indomethacin"]
        if any(med.lower() in medication_id.lower() for med in high_risk_geriatric):
            alerts.append(CDSSAlertCreate(
                alert_type="clinical_risk",
                severity="warning",
                message=f"Potentially inappropriate medication in the elderly per Beer's Criteria: {medication_id}.",
                recommended_action="Consider alternative therapy with lower risk of falls or confusion.",
                is_blocking=False
            ))

    # 2. Vital-Medication Interaction (Simplified example)
    # If heart rate is high, warn about caffeine/stimulants
    # (Note: context would need vitals, let's assume weight is there for now and maybe we add vitals later)
    
    return alerts
