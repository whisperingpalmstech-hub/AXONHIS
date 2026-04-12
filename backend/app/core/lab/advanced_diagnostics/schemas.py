from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- HISTOPATHOLOGY ---
class HistopathologySlideOut(BaseModel):
    id: str
    slide_label: str
    staining_type: str
    microscopic_diagnosis: Optional[str]
    microscopic_images: List[str]
    prepared_at: datetime
    class Config: from_attributes = True

class HistopathologyBlockOut(BaseModel):
    id: str
    block_label: str
    embedding_status: str
    slides: List[HistopathologySlideOut] = []
    class Config: from_attributes = True

class HistopathologySpecimenOut(BaseModel):
    id: str
    sample_id: str
    patient_uhid: str
    patient_name: Optional[str]
    current_stage: str
    macroscopic_notes: Optional[str]
    is_sensitive: bool
    requires_counseling: bool
    counseling_status: str
    is_oncology: bool
    created_at: datetime
    blocks: List[HistopathologyBlockOut] = []
    class Config: from_attributes = True

class HistoAdvanceStageRequest(BaseModel):
    new_stage: str # Block Creation, Slide Preparation, Microscopic Examination, Diagnosis
    macroscopic_notes: Optional[str]

class AddSlideImageRequest(BaseModel):
    slide_id: str
    image_url: str
    diagnosis: Optional[str]

# --- MICROBIOLOGY & INFECTION CONTROL ---
class AntibioticSensitivityOut(BaseModel):
    id: str
    antibiotic_name: str
    mic_value: Optional[float]
    susceptibility: str
    class Config: from_attributes = True

class MicrobiologyCultureOut(BaseModel):
    id: str
    sample_id: str
    patient_uhid: str
    source_department: Optional[str]
    incubation_type: Optional[str]
    growth_findings: Optional[str]
    organism_identified: Optional[str]
    is_infection_control_screen: bool
    sensitivities: List[AntibioticSensitivityOut] = []
    class Config: from_attributes = True

class RecordMicrobiologyRequest(BaseModel):
    growth_findings: str
    organism_identified: Optional[str]

class AddSensitivityRequest(BaseModel):
    antibiotic_name: str
    mic_value: Optional[float]
    susceptibility: str

# --- CSSD STERILITY ---
class CSSDSterilityTestOut(BaseModel):
    id: str
    test_sample_id: str
    control_sample_id: str
    sterilization_validated: bool
    growth_in_test_sample: bool
    growth_in_control_sample: bool
    tested_at: datetime
    class Config: from_attributes = True

class RegisterCSSDTestRequest(BaseModel):
    test_sample_id: str
    control_sample_id: str

class ConcludeCSSDTestRequest(BaseModel):
    growth_in_test_sample: bool
    growth_in_control_sample: bool
    report_sent_to: str

# --- BLOOD BANK ---
class BloodBankInventoryOut(BaseModel):
    id: str
    unit_id: str
    blood_group: str
    collection_date: datetime
    expiry_date: datetime
    component_type: str
    status: str
    class Config: from_attributes = True

class RegisterBloodUnitRequest(BaseModel):
    unit_id: str
    blood_group: str
    donor_id: str
    donor_email: str
    collection_date: datetime
    expiry_date: datetime
    component_type: str
