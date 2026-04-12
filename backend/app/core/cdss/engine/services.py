from datetime import datetime
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
from ..clinical_risk_.services import check_clinical_risks
from ..allergy_checks.models import DrugAllergyMapping
from app.core.encounters.timeline.services import TimelineService
from app.core.encounters.timeline.schemas import EncounterTimelineCreate
from app.core.encounters.diagnoses.models import EncounterDiagnosis
from app.core.pharmacy.prescriptions.models import Prescription, PrescriptionItem
from app.core.patients.patients.models import Patient
import uuid

class CDSSEngineService:
    @staticmethod
    async def get_patient_context(db: AsyncSession, patient_id: uuid.UUID, encounter_id: uuid.UUID) -> PatientContext:
        # 1. Get Patient (for age/allergies)
        result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = result.scalar_one_or_none()
        
        # 2. Get Diagnoses
        result = await db.execute(select(EncounterDiagnosis).where(EncounterDiagnosis.encounter_id == encounter_id))
        diagnoses_records = result.scalars().all()
        diagnoses = [d.diagnosis_code for d in diagnoses_records]
        
        # 3. Get Active Medications
        # Find all approved/dispensed prescriptions for this patient
        result = await db.execute(
            select(PrescriptionItem.drug_id)
            .join(Prescription)
            .where(Prescription.patient_id == patient_id, Prescription.status.in_(["approved", "dispensed"]))
        )
        active_med_ids = [str(mid) for mid in result.scalars().all()]
        
        # 4. Calculate approximate age
        age = None
        if patient and patient.date_of_birth:
            age = (datetime.now().date() - patient.date_of_birth).days / 365.25

        # 5. Get allergies from patient record
        allergies_list = []
        if patient and patient.allergies:
            allergies_list = [a.strip() for a in patient.allergies.split(",")]

        return PatientContext(
            patient_id=patient_id,
            encounter_id=encounter_id,
            age_years=age,
            weight_kg=70.0, # Defaulting for now
            allergies=allergies_list,
            active_medications=active_med_ids,
            diagnoses=diagnoses
        )

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

        # 6. Clinical Risks
        risk_alerts = await check_clinical_risks(db, context, request.new_medication_id)
        alerts_create.extend(risk_alerts)

        # Save alerts to DB
        saved_alerts = []
        # 7. Final status determination
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

            # Generate Timeline Events
            ts = TimelineService(db)
            event_type = "CDSS_CRITICAL_BLOCK" if status == "blocked" else "CDSS_WARNING_GENERATED"
            severity_str = "CRITICAL" if status == "blocked" else "WARNING"
            
            # Use any alert's patient/encounter context (they are same for request)
            await ts.add_event(
                encounter_id=context.encounter_id,
                actor_id=None, # System generated or could be user_id if passed
                data=EncounterTimelineCreate(
                    event_type=event_type,
                    description=f"Clinical Decision Support: {severity_str} alerts generated for medication {request.new_medication_id}.",
                    metadata_json={
                        "alert_status": status,
                        "alert_count": len(saved_alerts),
                        "medication_id": request.new_medication_id
                    }
                )
            )

        return CDSSCheckResponse(
            status=status,
            alerts=saved_alerts
        )
