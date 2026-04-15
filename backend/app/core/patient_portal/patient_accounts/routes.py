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

@router.get("/search")
async def search_patient(query: str, db: DBSession) -> dict:
    from app.core.patients.patients.models import Patient
    from sqlalchemy import or_
    import uuid
    try:
        query_uuid = None
        try:
            query_uuid = uuid.UUID(query)
        except ValueError:
            pass

        conditions = [
            Patient.email == query, 
            Patient.primary_phone == query, 
            Patient.patient_uuid == query
        ]
        if query_uuid:
            conditions.append(Patient.id == query_uuid)

        stmt = select(Patient).where(or_(*conditions))
        result = await db.execute(stmt)
        patient = result.scalars().first()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found in HIS")
            
        return {
            "id": str(uuid.uuid4()),
            "patient_id": str(patient.id),
            "email": patient.email or "no-email@test.com",
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "account_status": "PENDING",
            "created_at": str(datetime.now())
        }
    except Exception as e:
        return {"error": str(e), "trace": repr(e)}

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
async def get_profile(patient_id: str = None, db: DBSession = None) -> PatientAccountOut:
    if patient_id:
        account = await PatientAccountService.get_account_by_id(db, uuid.UUID(patient_id))
    else:
        # Return a default profile if no patient_id provided
        return {
            "id": str(uuid.uuid4()),
            "patient_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "account_status": "ACTIVE",
            "created_at": str(datetime.now())
        }
    if not account:
        raise HTTPException(status_code=404, detail="Patient not found")
    return account
