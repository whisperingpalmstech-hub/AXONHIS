"""
LIS Phlebotomy & Sample Collection Engine – Business Logic Services
"""
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    PhlebotomyWorklist, SampleCollection, ConsentDocument,
    RepeatSampleSchedule, SampleTransport, PhlebotomyAudit,
    SampleCollectionStatus, TransportStatus,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _gen_sample_id() -> str:
    ts = _now().strftime("%Y%m%d%H%M%S")
    return f"SMP-{ts}-{uuid.uuid4().hex[:6].upper()}"


def _gen_batch_id() -> str:
    ts = _now().strftime("%Y%m%d%H%M%S")
    return f"TRN-{ts}-{uuid.uuid4().hex[:4].upper()}"


# ── 1. Worklist Service ──────────────────────────────────────────────────────

class WorklistService:
    """Manage phlebotomy worklists."""

    @staticmethod
    async def get_pending_worklist(
        db: AsyncSession,
        location: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        collector: str | None = None,
    ) -> list[PhlebotomyWorklist]:
        stmt = select(PhlebotomyWorklist)
        filters = []
        if location:
            filters.append(PhlebotomyWorklist.collection_location == location)
        if priority:
            filters.append(PhlebotomyWorklist.priority == priority)
        if status:
            filters.append(PhlebotomyWorklist.status == status)
        else:
            filters.append(
                PhlebotomyWorklist.status.in_([
                    SampleCollectionStatus.PENDING_COLLECTION,
                    SampleCollectionStatus.COLLECTED,
                ])
            )
        if collector:
            filters.append(PhlebotomyWorklist.assigned_collector == collector)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(
            PhlebotomyWorklist.priority.desc(),
            PhlebotomyWorklist.created_at.asc(),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_worklist_item(db: AsyncSession, wl_id: uuid.UUID) -> PhlebotomyWorklist | None:
        result = await db.execute(
            select(PhlebotomyWorklist).where(PhlebotomyWorklist.id == wl_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def assign_collector(db: AsyncSession, wl_id: uuid.UUID, collector: str) -> PhlebotomyWorklist:
        await db.execute(
            update(PhlebotomyWorklist)
            .where(PhlebotomyWorklist.id == wl_id)
            .values(assigned_collector=collector)
        )
        await db.commit()
        return await WorklistService.get_worklist_item(db, wl_id)


# ── 2. Patient Verification Service ──────────────────────────────────────────

class PatientVerificationService:
    """Verify patient identity before sample collection."""

    @staticmethod
    async def verify_patient(db: AsyncSession, wl_id: uuid.UUID, method: str, verified_by: str) -> dict:
        item = await WorklistService.get_worklist_item(db, wl_id)
        if not item:
            raise ValueError("Worklist item not found")

        # Log audit entry
        await AuditService.log(db, "WORKLIST", item.id, "PATIENT_VERIFIED", verified_by, {
            "method": method,
            "patient_id": str(item.patient_id),
            "patient_uhid": item.patient_uhid,
        })

        return {
            "verified": True,
            "patient_name": item.patient_name or "Unknown",
            "patient_uhid": item.patient_uhid,
            "date_of_birth": None,
            "gender": None,
            "photo_url": None,
        }


# ── 3. Sample Collection Service ─────────────────────────────────────────────

class SampleCollectionService:
    """Handle sample collection workflow."""

    @staticmethod
    async def collect_sample(
        db: AsyncSession,
        worklist_id: str,
        collector_name: str,
        collector_id: str | None = None,
        container_type: str = "PLAIN_TUBE",
        collection_location: str = "OPD",
        identity_verified: bool = True,
        identity_method: str = "UHID",
        notes: str | None = None,
        quantity_ml: float | None = None,
    ) -> SampleCollection:
        wl_id = uuid.UUID(worklist_id)
        item = await WorklistService.get_worklist_item(db, wl_id)
        if not item:
            raise ValueError("Worklist item not found")

        # Consent check
        if item.consent_required and not item.consent_uploaded:
            raise ValueError("Consent document required but not uploaded. Upload consent before collecting sample.")

        sample_id = _gen_sample_id()
        barcode = item.barcode or f"BC-{uuid.uuid4().hex[:8].upper()}"

        sample = SampleCollection(
            worklist_id=wl_id,
            sample_id=sample_id,
            order_id=item.order_id,
            patient_id=item.patient_id,
            patient_uhid=item.patient_uhid,
            barcode=barcode,
            test_code=item.test_code,
            test_name=item.test_name,
            sample_type=item.sample_type,
            container_type=container_type,
            collection_location=collection_location,
            collector_name=collector_name,
            collector_id=uuid.UUID(collector_id) if collector_id else None,
            identity_verified=identity_verified,
            identity_method=identity_method,
            notes=notes,
            quantity_ml=quantity_ml,
            status=SampleCollectionStatus.COLLECTED,
            status_history=[{
                "status": SampleCollectionStatus.COLLECTED,
                "at": _now().isoformat(),
                "by": collector_name,
            }],
        )
        db.add(sample)

        # Update worklist status
        await db.execute(
            update(PhlebotomyWorklist)
            .where(PhlebotomyWorklist.id == wl_id)
            .values(
                status=SampleCollectionStatus.COLLECTED,
                barcode=barcode,
            )
        )

        await db.flush()

        # Audit
        await AuditService.log(db, "SAMPLE", sample.id, "SAMPLE_COLLECTED", collector_name, {
            "sample_id": sample_id,
            "test_code": item.test_code,
            "barcode": barcode,
            "container": container_type,
            "location": collection_location,
        })

        await db.commit()
        await db.refresh(sample)
        return sample

    @staticmethod
    async def get_sample(db: AsyncSession, sample_id: str) -> SampleCollection | None:
        result = await db.execute(
            select(SampleCollection).where(SampleCollection.sample_id == sample_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(
        db: AsyncSession, sample_id: str, new_status: str, updated_by: str | None = None, notes: str | None = None
    ) -> SampleCollection:
        sample = await SampleCollectionService.get_sample(db, sample_id)
        if not sample:
            raise ValueError("Sample not found")

        history = sample.status_history or []
        history.append({
            "status": new_status,
            "at": _now().isoformat(),
            "by": updated_by or "system",
            "notes": notes,
        })

        await db.execute(
            update(SampleCollection)
            .where(SampleCollection.sample_id == sample_id)
            .values(status=new_status, status_history=history)
        )

        # Also update worklist
        await db.execute(
            update(PhlebotomyWorklist)
            .where(PhlebotomyWorklist.id == sample.worklist_id)
            .values(status=new_status)
        )

        await AuditService.log(db, "SAMPLE", sample.id, f"STATUS_{new_status}", updated_by or "system", {
            "sample_id": sample_id,
            "new_status": new_status,
        })

        await db.commit()
        await db.refresh(sample)
        return sample

    @staticmethod
    async def list_collected(db: AsyncSession, patient_id: str | None = None) -> list[SampleCollection]:
        stmt = select(SampleCollection)
        if patient_id:
            stmt = stmt.where(SampleCollection.patient_id == uuid.UUID(patient_id))
        stmt = stmt.order_by(SampleCollection.collected_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_barcode_label(db: AsyncSession, sample_id: str) -> dict:
        sample = await SampleCollectionService.get_sample(db, sample_id)
        if not sample:
            raise ValueError("Sample not found")
        # Build worklist reference for order_number
        wl = await WorklistService.get_worklist_item(db, sample.worklist_id)
        return {
            "barcode": sample.barcode,
            "sample_id": sample.sample_id,
            "patient_uhid": sample.patient_uhid,
            "order_number": wl.order_number if wl else "N/A",
            "test_name": sample.test_name,
            "sample_type": sample.sample_type,
            "collected_at": sample.collected_at.isoformat() if sample.collected_at else "",
        }


# ── 4. Consent Service ───────────────────────────────────────────────────────

class ConsentService:
    """Manage consent document uploads for tests requiring consent."""

    @staticmethod
    async def upload_consent(
        db: AsyncSession,
        worklist_id: str,
        file_name: str,
        file_url: str,
        file_format: str = "PDF",
        uploaded_by: str | None = None,
    ) -> ConsentDocument:
        wl_id = uuid.UUID(worklist_id)
        item = await WorklistService.get_worklist_item(db, wl_id)
        if not item:
            raise ValueError("Worklist item not found")

        doc = ConsentDocument(
            worklist_id=wl_id,
            patient_id=item.patient_id,
            test_code=item.test_code,
            file_name=file_name,
            file_url=file_url,
            file_format=file_format.upper(),
            uploaded_by=uploaded_by,
            verified=True,
        )
        db.add(doc)

        # Mark consent as uploaded on worklist
        await db.execute(
            update(PhlebotomyWorklist)
            .where(PhlebotomyWorklist.id == wl_id)
            .values(consent_uploaded=True)
        )

        await AuditService.log(db, "CONSENT", doc.id, "CONSENT_UPLOADED", uploaded_by, {
            "test_code": item.test_code,
            "file_name": file_name,
        })

        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def get_consent_for_worklist(db: AsyncSession, worklist_id: str) -> list[ConsentDocument]:
        result = await db.execute(
            select(ConsentDocument).where(ConsentDocument.worklist_id == uuid.UUID(worklist_id))
        )
        return list(result.scalars().all())


# ── 5. Repeat Schedule Service ────────────────────────────────────────────────

class RepeatScheduleService:
    """Manage repeat/serial sample collection schedules."""

    @staticmethod
    async def create_schedule(
        db: AsyncSession,
        order_id: str,
        patient_id: str,
        test_code: str,
        test_name: str,
        total_samples: int = 3,
        interval_minutes: int = 30,
        schedule_config: dict | None = None,
    ) -> RepeatSampleSchedule:
        sch = RepeatSampleSchedule(
            order_id=uuid.UUID(order_id),
            patient_id=uuid.UUID(patient_id),
            test_code=test_code,
            test_name=test_name,
            total_samples=total_samples,
            interval_minutes=interval_minutes,
            schedule_config=schedule_config or {
                "samples": [
                    {"sample_number": i + 1, "minutes_offset": i * interval_minutes}
                    for i in range(total_samples)
                ]
            },
            started_at=_now(),
        )
        db.add(sch)
        await db.commit()
        await db.refresh(sch)
        return sch

    @staticmethod
    async def get_schedule(db: AsyncSession, schedule_id: str) -> RepeatSampleSchedule | None:
        result = await db.execute(
            select(RepeatSampleSchedule).where(RepeatSampleSchedule.id == uuid.UUID(schedule_id))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_sample_collected(db: AsyncSession, schedule_id: str) -> RepeatSampleSchedule:
        sch = await RepeatScheduleService.get_schedule(db, schedule_id)
        if not sch:
            raise ValueError("Schedule not found")

        new_count = sch.collected_count + 1
        is_done = new_count >= sch.total_samples

        await db.execute(
            update(RepeatSampleSchedule)
            .where(RepeatSampleSchedule.id == sch.id)
            .values(collected_count=new_count, is_complete=is_done)
        )
        await db.commit()
        await db.refresh(sch)
        return sch

    @staticmethod
    async def list_active(db: AsyncSession, patient_id: str | None = None) -> list[RepeatSampleSchedule]:
        stmt = select(RepeatSampleSchedule).where(RepeatSampleSchedule.is_complete == False)
        if patient_id:
            stmt = stmt.where(RepeatSampleSchedule.patient_id == uuid.UUID(patient_id))
        result = await db.execute(stmt)
        return list(result.scalars().all())


# ── 6. Transport Service ─────────────────────────────────────────────────────

class TransportService:
    """Track sample transport batches to Central Receiving."""

    @staticmethod
    async def create_batch(
        db: AsyncSession,
        sample_ids: list[str],
        transport_personnel: str,
        transport_method: str = "MANUAL",
        notes: str | None = None,
    ) -> SampleTransport:
        batch = SampleTransport(
            batch_id=_gen_batch_id(),
            sample_ids=sample_ids,
            sample_count=len(sample_ids),
            transport_personnel=transport_personnel,
            transport_method=transport_method,
            notes=notes,
            status=TransportStatus.DISPATCHED,
        )
        db.add(batch)

        # Update samples to IN_TRANSIT
        for sid in sample_ids:
            await SampleCollectionService.update_status(db, sid, SampleCollectionStatus.IN_TRANSIT, transport_personnel)

        await AuditService.log(db, "TRANSPORT", batch.id, "BATCH_DISPATCHED", transport_personnel, {
            "batch_id": batch.batch_id,
            "sample_count": len(sample_ids),
        })

        await db.commit()
        await db.refresh(batch)
        return batch

    @staticmethod
    async def receive_batch(db: AsyncSession, batch_id: str, received_by: str) -> SampleTransport:
        result = await db.execute(
            select(SampleTransport).where(SampleTransport.batch_id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if not batch:
            raise ValueError("Transport batch not found")

        await db.execute(
            update(SampleTransport)
            .where(SampleTransport.batch_id == batch_id)
            .values(
                status=TransportStatus.RECEIVED,
                received_time=_now(),
                received_by=received_by,
            )
        )

        # Update samples to RECEIVED_IN_LAB
        for sid in (batch.sample_ids or []):
            try:
                await SampleCollectionService.update_status(db, sid, SampleCollectionStatus.RECEIVED_IN_LAB, received_by)
            except Exception:
                pass

        await AuditService.log(db, "TRANSPORT", batch.id, "BATCH_RECEIVED", received_by, {
            "batch_id": batch_id,
        })

        await db.commit()
        await db.refresh(batch)
        return batch

    @staticmethod
    async def list_batches(db: AsyncSession, status: str | None = None) -> list[SampleTransport]:
        stmt = select(SampleTransport)
        if status:
            stmt = stmt.where(SampleTransport.status == status)
        stmt = stmt.order_by(SampleTransport.dispatch_time.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())


# ── 7. Audit Service ─────────────────────────────────────────────────────────

class AuditService:
    """Immutable audit trail for phlebotomy actions."""

    @staticmethod
    async def log(
        db: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        performed_by: str | None = None,
        details: dict | None = None,
    ) -> PhlebotomyAudit:
        entry = PhlebotomyAudit(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            performed_by=performed_by,
            details=details,
        )
        db.add(entry)
        return entry

    @staticmethod
    async def get_audit_trail(
        db: AsyncSession, entity_type: str | None = None, entity_id: str | None = None, limit: int = 50
    ) -> list[PhlebotomyAudit]:
        stmt = select(PhlebotomyAudit)
        if entity_type:
            stmt = stmt.where(PhlebotomyAudit.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(PhlebotomyAudit.entity_id == uuid.UUID(entity_id))
        stmt = stmt.order_by(PhlebotomyAudit.performed_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
