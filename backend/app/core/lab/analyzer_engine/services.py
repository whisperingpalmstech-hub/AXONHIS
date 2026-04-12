"""
LIS Analyzer & Device Integration Engine – Business Logic Services
"""
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AnalyzerDevice, AnalyzerWorklist, AnalyzerResult, ReagentUsage,
    DeviceError, DeviceAudit,
    DeviceStatus, AnalyzerWorklistStatus, AnalyzerResultStatus, ErrorSeverity,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Device Audit Helper ──────────────────────────────────────────────────────

class DeviceAuditService:
    @staticmethod
    async def log(db: AsyncSession, device_id: uuid.UUID, action: str,
                  direction: str = "IN", data_tx: str | None = None,
                  data_rx: str | None = None, status: str = "SUCCESS",
                  error_msg: str | None = None, performed_by: str | None = None,
                  details: dict | None = None):
        entry = DeviceAudit(
            device_id=device_id, action=action, direction=direction,
            data_transmitted=data_tx, data_received=data_rx,
            status=status, error_message=error_msg,
            performed_by=performed_by, details=details,
        )
        db.add(entry)
        return entry

    @staticmethod
    async def get_trail(db: AsyncSession, device_id: str | None = None,
                        action: str | None = None, limit: int = 100):
        stmt = select(DeviceAudit)
        if device_id:
            stmt = stmt.where(DeviceAudit.device_id == uuid.UUID(device_id))
        if action:
            stmt = stmt.where(DeviceAudit.action == action)
        stmt = stmt.order_by(DeviceAudit.performed_at.desc()).limit(limit)
        return list((await db.execute(stmt)).scalars().all())


# ── 1. Device Management Service ─────────────────────────────────────────────

class DeviceService:
    @staticmethod
    async def register_device(db: AsyncSession, data: dict) -> AnalyzerDevice:
        device = AnalyzerDevice(**{k: v for k, v in data.items() if v is not None})
        db.add(device)
        await db.flush()
        await DeviceAuditService.log(db, device.id, "DEVICE_REGISTERED",
                                      "OUT", performed_by="ADMIN",
                                      details={"device_code": data.get("device_code")})
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def list_devices(db: AsyncSession, department: str | None = None,
                           status: str | None = None, active_only: bool = True):
        stmt = select(AnalyzerDevice)
        if department:
            stmt = stmt.where(AnalyzerDevice.department == department)
        if status:
            stmt = stmt.where(AnalyzerDevice.status == status)
        if active_only:
            stmt = stmt.where(AnalyzerDevice.is_active == True)
        stmt = stmt.order_by(AnalyzerDevice.department, AnalyzerDevice.device_name)
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def get_device(db: AsyncSession, device_id: str):
        return (await db.execute(
            select(AnalyzerDevice).where(AnalyzerDevice.id == uuid.UUID(device_id))
        )).scalar_one_or_none()

    @staticmethod
    async def get_device_by_code(db: AsyncSession, code: str):
        return (await db.execute(
            select(AnalyzerDevice).where(AnalyzerDevice.device_code == code)
        )).scalar_one_or_none()

    @staticmethod
    async def update_device(db: AsyncSession, device_id: str, data: dict):
        updates = {k: v for k, v in data.items() if v is not None}
        updates["updated_at"] = _now()
        await db.execute(
            update(AnalyzerDevice).where(AnalyzerDevice.id == uuid.UUID(device_id))
            .values(**updates)
        )
        await DeviceAuditService.log(db, uuid.UUID(device_id), "DEVICE_UPDATED",
                                      "OUT", details=updates)
        await db.commit()
        return await DeviceService.get_device(db, device_id)

    @staticmethod
    async def update_status(db: AsyncSession, device_id: str, new_status: str,
                            performed_by: str | None = None):
        await db.execute(
            update(AnalyzerDevice).where(AnalyzerDevice.id == uuid.UUID(device_id))
            .values(status=new_status, last_communication=_now(), updated_at=_now())
        )
        await DeviceAuditService.log(db, uuid.UUID(device_id), "STATUS_CHANGE",
                                      "OUT", performed_by=performed_by,
                                      details={"new_status": new_status})
        await db.commit()
        return await DeviceService.get_device(db, device_id)


# ── 2. Worklist Distribution Service ─────────────────────────────────────────

