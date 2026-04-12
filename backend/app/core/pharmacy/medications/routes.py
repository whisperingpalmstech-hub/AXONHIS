import uuid
from fastapi import APIRouter, Query
from app.dependencies import DBSession, CurrentUser
from .schemas import (
    MedicationCreate, MedicationOut,
    GenericMappingCreate, GenericMappingOut,
    DrugInteractionCreate, DrugInteractionOut,
    DrugScheduleCreate, DrugScheduleOut,
    DosageRuleCreate, DosageRuleOut,
    DosageCalcRequest, DosageCalcResponse,
    PharmacyRoleCreate, PharmacyRoleOut,
    DrugAuditOut,
    InteractionCheckRequest, InteractionCheckResult
)
from .services import MedicationService

router = APIRouter(tags=["pharmacy-core-infrastructure"])

# ─── Drug Master ──────────────────────────────────────────────────────
@router.post("/medications", response_model=MedicationOut)
async def create_medication(data: MedicationCreate, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    med = await svc.create_medication(data)
    await db.commit()
    return med

@router.get("/medications/{med_id}", response_model=MedicationOut)
async def get_medication(med_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.get_medication(med_id)

@router.get("/medications", response_model=list[MedicationOut])
async def list_medications(db: DBSession, _: CurrentUser, limit: int = 100):
    svc = MedicationService(db)
    return await svc.list_medications(limit=limit)

@router.get("/medications/search/generic", response_model=list[MedicationOut])
async def search_by_generic(generic_name: str, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.search_by_generic(generic_name)

@router.put("/medications/{med_id}", response_model=MedicationOut)
async def update_medication(med_id: uuid.UUID, data: dict, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    med = await svc.update_medication(med_id, data, modified_by=str(_.id) if hasattr(_, 'id') else "system")
    await db.commit()
    return med

# ─── Generic Mapping ──────────────────────────────────────────────────
@router.post("/pharmacy/generic-mappings", response_model=GenericMappingOut)
async def add_generic_mapping(data: GenericMappingCreate, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    m = await svc.add_generic_mapping(data)
    await db.commit()
    return m

@router.get("/pharmacy/generic-mappings/substitutes")
async def get_brand_substitutes(generic_name: str, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.get_brand_substitutes(generic_name)

# ─── Drug Interaction Checker ─────────────────────────────────────────
@router.post("/pharmacy/drug-interactions", response_model=DrugInteractionOut)
async def add_drug_interaction(data: DrugInteractionCreate, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    ix = await svc.add_drug_interaction(data)
    await db.commit()
    return ix

@router.post("/pharmacy/drug-interactions/check", response_model=InteractionCheckResult)
async def check_drug_interactions(req: InteractionCheckRequest, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.check_interactions(req)

# ─── Drug Schedule ────────────────────────────────────────────────────
@router.post("/pharmacy/drug-schedules", response_model=DrugScheduleOut)
async def add_drug_schedule(data: DrugScheduleCreate, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    sch = await svc.add_drug_schedule(data)
    await db.commit()
    return sch

@router.get("/pharmacy/drug-schedules", response_model=list[DrugScheduleOut])
async def list_drug_schedules(db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.list_drug_schedules()

# ─── Dosage Calculator ────────────────────────────────────────────────
@router.post("/pharmacy/dosage-rules", response_model=DosageRuleOut)
async def add_dosage_rule(data: DosageRuleCreate, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    rule = await svc.add_dosage_rule(data)
    await db.commit()
    return rule

@router.post("/pharmacy/dosage-calculator", response_model=DosageCalcResponse)
async def calculate_dosage(req: DosageCalcRequest, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.calculate_dosage(req)

# ─── Pharmacy Roles ───────────────────────────────────────────────────
@router.post("/pharmacy/roles", response_model=PharmacyRoleOut)
async def add_pharmacy_role(data: PharmacyRoleCreate, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    role = await svc.add_pharmacy_role(data)
    await db.commit()
    return role

@router.get("/pharmacy/roles", response_model=list[PharmacyRoleOut])
async def list_pharmacy_roles(db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.list_pharmacy_roles()

# ─── Drug Audit Trail ────────────────────────────────────────────────
@router.get("/pharmacy/drug-audit/{drug_id}", response_model=list[DrugAuditOut])
async def get_drug_audit_trail(drug_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.get_drug_audit_trail(drug_id)
