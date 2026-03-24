from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

def build_uuid():
    return str(uuid.uuid4())

class HistopathologySpecimen(Base):
    __tablename__ = "lis_histopathology_specimens"
    id = Column(String, primary_key=True, default=build_uuid)
    sample_id = Column(String, index=True, nullable=False)
    test_order_id = Column(String, index=True, nullable=False)
    patient_uhid = Column(String, index=True, nullable=False)
    patient_name = Column(String, nullable=True)
    
    macroscopic_notes = Column(String, nullable=True)
    # Specimen Received -> Block Creation -> Slide Preparation -> Microscopic Examination -> Diagnosis -> Report Release.
    current_stage = Column(String, default="Specimen Received", index=True) 
    
    is_sensitive = Column(Boolean, default=False)
    requires_counseling = Column(Boolean, default=False)
    counseling_status = Column(String, default="PENDING") # PENDING, IN_PROGRESS, CLEARED
    is_oncology = Column(Boolean, default=False)
    cross_referral_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    blocks = relationship("HistopathologyBlock", back_populates="specimen")

class HistopathologyBlock(Base):
    __tablename__ = "lis_histopathology_blocks"
    id = Column(String, primary_key=True, default=build_uuid)
    specimen_id = Column(String, ForeignKey("lis_histopathology_specimens.id"), index=True)
    block_label = Column(String, nullable=False)
    embedding_status = Column(String, default="Prepared")
    creation_time = Column(DateTime, default=datetime.utcnow)
    
    specimen = relationship("HistopathologySpecimen", back_populates="blocks")
    slides = relationship("HistopathologySlide", back_populates="block")

class HistopathologySlide(Base):
    __tablename__ = "lis_histopathology_slides"
    id = Column(String, primary_key=True, default=build_uuid)
    block_id = Column(String, ForeignKey("lis_histopathology_blocks.id"), index=True)
    slide_label = Column(String, nullable=False)
    staining_type = Column(String, default="H&E")
    microscopic_diagnosis = Column(String, nullable=True)
    microscopic_images = Column(JSON, default=list) # e.g. ["url1.jpg", "url2.dicom"]
    prepared_at = Column(DateTime, default=datetime.utcnow)
    
    block = relationship("HistopathologyBlock", back_populates="slides")

class MicrobiologyCulture(Base):
    __tablename__ = "lis_microbiology_cultures"
    id = Column(String, primary_key=True, default=build_uuid)
    sample_id = Column(String, index=True, nullable=False)
    test_order_id = Column(String, index=True, nullable=False)
    patient_uhid = Column(String, index=True, nullable=False)
    source_department = Column(String, nullable=True) # OT, ICU, Ward
    
    incubation_type = Column(String, nullable=True) # Aerobic, Anaerobic
    incubation_time_hrs = Column(Integer, default=24)
    growth_findings = Column(String, nullable=True) # No Growth, Heavy Growth
    organism_identified = Column(String, nullable=True) # e.g. E. coli
    
    is_infection_control_screen = Column(Boolean, default=False)
    infection_control_report_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sensitivities = relationship("AntibioticSensitivity", back_populates="culture")

class AntibioticSensitivity(Base):
    __tablename__ = "lis_antibiotic_sensitivity"
    id = Column(String, primary_key=True, default=build_uuid)
    culture_id = Column(String, ForeignKey("lis_microbiology_cultures.id"), index=True)
    antibiotic_name = Column(String, nullable=False)
    mic_value = Column(Float, nullable=True)
    susceptibility = Column(String, nullable=False) # Sensitive, Intermediate, Resistant
    
    culture = relationship("MicrobiologyCulture", back_populates="sensitivities")

class CSSDSterilityTest(Base):
    __tablename__ = "lis_cssd_tests"
    id = Column(String, primary_key=True, default=build_uuid)
    test_sample_id = Column(String, nullable=False) # Sterilized
    control_sample_id = Column(String, nullable=False) # Non-sterilized benchmark
    sterilization_validated = Column(Boolean, default=False)
    growth_in_test_sample = Column(Boolean, default=False)
    growth_in_control_sample = Column(Boolean, default=True)
    report_sent_to = Column(String, nullable=True) # Department
    tested_at = Column(DateTime, default=datetime.utcnow)

class BloodBankInventory(Base):
    __tablename__ = "lis_blood_bank_inventory"
    id = Column(String, primary_key=True, default=build_uuid)
    unit_id = Column(String, unique=True, index=True, nullable=False)
    blood_group = Column(String, nullable=False, index=True)
    donor_id = Column(String, nullable=False)
    donor_email = Column(String, nullable=True)
    collection_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    component_type = Column(String, default="Whole Blood") # PRBC, FFP, Platelets
    status = Column(String, default="Available", index=True) # Available, Cross-Matched, Used, Discarded