class WorklistDistributionService:
    @staticmethod
    async def send_worklist(db: AsyncSession, data: dict) -> AnalyzerWorklist:
        device = await DeviceService.get_device(db, data["device_id"])
        if not device:
            raise ValueError("Analyzer device not found")

        # Map LIS test code to analyzer test code if mapping exists
        analyzer_code = None
        if device.test_code_mappings and data.get("test_code") in device.test_code_mappings:
            analyzer_code = device.test_code_mappings[data["test_code"]]

        wl = AnalyzerWorklist(
            device_id=device.id,
            sample_id=data["sample_id"], barcode=data["barcode"],
            patient_id=uuid.UUID(data["patient_id"]),
            patient_uhid=data.get("patient_uhid"),
            patient_name=data.get("patient_name"),
            order_id=uuid.UUID(data["order_id"]),
            test_code=data["test_code"], test_name=data["test_name"],
            analyzer_test_code=analyzer_code,
            priority=data.get("priority", "ROUTINE"),
            status=AnalyzerWorklistStatus.SENT,
            sent_at=_now(),
        )
        db.add(wl)
        await db.flush()

        # Update device last communication
        await db.execute(
            update(AnalyzerDevice).where(AnalyzerDevice.id == device.id)
            .values(last_communication=_now(), status=DeviceStatus.ONLINE)
        )

        await DeviceAuditService.log(db, device.id, "WORKLIST_SENT", "OUT",
                                      data_tx=f"Sample:{data['sample_id']} Test:{data['test_code']}",
                                      details={"worklist_id": str(wl.id), "priority": data.get("priority")})
        await db.commit()
        await db.refresh(wl)
        return wl

    @staticmethod
    async def batch_send(db: AsyncSession, device_id: str, items: list[dict]) -> list[AnalyzerWorklist]:
        results = []
        for item in items:
            item["device_id"] = device_id
            r = await WorklistDistributionService.send_worklist(db, item)
            results.append(r)
        return results

    @staticmethod
    async def list_worklists(db: AsyncSession, device_id: str | None = None,
                             status: str | None = None):
        stmt = select(AnalyzerWorklist)
        if device_id:
            stmt = stmt.where(AnalyzerWorklist.device_id == uuid.UUID(device_id))
        if status:
            stmt = stmt.where(AnalyzerWorklist.status == status)
        stmt = stmt.order_by(AnalyzerWorklist.created_at.desc())
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def acknowledge(db: AsyncSession, worklist_id: str):
        await db.execute(
            update(AnalyzerWorklist).where(AnalyzerWorklist.id == uuid.UUID(worklist_id))
            .values(status=AnalyzerWorklistStatus.ACKNOWLEDGED, acknowledged_at=_now())
        )
        await db.commit()


# ── 3. Result Import & Matching Service ──────────────────────────────────────

