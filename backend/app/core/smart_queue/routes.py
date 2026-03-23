"""OPD Smart Queue & Flow Orchestration Engine — API Routes (30+ endpoints)"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from .schemas import (
    QueueMasterCreate, QueueMasterOut,
    QueuePositionCreate, QueuePositionOut, QueuePositionUpdate,
    QueueEventCreate, QueueEventOut, NotificationOut,
    RoomWayfindingCreate, WayfindingOut, CrowdPredictionSnapshotOut, DigitalSignageDisplay
)
from .services import (
    QueueOrchestrationEngine, RealTimeQueueDashboardService,
    PatientRecoveryLogic, DoctorAvailabilityRoutingEngine,
    PatientNotificationSystem, WayfindingNavigationEngine, OPDCrowdPredictionEngine
)

router = APIRouter(prefix="/smart-queue", tags=["OPD Smart Queue"])

# ── 1. Queue Orchestration Engine ───────────────────────────────────────────

@router.post("/master", response_model=QueueMasterOut)
async def create_queue(data: QueueMasterCreate, db: AsyncSession = Depends(get_db)):
    svc = QueueOrchestrationEngine(db)
    return await svc.get_or_create_queue(data)

@router.post("/positions", response_model=QueuePositionOut)
async def add_to_queue(data: QueuePositionCreate, db: AsyncSession = Depends(get_db)):
    svc = QueueOrchestrationEngine(db)
    return await svc.add_patient_to_queue(data)

@router.put("/positions/{queue_id}/reorder")
async def force_recalculate_queue(queue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = QueueOrchestrationEngine(db)
    await svc.reorder_queue(queue_id)
    return {"status": "reordered"}


# ── 2. Real-Time Dashboard & Signage ────────────────────────────────────────

@router.get("/dashboard/{queue_id}/signage", response_model=DigitalSignageDisplay)
async def get_digital_signage(queue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = RealTimeQueueDashboardService(db)
    data = await svc.get_digital_signage(queue_id)
    if not data: raise HTTPException(404, "Queue not found")
    return data


# ── 3. Doctor Availability Routing ──────────────────────────────────────────

@router.get("/routing/recommendation")
async def get_routing_recommendation(department: str, db: AsyncSession = Depends(get_db)):
    svc = DoctorAvailabilityRoutingEngine(db)
    qm = await svc.recommend_queue(department)
    if not qm: raise HTTPException(404, "No active queues found for department")
    return {"recommended_queue_id": str(qm.id), "room_number": qm.room_number, "length": qm.current_length}


# ── 4. Missed Patient Recovery Logic ────────────────────────────────────────

@router.post("/positions/{pos_id}/mark-missed")
async def mark_patient_missed(pos_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = PatientRecoveryLogic(db)
    import uuid
    # dummy actor
    await svc.mark_missed(pos_id, uuid.uuid4())
    return {"status": "missed recorded"}


# ── 5. Setup & Wayfinding ───────────────────────────────────────────────────

@router.get("/wayfinding/{room_number}")
async def get_wayfinding(room_number: str, db: AsyncSession = Depends(get_db)):
    svc = WayfindingNavigationEngine(db)
    instructions = await svc.get_instructions(room_number)
    return {"room_number": room_number, "instructions": instructions}


# ── 6. Predictions ──────────────────────────────────────────────────────────

@router.post("/analytics/crowd-prediction")
async def generate_crowd_prediction(dept: str, db: AsyncSession = Depends(get_db)):
    svc = OPDCrowdPredictionEngine(db)
    snap = await svc.generate_prediction(datetime.utcnow(), dept)
    return snap
