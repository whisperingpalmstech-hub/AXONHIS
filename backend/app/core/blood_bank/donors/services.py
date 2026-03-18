from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import BloodDonor, BloodCollection, ScreeningStatus
from .schemas import BloodDonorCreate, BloodDonorUpdate, BloodCollectionCreate, BloodCollectionUpdate


class BloodDonorService:
    @staticmethod
    async def create_donor(session: AsyncSession, donor_in: BloodDonorCreate) -> BloodDonor:
        stmt = select(BloodDonor).where(BloodDonor.donor_id == donor_in.donor_id)
        existing = await session.scalar(stmt)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Donor already exists")

        db_donor = BloodDonor(**donor_in.model_dump())
        session.add(db_donor)
        await session.commit()
        await session.refresh(db_donor)
        return db_donor

    @staticmethod
    async def get_donor(session: AsyncSession, donor_id: UUID) -> BloodDonor:
        db_donor = await session.get(BloodDonor, donor_id)
        if not db_donor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")
        return db_donor

    @staticmethod
    async def list_donors(session: AsyncSession) -> list[BloodDonor]:
        result = await session.execute(select(BloodDonor))
        return list(result.scalars().all())

    @staticmethod
    async def update_donor(session: AsyncSession, donor_id: UUID, donor_in: BloodDonorUpdate) -> BloodDonor:
        db_donor = await BloodDonorService.get_donor(session, donor_id)
        update_data = donor_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_donor, key, value)
        await session.commit()
        await session.refresh(db_donor)
        return db_donor

    @staticmethod
    async def create_collection(session: AsyncSession, collection_in: BloodCollectionCreate) -> BloodCollection:
        donor = await session.get(BloodDonor, collection_in.donor_id)
        if not donor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")

        db_collection = BloodCollection(**collection_in.model_dump())
        
        # Update last_donation_date for donor
        donor.last_donation_date = db_collection.collection_date.date()

        session.add(db_collection)
        await session.commit()
        await session.refresh(db_collection)
        return db_collection

    @staticmethod
    async def get_donor_collections(session: AsyncSession, donor_id: UUID) -> list[BloodCollection]:
        stmt = select(BloodCollection).where(BloodCollection.donor_id == donor_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())