class ResultImportService:
    @staticmethod
    async def receive_result(db: AsyncSession, data: dict) -> AnalyzerResult:
        device = await DeviceService.get_device(db, data["device_id"])
        if not device:
            raise ValueError("Analyzer device not found")

        # 4. Sample-to-Test Matching Engine
        matched_wl = None
        match_status = AnalyzerResultStatus.RECEIVED
        match_confidence = 0.0
        patient_id = None

        # Try to match by sample_id and test_code
        test_code = data.get("test_code", "")
        # Reverse-map analyzer code to LIS code
        if device.test_code_mappings:
            for lis_code, analyzer_code in device.test_code_mappings.items():
                if analyzer_code == data.get("analyzer_test_code"):
                    test_code = lis_code
                    break

        wl_results = (await db.execute(
            select(AnalyzerWorklist).where(and_(
                AnalyzerWorklist.device_id == device.id,
                AnalyzerWorklist.sample_id == data["sample_id"],
            )).order_by(AnalyzerWorklist.created_at.desc())
        )).scalars().all()

        if wl_results:
            # Find exact match by test code
            for wl in wl_results:
                if wl.test_code == test_code or wl.analyzer_test_code == data.get("analyzer_test_code"):
                    matched_wl = wl
                    match_confidence = 1.0
                    break
            if not matched_wl and len(wl_results) == 1:
                matched_wl = wl_results[0]
                match_confidence = 0.7

            if matched_wl:
                match_status = AnalyzerResultStatus.MATCHED
                patient_id = matched_wl.patient_id
                # Update worklist status
                await db.execute(
                    update(AnalyzerWorklist)
                    .where(AnalyzerWorklist.id == matched_wl.id)
                    .values(status=AnalyzerWorklistStatus.COMPLETED, completed_at=_now())
                )
        else:
            match_status = AnalyzerResultStatus.MISMATCH
            # Log error for unmatched sample
            db.add(DeviceError(
                device_id=device.id, error_type="SAMPLE_MISMATCH",
                severity=ErrorSeverity.WARNING,
                message=f"Sample {data['sample_id']} not found in analyzer worklist",
                raw_data=data.get("raw_message"),
            ))

        result = AnalyzerResult(
            device_id=device.id,
            worklist_id=matched_wl.id if matched_wl else None,
            sample_id=data["sample_id"],
            barcode=data.get("barcode"),
            patient_id=patient_id,
            test_code=test_code,
            analyzer_test_code=data.get("analyzer_test_code"),
            result_value=data.get("result_value"),
            result_numeric=data.get("result_numeric"),
            result_unit=data.get("result_unit"),
            result_flag=data.get("result_flag"),
            raw_message=data.get("raw_message"),
            status=match_status,
            match_confidence=match_confidence,
            is_qc_sample=data.get("is_qc_sample", False),
        )
        db.add(result)
        await db.flush()

        # Update device last communication
        await db.execute(
            update(AnalyzerDevice).where(AnalyzerDevice.id == device.id)
            .values(last_communication=_now(), status=DeviceStatus.ONLINE)
        )

        await DeviceAuditService.log(db, device.id, "RESULT_RECEIVED", "IN",
                                      data_rx=f"Sample:{data['sample_id']} Value:{data.get('result_value')}",
                                      details={
                                          "result_id": str(result.id),
                                          "match_status": match_status,
                                          "confidence": match_confidence,
                                      })
        await db.commit()
        await db.refresh(result)
        return result

    @staticmethod
    async def batch_receive(db: AsyncSession, device_id: str,
                            results: list[dict]) -> list[AnalyzerResult]:
        imported = []
        for r in results:
            r["device_id"] = device_id
            res = await ResultImportService.receive_result(db, r)
            imported.append(res)
        return imported

    @staticmethod
    async def verify_result(db: AsyncSession, result_id: str, verified_by: str):
        await db.execute(
            update(AnalyzerResult).where(AnalyzerResult.id == uuid.UUID(result_id))
            .values(verified_by=verified_by, verified_at=_now(),
                    status=AnalyzerResultStatus.VERIFIED)
        )
        result = (await db.execute(
            select(AnalyzerResult).where(AnalyzerResult.id == uuid.UUID(result_id))
        )).scalar_one_or_none()
        if result:
            await DeviceAuditService.log(db, result.device_id, "RESULT_VERIFIED",
                                          "OUT", performed_by=verified_by)
        await db.commit()
        return result

    @staticmethod
    async def import_to_lis(db: AsyncSession, result_id: str):
        """Mark result as imported into the main LIS result entry system."""
        await db.execute(
            update(AnalyzerResult).where(AnalyzerResult.id == uuid.UUID(result_id))
            .values(status=AnalyzerResultStatus.IMPORTED, imported_at=_now())
        )
        await db.commit()

    @staticmethod
    async def list_results(db: AsyncSession, device_id: str | None = None,
                           status: str | None = None, unverified_only: bool = False):
        stmt = select(AnalyzerResult)
        if device_id:
            stmt = stmt.where(AnalyzerResult.device_id == uuid.UUID(device_id))
        if status:
            stmt = stmt.where(AnalyzerResult.status == status)
        if unverified_only:
            stmt = stmt.where(AnalyzerResult.verified_by == None)
        stmt = stmt.order_by(AnalyzerResult.received_at.desc())
        return list((await db.execute(stmt)).scalars().all())


# ── 5. Reagent Tracking Service ──────────────────────────────────────────────

class ReagentService:
    @staticmethod
    async def record_usage(db: AsyncSession, data: dict) -> ReagentUsage:
        is_low = False
        if data.get("current_stock") and data.get("reorder_level"):
            is_low = data["current_stock"] <= data["reorder_level"]

        usage = ReagentUsage(
            device_id=uuid.UUID(data["device_id"]),
            reagent_name=data["reagent_name"],
            reagent_lot=data.get("reagent_lot"),
            test_code=data["test_code"],
            quantity_used=data.get("quantity_used", 1.0),
            unit=data.get("unit", "tests"),
            current_stock=data.get("current_stock"),
            reorder_level=data.get("reorder_level"),
            is_low_stock=is_low,
        )
        db.add(usage)
        await DeviceAuditService.log(db, uuid.UUID(data["device_id"]),
                                      "REAGENT_CONSUMED", "IN",
                                      details={"reagent": data["reagent_name"],
                                               "low_stock": is_low})
        await db.commit()
        await db.refresh(usage)
        return usage

    @staticmethod
    async def list_usage(db: AsyncSession, device_id: str | None = None,
                         low_only: bool = False):
        stmt = select(ReagentUsage)
        if device_id:
            stmt = stmt.where(ReagentUsage.device_id == uuid.UUID(device_id))
        if low_only:
            stmt = stmt.where(ReagentUsage.is_low_stock == True)
        stmt = stmt.order_by(ReagentUsage.recorded_at.desc())
        return list((await db.execute(stmt)).scalars().all())


# ── 6. Error Handling Service ────────────────────────────────────────────────

