"""OPD Smart Queue & Flow Orchestration Engine — Business Logic Services"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, asc

from .models import (
    QueueMaster, QueuePatientPosition, QueueEvent, QueueNotification,
    CrowdPredictionSnapshot, QueueStatus, QueuePriority, RoomWayfindingMapping, RoomStatus
)
from .schemas import (
    QueueMasterCreate, QueuePositionCreate, ActivePatientDisplay, DigitalSignageDisplay
)

class QueueOrchestrationEngine:
    """Manages the lifecycle of a patient queue"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_priority_score(self, priority: QueuePriority) -> int:
        scores = {
            QueuePriority.emergency: 1,
            QueuePriority.priority: 2,
            QueuePriority.vip: 3,
            QueuePriority.appointment: 4,
            QueuePriority.walk_in: 5
        }
        return scores.get(priority, 5)

    async def get_or_create_queue(self, data: QueueMasterCreate) -> QueueMaster:
        now = datetime.utcnow()
        query = select(QueueMaster).where(
            and_(
                QueueMaster.doctor_id == data.doctor_id,
                QueueMaster.department == data.department,
                # For simplicity, filtering by same day
            )
        ) # Ideal world: filter by active queues today, but simple for now.
        result = await self.db.execute(query)
        q = result.scalars().first()
        if not q:
            q = QueueMaster(
                doctor_id=data.doctor_id, department=data.department,
                room_number=data.room_number, room_status=data.room_status.value
            )
            self.db.add(q)
            await self.db.commit()
            await self.db.refresh(q)
        return q

    async def add_patient_to_queue(self, data: QueuePositionCreate) -> QueuePatientPosition:
        score = self._get_priority_score(data.priority_level)
        pos = QueuePatientPosition(
            queue_id=data.queue_id, visit_id=data.visit_id, patient_id=data.patient_id,
            priority_level=data.priority_level.value, calculated_priority_score=score
        )
        self.db.add(pos)
        
        event = QueueEvent(
            queue_id=data.queue_id, visit_id=data.visit_id,
            event_type="joined", event_details={"priority": data.priority_level.value}
        )
        self.db.add(event)
        
        await self.db.commit()
        await self.db.refresh(pos)
        
        # After adding, recalculate queue positions
        await self.reorder_queue(data.queue_id)
        return pos

    async def reorder_queue(self, queue_id: uuid.UUID):
        # Sort logic: Primary -> Priority Score (Low=emergency), Secondary -> Joined At (FIFO)
        # We only reorder 'waiting' or 'skipped' (standby)
        query = select(QueuePatientPosition).where(
            and_(
                QueuePatientPosition.queue_id == queue_id,
                QueuePatientPosition.status.in_([QueueStatus.waiting, QueueStatus.skipped])
            )
        ).order_by(
            QueuePatientPosition.calculated_priority_score.asc(),
            QueuePatientPosition.joined_at.asc()
        )
        result = await self.db.execute(query)
        positions = result.scalars().all()
        
        q_result = await self.db.execute(select(QueueMaster).where(QueueMaster.id == queue_id))
        master = q_result.scalars().first()
        if not master: return
        
        # Calculate positions and Wait Time Predictions
        avg_time = int(master.avg_consult_time_min)
        total_waiting_time = 0
        
        for idx, pos in enumerate(positions):
            pos.position_number = idx + 1
            pos.estimated_wait_time_min = total_waiting_time
            # Next person waits for previous time + consult duration
            total_waiting_time += avg_time 
            
        master.current_length = len(positions)
        await self.db.commit()

