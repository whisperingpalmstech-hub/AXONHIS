from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update
from datetime import datetime, timezone, date
import uuid
from fastapi import HTTPException

from .models import TokenQueue, TokenHistory, QueueCounter, KioskSession, AppointmentCheckIn, QueueAnnouncement
from .schemas import TokenQueueCreate, CallTokenCommand, KioskAppointmentBooking
from app.core.notifications.services import NotificationService # for TV / announcements or staff

class KioskQueueService:
    @staticmethod
    async def generate_token(db: AsyncSession, data: TokenQueueCreate, machine_id: str = "KIOSK_MAIN"):
        today = date.today()
        # Get max token for today
        stmt = select(func.max(TokenQueue.token_number)).where(func.date(TokenQueue.generated_at) == today)
        res = await db.execute(stmt)
        max_num = res.scalar() or 0
        
        new_num = max_num + 1
        prefix = "ER" if data.priority else "T"
        display = f"{prefix}-{new_num:03d}"

        token = TokenQueue(
            token_number=new_num,
            token_prefix=prefix,
            token_display=display,
            department=data.department,
            doctor_id=data.doctor_id,
            patient_uhid=data.patient_uhid,
            patient_name=data.patient_name,
            priority=data.priority,
            priority_reason=data.priority_reason
        )
        db.add(token)
        
        session = KioskSession(
            kiosk_machine_id=machine_id,
            action_performed="Token Print",
            patient_uhid=data.patient_uhid
        )
        db.add(session)
        
        # log history
        await db.flush()
        db.add(TokenHistory(token_id=token.id, old_status=None, new_status="Pending"))
        
        await db.commit()
        await db.refresh(token)
        return token

    @staticmethod
    async def get_queue(db: AsyncSession, status: str = None):
        stmt = select(TokenQueue, QueueCounter.counter_name).outerjoin(QueueCounter, TokenQueue.counter_id == QueueCounter.id)
        if status:
            stmt = stmt.where(TokenQueue.status == status)
        # Sort by priority first, then token number
        stmt = stmt.order_by(TokenQueue.priority.desc(), TokenQueue.token_number.asc())
        res = await db.execute(stmt)
        
        out = []
        for tq, cname in res.all():
            dto = tq.__dict__.copy()
            dto['counter_name'] = cname
            out.append(dto)
        return out

    @staticmethod
    async def call_token(db: AsyncSession, cmd: CallTokenCommand):
        # Move token to calling
        tq = (await db.execute(select(TokenQueue).where(TokenQueue.id == cmd.token_id))).scalars().first()
        if not tq: raise HTTPException(status_code=404, detail="Token not found")
        
        counter = None
        if cmd.counter_id:
            c_res = await db.execute(select(QueueCounter).where(QueueCounter.id == cmd.counter_id))
            counter = c_res.scalars().first()
            
        if not counter:
            # Fallback to the first available counter
            c_res = await db.execute(select(QueueCounter).limit(1))
            counter = c_res.scalars().first()
            
        if not counter: raise HTTPException(status_code=404, detail="No counters configured. Please run seed script.")

        old = tq.status
        tq.status = "Calling"
        tq.counter_id = counter.id
        tq.called_at = datetime.now(timezone.utc)
        
        db.add(TokenHistory(token_id=tq.id, old_status=old, new_status="Calling"))
        
        # Trigger Voice Announcement Log
        msg = f"Token number {tq.token_number}, please proceed to {counter.counter_name}."
        ann = QueueAnnouncement(token_id=tq.id, announcement_text=msg)
        db.add(ann)
        
        await db.commit()
        
        # Mock Cross-module doctor desk / public display push here
        return {"status": "success", "announcement": msg, "token": tq.token_display}

    @staticmethod
    async def update_token_status(db: AsyncSession, token_id: uuid.UUID, new_status: str):
        tq = (await db.execute(select(TokenQueue).where(TokenQueue.id == token_id))).scalars().first()
        if not tq: raise HTTPException(status_code=404, detail="Token not found")
        
        old = tq.status
        tq.status = new_status
        db.add(TokenHistory(token_id=tq.id, old_status=old, new_status=new_status))
        await db.commit()
        return tq

    @staticmethod
    async def check_in(db: AsyncSession, identifier: str, machine_id: str = "KIOSK_MAIN"):
        # Dummy logic: assumes valid. Generates token linked to appointment
        # Reusing generate_token
        db.add(KioskSession(
            kiosk_machine_id=machine_id,
            action_performed="Check-In",
            patient_uhid=identifier
        ))
        await db.commit()
        
        return await KioskQueueService.generate_token(
            db, 
            TokenQueueCreate(department="OPD Consultation", patient_uhid=identifier)
        )

    @staticmethod
    async def get_departments(db: AsyncSession):
        return [
            {"id": "GEN", "name": "General Medicine"}, 
            {"id": "CARDIO", "name": "Cardiology"}, 
            {"id": "ORTHO", "name": "Orthopedics"},
            {"id": "PEDS", "name": "Pediatrics"}
        ]

    @staticmethod
    async def get_doctors(db: AsyncSession, department: str):
        return [
            {"id": "d4f3b259-2c3f-42e5-bc0c-123456789a01", "name": "Dr. Sarah Jenkins", "department": department},
            {"id": "d4f3b259-2c3f-42e5-bc0c-123456789a02", "name": "Dr. Michael Chen", "department": department}
        ]

    @staticmethod
    async def book_appointment(db: AsyncSession, data: KioskAppointmentBooking):
        uhid = f"TMP-{uuid.uuid4().hex[:6].upper()}"
        
        # Save kiosk session
        db.add(KioskSession(
            kiosk_machine_id="KIOSK_MAIN",
            action_performed="New Appointment",
            patient_uhid=uhid
        ))
        
        # We auto check them in immediately because they booked at the kiosk.
        await db.commit()
        return await KioskQueueService.generate_token(
            db,
            TokenQueueCreate(department=data.department, doctor_id=data.doctor_id, patient_uhid=uhid, patient_name=data.patient_name)
        )
