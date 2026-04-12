"""
ER Module — Service Layer
===========================
Business logic for ER workflows. Interconnected with:
- billing_masters.PricingEngine → for ER billing
- ipd.services → for ER-to-IPD admission transfer
- orders → for lab/radiology/medication ordering
- pharmacy → for medication dispensing
- patients → for patient registration linkage
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import EREncounter, ERTriage, ERBed, ERMlcCase, ERNursingScore, EROrder
from .schemas import (
    ERRegistrationCreate, ERTriageCreate, ERBedAssignRequest,
    ERMlcCreate, ERNursingScoreCreate, EROrderCreate, ERStatusUpdate,
    ERDashboardStats
)
from app.core.integration.services import ChargePostingService
from app.core.integration.schemas import ChargePostingCreate


def _now():
    return datetime.now(timezone.utc)

def _gen_er_number() -> str:
    ts = _now().strftime("%Y%m%d%H%M%S")
    short = str(uuid.uuid4())[:4].upper()
    return f"ER-{ts}-{short}"

TRIAGE_COLORS = {
    "resuscitation": "red", "emergent": "orange", "urgent": "yellow",
    "less_urgent": "green", "non_urgent": "blue", "dead": "black"
}


class ERRegistrationService:
    """ER patient registration — urgent (minimal) or normal (full UHID)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_patient(self, data: ERRegistrationCreate, org_id: uuid.UUID) -> EREncounter:
        from app.core.patients.patients.models import Patient
        from datetime import date
        
        patient_id = data.patient_id
        
        if not patient_id:
            # Create a temporary core Patient record so this patient shows up in RCM / Clinical Workspace
            names = (data.patient_name or "Unknown Patient").split(" ", 1)
            fname = names[0]
            lname = names[1] if len(names) > 1 else ""
            
            dob_year = _now().year - (int(data.age) if data.age else 30)
            p = Patient(
                first_name=fname,
                last_name=lname,
                date_of_birth=date(dob_year, 1, 1),
                gender=data.gender or "unknown",
                primary_phone=data.mobile,
                status="active",
                patient_uuid=str(uuid.uuid4())
            )
            self.db.add(p)
            await self.db.flush()
            patient_id = p.id

        encounter = EREncounter(
            org_id=org_id,
            er_number=_gen_er_number(),
            registration_type=data.registration_type,
            patient_id=patient_id,
            patient_name=data.patient_name,
            patient_uhid=data.patient_uhid,
            age=data.age,
            age_unit=data.age_unit,
            gender=data.gender,
            mobile=data.mobile,
            temp_id_description=data.temp_id_description,
            mode_of_arrival=data.mode_of_arrival,
            ambulance_number=data.ambulance_number,
            brought_by=data.brought_by,
            referral_source=data.referral_source,
            chief_complaint=data.chief_complaint,
            presenting_complaints=data.presenting_complaints,
            is_allergy=bool(data.allergy_details),
            allergy_details=data.allergy_details,
            status="registered",
        )
        self.db.add(encounter)
        await self.db.commit()
        await self.db.refresh(encounter)

        try:
            cp_service = ChargePostingService(self.db)
            await cp_service.post_charge(
                data=ChargePostingCreate(
                    patient_id=encounter.patient_id,
                    encounter_type="er",
                    encounter_id=encounter.id,
                    service_name="ER Registration Fee",
                    service_code="ER-REG-01",
                    service_group="consultation",
                    source_module="er",
                    quantity=1,
                    unit_price=Decimal("200.00"),
                    is_stat=True
                ),
                posted_by=uuid.UUID(int=1),
                posted_by_name="System",
                org_id=org_id or uuid.UUID(int=0)
            )
        except Exception as e:
            print("Failed to post charge:", e)
            await self.db.rollback()

        return encounter

    async def list_encounters(self, org_id: uuid.UUID, status: str = None, zone: str = None) -> List[EREncounter]:
        stmt = select(EREncounter).where(EREncounter.org_id == org_id)
        if status:
            stmt = stmt.where(EREncounter.status == status)
        if zone:
            stmt = stmt.where(EREncounter.zone == zone)
        # Exclude discharged by default unless explicitly requested
        if not status:
            stmt = stmt.where(EREncounter.status.notin_(["discharged", "transferred_to_ipd"]))
        stmt = stmt.order_by(EREncounter.arrival_time.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_encounter(self, encounter_id: uuid.UUID, org_id: uuid.UUID) -> EREncounter:
        enc = (await self.db.execute(
            select(EREncounter).where(EREncounter.id == encounter_id, EREncounter.org_id == org_id)
        )).scalars().first()
        if not enc:
            raise ValueError("ER encounter not found")
        return enc

    async def update_status(self, encounter_id: uuid.UUID, update: ERStatusUpdate, org_id: uuid.UUID) -> EREncounter:
        enc = await self.get_encounter(encounter_id, org_id)
        
        try:
            if update.status == "in_treatment" and enc.status != "in_treatment":
                cp_service = ChargePostingService(self.db)
                await cp_service.post_charge(
                    data=ChargePostingCreate(
                        patient_id=enc.patient_id,
                        encounter_type="er",
                        encounter_id=enc.id,
                        service_name="ER Treatment & Monitoring Fee",
                        service_code="ER-TX-01",
                        service_group="consultation",
                        source_module="er",
                        quantity=1,
                        unit_price=Decimal("1500.00"),
                        is_stat=True
                    ),
                    posted_by=uuid.UUID(int=1),
                    posted_by_name="System",
                    org_id=org_id
                )
        except Exception:
            pass
            
        enc.status = update.status
        if update.disposition:
            enc.disposition = update.disposition
        if update.disposition_department:
            enc.disposition_department = update.disposition_department
        if update.attending_doctor_name:
            enc.attending_doctor_name = update.attending_doctor_name
        if update.status == "discharged":
            enc.discharge_time = _now()
        enc.updated_at = _now()
        await self.db.commit()
        await self.db.refresh(enc)
        return enc


class ERTriageService:
    """ESI-based triage assessment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess_triage(self, data: ERTriageCreate, triaged_by: uuid.UUID, triaged_by_name: str, org_id: uuid.UUID) -> ERTriage:
        triage = ERTriage(
            org_id=org_id,
            er_encounter_id=data.er_encounter_id,
            triage_category=data.triage_category,
            triage_color=TRIAGE_COLORS.get(data.triage_category, "white"),
            temperature=data.temperature,
            pulse=data.pulse,
            bp_systolic=data.bp_systolic,
            bp_diastolic=data.bp_diastolic,
            respiratory_rate=data.respiratory_rate,
            spo2=data.spo2,
            gcs_score=data.gcs_score,
            pain_score=data.pain_score,
            blood_glucose=data.blood_glucose,
            airway=data.airway,
            breathing=data.breathing,
            circulation=data.circulation,
            disability=data.disability,
            exposure=data.exposure,
            allergies=data.allergies,
            current_medications=data.current_medications,
            past_medical_history=data.past_medical_history,
            last_meal=data.last_meal,
            triage_notes=data.triage_notes,
            triaged_by=triaged_by,
            triaged_by_name=triaged_by_name,
        )
        self.db.add(triage)

        # Update encounter status + priority + zone assignment
        enc = (await self.db.execute(
            select(EREncounter).where(EREncounter.id == data.er_encounter_id)
        )).scalars().first()
        if enc:
            enc.status = "triaged"
            enc.priority = data.triage_category
            enc.triage_time = _now()
            enc.is_critical = data.triage_category in ["resuscitation", "emergent"]
            # Auto-assign zone
            if data.triage_category == "resuscitation":
                enc.zone = "red"
            elif data.triage_category in ["emergent", "urgent"]:
                enc.zone = "yellow"
            else:
                enc.zone = "green"
            if data.allergies:
                enc.is_allergy = True
                enc.allergy_details = data.allergies

        await self.db.commit()
        await self.db.refresh(triage)
        
        try:
            if enc:
                cp_service = ChargePostingService(self.db)
                await cp_service.post_charge(
                    data=ChargePostingCreate(
                        patient_id=enc.patient_id,
                        encounter_type="er",
                        encounter_id=enc.id,
                        service_name=f"Triage Assessment - {data.triage_category.upper()}",
                        service_code="ER-TRIAGE",
                        service_group="consultation",
                        source_module="er",
                        quantity=1,
                        unit_price=Decimal("500.00") if data.triage_category in ["resuscitation", "emergent"] else Decimal("300.00"),
                        is_stat=True
                    ),
                    posted_by=triaged_by,
                    posted_by_name=triaged_by_name,
                    org_id=org_id
                )
        except Exception:
            pass

        return triage

    async def get_triage(self, er_encounter_id: uuid.UUID, org_id: uuid.UUID) -> Optional[ERTriage]:
        return (await self.db.execute(
            select(ERTriage).where(ERTriage.er_encounter_id == er_encounter_id, ERTriage.org_id == org_id)
        )).scalars().first()


class ERBedService:
    """Zone-based ER bed management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_bed(self, bed_code: str, zone: str, bed_type: str, org_id: uuid.UUID, **kwargs) -> ERBed:
        bed = ERBed(org_id=org_id, bed_code=bed_code, zone=zone, bed_type=bed_type, **kwargs)
        self.db.add(bed)
        await self.db.commit()
        await self.db.refresh(bed)
        return bed

    async def list_beds(self, org_id: uuid.UUID, zone: str = None) -> List[ERBed]:
        stmt = select(ERBed).where(ERBed.org_id == org_id, ERBed.is_active == True)
        if zone:
            stmt = stmt.where(ERBed.zone == zone)
        return list((await self.db.execute(stmt)).scalars().all())

    async def assign_bed(self, data: ERBedAssignRequest, org_id: uuid.UUID) -> ERBed:
        bed = (await self.db.execute(
            select(ERBed).where(ERBed.id == data.bed_id, ERBed.org_id == org_id)
        )).scalars().first()
        if not bed:
            raise ValueError("ER bed not found")
        if bed.status != "available":
            raise ValueError(f"Bed {bed.bed_code} is not available (status: {bed.status})")

        # Get encounter for gender coloring
        enc = (await self.db.execute(
            select(EREncounter).where(EREncounter.id == data.er_encounter_id)
        )).scalars().first()

        bed.status = "occupied"
        bed.occupied_by_er_encounter_id = data.er_encounter_id
        bed.occupied_since = _now()
        if enc:
            bed.patient_gender = enc.gender
            enc.zone = bed.zone
            enc.status = "in_treatment"
            enc.treatment_start_time = _now()

        await self.db.commit()
        await self.db.refresh(bed)
        return bed

    async def vacate_bed(self, bed_id: uuid.UUID, org_id: uuid.UUID) -> ERBed:
        bed = (await self.db.execute(
            select(ERBed).where(ERBed.id == bed_id, ERBed.org_id == org_id)
        )).scalars().first()
        if not bed:
            raise ValueError("Bed not found")
        bed.status = "cleaning"
        bed.occupied_by_er_encounter_id = None
        bed.patient_gender = None
        bed.occupied_since = None
        await self.db.commit()
        await self.db.refresh(bed)
        return bed

    async def mark_cleaned(self, bed_id: uuid.UUID, org_id: uuid.UUID) -> ERBed:
        bed = (await self.db.execute(
            select(ERBed).where(ERBed.id == bed_id, ERBed.org_id == org_id)
        )).scalars().first()
        if not bed:
            raise ValueError("Bed not found")
        bed.status = "available"
        await self.db.commit()
        await self.db.refresh(bed)
        return bed


class ERMlcService:
    """Medico-Legal Case management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_mlc(self, data: ERMlcCreate, created_by: uuid.UUID, org_id: uuid.UUID) -> ERMlcCase:
        ts = _now().strftime("%Y%m%d%H%M%S")
        short = str(uuid.uuid4())[:4].upper()
        mlc = ERMlcCase(
            org_id=org_id,
            er_encounter_id=data.er_encounter_id,
            mlc_number=f"MLC-{ts}-{short}",
            mlc_type=data.mlc_type,
            priority=data.priority,
            police_station=data.police_station,
            police_officer_name=data.police_officer_name,
            police_officer_badge=data.police_officer_badge,
            fir_number=data.fir_number,
            buckle_number=data.buckle_number,
            injury_description=data.injury_description,
            injury_details=data.injury_details,
            legal_notes=data.legal_notes,
            created_by=created_by,
        )
        self.db.add(mlc)

        # Flag encounter as MLC
        enc = (await self.db.execute(
            select(EREncounter).where(EREncounter.id == data.er_encounter_id)
        )).scalars().first()
        if enc:
            enc.is_mlc = True

        await self.db.commit()
        await self.db.refresh(mlc)
        return mlc

    async def list_mlc_cases(self, org_id: uuid.UUID) -> List[ERMlcCase]:
        return list((await self.db.execute(
            select(ERMlcCase).where(ERMlcCase.org_id == org_id).order_by(ERMlcCase.created_at.desc())
        )).scalars().all())


class ERScoringService:
    """Clinical scoring systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_score(self, data: ERNursingScoreCreate, scored_by: uuid.UUID, scored_by_name: str, org_id: uuid.UUID) -> ERNursingScore:
        score = ERNursingScore(
            org_id=org_id,
            er_encounter_id=data.er_encounter_id,
            score_type=data.score_type,
            total_score=data.total_score,
            risk_level=data.risk_level,
            score_components=data.score_components,
            interpretation=data.interpretation,
            scored_by=scored_by,
            scored_by_name=scored_by_name,
        )
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)
        return score

    async def get_scores(self, er_encounter_id: uuid.UUID, org_id: uuid.UUID) -> List[ERNursingScore]:
        return list((await self.db.execute(
            select(ERNursingScore).where(
                ERNursingScore.er_encounter_id == er_encounter_id,
                ERNursingScore.org_id == org_id
            ).order_by(ERNursingScore.scored_at.desc())
        )).scalars().all())


