import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import CurrentUser
from .schemas import OrgCreate, OrgOut, SiteCreate, SiteOut
from .services import TenantService

router = APIRouter(prefix="/tenants", tags=["Multi-Tenancy"])

def get_tenant_service(db: AsyncSession = Depends(get_db)):
    return TenantService(db)

@router.get("/organizations", response_model=List[OrgOut])
async def list_orgs(user: CurrentUser, svc: TenantService = Depends(get_tenant_service)):
    return await svc.get_all_organizations(org_id=getattr(user, 'org_id', None))

@router.post("/organizations", response_model=OrgOut)
async def create_org(data: OrgCreate, svc: TenantService = Depends(get_tenant_service)):
    return await svc.create_organization(data)

@router.get("/organizations/{org_id}", response_model=OrgOut)
async def get_org(org_id: uuid.UUID, svc: TenantService = Depends(get_tenant_service)):
    return await svc.get_org(org_id)

@router.post("/organizations/{org_id}/sites", response_model=SiteOut)
async def add_site(org_id: uuid.UUID, data: SiteCreate, svc: TenantService = Depends(get_tenant_service)):
    return await svc.add_site(org_id, data)

@router.post("/organizations/{org_id}/voice")
async def toggle_voice(org_id: uuid.UUID, enable: bool = Query(...), svc: TenantService = Depends(get_tenant_service)):
    await svc.toggle_voice_ai(org_id, enable)
    return {"status": f"System-wide Voice AI {'Enabled' if enable else 'Disabled'}"}

@router.post("/organizations/{org_id}/language")
async def change_lang(org_id: uuid.UUID, lang: str = Query(...), svc: TenantService = Depends(get_tenant_service)):
    await svc.change_language(org_id, lang)
    return {"status": f"Default system language changed to {lang.upper()}"}
