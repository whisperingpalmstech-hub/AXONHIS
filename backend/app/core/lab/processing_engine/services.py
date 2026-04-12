"""
LIS Laboratory Processing & Result Entry Engine – Business Logic Services
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ProcessingWorklist, ResultEntry, ResultFlag, DeltaCheck,
    QCResult, ResultComment, ProcessingAudit,
    ProcessingStatus, ResultType, FlagType, ResultSource, QCStatus,
    REFERENCE_RANGES, DELTA_THRESHOLDS,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditService:
    @staticmethod
    async def log(db: AsyncSession, entity_type: str, entity_id: uuid.UUID,
                  action: str, performed_by: str | None = None, details: dict | None = None):
        entry = ProcessingAudit(entity_type=entity_type, entity_id=entity_id,
                                action=action, performed_by=performed_by, details=details)
        db.add(entry)
        return entry

    @staticmethod
    async def get_trail(db: AsyncSession, entity_type: str | None = None,
                        entity_id: str | None = None, limit: int = 50):
        stmt = select(ProcessingAudit)
        if entity_type:
            stmt = stmt.where(ProcessingAudit.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(ProcessingAudit.entity_id == uuid.UUID(entity_id))
        stmt = stmt.order_by(ProcessingAudit.performed_at.desc()).limit(limit)
        return list((await db.execute(stmt)).scalars().all())


# ── 1. Worklist Service ──────────────────────────────────────────────────────

class WorklistService:
    @staticmethod
    async def list_worklist(db: AsyncSession, department: str | None = None,
                            status: str | None = None, priority: str | None = None):
        stmt = select(ProcessingWorklist)
        filters = []
        if department:
            filters.append(ProcessingWorklist.department == department)
        if status:
            filters.append(ProcessingWorklist.status == status)
        if priority:
            filters.append(ProcessingWorklist.priority == priority)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(
            ProcessingWorklist.priority.desc(),
            ProcessingWorklist.created_at.asc()
        )
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def get_item(db: AsyncSession, wl_id: str):
        return (await db.execute(
            select(ProcessingWorklist).where(ProcessingWorklist.id == uuid.UUID(wl_id))
        )).scalar_one_or_none()

    @staticmethod
    async def assign_technician(db: AsyncSession, wl_id: str, technician: str):
        await db.execute(
            update(ProcessingWorklist).where(ProcessingWorklist.id == uuid.UUID(wl_id))
            .values(assigned_technician=technician)
        )
        await db.commit()
        return await WorklistService.get_item(db, wl_id)

    @staticmethod
    async def start_processing(db: AsyncSession, wl_id: str, technician: str):
        await db.execute(
            update(ProcessingWorklist).where(ProcessingWorklist.id == uuid.UUID(wl_id))
            .values(status=ProcessingStatus.IN_PROGRESS,
                    assigned_technician=technician,
                    started_at=_now())
        )
        await AuditService.log(db, "WORKLIST", uuid.UUID(wl_id),
                                "PROCESSING_STARTED", technician)
        await db.commit()
        return await WorklistService.get_item(db, wl_id)

    @staticmethod
    async def create_from_routing(db: AsyncSession, receipt_id: str, sample_id: str,
                                   barcode: str, order_id: str, order_number: str,
                                   patient_id: str, patient_name: str | None,
                                   patient_uhid: str | None, test_code: str,
                                   test_name: str, sample_type: str,
                                   department: str, priority: str):
        """Create a processing worklist item when sample arrives at department."""
        wl = ProcessingWorklist(
            cr_receipt_id=uuid.UUID(receipt_id) if receipt_id else None,
            sample_id=sample_id, barcode=barcode,
            order_id=uuid.UUID(order_id), order_number=order_number,
            patient_id=uuid.UUID(patient_id),
            patient_name=patient_name, patient_uhid=patient_uhid,
            test_code=test_code, test_name=test_name,
            sample_type=sample_type, department=department,
            priority=priority, receipt_time=_now(),
        )
        db.add(wl)
        await db.commit()
        await db.refresh(wl)
        return wl


# ── 2. Result Entry Service ──────────────────────────────────────────────────

class ResultService:
    @staticmethod
    async def enter_result(db: AsyncSession, worklist_id: str,
                           result_type: str, result_value: str | None,
                           result_numeric: float | None, result_unit: str | None,
                           result_source: str, entered_by: str,
                           analyzer_id: str | None = None,
                           comments: str | None = None) -> ResultEntry:
        wl = await WorklistService.get_item(db, worklist_id)
        if not wl:
            raise ValueError("Worklist item not found")

        # Get reference ranges
        ref = REFERENCE_RANGES.get(wl.test_code, {})
        ref_low = ref.get("low")
        ref_high = ref.get("high")
        unit = result_unit or ref.get("unit", "")

        result = ResultEntry(
            worklist_id=uuid.UUID(worklist_id),
            sample_id=wl.sample_id, order_id=wl.order_id,
            patient_id=wl.patient_id,
            test_code=wl.test_code, test_name=wl.test_name,
            result_type=result_type,
            result_value=result_value or (str(result_numeric) if result_numeric is not None else None),
            result_numeric=result_numeric,
            result_unit=unit,
            reference_low=ref_low, reference_high=ref_high,
            result_source=result_source,
            analyzer_id=analyzer_id,
            entered_by=entered_by,
            status=ProcessingStatus.RESULT_ENTERED,
        )
        db.add(result)
        await db.flush()

        # Flag abnormal results
        if result_numeric is not None and ref:
            await ResultService._check_flags(db, result, ref)

        # Delta check
        if result_numeric is not None:
            await ResultService._delta_check(db, result)

        # Add comment if provided
        if comments:
            db.add(ResultComment(
                result_id=result.id, comment_type="REMARK",
                comment_text=comments, added_by=entered_by,
            ))

        # Update worklist status
        await db.execute(
            update(ProcessingWorklist).where(ProcessingWorklist.id == wl.id)
            .values(status=ProcessingStatus.RESULT_ENTERED, completed_at=_now())
        )

        await AuditService.log(db, "RESULT", result.id, "RESULT_ENTERED", entered_by, {
            "test_code": wl.test_code, "value": result_value or str(result_numeric),
            "source": result_source,
        })

        await db.commit()
        await db.refresh(result)
        return result

    @staticmethod
    async def _check_flags(db: AsyncSession, result: ResultEntry, ref: dict):
        value = result.result_numeric
        if value is None:
            return

        flag_type = FlagType.NORMAL
        is_critical = False
        message = None

        crit_low = ref.get("crit_low")
        crit_high = ref.get("crit_high")
        low = ref.get("low")
        high = ref.get("high")

        if crit_low is not None and value <= crit_low:
            flag_type = FlagType.CRITICAL_LOW
            is_critical = True
            message = f"CRITICAL LOW: {value} (critical threshold: {crit_low})"
        elif crit_high is not None and value >= crit_high:
            flag_type = FlagType.CRITICAL_HIGH
            is_critical = True
            message = f"CRITICAL HIGH: {value} (critical threshold: {crit_high})"
        elif low is not None and value < low:
            flag_type = FlagType.LOW
            message = f"Low: {value} (reference: {low}-{high})"
        elif high is not None and value > high:
            flag_type = FlagType.HIGH
            message = f"High: {value} (reference: {low}-{high})"

        if flag_type != FlagType.NORMAL:
            flag = ResultFlag(
                result_id=result.id, flag_type=flag_type,
                reference_low=low, reference_high=high,
                result_value=value, is_critical=is_critical,
                message=message,
            )
            db.add(flag)

    @staticmethod
    async def _delta_check(db: AsyncSession, result: ResultEntry):
        if result.result_numeric is None:
            return
        threshold = DELTA_THRESHOLDS.get(result.test_code)
        if threshold is None:
            return

        # Find previous result for same patient + test
        prev = (await db.execute(
            select(ResultEntry)
            .where(and_(
                ResultEntry.patient_id == result.patient_id,
                ResultEntry.test_code == result.test_code,
                ResultEntry.id != result.id,
            ))
            .order_by(ResultEntry.entered_at.desc())
            .limit(1)
        )).scalar_one_or_none()

        if not prev or prev.result_numeric is None:
            return

        delta_abs = abs(result.result_numeric - prev.result_numeric)
        delta_pct = (delta_abs / abs(prev.result_numeric) * 100) if prev.result_numeric != 0 else 0
        is_sig = delta_pct >= threshold

        dc = DeltaCheck(
            result_id=result.id, patient_id=result.patient_id,
            test_code=result.test_code,
            current_value=result.result_numeric,
            previous_value=prev.result_numeric,
            previous_date=prev.entered_at,
            delta_absolute=delta_abs, delta_percent=round(delta_pct, 1),
            threshold_percent=threshold, is_significant=is_sig,
            message=f"Delta {delta_pct:.1f}% ({'SIGNIFICANT' if is_sig else 'within limits'})" if is_sig else None,
        )
        db.add(dc)

    @staticmethod
    async def batch_enter(db: AsyncSession, items: list[dict],
                          result_source: str, entered_by: str) -> list[ResultEntry]:
        results = []
        for item in items:
            r = await ResultService.enter_result(
                db, item["worklist_id"], item.get("result_type", "NUMERIC"),
                item.get("result_value"), item.get("result_numeric"),
                item.get("result_unit"), result_source, entered_by,
                comments=item.get("comments"),
            )
            results.append(r)
        return results

    @staticmethod
    async def get_result(db: AsyncSession, result_id: str):
        return (await db.execute(
            select(ResultEntry).where(ResultEntry.id == uuid.UUID(result_id))
        )).scalar_one_or_none()

    @staticmethod
    async def get_result_with_details(db: AsyncSession, result_id: str) -> dict:
        result = await ResultService.get_result(db, result_id)
        if not result:
            return {}

        flags = list((await db.execute(
            select(ResultFlag).where(ResultFlag.result_id == result.id)
        )).scalars().all())

        delta = (await db.execute(
            select(DeltaCheck).where(DeltaCheck.result_id == result.id)
        )).scalar_one_or_none()

        comments = list((await db.execute(
            select(ResultComment).where(ResultComment.result_id == result.id)
            .order_by(ResultComment.added_at.asc())
        )).scalars().all())

        return {"result": result, "flags": flags, "delta": delta, "comments": comments}

    @staticmethod
    async def list_results(db: AsyncSession, patient_id: str | None = None,
                           status: str | None = None):
        stmt = select(ResultEntry)
        if patient_id:
            stmt = stmt.where(ResultEntry.patient_id == uuid.UUID(patient_id))
        if status:
            stmt = stmt.where(ResultEntry.status == status)
        stmt = stmt.order_by(ResultEntry.entered_at.desc())
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def review_result(db: AsyncSession, result_id: str,
                            reviewed_by: str, remarks: str | None = None):
        await db.execute(
            update(ResultEntry).where(ResultEntry.id == uuid.UUID(result_id))
            .values(is_reviewed=True, reviewed_by=reviewed_by,
                    reviewed_at=_now(),
                    status=ProcessingStatus.AWAITING_VALIDATION)
        )
        # Update worklist
        result = await ResultService.get_result(db, result_id)
        if result:
            await db.execute(
                update(ProcessingWorklist).where(ProcessingWorklist.id == result.worklist_id)
                .values(status=ProcessingStatus.AWAITING_VALIDATION)
            )
        if remarks:
            db.add(ResultComment(
                result_id=uuid.UUID(result_id), comment_type="REVIEW",
                comment_text=remarks, added_by=reviewed_by,
            ))
        await AuditService.log(db, "RESULT", uuid.UUID(result_id),
                                "RESULT_REVIEWED", reviewed_by)
        await db.commit()
        return await ResultService.get_result(db, result_id)

    @staticmethod
    async def validate_result(db: AsyncSession, result_id: str,
                              validated_by: str, remarks: str | None = None):
        """Validate a reviewed result and prepare for release."""
        result = await ResultService.get_result(db, result_id)
        if not result:
            raise ValueError("Result not found")

        # Check if QC has passed for the department
        qc_blocked = await QCService.check_qc_block(db, result.test_code)
        if qc_blocked:
            raise ValueError("QC has failed for this test. Cannot validate until QC passes.")

        await db.execute(
            update(ResultEntry).where(ResultEntry.id == uuid.UUID(result_id))
            .values(status=ProcessingStatus.VALIDATED)
        )
        await db.execute(
            update(ProcessingWorklist).where(ProcessingWorklist.id == result.worklist_id)
            .values(status=ProcessingStatus.VALIDATED)
        )
        if remarks:
            db.add(ResultComment(
                result_id=uuid.UUID(result_id), comment_type="VALIDATION",
                comment_text=remarks, added_by=validated_by,
            ))
        await AuditService.log(db, "RESULT", uuid.UUID(result_id),
                                "RESULT_VALIDATED", validated_by)
        await db.commit()
        return await ResultService.get_result(db, result_id)

    @staticmethod
    async def release_result(db: AsyncSession, result_id: str,
                             released_by: str, remarks: str | None = None):
        """Release a validated result to Doctor Desk / EMR / EHR."""
        result = await ResultService.get_result(db, result_id)
        if not result:
            raise ValueError("Result not found")
        if result.status != ProcessingStatus.VALIDATED:
            raise ValueError("Result must be validated before release")

        await db.execute(
            update(ResultEntry).where(ResultEntry.id == uuid.UUID(result_id))
            .values(status=ProcessingStatus.RELEASED)
        )
        await db.execute(
            update(ProcessingWorklist).where(ProcessingWorklist.id == result.worklist_id)
            .values(status=ProcessingStatus.RELEASED)
        )
        if remarks:
            db.add(ResultComment(
                result_id=uuid.UUID(result_id), comment_type="RELEASE",
                comment_text=remarks, added_by=released_by,
            ))
        await AuditService.log(db, "RESULT", uuid.UUID(result_id),
                                "RESULT_RELEASED", released_by, {
                                    "released_to": "EMR/EHR",
                                })
        await db.commit()
        return await ResultService.get_result(db, result_id)

    @staticmethod
    async def reject_result(db: AsyncSession, result_id: str,
                            rejected_by: str, reason: str):
        """Reject a result and send back for re-processing."""
        result = await ResultService.get_result(db, result_id)
        if not result:
            raise ValueError("Result not found")

        await db.execute(
            update(ResultEntry).where(ResultEntry.id == uuid.UUID(result_id))
            .values(status=ProcessingStatus.REJECTED)
        )
        await db.execute(
            update(ProcessingWorklist).where(ProcessingWorklist.id == result.worklist_id)
            .values(status=ProcessingStatus.PENDING)
        )
        db.add(ResultComment(
            result_id=uuid.UUID(result_id), comment_type="REJECTION",
            comment_text=reason, added_by=rejected_by,
        ))
        await AuditService.log(db, "RESULT", uuid.UUID(result_id),
                                "RESULT_REJECTED", rejected_by, {
                                    "reason": reason,
                                })
        await db.commit()
        return await ResultService.get_result(db, result_id)


# ── 3. QC Service ────────────────────────────────────────────────────────────

class QCService:
    @staticmethod
    async def record_qc(db: AsyncSession, data: dict) -> QCResult:
        expected = data["expected_value"]
        sd = data.get("expected_sd", 0)
        actual = data["actual_value"]

        # Determine pass/fail (within 2 SD)
        if sd > 0:
            if abs(actual - expected) <= 2 * sd:
                status = QCStatus.PASS
            elif abs(actual - expected) <= 3 * sd:
                status = QCStatus.WARNING
            else:
                status = QCStatus.FAIL
        else:
            status = QCStatus.PASS if actual == expected else QCStatus.WARNING

        qc = QCResult(
            department=data["department"],
            test_code=data["test_code"], test_name=data["test_name"],
            qc_lot_number=data["qc_lot_number"],
            qc_level=data.get("qc_level", "NORMAL"),
            expected_value=expected, expected_sd=sd,
            actual_value=actual, status=status,
            analyzer_id=data.get("analyzer_id"),
            performed_by=data["performed_by"],
            remarks=data.get("remarks"),
        )
        db.add(qc)

        await AuditService.log(db, "QC", qc.id, f"QC_{status}",
                                data["performed_by"], {
            "test_code": data["test_code"], "status": status,
        })

        await db.commit()
        await db.refresh(qc)
        return qc

    @staticmethod
    async def list_qc(db: AsyncSession, department: str | None = None,
                      status: str | None = None):
        stmt = select(QCResult)
        if department:
            stmt = stmt.where(QCResult.department == department)
        if status:
            stmt = stmt.where(QCResult.status == status)
        stmt = stmt.order_by(QCResult.performed_at.desc())
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def check_qc_block(db: AsyncSession, test_code: str) -> bool:
        """Check if QC failure blocks result release for a test code."""
        # Get the most recent QC result for this test code
        latest_qc = (await db.execute(
            select(QCResult)
            .where(QCResult.test_code == test_code)
            .order_by(QCResult.performed_at.desc())
            .limit(1)
        )).scalar_one_or_none()
        if latest_qc and latest_qc.status == QCStatus.FAIL:
            return True
        return False


# ── 4. Comment Service ───────────────────────────────────────────────────────

# ── Configurable Comment Libraries per Department ─────────────────────────────

COMMENT_LIBRARIES: dict[str, list[str]] = {
    "BIOCHEMISTRY": [
        "Sample hemolyzed", "Sample lipemic", "Sample icteric",
        "Result repeated for confirmation", "Insufficient sample volume",
        "Dilution factor applied", "Reagent lot changed during run",
    ],
    "HEMATOLOGY": [
        "Clotted sample", "Platelet clumps noted",
        "Manual differential performed", "Slide review required",
        "Reticulocyte count added", "RBC morphology abnormal",
    ],
    "SEROLOGY": [
        "Repeat testing recommended", "Confirmatory test ordered",
        "Borderline result", "Previous negative result on file",
        "Cross-reactivity possible",
    ],
    "MICROBIOLOGY": [
        "Culture in progress", "Gram stain performed",
        "Sensitivity testing pending", "No growth after 48 hours",
        "Contamination suspected", "Antibiotic sensitivity attached",
    ],
    "CLINICAL_PATHOLOGY": [
        "Sample recollection advised", "Microscopy performed",
        "Crystals observed", "Casts identified",
    ],
    "HISTOPATHOLOGY": [
        "Tissue processing in progress", "Additional sections cut",
        "Special stain ordered", "IHC panel requested",
        "Second opinion recommended",
    ],
}


class CommentService:
    @staticmethod
    async def add_comment(db: AsyncSession, result_id: str,
                          comment_type: str, text: str, added_by: str):
        c = ResultComment(
            result_id=uuid.UUID(result_id), comment_type=comment_type,
            comment_text=text, added_by=added_by,
        )
        db.add(c)
        await AuditService.log(db, "COMMENT", c.id, "COMMENT_ADDED", added_by)
        await db.commit()
        await db.refresh(c)
        return c

    @staticmethod
    async def get_comments(db: AsyncSession, result_id: str):
        return list((await db.execute(
            select(ResultComment).where(ResultComment.result_id == uuid.UUID(result_id))
            .order_by(ResultComment.added_at.asc())
        )).scalars().all())

    @staticmethod
    def get_comment_library(department: str) -> list[str]:
        """Return configurable comment templates for a department."""
        return COMMENT_LIBRARIES.get(department, [])


# ── 5. Dashboard Stats ───────────────────────────────────────────────────────

class StatsService:
    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        pending = (await db.execute(
            select(func.count()).select_from(ProcessingWorklist)
            .where(ProcessingWorklist.status == ProcessingStatus.PENDING)
        )).scalar() or 0

        in_prog = (await db.execute(
            select(func.count()).select_from(ProcessingWorklist)
            .where(ProcessingWorklist.status == ProcessingStatus.IN_PROGRESS)
        )).scalar() or 0

        entered = (await db.execute(
            select(func.count()).select_from(ProcessingWorklist)
            .where(ProcessingWorklist.status == ProcessingStatus.RESULT_ENTERED)
        )).scalar() or 0

        awaiting = (await db.execute(
            select(func.count()).select_from(ProcessingWorklist)
            .where(ProcessingWorklist.status == ProcessingStatus.AWAITING_VALIDATION)
        )).scalar() or 0

        critical = (await db.execute(
            select(func.count()).select_from(ResultFlag)
            .where(ResultFlag.is_critical == True)
        )).scalar() or 0

        deltas = (await db.execute(
            select(func.count()).select_from(DeltaCheck)
            .where(DeltaCheck.is_significant == True)
        )).scalar() or 0

        qc_fail = (await db.execute(
            select(func.count()).select_from(QCResult)
            .where(QCResult.status == QCStatus.FAIL)
        )).scalar() or 0

        dept_rows = (await db.execute(
            select(ProcessingWorklist.department, func.count())
            .where(ProcessingWorklist.status.in_([
                ProcessingStatus.PENDING, ProcessingStatus.IN_PROGRESS
            ]))
            .group_by(ProcessingWorklist.department)
        )).all()
        dept_counts = {r[0]: r[1] for r in dept_rows}

        return {
            "total_pending": pending, "in_progress": in_prog,
            "results_entered": entered, "awaiting_validation": awaiting,
            "critical_flags": critical, "delta_alerts": deltas,
            "qc_failures": qc_fail, "department_counts": dept_counts,
        }
