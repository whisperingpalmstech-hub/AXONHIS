"""
LIS Test Order Management Engine – Business Logic Services
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.lab.test_order_engine.models import (
    LISTestOrder, LISTestOrderItem, LISTestPanel, LISTestPanelItem,
    LISBarcodeRegistry, LISOrderDocument, LISOrderAuditTrail,
    TestOrderStatus, TestPriority, SampleType
)
from app.core.lab.test_order_engine.schemas import (
    TestOrderCreate, TestOrderItemCreate, PanelCreate, PanelItemCreate,
    PrescriptionScanResult, PhlebotomyWorklistItem
)


# ── 1. Test Order Creation Engine ─────────────────────────────────────────────

class TestOrderCreationEngine:
    """Handles creation of test orders from multiple HIS entry points."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_order_number(self) -> str:
        year = datetime.now(timezone.utc).year
        res = await self.db.execute(
            select(func.count(LISTestOrder.id))
        )
        count = res.scalar() or 0
        return f"LAB-ORD-{year}-{(count + 1):06d}"

    async def _generate_barcode(self, order_id: uuid.UUID, item_id: uuid.UUID,
                                 patient_id: uuid.UUID, sample_type: str) -> str:
        barcode = f"BC-{uuid.uuid4().hex[:8].upper()}"
        registry = LISBarcodeRegistry(
            barcode=barcode,
            order_id=order_id,
            order_item_id=item_id,
            patient_id=patient_id,
            sample_type=sample_type
        )
        self.db.add(registry)
        return barcode

    async def _log_audit(self, order_id: uuid.UUID, action: str,
                          performed_by: Optional[uuid.UUID] = None,
                          details: Optional[dict] = None):
        trail = LISOrderAuditTrail(
            order_id=order_id,
            action=action,
            performed_by=performed_by,
            details=details or {}
        )
        self.db.add(trail)

    async def create_order(self, data: TestOrderCreate,
                            user_id: Optional[uuid.UUID] = None) -> LISTestOrder:
        order_number = await self._generate_order_number()

        # Determine highest priority from items
        max_priority = data.priority
        for item in data.items:
            if item.priority == TestPriority.STAT:
                max_priority = TestPriority.STAT
                break
            elif item.priority == TestPriority.URGENT and max_priority != TestPriority.STAT:
                max_priority = TestPriority.URGENT

        order = LISTestOrder(
            order_number=order_number,
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            encounter_id=data.encounter_id,
            ordering_doctor=data.ordering_doctor,
            department_source=data.department_source,
            order_source=data.order_source,
            priority=max_priority,
            status=TestOrderStatus.DRAFT,
            clinical_indication=data.clinical_indication,
            provisional_diagnosis=data.provisional_diagnosis,
            symptoms=data.symptoms,
            medication_history=data.medication_history,
            created_by=user_id
        )
        self.db.add(order)
        await self.db.flush()

        # Add items
        for item_data in data.items:
            item = LISTestOrderItem(
                order_id=order.id,
                test_code=item_data.test_code,
                test_name=item_data.test_name,
                sample_type=item_data.sample_type,
                priority=item_data.priority,
                price=float(item_data.price),
                status=TestOrderStatus.DRAFT,
                panel_id=item_data.panel_id,
                collection_location=item_data.collection_location,
                notes=item_data.notes
            )
            self.db.add(item)
            await self.db.flush()

            # Generate barcode for each item
            barcode = await self._generate_barcode(
                order.id, item.id, order.patient_id, item.sample_type
            )
            item.barcode = barcode

        await self._log_audit(order.id, "ORDER_CREATED", user_id,
                               {"items_count": len(data.items), "source": data.order_source})
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def add_items_to_order(self, order_id: uuid.UUID,
                                  items: List[TestOrderItemCreate],
                                  user_id: Optional[uuid.UUID] = None) -> LISTestOrder:
        res = await self.db.execute(
            select(LISTestOrder).where(LISTestOrder.id == order_id)
        )
        order = res.scalar_one_or_none()
        if not order:
            raise ValueError("Order not found")

        for item_data in items:
            item = LISTestOrderItem(
                order_id=order.id,
                test_code=item_data.test_code,
                test_name=item_data.test_name,
                sample_type=item_data.sample_type,
                priority=item_data.priority,
                price=float(item_data.price),
                status=order.status,
                panel_id=item_data.panel_id,
                collection_location=item_data.collection_location,
                notes=item_data.notes
            )
            self.db.add(item)
            await self.db.flush()
            barcode = await self._generate_barcode(
                order.id, item.id, order.patient_id, item.sample_type
            )
            item.barcode = barcode

            # Escalate order priority if STAT test added
            if item_data.priority == TestPriority.STAT:
                order.priority = TestPriority.STAT

        await self._log_audit(order.id, "ITEMS_ADDED", user_id,
                               {"added": len(items)})
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def add_panel_to_order(self, order_id: uuid.UUID,
                                  panel_id: uuid.UUID,
                                  user_id: Optional[uuid.UUID] = None) -> LISTestOrder:
        res = await self.db.execute(
            select(LISTestPanel).where(LISTestPanel.id == panel_id)
        )
        panel = res.scalar_one_or_none()
        if not panel:
            raise ValueError("Panel not found")

        items = [
            TestOrderItemCreate(
                test_code=pi.test_code,
                test_name=pi.test_name,
                sample_type=pi.sample_type,
                price=pi.price,
                panel_id=panel.id
            )
            for pi in panel.panel_items
        ]
        return await self.add_items_to_order(order_id, items, user_id)

    async def confirm_order(self, order_id: uuid.UUID,
                             user_id: Optional[uuid.UUID] = None) -> LISTestOrder:
        res = await self.db.execute(
            select(LISTestOrder).where(LISTestOrder.id == order_id)
        )
        order = res.scalar_one_or_none()
        if not order:
            raise ValueError("Order not found")

        order.status = TestOrderStatus.CONFIRMED
        order.confirmed_at = datetime.now(timezone.utc)

        # Update all items
        for item in order.items:
            item.status = TestOrderStatus.CONFIRMED

        await self._log_audit(order.id, "ORDER_CONFIRMED", user_id)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def cancel_order(self, order_id: uuid.UUID, reason: str,
                            user_id: Optional[uuid.UUID] = None) -> LISTestOrder:
        res = await self.db.execute(
            select(LISTestOrder).where(LISTestOrder.id == order_id)
        )
        order = res.scalar_one_or_none()
        if not order:
            raise ValueError("Order not found")

        order.status = TestOrderStatus.CANCELLED
        order.cancelled_at = datetime.now(timezone.utc)
        order.cancellation_reason = reason

        for item in order.items:
            item.status = TestOrderStatus.CANCELLED

        await self._log_audit(order.id, "ORDER_CANCELLED", user_id,
                               {"reason": reason})
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_order(self, order_id: uuid.UUID) -> Optional[LISTestOrder]:
        res = await self.db.execute(
            select(LISTestOrder).where(LISTestOrder.id == order_id)
        )
        return res.scalar_one_or_none()

    async def get_orders_by_patient(self, patient_id: uuid.UUID) -> List[LISTestOrder]:
        res = await self.db.execute(
            select(LISTestOrder)
            .where(LISTestOrder.patient_id == patient_id)
            .order_by(LISTestOrder.created_at.desc())
        )
        return list(res.scalars().all())