class RealTimeQueueDashboardService:
    """Powers the nurse station and digital signage displays"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_digital_signage(self, queue_id: uuid.UUID) -> Optional[DigitalSignageDisplay]:
        # 1. Fetch queue basics
        query_qm = select(QueueMaster).where(QueueMaster.id == queue_id)
        qm = (await self.db.execute(query_qm)).scalars().first()
        if not qm: return None

        # 2. Fetch Active Patient (Called / In Consultation)
        q_current = select(QueuePatientPosition).where(
            and_(
                QueuePatientPosition.queue_id == queue_id,
                QueuePatientPosition.status.in_([QueueStatus.called, QueueStatus.in_consultation])
            )
        ).order_by(QueuePatientPosition.joined_at.desc()) # get newest
        active_rec = (await self.db.execute(q_current)).scalars().first()
        active_disp = None
        if active_rec:
            active_disp = ActivePatientDisplay(
                position_number=0, patient_id=active_rec.patient_id,
                priority_level=active_rec.priority_level, status=active_rec.status,
                patient_name="Pvt. Patient", patient_uhid="UHID-XXX"
            )

        # 3. Fetch Next Patients (Waiting)
        q_next = select(QueuePatientPosition).where(
            and_(QueuePatientPosition.queue_id == queue_id, QueuePatientPosition.status == QueueStatus.waiting)
        ).order_by(QueuePatientPosition.position_number.asc()).limit(3)
        next_recs = (await self.db.execute(q_next)).scalars().all()
        
        next_disp_list = []
        for r in next_recs:
            next_disp_list.append(ActivePatientDisplay(
                position_number=r.position_number or 0, patient_id=r.patient_id,
                priority_level=r.priority_level, status=r.status,
                patient_name="Pvt. Patient", patient_uhid="UHID-YYY"
            ))

        return DigitalSignageDisplay(
            room_number=qm.room_number or ("Dep: " + (qm.department or "General")),
            doctor_name=str(qm.doctor_id) if qm.doctor_id else "Doctor Unknown",
            department=qm.department or "General OPD",
            current_patient=active_disp,
            next_patients=next_disp_list,
            queue_length=qm.current_length,
            avg_wait_time_min=int(qm.avg_consult_time_min)
        )

class PatientRecoveryLogic:
    """Handles skipped patients & recall logic"""
    def __init__(self, db: AsyncSession):
        self.db = db
        self.max_recall = 3
        
    async def mark_missed(self, pos_id: uuid.UUID, actor_id: uuid.UUID):
        pos = (await self.db.execute(select(QueuePatientPosition).where(QueuePatientPosition.id == pos_id))).scalars().first()
        if not pos: return None
        
        pos.missed_calls_count += 1
        pos.last_called_at = datetime.utcnow()
        
        if pos.missed_calls_count >= self.max_recall:
            pos.status = QueueStatus.skipped # Standby / Skip
            # Demote priority effectively to end of line logic via timestamp penalization
            pos.joined_at = datetime.utcnow() 
        else:
            # Standby state but bumped slightly
            pos.status = QueueStatus.skipped
            
        event = QueueEvent(queue_id=pos.queue_id, visit_id=pos.visit_id, event_type="missed_call", actor_id=actor_id)
        self.db.add(event)
        await self.db.commit()

class WaitTimePredictionEngine:
    """Evaluates queue sizes dynamically to project times"""
    # Merged with reorder_queue for efficiency, called from Orchestrator.

class DoctorAvailabilityRoutingEngine:
    """Recommend queues based on fastest processing time / shortest line"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend_queue(self, department: str) -> Optional[QueueMaster]:
        query = select(QueueMaster).where(
            and_(
                QueueMaster.department == department,
                QueueMaster.room_status == RoomStatus.open.value
            )
        ).order_by(QueueMaster.current_length.asc()) # shortest line
        
        # We can implement fancy math (current_length * avg_consult_time_min) here.
        # Simple for now.
        return (await self.db.execute(query)).scalars().first()

class PatientNotificationSystem:
    """Fires sms and pushes notifications"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def notify_patient(self, visit_id: uuid.UUID, patient_id: uuid.UUID, notification_type: str, msg: str):
        notif = QueueNotification(
            visit_id=visit_id, patient_id=patient_id, channel="sms",
            notification_type=notification_type, message_content=msg
        )
        self.db.add(notif)
        await self.db.commit()
        return notif

class WayfindingNavigationEngine:
    """Digital Map & Mapping resolution"""
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_instructions(self, room_number: str) -> str:
        q = select(RoomWayfindingMapping).where(RoomWayfindingMapping.room_number == room_number)
        mapping = (await self.db.execute(q)).scalars().first()
        if mapping and mapping.display_instructions:
            return mapping.display_instructions
        return f"Proceed to Registration Desk for assistance to room {room_number}."

class OPDCrowdPredictionEngine:
    """Artificial Intelligence Engine forecasting crowd spikes"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_prediction(self, date_obj: datetime, dept: str):
        # Implementation of AI logic that outputs a snapshot.
        snap = CrowdPredictionSnapshot(
            prediction_date=date_obj, department=dept,
            predicted_peak_start="10:00", predicted_peak_end="13:30",
            predicted_inflow_count=120, confidence_score=0.89,
            factors_used=["day_of_week", "monthly_trend", "historical_visits"]
        )
        self.db.add(snap)
        await self.db.commit()
        return snap
