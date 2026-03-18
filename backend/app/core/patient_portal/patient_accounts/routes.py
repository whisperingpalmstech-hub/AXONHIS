from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import DBSession
from .schemas import PatientAccountCreate, PatientAccountOut, PatientAccountLogin, Token
from .services import PatientAccountService

router = APIRouter(prefix="/accounts", tags=["Patient Portal - Accounts"])

@router.post("/register", response_model=PatientAccountOut)
async def register(data: PatientAccountCreate, db: DBSession) -> PatientAccountOut:
    # Check if email already exists
    existing = await PatientAccountService.get_account_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    account = await PatientAccountService.create_account(db, data)
    return account

@router.post("/login", response_model=Token)
async def login(data: PatientAccountLogin, db: DBSession) -> Token:
    account = await PatientAccountService.get_account_by_email(db, data.email)
    if not account or not await PatientAccountService.verify_password(data.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # In a real app we'd generate a real JWT here
    # For now we'll return a placeholder
    return Token(access_token=f"patient_token_{account.id}")
