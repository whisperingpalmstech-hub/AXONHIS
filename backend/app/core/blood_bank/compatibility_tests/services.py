from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CrossmatchTest, CompatibilityResult
from .schemas import CrossmatchTestCreate, CrossmatchTestUpdate

COMPATIBILITY_MATRIX = {
    # Donor (Unit): [Compatible Recipients]
    "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
    "O+": ["O+", "A+", "B+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "A+": ["A+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"],
}


class CompatibilityTestService:
    @staticmethod
    def is_compatible(unit_blood_group: str, unit_rh: str, patient_blood_group: str, patient_rh: str) -> bool:
        unit_full = f"{unit_blood_group}{unit_rh}"
        patient_full = f"{patient_blood_group}{patient_rh}"
        
        # If any of the blood group or rh factor is missing, we must fail.
        # Ensure it's in the standard format like O-, AB+
        return patient_full in COMPATIBILITY_MATRIX.get(unit_full, [])

    @staticmethod
    async def create_crossmatch(session: AsyncSession, test_in: CrossmatchTestCreate) -> CrossmatchTest:
        db_test = CrossmatchTest(**test_in.model_dump())
        
        # We can run an initial system check and if they are biologically incompatible, reject directly
        # But crossmatch is a biological test performed in lab.
        # We can just prevent creating incompatible ones or just mark them incompatible?
        # A blood bank crossmatches "compatible" blood.
        if not CompatibilityTestService.is_compatible(
            test_in.unit_blood_group[:-1], test_in.unit_blood_group[-1],
            test_in.patient_blood_group[:-1], test_in.patient_blood_group[-1]
        ):
            db_test.compatibility_result = CompatibilityResult.INCOMPATIBLE
        else:
            db_test.compatibility_result = CompatibilityResult.PENDING

        session.add(db_test)
        await session.commit()
        await session.refresh(db_test)
        return db_test

    @staticmethod
    async def get_crossmatch(session: AsyncSession, test_id: UUID) -> CrossmatchTest:
        db_test = await session.get(CrossmatchTest, test_id)
        if not db_test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crossmatch test not found")
        return db_test

    @staticmethod
    async def list_crossmatches(session: AsyncSession) -> list[CrossmatchTest]:
        result = await session.execute(select(CrossmatchTest))
        return list(result.scalars().all())

    @staticmethod
    async def update_crossmatch(session: AsyncSession, test_id: UUID, test_in: CrossmatchTestUpdate) -> CrossmatchTest:
        db_test = await CompatibilityTestService.get_crossmatch(session, test_id)
        update_data = test_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_test, key, value)
        await session.commit()
        await session.refresh(db_test)
        return db_test