class EROrderService:
    """Quick clinical orders within ER — links to main orders module."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, data: EROrderCreate, ordered_by: uuid.UUID, ordered_by_name: str, org_id: uuid.UUID) -> EROrder:
        order = EROrder(
            org_id=org_id,
            er_encounter_id=data.er_encounter_id,
            order_type=data.order_type,
            order_description=data.order_description,
            priority=data.priority,
            ordered_by=ordered_by,
            ordered_by_name=ordered_by_name,
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def list_orders(self, er_encounter_id: uuid.UUID, org_id: uuid.UUID) -> List[EROrder]:
        return list((await self.db.execute(
            select(EROrder).where(
                EROrder.er_encounter_id == er_encounter_id, EROrder.org_id == org_id
            ).order_by(EROrder.ordered_at.desc())
        )).scalars().all())


class ERDashboardService:
    """Command Center dashboard aggregation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self, org_id: uuid.UUID) -> ERDashboardStats:
        active_statuses = ["registered", "triaged", "in_treatment", "observation",
                           "due_for_discharge", "marked_for_discharge", "ready_for_billing"]

        # Patient counts
        total = (await self.db.execute(
            select(func.count()).select_from(EREncounter).where(
                EREncounter.org_id == org_id, EREncounter.status.in_(active_statuses)
            )
        )).scalar() or 0

        triaged = (await self.db.execute(
            select(func.count()).select_from(EREncounter).where(
                EREncounter.org_id == org_id, EREncounter.status != "registered",
                EREncounter.status.in_(active_statuses)
            )
        )).scalar() or 0

        in_treatment = (await self.db.execute(
            select(func.count()).select_from(EREncounter).where(
                EREncounter.org_id == org_id, EREncounter.status == "in_treatment"
            )
        )).scalar() or 0

        awaiting = (await self.db.execute(
            select(func.count()).select_from(EREncounter).where(
                EREncounter.org_id == org_id, EREncounter.status == "registered"
            )
        )).scalar() or 0

        critical = (await self.db.execute(
            select(func.count()).select_from(EREncounter).where(
                EREncounter.org_id == org_id, EREncounter.is_critical == True,
                EREncounter.status.in_(active_statuses)
            )
        )).scalar() or 0

        mlc = (await self.db.execute(
            select(func.count()).select_from(EREncounter).where(
                EREncounter.org_id == org_id, EREncounter.is_mlc == True,
                EREncounter.status.in_(active_statuses)
            )
        )).scalar() or 0

        # Bed counts
        beds_total = (await self.db.execute(
            select(func.count()).select_from(ERBed).where(ERBed.org_id == org_id, ERBed.is_active == True)
        )).scalar() or 0

        beds_available = (await self.db.execute(
            select(func.count()).select_from(ERBed).where(
                ERBed.org_id == org_id, ERBed.is_active == True, ERBed.status == "available"
            )
        )).scalar() or 0

        beds_occupied = (await self.db.execute(
            select(func.count()).select_from(ERBed).where(
                ERBed.org_id == org_id, ERBed.is_active == True, ERBed.status == "occupied"
            )
        )).scalar() or 0

        # Zone occupancy
        zone_data = {}
        for zone_name in ["red", "yellow", "green", "peds", "obs"]:
            zt = (await self.db.execute(
                select(func.count()).select_from(ERBed).where(
                    ERBed.org_id == org_id, ERBed.zone == zone_name, ERBed.is_active == True
                )
            )).scalar() or 0
            zo = (await self.db.execute(
                select(func.count()).select_from(ERBed).where(
                    ERBed.org_id == org_id, ERBed.zone == zone_name, ERBed.status == "occupied"
                )
            )).scalar() or 0
            zone_data[zone_name] = {"total": zt, "occupied": zo, "available": zt - zo}

        return ERDashboardStats(
            total_patients=total, triaged=triaged, in_treatment=in_treatment,
            awaiting_triage=awaiting, critical=critical, mlc_cases=mlc,
            beds_total=beds_total, beds_available=beds_available, beds_occupied=beds_occupied,
            zone_occupancy=zone_data
        )


