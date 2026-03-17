import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from pydantic import BaseModel
from .schemas import DrugInteractionCreate, DrugInteractionOut
from .services import DrugInteractionService

router = APIRouter(tags=["pharmacy-interactions"])

class CheckInteractionRequest(BaseModel):
    drug_ids: list[uuid.UUID]

@router.post("/drug-interactions/check", response_model=list[DrugInteractionOut])
async def check_interactions(data: CheckInteractionRequest, db: DBSession, _: CurrentUser):
    svc = DrugInteractionService(db)
    return await svc.check_interactions(data.drug_ids)

@router.post("/drug-interactions", response_model=DrugInteractionOut)
async def create_interaction(data: DrugInteractionCreate, db: DBSession, _: CurrentUser):
    svc = DrugInteractionService(db)
    return await svc.create_interaction(data)

@router.get("/drug-interactions", response_model=list[DrugInteractionOut])
async def list_interactions(db: DBSession, _: CurrentUser, limit: int = 100):
    svc = DrugInteractionService(db)
    return await svc.list_interactions(limit=limit)