class DeviceErrorService:
    @staticmethod
    async def report_error(db: AsyncSession, data: dict) -> DeviceError:
        err = DeviceError(
            device_id=uuid.UUID(data["device_id"]),
            error_code=data.get("error_code"),
            error_type=data["error_type"],
            severity=data.get("severity", ErrorSeverity.ERROR),
            message=data["message"],
            raw_data=data.get("raw_data"),
        )
        db.add(err)

        # Update device status to ERROR if critical
        if data.get("severity") in (ErrorSeverity.ERROR, ErrorSeverity.CRITICAL):
            await db.execute(
                update(AnalyzerDevice)
                .where(AnalyzerDevice.id == uuid.UUID(data["device_id"]))
                .values(status=DeviceStatus.ERROR)
            )

        await DeviceAuditService.log(db, uuid.UUID(data["device_id"]),
                                      "ERROR_REPORTED", "IN",
                                      error_msg=data["message"],
                                      details={"severity": data.get("severity"),
                                               "error_type": data["error_type"]})
        await db.commit()
        await db.refresh(err)
        return err

    @staticmethod
    async def resolve_error(db: AsyncSession, error_id: str, resolved_by: str):
        await db.execute(
            update(DeviceError).where(DeviceError.id == uuid.UUID(error_id))
            .values(is_resolved=True, resolved_by=resolved_by, resolved_at=_now())
        )
        await db.commit()

    @staticmethod
    async def list_errors(db: AsyncSession, device_id: str | None = None,
                          unresolved_only: bool = False):
        stmt = select(DeviceError)
        if device_id:
            stmt = stmt.where(DeviceError.device_id == uuid.UUID(device_id))
        if unresolved_only:
            stmt = stmt.where(DeviceError.is_resolved == False)
        stmt = stmt.order_by(DeviceError.occurred_at.desc())
        return list((await db.execute(stmt)).scalars().all())


# ── 7. Dashboard Statistics ──────────────────────────────────────────────────

class AnalyzerStatsService:
    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        total = (await db.execute(select(func.count()).select_from(AnalyzerDevice).where(AnalyzerDevice.is_active == True))).scalar() or 0
        online = (await db.execute(select(func.count()).select_from(AnalyzerDevice).where(and_(AnalyzerDevice.is_active == True, AnalyzerDevice.status == DeviceStatus.ONLINE)))).scalar() or 0
        offline = (await db.execute(select(func.count()).select_from(AnalyzerDevice).where(and_(AnalyzerDevice.is_active == True, AnalyzerDevice.status == DeviceStatus.OFFLINE)))).scalar() or 0
        maint = (await db.execute(select(func.count()).select_from(AnalyzerDevice).where(and_(AnalyzerDevice.is_active == True, AnalyzerDevice.status == DeviceStatus.MAINTENANCE)))).scalar() or 0
        err_devs = (await db.execute(select(func.count()).select_from(AnalyzerDevice).where(and_(AnalyzerDevice.is_active == True, AnalyzerDevice.status == DeviceStatus.ERROR)))).scalar() or 0
        pending_wl = (await db.execute(select(func.count()).select_from(AnalyzerWorklist).where(AnalyzerWorklist.status.in_([AnalyzerWorklistStatus.QUEUED, AnalyzerWorklistStatus.SENT])))).scalar() or 0
        unverified = (await db.execute(select(func.count()).select_from(AnalyzerResult).where(and_(AnalyzerResult.verified_by == None, AnalyzerResult.status != AnalyzerResultStatus.REJECTED)))).scalar() or 0
        unresolved = (await db.execute(select(func.count()).select_from(DeviceError).where(DeviceError.is_resolved == False))).scalar() or 0
        low_stock = (await db.execute(select(func.count()).select_from(ReagentUsage).where(ReagentUsage.is_low_stock == True))).scalar() or 0

        today_start = _now().replace(hour=0, minute=0, second=0, microsecond=0)
        results_today = (await db.execute(select(func.count()).select_from(AnalyzerResult).where(AnalyzerResult.received_at >= today_start))).scalar() or 0

        dept_rows = (await db.execute(
            select(AnalyzerDevice.department, AnalyzerDevice.status, func.count())
            .where(AnalyzerDevice.is_active == True)
            .group_by(AnalyzerDevice.department, AnalyzerDevice.status)
        )).all()
        dept_status: dict = {}
        for dept, status, count in dept_rows:
            if dept not in dept_status:
                dept_status[dept] = {}
            dept_status[dept][status] = count

        return {
            "total_devices": total, "online_devices": online,
            "offline_devices": offline, "maintenance_devices": maint,
            "error_devices": err_devs, "pending_worklists": pending_wl,
            "unverified_results": unverified, "unresolved_errors": unresolved,
            "low_stock_reagents": low_stock, "department_status": dept_status,
            "results_today": results_today,
        }
