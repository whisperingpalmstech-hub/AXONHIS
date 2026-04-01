from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_, or_
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
import random
import uuid

from .models import (
    IpdAdmissionRequest,
    IpdAdmissionRecord,
    IpdAdmissionAuditLog,
    IpdCostEstimation,
    IpdAdmissionChecklist,
    IpdInsuranceDetails,
    IpdProjectedBill,
    IpdDepositRecord,
    IpdPatientTransport,
    IpdNursingWorklist,
    IpdNursingCoversheet,
    IpdPatientStatusMonitor,
    IpdNursingNote,
    IpdCareAssignment,
    IpdNursingAuditLog,
    IpdVitalsRecord,
    IpdNursingAssessment,
    IpdRiskAssessment,
    IpdPainScore,
    IpdNutritionAssessment,
    IpdNursingObservation,
)


class IPDService:
    def __init__(self, db: AsyncSession, org_id: Optional[UUID] = None):
        self.db = db
        self.org_id = org_id

    def generate_id(self, prefix: str) -> str:
        num = random.randint(100000, 999999)
        year = datetime.now().year
        return f"{prefix}-{year}-{num}"

    async def log_audit(
        self,
        action: str,
        entity_id: str,
        uhid: str | None,
        details: dict,
        user_id: UUID | None = None,
    ):
        log = IpdAdmissionAuditLog(
            action_type=action,
            entity_id=entity_id,
            patient_uhid=uhid,
            details=details or {},
            user_id=user_id,
            org_id=self.org_id,
        )
        self.db.add(log)

    # --- Admission Requests --- #
    async def create_admission_request(
        self, data: dict, user_id: UUID | None = None
    ) -> IpdAdmissionRequest:
        req_raw = data.copy()

        req = IpdAdmissionRequest(
            request_id=self.generate_id("ADM-REQ"),
            **req_raw,
            created_by=user_id,
            org_id=self.org_id or data.get("org_id"),
        )
        self.db.add(req)
        await self.db.flush()

        await self.log_audit(
            action="Request Created",
            entity_id=req.request_id,
            uhid=req.patient_uhid,
            details={"admitting_doctor": req.admitting_doctor, "category": req.admission_category},
            user_id=user_id,
        )
        return req

    async def get_pending_requests(self) -> list[IpdAdmissionRequest]:
        stmt = select(IpdAdmissionRequest).where(IpdAdmissionRequest.status == "Pending")
        if self.org_id:
            stmt = stmt.where(IpdAdmissionRequest.org_id == self.org_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_request_by_id(self, req_id: UUID) -> IpdAdmissionRequest | None:
        stmt = select(IpdAdmissionRequest).where(IpdAdmissionRequest.id == req_id)
        if self.org_id:
            stmt = stmt.where(IpdAdmissionRequest.org_id == self.org_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_request_status(
        self, req_id: UUID, status: str, user_id: UUID | None = None
    ) -> IpdAdmissionRequest | None:
        req = await self.get_request_by_id(req_id)
        if not req:
            return None
        req.status = status

        await self.log_audit(
            action=f"Admission {status}",
            entity_id=req.request_id,
            uhid=req.patient_uhid,
            details={"new_status": status},
            user_id=user_id,
        )
        await self.db.flush()
        return req

    # --- Dashboards --- #
    async def get_dashboard_stats(self) -> dict:
        from app.core.wards.models import Bed

        # 1. Beds Total
        tb_q = select(func.count(Bed.id))
        if self.org_id:
            tb_q = tb_q.where(Bed.org_id == self.org_id)
        total_beds = (await self.db.execute(tb_q)).scalar() or 0

        # 2. Status Breakdown
        st_q = select(Bed.status, func.count(Bed.id)).group_by(Bed.status)
        if self.org_id:
            st_q = st_q.where(Bed.org_id == self.org_id)
        status_counts = dict((await self.db.execute(st_q)).all())

        # 3. Pending Requests Queue
        pr_q = select(func.count(IpdAdmissionRequest.id)).where(
            IpdAdmissionRequest.status == "Pending"
        )
        if self.org_id:
            pr_q = pr_q.where(IpdAdmissionRequest.org_id == self.org_id)
        pending_requests = (await self.db.execute(pr_q)).scalar() or 0

        return {
            "total_beds": total_beds,
            "occupied_beds": status_counts.get("occupied", 0),
            "available_beds": status_counts.get("available", 0),
            "housekeeping_beds": status_counts.get("cleaning", 0),
            "reserved_beds": status_counts.get("reserved", 0),
            "pending_requests": pending_requests,
        }

    # --- Bed Allocation & Admission --- #
    async def allocate_bed(
        self, req_id: UUID, bed_code: str, user_id: UUID | None = None
    ) -> IpdAdmissionRecord | None:
        from app.core.wards.models import Bed

        # Load request
        req = await self.get_request_by_id(req_id)
        if not req or req.status != "Approved":
            return None

        # Load bed from central Wards module
        query = select(Bed).where(Bed.bed_code == bed_code)
        if self.org_id:
            query = query.where(Bed.org_id == self.org_id)
        res = await self.db.execute(query)
        bed = res.scalars().first()
        if not bed or bed.status not in ["available", "reserved", "cleaning"]:
            return None

        # Generate admission number
        adm_no = self.generate_id("IPD-ADM")

        # Create Encounter for Billing
        from app.core.encounters.models import Encounter
        from app.core.patients.patients.models import Patient

        from sqlalchemy import or_

        query_val = req.patient_uhid
        try:
            valid_uuid = uuid.UUID(query_val)
            stmt = select(Patient).where(
                or_(Patient.id == valid_uuid, Patient.patient_uuid == query_val)
            )
        except (ValueError, TypeError):
            stmt = select(Patient).where(
                or_(Patient.patient_uuid == query_val, Patient.mrn == query_val)
            )

        patient = (await self.db.execute(stmt)).scalar_one_or_none()
        enc = None
        if patient:
            enc = Encounter(
                patient_id=patient.id,
                encounter_type="IPD",
                status="ACTIVE",
                encounter_uuid=adm_no,
                department=req.specialty or "GENERAL",
                org_id=self.org_id or req.org_id,
            )
            self.db.add(enc)
            await self.db.flush()

            # Phase 23 - Bridge to Central Billing
            from app.core.encounter_bridge import EncounterBridgeService

            bridge = EncounterBridgeService(self.db)
            try:
                await bridge.initialize_bill(
                    patient_id=patient.id,
                    visit_id=enc.id,
                    generated_by=user_id or patient.id,
                    org_id=self.org_id or req.org_id,
                    encounter_type="IPD",
                )
            except Exception as e:
                import logging

                logging.getLogger(__name__).error(f"[IPD-BRIDGE] Failed to sync with Billing: {e}")

        # Create Admission Record
        adm = IpdAdmissionRecord(
            admission_number=adm_no,
            request_id=req_id,
            patient_uhid=req.patient_uhid,
            bed_uuid=bed.id,
            admitting_doctor=req.admitting_doctor,
            status="Admitted",
            visit_id=str(enc.id) if enc else None,
            org_id=self.org_id or req.org_id,
        )
        self.db.add(adm)

        # Update Central Bed Status
        bed.status = "occupied"

        # Update Request Status
        req.status = "Allocated"

        # Audit logs
        await self.log_audit(
            action="Bed Allocated",
            entity_id=adm_no,
            uhid=req.patient_uhid,
            details={"bed_id": str(bed.id)},
            user_id=user_id,
        )

        # Phase 15: Initialize Nursing Worklist and Patient Status Monitor
        from .models import IpdNursingWorklist, IpdPatientStatusMonitor

        wl = IpdNursingWorklist(
            admission_number=adm_no,
            patient_uhid=req.patient_uhid,
            bed_uuid=bed.id,
            ward_name="Ward",  # Simplified placeholder
            bed_number=bed.bed_code,
            admitting_doctor=req.admitting_doctor,
            admission_time=datetime.now(timezone.utc),
            status="Pending Acceptance",
            org_id=self.org_id,
        )
        self.db.add(wl)

        stat_monitor = IpdPatientStatusMonitor(
            admission_number=adm_no, status="Pending Acceptance", org_id=self.org_id
        )
        self.db.add(stat_monitor)

        await self.db.flush()
        return adm

    async def get_active_admissions(self) -> list["IpdAdmissionRecord"]:
        res = await self.db.execute(
            select(IpdAdmissionRecord).order_by(IpdAdmissionRecord.admission_time.desc())
        )
        return res.scalars().all()

    # --- Phase 14: Cost Estimation ---
    async def generate_cost_estimate(self, req_id: UUID, data: dict) -> IpdCostEstimation:
        from .models import IpdCostEstimation

        req = await self.get_request_by_id(req_id)
        if not req:
            return None

        # Simple algorithm to mock dynamic estimation
        lower = 50000.0 + (len(data.get("planned_procedures", [])) * 25000.0)
        upper = lower + 35000.0

        est = IpdCostEstimation(
            request_id=req_id,
            patient_uhid=req.patient_uhid,
            selected_bed_category=data.get("selected_bed_category"),
            planned_procedures=data.get("planned_procedures", []),
            planned_services=data.get("planned_services", []),
            estimated_cost_lower=lower,
            estimated_cost_upper=upper,
        )
        self.db.add(est)
        await self.db.flush()
        return est

    # --- Checklist ---
    async def get_checklist(self, adm_no: str) -> Optional[IpdAdmissionChecklist]:
        from .models import IpdAdmissionChecklist

        res = await self.db.execute(
            select(IpdAdmissionChecklist).where(IpdAdmissionChecklist.admission_number == adm_no)
        )
        return res.scalars().first()

    async def update_checklist(self, adm_no: str, data: dict) -> Optional[IpdAdmissionChecklist]:
        from .models import IpdAdmissionChecklist

        cl = await self.get_checklist(adm_no)
        if not cl:
            cl = IpdAdmissionChecklist(admission_number=adm_no)
            self.db.add(cl)

        for key, value in data.items():
            setattr(cl, key, value)

        # check if all true
        required_fields = [
            "registration_completed",
            "identity_proof_verified",
            "consent_taken",
            "deposit_collected",
        ]
        complete = all(getattr(cl, f, False) for f in required_fields)
        if complete and not cl.is_complete:
            cl.is_complete = True
            cl.completed_at = datetime.now(timezone.utc)

        await self.db.flush()
        return cl

    # --- Insurance Validation ---
    async def save_insurance(self, adm_no: str, data: dict) -> IpdInsuranceDetails:
        from .models import IpdInsuranceDetails

        ins = IpdInsuranceDetails(admission_number=adm_no, **data)

        # Basic validation logic mock
        limit = data.get("total_sum_assured", 0) * data.get("bed_charge_limit_percent", 0)
        if limit >= 5000:
            ins.eligible_bed_category = "Private"
        elif limit >= 3000:
            ins.eligible_bed_category = "Semi-Private"
        else:
            ins.eligible_bed_category = "General Ward"

        self.db.add(ins)
        await self.db.flush()
        return ins

    # --- Bill Projection & Recalculation ---
    async def get_projected_bill(self, adm_no: str) -> Optional[IpdProjectedBill]:
        from .models import IpdProjectedBill

        res = await self.db.execute(
            select(IpdProjectedBill).where(IpdProjectedBill.admission_number == adm_no)
        )
        bill = res.scalars().first()
        if not bill:
            bill = IpdProjectedBill(
                admission_number=adm_no,
                bed_charges=15000.0,
                investigations=5000.0,
                total_projected_amount=20000.0,
            )  # Default dummy representation, later recalcs
            self.db.add(bill)
            await self.db.flush()
        return bill

    # --- Deposits ---
    async def collect_deposit(self, adm_no: str, data: dict) -> IpdDepositRecord:
        from .models import IpdDepositRecord

        rec = self.generate_id("RCPT")
        dep = IpdDepositRecord(admission_number=adm_no, receipt_number=rec, **data)
        self.db.add(dep)
        await self.db.flush()
        return dep

    # --- Transportation ---
    async def request_transport(self, adm_no: str, data: dict) -> IpdPatientTransport:
        from .models import IpdPatientTransport

        t = IpdPatientTransport(admission_number=adm_no, **data)
        self.db.add(t)
        await self.db.flush()
        return t

    # --- Phase 15: Nursing Coversheet & Patient Acceptance ---

    async def get_nursing_worklist(self) -> list["IpdNursingWorklist"]:
        from .models import IpdNursingWorklist

        res = await self.db.execute(
            select(IpdNursingWorklist).order_by(IpdNursingWorklist.admission_time.desc())
        )
        return res.scalars().all()

    async def accept_patient(
        self, adm_no: str, priority_status: str, nurse_id: str, nurse_name: str
    ) -> "IpdNursingCoversheet":
        from .models import (
            IpdNursingCoversheet,
            IpdNursingWorklist,
            IpdAdmissionRecord,
            IpdPatientStatusMonitor,
        )

        # 1. Look up admission
        adm_res = await self.db.execute(
            select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
        )
        adm = adm_res.scalars().first()
        if not adm:
            raise ValueError("Admission not found")

        # 2. Check worklist
        wl_res = await self.db.execute(
            select(IpdNursingWorklist).where(IpdNursingWorklist.admission_number == adm_no)
        )
        wl = wl_res.scalars().first()
        if wl:
            wl.status = "Accepted"

        # 3. Create or update coversheet
        cs_res = await self.db.execute(
            select(IpdNursingCoversheet).where(IpdNursingCoversheet.admission_number == adm_no)
        )
        cs = cs_res.scalars().first()
        if not cs:
            cs = IpdNursingCoversheet(
                admission_number=adm_no,
                patient_uhid=adm.patient_uhid,
                bed_uuid=adm.bed_uuid,
                primary_diagnosis=None,
                treating_doctor_name=adm.admitting_doctor,
                priority_status=priority_status,
                acceptance_time=datetime.now(timezone.utc),
                accepted_by_nurse_id=UUID(nurse_id)
                if (nurse_id and nurse_id != "00000000-0000-0000-0000-000000000000")
                else None,
                accepted_by_nurse_name=nurse_name,
                org_id=self.org_id,
            )
            self.db.add(cs)
        else:
            cs.acceptance_time = datetime.now(timezone.utc)
            cs.accepted_by_nurse_id = (
                UUID(nurse_id)
                if (nurse_id and nurse_id != "00000000-0000-0000-0000-000000000000")
                else None
            )
            cs.accepted_by_nurse_name = nurse_name
            cs.priority_status = priority_status

        # 4. Update status monitor
        stat_res = await self.db.execute(
            select(IpdPatientStatusMonitor).where(
                IpdPatientStatusMonitor.admission_number == adm_no
            )
        )
        stat_monitor = stat_res.scalars().first()
        if not stat_monitor:
            stat_monitor = IpdPatientStatusMonitor(admission_number=adm_no, status="Accepted")
            self.db.add(stat_monitor)
        else:
            stat_monitor.status = "Accepted"
            stat_monitor.last_updated = datetime.now(timezone.utc)

        await self.db.flush()
        return cs

    async def add_nursing_note(
        self,
        admission_number: str,
        note_type: str,
        clinical_note: str,
        user_id: str,
        user_name: str,
    ) -> "IpdNursingNote":
        from .models import IpdNursingNote

        note = IpdNursingNote(
            admission_number=admission_number,
            note_type=note_type,
            clinical_note=clinical_note,
            logged_by_id=UUID(user_id)
            if (user_id and user_id != "00000000-0000-0000-0000-000000000000")
            else uuid.uuid4(),
            logged_by_name=user_name,
        )
        self.db.add(note)
        await self.db.flush()
        return note

    async def assign_nursing_care(self, admission_number: str, data: dict) -> "IpdCareAssignment":
        from .models import IpdCareAssignment

        assignment = IpdCareAssignment(
            admission_number=admission_number,
            **{
                k: v for k, v in data.items() if k != "id" and k != "start_time" and k != "end_time"
            },
        )
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    # --- Phase 16: Nursing Assessment & Vitals Monitoring ---

    def _check_vitals_alerts(self, data: dict) -> tuple[bool, str]:
        alerts = []
        if data.get("spo2") and data["spo2"] < 92:
            alerts.append(f"SpO2 critically low: {data['spo2']}%")
        if data.get("bp_systolic") and data["bp_systolic"] > 180:
            alerts.append(f"Systolic BP dangerously high: {data['bp_systolic']} mmHg")
        if data.get("bp_diastolic") and data["bp_diastolic"] > 110:
            alerts.append(f"Diastolic BP dangerously high: {data['bp_diastolic']} mmHg")
        if data.get("temperature") and data["temperature"] > 39:
            alerts.append(f"Hyperthermia: {data['temperature']}°C")
        if data.get("pulse_rate") and data["pulse_rate"] > 120:
            alerts.append(f"Tachycardia: {data['pulse_rate']} bpm")
        if data.get("pulse_rate") and data["pulse_rate"] < 50:
            alerts.append(f"Bradycardia: {data['pulse_rate']} bpm")
        if alerts:
            return True, "; ".join(alerts)
        return False, ""

    async def record_vitals(
        self, adm_no: str, data: dict, user_name: str = "Nurse"
    ) -> IpdVitalsRecord:
        adm_res = await self.db.execute(
            select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
        )
        adm = adm_res.scalars().first()
        if not adm:
            raise ValueError("Admission not found")

        # Auto-calculate BMI
        bmi = None
        if data.get("height_cm") and data.get("weight_kg") and data["height_cm"] > 0:
            height_m = data["height_cm"] / 100.0
            bmi = round(data["weight_kg"] / (height_m * height_m), 1)

        alert_triggered, alert_message = self._check_vitals_alerts(data)

        vitals = IpdVitalsRecord(
            admission_number=adm_no,
            patient_uhid=adm.patient_uhid,
            bmi=bmi,
            recorded_by_name=user_name,
            alert_triggered=alert_triggered,
            alert_message=alert_message if alert_triggered else None,
            **{k: v for k, v in data.items() if k not in ("bmi",)},
        )
        self.db.add(vitals)
        await self.db.flush()
        return vitals

    async def get_vitals_history(self, adm_no: str) -> list[IpdVitalsRecord]:
        res = await self.db.execute(
            select(IpdVitalsRecord)
            .where(IpdVitalsRecord.admission_number == adm_no)
            .order_by(IpdVitalsRecord.recorded_at.desc())
        )
        return res.scalars().all()

    async def save_nursing_assessment(
        self, adm_no: str, data: dict, user_name: str = "Nurse"
    ) -> IpdNursingAssessment:
        adm_res = await self.db.execute(
            select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
        )
        adm = adm_res.scalars().first()
        if not adm:
            raise ValueError("Admission not found")

        # Upsert
        existing = await self.db.execute(
            select(IpdNursingAssessment).where(IpdNursingAssessment.admission_number == adm_no)
        )
        assessment = existing.scalars().first()
        if assessment:
            for k, v in data.items():
                if hasattr(assessment, k):
                    setattr(assessment, k, v)
            assessment.assessed_by_name = user_name
            assessment.assessed_at = datetime.now(timezone.utc)
        else:
            assessment = IpdNursingAssessment(
                admission_number=adm_no,
                patient_uhid=adm.patient_uhid,
                assessed_by_name=user_name,
                **data,
            )
            self.db.add(assessment)
        await self.db.flush()
        return assessment

    async def get_nursing_assessment(self, adm_no: str) -> Optional[IpdNursingAssessment]:
        res = await self.db.execute(
            select(IpdNursingAssessment).where(IpdNursingAssessment.admission_number == adm_no)
        )
        return res.scalars().first()

    async def add_risk_assessment(
        self, adm_no: str, data: dict, user_name: str = "Nurse"
    ) -> IpdRiskAssessment:
        risk = IpdRiskAssessment(admission_number=adm_no, assessed_by_name=user_name, **data)
        self.db.add(risk)
        await self.db.flush()
        return risk

    async def get_risk_assessments(self, adm_no: str) -> list[IpdRiskAssessment]:
        res = await self.db.execute(
            select(IpdRiskAssessment)
            .where(IpdRiskAssessment.admission_number == adm_no)
            .order_by(IpdRiskAssessment.assessed_at.desc())
        )
        return res.scalars().all()

    async def add_pain_score(
        self, adm_no: str, data: dict, user_name: str = "Nurse"
    ) -> IpdPainScore:
        ps = IpdPainScore(admission_number=adm_no, recorded_by_name=user_name, **data)
        self.db.add(ps)
        await self.db.flush()
        return ps

    async def add_nutrition_assessment(
        self, adm_no: str, data: dict, user_name: str = "Nurse"
    ) -> IpdNutritionAssessment:
        na = IpdNutritionAssessment(admission_number=adm_no, assessed_by_name=user_name, **data)
        if data.get("malnutrition_risk") == "High":
            na.dietician_notified = True
        self.db.add(na)
        await self.db.flush()
        return na

    async def add_observation(
        self, adm_no: str, data: dict, user_name: str = "Nurse"
    ) -> IpdNursingObservation:
        obs = IpdNursingObservation(admission_number=adm_no, recorded_by_name=user_name, **data)
        self.db.add(obs)
        await self.db.flush()
        return obs

    async def get_observations(self, adm_no: str):
        from .models import IpdNursingObservation

        res = await self.db.execute(
            select(IpdNursingObservation)
            .where(IpdNursingObservation.admission_number == adm_no)
            .order_by(IpdNursingObservation.recorded_at.desc())
        )
        return res.scalars().all()

    # --- Phase 17: Doctor Coversheet & Clinical Documentation ---

    async def get_doctor_worklist(self):
        from .models import IpdAdmissionRecord, IpdDoctorWorklist

        # Retrieve all admitted patients lacking a worklist entry
        admissions = await self.db.execute(
            select(IpdAdmissionRecord).where(
                IpdAdmissionRecord.status.in_(
                    ["Admitted", "Pending Acceptance", "Accepted", "Under Observation", "Active"]
                ),
                ~IpdAdmissionRecord.admission_number.in_(
                    select(IpdDoctorWorklist.admission_number)
                ),
            )
        )
        missing_admissions = admissions.scalars().all()
        for adm in missing_admissions:
            wl = IpdDoctorWorklist(
                admission_number=adm.admission_number,
                patient_uhid=adm.patient_uhid,
                doctor_uuid=uuid.uuid4(),  # placeholder for test env
                doctor_name=adm.admitting_doctor or "Unassigned",
                status="Active",
            )
            self.db.add(wl)

        if missing_admissions:
            await self.db.flush()

        res = await self.db.execute(
            select(IpdDoctorWorklist).order_by(IpdDoctorWorklist.assigned_at.desc())
        )
        return res.scalars().all()

    async def get_doctor_coversheet(self, adm_no: str):
        from .models import IpdDoctorCoversheet, IpdAdmissionRecord

        res = await self.db.execute(
            select(IpdDoctorCoversheet).where(IpdDoctorCoversheet.admission_number == adm_no)
        )
        coversheet = res.scalars().first()
        if not coversheet:
            # Create a blank coversheet automatically if it doesn't exist
            adm = await self.db.execute(
                select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
            )
            adm_rec = adm.scalars().first()
            if not adm_rec:
                return None
            coversheet = IpdDoctorCoversheet(
                admission_number=adm_no,
                patient_uhid=adm_rec.patient_uhid,
                primary_diagnosis="Pending Evaluation",
                clinical_summary="",
            )
            self.db.add(coversheet)
            await self.db.flush()
        return coversheet

    async def update_doctor_coversheet(self, adm_no: str, data: dict, user_name: str = "Doctor"):
        coversheet = await self.get_doctor_coversheet(adm_no)
        if not coversheet:
            return None
        for k, v in data.items():
            if hasattr(coversheet, k) and v is not None:
                setattr(coversheet, k, v)
        coversheet.verified_by_doctor = user_name
        coversheet.verified_at = datetime.now(timezone.utc)
        self.db.add(coversheet)
        await self.db.flush()
        return coversheet

    async def get_diagnoses(self, adm_no: str):
        from .models import IpdDiagnosis

        res = await self.db.execute(
            select(IpdDiagnosis)
            .where(IpdDiagnosis.admission_number == adm_no)
            .order_by(IpdDiagnosis.diagnosed_at.desc())
        )
        return res.scalars().all()

    async def add_diagnosis(self, adm_no: str, data: dict, user_name: str = "Doctor"):
        from .models import IpdDiagnosis, IpdAdmissionRecord

        adm_res = await self.db.execute(
            select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
        )
        adm = adm_res.scalars().first()
        if not adm:
            raise ValueError("Admission not found")

        diag = IpdDiagnosis(
            admission_number=adm_no,
            patient_uhid=adm.patient_uhid,
            diagnosed_by_name=user_name,
            **data,
        )
        self.db.add(diag)
        await self.db.flush()
        return diag

    async def get_treatment_plans(self, adm_no: str):
        from .models import IpdTreatmentPlan

        res = await self.db.execute(
            select(IpdTreatmentPlan)
            .where(IpdTreatmentPlan.admission_number == adm_no)
            .order_by(IpdTreatmentPlan.created_at.desc())
        )
        return res.scalars().all()

    async def add_treatment_plan(self, adm_no: str, data: dict, user_name: str = "Doctor"):
        from .models import IpdTreatmentPlan, IpdAdmissionRecord

        adm_res = await self.db.execute(
            select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
        )
        adm = adm_res.scalars().first()
        if not adm:
            raise ValueError("Admission not found")

        plan = IpdTreatmentPlan(
            admission_number=adm_no,
            patient_uhid=adm.patient_uhid,
            created_by_name=user_name,
            **data,
        )
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def get_progress_notes(self, adm_no: str):
        from .models import IpdProgressNote

        res = await self.db.execute(
            select(IpdProgressNote)
            .where(IpdProgressNote.admission_number == adm_no)
            .order_by(IpdProgressNote.recorded_at.desc())
        )
        return res.scalars().all()

    async def add_progress_note(self, adm_no: str, data: dict, user_name: str = "Doctor"):
        from .models import IpdProgressNote

        note = IpdProgressNote(admission_number=adm_no, doctor_name=user_name, **data)
        self.db.add(note)
        await self.db.flush()
        return note

    async def get_clinical_procedures(self, adm_no: str):
        from .models import IpdClinicalProcedure

        res = await self.db.execute(
            select(IpdClinicalProcedure)
            .where(IpdClinicalProcedure.admission_number == adm_no)
            .order_by(IpdClinicalProcedure.procedure_date.desc())
        )
        return res.scalars().all()

    async def add_clinical_procedure(self, adm_no: str, data: dict, user_name: str = "Doctor"):
        from .models import IpdClinicalProcedure

        proc = IpdClinicalProcedure(admission_number=adm_no, performing_doctor=user_name, **data)
        self.db.add(proc)
        await self.db.flush()
        return proc

    async def get_consultation_requests(self, adm_no: str):
        from .models import IpdConsultationRequest

        res = await self.db.execute(
            select(IpdConsultationRequest)
            .where(IpdConsultationRequest.admission_number == adm_no)
            .order_by(IpdConsultationRequest.requested_at.desc())
        )
        return res.scalars().all()

    async def add_consultation_request(self, adm_no: str, data: dict, user_name: str = "Doctor"):
        from .models import IpdConsultationRequest

        req = IpdConsultationRequest(admission_number=adm_no, requested_by=user_name, **data)
        self.db.add(req)
        await self.db.flush()
        return req

    # --- Phase 18: IPD Clinical Orders Management Engine ---

    async def create_lab_order(self, adm_no: str, data: dict, doctor_name: str = "Doctor"):
        from .models import IpdOrdersMaster, IpdLabOrder, IpdOrderStatusLog, IpdAdmissionRecord

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
            )
        ).scalar_one_or_none()
        if not adm:
            return None
        priority = data.pop("priority", "Routine")
        master = IpdOrdersMaster(
            admission_number=adm_no,
            patient_uhid=adm.patient_uhid,
            doctor_name=doctor_name,
            order_type="Laboratory",
            priority=priority,
        )
        self.db.add(master)
        await self.db.flush()
        lab = IpdLabOrder(order_id=master.id, **data)
        self.db.add(lab)
        log = IpdOrderStatusLog(order_id=master.id, new_status="Ordered", updated_by=doctor_name)
        self.db.add(log)
        await self.db.flush()
        return {"order": master, "detail": lab}

    async def create_radiology_order(self, adm_no: str, data: dict, doctor_name: str = "Doctor"):
        from .models import (
            IpdOrdersMaster,
            IpdRadiologyOrder,
            IpdOrderStatusLog,
            IpdAdmissionRecord,
        )

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
            )
        ).scalar_one_or_none()
        if not adm:
            return None
        priority = data.pop("priority", "Routine")
        master = IpdOrdersMaster(
            admission_number=adm_no,
            patient_uhid=adm.patient_uhid,
            doctor_name=doctor_name,
            order_type="Radiology",
            priority=priority,
        )
        self.db.add(master)
        await self.db.flush()
        rad = IpdRadiologyOrder(order_id=master.id, **data)
        self.db.add(rad)
        log = IpdOrderStatusLog(order_id=master.id, new_status="Ordered", updated_by=doctor_name)
        self.db.add(log)
        await self.db.flush()
        return {"order": master, "detail": rad}

    async def create_medication_order(self, adm_no: str, data: dict, doctor_name: str = "Doctor"):
        from .models import (
            IpdOrdersMaster,
            IpdMedicationOrder,
            IpdOrderStatusLog,
            IpdAdmissionRecord,
        )

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
            )
        ).scalar_one_or_none()
        if not adm:
            return None
        priority = data.pop("priority", "Routine")
        master = IpdOrdersMaster(
            admission_number=adm_no,
            patient_uhid=adm.patient_uhid,
            doctor_name=doctor_name,
            order_type="Medication",
            priority=priority,
        )
        self.db.add(master)
        await self.db.flush()
        med = IpdMedicationOrder(order_id=master.id, **data)
        self.db.add(med)
        log = IpdOrderStatusLog(order_id=master.id, new_status="Ordered", updated_by=doctor_name)
        self.db.add(log)
        await self.db.flush()
        return {"order": master, "detail": med}

    async def create_procedure_order(self, adm_no: str, data: dict, doctor_name: str = "Doctor"):
        from .models import (
            IpdOrdersMaster,
            IpdProcedureOrder,
            IpdOrderStatusLog,
            IpdAdmissionRecord,
        )

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
            )
        ).scalar_one_or_none()
        if not adm:
            return None
        priority = data.pop("priority", "Routine")
        master = IpdOrdersMaster(
            admission_number=adm_no,
            patient_uhid=adm.patient_uhid,
            doctor_name=doctor_name,
            order_type="Procedure",
            priority=priority,
        )
        self.db.add(master)
        await self.db.flush()
        proc = IpdProcedureOrder(order_id=master.id, **data)
        self.db.add(proc)
        log = IpdOrderStatusLog(order_id=master.id, new_status="Ordered", updated_by=doctor_name)
        self.db.add(log)
        await self.db.flush()
        return {"order": master, "detail": proc}

    async def get_patient_orders(self, adm_no: str):
        from .models import IpdOrdersMaster

        res = await self.db.execute(
            select(IpdOrdersMaster)
            .where(IpdOrdersMaster.admission_number == adm_no)
            .order_by(IpdOrdersMaster.order_date.desc())
        )
        return res.scalars().all()

    async def get_order_detail(self, order_id):
        from .models import (
            IpdOrdersMaster,
            IpdLabOrder,
            IpdRadiologyOrder,
            IpdMedicationOrder,
            IpdProcedureOrder,
            IpdOrderStatusLog,
        )

        order = (
            await self.db.execute(select(IpdOrdersMaster).where(IpdOrdersMaster.id == order_id))
        ).scalar_one_or_none()
        if not order:
            return None
        lab = (
            await self.db.execute(select(IpdLabOrder).where(IpdLabOrder.order_id == order_id))
        ).scalar_one_or_none()
        rad = (
            await self.db.execute(
                select(IpdRadiologyOrder).where(IpdRadiologyOrder.order_id == order_id)
            )
        ).scalar_one_or_none()
        med = (
            await self.db.execute(
                select(IpdMedicationOrder).where(IpdMedicationOrder.order_id == order_id)
            )
        ).scalar_one_or_none()
        proc = (
            await self.db.execute(
                select(IpdProcedureOrder).where(IpdProcedureOrder.order_id == order_id)
            )
        ).scalar_one_or_none()
        logs = (
            (
                await self.db.execute(
                    select(IpdOrderStatusLog)
                    .where(IpdOrderStatusLog.order_id == order_id)
                    .order_by(IpdOrderStatusLog.updated_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return {
            "order": order,
            "lab_detail": lab,
            "radiology_detail": rad,
            "medication_detail": med,
            "procedure_detail": proc,
            "status_logs": logs,
        }

    async def update_order_status(
        self, order_id, new_status: str, user_name: str = "System", remarks: str = None
    ):
        from .models import IpdOrdersMaster, IpdOrderStatusLog

        order = (
            await self.db.execute(select(IpdOrdersMaster).where(IpdOrdersMaster.id == order_id))
        ).scalar_one_or_none()
        if not order:
            return None
        prev = order.status
        order.status = new_status
        log = IpdOrderStatusLog(
            order_id=order_id,
            previous_status=prev,
            new_status=new_status,
            updated_by=user_name,
            remarks=remarks,
        )
        self.db.add(log)
        await self.db.flush()
        return order

    async def get_nursing_execution_worklist(self):
        from .models import IpdOrdersMaster

        res = await self.db.execute(
            select(IpdOrdersMaster)
            .where(IpdOrdersMaster.status.in_(["Ordered", "Scheduled", "In Progress"]))
            .order_by(IpdOrdersMaster.order_date.desc())
        )
        return res.scalars().all()

    # --- Phase 19: IPD Bed Transfer & Patient Movement Engine ---

    async def create_transfer_request(self, adm_no: str, data: dict, user_name: str = "Doctor"):
        from .models import (
            IpdTransferRequest,
            IpdTransferAuditLog,
            IpdTransferHandover,
            IpdAdmissionRecord,
        )

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(IpdAdmissionRecord.admission_number == adm_no)
            )
        ).scalar_one_or_none()
        if not adm:
            return None

        handover_data = data.pop("handover", None)

        req = IpdTransferRequest(
            admission_number=adm_no, patient_uhid=adm.patient_uhid, requested_by=user_name, **data
        )
        self.db.add(req)
        await self.db.flush()

        if handover_data:
            ho = IpdTransferHandover(
                transfer_request_id=req.id,
                admission_number=adm_no,
                documented_by=user_name,
                **handover_data,
            )
            self.db.add(ho)

        log = IpdTransferAuditLog(
            transfer_request_id=req.id,
            action="Created",
            performed_by=user_name,
            details=f"Transfer requested to {req.requested_ward}",
        )
        self.db.add(log)
        await self.db.flush()

        return req

    async def get_transfer_requests(self, ward: str = None):
        from .models import IpdTransferRequest

        query = select(IpdTransferRequest).order_by(IpdTransferRequest.requested_at.desc())
        if ward:
            # Get requests either from or to this ward
            query = query.where(
                (IpdTransferRequest.current_ward == ward)
                | (IpdTransferRequest.requested_ward == ward)
            )
        res = await self.db.execute(query)
        return res.scalars().all()

    async def get_transfer_request_detail(self, req_id):
        from .models import IpdTransferRequest, IpdTransferHandover, IpdTransferAuditLog

        req = (
            await self.db.execute(select(IpdTransferRequest).where(IpdTransferRequest.id == req_id))
        ).scalar_one_or_none()
        if not req:
            return None
        handover = (
            await self.db.execute(
                select(IpdTransferHandover).where(IpdTransferHandover.transfer_request_id == req_id)
            )
        ).scalar_one_or_none()
        logs = (
            (
                await self.db.execute(
                    select(IpdTransferAuditLog)
                    .where(IpdTransferAuditLog.transfer_request_id == req_id)
                    .order_by(IpdTransferAuditLog.performed_at.desc())
                )
            )
            .scalars()
            .all()
        )

        req_dict = {c.name: getattr(req, c.name) for c in req.__table__.columns}
        req_dict["handover"] = handover
        req_dict["audit_logs"] = logs
        return req_dict

    async def approve_transfer_request(
        self, req_id: str, approved_bed: str, user_name: str, remarks: str = None
    ):
        from .models import (
            IpdTransferRequest,
            IpdTransferAuditLog,
            IpdTransferRecord,
            IpdBedMovement,
            IpdAdmissionRecord,
        )

        req = (
            await self.db.execute(select(IpdTransferRequest).where(IpdTransferRequest.id == req_id))
        ).scalar_one_or_none()
        if not req or req.status != "Pending":
            return None

        req.status = "Approved"

        # Create transfer record
        record = IpdTransferRecord(
            transfer_request_id=req.id,
            admission_number=req.admission_number,
            patient_uhid=req.patient_uhid,
            from_ward=req.current_ward,
            from_bed=req.current_bed,
            to_ward=req.requested_ward,
            to_bed=approved_bed,
            transfer_type=req.transfer_type,
            approved_by=user_name,
        )
        self.db.add(record)

        # Create bed movement
        movement = IpdBedMovement(
            admission_number=req.admission_number,
            patient_uhid=req.patient_uhid,
            previous_ward=req.current_ward,
            previous_bed=req.current_bed,
            new_ward=req.requested_ward,
            new_bed=approved_bed,
            movement_reason=req.reason,
            recorded_by=user_name,
        )
        self.db.add(movement)

        # Update admission record
        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == req.admission_number
                )
            )
        ).scalar_one_or_none()
        if adm:
            adm.ward_id = req.requested_ward
            adm.bed_number = approved_bed

        log = IpdTransferAuditLog(
            transfer_request_id=req.id,
            action="Approved",
            performed_by=user_name,
            details=f"Approved to bed {approved_bed}. Remarks: {remarks}",
        )
        self.db.add(log)
        await self.db.flush()
        return req

    async def reject_transfer_request(self, req_id: str, user_name: str, remarks: str = None):
        from .models import IpdTransferRequest, IpdTransferAuditLog

        req = (
            await self.db.execute(select(IpdTransferRequest).where(IpdTransferRequest.id == req_id))
        ).scalar_one_or_none()
        if not req or req.status != "Pending":
            return None

        req.status = "Rejected"
        log = IpdTransferAuditLog(
            transfer_request_id=req.id,
            action="Rejected",
            performed_by=user_name,
            details=f"Remarks: {remarks}",
        )
        self.db.add(log)
        await self.db.flush()
        return req

    # --- Phase 20: IPD Smart Discharge Planning Engine ---

    async def get_or_create_discharge_state(self, admission_number: str):
        from .models import (
            IpdAdmissionRecord,
            IpdDischargePlan,
            IpdDischargeChecklist,
            IpdDischargeSummary,
        )

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not adm:
            return None

        plan = (
            await self.db.execute(
                select(IpdDischargePlan).where(
                    IpdDischargePlan.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not plan:
            plan = IpdDischargePlan(
                admission_number=adm.admission_number,
                patient_uhid=adm.patient_uhid,
                doctor_uuid=adm.admitting_doctor,
            )
            self.db.add(plan)

        checklist = (
            await self.db.execute(
                select(IpdDischargeChecklist).where(
                    IpdDischargeChecklist.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not checklist:
            checklist = IpdDischargeChecklist(
                admission_number=adm.admission_number, patient_uhid=adm.patient_uhid
            )
            self.db.add(checklist)

        summary = (
            await self.db.execute(
                select(IpdDischargeSummary).where(
                    IpdDischargeSummary.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not summary:
            summary = IpdDischargeSummary(
                admission_number=adm.admission_number,
                patient_uhid=adm.patient_uhid,
                doctor_uuid=adm.admitting_doctor,
            )
            self.db.add(summary)

        await self.db.flush()
        return {"plan": plan, "checklist": checklist, "summary": summary}

    async def update_discharge_plan(self, admission_number: str, data: dict, user_name: str):
        from .models import IpdDischargePlan, IpdDischargeAuditLog

        state = await self.get_or_create_discharge_state(admission_number)
        if not state:
            return None
        plan = state["plan"]

        if "planned_discharge_date" in data and data["planned_discharge_date"]:
            plan.planned_discharge_date = data["planned_discharge_date"]
            if plan.status == "Planned":
                plan.status = "In Progress"

        log = IpdDischargeAuditLog(
            admission_number=admission_number,
            action="Plan Updated",
            performed_by=user_name,
            details=f"Planned discharge date updated: {plan.planned_discharge_date}",
        )
        self.db.add(log)
        await self.db.flush()
        return plan

    async def update_discharge_checklist(self, admission_number: str, data: dict, user_name: str):
        from .models import IpdDischargeChecklist, IpdDischargeAuditLog

        state = await self.get_or_create_discharge_state(admission_number)
        if not state:
            return None
        checklist = state["checklist"]

        details = []
        for field, val in data.items():
            if val is not None and hasattr(checklist, field):
                setattr(checklist, field, val)
                details.append(f"{field}={val}")

        checklist.updated_at = datetime.now(timezone.utc)

        if details:
            log = IpdDischargeAuditLog(
                admission_number=admission_number,
                action="Checklist Updated",
                performed_by=user_name,
                details=", ".join(details),
            )
            self.db.add(log)
            await self.db.flush()
        return checklist

    async def generate_discharge_summary(self, admission_number: str, user_name: str):
        from .models import IpdDischargeSummary, IpdOrdersMaster, IpdDiagnosis, IpdDischargeAuditLog

        state = await self.get_or_create_discharge_state(admission_number)
        if not state:
            return None
        summary = state["summary"]

        # Aggregate diagnoses
        diagnoses_records = (
            (
                await self.db.execute(
                    select(IpdDiagnosis).where(IpdDiagnosis.admission_number == admission_number)
                )
            )
            .scalars()
            .all()
        )
        diag_text = (
            ", ".join([d.diagnosis_name for d in diagnoses_records])
            if diagnoses_records
            else "Admitting Diagnosis"
        )

        # Aggregate completed procedures
        procedures_records = (
            (
                await self.db.execute(
                    select(IpdOrdersMaster).where(
                        IpdOrdersMaster.admission_number == admission_number,
                        IpdOrdersMaster.order_type == "Procedure",
                        IpdOrdersMaster.status == "Completed",
                    )
                )
            )
            .scalars()
            .all()
        )
        proc_text = (
            ", ".join([p.priority for p in procedures_records])
            if procedures_records
            else "None recorded"
        )

        summary.admission_diagnosis = diag_text
        summary.procedures_performed = proc_text
        summary.hospital_course = "Patient admitted and treated accordingly."
        summary.follow_up_instructions = "Follow up in OPD after 7 days."

        log = IpdDischargeAuditLog(
            admission_number=admission_number,
            action="Summary Auto-Generated",
            performed_by=user_name,
            details="Generated from patient records",
        )
        self.db.add(log)
        await self.db.flush()
        return summary

    async def update_discharge_summary(self, admission_number: str, data: dict, user_name: str):
        from .models import IpdDischargeSummary, IpdDischargeAuditLog

        state = await self.get_or_create_discharge_state(admission_number)
        if not state:
            return None
        summary = state["summary"]

        for field, val in data.items():
            if val is not None and hasattr(summary, field):
                setattr(summary, field, val)

        log = IpdDischargeAuditLog(
            admission_number=admission_number,
            action="Summary Updated",
            performed_by=user_name,
            details="Manual updates applied",
        )
        self.db.add(log)
        await self.db.flush()
        return summary

    async def validate_pending_orders(self, admission_number: str):
        from .models import IpdOrdersMaster

        orders = (
            (
                await self.db.execute(
                    select(IpdOrdersMaster).where(
                        IpdOrdersMaster.admission_number == admission_number,
                        IpdOrdersMaster.status.in_(["Prescribed", "In Progress", "Pending"]),
                    )
                )
            )
            .scalars()
            .all()
        )
        return orders

    async def finalize_discharge(self, admission_number: str, user_name: str):
        from .models import (
            IpdAdmissionRecord,
            IpdDischargePlan,
            IpdDischargeChecklist,
            IpdDischargeAuditLog,
        )
        from app.core.wards.models import Bed

        state = await self.get_or_create_discharge_state(admission_number)
        if not state:
            raise ValueError("Admission not found")

        checklist = state["checklist"]
        if not (
            checklist.doctor_approval
            and checklist.nursing_clearance
            and checklist.billing_clearance
        ):
            raise ValueError(
                "All clearances (Doctor, Nursing, Billing) must be approved to discharge."
            )

        pending_orders = await self.validate_pending_orders(admission_number)
        if pending_orders:
            raise ValueError(f"Cannot discharge: {len(pending_orders)} pending orders exist.")

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        adm.status = "Discharged"

        bed = (
            await self.db.execute(select(Bed).where(Bed.id == adm.bed_uuid))
        ).scalar_one_or_none()
        if bed:
            bed.status = "cleaning"

        plan = state["plan"]
        plan.status = "Discharged"

        summary = state["summary"]
        summary.status = "Finalized"
        summary.finalized_at = datetime.now(timezone.utc)

        log = IpdDischargeAuditLog(
            admission_number=admission_number,
            action="Discharge Finalized",
            performed_by=user_name,
            details="Patient physically discharged and bed freed.",
        )
        self.db.add(log)
        await self.db.flush()
        return True

    # --- Phase 21: IPD Billing & Payment Settlement Engine ---

    async def get_or_create_billing(self, admission_number: str):
        from .models import IpdAdmissionRecord, IpdBillingMaster

        billing = (
            await self.db.execute(
                select(IpdBillingMaster).where(
                    IpdBillingMaster.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if billing:
            return billing
        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not adm:
            return None

        patient_name = "Patient " + adm.patient_uhid
        if adm.request_id:
            from .models import IpdAdmissionRequest

            req = (
                await self.db.execute(
                    select(IpdAdmissionRequest).where(IpdAdmissionRequest.id == adm.request_id)
                )
            ).scalar_one_or_none()
            if req and req.patient_name:
                patient_name = req.patient_name

        billing = IpdBillingMaster(
            admission_number=adm.admission_number,
            patient_uhid=adm.patient_uhid,
            patient_name=patient_name,
            ward_name="IPD Ward",
            bed_code=str(adm.bed_uuid) if adm.bed_uuid else None,
            org_id=adm.org_id,
        )
        self.db.add(billing)
        await self.db.flush()
        return billing

    async def recalculate_billing(self, admission_number: str):
        from .models import (
            IpdBillingMaster,
            IpdBillingService,
            IpdBillingDeposit,
            IpdPaymentTransaction,
            IpdInsuranceClaim,
        )

        billing = await self.get_or_create_billing(admission_number)
        if not billing:
            return None
        services = (
            (
                await self.db.execute(
                    select(IpdBillingService).where(
                        IpdBillingService.admission_number == admission_number
                    )
                )
            )
            .scalars()
            .all()
        )
        billing.total_charges = sum(s.total_price for s in services)
        deposits = (
            (
                await self.db.execute(
                    select(IpdBillingDeposit).where(
                        IpdBillingDeposit.admission_number == admission_number,
                        IpdBillingDeposit.status == "Collected",
                    )
                )
            )
            .scalars()
            .all()
        )
        billing.total_deposits = sum(d.amount for d in deposits)
        payments = (
            (
                await self.db.execute(
                    select(IpdPaymentTransaction).where(
                        IpdPaymentTransaction.admission_number == admission_number,
                        IpdPaymentTransaction.payment_type != "Refund",
                    )
                )
            )
            .scalars()
            .all()
        )
        billing.total_paid = sum(p.amount for p in payments)
        claims = (
            (
                await self.db.execute(
                    select(IpdInsuranceClaim).where(
                        IpdInsuranceClaim.admission_number == admission_number,
                        IpdInsuranceClaim.status == "Approved",
                    )
                )
            )
            .scalars()
            .all()
        )
        billing.insurance_payable = sum(c.approved_amount for c in claims)
        billing.patient_payable = (
            billing.total_charges - billing.insurance_payable - billing.total_discount
        )
        billing.outstanding_balance = (
            billing.patient_payable - billing.total_paid - billing.total_deposits
        )
        billing.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return billing

    async def get_billing_services(self, admission_number: str):
        from .models import IpdBillingService

        return (
            (
                await self.db.execute(
                    select(IpdBillingService)
                    .where(IpdBillingService.admission_number == admission_number)
                    .order_by(IpdBillingService.service_date.desc())
                )
            )
            .scalars()
            .all()
        )

    async def add_billing_service(self, admission_number: str, data: dict, user_name: str):
        from .models import IpdBillingService, IpdBillingAuditLog, IpdAdmissionRecord

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not adm:
            return None
        qty = data.get("quantity", 1)
        unit_price = data["unit_price"]
        svc = IpdBillingService(
            admission_number=admission_number,
            service_category=data["service_category"],
            service_name=data["service_name"],
            quantity=qty,
            unit_price=unit_price,
            total_price=round(qty * unit_price, 2),
            notes=data.get("notes"),
        )
        self.db.add(svc)
        log = IpdBillingAuditLog(
            admission_number=admission_number,
            action="Service Added",
            performed_by=user_name,
            details=f"{data['service_name']} ₹{svc.total_price}",
        )
        self.db.add(log)
        await self.db.flush()
        await self.recalculate_billing(admission_number)
        return svc

    async def add_deposit(self, admission_number: str, data: dict, user_name: str):
        from .models import IpdBillingDeposit, IpdBillingAuditLog, IpdAdmissionRecord
        import random, string

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not adm:
            return None
        receipt = "DEP-" + "".join(random.choices(string.digits, k=8))
        dep = IpdBillingDeposit(
            admission_number=admission_number,
            patient_uhid=adm.patient_uhid,
            amount=data["amount"],
            payment_mode=data["payment_mode"],
            receipt_number=receipt,
            reference_number=data.get("reference_number"),
            collected_by=user_name,
        )
        self.db.add(dep)
        log = IpdBillingAuditLog(
            admission_number=admission_number,
            action="Deposit Collected",
            performed_by=user_name,
            details=f"₹{data['amount']} via {data['payment_mode']}",
        )
        self.db.add(log)
        await self.db.flush()
        await self.recalculate_billing(admission_number)
        return dep

    async def get_deposits(self, admission_number: str):
        from .models import IpdBillingDeposit

        return (
            (
                await self.db.execute(
                    select(IpdBillingDeposit)
                    .where(IpdBillingDeposit.admission_number == admission_number)
                    .order_by(IpdBillingDeposit.deposit_date.desc())
                )
            )
            .scalars()
            .all()
        )

    async def add_insurance_claim(self, admission_number: str, data: dict, user_name: str):
        from .models import IpdInsuranceClaim, IpdBillingAuditLog, IpdAdmissionRecord

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not adm:
            return None
        claim = IpdInsuranceClaim(
            admission_number=admission_number,
            patient_uhid=adm.patient_uhid,
            insurance_provider=data["insurance_provider"],
            policy_number=data["policy_number"],
            pre_auth_number=data.get("pre_auth_number"),
            coverage_limit=data.get("coverage_limit", 0),
            claimed_amount=data.get("claimed_amount", 0),
        )
        self.db.add(claim)
        log = IpdBillingAuditLog(
            admission_number=admission_number,
            action="Insurance Claim Created",
            performed_by=user_name,
            details=f"{data['insurance_provider']} - ₹{data.get('claimed_amount', 0)}",
        )
        self.db.add(log)
        await self.db.flush()
        return claim

    async def get_insurance_claims(self, admission_number: str):
        from .models import IpdInsuranceClaim

        return (
            (
                await self.db.execute(
                    select(IpdInsuranceClaim).where(
                        IpdInsuranceClaim.admission_number == admission_number
                    )
                )
            )
            .scalars()
            .all()
        )

    async def process_insurance_claim(self, claim_id: str, data: dict, user_name: str):
        from .models import IpdInsuranceClaim, IpdBillingAuditLog
        from datetime import datetime, timezone

        claim = (
            await self.db.execute(
                select(IpdInsuranceClaim).where(
                    IpdInsuranceClaim.id == claim_id
                )
            )
        ).scalar_one_or_none()
        if not claim:
            return None

        claim.approved_amount = data.get("approved_amount", 0)
        claim.patient_share = data.get("patient_share", 0)
        claim.status = data.get("status", "Approved")
        claim.updated_at = datetime.now(timezone.utc)

        log = IpdBillingAuditLog(
            admission_number=claim.admission_number,
            action=f"Insurance Claim {claim.status}",
            performed_by=user_name,
            details=f"Provider: {claim.insurance_provider}, Approved: ₹{claim.approved_amount}, Share: ₹{claim.patient_share}",
        )
        self.db.add(log)
        await self.db.flush()
        await self.recalculate_billing(claim.admission_number)
        return claim

    async def process_payment(self, admission_number: str, data: dict, user_name: str):
        from .models import IpdPaymentTransaction, IpdBillingAuditLog, IpdAdmissionRecord
        import random, string

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not adm:
            return None
        receipt = "PAY-" + "".join(random.choices(string.digits, k=8))
        txn = IpdPaymentTransaction(
            admission_number=admission_number,
            patient_uhid=adm.patient_uhid,
            amount=data["amount"],
            payment_mode=data["payment_mode"],
            reference_number=data.get("reference_number"),
            receipt_number=receipt,
            processed_by=user_name,
        )
        self.db.add(txn)
        log = IpdBillingAuditLog(
            admission_number=admission_number,
            action="Payment Received",
            performed_by=user_name,
            details=f"₹{data['amount']} via {data['payment_mode']}",
        )
        self.db.add(log)
        await self.db.flush()
        await self.recalculate_billing(admission_number)
        return txn

    async def get_payments(self, admission_number: str):
        from .models import IpdPaymentTransaction

        return (
            (
                await self.db.execute(
                    select(IpdPaymentTransaction)
                    .where(IpdPaymentTransaction.admission_number == admission_number)
                    .order_by(IpdPaymentTransaction.payment_date.desc())
                )
            )
            .scalars()
            .all()
        )

    async def get_billing_dashboard(self):
        from .models import IpdBillingMaster, IpdAdmissionRecord

        # Ensure billing masters exist for all active admissions
        active_adms = (
            (
                await self.db.execute(
                    select(IpdAdmissionRecord).where(IpdAdmissionRecord.status != "Discharged")
                )
            )
            .scalars()
            .all()
        )
        for adm in active_adms:
            await self.get_or_create_billing(adm.admission_number)

        return (
            (
                await self.db.execute(
                    select(IpdBillingMaster).order_by(IpdBillingMaster.updated_at.desc())
                )
            )
            .scalars()
            .all()
        )

    async def get_patient_active_insurance(self, admission_number: str):
        from .models import IpdAdmissionRecord

        try:
            from app.core.patients.patients.models import Patient
            from app.core.patients.insurance.models import PatientInsurance
        except ImportError:
            return []

        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == admission_number
                )
            )
        ).scalar_one_or_none()
        if not adm:
            return []

        patient = (
            await self.db.execute(select(Patient).where(Patient.patient_uuid == adm.patient_uhid))
        ).scalar_one_or_none()
        if not patient:
            return []

        insurances = (
            (
                await self.db.execute(
                    select(PatientInsurance).where(PatientInsurance.patient_id == patient.id)
                )
            )
            .scalars()
            .all()
        )
        return [
            {"provider": i.insurance_provider, "policy": i.policy_number, "type": i.coverage_type}
            for i in insurances
        ]

    # ─── Phase 22: Visitor Management & MLC Handling ────────────────

    async def register_visitor(self, data: dict):
        from .models import IpdVisitor

        visitor = IpdVisitor(**data)
        self.db.add(visitor)
        await self.db.flush()
        return visitor

    async def get_visitors(self, admission_number: str):
        from .models import IpdVisitor

        return (
            (
                await self.db.execute(
                    select(IpdVisitor)
                    .where(IpdVisitor.admission_number == admission_number)
                    .order_by(IpdVisitor.registered_at.desc())
                )
            )
            .scalars()
            .all()
        )

    async def generate_visitor_pass(self, data: dict):
        from .models import IpdVisitorPass
        import random

        year = datetime.now(timezone.utc).strftime("%Y")
        seq = random.randint(10000, 99999)
        pass_number = f"VIS-{year}-{seq}"
        vp = IpdVisitorPass(pass_number=pass_number, **data)
        self.db.add(vp)
        await self.db.flush()
        return vp

    async def get_visitor_passes(self, admission_number: str):
        from .models import IpdVisitorPass

        return (
            (
                await self.db.execute(
                    select(IpdVisitorPass)
                    .where(IpdVisitorPass.admission_number == admission_number)
                    .order_by(IpdVisitorPass.created_at.desc())
                )
            )
            .scalars()
            .all()
        )

    async def log_visitor_entry(self, data: dict):
        from .models import IpdVisitorLog

        log = IpdVisitorLog(**data)
        self.db.add(log)
        await self.db.flush()
        return log

    async def log_visitor_exit(self, log_id: str):
        from .models import IpdVisitorLog

        log = (
            await self.db.execute(select(IpdVisitorLog).where(IpdVisitorLog.id == log_id))
        ).scalar_one_or_none()
        if log:
            log.exit_time = datetime.now(timezone.utc)
            await self.db.flush()
        return log

    async def get_visitor_logs(self, pass_number: str):
        from .models import IpdVisitorLog

        return (
            (
                await self.db.execute(
                    select(IpdVisitorLog)
                    .where(IpdVisitorLog.pass_number == pass_number)
                    .order_by(IpdVisitorLog.entry_time.desc())
                )
            )
            .scalars()
            .all()
        )

    async def register_mlc_case(self, data: dict):
        from .models import IpdMlcCase, IpdSecurityNotification, IpdAdmissionRecord

        mlc = IpdMlcCase(**data)
        self.db.add(mlc)
        await self.db.flush()
        # Auto-create security notification
        adm = (
            await self.db.execute(
                select(IpdAdmissionRecord).where(
                    IpdAdmissionRecord.admission_number == data["admission_number"]
                )
            )
        ).scalar_one_or_none()
        ward_info = "Unknown Ward"
        notif = IpdSecurityNotification(
            admission_number=data["admission_number"],
            notification_type="MLC Alert",
            message=f"Medico-Legal Case registered: {data['case_type']} for patient {data['patient_uhid']} in {ward_info}. Adm: {data['admission_number']}",
        )
        self.db.add(notif)
        await self.db.flush()
        return mlc

    async def get_mlc_case(self, admission_number: str):
        from .models import IpdMlcCase

        return (
            await self.db.execute(
                select(IpdMlcCase).where(IpdMlcCase.admission_number == admission_number)
            )
        ).scalar_one_or_none()

    async def get_all_mlc_cases(self):
        from .models import IpdMlcCase

        return (
            (await self.db.execute(select(IpdMlcCase).order_by(IpdMlcCase.registered_at.desc())))
            .scalars()
            .all()
        )

    async def update_mlc_case(self, admission_number: str, data: dict):
        from .models import IpdMlcCase

        mlc = (
            await self.db.execute(
                select(IpdMlcCase).where(IpdMlcCase.admission_number == admission_number)
            )
        ).scalar_one_or_none()
        if mlc:
            for k, v in data.items():
                if v is not None:
                    setattr(mlc, k, v)
            await self.db.flush()
        return mlc

    async def add_mlc_document(self, data: dict):
        from .models import IpdMlcDocument

        doc = IpdMlcDocument(**data)
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def get_mlc_documents(self, mlc_id: str):
        from .models import IpdMlcDocument

        return (
            (
                await self.db.execute(
                    select(IpdMlcDocument)
                    .where(IpdMlcDocument.mlc_id == mlc_id)
                    .order_by(IpdMlcDocument.uploaded_at.desc())
                )
            )
            .scalars()
            .all()
        )

    async def get_security_notifications(self, read_filter: str = None):
        from .models import IpdSecurityNotification

        q = select(IpdSecurityNotification).order_by(IpdSecurityNotification.created_at.desc())
        if read_filter == "unread":
            q = q.where(IpdSecurityNotification.is_read == False)
        return (await self.db.execute(q)).scalars().all()

    async def mark_notification_read(self, notif_id: str):
        from .models import IpdSecurityNotification

        notif = (
            await self.db.execute(
                select(IpdSecurityNotification).where(IpdSecurityNotification.id == notif_id)
            )
        ).scalar_one_or_none()
        if notif:
            notif.is_read = True
            await self.db.flush()
        return notif
