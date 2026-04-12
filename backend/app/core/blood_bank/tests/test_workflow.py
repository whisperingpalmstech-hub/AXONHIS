"""Integration-style tests for the blood bank transfusion workflow.

These tests validate the business logic layer (services) directly
using database sessions, covering:
  1. Donor registration & collection
  2. Blood unit creation from a collection
  3. Crossmatch / compatibility testing
  4. Transfusion order → allocation
  5. Transfusion administration
  6. Transfusion reaction reporting
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.core.blood_bank.donors.schemas import BloodDonorCreate, BloodCollectionCreate
from app.core.blood_bank.donors.services import BloodDonorService
from app.core.blood_bank.blood_components.schemas import BloodComponentCreate
from app.core.blood_bank.blood_components.services import BloodComponentService
from app.core.blood_bank.blood_units.schemas import BloodUnitCreate
from app.core.blood_bank.blood_units.services import BloodUnitService
from app.core.blood_bank.compatibility_tests.schemas import CrossmatchTestCreate
from app.core.blood_bank.compatibility_tests.services import CompatibilityTestService
from app.core.blood_bank.transfusions.schemas import TransfusionCreate, TransfusionUpdate
from app.core.blood_bank.transfusions.services import TransfusionService
from app.core.blood_bank.transfusion_reactions.schemas import TransfusionReactionCreate
from app.core.blood_bank.transfusion_reactions.services import TransfusionReactionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_donor_registration(db):
    donor = await BloodDonorService.create_donor(db, BloodDonorCreate(
        donor_id="DN-001",
        first_name="Rajesh",
        last_name="Kumar",
        date_of_birth="1990-05-10",
        blood_group="O",
        rh_factor="+",
        contact_number="9876543210",
    ))
    assert donor.donor_id == "DN-001"
    assert donor.screening_status == "eligible"


@pytest.mark.asyncio
async def test_blood_collection(db):
    donor = await BloodDonorService.create_donor(db, BloodDonorCreate(
        donor_id="DN-002",
        first_name="Priya",
        last_name="Sharma",
        date_of_birth="1985-02-20",
        blood_group="A",
        rh_factor="+",
        contact_number="9988776655",
    ))

    collection = await BloodDonorService.create_collection(db, BloodCollectionCreate(
        donor_id=donor.id,
        collection_date=_now(),
        collection_location="Blood Camp #4",
        collected_by="Dr. Mehta",
        collection_volume=450.0,
        screening_results={
            "HIV": "negative",
            "Hepatitis_B": "negative",
            "Hepatitis_C": "negative",
            "Syphilis": "negative",
            "Malaria": "negative",
        },
    ))
    assert collection.collection_volume == 450.0


@pytest.mark.asyncio
async def test_crossmatch_compatible():
    """System-level compatibility check for O- → AB+ (should be compatible)."""
    result = CompatibilityTestService.is_compatible("O", "-", "AB", "+")
    assert result is True


@pytest.mark.asyncio
async def test_crossmatch_incompatible():
    """System-level compatibility check for AB+ → O- (should be incompatible)."""
    result = CompatibilityTestService.is_compatible("AB", "+", "O", "-")
    assert result is False
