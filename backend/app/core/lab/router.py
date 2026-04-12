"""Lab router – Full LIS API endpoints."""
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.lab.models import LabTest, LabOrder, LabSample, LabResult, LabValidation
from app.core.lab.schemas import (
    LabTestCreate, LabTestOut,
    LabOrderCreate, LabOrderOut,
    LabSampleCreate, LabSampleOut,
    LabResultCreate, LabResultOut,
    LabValidationCreate, LabValidationOut,
    LabDashboardStats,
)
from app.core.lab.services import LabService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/lab", tags=["lab"])


# ── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard/stats", response_model=LabDashboardStats)
async def get_dashboard_stats(db: DBSession, _: CurrentUser):
    stats = await LabService(db).get_dashboard_stats()
    return LabDashboardStats(**stats)


# ── Test Catalog ─────────────────────────────────────────────────────────────

@router.get("/tests", response_model=list[LabTestOut])
async def list_tests(db: DBSession, _: CurrentUser, category: str | None = None):
    tests = await LabService(db).list_tests(category=category)
    return [LabTestOut.model_validate(t) for t in tests]


@router.post("/tests", response_model=LabTestOut, status_code=201)
async def create_test(data: LabTestCreate, db: DBSession, user: CurrentUser):
    svc = LabService(db)
    existing = await svc.get_test_by_code(data.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"Test with code '{data.code}' already exists")
    test = await svc.create_test(**data.model_dump())
    return LabTestOut.model_validate(test)


@router.get("/tests/{test_id}", response_model=LabTestOut)
async def get_test(test_id: uuid.UUID, db: DBSession, _: CurrentUser):
    test = await LabService(db).get_test_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return LabTestOut.model_validate(test)


# ── Lab Orders ───────────────────────────────────────────────────────────────

@router.post("/orders", response_model=LabOrderOut, status_code=201)
async def create_lab_order(data: LabOrderCreate, db: DBSession, user: CurrentUser):
    lab_order = await LabService(db).create_lab_order(
        order_id=data.order_id,
        patient_id=data.patient_id,
        encounter_id=data.encounter_id,
        notes=data.notes,
    )
    await EventService(db).emit(
        EventType.ORDER_CREATED,
        summary="Lab order created",
        patient_id=data.patient_id,
        actor_id=user.id,
        payload={"lab_order_id": str(lab_order.id)},
    )
    return LabOrderOut.model_validate(lab_order)


@router.get("/orders", response_model=list[LabOrderOut])
async def list_lab_orders(db: DBSession, _: CurrentUser, status: str | None = None):
    orders = await LabService(db).list_lab_orders(status=status)
    return [LabOrderOut.model_validate(o) for o in orders]


@router.get("/orders/{lab_order_id}", response_model=LabOrderOut)
async def get_lab_order(lab_order_id: uuid.UUID, db: DBSession, _: CurrentUser):
    lab_order = await LabService(db).get_lab_order(lab_order_id)
    if not lab_order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return LabOrderOut.model_validate(lab_order)


# ── Samples ──────────────────────────────────────────────────────────────────

@router.post("/samples", response_model=LabSampleOut, status_code=201)
async def collect_sample(data: LabSampleCreate, db: DBSession, user: CurrentUser):
    sample = await LabService(db).collect_sample(
        lab_order_id=data.lab_order_id,
        sample_type=data.sample_type,
        collected_by=user.id,
        notes=data.notes,
    )
    return LabSampleOut.model_validate(sample)


@router.get("/samples", response_model=list[LabSampleOut])
async def list_samples(db: DBSession, _: CurrentUser, status: str | None = None):
    samples = await LabService(db).list_samples(status=status)
    return [LabSampleOut.model_validate(s) for s in samples]


@router.get("/samples/barcode/{barcode}", response_model=LabSampleOut)
async def get_sample_by_barcode(barcode: str, db: DBSession, _: CurrentUser):
    sample = await LabService(db).get_sample_by_barcode(barcode)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return LabSampleOut.model_validate(sample)


@router.post("/samples/{sample_id}/receive", response_model=LabSampleOut)
async def receive_sample(sample_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = LabService(db)
    sample = await svc.get_sample_by_id(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    sample = await svc.update_sample_status(sample, "RECEIVED_IN_LAB")
    return LabSampleOut.model_validate(sample)


@router.post("/samples/{sample_id}/process", response_model=LabSampleOut)
async def start_sample_processing(sample_id: uuid.UUID, db: DBSession, _: CurrentUser,
                                   analyzer_name: str | None = None):
    svc = LabService(db)
    sample = await svc.get_sample_by_id(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    await svc.start_processing(sample_id, analyzer_name=analyzer_name)
    sample = await svc.get_sample_by_id(sample_id)
    return LabSampleOut.model_validate(sample)


# ── Results ──────────────────────────────────────────────────────────────────

@router.post("/results", response_model=LabResultOut, status_code=201)
async def submit_result(data: LabResultCreate, db: DBSession, user: CurrentUser):
    svc = LabService(db)
    result = await svc.enter_result(
        sample_id=data.sample_id,
        test_id=data.test_id,
        order_id=data.order_id,
        patient_id=data.patient_id,
        value=data.value,
        numeric_value=data.numeric_value,
        unit=data.unit,
        reference_range=data.reference_range,
        notes=data.notes,
        entered_by=user.id,
    )

    # Emit event
    event_type = EventType.ALERT_RAISED if result.is_critical else EventType.LAB_RESULT_AVAILABLE
    summary = f"CRITICAL lab result for test" if result.is_critical else "Lab result submitted"
    await EventService(db).emit(
        event_type,
        summary=summary,
        patient_id=data.patient_id,
        actor_id=user.id,
        payload={
            "result_id": str(result.id),
            "order_id": str(data.order_id),
            "is_critical": result.is_critical,
            "result_flag": result.result_flag,
        },
    )
    return LabResultOut.model_validate(result)


@router.get("/results/patient/{patient_id}", response_model=list[LabResultOut])
async def get_patient_results(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    results = await LabService(db).get_patient_results(patient_id)
    return [LabResultOut.model_validate(r) for r in results]


@router.get("/results/order/{order_id}", response_model=list[LabResultOut])
async def get_order_results(order_id: uuid.UUID, db: DBSession, _: CurrentUser):
    results = await LabService(db).get_results_for_order(order_id)
    return [LabResultOut.model_validate(r) for r in results]


@router.get("/results/pending-validation", response_model=list[LabResultOut])
async def get_pending_validation(db: DBSession, _: CurrentUser):
    results = await LabService(db).list_pending_validation()
    return [LabResultOut.model_validate(r) for r in results]


# ── Validation ───────────────────────────────────────────────────────────────

@router.post("/validate", response_model=LabValidationOut)
async def validate_result(data: LabValidationCreate, db: DBSession, user: CurrentUser):
    validation = await LabService(db).validate_result(
        result_id=data.result_id,
        validated_by=user.id,
        validation_status=data.validation_status,
        rejection_reason=data.rejection_reason,
    )
    if not validation:
        raise HTTPException(status_code=404, detail="Result or validation not found")
    return LabValidationOut.model_validate(validation)
