"""Lab module – Business logic for the Laboratory Information System."""
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.lab.models import (
    LabTest, LabOrder, LabSample, LabResult, LabValidation, LabProcessing,
    SampleStatus, LabOrderStatus, ResultFlag, ValidationStatus, ProcessingStatus,
)


class LabService:
    """Central service for all lab operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Test Catalog ─────────────────────────────────────────────────────

    async def create_test(self, **kwargs) -> LabTest:
        test = LabTest(**kwargs)
        self.db.add(test)
        await self.db.flush()
        return test

    async def list_tests(self, category: str | None = None, active_only: bool = True) -> list[LabTest]:
        stmt = select(LabTest)
        if active_only:
            stmt = stmt.where(LabTest.is_active == True)
        if category:
            stmt = stmt.where(LabTest.category == category)
        stmt = stmt.order_by(LabTest.category, LabTest.name)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_test_by_id(self, test_id: uuid.UUID) -> LabTest | None:
        return await self.db.get(LabTest, test_id)

    async def get_test_by_code(self, code: str) -> LabTest | None:
        stmt = select(LabTest).where(LabTest.code == code)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    # ── Lab Orders ───────────────────────────────────────────────────────

    async def create_lab_order(self, order_id: uuid.UUID, patient_id: uuid.UUID,
                                encounter_id: uuid.UUID, notes: str | None = None) -> LabOrder:
        lab_order = LabOrder(
            order_id=order_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            notes=notes,
        )
        self.db.add(lab_order)
        await self.db.flush()
        return lab_order

    async def get_lab_order(self, lab_order_id: uuid.UUID) -> LabOrder | None:
        stmt = select(LabOrder).options(selectinload(LabOrder.samples)).where(LabOrder.id == lab_order_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_lab_orders(self, status: str | None = None) -> list[LabOrder]:
        stmt = select(LabOrder).options(selectinload(LabOrder.samples))
        if status:
            stmt = stmt.where(LabOrder.status == status)
        stmt = stmt.order_by(LabOrder.ordered_at.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def update_lab_order_status(self, lab_order: LabOrder, new_status: str) -> LabOrder:
        lab_order.status = new_status
        if new_status == LabOrderStatus.COMPLETED:
            lab_order.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return lab_order

    # ── Samples ──────────────────────────────────────────────────────────

    def _generate_barcode(self) -> str:
        """Generate a unique sample barcode: LAB-YYYYMMDD-XXXX."""
        now = datetime.now(timezone.utc)
        short_id = uuid.uuid4().hex[:8].upper()
        return f"LAB-{now.strftime('%Y%m%d')}-{short_id}"

    async def collect_sample(self, lab_order_id: uuid.UUID, sample_type: str,
                              collected_by: uuid.UUID, notes: str | None = None) -> LabSample:
        sample = LabSample(
            lab_order_id=lab_order_id,
            sample_barcode=self._generate_barcode(),
            sample_type=sample_type,
            collected_by=collected_by,
            status=SampleStatus.COLLECTED,
            notes=notes,
        )
        self.db.add(sample)
        await self.db.flush()

        # Update lab order status
        lab_order = await self.get_lab_order(lab_order_id)
        if lab_order and lab_order.status == LabOrderStatus.PENDING:
            await self.update_lab_order_status(lab_order, LabOrderStatus.SAMPLE_COLLECTED)

        return sample

    async def get_sample_by_barcode(self, barcode: str) -> LabSample | None:
        stmt = (
            select(LabSample)
            .options(selectinload(LabSample.results), selectinload(LabSample.processing))
            .where(LabSample.sample_barcode == barcode)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_sample_by_id(self, sample_id: uuid.UUID) -> LabSample | None:
        stmt = (
            select(LabSample)
            .options(selectinload(LabSample.results), selectinload(LabSample.processing))
            .where(LabSample.id == sample_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def update_sample_status(self, sample: LabSample, new_status: str) -> LabSample:
        sample.status = new_status
        if new_status == SampleStatus.RECEIVED_IN_LAB:
            sample.received_at = datetime.now(timezone.utc)
        await self.db.flush()
        return sample

    async def list_samples(self, status: str | None = None) -> list[LabSample]:
        stmt = select(LabSample).options(selectinload(LabSample.results))
        if status:
            stmt = stmt.where(LabSample.status == status)
        stmt = stmt.order_by(LabSample.collection_time.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    # ── Processing ───────────────────────────────────────────────────────

    async def start_processing(self, sample_id: uuid.UUID, analyzer_name: str | None = None) -> LabProcessing:
        processing = LabProcessing(
            sample_id=sample_id,
            analyzer_name=analyzer_name,
            status=ProcessingStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(processing)
        await self.db.flush()

        # Update sample status
        sample = await self.get_sample_by_id(sample_id)
        if sample:
            await self.update_sample_status(sample, SampleStatus.PROCESSING)

        return processing

    async def complete_processing(self, processing_id: uuid.UUID) -> LabProcessing | None:
        proc = await self.db.get(LabProcessing, processing_id)
        if not proc:
            return None
        proc.status = ProcessingStatus.COMPLETED
        proc.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return proc

    # ── Results ──────────────────────────────────────────────────────────

    async def enter_result(self, sample_id: uuid.UUID, test_id: uuid.UUID,
                            order_id: uuid.UUID, patient_id: uuid.UUID,
                            value: str, entered_by: uuid.UUID,
                            numeric_value: float | None = None,
                            unit: str | None = None,
                            reference_range: str | None = None,
                            notes: str | None = None) -> LabResult:
        # Get test for reference ranges
        test = await self.get_test_by_id(test_id)

        # Calculate flag
        result_flag = ResultFlag.NORMAL
        is_abnormal = False
        is_critical = False

        if numeric_value is not None and test:
            if test.critical_high is not None and numeric_value >= test.critical_high:
                result_flag = ResultFlag.CRITICAL_HIGH
                is_abnormal = True
                is_critical = True
            elif test.critical_low is not None and numeric_value <= test.critical_low:
                result_flag = ResultFlag.CRITICAL_LOW
                is_abnormal = True
                is_critical = True
            elif test.normal_range_high is not None and numeric_value > test.normal_range_high:
                result_flag = ResultFlag.HIGH
                is_abnormal = True
            elif test.normal_range_low is not None and numeric_value < test.normal_range_low:
                result_flag = ResultFlag.LOW
                is_abnormal = True

        # Use test reference range if not provided
        if not reference_range and test and test.reference_range:
            reference_range = test.reference_range
        if not unit and test and test.unit:
            unit = test.unit

        result = LabResult(
            sample_id=sample_id,
            test_id=test_id,
            order_id=order_id,
            patient_id=patient_id,
            value=value,
            numeric_value=numeric_value,
            unit=unit,
            reference_range=reference_range,
            result_flag=result_flag,
            is_abnormal=is_abnormal,
            is_critical=is_critical,
            entered_by=entered_by,
            notes=notes,
        )
        self.db.add(result)
        await self.db.flush()

        # Auto-create pending validation
        validation = LabValidation(result_id=result.id)
        self.db.add(validation)
        await self.db.flush()

        return result

    async def get_result(self, result_id: uuid.UUID) -> LabResult | None:
        stmt = (
            select(LabResult)
            .options(selectinload(LabResult.validation))
            .where(LabResult.id == result_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_patient_results(self, patient_id: uuid.UUID) -> list[LabResult]:
        stmt = (
            select(LabResult)
            .options(selectinload(LabResult.validation))
            .where(LabResult.patient_id == patient_id)
            .order_by(LabResult.entered_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_results_for_order(self, order_id: uuid.UUID) -> list[LabResult]:
        stmt = (
            select(LabResult)
            .options(selectinload(LabResult.validation))
            .where(LabResult.order_id == order_id)
            .order_by(LabResult.entered_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_pending_validation(self) -> list[LabResult]:
        stmt = (
            select(LabResult)
            .join(LabValidation)
            .options(selectinload(LabResult.validation))
            .where(LabValidation.validation_status == ValidationStatus.PENDING)
            .order_by(LabResult.entered_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # ── Validation ───────────────────────────────────────────────────────

    async def validate_result(self, result_id: uuid.UUID, validated_by: uuid.UUID,
                               validation_status: str,
                               rejection_reason: str | None = None) -> LabValidation | None:
        result = await self.get_result(result_id)
        if not result or not result.validation:
            return None

        validation = result.validation
        validation.validated_by = validated_by
        validation.validated_at = datetime.now(timezone.utc)
        validation.validation_status = validation_status
        validation.rejection_reason = rejection_reason

        # Update result status
        if validation_status == ValidationStatus.VALIDATED:
            result.status = "FINAL"
        elif validation_status == ValidationStatus.REJECTED:
            result.status = "CORRECTED"

        await self.db.flush()
        return validation

    # ── Dashboard Stats ──────────────────────────────────────────────────

    async def get_dashboard_stats(self) -> dict:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # Pending samples
        pending_q = select(func.count()).select_from(LabSample).where(
            LabSample.status.in_([SampleStatus.COLLECTED, SampleStatus.IN_TRANSIT, SampleStatus.RECEIVED_IN_LAB])
        )
        pending = (await self.db.execute(pending_q)).scalar() or 0

        # Processing
        processing_q = select(func.count()).select_from(LabSample).where(
            LabSample.status == SampleStatus.PROCESSING
        )
        processing = (await self.db.execute(processing_q)).scalar() or 0

        # Completed today
        completed_q = select(func.count()).select_from(LabResult).where(
            LabResult.entered_at >= today_start
        )
        completed = (await self.db.execute(completed_q)).scalar() or 0

        # Critical results
        critical_q = select(func.count()).select_from(LabResult).where(
            LabResult.is_critical == True
        )
        critical = (await self.db.execute(critical_q)).scalar() or 0

        # Pending validation
        pv_q = select(func.count()).select_from(LabValidation).where(
            LabValidation.validation_status == ValidationStatus.PENDING
        )
        pv = (await self.db.execute(pv_q)).scalar() or 0

        # Total tests
        tests_q = select(func.count()).select_from(LabTest).where(LabTest.is_active == True)
        tests = (await self.db.execute(tests_q)).scalar() or 0

        return {
            "pending_samples": pending,
            "processing_samples": processing,
            "completed_today": completed,
            "critical_results": critical,
            "pending_validation": pv,
            "total_tests_catalog": tests,
        }
