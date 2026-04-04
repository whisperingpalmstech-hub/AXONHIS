from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db

from .schemas import TokenQueueCreate, TokenQueueOut, CallTokenCommand, AppointmentCheckInCommand, KioskAppointmentBooking
from .services import KioskQueueService

router = APIRouter(prefix="/kiosk", tags=["Self-Service Kiosk & Queue"])

@router.post("/token", response_model=TokenQueueOut)
async def generate_token(data: TokenQueueCreate, db: AsyncSession = Depends(get_db)):
    return await KioskQueueService.generate_token(db, data)

@router.get("/queue")
async def get_live_queue(status: str = None, db: AsyncSession = Depends(get_db)):
    return await KioskQueueService.get_queue(db, status)

@router.post("/call")
async def call_patient(cmd: CallTokenCommand, db: AsyncSession = Depends(get_db)):
    return await KioskQueueService.call_token(db, cmd)

@router.post("/check-in", response_model=TokenQueueOut)
async def kiosk_check_in(cmd: AppointmentCheckInCommand, db: AsyncSession = Depends(get_db)):
    return await KioskQueueService.check_in(db, cmd.identifier)

@router.put("/token/{token_id}/status", response_model=TokenQueueOut)
async def update_status(token_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    return await KioskQueueService.update_token_status(db, token_id, payload.get("status"))

@router.get("/departments")
async def get_departments(db: AsyncSession = Depends(get_db)):
    return await KioskQueueService.get_departments(db)

@router.get("/doctors")
async def get_doctors(department: str, db: AsyncSession = Depends(get_db)):
    return await KioskQueueService.get_doctors(db, department)

@router.post("/appointments", response_model=TokenQueueOut)
async def book_appointment(data: KioskAppointmentBooking, db: AsyncSession = Depends(get_db)):
    return await KioskQueueService.book_appointment(db, data)
