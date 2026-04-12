"""
LIS Central Receiving & Specimen Tracking Engine – Business Logic Services
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    CRReceipt, CRVerification, CRRejection, CRRouting, CRStorage,
    CRChainOfCustody, CRAlert, CRAudit,
    ReceiptStatus, VerificationResult, AlertSeverity, AlertStatus,
    TEST_DEPARTMENT_MAP, LabDepartment,
)
from app.core.lab.phlebotomy_engine.models import SampleCollection, SampleCollectionStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Audit Helper ──────────────────────────────────────────────────────────────

class CRAuditService:
    @staticmethod
    async def log(db: AsyncSession, entity_type: str, entity_id: uuid.UUID,
                  action: str, performed_by: str | None = None, details: dict | None = None):
        entry = CRAudit(entity_type=entity_type, entity_id=entity_id,
                        action=action, performed_by=performed_by, details=details)
        db.add(entry)
        return entry

    @staticmethod
    async def get_trail(db: AsyncSession, entity_type: str | None = None,
                        entity_id: str | None = None, limit: int = 50) -> list[CRAudit]:
        stmt = select(CRAudit)
        if entity_type:
            stmt = stmt.where(CRAudit.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(CRAudit.entity_id == uuid.UUID(entity_id))
        stmt = stmt.order_by(CRAudit.performed_at.desc()).limit(limit)
        return list((await db.execute(stmt)).scalars().all())


# ── Chain of Custody ──────────────────────────────────────────────────────────

class ChainOfCustodyService:
    @staticmethod
    async def add_entry(db: AsyncSession, receipt_id: uuid.UUID, sample_id: str,
                        stage: str, location: str, staff: str, notes: str | None = None):
        entry = CRChainOfCustody(
            receipt_id=receipt_id, sample_id=sample_id,
            stage=stage, location=location, responsible_staff=staff, notes=notes,
        )
        db.add(entry)
        return entry

    @staticmethod
    async def get_chain(db: AsyncSession, receipt_id: str) -> list[CRChainOfCustody]:
        stmt = (select(CRChainOfCustody)
                .where(CRChainOfCustody.receipt_id == uuid.UUID(receipt_id))
                .order_by(CRChainOfCustody.timestamp.asc()))
        return list((await db.execute(stmt)).scalars().all())


# ── 1. Receipt Service ────────────────────────────────────────────────────────

class ReceiptService:
    @staticmethod
    async def register_by_barcode(db: AsyncSession, barcode: str, received_by: str,
                                   notes: str | None = None) -> CRReceipt:
        """Scan barcode → find sample from phlebotomy → create CR receipt."""
        # Look up collected sample
        result = await db.execute(
            select(SampleCollection).where(SampleCollection.barcode == barcode)
        )
        sample = result.scalar_one_or_none()
        if not sample:
            raise ValueError(f"No collected sample found with barcode: {barcode}")

        # Check for duplicate receipt
        dup = await db.execute(
            select(CRReceipt).where(CRReceipt.barcode == barcode)
        )
        if dup.scalar_one_or_none():
            raise ValueError(f"Sample with barcode {barcode} already received at CR")

        # Look up worklist for order info
        from app.core.lab.phlebotomy_engine.models import PhlebotomyWorklist
        wl_result = await db.execute(
            select(PhlebotomyWorklist).where(PhlebotomyWorklist.id == sample.worklist_id)
        )
        wl = wl_result.scalar_one_or_none()

        receipt = CRReceipt(
            sample_id=sample.sample_id,
            barcode=barcode,
            order_id=sample.order_id,
            order_number=wl.order_number if wl else "N/A",
            patient_id=sample.patient_id,
            patient_name=wl.patient_name if wl else None,
            patient_uhid=sample.patient_uhid,
            test_code=sample.test_code,
            test_name=sample.test_name,
            sample_type=sample.sample_type,
            container_type=sample.container_type,
            collection_time=sample.collected_at,
            collection_location=sample.collection_location,
            priority=wl.priority if wl else "ROUTINE",
            received_by=received_by,
            status=ReceiptStatus.RECEIVED,
            notes=notes,
        )
        db.add(receipt)

        # Update sample status to RECEIVED_IN_LAB
        await db.execute(
            update(SampleCollection).where(SampleCollection.id == sample.id)
            .values(status=SampleCollectionStatus.RECEIVED_IN_LAB)
        )

        # Chain of custody
        await ChainOfCustodyService.add_entry(
            db, receipt.id, sample.sample_id,
            "RECEIVED_AT_CR", "CENTRAL_RECEIVING", received_by
        )

        await CRAuditService.log(db, "RECEIPT", receipt.id, "SAMPLE_RECEIVED", received_by, {
            "barcode": barcode, "sample_id": sample.sample_id, "test_code": sample.test_code,
        })

        await db.commit()
        await db.refresh(receipt)
        return receipt

    @staticmethod
    async def get_receipt(db: AsyncSession, receipt_id: str) -> CRReceipt | None:
        return (await db.execute(
            select(CRReceipt).where(CRReceipt.id == uuid.UUID(receipt_id))
        )).scalar_one_or_none()

    @staticmethod
    async def get_receipt_by_barcode(db: AsyncSession, barcode: str) -> CRReceipt | None:
        return (await db.execute(
            select(CRReceipt).where(CRReceipt.barcode == barcode)
        )).scalar_one_or_none()

    @staticmethod
    async def list_receipts(db: AsyncSession, status: str | None = None,
                            priority: str | None = None, department: str | None = None
                            ) -> list[CRReceipt]:
        stmt = select(CRReceipt)
        filters = []
        if status:
            filters.append(CRReceipt.status == status)
        if priority:
            filters.append(CRReceipt.priority == priority)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(CRReceipt.priority.desc(), CRReceipt.received_at.desc())
        return list((await db.execute(stmt)).scalars().all())


# ── 2. Verification Service ──────────────────────────────────────────────────

class VerificationService:
    @staticmethod
    async def verify_sample(db: AsyncSession, receipt_id: str,
                            checks: dict, verified_by: str,
                            remarks: str | None = None) -> CRVerification:
        rcpt = await ReceiptService.get_receipt(db, receipt_id)
        if not rcpt:
            raise ValueError("Receipt not found")

        all_pass = all([
            checks.get("sample_type_correct", True),
            checks.get("container_correct", True),
            checks.get("volume_adequate", True),
            checks.get("labeling_correct", True),
            checks.get("transport_ok", True),
            not checks.get("hemolyzed", False),
            not checks.get("clotted", False),
        ])

        result = VerificationResult.PASS if all_pass else VerificationResult.FAIL

        verification = CRVerification(
            receipt_id=uuid.UUID(receipt_id),
            sample_type_correct=checks.get("sample_type_correct", True),
            container_correct=checks.get("container_correct", True),
            volume_adequate=checks.get("volume_adequate", True),
            labeling_correct=checks.get("labeling_correct", True),
            transport_ok=checks.get("transport_ok", True),
            hemolyzed=checks.get("hemolyzed", False),
            clotted=checks.get("clotted", False),
            overall_result=result,
            verified_by=verified_by,
            remarks=remarks,
        )
        db.add(verification)

        new_status = ReceiptStatus.ACCEPTED if all_pass else ReceiptStatus.VERIFIED
        await db.execute(
            update(CRReceipt).where(CRReceipt.id == rcpt.id).values(status=new_status)
        )

        await ChainOfCustodyService.add_entry(
            db, rcpt.id, rcpt.sample_id,
            f"VERIFIED_{result}", "CENTRAL_RECEIVING", verified_by
        )

        await CRAuditService.log(db, "VERIFICATION", verification.id,
                                  f"SAMPLE_{result}", verified_by, {
            "receipt_id": receipt_id, "result": result,
        })

        await db.commit()
        await db.refresh(verification)
        return verification


# ── 3. Rejection Service ──────────────────────────────────────────────────────

class RejectionService:
    @staticmethod
    async def reject_sample(db: AsyncSession, receipt_id: str, reason: str,
                            details: str | None, rejected_by: str,
                            recollection: bool = True) -> CRRejection:
        rcpt = await ReceiptService.get_receipt(db, receipt_id)
        if not rcpt:
            raise ValueError("Receipt not found")

        rejection = CRRejection(
            receipt_id=uuid.UUID(receipt_id),
            rejection_reason=reason,
            rejection_details=details,
            rejected_by=rejected_by,
            recollection_requested=recollection,
            notification_sent=True,
            notification_targets={
                "ordering_doctor": True,
                "phlebotomy_team": True,
                "nursing_station": True,
            },
        )
        db.add(rejection)

        await db.execute(
            update(CRReceipt).where(CRReceipt.id == rcpt.id)
            .values(status=ReceiptStatus.REJECTED)
        )

        await ChainOfCustodyService.add_entry(
            db, rcpt.id, rcpt.sample_id,
            "REJECTED", "CENTRAL_RECEIVING", rejected_by, f"Reason: {reason}"
        )

        # Create alert for recollection
        if recollection:
            alert = CRAlert(
                alert_type="RECOLLECTION_REQUIRED",
                severity=AlertSeverity.WARNING,
                sample_id=rcpt.sample_id,
                order_number=rcpt.order_number,
                patient_name=rcpt.patient_name,
                message=f"Sample {rcpt.sample_id} rejected ({reason}). Recollection required for {rcpt.test_name}.",
            )
            db.add(alert)

        await CRAuditService.log(db, "REJECTION", rejection.id,
                                  "SAMPLE_REJECTED", rejected_by, {
            "receipt_id": receipt_id, "reason": reason,
        })

        await db.commit()
        await db.refresh(rejection)
        return rejection

    @staticmethod
    async def list_rejections(db: AsyncSession) -> list[CRRejection]:
        return list((await db.execute(
            select(CRRejection).order_by(CRRejection.rejected_at.desc())
        )).scalars().all())


# ── 4. Routing Service ────────────────────────────────────────────────────────

class RoutingService:
    @staticmethod
    async def route_sample(db: AsyncSession, receipt_id: str,
                           target_dept: str | None, routed_by: str,
                           notes: str | None = None) -> CRRouting:
        rcpt = await ReceiptService.get_receipt(db, receipt_id)
        if not rcpt:
            raise ValueError("Receipt not found")

        # Auto-detect department
        if not target_dept:
            target_dept = TEST_DEPARTMENT_MAP.get(rcpt.test_code, LabDepartment.BIOCHEMISTRY)

        routing = CRRouting(
            receipt_id=uuid.UUID(receipt_id),
            target_department=target_dept,
            routed_by=routed_by,
            notes=notes,
        )
        db.add(routing)

        await db.execute(
            update(CRReceipt).where(CRReceipt.id == rcpt.id)
            .values(status=ReceiptStatus.ROUTED, current_location=target_dept)
        )

        await ChainOfCustodyService.add_entry(
            db, rcpt.id, rcpt.sample_id,
            "ROUTED_TO_DEPT", target_dept, routed_by
        )

        await CRAuditService.log(db, "ROUTING", routing.id,
                                  "SAMPLE_ROUTED", routed_by, {
            "receipt_id": receipt_id, "department": target_dept,
        })

        await db.commit()
        await db.refresh(routing)
        return routing

    @staticmethod
    async def receive_at_department(db: AsyncSession, routing_id: str,
                                     received_by: str) -> CRRouting:
        result = await db.execute(
            select(CRRouting).where(CRRouting.id == uuid.UUID(routing_id))
        )
        routing = result.scalar_one_or_none()
        if not routing:
            raise ValueError("Routing not found")

        await db.execute(
            update(CRRouting).where(CRRouting.id == routing.id)
            .values(received_at_dept=_now(), received_by_dept=received_by, status="RECEIVED_AT_DEPT")
        )

        await db.execute(
            update(CRReceipt).where(CRReceipt.id == routing.receipt_id)
            .values(status=ReceiptStatus.PROCESSING)
        )

        # Chain of custody
        rcpt = await ReceiptService.get_receipt(db, str(routing.receipt_id))
        if rcpt:
            await ChainOfCustodyService.add_entry(
                db, rcpt.id, rcpt.sample_id,
                "RECEIVED_AT_DEPT", routing.target_department, received_by
            )

        await CRAuditService.log(db, "ROUTING", routing.id,
                                  "RECEIVED_AT_DEPT", received_by, {
            "department": routing.target_department,
        })

        await db.commit()
        await db.refresh(routing)
        return routing

    @staticmethod
    async def list_routings(db: AsyncSession, department: str | None = None) -> list[CRRouting]:
        stmt = select(CRRouting)
        if department:
            stmt = stmt.where(CRRouting.target_department == department)
        stmt = stmt.order_by(CRRouting.routed_at.desc())
        return list((await db.execute(stmt)).scalars().all())


# ── 5. Storage Service ────────────────────────────────────────────────────────

class StorageService:
    @staticmethod
    async def store_sample(db: AsyncSession, receipt_id: str, location: str,
                           temperature: str, max_hours: int, stored_by: str) -> CRStorage:
        rcpt = await ReceiptService.get_receipt(db, receipt_id)
        if not rcpt:
            raise ValueError("Receipt not found")

        storage = CRStorage(
            receipt_id=uuid.UUID(receipt_id),
            storage_location=location,
            storage_temperature=temperature,
            max_duration_hours=max_hours,
            stored_by=stored_by,
        )
        db.add(storage)

        await db.execute(
            update(CRReceipt).where(CRReceipt.id == rcpt.id)
            .values(status=ReceiptStatus.STORED, current_location=f"STORAGE:{location}")
        )

        await ChainOfCustodyService.add_entry(
            db, rcpt.id, rcpt.sample_id,
            "STORED", f"STORAGE:{location}", stored_by, f"Temp: {temperature}"
        )

        await CRAuditService.log(db, "STORAGE", storage.id,
                                  "SAMPLE_STORED", stored_by, {
            "location": location, "temperature": temperature,
        })

        await db.commit()
        await db.refresh(storage)
        return storage

    @staticmethod
    async def retrieve_sample(db: AsyncSession, storage_id: str,
                               retrieved_by: str) -> CRStorage:
        result = await db.execute(
            select(CRStorage).where(CRStorage.id == uuid.UUID(storage_id))
        )
        storage = result.scalar_one_or_none()
        if not storage:
            raise ValueError("Storage record not found")

        await db.execute(
            update(CRStorage).where(CRStorage.id == storage.id)
            .values(retrieved_at=_now(), retrieved_by=retrieved_by, is_active=False)
        )

        rcpt = await ReceiptService.get_receipt(db, str(storage.receipt_id))
        if rcpt:
            await ChainOfCustodyService.add_entry(
                db, rcpt.id, rcpt.sample_id,
                "RETRIEVED_FROM_STORAGE", "CENTRAL_RECEIVING", retrieved_by
            )

        await CRAuditService.log(db, "STORAGE", storage.id,
                                  "SAMPLE_RETRIEVED", retrieved_by, {})

        await db.commit()
        await db.refresh(storage)
        return storage

    @staticmethod
    async def list_active_storage(db: AsyncSession) -> list[CRStorage]:
        return list((await db.execute(
            select(CRStorage).where(CRStorage.is_active == True)
            .order_by(CRStorage.stored_at.asc())
        )).scalars().all())


# ── 6. Alert Service ──────────────────────────────────────────────────────────

class AlertService:
    @staticmethod
    async def list_alerts(db: AsyncSession, status: str | None = None) -> list[CRAlert]:
        stmt = select(CRAlert)
        if status:
            stmt = stmt.where(CRAlert.status == status)
        stmt = stmt.order_by(CRAlert.created_at.desc())
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def acknowledge_alert(db: AsyncSession, alert_id: str,
                                 acknowledged_by: str) -> CRAlert:
        await db.execute(
            update(CRAlert).where(CRAlert.id == uuid.UUID(alert_id))
            .values(status=AlertStatus.ACKNOWLEDGED,
                    acknowledged_by=acknowledged_by,
                    acknowledged_at=_now())
        )
        await db.commit()
        result = await db.execute(
            select(CRAlert).where(CRAlert.id == uuid.UUID(alert_id))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def resolve_alert(db: AsyncSession, alert_id: str) -> CRAlert:
        await db.execute(
            update(CRAlert).where(CRAlert.id == uuid.UUID(alert_id))
            .values(status=AlertStatus.RESOLVED)
        )
        await db.commit()
        result = await db.execute(
            select(CRAlert).where(CRAlert.id == uuid.UUID(alert_id))
        )
        return result.scalar_one_or_none()


# ── 7. Dashboard Stats ───────────────────────────────────────────────────────

class DashboardService:
    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        today_start = _now().replace(hour=0, minute=0, second=0, microsecond=0)

        received = (await db.execute(
            select(func.count()).select_from(CRReceipt)
            .where(CRReceipt.received_at >= today_start)
        )).scalar() or 0

        pending = (await db.execute(
            select(func.count()).select_from(CRReceipt)
            .where(CRReceipt.status == ReceiptStatus.RECEIVED)
        )).scalar() or 0

        accepted = (await db.execute(
            select(func.count()).select_from(CRReceipt)
            .where(CRReceipt.status.in_([ReceiptStatus.ACCEPTED, ReceiptStatus.ROUTED,
                                          ReceiptStatus.PROCESSING]))
        )).scalar() or 0

        rejected = (await db.execute(
            select(func.count()).select_from(CRReceipt)
            .where(CRReceipt.status == ReceiptStatus.REJECTED)
        )).scalar() or 0

        routed = (await db.execute(
            select(func.count()).select_from(CRReceipt)
            .where(CRReceipt.status == ReceiptStatus.ROUTED)
        )).scalar() or 0

        stored = (await db.execute(
            select(func.count()).select_from(CRStorage)
            .where(CRStorage.is_active == True)
        )).scalar() or 0

        alerts = (await db.execute(
            select(func.count()).select_from(CRAlert)
            .where(CRAlert.status == AlertStatus.ACTIVE)
        )).scalar() or 0

        # Department distribution
        dept_rows = (await db.execute(
            select(CRRouting.target_department, func.count())
            .group_by(CRRouting.target_department)
        )).all()
        dept_dist = {row[0]: row[1] for row in dept_rows}

        return {
            "received_today": received,
            "pending_verification": pending,
            "accepted": accepted,
            "rejected": rejected,
            "routed": routed,
            "stored": stored,
            "active_alerts": alerts,
            "department_distribution": dept_dist,
        }
