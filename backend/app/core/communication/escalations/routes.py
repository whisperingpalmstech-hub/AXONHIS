import uuid
from fastapi import APIRouter, status
from app.dependencies import DBSession, CurrentUser
from .schemas import TaskEscalationCreate, TaskEscalationOut
from .services import EscalationService

router = APIRouter(prefix="/escalation", tags=["Communication - Escalations"])

@router.post("/", response_model=TaskEscalationOut, status_code=status.HTTP_201_CREATED)
async def create_escalation(data: TaskEscalationCreate, db: DBSession, user: CurrentUser) -> TaskEscalationOut:
    return await EscalationService.create_escalation(db, data, escalated_by=user.id)

@router.get("/", response_model=list[TaskEscalationOut])
async def get_escalations(db: DBSession, _: CurrentUser) -> list[TaskEscalationOut]:
    return await EscalationService.get_escalations(db)
