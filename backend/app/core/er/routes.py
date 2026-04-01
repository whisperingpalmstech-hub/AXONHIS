"""ER Module — API Routes. Interconnected with billing, IPD, orders, pharmacy."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import CurrentUser

from .schemas import (
    ERRegistrationCreate, EREncounterOut, ERTriageCreate, ERTriageOut,
    ERBedCreate, ERBedOut, ERBedAssignRequest, ERMlcCreate, ERMlcOut,
    ERNursingScoreCreate, ERNursingScoreOut, EROrderCreate, EROrderOut,
    ERStatusUpdate, ERDashboardStats
)
from .services import (
    ERRegistrationService, ERTriageService, ERBedService,
    ERMlcService, ERScoringService, EROrderService,
    ERDashboardService, ERBedSeeder
)

router = APIRouter(prefix="/er", tags=["Emergency Room (ER)"])

# ── Dashboard ────────────────────────────────────
@router.get("/dashboard", response_model=ERDashboardStats)
async def get_er_dashboard(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERDashboardService(db).get_stats(user.org_id)

# ── Registration ─────────────────────────────────
@router.post("/register", response_model=EREncounterOut)
async def register_er_patient(data: ERRegistrationCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERRegistrationService(db).register_patient(data, user.org_id)

@router.get("/encounters", response_model=List[EREncounterOut])
async def list_er_encounters(user: CurrentUser, status: Optional[str] = None, zone: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return await ERRegistrationService(db).list_encounters(user.org_id, status, zone)

@router.get("/encounters/{encounter_id}", response_model=EREncounterOut)
async def get_er_encounter(encounter_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERRegistrationService(db).get_encounter(encounter_id, user.org_id)

@router.put("/encounters/{encounter_id}/status", response_model=EREncounterOut)
async def update_er_status(encounter_id: uuid.UUID, data: ERStatusUpdate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERRegistrationService(db).update_status(encounter_id, data, user.org_id)

# ── Triage ───────────────────────────────────────
@router.post("/triage", response_model=ERTriageOut)
async def assess_triage(data: ERTriageCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    name = getattr(user, 'full_name', None) or getattr(user, 'email', 'Staff')
    return await ERTriageService(db).assess_triage(data, user.id, str(name), user.org_id)

@router.get("/triage/{er_encounter_id}", response_model=ERTriageOut)
async def get_triage(er_encounter_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    t = await ERTriageService(db).get_triage(er_encounter_id, user.org_id)
    if not t: raise HTTPException(404, "Triage not found")
    return t

# ── Beds ─────────────────────────────────────────
@router.get("/beds", response_model=List[ERBedOut])
async def list_er_beds(user: CurrentUser, zone: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return await ERBedService(db).list_beds(user.org_id, zone)

@router.post("/beds", response_model=ERBedOut)
async def create_er_bed(data: ERBedCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERBedService(db).create_bed(data.bed_code, data.zone, data.bed_type, user.org_id, is_monitored=data.is_monitored, has_ventilator=data.has_ventilator)

@router.post("/beds/assign", response_model=ERBedOut)
async def assign_er_bed(data: ERBedAssignRequest, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERBedService(db).assign_bed(data, user.org_id)

@router.post("/beds/{bed_id}/vacate", response_model=ERBedOut)
async def vacate_er_bed(bed_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERBedService(db).vacate_bed(bed_id, user.org_id)

@router.post("/beds/{bed_id}/cleaned", response_model=ERBedOut)
async def mark_er_bed_cleaned(bed_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERBedService(db).mark_cleaned(bed_id, user.org_id)

# ── MLC ──────────────────────────────────────────
@router.post("/mlc", response_model=ERMlcOut)
async def create_mlc_case(data: ERMlcCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERMlcService(db).create_mlc(data, user.id, user.org_id)

@router.get("/mlc", response_model=List[ERMlcOut])
async def list_mlc_cases(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERMlcService(db).list_mlc_cases(user.org_id)

# ── Scores ───────────────────────────────────────
@router.post("/scores", response_model=ERNursingScoreOut)
async def record_nursing_score(data: ERNursingScoreCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    name = getattr(user, 'full_name', None) or getattr(user, 'email', 'Staff')
    return await ERScoringService(db).record_score(data, user.id, str(name), user.org_id)

@router.get("/scores/{er_encounter_id}", response_model=List[ERNursingScoreOut])
async def get_nursing_scores(er_encounter_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ERScoringService(db).get_scores(er_encounter_id, user.org_id)

# ── Orders ───────────────────────────────────────
@router.post("/orders", response_model=EROrderOut)
async def create_er_order(data: EROrderCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    name = getattr(user, 'full_name', None) or getattr(user, 'email', 'Staff')
    return await EROrderService(db).create_order(data, user.id, str(name), user.org_id)

@router.get("/orders/{er_encounter_id}", response_model=List[EROrderOut])
async def list_er_orders(er_encounter_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await EROrderService(db).list_orders(er_encounter_id, user.org_id)

# ── Seed ─────────────────────────────────────────
@router.post("/seed-beds")
async def seed_er_beds(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    count = await ERBedSeeder(db).seed_default_beds(user.org_id)
    return {"status": "ok", "beds_seeded": count}
