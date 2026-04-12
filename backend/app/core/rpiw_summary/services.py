from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import (
    RpiwPatientSummary, RpiwSummarySource, RpiwSummaryAlert,
    RpiwSummaryTask, RpiwSummaryVital, RpiwSummaryMedication
)

import uuid


class RPIWSummaryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_summary(self, patient_uhid: str, admission_number: str = None, visit_id: str = None):
        """Fetch existing summary or create a new one."""
        query = select(RpiwPatientSummary).where(RpiwPatientSummary.patient_uhid == patient_uhid)
        if admission_number:
            query = query.where(RpiwPatientSummary.admission_number == admission_number)
        if visit_id:
            query = query.where(RpiwPatientSummary.visit_id == visit_id)

        summary = (await self.db.execute(query)).scalar_one_or_none()

        if not summary:
            summary = RpiwPatientSummary(
                patient_uhid=patient_uhid,
                admission_number=admission_number,
                visit_id=visit_id
            )
            self.db.add(summary)
            await self.db.flush()

        return summary

    async def update_summary(self, summary_id: str, data: dict):
        """Update core summary text fields."""
        summary = (await self.db.execute(select(RpiwPatientSummary).where(RpiwPatientSummary.id == summary_id))).scalar_one_or_none()
        if summary:
            if "chief_issue" in data: summary.chief_issue = data["chief_issue"]
            if "primary_diagnosis" in data: summary.primary_diagnosis = data["primary_diagnosis"]
            if "current_clinical_status" in data: summary.current_clinical_status = data["current_clinical_status"]
            if "last_updated_by" in data: summary.last_updated_by = data["last_updated_by"]
            summary.last_updated_at = datetime.now(timezone.utc)
            await self.db.flush()
        return summary


    # ─── Data Aggregation Tracks ──────────────────────────────────

    async def add_source(self, summary_id: str, module: str, record_id: str):
        """Log data source for audit trail."""
        source = RpiwSummarySource(summary_id=summary_id, source_module=module, source_record_id=record_id)
        self.db.add(source)
        await self.db.flush()
        return source


    async def add_alert(self, summary_id: str, data: dict):
        alert = RpiwSummaryAlert(summary_id=summary_id, **data)
        self.db.add(alert)
        
        # Also touch the summary's last_updated_at
        await self.db.execute(update(RpiwPatientSummary).where(RpiwPatientSummary.id == summary_id).values(last_updated_at=datetime.now(timezone.utc)))
        await self.db.flush()
        return alert

    async def resolve_alert(self, alert_id: str):
        alert = (await self.db.execute(select(RpiwSummaryAlert).where(RpiwSummaryAlert.id == alert_id))).scalar_one_or_none()
        if alert:
            alert.is_active = False
            alert.resolved_at = datetime.now(timezone.utc)
            await self.db.flush()
        return alert


    async def add_task(self, summary_id: str, data: dict):
        task = RpiwSummaryTask(summary_id=summary_id, **data)
        self.db.add(task)
        await self.db.execute(update(RpiwPatientSummary).where(RpiwPatientSummary.id == summary_id).values(last_updated_at=datetime.now(timezone.utc)))
        await self.db.flush()
        return task

    async def update_task_status(self, task_id: str, status: str):
        task = (await self.db.execute(select(RpiwSummaryTask).where(RpiwSummaryTask.id == task_id))).scalar_one_or_none()
        if task:
            task.status = status
            await self.db.flush()
        return task


    async def add_vital(self, summary_id: str, data: dict):
        vital = RpiwSummaryVital(summary_id=summary_id, **data)
        if vital.recorded_at is None:
            vital.recorded_at = datetime.now(timezone.utc)
        self.db.add(vital)
        await self.db.execute(update(RpiwPatientSummary).where(RpiwPatientSummary.id == summary_id).values(last_updated_at=datetime.now(timezone.utc)))
        await self.db.flush()
        return vital


    async def add_medication(self, summary_id: str, data: dict):
        med = RpiwSummaryMedication(summary_id=summary_id, **data)
        self.db.add(med)
        await self.db.execute(update(RpiwPatientSummary).where(RpiwPatientSummary.id == summary_id).values(last_updated_at=datetime.now(timezone.utc)))
        await self.db.flush()
        return med


    # ─── Patient Summary View ──────────────────────────────────

    async def get_composite_summary(self, patient_uhid: str, admission_number: str = None, visit_id: str = None):
        """Construct the full 360-degree patient summary view."""
        summary = await self.get_or_create_summary(patient_uhid, admission_number, visit_id)
        
        # Load related data using sequential queries (to keep it straightforward)
        sources = (await self.db.execute(select(RpiwSummarySource).where(RpiwSummarySource.summary_id == summary.id))).scalars().all()
        
        # only active alerts
        alerts = (await self.db.execute(select(RpiwSummaryAlert).where(
            RpiwSummaryAlert.summary_id == summary.id,
            RpiwSummaryAlert.is_active == True
        ).order_by(RpiwSummaryAlert.detected_at.desc()))).scalars().all()
        
        # all tasks, sorted by uncompleted
        tasks = (await self.db.execute(select(RpiwSummaryTask).where(
            RpiwSummaryTask.summary_id == summary.id
        ).order_by(RpiwSummaryTask.created_at.desc()))).scalars().all()
        
        # 10 most recent vitals per type (simplified here to just 50 total limit)
        vitals = (await self.db.execute(select(RpiwSummaryVital).where(
            RpiwSummaryVital.summary_id == summary.id
        ).order_by(RpiwSummaryVital.recorded_at.desc()).limit(50))).scalars().all()
        
        # Active medications only
        medications = (await self.db.execute(select(RpiwSummaryMedication).where(
            RpiwSummaryMedication.summary_id == summary.id,
            RpiwSummaryMedication.is_active == True
        ))).scalars().all()

        return {
            "summary": summary,
            "sources": sources,
            "alerts": alerts,
            "tasks": tasks,
            "vitals": vitals,
            "medications": medications
        }

    # ─── Mock Data Generators for Dashboard Visualization ────────────────

    async def _mock_seed_data(self, summary_id: str):
        # Insert a few vitals
        import random
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        
        self.db.add(RpiwSummaryVital(summary_id=summary_id, vital_sign="BP", value="120/80", unit="mmHg", recorded_at=now - timedelta(hours=2)))
        self.db.add(RpiwSummaryVital(summary_id=summary_id, vital_sign="BP", value="130/85", unit="mmHg", recorded_at=now - timedelta(hours=1)))
        self.db.add(RpiwSummaryVital(summary_id=summary_id, vital_sign="Temperature", value="37.2", unit="°C", recorded_at=now))
        self.db.add(RpiwSummaryVital(summary_id=summary_id, vital_sign="Heart Rate", value="88", unit="bpm", recorded_at=now))
        
        # Insert medications
        self.db.add(RpiwSummaryMedication(summary_id=summary_id, drug_name="Ceftriaxone", dosage="1g", frequency="Twice daily", route="IV", is_active=True))
        self.db.add(RpiwSummaryMedication(summary_id=summary_id, drug_name="Paracetamol", dosage="500mg", frequency="SOS", route="Oral", is_active=True))

        # Insert alerts
        self.db.add(RpiwSummaryAlert(summary_id=summary_id, alert_type="critical_lab", severity="high", message="Elevated WBC count (15.2 x10^9/L)", is_active=True))
        
        # Insert tasks
        self.db.add(RpiwSummaryTask(summary_id=summary_id, task_category="lab_test", description="Collect blood sample for CBC", status="Pending"))
        self.db.add(RpiwSummaryTask(summary_id=summary_id, task_category="imaging", description="Chest X-Ray", status="Completed"))

        await self.db.flush()

    async def generate_mock_summary(self, patient_uhid: str):
        """Force populate a fake summary for visualization purposes."""
        summary = await self.get_or_create_summary(patient_uhid)
        summary.chief_issue = "Post-operative appendectomy recovery"
        summary.primary_diagnosis = "Acute appendicitis"
        summary.current_clinical_status = "Patient is stable, wound healing well, afebrile."
        
        await self._mock_seed_data(str(summary.id))
        await self.db.commit()
        return summary

