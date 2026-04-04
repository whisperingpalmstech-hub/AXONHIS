from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Histo
class HistoSlideBase(BaseModel):
    slide_label: str
    staining_type: str
    microscopic_diagnosis: Optional[str] = None
    microscopic_images: List[str] = []

class HistoSlideOut(HistoSlideBase):
    id: str
    block_id: str
    prepared_at: datetime
    class Config:
        from_attributes = True

class HistoBlockBase(BaseModel):
    block_label: str
    embedding_status: str

class HistoBlockOut(HistoBlockBase):
    id: str
    specimen_id: str
    slides: List[HistoSlideOut] = []
    class Config:
        from_attributes = True

class HistoSpecimenBase(BaseModel):
    sample_id: str
    patient_uhid: str
    patient_name: str
    current_stage: str
    macroscopic_notes: Optional[str] = None
    is_sensitive: bool = False
    requires_counseling: bool = False
    counseling_status: str = "NA"
    is_oncology: bool = False

class HistoSpecimenOut(HistoSpecimenBase):
    id: str
    created_at: datetime
    blocks: List[HistoBlockOut] = []
    class Config:
        from_attributes = True

class AdvanceHistoCommand(BaseModel):
    new_stage: str
    macroscopic_notes: Optional[str] = None
    diagnostic: Optional[str] = None

class AddSlideImageCommand(BaseModel):
    slide_id: str
    image_url: str
    diagnosis: Optional[str] = None

# Micro
class AntiSensitivityBase(BaseModel):
    antibiotic_name: str
    mic_value: Optional[float] = None
    susceptibility: str

class AntiSensitivityOut(AntiSensitivityBase):
    id: str
    culture_id: str
    class Config:
        from_attributes = True

class MicroCultureBase(BaseModel):
    sample_id: str
    patient_uhid: str
    source_department: Optional[str] = None
    incubation_type: Optional[str] = None
    growth_findings: Optional[str] = None
    organism_identified: Optional[str] = None
    is_infection_control_screen: bool = False

class MicroCultureOut(MicroCultureBase):
    id: str
    sensitivities: List[AntiSensitivityOut] = []
    class Config:
        from_attributes = True

class RecordGrowthCommand(BaseModel):
    growth_findings: str
    organism_identified: Optional[str] = None

class AddSensitivityCommand(BaseModel):
    antibiotic_name: str
    mic_value: Optional[float] = None
    susceptibility: str

# CSSD
class CSSDTestBase(BaseModel):
    test_sample_id: str
    control_sample_id: str

class CSSDTestOut(CSSDTestBase):
    id: str
    sterilization_validated: bool
    growth_in_test_sample: bool
    growth_in_control_sample: bool
    tested_at: datetime
    report_sent_to: Optional[str] = None
    class Config:
        from_attributes = True

class RegisterCSSDCommand(CSSDTestBase):
    pass

class ConcludeCSSDCommand(BaseModel):
    growth_in_test_sample: bool
    growth_in_control_sample: bool
    report_sent_to: Optional[str] = None

# Blood Bank
class BloodBankUnitBase(BaseModel):
    unit_id: str
    blood_group: str
    collection_date: datetime
    expiry_date: datetime
    component_type: str
    status: str = "Available"

class BloodBankUnitOut(BloodBankUnitBase):
    id: str
    class Config:
        from_attributes = True
