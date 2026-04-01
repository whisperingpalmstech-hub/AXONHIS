"""IPD Enhancements — Services. Links to billing_masters, pharmacy, wards."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import IPDAdmissionEstimate, IPDPreAuthorization, IPDDischargeSummaryEnhanced as IPDDischargeSummary, IPDDietOrder, IPDConsentForm

def _now(): return datetime.now(timezone.utc)
def _gen(prefix):
    return f"{prefix}-{_now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"

class AdmissionEstimateService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create(self, data, created_by, org_id):
        est = IPDAdmissionEstimate(
            org_id=org_id, **data.model_dump(),
            estimated_room_charges=Decimal("5000") * data.expected_stay_days,
            estimated_procedure_charges=Decimal("15000"),
            estimated_pharmacy_charges=Decimal("3000"),
            estimated_lab_charges=Decimal("2000"),
            total_estimated_cost=Decimal("5000") * data.expected_stay_days + Decimal("20000"),
            deposit_required=Decimal("5000") * data.expected_stay_days * Decimal("0.5"),
            patient_liability=Decimal("5000") * data.expected_stay_days + Decimal("20000"),
            created_by=created_by
        )
        self.db.add(est); await self.db.commit(); await self.db.refresh(est); return est

    async def list_estimates(self, org_id):
        return list((await self.db.execute(select(IPDAdmissionEstimate).where(
            IPDAdmissionEstimate.org_id == org_id).order_by(IPDAdmissionEstimate.created_at.desc())
        )).scalars().all())

class PreAuthService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create(self, data, requested_by, org_id):
        pa = IPDPreAuthorization(org_id=org_id, **data.model_dump(),
            pre_auth_number=_gen("PA"), requested_by=requested_by)
        self.db.add(pa); await self.db.commit(); await self.db.refresh(pa); return pa

    async def respond(self, pa_id, response, org_id):
        pa = (await self.db.execute(select(IPDPreAuthorization).where(
            IPDPreAuthorization.id == pa_id, IPDPreAuthorization.org_id == org_id
        ))).scalars().first()
        if not pa: raise ValueError("Pre-auth not found")
        if response.action == "approve":
            pa.status = "approved"; pa.approved_amount = response.approved_amount or pa.requested_amount
        elif response.action == "reject":
            pa.status = "rejected"
        elif response.action == "enhance":
            pa.status = "enhanced"; pa.approved_amount = response.approved_amount
        pa.response_notes = response.response_notes; pa.responded_at = _now()
        await self.db.commit(); await self.db.refresh(pa); return pa

    async def list_preauths(self, org_id, status=None):
        stmt = select(IPDPreAuthorization).where(IPDPreAuthorization.org_id == org_id)
        if status: stmt = stmt.where(IPDPreAuthorization.status == status)
        return list((await self.db.execute(stmt.order_by(IPDPreAuthorization.requested_at.desc()))).scalars().all())

class DischargeSummaryService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create(self, data, prepared_by, org_id):
        ds = IPDDischargeSummary(org_id=org_id, **data.model_dump(),
            summary_number=_gen("DS"), prepared_by=prepared_by, status="draft")
        self.db.add(ds); await self.db.commit(); await self.db.refresh(ds); return ds

    async def approve(self, ds_id, approver_id, org_id):
        ds = (await self.db.execute(select(IPDDischargeSummary).where(
            IPDDischargeSummary.id == ds_id, IPDDischargeSummary.org_id == org_id
        ))).scalars().first()
        if not ds: raise ValueError("Summary not found")
        ds.status = "approved"; ds.approved_by = approver_id; ds.approved_at = _now()
        await self.db.commit(); await self.db.refresh(ds); return ds

    async def get_by_admission(self, admission_id, org_id):
        return (await self.db.execute(select(IPDDischargeSummary).where(
            IPDDischargeSummary.admission_id == admission_id, IPDDischargeSummary.org_id == org_id
        ))).scalars().first()

class DietOrderService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create(self, data, ordered_by, ordered_by_name, org_id):
        diet = IPDDietOrder(org_id=org_id, **data.model_dump(),
            ordered_by=ordered_by, ordered_by_name=ordered_by_name)
        self.db.add(diet); await self.db.commit(); await self.db.refresh(diet); return diet

    async def list_active(self, admission_id, org_id):
        return list((await self.db.execute(select(IPDDietOrder).where(
            IPDDietOrder.admission_id == admission_id, IPDDietOrder.org_id == org_id, IPDDietOrder.is_active == True
        ))).scalars().all())

class ConsentFormService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create(self, data, obtained_by, obtained_by_name, org_id):
        cf = IPDConsentForm(org_id=org_id, **data.model_dump(),
            obtained_by=obtained_by, obtained_by_name=obtained_by_name)
        self.db.add(cf); await self.db.commit(); await self.db.refresh(cf); return cf

    async def sign(self, consent_id, patient_signature, org_id):
        cf = (await self.db.execute(select(IPDConsentForm).where(
            IPDConsentForm.id == consent_id, IPDConsentForm.org_id == org_id
        ))).scalars().first()
        if not cf: raise ValueError("Consent not found")
        cf.patient_signature = patient_signature; cf.status = "signed"; cf.signed_at = _now()
        await self.db.commit(); await self.db.refresh(cf); return cf

    async def list_consents(self, admission_id, org_id):
        return list((await self.db.execute(select(IPDConsentForm).where(
            IPDConsentForm.admission_id == admission_id, IPDConsentForm.org_id == org_id
        ))).scalars().all())
