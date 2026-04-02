import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from .models import PatientAccount, PatientAccountStatus
from .schemas import PatientAccountCreate

class PatientAccountService:
    @staticmethod
    async def get_account_by_email(db: AsyncSession, email: str) -> PatientAccount | None:
        result = await db.execute(select(PatientAccount).where(PatientAccount.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_account(db: AsyncSession, data: PatientAccountCreate) -> PatientAccount:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(data.password.encode('utf-8'), salt).decode('utf-8')
        db_account = PatientAccount(
            patient_id=data.patient_id,
            email=data.email,
            phone_number=data.phone_number,
            password_hash=hashed,
            account_status=PatientAccountStatus.ACTIVE.value
        )
        db.add(db_account)
        await db.flush()
        return db_account

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError:
            return False

    @staticmethod
    async def get_account_by_id(db: AsyncSession, patient_id: uuid.UUID) -> dict | None:
        from app.core.patients.patients.models import Patient
        query = (
            select(PatientAccount, Patient.first_name, Patient.last_name)
            .join(Patient, PatientAccount.patient_id == Patient.id)
            .where(PatientAccount.patient_id == patient_id)
        )
        result = await db.execute(query)
        row = result.first()
        if not row:
            return None
        
        account, first_name, last_name = row
        return {
            "id": account.id,
            "patient_id": account.patient_id,
            "email": account.email,
            "phone_number": account.phone_number,
            "account_status": account.account_status,
            "first_name": first_name,
            "last_name": last_name,
            "created_at": account.created_at
        }