# ── 2. Prescription Scan Engine ───────────────────────────────────────────────

class PrescriptionScanEngine:
    """Simulates OCR-based prescription scanning to detect test names."""

    KNOWN_TESTS = {
        "cbc": ("CBC", "Complete Blood Count"),
        "complete blood count": ("CBC", "Complete Blood Count"),
        "lipid profile": ("LIPID", "Lipid Profile"),
        "hba1c": ("HBA1C", "HbA1c - Glycated Hemoglobin"),
        "thyroid profile": ("THYROID", "Thyroid Function Panel"),
        "tsh": ("TSH", "Thyroid Stimulating Hormone"),
        "lft": ("LFT", "Liver Function Test"),
        "liver function": ("LFT", "Liver Function Test"),
        "kft": ("KFT", "Kidney Function Test"),
        "kidney function": ("KFT", "Kidney Function Test"),
        "blood sugar": ("FBS", "Fasting Blood Sugar"),
        "fbs": ("FBS", "Fasting Blood Sugar"),
        "urine routine": ("URINE_RE", "Urine Routine Examination"),
        "ecg": ("ECG", "Electrocardiogram"),
        "crp": ("CRP", "C-Reactive Protein"),
        "esr": ("ESR", "Erythrocyte Sedimentation Rate"),
        "troponin": ("TROP", "Troponin I/T"),
        "hemoglobin": ("HB", "Hemoglobin"),
    }

    async def scan_prescription(self, text: str) -> PrescriptionScanResult:
        text_lower = text.lower()
        detected = []
        for keyword, (code, name) in self.KNOWN_TESTS.items():
            if keyword in text_lower:
                detected.append(name)
        return PrescriptionScanResult(
            detected_tests=detected,
            ocr_text=text,
            confidence=0.85 if detected else 0.0
        )


# ── 3. Panel Management Service ───────────────────────────────────────────────

class PanelManagementService:
    """Manages test panels and profiles."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_panel(self, data: PanelCreate) -> LISTestPanel:
        panel = LISTestPanel(
            panel_code=data.panel_code,
            panel_name=data.panel_name,
            description=data.description,
            category=data.category,
            total_price=float(data.total_price)
        )
        self.db.add(panel)
        await self.db.flush()

        for item_data in data.items:
            item = LISTestPanelItem(
                panel_id=panel.id,
                test_code=item_data.test_code,
                test_name=item_data.test_name,
                sample_type=item_data.sample_type,
                price=float(item_data.price)
            )
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(panel)
        return panel

    async def list_panels(self) -> List[LISTestPanel]:
        res = await self.db.execute(
            select(LISTestPanel).where(LISTestPanel.is_active == True)
        )
        return list(res.scalars().all())

    async def get_panel(self, panel_id: uuid.UUID) -> Optional[LISTestPanel]:
        res = await self.db.execute(
            select(LISTestPanel).where(LISTestPanel.id == panel_id)
        )
        return res.scalar_one_or_none()


# ── 8. Phlebotomy Worklist Service ────────────────────────────────────────────

class PhlebotomyWorklistService:
    """Generates the phlebotomy worklist from confirmed orders."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_worklist(self) -> List[PhlebotomyWorklistItem]:
        res = await self.db.execute(
            select(LISTestOrder)
            .where(LISTestOrder.status.in_([
                TestOrderStatus.CONFIRMED,
                TestOrderStatus.BILLED
            ]))
            .order_by(
                # STAT first, then URGENT, then ROUTINE
                LISTestOrder.priority.desc(),
                LISTestOrder.created_at.asc()
            )
        )
        orders = res.scalars().all()

        worklist = []
        for order in orders:
            for item in order.items:
                worklist.append(PhlebotomyWorklistItem(
                    order_id=order.id,
                    order_number=order.order_number,
                    patient_id=order.patient_id,
                    test_name=item.test_name,
                    test_code=item.test_code,
                    sample_type=item.sample_type,
                    priority=item.priority,
                    collection_location=item.collection_location,
                    barcode=item.barcode
                ))
        return worklist
