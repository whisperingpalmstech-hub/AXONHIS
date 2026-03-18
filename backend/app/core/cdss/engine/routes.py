from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
import uuid

from app.database import get_db
from app.dependencies import get_current_user

from .schemas import MedicationCheckRequest, CDSSCheckResponse, CDSSAlertResponse, PatientContext
from .services import CDSSEngineService
from .models import CDSSAlert

from ..allergy_checks.services import check_allergy_conflicts
from ..dose_validation.services import validate_drug_dose
from ..duplicate_therapy.models import DrugClass

router = APIRouter()


@router.post("/check-medication", response_model=CDSSCheckResponse)
async def check_medication_safety(
    request: MedicationCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Run full CDSS safety checks on a new medication order.
    Checks: Drug Interactions, Allergy Conflicts, Dose Validation, Duplicate Therapy, Contraindications.
    """
    service = CDSSEngineService()
    return await service.run_medication_checks(db, request)


@router.post("/check-medication-smart", response_model=CDSSCheckResponse)
async def check_medication_safety_smart(
    medication_id: str,
    encounter_id: uuid.UUID,
    patient_id: uuid.UUID,
    dose: float | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Run full CDSS safety checks with automatic context harvesting.
    """
    service = CDSSEngineService()
    context = await service.get_patient_context(db, patient_id, encounter_id)
    
    request = MedicationCheckRequest(
        patient_context=context,
        new_medication_id=medication_id,
        dose=dose
    )
    return await service.run_medication_checks(db, request)


@router.post("/check-allergies", response_model=CDSSCheckResponse)
async def run_allergy_checks(
    request: MedicationCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Run only allergy conflict checks."""
    context = request.patient_context

    result = await db.execute(
        select(DrugClass).where(DrugClass.drug_id == request.new_medication_id)
    )
    drug_class_entry = result.scalar_one_or_none()
    new_med_class = drug_class_entry.drug_class if drug_class_entry else None

    alerts = await check_allergy_conflicts(
        db=db,
        new_med_class=new_med_class,
        patient_allergies=context.allergies,
        patient_id=context.patient_id,
        encounter_id=context.encounter_id
    )

    status_label = "approved"
    for a in alerts:
        if a.severity == "critical":
            status_label = "blocked"
            break
        elif a.severity == "warning":
            status_label = "warning"

    response_alerts = [
        CDSSAlertResponse(id=uuid.uuid4(), created_at=datetime.utcnow(), **a.dict())
        for a in alerts
    ]
    return CDSSCheckResponse(status=status_label, alerts=response_alerts)


@router.post("/check-dose", response_model=CDSSCheckResponse)
async def check_dose(
    request: MedicationCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Run only dose validation checks."""
    context = request.patient_context
    alerts = await validate_drug_dose(
        db=db,
        new_med_id=request.new_medication_id,
        dose=request.dose,
        patient_weight=context.weight_kg,
        patient_age=context.age_years,
        patient_id=context.patient_id,
        encounter_id=context.encounter_id
    )

    status_label = "approved"
    for a in alerts:
        if a.severity == "critical":
            status_label = "blocked"
            break
        elif a.severity == "warning":
            status_label = "warning"

    response_alerts = [
        CDSSAlertResponse(id=uuid.uuid4(), created_at=datetime.utcnow(), **a.dict())
        for a in alerts
    ]
    return CDSSCheckResponse(status=status_label, alerts=response_alerts)


@router.get("/alerts/{encounter_id}", response_model=List[CDSSAlertResponse])
async def get_cdss_alerts(
    encounter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Retrieve all CDSS alerts stored for a given encounter."""
    result = await db.execute(
        select(CDSSAlert).where(CDSSAlert.encounter_id == encounter_id)
    )
    alerts = result.scalars().all()
    return alerts
