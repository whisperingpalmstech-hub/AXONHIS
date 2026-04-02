from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import DBSession
from .schemas import PatientAccountCreate, PatientAccountOut, PatientAccountLogin, Token
from .services import PatientAccountService
import uuid
from datetime import datetime

router = APIRouter(prefix="/accounts", tags=["Patient Portal - Accounts"])

@router.post("/register", response_model=PatientAccountOut)
async def register(data: PatientAccountCreate, db: DBSession) -> PatientAccountOut:
    # Check if email already exists in portal accounts
    existing = await PatientAccountService.get_account_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered for this portal"
        )
    
    account = await PatientAccountService.create_account(db, data)
    return account

@router.get("/search", response_model=PatientAccountOut)
async def search_patient(query: str, db: DBSession) -> dict:
    from app.core.patients.patients.models import Patient
    # Search in main patients table
    from sqlalchemy import or_
    stmt = select(Patient).where(or_(Patient.email == query, Patient.phone_number == query))
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found in HIS")
        
    return {
        "id": uuid.uuid4(), # Placeholder ID for the account-to-be
        "patient_id": patient.id,
        "email": patient.email,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "account_status": "PENDING",
        "created_at": datetime.now()
    }

@router.post("/login", response_model=Token)
async def login(data: PatientAccountLogin, db: DBSession) -> Token:
    account = await PatientAccountService.get_account_by_email(db, data.email)
    if not account or not await PatientAccountService.verify_password(data.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # In a real app we'd generate a real JWT here
    return Token(access_token=f"patient_token_{account.id}")

@router.get("/profile", response_model=PatientAccountOut)
async def get_profile(patient_id: str, db: DBSession) -> PatientAccountOut:
    account = await PatientAccountService.get_account_by_id(db, uuid.UUID(patient_id))
    if not account:
        raise HTTPException(status_code=404, detail="Patient not found")
    return account
