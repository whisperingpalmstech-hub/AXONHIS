"""
LIS Test Order Management Engine – API Routes
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.lab.test_order_engine.schemas import (
    TestOrderCreate, TestOrderOut, AddItemsRequest, AddPanelRequest,
    CancelOrderRequest, PanelCreate, PanelOut, BarcodeOut,
    PrescriptionScanResult, PhlebotomyWorklistItem, AuditTrailOut
)
from app.core.lab.test_order_engine.services import (
    TestOrderCreationEngine, PrescriptionScanEngine,
    PanelManagementService, PhlebotomyWorklistService
)

router = APIRouter(prefix="/lis-orders", tags=["LIS Test Order Management Engine"])


# ── 1. Test Order CRUD ────────────────────────────────────────────────────────

@router.post("/orders", response_model=TestOrderOut)
async def create_test_order(
    data: TestOrderCreate,
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new laboratory test order."""
    engine = TestOrderCreationEngine(db)
    order = await engine.create_order(data, user_id)
    return order


@router.get("/orders/{order_id}", response_model=TestOrderOut)
async def get_test_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific test order by ID."""
    engine = TestOrderCreationEngine(db)
    order = await engine.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/orders/patient/{patient_id}", response_model=List[TestOrderOut])
async def get_patient_orders(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get all test orders for a patient."""
    engine = TestOrderCreationEngine(db)
    return await engine.get_orders_by_patient(patient_id)


# ── Add items / panels to order ───────────────────────────────────────────────

@router.post("/orders/{order_id}/items", response_model=TestOrderOut)
async def add_items_to_order(
    order_id: uuid.UUID,
    data: AddItemsRequest,
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Add individual tests to an existing order."""
    engine = TestOrderCreationEngine(db)
    try:
        return await engine.add_items_to_order(order_id, data.items, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/orders/{order_id}/panel", response_model=TestOrderOut)
async def add_panel_to_order(
    order_id: uuid.UUID,
    data: AddPanelRequest,
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Add an entire test panel to an existing order."""
    engine = TestOrderCreationEngine(db)
    try:
        return await engine.add_panel_to_order(order_id, data.panel_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Confirm / Cancel ──────────────────────────────────────────────────────────

@router.post("/orders/{order_id}/confirm", response_model=TestOrderOut)
async def confirm_test_order(
    order_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Confirm an order and push it to phlebotomy worklist."""
    engine = TestOrderCreationEngine(db)
    try:
        return await engine.confirm_order(order_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/orders/{order_id}/cancel", response_model=TestOrderOut)
async def cancel_test_order(
    order_id: uuid.UUID,
    data: CancelOrderRequest,
    user_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a test order."""
    engine = TestOrderCreationEngine(db)
    try:
        return await engine.cancel_order(order_id, data.reason, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── 2. Prescription Scan ─────────────────────────────────────────────────────

@router.post("/prescription-scan", response_model=PrescriptionScanResult)
async def scan_prescription(text: str = Query(..., description="Prescription text to scan")):
    """Scan prescription text to detect lab tests via OCR engine."""
    engine = PrescriptionScanEngine()
    return await engine.scan_prescription(text)


# ── 3. Panel Management ──────────────────────────────────────────────────────

@router.post("/panels", response_model=PanelOut)
async def create_panel(data: PanelCreate, db: AsyncSession = Depends(get_db)):
    """Create a new test panel/profile."""
    svc = PanelManagementService(db)
    return await svc.create_panel(data)


@router.get("/panels", response_model=List[PanelOut])
async def list_panels(db: AsyncSession = Depends(get_db)):
    """List all active test panels."""
    svc = PanelManagementService(db)
    return await svc.list_panels()


@router.get("/panels/{panel_id}", response_model=PanelOut)
async def get_panel(panel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific panel by ID."""
    svc = PanelManagementService(db)
    panel = await svc.get_panel(panel_id)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    return panel


# ── 8. Phlebotomy Worklist ────────────────────────────────────────────────────

@router.get("/phlebotomy-worklist", response_model=List[PhlebotomyWorklistItem])
async def get_phlebotomy_worklist(db: AsyncSession = Depends(get_db)):
    """Get the current phlebotomy sample collection worklist."""
    svc = PhlebotomyWorklistService(db)
    return await svc.get_worklist()