class ERBedSeeder:
    """Seed default ER beds for a new organization."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.bed_svc = ERBedService(db)

    async def seed_default_beds(self, org_id: uuid.UUID) -> int:
        beds_config = [
            # Red Zone (Resuscitation) - 4 beds
            ("ER-R01", "red", "bed", True, True), ("ER-R02", "red", "bed", True, True),
            ("ER-R03", "red", "bed", True, False), ("ER-R04", "red", "bed", True, False),
            # Yellow Zone (Acute) - 8 beds
            ("ER-Y01", "yellow", "stretcher", True, False), ("ER-Y02", "yellow", "stretcher", True, False),
            ("ER-Y03", "yellow", "stretcher", False, False), ("ER-Y04", "yellow", "stretcher", False, False),
            ("ER-Y05", "yellow", "bed", True, False), ("ER-Y06", "yellow", "bed", True, False),
            ("ER-Y07", "yellow", "bed", False, False), ("ER-Y08", "yellow", "bed", False, False),
            # Green Zone (Fast Track) - 6 beds
            ("ER-G01", "green", "recliner", False, False), ("ER-G02", "green", "recliner", False, False),
            ("ER-G03", "green", "chair", False, False), ("ER-G04", "green", "chair", False, False),
            ("ER-G05", "green", "stretcher", False, False), ("ER-G06", "green", "stretcher", False, False),
            # Pediatrics - 4 beds
            ("ER-P01", "peds", "bed", True, False), ("ER-P02", "peds", "bed", True, False),
            ("ER-P03", "peds", "bed", False, False), ("ER-P04", "peds", "bed", False, False),
            # Observation - 4 beds
            ("ER-O01", "obs", "bed", True, False), ("ER-O02", "obs", "bed", True, False),
            ("ER-O03", "obs", "bed", False, False), ("ER-O04", "obs", "bed", False, False),
        ]
        count = 0
        for code, zone, btype, monitored, vent in beds_config:
            await self.bed_svc.create_bed(code, zone, btype, org_id, is_monitored=monitored, has_ventilator=vent)
            count += 1
        return count


class ERDischargeService:
    """Full discharge workflow: discharge record → auto bed vacate → billing finalization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def discharge_patient(
        self, data, discharged_by: uuid.UUID, discharged_by_name: str, org_id: uuid.UUID
    ):
        from .models import ERDischarge

        enc = (await self.db.execute(
            select(EREncounter).where(EREncounter.id == data.er_encounter_id, EREncounter.org_id == org_id)
        )).scalars().first()
        if not enc:
            raise ValueError("ER encounter not found")

        discharge = ERDischarge(
            org_id=org_id,
            er_encounter_id=data.er_encounter_id,
            discharge_type=data.discharge_type,
            discharge_summary=data.discharge_summary,
            follow_up_instructions=data.follow_up_instructions,
            follow_up_date=data.follow_up_date,
            total_amount=data.total_amount,
            paid_amount=data.paid_amount,
            payment_mode=data.payment_mode,
            billing_cleared=bool(data.paid_amount and data.total_amount and float(data.paid_amount) >= float(data.total_amount)),
            disposition=data.disposition,
            destination_department=data.destination_department,
            discharged_by=discharged_by,
            discharged_by_name=discharged_by_name,
        )
        self.db.add(discharge)

        # Update encounter status
        enc.status = "discharged"
        enc.disposition = data.disposition or data.discharge_type
        enc.discharge_time = _now()
        enc.updated_at = _now()

        # Auto-vacate bed if patient had one assigned
        bed = (await self.db.execute(
            select(ERBed).where(
                ERBed.occupied_by_er_encounter_id == data.er_encounter_id,
                ERBed.org_id == org_id
            )
        )).scalars().first()
        if bed:
            bed.status = "cleaning"
            bed.occupied_by_er_encounter_id = None
            bed.patient_gender = None
            bed.occupied_since = None
            discharge.bed_vacated = True
            discharge.bed_id = bed.id

        await self.db.commit()
        await self.db.refresh(discharge)
        return discharge

    async def list_due_for_discharge(self, org_id: uuid.UUID):
        return list((await self.db.execute(
            select(EREncounter).where(
                EREncounter.org_id == org_id,
                EREncounter.status.in_(["due_for_discharge", "marked_for_discharge", "ready_for_billing"])
            ).order_by(EREncounter.arrival_time.asc())
        )).scalars().all())


