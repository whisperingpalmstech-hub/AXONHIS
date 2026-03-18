from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from .models import CDSSAlert
from .schemas import CDSSCheckResponse, CDSSAlertCreate, MedicationCheckRequest, PatientContext
from ..drug_interactions.services import check_drug_interactions
from ..allergy_checks.services import check_allergy_conflicts
from ..dose_validation.services import validate_drug_dose
from ..duplicate_therapy.services import detect_duplicate_therapy
from ..contraindications.services import check_contraindications
from ..allergy_checks.models import DrugAllergyMapping

class CDSSEngineService:
    @staticmethod
    async def run_medication_checks(db: AsyncSession, request: MedicationCheckRequest) -> CDSSCheckResponse:
        context = request.patient_context
        alerts_create: List[CDSSAlertCreate] = []

        # 1. Drug-Drug Interactions
        interactions = await check_drug_interactions(
            db=db,
            new_med_id=request.new_medication_id,
            active_meds=context.active_medications,
            patient_id=context.patient_id,
            encounter_id=context.encounter_id
        )
        alerts_create.extend(interactions)

        # 2. Allergy Conflicts
        from ..duplicate_therapy.models import DrugClass
        # Need to know the drug class of the new medication
        result = await db.execute(select(DrugClass).where(DrugClass.drug_id == request.new_medication_id))
        drug_class_entry = result.scalar_one_or_none()
        new_med_class = drug_class_entry.drug_class if drug_class_entry else None
        
        allergies = await check_allergy_conflicts(
            db=db,
            new_med_class=new_med_class,
            patient_allergies=context.allergies,
            patient_id=context.patient_id,
            encounter_id=context.encounter_id
        )
        alerts_create.extend(allergies)

        # 3. Dose Validation
        dose_alerts = await validate_drug_dose(
            db=db,
            new_med_id=request.new_medication_id,
            dose=request.dose,
            patient_weight=context.weight_kg,
            patient_age=context.age_years,
            patient_id=context.patient_id,
            encounter_id=context.encounter_id
        )
        alerts_create.extend(dose_alerts)

        # 4. Duplicate Therapy
        duplicate_alerts = await detect_duplicate_therapy(
            db=db,
            new_med_id=request.new_medication_id,
            active_meds=context.active_medications,
            patient_id=context.patient_id,
            encounter_id=context.encounter_id
        )
        alerts_create.extend(duplicate_alerts)

        # 5. Contraindications
        contraindications = await check_contraindications(
            db=db,
            new_med_id=request.new_medication_id,
            diagnoses=context.diagnoses,
            patient_id=context.patient_id,
            encounter_id=context.encounter_id
        )
        alerts_create.extend(contraindications)

        # Save alerts to DB
        saved_alerts = []
        status = "approved"
        
        for alert_data in alerts_create:
            if alert_data.severity == "critical":
                status = "blocked"
            elif alert_data.severity in ["warning", "major", "moderate", "minor"] and status != "blocked":
                status = "warning"
                
            db_alert = CDSSAlert(**alert_data.model_dump())
            db.add(db_alert)
            saved_alerts.append(db_alert)
            
        if saved_alerts:
            await db.commit()
            for a in saved_alerts:
                await db.refresh(a)

        return CDSSCheckResponse(
            status=status,
            alerts=saved_alerts
        )
