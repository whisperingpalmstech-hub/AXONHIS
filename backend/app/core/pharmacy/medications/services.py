import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from .models import (
    Medication, PharmacyGenericMapping, PharmacyDrugInteraction,
    PharmacyDrugSchedule, PharmacyDosageRule, PharmacyRolePermission,
    PharmacyDrugMasterAudit
)
from .schemas import (
    MedicationCreate, GenericMappingCreate, DrugInteractionCreate,
    DrugScheduleCreate, DosageRuleCreate, DosageCalcRequest, DosageCalcResponse,
    PharmacyRoleCreate, InteractionCheckRequest, InteractionCheckResult,
    DrugInteractionOut
)


class MedicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Drug Master CRUD ─────────────────────────────────────────────
    async def create_medication(self, data: MedicationCreate) -> Medication:
        med = Medication(**data.model_dump())
        self.db.add(med)
        try:
            await self.db.flush()
        except IntegrityError:
            raise HTTPException(status_code=400, detail="Medication code already exists")
        return med

    async def get_medication(self, med_id: uuid.UUID) -> Medication:
        res = await self.db.execute(select(Medication).where(Medication.id == med_id))
        med = res.scalar_one_or_none()
        if not med:
            raise HTTPException(status_code=404, detail="Medication not found")
        return med

    async def list_medications(self, limit: int = 100) -> list[Medication]:
        res = await self.db.execute(select(Medication).limit(limit))
        return list(res.scalars().all())

    async def search_by_generic(self, generic_name: str) -> list[Medication]:
        q = select(Medication).where(Medication.generic_name.ilike(f"%{generic_name}%"))
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def update_medication(self, med_id: uuid.UUID, data: dict, modified_by: str) -> Medication:
        med = await self.get_medication(med_id)
        old_val = {c.name: getattr(med, c.name) for c in Medication.__table__.columns if c.name != 'id'}
        # Convert non-serializable types
        old_serializable = {}
        for k, v in old_val.items():
            old_serializable[k] = str(v) if v is not None else None

        for key, val in data.items():
            if hasattr(med, key):
                setattr(med, key, val)

        new_val = {k: str(v) if v is not None else None for k, v in data.items()}
        audit = PharmacyDrugMasterAudit(drug_id=med.id, modified_by=modified_by, old_value=old_serializable, new_value=new_val)
        self.db.add(audit)
        await self.db.flush()
        return med

    # ─── Generic Mapping ──────────────────────────────────────────────
    async def add_generic_mapping(self, data: GenericMappingCreate):
        mapping = PharmacyGenericMapping(**data.model_dump())
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def get_brand_substitutes(self, generic_name: str):
        q = select(PharmacyGenericMapping).where(PharmacyGenericMapping.generic_name.ilike(f"%{generic_name}%")).order_by(PharmacyGenericMapping.brand_substitute_rank)
        res = await self.db.execute(q)
        mappings = res.scalars().all()
        # Fetch drug details for each
        results = []
        for m in mappings:
            drug = await self.db.execute(select(Medication).where(Medication.id == m.drug_id))
            d = drug.scalar_one_or_none()
            if d:
                results.append({"mapping_id": str(m.id), "generic_name": m.generic_name, "brand": d.drug_name, "strength": d.strength, "manufacturer": d.manufacturer})
        return results

    # ─── Drug Interaction Checker ─────────────────────────────────────
    async def add_drug_interaction(self, data: DrugInteractionCreate):
        ix = PharmacyDrugInteraction(**data.model_dump())
        self.db.add(ix)
        await self.db.flush()
        return ix

    async def check_interactions(self, req: InteractionCheckRequest) -> InteractionCheckResult:
        generics = [g.lower() for g in req.active_generics]
        found = []
        for i in range(len(generics)):
            for j in range(i + 1, len(generics)):
                q = select(PharmacyDrugInteraction).where(
                    ((PharmacyDrugInteraction.drug_a_generic.ilike(generics[i])) & (PharmacyDrugInteraction.drug_b_generic.ilike(generics[j]))) |
                    ((PharmacyDrugInteraction.drug_a_generic.ilike(generics[j])) & (PharmacyDrugInteraction.drug_b_generic.ilike(generics[i])))
                )
                res = await self.db.execute(q)
                found.extend(res.scalars().all())
        return InteractionCheckResult(
            has_interactions=len(found) > 0,
            interactions=[DrugInteractionOut.model_validate(f) for f in found]
        )

    # ─── Drug Schedule ────────────────────────────────────────────────
    async def add_drug_schedule(self, data: DrugScheduleCreate):
        sch = PharmacyDrugSchedule(**data.model_dump())
        self.db.add(sch)
        await self.db.flush()
        return sch

    async def list_drug_schedules(self):
        res = await self.db.execute(select(PharmacyDrugSchedule))
        return list(res.scalars().all())

    # ─── Dosage Calculator ────────────────────────────────────────────
    async def add_dosage_rule(self, data: DosageRuleCreate):
        rule = PharmacyDosageRule(**data.model_dump())
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def calculate_dosage(self, req: DosageCalcRequest) -> DosageCalcResponse:
        q = select(PharmacyDosageRule).where(
            PharmacyDosageRule.generic_name.ilike(req.generic_name),
            PharmacyDosageRule.patient_category.ilike(req.patient_category)
        )
        res = await self.db.execute(q)
        rule = res.scalar_one_or_none()

        if not rule:
            return DosageCalcResponse(generic_name=req.generic_name, patient_category=req.patient_category, calculated_dosage="No dosage rule found.")

        if rule.dosage_per_kg and req.weight_kg:
            calc = float(rule.dosage_per_kg) * req.weight_kg
            return DosageCalcResponse(generic_name=req.generic_name, patient_category=req.patient_category, calculated_dosage=f"{calc:.1f} mg (based on {rule.dosage_per_kg} mg/kg × {req.weight_kg} kg)")
        elif rule.fixed_dosage:
            return DosageCalcResponse(generic_name=req.generic_name, patient_category=req.patient_category, calculated_dosage=rule.fixed_dosage)
        else:
            return DosageCalcResponse(generic_name=req.generic_name, patient_category=req.patient_category, calculated_dosage="Dosage rule incomplete.")

    # ─── Pharmacy Roles ───────────────────────────────────────────────
    async def add_pharmacy_role(self, data: PharmacyRoleCreate):
        role = PharmacyRolePermission(**data.model_dump())
        self.db.add(role)
        await self.db.flush()
        return role

    async def list_pharmacy_roles(self):
        res = await self.db.execute(select(PharmacyRolePermission))
        return list(res.scalars().all())

    # ─── Audit Trail ──────────────────────────────────────────────────
    async def get_drug_audit_trail(self, drug_id: uuid.UUID):
        q = select(PharmacyDrugMasterAudit).where(PharmacyDrugMasterAudit.drug_id == drug_id).order_by(PharmacyDrugMasterAudit.modified_at.desc())
        res = await self.db.execute(q)
        return list(res.scalars().all())
