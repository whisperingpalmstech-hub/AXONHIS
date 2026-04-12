import uuid
from fastapi import APIRouter, HTTPException, status
from .schemas import SurgicalProcedureCreate, SurgicalProcedureUpdate, SurgicalProcedureOut
from .services import SurgicalProcedureService
from app.dependencies import CurrentUser, DBSession


router = APIRouter(prefix="/procedures", tags=["Surgical Procedures"])

@router.post("/", response_model=SurgicalProcedureOut, status_code=status.HTTP_201_CREATED)
async def create_procedure(data: SurgicalProcedureCreate, db: DBSession, _: CurrentUser) -> SurgicalProcedureOut:
    return await SurgicalProcedureService.create_procedure(db, data)

@router.get("/", response_model=list[SurgicalProcedureOut])
async def list_procedures(db: DBSession, _: CurrentUser) -> list[SurgicalProcedureOut]:
    return await SurgicalProcedureService.get_all_procedures(db)

@router.get("/{procedure_id}", response_model=SurgicalProcedureOut)
async def get_procedure(procedure_id: uuid.UUID, db: DBSession, _: CurrentUser) -> SurgicalProcedureOut:
    procedure = await SurgicalProcedureService.get_procedure(db, procedure_id)
    if not procedure:
        raise HTTPException(status_code=404, detail="Surgical procedure not found")
    return procedure

@router.put("/{procedure_id}", response_model=SurgicalProcedureOut)
async def update_procedure(procedure_id: uuid.UUID, data: SurgicalProcedureUpdate, db: DBSession, _: CurrentUser) -> SurgicalProcedureOut:
    procedure = await SurgicalProcedureService.update_procedure(db, procedure_id, data)
    if not procedure:
        raise HTTPException(status_code=404, detail="Surgical procedure not found")
    return procedure

@router.delete("/{procedure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_procedure(procedure_id: uuid.UUID, db: DBSession, _: CurrentUser):
    if not await SurgicalProcedureService.delete_procedure(db, procedure_id):
        raise HTTPException(status_code=404, detail="Surgical procedure not found")