class ERClinicalNoteService:
    """Clinical documentation — nursing cover sheet notes, shift notes, SOAP."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_note(self, data, authored_by: uuid.UUID, authored_by_name: str, authored_by_role: str, org_id: uuid.UUID):
        from .models import ERClinicalNote
        note = ERClinicalNote(
            org_id=org_id,
            er_encounter_id=data.er_encounter_id,
            note_type=data.note_type,
            content=data.content,
            structured_data=data.structured_data,
            authored_by=authored_by,
            authored_by_name=authored_by_name,
            authored_by_role=authored_by_role,
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def list_notes(self, er_encounter_id: uuid.UUID, org_id: uuid.UUID, note_type: str = None):
        from .models import ERClinicalNote
        stmt = select(ERClinicalNote).where(
            ERClinicalNote.er_encounter_id == er_encounter_id,
            ERClinicalNote.org_id == org_id
        )
        if note_type:
            stmt = stmt.where(ERClinicalNote.note_type == note_type)
        stmt = stmt.order_by(ERClinicalNote.authored_at.desc())
        return list((await self.db.execute(stmt)).scalars().all())


class ERDiagnosisService:
    """ICD-10 diagnosis recording for ER encounters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_diagnosis(self, data, recorded_by: uuid.UUID, recorded_by_name: str, org_id: uuid.UUID):
        from .models import ERDiagnosis
        dx = ERDiagnosis(
            org_id=org_id,
            er_encounter_id=data.er_encounter_id,
            icd_code=data.icd_code,
            diagnosis_description=data.diagnosis_description,
            diagnosis_type=data.diagnosis_type,
            is_primary=data.is_primary,
            recorded_by=recorded_by,
            recorded_by_name=recorded_by_name,
        )
        self.db.add(dx)
        await self.db.commit()
        await self.db.refresh(dx)
        return dx

    async def list_diagnoses(self, er_encounter_id: uuid.UUID, org_id: uuid.UUID):
        from .models import ERDiagnosis
        return list((await self.db.execute(
            select(ERDiagnosis).where(
                ERDiagnosis.er_encounter_id == er_encounter_id,
                ERDiagnosis.org_id == org_id
            ).order_by(ERDiagnosis.recorded_at.desc())
        )).scalars().all())

