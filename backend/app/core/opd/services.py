"""
AXONHIS Complete OPD Module — Orchestrator Service Layer
========================================================
Unified service that ties together ALL OPD subsystems:
  - Pre-Registration → UHID Conversion
  - Deposit Management (create, consume, refund)
  - Consent Documents (create, sign, email, print)
  - Pro-forma Billing
  - Kiosk Self Check-in
  - Waitlist Management
  - AI Scheduling Predictions
  - Bill Cancellation with Audit
  - Daily Analytics Computation
  - Patient Journey Tracking
"""
import uuid
import math
import logging
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from .models import (
    PreRegistration, PreRegStatus,
    OPDDeposit, OPDDepositConsumption, DepositStatus,
    OPDConsentTemplate, OPDConsentDocument, ConsentStatus,
    OPDProFormaBill,
    OPDKioskCheckin, KioskStatus,
    OPDPatientNotification,
    OPDWaitlistEntry,
    AISchedulingPrediction,
    OPDDailyAnalytics,
    OPDBillCancellationLog,
)
from .schemas import (
    PreRegistrationCreate, ConvertPreRegRequest,
    DepositCreate, DepositRefundRequest, DepositConsumeRequest,
    ConsentTemplateCreate, ConsentDocumentCreate, ConsentDocumentSign,
    ConsentEmailRequest, ConsentUploadRequest,
    ProFormaBillCreate,
    KioskCheckinRequest,
    WaitlistCreate,
    BillCancelRequest,
    PatientJourneyStep, PatientJourneyOut,
)

logger = logging.getLogger(__name__)


