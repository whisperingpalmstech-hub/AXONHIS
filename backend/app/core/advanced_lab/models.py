from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

def generate_uuid():
    return f"adv_{uuid.uuid4().hex[:8]}"

class HistoSpecimen(Base):
    __tablename__ = "advanced_histo_specimens"
    id = Column(String, primary_key=True, default=generate_uuid)
    sample_id = Column(String, index=True)
    patient_uhid = Column(String, index=True)
    patient_name = Column(String)
    current_stage = Column(String, default="Specimen Received")
    macroscopic_notes = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False)
    requires_counseling = Column(Boolean, default=False)
    counseling_status = Column(String, default="NA")
    is_oncology = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    blocks = relationship("HistoBlock", back_populates="specimen", cascade="all, delete-orphan")

class HistoBlock(Base):
    __tablename__ = "advanced_histo_blocks"
    id = Column(String, primary_key=True, default=generate_uuid)
    specimen_id = Column(String, ForeignKey("advanced_histo_specimens.id"))
    block_label = Column(String)
    embedding_status = Column(String, default="Pending")
    
    specimen = relationship("HistoSpecimen", back_populates="blocks")
    slides = relationship("HistoSlide", back_populates="block", cascade="all, delete-orphan")

class HistoSlide(Base):
    __tablename__ = "advanced_histo_slides"
    id = Column(String, primary_key=True, default=generate_uuid)
    block_id = Column(String, ForeignKey("advanced_histo_blocks.id"))
    slide_label = Column(String)
    staining_type = Column(String)
    microscopic_diagnosis = Column(Text, nullable=True)
    # Storing JSON array of image URLs
    microscopic_images = Column(JSON, default=list)
    prepared_at = Column(DateTime(timezone=True), server_default=func.now())
    
    block = relationship("HistoBlock", back_populates="slides")

class MicroCulture(Base):
    __tablename__ = "advanced_micro_cultures"
    id = Column(String, primary_key=True, default=generate_uuid)
    sample_id = Column(String, index=True)
    patient_uhid = Column(String, index=True)
    source_department = Column(String, nullable=True)
    incubation_type = Column(String, nullable=True)
    growth_findings = Column(Text, nullable=True)
    organism_identified = Column(String, nullable=True)
    is_infection_control_screen = Column(Boolean, default=False)
    
    sensitivities = relationship("AntiSensitivity", back_populates="culture", cascade="all, delete-orphan")

class AntiSensitivity(Base):
    __tablename__ = "advanced_micro_sensitivities"
    id = Column(String, primary_key=True, default=generate_uuid)
    culture_id = Column(String, ForeignKey("advanced_micro_cultures.id"))
    antibiotic_name = Column(String)
    mic_value = Column(Float, nullable=True)
    susceptibility = Column(String) # Sensitive, Resistant, Intermediate
    
    culture = relationship("MicroCulture", back_populates="sensitivities")

class CSSDTest(Base):
    __tablename__ = "advanced_cssd_tests"
    id = Column(String, primary_key=True, default=generate_uuid)
    test_sample_id = Column(String)
    control_sample_id = Column(String)
    sterilization_validated = Column(Boolean, default=False)
    growth_in_test_sample = Column(Boolean, default=False)
    growth_in_control_sample = Column(Boolean, default=False)
    tested_at = Column(DateTime(timezone=True), server_default=func.now())
    report_sent_to = Column(String, nullable=True)

class BloodBankUnit(Base):
    __tablename__ = "advanced_blood_bank"
    id = Column(String, primary_key=True, default=generate_uuid)
    unit_id = Column(String, index=True, unique=True)
    blood_group = Column(String)
    collection_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    component_type = Column(String) # PRBC, FFP, Platelets
    status = Column(String, default="Available")
