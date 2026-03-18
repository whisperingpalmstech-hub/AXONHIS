import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from .models import PatientAccount, PatientAccountStatus
from .schemas import PatientAccountCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PatientAccountService:
    @staticmethod
    async def get_account_by_email(db: AsyncSession, email: str) -> PatientAccount | None:
        result = await db.execute(select(PatientAccount).where(PatientAccount.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_account(db: AsyncSession, data: PatientAccountCreate) -> PatientAccount:
        db_account = PatientAccount(
            patient_id=data.patient_id,
            email=data.email,
            phone_number=data.phone_number,
            password_hash=pwd_context.hash(data.password),
            account_status=PatientAccountStatus.ACTIVE.value
        )
        db.add(db_account)
        await db.flush()
        return db_account

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