def _gen_id(prefix: str) -> str:
    """Generate ID like PRE-20260402-123456."""
    now = datetime.now(timezone.utc)
    return f"{prefix}-{now.strftime('%Y%m%d')}-{str(uuid.uuid4().int)[:6]}"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PRE-REGISTRATION SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class PreRegistrationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_pre_registration(
        self, data: PreRegistrationCreate, user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> PreRegistration:
        # Duplicate detection via fuzzy matching
        dup_score, dup_id = await self._check_duplicates(data, org_id)
        
        prereg = PreRegistration(
            pre_reg_id=_gen_id("PRE"),
            org_id=org_id,
            first_name=data.first_name,
            last_name=data.last_name,
            gender=data.gender,
            date_of_birth=data.date_of_birth,
            mobile_number=data.mobile_number,
            email=data.email,
            address_line=data.address_line,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            nok_name=data.nok_name,
            nok_relationship=data.nok_relationship,
            nok_phone=data.nok_phone,
            payer_category=data.payer_category,
            insurance_provider=data.insurance_provider,
            policy_number=data.policy_number,
            preferred_doctor_id=data.preferred_doctor_id,
            preferred_department=data.preferred_department,
            preferred_date=data.preferred_date,
            photo_url=data.photo_url,
            status=PreRegStatus.PENDING,
            duplicate_score=dup_score,
            potential_duplicate_id=dup_id,
            created_by=user_id,
        )
        self.db.add(prereg)
        await self.db.commit()
        await self.db.refresh(prereg)
        logger.info(f"[OPD] Pre-registration created: {prereg.pre_reg_id}")
        return prereg

    async def _check_duplicates(
        self, data: PreRegistrationCreate, org_id: uuid.UUID | None
    ) -> tuple[float | None, uuid.UUID | None]:
        """Simple fuzzy duplicate check on name + mobile + DOB."""
        from app.core.patients.patients.models import Patient
        
        stmt = select(Patient)
        if org_id:
            stmt = stmt.where(Patient.org_id == org_id)
        
        # Check by mobile number first (strongest signal)
        if data.mobile_number:
            stmt_phone = stmt.where(Patient.primary_phone == data.mobile_number)
            result = await self.db.execute(stmt_phone.limit(1))
            match = result.scalar_one_or_none()
            if match:
                # Calculate name similarity
                name_sim = self._name_similarity(
                    f"{data.first_name} {data.last_name}",
                    f"{match.first_name} {match.last_name}"
                )
                score = 0.5 + (name_sim * 0.3)  # Phone match = 0.5 base
                if data.date_of_birth and match.date_of_birth == data.date_of_birth:
                    score += 0.2  # DOB match bonus
                return (score, match.id)
        
        return (None, None)

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Simple Jaccard similarity for names."""
        s1 = set(name1.lower().split())
        s2 = set(name2.lower().split())
        if not s1 or not s2:
            return 0.0
        return len(s1 & s2) / len(s1 | s2)

    async def convert_to_patient(
        self, prereg_id: uuid.UUID, data: ConvertPreRegRequest,
        user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> PreRegistration:
        """Convert pre-registration to full Patient with UHID."""
        from app.core.patients.patients.models import Patient
        
        stmt = select(PreRegistration).where(PreRegistration.id == prereg_id)
        if org_id:
            stmt = stmt.where(PreRegistration.org_id == org_id)
        result = await self.db.execute(stmt)
        prereg = result.scalar_one_or_none()
        
        if not prereg:
            raise ValueError("Pre-registration not found")
        if prereg.status != PreRegStatus.PENDING:
            raise ValueError(f"Pre-registration is already {prereg.status}")

        # Generate UHID
        uhid = f"UHID-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4().int)[:6]}"

        patient = Patient(
            patient_uuid=uhid,
            first_name=prereg.first_name,
            last_name=prereg.last_name,
            date_of_birth=prereg.date_of_birth or date(2000, 1, 1),
            gender=prereg.gender or "other",
            primary_phone=prereg.mobile_number,
            email=prereg.email,
            address=data.address or prereg.address_line,
            blood_group=data.blood_group,
            allergies=data.allergies,
            emergency_contact_name=data.emergency_contact_name or prereg.nok_name,
            emergency_contact_phone=data.emergency_contact_phone or prereg.nok_phone,
            status="active",
            org_id=org_id,
        )
        self.db.add(patient)
        await self.db.flush()

        # Update pre-reg
        prereg.status = PreRegStatus.CONVERTED
        prereg.converted_patient_id = patient.id
        prereg.converted_uhid = uhid

        await self.db.commit()
        await self.db.refresh(prereg)
        logger.info(f"[OPD] Pre-registration {prereg.pre_reg_id} converted to UHID {uhid}")
        return prereg

    async def list_pre_registrations(
        self, status: str | None = None, org_id: uuid.UUID | None = None
    ) -> list[PreRegistration]:
        stmt = select(PreRegistration).order_by(PreRegistration.created_at.desc())
        if org_id:
            stmt = stmt.where(PreRegistration.org_id == org_id)
        if status:
            stmt = stmt.where(PreRegistration.status == status)
        result = await self.db.execute(stmt.limit(200))
        return list(result.scalars().all())

    async def get_pre_registration(
        self, prereg_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> PreRegistration | None:
        stmt = select(PreRegistration).where(PreRegistration.id == prereg_id)
        if org_id:
            stmt = stmt.where(PreRegistration.org_id == org_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DEPOSIT MANAGEMENT SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class DepositService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deposit(
        self, data: DepositCreate, user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> OPDDeposit:
        dep = OPDDeposit(
            deposit_number=_gen_id("DEP"),
            org_id=org_id,
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            deposit_amount=data.deposit_amount,
            balance_amount=data.deposit_amount,
            payment_mode=data.payment_mode,
            transaction_reference=data.transaction_reference,
            receipt_number=_gen_id("REC"),
            status=DepositStatus.ACTIVE,
            collected_by=user_id,
            notes=data.notes,
        )
        self.db.add(dep)
        await self.db.commit()
        await self.db.refresh(dep)
        logger.info(f"[OPD] Deposit {dep.deposit_number} created: ₹{data.deposit_amount}")
        return dep

    async def consume_deposit(
        self, deposit_id: uuid.UUID, data: DepositConsumeRequest,
        user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> OPDDeposit:
        stmt = select(OPDDeposit).where(OPDDeposit.id == deposit_id)
        if org_id:
            stmt = stmt.where(OPDDeposit.org_id == org_id)
        result = await self.db.execute(stmt)
        dep = result.scalar_one_or_none()
        
        if not dep:
            raise ValueError("Deposit not found")
        if dep.status in [DepositStatus.FULLY_CONSUMED, DepositStatus.REFUNDED]:
            raise ValueError(f"Deposit is {dep.status}, cannot consume")
        
        balance = float(dep.balance_amount)
        if data.amount > balance:
            raise ValueError(f"Insufficient balance. Available: ₹{balance}")

        # Record consumption
        consumption = OPDDepositConsumption(
            deposit_id=dep.id,
            bill_id=data.bill_id,
            consumed_amount=data.amount,
            consumed_by=user_id,
            notes=data.notes,
        )
        self.db.add(consumption)

        # Update deposit
        dep.consumed_amount = float(dep.consumed_amount) + data.amount
        dep.balance_amount = float(dep.balance_amount) - data.amount
        if dep.balance_amount <= 0:
            dep.status = DepositStatus.FULLY_CONSUMED
        else:
            dep.status = DepositStatus.PARTIALLY_CONSUMED

        await self.db.commit()
        await self.db.refresh(dep)
        return dep

    async def refund_deposit(
        self, deposit_id: uuid.UUID, data: DepositRefundRequest,
        user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> OPDDeposit:
        stmt = select(OPDDeposit).where(OPDDeposit.id == deposit_id)
        if org_id:
            stmt = stmt.where(OPDDeposit.org_id == org_id)
        result = await self.db.execute(stmt)
        dep = result.scalar_one_or_none()
        
        if not dep:
            raise ValueError("Deposit not found")
        
        balance = float(dep.balance_amount)
        refund_amount = data.refund_amount if data.refund_amount else balance
        
        if refund_amount > balance:
            raise ValueError(f"Refund amount exceeds balance ₹{balance}")

        dep.refunded_amount = float(dep.refunded_amount or 0) + refund_amount
        dep.balance_amount = balance - refund_amount
        dep.status = DepositStatus.REFUNDED
        dep.refund_reason = data.reason
        dep.refunded_by = user_id
        dep.refunded_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(dep)
        logger.info(f"[OPD] Deposit {dep.deposit_number} refunded: ₹{refund_amount}")
        return dep

    async def list_deposits(
        self, patient_id: uuid.UUID | None = None,
        status: str | None = None,
        org_id: uuid.UUID | None = None
    ) -> list[OPDDeposit]:
        stmt = select(OPDDeposit).order_by(OPDDeposit.created_at.desc())
        if org_id:
            stmt = stmt.where(OPDDeposit.org_id == org_id)
        if patient_id:
            stmt = stmt.where(OPDDeposit.patient_id == patient_id)
        if status:
            stmt = stmt.where(OPDDeposit.status == status)
        result = await self.db.execute(stmt.limit(200))
        return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CONSENT DOCUMENT SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class ConsentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(
        self, data: ConsentTemplateCreate, user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> OPDConsentTemplate:
        t = OPDConsentTemplate(
            org_id=org_id,
            template_name=data.template_name,
            template_category=data.template_category,
            template_body=data.template_body,
            language=data.language,
            created_by=user_id,
        )
        self.db.add(t)
        await self.db.commit()
        await self.db.refresh(t)
        return t

    async def list_templates(
        self, category: str | None = None, org_id: uuid.UUID | None = None
    ) -> list[OPDConsentTemplate]:
        stmt = select(OPDConsentTemplate).where(OPDConsentTemplate.is_active == True)
        if org_id:
            stmt = stmt.where(OPDConsentTemplate.org_id == org_id)
        if category:
            stmt = stmt.where(OPDConsentTemplate.template_category == category)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_document(
        self, data: ConsentDocumentCreate, user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> OPDConsentDocument:
        doc = OPDConsentDocument(
            org_id=org_id,
            consent_number=_gen_id("CON"),
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            template_id=data.template_id,
            consent_title=data.consent_title,
            consent_body=data.consent_body,
            status=ConsentStatus.PENDING_SIGNATURE,
            created_by=user_id,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def sign_document(
        self, doc_id: uuid.UUID, data: ConsentDocumentSign, org_id: uuid.UUID | None = None
    ) -> OPDConsentDocument:
        stmt = select(OPDConsentDocument).where(OPDConsentDocument.id == doc_id)
        if org_id:
            stmt = stmt.where(OPDConsentDocument.org_id == org_id)
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise ValueError("Consent document not found")

        doc.signature_data = data.signature_data
        doc.signed_by_name = data.signed_by_name
        doc.witness_name = data.witness_name
        doc.witness_designation = data.witness_designation
        doc.signed_at = datetime.now(timezone.utc)
        doc.status = ConsentStatus.SIGNED

        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def email_document(
        self, doc_id: uuid.UUID, data: ConsentEmailRequest, org_id: uuid.UUID | None = None
    ) -> OPDConsentDocument:
        stmt = select(OPDConsentDocument).where(OPDConsentDocument.id == doc_id)
        if org_id:
            stmt = stmt.where(OPDConsentDocument.org_id == org_id)
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError("Consent document not found")

        doc.emailed_to = data.email
        doc.emailed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(doc)
        logger.info(f"[OPD] Consent {doc.consent_number} emailed to {data.email}")
        return doc

    async def upload_scanned(
        self, doc_id: uuid.UUID, data: ConsentUploadRequest, org_id: uuid.UUID | None = None
    ) -> OPDConsentDocument:
        stmt = select(OPDConsentDocument).where(OPDConsentDocument.id == doc_id)
        if org_id:
            stmt = stmt.where(OPDConsentDocument.org_id == org_id)
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError("Consent document not found")
        doc.scanned_document_url = data.document_url
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list_documents(
        self, patient_id: uuid.UUID | None = None,
        visit_id: uuid.UUID | None = None,
        org_id: uuid.UUID | None = None
    ) -> list[OPDConsentDocument]:
        stmt = select(OPDConsentDocument).order_by(OPDConsentDocument.created_at.desc())
        if org_id:
            stmt = stmt.where(OPDConsentDocument.org_id == org_id)
        if patient_id:
            stmt = stmt.where(OPDConsentDocument.patient_id == patient_id)
        if visit_id:
            stmt = stmt.where(OPDConsentDocument.visit_id == visit_id)
        result = await self.db.execute(stmt.limit(200))
        return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PRO-FORMA BILLING SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class ProFormaBillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_proforma(
        self, data: ProFormaBillCreate, user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> OPDProFormaBill:
        items_data = [item.model_dump() for item in data.items]
        subtotal = sum(item.unit_price * item.quantity for item in data.items)
        estimated_total = subtotal - data.discount_amount

        bill = OPDProFormaBill(
            org_id=org_id,
            proforma_number=_gen_id("PFB"),
            patient_id=data.patient_id,
            visit_id=data.visit_id,
            items=items_data,
            subtotal=subtotal,
            discount_amount=data.discount_amount,
            estimated_total=estimated_total,
            valid_until=date.today() + timedelta(days=data.valid_days),
            notes=data.notes,
            generated_by=user_id,
        )
        self.db.add(bill)
        await self.db.commit()
        await self.db.refresh(bill)
        return bill

    async def list_proformas(
        self, patient_id: uuid.UUID | None = None, org_id: uuid.UUID | None = None
    ) -> list[OPDProFormaBill]:
        stmt = select(OPDProFormaBill).order_by(OPDProFormaBill.generated_at.desc())
        if org_id:
            stmt = stmt.where(OPDProFormaBill.org_id == org_id)
        if patient_id:
            stmt = stmt.where(OPDProFormaBill.patient_id == patient_id)
        result = await self.db.execute(stmt.limit(100))
        return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════════════════
# 5. KIOSK CHECK-IN SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class KioskCheckinService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_checkin(
        self, data: KioskCheckinRequest, org_id: uuid.UUID | None = None
    ) -> OPDKioskCheckin:
        from app.core.patients.patients.models import Patient
        from app.core.scheduling.models import SlotBooking
        
        session = OPDKioskCheckin(
            org_id=org_id,
            kiosk_id=data.kiosk_id,
            verification_method=data.verification_method,
            verification_data=data.verification_data,
            status=KioskStatus.STARTED,
        )
        self.db.add(session)
        await self.db.flush()

        try:
            patient = None
            
            if data.verification_method == "uhid":
                result = await self.db.execute(
                    select(Patient).where(
                        Patient.patient_uuid == data.verification_data
                    )
                )
                patient = result.scalar_one_or_none()
            
            elif data.verification_method == "mobile_otp":
                result = await self.db.execute(
                    select(Patient).where(
                        Patient.primary_phone == data.verification_data
                    )
                )
                patient = result.scalar_one_or_none()

            if not patient:
                session.status = KioskStatus.FAILED
                session.error_message = "Patient not found"
                await self.db.commit()
                return session

            session.patient_id = patient.id
            session.status = KioskStatus.IDENTITY_VERIFIED

            # Check for today's appointments
            today = date.today()
            booking_res = await self.db.execute(
                select(SlotBooking).where(
                    and_(
                        SlotBooking.patient_id == patient.id,
                        SlotBooking.booking_date == today,
                        SlotBooking.status.in_(["confirmed", "checked_in"]),
                    )
                )
            )
            booking = booking_res.scalar_one_or_none()

            if booking:
                session.appointment_id = booking.id
                booking.status = "checked_in"
                booking.check_in_time = datetime.now(timezone.utc)

            # Generate token
            token_count = await self.db.execute(
                select(func.count(OPDKioskCheckin.id)).where(
                    and_(
                        OPDKioskCheckin.status == KioskStatus.CHECKED_IN,
                        func.date(OPDKioskCheckin.started_at) == today,
                    )
                )
            )
            count = token_count.scalar() or 0
            token = f"T{today.strftime('%m%d')}{count + 1:03d}"

            session.token_number = token
            session.status = KioskStatus.CHECKED_IN
            session.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            session.status = KioskStatus.FAILED
            session.error_message = str(e)
            logger.error(f"[OPD] Kiosk check-in failed: {e}")

        await self.db.commit()
        await self.db.refresh(session)
        return session


# ═══════════════════════════════════════════════════════════════════════════════
# 6. WAITLIST SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class WaitlistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_waitlist(
        self, data: WaitlistCreate, org_id: uuid.UUID | None = None
    ) -> OPDWaitlistEntry:
        entry = OPDWaitlistEntry(
            org_id=org_id,
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            department=data.department,
            preferred_date=data.preferred_date,
            preferred_time_start=data.preferred_time_start,
            preferred_time_end=data.preferred_time_end,
            reason=data.reason,
            priority=data.priority,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def process_cancellation_waitlist(
        self, doctor_id: uuid.UUID, slot_date: date, org_id: uuid.UUID | None = None
    ) -> OPDWaitlistEntry | None:
        """When a slot is cancelled, find and notify the next waitlisted patient."""
        stmt = (
            select(OPDWaitlistEntry)
            .where(
                and_(
                    OPDWaitlistEntry.doctor_id == doctor_id,
                    OPDWaitlistEntry.preferred_date == slot_date,
                    OPDWaitlistEntry.status == "waiting",
                )
            )
            .order_by(OPDWaitlistEntry.priority.asc(), OPDWaitlistEntry.created_at.asc())
            .limit(1)
        )
        if org_id:
            stmt = stmt.where(OPDWaitlistEntry.org_id == org_id)
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()
        
        if entry:
            entry.status = "offered"
            entry.notified_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(entry)
            logger.info(f"[OPD] Waitlist: Offered slot to patient {entry.patient_id}")
        
        return entry

    async def list_waitlist(
        self, doctor_id: uuid.UUID | None = None,
        status: str | None = None,
        org_id: uuid.UUID | None = None
    ) -> list[OPDWaitlistEntry]:
        stmt = select(OPDWaitlistEntry).order_by(OPDWaitlistEntry.priority.asc())
        if org_id:
            stmt = stmt.where(OPDWaitlistEntry.org_id == org_id)
        if doctor_id:
            stmt = stmt.where(OPDWaitlistEntry.doctor_id == doctor_id)
        if status:
            stmt = stmt.where(OPDWaitlistEntry.status == status)
        result = await self.db.execute(stmt.limit(100))
        return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════════════════
# 7. AI SCHEDULING PREDICTION SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class AISchedulingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def predict_no_show(
        self, patient_id: uuid.UUID, doctor_id: uuid.UUID,
        appointment_date: date, booking_id: uuid.UUID | None = None,
        org_id: uuid.UUID | None = None
    ) -> AISchedulingPrediction:
        """AI prediction for no-show probability based on patient history."""
        from app.core.opd_visits.models import VisitMaster, VisitStatus

        # Factor 1: Previous no-shows
        no_show_stmt = select(func.count(VisitMaster.id)).where(
            and_(
                VisitMaster.patient_id == patient_id,
                VisitMaster.status == VisitStatus.no_show,
            )
        )
        no_show_count = (await self.db.execute(no_show_stmt)).scalar() or 0

        # Factor 2: Total previous visits
        total_stmt = select(func.count(VisitMaster.id)).where(
            VisitMaster.patient_id == patient_id
        )
        total_visits = (await self.db.execute(total_stmt)).scalar() or 0

        # Factor 3: Day of week (weekends have higher no-show)
        day_factor = 0.1 if appointment_date.weekday() < 5 else 0.2

        # Calculate probability
        factors = []
        base_prob = 0.1  # 10% base

        if total_visits > 0:
            ns_rate = no_show_count / total_visits
            base_prob += ns_rate * 0.4
            factors.append({"factor": "historical_no_show_rate", "value": round(ns_rate, 2)})

        base_prob += day_factor
        factors.append({"factor": "day_of_week", "value": appointment_date.strftime("%A")})

        # Determine recommendation
        prob = min(base_prob, 0.95)
        if prob > 0.5:
            recommendation = "overbook"
        elif prob > 0.3:
            recommendation = "call_confirm"
        else:
            recommendation = "send_reminder"

        prediction = AISchedulingPrediction(
            org_id=org_id,
            booking_id=booking_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            no_show_probability=round(prob, 3),
            prediction_factors=factors,
            recommendation=recommendation,
        )
        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)
        return prediction


# ═══════════════════════════════════════════════════════════════════════════════
# 8. BILL CANCELLATION SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class BillCancellationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def cancel_bill(
        self, bill_id: uuid.UUID, data: BillCancelRequest,
        user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> OPDBillCancellationLog:
        from app.core.rcm_billing.models import BillingMaster, BillStatus

        stmt = select(BillingMaster).where(BillingMaster.id == bill_id)
        if org_id:
            stmt = stmt.where(BillingMaster.org_id == org_id)
        result = await self.db.execute(stmt)
        bill = result.scalar_one_or_none()

        if not bill:
            raise ValueError("Bill not found")
        if bill.status == BillStatus.cancelled:
            raise ValueError("Bill is already cancelled")

        # Create audit log
        log = OPDBillCancellationLog(
            org_id=org_id,
            bill_id=bill.id,
            bill_number=bill.bill_number,
            patient_id=bill.patient_id,
            original_amount=bill.net_amount,
            cancellation_reason=data.reason,
            cancelled_by=user_id,
            authorized_by=data.authorized_by,
            supporting_document_url=data.supporting_document_url,
        )
        self.db.add(log)

        # Cancel the bill
        bill.status = BillStatus.cancelled

        await self.db.commit()
        await self.db.refresh(log)
        logger.info(f"[OPD] Bill {bill.bill_number} cancelled. Reason: {data.reason}")
        return log


# ═══════════════════════════════════════════════════════════════════════════════
# 9. OPD ANALYTICS SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class OPDAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_daily_analytics(
        self, for_date: date, org_id: uuid.UUID | None = None
    ) -> OPDDailyAnalytics:
        from app.core.opd_visits.models import VisitMaster, VisitStatus, PriorityTag
        from app.core.scheduling.models import SlotBooking, CalendarSlot
        from app.core.rcm_billing.models import BillingMaster

        # Visits
        visit_stmt = select(VisitMaster).where(
            func.date(VisitMaster.visit_date_time) == for_date
        )
        if org_id:
            visit_stmt = visit_stmt.where(VisitMaster.org_id == org_id)
        visits = list((await self.db.execute(visit_stmt)).scalars().all())

        total = len(visits)
        completed = sum(1 for v in visits if v.status == VisitStatus.completed)
        cancelled = sum(1 for v in visits if v.status == VisitStatus.cancelled)
        no_shows = sum(1 for v in visits if v.status == VisitStatus.no_show)
        walkins = sum(1 for v in visits if v.visit_source == "front_office")
        
        # Appointments
        appt_stmt = select(func.count(SlotBooking.id)).where(
            SlotBooking.booking_date == for_date
        )
        total_appointments = (await self.db.execute(appt_stmt)).scalar() or 0

        # Wait times
        wait_times = [v.estimated_wait_min for v in visits if v.estimated_wait_min]
        avg_wait = sum(wait_times) / len(wait_times) if wait_times else None
        max_wait = max(wait_times) if wait_times else None

        # Revenue
        bill_stmt = select(BillingMaster).where(
            func.date(BillingMaster.generated_at) == for_date
        )
        if org_id:
            bill_stmt = bill_stmt.where(BillingMaster.org_id == org_id)
        bills = list((await self.db.execute(bill_stmt)).scalars().all())
        total_revenue = float(sum(float(b.net_amount or 0) for b in bills))

        # Deposits
        dep_stmt = select(func.sum(OPDDeposit.deposit_amount)).where(
            func.date(OPDDeposit.collected_at) == for_date
        )
        if org_id:
            dep_stmt = dep_stmt.where(OPDDeposit.org_id == org_id)
        total_deposits = float((await self.db.execute(dep_stmt)).scalar() or 0)

        # Hourly distribution
        hourly = {}
        for v in visits:
            if v.visit_date_time:
                h = v.visit_date_time.strftime("%H")
                hourly[h] = hourly.get(h, 0) + 1
        
        peak_hour = max(hourly, key=hourly.get) if hourly else None

        # Department breakdown
        dept_break = {}
        for v in visits:
            dept = v.department or "Unknown"
            if dept not in dept_break:
                dept_break[dept] = {"visits": 0}
            dept_break[dept]["visits"] += 1

        # Check if analytics already exists for this date and org
        stmt = select(OPDDailyAnalytics).where(
            and_(
                OPDDailyAnalytics.analytics_date == for_date,
                OPDDailyAnalytics.org_id == org_id
            )
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if existing:
            analytics = existing
            analytics.total_appointments = total_appointments
            analytics.total_walkins = walkins
            analytics.total_checkins = total
            analytics.total_visits = total
            analytics.completed_visits = completed
            analytics.cancelled_visits = cancelled
            analytics.no_show_count = no_shows
            analytics.avg_wait_time_min = avg_wait
            analytics.max_wait_time_min = max_wait
            analytics.total_revenue = total_revenue
            analytics.total_deposits = total_deposits
            analytics.department_breakdown = dept_break
            analytics.peak_hour = peak_hour
            analytics.hourly_distribution = hourly
            analytics.computed_at = datetime.now(timezone.utc)
        else:
            analytics = OPDDailyAnalytics(
                org_id=org_id,
                analytics_date=for_date,
                total_appointments=total_appointments,
                total_walkins=walkins,
                total_checkins=total,
                total_visits=total,
                completed_visits=completed,
                cancelled_visits=cancelled,
                no_show_count=no_shows,
                avg_wait_time_min=avg_wait,
                max_wait_time_min=max_wait,
                total_revenue=total_revenue,
                total_deposits=total_deposits,
                department_breakdown=dept_break,
                peak_hour=peak_hour,
                hourly_distribution=hourly,
                computed_at=datetime.now(timezone.utc)
            )
            self.db.add(analytics)
            
        await self.db.commit()
        await self.db.refresh(analytics)
        return analytics


# ═══════════════════════════════════════════════════════════════════════════════
# 10. PATIENT JOURNEY TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

class PatientJourneyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_journey(
        self, visit_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> PatientJourneyOut:
        from app.core.opd_visits.models import VisitMaster
        from app.core.nursing_triage.models import NursingWorklist, NursingVitals
        from app.core.doctor_desk.models import DoctorWorklist, ConsultationNote
        from app.core.rcm_billing.models import BillingMaster
        from app.core.patients.patients.models import Patient

        # Get visit
        visit_stmt = select(VisitMaster).where(VisitMaster.id == visit_id)
        if org_id:
            visit_stmt = visit_stmt.where(VisitMaster.org_id == org_id)
        visit = (await self.db.execute(visit_stmt)).scalar_one_or_none()
        if not visit:
            raise ValueError("Visit not found")

        # Get patient
        patient = (await self.db.execute(
            select(Patient).where(Patient.id == visit.patient_id)
        )).scalar_one_or_none()

        steps = []

        # Step 1: Registration/Check-in
        steps.append(PatientJourneyStep(
            step_name="Registration & Check-in",
            status="completed",
            timestamp=visit.created_at,
            details={"visit_id": visit.visit_id, "token": visit.queue_token}
        ))

        # Step 2: Nursing Triage
        triage = (await self.db.execute(
            select(NursingWorklist).where(NursingWorklist.visit_id == visit.id)
        )).scalar_one_or_none()
        
        vitals = (await self.db.execute(
            select(NursingVitals).where(NursingVitals.visit_id == visit.id)
        )).scalar_one_or_none()

        triage_status = "completed" if (triage and triage.triage_status == "completed") else (
            "in_progress" if triage else "pending"
        )
        steps.append(PatientJourneyStep(
            step_name="Nursing Assessment & Vitals",
            status=triage_status,
            timestamp=triage.completed_at if triage else None,
            details={"has_vitals": vitals is not None}
        ))

        # Step 3: Doctor Consultation
        doc_wl = (await self.db.execute(
            select(DoctorWorklist).where(DoctorWorklist.visit_id == visit.id)
        )).scalar_one_or_none()
        
        consult_note = (await self.db.execute(
            select(ConsultationNote).where(ConsultationNote.visit_id == visit.id)
        )).scalar_one_or_none()

        consult_status = "completed" if consult_note else (
            "in_progress" if (doc_wl and doc_wl.status == "in_consultation") else (
                "pending" if doc_wl else "pending"
            )
        )
        steps.append(PatientJourneyStep(
            step_name="Doctor Consultation",
            status=consult_status,
            timestamp=doc_wl.started_at if doc_wl else None,
        ))

        # Step 4: Billing
        bill = (await self.db.execute(
            select(BillingMaster).where(BillingMaster.visit_id == uuid.UUID(visit.encounter_id) if visit.encounter_id else None)
        )).scalar_one_or_none() if visit.encounter_id else None

        bill_status = "completed" if (bill and bill.status == "paid") else (
            "in_progress" if bill else "pending"
        )
        steps.append(PatientJourneyStep(
            step_name="Billing & Settlement",
            status=bill_status,
            timestamp=bill.settled_at if bill else None,
        ))

        # Step 5: Pharmacy / Lab
        steps.append(PatientJourneyStep(
            step_name="Orders (Lab/Pharmacy/Radiology)",
            status="pending" if consult_status != "completed" else "in_progress",
        ))

        # Step 6: Visit Closure
        steps.append(PatientJourneyStep(
            step_name="Visit Complete",
            status="completed" if visit.status == "completed" else "pending",
        ))

        # Determine current step
        current = "Registration & Check-in"
        for step in steps:
            if step.status in ["in_progress", "pending"]:
                current = step.step_name
                break
            current = step.step_name

        return PatientJourneyOut(
            patient_id=visit.patient_id,
            visit_id=visit.id,
            visit_number=visit.visit_id,
            patient_name=f"{patient.first_name} {patient.last_name}" if patient else "Unknown",
            uhid=patient.patient_uuid if patient else None,
            steps=steps,
            current_step=current,
            overall_status=visit.status,
        )
