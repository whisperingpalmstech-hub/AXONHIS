from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

# --- Drug Master ---
class MedicationCreate(BaseModel):
    drug_code: str
    drug_name: str
    generic_name: str
    drug_class: Optional[str] = None
    form: Optional[str] = None
    strength: Optional[str] = None
    pack_size: Optional[str] = None
    manufacturer: Optional[str] = None
    schedule_category: Optional[str] = None
    global_code: Optional[str] = None

class MedicationOut(MedicationCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Generic Mapping ---
class GenericMappingCreate(BaseModel):
    generic_name: str
    drug_id: uuid.UUID
    brand_substitute_rank: Optional[int] = 1

class GenericMappingOut(GenericMappingCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Drug Interaction ---
class DrugInteractionCreate(BaseModel):
    drug_a_generic: str
    drug_b_generic: str
    severity: str  # High, Moderate, Low
    interaction_effect: str

class DrugInteractionOut(DrugInteractionCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Drug Schedule ---
class DrugScheduleCreate(BaseModel):
    schedule_name: str
    requires_prescription: bool = True
    strict_narcotic: bool = False

class DrugScheduleOut(DrugScheduleCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Dosage Rule ---
class DosageRuleCreate(BaseModel):
    generic_name: str
    patient_category: str  # Adult, Pediatric, Geriatric
    dosage_per_kg: Optional[float] = None
    fixed_dosage: Optional[str] = None

class DosageRuleOut(DosageRuleCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Dosage Calculator Request ---
class DosageCalcRequest(BaseModel):
    generic_name: str
    patient_category: str
    weight_kg: Optional[float] = None

class DosageCalcResponse(BaseModel):
    generic_name: str
    patient_category: str
    calculated_dosage: str

# --- Pharmacy Role Permission ---
class PharmacyRoleCreate(BaseModel):
    role_name: str
    can_dispense: bool = False
    can_manage_inventory: bool = False
    can_manage_master: bool = False

class PharmacyRoleOut(PharmacyRoleCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Drug Master Audit ---
class DrugAuditOut(BaseModel):
    id: uuid.UUID
    drug_id: uuid.UUID
    modified_by: str
    modified_at: datetime
    old_value: Optional[dict] = None
    new_value: dict
    model_config = ConfigDict(from_attributes=True)

# --- Interaction Check Request ---
class InteractionCheckRequest(BaseModel):
    active_generics: List[str]

class InteractionCheckResult(BaseModel):
    has_interactions: bool
    interactions: List[DrugInteractionOut]
